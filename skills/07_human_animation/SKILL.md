---
name: human_animation
description: "Анимация человека, ходьба, жесты, bake NLA action / Animate character, walk cycle, gestures, keyframe pose bones. Trigger on requests for character animation, human keyframing, or baking actions for export."
depends_on: [human_skeleton]
---

# Human Animation Skill

## Purpose
Governs organic character keyframing, pose bone manipulation, IK/FK workflows, and NLA action baking.

## Rules

### Rule 1: Manipulate Pose Bones
Set rotation and keyframes on `arm_obj.pose.bones["bone_name"]`, never edit bones (`data.edit_bones`), during animation scripting.

### Rule 2: IK / FK Workflows
Utilize Rigify IK targets for locomotion (feet contact, hands) and FK mode for fluid organic gestures.

### Rule 3: Mandatory Action Baking
Always execute `bpy.ops.nla.bake(visual_keying=True, clear_constraints=True, bake_types={'POSE'})` before glTF export; unbaked IK solvers will not evaluate in Godot.
