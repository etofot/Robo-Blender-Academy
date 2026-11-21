# 07. Анимация Механизмов, Турелей и Отдачи Оружия

### 1. Анимация башни через пустой объект (Empty Pivot)
```python
import bpy, math

def animate_turret_turn(empty_pivot, start_frame=1, end_frame=60, target_deg=90):
    empty_pivot.rotation_euler.z = 0.0
    empty_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=start_frame)
    
    empty_pivot.rotation_euler.z = math.radians(target_deg)
    empty_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=end_frame)
    
    # Линейный поворот сервопривода
    fc = empty_pivot.animation_data.action.fcurves.find("rotation_euler", index=2)
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
```

### 2. Симуляция импульса отдачи ствола (Recoil)
1. Кадр 0: Ствол в покое `Y = 0.0`.
2. Кадр 2: Выстрел! Мгновенный резкий откат назад `Y = -0.35` м (2 кадра, жесткий удар).
3. Кадры 3..18: Плавное гидравлическое возвращение в исходную позицию (плавная кривая торможения демпфером).
