"""
Procedural Metallic & Wear Texturing for Mechanical Robots.
Source: 222.txt / robot_texture.
"""
import bpy

def create_procedural_metal_wear_material(mat_name, base_color=(0.1, 0.1, 0.12, 1.0), scale=15.0):
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]

    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Metallic'].default_value = 1.0

    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    ramp = nodes.new('ShaderNodeValToRGB')

    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Roughness'])

    return mat
