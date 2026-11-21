# 🦾 MECH LEG 3D ASSETS & REFERENCE STUDY LAB

Этот каталог содержит оригинальную 3D-модель ноги робота-меха, чертежи, фотографии референса и готовую мастер-сборку для ИИ-агентов.

---

## 📦 1. Готовые 3D Модели (Ready-to-use 3D Assets)

Для любого облачного ИИ-агента доступны форматы `.glb` (универсальный) и `.blend` (Blender 4.2+ / 5.2+):

| Файл | Формат | Описание |
| :--- | :--- | :--- |
| **`REFERENCE_LEG_ISOLATED.glb`** | `GLB` (667 KB) | **Оригинальная нога-образец со скриншота** (53 детали, PBR материалы, универсальный формат для Three.js, Godot, Blender, Python). |
| **`REFERENCE_LEG_ISOLATED.blend`** | `BLEND` (517 KB) | Изолированная сцена оригинальной ноги для Blender. |
| **`LEG_REFERENCE_OK.blend`** | `BLEND` (523 KB) | Чистая проверенная сцена ноги (без пробелов в имени файла). |
| **`MASTER_LEG_50_STEPS_COMPLETE.glb`** | `GLB` (4.5 MB) | Финальная мастер-нога (344 детали, болты PCD, гидравлика, зубчатые венцы). |
| **`MASTER_LEG_50_STEPS_COMPLETE.blend`** | `BLEND` (3.0 MB) | Полный 50-шаговый мастер-проект в Blender. |

---

## 🖼️ 2. Фотографии и Чертежи (Reference Photos & Blueprints)

* **`user_viewport_reference.jpg`** — Оригинальный скриншот из Blender Viewport (ракурс пользователя).
* **`real_reference_perspective.png`** — Чистый студийный ракурс 3/4 модели-образца.
* **`user_viewpoint_match.png`** — Рендер с идентичной позиции камеры.
* **`step50_master_leg_side_ortho.png`** — Боковой ортографический чертеж с пропорциями осей вращения.
* **`step50_master_leg_wireframe.png`** — Сетка топологии (Wireframe).
* **`step41_step46_foot_top_ortho.png`** — Чертеж 4-палой стопы (вид сверху).
* **`step33_step40_armor_ortho_side.png`** — Схема раскроя накладных бронеплит.
* **`step03_layer_color_coded_id_map.png`** — Карта 4 функциональных слоев (Chassis, Actuation, Thermal, Armor).

---

## 🛠️ 3. Быстрая загрузка для облачного агента в Python / Blender

```python
import bpy

# 1. Загрузка через универсальный GLB:
bpy.ops.import_scene.gltf(filepath="LEG_STUDY_LAB/REFERENCE_LEG_ISOLATED.glb")

# 2. Либо открытие .blend файла:
# bpy.ops.wm.open_mainfile(filepath="LEG_STUDY_LAB/REFERENCE_LEG_ISOLATED.blend")

print(f"Успешно загружено {len(bpy.data.objects)} деталей ноги-образца!")
```
