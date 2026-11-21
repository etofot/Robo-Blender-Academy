"""
Procedural Character Keyframe Animation & Action Baking.
Source: 222.txt / human_animation.
"""
import bpy

def keyframe_pose_bone_rotation(arm_obj, bone_name, frame, rotation_euler):
    pbone = arm_obj.pose.bones[bone_name]
    pbone.rotation_mode = 'XYZ'
    pbone.rotation_euler = rotation_euler
    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)

def bake_action_for_export(frame_start=1, frame_end=60):
    bpy.ops.nla.bake(
        frame_start=frame_start,
        frame_end=frame_end,
        only_selected=False,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )
