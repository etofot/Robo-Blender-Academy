# 07. Линейная Интерполяция и Бесконечные Циклы (F-Curve Cycles)

> [!CAUTION]
> По умолчанию Blender создает ключевые кадры с интерполяцией `BEZIER` (плавный старт и торможение).  
> Для механизмов, гусениц и вращающихся колес это создает нелепый эффект: колесо крутится рывками.

---

## 1. Настройка Линейной Интерполяции в Blender 5.2+
```python
orig_interp = bpy.context.preferences.edit.keyframe_new_interpolation_type
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

# Ставим ключи...
# ...

bpy.context.preferences.edit.keyframe_new_interpolation_type = orig_interp
```

---

## 2. Бесконечное вращение колеса через модификатор F-Curve `CYCLES`
Вместо дублирования десятков ключей добавь циклический модификатор к кривой вращения:
```python
fc = obj.animation_data.action.fcurves.find("rotation_euler", index=0)
cyc = fc.modifiers.new(type='CYCLES')
cyc.mode_after = 'REPEAT_OFFSET' # Колесо продолжает непрерывно наматывать градусы вперед!
```
