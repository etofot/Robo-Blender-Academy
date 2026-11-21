import bpy
import bmesh
from mathutils import Vector

glb_p = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Mech_gameready-220d9957\Mech_gameready.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_p)

# We want only the Right Leg (X > 0)
leg_objs = [o for o in bpy.data.objects if o.type == 'MESH' and 'legs' in o.name.lower()]

# Delete everything else
for o in list(bpy.data.objects):
    if o not in leg_objs:
        bpy.data.objects.remove(o, do_unlink=True)

# In each leg object, split or delete geometry on X < 0 to keep only one single leg
kept_objs = []
for o in leg_objs:
    bm = bmesh.new()
    bm.from_mesh(o.data)
    
    # transform bm to world space to filter by world X
    bm.transform(o.matrix_world)
    
    verts_to_del = [v for v in bm.verts if v.co.x < 0.0]
    bmesh.ops.delete(bm, geom=verts_to_del, context='VERTS')
    
    # if empty, delete object
    if len(bm.verts) == 0:
        bm.free()
        bpy.data.objects.remove(o, do_unlink=True)
        continue
        
    # reset matrix_world to identity and write back
    bm.to_mesh(o.data)
    bm.free()
    o.matrix_world.identity()
    o.data.update()
    kept_objs.append(o)

print(f"Isolated single leg with {len(kept_objs)} distinct parts.")

# Center the single leg around X=0
all_verts = [v.co for o in kept_objs for v in o.data.vertices]
avg_x = (min(v.x for v in all_verts) + max(v.x for v in all_verts)) / 2.0
for o in kept_objs:
    for v in o.data.vertices:
        v.co.x -= avg_x
    o.data.update()

out_blend = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB\REFERENCE_LEG_ISOLATED.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print(f"Saved isolated reference leg to {out_blend}")

