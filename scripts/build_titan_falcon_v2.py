import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

# ----------------- PATHS & SETUP -----------------
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\TITAN_FALCON_WALKER"
ARTIFACT_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BLEND_FILE = os.path.join(OUT_DIR, "TITAN_FALCON_V2.blend")
HERO_RENDER = os.path.join(OUT_DIR, "titan_falcon_v2_hero.png")
SHEET_RENDER = os.path.join(OUT_DIR, "titan_falcon_v2_sheet.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

col_main = bpy.data.collections.new('TITAN_MECH_V2')
col_cutters = bpy.data.collections.new('CUTTERS')
scn.collection.children.link(col_main)
scn.collection.children.link(col_cutters)

def link(o, col=col_main):
    col.objects.link(o)
    return o

# ----------------- ADVANCED HARD-SURFACE MATERIALS -----------------
def create_mat(name, rgb, rough=0.35, metal=0.7, emit=None, strength=10.0, coat=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (*rgb, 1.0)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if 'Coat Weight' in b.inputs:
            b.inputs['Coat Weight'].default_value = coat
        if emit:
            b.inputs['Emission Color'].default_value = (*emit, 1.0)
            b.inputs['Emission Strength'].default_value = strength
    return m

# High-Contrast Tactical PBR Palette
M_BALLISTIC_DARK = create_mat('M_BallisticDark', (0.035, 0.040, 0.050), rough=0.25, metal=0.85, coat=0.4)
M_ARMOR_WHITE = create_mat('M_ArmorWhite', (0.82, 0.84, 0.86), rough=0.28, metal=0.40, coat=0.6)
M_CARBON_ACCENT = create_mat('M_CarbonAccent', (0.015, 0.018, 0.022), rough=0.18, metal=0.5, coat=1.0)
M_CHASSIS_GUNMETAL = create_mat('M_ChassisGunmetal', (0.15, 0.16, 0.18), rough=0.38, metal=0.95)
M_HYDRAULIC_GOLD = create_mat('M_HydraulicGold', (0.88, 0.68, 0.20), rough=0.10, metal=1.0)
M_STEEL_CHROME = create_mat('M_SteelChrome', (0.72, 0.74, 0.76), rough=0.15, metal=0.98)
M_SENSOR_CYAN = create_mat('M_SensorCyan', (0.01, 0.12, 0.22), rough=0.04, metal=0.05, emit=(0.08, 0.90, 1.0), strength=15.0)
M_EXHAUST_ORANGE = create_mat('M_ExhaustOrange', (0.18, 0.04, 0.01), rough=0.15, metal=0.2, emit=(1.0, 0.38, 0.02), strength=18.0)
M_HAZARD_YELLOW = create_mat('M_HazardYellow', (0.85, 0.75, 0.08), rough=0.30, metal=0.3)

def set_mat(o, mat):
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o

def hs_finish(o, bevel_width=0.0014, segments=2):
    for p in o.data.polygons:
        p.use_smooth = True
    mod = o.modifiers.new('Bevel', 'BEVEL')
    mod.width = bevel_width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(35)
    return o

def make_cylinder(name, r, h, loc, rot=(0,0,0), verts=32, mat=M_CHASSIS_GUNMETAL, bevel=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    set_mat(o, mat)
    if bevel:
        hs_finish(o, bevel_width=max(0.0006, r * 0.08))
    return o

def make_box(name, dims, loc, rot=(0,0,0), mat=M_BALLISTIC_DARK, bevel=0.0018):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(scale=True)
    set_mat(o, mat)
    if bevel > 0:
        hs_finish(o, bevel_width=bevel)
    return o

# Bolt generator
def make_bolt(name, loc, rot=(0,0,0), r=0.0022, h=0.0018, mat=M_STEEL_CHROME):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    set_mat(o, mat)
    return o

# ----------------- 1. PELVIS TURNTABLE & MULTI-CHAMBER CARRIAGE -----------------
print("V2: Constructing Reinforced Pelvis Turntable & Power Turbine...")
turntable_z = 0.125

# Azimuth ring with gear teeth collar
ring_outer = make_cylinder("Pelvis_RingOuter", r=0.042, h=0.016, loc=(0, 0, turntable_z), mat=M_CHASSIS_GUNMETAL)
ring_inner = make_cylinder("Pelvis_RingInner", r=0.034, h=0.022, loc=(0, 0, turntable_z), mat=M_STEEL_CHROME)
ring_teeth = make_cylinder("Pelvis_RingGear", r=0.037, h=0.018, loc=(0, 0, turntable_z), verts=48, mat=M_BALLISTIC_DARK)

# Main Underbelly Chassis Cradle (Armored box with angled chamfers)
cradle = make_box("Chassis_Cradle", dims=(0.076, 0.058, 0.024), loc=(0, -0.006, turntable_z - 0.015), mat=M_BALLISTIC_DARK, bevel=0.0035)

# Heavy Dual Turbine Engines on Chassis Rear
for sx in (-1, 1):
    ex_x = sx * 0.022
    turbine = make_cylinder(f"Rear_Turbine_{'R' if sx>0 else 'L'}", r=0.014, h=0.048, loc=(ex_x, 0.028, turntable_z - 0.004), rot=(math.radians(90), 0, 0), mat=M_CHASSIS_GUNMETAL)
    # Glowing exhaust thrust cone
    nozzle = make_cylinder(f"Rear_NozzleGlow_{'R' if sx>0 else 'L'}", r=0.010, h=0.008, loc=(ex_x, 0.054, turntable_z - 0.004), rot=(math.radians(90), 0, 0), mat=M_EXHAUST_ORANGE)
    # Heat-shield cowl
    cowl = make_box(f"Turbine_Cowl_{'R' if sx>0 else 'L'}", dims=(0.024, 0.035, 0.006), loc=(ex_x, 0.030, turntable_z + 0.012), mat=M_ARMOR_WHITE, bevel=0.0015)

# ----------------- 2. PREDATOR COCKPIT PENTHOUSE WITH MULTI-LAYER ARMOR -----------------
print("V2: Generating Aerodynamic Falcon Cockpit & Multi-Plate Shell...")

def falcon_point(u, v):
    s, c = math.sin(v), math.cos(v)
    front = math.cos(u)
    side = math.sin(u)
    
    # Base aerodynamic proportions
    z = (0.062 if c > 0 else 0.044) * c
    x = 0.056 * s * side
    ry = 0.088 if front > 0 else 0.068
    y = -ry * s * front
    
    # Razor-sharp forward beak canted downward
    if front > 0:
        beak = 0.032 * (front**2.5) * math.exp(-((x / 0.020)**2))
        y -= beak
        z += 0.012 * c * math.exp(-((x / 0.022)**2))
        if z < 0.01:
            z -= 0.015 * front * math.exp(-((x / 0.018)**2)) # downward predatory droop
            
    # Lateral air intake cheek sponsons
    if abs(side) > 0.35 and c < 0.3:
        flare = 0.015 * (abs(side)**2)
        x += math.copysign(flare, side)
        
    # Underbelly chin recession
    if z < 0:
        k = -z / 0.044
        x *= (1.0 - 0.38 * (k**1.2))
        if front > 0:
            y -= 0.016 * k
            
    return Vector((x, y, z))

def generate_falcon_hull(nu=112, nv=56):
    bm = bmesh.new()
    rows = []
    for j in range(1, nv):
        v = math.pi * j / nv
        rows.append([bm.verts.new(falcon_point(2 * math.pi * i / nu, v)) for i in range(nu)])
    top = bm.verts.new(falcon_point(0, 0))
    bot = bm.verts.new(falcon_point(0, math.pi))
    
    for j in range(len(rows) - 1):
        for i in range(nu):
            a, b = rows[j][i], rows[j][(i + 1) % nu]
            c_, d = rows[j + 1][(i + 1) % nu], rows[j + 1][i]
            bm.faces.new((a, d, c_, b))
    for i in range(nu):
        bm.faces.new((top, rows[0][i], rows[0][(i + 1) % nu]))
        bm.faces.new((bot, rows[-1][(i + 1) % nu], rows[-1][i]))
        
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('Cockpit_Hull_V2_Mesh')
    bm.to_mesh(me)
    bm.free()
    
    for p in me.polygons:
        p.use_smooth = True
        
    obj = link(bpy.data.objects.new('Cockpit_Base_Hull', me))
    obj.location = (0, 0.015, turntable_z + 0.054)
    set_mat(obj, M_BALLISTIC_DARK)
    hs_finish(obj, bevel_width=0.0014)
    return obj

hull = generate_falcon_hull()

# V2: Layered White Composite Armor Plates (Floating with real 3mm gap!)
# Plate A: Dorsal Crest Spine Plate
crest_plate = make_box("Armor_DorsalCrest", dims=(0.038, 0.082, 0.009), loc=(0, 0.018, turntable_z + 0.104), rot=(math.radians(-12), 0, 0), mat=M_ARMOR_WHITE, bevel=0.0018)

# Plate B: Forehead Brow Visor Hood
visor_hood = make_box("Armor_ForeheadHood", dims=(0.046, 0.036, 0.008), loc=(0, -0.045, turntable_z + 0.078), rot=(math.radians(24), 0, 0), mat=M_ARMOR_WHITE, bevel=0.0015)

# Primary Panoramic Targeting Sensor Visor (Glowing Cyan Glass)
main_visor = make_box("Sensor_MainVisor", dims=(0.042, 0.014, 0.008), loc=(0, -0.058, turntable_z + 0.062), rot=(math.radians(22), 0, 0), mat=M_SENSOR_CYAN, bevel=0.0008)

# Secondary Triple Sensor Cluster (Left, Center, Right telemetric aperture eyes)
for eye_i, eye_x in enumerate((-0.016, 0.0, 0.016)):
    eye_bezel = make_cylinder(f"Eye_Bezel_{eye_i}", r=0.0055, h=0.006, loc=(eye_x, -0.065, turntable_z + 0.048), rot=(math.radians(72), 0, 0), mat=M_STEEL_CHROME)
    eye_lens = make_cylinder(f"Eye_Lens_{eye_i}", r=0.0035, h=0.007, loc=(eye_x, -0.067, turntable_z + 0.048), rot=(math.radians(72), 0, 0), mat=M_SENSOR_CYAN)

# Lateral Flared Cheek Armor Plates with Ventilation Slots
for sx in (-1, 1):
    side_sfx = 'R' if sx > 0 else 'L'
    cheek_plate = make_box(f"Armor_CheekPlate_{side_sfx}", dims=(0.014, 0.068, 0.032), loc=(sx * 0.054, 0.012, turntable_z + 0.050), rot=(0, sx * math.radians(18), math.radians(4)), mat=M_ARMOR_WHITE, bevel=0.0018)
    
    # Recessed Carbon Fiber Intake Grille
    grille = make_box(f"Intake_Grille_{side_sfx}", dims=(0.005, 0.042, 0.016), loc=(sx * 0.061, 0.014, turntable_z + 0.052), rot=(0, sx * math.radians(18), 0), mat=M_CARBON_ACCENT)
    
    # Decorative Hex Bolts along plate edge
    for b_idx, b_y in enumerate((-0.015, 0.010, 0.035)):
        make_bolt(f"Cheek_Bolt_{side_sfx}_{b_idx}", loc=(sx * 0.062, b_y, turntable_z + 0.066), rot=(0, math.radians(90), 0))

# ----------------- 3. REINFORCED 3-SEGMENT AVIAN DIGITIGRADE LEGS -----------------
print("V2: Engineering 3-Segment Bridge-Truss Legs, Dual Pistons & Stabilizer Claws...")

for sx in (-1, 1):
    sfx = 'R' if sx > 0 else 'L'
    
    hip_pt = Vector((sx * 0.042, -0.006, turntable_z - 0.012))
    knee_pt = Vector((sx * 0.054, 0.044, turntable_z - 0.060))   # Forward cant
    hock_pt = Vector((sx * 0.046, -0.035, turntable_z - 0.120))  # Backward hock
    foot_pt = Vector((sx * 0.046, 0.008, 0.005))
    
    # A. Hip Rotary Hub & Heavy Bolted Flange
    hip_hub = make_cylinder(f"Hip_Hub_{sfx}", r=0.016, h=0.022, loc=hip_pt, rot=(0, math.radians(90), 0), mat=M_CHASSIS_GUNMETAL)
    hip_flange = make_cylinder(f"Hip_Flange_{sfx}", r=0.020, h=0.006, loc=hip_pt + Vector((sx * 0.008, 0, 0)), rot=(0, math.radians(90), 0), mat=M_STEEL_CHROME)
    
    # B. Femur Upper Leg Pylon (Heavy structural column)
    f_dir = knee_pt - hip_pt
    f_len = f_dir.length
    f_mid = (hip_pt + knee_pt) / 2.0
    f_quat = Vector((0, 0, 1)).rotation_difference(f_dir)
    
    femur_core = make_box(f"Femur_Core_{sfx}", dims=(0.020, 0.028, f_len * 0.94), loc=f_mid, rot=f_quat.to_euler(), mat=M_CHASSIS_GUNMETAL, bevel=0.0022)
    
    # Femur Front Armor Plate with Beveled Chamfers
    femur_shield = make_box(f"Femur_Shield_{sfx}", dims=(0.024, 0.011, f_len * 0.78), loc=f_mid + f_quat @ Vector((0, -0.015, 0)), rot=f_quat.to_euler(), mat=M_ARMOR_WHITE, bevel=0.0016)
    
    # C. Dual Massive Knee Discs & Gimbal Pin
    knee_outer_disc = make_cylinder(f"Knee_OuterDisc_{sfx}", r=0.018, h=0.026, loc=knee_pt, rot=(0, math.radians(90), 0), mat=M_STEEL_CHROME)
    knee_inner_hub = make_cylinder(f"Knee_InnerHub_{sfx}", r=0.012, h=0.032, loc=knee_pt, rot=(0, math.radians(90), 0), mat=M_BALLISTIC_DARK)
    
    # D. Reverse Hock / Lower Shin (Truss Structure with Weight-Reduction Recess)
    t_dir = hock_pt - knee_pt
    t_len = t_dir.length
    t_mid = (knee_pt + hock_pt) / 2.0
    t_quat = Vector((0, 0, 1)).rotation_difference(t_dir)
    
    shin_truss = make_box(f"Tibia_BridgeTruss_{sfx}", dims=(0.018, 0.030, t_len * 0.96), loc=t_mid, rot=t_quat.to_euler(), mat=M_CHASSIS_GUNMETAL, bevel=0.002)
    
    # Front Shin Armor with Pocketing
    shin_armor = make_box(f"Tibia_Armor_{sfx}", dims=(0.022, 0.010, t_len * 0.82), loc=t_mid + t_quat @ Vector((0, 0.014, 0)), rot=t_quat.to_euler(), mat=M_ARMOR_WHITE, bevel=0.0015)
    
    # Triangular weight-reduction pocket cutout plate
    shin_pocket = make_box(f"Tibia_PocketAccent_{sfx}", dims=(0.014, 0.004, t_len * 0.45), loc=t_mid + t_quat @ Vector((0, 0.018, 0)), rot=t_quat.to_euler(), mat=M_CARBON_ACCENT)
    
    # E. Dual Parallel Hydraulic Shock Absorbers (Real High-Tech Kinematics)
    # Piston 1: Main Femur-to-Hock Cylinder
    p1_top = hip_pt + Vector((0, -0.016, -0.012))
    p1_bot = hock_pt + Vector((0, 0.014, 0.018))
    p1_dir = p1_bot - p1_top
    p1_len = p1_dir.length
    p1_quat = Vector((0, 0, 1)).rotation_difference(p1_dir)
    
    cyl1 = make_cylinder(f"Hydraulic_Cylinder1_{sfx}", r=0.006, h=p1_len * 0.56, loc=p1_top + p1_dir * 0.28, rot=p1_quat.to_euler(), mat=M_CHASSIS_GUNMETAL)
    rod1 = make_cylinder(f"Hydraulic_Rod1_{sfx}", r=0.0038, h=p1_len * 0.62, loc=p1_bot - p1_dir * 0.28, rot=p1_quat.to_euler(), mat=M_HYDRAULIC_GOLD)
    
    # Piston 2: Knee Rebound Stabilizer (Front auxiliary damper)
    p2_top = hip_pt + Vector((0, 0.014, -0.010))
    p2_bot = knee_pt + Vector((0, -0.010, -0.015))
    p2_dir = p2_bot - p2_top
    p2_len = p2_dir.length
    p2_quat = Vector((0, 0, 1)).rotation_difference(p2_dir)
    
    cyl2 = make_cylinder(f"Aux_Damper_Cyl_{sfx}", r=0.0042, h=p2_len * 0.55, loc=p2_top + p2_dir * 0.28, rot=p2_quat.to_euler(), mat=M_BALLISTIC_DARK)
    rod2 = make_cylinder(f"Aux_Damper_Rod_{sfx}", r=0.0026, h=p2_len * 0.60, loc=p2_bot - p2_dir * 0.28, rot=p2_quat.to_euler(), mat=M_STEEL_CHROME)
    
    # F. Ankle Gimbal Joint
    ankle_pin = make_cylinder(f"Ankle_Pin_{sfx}", r=0.014, h=0.022, loc=hock_pt, rot=(0, math.radians(90), 0), mat=M_STEEL_CHROME)
    
    # G. Articulated 3-Point Cleat Foundation (Heel Spike + Dual Splayed Claws)
    foot_center = Vector((hock_pt.x, 0.008, 0.006))
    foot_bed = make_box(f"Foot_ChassisBed_{sfx}", dims=(0.032, 0.052, 0.010), loc=foot_center, mat=M_BALLISTIC_DARK, bevel=0.002)
    
    # Heavy Anti-Recoil Heel Wedge with Ground Serrations
    heel_wedge = make_box(f"Heel_RecoilWedge_{sfx}", dims=(0.026, 0.028, 0.014), loc=(hock_pt.x, -0.042, 0.010), rot=(math.radians(28), 0, 0), mat=M_CHASSIS_GUNMETAL, bevel=0.002)
    
    # Dual Splayed Forward Toe Claws
    for toe_idx, toe_ang in enumerate((-16, 16)):
        t_x = hock_pt.x + (0.011 if toe_idx==1 else -0.011)
        t_claw = make_box(f"Toe_Claw_{sfx}_{toe_idx}", dims=(0.010, 0.042, 0.009), loc=(t_x, 0.036, 0.006), rot=(math.radians(-14), 0, math.radians(toe_ang)), mat=M_ARMOR_WHITE, bevel=0.0014)
        # Hydraulic toe tension actuator
        t_link = make_cylinder(f"Toe_Actuator_{sfx}_{toe_idx}", r=0.0028, h=0.020, loc=(t_x, 0.020, 0.014), rot=(math.radians(52), 0, 0), mat=M_HYDRAULIC_GOLD)

# ----------------- 4. MODULAR ROTARY TRIPLE-BARREL AUTOCANNON BATTERIES -----------------
print("V2: Assembling Modular Rotary Autocannon Batteries & Ammo Feeds...")

for sx in (-1, 1):
    sfx = 'R' if sx > 0 else 'L'
    gun_x = sx * 0.082
    gun_y = -0.014
    gun_z = turntable_z + 0.052
    
    # A. Shoulder Pivot Gimbal & Swivel Collar
    swivel = make_cylinder(f"Weapon_Swivel_{sfx}", r=0.016, h=0.020, loc=(gun_x - sx*0.014, gun_y, gun_z), rot=(0, math.radians(90), 0), mat=M_STEEL_CHROME)
    
    # B. Armored Breech Body & Ammo Feed Chamber
    breech_box = make_box(f"Cannon_BreechBox_{sfx}", dims=(0.022, 0.072, 0.030), loc=(gun_x, gun_y - 0.008, gun_z), mat=M_BALLISTIC_DARK, bevel=0.0025)
    
    # Top Armor Cover Plate on Breech
    breech_cover = make_box(f"Cannon_TopShield_{sfx}", dims=(0.024, 0.054, 0.006), loc=(gun_x, gun_y - 0.008, gun_z + 0.017), mat=M_ARMOR_WHITE, bevel=0.0012)
    
    # Lateral Heat Dissipation Vents
    for vi in range(5):
        vy = gun_y + 0.012 + vi * 0.006
        make_box(f"Gun_Vent_{sfx}_{vi}", dims=(0.026, 0.002, 0.024), loc=(gun_x, vy, gun_z), mat=M_CHASSIS_GUNMETAL, bevel=0.0005)
        
    # C. Rotary 3-Barrel Gatling Cluster!
    rotor_y = gun_y - 0.050
    rotor_hub = make_cylinder(f"Rotor_Hub_{sfx}", r=0.011, h=0.018, loc=(gun_x, rotor_y, gun_z), rot=(math.radians(90), 0, 0), mat=M_CHASSIS_GUNMETAL)
    
    # 3 Parallel Barrels placed at 120-degree intervals
    barrel_radius_offset = 0.0065
    for b_idx in range(3):
        b_ang = b_idx * (2 * math.pi / 3)
        bx = gun_x + barrel_radius_offset * math.cos(b_ang)
        bz = gun_z + barrel_radius_offset * math.sin(b_ang)
        by = gun_y - 0.098
        
        # Barrel Tube
        barrel_tube = make_cylinder(f"Gatling_Barrel_{sfx}_{b_idx}", r=0.0035, h=0.096, loc=(bx, by, bz), rot=(math.radians(90), 0, 0), verts=20, mat=M_CHASSIS_GUNMETAL)
        
        # Muzzle Compensator
        muzzle_tip = make_cylinder(f"Muzzle_Tip_{sfx}_{b_idx}", r=0.0048, h=0.016, loc=(bx, gun_y - 0.144, bz), rot=(math.radians(90), 0, 0), verts=20, mat=M_STEEL_CHROME)
        
    # Barrel Retention Disks (Spacer Rings)
    for ring_i, ry_offset in enumerate((-0.085, -0.125)):
        make_cylinder(f"Barrel_Ring_{sfx}_{ring_i}", r=0.012, h=0.004, loc=(gun_x, gun_y + ry_offset, gun_z), rot=(math.radians(90), 0, 0), verts=24, mat=M_BALLISTIC_DARK)
        
    # D. Heavy Flexible Segmented Power/Ammo Conduit (Braided Hose)
    cu = bpy.data.curves.new(f"Ammo_Conduit_{sfx}", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.0042
    cu.bevel_resolution = 4
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(2)
    
    p0 = Vector((sx * 0.040, 0.015, turntable_z + 0.008))
    p1 = Vector((sx * 0.072, 0.038, turntable_z + 0.032))
    p2 = Vector((gun_x, gun_y + 0.024, gun_z - 0.010))
    
    for idx, pt in enumerate((p0, p1, p2)):
        bp = sp.bezier_points[idx]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
        
    cable = bpy.data.objects.new(f"Ammo_Belt_{sfx}", cu)
    link(cable)
    set_mat(cable, M_CARBON_ACCENT)

# ----------------- 5. CINEMATIC 3-POINT STUDIO LIGHTING & RENDER -----------------
print("V2: Configuring High-Dynamic Sci-Fi Lighting & Renders...")

world = bpy.data.worlds.new("Titan_World_V2")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (0.015, 0.020, 0.028, 1.0)
    bg.inputs['Strength'].default_value = 0.9
scn.world = world

cam_data = bpy.data.cameras.new("Titan_Cam_V2")
cam_obj = bpy.data.objects.new("Titan_Cam_V2", cam_data)
scn.collection.objects.link(cam_obj)
scn.camera = cam_obj

# Key Light (Warm Sunlight)
sun_key = bpy.data.lights.new("Sun_Key", type='SUN')
sun_key.energy = 6.0
sun_key.color = (1.0, 0.97, 0.94)
obj_key = bpy.data.objects.new("Sun_Key", sun_key)
obj_key.rotation_euler = (math.radians(52), math.radians(22), math.radians(48))
scn.collection.objects.link(obj_key)

# Cyan Cyber Rim Light (Back-Angle)
sun_rim = bpy.data.lights.new("Sun_Rim", type='SUN')
sun_rim.energy = 4.8
sun_rim.color = (0.25, 0.80, 1.0)
obj_rim = bpy.data.objects.new("Sun_Rim", sun_rim)
obj_rim.rotation_euler = (math.radians(-38), math.radians(-28), math.radians(-130))
scn.collection.objects.link(obj_rim)

# Amber Ground Fill Light
sun_fill = bpy.data.lights.new("Sun_Fill", type='SUN')
sun_fill.energy = 2.2
sun_fill.color = (0.95, 0.55, 0.25)
obj_fill = bpy.data.objects.new("Sun_Fill", sun_fill)
obj_fill.rotation_euler = (math.radians(-65), math.radians(12), math.radians(85))
scn.collection.objects.link(obj_fill)

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1600
scn.render.resolution_y = 1200

target = Vector((0, -0.015, turntable_z + 0.028))

# 1. Hero Shot
cam_data.type = 'PERSP'
cam_data.lens = 68
cam_obj.location = (0.36, -0.42, turntable_z + 0.17)
d_vec = target - cam_obj.location
cam_obj.rotation_euler = d_vec.to_track_quat('-Z', 'Y').to_euler()

scn.render.filepath = HERO_RENDER
print("Rendering V2 Hero Beauty Shot...")
bpy.ops.render.render(write_still=True)

# 2. Orthographic 4-View Contact Renders
views = [
    ("titan_v2_1_front.png", (0, -0.48, target.z), (math.radians(90), 0, 0), True, 0.28),
    ("titan_v2_2_side.png", (0.48, 0, target.z), (math.radians(90), 0, math.radians(90)), True, 0.30),
    ("titan_v2_3_top.png", (0, 0, target.z + 0.48), (0, 0, 0), True, 0.28),
    ("titan_v2_4_rear34.png", (-0.36, 0.40, target.z + 0.16), (0,0,0), False, 0)
]

v2_renders = []
for fname, cloc, crot, is_ortho, oscale in views:
    cam_obj.location = cloc
    if is_ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = oscale
        cam_obj.rotation_euler = crot
    else:
        cam_data.type = 'PERSP'
        cam_data.lens = 58
        d_vec = target - cam_obj.location
        cam_obj.rotation_euler = d_vec.to_track_quat('-Z', 'Y').to_euler()
        
    out_p = os.path.join(OUT_DIR, fname)
    scn.render.filepath = out_p
    bpy.ops.render.render(write_still=True)
    v2_renders.append(out_p)

# Save .blend
bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
print(f"V2 Master Blend saved: {BLEND_FILE}")

# Copy to Artifact directory
import shutil
for p in [HERO_RENDER] + v2_renders:
    if os.path.exists(p):
        bn = os.path.basename(p)
        shutil.copyfile(p, os.path.join(ARTIFACT_DIR, bn))
        print(f"Copied V2 artifact: {bn}")

print("=== V2 GENERATION COMPLETE ===")

