# 03. Архитектура Меша Робота и Хард-Серфейс Моделирование

Моделирование техники кардинально отличается от органики: здесь нет мягких деформаций, все детали разделены на функциональные узлы, швы и бронеплиты.

---

## Правила Построения Механической Геометрии

### 1. Модульная конструкция панелей
Не делай робота единым сплошным мешем. Создавай отдельные физические блоки:
- `Hull_Chassis` (несущая рама)
- `Armor_Plate_Front` (лобовой бронелист)
- `Side_Skirts_L / R` (бортовые экраны)
- `Engine_Exhaust` (модуль радиаторов)

### 2. Применение модификатора Bevel
```python
bev = obj.modifiers.new(name="HardBevel", type='BEVEL')
bev.width = 0.012               # 1.2 см ширина фаски
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(30.0) # Фаска наносится только на ребра резче 30 градусов
```

### 3. Булевы операции и удаление каттеров
После булевой нарезки люков и вентиляций удаляй объект-резак немедленно:
```python
mod = main_hull.modifiers.new(name="HatchCut", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter_cylinder
bpy.context.view_layer.objects.active = main_hull
bpy.ops.object.modifier_apply(modifier="HatchCut")

# Удаление каттера
bpy.data.objects.remove(cutter_cylinder, do_unlink=True)
```

### 4. Триангуляция строго при экспорте
Внутри Blender сохраняй сетку из 4-угольников (Quads). Модификатор `TRIANGULATE` накладывается только перед отдачей в движок.
