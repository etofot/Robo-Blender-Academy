"""Repair the known double-X parenting offset in CLEAN_RTS_ROCKET_CAR."""
import bpy

ROOT = bpy.data.objects.get("CLEAN_ROCKET_CAR_ROOT")
RIG = bpy.data.objects.get("RTS_RocketCar_Rig")
if not ROOT or not RIG:
    raise RuntimeError("Expected clean-vehicle root/rig is missing.")

fixed = []
# These objects are direct children of ROOT.  They were created at world X=10
# and then parented to ROOT at X=10, leaving local X≈10 and world X≈20.
for obj in bpy.data.objects:
    if obj.parent == ROOT and 8.0 < obj.location.x < 12.0:
        obj.location.x -= 10.0
        fixed.append(obj.name)

# Launcher groups are bone children and suffered the same construction order.
# Their module meshes are children of the group, so moving each group once also
# repairs its housing, ports, pivots and braces without touching missile bones.
for name in ("Launcher_L_Group", "Launcher_R_Group"):
    obj = bpy.data.objects.get(name)
    if obj and obj.parent == RIG and obj.parent_type == 'BONE' and 8.0 < obj.location.x < 12.0:
        obj.location.x -= 10.0
        fixed.append(name)

bpy.context.view_layer.update()
print("Fixed double-X offset for %d objects: %s" % (len(fixed), ", ".join(fixed)))
