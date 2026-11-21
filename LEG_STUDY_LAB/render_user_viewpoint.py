import bpy, os
from mathutils import Vector

blend_p = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB\MASTER_LEG_50_STEPS_COMPLETE.blend"
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

# Sun
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

# Same angle as user screenshot
cam_o.location = (center.x + 3.8, center.y - 3.2, center.z + 1.2)
dir_vec = center - cam_o.location
rot_quat = dir_vec.to_track_quat('-Z', 'Y')
cam_o.rotation_euler = rot_quat.to_euler()

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1200
scn.render.resolution_y = 1200
out_p = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB\user_viewpoint_match.png"
scn.render.filepath = out_p
bpy.ops.render.render(write_still=True)
print(f"Rendered User Viewpoint Match: {out_p}")

