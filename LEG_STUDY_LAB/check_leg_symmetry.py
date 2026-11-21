import bpy
from mathutils import Vector

glb_p = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Mech_gameready-220d9957\Mech_gameready.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_p)

# We want to see one single leg (left leg: X < 0, or right leg: X > 0)
# Let's check how the leg objects are mirrored or separated
leg_objs = [o for o in bpy.data.objects if o.type == 'MESH' and 'legs' in o.name.lower()]

print(f"Total leg objects: {len(leg_objs)}")

# Let's separate into Left and Right if possible, or see if each object contains both sides
for o in leg_objs[:15]:
    verts = [o.matrix_world @ v.co for v in o.data.vertices]
    xs = [v.x for v in verts]
    x_min, x_max = min(xs), max(xs)
    print(f"{o.name}: X range [{x_min:.2f}, {x_max:.2f}] (Spans both sides? {x_min < -0.1 and x_max > 0.1})")

