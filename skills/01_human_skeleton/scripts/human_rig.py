"""
Procedural Human Skeleton & Rigify Generation.
Source: 111.txt / human_skeleton.
"""
import bpy

def make_bone(arm_obj, name, head, tail, parent=None):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_obj.data.edit_bones
    bone = eb.new(name)
    bone.head, bone.tail = head, tail
    if parent and parent in eb:
        bone.parent = eb[parent]
        bone.use_connect = True
    bpy.ops.object.mode_set(mode='OBJECT')
    return bone.name

def generate_human_metarig():
    bpy.ops.object.armature_human_metarig_add()
    metarig = bpy.context.active_object
    metarig.name = "Human_MetaRig"
    return metarig

def generate_rigify_rig(metarig_obj):
    bpy.context.view_layer.objects.active = metarig_obj
    bpy.ops.pose.rigify_generate()
    rig = bpy.context.active_object
    return rig

def bind_mesh_to_armature(mesh_obj, arm_obj):
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
