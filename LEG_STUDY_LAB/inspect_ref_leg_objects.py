import bpy
from mathutils import Vector

glb_p = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Mech_gameready-220d9957\Mech_gameready.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_p)

leg_objs = [o for o in bpy.data.objects if o.type == 'MESH' and 'legs' in o.name.lower()]
print(f"TOTAL LEG OBJECTS: {len(leg_objs)}")
for o in leg_objs:
    mw = o.matrix_world
    bbox = [mw @ Vector(c) for c in o.bound_box]
    z_min = min(p.z for p in bbox)
    z_max = max(p.z for p in bbox)
    y_min = min(p.y for p in bbox)
    y_max = max(p.y for p in bbox)
    x_min = min(p.x for p in bbox)
    x_max = max(p.x for p in bbox)
    print(f"OBJ: {o.name:<30} | verts={len(o.data.vertices):<5} | faces={len(o.data.polygons):<5} | X:[{x_min:+.2f}, {x_max:+.2f}] Y:[{y_min:+.2f}, {y_max:+.2f}] Z:[{z_min:+.2f}, {z_max:+.2f}]")

