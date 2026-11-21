import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
os.makedirs(OUT_DIR, exist_ok=True)

ANUBIS_PATH = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Anubis_-_Lowpoly_Animated_Mech-74bc038b\Anubis_-_Lowpoly_Animated_Mech.glb"
KW2_PATH = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\mech_robot_kw-ii.glb"

# ----------------- COMMON STUDIO SETUP -----------------
def setup_studio():
    scn = bpy.context.scene
    world = bpy.data.worlds.new("Study_World")
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.08, 0.10, 0.13, 1.0)
    scn.world = world

    # Key light
    key = bpy.data.lights.new("Study_Key", type='SUN')
    key.energy = 4.8
    key.color = (1.0, 0.98, 0.95)
    ko = bpy.data.objects.new("Study_Key", key)
    ko.rotation_euler = (math.radians(52), math.radians(22), math.radians(65))
    scn.collection.objects.link(ko)

    # Rim light
    rim = bpy.data.lights.new("Study_Rim", type='SUN')
    rim.energy = 3.5
    rim.color = (0.35, 0.75, 1.0)
    ro = bpy.data.objects.new("Study_Rim", rim)
    ro.rotation_euler = (math.radians(-42), math.radians(-28), math.radians(-120))
    scn.collection.objects.link(ro)

    # Camera
    cam_data = bpy.data.cameras.new("Study_Cam")
    cam_obj = bpy.data.objects.new("Study_Cam", cam_data)
    scn.collection.objects.link(cam_obj)
    scn.camera = cam_obj
    
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x = 1200
    scn.render.resolution_y = 1200
    return cam_obj

def make_clay_mat():
    m = bpy.data.materials.new("Mat_Clay")
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs['Base Color'].default_value = (0.76, 0.74, 0.72, 1.0)
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Metallic'].default_value = 0.05
    return m

def add_wireframe_overlay(objs, wire_color=(0.05, 0.55, 0.95, 1.0), thickness=0.035):
    mat_wire = bpy.data.materials.new('Mat_Wire')
    mat_wire.use_nodes = True
    b = mat_wire.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = wire_color
    b.inputs['Emission Color'].default_value = wire_color
    b.inputs['Emission Strength'].default_value = 2.5
    
    for o in objs:
        o.data.materials.append(mat_wire)
        wf = o.modifiers.new('Wire', 'WIREFRAME')
        wf.thickness = thickness
        wf.use_replace = False
        wf.material_offset = len(o.data.materials) - 1

# ================= 1. DISSECT ANUBIS LEG =================
print(">>> DISSECTING ANUBIS LEG...")
bpy.ops.wm.read_factory_settings(use_empty=True)
cam_obj = setup_studio()
bpy.ops.import_scene.gltf(filepath=ANUBIS_PATH)

anubis_leg_names = [
    'right_leg_upper_blinn5_0', 'right_leg_lower_blinn5_0', 'right_leg_foot_blinn5_0',
    'right_toe_front_blinn5_0', 'right_toe_side_out_blinn5_0', 'right_toe_side_in_blinn5_0', 'right_toe_rear_blinn5_0'
]

anubis_leg_objs = [o for o in bpy.context.scene.objects if o.name in anubis_leg_names]
for o in bpy.context.scene.objects:
    if o not in anubis_leg_objs and o.type in ('MESH', 'EMPTY'):
        o.hide_render = True

pts = []
for o in anubis_leg_objs:
    for c in o.bound_box:
        pts.append(o.matrix_world @ Vector(c))

lx_min, lx_max = min(p.x for p in pts), max(p.x for p in pts)
ly_min, ly_max = min(p.y for p in pts), max(p.y for p in pts)
lz_min, lz_max = min(p.z for p in pts), max(p.z for p in pts)
anubis_w, anubis_d, anubis_h = lx_max - lx_min, ly_max - ly_min, lz_max - lz_min
anubis_center = Vector(((lx_min + lx_max)/2.0, (ly_min + ly_max)/2.0, (lz_min + lz_max)/2.0))

print(f"Anubis Leg Size: {anubis_w:.3f}m W x {anubis_d:.3f}m D x {anubis_h:.3f}m H")

# Apply clay
clay_mat = make_clay_mat()
for o in anubis_leg_objs:
    o.data.materials.clear()
    o.data.materials.append(clay_mat)

# 1. Render Clay Side
cam_obj.data.type = 'ORTHO'
cam_obj.data.ortho_scale = anubis_h * 1.30
cam_obj.location = (anubis_center.x + anubis_w * 4.0, anubis_center.y, anubis_center.z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_anubis_clay_side = os.path.join(OUT_DIR, "anubis_leg_1_clay_side.png")
bpy.context.scene.render.filepath = p_anubis_clay_side
bpy.ops.render.render(write_still=True)

# 2. Render Clay 3/4 Perspective
cam_obj.data.type = 'PERSP'
cam_obj.data.lens = 75
cam_obj.location = (anubis_center.x + anubis_w * 2.5, anubis_center.y - anubis_d * 2.8, anubis_center.z + anubis_h * 0.35)
cam_obj.rotation_euler = (anubis_center - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

p_anubis_clay_hero = os.path.join(OUT_DIR, "anubis_leg_2_clay_hero.png")
bpy.context.scene.render.filepath = p_anubis_clay_hero
bpy.ops.render.render(write_still=True)

# 3. Add Wireframe and Render Wire Side
add_wireframe_overlay(anubis_leg_objs, wire_color=(0.05, 0.55, 0.95, 1.0), thickness=0.035)

cam_obj.data.type = 'ORTHO'
cam_obj.data.ortho_scale = anubis_h * 1.30
cam_obj.location = (anubis_center.x + anubis_w * 4.0, anubis_center.y, anubis_center.z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_anubis_wire_side = os.path.join(OUT_DIR, "anubis_leg_3_wire_side.png")
bpy.context.scene.render.filepath = p_anubis_wire_side
bpy.ops.render.render(write_still=True)

blend_anubis = os.path.join(OUT_DIR, "ANUBIS_LEG_STUDY.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_anubis)
print("Saved Anubis Study Blend.")

# ================= 2. DISSECT KW-II HEAVY INDUSTRIAL LEG =================
print(">>> DISSECTING MECH ROBOT KW-II LEG...")
bpy.ops.wm.read_factory_settings(use_empty=True)
cam_obj = setup_studio()
bpy.ops.import_scene.gltf(filepath=KW2_PATH)

dg = bpy.context.evaluated_depsgraph_get()
kw_leg_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data and 'low_legs' in o.data.name]

print(f"KW-II Leg Components: {len(kw_leg_objs)}")

for o in bpy.context.scene.objects:
    if o not in kw_leg_objs and o.type in ('MESH', 'EMPTY', 'ARMATURE'):
        o.hide_render = True

pts_kw = []
for o in kw_leg_objs:
    eval_o = o.evaluated_get(dg)
    for v in eval_o.data.vertices:
        pts_kw.append(eval_o.matrix_world @ v.co)

kx_min, kx_max = min(p.x for p in pts_kw), max(p.x for p in pts_kw)
ky_min, ky_max = min(p.y for p in pts_kw), max(p.y for p in pts_kw)
kz_min, kz_max = min(p.z for p in pts_kw), max(p.z for p in pts_kw)
kw_w, kw_d, kw_h = kx_max - kx_min, ky_max - ky_min, kz_max - kz_min
kw_center = Vector(((kx_min + kx_max)/2.0, (ky_min + ky_max)/2.0, (kz_min + kz_max)/2.0))

print(f"KW-II Leg Size: {kw_w:.3f}m W x {kw_d:.3f}m D x {kw_h:.3f}m H")

# Apply clay
clay_mat_kw = make_clay_mat()
for o in kw_leg_objs:
    o.data.materials.clear()
    o.data.materials.append(clay_mat_kw)

# 1. Render Clay Side
cam_obj.data.type = 'ORTHO'
cam_obj.data.ortho_scale = kw_h * 1.25
cam_obj.location = (kw_center.x + kw_w * 4.0, kw_center.y, kw_center.z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_kw_clay_side = os.path.join(OUT_DIR, "kw2_leg_1_clay_side.png")
bpy.context.scene.render.filepath = p_kw_clay_side
bpy.ops.render.render(write_still=True)

# 2. Render Clay 3/4 Hero
cam_obj.data.type = 'PERSP'
cam_obj.data.lens = 75
cam_obj.location = (kw_center.x + kw_w * 2.6, kw_center.y - kw_d * 2.8, kw_center.z + kw_h * 0.32)
cam_obj.rotation_euler = (kw_center - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

p_kw_clay_hero = os.path.join(OUT_DIR, "kw2_leg_2_clay_hero.png")
bpy.context.scene.render.filepath = p_kw_clay_hero
bpy.ops.render.render(write_still=True)

# 3. Add Wireframe and Render Wire Side
add_wireframe_overlay(kw_leg_objs, wire_color=(0.1, 0.8, 0.3, 1.0), thickness=0.012)

cam_obj.data.type = 'ORTHO'
cam_obj.data.ortho_scale = kw_h * 1.25
cam_obj.location = (kw_center.x + kw_w * 4.0, kw_center.y, kw_center.z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_kw_wire_side = os.path.join(OUT_DIR, "kw2_leg_3_wire_side.png")
bpy.context.scene.render.filepath = p_kw_wire_side
bpy.ops.render.render(write_still=True)

blend_kw = os.path.join(OUT_DIR, "KW2_LEG_STUDY.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_kw)
print("Saved KW-II Study Blend.")

# ================= 3. ASSEMBLE 3-LEG COMPARISON SHEET =================
print(">>> ASSEMBLING 3-LEG COMPARATIVE MATRIX SHEET...")
from PIL import Image, ImageDraw, ImageFont

p_vult_clay = os.path.join(OUT_DIR, "vulture_leg_1_side_profile.png")
p_vult_wire = os.path.join(OUT_DIR, "vulture_leg_wire_side.png")

im_v_clay = Image.open(p_vult_clay).resize((600, 600), Image.Resampling.LANCZOS)
im_v_wire = Image.open(p_vult_wire).resize((600, 600), Image.Resampling.LANCZOS)

im_a_clay = Image.open(p_anubis_clay_side).resize((600, 600), Image.Resampling.LANCZOS)
im_a_wire = Image.open(p_anubis_wire_side).resize((600, 600), Image.Resampling.LANCZOS)

im_k_clay = Image.open(p_kw_clay_side).resize((600, 600), Image.Resampling.LANCZOS)
im_k_wire = Image.open(p_kw_wire_side).resize((600, 600), Image.Resampling.LANCZOS)

# 3 columns x 2 rows (Row 1 = Clay, Row 2 = Wireframe)
master_sheet = Image.new('RGB', (1860, 1360), (12, 16, 22))
draw = ImageDraw.Draw(master_sheet)

try:
    font_main = ImageFont.truetype('arial.ttf', 30)
    font_col = ImageFont.truetype('arial.ttf', 22)
    font_sub = ImageFont.truetype('arial.ttf', 18)
except:
    font_main = ImageFont.load_default()
    font_col = ImageFont.load_default()
    font_sub = ImageFont.load_default()

# Header
draw.text((25, 20), 'TRIO HARD-SURFACE LEG DISSECTION: VULTURE vs ANUBIS vs KW-II', fill=(245, 248, 255), font=font_main)

# Column 1: VULTURE
draw.text((25, 80), 'PARADIGM 1: VULTURE (Avian Aero-Fin)', fill=(255, 205, 75), font=font_col)
draw.text((25, 108), 'Octagonal Boss | Dual Rear Fins | Arched Bridge Foot', fill=(180, 190, 205), font=font_sub)
master_sheet.paste(im_v_clay, (20, 135))
master_sheet.paste(im_v_wire, (20, 745))

# Column 2: ANUBIS
draw.text((645, 80), 'PARADIGM 2: ANUBIS (Heavy 4-Claw Hock)', fill=(80, 215, 255), font=font_col)
draw.text((645, 108), 'Splayed 4-Directional Claws | Armor Overlap | High Hock', fill=(180, 190, 205), font=font_sub)
master_sheet.paste(im_a_clay, (640, 135))
master_sheet.paste(im_a_wire, (640, 745))

# Column 3: KW-II
draw.text((1265, 80), 'PARADIGM 3: KW-II (Military Hydraulic Titan)', fill=(90, 240, 140), font=font_col)
draw.text((1265, 108), 'Double-Acting Pistons | Exposed Cables | Armor Skirts', fill=(180, 190, 205), font=font_sub)
master_sheet.paste(im_k_clay, (1260, 135))
master_sheet.paste(im_k_wire, (1260, 745))

p_master_sheet = os.path.join(OUT_DIR, "trio_legs_comparative_sheet.png")
master_sheet.save(p_master_sheet)
shutil.copyfile(p_master_sheet, os.path.join(ART_DIR, "trio_legs_comparative_sheet.png"))

# Also copy individual clay & wire renders to artifacts
for p in [p_anubis_clay_side, p_anubis_clay_hero, p_anubis_wire_side, p_kw_clay_side, p_kw_clay_hero, p_kw_wire_side]:
    shutil.copyfile(p, os.path.join(ART_DIR, os.path.basename(p)))

print("Master Trio Comparison Sheet successfully saved!")
