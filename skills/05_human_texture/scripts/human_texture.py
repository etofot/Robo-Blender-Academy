"""
PBR Texturing & Shader Setup for Human Characters.
Source: 222.txt / human_texture.
"""
import bpy

def create_pbr_skin_material(mat_name, albedo_path=None, normal_path=None):
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]

    if albedo_path:
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = bpy.data.images.load(albedo_path)
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    if normal_path:
        norm_img = bpy.data.images.load(normal_path)
        norm_img.colorspace_settings.name = 'Non-Color'
        norm_tex = nodes.new('ShaderNodeTexImage')
        norm_tex.image = norm_img
        norm_map = nodes.new('ShaderNodeNormalMap')
        links.new(norm_tex.outputs['Color'], norm_map.inputs['Color'])
        links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat
