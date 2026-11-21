import bpy
import bmesh
import math
import os
import json
from mathutils import Vector, Matrix, Color

# Paths
INPUT_GLB = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Falcon_Mk_2_-_Lowpoly_Animated_Mech-9d3a070b\Falcon_Mk_2_-_Lowpoly_Animated_Mech.glb"
OUTPUT_BLEND = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\FALCON_MK2_ARCHITECTURAL_ANALYSIS.blend"
OUTPUT_JSON = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\FALCON_MK2_ARCHITECTURAL_BLUEPRINT.json"
OUTPUT_REPORT_MD = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\FALCON_MK2_ARCHITECTURAL_BLUEPRINT.md"
RENDER_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY"
ARTIFACT_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"

# 1. Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Import reference GLB
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)
all_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']

# Calculate global bounding box
world_coords = []
for o in all_objs:
    for c in o.bound_box:
        world_coords.append(o.matrix_world @ Vector(c))

min_x = min(v.x for v in world_coords)
max_x = max(v.x for v in world_coords)
min_y = min(v.y for v in world_coords)
max_y = max(v.y for v in world_coords)
min_z = min(v.z for v in world_coords)
max_z = max(v.z for v in world_coords)

total_w = max_x - min_x
total_d = max_y - min_y
total_h = max_z - min_z
center = Vector(((min_x + max_x)/2.0, (min_y + max_y)/2.0, (min_z + max_z)/2.0))

print(f"=== FALCON MK 2 ARCHITECTURAL SCAN ===")
print(f"Total Meshes: {len(all_objs)}")
print(f"Total Dimensions: {total_w:.4f}m W x {total_d:.4f}m D x {total_h:.4f}m H")
print(f"Global Center: {center}")

# 3. Architectural Zoning / Room-like Functional Categorization
# Analogy:
# - Cockpit Penthouse (living quarters, bridge, avionics)
# - Pelvis Turntable (elevator shaft, rotary bearing)
# - Upper Leg Pylons (structural bridge pillars, hydraulic elevator shafts)
# - Lower Hock / Shins (diagonal reinforcement trusses, shock absorption bays)
# - Foot Cleat Pads (foundation footings, stabilization jacks)
# - Heavy Armament Batteries (power generation & heavy artillery wings)
# - Hardware & Greebles (conduits, vents, bolts, access hatches)

zones = {
    "COCKPIT_PENTHOUSE": {
        "title": "Cockpit & Avionics Penthouse (Main Hull)",
        "color": (0.1, 0.6, 1.0, 1.0), # Cyan
        "desc": "Primary command deck, sloped canopy, sensor arrays and dorsal carapace",
        "objects": []
    },
    "PELVIS_TURNTABLE": {
        "title": "Chassis Turntable & Core Carriage",
        "color": (1.0, 0.7, 0.1, 1.0), # Orange
        "desc": "Central structural hub, 360-deg azimuth yaw bearing, power distribution ring",
        "objects": []
    },
    "UPPER_LEG_PYLONS": {
        "title": "Upper Femur Pylons & Hip Gimbals",
        "color": (0.2, 0.8, 0.2, 1.0), # Green
        "desc": "Forward-canted heavy load-bearing structural columns with hydraulic sleeves",
        "objects": []
    },
    "HOCK_REVERSE_SHINS": {
        "title": "Reverse-Hock Shins & Kinetic Trusses",
        "color": (0.8, 0.2, 0.8, 1.0), # Magenta
        "desc": "Backward-canted diagonal suspension beams with kinetic rebound dampening",
        "objects": []
    },
    "FOOT_FOUNDATION": {
        "title": "Foot Foundation & Multi-Cleat Stabilizers",
        "color": (0.9, 0.9, 0.2, 1.0), # Yellow
        "desc": "Multi-jointed floor contact plates with hydraulic claw splay",
        "objects": []
    },
    "ARMAMENT_BATTERIES": {
        "title": "Laser / Autocannon Gun Pods & Turret Sockets",
        "color": (1.0, 0.15, 0.15, 1.0), # Red
        "desc": "Lateral heavy weapon batteries, heat-sink fins, barrels and socket collars",
        "objects": []
    },
    "GREEBLES_AND_FITTINGS": {
        "title": "Hardware Fittings, Hatches & Mechanical Pocketing",
        "color": (0.5, 0.5, 0.5, 1.0), # Steel Gray
        "desc": "Small access doors, vent louvers, actuator linkages and weight-reduction cutouts",
        "objects": []
    }
}

# Semantic Classification based on coordinate height (Z) and name hints
for o in all_objs:
    # compute part bounds in world space
    part_pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    pz_min = min(p.z for p in part_pts)
    pz_max = max(p.z for p in part_pts)
    pz_mid = (pz_min + pz_max) / 2.0
    px_mid = sum(p.x for p in part_pts) / 8.0
    py_mid = sum(p.y for p in part_pts) / 8.0
    
    pw = max(p.x for p in part_pts) - min(p.x for p in part_pts)
    pd = max(p.y for p in part_pts) - min(p.y for p in part_pts)
    ph = pz_max - pz_min
    part_vol = pw * pd * ph
    
    oname = o.name.lower()
    
    # Classify
    if "laser" in oname or "barrel" in oname:
        target_zone = "ARMAMENT_BATTERIES"
    elif pz_mid < (min_z + total_h * 0.18):
        target_zone = "FOOT_FOUNDATION"
    elif pz_mid < (min_z + total_h * 0.45):
        target_zone = "HOCK_REVERSE_SHINS"
    elif pz_mid < (min_z + total_h * 0.65):
        if abs(px_mid - center.x) > (total_w * 0.2):
            target_zone = "UPPER_LEG_PYLONS"
        else:
            target_zone = "PELVIS_TURNTABLE"
    else:
        # Above 65% height
        if pw > (total_w * 0.3) or pd > (total_d * 0.3):
            target_zone = "COCKPIT_PENTHOUSE"
        elif "laser" in oname:
            target_zone = "ARMAMENT_BATTERIES"
        else:
            target_zone = "GREEBLES_AND_FITTINGS"
            
    zones[target_zone]["objects"].append({
        "name": o.name,
        "obj_ref": o,
        "width": round(pw, 5),
        "depth": round(pd, 5),
        "height": round(ph, 5),
        "center": [round(px_mid, 4), round(py_mid, 4), round(pz_mid, 4)],
        "poly_count": len(o.data.polygons),
        "vert_count": len(o.data.vertices)
    })

# 4. Color-code materials for visual architectural blueprint rendering
mat_cache = {}
for z_key, z_info in zones.items():
    mat = bpy.data.materials.new(name=f"Mat_Zone_{z_key}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = z_info["color"]
        bsdf.inputs['Roughness'].default_value = 0.35
        bsdf.inputs['Metallic'].default_value = 0.6
    mat_cache[z_key] = mat
    
    for item in z_info["objects"]:
        o = item["obj_ref"]
        o.data.materials.clear()
        o.data.materials.append(mat)

# 5. Extract Cross-Section Contours of the Cockpit Hull (Tomographic Slices)
# Find the largest mesh in COCKPIT_PENTHOUSE
cockpit_objs = [item for item in zones["COCKPIT_PENTHOUSE"]["objects"]]
cockpit_objs.sort(key=lambda x: x["width"] * x["depth"] * x["height"], reverse=True)
main_cockpit_obj = cockpit_objs[0]["obj_ref"] if cockpit_objs else all_objs[0]

print(f"Main Cockpit Mesh for Contour Slicing: {main_cockpit_obj.name}")

# Perform 3 horizontal bisect slices (25%, 50%, 75% of cockpit height)
cockpit_pts = [main_cockpit_obj.matrix_world @ Vector(c) for c in main_cockpit_obj.bound_box]
c_zmin = min(p.z for p in cockpit_pts)
c_zmax = max(p.z for p in cockpit_pts)
c_h = c_zmax - c_zmin

slice_levels = [0.25, 0.50, 0.75]
slice_profiles = []

for s_ratio in slice_levels:
    slice_z = c_zmin + c_h * s_ratio
    # Duplicate mesh to slice via BMesh
    bm = bmesh.new()
    bm.from_mesh(main_cockpit_obj.data)
    # Transform vertices to world space
    bmesh.ops.transform(bm, matrix=main_cockpit_obj.matrix_world, verts=bm.verts)
    
    # Plane bisect
    geom = bm.faces[:] + bm.edges[:] + bm.verts[:]
    res = bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        plane_co=(0, 0, slice_z),
        plane_no=(0, 0, 1),
        clear_inner=False,
        clear_outer=False
    )
    
    # Find intersection cut edges
    cut_edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    cut_verts = set()
    for e in cut_edges:
        cut_verts.add(e.verts[0])
        cut_verts.add(e.verts[1])
        
    pts_2d = [(round(v.co.x, 4), round(v.co.y, 4)) for v in cut_verts]
    slice_profiles.append({
        "height_ratio": s_ratio,
        "world_z": round(slice_z, 4),
        "point_count": len(pts_2d),
        "contour_points_sample": pts_2d[:16],
        "envelope_width_x": round(max([p[0] for p in pts_2d]) - min([p[0] for p in pts_2d]), 4) if pts_2d else 0,
        "envelope_depth_y": round(max([p[1] for p in pts_2d]) - min([p[1] for p in pts_2d]), 4) if pts_2d else 0
    })
    bm.free()

print("Tomographic Slices of Cockpit successfully extracted.")

# 6. Extract Joint Pivots & Kinematics
# Find centers of key anatomical clusters
def get_zone_center(z_name):
    objs = zones[z_name]["objects"]
    if not objs:
        return [0, 0, 0]
    avg_x = sum(o["center"][0] for o in objs) / len(objs)
    avg_y = sum(o["center"][1] for o in objs) / len(objs)
    avg_z = sum(o["center"][2] for o in objs) / len(objs)
    return [round(avg_x, 4), round(avg_y, 4), round(avg_z, 4)]

kinematic_blueprint = {
    "turntable_yaw_pivot": get_zone_center("PELVIS_TURNTABLE"),
    "cockpit_mass_center": get_zone_center("COCKPIT_PENTHOUSE"),
    "upper_hip_gimbals": get_zone_center("UPPER_LEG_PYLONS"),
    "reverse_knee_hinges": get_zone_center("HOCK_REVERSE_SHINS"),
    "ankle_cleat_pivots": get_zone_center("FOOT_FOUNDATION"),
    "weapon_hardpoint_sockets": get_zone_center("ARMAMENT_BATTERIES")
}

# 7. Render 4-View Architectural Blueprint (Top, Side, Front, Hero Perspective)
cam_data = bpy.data.cameras.new("Arch_Camera")
cam_obj = bpy.data.objects.new("Arch_Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# World lighting
world = bpy.data.worlds.new("Arch_World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (0.05, 0.07, 0.1, 1.0) # Deep blueprint dark navy
    bg.inputs['Strength'].default_value = 1.0
bpy.context.scene.world = world

# Studio Sun & Key Lights
light_data = bpy.data.lights.new("Arch_KeyLight", type='SUN')
light_data.energy = 4.0
light_data.color = (1.0, 0.98, 0.95)
light_obj = bpy.data.objects.new("Arch_KeyLight", light_data)
light_obj.rotation_euler = (math.radians(45), math.radians(25), math.radians(60))
bpy.context.scene.collection.objects.link(light_obj)

fill_data = bpy.data.lights.new("Arch_FillLight", type='SUN')
fill_data.energy = 2.0
fill_data.color = (0.5, 0.7, 1.0)
fill_obj = bpy.data.objects.new("Arch_FillLight", fill_data)
fill_obj.rotation_euler = (math.radians(-30), math.radians(-40), math.radians(-120))
bpy.context.scene.collection.objects.link(fill_obj)

# Render settings
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 960

view_configs = [
    ("falcon_arch_1_floorplan_top.png", (center.x, center.y, center.z + total_h * 3.5), (0, 0, 0), True, total_d * 1.5),
    ("falcon_arch_2_elevation_side.png", (center.x + total_w * 3.5, center.y, center.z), (math.radians(90), 0, math.radians(90)), True, total_h * 1.5),
    ("falcon_arch_3_elevation_front.png", (center.x, center.y - total_d * 3.5, center.z), (math.radians(90), 0, 0), True, total_w * 1.6),
    ("falcon_arch_4_hero_isometric.png", (center.x + total_w * 2.2, center.y - total_d * 2.5, center.z + total_h * 1.8), (math.radians(60), 0, math.radians(45)), False, 0)
]

rendered_files = []
for filename, cam_loc, cam_rot, is_ortho, ortho_scale in view_configs:
    cam_obj.location = cam_loc
    cam_obj.rotation_euler = cam_rot
    if is_ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = ortho_scale
    else:
        cam_data.type = 'PERSP'
        cam_data.lens = 50
        
    out_path = os.path.join(RENDER_DIR, filename)
    art_path = os.path.join(ARTIFACT_DIR, filename)
    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    
    # Copy to artifact dir for direct preview
    if os.path.exists(out_path):
        import shutil
        shutil.copyfile(out_path, art_path)
        rendered_files.append((filename, art_path))
        print(f"Rendered: {filename}")

# Save annotated .blend file
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
print(f"Saved .blend analysis file: {OUTPUT_BLEND}")

# 8. Compile Master Architectural JSON
summary_json = {
    "model_name": "Falcon Mk 2 Lowpoly Animated Mech",
    "overall_dimensions_meters": {
        "width_x": round(total_w, 4),
        "depth_y": round(total_d, 4),
        "height_z": round(total_h, 4),
        "ground_clearance_z": round(min_z, 4)
    },
    "architectural_zones": {},
    "cockpit_tomography_slices": slice_profiles,
    "kinematic_joint_hierarchy": kinematic_blueprint,
    "reconstruction_recipe": {
        "proportions": {
            "cockpit_to_total_height_ratio": round(c_h / total_h, 3),
            "leg_stride_width_ratio": round(total_w / total_h, 3),
            "fuselage_depth_ratio": round(total_d / total_h, 3)
        },
        "recommended_procedural_steps": [
            "1. Instantiate Pelvis Turntable ring at z = 0.55 * total_h",
            "2. Loft Cockpit Penthouse through 3 profile slices with 15-deg forward aerodynamic droop",
            "3. Cut 2 lateral recess pockets for laser hardpoint mounting",
            "4. Construct 3-part reverse knee leg chain (Femur canted 35 deg forward, Hock canted 45 deg back)",
            "5. Mirror twin laser cannon batteries with cylindrical heat-sink flanges"
        ]
    }
}

for z_key, z_val in zones.items():
    summary_json["architectural_zones"][z_key] = {
        "title": z_val["title"],
        "description": z_val["desc"],
        "part_count": len(z_val["objects"]),
        "total_triangles": sum(o["poly_count"] for o in z_val["objects"]),
        "sample_parts": [o["name"] for o in z_val["objects"][:6]]
    }

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(summary_json, f, indent=2)

# 9. Generate Master Markdown Blueprint
md_lines = []
md_lines.append("# Falcon Mk 2 — Architectural Blueprint & Reverse-Engineering Master Specification")
md_lines.append("")
md_lines.append("> **Reference Source**: `Falcon_Mk_2_-_Lowpoly_Animated_Mech.glb`  ")
md_lines.append(f"> **Master Analysis Blend**: [`{OUTPUT_BLEND}`](file:///{OUTPUT_BLEND.replace(' ', '%20').replace('\\', '/')})  ")
md_lines.append(f"> **Full Metrics JSON**: [`{OUTPUT_JSON}`](file:///{OUTPUT_JSON.replace(' ', '%20').replace('\\', '/')})  ")
md_lines.append("")
md_lines.append("---")
md_lines.append("")
md_lines.append("## 1. Architectural Zoning Map (The Room/Floorplan Analogy)")
md_lines.append("")
md_lines.append("Viewing a combat mech through the lens of complex architecture: each side is an elevation facade, and horizontal cross-sections act as floor plans with designated functional rooms, structural trusses, conduits, and machinery bays.")
md_lines.append("")
md_lines.append("| Color Code | Architectural Zone | Part Count | Triangles | Structural & Functional Purpose |")
md_lines.append("| :--- | :--- | :---: | :---: | :--- |")
for z_key, z_val in zones.items():
    cnt = len(z_val["objects"])
    tris = sum(o["poly_count"] for o in z_val["objects"])
    md_lines.append(f"| `{z_key}` | **{z_val['title']}** | {cnt} | {tris:,} | {z_val['desc']} |")
md_lines.append("")
md_lines.append("---")
md_lines.append("")
md_lines.append("## 2. Metric Proportions & Kinematic Joint Nodes")
md_lines.append("")
md_lines.append(f"- **Total Envelope**: Width: `{total_w:.4f}m` | Depth: `{total_d:.4f}m` | Height: `{total_h:.4f}m`")
md_lines.append(f"- **Aspect Ratios**: Width/Height: `{total_w/total_h:.2f}` | Depth/Height: `{total_d/total_h:.2f}`")
md_lines.append("- **Kinematic Joint Pivot Table**:")
for k, v in kinematic_blueprint.items():
    md_lines.append(f"  * **`{k}`**: `X={v[0]:+.4f}m, Y={v[1]:+.4f}m, Z={v[2]:+.4f}m`")
md_lines.append("")
md_lines.append("---")
md_lines.append("")
md_lines.append("## 3. Cockpit Aerodynamic Cross-Section Profiles (Tomographic Slices)")
md_lines.append("")
md_lines.append("To avoid generating simple 'boxes', the cockpit contour was sliced horizontally at 3 elevations:")
for sl in slice_profiles:
    md_lines.append(f"- **Elevation {int(sl['height_ratio']*100)}% (Z = {sl['world_z']:.4f}m)**: Envelope: `{sl['envelope_width_x']:.4f}m W x {sl['envelope_depth_y']:.4f}m D` ({sl['point_count']} boundary vertices)")
md_lines.append("")
md_lines.append("---")
md_lines.append("")
md_lines.append("## 4. Architectural Diagnostic Render Gallery")
md_lines.append("")
for fname, art_p in rendered_files:
    md_lines.append(f"### {fname.replace('.png', '').replace('_', ' ').title()}")
    md_lines.append(f"![{fname}](file:///{art_p.replace(' ', '%20').replace('\\', '/')})")
    md_lines.append("")

with open(OUTPUT_REPORT_MD, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"Master Blueprint MD successfully written: {OUTPUT_REPORT_MD}")
