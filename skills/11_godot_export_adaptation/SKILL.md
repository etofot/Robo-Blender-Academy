---
name: godot_export_adaptation
description: "Экспорт glTF 2.0 / .glb под Godot 4 / Export glTF 2.0 .glb for Godot engine, prepare physics colliders, sanitize bone names. Trigger on requests to export models for Godot or prepare glTF/GLB assets."
depends_on: [human_animation, robot_animation, building_mesh]
---

# Godot Export Adaptation Skill

## Purpose
Prepares, sanitizes, and exports Blender 3D models, armatures, animations, and collision meshes for Godot 4.

## Rules

### Rule 1: Mandatory Action Bake Before Export
Run NLA action baking (`bpy.ops.nla.bake`) across all animated armatures before exporting glTF files.

### Rule 2: glTF 2.0 Parameter Configuration
Always export using binary `.glb` format with settings:
- `export_apply = True`
- `export_animations = True`
- `export_bake_animation = True`
- `export_nla_strips = False`

### Rule 3: Sanitize Bone Naming
Godot 4 can misinterpret bone names containing multiple period delimiters (e.g. `bone.L.001`). Convert period delimiters to underscores (`bone_L_001`).

### Rule 4: Godot Physics Naming Suffixes
- append `-col` for static collision shapes (`CollisionShape3D`)
- append `-colonly` for collision without visual mesh rendering
- append `-navmesh` for navigation mesh regions

### Rule 5: Verification in Godot Engine
Verify imported `.glb` assets in Godot FileSystem dock to ensure `AnimationPlayer` clips and colliders generate properly.

### Rule 6: Modular glTF 2.0 / FBX Multi-Kit Export Architecture
For modular character customization systems (Godot 4, Unity, Unreal Engine 5):
1. **Shared Rest Skeleton**: All modular parts (Body, Heads, Hair, Tops, Bottoms, Shoes) must be bound to identical rest-pose bone transforms.
2. **Export Modes**:
   - **Monolithic Master glTF**: Single `.glb` containing the armature and all modular collections as separate mesh nodes. In Godot 4 / Unity, toggle individual `MeshInstance3D` / `SkinnedMeshRenderer` node visibility at runtime.
   - **Separate Part glTF**: Export each wardrobe item as an isolated `.glb` containing only the mesh and the skeleton hierarchy with matching skin weights. At runtime in Godot 4, assign the shared skeleton to each part:
     ```gdscript
     part_mesh_instance.skeleton = master_skeleton.get_path()
     ```
3. **Keep Armature Root Selected**: During export, ensure `export_skins = True` and `export_all_influences = False` (clamps bone weights to standard 4 influences per vertex).

### Rule 7: Clean Vertex Weights & Skinning Integrity
Game engines running Vulkan, Direct3D 12, or OpenGL ES 3.0 strictly limit skinning matrices:
1. **Max 4 Influences**: Prune vertex groups with near-zero weights (`< 0.005`) using Blender's `bpy.ops.object.vertex_group_clean(threshold=0.005)`.
2. **Limit Total Influences**: Run `bpy.ops.object.vertex_group_limit_total(limit=4)` to ensure compatibility with Godot 4 and mobile GPUs without shader compiler errors.
3. **Normalize Weights**: Always normalize weights via `bpy.ops.object.vertex_group_normalize_all()` so the sum of bone weights per vertex equals exactly $1.0$.

### Rule 8: Engine-Agnostic Material Architecture
To guarantee flawless cross-engine rendering without missing texture shaders:
1. Use standard glTF 2.0 PBR Metallic/Roughness parameters:
   - `Base Color` (sRGB)
   - `Metallic` (Linear non-color)
   - `Roughness` (Linear non-color)
   - `Normal` (OpenGL tangent-space normal map, inverted green channel for DirectX/Unreal if needed)
2. **Alpha Handling**:
   - Alpha-tested cutouts (hair strands, fringes, lace): Export with `Alpha Mode = MASK`, `Alpha Cutoff = 0.5`.
   - Semi-transparent glass / cornea lenses: Export with `Alpha Mode = BLEND`.
   - Opaque skin and fabrics: Export with `Alpha Mode = OPAQUE`.
