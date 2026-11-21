import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BASE_BLEND = os.path.join(OUT_DIR, "PHASE1_AND_PHASE2_EXECUTION.blend")

bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
scn = bpy.context.scene

# Materials
M_CYAN_HYDRO = bpy.data.materials.get("L2_Hydro_Cyan")
M_ARMOR_OLIV = bpy.data.materials.get("L4_Armor_Olive")
M_DARK_STEEL = bpy.data.materials.get("M_DarkSteel")

# Chrome material for hydraulic rod
M_CHROME = bpy.data.materials.new("M_ChromeRod")
M_CHROME.use_nodes = True
b_ch = M_CHROME.node_tree.nodes.get("Principled BSDF")
b_ch.inputs['Base Color'].default_value = (0.95, 0.95, 0.97, 1.0)
b_ch.inputs['Metallic'].default_value = 1.0
b_ch.inputs['Roughness'].default_value = 0.05 # Mirror sheen

# High-pressure braided hose material
M_HOSE = bpy.data.materials.new("M_BraidedHose")
M_HOSE.use_nodes = True
b_hs = M_HOSE.node_tree.nodes.get("Principled BSDF")
b_hs.inputs['Base Color'].default_value = (0.05, 0.06, 0.07, 1.0)
b_hs.inputs['Roughness'].default_value = 0.65
b_hs.inputs['Metallic'].default_value = 0.20

hydro_col = bpy.data.collections.new("Hydraulic_Actuation_Group")
scn.collection.children.link(hydro_col)

# =========================================================================
# STEP 17 - 20: MAIN DIAGONAL KNEE HYDRAULIC CYLINDER (RAM) & CLEVIS MOUNTS
# True pivot vector:
# Upper Thigh Clevis: (X=0.0, Y=0.38, Z=2.45)
# Lower Shin Clevis:  (X=0.0, Y=-0.42, Z=1.52)
# =========================================================================
print("\n>>> EXECUTING STEPS 17-20: Main Diagonal Knee Hydraulic Ram...")

p_upper = Vector((0.0, 0.38, 2.45))
p_lower = Vector((0.0, -0.42, 1.52))
ram_vec = p_lower - p_upper
ram_len = ram_vec.length
ram_dir = ram_vec.normalized()

# Rotation to align Z axis with ram_dir
rot_quat = Vector((0, 0, 1)).rotation_difference(ram_dir)
rot_euler = rot_quat.to_euler()

# 1. Upper Anchor Clevis Mount (Thigh)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=p_upper)
clevis_up = bpy.context.object; clevis_up.name = "Thigh_Hydraulic_Clevis"
clevis_up.scale = (0.34, 0.22, 0.22); bpy.ops.object.transform_apply(scale=True)
clevis_up.rotation_euler = rot_euler
clevis_up.data.materials.append(M_DARK_STEEL)
hydro_col.objects.link(clevis_up); scn.collection.objects.unlink(clevis_up)

# 2. Main Cylinder Barrel (Step 17)
barrel_len = ram_len * 0.58
barrel_r = 0.11
barrel_center = p_upper + ram_dir * (barrel_len * 0.5)

bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=barrel_r, depth=barrel_len,
                                    location=barrel_center)
barrel = bpy.context.object; barrel.name = "Knee_Hydraulic_Barrel"
barrel.rotation_euler = rot_euler
barrel.data.materials.append(M_CYAN_HYDRO)
hydro_col.objects.link(barrel); scn.collection.objects.unlink(barrel)

# Barrel Reinforcing Girdle Rings (3 rings)
for r_idx in (-0.35, 0.0, 0.35):
    ring_pos = barrel_center + ram_dir * (barrel_len * r_idx)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=barrel_r * 1.14, depth=barrel_len * 0.08,
                                        location=ring_pos)
    ring = bpy.context.object; ring.name = f"Barrel_Girdle_Ring_{r_idx}"
    ring.rotation_euler = rot_euler
    ring.data.materials.append(M_DARK_STEEL)
    hydro_col.objects.link(ring); scn.collection.objects.unlink(ring)

# Barrel Gland Nut / Seal Head
gland_pos = barrel_center + ram_dir * (barrel_len * 0.5 + 0.04)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=barrel_r * 1.18, depth=0.08,
                                    location=gland_pos)
gland = bpy.context.object; gland.name = "Barrel_Gland_Seal_Nut"
gland.rotation_euler = rot_euler
gland.data.materials.append(M_DARK_STEEL)
hydro_col.objects.link(gland); scn.collection.objects.unlink(gland)

# 3. Mirror Polished Chrome Piston Rod (Step 18)
rod_r = 0.065
rod_len = ram_len * 0.52
rod_center = gland_pos + ram_dir * (rod_len * 0.5)

bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=rod_r, depth=rod_len,
                                    location=rod_center)
rod = bpy.context.object; rod.name = "Knee_Piston_Rod_Chrome"
rod.rotation_euler = rot_euler
rod.data.materials.append(M_CHROME)
hydro_col.objects.link(rod); scn.collection.objects.unlink(rod)

# 4. Lower Anchor Clevis Mount (Shin Prow) (Step 20)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=p_lower)
clevis_low = bpy.context.object; clevis_low.name = "Shin_Hydraulic_Clevis"
clevis_low.scale = (0.28, 0.20, 0.20); bpy.ops.object.transform_apply(scale=True)
clevis_low.rotation_euler = rot_euler
clevis_low.data.materials.append(M_DARK_STEEL)
hydro_col.objects.link(clevis_low); scn.collection.objects.unlink(clevis_low)

# Cross pins through both clevises
for c_pos, c_name in [(p_upper, "Upper_Pin"), (p_lower, "Lower_Pin")]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.038, depth=0.38,
                                        location=c_pos, rotation=(0, math.radians(90), 0))
    pin = bpy.context.object; pin.name = f"Clevis_{c_name}"
    pin.data.materials.append(M_CHROME)
    hydro_col.objects.link(pin); scn.collection.objects.unlink(pin)

# =========================================================================
# STEP 21: TWIN ANKLE STABILIZATION DAMPERS
# Located on left and right sides of the ankle joint
# Connecting shin rear to ankle heel
# =========================================================================
print("\n>>> EXECUTING STEP 21: Twin Ankle Stabilization Dampers...")

ankle_dampers_col = bpy.data.collections.new("Ankle_Stabilizer_Dampers")
scn.collection.children.link(ankle_dampers_col)

for side in (-1, 1):
    d_up = Vector((side * 0.32, 0.05, 1.05))
    d_low = Vector((side * 0.28, -0.35, 0.45))
    d_vec = d_low - d_up
    d_len = d_vec.length
    d_dir = d_vec.normalized()
    d_rot = Vector((0, 0, 1)).rotation_difference(d_dir).to_euler()
    
    # Damper Cylinder
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.055, depth=d_len * 0.55,
                                        location=d_up + d_dir * (d_len * 0.28))
    d_cyl = bpy.context.object; d_cyl.name = f"Ankle_Damper_Cyl_{side}"
    d_cyl.rotation_euler = d_rot
    d_cyl.data.materials.append(M_CYAN_HYDRO)
    ankle_dampers_col.objects.link(d_cyl); scn.collection.objects.unlink(d_cyl)
    
    # Damper Rod
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.032, depth=d_len * 0.50,
                                        location=d_low - d_dir * (d_len * 0.25))
    d_rod = bpy.context.object; d_rod.name = f"Ankle_Damper_Rod_{side}"
    d_rod.rotation_euler = d_rot
    d_rod.data.materials.append(M_CHROME)
    ankle_dampers_col.objects.link(d_rod); scn.collection.objects.unlink(d_rod)

# =========================================================================
# STEP 22 & 23: HYDRAULIC MANIFOLD BLOCK & HIGH-PRESSURE LINES
# Manifold block mounted to thigh inner frame
# Hardline steel tubes and flexible braided hoses running to cylinders
# =========================================================================
print("\n>>> EXECUTING STEPS 22-23: Hydraulic Manifold Block & Hardline Lines...")

# Manifold Block
manifold_pos = Vector((0.26, 0.22, 2.30))
bpy.ops.mesh.primitive_cube_add(size=1.0, location=manifold_pos)
manifold = bpy.context.object; manifold.name = "Hydraulic_Manifold_Block"
manifold.scale = (0.16, 0.22, 0.18); bpy.ops.object.transform_apply(scale=True)
manifold.data.materials.append(M_DARK_STEEL)
hydro_col.objects.link(manifold); scn.collection.objects.unlink(manifold)

# 4 Test Fittings / Pressure Ports on the Manifold
for p_idx in range(4):
    f_ang = p_idx * (math.pi / 2.0)
    fy = manifold_pos.y + 0.08 * math.cos(f_ang)
    fz = manifold_pos.z + 0.06 * math.sin(f_ang)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.022, depth=0.05,
                                        location=(manifold_pos.x + 0.09, fy, fz),
                                        rotation=(0, math.radians(90), 0))
    port = bpy.context.object; port.name = f"Pressure_Port_{p_idx}"
    port.data.materials.append(M_CHROME)
    hydro_col.objects.link(port); scn.collection.objects.unlink(port)

# High-Pressure Braided Hose running from Manifold to Main Barrel
hose_pts = [
    Vector((manifold_pos.x + 0.08, manifold_pos.y - 0.05, manifold_pos.z)),
    Vector((0.22, 0.10, 2.15)),
    Vector((0.15, -0.05, 1.95)),
    barrel_center + Vector((barrel_r * 0.9, 0, 0))
]

# Build smooth curved pipe mesh along points
bm_h = bmesh.new()
h_rad = 0.022
n_segments = len(hose_pts)
prev_ring = None
for s_idx, pt in enumerate(hose_pts):
    # Ring of 8 vertices
    ring = []
    for vi in range(8):
        ang = vi * (2 * math.pi / 8.0)
        vy = pt.y + h_rad * math.cos(ang)
        vz = pt.z + h_rad * math.sin(ang)
        ring.append(bm_h.verts.new(Vector((pt.x, vy, vz))))
    if prev_ring:
        for vi in range(8):
            nxt = (vi + 1) % 8
            bm_h.faces.new((prev_ring[vi], prev_ring[nxt], ring[nxt], ring[vi]))
    prev_ring = ring

bmesh.ops.recalc_face_normals(bm_h, faces=bm_h.faces)
me_hose = bpy.data.meshes.new("Hydraulic_Hose_Mesh")
bm_h.to_mesh(me_hose); bm_h.free()

hose_obj = bpy.data.objects.new("Knee_Pressure_Hose", me_hose)
hydro_col.objects.link(hose_obj)
hose_obj.data.materials.append(M_HOSE)

# =========================================================================
# STEP 24: KINEMATIC AUDIT PASS & MULTI-VIEW RENDERS
# =========================================================================
print("\n>>> EXECUTING STEP 24: Critical Kinematic Pressure Group Audit Render...")

cam = scn.camera
cam_d = cam.data

# 1. Macro Closeup on Diagonal Cylinder & Chrome Rod
cam_d.type = 'PERSP'
cam_d.lens = 90
cam.location = (barrel_center.x + 2.5, barrel_center.y - 2.8, barrel_center.z + 0.6)
d_ram = barrel_center - cam.location
cam.rotation_euler = d_ram.to_track_quat('-Z', 'Y').to_euler()

p_ram_audit = os.path.join(OUT_DIR, "step17_step20_hydraulic_ram_audit.png")
scn.render.filepath = p_ram_audit
bpy.ops.render.render(write_still=True)
print(f"Rendered Hydraulic Ram Audit: {p_ram_audit}")
shutil.copyfile(p_ram_audit, os.path.join(ART_DIR, "step17_step20_hydraulic_ram_audit.png"))

# 2. Hero 3/4 Perspective of Full Leg Kinematics
cam_d.lens = 70
cam.location = (4.5, -4.8, 2.5)
target_leg = Vector((0.0, 0.1, 1.85))
d_hero = target_leg - cam.location
cam.rotation_euler = d_hero.to_track_quat('-Z', 'Y').to_euler()

p_hero_audit = os.path.join(OUT_DIR, "steps_17_24_hero_kinematics_audit.png")
scn.render.filepath = p_hero_audit
bpy.ops.render.render(write_still=True)
print(f"Rendered Hero Kinematics Audit: {p_hero_audit}")
shutil.copyfile(p_hero_audit, os.path.join(ART_DIR, "steps_17_24_hero_kinematics_audit.png"))

# Save updated scene
BLEND_PHASE3 = os.path.join(OUT_DIR, "PHASE1_2_3_EXECUTION.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PHASE3)
print(f"Saved Phase 3 Scene to {BLEND_PHASE3}")
print("Phase III (Steps 17-24) Successfully Executed!")

