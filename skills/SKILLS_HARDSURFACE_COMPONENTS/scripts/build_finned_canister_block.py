import bpy
import bmesh
import math
from mathutils import Vector

def create_finned_canister_block(name="Dual_Finned_Accumulators", 
                                 canister_radius=0.08, canister_length=0.48, 
                                 num_fins=7, fin_depth=0.025, fin_width=0.012,
                                 canister_spacing=0.20):
    """
    Creates an industrial H-bracket mounting unit carrying dual finned cooling/accumulator canisters.
    """
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    
    # 1. Dual Finned Canisters
    for c_idx, y_off in enumerate([-canister_spacing * 0.5, canister_spacing * 0.5]):
        bm = bmesh.new()
        # Main core cylinder
        # Create along Z axis, then we orient as needed
        r_core = canister_radius
        r_fin = canister_radius + fin_depth
        z_half = canister_length * 0.5
        
        # Build stepped profile along length (annular fins)
        fin_spacing = (canister_length * 0.70) / num_fins
        fin_start_z = -canister_length * 0.35
        
        # Base cylinder
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20,
                              radius1=r_core, radius2=r_core, depth=canister_length)
                              
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me_can = bpy.data.meshes.new(f"Canister_Core_{c_idx}")
        bm.to_mesh(me_can); bm.free()
        
        can_obj = bpy.data.objects.new(f"{name}_Canister_{c_idx}", me_can)
        can_obj.location = (0, y_off, 0)
        col.objects.link(can_obj)
        
        # Add cooling fin rings
        for f_idx in range(num_fins):
            fz = fin_start_z + f_idx * fin_spacing
            bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=r_fin, depth=fin_width,
                                                location=(0, y_off, fz))
            fin = bpy.context.object; fin.name = f"{name}_Fin_{c_idx}_{f_idx}"
            col.objects.link(fin); bpy.context.scene.collection.objects.unlink(fin)
            fin.parent = can_obj
            
        # Domed end caps
        for cap_sign in (-1, 1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r_core * 1.05, depth=0.04,
                                                location=(0, y_off, cap_sign * (z_half + 0.02)))
            cap = bpy.context.object; cap.name = f"{name}_Cap_{c_idx}_{cap_sign}"
            col.objects.link(cap); bpy.context.scene.collection.objects.unlink(cap)
            cap.parent = can_obj
            
    # 2. H-Bracket Frame clamping both canisters
    bm_h = bmesh.new()
    bw = 0.06; bd = canister_spacing + canister_radius * 2.8; bh = canister_length * 0.45
    # Central horizontal tie-plate
    bmesh.ops.create_cube(bm_h, size=1.0)
    for v in bm_h.verts:
        v.co.x *= bw
        v.co.y *= bd
        v.co.z *= bh * 0.35
        
    bmesh.ops.recalc_face_normals(bm_h, faces=bm_h.faces)
    me_h = bpy.data.meshes.new(f"{name}_H_Frame_Mesh")
    bm_h.to_mesh(me_h); bm_h.free()
    
    h_frame = bpy.data.objects.new(f"{name}_H_Bracket", me_h)
    col.objects.link(h_frame)
    mod = h_frame.modifiers.new("Bevel", 'BEVEL')
    mod.width = 0.012; mod.segments = 2
    
    return col
