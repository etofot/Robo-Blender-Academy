"""
Procedural Human Mesh Generation for RTS Units.
Source: 111.txt / human_mesh.
"""
import bpy

HEAD_UNIT = 0.23  # ~23cm for 1.84m tall character (8 head units)

PROPORTIONS = {
    "head": HEAD_UNIT,
    "torso": HEAD_UNIT * 3,
    "leg": HEAD_UNIT * 4,
}

def clean_duplicate_vertices(mesh_obj, threshold=0.001):
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=threshold)
    bpy.ops.object.mode_set(mode='OBJECT')

def generate_smart_uv(mesh_obj, island_margin=0.05):
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=island_margin)
    bpy.ops.object.mode_set(mode='OBJECT')
