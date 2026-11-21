---
name: robot_texture
description: "Текстурирование робота, брони, металл и процедурный износ / Texture robot, mechanical armor, procedural wear, metal PBR. Trigger on requests for robot texturing, metallic armor shaders, or procedural metal wear."
depends_on: [robot_mesh]
---

# Robot Texture Skill

## Purpose
Generates procedural metallic PBR shaders, procedural roughness wear masks, and decal slot layers for robots and vehicles.

## Rules

### Rule 1: Metallic Roughness Workflow
Set `Metallic = 1.0` for bare metal parts and control surface variation using procedural noise maps wired into `Roughness` rather than uniform scalar values.

### Rule 2: Procedural Wear Masks
Generate edge and surface wear using `ShaderNodeTexNoise` and `ShaderNodeValToRGB` color ramps directly in the shader tree.

### Rule 3: Decal Layering via Separate Slot
Assign decals (unit insignia, numbers) to distinct material slots with alpha transparency instead of baking them into base albedo maps, enabling instant team color or unit numbering changes.
