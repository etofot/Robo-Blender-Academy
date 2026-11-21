"""Safe in-place upgrade for CLEAN_RTS_ROCKET_CAR.

Replaces only the early blockout hood with a closed, all-quad turtle-shell
carapace.  Designed to be executed inside Blender through the MCP bridge.
"""
import bpy
from mathutils import Vector

COLLECTION = "CLEAN_RTS_ROCKET_CAR"
ROOT_NAME = "CLEAN_ROCKET_CAR_ROOT"


def get_material(name):
    mat = bpy.data.materials.get(name)
    if not mat:
        raise RuntimeError(f"Required material is missing: {name}")
    return mat


ARMOR = get_material("RTS_Armor")
DARK = get_material("RTS_DarkMechanics")
col = bpy.data.collections.get(COLLECTION)
root = bpy.data.objects.get(ROOT_NAME)
if not col or not root:
    raise RuntimeError("Clean vehicle collection/root not found; build the vehicle first.")


def remove(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


for old in ("Armor_Hood", "Armor_Hood_Overlay", "Armor_Hood_CenterPlate",
            "Carapace_Main", "Carapace_Border", "Carapace_Center_Ridge"):
    remove(old)


def shell_mesh(name, sections, material, lower=0.075):
    """Closed loft with a 5-point crowned section: every face is a quad."""
    xs = (-1.0, -0.45, 0.0, 0.45, 1.0)
    verts = []
    # Crowned top: narrow central high line and gently drooped armour shoulders.
    for y, width, z, crown in sections:
        for factor in xs:
            edge_drop = 0.035 if abs(factor) > 0.9 else 0.008 if abs(factor) > 0.2 else 0.0
            verts.append((factor * width, y, z + crown * (1.0 - abs(factor)) - edge_drop))
    top_count = len(verts)
    for y, width, z, crown in sections:
        for factor in xs:
            verts.append((factor * width, y, z + crown * (1.0 - abs(factor)) - lower))

    rows, cols = len(sections), len(xs)
    faces = []
    # Top and underside grid.
    for r in range(rows - 1):
        for c in range(cols - 1):
            a = r * cols + c
            faces.append((a, a + 1, a + cols + 1, a + cols))
            b = top_count + a
            faces.append((b + cols, b + cols + 1, b + 1, b))
    # Two long perimeter rails and the front/rear caps.
    for r in range(rows - 1):
        a, b = r * cols, (r + 1) * cols
        faces.append((a, b, top_count + b, top_count + a))
        a, b = r * cols + cols - 1, (r + 1) * cols + cols - 1
        faces.append((a, top_count + a, top_count + b, b))
    for r in (0, rows - 1):
        for c in range(cols - 1):
            a = r * cols + c
            faces.append((a, top_count + a, top_count + a + 1, a + 1))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.parent = root
    obj.location = (0.0, 0.0, 0.0)
    obj["construction"] = "closed all-quad crowned loft"
    obj["quad_faces"] = len(faces)
    return obj


# Rear neck -> broad shoulders -> shielded, pointed nose.  Front is +Y.
main = shell_mesh("Carapace_Main", [
    (0.03, 0.36, 1.015, 0.035),
    (0.20, 0.58, 1.020, 0.060),
    (0.48, 0.76, 0.982, 0.070),
    (0.79, 0.80, 0.905, 0.062),
    (1.11, 0.66, 0.820, 0.048),
    (1.37, 0.32, 0.735, 0.018),
], ARMOR, 0.080)

# A nested dark inlay makes the shell read as layered armour rather than a cube.
border = shell_mesh("Carapace_Border", [
    (0.13, 0.31, 1.062, 0.014),
    (0.30, 0.48, 1.065, 0.020),
    (0.57, 0.63, 1.025, 0.022),
    (0.83, 0.64, 0.950, 0.020),
    (1.08, 0.51, 0.872, 0.015),
    (1.27, 0.24, 0.800, 0.008),
], DARK, 0.030)

# Raised central keel: carries the turtle/armadillo silhouette from the cockpit to nose.
ridge = shell_mesh("Carapace_Center_Ridge", [
    (0.21, 0.15, 1.110, 0.020),
    (0.55, 0.23, 1.090, 0.030),
    (0.87, 0.22, 1.015, 0.025),
    (1.16, 0.13, 0.925, 0.010),
], ARMOR, 0.035)

# Make the inlay sit above the main carapace without relying on modifiers/operators.
border.location.z = 0.004
ridge.location.z = 0.012

for obj in (main, border, ridge):
    obj.data.update()

# The previous blockout had a 2 x 3 depth stack: from the camera it looked
# like two missiles.  Put the existing 12 bone-parented missiles into an
# unmistakable 3 columns x 2 rows launch face.  matrix_world assignment keeps
# bone parenting intact and avoids context-dependent operators.
for side, sx in (("L", -1), ("R", 1)):
    for row in range(2):
        for column in range(3):
            obj = bpy.data.objects.get(f"Missile_{side}_{row}_{column}")
            if obj:
                world_pos = root.matrix_world @ Vector((0.66 * sx + (column - 1) * 0.125,
                                                        -0.18, 1.105 + row * 0.145))
                world = obj.matrix_world.copy()
                world.translation = world_pos
                obj.matrix_world = world

print("Carapace upgraded: 3 closed crowned all-quad panels; 6 missiles per launcher now form a visible 3x2 face.")
