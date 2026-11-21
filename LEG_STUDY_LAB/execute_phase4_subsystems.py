import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BASE_BLEND = os.path.join(OUT_DIR, "PHASE1_2_3_EXECUTION.blend")

bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
scn = bpy.context.scene

# Materials
M_CYAN_HYDRO = bpy.data.materials.get("L2_Hydro_Cyan")
M_ARMOR_OLIV = bpy.data.materials.get("L4_Armor_Olive")
M_DARK_STEEL = bpy.data.materials.get("M_DarkSteel")
M_CHROME     = bpy.data.materials.get("M_ChromeRod")
M_HOSE       = bpy.data.materials.get("M_BraidedHose")

# Bright Industrial Orange for Secondary Subsystems / Heat Sinks
M_ORANGE = bpy.data.materials.new("M_SubsysOrange")
M_ORANGE.use_nodes = True
b_or = M_ORANGE.node_tree.nodes.get("Principled BSDF")
b_or.inputs['Base Color'].default_value = (0.95, 0.42, 0.08, 1.0)
b_or.inputs['Metallic'].default_value = 0.85
b_or.inputs['Roughness'].default_value = 0.28

phase4_col = bpy.data.collections.new("Phase4_Secondary_Subsystems")
scn.collection.children.link(phase4_col)

# =========================================================================
# STEP 25 & 26: H-BRACKET & DUAL FINNED ACCUMULATOR CANISTERS
# Location: Outer board of the Thigh at (X=0.48, Y=0.28, Z=2.68)
# Angled to match thigh rake (pitch ~ 25 deg)
# =========================================================================
print("\n>>> EXECUTING STEPS 25-26: H-Bracket & Dual Finned Canisters...")

h_center = Vector((0.46, 0.28, 2.68))
h_rot = Euler((math.radians(24), 0, 0)) # Rake angle

# 1. H-Frame Mounting Bracket
bpy.ops.mesh.primitive_cube_add(size=1.0, location=h_center)
h_frame = bpy.context.object; h_frame.name = "Thigh_H_Bracket"
h_frame.scale = (0.05, 0.28, 0.18); bpy.ops.object.transform_apply(scale=True)
h_frame.rotation_euler = h_rot
h_frame.data.materials.append(M_DARK_STEEL)
phase4_col.objects.link(h_frame); scn.collection.objects.unlink(h_frame)
mod_h = h_frame.modifiers.new("Bevel", 'BEVEL')
mod_h.width = 0.008; mod_h.segments = 2

# Inset central crossbar cutout in H-frame
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(h_center.x + 0.02, h_center.y, h_center.z))
h_bar = bpy.context.object; h_bar.name = "Thigh_H_Bar"
h_bar.scale = (0.04, 0.08, 0.32); bpy.ops.object.transform_apply(scale=True)
h_bar.rotation_euler = h_rot
h_bar.data.materials.append(M_DARK_STEEL)
phase4_col.objects.link(h_bar); scn.collection.objects.unlink(h_bar)

# 2. Dual Finned Canisters (Front and Rear of the H-bracket)
can_r = 0.065
can_len = 0.42
num_fins = 6
fin_depth = 0.022
can_spacing = 0.17

for c_idx, y_sign in enumerate([-1, 1]):
    # Compute local offset rotated by h_rot
    local_off = Vector((0.04, y_sign * can_spacing * 0.5, 0.0))
    local_off.rotate(h_rot)
    c_pos = h_center + local_off
    
    # Core canister
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=can_r, depth=can_len,
                                        location=c_pos)
    can = bpy.context.object; can.name = f"Accumulator_Canister_{c_idx}"
    can.rotation_euler = (h_rot.x + math.radians(90), 0, 0)
    can.data.materials.append(M_ORANGE)
    phase4_col.objects.link(can); scn.collection.objects.unlink(can)
    
    # Annular cooling fins along canister
    fin_step = (can_len * 0.65) / num_fins
    for f_idx in range(num_fins):
        f_offset_local = Vector((0.0, 0.0, -can_len*0.32 + f_idx * fin_step))
        f_rot = Euler((h_rot.x + math.radians(90), 0, 0))
        f_offset_local.rotate(f_rot)
        
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=can_r + fin_depth, depth=0.012,
                                            location=c_pos + f_offset_local)
        fin = bpy.context.object; fin.name = f"Canister_{c_idx}_Fin_{f_idx}"
        fin.rotation_euler = f_rot
        fin.data.materials.append(M_DARK_STEEL)
        phase4_col.objects.link(fin); scn.collection.objects.unlink(fin)
        
    # Domed End Caps with Center Hex Ports
    for cap_sign in (-1, 1):
        cap_off = Vector((0.0, 0.0, cap_sign * (can_len * 0.5 + 0.015)))
        cap_off.rotate(Euler((h_rot.x + math.radians(90), 0, 0)))
        
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=can_r * 1.08, depth=0.03,
                                            location=c_pos + cap_off)
        cap = bpy.context.object; cap.name = f"Canister_{c_idx}_Cap_{cap_sign}"
        cap.rotation_euler = (h_rot.x + math.radians(90), 0, 0)
        cap.data.materials.append(M_DARK_STEEL)
        phase4_col.objects.link(cap); scn.collection.objects.unlink(cap)
        
        # Center hex port
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.022, depth=0.02,
                                            location=c_pos + cap_off * 1.1)
        hex_p = bpy.context.object; hex_p.name = f"Canister_{c_idx}_Port_{cap_sign}"
        hex_p.rotation_euler = (h_rot.x + math.radians(90), 0, 0)
        hex_p.data.materials.append(M_CHROME)
        phase4_col.objects.link(hex_p); scn.collection.objects.unlink(hex_p)

# =========================================================================
# STEP 27: HARDLINE HYDRAULIC FEED TUBES FROM H-BLOCK TO MANIFOLD
# =========================================================================
print("\n>>> EXECUTING STEP 27: Hardline Feed Lines & P-Clamps...")

line_pts = [
    Vector((h_center.x + 0.02, h_center.y - 0.12, h_center.z - 0.15)),
    Vector((0.36, 0.20, 2.45)),
    Vector((0.28, 0.22, 2.38)) # Inflow into manifold
]

bm_tube = bmesh.new()
t_rad = 0.016
prev_ring = None
for s_idx, pt in enumerate(line_pts):
    ring = []
    for vi in range(8):
        ang = vi * (2 * math.pi / 8.0)
        vy = pt.y + t_rad * math.cos(ang)
        vz = pt.z + t_rad * math.sin(ang)
        ring.append(bm_tube.verts.new(Vector((pt.x, vy, vz))))
    if prev_ring:
        for vi in range(8):
            nxt = (vi + 1) % 8
            bm_tube.faces.new((prev_ring[vi], prev_ring[nxt], ring[nxt], ring[vi]))
    prev_ring = ring

bmesh.ops.recalc_face_normals(bm_tube, faces=bm_tube.faces)
me_tube = bpy.data.meshes.new("Accumulator_Feed_Tube_Mesh")
bm_tube.to_mesh(me_tube); bm_tube.free()

tube_obj = bpy.data.objects.new("Accumulator_Feed_Tube", me_tube)
phase4_col.objects.link(tube_obj)
tube_obj.data.materials.append(M_CHROME)

# =========================================================================
# STEP 28: KNEE TRAVEL-STOP DAMPER (DISC SPRING BUMPER)
# Positioned directly behind the knee joint to limit reverse hyperextension
# Location: (X=0.0, Y=-0.25, Z=1.92)
# =========================================================================
print("\n>>> EXECUTING STEP 28: Knee Travel-Stop Damper with Disc Spring Stack...")

bumper_pos = Vector((0.0, -0.22, 1.95))

# Heavy Cast Mounting Bracket
bpy.ops.mesh.primitive_cube_add(size=1.0, location=bumper_pos)
bumper_base = bpy.context.object; bumper_base.name = "Knee_Travel_Stop_Base"
bumper_base.scale = (0.28, 0.18, 0.16); bpy.ops.object.transform_apply(scale=True)
bumper_base.data.materials.append(M_DARK_STEEL)
phase4_col.objects.link(bumper_base); scn.collection.objects.unlink(bumper_base)

# Disc Spring Pack (5 stacked conical washer discs)
for s_idx in range(5):
    sz = bumper_pos.z - 0.06 + s_idx * 0.025
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.095, depth=0.015,
                                        location=(bumper_pos.x, bumper_pos.y - 0.10, sz))
    disc = bpy.context.object; disc.name = f"Belleville_Spring_Disc_{s_idx}"
    disc.data.materials.append(M_DARK_STEEL)
    phase4_col.objects.link(disc); scn.collection.objects.unlink(disc)

# Striker Contact Pad (Hardened steel anvil pad)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bumper_pos.x, bumper_pos.y - 0.12, bumper_pos.z))
anvil = bpy.context.object; anvil.name = "Knee_Damper_Striker_Anvil"
anvil.scale = (0.22, 0.06, 0.12); bpy.ops.object.transform_apply(scale=True)
anvil.data.materials.append(M_CHROME)
phase4_col.objects.link(anvil); scn.collection.objects.unlink(anvil)

# =========================================================================
# STEP 29: SENSOR JUNCTION BOX & FLEX CONDUIT
# Location: Thigh forward flank at (X=-0.38, Y=0.35, Z=2.85)
# =========================================================================
print("\n>>> EXECUTING STEP 29: Electrical Sensor Junction Box...")

jbox_pos = Vector((-0.38, 0.35, 2.85))
bpy.ops.mesh.primitive_cube_add(size=1.0, location=jbox_pos)
jbox = bpy.context.object; jbox.name = "Sensor_Junction_Box"
jbox.scale = (0.10, 0.18, 0.22); bpy.ops.object.transform_apply(scale=True)
jbox.rotation_euler = (math.radians(18), 0, math.radians(-15))
jbox.data.materials.append(M_DARK_STEEL)
phase4_col.objects.link(jbox); scn.collection.objects.unlink(jbox)

# 3 Brass/Steel Gland Nuts for conduit entry
for g_idx in range(3):
    gz = jbox_pos.z - 0.06 + g_idx * 0.06
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.018, depth=0.04,
                                        location=(jbox_pos.x - 0.055, jbox_pos.y, gz),
                                        rotation=(0, math.radians(90), 0))
    gland = bpy.context.object; gland.name = f"JBox_Gland_{g_idx}"
    gland.data.materials.append(M_CHROME)
    phase4_col.objects.link(gland); scn.collection.objects.unlink(gland)

# =========================================================================
# STEP 30: PERFORATED DEBRIS/HEAT SHIELD
# Shield plate protecting the manifold lines from shrapnel and hot exhaust
# =========================================================================
print("\n>>> EXECUTING STEP 30: Perforated Heat & Debris Shield...")

shield_pos = Vector((0.35, 0.15, 2.15))
bpy.ops.mesh.primitive_cube_add(size=1.0, location=shield_pos)
shield = bpy.context.object; shield.name = "Hydro_Debris_Shield"
shield.scale = (0.018, 0.16, 0.36); bpy.ops.object.transform_apply(scale=True)
shield.rotation_euler = (math.radians(28), 0, 0)
shield.data.materials.append(M_DARK_STEEL)
phase4_col.objects.link(shield); scn.collection.objects.unlink(shield)
mod_s = shield.modifiers.new("Bevel", 'BEVEL')
mod_s.width = 0.005; mod_s.segments = 2

# =========================================================================
# STEP 31 & 32: CRITICAL AUDIT RENDERS (Steps 25 - 32)
# =========================================================================
print("\n>>> EXECUTING STEPS 31-32: Audit Renders for Secondary Subsystems...")

cam = scn.camera
cam_d = cam.data

# 1. Macro Closeup of the H-Bracket & Finned Canisters
cam_d.type = 'PERSP'
cam_d.lens = 95
cam.location = (h_center.x + 2.2, h_center.y - 2.4, h_center.z + 0.5)
d_h = h_center - cam.location
cam.rotation_euler = d_h.to_track_quat('-Z', 'Y').to_euler()

p_h_audit = os.path.join(OUT_DIR, "step25_step26_finned_canisters_audit.png")
scn.render.filepath = p_h_audit
bpy.ops.render.render(write_still=True)
print(f"Rendered Finned Canisters Audit: {p_h_audit}")
shutil.copyfile(p_h_audit, os.path.join(ART_DIR, "step25_step26_finned_canisters_audit.png"))

# 2. Closeup of Travel-Stop Damper Behind Knee
cam.location = (bumper_pos.x + 1.8, bumper_pos.y - 2.2, bumper_pos.z - 0.2)
d_bump = bumper_pos - cam.location
cam.rotation_euler = d_bump.to_track_quat('-Z', 'Y').to_euler()

p_bump_audit = os.path.join(OUT_DIR, "step28_travel_stop_damper_audit.png")
scn.render.filepath = p_bump_audit
bpy.ops.render.render(write_still=True)
print(f"Rendered Travel-Stop Damper Audit: {p_bump_audit}")
shutil.copyfile(p_bump_audit, os.path.join(ART_DIR, "step28_travel_stop_damper_audit.png"))

# 3. Hero 3/4 Perspective of Full Leg Kinematics + Subsystems
cam_d.lens = 72
cam.location = (4.8, -5.2, 2.6)
leg_mid = Vector((0.0, 0.15, 1.85))
d_hero = leg_mid - cam.location
cam.rotation_euler = d_hero.to_track_quat('-Z', 'Y').to_euler()

p_subsys_hero = os.path.join(OUT_DIR, "steps_25_32_subsystems_hero_audit.png")
scn.render.filepath = p_subsys_hero
bpy.ops.render.render(write_still=True)
print(f"Rendered Subsystems Hero Audit: {p_subsys_hero}")
shutil.copyfile(p_subsys_hero, os.path.join(ART_DIR, "steps_25_32_subsystems_hero_audit.png"))

# Save updated scene
BLEND_PHASE4 = os.path.join(OUT_DIR, "PHASE1_2_3_4_EXECUTION.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PHASE4)
print(f"Saved Phase 4 Scene to {BLEND_PHASE4}")
print("Phase IV (Steps 25-32) Successfully Executed!")

