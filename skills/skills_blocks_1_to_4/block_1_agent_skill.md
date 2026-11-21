Ниже — практический Agent Skill Guide для блока 1. Главный принцип: **верификация** установленного API перед записью команды в скилл.

Сразу обозначу границу достоверности: я нашёл документацию функций этих аддонов, но не исходники именно ваших сборок HOps 26.1.7a, Boxcutter 26.1.5_1, Fluent 4.3.2/4.2.0 и MESHmachine 0.21/0.20. Поэтому не буду придумывать имена `bpy.ops` и параметры. Для них ниже — конкретные алгоритмы, безопасный механизм обнаружения реальных операторов и шаблоны привязки. Для современного Bool Tool есть подтверждённые имена операторов, но соответствие именно вашей версии 2.0 всё равно нужно проверить. В Blender операторы зависят от контекста, а `INVOKE_DEFAULT` и `EXEC_DEFAULT` выполняют разные пути кода. [docs.blender](https://docs.blender.org/api/current/bpy.ops.html)

## 0. Архитектура пакета скиллов

Предлагаемая структура:

```text
skills/blender-block-1/
├── SKILL.md
├── references/
│   ├── installed_api.json
│   ├── operator_bindings.json
│   ├── hardops.md
│   ├── boxcutter.md
│   ├── fluent.md
│   ├── meshmachine.md
│   ├── bool_tool.md
│   └── half_knife.md
├── scripts/
│   ├── discover_api.py
│   ├── runtime.py
│   ├── build_parts.py
│   └── geometry_qa.py
└── tests/
    ├── test_boolean_panel.py
    ├── test_hatch_recess.py
    ├── test_fillet_strip.py
    └── test_plane_cut.py
```

### Общие правила для агента

Это предлагаемый контракт вашей системы:

1. Моделировать в локальной системе детали: XY — плоскость чертежа, Z — толщина.
2. На вход принимать размеры, контуры, оси и координаты вырезов, а не экранные пиксели.
3. Хранить исходный контур и параметры отдельно от результирующей сетки.
4. Не запускать неизвестные операторы «на пробу» в рабочей сцене.
5. Не считать `{'FINISHED'}` достаточным доказательством правильной геометрии.
6. Не использовать `INVOKE_DEFAULT` в автономном скилле, пока явно не реализовано завершение modal-операции.
7. Все изменения `bpy` выполнять через главный поток Blender. WebSocket-поток не должен напрямую изменять сцену: Python-интеграция Blender не потокобезопасна. [docs.blender](https://docs.blender.org/api/current/bpy.ops.html)

## 1. Сначала получить реальные команды установленных сборок

Этот скрипт ничего не моделирует и не запускает операторы. Он собирает зарегистрированные Python-операторы интересующих аддонов, их RNA-параметры и расположение исходников.

Запустить через ваш MCP внутри Blender:

```python
import bpy
import sys
import inspect
import json

TOKENS = (
    "hardops", "hops", "boxcutter", "fluent",
    "meshmachine", "bool_tool", "half_knife",
)

def discover_block1_api():
    report = {
        "blender": bpy.app.version_string,
        "enabled_addons": list(bpy.context.preferences.addons.keys()),
        "operators": [],
    }
    seen = set()

    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue
        if not any(t in module_name.lower() for t in TOKENS):
            continue

        for value in list(vars(module).values()):
            if not inspect.isclass(value):
                continue
            try:
                if not issubclass(value, bpy.types.Operator):
                    continue
            except TypeError:
                continue

            idname = getattr(value, "bl_idname", "")
            if not idname or idname in seen or "." not in idname:
                continue

            try:
                namespace, name = idname.split(".", 1)
                op = getattr(getattr(bpy.ops, namespace), name)
                rna = op.get_rna_type()
            except Exception:
                continue

            seen.add(idname)
            properties = {}

            for p in rna.properties:
                if p.identifier == "rna_type":
                    continue
                item = {
                    "type": p.type,
                    "description": p.description,
                    "readonly": p.is_readonly,
                }
                try:
                    default = p.default
                    json.dumps(default)
                    item["default"] = default
                except Exception:
                    pass
                if p.type == "ENUM":
                    try:
                        item["enum"] = [
                            e.identifier for e in p.enum_items
                        ]
                    except Exception:
                        item["enum"] = "dynamic"
                properties[p.identifier] = item

            try:
                source_file = inspect.getsourcefile(value)
            except Exception:
                source_file = None

            report["operators"].append({
                "idname": idname,
                "class": value.__name__,
                "module": value.__module__,
                "source_file": source_file,
                "defines_execute": "execute" in value.__dict__,
                "defines_invoke": "invoke" in value.__dict__,
                "defines_modal": "modal" in value.__dict__,
                "properties": properties,
            })

    report["operators"].sort(key=lambda x: x["idname"])

    text = bpy.data.texts.get("BLOCK1_API.json")
    if text is None:
        text = bpy.data.texts.new("BLOCK1_API.json")
    text.clear()
    text.write(json.dumps(report, ensure_ascii=False, indent=2))
    return report

report = discover_block1_api()
```

Ограничения сканера:

- Он перечисляет доступные Python-классы в загруженных модулях, а не гарантированно все операции аддона.
- Наличие `execute()` не доказывает независимость от GUI.
- Отсутствие `execute()` непосредственно в классе не исключает наследуемую реализацию.
- Версии аддонов и хеши исходников нужно дополнительно взять из `bl_info`/manifest конкретной установки.

Следующий этап — прочитать `poll()`, `execute()`, `invoke()` и функции, которые они вызывают. RNA показывает свойства оператора, но не раскрывает все зависимости от выделения, Preferences, текущего вида и внутренних объектов. Это следует из устройства операторов Blender. [docs.blender](https://docs.blender.org/api/current/bpy.ops.html)

## 2. Общее runtime-ядро для примеров

Ниже — предлагаемый код адаптера. Он не притворяется API аддонов.

Он:

- проверяет существование оператора;
- проверяет имена переданных параметров;
- задаёт реальное выделение;
- при необходимости предоставляет существующий `VIEW_3D`;
- вызывает только `EXEC_DEFAULT`;
- проверяет результат;
- восстанавливает Object Mode и объектное выделение.

Не является полной транзакцией: не восстанавливает Preferences, внутреннее состояние аддона и произвольные побочные изменения. Поэтому неизвестные операторы сначала проверяются в отдельном `.blend`.

```python
import bpy
import bmesh
from contextlib import contextmanager

def resolve_operator(idname):
    namespace, name = idname.split(".", 1)
    op = getattr(getattr(bpy.ops, namespace), name)
    op.get_rna_type()
    return op

@contextmanager
def object_context(objects, active, view3d=False):
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Start skill in Object Mode")

    previous_selected = list(bpy.context.selected_objects)
    previous_active = bpy.context.view_layer.objects.active

    override = {}
    if view3d:
        found = False
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != "VIEW_3D":
                    continue
                region = next(
                    (r for r in area.regions if r.type == "WINDOW"),
                    None,
                )
                if region:
                    override = {
                        "window": window,
                        "area": area,
                        "region": region,
                    }
                    found = True
                    break
            if found:
                break
        if not found:
            raise RuntimeError("Existing VIEW_3D context required")

    try:
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active

        with bpy.context.temp_override(**override):
            yield
    finally:
        if bpy.context.mode != "OBJECT":
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT")

        for obj in list(bpy.context.selected_objects):
            obj.select_set(False)

        for obj in previous_selected:
            if bpy.context.view_layer.objects.get(obj.name) is obj:
                obj.select_set(True)

        if previous_active is not None:
            if bpy.context.view_layer.objects.get(
                previous_active.name
            ) is previous_active:
                bpy.context.view_layer.objects.active = previous_active

def run_bound_operator(binding, objects, active):
    if not binding or not binding.get("verified_exec"):
        raise RuntimeError("Operator binding has not passed sandbox test")

    op = resolve_operator(binding["idname"])
    props = binding.get("props", {})
    valid = set(op.get_rna_type().properties.keys())

    unknown = set(props) - valid
    if unknown:
        raise ValueError(f"Unknown operator properties: {sorted(unknown)}")

    with object_context(
        objects, active, view3d=binding.get("view3d", False)
    ):
        if not op.poll():
            raise RuntimeError(f"poll() failed: {binding['idname']}")

        result = op("EXEC_DEFAULT", **props)
        if result != {"FINISHED"}:
            raise RuntimeError(
                f"Unexpected result {binding['idname']}: {result}"
            )
    return result

def make_box(name, dimensions, location=(0, 0, 0)):
    if any(d <= 0 for d in dimensions):
        raise ValueError("Dimensions must be positive")

    bm = bmesh.new()
    try:
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= dimensions[0]
            v.co.y *= dimensions [docs.blender](https://docs.blender.org/api/current/bpy.ops.html)
            v.co.z *= dimensions [github](https://github.com/oRazeD/PieMenusPlus/blob/master/ui.py)

        mesh = bpy.data.meshes.new(name + "_mesh")
        bm.to_mesh(mesh)
    finally:
        bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj

def discard_objects(objects):
    for obj in reversed(objects):
        try:
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        except ReferenceError:
            pass

def evaluated_basic_qa(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        return {
            "verts": len(bm.verts),
            "faces": len(bm.faces),
            "non_manifold_edges": sum(
                not e.is_manifold for e in bm.edges
            ),
            "zero_area_faces": sum(
                f.calc_area() < 1e-12 for f in bm.faces
            ),
            "volume": abs(bm.calc_volume(signed=True)),
        }
    finally:
        bm.free()
        evaluated.to_mesh_clear()
```

`poll()`, `EXEC_DEFAULT`, наборы возвращаемых статусов и `temp_override()` — документированные механизмы Blender. BMesh-операции позволяют работать с геометрией без интерактивных mesh-операторов. [docs.blender](https://docs.blender.org/api/current/bpy.ops.html)

Важно: `evaluated_basic_qa()` не проверяет самопересечения и не доказывает соответствие чертежу.

***

## 3. Скилл Hard Ops — бронеплита с технологическими вырезами

### 3.1. Архитектура и команды

Hard Ops — hard-surface toolkit с собственной организацией boolean-workflow. Документация подтверждает операции Difference, Union, Slash и работу с несколькими выбранными объектами. Bool Tool для этого ему не требуется. [hardops-manual.readthedocs](https://hardops-manual.readthedocs.io/en/latest/boolean/)

Что искать в установленной сборке:

| Назначение | Что агент проверяет |
|---|---|
| Boolean Difference | Оператор добавления boolean по выбранным объектам |
| Union / Slash | Настройка операции и какие объекты создаются |
| Bevel | Можно ли задать ширину и сегменты через `execute()` |
| Sharpen / shading | Какие модификаторы и настройки меняются |
| Modifier management | Не применяет ли операция лишние модификаторы |

В пространстве `bpy.ops.hops` встречаются и заведомо интерактивные инструменты, например Bool Scroll. Использовать наличие namespace как доказательство пакетного API нельзя. [blenderartists](https://blenderartists.org/t/hard-ops-thread/657591?page=107)

Имена операторов именно 26.1.7a должны попасть в `operator_bindings.json` после локального discovery.

### 3.2. Пайплайн «чертёж → деталь»

Предлагаемый алгоритм:

1. Перевести размеры чертежа в локальные координаты детали.
2. Построить замкнутый контур бронеплиты.
3. Создать толщину.
4. Построить отдельные cutters: люк, разъём, монтажные отверстия.
5. Вызвать проверенный HOps boolean-оператор.
6. Проверить новые модификаторы и их targets.
7. Настроить фаску после конструктивных вырезов.
8. Проверить evaluated mesh и силуэт.
9. Только после приёмки применять модификаторы для экспортной копии.

### 3.3. Особенности автоматизации

- Не передавать cutter, который только касается поверхности. Предусмотреть явное пересечение по глубине.
- Не рассчитывать, что значение solver по умолчанию подходит всем версиям.
- После вызова сравнивать стек модификаторов до/после.
- Не применять Sharpen вслепую после каждого реза: сначала выяснить его побочные эффекты в вашей сборке.
- Хранить cutters редактируемыми до утверждения формы.

Это инженерные правила предлагаемого пайплайна. Для проблемных пересечений Blender документирует Exact solver; опции Self Intersection и Hole Tolerant имеют дополнительную стоимость и не должны включаться автоматически на всех деталях. [docs.blender](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html)

### 3.4. Snippet

Функция действительно вызывает выбранный оператор аддона, но требует проверенного binding. Она не является готовой привязкой к неизвестному API 26.1.7a.

```python
def build_hops_armor(difference_binding):
    created = []
    try:
        plate = make_box(
            "HOps_armor", (0.60, 0.42, 0.025)
        )
        created.append(plate)

        cutter = make_box(
            "HOps_service_slot",
            (0.20, 0.06, 0.075),
            (0.0, 0.08, 0.0),
        )
        created.append(cutter)

        run_bound_operator(
            difference_binding,
            objects=[cutter, plate],
            active=plate,
        )

        qa = evaluated_basic_qa(plate)
        if qa["faces"] == 0 or qa["non_manifold_edges"]:
            raise RuntimeError(f"Invalid armor: {qa}")

        return {"object": plate.name, "qa": qa}
    except Exception:
        discard_objects(created)
        raise
```

Предусловие binding: проверено, что выбранный оператор воспринимает активный объект как target и остальные выбранные объекты как cutters.

***

## 4. Скилл Boxcutter — сложный рез по заранее построенному контуру

### 4.1. Архитектура и команды

Boxcutter ориентирован на интерактивное рисование cutters. Документация описывает состояния Draw, Extrude, Edit Mode, custom cutters и переходы между режимами. Это stateful-инструмент, а не подтверждённая функция «передал вершины — получил boolean». [boxcutter-manual.readthedocs](https://boxcutter-manual.readthedocs.io/en/latest/edit_mode/)

Для вашей сборки нужно отдельно установить:

- есть ли оператор, принимающий уже готовый cutter;
- есть ли у него рабочий `execute()`;
- какие Scene/WindowManager-свойства обязательны;
- создаёт ли `invoke()` необходимое внутреннее состояние;
- можно ли закончить операцию без событий мыши.

Если оператор только запускает рисование и возвращает `RUNNING_MODAL`, автономный скилл ещё не готов. `EXEC_DEFAULT` сам по себе не эмулирует `invoke()` и mouse events. [docs.blender](https://docs.blender.org/api/current/bpy.ops.html)

### 4.2. Пайплайн

1. Агент строит polygonal cutter по контуру чертежа.
2. Проверяет его замкнутость.
3. Задаёт глубину реза численно.
4. Через проверенный адаптер Boxcutter использует готовую геометрию.
5. Проверяет режим: Cut, Slice, Join — не полагается на последний UI-state.
6. Проверяет target и созданный boolean.
7. Сохраняет cutter и параметры.

### 4.3. Особенности и хаки

Документация Boxcutter указывает различное направление offset для Cut и Join. Поэтому переход от Union к Cut может менять фактическое пересечение с поверхностью. Число из старой документации нельзя превращать в универсальный допуск всех размеров и версий. [boxcutter-manual.readthedocs](https://boxcutter-manual.readthedocs.io/en/latest/mode_green/)

Практическое правило: адаптер должен хранить собственный `cut_overlap`, вычисленный из размеров детали, а не надеяться на скрытое состояние аддона.

Если headless-входа нет, корректное решение — написать адаптер к внутренним функциям установленного Boxcutter. Нативный Boolean может быть fallback, но его нужно честно обозначать как fallback, а не как вызов Boxcutter.

### 4.4. Snippet

```python
def build_boxcutter_hatch(cut_existing_shape_binding):
    created = []
    try:
        panel = make_box(
            "BC_hatch_panel", (0.70, 0.50, 0.035)
        )
        created.append(panel)

        cutter = make_box(
            "BC_hatch_cutter",
            (0.32, 0.22, 0.10),
            (0.0, 0.0, 0.0),
        )
        created.append(cutter)

        run_bound_operator(
            cut_existing_shape_binding,
            objects=[cutter, panel],
            active=panel,
        )

        qa = evaluated_basic_qa(panel)
        if qa["faces"] == 0 or qa["non_manifold_edges"]:
            raise RuntimeError(f"Invalid hatch: {qa}")

        return {"object": panel.name, "qa": qa}
    except Exception:
        discard_objects(created)
        raise
```

Этот шаблон применим только после реализации binding «cut existing shape». Наличие такого готового оператора в 26.1.5_1 я не подтвердил. Без него данный пример намеренно не запускается.

***

## 5. Скилл Fluent 4 Power Trip — редактируемая бронепанель с выемкой

### 5.1. Архитектура и команды

Fluent позиционируется как недеструктивный hard-surface toolkit с boolean-, bevel-, plate-, wire- и pipe-workflows. Но пользовательская документация не является спецификацией Python API. Power Trip также отличается по комплекту функций от базовой редакции. [cgthoughts.gumroad](https://cgthoughts.gumroad.com/l/HtPBE)

Для 4.2.0 и 4.3.2 нужны отдельные bindings.

Что искать:

- оператор применения boolean к существующим объектам;
- оператор создания/редактирования Fluent-объекта;
- параметры толщины и bevel;
- внутренние builders для panel/plate;
- функции сортировки модификаторов;
- property groups и custom properties, на которые опирается редактирование.

Нельзя считать объект «Fluent-объектом», просто создав пару пользовательских свойств с предполагаемыми именами.

### 5.2. Пайплайн

1. Построить внешний контур панели.
2. Создать тело панели с известной толщиной.
3. Построить неглубокий cutter люка.
4. Выполнить проверенный boolean-workflow Fluent.
5. Численно настроить толщину, наружную фаску и фаску выемки.
6. Проверить порядок модификаторов.
7. Сохранить редактируемые объекты и параметры.
8. Сделать рендер с ортографической камеры для сравнения с чертежом.

### 5.3. Особенности и хаки

Предлагаемые ограничения адаптера:

- Не редактировать модификаторы по одному отображаемому имени: оно может меняться и локализоваться.
- После операции искать новые модификаторы по типу и ссылкам на объекты.
- Не запускать повторно функцию «создать объект», если требуется «редактировать».
- Не давать глобальной сортировке стека переставлять осознанно расположенные деформирующие модификаторы.
- Перед запуском записывать фактическую версию Fluent и используемую редакцию.

### 5.4. Snippet

Ниже пример неглубокой выемки: cutter пересекает верхнюю поверхность, но оставляет дно.

```python
def build_fluent_recess(difference_binding):
    created = []
    try:
        panel = make_box(
            "Fluent_recess_panel", (0.60, 0.40, 0.030)
        )
        created.append(panel)

        cutter = make_box(
            "Fluent_recess_cutter",
            (0.24, 0.16, 0.020),
            (0.0, 0.0, 0.015),
        )
        created.append(cutter)

        run_bound_operator(
            difference_binding,
            objects=[cutter, panel],
            active=panel,
        )

        qa = evaluated_basic_qa(panel)
        if qa["faces"] == 0 or qa["non_manifold_edges"]:
            raise RuntimeError(f"Invalid Fluent panel: {qa}")

        return {"object": panel.name, "qa": qa}
    except Exception:
        discard_objects(created)
        raise
```

Здесь вызывается Fluent только через locally verified binding. Настройку собственных Fluent bevel-controls нужно добавить после исследования именно вашей версии.

***

## 6. Скилл MESHmachine — конструктивные сопряжения, а не глобальное сглаживание

### 6.1. Архитектура и команды

MESHmachine работает на уровне сетки. Основные инструменты:

- Fuse / Unfuse.
- Chamfer / Unchamfer, обработка bevel.
- Boolean Cleanup.
- Offset / Offset Cut.
- Stashes.
- Plugs.
- Normal Transfer и другие инструменты нормалей. [machin3](https://machin3.io/MESHmachine/docs/index.html)

Принципиальная особенность: Fuse превращает полосу плоской фаски в переходную поверхность. В документации явно задано предусловие — выбранная последовательная полоса полигонов вдоль chamfer. Это не команда «скруглить весь объект». [machin3](https://machin3.io/MESHmachine/docs/fuse/)

Имена `bpy.ops` для 0.20/0.21 нужно получить локальным сканером; не следует угадывать их по названиям кнопок.

### 6.2. Пайплайн

1. Создать исходную форму детали.
2. Сформировать конструктивную фаску — полосу полигонов.
3. Сохранить исходную форму через stash либо собственную копию.
4. Выделить только нужную полосу.
5. Вызвать Fuse с явно заданными параметрами.
6. Проверить переход и отсутствие overshoot.
7. Для исправлений вернуть chamfer через Unfuse.
8. После изменения формы выполнить локальную настройку нормалей.

### 6.3. Особенности и хаки

- «Радиус» Fuse не следует трактовать как точный CAD-радиус окружности: автор указывает, что поверхность зависит от tension и не обязательно точно круговая. [machin3](https://machin3.io/MESHmachine/docs/index.html)
- Не запускать Boolean Cleanup на всей сетке. Инструмент предназначен для переходных рёбер после boolean. [machin3](https://machin3.io/MESHmachine/docs/index.html)
- Использовать stash как источник нормалей с неповреждённой поверхности.
- Не переносить нормали исходной оболочки на новые внутренние стенки отверстий.
- Для деталей с custom normals учитывать специализированные Symmetrize/Real Mirror: они решают в том числе сохранение корректных нормалей при зеркалировании. [machin3](https://machin3.io/MESHmachine/docs/index.html)

### 6.4. Snippet

Честный шаблон для Fuse должен принимать подготовленную полосу, а не случайные индексы граней из сложного boolean-результата.

```python
def meshmachine_fuse_copy(
    source,
    strip_face_indices,
    fuse_binding,
):
    if source.type != "MESH":
        raise TypeError("Mesh object required")
    if not strip_face_indices:
        raise ValueError("Chamfer strip is empty")
    if source.modifiers:
        raise ValueError(
            "Use a prepared mesh copy without live modifiers"
        )

    work = source.copy()
    work.data = source.data.copy()
    work.name = source.name + "_MM_fused"
    bpy.context.collection.objects.link(work)

    try:
        with object_context([work], work, view3d=True):
            bpy.context.tool_settings.mesh_select_mode = (
                False, False, True
            )
            bpy.ops.object.mode_set(mode="EDIT")
            bm = bmesh.from_edit_mesh(work.data)
            bm.faces.ensure_lookup_table()

            wanted = set(strip_face_indices)
            if min(wanted) < 0 or max(wanted) >= len(bm.faces):
                raise IndexError("Invalid chamfer face index")

            for f in bm.faces:
                f.select_set(False)
            for e in bm.edges:
                e.select_set(False)
            for v in bm.verts:
                v.select_set(False)

            for index in wanted:
                bm.faces[index].select_set(True)

            bm.select_flush_mode()
            bmesh.update_edit_mesh(work.data)

            if not fuse_binding.get("verified_exec"):
                raise RuntimeError("Fuse binding is unverified")

            op = resolve_operator(fuse_binding["idname"])
            if not op.poll():
                raise RuntimeError("Fuse poll failed")

            result = op(
                "EXEC_DEFAULT",
                **fuse_binding.get("props", {}),
            )
            if result != {"FINISHED"}:
                raise RuntimeError(f"Fuse returned {result}")

            bpy.ops.object.mode_set(mode="OBJECT")

        qa = evaluated_basic_qa(work)
        if qa["faces"] == 0 or qa["non_manifold_edges"]:
            raise RuntimeError(f"Fuse QA failed: {qa}")

        return {"object": work.name, "qa": qa}
    except Exception:
        discard_objects([work])
        raise
```

Дополнительное предусловие: полоса должна соответствовать требованиям Fuse; проверка одного набора индексов этого не доказывает. Для production-версии нужно добавить проверку связности и двух граничных цепочек. Требование последовательной полосы подтверждено документацией. [machin3](https://machin3.io/MESHmachine/docs/fuse/)

***

## 7. Скилл Bool Tool — наиболее прямой пакетный boolean-workflow

### 7.1. Архитектура и команды

У современного Bool Tool подтверждены следующие идентификаторы в интеграционном коде для Blender 4.2+: [github](https://github.com/oRazeD/PieMenusPlus/blob/master/ui.py)

```python
bpy.ops.object.boolean_brush_difference()
bpy.ops.object.boolean_brush_union()
bpy.ops.object.boolean_brush_intersect()
bpy.ops.object.boolean_brush_slice()

bpy.ops.object.boolean_auto_difference()
bpy.ops.object.boolean_auto_union()
bpy.ops.object.boolean_auto_intersect()
bpy.ops.object.boolean_auto_slice()
```

Смысл:

- Brush — недеструктивный boolean с cutter-объектом.
- Auto — применение операции к геометрии.
- Canvas — активный целевой объект.
- Остальные выбранные объекты — brushes/cutters. [nickberckley.github](https://nickberckley.github.io/bool_tool/booleans/brush_booleans.html)

Не путать со старыми именами `btool.boolean_diff` и `object.booltool_auto_difference`. [github](https://github.com/oRazeD/PieMenusPlus/blob/master/ui.py)

Также актуальная ветка Bool Tool использует новый API Blender 4.5 и не поддерживает 4.4/4.3; ветка 4.2 LTS обслуживается отдельно. Это важнее общего заявления «аддон для Blender 4.x». [extensions.blender](https://extensions.blender.org/add-ons/bool-tool/)

### 7.2. Пайплайн

1. Создать панель.
2. Построить cutters вентиляционных щелей по размерам.
3. Выделить cutters, сделать панель активной.
4. Вызвать Brush Difference.
5. Проверить ссылки boolean-модификаторов.
6. Выставить Exact для создаваемых в примере операций.
7. Проверить evaluated geometry.
8. Оставить cutters для редактирования.

### 7.3. Особенности и хаки

- Для генератора предпочитать Brush, пока форма не утверждена.
- Cutter должен пересекать всю толщину для сквозного отверстия.
- Перед повторным запуском не создавать второй одинаковый boolean.
- Не удалять cutter после Brush: модификатор продолжает на него ссылаться.
- Auto-режим тестировать отдельно: у него иной lifecycle cutters.
- Не считать отсутствие non-manifold рёбер доказательством отсутствия самопересечений.

### 7.4. Snippet — вентиляционная решётка с реальным оператором Bool Tool

Это наиболее конкретный пример блока: в нём нет незаполненного binding. Если вашей установке неизвестен оператор, функция остановится, а не переключится молча на другой инструмент.

```python
def build_booltool_vent(count=6):
    if not isinstance(count, int) or not 1 <= count <= 12:
        raise ValueError("count must be an integer from 1 to 12")

    idname = "object.boolean_brush_difference"
    resolve_operator(idname)

    created = []
    try:
        panel = make_box(
            "BT_vent_panel", (0.60, 0.40, 0.025)
        )
        created.append(panel)

        cutters = []
        pitch = 0.035
        for i in range(count):
            y = (i - (count - 1) / 2) * pitch
            cutter = make_box(
                f"BT_slot_{i:02d}",
                (0.38, 0.015, 0.075),
                (0.0, y, 0.0),
            )
            cutters.append(cutter)
            created.append(cutter)

        before = {
            m.as_pointer() for m in panel.modifiers
        }

        with object_context(cutters + [panel], panel):
            op = resolve_operator(idname)
            if not op.poll():
                raise RuntimeError("Bool Tool poll failed")

            result = op("EXEC_DEFAULT")
            if result != {"FINISHED"}:
                raise RuntimeError(f"Bool Tool returned {result}")

        new_booleans = [
            m for m in panel.modifiers
            if m.type == "BOOLEAN"
            and m.as_pointer() not in before
        ]
        if not new_booleans:
            raise RuntimeError("No Boolean modifiers created")

        for mod in new_booleans:
            mod.solver = "EXACT"

        qa = evaluated_basic_qa(panel)
        if qa["faces"] == 0 or qa["non_manifold_edges"]:
            raise RuntimeError(f"Vent QA failed: {qa}")

        return {
            "object": panel.name,
            "cutters": [o.name for o in cutters],
            "qa": qa,
        }

    except Exception:
        discard_objects(created)
        raise
```

Для особо строгой приёмки добавьте проверку количества отверстий и соответствия объёма ожидаемому — базовый QA этого не делает.

***

## 8. Скилл Half Knife — точные локальные разрезы, но не готовый headless knife

### 8.1. Архитектура и команды

В репозитории автор описывает:

- `modal(self, context, event)` — обработчики мыши;
- `invoke(self, context, event)` — запуск modal либо `run_cut`;
- `run_cut(self)` — логика реза;
- `GeometryMath` — преобразования экранных координат в 3D и обратно. [github](https://github.com/artempoletsky/blender_half_knife)

Это прямо указывает на зависимость от интерактивного контекста.

Режим Cut without preview не равен независимому от GUI API. Пользовательская инструкция всё равно опирается на положение курсора, выбранные элементы и состояние вида. [github](https://github.com/artempoletsky/half_knife_docs)

Следовательно, готовую команду вида:

```python
bpy.ops.half_knife.cut(start=(...), end=(...))
```

я не привожу: наличие такого API не подтверждено.

### 8.2. Пайплайн

Для агента есть два разных сценария:

1. Локальный разрез между выбранными элементами: исследовать `run_cut()` вашей версии и выделить независимое геометрическое ядро.
2. Разрез всей детали заданной плоскостью: использовать BMesh Bisect как явно обозначенную альтернативу, а не выдавать его за Half Knife.

`bmesh.ops.bisect_plane()` принимает точку, нормаль плоскости и параметры удаления сторон. Это документированный геометрический интерфейс. [docs.blender](https://docs.blender.org/api/current/bmesh.ops.html)

### 8.3. Особенности и хаки

- Документация Half Knife предупреждает отключать On Cage у модификаторов, иначе направление разрезов может быть неверным. [github](https://github.com/artempoletsky/half_knife_docs)
- Разрез по плоскости и конечный knife-сегмент — разные операции.
- Не превращать координаты чертежа в screen-space без фиксированных камеры, viewport и матрицы преобразования.
- Не вызывать `run_cut()` на незаполненном экземпляре оператора: `invoke()` мог бы создавать необходимые поля.
- Предпочитать отдельный адаптер с явными входными геометрическими данными.

### 8.4. Snippet — безопасный каркас вызова Half Knife

```python
def halfknife_cut_copy(source, prepared_cut_binding):
    if source.type != "MESH":
        raise TypeError("Mesh object required")
    if source.modifiers:
        raise ValueError("Use a prepared mesh copy")

    work = source.copy()
    work.data = source.data.copy()
    work.name = source.name + "_HK_cut"
    bpy.context.collection.objects.link(work)

    try:
        with object_context([work], work, view3d=True):
            bpy.ops.object.mode_set(mode="EDIT")

            if not prepared_cut_binding.get("verified_exec"):
                raise RuntimeError(
                    "Half Knife requires a verified headless adapter"
                )

            op = resolve_operator(
                prepared_cut_binding["idname"]
            )
            if not op.poll():
                raise RuntimeError("Half Knife adapter poll failed")

            result = op(
                "EXEC_DEFAULT",
                **prepared_cut_binding.get("props", {}),
            )
            if result != {"FINISHED"}:
                raise RuntimeError(f"Knife returned {result}")

            bpy.ops.object.mode_set(mode="OBJECT")

        return {
            "object": work.name,
            "qa": evaluated_basic_qa(work),
        }

    except Exception:
        discard_objects([work])
        raise
```

Это каркас для локально реализованного адаптера. Готового безмышечного Half Knife binding в найденной документации нет; утверждать обратное было бы недостоверно.

***

## 9. Общая защита геометрии и нормалей

### Разделять три разных вида проблем

| Проблема | Что проверять | Что не поможет само по себе |
|---|---|---|
| Неверный объём / отверстия в оболочке | Границы, non-manifold рёбра, вырожденные грани | Weighted normals |
| Самопересечения | Геометрические пересечения поверхностей | Одна проверка manifold |
| Плохой shading | Ориентация граней, smooth/sharp, custom normals | Простое увеличение плотности сетки |

Boolean Exact поддерживает пересекающуюся геометрию лучше простого solver; для self-intersections и проблемных открытых мешей есть дополнительные параметры. Но это не универсальный ремонт исходной модели. [docs.blender](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html)

### Рекомендуемый порядок после сложного реза

1. Проверить фактическую топологию.
2. Исправить вырожденные элементы локально.
3. Проверить ориентацию граней.
4. Если используется BMesh-перестроение — пересчитать face normals на рабочей копии.
5. Затем восстановить smooth/sharp и, при необходимости, custom normals.
6. Только после этого оценивать визуальный shading.

Документированная операция пересчёта:

```python
def recalc_face_orientation(obj):
    if obj.type != "MESH" or obj.mode != "OBJECT":
        raise RuntimeError("Object Mode mesh required")

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(
            bm, faces=list(bm.faces)
        )
        bm.to_mesh(obj.data)
        obj.data.update()
    finally:
        bm.free()
```

`recalc_face_normals` исправляет ориентацию граней, а не восстанавливает художественно настроенные corner normals. После изменения топологии custom-normal workflow нужно проверять отдельно. Для переноса с сохранённой поверхности MESHmachine имеет специализированные инструменты. [docs.blender](https://docs.blender.org/api/current/bmesh.ops.html)

Не запускать такой общий проход без необходимости на финальной детали с уже настроенными UV/custom normals: любые перестроения требуют регрессионной проверки.

## 10. Критерии готовности каждого скилла

Скилл считается рабочим только после выполнения всех условий:

```text
[ ] Зафиксированы Blender version и addon version.
[ ] Записан реальный bl_idname оператора.
[ ] Зафиксированы все используемые RNA-параметры.
[ ] Прочитаны poll / execute / invoke и их зависимости.
[ ] EXEC_DEFAULT завершает действие без мыши.
[ ] Нет оставшегося RUNNING_MODAL.
[ ] Проверено выделение и active object.
[ ] Проверен результат, а не только статус оператора.
[ ] Проверена evaluated mesh.
[ ] Повторный запуск не удваивает вырезы и модификаторы.
[ ] Ошибка не повреждает исходный объект.
[ ] Есть screenshot до/после и тестовая сцена.
[ ] Binding привязан к конкретной сборке.
```

### Приоритет реализации блока 1

1. Bool Tool — самый прямой подтверждённый путь к пакетным boolean-операциям. [github](https://github.com/oRazeD/PieMenusPlus/blob/master/ui.py)
2. Hard Ops — адаптировать конкретные исполняемые boolean/bevel-команды, не весь UI.
3. Fluent — обеспечить корректный lifecycle его объектов и стека.
4. MESHmachine — сделать узкие скиллы под Fuse, Cleanup и Normal Transfer с явными предусловиями. [machin3](https://machin3.io/MESHmachine/docs/index.html)
5. Boxcutter и Half Knife — сначала установить, где заканчивается интерактивная оболочка и начинается вызываемое геометрическое ядро. [boxcutter-manual.readthedocs](https://boxcutter-manual.readthedocs.io/en/latest/edit_mode/)

Таким образом, это проверяемая основа пакета, но не завершённая спецификация API всех перечисленных сборок. Недостающая часть строго определена: локальный `BLOCK1_API.json`, чтение исходников нужных операторов и sandbox-тесты. Без этого «исчерпывающие готовые команды» для платных сборок были бы выдумкой.

