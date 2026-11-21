"""
Procedural Mechanical Robot Armature & Constraints.
Source: 111.txt / robot_skeleton.
"""
import bpy

def add_rotation_constraint(child_name, target_name, axis='Z'):
    child = bpy.data.objects[child_name]
    c = child.constraints.new(type='COPY_ROTATION')
    c.target = bpy.data.objects[target_name]
    c.use_x = axis == 'X'
    c.use_y = axis == 'Y'
    c.use_z = axis == 'Z'
    return c

def add_limit_rotation_bone(pose_bone, min_z=-3.14159, max_z=3.14159):
    c = pose_bone.constraints.new('LIMIT_ROTATION')
    c.use_limit_z = True
    c.min_z = min_z
    c.max_z = max_z
    return c

def apply_rigid_weights(mesh_obj, target_group_name):
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    vg = mesh_obj.vertex_groups.get(target_group_name)
    if vg:
        indices = [v.index for v in mesh_obj.data.vertices]
        vg.add(indices, 1.0, 'REPLACE')
    bpy.ops.object.mode_set(mode='OBJECT')
