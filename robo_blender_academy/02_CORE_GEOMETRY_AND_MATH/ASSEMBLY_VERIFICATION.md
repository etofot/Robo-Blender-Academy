# 02. Верификация Сборки и Карта Соединений (Assembly Verification)

Чтобы механическая модель выглядела монолитной и физически достоверной, все детали должны соприкасаться с гарантированным перекрытием (минимум 5 мм / 0.005 м).

---

## 1. Connection Map (Карта Соединений)

Перед написанием кода сборки агент должен составить в уме или в комментарии карту контактов:
```
Connection Map:
  chassis_top (Z=0.40) <-> cabin_bottom (Z=0.39)      перекрытие 0.01м по Z
  wheel_mount (X=0.60) <-> wheel_hub (X=0.59)         перекрытие 0.01м по X
  turret_base          <-> cannon_mantlet             поворотный шарнир
```

---

## 2. Автоматический аудит сцены через `geometry_utils.py`

```python
from geometry_utils import verify_bounds, verify_overlap, finalize, audit_all

# Проверка физического нахлеста деталей
overlap = verify_overlap("Chassis", "Cabin", axis='z', min_overlap=0.005)

# Финализация детали (origin в центр, smooth shading, применение scale/rotation)
finalize("Chassis")

# Итоговый аудит всей сцены: проверяет, что у всех мешей scale=(1,1,1) и rot=(0,0,0)
audit_all()
```
