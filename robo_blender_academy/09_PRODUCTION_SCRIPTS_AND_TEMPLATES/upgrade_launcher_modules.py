"""Safe in-place modular launcher upgrade for the clean RTS vehicle.

Geometry is created only with mesh Data API: no primitive operators and no
dependency-graph burst.  Existing launcher and missile bones are preserved.
"""
import bpy
import math

COLLECTION = "CLEAN_RTS_ROCKET_CAR"
col = bpy.data.collections.get(COLLECTION)
if not col:
    raise RuntimeError("Clean rocket-car collection was not found.")

ARMOR = bpy.data.materials.get("RTS_Armor")
DARK = bpy.data.materials.get("RTS_DarkMechanics")
GLOW = bpy.data.materials.get("RTS_OrangeGlow")
if not all((ARMOR, DARK, GLOW)):
    raise RuntimeError("Vehicle materials are missing.")


def remove_prefix(prefix):
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix):
            bpy.data.objects.remove(obj, do_unlink=True)


for prefix in ("Launcher_L_Housing", "Launcher_R_Housing", "Launcher_L_Port", "Launcher_R_Port",
               "Launcher_L_Pivot", "Launcher_R_Pivot", "Launcher_L_Brace", "Launcher_R_Brace",
               "Launcher_L_Status", "Launcher_R_Status"):
    remove_prefix(prefix)


def local_mesh(name, parent, verts, faces, mat):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.parent = parent
    obj.location = (0.0, 0.0, 0.0)
    return obj


def octagonal_housing(name, parent, width=0.29, height=0.23):
    # A slightly tapered shell.  The end face is hidden by six port bezels.
    profile = [(-width+0.07, -height), (width-0.07, -height),
               (width, -height+0.07), (width, height-0.05),
               (width-0.06, height), (-width+0.06, height),
               (-width, height-0.05), (-width, -height+0.07)]
    ys = (-0.36, 0.27)
    verts = [(x, y, z + (0.025 if y > 0 else 0.0)) for y in ys for x, z in profile]
    faces = []
    n = len(profile)
    for i in range(n):
        ni = (i + 1) % n
        faces.append((i, ni, n + ni, n + i))
    faces += [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    obj = local_mesh(name, parent, verts, faces, ARMOR)
    obj["module"] = "tapered octagonal launcher shell"
    return obj


def port_bezel(name, parent, center, outer=0.073, inner=0.047, sides=10):
    # Hollow, six-loop radial profile along Y: a true circular launch socket.
    profile = ((0.255, outer), (0.295, outer), (0.337, inner + 0.009),
               (0.347, inner), (0.300, inner), (0.255, inner + 0.010))
    verts = []
    cx, cz = center
    for y, radius in profile:
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((cx + radius * math.cos(a), y, cz + radius * math.sin(a)))
    faces = []
    for row in range(len(profile) - 1):
        for i in range(sides):
            ni = (i + 1) % sides
            a = row * sides + i
            faces.append((a, a + 1 if ni == i + 1 else row * sides, (row + 1) * sides + ni, (row + 1) * sides + i))
    obj = local_mesh(name, parent, verts, faces, DARK)
    obj["topology"] = "all-quad hollow circular bezel"
    return obj


def x_cylinder(name, parent, center, radius, length, mat, sides=12):
    # Low-poly cylinder with its axle strictly along X.
    cx, cy, cz = center
    verts = []
    for x in (cx - length * 0.5, cx + length * 0.5):
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((x, cy + radius * math.cos(a), cz + radius * math.sin(a)))
    faces = []
    for i in range(sides):
        ni = (i + 1) % sides
        faces.append((i, ni, sides + ni, sides + i))
    faces += [tuple(range(sides - 1, -1, -1)), tuple(range(sides, sides * 2))]
    return local_mesh(name, parent, verts, faces, mat)


def brace(name, parent, center, sx, sy, sz, mat):
    x, y, z = center
    verts = [(x + dx * sx * .5, y + dy * sy * .5, z + dz * sz * .5)
             for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
    faces = ((0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4),
             (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6))
    return local_mesh(name, parent, verts, faces, mat)


for side in ("L", "R"):
    group = bpy.data.objects.get(f"Launcher_{side}_Group")
    if not group:
        raise RuntimeError(f"Launcher group {side} is missing.")
    octagonal_housing(f"Launcher_{side}_Housing", group)
    # Three wide by two tall: fully visible, matching the reference's six tubes.
    for row, z in enumerate((-0.075, 0.085)):
        for column, x in enumerate((-0.135, 0.0, 0.135)):
            port_bezel(f"Launcher_{side}_Port_{row}_{column}", group, (x, z))
    # A transverse hinge and twin hinge caps express the 45-degree pitch module.
    x_cylinder(f"Launcher_{side}_PivotAxle", group, (0.0, -0.285, -0.205), 0.060, 0.72, DARK)
    for idx, x in enumerate((-0.29, 0.29)):
        x_cylinder(f"Launcher_{side}_PivotCap_{idx}", group, (x, -0.285, -0.205), 0.090, 0.042, ARMOR)
        brace(f"Launcher_{side}_Brace_{idx}", group, (x, -0.22, -0.105), 0.055, 0.18, 0.20, DARK)
    brace(f"Launcher_{side}_Status", group, (0.0, -0.375, 0.035), 0.15, 0.020, 0.060, GLOW)

print("Launchers upgraded: 2 tapered modular shells, 12 circular bezels, and independent visible pivot hardware.")
