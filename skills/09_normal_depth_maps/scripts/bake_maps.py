"""
Cycles Normal & Depth Map Baking Utilities.
Source: 222.txt / normal_depth_maps.
"""
import bpy

def bake_normal_map_selected_to_active(high_poly_obj, low_poly_obj, output_filepath, resolution=2048, cage_extrusion=0.02):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'NORMAL'

    img = bpy.data.images.new("NormalMap_Temp", resolution, resolution, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'

    mat = low_poly_obj.active_material
    if not mat:
        mat = bpy.data.materials.new("Bake_Mat")
        low_poly_obj.data.materials.append(mat)
    mat.use_nodes = True

    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = img
    mat.node_tree.nodes.active = node

    bpy.ops.object.select_all(action='DESELECT')
    high_poly_obj.select_set(True)
    low_poly_obj.select_set(True)
    bpy.context.view_layer.objects.active = low_poly_obj

    bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, cage_extrusion=cage_extrusion)
    img.filepath_raw = output_filepath
    img.file_format = 'PNG'
    img.save()
    return output_filepath
