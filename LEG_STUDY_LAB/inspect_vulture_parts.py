import bpy
from mathutils import Vector

gltf_path = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Vulture_-_Lowpoly_Animated_Mech-71178c77\Vulture_-_Lowpoly_Animated_Mech.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=gltf_path)

print("--- IMPORTED OBJECTS IN VULTURE ---")
leg_objs = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        min_x = min(c.x for c in bb); max_x = max(c.x for c in bb)
        min_y = min(c.y for c in bb); max_y = max(c.y for c in bb)
        min_z = min(c.z for c in bb); max_z = max(c.z for c in bb)
        # Check if it belongs to right or left leg (x > 1 or x < -1, and z < 15)
        print(f"OBJ: {o.name:<20} | V={len(o.data.vertices):<5} F={len(o.data.polygons):<5} | X=({min_x:5.2f}, {max_x:5.2f}) Y=({min_y:5.2f}, {max_y:5.2f}) Z=({min_z:5.2f}, {max_z:5.2f})")

