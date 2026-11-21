---
name: normal_depth_maps
description: "Запекание карт нормалей и глубины / Bake normal maps, depth maps, high-poly to low-poly baking. Trigger on requests to bake normal maps, transfer high-poly detail, or create depth textures."
depends_on: [core_geometry_rules]
---

# Normal & Depth Maps Skill

## Purpose
Manages Cycles texture baking from high-poly detail models to low-poly RTS meshes.

## Rules

### Rule 1: Scene Selection State
Both High-Poly and Low-Poly models must exist in the scene during baking. Selection order: High-Poly selected first, Low-Poly selected second (active object).

### Rule 2: Active Node Selection
An active `ShaderNodeTexImage` node targeting a `Non-Color` image buffer must be selected in the Low-Poly material node tree before triggering `bpy.ops.object.bake()`.

### Rule 3: Cage Extrusion Offsets
Use `cage_extrusion = 0.01..0.03m` to eliminate ray-miss baking artifacts along sharp edges.

### Rule 4: Non-Color Space Export
Target images must strictly remain in `Non-Color` color space so Godot interprets normal vectors correctly upon import.
