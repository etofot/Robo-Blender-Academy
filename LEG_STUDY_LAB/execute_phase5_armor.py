import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BASE_BLEND = os.path.join(OUT_DIR, "PHASE1_2_3_4_EXECUTION.blend")

bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
scn = bpy.context.scene

# Materials
M_CYAN_HYDRO = bpy.data.materials.get("L2_Hydro_Cyan")
M_ARMOR_OLIV = bpy.data.materials.get("L4_Armor_Olive")
M_DARK_STEEL = bpy.data.materials.get("M_DarkSteel")
M_CHROME     = bpy.data.materials.get("M_ChromeRod")

# High-Grade Armor Coating (Ochre Gold Ceramic)
M_ARMOR_OCHRE = bpy.data.materials.new("M_ArmorOchreCeramic")
M_ARMOR_OCHRE.use_nodes = True
b_oc = M_ARMOR_OCHRE.node_tree.nodes.get("Principled BSDF")
b_oc.inputs['Base Color'].default_value = (0.78, 0.64, 0.30, 1.0)
b_oc.inputs['Metallic'].default_value = 0.40
b_oc.inputs['Roughness'].default_value = 0.32

# Secondary Dark Armor Plating (Gunmetal Grey)
M_ARMOR_DARK = bpy.data.materials.new("M_ArmorDarkPlate")
M_ARMOR_DARK.use_nodes = True
b_ad = M_ARMOR_DARK.node_tree.nodes.get("Principled BSDF")
b_ad.inputs['Base Color'].default_value = (0.16, 0.18, 0.22, 1.0)
b_ad.inputs['Metallic'].default_value = 0.85
b_ad.inputs['Roughness'].default_value = 0.25

phase5_col = bpy.data.collections.new("Phase5_Armor_Shells")
scn.collection.children.link(phase5_col)

def finish_armor(obj, bevel_w=0.015, seg=2):
    for p in obj.data.polygons: p.use_smooth = True
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = bevel_w; mod.segments = seg
    mod.limit_method = 'ANGLE'; mod.angle_limit = math.radians(35)
    return obj

# =========================================================================
# STEP 33 & 34: MAIN THIGH ARMOR HULL & H-BLOCK CUTOUT WINGS
# Forward wedge beak, 45-deg prow, and flank cutout exposing the H-block
# Location: Z from 2.10 to 3.45, Y from -0.35 to 0.95
# =========================================================================
print("\n>>> EXECUTING STEPS 33-34: Thigh Armor Hull with H-Block Cutout...")

bm_thigh = bmesh.new()

# Multi-station faceted shell surrounding the thigh frame
# Stations along Z:
# Z=3.35 (top deck), Z=2.95 (cantilever beak), Z=2.55 (mid thigh), Z=2.15 (lower cradle)
w_thigh = 0.82

thigh_pts_335 = [
    ( w_thigh*0.5,  0.75, 3.35), # Rear right
    ( w_thigh*0.5, -0.15, 3.35), # Front right
    ( 0.00,        -0.32, 3.35), # Center prow
    (-w_thigh*0.5, -0.15, 3.35), # Front left
    (-w_thigh*0.5,  0.75, 3.35)  # Rear left
]

thigh_pts_295 = [
    ( w_thigh*0.58,  0.88, 2.95), # Rear right
    ( w_thigh*0.58, -0.38, 2.95), # Forward beak right
    ( 0.00,         -0.62, 2.95), # Sharp cantilever beak tip!
    (-w_thigh*0.58, -0.38, 2.95), # Forward beak left
    (-w_thigh*0.58,  0.88, 2.95)  # Rear left
]

thigh_pts_255 = [
    ( w_thigh*0.54,  0.65, 2.55), # Rear right (cutout zone starts here)
    ( w_thigh*0.54, -0.22, 2.55), # Mid front right
    ( 0.00,         -0.45, 2.55), # Center prow
    (-w_thigh*0.54, -0.22, 2.55), # Mid front left
    (-w_thigh*0.54,  0.65, 2.55)  # Rear left
]

thigh_pts_215 = [
    ( w_thigh*0.42,  0.35, 2.15), # Lower rear right
    ( w_thigh*0.42, -0.05, 2.15), # Lower front right
    ( 0.00,         -0.18, 2.15), # Lower prow tip
    (-w_thigh*0.42, -0.05, 2.15), # Lower front left
    (-w_thigh*0.42,  0.35, 2.15)  # Lower rear left
]

station_rings = []
for st in [thigh_pts_335, thigh_pts_295, thigh_pts_255, thigh_pts_215]:
    ring = [bm_thigh.verts.new(Vector(p)) for p in st]
    station_rings.append(ring)

# Loft between stations
for s in range(len(station_rings) - 1):
    r1 = station_rings[s]
    r2 = station_rings[s + 1]
    for i in range(len(r1) - 1):
        bm_thigh.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))

# Cap rear faces to close volume
for s in range(len(station_rings) - 1):
    r1 = station_rings[s]
    r2 = station_rings[s + 1]
    bm_thigh.faces.new((r1[4], r1[0], r2[0], r2[4]))

bmesh.ops.recalc_face_normals(bm_thigh, faces=bm_thigh.faces)
me_thigh = bpy.data.meshes.new("Thigh_Armor_Hull_Mesh")
bm_thigh.to_mesh(me_thigh); bm_thigh.free()

thigh_armor_obj = bpy.data.objects.new("Thigh_Armor_Hull", me_thigh)
phase5_col.objects.link(thigh_armor_obj)
thigh_armor_obj.data.materials.append(M_ARMOR_OCHRE)
finish_armor(thigh_armor_obj, bevel_w=0.018)

# Add Flank Cutout Border Rim for H-block
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.49, 0.28, 2.68))
rim = bpy.context.object; rim.name = "H_Block_Armor_Bezel"
rim.scale = (0.04, 0.34, 0.46); bpy.ops.object.transform_apply(scale=True)
rim.rotation_euler = (math.radians(24), 0, 0)
rim.data.materials.append(M_ARMOR_DARK)
phase5_col.objects.link(rim); scn.collection.objects.unlink(rim)
finish_armor(rim, bevel_w=0.008)

# =========================================================================
# STEP 35: KNEE FLOATING ARMOR COWLING (Knee Armor Shield)
# Bridges the knee gap and covers the hydraulic rod from direct fire
# Location: (X=0.0, Y=-0.22, Z=1.95)
# =========================================================================
print("\n>>> EXECUTING STEP 35: Floating Knee Armor Cowling...")

bm_knee_c = bmesh.new()
# Faceted chevron shield in bmesh
kw = 0.58; kd = 0.24; kh = 0.44

v_k1 = bm_knee_c.verts.new(Vector((-kw*0.5,  kd*0.5, -kh*0.5)))
v_k2 = bm_knee_c.verts.new(Vector(( kw*0.5,  kd*0.5, -kh*0.5)))
v_k3 = bm_knee_c.verts.new(Vector(( kw*0.35, -kd*0.5, -kh*0.5)))
v_k4 = bm_knee_c.verts.new(Vector(( 0.00,    -kd*0.8, -kh*0.3))) # Prow tip bottom
v_k5 = bm_knee_c.verts.new(Vector((-kw*0.35, -kd*0.5, -kh*0.5)))

v_k6 = bm_knee_c.verts.new(Vector((-kw*0.45,  kd*0.4,  kh*0.5)))
v_k7 = bm_knee_c.verts.new(Vector(( kw*0.45,  kd*0.4,  kh*0.5)))
v_k8 = bm_knee_c.verts.new(Vector(( kw*0.30, -kd*0.4,  kh*0.5)))
v_k9 = bm_knee_c.verts.new(Vector(( 0.00,    -kd*0.7,  kh*0.5))) # Prow tip top
v_k10= bm_knee_c.verts.new(Vector((-kw*0.30, -kd*0.4,  kh*0.5)))

bm_knee_c.faces.new((v_k1, v_k2, v_k7, v_k6))
bm_knee_c.faces.new((v_k2, v_k3, v_k8, v_k7))
bm_knee_c.faces.new((v_k3, v_k4, v_k9, v_k8))
bm_knee_c.faces.new((v_k4, v_k5, v_k10, v_k9))
bm_knee_c.faces.new((v_k5, v_k1, v_k6, v_k10))
bm_knee_c.faces.new((v_k1, v_k5, v_k4, v_k3, v_k2))
bm_knee_c.faces.new((v_k6, v_k7, v_k8, v_k9, v_k10))

bmesh.ops.recalc_face_normals(bm_knee_c, faces=bm_knee_c.faces)
me_knee_c = bpy.data.meshes.new("Knee_Cowling_Mesh")
bm_knee_c.to_mesh(me_knee_c); bm_knee_c.free()

knee_cowling = bpy.data.objects.new("Knee_Armor_Cowling", me_knee_c)
knee_cowling.location = (0.0, -0.32, 1.95)
knee_cowling.rotation_euler = (math.radians(-22), 0, 0) # Angled with cylinder
phase5_col.objects.link(knee_cowling)
knee_cowling.data.materials.append(M_ARMOR_OCHRE)
finish_armor(knee_cowling, bevel_w=0.012)

# =========================================================================
# STEP 36 & 37: SHIN FACETED PROW & TWIN AERO-DEFLECTOR REAR FINS
# Front faceted monocoque with dual chevron fins angled backward at 40 deg
# Location: Z from 0.70 to 1.85, Y from -0.55 to 0.85
# =========================================================================
print("\n>>> EXECUTING STEPS 36-37: Shin Faceted Monocoque & Twin Aero-Fins...")

bm_shin = bmesh.new()
# Stations along Z for the shin:
# Z=1.75 (top knee socket), Z=1.40 (aero fin peak), Z=1.05 (mid calf), Z=0.70 (ankle neck)
sw = 0.74

# Z=1.75: Top socket
s_175 = [
    ( sw*0.48,  0.25, 1.75),
    ( sw*0.48, -0.42, 1.75),
    ( 0.00,    -0.58, 1.75), # Front prow
    (-sw*0.48, -0.42, 1.75),
    (-sw*0.48,  0.25, 1.75)
]

# Z=1.40: Wing peak extending backward (Y reaches 0.75m!)
s_140 = [
    ( sw*0.52,  0.75, 1.40), # Rear aero-fin tip right!
    ( sw*0.52, -0.48, 1.40),
    ( 0.00,    -0.68, 1.40), # Deep front prow
    (-sw*0.52, -0.48, 1.40),
    (-sw*0.52,  0.75, 1.40)  # Rear aero-fin tip left!
]

# Z=1.05: Mid calf taper
s_105 = [
    ( sw*0.44,  0.55, 1.05), # Rear fin lower edge
    ( sw*0.44, -0.38, 1.05),
    ( 0.00,    -0.52, 1.05),
    (-sw*0.44, -0.38, 1.05),
    (-sw*0.44,  0.55, 1.05)
]

# Z=0.70: Ankle socket
s_070 = [
    ( sw*0.38,  0.15, 0.70),
    ( sw*0.38, -0.25, 0.70),
    ( 0.00,    -0.38, 0.70),
    (-sw*0.38, -0.25, 0.70),
    (-sw*0.38,  0.15, 0.70)
]

shin_rings = []
for st in [s_175, s_140, s_105, s_070]:
    ring = [bm_shin.verts.new(Vector(p)) for p in st]
    shin_rings.append(ring)

for s in range(len(shin_rings) - 1):
    r1 = shin_rings[s]
    r2 = shin_rings[s + 1]
    for i in range(len(r1) - 1):
        bm_shin.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))

# Central rear trench between twin fins (inward notch)
for s in range(len(shin_rings) - 1):
    r1 = shin_rings[s]
    r2 = shin_rings[s + 1]
    bm_shin.faces.new((r1[4], r1[0], r2[0], r2[4]))

bmesh.ops.recalc_face_normals(bm_shin, faces=bm_shin.faces)
me_shin = bpy.data.meshes.new("Shin_Monocoque_Mesh")
bm_shin.to_mesh(me_shin); bm_shin.free()

shin_armor_obj = bpy.data.objects.new("Shin_Armor_Monocoque", me_shin)
phase5_col.objects.link(shin_armor_obj)
shin_armor_obj.data.materials.append(M_ARMOR_OCHRE)
finish_armor(shin_armor_obj, bevel_w=0.016)

# =========================================================================
# STEP 38: SLOTTED COOLING LOUVERS ON SHIN FLANKS
# 4 recessed ventilation louvers along each flank
# =========================================================================
print("\n>>> EXECUTING STEP 38: Slotted Cooling Louvers on Shin...")

for side in (-1, 1):
    for l_idx in range(4):
        lz = 1.35 - l_idx * 0.10
        ly = -0.15 - l_idx * 0.06
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side * 0.39, ly, lz))
        louver = bpy.context.object; louver.name = f"Shin_Louver_{side}_{l_idx}"
        louver.scale = (0.02, 0.12, 0.025); bpy.ops.object.transform_apply(scale=True)
        louver.rotation_euler = (math.radians(-35), 0, 0)
        louver.data.materials.append(M_ARMOR_DARK)
        phase5_col.objects.link(louver); scn.collection.objects.unlink(louver)

# =========================================================================
# STEP 39: ANKLE HORSESHOE C-CLAMP COLLAR WITH DUAL HORNS
# Location: (X=0.0, Y=-0.22, Z=0.55)
# Wraps around ankle gear hub, with twin horns projecting forward
# =========================================================================
print("\n>>> EXECUTING STEP 39: Ankle Horseshoe C-Clamp Collar with Horns...")

bm_cuff = bmesh.new()
cw = 0.88; cd = 0.65; ch = 0.28
# U-profile with forward horns
cuff_u = [
    ( cw*0.5, -cd*0.35), # Rear right
    ( cw*0.5,  cd*0.35), # Front right
    ( cw*0.3,  cd*0.65), # Front horn right tip!
    ( cw*0.2,  cd*0.35), # Front inner notch
    (-cw*0.2,  cd*0.35), # Front inner notch
    (-cw*0.3,  cd*0.65), # Front horn left tip!
    (-cw*0.5,  cd*0.35), # Front left
    (-cw*0.5, -cd*0.35), # Rear left
    ( 0.00,   -cd*0.45)  # Rear bridge
]

v_cb = [bm_cuff.verts.new(Vector((x, y, -ch*0.5))) for x, y in cuff_u]
v_ct = [bm_cuff.verts.new(Vector((x, y,  ch*0.5))) for x, y in cuff_u]

n_cu = len(cuff_u)
for i in range(n_cu):
    nxt = (i + 1) % n_cu
    bm_cuff.faces.new((v_cb[i], v_cb[nxt], v_ct[nxt], v_ct[i]))

bm_cuff.faces.new(reversed(v_cb))
bm_cuff.faces.new(v_ct)

bmesh.ops.recalc_face_normals(bm_cuff, faces=bm_cuff.faces)
me_cuff = bpy.data.meshes.new("Ankle_C_Clamp_Mesh")
bm_cuff.to_mesh(me_cuff); bm_cuff.free()

cuff_obj = bpy.data.objects.new("Ankle_C_Clamp_Collar", me_cuff)
cuff_obj.location = (0.0, -0.22, 0.55)
phase5_col.objects.link(cuff_obj)
cuff_obj.data.materials.append(M_ARMOR_OCHRE)
finish_armor(cuff_obj, bevel_w=0.012)

# =========================================================================
# STEP 40: CRITICAL AUDIT RENDERS FOR ARMOR PHASE
# Silhouette verification against Photo 4
# =========================================================================
print("\n>>> EXECUTING STEP 40: Critical Armor Audit & Silhouette Pass...")

cam = scn.camera
cam_d = cam.data

# 1. Full Leg Orthographic Side Profile (Direct comparison with Photo 4)
cam_d.type = 'ORTHO'
cam_d.ortho_scale = 4.2
leg_mid = Vector((0.0, 0.15, 1.85))
cam.location = (leg_mid.x + 12.0, leg_mid.y, leg_mid.z)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))

p_armor_side = os.path.join(OUT_DIR, "step33_step40_armor_ortho_side.png")
scn.render.filepath = p_armor_side
bpy.ops.render.render(write_still=True)
print(f"Rendered Armor Ortho Side: {p_armor_side}")
shutil.copyfile(p_armor_side, os.path.join(ART_DIR, "step33_step40_armor_ortho_side.png"))

# 2. Hero 3/4 Perspective of Full Armored Leg
cam_d.type = 'PERSP'
cam_d.lens = 72
cam.location = (4.8, -5.2, 2.6)
d_hero = leg_mid - cam.location
cam.rotation_euler = d_hero.to_track_quat('-Z', 'Y').to_euler()

p_armor_hero = os.path.join(OUT_DIR, "step33_step40_armor_hero_perspective.png")
scn.render.filepath = p_armor_hero
bpy.ops.render.render(write_still=True)
print(f"Rendered Armor Hero Perspective: {p_armor_hero}")
shutil.copyfile(p_armor_hero, os.path.join(ART_DIR, "step33_step40_armor_hero_perspective.png"))

# 3. Knee & Thigh Armor Transition Closeup
knee_c_pos = Vector((0.0, -0.15, 2.10))
cam_d.lens = 92
cam.location = (knee_c_pos.x + 2.4, knee_c_pos.y - 2.8, knee_c_pos.z + 0.6)
d_k = knee_c_pos - cam.location
cam.rotation_euler = d_k.to_track_quat('-Z', 'Y').to_euler()

p_armor_knee = os.path.join(OUT_DIR, "step35_knee_armor_cowling_audit.png")
scn.render.filepath = p_armor_knee
bpy.ops.render.render(write_still=True)
print(f"Rendered Knee Armor Audit: {p_armor_knee}")
shutil.copyfile(p_armor_knee, os.path.join(ART_DIR, "step35_knee_armor_cowling_audit.png"))

# Save updated scene
BLEND_PHASE5 = os.path.join(OUT_DIR, "PHASE1_TO_5_EXECUTION.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PHASE5)
print(f"Saved Phase 5 Scene to {BLEND_PHASE5}")
print("Phase V (Steps 33-40) Successfully Executed!")

