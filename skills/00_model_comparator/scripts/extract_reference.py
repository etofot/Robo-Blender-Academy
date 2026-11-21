"""
Extract armature bone hierarchy and object structure from blend file for reference comparison.
Source: 111.txt / model_comparator.
"""
import bpy
import json
import sys

def dump_armature(name):
    arm = bpy.data.objects[name]
    bones = []
    for b in arm.data.bones:
        bones.append({
            "name": b.name,
            "parent": b.parent.name if b.parent else None,
            "head": tuple(b.head_local),
            "tail": tuple(b.tail_local),
            "roll": b.matrix_local.to_euler().z,
        })
    return bones

def extract_reference_data(blend_path):
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    result = {}
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            result[obj.name] = dump_armature(obj.name)
        elif obj.type == 'MESH':
            result[obj.name] = {
                "type": "MESH",
                "parent": obj.parent.name if obj.parent else None,
                "vertex_count": len(obj.data.vertices),
                "polygon_count": len(obj.data.polygons),
                "modifiers": [m.name for m in obj.modifiers]
            }
    return result

if __name__ == "__main__":
    if "--" in sys.argv:
        path = sys.argv[sys.argv.index("--") + 1]
        data = extract_reference_data(path)
        print(json.dumps(data, indent=2))
