import bpy

print("="*60)
print("DEEP INSPECTION OF MASTER_LEG_50_STEPS_COMPLETE.blend")
print("="*60)

for o in bpy.data.objects:
    if o.type == 'MESH':
        n_verts = len(o.data.vertices)
        n_faces = len(o.data.polygons)
        colls = [c.name for c in o.users_collection]
        print(f"[{o.name}] | Type: {o.type} | Verts: {n_verts} | Faces: {n_faces} | Loc: {tuple(round(v, 2) for v in o.location)} | HideV: {o.hide_get()} | HideR: {o.hide_render} | Colls: {colls}")

