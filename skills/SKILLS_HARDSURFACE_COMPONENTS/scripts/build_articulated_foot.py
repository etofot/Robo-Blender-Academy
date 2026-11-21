import bpy
import bmesh
import math
from mathutils import Vector

def build_toe_claw(name, base_pos, rot_z_deg=0.0, toe_length=0.95, toe_width=0.36, toe_height=0.28):
    """
    Creates an articulated ground-conforming toe claw with 3-tier terraced armor and an underside hollow bridge arch.
    """
    bm = bmesh.new()
    
    # 2D profile along length Y and height Z:
    # 3-tier stepped forward slope + arched bridge on the bottom
    toe_profile = [
        # (Y, Z)
        ( toe_length * 0.45,  toe_height * 0.45), # Rear top hinge
        ( toe_length * 0.20,  toe_height * 0.55), # Tier 1 top crest
        (-toe_length * 0.05,  toe_height * 0.40), # Tier 2 step
        (-toe_length * 0.30,  toe_height * 0.20), # Tier 3 step down
        (-toe_length * 0.55, -toe_height * 0.35), # Chisel tip top
        (-toe_length * 0.55, -toe_height * 0.50), # Chisel tip ground front
        (-toe_length * 0.35, -toe_height * 0.50), # Front ground contact pad
        (-toe_length * 0.15, -toe_height * 0.20), # Arched bridge start
        ( toe_length * 0.15, -toe_height * 0.20), # Arched bridge peak
        ( toe_length * 0.35, -toe_height * 0.50), # Rear ground contact pad
        ( toe_length * 0.45, -toe_height * 0.50)  # Rear ground end
    ]
    
    w_out = toe_width
    w_rail = toe_width * 0.72
    n_p = len(toe_profile)
    
    v_left_out  = [bm.verts.new(Vector((-w_out*0.5,  y, z))) for y, z in toe_profile]
    v_right_out = [bm.verts.new(Vector(( w_out*0.5,  y, z))) for y, z in toe_profile]
    v_left_mid  = [bm.verts.new(Vector((-w_rail*0.5, y, z + (0.02 if z > 0 else 0)))) for y, z in toe_profile]
    v_right_mid = [bm.verts.new(Vector(( w_rail*0.5, y, z + (0.02 if z > 0 else 0)))) for y, z in toe_profile]
    
    for i in range(n_p):
        nxt = (i + 1) % n_p
        bm.faces.new((v_left_out[i],  v_left_out[nxt],  v_left_mid[nxt],  v_left_mid[i]))
        bm.faces.new((v_right_mid[i], v_right_mid[nxt], v_right_out[nxt], v_right_out[i]))
        bm.faces.new((v_left_mid[i],  v_left_mid[nxt],  v_right_mid[nxt], v_right_mid[i]))
        
    bm.faces.new(v_left_out)
    bm.faces.new(reversed(v_right_out))
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(me); bm.free()
    
    obj = bpy.data.objects.new(name, me)
    obj.location = base_pos
    obj.rotation_euler = (0, 0, math.radians(rot_z_deg))
    bpy.context.scene.collection.objects.link(obj)
    
    for p in obj.data.polygons: p.use_smooth = True
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = 0.012; mod.segments = 2
    mod.limit_method = 'ANGLE'; mod.angle_limit = math.radians(35)
    
    return obj
