import bpy
import bmesh
from mathutils import Vector

blend_path = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB\VULTURE_LEG_DEEP_STUDY.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

leg_names = [
    'polySurface191_aiSS_vulture_0', # Thigh
    'polySurface200_aiSS_vulture_0', # Hip Boss
    'polySurface195_aiSS_vulture_0', # Knee Knuckle
    'polySurface196_aiSS_vulture_0', # Shin
    'polySurface198_aiSS_vulture_0', # Ankle Cuff
]

for name in leg_names:
    o = bpy.data.objects.get(name)
    if not o: continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    # Find islands (connected components)
    visited = set()
    islands = []
    for f in bm.faces:
        if f in visited: continue
        island = []
        stack = [f]
        visited.add(f)
        while stack:
            cf = stack.pop()
            island.append(cf)
            for edge in cf.edges:
                for nf in edge.link_faces:
                    if nf not in visited:
                        visited.add(nf)
                        stack.append(nf)
        islands.append(island)
        
    print(f"\n==========================================")
    print(f"OBJECT: {name}")
    print(f"Total Verts: {len(bm.verts)}, Total Faces: {len(bm.faces)}, Islands: {len(islands)}")
    for idx, isl in enumerate(islands):
        v_co = [v.co for f in isl for v in f.verts]
        min_x, max_x = min(v.x for v in v_co), max(v.x for v in v_co)
        min_y, max_y = min(v.y for v in v_co), max(v.y for v in v_co)
        min_z, max_z = min(v.z for v in v_co), max(v.z for v in v_co)
        print(f"  Island {idx+1}: Faces={len(isl)} | X=({min_x:5.2f}, {max_x:5.2f}) Y=({min_y:5.2f}, {max_y:5.2f}) Z=({min_z:5.2f}, {max_z:5.2f}) | W={max_x-min_x:4.2f} D={max_y-min_y:4.2f} H={max_z-min_z:4.2f}")
    bm.free()

