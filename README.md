# 🤖 Robo-Blender-Academy: Procedural 3D Mech, Rigging & IK Studio

Комплексная инженерная база знаний, школа процедурного 3D-моделирования мехов в Blender, библиотека навыков (Agent Skills) для автономных ИИ-агентов и готовая интерактивная 3D-студия **Dreadnought MK-IV TITAN** с физическими анимациями и энергетическим щитом.

---

## 🌟 Главные разделы репозитория

### 1. `dreadnought-3d-ik-studio/` — Интерактивная 3D-студия меха (Three.js / WebGL)
Готовая рабочая 3D-лаборатория (файл `index.html`), работающая прямо в браузере или на GitHub Pages без сборщиков и внешних зависимостей:
* **11 процедурных анимаций:**
  * `shield_wall` — Развертывание многоконтурного полупрозрачного плазменного щита (`opacity = 0.34..0.66`) на предплечье с защитной стойкой фланга.
  * `claw_smash` — Силовой удар боевой клешней с фазами замаха, кинетического хлеста и Hit-Stop.
  * `claw_combo` — Серия ударов и захватов.
  * `walk` & `run` — Локомоция с честным переносом центра тяжести.
  * `railgun` & `missiles` — Стрельба из рельсотрона и выдвижных ракетных шахт с физической отдачей.
  * `jet_jump`, `idle`, `victory`, `dance`.
* **Zero-Drift Foot IK:** Аналитическая инверсная кинематика ног на 2 костях — стопы намертво зафиксированы на плоскости пола и не скользят при приседаниях и выпадах таза.
* **In-Memory PBR CanvasTextures:** Процедурная генерация сварных швов, заклепок, шероховатости, сбитой краски и трафаретов в HTML5 Canvas за 2 мс.
* **3D Экспорт:** Экспорт модели прямо из окна студии в `.GLTF`, `.OBJ`, `.STL`.

### 2. `robo_blender_academy/` — Полный курс создания роботов (Модули 01–09)
Пошаговое руководство для обучения ИИ-агентов и 3D-инженеров:
* **00_AGENT_TUTORIAL_START_HERE.md** — Главный манифест входа для агентов.
* **01_MCP_AND_BLENDER_CONTROL/** — Интеграция Blender через MCP-серверы и live-мосты (`antigravity-blender-mcp`, `blender-live-addon`).
* **02_CORE_GEOMETRY_AND_MATH/** — Математика и правила построения твердотельной геометрии (`geometry_utils.py`).
* **03_ROBOT_HARD_SURFACE_MODELING/** — Хард-сурфейс моделирование, конформная топология, распил бронеплит, кабины и **`MASTERCLASS_MECH_LEG_ENGINEERING.md`** (детальный мастеркласс 4-слойной сборки ноги боевого меха).
* **04_VEHICLE_AND_UNIT_LIBRARY/** — Библиотека шасси, гусениц, шагателей и летательных аппаратов.
* **05_PBR_MATERIALS_AND_SURFACE_WEAR/** — Процедурные PBR металлы, износ граней и тактические декали.
* **06_MECHANICAL_RIGGING_AND_SKELETONS/** — Риггинг суставов, поршней, двуногих мехов и кейс-стади Dreadnought Titan.
* **07_MECHANICAL_ANIMATION/** — Биомеханика анимации тяжелых роботов.
* **08_ENGINE_EXPORT_ADAPTATION/** — Подготовка и экспорт в игровые движки (Unreal Engine, Unity, Three.js).
* **09_PRODUCTION_SCRIPTS_AND_TEMPLATES/** — Эталонные скрипты и документация `dreadnought_agent_skill_guide.md`.
* **EXTENSIONS_HUMANOID_AND_ORGANIC/** — Расширения для биомеханических и гуманоидных моделей.

### 3. `LEG_STUDY_LAB/` — Эталонная Hard-Surface Нога Меха (3D Сборка, 50 шагов)
Полная лаборатория реверса и процедурного воссоздания эталонной ноги:
* **Универсальные 3D Модели для Облачных Агентов (`.glb` / `.blend`):**
  * **`REFERENCE_LEG_ISOLATED.glb`** — Оригинальная нога-образец со скриншота в формате glTF/GLB (53 детали, PBR).
  * **`REFERENCE_LEG_ISOLATED.blend`** & **`LEG_REFERENCE_OK.blend`** — Сцены для Blender.
  * **`MASTER_LEG_50_STEPS_COMPLETE.glb`** & **`.blend`** — Полная 50-шаговая мастер-сборка.
  * Фазовые сборки: `PHASE1_TO_6_EXECUTION.blend`, `PHASE1_TO_5_EXECUTION.blend`, `PHASE1_AND_PHASE2_EXECUTION.blend`.
* **Скрипты сборки по фазам (`execute_phase*.py`):**
  * `execute_phase1_steps.py` — Блокаут кинематических осей и габаритов.
  * `execute_phase3_hydraulics.py` — Гидроцилиндры и зеркальные штоки.
  * `execute_phase4_subsystems.py` — Теплообменные бачки и щелевые радиаторы.
  * `execute_phase5_armor.py` — Накладные фацетированные бронеплиты.
  * `execute_phase6_foot.py` & `execute_phase7_final_assembly.py` — 4-палая карданная стопа и финальная сборка.
* **Визуальные контактные листы, чертежи и рендеры:**
  * `user_viewport_reference.jpg` — Исходный скриншот из Blender Viewport.
  * `real_reference_perspective.png` — Студийный ракурс 3/4 модели-образца.
  * `step50_master_leg_side_ortho.png` — Боковой ортографический чертеж с осями вращения.
  * `step50_master_leg_wireframe.png` — Полигональная сетка топологии (Wireframe).
  * Поэтапные аудиты `phase1_audit_contact_sheet.png` ... `phase6_audit_contact_sheet.png`.

### 3. `skills/` — Библиотека навыков для ИИ-Агентов (Agent Skills)
Стандартизированные файлы `SKILL.md`, готовые к подключению к автономным агентам:
* **`procedural-3d-mech-animator/`** — Скилл создания процедурных 3D-мехов, разверток и IK-анимаций.
* **`SKILLS_HARDSURFACE_COMPONENTS/`** — Правила сборки хард-сурфейс узлов.
* **`skills_blocks_1_to_4/`** — Пошаговые руководства по блокам моделирования, детализации кабелей, жесткого скининга (Rigid Weighting) и QA-проверкам.
* **`16_halo_xl_cocoon_lens/`**, **`POPfilter_v1/`** — Процедурные акустические линзы и коконы.

### 4. `scripts/` — Рабочие Python-скрипты для Blender
* `build_titan_falcon_v2.py` — Процедурный генератор двуногого шагателя Falcon Titan v2.
* `upgrade_carapace_panel.py` — Скрипт апгрейда бронеплит с фасками и зазорами.
* `mech_architectural_scanner.py` — Инструмент проверки геометрии и иерархии костей.
* `apply_cyber_biomech_materials.py` — Процедурные материалы кибер-биомеханики.

### 5. `blender_addons/` — Инструменты и аддоны
Набор проверенных процедурных аддонов для Blender:
* **BY-GEN** — Генератор процедурных структур и органических поверхностей.
* **CurveBasher** — Прокладка кабелей, шлангов и трасс между шарнирами.
* **Node Arrange** — Автоматическая раскладка шейдерных и геометрических нод.
* **Random Flow** — Процедурная рандомизация деталей и панелей.
* **3D-Motion with Claude Code and Blender** — Руководства и пайплайны анимации через агентов.

---

## 🚀 Быстрый старт

### Открытие 3D-студии Dreadnought MK-IV:
Просто откройте файл `dreadnought-3d-ik-studio/index.html` в любом современном браузере. Либо включите GitHub Pages в настройках репозитория.

### Для подключения к новому ИИ-агенту:
Передайте агенту файл:
`robo_blender_academy/00_AGENT_TUTORIAL_START_HERE.md`
или скилл:
`skills/procedural-3d-mech-animator/SKILL.md`

Агент сможет изучить архитектуру шарниров, компенсацию пивотов, расчет инверсной кинематики и самостоятельно проектировать новых мехов следующего поколения.
