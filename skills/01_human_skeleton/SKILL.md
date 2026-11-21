---
name: human_skeleton
description: "Процедурная генерация скелета человека и риггинг / Create or generate procedural human skeleton, character rig, Rigify metarig. Trigger when user asks to generate human skeleton, character armature, or character rigging."
depends_on: [core_geometry_rules]
---

# Human Skeleton Skill

## Purpose
Generates human armature hierarchies compatible with automatic skinning, Rigify, and Godot export.

## Rules

### Rule 1: Naming & Hierarchy
Follow Rigify bone naming conventions (`spine`, `spine.001`, `shoulder.L`, `upper_arm.L`, `forearm.L`, `thigh.L`, `shin.L`).
Hierarchy order: `root` -> `spine` -> `limbs`.

### Rule 2: Rigify Generation
Prefer Rigify generation (`bpy.ops.pose.rigify_generate()`) over manually adding 60+ individual edit bones.

### Rule 3: Skinning & Parent Order
Selection order is critical: select mesh object FIRST, select armature LAST (active object), then invoke `bpy.ops.object.parent_set(type='ARMATURE_AUTO')`.

### Rule 4: RTS Scale & Bound Verification
Unit character height target: ~1.8m to 1.85m. Verify bounds using `verify_bounds()` before and after parenting to prevent vertex shifting.

### Rule 5: Universal Bip001 Master Armature Architecture
In modular character systems (such as Aniimo and multi-costume anime productions), a single master armature serves as the universal skeleton for all modular components (heads, bodies, outfits, shoes, and hair):
- **Core Skeletal Hierarchy**:
  - `CharacterRoot` -> `Bip001` -> `Bip001 Pelvis` -> `Bip001 Spine` -> `Spine1` -> `Spine2` -> `Bip001 Neck` -> `Bip001 Head`.
  - Limbs: `Bip001 L/R Clavicle`, `UpperArm`, `Forearm`, `Hand`, with 5 finger chains (Thumb, Index, Middle, Ring, Little; 3 bones each).
  - Legs: `Bip001 L/R Thigh`, `Calf`, `Foot`, `Toe0`, plus twist bones (`LThighTwist`, `LCalfTwist`) and buttock helper bones (`Bone Butt L/R`).
- **Facial Sub-Rig**: `Bn_Head_Center`, `Bn_Nose_Front`, `Bn_Mouth_upper/lower`, `Bn_Mouth_Tongue_01..02`, `Bn_Eye_Eyeball_L/R_Help`.
- **Dynamic Chains**: Hair chains (`Bone Hair Root`, `Bone R/L/C/F Hair...`) and cloth helper bones (skirt ribbons, coat tails). Total bone count: ~220 bones.

### Rule 6: Automated Vertex Weight Transfer (`Nearest Face Interpolated`)
When importing raw polygonal meshes (OBJ) that lack skeletal skinning:
1. Never paint weights manually on hundreds of wardrobe assets.
2. Ensure the base reference body (`Body_Node`) is properly skinned to the master armature.
3. For any clothing, coat, skirt, sock, glove, or footwear mesh:
   - Add a `DATA_TRANSFER` modifier:
     ```python
     dt = obj.modifiers.new(name="WeightTransfer", type='DATA_TRANSFER')
     dt.object = body_obj
     dt.use_vert_data = True
     dt.data_types_verts = {'VGROUP_WEIGHTS'}
     dt.vert_mapping = 'POLYINTERP_NEAREST'
     bpy.context.view_layer.objects.active = obj
     bpy.ops.object.datalayout_transfer(modifier="WeightTransfer")
     bpy.ops.object.modifier_apply(modifier="WeightTransfer")
     ```
   - Add an `ARMATURE` modifier targeting the master armature:
     ```python
     arm_mod = obj.modifiers.new(name="Armature", type='ARMATURE')
     arm_mod.object = master_armature
     ```
4. This interpolates vertex weights from the underlying body skin with 100% boundary conformity, preventing mesh tearing and poke-through during character pose deformations.

### Rule 7: Deformable Skinning vs Rigid Bone Parenting
- **Deformable Apparel**: Shirts, pants, skirts, boots, long hair, and coats bend with body joints. They MUST use `Armature` modifiers with vertex groups.
- **Rigid Accessories**: Hats, glasses, earrings, helmets, hairpins, and backpacks do NOT deform. They should be parented directly to their anchor bone:
  ```python
  obj.parent = master_armature
  obj.parent_type = 'BONE'
  obj.parent_bone = 'Bip001 Head'  # or 'Bip001 Spine2' for backpacks
  ```

### Rule 8: Multi-Engine Armature Compatibility Standards (Godot 4, Unity, Unreal Engine 5)
1. **Single Root Coordinate System**: The armature object MUST have location `(0, 0, 0)`, rotation `(0, 0, 0)`, and scale `(1, 1, 1)` at rest pose. Never leave unapplied object transforms.
2. **Bone Naming Sanitization**: Bone names must strictly use alphanumeric characters, spaces, or underscores (`Bip001_Pelvis` or `Bip001 Pelvis`). Avoid dots (`.`) in bone names when targeting Godot 4 or Unreal Engine to prevent hierarchy splitting.
3. **Rest Pose Alignment**: The default rest pose must be standard T-Pose or A-Pose across all modular mesh pieces to guarantee zero-offset mesh swapping at runtime.
