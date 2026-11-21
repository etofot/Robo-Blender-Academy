"""
Procedural Hard-surface Robot Mesh & Armor Generation.
Source: 222.txt / robot_mesh.
"""
import bpy

def apply_hard_surface_bevel(obj, width=0.003, segments=2, angle_limit=0.5236):
    bevel = obj.modifiers.new("Edge_Bevel", 'BEVEL')
    bevel.width = width
    bevel.segments = segments
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = angle_limit
    return bevel

def apply_boolean_cutout(target_obj, cutter_obj, operation='DIFFERENCE'):
    bool_mod = target_obj.modifiers.new("Cutout", 'BOOLEAN')
    bool_mod.operation = operation
    bool_mod.object = cutter_obj
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier="Cutout")
    bpy.data.objects.remove(cutter_obj, do_unlink=True)

def apply_triangulate_for_export(obj):
    tri = obj.modifiers.new("Triangulate_Export", 'TRIANGULATE')
    tri.keep_custom_normals = True
    return tri
