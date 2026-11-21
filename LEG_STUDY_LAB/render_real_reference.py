import bpy, os
from mathutils import Vector

blend_p = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB\REFERENCE_LEG_ISOLATED.blend"
bpy.ops.wm.open_mainfile(filepath=blend_p)

scn = bpy.context.scene

# Clean lights and cams
for o in list(scn.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

# Leg bounds
leg_objs = [o for o in scn.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in leg_objs for c in o.bound_box]
lx_min, lx_max = min(p.x for p in pts), max(p.x for p in pts)
ly_min, ly_max = min(p.y for p in pts), max(p.y for p in pts)
lz_min, lz_max = min(p.z for p in pts), max(p.z for p in pts)
center = Vector(((lx_min + lx_max)/2.0, (ly_min + ly_max)/2.0, (lz_min + lz_max)/2.0))
h = lz_max - lz_min

# Materials
clay = bpy.data.materials.new("ClayMat")
clay.use_nodes = True
bsdf = clay.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.8, 0.76, 0.68, 1.0)
bsdf.inputs['Roughness'].default_value = 0.4

for o in leg_objs:
    o.data.materials.clear()
    o.data.materials.append(clay)

# Sun & Ambient
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 4.0
suno = bpy.data.objects.new("Sun", sun)
suno.rotation_euler = (0.7, 0.4, 0.9)
scn.collection.objects.link(suno)

cam_d = bpy.data.cameras.new("Cam")
cam_d.type = 'PERSP'
cam_d.lens = 65
cam_o = bpy.data.objects.new("Cam", cam_d)
scn.collection.objects.link(cam_o)
scn.camera = cam_o

# 3/4 perspective matching user's viewport screenshot!
# In user screenshot: viewing from front-right slightly elevated
cam_o.location = (center.x + 3.8, center.y - 3.2, center.z + 1.2)
dir_vec = center - cam_o.location
rot_quat = dir_vec.to_track_quat('-Z', 'Y')
cam_o.rotation_euler = rot_quat.to_euler()

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1200
scn.render.resolution_y = 1200
out_p = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB\real_reference_perspective.png"
scn.render.filepath = out_p
bpy.ops.render.render(write_still=True)
print(f"Rendered Real Reference: {out_p}")

