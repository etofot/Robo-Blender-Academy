import bpy
import bmesh
import math
from mathutils import Vector

def create_sunburst_gear(name, radius_outer=0.50, radius_inner=0.25, depth=0.10, 
                         num_teeth=24, tooth_depth=0.065, bevel_width=0.012):
    """
    Creates a master-grade radial sunburst gear disc with stepped teeth and inner bore.
    """
    bm = bmesh.new()
    pts_ring_f = []
    pts_ring_b = []
    
    n_pts = num_teeth * 2
    for i in range(n_pts):
        ang = i * (2.0 * math.pi / n_pts)
        is_tip = (i % 2 == 1)
        r = radius_outer if is_tip else (radius_outer - tooth_depth)
        y = r * math.cos(ang)
        z = r * math.sin(ang)
        
        pts_ring_f.append(bm.verts.new(Vector(( depth * 0.5, y, z))))
        pts_ring_b.append(bm.verts.new(Vector((-depth * 0.5, y, z))))
        
    pts_bore_f = []
    pts_bore_b = []
    for i in range(n_pts):
        ang = i * (2.0 * math.pi / n_pts)
        y = radius_inner * math.cos(ang)
        z = radius_inner * math.sin(ang)
        pts_bore_f.append(bm.verts.new(Vector(( depth * 0.5, y, z))))
        pts_bore_b.append(bm.verts.new(Vector((-depth * 0.5, y, z))))
        
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        # Outer teeth band
        bm.faces.new((pts_ring_f[i], pts_ring_f[nxt], pts_ring_b[nxt], pts_ring_b[i]))
        # Inner bore band
        bm.faces.new((pts_bore_b[i], pts_bore_b[nxt], pts_bore_f[nxt], pts_bore_f[i]))
        # Front face quads
        bm.faces.new((pts_ring_f[i], pts_bore_f[i], pts_bore_f[nxt], pts_ring_f[nxt]))
        # Back face quads
        bm.faces.new((pts_ring_b[nxt], pts_bore_b[nxt], pts_bore_b[i], pts_ring_b[i]))
        
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(me); bm.free()
    
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    
    for p in obj.data.polygons: p.use_smooth = True
    if bevel_width > 0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel_width
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(35)
        
    return obj
