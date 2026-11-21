---
name: robot_mesh
description: "Процедурный меш робота, броня, хард-серфейс / Create robot mesh, mechanical hard-surface armor, mech plating. Trigger on requests for robot mesh generation, mech armor plates, or hard-surface mechanical geometry."
depends_on: [core_geometry_rules]
---

# Robot Mesh Skill

## Purpose
Generates hard-surface mechanical geometry, armor plates, and structural components for robots and RTS vehicles.

## Rules

### Rule 1: Bevel Modifier over Subsurf
Use Bevel modifier with angle limit (`BEVEL`, `angle_limit=30°`) instead of Subdivision Surface (`SUBSURF`) to prevent shrinkage on hard-surface edges.

### Rule 2: Modular Panel Construction
Keep armor plates as separate modular objects (`hull_plate_front`, `hull_plate_side.L`) tested for gap overlaps with `verify_overlap()` before merging.

### Rule 3: Boolean Cutout Cleanup
Always delete temporary cutter objects (`bpy.data.objects.remove(cutter_obj, do_unlink=True)`) immediately after applying Boolean modifiers to keep the scene clean.

### Rule 4: End-of-Pipeline Triangulation
Add Triangulate modifier only right before export, keeping quad topology during modeling operations.
