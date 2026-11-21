"""
Procedural Building Mesh & Array Layout Utilities.
Source: 222.txt / building_mesh.
"""
import bpy

def add_building_array_modifier(wall_obj, count=5, offset_x=1.0):
    arr = wall_obj.modifiers.new("Wall_Array", 'ARRAY')
    arr.count = count
    arr.use_relative_offset = True
    arr.relative_offset_displace[0] = offset_x
    return arr

def create_simplified_collision_box(building_obj, suffix="-col"):
    col_name = building_obj.name + suffix
    mesh = bpy.data.meshes.new(col_name)
    col_obj = bpy.data.objects.new(col_name, mesh)
    bpy.context.collection.objects.link(col_obj)

    matrix_world = building_obj.matrix_world
    bbox = building_obj.bound_box

    import bmesh
    bm = bmesh.new()
    for pt in bbox:
        bm.verts.new(pt)
    bm.verts.ensure_lookup_table()

    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.to_mesh(mesh)
    bm.free()

    col_obj.matrix_world = matrix_world
    return col_obj
