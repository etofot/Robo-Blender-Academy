---
name: building_mesh
description: "Процедурная генерация зданий, сооружений и коллизий / Create building mesh, architectural procedural structure, Godot collision shapes. Trigger on requests for building generation, RTS structure mesh, or architectural layout."
depends_on: [core_geometry_rules]
---

# Building Mesh Skill

## Purpose
Generates modular grid-based architecture, procedural wall arrays, and simplified collision shapes for Godot RTS structures.

## Rules

### Rule 1: Modular Grid Alignment
All wall, floor, and roof segments must snap to a strict unit grid (e.g., 1.0m or 2.0m increments) verified via `verify_bounds()`.

### Rule 2: Array Modifiers for Repeating Facades
Use Array modifiers (`ARRAY`) for repeating architectural elements (windows, columns, fence posts) rather than instantiating loose objects.

### Rule 3: Doorway & Window Cutouts
Reuse Boolean cutout patterns (`apply_boolean_cutout`) from `04_robot_mesh` to carve structural openings.

### Rule 4: Simplified Physics Colliders (`-col` Suffix)
Generate low-poly convex hull collision objects with `-col` suffix (e.g., `bunker_wall-col`) for automatic Godot `CollisionShape3D` import.
