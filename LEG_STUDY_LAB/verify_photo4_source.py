import bpy, os
from mathutils import Vector

OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
glb_p = r"I:\1_VSCODE\2026_3  GAMES\3dModelsFab\MechRobo\Mech_gameready-220d9957\Mech_gameready.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb_p)

# Find all leg objects
leg_objs = [o for o in scn.objects if o.type == 'MESH' and 'legs' in o.name.lower()]
print(f"Found {len(leg_objs)} leg objects in Mech_gameready")

# Hide non-leg objects
for o in scn.objects:
    if o not in leg_objs:
        o.hide_render = True
        o.hide_viewport = True

# Focus target on leg center
leg_pts = [o.matrix_world @ Vector(c) for o in leg_objs for c in o.bound_box]
lx_min, lx_max = min(p.x for p in leg_pts), max(p.x for p in leg_pts)
ly_min, ly_max = min(p.y for p in leg_pts), max(p.y for p in leg_pts)
lz_min, lz_max = min(p.z for p in leg_pts), max(p.z for p in leg_pts)

leg_w = lx_max - lx_min; leg_d = ly_max - ly_min; leg_h = lz_max - lz_min
leg_center = Vector(((lx_min + lx_max)/2.0, (ly_min + ly_max)/2.0, (lz_min + lz_max)/2.0))
print(f"Leg Center: {leg_center}, Size: ({leg_w:.2f}, {leg_d:.2f}, {leg_h:.2f})")

# Clay material
clay = bpy.data.materials.new("Clay")
clay.use_nodes = True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.78, 0.76, 1.0)
clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.35

# Wire overlay
wire = bpy.data.materials.new("Wire")
wire.use_nodes = True
wire.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.3, 0.9, 0.6, 1.0)
wire.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (0.3, 0.9, 0.6, 1.0)
wire.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.5

for o in leg_objs:
    o.data.materials.clear()
    o.data.materials.append(clay)
    o.data.materials.append(wire)
    mod = o.modifiers.new("Wire", 'WIREFRAME')
    mod.thickness = 0.003
    mod.use_replace = False
    mod.material_offset = 1

# Setup studio
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.15, 0.18, 0.22, 1.0)
scn.world = world

sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 4.5
suno = bpy.data.objects.new("Sun", sun)
suno.rotation_euler = (0.8, 0.3, 1.0)
scn.collection.objects.link(suno)

cam_d = bpy.data.cameras.new("Cam")
cam_d.type = 'ORTHO'
cam_d.ortho_scale = leg_h * 1.15
cam_o = bpy.data.objects.new("Cam", cam_d)
scn.collection.objects.link(cam_o)
scn.camera = cam_o

cam_o.location = (leg_center.x + leg_w * 4.0 + 5.0, leg_center.y, leg_center.z)
cam_o.rotation_euler = (1.5708, 0, 1.5708)

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1200
scn.render.resolution_y = 1600

out_p = os.path.join(OUT_DIR, "confirmed_photo4_source_render.png")
scn.render.filepath = out_p
bpy.ops.render.render(write_still=True)
print(f"Rendered: {out_p}")

import shutil
shutil.copyfile(out_p, os.path.join(ART_DIR, "confirmed_photo4_source_render.png"))

