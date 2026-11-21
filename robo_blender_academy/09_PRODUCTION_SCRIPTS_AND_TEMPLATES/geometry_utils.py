"""
Core Geometry Utilities for Blender Procedural Generation.
Source: Blender-MCP-Assembly-Skill & Project Core Geometry Rules.
"""
import bpy
import bmesh
import math

def make_beam(name, start, end, hw=0.012, hh=0.010):
    """Build a rectangular beam from start to end points using bmesh (no Euler rotation bugs)."""
    dx, dy, dz = end[0]-start[0], end[1]-start[1], end[2]-start[2]
    L = math.sqrt(dx*dx + dy*dy + dz*dz)
    if L < 1e-6:
        return None
    fx, fy, fz = dx/L, dy/L, dz/L
    ux, uy, uz = (0,0,1) if abs(fz) < 0.99 else (1,0,0)
    rx = fy*uz-fz*uy; ry = fz*ux-fx*uz; rz = fx*uy-fy*ux
    rL = math.sqrt(rx*rx+ry*ry+rz*rz); rx,ry,rz = rx/rL,ry/rL,rz/rL
    upx = ry*fz-rz*fy; upy = rz*fx-rx*fz; upz = rx*fy-ry*fx

    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    verts = []
    for base in [start, end]:
        for sx, sy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            verts.append(bm.verts.new((
                base[0]+rx*hw*sx+upx*hh*sy,
                base[1]+ry*hw*sx+upy*hh*sy,
                base[2]+rz*hw*sx+upz*hh*sy,
            )))
    v = verts
    for f in [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(0,3,2,1),(4,5,6,7)]:
        bm.faces.new([v[i] for i in f])
    bm.to_mesh(mesh)
    bm.free()
    return obj

def verify_bounds(name):
    """Print and return world-space bounding box dictionary for named object."""
    obj = bpy.data.objects[name]
    vs  = [obj.matrix_world @ v.co for v in obj.data.vertices]
    b = {
        'x': (min(v.x for v in vs), max(v.x for v in vs)),
        'y': (min(v.y for v in vs), max(v.y for v in vs)),
        'z': (min(v.z for v in vs), max(v.z for v in vs)),
    }
    print(f"{name}: X[{b['x'][0]:.4f},{b['x'][1]:.4f}] Y[{b['y'][0]:.4f},{b['y'][1]:.4f}] Z[{b['z'][0]:.4f},{b['z'][1]:.4f}]")
    return b

def verify_overlap(name_a, name_b, axis='z', min_overlap=0.005):
    """Confirm two parts physically overlap on the given axis."""
    a = verify_bounds(name_a)
    b = verify_bounds(name_b)
    overlap = min(a[axis][1], b[axis][1]) - max(a[axis][0], b[axis][0])
    ok = overlap >= min_overlap
    print(f"  {name_a} <-> {name_b} [{axis.upper()}]: {'OK' if ok else 'GAP WARNING'} ({overlap:.4f}m)")
    return overlap

def finalize(name):
    """Apply transforms, set origin to median geometry, and shade smooth."""
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT')
    return obj

def audit_all():
    """Audit all mesh objects in scene to ensure rotation=0 and scale=1."""
    meshes = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
    all_ok = True
    for obj in meshes:
        rot = tuple(round(c, 3) for c in obj.rotation_euler)
        scl = tuple(round(c, 3) for c in obj.scale)
        ok  = rot == (0.0,0.0,0.0) and scl == (1.0,1.0,1.0)
        if not ok:
            all_ok = False
        print(f"  [{'OK' if ok else '!!'}] {obj.name:30s} rot={rot} scl={scl}")
    print(f"\nAll transforms clean: {all_ok}")
    return all_ok
