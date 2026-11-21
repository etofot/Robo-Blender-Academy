import bpy
import bmesh
import math
import os
import glob
from mathutils import Vector

# Setup paths
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ARTIFACT_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
os.makedirs(OUT_DIR, exist_ok=True)

CORPUS_ROOT = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo"
VULTURE_PATH = glob.glob(os.path.join(CORPUS_ROOT, "*Vulture*", "*Vulture*.glb"))[0]

# 1. Reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

# 2. Import Vulture
bpy.ops.import_scene.gltf(filepath=VULTURE_PATH)

# Identify leg objects on the right side (or left)
# In Vulture: let's inspect all mesh objects and their heights/names
leg_objs = []
all_mesh_objs = [o for o in scn.objects if o.type == 'MESH']

# Calculate global bounding box
world_pts = []
for o in all_mesh_objs:
    for c in o.bound_box:
        world_pts.append(o.matrix_world @ Vector(c))

min_z = min(p.z for p in world_pts)
max_z = max(p.z for p in world_pts)
total_h = max_z - min_z

print(f"Vulture imported. Total height: {total_h:.2f}m")

# Select only objects below 62% height that belong to the leg
for o in all_mesh_objs:
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    z_mid = sum(p.z for p in pts) / len(pts)
    x_mid = sum(p.x for p in pts) / len(pts)
    # Right leg (X > 0)
    if z_mid < (min_z + total_h * 0.65) and x_mid > 0.5:
        leg_objs.append(o)

print(f"Identified {len(leg_objs)} leg components for Right Leg:")
for o in leg_objs:
    print(f" - {o.name} | Polys: {len(o.data.polygons)} | Verts: {len(o.data.vertices)}")

# Hide all non-leg objects
for o in all_mesh_objs:
    if o not in leg_objs:
        o.hide_render = True
        o.hide_viewport = True

# Focus target on leg center
leg_pts = []
for o in leg_objs:
    for c in o.bound_box:
        leg_pts.append(o.matrix_world @ Vector(c))

lx_min, lx_max = min(p.x for p in leg_pts), max(p.x for p in leg_pts)
ly_min, ly_max = min(p.y for p in leg_pts), max(p.y for p in leg_pts)
lz_min, lz_max = min(p.z for p in leg_pts), max(p.z for p in leg_pts)

leg_w = lx_max - lx_min
leg_d = ly_max - ly_min
leg_h = lz_max - lz_min
leg_center = Vector(((lx_min + lx_max)/2.0, (ly_min + ly_max)/2.0, (lz_min + lz_max)/2.0))

print(f"Leg Dimensions: {leg_w:.3f}m W x {leg_d:.3f}m D x {leg_h:.3f}m H")
print(f"Leg Center: {leg_center}")

# 3. Create High-Contrast Industrial Clay / Topology Materials
# Mat A: Pure Industrial Clay (Warm gray with soft sheen for bevel inspection)
mat_clay = bpy.data.materials.new("Mat_Clay_Inspector")
mat_clay.use_nodes = True
b_clay = mat_clay.node_tree.nodes.get("Principled BSDF")
b_clay.inputs['Base Color'].default_value = (0.75, 0.73, 0.70, 1.0)
b_clay.inputs['Roughness'].default_value = 0.38
b_clay.inputs['Metallic'].default_value = 0.05

# Apply clay material
for o in leg_objs:
    o.data.materials.clear()
    o.data.materials.append(mat_clay)

# Setup Camera
cam_data = bpy.data.cameras.new("Leg_Study_Cam")
cam_obj = bpy.data.objects.new("Leg_Study_Cam", cam_data)
scn.collection.objects.link(cam_obj)
scn.camera = cam_obj

# Studio Lights
world = bpy.data.worlds.new("Leg_World")
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.10, 0.12, 0.15, 1.0)
scn.world = world

key_l = bpy.data.lights.new("Leg_Key", type='SUN')
key_l.energy = 4.5
key_l.color = (1.0, 0.98, 0.95)
key_o = bpy.data.objects.new("Leg_Key", key_l)
key_o.rotation_euler = (math.radians(50), math.radians(25), math.radians(65))
scn.collection.objects.link(key_o)

rim_l = bpy.data.lights.new("Leg_Rim", type='SUN')
rim_l.energy = 3.2
rim_l.color = (0.4, 0.7, 1.0)
rim_o = bpy.data.objects.new("Leg_Rim", rim_l)
rim_o.rotation_euler = (math.radians(-45), math.radians(-30), math.radians(-115))
scn.collection.objects.link(rim_o)

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1600
scn.render.resolution_y = 1200

# Diagnostic Views of the Isolated Leg
views = [
    ("vulture_leg_1_side_profile.png", (leg_center.x + leg_w * 4.0, leg_center.y, leg_center.z), (math.radians(90), 0, math.radians(90)), True, leg_h * 1.25),
    ("vulture_leg_2_front_view.png", (leg_center.x, leg_center.y - leg_d * 4.0, leg_center.z), (math.radians(90), 0, 0), True, leg_h * 1.25),
    ("vulture_leg_3_rear_view.png", (leg_center.x, leg_center.y + leg_d * 4.0, leg_center.z), (math.radians(90), 0, math.radians(180)), True, leg_h * 1.25),
    ("vulture_leg_4_hero_34.png", (leg_center.x + leg_w * 2.5, leg_center.y - leg_d * 2.8, leg_center.z + leg_h * 0.4), (0,0,0), False, 0),
    ("vulture_leg_5_knee_closeup.png", (leg_center.x + leg_w * 1.8, leg_center.y - leg_d * 1.2, leg_center.z + leg_h * 0.15), (0,0,0), False, 0),
    ("vulture_leg_6_foot_closeup.png", (leg_center.x + leg_w * 1.6, leg_center.y - leg_d * 1.5, lz_min + leg_h * 0.12), (0,0,0), False, 0)
]

rendered_paths = []
for fname, cloc, crot, is_ortho, oscale in views:
    cam_obj.location = cloc
    if is_ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = oscale
        cam_obj.rotation_euler = crot
    else:
        cam_data.type = 'PERSP'
        cam_data.lens = 75
        d_vec = leg_center - cam_obj.location
        if "foot" in fname:
            d_vec = Vector((leg_center.x, leg_center.y, lz_min + 0.15 * leg_h)) - cam_obj.location
        elif "knee" in fname:
            d_vec = Vector((leg_center.x, leg_center.y, leg_center.z + 0.1 * leg_h)) - cam_obj.location
        cam_obj.rotation_euler = d_vec.to_track_quat('-Z', 'Y').to_euler()
        
    out_p = os.path.join(OUT_DIR, fname)
    scn.render.filepath = out_p
    bpy.ops.render.render(write_still=True)
    rendered_paths.append(out_p)
    print(f"Rendered: {fname}")

# Save isolated study blend file
study_blend = os.path.join(OUT_DIR, "VULTURE_LEG_DEEP_STUDY.blend")
bpy.ops.wm.save_as_mainfile(filepath=study_blend)
print(f"Saved: {study_blend}")

# Copy to artifacts
import shutil
for p in rendered_paths:
    if os.path.exists(p):
        bn = os.path.basename(p)
        shutil.copyfile(p, os.path.join(ARTIFACT_DIR, bn))
        print(f"Copied to artifact: {bn}")

