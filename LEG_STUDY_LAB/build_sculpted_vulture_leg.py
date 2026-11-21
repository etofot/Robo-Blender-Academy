import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BLEND_FILE = os.path.join(OUT_DIR, "GENUINE_HARDSURFACE_LEG.blend")

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

col_leg = bpy.data.collections.new('SCULPTED_LEG')
scn.collection.children.link(col_leg)

def link(o):
    col_leg.objects.link(o)
    return o

# PBR & Clay Materials
def make_mat(name, rgb, rough=0.32, metal=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

M_OCHRE_THIGH = make_mat('M_OchreThigh', (0.72, 0.58, 0.22), rough=0.30, metal=0.6)
M_PURPLE_SHIN = make_mat('M_PurpleShin', (0.55, 0.25, 0.65), rough=0.30, metal=0.6)
M_OLIVE_FOOT = make_mat('M_OliveFoot', (0.65, 0.68, 0.35), rough=0.35, metal=0.5)
M_STEEL_PINS = make_mat('M_SteelPins', (0.75, 0.77, 0.80), rough=0.15, metal=0.98)
M_DARK_CHASSIS = make_mat('M_DarkChassis', (0.12, 0.13, 0.15), rough=0.40, metal=0.9)

def hs_finish(o, bevel_w=0.08, seg=2):
    for p in o.data.polygons: p.use_smooth = True
    mod = o.modifiers.new('Bevel', 'BEVEL')
    mod.width = bevel_w
    mod.segments = seg
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(35)
    return o

# =========================================================================
# REAL 2D PROFILES EXTRACTED FROM VULTURE'S ACTUAL GEOMETRY
# =========================================================================

# 1. THIGH CONTOUR (Y, Z in meters) - Massive faceted armor casting!
# True coordinates from Vulture:
pts_thigh_yz = [
    (-6.90, 8.06), (-6.47, 7.61), (-4.72, 6.86), (-3.99, 6.85),
    (-3.29, 6.85), (-2.43, 7.72), (1.37, 11.78), (1.39, 13.42),
    (0.88, 13.96), (-0.44, 14.38), (-1.48, 14.39), (-1.92, 14.39),
    (-4.68, 12.08), (-6.28, 10.59), (-6.49, 10.38), (-6.88, 9.36)
]

# 2. SHIN CONTOUR (Y, Z in meters) - Heavy finned aero-chevron casting!
pts_shin_yz = [
    (-3.71, 1.73), (-3.66, 1.15), (-3.06, -0.26), (-2.49, -0.54),
    (-1.71, -0.54), (-1.14, -0.26), (0.97, 2.80), (1.68, 3.84),
    (2.15, 5.14), (2.25, 5.95), (2.26, 7.27), (1.87, 7.95),
    (1.40, 8.22), (0.68, 8.35), (-1.21, 8.35), (-2.04, 7.48),
    (-3.42, 3.19), (-3.63, 2.53)
]

# 3. FOOT CONTOUR (Y, Z in meters) - Arched bridge base!
pts_foot_yz = [
    (-5.20, -1.46), (-3.20, -1.46), (-2.00, -0.80), (1.00, -0.80),
    (3.50, -1.46), (4.50, -1.46), (4.30, -0.30), (2.00, 0.40),
    (-0.50, 1.05), (-2.50, 1.05), (-4.80, 0.20)
]

# Builder: Extrude 2D polygon symmetrically along X with stepped chamfers
def build_sculpted_volume_from_2d(name, pts_yz, x_center, width, chamfer_inset=0.35, chamfer_w=0.4):
    bm = bmesh.new()
    n = len(pts_yz)
    
    # Outer left/right faces (slightly chamfered/stepped)
    v_left_outer = [bm.verts.new(Vector((x_center - width*0.5, y, z))) for y, z in pts_yz]
    v_right_outer = [bm.verts.new(Vector((x_center + width*0.5, y, z))) for y, z in pts_yz]
    
    # Inner central body
    v_left_mid = [bm.verts.new(Vector((x_center - (width*0.5 - chamfer_w), y, z))) for y, z in pts_yz]
    v_right_mid = [bm.verts.new(Vector((x_center + (width*0.5 - chamfer_w), y, z))) for y, z in pts_yz]
    
    # Perimeter faces connecting outer to mid
    for i in range(n):
        nxt = (i + 1) % n
        bm.faces.new((v_left_outer[i], v_left_outer[nxt], v_left_mid[nxt], v_left_mid[i]))
        bm.faces.new((v_right_mid[i], v_right_mid[nxt], v_right_outer[nxt], v_right_outer[i]))
        bm.faces.new((v_left_mid[i], v_left_mid[nxt], v_right_mid[nxt], v_right_mid[i]))
        
    # Cap side faces
    bm.faces.new(v_left_outer)
    bm.faces.new(reversed(v_right_outer))
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(me); bm.free()
    
    obj = bpy.data.objects.new(name, me)
    link(obj)
    hs_finish(obj, bevel_w=0.06)
    return obj

# ----------------- BUILD GENUINE PARTS -----------------
print("Building Genuine Hard-Surface Thigh from Contour...")
x_leg = 4.33 # World position in Vulture
thigh_w = 4.80 # Massive 4.8m width!
thigh_obj = build_sculpted_volume_from_2d("Genuine_Thigh", pts_thigh_yz, x_leg, thigh_w)
thigh_obj.data.materials.append(M_OCHRE_THIGH)

# Octagonal Hub Boss on the Thigh
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.65, depth=1.2, location=(x_leg + thigh_w*0.5 + 0.5, -0.6, 12.8), rotation=(0, math.radians(90), 0))
hub_outer = bpy.context.object; hub_outer.name = "Thigh_OctagonalHub"; hs_finish(hub_outer, bevel_w=0.08)
hub_outer.data.materials.append(M_OCHRE_THIGH); link(hub_outer)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.10, depth=1.5, location=(x_leg + thigh_w*0.5 + 0.6, -0.6, 12.8), rotation=(0, math.radians(90), 0))
hub_cap = bpy.context.object; hub_cap.name = "Thigh_OctagonalCap"; hs_finish(hub_cap, bevel_w=0.06)
hub_cap.data.materials.append(M_DARK_CHASSIS); link(hub_cap)

print("Building Genuine Hard-Surface Shin from Contour...")
shin_w = 4.20 # Massive 4.2m width!
shin_obj = build_sculpted_volume_from_2d("Genuine_Shin", pts_shin_yz, x_leg, shin_w)
shin_obj.data.materials.append(M_PURPLE_SHIN)

# Heavy Capsule Knee Joint Linkage connecting Thigh to Shin
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_leg + shin_w*0.5 + 0.35, -2.2, 7.4), rotation=(0, 0, math.radians(35)))
knee_link = bpy.context.object; knee_link.scale = (0.70, 3.4, 2.2)
bpy.ops.object.transform_apply(scale=True)
hs_finish(knee_link, bevel_w=0.18, seg=3) # Full pill rounding
knee_link.name = "Knee_PillHinge"; knee_link.data.materials.append(M_PURPLE_SHIN); link(knee_link)

# Knee Steel Pivot Pins
for pz, py in ((8.3, -1.2), (6.5, -3.2)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.65, depth=5.5, location=(x_leg, py, pz), rotation=(0, math.radians(90), 0))
    pin = bpy.context.object; pin.name = f"Knee_Pin_{pz}"; hs_finish(pin, bevel_w=0.04)
    pin.data.materials.append(M_STEEL_PINS); link(pin)

print("Building Genuine Ankle Cuff & Foot Bridge...")
# Ankle Cuff Bracket wrapping shin
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_leg, -2.1, 0.4))
cuff = bpy.context.object; cuff.scale = (4.8, 2.4, 1.8)
bpy.ops.object.transform_apply(scale=True)
hs_finish(cuff, bevel_w=0.12); cuff.name = "Ankle_ClampingCuff"; cuff.data.materials.append(M_OLIVE_FOOT); link(cuff)

# Foot Base from Contour
foot_w = 5.40 # 5.4m wide foot platform!
foot_obj = build_sculpted_volume_from_2d("Genuine_FootBase", pts_foot_yz, x_leg, foot_w)
foot_obj.data.materials.append(M_OLIVE_FOOT)

# Splayed Front Toes (2 heavy curved wedge blocks)
for toe_i, toe_ang in enumerate((-12, 12)):
    tx = x_leg + (1.3 if toe_i==1 else -1.3)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(tx, 2.6, -1.1), rotation=(math.radians(-8), 0, math.radians(toe_ang)))
    toe = bpy.context.object; toe.scale = (1.4, 3.8, 1.1)
    bpy.ops.object.transform_apply(scale=True)
    hs_finish(toe, bevel_w=0.08); toe.name = f"Toe_Claw_{toe_i}"; toe.data.materials.append(M_OLIVE_FOOT); link(toe)
    
    # Side oval pocketing
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(tx, 1.8, -0.6))
    poc = bpy.context.object; poc.scale = (1.5, 1.4, 0.4)
    bpy.ops.object.transform_apply(scale=True)
    hs_finish(poc, bevel_w=0.08, seg=2); poc.name = f"Toe_Pocket_{toe_i}"; poc.data.materials.append(M_DARK_CHASSIS); link(poc)

# ----------------- STUDIO LIGHTING & RENDER -----------------
print("Configuring Studio Render...")
world = bpy.data.worlds.new("Real_World")
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.07, 0.09, 1.0)
scn.world = world

cam_data = bpy.data.cameras.new("Real_Cam")
cam_obj = bpy.data.objects.new("Real_Cam", cam_data)
scn.collection.objects.link(cam_obj)
scn.camera = cam_obj

# Lights
sun_key = bpy.data.lights.new("Sun_Key", type='SUN'); sun_key.energy = 5.0; sun_key.color = (1.0, 0.98, 0.95)
o_k = bpy.data.objects.new("Sun_Key", sun_key); o_k.rotation_euler = (math.radians(52), math.radians(20), math.radians(60))
scn.collection.objects.link(o_k)

sun_rim = bpy.data.lights.new("Sun_Rim", type='SUN'); sun_rim.energy = 3.8; sun_rim.color = (0.35, 0.75, 1.0)
o_r = bpy.data.objects.new("Sun_Rim", sun_rim); o_r.rotation_euler = (math.radians(-40), math.radians(-30), math.radians(-120))
scn.collection.objects.link(o_r)

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1200
scn.render.resolution_y = 1200

center = Vector((x_leg, -2.1, 6.35))

# 1. Side Orthographic Profile
cam_data.type = 'ORTHO'; cam_data.ortho_scale = 18.0
cam_obj.location = (x_leg + 25.0, -2.1, 6.35)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_side = os.path.join(OUT_DIR, "genuine_leg_1_side_profile.png")
scn.render.filepath = p_side; bpy.ops.render.render(write_still=True)

# 2. Hero 3/4 Perspective
cam_data.type = 'PERSP'; cam_data.lens = 70
cam_obj.location = (x_leg + 18.0, -2.1 - 22.0, 6.35 + 6.0)
cam_obj.rotation_euler = (center - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

p_hero = os.path.join(OUT_DIR, "genuine_leg_2_hero_34.png")
scn.render.filepath = p_hero; bpy.ops.render.render(write_still=True)

# Save master blend
bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
print(f"Genuine Leg blend saved: {BLEND_FILE}")

# Copy to artifacts
for p in [p_side, p_hero]:
    shutil.copyfile(p, os.path.join(ART_DIR, os.path.basename(p)))

print("=== SCULPTED LEG BUILD COMPLETED ===")

