import bpy, glob, os
from mathutils import Vector

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
CORPUS = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo"

candidates = [
    "MECH_-_High_Poly",
    "Mech_gameready",
    "Mech_Soldier",
    "Peacekeeper_Mech",
    "PINK_MECH",
    "RONIN_Mech",
    "mech_robot_kw-ii",
    "ar-22_armadillo_heavy_battle_mech"
]

for c in candidates:
    matches = glob.glob(os.path.join(CORPUS, "**", f"*{c}*.glb"), recursive=True)
    if not matches:
        matches = glob.glob(os.path.join(CORPUS, f"*{c}*.glb"))
    if not matches: continue
    glb_p = matches[0]
    
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    try:
        bpy.ops.import_scene.gltf(filepath=glb_p)
    except Exception as e:
        continue
        
    mesh_objs = [o for o in scn.objects if o.type == 'MESH']
    if not mesh_objs: continue
    
    pts = [o.matrix_world @ Vector(co) for o in mesh_objs for co in o.bound_box]
    min_x, max_x = min(p.x for p in pts), max(p.x for p in pts)
    min_y, max_y = min(p.y for p in pts), max(p.y for p in pts)
    min_z, max_z = min(p.z for p in pts), max(p.z for p in pts)
    
    total_h = max_z - min_z
    center = Vector(((min_x+max_x)/2, (min_y+max_y)/2, (min_z+max_z)/2))
    
    # Setup camera for side orthographic
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = total_h * 1.1
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    cam_o.location = (center.x + (max_x - min_x) * 4.0 + 10.0, center.y, center.z)
    cam_o.rotation_euler = (1.5708, 0, 1.5708)
    
    # Sun light
    sun = bpy.data.lights.new("Sun", 'SUN')
    sun.energy = 4.0
    sun_o = bpy.data.objects.new("Sun", sun)
    sun_o.rotation_euler = (0.8, 0.4, 0.9)
    scn.collection.objects.link(sun_o)
    
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x = 600
    scn.render.resolution_y = 600
    
    out_img = os.path.join(OUT_DIR, f"candidate_{c}.png")
    scn.render.filepath = out_img
    bpy.ops.render.render(write_still=True)
    print(f"Rendered candidate: {c} -> {out_img}")

