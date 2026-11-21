import bpy, glob, os

corpus = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo"
glbs = glob.glob(os.path.join(corpus, "**", "*.glb"), recursive=True)

print(f"Total GLBs found: {len(glbs)}")

target_models = []

for g in glbs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=g)
        objs = [o for o in bpy.data.objects if o.type == 'MESH']
        # Look for cylinder with high vertex count around 24-48, or objects with specific shapes
        # In Photo 4, there are sunburst gear hubs (lots of small triangular teeth)
        gear_like = 0
        h_like = 0
        curved_chain = 0
        for o in objs:
            name = o.name.lower()
            if any(k in name for k in ['gear', 'spoke', 'cog', 'dente', 'ruota', 'ingranaggio', 'piston', 'pistone', 'joint']):
                gear_like += 1
            # Check topology: sunburst gear hub has a circular face loop with ~24 radial teeth
            v_cnt = len(o.data.vertices)
            f_cnt = len(o.data.polygons)
            # Find if there are many small interconnected components
            if 20 <= v_cnt <= 300 and f_cnt >= 20:
                pass
        print(f"Model: {os.path.basename(g):<40} | Meshes: {len(objs):<4} | Key matches: {gear_like}")
        if gear_like > 0 or len(objs) > 50:
            target_models.append((os.path.basename(g), g, len(objs), gear_like))
    except Exception as e:
        pass

print("\n=== TOP CANDIDATES ===")
for m in sorted(target_models, key=lambda x: (x[3], x[2]), reverse=True):
    print(m)

