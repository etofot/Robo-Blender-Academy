"""Safe MCP build: a clean rigged RTS rocket car. Execute inside Blender, not CPython."""
import bpy
import math
from mathutils import Vector

BASE = Vector((10.0, 0.0, 0.0))
COLLECTION = "CLEAN_RTS_ROCKET_CAR"


def material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


ARMOR = material("RTS_Armor", (0.075, 0.095, 0.10), 0.78, 0.30)
DARK = material("RTS_DarkMechanics", (0.018, 0.022, 0.026), 0.65, 0.38)
RUBBER = material("RTS_Rubber", (0.012, 0.014, 0.017), 0.0, 0.62)
MISSILE = material("RTS_MissileRed", (0.52, 0.015, 0.065), 0.35, 0.25)
GLOW = material("RTS_OrangeGlow", (1.0, 0.15, 0.01), 0.1, 0.22)


def clear_collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        return
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(col)


clear_collection(COLLECTION)
# A failed pre-restart attempt can leave Blender's default armature outside our collection.
for orphan_name in ("Armature", "RTS_RocketCar_Rig"):
    orphan = bpy.data.objects.get(orphan_name)
    if orphan and orphan.type == 'ARMATURE':
        bpy.data.objects.remove(orphan, do_unlink=True)
col = bpy.data.collections.new(COLLECTION)
bpy.context.scene.collection.children.link(col)


def mesh_object(name, verts, faces, mat, location=(0, 0, 0)):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.location = BASE + Vector(location)
    return obj


def box(name, center, size, mat):
    hx, hy, hz = (v * 0.5 for v in size)
    verts = [(x, y, z) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
    faces = [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]
    return mesh_object(name, verts, faces, mat, center)


def wedge(name, center, width, y_back, y_front, z_bottom, z_back, z_front, mat):
    x = width * 0.5
    verts = [(-x, y_back, z_bottom), (x, y_back, z_bottom), (-x, y_front, z_bottom), (x, y_front, z_bottom),
             (-x, y_back, z_back), (x, y_back, z_back), (-x, y_front, z_front), (x, y_front, z_front)]
    faces = [(0, 1, 3, 2), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3), (4, 6, 7, 5)]
    return mesh_object(name, verts, faces, mat, center)


def beam(name, a, b, thickness, mat):
    obj = box(name, (0, 0, 0), (thickness, thickness, 1.0), mat)
    direction = Vector(b) - Vector(a)
    obj.location = BASE + (Vector(a) + Vector(b)) * 0.5
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    obj.scale.z = direction.length
    return obj


def wheel_mesh(name, loc):
    # 24 x 9 closed all-quad tire plus all-quad rim and 24 tread blocks.
    verts, faces, ids = [], [], []
    def q(a, b, c, d, mi): faces.append((a, b, c, d)); ids.append(mi)
    def ring(x, radius, n=24):
        start = len(verts)
        for i in range(n):
            angle = 2 * math.pi * i / n
            verts.append((x, radius * math.cos(angle), radius * math.sin(angle)))
        return start
    n = 24
    profile = [(0.255, -0.135), (0.310, -0.108), (0.340, -0.055), (0.340, 0.055), (0.310, 0.108), (0.255, 0.135), (0.165, 0.100), (0.120, 0.0), (0.165, -0.100)]
    loops = [ring(x, r, n) for r, x in profile]
    for j in range(len(loops)):
        for i in range(n):
            ni, nxt = (i + 1) % n, (j + 1) % len(loops)
            q(loops[j]+i, loops[j]+ni, loops[nxt]+ni, loops[nxt]+i, 0)
    rim = [ring(-0.142, 0.165, n), ring(0.142, 0.165, n), ring(0.142, 0.060, n), ring(-0.142, 0.060, n)]
    for j in range(4):
        for i in range(n):
            ni, nxt = (i + 1) % n, (j + 1) % 4
            q(rim[j]+i, rim[j]+ni, rim[nxt]+ni, rim[nxt]+i, 1)
    for i in range(12):
        for row, x in enumerate((-0.070, 0.070)):
            angle = 2 * math.pi * i / 12 + (math.pi / 12 if row else 0)
            start = len(verts)
            for sx in (-0.050, 0.050):
                for st in (-0.030, 0.030):
                    for sr in (-0.022, 0.022):
                        radius = 0.350 + sr
                        verts.append((x+sx, radius*math.cos(angle)-st*math.sin(angle), radius*math.sin(angle)+st*math.cos(angle)))
            for face in ((0,4,6,2), (1,3,7,5), (0,1,5,4), (2,6,7,3), (0,2,3,1), (4,5,7,6)):
                q(*(start+k for k in face), 0)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(RUBBER); mesh.materials.append(DARK)
    for poly, mi in zip(mesh.polygons, ids): poly.material_index = mi
    obj = bpy.data.objects.new(name, mesh); col.objects.link(obj); obj.location = BASE + Vector(loc)
    obj["all_quad_faces"] = len(faces); obj["tread_lugs"] = 24
    return obj


def missile(name, loc, parent=None):
    # Axis is local +Y; prism body plus pointed nose, deliberately low-poly.
    radius, body_len, nose_len, n = 0.045, 0.23, 0.095, 8
    verts = []
    for y in (-body_len*0.5, body_len*0.5):
        for i in range(n):
            a = 2*math.pi*i/n; verts.append((radius*math.cos(a), y, radius*math.sin(a)))
    tip = len(verts); verts.append((0, body_len*0.5+nose_len, 0))
    faces = []
    for i in range(n):
        ni = (i+1)%n; faces.append((i, ni, n+ni, n+i)); faces.append((n+i, n+ni, tip))
    obj = mesh_object(name, verts, faces, MISSILE, loc)
    if parent: obj.parent = parent
    return obj


root = bpy.data.objects.new("CLEAN_ROCKET_CAR_ROOT", None)
col.objects.link(root); root.location = BASE

# Chassis: a low center tub, central spine, and the distinctive armored wedge in front.
lower = box("Hull_Lower", (0, 0.0, 0.61), (1.16, 1.82, 0.34), DARK); lower.parent = root
spine = box("Hull_Spine", (0, -0.16, 0.91), (0.72, 1.30, 0.30), ARMOR); spine.parent = root
hood = wedge("Armor_Hood", (0, 0, 0), 1.30, 0.06, 1.43, 0.61, 1.05, 0.73, ARMOR); hood.parent = root
hood.location = BASE
hood_plate = wedge("Armor_Hood_Overlay", (0, 0, 0), 1.18, 0.12, 1.36, 1.045, 1.085, 0.755, DARK); hood_plate.parent = root; hood_plate.location = BASE
box("Armor_Hood_CenterPlate", (0, 0.72, 0.79), (0.42, 0.48, 0.055), ARMOR).parent = root

# Four wheels, exact numeric symmetry; front is +Y.
wheel_positions = {"FL": (-0.76, 0.72, 0.36), "FR": (0.76, 0.72, 0.36), "RL": (-0.76, -0.72, 0.36), "RR": (0.76, -0.72, 0.36)}
wheels = {key: wheel_mesh(f"Wheel_{key}", pos) for key, pos in wheel_positions.items()}
for key, pos in wheel_positions.items():
    x, y, z = pos
    beam(f"LowerArm_{key}", (x*0.55, y, 0.56), (x*0.92, y, z), 0.065, DARK).parent = root
    beam(f"UpperArm_{key}", (x*0.45, y, 0.83), (x*0.88, y, z+0.08), 0.055, ARMOR).parent = root
    beam(f"Shock_{key}", (x*0.42, y-0.09, 0.92), (x*0.72, y, 0.52), 0.050, DARK).parent = root

# Launcher pivot groups and two 2x3 missile arrays.
launchers = {}
for side, sx in (("L", -1), ("R", 1)):
    group = bpy.data.objects.new(f"Launcher_{side}_Group", None); col.objects.link(group); group.location = BASE + Vector((0.66*sx, -0.61, 1.17)); group.parent = root
    box_obj = box(f"Launcher_{side}_Housing", (0.66*sx, -0.61, 1.17), (0.48, 0.66, 0.34), ARMOR); box_obj.parent = group; box_obj.location -= group.location
    for row in range(2):
        for column in range(3):
            missile_obj = missile(f"Missile_{side}_{row}_{column}", (0.66*sx + (-0.10 if sx < 0 else 0.10), -0.36 + column*0.14, 1.14 + (row-0.5)*0.12), group)
            missile_obj.location -= group.location
    launchers[side] = group

# Small rear lamps and antenna to carry the reference silhouette.
for sx in (-0.42, 0.42):
    box("RearLamp_L" if sx < 0 else "RearLamp_R", (sx, -0.99, 0.76), (0.16, 0.045, 0.10), GLOW).parent = root
antenna = beam("Antenna", (0, -0.42, 1.02), (0, -0.42, 1.72), 0.018, DARK); antenna.parent = root

# Rig: only this compact armature creation uses operators; all visual geometry is Data API.
bones_before = {obj.name for obj in bpy.data.objects}
bpy.ops.object.armature_add(enter_editmode=True, location=BASE)
rig = next(obj for obj in bpy.data.objects if obj.name not in bones_before and obj.type == 'ARMATURE')
rig.name = "RTS_RocketCar_Rig"
rig.data.name = "RTS_RocketCar_Rig_Data"
rig.data.edit_bones.remove(rig.data.edit_bones[0])
eb = rig.data.edit_bones
def bone(name, head, tail, parent=None):
    b = eb.new(name); b.head = head; b.tail = tail; b.parent = parent; return b
root_b = bone("root", (0,0,0), (0,0,0.45))
chassis_b = bone("chassis", (0,0,0.45), (0,0,1.20), root_b)
bones = {"root": root_b, "chassis": chassis_b}
for key, (x,y,z) in wheel_positions.items():
    susp = bone(f"suspension_{key}", (x,y,0.82), (x,y,z), chassis_b)
    wheel_b = bone(f"wheel_{key}", (x,y,z), (x+0.22,y,z), susp)
    shock = bone(f"shock_{key}", (x*0.45,y-0.09,0.92), (x*0.72,y,0.52), chassis_b)
    bones[f"wheel_{key}"] = wheel_b; bones[f"suspension_{key}"] = susp; bones[f"shock_{key}"] = shock
for side, sx in (("L", -1), ("R", 1)):
    lb = bone(f"launcher_{side}_pitch", (0.66*sx,-0.61,1.17), (0.66*sx,-0.23,1.17), chassis_b)
    bones[f"launcher_{side}_pitch"] = lb
    for row in range(2):
        for column in range(3):
            mb = bone(f"missile_{side}_{row}_{column}", (0.66*sx + (-0.10 if sx < 0 else 0.10), -0.36+column*0.14, 1.14+(row-0.5)*0.12), (0.66*sx + (-0.10 if sx < 0 else 0.10), -0.08+column*0.14, 1.14+(row-0.5)*0.12), lb)
            bones[mb.name] = mb
bpy.ops.object.mode_set(mode='POSE')
for side in ("L", "R"):
    pb = rig.pose.bones[f"launcher_{side}_pitch"]
    limit = pb.constraints.new('LIMIT_ROTATION'); limit.owner_space = 'LOCAL'; limit.use_limit_x = True; limit.min_x = math.radians(-45); limit.max_x = math.radians(45)
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front = True

def parent_to_bone(obj, bone_name):
    world = obj.matrix_world.copy(); obj.parent = rig; obj.parent_type = 'BONE'; obj.parent_bone = bone_name; obj.matrix_world = world

for key, obj in wheels.items(): parent_to_bone(obj, f"wheel_{key}")
for side, group in launchers.items(): parent_to_bone(group, f"launcher_{side}_pitch")
for side in ("L", "R"):
    for row in range(2):
        for column in range(3):
            obj = bpy.data.objects.get(f"Missile_{side}_{row}_{column}")
            if obj: parent_to_bone(obj, f"missile_{side}_{row}_{column}")

rig["wheel_bones"] = 4
rig["suspension_bones"] = 4
rig["launcher_pitch_limits_deg"] = 45
rig["missile_bones"] = 12
print("RTS rocket car built: 4 wheels, independent suspension bones, 2 launcher pitch bones, 12 missile bones.")
