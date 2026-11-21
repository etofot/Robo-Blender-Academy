# 08. Санация Имен Костей и Лимиты GPU

### 1. Правило Точек в Именах Костей
В Blender принято называть симметричные кости через точку: `arm.L`, `finger.001.R`.  
Однако игровые движки (особенно парсеры нод и путей Godot 4 и Unreal Engine 5) часто интерпретируют точку как оператор доступа к свойству (`object.property`).

```python
import bpy

def sanitize_bone_names(armature_obj):
    for bone in armature_obj.data.bones:
        if '.' in bone.name:
            new_name = bone.name.replace('.', '_')
            print(f"Renaming bone: {bone.name} -> {new_name}")
            bone.name = new_name
```

---

### 2. Лимит 4 Влияний на Вершину
Игровые движки используют оптимизированные матричные палитры для скиннинга. Если у вершины больше 4 костей с ненулевым весом, движок либо обрежет 5-ю кость со случайным артефактом, либо выбросит ошибку шейдера.  
Перед экспортом всегда выполняй:
```python
bpy.ops.object.vertex_group_clean(threshold=0.005)
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all()
```
