# ROBO_BLENDER_ACADEMY — Полный Самоучитель по 3D Робототехнике и Технике в Blender для ИИ-Агентов

> **Добро пожаловать в Академию Робототехники и Моделирования Техники в Blender!**  
> Этот репозиторий представляет собой полностью автономный, самодостаточный пакет знаний, инструментов и производственных скриптов для любого ИИ-агента (LLM / Agentic Pair Programmer), создающего 3D-роботов, мехов, танки, турели, самолеты, военную технику и процедурные механизмы в Blender.

---

## 🧭 Навигатор по Академии (Структура Знаний)

| Раздел | Папка | Содержание и Назначение |
| :--- | :--- | :--- |
| **00. Главный Старт** | [`00_AGENT_TUTORIAL_START_HERE.md`](./00_AGENT_TUTORIAL_START_HERE.md) | **Начни отсюда!** Манифест агента, 10 железных правил геометрии и пошаговый пайплайн |
| **01. Управление Blender** | [`01_MCP_AND_BLENDER_CONTROL/`](./01_MCP_AND_BLENDER_CONTROL/) | MCP-протокол, живой WebSocket-мост, Headless CLI, а также [Карта Профессиональных Аддонов](./01_MCP_AND_BLENDER_CONTROL/ADDON_TOOLKIT_MAP.md) (MESHmachine, MACHIN3tools, Image to 3D, Mesh Materializer) |
| **02. Математика Геометрии** | [`02_CORE_GEOMETRY_AND_MATH/`](./02_CORE_GEOMETRY_AND_MATH/) | Правило `size=2`, балки `bmesh` без вращений Эйлера, `verify_bounds`, `verify_overlap` |
| **03. Хард-Серфейс и Броня** | [`03_ROBOT_HARD_SURFACE_MODELING/`](./03_ROBOT_HARD_SURFACE_MODELING/) | Фаски Bevel вместо Subsurf, конформная UV-развертка без швов, нарезка панелей `bisect` |
| **04. Библиотека Техники** | [`04_VEHICLE_AND_UNIT_LIBRARY/`](./04_VEHICLE_AND_UNIT_LIBRARY/) | Гусеничные шасси, башни, ракетные контейнеры, крылья самолетов, PCA-ориентация в пространстве |
| **05. PBR Металлы и Износ** | [`05_PBR_MATERIALS_AND_SURFACE_WEAR/`](./05_PBR_MATERIALS_AND_SURFACE_WEAR/) | Процедурный металл, царапины, сварные швы, трафареты брони, слоты тактических декалей |
| **06. Риггинг и Шарниры** | [`06_MECHANICAL_RIGGING_AND_SKELETONS/`](./06_MECHANICAL_RIGGING_AND_SKELETONS/) | Жесткие бинарные веса (100%/0%), компенсация пивотов, аналитический Zero-Drift Foot IK |
| **07. Анимация Механизмов** | [`07_MECHANICAL_ANIMATION/`](./07_MECHANICAL_ANIMATION/) | Линейные F-кривые (без желе-эффекта), циклы вращения, отдача пушек, обход багов Blender 5.2 |
| **08. Экспорт в Движки** | [`08_ENGINE_EXPORT_ADAPTATION/`](./08_ENGINE_EXPORT_ADAPTATION/) | glTF 2.0 / FBX для Godot 4, Unity, UE5: лимит 4 кости, санация имен костей, физика `-col` |
| **09. Боевые Скрипты** | [`09_PRODUCTION_SCRIPTS_AND_TEMPLATES/`](./09_PRODUCTION_SCRIPTS_AND_TEMPLATES/) | Готовые генераторы броневиков, ракетных модулей, риггинга подвески и шагохода Dreadnought |
| **🌟 Дополнение: Органика** | [`EXTENSIONS_HUMANOID_AND_ORGANIC/`](./EXTENSIONS_HUMANOID_AND_ORGANIC/) | *Дополнительный модуль:* Скелет Bip001 (220 костей), разбор лица/глаз/линз, Alpha-Stencil ресниц |

---

## 🚀 Как использовать в новом проекте

1. Скопируй всю папку `ROBO_BLENDER_ACADEMY` в корень твоего нового проекта.
2. Подключи файл `00_AGENT_TUTORIAL_START_HERE.md` в системный промпт твоего ИИ-агента или дай команду:
   ```
   "Изучи документацию в папке ROBO_BLENDER_ACADEMY и создай процедурного робота/технику строго по стандартам Академии."
   ```
3. Для автоматического выполнения скриптов импортируй модуль `02_CORE_GEOMETRY_AND_MATH/geometry_utils.py`.
