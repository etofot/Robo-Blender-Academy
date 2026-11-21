import bpy
import bmesh
import math
from mathutils import Vector, Matrix

def distribute_bolts(center=Vector((0,0,0)), normal=Vector((1,0,0)), pcd_radius=0.40, count=8, 
                     bolt_radius=0.035, bolt_depth=0.06, head_type='HEX', parent_obj=None, prefix="Bolt"):
    """
    Distributes structural bolts around a Pitch Circle Diameter (PCD) along a plane normal.
    """
    normal = normal.normalized()
    # Find perpendicular axes
    up = Vector((0, 0, 1)) if abs(normal.z) < 0.9 else Vector((0, 1, 0))
    tangent = normal.cross(up).normalized()
    bitangent = normal.cross(tangent).normalized()
    
    verts_count = 6 if head_type == 'HEX' else 16
    bolt_objs = []
    
    for i in range(count):
        ang = i * (2.0 * math.pi / count)
        offset = tangent * (pcd_radius * math.cos(ang)) + bitangent * (pcd_radius * math.sin(ang))
        b_pos = center + offset
        
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=verts_count,
            radius=bolt_radius,
            depth=bolt_depth,
            location=b_pos
        )
        b_obj = bpy.context.object
        b_obj.name = f"{prefix}_{i:02d}"
        
        # Orient cylinder along normal
        rot_quat = Vector((0, 0, 1)).rotation_difference(normal)
        b_obj.rotation_euler = rot_quat.to_euler()
        
        # Soft bevel
        mod = b_obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bolt_radius * 0.15
        mod.segments = 1
        
        if parent_obj:
            b_obj.parent = parent_obj
            
        bolt_objs.append(b_obj)
        
    return bolt_objs
