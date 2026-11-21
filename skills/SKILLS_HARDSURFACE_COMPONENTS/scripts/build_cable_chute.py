import bpy
import bmesh
import math
from mathutils import Vector

def build_armor_cable_chute(name="Armor_Cable_Chute", arc_center=(0, 0.6, 3.35), 
                            radius_y=0.65, radius_z=0.40, angle_start_deg=20, angle_end_deg=160, 
                            num_links=14, link_dims=(0.32, 0.14, 0.08)):
    """
    Constructs an articulated 3D segmented armored cable chute with overlapping links.
    """
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    
    lw, ld, lh = link_dims
    cx, cy, cz = arc_center
    
    for i in range(num_links):
        t = i / (num_links - 1)
        ang_deg = angle_start_deg + t * (angle_end_deg - angle_start_deg)
        angle = math.radians(ang_deg)
        
        py = cy - radius_y * math.cos(angle)
        pz = cz + radius_z * math.sin(angle)
        px = cx
        tangent_angle = angle + math.pi / 2.0
        
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= lw
            v.co.y *= ld
            v.co.z *= lh
            if v.co.z > 0:
                v.co.z += (0.02 if abs(v.co.y) < ld * 0.3 else 0.0)
                
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(f"{name}_Mesh_{i:02d}")
        bm.to_mesh(me); bm.free()
        
        obj = bpy.data.objects.new(f"{name}_Link_{i:02d}", me)
        obj.location = (px, py, pz)
        obj.rotation_euler = (tangent_angle, 0, 0)
        col.objects.link(obj)
        
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = 0.008; mod.segments = 2
        
    return col
