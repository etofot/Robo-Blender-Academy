import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BASE_BLEND = os.path.join(OUT_DIR, "PHASE1_TO_5_EXECUTION.blend")

bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
scn = bpy.context.scene

# Materials
M_ARMOR_OCHRE = bpy.data.materials.get("M_ArmorOchreCeramic")
M_ARMOR_DARK  = bpy.data.materials.get("M_ArmorDarkPlate")
M_DARK_STEEL  = bpy.data.materials.get("M_DarkSteel")
M_CHROME      = bpy.data.materials.get("M_ChromeRod")
M_CYAN_HYDRO  = bpy.data.materials.get("L2_Hydro_Cyan")

# Rubber ground pad material
M_RUBBER = bpy.data.materials.new("M_RubberTreadPad")
M_RUBBER.use_nodes = True
b_rb = M_RUBBER.node_tree.nodes.get("Principled BSDF")
b_rb.inputs['Base Color'].default_value = (0.04, 0.04, 0.05, 1.0)
b_rb.inputs['Roughness'].default_value = 0.85
b_rb.inputs['Metallic'].default_value = 0.05

phase6_col = bpy.data.collections.new("Phase6_Articulated_Foot")
scn.collection.children.link(phase6_col)

def finish_hs(obj, bevel_w=0.012, seg=2):
    for p in obj.data.polygons: p.use_smooth = True
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = bevel_w; mod.segments = seg
    mod.limit_method = 'ANGLE'; mod.angle_limit = math.radians(35)
    return obj

# =========================================================================
# STEP 41: FOOT CENTRAL GIMBAL CORE
# Position: (X=0.0, Y=-0.22, Z=0.38)
# Heavy dual-axis gimbal block connecting the ankle cuff to the foot base
# =========================================================================
print("\n>>> EXECUTING STEP 41: Foot Central Gimbal Core...")

gimbal_center = Vector((0.0, -0.22, 0.38))

# Heavy Cast Gimbal Block (Octagonal Cross-Hub)
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.32, depth=0.28,
                                    location=gimbal_center)
gimbal = bpy.context.object; gimbal.name = "Foot_Gimbal_Core_Hub"
gimbal.data.materials.append(M_DARK_STEEL)
phase6_col.objects.link(gimbal); scn.collection.objects.unlink(gimbal)
finish_hs(gimbal, bevel_w=0.015)

# Lateral gimbal trunnions (pitch/roll bearing pins)
for side in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.10, depth=0.18,
                                        location=(side * 0.35, gimbal_center.y, gimbal_center.z),
                                        rotation=(0, math.radians(90), 0))
    pin = bpy.context.object; pin.name = f"Gimbal_Trunnion_{side}"
    pin.data.materials.append(M_CHROME)
    phase6_col.objects.link(pin); scn.collection.objects.unlink(pin)

# =========================================================================
# STEP 42 - 44: ARTICULATED FORE CLAWS & AFT HEEL OUTRIGGERS
# With 3-tier stepped forward slope, underside bridge clearance, and side pockets
# Splayed configuration: Fore claws at +/- 22 deg, Aft claws at +/- 155 deg
# =========================================================================
print("\n>>> EXECUTING STEPS 42-44: Articulated Fore & Aft Claws with Bridge Arch...")

def build_claw_mesh(name, toe_len=0.92, toe_w=0.32, toe_h=0.26):
    bm = bmesh.new()
    toe_profile = [
        # (Y, Z)
        ( toe_len * 0.45,  toe_h * 0.45), # Rear top hinge
        ( toe_len * 0.20,  toe_h * 0.55), # Tier 1 top crest
        (-toe_len * 0.05,  toe_h * 0.38), # Tier 2 step
        (-toe_len * 0.32,  toe_h * 0.18), # Tier 3 step down
        (-toe_len * 0.55, -toe_h * 0.35), # Chisel tip top
        (-toe_len * 0.55, -toe_h * 0.50), # Chisel tip ground
        (-toe_len * 0.35, -toe_h * 0.50), # Front contact pad
        (-toe_len * 0.15, -toe_h * 0.18), # Under-foot bridge arch start (85mm clearance!)
        ( toe_len * 0.15, -toe_h * 0.18), # Under-foot bridge arch peak
        ( toe_len * 0.35, -toe_h * 0.50), # Rear contact pad
        ( toe_len * 0.45, -toe_h * 0.50)  # Rear end
    ]
    w_out = toe_w
    w_rail = toe_w * 0.70
    n_p = len(toe_profile)
    
    v_lo = [bm.verts.new(Vector((-w_out*0.5,  y, z))) for y, z in toe_profile]
    v_ro = [bm.verts.new(Vector(( w_out*0.5,  y, z))) for y, z in toe_profile]
    v_lm = [bm.verts.new(Vector((-w_rail*0.5, y, z + (0.025 if z > 0 else 0)))) for y, z in toe_profile]
    v_rm = [bm.verts.new(Vector(( w_rail*0.5, y, z + (0.025 if z > 0 else 0)))) for y, z in toe_profile]
    
    for i in range(n_p):
        nxt = (i + 1) % n_p
        bm.faces.new((v_lo[i], v_lo[nxt], v_lm[nxt], v_lm[i]))
        bm.faces.new((v_rm[i], v_rm[nxt], v_ro[nxt], v_ro[i]))
        bm.faces.new((v_lm[i], v_lm[nxt], v_rm[nxt], v_rm[i]))
        
    bm.faces.new(v_lo)
    bm.faces.new(reversed(v_ro))
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(me); bm.free()
    
    obj = bpy.data.objects.new(name, me)
    phase6_col.objects.link(obj)
    obj.data.materials.append(M_ARMOR_OCHRE)
    finish_hs(obj, bevel_w=0.012)
    return obj

# 4 Claws:
claws_config = [
    # (name, offset_from_gimbal, rot_z_deg, length, width, height)
    ("Fore_Claw_Right", Vector(( 0.32, -0.42, -0.22)), -22, 1.05, 0.36, 0.28),
    ("Fore_Claw_Left",  Vector((-0.32, -0.42, -0.22)),  22, 1.05, 0.36, 0.28),
    ("Aft_Heel_Right",  Vector(( 0.28,  0.35, -0.22)),-155, 0.85, 0.32, 0.25),
    ("Aft_Heel_Left",   Vector((-0.28,  0.35, -0.22)), 155, 0.85, 0.32, 0.25)
]

claw_objects = []
for c_name, c_off, c_rot, c_len, c_w, c_h in claws_config:
    c_pos = gimbal_center + c_off
    claw = build_claw_mesh(c_name, toe_len=c_len, toe_w=c_w, toe_h=c_h)
    claw.location = c_pos
    claw.rotation_euler = (0, 0, math.radians(c_rot))
    claw_objects.append((claw, c_pos, c_rot))
    
    # Recessed Stadium Side Pockets on each claw
    for side in (-1, 1):
        pock_off = Vector((side * (c_w * 0.5 + 0.005), 0.05, 0.02))
        pock_off.rotate(Euler((0, 0, math.radians(c_rot))))
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.045, depth=0.03,
                                            location=c_pos + pock_off)
        pocket = bpy.context.object; pocket.name = f"{c_name}_Pocket_{side}"
        pocket.scale = (1.0, 2.5, 1.0); bpy.ops.object.transform_apply(scale=True)
        pocket.rotation_euler = (0, math.radians(90), math.radians(c_rot))
        pocket.data.materials.append(M_ARMOR_DARK)
        phase6_col.objects.link(pocket); scn.collection.objects.unlink(pocket)
        finish_hs(pocket, bevel_w=0.005)

# =========================================================================
# STEP 45: TOE ACTUATOR HYDRAULIC STRUTS (Ground Adaptation Pistons)
# 4 miniature hydraulic rams connecting the gimbal hub to each claw
# =========================================================================
print("\n>>> EXECUTING STEP 45: Toe Actuator Hydraulic Struts...")

for c_name, c_pos, c_rot in claw_objects:
    # Gimbal anchor point
    strut_up = Vector((gimbal_center.x + (0.18 if c_pos.x > 0 else -0.18),
                       gimbal_center.y + (0.12 if c_pos.y > gimbal_center.y else -0.12),
                       gimbal_center.z - 0.05))
    # Claw anchor point
    strut_low = c_pos + Vector((0, 0, 0.10))
    
    s_vec = strut_low - strut_up
    s_len = s_vec.length
    s_dir = s_vec.normalized()
    s_rot = Vector((0, 0, 1)).rotation_difference(s_dir).to_euler()
    
    # Cylinder Barrel
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.032, depth=s_len * 0.52,
                                        location=strut_up + s_dir * (s_len * 0.26))
    s_cyl = bpy.context.object; s_cyl.name = f"{c_name}_Strut_Cyl"
    s_cyl.rotation_euler = s_rot
    s_cyl.data.materials.append(M_CYAN_HYDRO)
    phase6_col.objects.link(s_cyl); scn.collection.objects.unlink(s_cyl)
    
    # Piston Rod (Chrome)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.018, depth=s_len * 0.50,
                                        location=strut_low - s_dir * (s_len * 0.24))
    s_rod = bpy.context.object; s_rod.name = f"{c_name}_Strut_Rod"
    s_rod.rotation_euler = s_rot
    s_rod.data.materials.append(M_CHROME)
    phase6_col.objects.link(s_rod); scn.collection.objects.unlink(s_rod)

# =========================================================================
# STEP 46: RUBBER GROUND CONTACT PADS & PRESSURE SENSORS
# Mounted underneath each claw's contact points
# =========================================================================
print("\n>>> EXECUTING STEP 46: Rubber Ground Contact Pads...")

for c_name, c_pos, c_rot in claw_objects:
    is_fore = ("Fore" in c_name)
    toe_length = 1.05 if is_fore else 0.85
    
    for pad_idx, y_loc in enumerate([-toe_length * 0.35, toe_length * 0.35]):
        pad_off = Vector((0.0, y_loc, -0.14))
        pad_off.rotate(Euler((0, 0, math.radians(c_rot))))
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=c_pos + pad_off)
        pad = bpy.context.object; pad.name = f"{c_name}_Pad_{pad_idx}"
        pad.scale = (0.28, 0.18, 0.035); bpy.ops.object.transform_apply(scale=True)
        pad.rotation_euler = (0, 0, math.radians(c_rot))
        pad.data.materials.append(M_RUBBER)
        phase6_col.objects.link(pad); scn.collection.objects.unlink(pad)

# =========================================================================
# AUDIT RENDERS FOR PHASE VI
# =========================================================================
print("\n>>> EXECUTING AUDIT RENDERS FOR PHASE VI...")

cam = scn.camera
cam_d = cam.data

# 1. Macro Closeup of the Articulated Foot & Struts
cam_d.type = 'PERSP'
cam_d.lens = 85
foot_lookat = Vector((0.0, -0.22, 0.18))
cam.location = (2.2, -2.4, 1.4)
d_foot = foot_lookat - cam.location
cam.rotation_euler = d_foot.to_track_quat('-Z', 'Y').to_euler()

p_foot_macro = os.path.join(OUT_DIR, "step41_step46_foot_macro_closeup.png")
scn.render.filepath = p_foot_macro
bpy.ops.render.render(write_still=True)
print(f"Rendered Foot Macro: {p_foot_macro}")
shutil.copyfile(p_foot_macro, os.path.join(ART_DIR, "step41_step46_foot_macro_closeup.png"))

# 2. Top Orthographic View of the Foot (Direct test against Photo 1)
cam_d.type = 'ORTHO'
cam_d.ortho_scale = 2.4
cam.location = (gimbal_center.x, gimbal_center.y, gimbal_center.z + 5.0)
cam.rotation_euler = (0, 0, 0) # Looking straight down

p_foot_top = os.path.join(OUT_DIR, "step41_step46_foot_top_ortho.png")
scn.render.filepath = p_foot_top
bpy.ops.render.render(write_still=True)
print(f"Rendered Foot Top Ortho: {p_foot_top}")
shutil.copyfile(p_foot_top, os.path.join(ART_DIR, "step41_step46_foot_top_ortho.png"))

# 3. Full Leg PBR Side Orthographic View (Hip to Ground)
cam_d.ortho_scale = 4.2
leg_mid = Vector((0.0, 0.15, 1.85))
cam.location = (leg_mid.x + 12.0, leg_mid.y, leg_mid.z)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))

p_full_pbr = os.path.join(OUT_DIR, "step41_step46_full_leg_pbr_side.png")
scn.render.filepath = p_full_pbr
bpy.ops.render.render(write_still=True)
print(f"Rendered Full Leg PBR Side: {p_full_pbr}")
shutil.copyfile(p_full_pbr, os.path.join(ART_DIR, "step41_step46_full_leg_pbr_side.png"))

# Save updated scene
BLEND_PHASE6 = os.path.join(OUT_DIR, "PHASE1_TO_6_EXECUTION.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PHASE6)
print(f"Saved Phase 6 Scene to {BLEND_PHASE6}")
print("Phase VI (Steps 41-46) Successfully Executed!")

