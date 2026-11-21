---
name: model_comparator
description: "Извлечение и сравнение паттернов из эталонных .blend файлов / Extract and compare patterns from reference .blend files. Trigger on user requests to analyze reference models, extract bone hierarchies, or update skills from reference files."
---

# Model Comparator Skill

## Purpose
Extracts structural patterns (bone hierarchy, constraints, modifier stacks, mesh polygon counts) from reference `.blend` files and updates target procedural skills with verified patterns.

## Workflow
1. Execute headless extraction script:
   `blender --background --python scripts/extract_reference.py -- <path_to_blend>`
2. Compare output JSON against current skill templates.
3. Identify bone names, parent relationships, constraints, or modifier settings.
4. Record findings and update target skill rules.
5. Log changes to `_LEARNING_LOG.md`.

## Execution Rule
Do not execute if no new reference `.blend` files are supplied to save execution cycles.
