"""
Mechanical & Turret Rotation Animation Utilities.
Source: 222.txt / robot_animation.
"""
import bpy

def animate_turret_rotation(pivot_obj, start_frame=1, end_frame=120, rotation_z=6.283185):
    pivot_obj.rotation_euler = (0, 0, 0)
    pivot_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=start_frame)
    pivot_obj.rotation_euler = (0, 0, rotation_z)
    pivot_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=end_frame)

    if pivot_obj.animation_data and pivot_obj.animation_data.action:
        for fc in pivot_obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

def add_cyclic_modifier_to_action(action):
    for fc in action.fcurves:
        fc.modifiers.new('CYCLES')
