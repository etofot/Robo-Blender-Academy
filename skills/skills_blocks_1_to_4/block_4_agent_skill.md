Подготовил архив блока 4: 16 файлов — скиллы подготовки игрового меха, скрипт жёсткого скининга и экспорта, QA-политика, конфигурация и приёмочные тесты.

Основное правило: **Rigid** означает не просто «одна кость на вершину», а «одна и та же кость с весом 1.0 для всех вершин конкретной металлической детали». Поршневой шток, цилиндр, бронеплита и кожух могут принадлежать разным костям, но каждый отдельный жёсткий элемент не должен сгибаться.

Важные границы пакета:

- У Adaptive Auto Skinning найден документированный Python API — его можно использовать предметно. [jessyleite](https://jessyleite.dev/posts/autoskin-documentation/)
- Section Analysis Tool — инструмент диагностических сечений, не автоматический сертификатор толщины и герметичности. [github](https://github.com/Morbidmod/section-analysis-tool-blender)
- Надёжный официальный источник под точным названием Dreadnought 3D Export Suite не найден. Его команды не выдуманы.
- Код архива проверен синтаксически, но не запускался в Blender и игровых движках. Это строгий reference pipeline для подготовки экспортного кандидата, не уже сертифицированный production-инструмент.

## 1. Состав пакета

```text
blender-block4/
├── README.md
├── config/
│   └── EXAMPLE.py.txt
├── scripts/
│   ├── rigid_export.py
│   ├── autoskin_candidate.py
│   └── discover_api.py
├── skills/
│   ├── 01-autoskin/SKILL.md
│   ├── 02-quad-connect/SKILL.md
│   ├── 03-delta-quad/SKILL.md
│   ├── 04-machin3tools/SKILL.md
│   ├── 05-section/SKILL.md
│   ├── 06-kekit/SKILL.md
│   └── 07-dreadnought/SKILL.md
├── references/
│   ├── QA_POLICY.md
│   ├── ENGINE_PROFILES.md
│   └── SOURCES.md
└── tests/
    └── ACCEPTANCE.md
```

## 2. Общий регламент: исходник → экспортный кандидат

Предлагаемая архитектура:

```text
SOURCE — редактируемый мех
    ↓
STAGING — отдельные копии мешей и экспортного скелета
    ↓
Применение разрешённых геометрических модификаторов
    ↓
Проверка геометрии и координат
    ↓
Настройка origins по проектным суставам
    ↓
Жёсткие веса по Part → Bone
    ↓
Проверка скелета и весов
    ↓
GLB / FBX + JSON QA
    ↓
Повторный импорт и тест в движке
    ↓
RELEASE
```

### Что запрещено агенту

1. Применять Armature modifier у ассета, который должен сохранить скининг.
2. Изменять `head`, `tail` и `roll` костей после bind без отдельного rebinding/rebaking.
3. Делать глобальный Merge by Distance по всему роботу.
4. Автоматически закрывать все отверстия: часть из них конструктивная.
5. Переносить пивоты суставов в центры bounding box.
6. Удалять custom normals без явной политики.
7. Считать непустой FBX доказательством корректного экспорта.
8. Превращать непроверенные параметры аддонов в «подтверждённые» `bpy.ops`.

Экспортёры glTF и FBX предоставляют отдельные параметры skinning, модификаторов и анимации. Их следует задавать явно и проверять через RNA установленного Blender. [docs.blender](https://docs.blender.org/api/current/bpy.ops.export_scene.html)

## 3. Adaptive Auto Skinning v1.5.2

Источник: [полная документация автора с Python API](https://jessyleite.dev/posts/autoskin-documentation/).

### 3.1. Подтверждённый Python API

Автор документирует сервисный интерфейс:

```python
from autoskin.services.diffusion import bind_to_armature

stats = bind_to_armature(
    mesh,
    armature,
    coarse_res=92,
    max_depth=2,
    quality="BALANCED",
    top_k=4,
)
```

Он записывает vertex groups, атрибуты визуализации весов и Armature modifier. Также документирован `write_to_mesh=False` для получения результата без записи весов в меш. Полная спецификация поставляется в `API.md` внутри аддона; её необходимо сверить с установленной 1.5.2. [jessyleite](https://jessyleite.dev/posts/autoskin-documentation/)

### 3.2. Почему `top_k=1` недостаточно для бронеплиты

При `top_k=1` разные вершины одного объекта могут выбрать разные кости:

```text
Вершины слева  → upper_arm.L = 1.0
Вершины справа → forearm.L   = 1.0
```

На каждой вершине вес бинарный, но вся пластина перестаёт быть единым жёстким телом.

Adaptive Auto Skinning использует объёмную диффузию и сохраняет top-K влияний на вершину. В документации не заявлена гарантия единой кости на механическую деталь. [jessyleite](https://jessyleite.dev/posts/autoskin-documentation/)

### 3.3. Правильный скилл для металла

Предлагаемый порядок:

1. Определить механическую принадлежность детали.
2. Записать точный `bone_name`.
3. Удалить конкурирующие deform-веса на экспортной копии.
4. Назначить всем вершинам детали вес 1.0 на выбранную кость.
5. Отключить envelopes.
6. Проверить, что вся деталь имеет одинаковый owner bone.

```python
def assign_rigid_part(obj, armature, bone_name):
    bone = armature.data.bones.get(bone_name)
    if bone is None or not bone.use_deform:
        raise ValueError(f"Invalid deform bone: {bone_name}")

    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)

    group = obj.vertex_groups.new(name=bone_name)
    indices = list(range(len(obj.data.vertices)))

    if indices:
        group.add(indices, 1.0, "REPLACE")

    modifier = obj.modifiers.new("EXPORT_RIG", "ARMATURE")
    modifier.object = armature
    modifier.use_vertex_groups = True
    modifier.use_bone_envelopes = False
    modifier.use_deform_preserve_volume = False
```

В таком варианте исходный автоскиннинг для известных бронеплит вообще не нужен. Он полезнее для гибких элементов или как источник предварительных кандидатов.

### 3.4. Где применять Adaptive Auto Skinning

| Тип детали | Политика |
|---|---|
| Бронеплита | Одна заданная кость, 1.0 на все вершины |
| Шток поршня | Отдельная кость, 1.0 |
| Корпус цилиндра | Другая кость, 1.0 |
| Резиновая гофра | Мягкие веса, максимум 4 по контракту проекта |
| Гибкий шланг | Отдельная цепочка/риг, максимум 4 |
| Жёсткая муфта | Одна кость, 1.0 |

Число 4 здесь — ваш переносимый бюджет, а не универсальный аппаратный предел всех движков. Сам аддон допускает больше влияний и предлагает снижать `top_k` под ограничения целевой системы. [jessyleite](https://jessyleite.dev/posts/autoskin-documentation/)

## 4. Quad Connect v1

Источники: [описание инструмента](https://superhivemarket.com/products/quad-connect/docs) · [описание актуальной V2](https://blenderartists.org/t/3dprs-quad-connect-v2-intelligent-edge-bridging-for-clean-quad-topology/1649148).

### Назначение

Локальное соединение цепочек рёбер и организация quad-flow, в том числе между неравными наборами рёбер. Это не авторетопология всего меха. Публичная документация сейчас описывает V2; её операторы нельзя автоматически переносить на V1. [superhivemarket](https://superhivemarket.com/products/quad-connect/docs)

### Контракт адаптера

```python
connect_edge_chains(
    mesh,
    chain_a,
    chain_b,
    endpoint_mapping,
    flow_mode,
    options,
)
```

Это API вашей обёртки, не подтверждённая сигнатура производителя.

### Скилл

1. Найти конкретный топологический разрыв.
2. Определить обе цепочки.
3. Проверить направление обхода.
4. Явно сопоставить концы.
5. Выполнить соединение.
6. Проверить вырожденные грани и перекрученные соединения.
7. Проверить UV и shading в изменённой области.

### Для робота

Подходит для соединения оболочки вокруг люка, перехода между деталями корпуса или исправления локального участка после boolean.

Не использовать его для «герметизации» технологического отверстия, которое должно остаться открытым.

## 5. Delta Quad

Источник: [страница аддона](https://superhivemarket.com/products/delta-quad).

### Назначение

Разбивает выбранные N-gon грани на quads. Автор прямо описывает его как локальный инструмент обработки больших N-gon, а не ремешер плотного скана. [superhivemarket](https://superhivemarket.com/products/delta-quad)

### Контракт адаптера

```python
quadify_region(
    mesh,
    face_ids,
    flow_mode,
    options,
)
```

Точный `bpy.ops` нужно получить из установленной версии.

### Скилл

1. Выбрать локальные N-gon после конструктивных вырезов.
2. Проверить планарность.
3. Применить Delta Quad только к этой области.
4. Сравнить силуэт и нормали до/после.
5. Проверить количество полигонов.
6. Перед финальным выпуском зафиксировать триангуляцию.

### Важное ограничение

Quadify не означает optimize. Если один N-gon превращён в много quads, геометрии может стать больше. Для игрового ассета результат оценивается по конечным треугольникам и качеству поверхности, а не проценту четырёхугольников.

## 6. MACHIN3tools DeusEx v1.13.3

Источники: [Align](https://machin3.io/MACHIN3tools/docs/align/) · [changelog](https://machin3.io/MACHIN3tools/docs/changelog/index.html).

### Совместимость

Для вашей версии особенно важно:

- 1.13.3 выпущена до изменений поддержки Blender 5.1.
- Поддержка Blender 5.1 / Python 3.13 добавлена в 1.13.8.
- Поддержка Blender 5.2 добавлена в 1.13.9.

Поэтому 1.13.3 нельзя объявлять проверенной для всей линейки Blender 5.x. [machin3](https://machin3.io/MACHIN3tools/docs/changelog/index.html)

### Python API

Исторически подтверждаются пространства и операторы:

```python
bpy.ops.machin3.align(...)
bpy.ops.machin3.mirror(...)
```

Но параметры именно вашей сборки нужно проверить через RNA. В регистрационном коде также присутствуют Origin to Cursor, Origin to Active и Apply Transformations. [github](https://github.com/jonaMclaurin/MACHIN3tools/blob/master/registration.py)

### Скилл выравнивания суставов

1. Получить проектную точку и ось сустава.
2. Сопоставить её с rest bone.
3. Разместить origin детали с компенсацией локальных координат меша.
4. Проверить неизменность геометрии в world-space.
5. Не перемещать саму кость ради исправления origin.

Для переноса origin без движения меша:

\[
v_{\text{new}}=M_{\text{new}}^{-1}M_{\text{old}}v_{\text{old}}.
\]

```python
old_matrix = obj.matrix_world.copy()
new_matrix = Matrix.Translation(joint_world_position)

obj.data.transform(new_matrix.inverted() @ old_matrix)
obj.matrix_world = new_matrix
```

В архивном скрипте это делается на отдельном mesh datablock экспортной копии.

### Критическое различие

Origin объекта и pivot skinning — не одно и то же. Вращение бронеплиты при скининге определяется rest-матрицами костей и весами. Перенос origin не исправит ошибочно поставленный локоть.

Для assembly-origin у MACHIN3tools есть дополнительные механизмы компенсации объектов внутри коллекций; документация отдельно описывает изменение не только положения, но и ориентации assembly origin. [machin3](https://machin3.io/MACHIN3tools/docs/whatsnew/)

## 7. Section Analysis Tool v1.0.0

Найден одноимённый открытый проект: [Morbidmod/section-analysis-tool-blender](https://github.com/Morbidmod/section-analysis-tool-blender). Его identity и версию следует сверить с вашей установкой.

### Что он действительно делает

- Осевые сечения X/Y/Z.
- Offset и tilt.
- Позиционирование по центру выделения.
- Автоматический размер cutter.
- Boolean Difference на объектах.
- Удаление диагностических сечений без разрушения исходной геометрии.
- Требует Blender 4.2+. [github](https://github.com/Morbidmod/section-analysis-tool-blender)

### Чего он не подтверждает автоматически

- Минимальную толщину всех стенок.
- Полную watertight-корректность.
- Отсутствие самопересечений.
- Лимит bone influences.
- Правильность скелета.

### Контракт адаптера

```python
section_preview(
    objects,
    axis,
    offset,
    tilt,
    center_on_selection,
    size_mode,
)
```

Точные операторные имена не подтверждены.

### Скилл QA

1. Создать отдельную QA-копию.
2. Сделать несколько сечений корпуса.
3. Проверить внутренние оболочки, полости, пересекающиеся панели.
4. Измерять толщины в заданных контрольных местах.
5. Для автоматической приёмки использовать отдельную числовую проверку.
6. Перед экспортом удалить section-модификаторы и cutter.

Последний пункт критичен: поскольку инструмент использует booleans, его диагностический результат нельзя случайно запечь в экспортную геометрию. [github](https://github.com/Morbidmod/section-analysis-tool-blender)

## 8. keKit Pro

Источник: [официальная страница и release notes](https://ke-code.xyz/scripts/kekit.html).

### Роль

Инструменты очистки, измерения, выравнивания origins, трансформаций и организации моделирования. Модули могут включаться и отключаться, а набор операторов меняется между версиями. Текущий Pro 4.02 поддерживает Blender 5.2+; для 4.5 существуют отдельные LTS-сборки. [ke-code](https://ke-code.xyz/scripts/kekit.html)

### Python API

В истории встречается `ke_clean`, но это не основание считать его стабильной актуальной сигнатурой Pro. Новые версии меняют операторы и их организацию; точные вызовы должны быть получены локальным discovery. [ke-code](https://ke-code.xyz/scripts/kekit.html)

Контракты:

```python
clean_select(mesh, rules)
repair_selected(mesh, element_ids, repair_policy)
align_origin(obj, joint_frame)
measure_region(mesh, region_ids)
```

### Скилл очистки

1. Сначала выделить и отчитаться о проблемах.
2. Затем исправлять локально на staging.
3. Не применять глобальное слияние вершин.
4. Не удалять seams и hard edges «ради чистоты».
5. Сравнить UV, normals и размеры до/после.
6. Повторно проверить веса, если изменилась топология.

keKit — удобный набор операций, но проверка бинарных весов и скелета должна быть отдельным числовым валидатором.

## 9. Dreadnought 3D Export Suite

Под точным названием не удалось найти надёжную документацию, поэтому в пакете для него предусмотрен скилл инвентаризации, а не вымышленные команды.

Агент должен получить из локальной установки:

```text
module_id
bl_info / blender_manifest
version
export operator IDs
RNA properties
engine presets
animation handling
modifier policy
bone filtering policy
```

До этого используется явно названный нативный экспорт Blender:

```python
bpy.ops.export_scene.gltf(...)
bpy.ops.export_scene.fbx(...)
```

Эти экспортёры и их параметры документированы. Нативный экспорт нельзя записывать в отчёт как успешную интеграцию Dreadnought. [docs.blender](https://docs.blender.org/api/current/bpy.ops.export_scene.html)

## 10. Числовой QA перед экспортом

### Геометрия

Для каждой детали:

```text
finite coordinates
non-empty mesh
zero-area faces/triangles
wire edges
boundary edges
non-manifold edges
self-intersections
wall thickness
triangle budget
```

Пример базового контроля:

```python
bm = bmesh.new()
try:
    bm.from_mesh(obj.data)

    boundary_count = sum(e.is_boundary for e in bm.edges)
    nonmanifold_count = sum(not e.is_manifold for e in bm.edges)
    zero_area_count = sum(
        face.calc_area() <= area_epsilon
        for face in bm.faces
    )
finally:
    bm.free()
```

Этот тест не проверяет самопересечения и толщины.

### Герметичность — по назначению детали

| Тип | Политика |
|---|---|
| Закрытая collision-деталь | Требовать замкнутую корректную оболочку |
| Цельная бронедеталь | Обычно требовать замкнутость |
| Декальная поверхность | Разрешать границы по manifest |
| Односторонняя решётка | Проверять согласно её конструкции |
| Весь робот | Не требовать единой сваренной оболочки |

### Веса

Для металлической детали:

\[
\forall v\in P:\quad w(v,b_P)=1,
\]

\[
w(v,b\neq b_P)=0.
\]

Для гибкой детали по вашему контракту:

\[
N_{\text{influences}}\leq4,
\qquad
\left|\sum_i w_i-1\right|<\varepsilon.
\]

Проверять нужно не просто число vertex groups у объекта, а реальные положительные веса каждой вершины на deform bones.

### Толщина

Регламент должен задавать минимум отдельно:

```text
armor_min_thickness
bracket_min_thickness
hose_wall_thickness
collision_shell_policy
```

Направленные raycasts или измерения противоположных поверхностей требуют исключения self-hit и обработки сложных полостей. Если область не проверена, её статус — `UNKNOWN`, не `PASS`.

## 11. Скрипт полного staging-цикла

В архиве находится `rigid_export.py`.

Пример запуска после загрузки скрипта:

```python
PART_TO_BONE = {
    "TorsoArmor": "spine",
    "UpperArmArmor.L": "upper_arm.L",
    "ForearmArmor.L": "forearm.L",
}

report = prepare_and_export(
    armature_name="MechExportRig",
    part_to_bone=PART_TO_BONE,

    output_dir=r"D:\mech_export_jobs\job_001",

    formats=("GLB", "FBX"),

    closed_parts=set(PART_TO_BONE),
    normal_policy="PRESERVE",
    triangle_budget=50000,
)
```

### Что выполняется

1. Проверка исходного экспортного скелета.
2. Проверка допустимости объектов и стека модификаторов.
3. Создание staging-коллекции.
4. Копирование скелета и mesh datablocks.
5. Применение разрешённых геометрических модификаторов.
6. Перенос origins к головам назначенных костей с компенсацией геометрии.
7. Проверка топологии.
8. Назначение единичных rigid-весов.
9. Проверка весов.
10. Проверка triangle budget.
11. Экспорт GLB/FBX.
12. Проверка заголовка GLB и наличия skin-атрибутов.
13. Сохранение JSON-отчёта.
14. Восстановление выделения.

### Почему скрипт строгий

Он останавливается, а не угадывает поведение, если обнаруживает:

- неизвестный модификатор;
- shape keys;
- неподдерживаемые constraints;
- чужой Armature modifier;
- отрицательный или вырожденный transform;
- отсутствие назначенной кости;
- геометрические модификаторы после Armature;
- неподдерживаемые параметры экспортёра.

Вместо агрессивного автоматического «ремонта» нулевых граней он блокирует экспорт проблемного объекта. Для необратимых исправлений нужен отдельный локальный repair-skill.

### Область применения

Скрипт рассчитан на bind/rest asset:

- отдельный экспортный скелет;
- один root по контракту проекта;
- известное соответствие `Part → Bone`;
- исходный rig в REST;
- единичная world matrix скелета;
- без переноса анимационных клипов.

Контроллерный риг, IK/constraints и анимационные клипы нужно предварительно запечь в экспортный скелет отдельным этапом. glTF поддерживает экспорт pose-bone animation, но режимы Actions/NLA и sampling требуют явной настройки. [docs.blender](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html)

## 12. Профили экспорта под движки

| Движок | Базовый маршрут | Обязательная приёмка |
|---|---|---|
| Godot 4 | GLB/glTF 2.0 | Skeleton, skin, масштабы, ориентация и материалы |
| Unreal Engine 5 | FBX Skeletal Mesh | Root, оси, scale, skeleton mapping, Physics Asset |
| Unity | FBX; для негуманоидного меха рассмотреть Generic | Root node, иерархия, scale, normals и clips |

Godot официально рекомендует glTF; актуальный FBX workflow использует ufbx, а не обязательный старый FBX2glTF. [docs.godotengine](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html)

Unreal документирует FBX Skeletal Mesh Pipeline и отмечает использование FBX 2020.2 в своём импортном конвейере. Это не означает, что настройка одного флага Blender автоматически устраняет все различия форматов. [dev.epicgames](https://dev.epicgames.com/documentation/unreal-engine/fbx-skeletal-mesh-pipeline-in-unreal-engine?lang=en-US)

Unity различает Humanoid и Generic; негуманоидные модели относятся к Generic. При раздельном импорте модели и анимаций также важно сохранять согласованную иерархию root. [docs.unity3d](https://docs.unity3d.com/6000.6/Documentation/Manual/ConfiguringtheAvatar.html)

В скрипте FBX `-Z/Y` — исходная настройка экспортёра, не сертифицированный профиль всех трёх движков.

## 13. Когда ассет действительно готов

Пакет намеренно сохраняет статус:

```text
CANDIDATE_READY
publication = BLOCKED_PENDING_EXTERNAL_QA
```

Выпуск разрешается только после:

- проверки толщин и самопересечений;
- pose-тестов суставов;
- проверки rigid-инвариантов металлических деталей;
- декодирования экспортированных JOINTS/WEIGHTS;
- повторного импорта GLB/FBX в чистый worker;
- проверки skeleton hierarchy и bind pose;
- проверки материалов, UV, текстур и LOD;
- импорта в целевой движок.

Такой регламент не даёт агенту объявить мех «готовым к игре» только потому, что экспортёр вернул `FINISHED`.

