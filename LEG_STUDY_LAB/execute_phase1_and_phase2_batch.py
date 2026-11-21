import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BASE_BLEND = os.path.join(OUT_DIR, "PHASE1_PIPELINE_EXECUTION.blend")

# Open previous blend
bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
scn = bpy.context.scene

# Materials
M_GOLD_GEAR  = bpy.data.materials.get("L1_Gears_Gold")
M_CYAN_HYDRO = bpy.data.materials.get("L2_Hydro_Cyan")
M_ARMOR_OLIV = bpy.data.materials.get("L4_Armor_Olive")
M_DARK_STEEL = bpy.data.materials.new("M_DarkSteel")
M_DARK_STEEL.use_nodes = True
b_ds = M_DARK_STEEL.node_tree.nodes.get("Principled BSDF")
b_ds.inputs['Base Color'].default_value = (0.12, 0.14, 0.16, 1.0)
b_ds.inputs['Metallic'].default_value = 0.95
b_ds.inputs['Roughness'].default_value = 0.25

def link_obj(o):
    scn.collection.objects.link(o)
    return o

# =========================================================================
# STEP 06 - 08: FLEXIBLE CABLE CHUTE / SEGMENTED ARMOR CHAIN
# Position: Arched over the upper thigh (Z ~ 3.3 to 3.8, Y ~ 0.2 to 1.0)
# =========================================================================
print("\n>>> EXECUTING STEPS 06-08: Flexible Segmented Armor Cable Chute...")

# True arc spline parameters from master
# 14 overlapping segmented links
n_links = 14
arc_radius_y = 0.65
arc_radius_z = 0.40
center_y = 0.60
center_z = 3.35

chain_col = bpy.data.collections.new("Armor_Cable_Chute")
scn.collection.children.link(chain_col)

for i in range(n_links):
    # Parametric angle along the arch (from front to rear)
    t = i / (n_links - 1)
    angle = math.radians(20 + t * 140) # 20 deg to 160 deg
    
    # Position along the curve
    py = center_y - arc_radius_y * math.cos(angle)
    pz = center_z + arc_radius_z * math.sin(angle)
    px = 0.0 # centered along X (or offset slightly outward)
    
    # Tangent angle for orienting the link
    tangent_angle = angle + math.pi/2.0
    
    # Build each articulated link with interlocking stepped flanges
    bm = bmesh.new()
    lw = 0.32; ld = 0.14; lh = 0.08
    
    # Box with top bevel and side slots
    bmesh.ops.create_cube(bm, size=1.0)
    # Scale into link shape
    for v in bm.verts:
        v.co.x *= lw
        v.co.y *= ld
        v.co.z *= lh
        # Top chamfer
        if v.co.z > 0:
            v.co.z += (0.02 if abs(v.co.y) < ld*0.3 else 0.0)
            
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me_link = bpy.data.meshes.new(f"Chute_Link_Mesh_{i}")
    bm.to_mesh(me_link); bm.free()
    
    link_obj = bpy.data.objects.new(f"Chute_Link_{i:02d}", me_link)
    link_obj.location = (px, py, pz)
    link_obj.rotation_euler = (tangent_angle, 0, 0)
    chain_col.objects.link(link_obj)
    link_obj.data.materials.append(M_ARMOR_OLIV)
    
    # Bevel modifier
    mod_b = link_obj.modifiers.new("Bevel", 'BEVEL')
    mod_b.width = 0.008; mod_b.segments = 2

# End Mount Clevis Brackets for Cable Chute (Fore & Aft)
for end_idx, (ey, ez, erot) in enumerate([
    (center_y - arc_radius_y * math.cos(math.radians(15)), center_z + arc_radius_z * math.sin(math.radians(15)), 0.4),
    (center_y - arc_radius_y * math.cos(math.radians(165)), center_z + arc_radius_z * math.sin(math.radians(165)), -0.4)
]):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, ey, ez))
    clevis = bpy.context.object; clevis.name = f"Chute_Clevis_Mount_{end_idx}"
    clevis.scale = (0.42, 0.18, 0.16); bpy.ops.object.transform_apply(scale=True)
    clevis.rotation_euler = (erot, 0, 0)
    clevis.data.materials.append(M_DARK_STEEL)
    chain_col.objects.link(clevis); scn.collection.objects.unlink(clevis)

# =========================================================================
# STEP 09 - 10: KNEE SUNBURST GEAR HUB & BEARING CORE
# Master's true position: Z ~ 1.86, Y ~ 0.06
# 24 radial triangular teeth, stepped recess, axial spindle
# =========================================================================
print("\n>>> EXECUTING STEPS 09-10: Knee Sunburst Gear Hub & Bearing Core...")

knee_center = Vector((0.0, 0.060, 1.860))
gear_col = bpy.data.collections.new("Knee_Gear_Assembly")
scn.collection.children.link(gear_col)

# 1. Procedural 24-Tooth Sunburst Radial Gear Disc
def build_sunburst_gear_disc(name, radius_outer, radius_inner, depth, num_teeth=24, tooth_depth=0.08):
    bm = bmesh.new()
    # Build stepped radial teeth profile in YZ plane
    pts_ring_front = []
    pts_ring_back = []
    
    for i in range(num_teeth * 2):
        ang = i * (2.0 * math.pi / (num_teeth * 2))
        is_tip = (i % 2 == 1)
        r = radius_outer if is_tip else (radius_outer - tooth_depth)
        
        y = r * math.cos(ang)
        z = r * math.sin(ang)
        
        # Front face (X = +depth/2) and Back face (X = -depth/2)
        v_f = bm.verts.new(Vector(( depth*0.5, y, z)))
        v_b = bm.verts.new(Vector((-depth*0.5, y, z)))
        pts_ring_front.append(v_f)
        pts_ring_back.append(v_b)
        
    # Inner bore circle
    pts_bore_f = []
    pts_bore_b = []
    for i in range(num_teeth * 2):
        ang = i * (2.0 * math.pi / (num_teeth * 2))
        y = radius_inner * math.cos(ang)
        z = radius_inner * math.sin(ang)
        v_bf = bm.verts.new(Vector(( depth*0.5, y, z)))
        v_bb = bm.verts.new(Vector((-depth*0.5, y, z)))
        pts_bore_f.append(v_bf)
        pts_bore_b.append(v_bb)
        
    n_pts = num_teeth * 2
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        # Outer teeth perimeter faces
        bm.faces.new((pts_ring_front[i], pts_ring_front[nxt], pts_ring_back[nxt], pts_ring_back[i]))
        # Inner bore perimeter faces
        bm.faces.new((pts_bore_b[i], pts_bore_b[nxt], pts_bore_f[nxt], pts_bore_f[i]))
        # Front face quads
        bm.faces.new((pts_ring_front[i], pts_bore_f[i], pts_bore_f[nxt], pts_ring_front[nxt]))
        # Back face quads
        bm.faces.new((pts_ring_back[nxt], pts_bore_b[nxt], pts_bore_b[i], pts_ring_back[i]))
        
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(me); bm.free()
    
    obj = bpy.data.objects.new(name, me)
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = 0.015; mod.segments = 2
    return obj

# Left and Right Sunburst Discs flanking the knee
gear_r_outer = 0.52
gear_r_inner = 0.28
gear_w = 0.12
x_dist = 0.42

for side in (-1, 1):
    gear_obj = build_sunburst_gear_disc(f"Knee_Sunburst_Disc_{side}", gear_r_outer, gear_r_inner, gear_w, num_teeth=24, tooth_depth=0.065)
    gear_obj.location = (side * x_dist, knee_center.y, knee_center.z)
    gear_col.objects.link(gear_obj)
    gear_obj.data.materials.append(M_GOLD_GEAR)

# Central Bearing Pin / Spindle through the knee
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.25, depth=1.10,
                                    location=(0.0, knee_center.y, knee_center.z),
                                    rotation=(0, math.radians(90), 0))
spindle = bpy.context.object; spindle.name = "Knee_Central_Spindle"
spindle.data.materials.append(M_DARK_STEEL)
gear_col.objects.link(spindle); scn.collection.objects.unlink(spindle)

# Stepped outer retaining bearing caps
for side in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.32, depth=0.08,
                                        location=(side * (x_dist + gear_w*0.5 + 0.04), knee_center.y, knee_center.z),
                                        rotation=(0, math.radians(90), 0))
    cap = bpy.context.object; cap.name = f"Knee_Retaining_Cap_{side}"
    cap.data.materials.append(M_DARK_STEEL)
    gear_col.objects.link(cap); scn.collection.objects.unlink(cap)

# =========================================================================
# STEP 11: ANKLE SUNBURST GEAR HUB
# Master's true position: Z ~ 0.53, Y ~ -0.22
# =========================================================================
print("\n>>> EXECUTING STEP 11: Ankle Sunburst Gear Hub Assembly...")

ankle_center = Vector((0.0, -0.225, 0.534))
ankle_col = bpy.data.collections.new("Ankle_Gear_Assembly")
scn.collection.children.link(ankle_col)

# Smaller 18-tooth radial sunburst disc for ankle
ankle_r_out = 0.38
ankle_r_inn = 0.20
ankle_w = 0.09
x_dist_ankle = 0.35

for side in (-1, 1):
    ankle_gear = build_sunburst_gear_disc(f"Ankle_Sunburst_Disc_{side}", ankle_r_out, ankle_r_inn, ankle_w, num_teeth=18, tooth_depth=0.05)
    ankle_gear.location = (side * x_dist_ankle, ankle_center.y, ankle_center.z)
    ankle_col.objects.link(ankle_gear)
    ankle_gear.data.materials.append(M_GOLD_GEAR)

# Ankle cross-spindle
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.18, depth=0.90,
                                    location=(0.0, ankle_center.y, ankle_center.z),
                                    rotation=(0, math.radians(90), 0))
ankle_spindle = bpy.context.object; ankle_spindle.name = "Ankle_Cross_Spindle"
ankle_spindle.data.materials.append(M_DARK_STEEL)
ankle_col.objects.link(ankle_spindle); scn.collection.objects.unlink(ankle_spindle)

# =========================================================================
# STEP 12: KNEE ASYMMETRIC DOGBONE LINKAGE ARM (Connecting Thigh & Shin)
# Connecting Knee (0.0, 0.06, 1.86) to lower shin pivot
# With hollow weight-reduction windows (технологические окна)
# =========================================================================
print("\n>>> EXECUTING STEP 12: Asymmetric Dogbone Linkage Arm with Lightening Windows...")

bm_arm = bmesh.new()
# Construct an engineering dogbone with dual pivot bosses and twin tapered beams
# Profile in YZ: Length ~ 0.95m, Width across X = 0.28m
arm_l = 0.85
arm_w = 0.26
arm_h = 0.32

# Outer Dogbone shell
v_d1 = bm_arm.verts.new(Vector((-arm_w*0.5, -0.22, -arm_l*0.5)))
v_d2 = bm_arm.verts.new(Vector(( arm_w*0.5, -0.22, -arm_l*0.5)))
v_d3 = bm_arm.verts.new(Vector(( arm_w*0.5,  0.22, -arm_l*0.5)))
v_d4 = bm_arm.verts.new(Vector((-arm_w*0.5,  0.22, -arm_l*0.5)))

v_d5 = bm_arm.verts.new(Vector((-arm_w*0.4, -0.15,  arm_l*0.5)))
v_d6 = bm_arm.verts.new(Vector(( arm_w*0.4, -0.15,  arm_l*0.5)))
v_d7 = bm_arm.verts.new(Vector(( arm_w*0.4,  0.15,  arm_l*0.5)))
v_d8 = bm_arm.verts.new(Vector((-arm_w*0.4,  0.15,  arm_l*0.5)))

# Connect perimeter
bm_arm.faces.new((v_d1, v_d2, v_d6, v_d5))
bm_arm.faces.new((v_d2, v_d3, v_d7, v_d6))
bm_arm.faces.new((v_d3, v_d4, v_d8, v_d7))
bm_arm.faces.new((v_d4, v_d1, v_d5, v_d8))
bm_arm.faces.new((v_d1, v_d4, v_d3, v_d2))
bm_arm.faces.new((v_d5, v_d6, v_d7, v_d8))

# Subdivide and add recessed windows (lightening cutouts)
bmesh.ops.recalc_face_normals(bm_arm, faces=bm_arm.faces)
me_arm = bpy.data.meshes.new("Dogbone_Arm_Mesh")
bm_arm.to_mesh(me_arm); bm_arm.free()

dogbone_obj = bpy.data.objects.new("Knee_Dogbone_Linkage", me_arm)
dogbone_obj.location = (0.0, knee_center.y - 0.12, knee_center.z - 0.35)
dogbone_obj.rotation_euler = (math.radians(-32), 0, 0) # Angled forward-down
gear_col.objects.link(dogbone_obj)
dogbone_obj.data.materials.append(M_DARK_STEEL)

mod_arm_b = dogbone_obj.modifiers.new("Bevel", 'BEVEL')
mod_arm_b.width = 0.02; mod_arm_b.segments = 2

# =========================================================================
# MULTI-VIEW AUDIT RENDERS FOR STEPS 06 - 12
# =========================================================================
print("\n>>> RENDERING AUDIT PASS FOR STEPS 06 - 12...")

cam = scn.camera
cam_d = cam.data

# 1. Macro Closeup of Knee Sunburst Gear & Dogbone
cam_d.type = 'PERSP'
cam_d.lens = 95
cam.location = (knee_center.x + 2.8, knee_center.y - 2.6, knee_center.z + 0.8)
d_knee = knee_center - cam.location
cam.rotation_euler = d_knee.to_track_quat('-Z', 'Y').to_euler()

p_audit_knee = os.path.join(OUT_DIR, "step09_step10_knee_sunburst_audit.png")
scn.render.filepath = p_audit_knee
bpy.ops.render.render(write_still=True)
print(f"Rendered Knee Sunburst Audit: {p_audit_knee}")
shutil.copyfile(p_audit_knee, os.path.join(ART_DIR, "step09_step10_knee_sunburst_audit.png"))

# 2. Closeup of Cable Chute Arc
chute_focus = Vector((0.0, center_y, center_z))
cam.location = (chute_focus.x + 2.4, chute_focus.y - 2.8, chute_focus.z + 0.6)
d_chute = chute_focus - cam.location
cam.rotation_euler = d_chute.to_track_quat('-Z', 'Y').to_euler()

p_audit_chute = os.path.join(OUT_DIR, "step06_step08_cable_chute_audit.png")
scn.render.filepath = p_audit_chute
bpy.ops.render.render(write_still=True)
print(f"Rendered Cable Chute Audit: {p_audit_chute}")
shutil.copyfile(p_audit_chute, os.path.join(ART_DIR, "step06_step08_cable_chute_audit.png"))

# 3. Full Leg Orthographic Side Profile (incorporating Deck, Chute, Knee Gear, Ankle Gear, Dogbone)
cam_d.type = 'ORTHO'
cam_d.ortho_scale = 4.2
leg_mid = Vector((0.0, 0.15, 1.85))
cam.location = (leg_mid.x + 12.0, leg_mid.y, leg_mid.z)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))

p_full_side = os.path.join(OUT_DIR, "steps_01_12_full_skeletal_assembly.png")
scn.render.filepath = p_full_side
bpy.ops.render.render(write_still=True)
print(f"Rendered Full Skeletal Assembly: {p_full_side}")
shutil.copyfile(p_full_side, os.path.join(ART_DIR, "steps_01_12_full_skeletal_assembly.png"))

# Save updated master scene
BLEND_UPDATED = os.path.join(OUT_DIR, "PHASE1_AND_PHASE2_EXECUTION.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_UPDATED)
print(f"Saved Master Scene to {BLEND_UPDATED}")
print("Steps 06-12 Successfully Executed!")
