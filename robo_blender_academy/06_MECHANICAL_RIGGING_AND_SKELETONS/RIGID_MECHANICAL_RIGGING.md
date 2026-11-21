# 06. Жесткий Механический Риггинг и Бинарный Скиннинг

> [!IMPORTANT]
> **Золотое правило техники:** Металлические плиты, башни и шестерни НЕ растягиваются и не деформируются как кожа человека!  
> Вся геометрия должна иметь **100% бинарную привязку (вес 1.0)** к своей кости.

---

## 1. Скрипт Абсолютно Жесткой Привязки (1.0 Rigid Weight)

```python
import bpy

def bind_rigid_mesh_to_bone(rig_obj, mesh_obj, bone_name):
    # Сохраняем мировую трансформацию меша
    world_mat = mesh_obj.matrix_world.copy()
    
    # Привязываем объект к арматуре
    mesh_obj.parent = rig_obj
    mesh_obj.parent_type = 'OBJECT'
    mesh_obj.matrix_world = world_mat
    
    # Создаем вершиную группу с именем кости
    vg = mesh_obj.vertex_groups.get(bone_name) or mesh_obj.vertex_groups.new(name=bone_name)
    vg.remove(range(len(mesh_obj.data.vertices))) # очистка старых весов
    vg.add(range(len(mesh_obj.data.vertices)), 1.0, 'REPLACE') # 100% вес!
    
    # Добавляем модификатор Armature
    mod = next((m for m in mesh_obj.modifiers if m.type == 'ARMATURE'), None)
    if not mod:
        mod = mesh_obj.modifiers.new(name="RigidSkin", type='ARMATURE')
        mod.object = rig_obj
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False
```

---

## 2. Иерархия Костей Танка / Шагохода

| Кость | Родитель | Назначение | Ограничители (Constraints) |
| :--- | :--- | :--- | :--- |
| `root` | - | Общий узел центра масс на земле `(0,0,0)` | - |
| `hull` / `pelvis` | `root` | Корпус машины / таз робота | - |
| `turret` | `hull` | Поворот башни влево/вправо | `Limit Rotation` (только Z) |
| `cannon_mantlet`| `turret` | Вертикальное наведение орудия | `Limit Rotation` (от -10° до +25° по X) |
| `wheel_FL..RR` | `hull` | Колеса / катки | `Limit Rotation` (вращение вокруг X/Y) |
