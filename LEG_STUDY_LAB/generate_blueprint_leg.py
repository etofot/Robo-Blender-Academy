import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler, Quaternion

# ----------------- PATHS & CONFIG -----------------
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"
ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
BLEND_FILE = os.path.join(OUT_DIR, "HARD_SURFACE_BLUEPRINT_LEG.blend")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

col_leg = bpy.data.collections.new('HARD_SURFACE_LEG')
col_gizmo = bpy.data.collections.new('LANDMARK_SKELETON')
scn.collection.children.link(col_leg)
scn.collection.children.link(col_gizmo)

def link(o, col=col_leg):
    col.objects.link(o)
    return o

# ----------------- HARD-SURFACE PBR MATERIALS -----------------
def create_mat(name, rgb, rough=0.35, metal=0.7, emit=None, strength=10.0, coat=0.0):
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (*rgb, 1.0)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if 'Coat Weight' in b.inputs: b.inputs['Coat Weight'].default_value = coat
        if emit:
            b.inputs['Emission Color'].default_value = (*emit, 1.0)
            b.inputs['Emission Strength'].default_value = strength
    return m

M_BALLISTIC = create_mat('M_BallisticDark', (0.045, 0.052, 0.065), rough=0.28, metal=0.85, coat=0.35)
M_ARMOR_WHITE = create_mat('M_ArmorWhite', (0.80, 0.82, 0.85), rough=0.30, metal=0.40, coat=0.5)
M_CHASSIS_GUN = create_mat('M_ChassisGun', (0.16, 0.17, 0.19), rough=0.38, metal=0.95)
M_HYDRAULIC_GOLD = create_mat('M_HydraulicGold', (0.88, 0.68, 0.22), rough=0.12, metal=1.0)
M_STEEL_CHROME = create_mat('M_SteelChrome', (0.75, 0.77, 0.80), rough=0.15, metal=0.98)
M_GLOW_CYAN = create_mat('M_GlowCyan', (0.02, 0.15, 0.25), rough=0.05, emit=(0.08, 0.85, 1.0), strength=14.0)

def set_mat(o, mat):
    o.data.materials.clear(); o.data.materials.append(mat); return o

def hs_bevel(o, width=0.002, segments=2):
    for p in o.data.polygons: p.use_smooth = True
    mod = o.modifiers.new('Bevel', 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(35)
    return o

# =========================================================================
# 1. LANDMARK GRAPH SCHEMA (Точечно-узловая кинематическая схема ноги)
# =========================================================================
# Все ключевые точки сопряжения, выверенные по Vulture и Anubis:
# Нога масштабирована к высоте ~0.24м (как у реального легкого робота)

P_HIP = Vector((0.040, -0.005, 0.130))
P_KNEE_TOP = Vector((0.052, 0.048, 0.076))       # Верхний палец кулисы
P_KNEE_BOT = Vector((0.052, 0.042, 0.062))       # Нижний палец кулисы (соединен с голенью)
P_HOCK_ELBOW = Vector((0.046, -0.038, 0.026))    # Скакательный сустав (обратный угол)
P_ANKLE = Vector((0.044, -0.022, 0.012))         # Шарнир голеностопной скобы
P_HEEL_TIP = Vector((0.044, -0.056, 0.004))      # Конец пяточного упора
P_TOE_BASE = Vector((0.044, 0.012, 0.008))       # Основание носовых пальцев
P_TOE_TIP = Vector((0.044, 0.058, 0.001))        # Кончик передней стопы

# Проушины навески гидравлики (Hardpoint Mounts):
P_CYL_HIP_MOUNT = Vector((0.034, -0.018, 0.118)) # Верхняя проушина цилиндра на бедре
P_ROD_HOCK_MOUNT = Vector((0.042, -0.018, 0.038))# Нижняя проушина штока на голени

# Проушины пальцевых амортизаторов:
P_TOE_ACTUATOR_TOP = Vector((0.044, -0.006, 0.018))
P_TOE_ACTUATOR_BOT = Vector((0.044, 0.032, 0.006))

# Отрисовка схемы опорных точек (Landmark Gizmos)
def make_landmark_point(name, pt, r=0.0035, col=(1.0, 0.2, 0.2)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=pt)
    o = bpy.context.object; o.name = name
    m = create_mat(f"Mat_Gizmo_{name}", col, rough=0.2, emit=col, strength=8.0)
    set_mat(o, m); link(o, col_gizmo)
    return o

def make_landmark_vector(name, p1, p2, r=0.0012, col=(0.2, 0.8, 1.0)):
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(p1 + p2)/2.0)
    o = bpy.context.object; o.name = name
    o.rotation_euler = Vector((0,0,1)).rotation_difference(d).to_euler()
    m = create_mat(f"Mat_Bone_{name}", col, rough=0.3, emit=col, strength=3.0)
    set_mat(o, m); link(o, col_gizmo)
    return o

print("Building Landmark Graph Points & Vectors...")
make_landmark_point("LM_Hip", P_HIP, col=(1.0, 0.8, 0.1))
make_landmark_point("LM_KneeTop", P_KNEE_TOP, col=(1.0, 0.3, 0.1))
make_landmark_point("LM_KneeBot", P_KNEE_BOT, col=(1.0, 0.3, 0.1))
make_landmark_point("LM_Ankle", P_ANKLE, col=(0.1, 0.8, 1.0))
make_landmark_point("LM_Heel", P_HEEL_TIP, col=(0.8, 0.2, 0.8))
make_landmark_point("LM_ToeTip", P_TOE_TIP, col=(0.2, 1.0, 0.3))

make_landmark_vector("Bone_Femur", P_HIP, P_KNEE_TOP)
make_landmark_vector("Bone_KneeLink", P_KNEE_TOP, P_KNEE_BOT)
make_landmark_vector("Bone_Tibia", P_KNEE_BOT, P_ANKLE)
make_landmark_vector("Bone_Foot", P_HEEL_TIP, P_TOE_TIP)
make_landmark_vector("Vector_Hydraulic", P_CYL_HIP_MOUNT, P_ROD_HOCK_MOUNT, col=(1.0, 0.7, 0.1))

# =========================================================================
# 2. HARD-SURFACE BUILDERS ПО ОПОРНЫМ ТОЧКАМ (Выдавливание и сопряжения)
# =========================================================================

# A. МОДУЛЬ ТАЗОБЕДРЕННОГО СУСТАВА (Octagonal Hip Hub с утопленной шайбой)
def build_hip_hub(center_pt):
    # 8-гранный главный диск
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.018, depth=0.016, location=center_pt, rotation=(0, math.radians(90), 0))
    hub = hs_bevel(bpy.context.object, width=0.0016)
    hub.name = "Hip_OctagonalHub"; set_mat(hub, M_BALLISTIC); link(hub)
    
    # Концентрический выступающий ступенчатый колпак с фаской
    cap_pt = center_pt + Vector((0.009, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.012, depth=0.005, location=cap_pt, rotation=(0, math.radians(90), 0))
    cap = hs_bevel(bpy.context.object, width=0.0012)
    cap.name = "Hip_OctagonalCap"; set_mat(cap, M_ARMOR_WHITE); link(cap)
    
    # Утопленная центральная шайба с болтом
    bolt_pt = center_pt + Vector((0.012, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.004, depth=0.003, location=bolt_pt, rotation=(0, math.radians(90), 0))
    b_obj = bpy.context.object; b_obj.name = "Hip_CenterBolt"; set_mat(b_obj, M_STEEL_CHROME); link(b_obj)
    
    # Проушина под верхний кронштейн гидроцилиндра (Clevis Mount)
    clevis_pt = P_CYL_HIP_MOUNT
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=clevis_pt)
    clevis = bpy.context.object; clevis.scale = (0.008, 0.012, 0.012)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(clevis, width=0.0012); clevis.name = "Hip_ClevisMount"; set_mat(clevis, M_CHASSIS_GUN); link(clevis)

# B. МОДУЛЬ БЕДРА (8-гранный пилон с передним скосом 45° и коленной вилкой)
def build_faceted_femur(p_start, p_end):
    dir_vec = p_end - p_start
    length = dir_vec.length
    mid_pt = (p_start + p_end) / 2.0
    rot = Vector((0,0,1)).rotation_difference(dir_vec).to_euler()
    
    # 8-гранный профиль, выдавленный вдоль оси кости
    bm = bmesh.new()
    # 8 вершин базового сечения
    pts_2d = [
        (-0.010, -0.015), (0.010, -0.015), (0.014, -0.006), (0.014, 0.008),
        (0.008, 0.016), (-0.008, 0.016), (-0.014, 0.008), (-0.014, -0.006)
    ]
    verts_bot = [bm.verts.new(Vector((x * 0.9, y * 0.85, -length * 0.46))) for x, y in pts_2d]
    verts_top = [bm.verts.new(Vector((x * 1.1, y * 1.15, length * 0.46))) for x, y in pts_2d]
    
    for i in range(8):
        i_next = (i + 1) % 8
        bm.faces.new((verts_bot[i], verts_bot[i_next], verts_top[i_next], verts_top[i]))
    bm.faces.new(verts_top)
    bm.faces.new(reversed(verts_bot))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    me = bpy.data.meshes.new('Femur_Mesh')
    bm.to_mesh(me); bm.free()
    femur = bpy.data.objects.new('Femur_FacetedPylon', me)
    femur.location = mid_pt
    femur.rotation_euler = rot
    link(femur); set_mat(femur, M_BALLISTIC); hs_bevel(femur, width=0.0016)
    
    # Передний белый накладной бронещит со скошенными краями
    shield_pt = mid_pt + Vector((0, 0.009, 0))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=shield_pt, rotation=rot)
    shield = bpy.context.object; shield.scale = (0.022, 0.007, length * 0.72)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(shield, width=0.0014); shield.name = "Femur_ArmorShield"; set_mat(shield, M_ARMOR_WHITE); link(shield)

# C. МОДУЛЬ КОЛЕННОЙ КУЛИСЫ (Pill-Linkage Plate с соосными цапфами)
def build_pill_knee_link(p_top, p_bot):
    mid_pt = (p_top + p_bot) / 2.0
    dir_vec = p_bot - p_top
    length = dir_vec.length
    rot = Vector((0,0,1)).rotation_difference(dir_vec).to_euler()
    
    # Капсульная кулиса (Pill Plate) толщиной 7 мм
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mid_pt, rotation=rot)
    pill = bpy.context.object; pill.scale = (0.007, 0.026, length + 0.016)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(pill, width=0.0035, segments=3) # Закругление торцов в капсулу!
    pill.name = "Knee_PillLinkage"; set_mat(pill, M_ARMOR_WHITE); link(pill)
    
    # Верхний поворотный палец-цапфа
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0075, depth=0.024, location=p_top, rotation=(0, math.radians(90), 0))
    pin_top = hs_bevel(bpy.context.object, width=0.001); pin_top.name = "Knee_PivotPin_Top"; set_mat(pin_top, M_STEEL_CHROME); link(pin_top)
    
    # Нижний поворотный палец-цапфа
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0075, depth=0.024, location=p_bot, rotation=(0, math.radians(90), 0))
    pin_bot = hs_bevel(bpy.context.object, width=0.001); pin_bot.name = "Knee_PivotPin_Bot"; set_mat(pin_bot, M_STEEL_CHROME); link(pin_bot)

# D. МОДУЛЬ ГОЛЕНИ С ОПЕРЕНИЕМ (Finned Tibia со стреловидными плавниками)
def build_finned_tibia(p_start, p_end):
    dir_vec = p_end - p_start
    length = dir_vec.length
    mid_pt = (p_start + p_end) / 2.0
    rot = Vector((0,0,1)).rotation_difference(dir_vec).to_euler()
    
    # Несущая шевронная балка
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mid_pt, rotation=rot)
    tibia = bpy.context.object; tibia.scale = (0.018, 0.028, length * 0.94)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(tibia, width=0.002); tibia.name = "Tibia_ChevronBeam"; set_mat(tibia, M_BALLISTIC); link(tibia)
    
    # ПЕРВЫЙ И ВТОРОЙ ХВОСТОВЫЕ ПЛАВНИКИ-ОТБОЙНИКИ (Двойные плавники Vulture!)
    quat = Vector((0,0,1)).rotation_difference(dir_vec)
    fin_root = p_start + dir_vec * 0.35
    
    for fin_i, fin_z_offset in enumerate((-0.012, 0.012)):
        # Плавник скошен назад под 45 градусов
        fin_loc = fin_root + quat @ Vector((0, -0.028, fin_z_offset))
        fin_rot = Euler((math.radians(45), 0, rot.z), 'XYZ')
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=fin_loc, rotation=fin_rot)
        fin = bpy.context.object; fin.scale = (0.005, 0.042, 0.014)
        bpy.ops.object.transform_apply(scale=True)
        hs_bevel(fin, width=0.0014); fin.name = f"Tibia_AeroFin_{fin_i}"; set_mat(fin, M_ARMOR_WHITE); link(fin)
        
    # Продольная канавка облегчения (Carbon Channel)
    pocket_loc = mid_pt + quat @ Vector((0.009, 0, 0))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=pocket_loc, rotation=rot)
    pocket = bpy.context.object; pocket.scale = (0.003, 0.016, length * 0.55)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(pocket, width=0.0008); pocket.name = "Tibia_LighteningPocket"; set_mat(pocket, M_CHASSIS_GUN); link(pocket)
    
    # Нижняя проушина крепления гидроцилиндра на скакательном угле
    h_clevis = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=P_ROD_HOCK_MOUNT)
    h_clevis = bpy.context.object; h_clevis.scale = (0.008, 0.010, 0.010)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(h_clevis, width=0.001); h_clevis.name = "Tibia_ShockMount"; set_mat(h_clevis, M_CHASSIS_GUN); link(h_clevis)

# E. МОДУЛЬ ГИДРОЦИЛИНДРА (Двухсоставной поршень точно по точкам проушин)
def build_hydraulic_actuator(p_top, p_bot):
    dir_vec = p_bot - p_top
    total_len = dir_vec.length
    rot = Vector((0,0,1)).rotation_difference(dir_vec).to_euler()
    
    # Верхняя гильза цилиндра (60% длины, заходит на верхнюю проушину)
    cyl_len = total_len * 0.58
    cyl_mid = p_top + dir_vec * 0.29
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0055, depth=cyl_len, location=cyl_mid, rotation=rot)
    cyl = hs_bevel(bpy.context.object, width=0.0008); cyl.name = "Hydraulic_Barrel"; set_mat(cyl, M_CHASSIS_GUN); link(cyl)
    
    # Нижний полированный шток (входит внутрь гильзы и крепится к нижней проушине)
    rod_len = total_len * 0.58
    rod_mid = p_bot - dir_vec * 0.29
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.0034, depth=rod_len, location=rod_mid, rotation=rot)
    rod = hs_bevel(bpy.context.object, width=0.0006); rod.name = "Hydraulic_PistonRod"; set_mat(rod, M_HYDRAULIC_GOLD); link(rod)
    
    # Верхняя и нижняя сферические проушины (Eyelet Rings)
    for p_mount, name in ((p_top, "Cyl_TopEyelet"), (p_bot, "Cyl_BotEyelet")):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.006, depth=0.009, location=p_mount, rotation=(0, math.radians(90), 0))
        eye = hs_bevel(bpy.context.object, width=0.0008); eye.name = name; set_mat(eye, M_STEEL_CHROME); link(eye)

# F. МОДУЛЬ ГОЛЕНОСТОПНОЙ СКОБЫ-ХОМУТА (U-Bracket Ankle Cuff)
def build_ankle_cuff(p_ankle):
    # U-образный хомут: центральная база + 2 боковых щеки
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=p_ankle + Vector((0, -0.002, 0)))
    cuff_base = bpy.context.object; cuff_base.scale = (0.026, 0.016, 0.012)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(cuff_base, width=0.0016); cuff_base.name = "Ankle_CuffBracket"; set_mat(cuff_base, M_ARMOR_WHITE); link(cuff_base)
    
    # Боковые цапфы фиксации в стопе
    for sx in (-1, 1):
        pin_pt = p_ankle + Vector((sx * 0.014, 0, 0))
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.005, depth=0.006, location=pin_pt, rotation=(0, math.radians(90), 0))
        p = hs_bevel(bpy.context.object, width=0.0008); p.name = f"Ankle_SidePin_{'R' if sx>0 else 'L'}"; set_mat(p, M_STEEL_CHROME); link(p)

# G. МОДУЛЬ АРОЧНОЙ СТОПЫ (Arched Foot Bridge с канавками и выштамповками)
def build_arched_foot(p_ankle, p_heel, p_toe_base, p_toe_tip):
    foot_mid = (p_heel + p_toe_tip) / 2.0
    foot_len = (p_toe_tip - p_heel).length
    
    # 1. АРОЧНАЯ ПОДОШВА С КЛИРЕНСОМ:
    # Контактная передняя подушка
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=p_toe_base + Vector((0, 0.012, -0.004)))
    toe_pad = bpy.context.object; toe_pad.scale = (0.028, 0.038, 0.008)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(toe_pad, width=0.0016); toe_pad.name = "Foot_FrontPad"; set_mat(toe_pad, M_BALLISTIC); link(toe_pad)
    
    # Контактный пяточный упор
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=p_heel + Vector((0, 0.010, -0.002)))
    heel_pad = bpy.context.object; heel_pad.scale = (0.026, 0.026, 0.010)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(heel_pad, width=0.0016); heel_pad.name = "Foot_HeelPad"; set_mat(heel_pad, M_BALLISTIC); link(heel_pad)
    
    # Несущий арочный мост (Bridge Spine), нависающий над землей!
    bridge_loc = foot_mid + Vector((0, 0, 0.006))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=bridge_loc)
    bridge = bpy.context.object; bridge.scale = (0.022, foot_len * 0.75, 0.014)
    bpy.ops.object.transform_apply(scale=True)
    hs_bevel(bridge, width=0.002); bridge.name = "Foot_ArchedSpine"; set_mat(bridge, M_ARMOR_WHITE); link(bridge)
    
    # 2. ПРОДОЛЬНЫЕ РЕЛЬЕФНЫЕ КАНАВКИ (Longitudinal Grooves на пальцах)
    for sx in (-0.006, 0.006):
        gr_loc = p_toe_base + Vector((sx, 0.018, 0.006))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=gr_loc, rotation=(math.radians(-10), 0, 0))
        gr = bpy.context.object; gr.scale = (0.0025, 0.028, 0.004)
        bpy.ops.object.transform_apply(scale=True)
        hs_bevel(gr, width=0.0006); gr.name = f"Foot_ToeGroove_{sx}"; set_mat(gr, M_CHASSIS_GUN); link(gr)
        
    # 3. БОКОВЫЕ ОВАЛЬНЫЕ ВЫШТАМПОВКИ (Pill Pocketing)
    for sx in (-1, 1):
        poc_loc = foot_mid + Vector((sx * 0.014, -0.004, 0.004))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=poc_loc)
        poc = bpy.context.object; poc.scale = (0.002, 0.018, 0.006)
        bpy.ops.object.transform_apply(scale=True)
        hs_bevel(poc, width=0.0018, segments=2) # Скругление в овал
        poc.name = f"Foot_SidePocket_{'R' if sx>0 else 'L'}"; set_mat(poc, M_CHASSIS_GUN); link(poc)
        
    # 4. Пальцевый стабилизирующий гидродемпфер
    d_vec = P_TOE_ACTUATOR_BOT - P_TOE_ACTUATOR_TOP
    d_rot = Vector((0,0,1)).rotation_difference(d_vec).to_euler()
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0028, depth=d_vec.length, location=(P_TOE_ACTUATOR_TOP + P_TOE_ACTUATOR_BOT)/2.0, rotation=d_rot)
    damper = hs_bevel(bpy.context.object, width=0.0006); damper.name = "Foot_ToeDamper"; set_mat(damper, M_HYDRAULIC_GOLD); link(damper)

# =========================================================================
# 3. ВЫПОЛНЕНИЕ СБОРКИ НОГИ
# =========================================================================
print("Executing Hard-Surface Assembly from Landmarks...")
build_hip_hub(P_HIP)
build_faceted_femur(P_HIP, P_KNEE_TOP)
build_pill_knee_link(P_KNEE_TOP, P_KNEE_BOT)
build_finned_tibia(P_KNEE_BOT, P_ANKLE)
build_hydraulic_actuator(P_CYL_HIP_MOUNT, P_ROD_HOCK_MOUNT)
build_ankle_cuff(P_ANKLE)
build_arched_foot(P_ANKLE, P_HEEL_TIP, P_TOE_BASE, P_TOE_TIP)

# =========================================================================
# 4. СТУДИЙНЫЙ РЕНДЕР И ДИАГНОСТИКА
# =========================================================================
print("Configuring Studio Render & Diagnostic Passes...")

world = bpy.data.worlds.new("Blueprint_World")
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.015, 0.020, 0.028, 1.0)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
scn.world = world

cam_data = bpy.data.cameras.new("Leg_Cam")
cam_obj = bpy.data.objects.new("Leg_Cam", cam_data)
scn.collection.objects.link(cam_obj)
scn.camera = cam_obj

# Sun Lights
sun1 = bpy.data.lights.new("Sun1", type='SUN'); sun1.energy = 5.5; sun1.color = (1.0, 0.98, 0.95)
o_s1 = bpy.data.objects.new("Sun1", sun1); o_s1.rotation_euler = (math.radians(55), math.radians(20), math.radians(50))
scn.collection.objects.link(o_s1)

sun2 = bpy.data.lights.new("Sun2", type='SUN'); sun2.energy = 4.0; sun2.color = (0.25, 0.80, 1.0)
o_s2 = bpy.data.objects.new("Sun2", sun2); o_s2.rotation_euler = (math.radians(-35), math.radians(-30), math.radians(-130))
scn.collection.objects.link(o_s2)

scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1200
scn.render.resolution_y = 1200

center = Vector((0.044, 0.002, 0.065))

# Рендер 1: Hero Perspective (Готовая Hard-Surface нога в PBR)
col_gizmo.hide_render = True
cam_data.type = 'PERSP'; cam_data.lens = 75
cam_obj.location = (0.24, -0.22, 0.12)
cam_obj.rotation_euler = (center - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

p_hero = os.path.join(OUT_DIR, "procedural_leg_1_hero_pbr.png")
scn.render.filepath = p_hero; bpy.ops.render.render(write_still=True)

# Рендер 2: Ортографический профиль сбоку (Side Profile в PBR)
cam_data.type = 'ORTHO'; cam_data.ortho_scale = 0.17
cam_obj.location = (0.35, 0.002, 0.065)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

p_side_pbr = os.path.join(OUT_DIR, "procedural_leg_2_side_pbr.png")
scn.render.filepath = p_side_pbr; bpy.ops.render.render(write_still=True)

# Рендер 3: Оверлей схемы Landmark Skeleton поверх геометрии
col_gizmo.hide_render = False
p_skeleton = os.path.join(OUT_DIR, "procedural_leg_3_skeleton_overlay.png")
scn.render.filepath = p_skeleton; bpy.ops.render.render(write_still=True)

# Рендер 4: Сетка (Wireframe) профиля
col_gizmo.hide_render = True
for o in col_leg.objects:
    wf = o.modifiers.new('Wf', 'WIREFRAME')
    wf.thickness = 0.0006; wf.use_replace = False

p_wire = os.path.join(OUT_DIR, "procedural_leg_4_wire_side.png")
scn.render.filepath = p_wire; bpy.ops.render.render(write_still=True)

# Сохранение .blend
bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
print(f"Master Blueprint Leg blend saved: {BLEND_FILE}")

# Копирование в артефакты
for p in [p_hero, p_side_pbr, p_skeleton, p_wire]:
    shutil.copyfile(p, os.path.join(ART_DIR, os.path.basename(p)))

print("=== SCRIPT FINISHED SUCCESSFULLY ===")

