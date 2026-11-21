# 08. Стандарты Экспорта в Игровые Движки (Godot 4, Unity, UE5)

Чтобы сгенерированная модель робота или машины открывалась в Godot 4, Unity и Unreal Engine 5 без ошибок шейдеров и разрывов скелета:

---

## 1. Ограничение влияния костей (Max 4 Influences)
Мобильные и современные десктопные GPU шейдеры жестко требуют не более 4 костей на вершину:
```python
import bpy

# 1. Удаление микро-весов меньше 0.005
bpy.ops.object.vertex_group_clean(threshold=0.005)

# 2. Ограничение максимума костей
bpy.ops.object.vertex_group_limit_total(limit=4)

# 3. Обязательная нормализация суммы весов к 1.0!
bpy.ops.object.vertex_group_normalize_all()
```

---

## 2. Санация Имен Костей (Удаление Точек)
Игровые парсеры часто воспринимают точки как разделители путей объектов.
- Заменяй `turret.L.001` на `turret_L_001`.

---

## 3. Коллизии для Godot 4
Используй специальные суффиксы в именах мешей:
- `Chassis_Collision-col` — создаст статическую форму столкновения `CollisionShape3D`.
- `Hitbox_Armor-colonly` — создаст невидимую зону столкновения без рендера геометрии.
- `NavFloor-navmesh` — автоматически запечет поверхность навигационной сетки.

---

## 4. Команда Экспорта glTF 2.0
```python
bpy.ops.export_scene.gltf(
    filepath="Robot_Master.glb",
    export_format='GLB',
    use_selection=False,
    export_skins=True,
    export_all_influences=False, # Ограничивает кости до 4!
    export_animations=True,
    export_bake_animation=True
)
```
