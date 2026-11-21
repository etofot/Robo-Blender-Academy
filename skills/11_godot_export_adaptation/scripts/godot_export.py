"""
Blender glTF 2.0 Export & Godot 4 Asset Pipeline Adaptation.
Source: 222.txt / godot_export_adaptation.
"""
import bpy

def sanitize_bone_names_for_godot(arm_obj):
    for bone in arm_obj.data.bones:
        if "." in bone.name:
            new_name = bone.name.replace(".", "_")
            bone.name = new_name

def export_gltf_for_godot(filepath):
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        export_apply=True,
        export_animations=True,
        export_bake_animation=True,
        export_nla_strips=False,
    )
    return filepath
