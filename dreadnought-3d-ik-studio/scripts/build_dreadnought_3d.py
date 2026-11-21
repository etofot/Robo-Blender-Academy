import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import math

# ==============================================================================
# 1. MATERIALS PALETTE
# ==============================================================================
MATERIALS = {
    'armor_dark':    {'color': (0.22, 0.25, 0.29), 'spec': 0.40, 'emit': 0.0},
    'armor_mid':     {'color': (0.32, 0.36, 0.41), 'spec': 0.50, 'emit': 0.0},
    'armor_light':   {'color': (0.43, 0.47, 0.52), 'spec': 0.55, 'emit': 0.0},
    'steel_dark':    {'color': (0.13, 0.15, 0.17), 'spec': 0.65, 'emit': 0.0},
    'steel_bright':  {'color': (0.60, 0.64, 0.68), 'spec': 0.85, 'emit': 0.0},
    'accent_orange': {'color': (0.82, 0.45, 0.14), 'spec': 0.35, 'emit': 0.0},
    'glow_amber':    {'color': (1.00, 0.58, 0.10), 'spec': 0.90, 'emit': 1.0},
    'glow_cyan':     {'color': (0.30, 0.90, 1.00), 'spec': 0.90, 'emit': 1.0},
}

class MeshPart:
    def __init__(self, name):
        self.name = name
        self.verts = []
        self.faces = []
        self.mats = []
        self.v_offset = 0

    def add_mesh(self, v, f, mat_name):
        v = np.asarray(v, dtype=np.float32)
        f = np.asarray(f, dtype=np.int32) + self.v_offset
        self.verts.append(v)
        self.faces.append(f)
        self.mats.extend([mat_name] * len(f))
        self.v_offset += len(v)

    def finalize(self):
        if not self.verts:
            return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.int32), []
        return np.vstack(self.verts), np.vstack(self.faces), self.mats

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]], dtype=np.float32)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]], dtype=np.float32)

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]], dtype=np.float32)

def transform_verts(v, R=None, T=None, S=None):
    v = np.asarray(v, dtype=np.float32).copy()
    if S is not None:
        v = v * np.asarray(S, dtype=np.float32)
    if R is not None:
        v = v @ R.T
    if T is not None:
        v = v + np.asarray(T, dtype=np.float32)
    return v

def make_chamfer_box(sx, sy, sz, chamfer=0.06, top_taper=(1.0, 1.0), front_taper=1.0, center=(0,0,0), R=None):
    """Creates a beveled/tapered hard-surface armor hull."""
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    c = min(chamfer, hx*0.42, hy*0.42, hz*0.42)
    y_vals = [-hy, -hy + c, hy - c, hy]
    tx, tz = top_taper
    scales = [
        (hx - c,        hz - c,        1.0),
        (hx,            hz,            1.0),
        (hx * tx,       hz * tz,       front_taper),
        (hx * tx - c,   hz * tz - c,   front_taper)
    ]
    ring_pts = []
    for (rx, rz, ft), y in zip(scales, y_vals):
        rx = max(rx, 0.01)
        rz = max(rz, 0.01)
        bc = min(c, rx*0.35, rz*0.35)
        rxf = rx * ft
        pts = [
            [-rxf+bc, y,  rz], [ rxf-bc, y,  rz],
            [ rxf,    y,  rz-bc], [ rx,    y, -rz+bc],
            [ rx-bc,  y, -rz], [-rx+bc,  y, -rz],
            [-rx,     y, -rz+bc], [-rxf,   y,  rz-bc]
        ]
        ring_pts.extend(pts)
    verts = np.array(ring_pts, dtype=np.float32)
    faces = []
    for r in range(3):
        b0, b1 = r * 8, (r + 1) * 8
        for i in range(8):
            ni = (i + 1) % 8
            faces.append([b0+i, b0+ni, b1+ni])
            faces.append([b0+i, b1+ni, b1+i])
    bot_c, top_c = len(verts), len(verts) + 1
    verts = np.vstack([verts, [[0, -hy, 0], [0, hy, 0]]])
    for i in range(8):
        ni = (i + 1) % 8
        faces.append([bot_c, ni, i])
        faces.append([top_c, 24 + i, 24 + ni])
    verts = transform_verts(verts, R=R, T=center)
    return verts, np.array(faces, dtype=np.int32)

def make_cylinder(r_bot, r_top, height, segs=16, center=(0,0,0), axis='y', R=None):
    hy = height * 0.5
    angles = np.linspace(0, 2*np.pi, segs, endpoint=False)
    ca, sa = np.cos(angles), np.sin(angles)
    bot = np.stack([r_bot*ca, np.full_like(ca, -hy), r_bot*sa], axis=1)
    top = np.stack([r_top*ca, np.full_like(ca,  hy), r_top*sa], axis=1)
    verts = np.vstack([bot, top, [[0, -hy, 0], [0, hy, 0]]]).astype(np.float32)
    faces = []
    bc, tc = 2*segs, 2*segs + 1
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append([i, ni, segs + ni])
        faces.append([i, segs + ni, segs + i])
        faces.append([bc, ni, i])
        faces.append([tc, segs + i, segs + ni])
    if axis == 'x':
        verts = transform_verts(verts, R=rot_z(-np.pi/2))
    elif axis == 'z':
        verts = transform_verts(verts, R=rot_x(np.pi/2))
    verts = transform_verts(verts, R=R, T=center)
    return verts, np.array(faces, dtype=np.int32)

def make_tube(r_outer, r_inner, height, segs=16, center=(0,0,0), axis='z', R=None):
    hy = height * 0.5
    angles = np.linspace(0, 2*np.pi, segs, endpoint=False)
    ca, sa = np.cos(angles), np.sin(angles)
    ob = np.stack([r_outer*ca, np.full_like(ca, -hy), r_outer*sa], axis=1)
    ot = np.stack([r_outer*ca, np.full_like(ca,  hy), r_outer*sa], axis=1)
    ib = np.stack([r_inner*ca, np.full_like(ca, -hy), r_inner*sa], axis=1)
    it = np.stack([r_inner*ca, np.full_like(ca,  hy), r_inner*sa], axis=1)
    verts = np.vstack([ob, ot, ib, it]).astype(np.float32)
    faces = []
    for i in range(segs):
        ni = (i + 1) % segs
        faces.append([i, ni, segs+ni])
        faces.append([i, segs+ni, segs+i])
        faces.append([2*segs+i, 3*segs+ni, 2*segs+ni])
        faces.append([2*segs+i, 3*segs+i, 3*segs+ni])
        faces.append([segs+i, segs+ni, 3*segs+ni])
        faces.append([segs+i, 3*segs+ni, 3*segs+i])
        faces.append([i, 2*segs+ni, ni])
        faces.append([i, 2*segs+i, 2*segs+ni])
    if axis == 'x':
        verts = transform_verts(verts, R=rot_z(-np.pi/2))
    elif axis == 'z':
        verts = transform_verts(verts, R=rot_x(np.pi/2))
    verts = transform_verts(verts, R=R, T=center)
    return verts, np.array(faces, dtype=np.int32)

# ==============================================================================
# 2. SCULPTED HARD-SURFACE DREADNOUGHT HIERARCHY
# ==============================================================================
def build_dreadnought_parts():
    parts = {}

    # ---------------- PELVIS & WAIST ----------------
    pelvis = MeshPart('pelvis')
    # Central armored pelvis core
    v, f = make_chamfer_box(0.96, 0.48, 0.86, chamfer=0.09, top_taper=(1.08, 1.0), center=(0, 0.0, 0))
    pelvis.add_mesh(v, f, 'armor_dark')
    # Front central codpiece / thruster block
    v, f = make_chamfer_box(0.46, 0.56, 0.34, chamfer=0.07, top_taper=(1.15, 1.0), center=(0, -0.08, 0.38), R=rot_x(0.12))
    pelvis.add_mesh(v, f, 'armor_mid')
    v, f = make_chamfer_box(0.32, 0.08, 0.06, chamfer=0.01, center=(0, -0.24, 0.54), R=rot_x(0.12))
    pelvis.add_mesh(v, f, 'accent_orange')
    # Side hip skirts / piston mounts
    for sx in [-1, 1]:
        v, f = make_chamfer_box(0.22, 0.32, 0.64, chamfer=0.05, center=(sx*0.54, 0.06, 0.04), R=rot_z(-sx*0.25))
        pelvis.add_mesh(v, f, 'armor_light')
        # Heavy hip ball/cylinder axle
        v, f = make_cylinder(0.21, 0.21, 0.42, segs=16, center=(sx*0.58, -0.08, 0), axis='x')
        pelvis.add_mesh(v, f, 'steel_dark')
        v, f = make_cylinder(0.14, 0.14, 0.52, segs=14, center=(sx*0.58, -0.08, 0), axis='x')
        pelvis.add_mesh(v, f, 'steel_bright')
    # Waist turret ring & hydraulic spine
    v, f = make_cylinder(0.44, 0.48, 0.34, segs=20, center=(0, 0.34, 0), axis='y')
    pelvis.add_mesh(v, f, 'steel_dark')
    v, f = make_cylinder(0.49, 0.49, 0.06, segs=20, center=(0, 0.28, 0), axis='y')
    pelvis.add_mesh(v, f, 'steel_bright')
    parts['pelvis'] = pelvis

    # ---------------- TORSO, OPTICAL SENSOR POD & TWIN REACTORS ----------------
    torso = MeshPart('torso')
    # Main sculpted faceted chest core (tapered toward front like a tank glacis)
    v, f = make_chamfer_box(1.56, 1.15, 1.28, chamfer=0.18, top_taper=(1.08, 0.94), front_taper=0.78, center=(0, 0.88, 0.0))
    torso.add_mesh(v, f, 'armor_dark')
    # Central upper glacis breastplate (angled forward)
    v, f = make_chamfer_box(0.92, 0.54, 0.42, chamfer=0.10, front_taper=0.82, center=(0, 0.72, 0.54), R=rot_x(0.32))
    torso.add_mesh(v, f, 'armor_mid')
    # Center chest ID plaque & vent slot
    v, f = make_chamfer_box(0.42, 0.18, 0.08, chamfer=0.02, center=(0, 0.68, 0.74), R=rot_x(0.32))
    torso.add_mesh(v, f, 'armor_light')
    # Lower abdominal sloped plate
    v, f = make_chamfer_box(0.88, 0.38, 0.44, chamfer=0.07, front_taper=0.80, center=(0, 0.38, 0.46), R=rot_x(-0.42))
    torso.add_mesh(v, f, 'armor_dark')

    # Angled side cheek armor plates with recessed circular sub-sensors (dark lenses, not giant bulbs)
    for sx in [-1, 1]:
        v, f = make_chamfer_box(0.42, 0.58, 0.48, chamfer=0.08, center=(sx*0.58, 0.72, 0.46), R=rot_y(sx*0.42) @ rot_x(0.15))
        torso.add_mesh(v, f, 'armor_mid')
        # Recessed dark optical port on side cheek
        v, f = make_tube(0.11, 0.07, 0.08, segs=14, center=(sx*0.64, 0.70, 0.66), axis='z', R=rot_y(sx*0.42))
        torso.add_mesh(v, f, 'steel_dark')
        v, f = make_cylinder(0.065, 0.065, 0.04, segs=12, center=(sx*0.64, 0.70, 0.66), axis='z', R=rot_y(sx*0.42))
        torso.add_mesh(v, f, 'accent_orange')
        # Exposed waist-to-chest hydraulic pistons
        v, f = make_cylinder(0.065, 0.065, 0.48, segs=12, center=(sx*0.44, 0.38, 0.28), axis='y', R=rot_z(sx*0.14))
        torso.add_mesh(v, f, 'steel_bright')
        v, f = make_cylinder(0.085, 0.085, 0.24, segs=12, center=(sx*0.46, 0.28, 0.28), axis='y', R=rot_z(sx*0.14))
        torso.add_mesh(v, f, 'steel_dark')
        # Upper collar intakes flanking sensor pod
        v, f = make_chamfer_box(0.32, 0.28, 0.52, chamfer=0.06, center=(sx*0.52, 1.34, 0.16), R=rot_z(-sx*0.18))
        torso.add_mesh(v, f, 'armor_mid')
        # Shoulder joint drum & orange collar ring
        v, f = make_cylinder(0.34, 0.34, 0.36, segs=18, center=(sx*0.86, 1.02, 0.0), axis='x')
        torso.add_mesh(v, f, 'steel_dark')
        v, f = make_tube(0.38, 0.33, 0.08, segs=18, center=(sx*0.78, 1.02, 0.0), axis='x')
        torso.add_mesh(v, f, 'accent_orange')

    # Recessed Central Optical Sensor Pod (Armored Octagonal Hood + 4 Amber Lenses)
    v, f = make_chamfer_box(0.68, 0.52, 0.62, chamfer=0.11, top_taper=(0.82, 0.90), front_taper=0.85, center=(0, 1.22, 0.35))
    torso.add_mesh(v, f, 'armor_mid')
    # Deep dark recessed sensor bay
    v, f = make_chamfer_box(0.46, 0.36, 0.22, chamfer=0.06, center=(0, 1.20, 0.58))
    torso.add_mesh(v, f, 'steel_dark')
    # Brass/Orange octagonal sensor housing plate
    v, f = make_chamfer_box(0.38, 0.30, 0.08, chamfer=0.06, center=(0, 1.20, 0.67))
    torso.add_mesh(v, f, 'accent_orange')
    # 4 Distinct camera lenses with dark steel bezels and amber glass cores
    lens_specs = [
        ( 0.00, 1.13, 0.71, 0.075), # Main lower rangefinder lens
        (-0.10, 1.25, 0.71, 0.052), # Upper left optical sensor
        ( 0.10, 1.25, 0.71, 0.052), # Upper right optical sensor
        ( 0.00, 1.27, 0.71, 0.035), # Top laser targeter
    ]
    for lx, ly, lz, lr in lens_specs:
        v, f = make_tube(lr*1.32, lr*0.95, 0.06, segs=14, center=(lx, ly, lz), axis='z')
        torso.add_mesh(v, f, 'steel_dark')
        v, f = make_cylinder(lr*0.95, lr*0.95, 0.04, segs=14, center=(lx, ly, lz+0.01), axis='z')
        torso.add_mesh(v, f, 'glow_amber')

    # Twin Upper-Back Fusion Turbine Reactors
    for sx in [-1, 1]:
        rx, ry, rz = sx*0.42, 1.56, -0.32
        v, f = make_cylinder(0.24, 0.22, 0.20, segs=16, center=(rx, ry-0.10, rz), axis='y')
        torso.add_mesh(v, f, 'steel_dark')
        # Glowing turbine core
        v, f = make_cylinder(0.19, 0.19, 0.20, segs=16, center=(rx, ry+0.06, rz), axis='y')
        torso.add_mesh(v, f, 'glow_amber')
        # Protective cage ribs & rings
        for r_off in [-0.02, 0.06, 0.14]:
            v, f = make_tube(0.215, 0.185, 0.025, segs=16, center=(rx, ry+r_off, rz), axis='y')
            torso.add_mesh(v, f, 'steel_dark')
        for bi in range(8):
            ang = bi * (2*np.pi / 8)
            bx, bz = rx + 0.205 * math.cos(ang), rz + 0.205 * math.sin(ang)
            v, f = make_cylinder(0.018, 0.018, 0.22, segs=8, center=(bx, ry+0.06, bz), axis='y')
            torso.add_mesh(v, f, 'steel_dark')
        # Beveled top nozzle cap
        v, f = make_tube(0.23, 0.14, 0.10, segs=16, center=(rx, ry+0.20, rz), axis='y')
        torso.add_mesh(v, f, 'armor_light')

    # Rear Armored Reactor Backpack & Slanted Heat-Sink Louvers
    v, f = make_chamfer_box(1.18, 0.96, 0.48, chamfer=0.10, top_taper=(0.92, 0.90), center=(0, 0.88, -0.68))
    torso.add_mesh(v, f, 'armor_mid')
    for i in range(5):
        v, f = make_chamfer_box(0.76, 0.07, 0.14, chamfer=0.015, center=(0, 0.58 + i*0.14, -0.92), R=rot_x(0.25))
        torso.add_mesh(v, f, 'steel_dark')
    parts['torso'] = torso

    # ---------------- SHOULDERS & HEX MISSILE PODS ----------------
    for side, sx in [('L', 1), ('R', -1)]:
        sh = MeshPart(f'shoulder_{side}')
        # Upper sloped pauldron armor
        v, f = make_chamfer_box(0.62, 0.58, 0.82, chamfer=0.10, top_taper=(0.82, 0.88), center=(sx*1.18, 1.06, 0.0), R=rot_z(-sx*0.15))
        sh.add_mesh(v, f, 'armor_mid')
        # Outer lower pauldron plate with orange tactical stripe
        v, f = make_chamfer_box(0.66, 0.22, 0.84, chamfer=0.05, center=(sx*1.23, 0.74, 0.0), R=rot_z(-sx*0.10))
        sh.add_mesh(v, f, 'armor_dark')
        v, f = make_chamfer_box(0.68, 0.08, 0.85, chamfer=0.02, center=(sx*1.25, 0.65, 0.0), R=rot_z(-sx*0.10))
        sh.add_mesh(v, f, 'accent_orange')
        # Front & rear bolt caps on shoulder armor
        for sz in [-1, 1]:
            v, f = make_cylinder(0.11, 0.11, 0.08, segs=14, center=(sx*1.16, 1.02, sz*0.41), axis='z')
            sh.add_mesh(v, f, 'steel_bright')
            v, f = make_cylinder(0.07, 0.07, 0.10, segs=12, center=(sx*1.16, 1.02, sz*0.42), axis='z')
            sh.add_mesh(v, f, 'steel_dark')

        # Shoulder-Mounted Hexagonal 7-Tube Micro-Missile Pod
        px, py, pz = sx*1.10, 1.54, 0.04
        v, f = make_chamfer_box(0.52, 0.46, 0.72, chamfer=0.09, center=(px, py, pz))
        sh.add_mesh(v, f, 'armor_dark')
        # Recessed launch tube matrix face
        v, f = make_chamfer_box(0.40, 0.34, 0.06, chamfer=0.04, center=(px, py, pz+0.35))
        sh.add_mesh(v, f, 'steel_dark')
        offsets = [(0,0)] + [(0.115*math.cos(k*np.pi/3), 0.115*math.sin(k*np.pi/3)) for k in range(6)]
        for ox, oy in offsets:
            v, f = make_tube(0.048, 0.036, 0.08, segs=12, center=(px+ox, py+oy, pz+0.37), axis='z')
            sh.add_mesh(v, f, 'steel_bright')
            v, f = make_cylinder(0.032, 0.008, 0.06, segs=10, center=(px+ox, py+oy, pz+0.39), axis='z')
            sh.add_mesh(v, f, 'accent_orange')
        # Open Armored Blast Hatch on top of pod
        v, f = make_chamfer_box(0.46, 0.05, 0.36, chamfer=0.015, center=(px, py+0.34, pz+0.44), R=rot_x(-0.92))
        sh.add_mesh(v, f, 'armor_light')
        parts[f'shoulder_{side}'] = sh

    # ---------------- RIGHT ARM: SEISMIC CRUSHER CLAW + ENERGY SHIELD (-X) ----------------
    arm_R = MeshPart('arm_R')
    ax = -1.22
    # Upper arm & hydraulic cylinder
    v, f = make_cylinder(0.18, 0.17, 0.48, segs=16, center=(ax, 0.42, 0), axis='y')
    arm_R.add_mesh(v, f, 'steel_dark')
    v, f = make_chamfer_box(0.36, 0.34, 0.40, chamfer=0.05, center=(ax, 0.42, 0))
    arm_R.add_mesh(v, f, 'armor_dark')
    # Elbow joint drum
    v, f = make_cylinder(0.20, 0.20, 0.42, segs=16, center=(ax, 0.12, 0), axis='x')
    arm_R.add_mesh(v, f, 'steel_bright')

    # Forearm assembly angled slightly forward (rx_arm = 0.28 rad)
    R_fa = rot_x(0.28)
    fa_c = np.array([ax, -0.24, 0.12], dtype=np.float32)
    # Main armored forearm gauntlet (faceted octagonal cylinder)
    v, f = make_chamfer_box(0.46, 0.56, 0.48, chamfer=0.10, top_taper=(0.88, 0.88), center=fa_c, R=R_fa)
    arm_R.add_mesh(v, f, 'armor_mid')
    # Wrist rotary chuck & orange collar band (aligned with forearm axis!)
    wrist_c = fa_c + R_fa @ np.array([0, -0.32, 0], dtype=np.float32)
    v, f = make_cylinder(0.24, 0.26, 0.12, segs=18, center=wrist_c, axis='y', R=R_fa)
    arm_R.add_mesh(v, f, 'accent_orange')
    chuck_c = fa_c + R_fa @ np.array([0, -0.42, 0], dtype=np.float32)
    v, f = make_cylinder(0.26, 0.22, 0.14, segs=18, center=chuck_c, axis='y', R=R_fa)
    arm_R.add_mesh(v, f, 'steel_dark')

    # Side-Mounted Energy Shield Emitter on outer right forearm
    sh_c = fa_c + R_fa @ np.array([-0.26, -0.02, 0.02], dtype=np.float32)
    v, f = make_chamfer_box(0.16, 0.50, 0.32, chamfer=0.04, center=sh_c, R=R_fa)
    arm_R.add_mesh(v, f, 'armor_dark')
    em_c = fa_c + R_fa @ np.array([-0.33, -0.08, 0.04], dtype=np.float32)
    v, f = make_chamfer_box(0.08, 0.28, 0.18, chamfer=0.03, top_taper=(0.7, 0.7), center=em_c, R=R_fa)
    arm_R.add_mesh(v, f, 'glow_cyan')

    # 3-Fingered Articulated Seismic Crusher Claw
    for ci in range(3):
        ca = ci * (2*np.pi / 3.0) + 0.52
        R_jaw = R_fa @ rot_y(ca)
        # Knuckle mount
        kn_c = chuck_c + R_jaw @ np.array([0.16, -0.04, 0], dtype=np.float32)
        v, f = make_chamfer_box(0.12, 0.12, 0.14, chamfer=0.02, center=kn_c, R=R_jaw)
        arm_R.add_mesh(v, f, 'steel_bright')
        # Proximal jaw beam (angled outward)
        p1_c = chuck_c + R_jaw @ np.array([0.22, -0.22, 0], dtype=np.float32)
        v, f = make_chamfer_box(0.10, 0.34, 0.14, chamfer=0.02, center=p1_c, R=R_jaw @ rot_z(-0.28))
        arm_R.add_mesh(v, f, 'steel_bright')
        # Distal crusher talon (angled inward to pinch)
        p2_c = chuck_c + R_jaw @ np.array([0.18, -0.50, 0], dtype=np.float32)
        v, f = make_chamfer_box(0.08, 0.32, 0.12, chamfer=0.02, top_taper=(0.5, 0.7), center=p2_c, R=R_jaw @ rot_z(0.48))
        arm_R.add_mesh(v, f, 'armor_dark')
    parts['arm_R'] = arm_R

    # ---------------- LEFT ARM: TWIN-BARREL ELECTROMAGNETIC RAIL-CANNON (+X) ----------------
    arm_L = MeshPart('arm_L')
    lx = 1.22
    # Upper arm
    v, f = make_cylinder(0.18, 0.17, 0.48, segs=16, center=(lx, 0.42, 0), axis='y')
    arm_L.add_mesh(v, f, 'steel_dark')
    v, f = make_chamfer_box(0.36, 0.34, 0.40, chamfer=0.05, center=(lx, 0.42, 0))
    arm_L.add_mesh(v, f, 'armor_dark')
    # Elbow drum
    v, f = make_cylinder(0.20, 0.20, 0.42, segs=16, center=(lx, 0.12, 0), axis='x')
    arm_L.add_mesh(v, f, 'steel_bright')

    # Rail-Cannon assembly in local frame (gun_origin + R_gun)
    R_gun = rot_x(0.16)
    gun_o = np.array([lx, -0.08, 0.22], dtype=np.float32)
    # Heavy receiver housing
    v, f = make_chamfer_box(0.44, 0.44, 0.78, chamfer=0.06, center=gun_o, R=R_gun)
    arm_L.add_mesh(v, f, 'armor_mid')
    # Orange side plates on receiver
    v, f = make_chamfer_box(0.46, 0.16, 0.36, chamfer=0.02, center=gun_o + R_gun @ np.array([0, 0.04, 0.12]), R=R_gun)
    arm_L.add_mesh(v, f, 'accent_orange')

    # Underslung Drum Magazine & Curved Segmented Ammo Chute
    drum_c = gun_o + R_gun @ np.array([-0.04, -0.36, -0.14], dtype=np.float32)
    v, f = make_cylinder(0.25, 0.25, 0.38, segs=18, center=drum_c, axis='x', R=R_gun)
    arm_L.add_mesh(v, f, 'armor_dark')
    v, f = make_tube(0.26, 0.18, 0.06, segs=18, center=drum_c + R_gun @ np.array([0.17, 0, 0]), axis='x', R=R_gun)
    arm_L.add_mesh(v, f, 'accent_orange')
    # Curved ammo belt segments looping from drum to receiver
    for bi in range(6):
        t_ang = -0.3 + bi * 0.38
        bx_loc = 0.22 * math.cos(t_ang) + 0.06
        by_loc = -0.22 - 0.18 * math.sin(t_ang)
        bz_loc = 0.12 + bi * 0.03
        seg_c = gun_o + R_gun @ np.array([bx_loc, by_loc, bz_loc], dtype=np.float32)
        v, f = make_chamfer_box(0.08, 0.05, 0.12, chamfer=0.01, center=seg_c, R=R_gun @ rot_z(t_ang))
        arm_L.add_mesh(v, f, 'steel_dark' if bi % 2 == 0 else 'steel_bright')

    # Twin Electromagnetic Barrels with Segmented Plasma Cooling Coils
    for by_off in [0.10, -0.10]:
        # Inner steel barrel core
        b_core = gun_o + R_gun @ np.array([0, by_off, 0.72], dtype=np.float32)
        v, f = make_cylinder(0.045, 0.045, 0.82, segs=12, center=b_core, axis='z', R=R_gun)
        arm_L.add_mesh(v, f, 'steel_dark')
        # Alternating glowing orange plasma coils and dark cooling fins (prevents over-bloom!)
        for ri in range(9):
            rz_off = 0.44 + ri * 0.06
            rc_pos = gun_o + R_gun @ np.array([0, by_off, rz_off], dtype=np.float32)
            mat_n = 'glow_amber' if ri % 2 == 0 else 'steel_dark'
            rad_c = 0.068 if ri % 2 == 0 else 0.076
            v, f = make_cylinder(rad_c, rad_c, 0.028, segs=14, center=rc_pos, axis='z', R=R_gun)
            arm_L.add_mesh(v, f, mat_n)
        # Heavy cylindrical muzzle brake at tip
        mz_pos = gun_o + R_gun @ np.array([0, by_off, 1.12], dtype=np.float32)
        v, f = make_tube(0.085, 0.048, 0.26, segs=16, center=mz_pos, axis='z', R=R_gun)
        arm_L.add_mesh(v, f, 'steel_bright')
    # Top, middle, and bottom rail shrouds binding the twin barrels
    for sy_sh in [0.20, 0.0, -0.20]:
        sh_pos = gun_o + R_gun @ np.array([0, sy_sh, 0.74], dtype=np.float32)
        v, f = make_chamfer_box(0.18, 0.045, 0.76, chamfer=0.01, center=sh_pos, R=R_gun)
        arm_L.add_mesh(v, f, 'armor_dark')
    parts['arm_L'] = arm_L

    # ---------------- BIPEDAL LEGS (THIGHS, KNEES, SHINS, 4-TOED FEET) ----------------
    for side, sx in [('L', 1), ('R', -1)]:
        leg = MeshPart(f'leg_{side}')
        lx = sx * 0.64
        # Sculpted Upper Thigh Armor Block
        v, f = make_chamfer_box(0.50, 0.76, 0.62, chamfer=0.09, top_taper=(0.92, 0.92), center=(lx, -0.36, 0.04), R=rot_x(-0.14))
        leg.add_mesh(v, f, 'armor_mid')
        # Outer Thigh Hydraulic Cylinder & Chrome Piston Rod
        v, f = make_cylinder(0.075, 0.075, 0.36, segs=12, center=(lx + sx*0.26, -0.22, -0.08), axis='y', R=rot_x(-0.14))
        leg.add_mesh(v, f, 'steel_dark')
        v, f = make_cylinder(0.052, 0.052, 0.62, segs=12, center=(lx + sx*0.26, -0.38, -0.10), axis='y', R=rot_x(-0.14))
        leg.add_mesh(v, f, 'steel_bright')

        # Heavy Knee Joint & Layered Knee Guard
        v, f = make_cylinder(0.22, 0.22, 0.52, segs=16, center=(lx, -0.78, 0.12), axis='x')
        leg.add_mesh(v, f, 'steel_dark')
        v, f = make_chamfer_box(0.42, 0.38, 0.28, chamfer=0.06, top_taper=(0.85, 0.90), center=(lx, -0.76, 0.32), R=rot_x(0.10))
        leg.add_mesh(v, f, 'armor_dark')
        v, f = make_chamfer_box(0.28, 0.07, 0.05, chamfer=0.01, center=(lx, -0.89, 0.45))
        leg.add_mesh(v, f, 'accent_orange')

        # Heavy Flared Lower Shin Greave
        v, f = make_chamfer_box(0.58, 0.84, 0.70, chamfer=0.10, top_taper=(0.86, 0.88), center=(lx, -1.28, 0.02), R=rot_x(0.08))
        leg.add_mesh(v, f, 'armor_mid')
        # Front shin recessed armor plate
        v, f = make_chamfer_box(0.42, 0.56, 0.22, chamfer=0.05, center=(lx, -1.32, 0.34), R=rot_x(0.06))
        leg.add_mesh(v, f, 'armor_dark')
        # Twin rear calf hydraulic struts
        for ox in [-0.14, 0.14]:
            v, f = make_cylinder(0.055, 0.055, 0.68, segs=12, center=(lx+ox, -1.26, -0.32), axis='y', R=rot_x(-0.10))
            leg.add_mesh(v, f, 'steel_bright')

        # Ankle Gimbal & 4-Toed Wide Stabilizer Foot
        fy = -1.80
        v, f = make_cylinder(0.22, 0.26, 0.20, segs=16, center=(lx, fy+0.10, 0.04), axis='y')
        leg.add_mesh(v, f, 'steel_dark')
        v, f = make_chamfer_box(0.62, 0.18, 0.66, chamfer=0.05, center=(lx, fy, 0.06))
        leg.add_mesh(v, f, 'armor_dark')
        # Two Heavy Articulated Front Toes
        for tx_off in [-0.18, 0.18]:
            v, f = make_chamfer_box(0.23, 0.20, 0.44, chamfer=0.04, top_taper=(0.82, 0.85), center=(lx+tx_off, fy-0.02, 0.46), R=rot_x(0.12))
            leg.add_mesh(v, f, 'armor_mid')
            v, f = make_chamfer_box(0.19, 0.13, 0.18, chamfer=0.03, center=(lx+tx_off, fy-0.05, 0.68), R=rot_x(0.24))
            leg.add_mesh(v, f, 'steel_dark')
        # Rear Heel Stabilizer Spade
        v, f = make_chamfer_box(0.40, 0.18, 0.34, chamfer=0.04, center=(lx, fy-0.02, -0.34), R=rot_x(-0.14))
        leg.add_mesh(v, f, 'armor_mid')
        # Outer Side Stabilizer Toe
        v, f = make_chamfer_box(0.22, 0.16, 0.32, chamfer=0.03, center=(lx + sx*0.38, fy-0.03, 0.06), R=rot_z(-sx*0.18))
        leg.add_mesh(v, f, 'armor_mid')

        parts[f'leg_{side}'] = leg

    return parts

# ==============================================================================
# 3. POSE / ANIMATION EVALUATOR
# ==============================================================================
def assemble_posed_mesh(parts, pose='neutral'):
    all_v, all_f, all_m = [], [], []
    v_off = 0

    pivots = {
        'pelvis':     (0.0, 0.0, 0.0),
        'torso':      (0.0, 0.34, 0.0),
        'shoulder_L': (0.86, 1.02, 0.0),
        'shoulder_R': (-0.86, 1.02, 0.0),
        'arm_L':      (1.22, 0.68, 0.0),
        'arm_R':      (-1.22, 0.68, 0.0),
        'leg_L':      (0.64, -0.08, 0.0),
        'leg_R':      (-0.64, -0.08, 0.0),
    }

    if pose == 'neutral':
        torso_R, torso_T = rot_y(0.0), (0, 0, 0)
        pelvis_R, pelvis_T = rot_y(0.0), (0, 0, 0)
        arm_L_R, arm_R_R = rot_x(0.0), rot_x(0.0)
        leg_L_R, leg_R_R = rot_x(0.0), rot_x(0.0)
    elif pose == 'combat_salvo':
        pelvis_R, pelvis_T = rot_y(-0.14), (0, -0.03, 0)
        torso_R, torso_T = rot_y(0.28) @ rot_x(0.08), (0, -0.03, 0)
        arm_L_R = rot_x(-0.48) @ rot_z(0.12)
        arm_R_R = rot_x(-0.42) @ rot_z(-0.28)
        leg_L_R = rot_x(-0.28) @ rot_z(0.05)
        leg_R_R = rot_x(0.24) @ rot_z(-0.05)

    def apply_pivot(v, pivot, R_local, parent_pivot=None, R_parent=None, T_root=(0,0,0)):
        p = np.asarray(pivot, dtype=np.float32)
        v_out = (v - p) @ R_local.T + p
        if R_parent is not None and parent_pivot is not None:
            pp = np.asarray(parent_pivot, dtype=np.float32)
            v_out = (v_out - pp) @ R_parent.T + pp
        return v_out + np.asarray(T_root, dtype=np.float32)

    for name, part in parts.items():
        v, f, m = part.finalize()
        if name == 'pelvis':
            v = apply_pivot(v, pivots['pelvis'], pelvis_R, T_root=pelvis_T)
        elif name == 'torso':
            v = apply_pivot(v, pivots['torso'], torso_R, T_root=torso_T)
        elif name in ('shoulder_L', 'shoulder_R'):
            v = apply_pivot(v, pivots[name], np.eye(3, dtype=np.float32), pivots['torso'], torso_R, T_root=torso_T)
        elif name == 'arm_L':
            v = apply_pivot(v, pivots['arm_L'], arm_L_R, pivots['torso'], torso_R, T_root=torso_T)
        elif name == 'arm_R':
            v = apply_pivot(v, pivots['arm_R'], arm_R_R, pivots['torso'], torso_R, T_root=torso_T)
        elif name == 'leg_L':
            v = apply_pivot(v, pivots['leg_L'], leg_L_R, pivots['pelvis'], pelvis_R, T_root=pelvis_T)
        elif name == 'leg_R':
            v = apply_pivot(v, pivots['leg_R'], leg_R_R, pivots['pelvis'], pelvis_R, T_root=pelvis_T)

        all_v.append(v)
        all_f.append(f + v_off)
        all_m.extend(m)
        v_off += len(v)

    return np.vstack(all_v), np.vstack(all_f), all_m

# ==============================================================================
# 4. TRUE PER-PIXEL Z-BUFFER 3D VIEWPORT RASTERIZER
# ==============================================================================
def render_viewport_zbuf(verts, faces, mats, width=960, height=700, yaw=0.52, pitch=0.18, dist=7.6,
                         target=(0, -0.08, 0), wireframe=False):
    # Supersample 2x for clean anti-aliased edges and wireframes
    W, H = width * 2, height * 2
    img = np.zeros((H, W, 3), dtype=np.uint8)
    glow_layer = np.zeros((H, W, 3), dtype=np.uint8)
    zbuf = np.full((H, W), np.inf, dtype=np.float32)

    # Studio dark viewport radial gradient
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W * 0.5, H * 0.52
    rad = np.sqrt(((xx - cx) / (W * 0.7))**2 + ((yy - cy) / (H * 0.7))**2)
    bg = np.clip(46 - rad * 26, 16, 48).astype(np.uint8)
    img[:, :, 0] = bg + 5
    img[:, :, 1] = bg + 2
    img[:, :, 2] = bg

    # Camera matrices
    cy_a, sy_a = math.cos(yaw), math.sin(yaw)
    cp_a, sp_a = math.cos(pitch), math.sin(pitch)
    cam_pos = np.array([
        target[0] + dist * cp_a * sy_a,
        target[1] + dist * sp_a,
        target[2] + dist * cp_a * cy_a
    ], dtype=np.float32)

    fwd = np.array(target, dtype=np.float32) - cam_pos
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0, 1, 0], dtype=np.float32))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    R_view = np.stack([right, up, -fwd], axis=0)
    fov_scale = (H * 0.5) / math.tan(math.radians(38.0) * 0.5)

    def project_pts(pts_3d):
        vc = (pts_3d - cam_pos) @ R_view.T
        z = -vc[:, 2]
        z_safe = np.maximum(z, 0.1)
        sx = cx + (vc[:, 0] / z_safe) * fov_scale
        sy = cy - (vc[:, 1] / z_safe) * fov_scale
        return np.stack([sx, sy, z], axis=1)

    # Ground reference grid at y = -1.92
    grid_y = -1.92
    for gi in range(-5, 6):
        g_step = 0.55
        p1 = np.array([[gi*g_step, grid_y, -5*g_step], [gi*g_step, grid_y, 5*g_step]], dtype=np.float32)
        p2 = np.array([[-5*g_step, grid_y, gi*g_step], [5*g_step, grid_y, gi*g_step]], dtype=np.float32)
        for seg in (p1, p2):
            ps = project_pts(seg)
            if np.all(ps[:, 2] > 0.5):
                col = (78, 72, 65) if gi == 0 else (50, 47, 43)
                cv2.line(img, (int(ps[0,0]), int(ps[0,1])), (int(ps[1,0]), int(ps[1,1])), col, 2, cv2.LINE_AA)

    proj = project_pts(verts)

    # Compute face normals & centroids
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    fn_len = np.linalg.norm(fn, axis=1, keepdims=True)
    fn = fn / np.maximum(fn_len, 1e-8)
    centroids = (v0 + v1 + v2) / 3.0

    to_cam = cam_pos - centroids
    view_dir = to_cam / np.maximum(np.linalg.norm(to_cam, axis=1, keepdims=True), 1e-6)
    facing = np.sum(fn * view_dir, axis=1)
    valid_idx = np.where((facing > 0.0) & (proj[faces[:, 0], 2] > 0.5))[0]

    # 3-Point Studio Lighting
    L_key = np.array([0.55, 0.72, 0.42], dtype=np.float32); L_key /= np.linalg.norm(L_key)
    L_fill = np.array([-0.65, 0.25, 0.55], dtype=np.float32); L_fill /= np.linalg.norm(L_fill)
    L_rim = np.array([0.0, 0.45, -0.88], dtype=np.float32); L_rim /= np.linalg.norm(L_rim)

    wire_edges = []

    for fi in valid_idx:
        tri = faces[fi]
        p0, p1, p2 = proj[tri[0]], proj[tri[1]], proj[tri[2]]

        # Bounding box in screen space
        min_x = max(0, int(math.floor(min(p0[0], p1[0], p2[0]))))
        max_x = min(W - 1, int(math.ceil(max(p0[0], p1[0], p2[0]))))
        min_y = max(0, int(math.floor(min(p0[1], p1[1], p2[1]))))
        max_y = min(H - 1, int(math.ceil(max(p0[1], p1[1], p2[1]))))
        if min_x > max_x or min_y > max_y:
            continue

        # Edge function / barycentric coordinates
        denom = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(denom) < 1e-5:
            continue
        inv_d = 1.0 / denom

        # Shade triangle color
        n = fn[fi]
        v_d = view_dir[fi]
        mat = MATERIALS[mats[fi]]
        base_col = np.array(mat['color'], dtype=np.float32)

        if mat['emit'] > 0.5:
            rgb = np.clip(base_col * 1.15 + 0.12, 0.0, 1.0)
        else:
            ndotl_k = max(0.0, float(np.dot(n, L_key)))
            ndotl_f = max(0.0, float(np.dot(n, L_fill)))
            ndotl_r = max(0.0, float(np.dot(n, L_rim)))
            h_vec = L_key + v_d
            h_vec /= max(np.linalg.norm(h_vec), 1e-6)
            spec = (max(0.0, float(np.dot(n, h_vec))) ** 24.0) * mat['spec']
            ao = np.clip((centroids[fi, 1] + 2.0) / 3.6, 0.68, 1.08)
            diff = (0.30 + 0.68 * ndotl_k + 0.25 * ndotl_f) * ao
            rim = 0.20 * (ndotl_r ** 2.0)
            rgb = np.clip(base_col * diff + spec * np.array([1.0, 0.96, 0.90]) + rim * np.array([0.55, 0.70, 0.90]), 0.0, 1.0)

        bgr = np.array([int(rgb[2]*255), int(rgb[1]*255), int(rgb[0]*255)], dtype=np.uint8)

        # Vectorized rasterization inside bounding box
        gy, gx = np.mgrid[min_y:max_y+1, min_x:max_x+1]
        gx_f = gx.astype(np.float32) + 0.5
        gy_f = gy.astype(np.float32) + 0.5

        w0 = ((p1[1] - p2[1]) * (gx_f - p2[0]) + (p2[0] - p1[0]) * (gy_f - p2[1])) * inv_d
        w1 = ((p2[1] - p0[1]) * (gx_f - p2[0]) + (p0[0] - p2[0]) * (gy_f - p2[1])) * inv_d
        w2 = 1.0 - w0 - w1

        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not np.any(inside):
            continue

        z_pix = w0 * p0[2] + w1 * p1[2] + w2 * p2[2]
        z_sub = zbuf[min_y:max_y+1, min_x:max_x+1]
        vis = inside & (z_pix < z_sub)
        if np.any(vis):
            z_sub[vis] = z_pix[vis]
            img_sub = img[min_y:max_y+1, min_x:max_x+1]
            img_sub[vis] = bgr
            if mat['emit'] > 0.5:
                glow_sub = glow_layer[min_y:max_y+1, min_x:max_x+1]
                glow_sub[vis] = bgr
            elif glow_layer[min_y:max_y+1, min_x:max_x+1][vis].any():
                # Occlude glow behind solid objects!
                glow_sub = glow_layer[min_y:max_y+1, min_x:max_x+1]
                glow_sub[vis] = 0

        if wireframe:
            wire_edges.append((p0, p1, p2, bgr))

    # Draw depth-tested wireframe overlay
    if wireframe:
        for p0, p1, p2, bgr in wire_edges:
            mid_z = (p0[2] + p1[2] + p2[2]) / 3.0
            mx = min(W-1, max(0, int((p0[0]+p1[0]+p2[0])/3.0)))
            my = min(H-1, max(0, int((p0[1]+p1[1]+p2[1])/3.0)))
            if mid_z <= zbuf[my, mx] + 0.12:
                pts2d = np.array([[int(p0[0]), int(p0[1])], [int(p1[0]), int(p1[1])], [int(p2[0]), int(p2[1])]], dtype=np.int32)
                w_col = (int(bgr[0]*0.5+65), int(bgr[1]*0.5+85), int(bgr[2]*0.5+105))
                cv2.polylines(img, [pts2d], True, w_col, 1, cv2.LINE_AA)

    # Subtle bloom ONLY on visible emissive pixels
    if np.any(glow_layer > 0):
        bloom1 = cv2.GaussianBlur(glow_layer, (21, 21), 0)
        bloom2 = cv2.GaussianBlur(glow_layer, (45, 45), 0)
        img = np.clip(img.astype(np.int32) + (bloom1.astype(np.int32) * 0.45) + (bloom2.astype(np.int32) * 0.25), 0, 255).astype(np.uint8)

    out = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)

# ==============================================================================
# 5. RENDER & SAVE 4-PANEL 3D VIEWPORT SCREENSHOT SHEET
# ==============================================================================
parts = build_dreadnought_parts()
v_neutral, f_neutral, m_neutral = assemble_posed_mesh(parts, pose='neutral')
v_combat,  f_combat,  m_combat  = assemble_posed_mesh(parts, pose='combat_salvo')

print(f"Mesh ready: {len(v_neutral)} vertices, {len(f_neutral)} triangles across {len(parts)} rigged groups.")

p1 = render_viewport_zbuf(v_neutral, f_neutral, m_neutral, 960, 700, yaw=0.52,  pitch=0.16, dist=7.6, target=(0, -0.08, 0), wireframe=False)
p2 = render_viewport_zbuf(v_neutral, f_neutral, m_neutral, 960, 700, yaw=-0.48, pitch=0.16, dist=7.6, target=(0, -0.08, 0), wireframe=True)
p3 = render_viewport_zbuf(v_neutral, f_neutral, m_neutral, 960, 700, yaw=2.55,  pitch=0.18, dist=7.6, target=(0, -0.08, 0), wireframe=False)
p4 = render_viewport_zbuf(v_combat,  f_combat,  m_combat,  960, 700, yaw=0.40,  pitch=0.14, dist=7.6, target=(0, -0.08, 0), wireframe=False)

sheet = Image.new('RGB', (1920, 1480), (18, 20, 24))
sheet.paste(Image.fromarray(p1), (0, 80))
sheet.paste(Image.fromarray(p2), (960, 80))
sheet.paste(Image.fromarray(p3), (0, 780))
sheet.paste(Image.fromarray(p4), (960, 780))

draw = ImageDraw.Draw(sheet)
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 23)
    font_label = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 18)
    font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 15)
except Exception:
    font_title = font_label = font_sub = ImageFont.load_default()

draw.rectangle([0, 0, 1920, 78], fill=(24, 28, 34))
draw.text((28, 24), "3D-МОДЕЛЬ: ТЯЖЕЛЫЙ ДРЕДНОУТ (HARD-SURFACE MESH & RIG PREVIEW)", fill=(235, 240, 245), font=font_title)
stats_txt = f"Вершин: {len(v_neutral):,}   |   Треугольников: {len(f_neutral):,}   |   Костей рига: {len(parts)}   |   Материалов: {len(MATERIALS)}"
draw.text((1120, 28), stats_txt, fill=(245, 165, 65), font=font_sub)

draw.line([(960, 80), (960, 1480)], fill=(55, 62, 72), width=3)
draw.line([(0, 780), (1920, 780)], fill=(55, 62, 72), width=3)
draw.line([(0, 78), (1920, 78)], fill=(215, 120, 40), width=2)

badges = [
    (24, 100,  "КАМЕРА 01 // ВИД СПЕРЕДИ 3/4 (SHADED + PBR)", "Спаренный рельсотрон, оптический блок и ракетные кассеты"),
    (984, 100, "КАМЕРА 02 // ТОПОЛОГИЯ СЕТКИ (WIREFRAME OVERLAY)", "Трехпалая сейсмическая клешня и генератор энергощита"),
    (24, 800,  "КАМЕРА 03 // ВИД СЗАДИ 3/4 (ТЕХНИЧЕСКИЙ ОБЗОР)", "Сдвоенные термоядерные турбореакторы, радиаторы и гидравлика"),
    (984, 800, "КАМЕРА 04 // ТЕСТ РИГА И АНИМАЦИИ: БОЕВОЙ ЗАЛП", "Поворот торса, шаг вперед, прицеливание и замах клешней"),
]
for bx, by, title, sub in badges:
    draw.rounded_rectangle([bx, by, bx+590, by+64], radius=6, fill=(18, 22, 28))
    draw.text((bx+14, by+10), title, fill=(250, 175, 75), font=font_label)
    draw.text((bx+14, by+36), sub, fill=(175, 185, 198), font=font_sub)

preview_path = "artifacts/file_generation/ttl=63d/intermediate/dreadnought_3d_preview.png"
output_path  = "artifacts/file_generation/ttl=63d/output/dreadnought_3d_screenshots.png"
sheet.save(preview_path)
sheet.save(output_path)
print("Saved Z-buffered preview sheet to", output_path)
