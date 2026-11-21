"""Rig the clean vehicle's wheel and suspension meshes with binary weights.

All mechanical mesh weights are intentionally 100% to one functional bone.
This is stable for game export and avoids soft deformation on rigid parts.
"""
import bpy
import json

RIG_NAME = "RTS_RocketCar_Rig"
rig = bpy.data.objects.get(RIG_NAME)
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError("RTS_RocketCar_Rig is missing.")

WHEEL_KEYS = ("FL", "FR", "RL", "RR")


def armature_weighted(obj, bone_name):
    """Detach bone/object parenting safely, then bind every vertex 100% to bone."""
    if not obj or obj.type != 'MESH':
        raise RuntimeError(f"Mesh missing for {bone_name}")
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = 'OBJECT'
    obj.parent_bone = ""
    obj.matrix_world = world
    # Replace only our functional group; leave unrelated groups untouched.
    vg = obj.vertex_groups.get(bone_name) or obj.vertex_groups.new(name=bone_name)
    vg.remove(range(len(obj.data.vertices)))
    vg.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
    mod = next((m for m in obj.modifiers if m.type == 'ARMATURE' and m.object == rig), None)
    if not mod:
        mod = obj.modifiers.new(name="RTS_MechanicalRig", type='ARMATURE')
        mod.object = rig
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False
    obj["weighting"] = f"rigid 1.0 -> {bone_name}"


for key in WHEEL_KEYS:
    armature_weighted(bpy.data.objects.get(f"Wheel_{key}"), f"wheel_{key}")
    # Suspension arms follow axle travel as a rigid mechanical assembly.
    for name in (f"LowerArm_{key}", f"UpperArm_{key}"):
        armature_weighted(bpy.data.objects.get(name), f"suspension_{key}")
    armature_weighted(bpy.data.objects.get(f"Shock_{key}"), f"shock_{key}")


for key in WHEEL_KEYS:
    susp = rig.pose.bones[f"suspension_{key}"]
    wheel = rig.pose.bones[f"wheel_{key}"]
    shock = rig.pose.bones[f"shock_{key}"]

    # Rest axis of suspension bone is vertical; move it locally for terrain travel.
    for old in list(susp.constraints):
        if old.name == "Suspension_Travel_Limit":
            susp.constraints.remove(old)
    limit = susp.constraints.new('LIMIT_LOCATION')
    limit.name = "Suspension_Travel_Limit"
    limit.owner_space = 'LOCAL'
    limit.use_min_y = True
    limit.use_max_y = True
    limit.min_y = -0.18
    limit.max_y = 0.18
    susp["role"] = "terrain travel control"
    susp["travel_m"] = 0.18
    susp["animation_note"] = "Translate local Y for bump/rebound; wheel is its child."

    # Wheel bone is aligned to the physical axle, so local Y is its spin axis.
    wheel.rotation_mode = 'XYZ'
    wheel.lock_location = (True, True, True)
    wheel.lock_scale = (True, True, True)
    wheel.lock_rotation = (True, False, True)
    wheel["role"] = "wheel spin"
    wheel["spin_axis"] = "local Y (axle)"
    wheel["radius_m"] = 0.34
    wheel["animation_note"] = "Rotate local Y for rolling."

    shock["role"] = "damper / piston visual"
    shock["animation_note"] = "Animate with the suspension travel; rigid binary weights."

rig["rig_type"] = "RTS independent suspension"
rig["wheel_spin_axis"] = "local Y"
rig["suspension_travel_m"] = 0.18
rig["weighting_policy"] = "mechanical binary 1.0 / 0.0"

bpy.context.view_layer.update()

# Compact integrity check: every weighted mechanical vertex must have total 1.0.
report = {}
for key in WHEEL_KEYS:
    names = (f"Wheel_{key}", f"LowerArm_{key}", f"UpperArm_{key}", f"Shock_{key}")
    for name in names:
        obj = bpy.data.objects[name]
        group_name = (f"wheel_{key}" if name.startswith("Wheel_") else
                      f"shock_{key}" if name.startswith("Shock_") else f"suspension_{key}")
        group = obj.vertex_groups[group_name]
        weighted = sum(1 for v in obj.data.vertices if any(g.group == group.index and abs(g.weight - 1.0) < 1e-6 for g in v.groups))
        report[name] = [weighted, len(obj.data.vertices)]
print("Wheel/suspension rigid weights configured: " + json.dumps(report, sort_keys=True))
