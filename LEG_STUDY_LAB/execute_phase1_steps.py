import bpy
import bmesh
import math
import os
import json
import shutil
from mathutils import Vector, Matrix

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
GLB_PATH = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Mech_gameready-220d9957\Mech_gameready.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB_PATH)

leg_objs = [o for o in scn.objects if o.type == 'MESH' and 'legs' in o.name.lower()]
print(f"Total leg objects in Mech_gameready: {len(leg_objs)}")

# =========================================================================
# STEP 01: KINEMATIC MATRIX & DEGREES OF FREEDOM (DoF)
# =========================================================================
print("\n>>> EXECUTING STEP 01: Kinematic Matrix & Pivot Axes...")

# Compute bounding boxes and centroids of each object
parts_data = []
for o in leg_objs:
    mw = o.matrix_world
    pts = [mw @ Vector(c) for c in o.bound_box]
    c_min = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    c_max = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (c_min + c_max) / 2.0
    dim = c_max - c_min
    
    parts_data.append({
        'name': o.name,
        'center': (round(center.x, 3), round(center.y, 3), round(center.z, 3)),
        'dims': (round(dim.x, 3), round(dim.y, 3), round(dim.z, 3)),
        'verts': len(o.data.vertices),
        'faces': len(o.data.polygons),
        'min_z': round(c_min.z, 3),
        'max_z': round(c_max.z, 3)
    })

# Group into height tiers:
# Hip: Z > 2.8
# Thigh: 2.0 <= Z <= 3.2
# Knee: 1.5 <= Z <= 2.2
# Shin/Calf: 0.8 <= Z <= 1.8
# Ankle & Foot: Z < 0.9

hip_parts = [p for p in parts_data if p['center'][2] >= 2.7]
thigh_parts = [p for p in parts_data if 2.0 <= p['center'][2] < 2.7]
knee_parts = [p for p in parts_data if 1.4 <= p['center'][2] < 2.0 and p['center'][1] < 0.4]
shin_parts = [p for p in parts_data if 0.8 <= p['center'][2] < 1.6 and p['center'][1] > 0.0]
foot_parts = [p for p in parts_data if p['center'][2] < 0.8]

print(f"Hierarchical Grouping:")
print(f"  - Hip Group: {len(hip_parts)} parts")
print(f"  - Thigh Group: {len(thigh_parts)} parts")
print(f"  - Knee & Actuator Group: {len(knee_parts)} parts")
print(f"  - Shin & Deflector Group: {len(shin_parts)} parts")
print(f"  - Foot & Outrigger Group: {len(foot_parts)} parts")

# =========================================================================
# STEP 02: BOUNDING VOLUMES & CLEARANCE ENVELOPES
# =========================================================================
print("\n>>> EXECUTING STEP 02: Bounding Volumes & Collision Envelopes...")

# Find primary pivot points
# Pelvis / Hip Pivot:
p_hip = Vector((0.0, 0.0, 3.20)) # approximate
if hip_parts:
    p_hip = Vector((sum(p['center'][0] for p in hip_parts)/len(hip_parts),
                    sum(p['center'][1] for p in hip_parts)/len(hip_parts),
                    sum(p['center'][2] for p in hip_parts)/len(hip_parts)))

# Knee Pivot:
p_knee = Vector((0.0, 0.0, 1.85))
if knee_parts:
    p_knee = Vector((sum(p['center'][0] for p in knee_parts)/len(knee_parts),
                     sum(p['center'][1] for p in knee_parts)/len(knee_parts),
                     sum(p['center'][2] for p in knee_parts)/len(knee_parts)))

# Ankle Pivot:
p_ankle = Vector((0.0, 0.0, 0.85))
if foot_parts:
    ankle_cands = [p for p in foot_parts if p['center'][2] > 0.4]
    if ankle_cands:
        p_ankle = Vector((sum(p['center'][0] for p in ankle_cands)/len(ankle_cands),
                          sum(p['center'][1] for p in ankle_cands)/len(ankle_cands),
                          sum(p['center'][2] for p in ankle_cands)/len(ankle_cands)))

print(f"Pivots Extracted:")
print(f"  Hip Pivot Vector:   {p_hip}")
print(f"  Knee Pivot Vector:  {p_knee}")
print(f"  Ankle Pivot Vector: {p_ankle}")

thigh_vec = p_knee - p_hip
shin_vec = p_ankle - p_knee
print(f"Thigh Bone Vector: Length = {thigh_vec.length:.3f}m, Direction = {thigh_vec.normalized()}")
print(f"Shin Bone Vector:  Length = {shin_vec.length:.3f}m, Direction = {shin_vec.normalized()}")

# =========================================================================
# STEP 03: TOPOLOGICAL DECOMPOSITION & LAYER COLOR CODING
# =========================================================================
print("\n>>> EXECUTING STEP 03: Layer Color Coding & Functional ID Map...")

# Layer 1: Skeletal Hubs & Gears (Gold)
# Layer 2: Hydraulics & Actuators (Cyan)
# Layer 3: Secondary Sub-systems & Accumulators (Orange)
# Layer 4: Structural Armor Shells (Olive / Grey)

def make_layer_mat(name, rgb, rough=0.35, metal=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

M_L1_GEARS   = make_layer_mat("L1_Gears_Gold", (0.95, 0.75, 0.15))
M_L2_HYDRO   = make_layer_mat("L2_Hydro_Cyan", (0.10, 0.75, 0.95), metal=0.95, rough=0.15)
M_L3_SUBSYS  = make_layer_mat("L3_Subsys_Orange", (0.95, 0.45, 0.10))
M_L4_ARMOR   = make_layer_mat("L4_Armor_Olive", (0.55, 0.58, 0.45), metal=0.35, rough=0.45)

for o in leg_objs:
    o.data.materials.clear()
    n = o.name.lower()
    if 'cylinder' in n or 'nurbspath' in n:
        # Shafts, cylinders, pipes, gears
        if any(k in n for k in ['40', '41', '44', '45', '46']):
            o.data.materials.append(M_L1_GEARS)
        else:
            o.data.materials.append(M_L2_HYDRO)
    elif 'plane' in n:
        o.data.materials.append(M_L3_SUBSYS)
    else:
        o.data.materials.append(M_L4_ARMOR)

# Hide non-leg
for o in scn.objects:
    if o not in leg_objs and o.type == 'MESH':
        o.hide_render = True

# Studio Setup
world = bpy.data.worlds.new("World_IDMap")
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.10, 0.12, 0.16, 1.0)
scn.world = world

sun = bpy.data.lights.new("Sun_ID", 'SUN')
sun.energy = 4.5
so = bpy.data.objects.new("Sun_ID", sun)
so.rotation_euler = (math.radians(55), math.radians(20), math.radians(70))
scn.collection.objects.link(so)

rim = bpy.data.lights.new("Rim_ID", 'SUN')
rim.energy = 3.5; rim.color = (0.4, 0.7, 1.0)
ro = bpy.data.objects.new("Rim_ID", rim)
ro.rotation_euler = (math.radians(-40), math.radians(-30), math.radians(-110))
scn.collection.objects.link(ro)

# Focus Target
leg_pts = [o.matrix_world @ Vector(c) for o in leg_objs for c in o.bound_box]
lx_min, lx_max = min(p.x for p in leg_pts), max(p.x for p in leg_pts)
ly_min, ly_max = min(p.y for p in leg_pts), max(p.y for p in leg_pts)
lz_min, lz_max = min(p.z for p in leg_pts), max(p.z for p in leg_pts)
l_center = Vector(((lx_min+lx_max)/2, (ly_min+ly_max)/2, (lz_min+lz_max)/2))
l_h = lz_max - lz_min
l_w = lx_max - lx_min

cam_d = bpy.data.cameras.new("Cam_ID")
cam_d.type = 'ORTHO'
cam_d.ortho_scale = l_h * 1.18
cam_o = bpy.data.objects.new("Cam_ID", cam_d)
scn.collection.objects.link(cam_o)
scn.camera = cam_o

cam_o.location = (l_center.x + l_w * 4.0 + 8.0, l_center.y, l_center.z)
cam_o.rotation_euler = (math.radians(90), 0, math.radians(90))

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1400
scn.render.resolution_y = 1600

# Render Step 03: Layer Color Coding
p_idmap = os.path.join(OUT_DIR, "step03_layer_color_coded_id_map.png")
scn.render.filepath = p_idmap
bpy.ops.render.render(write_still=True)
print(f"Rendered Step 03 ID Map: {p_idmap}")
shutil.copyfile(p_idmap, os.path.join(ART_DIR, "step03_layer_color_coded_id_map.png"))

# =========================================================================
# STEP 04: BUILD MASTER PELVIS MOUNTING DECK WITH LIGHTENING POCKETS
# =========================================================================
print("\n>>> EXECUTING STEP 04: Procedural Pelvis Cantilever Mounting Deck...")

# Build procedural high-fidelity Pelvis Deck in bmesh
# Based on the true coordinates of the upper hip bracket:
# Location: around l_center.x, l_center.y - 0.25, lz_max - 0.4
deck_w = 1.60; deck_d = 2.40; deck_h = 0.55

bm = bmesh.new()
# Hexagonal/faceted cantilever deck profile in XY
deck_pts_xy = [
    ( deck_w*0.5, -deck_d*0.35), # Rear right
    ( deck_w*0.5,  deck_d*0.25), # Mid right
    ( deck_w*0.35, deck_d*0.50), # Front right chamfer
    (-deck_w*0.35, deck_d*0.50), # Front left chamfer
    (-deck_w*0.5,  deck_d*0.25), # Mid left
    (-deck_w*0.5, -deck_d*0.35), # Rear left
    ( 0.00,        -deck_d*0.50)  # Rear keel
]

v_low = [bm.verts.new(Vector((x, y, -deck_h*0.5))) for x, y in deck_pts_xy]
v_top = [bm.verts.new(Vector((x*0.88, y*0.92, deck_h*0.5))) for x, y in deck_pts_xy] # Angled taper

n_d = len(deck_pts_xy)
for i in range(n_d):
    nxt = (i + 1) % n_d
    bm.faces.new((v_low[i], v_low[nxt], v_top[nxt], v_top[i]))
    
bm.faces.new(reversed(v_low))
bm.faces.new(v_top)

# Inset lightening pockets (выборки облегчения веса) on top face
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
top_faces = [f for f in bm.faces if f.normal.z > 0.8]
if top_faces:
    res = bmesh.ops.inset_individual(bm, faces=top_faces, thickness=0.15, depth=-0.12)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me_deck = bpy.data.meshes.new("Procedural_Pelvis_Deck_Mesh")
bm.to_mesh(me_deck); bm.free()

deck_loc = Vector((l_center.x, l_center.y - 0.35, lz_max - 0.35))
obj_deck = bpy.data.objects.new("Procedural_Pelvis_Deck", me_deck)
obj_deck.location = deck_loc
scn.collection.objects.link(obj_deck)
obj_deck.data.materials.append(M_L4_ARMOR)

# Bevel modifier
mod_b = obj_deck.modifiers.new("Bevel", 'BEVEL')
mod_b.width = 0.035; mod_b.segments = 2; mod_b.limit_method = 'ANGLE'

# 8 M16 structural mounting studs on the deck
for i in range(8):
    ang = i * (2 * math.pi / 8.0)
    bx = deck_loc.x + 0.55 * math.cos(ang)
    by = deck_loc.y + 0.75 * math.sin(ang)
    bz = deck_loc.z + deck_h * 0.5 + 0.03
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.045, depth=0.08,
                                        location=(bx, by, bz))
    bolt = bpy.context.object; bolt.name = f"Deck_Bolt_{i}"
    bolt.data.materials.append(M_L1_GEARS)

# =========================================================================
# STEP 05: CRITICAL COMPARATIVE AUDIT & VERIFICATION SHEET
# =========================================================================
print("\n>>> EXECUTING STEP 05: Critical Comparative Audit Render...")

# Camera closeup on the Pelvis Mount Deck
cam_d.type = 'PERSP'
cam_d.lens = 85
cam_o.location = (deck_loc.x + 3.8, deck_loc.y - 4.2, deck_loc.z + 2.2)
d_target = deck_loc - cam_o.location
cam_o.rotation_euler = d_target.to_track_quat('-Z', 'Y').to_euler()

p_deck = os.path.join(OUT_DIR, "step04_step05_pelvis_deck_audit.png")
scn.render.filepath = p_deck
bpy.ops.render.render(write_still=True)
print(f"Rendered Step 04-05 Audit: {p_deck}")
shutil.copyfile(p_deck, os.path.join(ART_DIR, "step04_step05_pelvis_deck_audit.png"))

# Save Scene
blend_phase1 = os.path.join(OUT_DIR, "PHASE1_PIPELINE_EXECUTION.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_phase1)
print(f"Saved Phase 1 Blend to {blend_phase1}")

# Export kinematic data JSON
kinematic_report = {
    'phase': 'PHASE_I',
    'steps_completed': ['01', '02', '03', '04', '05'],
    'pivots': {
        'hip': [round(v, 4) for v in p_hip],
        'knee': [round(v, 4) for v in p_knee],
        'ankle': [round(v, 4) for v in p_ankle]
    },
    'thigh_bone_length': round(thigh_vec.length, 4),
    'shin_bone_length': round(shin_vec.length, 4),
    'deck_dimensions': [deck_w, deck_d, deck_h],
    'deck_bolts_count': 8,
    'total_master_parts': len(leg_objs)
}

with open(os.path.join(OUT_DIR, "phase1_kinematic_data.json"), "w") as f:
    json.dump(kinematic_report, f, indent=2)

print("Phase I (Steps 01-05) Successfully Executed!")

