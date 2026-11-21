import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BLEND_FILE = os.path.join(OUT_DIR, "MASTER_HARDSURFACE_LEG_V2.blend")

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

col_leg = bpy.data.collections.new('MASTER_HS_LEG')
scn.collection.children.link(col_leg)

def link(o):
    col_leg.objects.link(o)
    return o

# =========================================================================
# MATERIALS (Exact PBR matching user reference image)
# =========================================================================
def make_mat(name, rgb, rough=0.32, metal=0.75):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

# Exact colors from media_1794170243573_e02bfbb9.jpg:
M_OCHRE_ARMOR  = make_mat('M_OchreArmor', (0.76, 0.62, 0.28), rough=0.32, metal=0.45) # Thigh & Foot
M_PURPLE_ARMOR = make_mat('M_PurpleArmor', (0.58, 0.32, 0.68), rough=0.30, metal=0.45) # Shin & Knee
M_OLIVE_CUFF   = make_mat('M_OliveCuff', (0.70, 0.70, 0.42), rough=0.35, metal=0.40) # Ankle Collar
M_DARK_CHASSIS = make_mat('M_DarkChassis', (0.10, 0.11, 0.13), rough=0.40, metal=0.90) # Mechanical cores
M_STEEL_PINS   = make_mat('M_SteelPins', (0.80, 0.82, 0.85), rough=0.15, metal=0.98) # Bearing caps & shafts

def hs_finish(o, bevel_w=0.04, seg=2):
    for p in o.data.polygons: p.use_smooth = True
    mod = o.modifiers.new('Bevel', 'BEVEL')
    mod.width = bevel_w
    mod.segments = seg
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(35)
    return o

# World coordinate origin for the leg
X_LEG = 4.35

# =========================================================================
# 1. KNEE KNUCKLE LINKAGE (polySurface195 exact broken-line architecture)
# Not an oval! A double-crank industrial knuckle with stepped waist,
# recessed clearance slot, and dual-width beveled pivot heads!
# =========================================================================
def build_master_knee_knuckle():
    print("Building Master Knee Knuckle (True broken lines & stepped facets)...")
    bm = bmesh.new()
    
    # The master's exact 44-vertex knuckle coordinates (normalized to knee local center)
    # Knee center in world: (X_LEG, -2.11, 7.42)
    # Width: Upper head W = 1.84 (X = +/- 0.921), Lower head W = 1.49 (X = +/- 0.747)
    raw_verts = [
        (-0.747, -2.335, -0.348), ( 0.747, -2.335, -0.348),
        (-0.747, -2.691,  0.036), ( 0.747, -2.691,  0.036),
        ( 0.921,  0.600,  0.517), ( 0.747, -0.556,  1.502),
        ( 0.921,  0.600, -0.493), ( 0.747, -0.600,  0.493),
        (-0.921,  0.556, -1.502), (-0.747, -0.600, -0.517),
        (-0.921,  0.600, -0.493), (-0.747, -0.600,  0.493),
        ( 0.921,  1.846,  0.493), (-0.921,  0.600,  0.517),
        (-0.921,  1.846,  0.493), (-0.747, -1.846, -0.493),
        (-0.747, -1.801,  0.517), (-0.921,  1.801, -0.517),
        ( 0.747, -1.801,  0.517), ( 0.747, -0.600, -0.517),
        ( 0.747, -1.846, -0.493), (-0.921,  1.801, -1.526),
        ( 0.921,  0.556, -1.502), ( 0.921,  1.801, -1.526),
        ( 0.747, -1.801,  1.526), (-0.747, -1.801,  1.526),
        (-0.747, -0.556,  1.502), ( 0.921,  2.824, -0.541),
        (-0.921,  2.824, -0.541), ( 0.921,  2.691, -0.036),
        (-0.921,  2.691, -0.036), ( 0.921,  2.335,  0.348),
        (-0.921,  2.335,  0.348), ( 0.747, -2.291,  1.406),
        (-0.747, -2.291,  1.406), ( 0.747, -2.691,  1.045),
        (-0.747, -2.691,  1.045), ( 0.747, -2.824,  0.541),
        (-0.747, -2.824,  0.541), ( 0.921,  2.291, -1.406),
        (-0.921,  2.291, -1.406), ( 0.921,  2.691, -1.045),
        (-0.921,  2.691, -1.045), ( 0.921,  1.801, -0.517)
    ]
    
    # Exact face topology from the master's model
    raw_faces = [
        [0, 1, 2], [2, 1, 3], [4, 5, 6], [6, 5, 7], [8, 9, 10], [10, 9, 11],
        [4, 12, 13], [13, 12, 14], [9, 15, 11], [11, 15, 16], [13, 14, 10], [10, 14, 17],
        [7, 18, 19], [19, 18, 20], [8, 21, 22], [22, 21, 23], [24, 5, 25], [25, 5, 26],
        [15, 9, 20], [20, 9, 19], [5, 4, 26], [26, 4, 13], [27, 28, 29], [29, 28, 30],
        [29, 30, 31], [31, 30, 32], [31, 32, 12], [12, 32, 14], [24, 25, 33], [33, 25, 34],
        [33, 34, 35], [35, 34, 36], [35, 36, 37], [37, 36, 38], [37, 38, 3], [3, 38, 2],
        [22, 23, 8], [8, 23, 21], [39, 40, 41], [41, 40, 42], [41, 42, 27], [27, 42, 28],
        [6, 43, 4], [4, 43, 12], [17, 10, 43], [43, 10, 6], [23, 39, 43], [43, 39, 41],
        [21, 17, 40], [40, 17, 42], [18, 7, 0], [0, 7, 11], [1, 20, 3], [3, 20, 15],
        [16, 25, 2], [2, 25, 34], [18, 24, 1], [1, 24, 33], [26, 8, 25], [25, 8, 21],
        [22, 5, 23], [23, 5, 24], [14, 12, 28], [28, 12, 27], [16, 15, 36], [36, 15, 2],
        [18, 1, 35], [35, 1, 37], [10, 8, 6], [6, 8, 22], [7, 5, 19], [19, 5, 22],
        [11, 9, 16], [16, 9, 15], [4, 6, 12], [12, 6, 43], [14, 32, 17], [17, 32, 30],
        [30, 28, 42], [42, 28, 27], [37, 3, 35], [35, 3, 1], [38, 0, 36], [36, 0, 2]
    ]
    
    bm_verts = [bm.verts.new(Vector((vx, vy, vz))) for vx, vy, vz in raw_verts]
    for f_idx in raw_faces:
        try:
            bm.faces.new([bm_verts[i] for i in f_idx])
        except Exception:
            pass
            
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Master_Knee_Knuckle_Mesh")
    bm.to_mesh(me); bm.free()
    
    knuckle_obj = bpy.data.objects.new("Master_Knee_Knuckle", me)
    # Position in world space matching Vulture
    knuckle_obj.location = (X_LEG, -2.11, 7.42)
    link(knuckle_obj)
    knuckle_obj.data.materials.append(M_PURPLE_ARMOR)
    hs_finish(knuckle_obj, bevel_w=0.03, seg=2)
    
    # Add outer pivot bearing caps (distinct concentric rings, not flat circles)
    for side in (-1, 1):
        x_cap = X_LEG + side * (0.921 + 0.12)
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.68, depth=0.25, 
                                            location=(x_cap, -2.11 + 1.846, 7.42 + 0.493), 
                                            rotation=(0, math.radians(90), 0))
        cap1 = bpy.context.object; cap1.name = f"Knee_BearingCap_Upper_{side}"
        cap1.data.materials.append(M_STEEL_PINS); hs_finish(cap1, bevel_w=0.02); link(cap1)
        
        # Inset center hex bolt
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.32, depth=0.35,
                                            location=(x_cap + side * 0.05, -2.11 + 1.846, 7.42 + 0.493),
                                            rotation=(0, math.radians(90), 0))
        bolt1 = bpy.context.object; bolt1.name = f"Knee_HexBolt_Upper_{side}"
        bolt1.data.materials.append(M_DARK_CHASSIS); hs_finish(bolt1, bevel_w=0.015); link(bolt1)

    # Lower pivot bearing cap
    for side in (-1, 1):
        x_cap_low = X_LEG + side * (0.747 + 0.10)
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.55, depth=0.20,
                                            location=(x_cap_low, -2.11 - 1.846, 7.42 - 0.493),
                                            rotation=(0, math.radians(90), 0))
        cap2 = bpy.context.object; cap2.name = f"Knee_BearingCap_Lower_{side}"
        cap2.data.materials.append(M_STEEL_PINS); hs_finish(cap2, bevel_w=0.02); link(cap2)
        
    return knuckle_obj

# =========================================================================
# 2. MASTER THIGH (polySurface191 & polySurface200)
# Multi-tiered terraced architectural hull:
# - Raised central dorsal ridge
# - Recessed longitudinal service pocket
# - Raised structural border rails
# - 45-degree chamfered flanks
# - Sharp cantilever forward overhang with undercut shelf
# - Lower knee-docking cradle
# - Octagonal hip boss with nested socket bed
# =========================================================================
def build_master_thigh():
    print("Building Master Architectural Thigh (Multi-tier terraced armor)...")
    bm = bmesh.new()
    
    # 7 distinct width levels across X:
    # 0.0 (center), 0.35 (ridge), 0.86 (pocket), 1.35 (rail), 1.69 (chamfer), 2.03 (outer hull)
    
    # Key profile stations along (Y, Z) from top hip to lower knee cradle:
    # Top plate: (Y ~ 1.3, Z ~ 14.3)
    # Forward overhang tip: (Y ~ -4.7, Z ~ 12.1)
    # Undercut forward shelf: (Y ~ -6.5, Z ~ 10.4)
    # Front knee approach: (Y ~ -6.9, Z ~ 8.1)
    # Lower knee cradle: (Y ~ -3.3, Z ~ 6.85)
    # Rear hip taper: (Y ~ 1.4, Z ~ 11.8)
    
    # Let's construct the 3D terraced armor volume symmetrically:
    # We create cross-section ribs at distinct height stations Z
    stations = [
        # (Z_world, Y_front, Y_rear, Z_cradle_offset)
        (14.39, -1.92,  1.39, 0.0),   # Top hip mounting deck
        (13.42, -3.50,  1.37, 0.0),   # Upper hip expansion
        (12.08, -4.68,  0.80, 0.0),   # Sharp forward cantilever beak
        (10.59, -6.28, -0.40, 0.0),   # Undercut shelf & mid thigh
        ( 9.36, -6.88, -1.50, 0.0),   # Lower forward prow
        ( 8.06, -6.90, -2.43, 0.0),   # Knee hinge transition
        ( 6.85, -4.00, -3.29, 0.0)    # Knee docking cradle base
    ]
    
    # Build tiered perimeter rings for each station
    # Rib vertices at each station:
    # Outer hull: X = +/- 2.03
    # Bevel facet: X = +/- 1.69
    # Border rail: X = +/- 1.35
    # Recessed pocket: X = +/- 0.86 (sunken slightly in Y)
    # Ridge: X = 0.0 (protruding slightly in Y)
    
    st_verts = []
    for z_st, y_f, y_r, _ in stations:
        is_pocket_zone = (8.5 <= z_st <= 13.0)
        pocket_d = 0.28 if is_pocket_zone else 0.0
        ridge_p = 0.22
        
        # Ring of 12 vertices defining the cross-section
        pts = [
            # Front face (from +X to -X):
            ( 2.03, y_f, z_st),                     # 0: Outer Right Front
            ( 1.35, y_f + 0.08, z_st),              # 1: Right Border Rail
            ( 0.86, y_f + 0.08 - pocket_d, z_st),   # 2: Right Pocket Inset
            ( 0.00, y_f + 0.08 + ridge_p, z_st),    # 3: Center Dorsal Ridge
            (-0.86, y_f + 0.08 - pocket_d, z_st),   # 4: Left Pocket Inset
            (-1.35, y_f + 0.08, z_st),              # 5: Left Border Rail
            (-2.03, y_f, z_st),                     # 6: Outer Left Front
            # Rear face (from -X to +X):
            (-2.03, y_r, z_st),                     # 7: Outer Left Rear
            (-1.35, y_r - 0.05, z_st),              # 8: Left Rear Chamfer
            ( 0.00, y_r - 0.12, z_st),              # 9: Center Rear Spine
            ( 1.35, y_r - 0.05, z_st),              # 10: Right Rear Chamfer
            ( 2.03, y_r, z_st)                      # 11: Outer Right Rear
        ]
        ring = [bm.verts.new(Vector((px, py, pz))) for px, py, pz in pts]
        st_verts.append(ring)
        
    # Connect consecutive station rings with quads
    for s in range(len(stations) - 1):
        r1 = st_verts[s]
        r2 = st_verts[s + 1]
        n_pts = len(r1)
        for i in range(n_pts):
            nxt = (i + 1) % n_pts
            bm.faces.new((r1[i], r1[nxt], r2[nxt], r2[i]))
            
    # Cap top face
    bm.faces.new(st_verts[0])
    # Cap bottom face
    bm.faces.new(reversed(st_verts[-1]))
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Master_Thigh_Mesh")
    bm.to_mesh(me); bm.free()
    
    thigh_obj = bpy.data.objects.new("Master_Thigh", me)
    thigh_obj.location = (X_LEG, 0, 0)
    link(thigh_obj)
    thigh_obj.data.materials.append(M_OCHRE_ARMOR)
    hs_finish(thigh_obj, bevel_w=0.05, seg=2)
    
    # -------------------------------------------------------------
    # HIP BOSS (polySurface200): Nested Octagonal Turret Hub
    # -------------------------------------------------------------
    hub_loc = (X_LEG + 2.03 + 0.15, -0.59, 12.76)
    
    # Outer Octagonal Collar / Socket Bed
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.75, depth=0.55,
                                        location=hub_loc, rotation=(0, math.radians(90), 0))
    hub_socket = bpy.context.object; hub_socket.name = "Hip_OctagonalSocketBed"
    hub_socket.data.materials.append(M_OCHRE_ARMOR); hs_finish(hub_socket, bevel_w=0.06); link(hub_socket)
    
    # Inner Sunken Octagonal Core Plate
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.25, depth=0.85,
                                        location=(hub_loc[0] + 0.20, hub_loc[1], hub_loc[2]),
                                        rotation=(0, math.radians(90), 0))
    hub_core = bpy.context.object; hub_core.name = "Hip_OctagonalCorePlate"
    hub_core.data.materials.append(M_DARK_CHASSIS); hs_finish(hub_core, bevel_w=0.04); link(hub_core)
    
    # Center Circular Bearing Spindle & Steel Bolts
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.65, depth=1.05,
                                        location=(hub_loc[0] + 0.32, hub_loc[1], hub_loc[2]),
                                        rotation=(0, math.radians(90), 0))
    hub_pin = bpy.context.object; hub_pin.name = "Hip_CentralSpindle"
    hub_pin.data.materials.append(M_STEEL_PINS); hs_finish(hub_pin, bevel_w=0.025); link(hub_pin)
    
    # 8 Perimeter Hex Bolts on the Socket Bed
    for i in range(8):
        ang = i * (2 * math.pi / 8.0)
        by = hub_loc[1] + 1.45 * math.cos(ang)
        bz = hub_loc[2] + 1.45 * math.sin(ang)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.10, depth=0.65,
                                            location=(hub_loc[0] + 0.12, by, bz),
                                            rotation=(0, math.radians(90), 0))
        bolt = bpy.context.object; bolt.name = f"Hip_PerimeterBolt_{i}"
        bolt.data.materials.append(M_STEEL_PINS); hs_finish(bolt, bevel_w=0.01); link(bolt)
        
    return thigh_obj

# =========================================================================
# 3. MASTER SHIN (polySurface196)
# Advanced Hard-Surface Shin features:
# - Front faceted armor prow with double-beveled central dorsal spine
# - Lateral recessed service channels with 45-degree angled stop caps
# - Twin aerodynamic rear deflector fins with central hollow channel & chevron cutout
# - Upper rear stepped damper bracket housing with horizontal damper ribs
# =========================================================================
def build_master_shin():
    print("Building Master Architectural Shin (Deflector fins, dorsal spine, damper unit)...")
    bm = bmesh.new()
    
    # Stations along Z for the main shin body (from knee socket to ankle socket):
    # Z from 8.35 down to -0.54
    shin_stations = [
        # (Z_world, Y_front, Y_rear, has_fins)
        ( 8.35,  0.68, -1.21, False),  # Top knee socket cradle
        ( 7.48,  1.40, -2.04, False),  # Upper knee pivot neck
        ( 5.95,  2.25, -2.85, True),   # Deflector fin initiation
        ( 3.84,  1.68, -3.35, True),   # Deflector fin peak & chevron cut
        ( 1.73,  0.97, -3.71, True),   # Mid shin fin taper
        ( 0.50, -0.20, -3.60, False),  # Lower shin transition to ankle
        (-0.54, -1.71, -2.49, False)   # Ankle cuff pivot socket
    ]
    
    st_rings = []
    for z_st, y_f, y_r, has_fins in shin_stations:
        # Cross section profile:
        # Front spine at X=0, lateral pocket at X = +/- 1.05, outer hull at X = +/- 1.82
        # If has_fins is True, rear extends backwards into twin fins at X = +/- 0.90 to 1.35
        
        # Inset channel depth
        ch_d = 0.20 if (1.0 <= z_st <= 7.0) else 0.0
        
        pts = [
            # Front faceted prow (double beveled):
            ( 1.82, y_f, z_st),                     # 0: Right Front Outer
            ( 1.05, y_f + 0.12 - ch_d, z_st),       # 1: Right Channel Inset
            ( 0.45, y_f + 0.22, z_st),              # 2: Right Spine Crest
            ( 0.00, y_f + 0.28, z_st),              # 3: Center Prow Peak
            (-0.45, y_f + 0.22, z_st),              # 4: Left Spine Crest
            (-1.05, y_f + 0.12 - ch_d, z_st),       # 5: Left Channel Inset
            (-1.82, y_f, z_st),                     # 6: Left Front Outer
            # Flank & Rear:
            (-1.82, y_r, z_st),                     # 7: Left Rear Outer
            (-0.95, y_r - (0.95 if has_fins else 0.0), z_st), # 8: Left Fin Tip / Rear
            (-0.35, y_r - 0.10, z_st),              # 9: Central Rear Trench
            ( 0.35, y_r - 0.10, z_st),              # 10: Central Rear Trench
            ( 0.95, y_r - (0.95 if has_fins else 0.0), z_st), # 11: Right Fin Tip / Rear
            ( 1.82, y_r, z_st)                      # 12: Right Rear Outer
        ]
        ring = [bm.verts.new(Vector((px, py, pz))) for px, py, pz in pts]
        st_rings.append(ring)
        
    for s in range(len(shin_stations) - 1):
        r1 = st_rings[s]
        r2 = st_rings[s + 1]
        n_pts = len(r1)
        for i in range(n_pts):
            nxt = (i + 1) % n_pts
            bm.faces.new((r1[i], r1[nxt], r2[nxt], r2[i]))
            
    bm.faces.new(st_rings[0])
    bm.faces.new(reversed(st_rings[-1]))
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Master_Shin_Mesh")
    bm.to_mesh(me); bm.free()
    
    shin_obj = bpy.data.objects.new("Master_Shin", me)
    shin_obj.location = (X_LEG, 0, 0)
    link(shin_obj)
    shin_obj.data.materials.append(M_PURPLE_ARMOR)
    hs_finish(shin_obj, bevel_w=0.04, seg=2)
    
    # -------------------------------------------------------------
    # REAR HYDRAULIC DAMPER BRACKET & TRAVEL-STOP UNIT (polySurface192)
    # Right behind the knee knuckle: stepped horizontal rib pack
    # -------------------------------------------------------------
    damper_base_loc = (X_LEG, -0.14, 5.06)
    
    # Damper mounting bracket
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=damper_base_loc)
    d_brack = bpy.context.object; d_brack.name = "Shin_DamperBracket"
    d_brack.scale = (1.60, 2.20, 1.40); bpy.ops.object.transform_apply(scale=True)
    d_brack.data.materials.append(M_DARK_CHASSIS); hs_finish(d_brack, bevel_w=0.04); link(d_brack)
    
    # 3 Stepped Horizontal Cooling / Damper Ribs
    for i in range(3):
        rz = damper_base_loc[2] - 0.40 + i * 0.40
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.92, depth=0.15,
                                            location=(damper_base_loc[0], damper_base_loc[1] + 0.35, rz),
                                            rotation=(math.radians(90), 0, 0))
        rib = bpy.context.object; rib.name = f"Shin_DamperRib_{i}"
        rib.data.materials.append(M_PURPLE_ARMOR); hs_finish(rib, bevel_w=0.02); link(rib)
        
    return shin_obj

# =========================================================================
# 4. MASTER ANKLE CUFF (polySurface198)
# Real Horseshoe C-Clamp Wrap-Around Collar:
# - Front twin vertical clamp horns
# - Horizontal tie-bar cross members wrapping around shin pivot
# - Lateral circular/octagonal bearing pivot housings
# =========================================================================
def build_master_ankle_cuff():
    print("Building Master Ankle C-Clamp Collar (Twin horns, bearing caps)...")
    cuff_center = (X_LEG, -2.10, -0.20)
    
    # Main U-shaped clamping collar
    # Built using bmesh to create a true hollow C-clamp collar with front horns
    bm = bmesh.new()
    w_outer = 4.20; w_inner = 2.40 # Hollow collar width
    d_len = 3.60
    h_cuff = 1.40
    
    # Create the U-bracket profile in XY, extruded vertically in Z
    # Outer U points (counter-clockwise)
    pts_u = [
        ( w_outer*0.5, -d_len*0.5), # Rear right
        ( w_outer*0.5,  d_len*0.5), # Front right horn outer
        ( w_inner*0.5,  d_len*0.5 + 0.45), # Front right horn tip (raised horn)
        ( w_inner*0.5,  d_len*0.35), # Front right horn inner
        ( w_inner*0.5, -d_len*0.25), # Inner right pocket
        (-w_inner*0.5, -d_len*0.25), # Inner left pocket
        (-w_inner*0.5,  d_len*0.35), # Front left horn inner
        (-w_inner*0.5,  d_len*0.5 + 0.45), # Front left horn tip (raised horn)
        (-w_outer*0.5,  d_len*0.5), # Front left horn outer
        (-w_outer*0.5, -d_len*0.5), # Rear left
        ( 0.00,        -d_len*0.55) # Rear bridge center
    ]
    
    v_bot = [bm.verts.new(Vector((x, y, -h_cuff*0.5))) for x, y in pts_u]
    v_top = [bm.verts.new(Vector((x, y,  h_cuff*0.5))) for x, y in pts_u]
    
    n_u = len(pts_u)
    for i in range(n_u):
        nxt = (i + 1) % n_u
        bm.faces.new((v_bot[i], v_bot[nxt], v_top[nxt], v_top[i]))
        
    bm.faces.new(reversed(v_bot))
    bm.faces.new(v_top)
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Master_Ankle_Cuff_Mesh")
    bm.to_mesh(me); bm.free()
    
    cuff_obj = bpy.data.objects.new("Master_Ankle_Cuff", me)
    cuff_obj.location = cuff_center
    link(cuff_obj)
    cuff_obj.data.materials.append(M_OLIVE_CUFF)
    hs_finish(cuff_obj, bevel_w=0.05, seg=2)
    
    # Lateral Ankle Pivot Bearing Lugs (on left and right sides)
    for side in (-1, 1):
        x_lug = cuff_center[0] + side * (w_outer * 0.5 + 0.15)
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.62, depth=0.35,
                                            location=(x_lug, cuff_center[1], cuff_center[2]),
                                            rotation=(0, math.radians(90), 0))
        lug = bpy.context.object; lug.name = f"Ankle_BearingLug_{side}"
        lug.data.materials.append(M_DARK_CHASSIS); hs_finish(lug, bevel_w=0.03); link(lug)
        
        # Inset steel center pin
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.35, depth=0.45,
                                            location=(x_lug + side * 0.08, cuff_center[1], cuff_center[2]),
                                            rotation=(0, math.radians(90), 0))
        pin = bpy.context.object; pin.name = f"Ankle_CenterPin_{side}"
        pin.data.materials.append(M_STEEL_PINS); hs_finish(pin, bevel_w=0.015); link(pin)
        
    return cuff_obj

# =========================================================================
# 5. MASTER FOOT ASSEMBLY (polySurface189...206)
# Multi-Toe Outrigger Foot Architecture:
# - Central gimbal pivot hub
# - 4 Splayed Toes/Claws (2 front splayed claws, 2 rear splayed claws)
# - Each toe features:
#   * 3-tier stepped forward slope (terraced armor plating)
#   * Arched underside bridge (hollow ground clearance under the claw)
#   * Recessed stadium/capsule deboss pocket on both lateral flanks
#   * Sharp angled chisel-toe tip
# =========================================================================
def build_master_toe_claw(name, loc, rot_z):
    # Single master toe claw (length ~ 4.2m, width ~ 1.8m, height ~ 1.2m)
    bm = bmesh.new()
    
    # Profile along length Y and height Z (with 3-tier stepped forward slope and bottom arch)
    # Length: Y from 2.0 (hinge) to -2.2 (toe tip)
    toe_profile_yz = [
        # (Y, Z)
        ( 2.00,  0.45), # Hinge top rear
        ( 1.10,  0.55), # Tier 1 top crest
        ( 0.10,  0.42), # Tier 2 step
        (-1.00,  0.22), # Tier 3 step down
        (-2.20, -0.45), # Chisel toe front tip
        (-2.20, -0.65), # Chisel toe ground front
        (-1.50, -0.65), # Ground contact front pad
        (-0.80, -0.25), # Arched underside start (bridge clearance)
        ( 0.50, -0.25), # Arched underside peak
        ( 1.20, -0.65), # Ground contact rear pad
        ( 2.00, -0.65)  # Rear heel ground
    ]
    
    # 3-tier cross section across X:
    # Outer hull W=1.80 (X = +/- 0.90)
    # Border facet W=1.40 (X = +/- 0.70)
    # Recessed stadium pocket at X = +/- 0.90, inset by 0.15m between Y=-0.5 and Y=1.0
    
    w_outer = 1.80; w_rail = 1.30
    n = len(toe_profile_yz)
    
    # Left and Right Outer Vertices
    v_left_out = [bm.verts.new(Vector((-w_outer*0.5, y, z))) for y, z in toe_profile_yz]
    v_right_out = [bm.verts.new(Vector(( w_outer*0.5, y, z))) for y, z in toe_profile_yz]
    
    # Left and Right Rail Vertices (slightly raised on top)
    v_left_rail = [bm.verts.new(Vector((-w_rail*0.5, y, z + (0.08 if z > 0 else 0.0)))) for y, z in toe_profile_yz]
    v_right_rail = [bm.verts.new(Vector(( w_rail*0.5, y, z + (0.08 if z > 0 else 0.0)))) for y, z in toe_profile_yz]
    
    for i in range(n):
        nxt = (i + 1) % n
        bm.faces.new((v_left_out[i], v_left_out[nxt], v_left_rail[nxt], v_left_rail[i]))
        bm.faces.new((v_right_rail[i], v_right_rail[nxt], v_right_out[nxt], v_right_out[i]))
        bm.faces.new((v_left_rail[i], v_left_rail[nxt], v_right_rail[nxt], v_right_rail[i]))
        
    bm.faces.new(v_left_out)
    bm.faces.new(reversed(v_right_out))
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(me); bm.free()
    
    toe_obj = bpy.data.objects.new(name, me)
    toe_obj.location = loc
    toe_obj.rotation_euler = (0, 0, rot_z)
    link(toe_obj)
    toe_obj.data.materials.append(M_OCHRE_ARMOR)
    hs_finish(toe_obj, bevel_w=0.035, seg=2)
    
    # Add Recessed Stadium/Capsule Side Deboss Pocket on both flanks
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.22, depth=0.18,
                                            location=(0, 0.35, 0.05),
                                            rotation=(0, math.radians(90), 0))
        pocket = bpy.context.object; pocket.name = f"{name}_Pocket_{side}"
        pocket.scale = (1.0, 2.2, 1.0); bpy.ops.object.transform_apply(scale=True)
        pocket.location = (loc[0] + side * (w_outer * 0.5 + 0.02) * math.cos(rot_z),
                           loc[1] + side * (w_outer * 0.5 + 0.02) * math.sin(rot_z),
                           loc[2] + 0.05)
        pocket.rotation_euler = (0, math.radians(90), rot_z)
        pocket.data.materials.append(M_DARK_CHASSIS); hs_finish(pocket, bevel_w=0.015); link(pocket)
        
    return toe_obj

def build_master_foot_assembly():
    print("Building Master Multi-Toe Foot Assembly (Central gimbal hub + 4 splayed claws)...")
    foot_center = (X_LEG, -2.10, -1.02)
    
    # Central Gimbal Hub Block (polySurface206)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.35, depth=1.10,
                                        location=(foot_center[0], foot_center[1], foot_center[2] + 0.55),
                                        rotation=(0, 0, 0))
    gimbal = bpy.context.object; gimbal.name = "Foot_CentralGimbalHub"
    gimbal.data.materials.append(M_DARK_CHASSIS); hs_finish(gimbal, bevel_w=0.04); link(gimbal)
    
    # 4 Radial Splayed Claws (matching Vulture's 4-toe configuration):
    # Front-Right Claw (splayed 25 deg out)
    build_master_toe_claw("Foot_Toe_FrontRight", 
                          (foot_center[0] + 1.15, foot_center[1] - 1.85, foot_center[2]), 
                          math.radians(-25))
    # Front-Left Claw (splayed 25 deg in)
    build_master_toe_claw("Foot_Toe_FrontLeft", 
                          (foot_center[0] - 1.15, foot_center[1] - 1.85, foot_center[2]), 
                          math.radians(25))
    # Rear-Right Heel Claw (splayed backward 155 deg)
    build_master_toe_claw("Foot_Toe_RearRight", 
                          (foot_center[0] + 1.10, foot_center[1] + 1.65, foot_center[2]), 
                          math.radians(-155))
    # Rear-Left Heel Claw (splayed backward 155 deg)
    build_master_toe_claw("Foot_Toe_RearLeft", 
                          (foot_center[0] - 1.10, foot_center[1] + 1.65, foot_center[2]), 
                          math.radians(155))

# =========================================================================
# BUILD THE ENTIRE MASTER HARDSURFACE LEG V2
# =========================================================================
build_master_knee_knuckle()
build_master_thigh()
build_master_shin()
build_master_ankle_cuff()
build_master_foot_assembly()

# =========================================================================
# STUDIO LIGHTING & CAMERA SETUP (Exact Ortho & Hero Angles)
# =========================================================================
world = bpy.data.worlds.new("Master_World")
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.12, 0.14, 0.18, 1.0)
scn.world = world

# Sun Key Light
key_l = bpy.data.lights.new("Master_Key", type='SUN')
key_l.energy = 5.0; key_l.color = (1.0, 0.98, 0.95)
key_o = bpy.data.objects.new("Master_Key", key_l)
key_o.rotation_euler = (math.radians(50), math.radians(20), math.radians(65))
scn.collection.objects.link(key_o)

# Sun Rim Light
rim_l = bpy.data.lights.new("Master_Rim", type='SUN')
rim_l.energy = 4.2; rim_l.color = (0.40, 0.75, 1.0)
rim_o = bpy.data.objects.new("Master_Rim", rim_l)
rim_o.rotation_euler = (math.radians(-45), math.radians(-30), math.radians(-115))
scn.collection.objects.link(rim_o)

# Fill Light
fill_l = bpy.data.lights.new("Master_Fill", type='SUN')
fill_l.energy = 2.0; fill_l.color = (0.90, 0.95, 1.0)
fill_o = bpy.data.objects.new("Master_Fill", fill_l)
fill_o.rotation_euler = (math.radians(15), math.radians(-50), math.radians(-30))
scn.collection.objects.link(fill_o)

cam_data = bpy.data.cameras.new("Master_Cam")
cam_obj = bpy.data.objects.new("Master_Cam", cam_data)
scn.collection.objects.link(cam_obj)
scn.camera = cam_obj

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1600
scn.render.resolution_y = 1400

leg_target = Vector((X_LEG, -1.8, 6.2))

# 1. ORTHOGRAPHIC SIDE PROFILE (Exact match to user's reference image)
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 18.5
cam_obj.location = (X_LEG + 25.0, leg_target.y, leg_target.z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_side = os.path.join(OUT_DIR, "master_leg_v2_1_side_ortho.png")
scn.render.filepath = p_side
bpy.ops.render.render(write_still=True)
print(f"Rendered: {p_side}")

# 2. HERO 3/4 PERSPECTIVE VIEW
cam_data.type = 'PERSP'
cam_data.lens = 75
cam_obj.location = (X_LEG + 15.0, leg_target.y - 16.0, leg_target.z + 5.0)
d_vec = leg_target - cam_obj.location
cam_obj.rotation_euler = d_vec.to_track_quat('-Z', 'Y').to_euler()

p_hero = os.path.join(OUT_DIR, "master_leg_v2_2_hero_34.png")
scn.render.filepath = p_hero
bpy.ops.render.render(write_still=True)
print(f"Rendered: {p_hero}")

# 3. KNEE KNUCKLE CLOSEUP (Highlighting the non-oval, broken-line stepped knuckle)
knee_pos = Vector((X_LEG, -2.11, 7.42))
cam_data.lens = 95
cam_obj.location = (X_LEG + 9.5, knee_pos.y - 6.5, knee_pos.z + 1.2)
d_knee = knee_pos - cam_obj.location
cam_obj.rotation_euler = d_knee.to_track_quat('-Z', 'Y').to_euler()

p_knee = os.path.join(OUT_DIR, "master_leg_v2_3_knee_closeup.png")
scn.render.filepath = p_knee
bpy.ops.render.render(write_still=True)
print(f"Rendered: {p_knee}")

# 4. WIREFRAME OVERLAY PASS (Orthographic side)
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 18.5
cam_obj.location = (X_LEG + 25.0, leg_target.y, leg_target.z)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

mat_wire = bpy.data.materials.new('Mat_Wire_Overlay')
mat_wire.use_nodes = True
bw = mat_wire.node_tree.nodes.get('Principled BSDF')
bw.inputs['Base Color'].default_value = (0.05, 0.85, 1.0, 1.0)
bw.inputs['Emission Color'].default_value = (0.05, 0.85, 1.0, 1.0)
bw.inputs['Emission Strength'].default_value = 2.0

for o in col_leg.objects:
    if o.type == 'MESH':
        o.data.materials.append(mat_wire)
        wf = o.modifiers.new('Wire', 'WIREFRAME')
        wf.thickness = 0.025
        wf.use_replace = False
        wf.material_offset = len(o.data.materials) - 1

p_wire = os.path.join(OUT_DIR, "master_leg_v2_4_wire_ortho.png")
scn.render.filepath = p_wire
bpy.ops.render.render(write_still=True)
print(f"Rendered: {p_wire}")

# Save Blend file
bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
print(f"Saved .blend to {BLEND_FILE}")

# Copy renders to Artifacts Directory
for p in [p_side, p_hero, p_knee, p_wire]:
    if os.path.exists(p):
        bn = os.path.basename(p)
        shutil.copyfile(p, os.path.join(ART_DIR, bn))
        print(f"Copied to artifact: {bn}")

