import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import math

# ==============================================================================
# 1. HIGH-DETAIL HARD-SURFACE GEOMETRY BUILDER WITH CREASE NORMALS & EDGE WEAR
# ==============================================================================
MATERIALS = {
    # id: (R, G, B, metallic, roughness, emissive, edge_wear_strength)
    0: (0.23, 0.26, 0.30, 0.58, 0.40, 0.0, 0.50), # armor_slate (main dark slate-grey titanium)
    1: (0.31, 0.35, 0.40, 0.62, 0.36, 0.0, 0.58), # armor_mid (secondary beveled plates)
    2: (0.14, 0.16, 0.18, 0.78, 0.30, 0.0, 0.38), # steel_dark (inner frame, barrels, vents)
    3: (0.60, 0.64, 0.68, 0.92, 0.20, 0.0, 0.22), # steel_chrome (pistons, bolts, muzzle rings)
    4: (0.78, 0.44, 0.14, 0.48, 0.42, 0.0, 0.42), # accent_orange (tactical markings, sensor bezel)
    5: (1.00, 0.54, 0.08, 0.20, 0.20, 1.0, 0.00), # glow_amber (rail coils, reactor cores, lenses)
    6: (0.48, 0.92, 1.00, 0.20, 0.20, 1.0, 0.00), # glow_cyan (energy shield crystal emitter)
    7: (0.07, 0.08, 0.10, 0.85, 0.15, 0.0, 0.10), # panel_groove / dark lens glass
}

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]], dtype=np.float32)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]], dtype=np.float32)

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]], dtype=np.float32)

class HighPolyPart:
    def __init__(self, name, pivot=(0,0,0)):
        self.name = name
        self.pivot = np.array(pivot, dtype=np.float32)
        self.verts = []
        self.faces = []
        self.mats = []
        self.edge_flags = []
        self.v_offset = 0

    def add_raw(self, v, f, mat_id, is_bevel=None):
        v = np.asarray(v, dtype=np.float32)
        f = np.asarray(f, dtype=np.int32) + self.v_offset
        self.verts.append(v)
        self.faces.append(f)
        self.mats.append(np.full(len(f), mat_id, dtype=np.int32))
        if is_bevel is None:
            self.edge_flags.append(np.zeros(len(v), dtype=np.float32))
        else:
            self.edge_flags.append(np.asarray(is_bevel, dtype=np.float32))
        self.v_offset += len(v)

    def add_loft(self, slices, mat_id, cap_bot=True, cap_top=True):
        rings = [np.asarray(s, dtype=np.float32) for s in slices]
        num_rings = len(rings)
        n_pts = len(rings[0])
        verts = np.vstack(rings)
        bevel = np.zeros(len(verts), dtype=np.float32)
        for r in range(num_rings):
            if r in (1, num_rings - 2):
                bevel[r*n_pts:(r+1)*n_pts] = 1.0
            else:
                bevel[r*n_pts:(r+1)*n_pts] = 0.30

        faces = []
        for r in range(num_rings - 1):
            b0, b1 = r * n_pts, (r + 1) * n_pts
            for i in range(n_pts):
                ni = (i + 1) % n_pts
                faces.append([b0+i, b0+ni, b1+ni])
                faces.append([b0+i, b1+ni, b1+i])

        if cap_bot:
            bc = len(verts)
            c_pt = np.mean(rings[0], axis=0, keepdims=True)
            verts = np.vstack([verts, c_pt])
            bevel = np.append(bevel, 0.0)
            for i in range(n_pts):
                ni = (i + 1) % n_pts
                faces.append([bc, ni, i])

        if cap_top:
            tc = len(verts)
            c_pt = np.mean(rings[-1], axis=0, keepdims=True)
            verts = np.vstack([verts, c_pt])
            bevel = np.append(bevel, 0.0)
            top_start = (num_rings - 1) * n_pts
            for i in range(n_pts):
                ni = (i + 1) % n_pts
                faces.append([tc, top_start + i, top_start + ni])

        self.add_raw(verts, faces, mat_id, bevel)

    def add_beveled_block(self, sx, sy, sz, chamfer=0.045, taper_top=(1.0, 1.0),
                          taper_front=1.0, shear_z=0.0, center=(0,0,0), R=None, mat_id=0):
        hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
        c = min(chamfer, hx*0.38, hy*0.38, hz*0.38)
        tx, tz = taper_top

        def make_ring(y_val, rx, rz, ft, z_off, b_c):
            rx = max(rx, 0.005)
            rz = max(rz, 0.005)
            bc = min(b_c, rx*0.35, rz*0.35)
            rxf = rx * ft
            pts = np.array([
                [-rxf+bc, y_val,  rz+z_off],
                [ rxf-bc, y_val,  rz+z_off],
                [ rxf,    y_val,  rz-bc+z_off],
                [ rx,     y_val, -rz+bc+z_off],
                [ rx-bc,  y_val, -rz+z_off],
                [-rx+bc,  y_val, -rz+z_off],
                [-rx,     y_val, -rz+bc+z_off],
                [-rxf,    y_val,  rz-bc+z_off],
            ], dtype=np.float32)
            if R is not None:
                pts = pts @ R.T
            return pts + np.asarray(center, dtype=np.float32)

        slices = [
            make_ring(-hy,     hx-c,        hz-c,        1.0,         -shear_z*0.5, c*0.7),
            make_ring(-hy+c,   hx,          hz,          1.0,         -shear_z*0.4, c),
            make_ring(0.0,     hx*(1+tx)/2, hz*(1+tz)/2, (1+taper_front)/2, 0.0,    c),
            make_ring(hy-c,    hx*tx,       hz*tz,       taper_front,  shear_z*0.4, c),
            make_ring(hy,      hx*tx-c,     hz*tz-c,     taper_front,  shear_z*0.5, c*0.7),
        ]
        self.add_loft(slices, mat_id=mat_id)

    def add_cylinder(self, r_bot, r_top, height, segs=24, bevel=0.02, center=(0,0,0), axis='y', R=None, mat_id=2):
        hy = height * 0.5
        b = min(bevel, hy * 0.35, min(r_bot, r_top) * 0.35)
        angles = np.linspace(0, 2*np.pi, segs, endpoint=False)
        ca, sa = np.cos(angles), np.sin(angles)

        if b > 1e-4:
            y_levels = [
                (-hy,   max(0.002, r_bot - b)),
                (-hy+b, r_bot),
                ( hy-b, r_top),
                ( hy,   max(0.002, r_top - b))
            ]
        else:
            y_levels = [(-hy, r_bot), (hy, r_top)]

        R_ax = np.eye(3, dtype=np.float32)
        if axis == 'x':
            R_ax = rot_z(-np.pi/2)
        elif axis == 'z':
            R_ax = rot_x(np.pi/2)
        if R is not None:
            R_ax = R @ R_ax

        slices = []
        for y_v, rad in y_levels:
            ring = np.stack([rad*ca, np.full_like(ca, y_v), rad*sa], axis=1).astype(np.float32)
            ring = ring @ R_ax.T + np.asarray(center, dtype=np.float32)
            slices.append(ring)
        self.add_loft(slices, mat_id=mat_id)

    def add_tube(self, r_outer, r_inner, height, segs=24, center=(0,0,0), axis='z', R=None, mat_id=2):
        hy = height * 0.5
        angles = np.linspace(0, 2*np.pi, segs, endpoint=False)
        ca, sa = np.cos(angles), np.sin(angles)
        ob = np.stack([r_outer*ca, np.full_like(ca, -hy), r_outer*sa], axis=1)
        ot = np.stack([r_outer*ca, np.full_like(ca,  hy), r_outer*sa], axis=1)
        ib = np.stack([r_inner*ca, np.full_like(ca, -hy), r_inner*sa], axis=1)
        it = np.stack([r_inner*ca, np.full_like(ca,  hy), r_inner*sa], axis=1)
        verts = np.vstack([ob, ot, ib, it]).astype(np.float32)

        R_ax = np.eye(3, dtype=np.float32)
        if axis == 'x':
            R_ax = rot_z(-np.pi/2)
        elif axis == 'z':
            R_ax = rot_x(np.pi/2)
        if R is not None:
            R_ax = R @ R_ax
        verts = verts @ R_ax.T + np.asarray(center, dtype=np.float32)

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
        bevel = np.ones(len(verts), dtype=np.float32) * 0.7
        self.add_raw(verts, faces, mat_id, bevel)

    def add_limb_segment(self, p0, p1, r0_x, r0_z, r1_x, r1_z, mat_id=1, chamfer=0.28):
        """Connects two 3D points p0 -> p1 with a seamless beveled octagonal prism!"""
        p0 = np.asarray(p0, dtype=np.float32)
        p1 = np.asarray(p1, dtype=np.float32)
        vec = p1 - p0
        L = float(np.linalg.norm(vec))
        if L < 1e-5:
            return
        d = vec / L
        up = np.array([0, 0, 1], dtype=np.float32) if abs(d[1]) > 0.9 else np.array([0, 1, 0], dtype=np.float32)
        rx_v = np.cross(up, d); rx_v /= np.linalg.norm(rx_v)
        rz_v = np.cross(d, rx_v)
        R_seg = np.stack([rx_v, d, rz_v], axis=1) # columns are local X, Y, Z

        def ring_at(t, sx, sz):
            c = chamfer
            pts = np.array([
                [-sx*(1-c), 0,  sz], [ sx*(1-c), 0,  sz],
                [ sx,       0,  sz*(1-c)], [ sx,  0, -sz*(1-c)],
                [ sx*(1-c), 0, -sz], [-sx*(1-c), 0, -sz],
                [-sx,       0, -sz*(1-c)], [-sx,  0,  sz*(1-c)],
            ], dtype=np.float32)
            return (pts @ R_seg.T) + (p0 * (1.0 - t) + p1 * t)

        slices = [
            ring_at(0.00, r0_x*0.85, r0_z*0.85),
            ring_at(0.08, r0_x,      r0_z),
            ring_at(0.92, r1_x,      r1_z),
            ring_at(1.00, r1_x*0.85, r1_z*0.85),
        ]
        self.add_loft(slices, mat_id=mat_id)

    def finalize(self):
        return (
            np.vstack(self.verts),
            np.vstack(self.faces),
            np.concatenate(self.mats),
            np.concatenate(self.edge_flags)
        )

# ==============================================================================
# 2. SCULPT EXACT REFERENCE DREADNOUGHT (watermarked_img_1366580511548381503.jpg)
# ==============================================================================
def build_reference_dreadnought():
    parts = {}

    # --------------------------------------------------------------------------
    # A. PELVIS, GROIN THRUSTER BLOCK & WAIST HYDRAULICS
    # --------------------------------------------------------------------------
    pelvis = HighPolyPart('pelvis', pivot=(0.0, 0.0, 0.0))
    pelvis.add_beveled_block(0.84, 0.44, 0.78, chamfer=0.06, taper_top=(1.12, 1.05), center=(0, -0.04, 0.0), mat_id=2)
    pelvis.add_beveled_block(0.42, 0.56, 0.34, chamfer=0.05, taper_top=(1.18, 1.08), taper_front=0.82,
                             center=(0, -0.10, 0.34), R=rot_x(0.08), mat_id=0)
    pelvis.add_beveled_block(0.46, 0.14, 0.36, chamfer=0.03, taper_front=0.85,
                             center=(0, 0.16, 0.36), R=rot_x(-0.18), mat_id=1)
    pelvis.add_beveled_block(0.10, 0.26, 0.06, chamfer=0.01, center=(0, -0.14, 0.50), R=rot_x(0.08), mat_id=7)
    for sx in [-1, 1]:
        pelvis.add_beveled_block(0.24, 0.36, 0.58, chamfer=0.04, center=(sx*0.44, 0.04, 0.08), R=rot_z(-sx*0.32), mat_id=1)
        pelvis.add_beveled_block(0.10, 0.16, 0.22, chamfer=0.02, center=(sx*0.46, 0.02, 0.26), R=rot_z(-sx*0.32), mat_id=4)
        pelvis.add_cylinder(0.22, 0.22, 0.38, segs=24, bevel=0.02, center=(sx*0.52, -0.12, 0.0), axis='x', mat_id=2)
        pelvis.add_cylinder(0.15, 0.15, 0.48, segs=20, bevel=0.015, center=(sx*0.54, -0.12, 0.0), axis='x', mat_id=3)
        pelvis.add_cylinder(0.055, 0.055, 0.44, segs=14, bevel=0.005, center=(sx*0.40, 0.24, 0.18), axis='y', R=rot_z(sx*0.24), mat_id=3)
        pelvis.add_cylinder(0.075, 0.075, 0.22, segs=14, bevel=0.008, center=(sx*0.44, 0.14, 0.18), axis='y', R=rot_z(sx*0.24), mat_id=2)
    pelvis.add_cylinder(0.38, 0.42, 0.34, segs=28, bevel=0.02, center=(0, 0.26, 0.0), axis='y', mat_id=2)
    parts['pelvis'] = pelvis

    # --------------------------------------------------------------------------
    # B. TORSO: MULTI-FACETED ARMORED CORE, SEAMLESS ARCH HOOD & TWIN REACTORS
    # --------------------------------------------------------------------------
    torso = HighPolyPart('torso', pivot=(0.0, 0.32, 0.0))
    # Main wide torso core hull
    torso.add_beveled_block(1.42, 0.96, 1.18, chamfer=0.12, taper_top=(1.06, 0.92), taper_front=0.76,
                            center=(0, 0.84, -0.02), mat_id=0)
    # Lower abdominal V-wedge armor
    torso.add_beveled_block(0.92, 0.34, 0.56, chamfer=0.06, taper_top=(1.22, 1.15), taper_front=0.72,
                            center=(0, 0.42, 0.34), R=rot_x(-0.48), mat_id=0)
    torso.add_beveled_block(0.46, 0.14, 0.12, chamfer=0.02, center=(0, 0.36, 0.58), R=rot_x(-0.35), mat_id=2)

    # Center Chest Glacis Wedge (Upper sloped plate + Lower sloped plate meeting at sharp horizontal ridge)
    torso.add_beveled_block(0.86, 0.42, 0.44, chamfer=0.06, taper_top=(0.86, 0.90), taper_front=0.78,
                            center=(0, 0.78, 0.48), R=rot_x(0.42), mat_id=1)
    torso.add_beveled_block(0.88, 0.32, 0.40, chamfer=0.05, taper_top=(1.08, 1.05), taper_front=0.80,
                            center=(0, 0.56, 0.52), R=rot_x(-0.28), mat_id=0)
    # Recessed trapezoidal stencil/ID badge plate in center of chest ridge
    torso.add_beveled_block(0.32, 0.15, 0.06, chamfer=0.015, taper_top=(1.15, 1.0),
                            center=(0, 0.68, 0.69), R=rot_x(0.12), mat_id=2)
    torso.add_beveled_block(0.26, 0.10, 0.04, chamfer=0.01, taper_top=(1.15, 1.0),
                            center=(0, 0.68, 0.71), R=rot_x(0.12), mat_id=1)

    # Left & Right Angled Cheek Armor Pods with Recessed Dark Circular Ports
    for sx in [-1, 1]:
        R_chk = rot_y(sx*0.42) @ rot_x(0.10)
        chk_c = np.array([sx*0.52, 0.68, 0.44], dtype=np.float32)
        torso.add_beveled_block(0.44, 0.52, 0.42, chamfer=0.06, taper_top=(0.90, 0.92), center=chk_c, R=R_chk, mat_id=0)
        bez_c = chk_c + R_chk @ np.array([0.0, -0.02, 0.19], dtype=np.float32)
        torso.add_beveled_block(0.24, 0.26, 0.06, chamfer=0.03, center=bez_c, R=R_chk, mat_id=1)
        port_c = chk_c + R_chk @ np.array([0.0, -0.02, 0.21], dtype=np.float32)
        torso.add_tube(0.088, 0.055, 0.06, segs=20, center=port_c, axis='z', R=R_chk, mat_id=2)
        torso.add_cylinder(0.055, 0.055, 0.03, segs=16, bevel=0.002, center=port_c, axis='z', R=R_chk, mat_id=7)
        torso.add_tube(0.042, 0.028, 0.035, segs=16, center=port_c, axis='z', R=R_chk, mat_id=4)
        for bx in [-0.08, 0.08]:
            for by in [-0.09, 0.09]:
                b_pos = bez_c + R_chk @ np.array([bx, by, 0.03], dtype=np.float32)
                torso.add_cylinder(0.012, 0.012, 0.02, segs=8, bevel=0.002, center=b_pos, axis='z', R=R_chk, mat_id=3)

        # Upper chest collar armor flanking the central hood
        col_c = np.array([sx*0.48, 1.18, 0.22], dtype=np.float32)
        torso.add_beveled_block(0.38, 0.38, 0.58, chamfer=0.05, taper_top=(0.85, 0.88),
                                center=col_c, R=rot_z(-sx*0.22) @ rot_x(0.18), mat_id=1)
        vent_c = np.array([sx*0.44, 1.20, 0.48], dtype=np.float32)
        torso.add_beveled_block(0.14, 0.14, 0.08, chamfer=0.02, center=vent_c, R=rot_z(-sx*0.22) @ rot_x(0.18), mat_id=2)
        torso.add_beveled_block(0.09, 0.09, 0.09, chamfer=0.01, center=vent_c, R=rot_z(-sx*0.22) @ rot_x(0.18), mat_id=7)

        # Massive circular shoulder joint ring on torso side
        torso.add_cylinder(0.36, 0.36, 0.28, segs=28, bevel=0.02, center=(sx*0.76, 0.94, -0.02), axis='x', mat_id=2)
        torso.add_tube(0.39, 0.34, 0.08, segs=28, center=(sx*0.72, 0.94, -0.02), axis='x', mat_id=4)

    # Seamless Sculpted Arched Armored Cowl / Hood Framing the Recessed Optical Pod!
    torso.add_beveled_block(0.72, 0.54, 0.64, chamfer=0.12, taper_top=(0.76, 0.86), taper_front=0.84,
                            center=(0, 1.18, 0.26), mat_id=1)
    # Deep Dark Recessed Bay inside the Cowl
    torso.add_beveled_block(0.46, 0.38, 0.24, chamfer=0.08, taper_top=(0.82, 0.90),
                            center=(0, 1.15, 0.48), mat_id=7)
    # Octagonal Bronze/Orange Sensor Cluster Plate (inset inside the cowl)
    torso.add_beveled_block(0.38, 0.32, 0.08, chamfer=0.07, taper_top=(0.85, 0.95),
                            center=(0, 1.15, 0.56), mat_id=4)
    torso.add_beveled_block(0.31, 0.26, 0.09, chamfer=0.05, taper_top=(0.85, 0.95),
                            center=(0, 1.15, 0.57), mat_id=2)

    # 4 Precision Optical Camera Lenses
    lens_specs = [
        ( 0.00,  1.08, 0.61, 0.068), # Bottom center main rangefinder lens
        (-0.085, 1.19, 0.61, 0.048), # Upper left lens
        ( 0.085, 1.19, 0.61, 0.048), # Upper right lens
        ( 0.00,  1.22, 0.61, 0.032), # Top center laser diode
    ]
    for lx, ly, lz, lr in lens_specs:
        torso.add_tube(lr*1.35, lr*1.05, 0.05, segs=20, center=(lx, ly, lz), axis='z', mat_id=4)
        torso.add_tube(lr*1.05, lr*0.78, 0.06, segs=20, center=(lx, ly, lz+0.005), axis='z', mat_id=2)
        torso.add_cylinder(lr*0.80, lr*0.80, 0.03, segs=18, bevel=0.002, center=(lx, ly, lz), axis='z', mat_id=7)
        torso.add_tube(lr*0.68, lr*0.35, 0.035, segs=18, center=(lx, ly, lz+0.01), axis='z', mat_id=5)

    # Twin Upper-Back Fusion Turbine Reactors (Positioned prominently on upper back like reference!)
    for sx in [-1, 1]:
        rx, ry, rz = sx*0.38, 1.54, -0.22
        torso.add_cylinder(0.23, 0.21, 0.18, segs=24, bevel=0.015, center=(rx, ry-0.10, rz), axis='y', mat_id=2)
        torso.add_cylinder(0.175, 0.175, 0.18, segs=20, bevel=0.005, center=(rx, ry+0.05, rz), axis='y', mat_id=5)
        for r_off in [-0.02, 0.04, 0.10, 0.15]:
            torso.add_tube(0.195, 0.165, 0.022, segs=20, center=(rx, ry+r_off, rz), axis='y', mat_id=2)
        for bi in range(12):
            ang = bi * (2*np.pi / 12)
            bx, bz = rx + 0.185 * math.cos(ang), rz + 0.185 * math.sin(ang)
            torso.add_cylinder(0.016, 0.016, 0.20, segs=8, bevel=0.002, center=(bx, ry+0.05, bz), axis='y', mat_id=2)
        torso.add_tube(0.21, 0.13, 0.08, segs=24, center=(rx, ry+0.17, rz), axis='y', mat_id=1)

    # Rear Armored Backpack & Heat Exchanger Louvers
    torso.add_beveled_block(1.12, 0.88, 0.44, chamfer=0.09, taper_top=(0.90, 0.88), center=(0, 0.84, -0.64), mat_id=1)
    for i in range(5):
        torso.add_beveled_block(0.68, 0.06, 0.12, chamfer=0.01, center=(0, 0.56 + i*0.13, -0.86), R=rot_x(0.28), mat_id=2)
    parts['torso'] = torso

    # --------------------------------------------------------------------------
    # C. SHOULDERS & SLEEK HEXAGONAL 7-TUBE MISSILE PODS WITH OPEN HATCHES
    # --------------------------------------------------------------------------
    for side, sx in [('L', 1), ('R', -1)]:
        sh = HighPolyPart(f'shoulder_{side}', pivot=(sx*0.76, 0.94, 0.0))
        R_sh = rot_z(-sx*0.20)
        sh_c = np.array([sx*1.12, 0.92, -0.02], dtype=np.float32)

        sh.add_beveled_block(0.58, 0.56, 0.78, chamfer=0.08, taper_top=(0.78, 0.86), center=sh_c, R=R_sh, mat_id=0)
        skirt_c = sh_c + R_sh @ np.array([sx*0.04, -0.24, 0.0], dtype=np.float32)
        sh.add_beveled_block(0.62, 0.16, 0.80, chamfer=0.03, center=skirt_c, R=R_sh, mat_id=1)
        stripe_c = sh_c + R_sh @ np.array([sx*0.28, -0.22, 0.12], dtype=np.float32)
        sh.add_beveled_block(0.08, 0.10, 0.36, chamfer=0.01, center=stripe_c, R=R_sh, mat_id=4)

        for sz in [-1, 1]:
            emb_c = sh_c + R_sh @ np.array([-sx*0.04, 0.02, sz*0.38], dtype=np.float32)
            sh.add_tube(0.115, 0.085, 0.05, segs=20, center=emb_c, axis='z', R=R_sh, mat_id=2)
            sh.add_cylinder(0.080, 0.080, 0.04, segs=18, bevel=0.005, center=emb_c, axis='z', R=R_sh, mat_id=1)
            sh.add_beveled_block(0.12, 0.025, 0.05, chamfer=0.005, center=emb_c, R=R_sh @ rot_z(0.5), mat_id=2)

        # Shoulder-Mounted Hexagonal 7-Tube Micro-Missile Pod
        R_pod = rot_z(-sx*0.12)
        pod_c = np.array([sx*1.04, 1.38, 0.02], dtype=np.float32)
        sh.add_beveled_block(0.46, 0.44, 0.68, chamfer=0.09, center=pod_c, R=R_pod, mat_id=0)
        sh.add_beveled_block(0.42, 0.40, 0.08, chamfer=0.07, center=pod_c + R_pod @ np.array([0,0,0.32]), R=R_pod, mat_id=1)
        sh.add_beveled_block(0.35, 0.33, 0.06, chamfer=0.05, center=pod_c + R_pod @ np.array([0,0,0.34]), R=R_pod, mat_id=7)

        offsets = [(0,0)] + [(0.105*math.cos(k*np.pi/3), 0.105*math.sin(k*np.pi/3)) for k in range(6)]
        for ox, oy in offsets:
            t_pos = pod_c + R_pod @ np.array([ox, oy, 0.35], dtype=np.float32)
            sh.add_tube(0.044, 0.034, 0.06, segs=16, center=t_pos, axis='z', R=R_pod, mat_id=2)
            sh.add_cylinder(0.032, 0.032, 0.04, segs=12, bevel=0.002, center=t_pos, axis='z', R=R_pod, mat_id=7)
            w_pos = pod_c + R_pod @ np.array([ox, oy, 0.36], dtype=np.float32)
            sh.add_cylinder(0.022, 0.008, 0.03, segs=12, bevel=0.002, center=w_pos, axis='z', R=R_pod, mat_id=3)

        # Open Mechanical Blast Hatches (hinged cleanly at top & outer edges of pod!)
        top_h = pod_c + R_pod @ np.array([0.0, 0.31, 0.34], dtype=np.float32)
        sh.add_beveled_block(0.36, 0.04, 0.26, chamfer=0.01, center=top_h, R=R_pod @ rot_x(-1.18), mat_id=1)
        side_h = pod_c + R_pod @ np.array([sx*0.31, 0.0, 0.34], dtype=np.float32)
        sh.add_beveled_block(0.04, 0.32, 0.24, chamfer=0.01, center=side_h, R=R_pod @ rot_y(sx*1.18), mat_id=1)

        parts[f'shoulder_{side}'] = sh

    # --------------------------------------------------------------------------
    # D. RIGHT ARM (-X): HEAVY BARREL FOREARM, ENERGY SHIELD & CONNECTED 3-CLAW CRUSHER
    # --------------------------------------------------------------------------
    arm_R = HighPolyPart('arm_R', pivot=(-1.14, 0.62, 0.0))
    ax = -1.16
    arm_R.add_cylinder(0.16, 0.15, 0.44, segs=20, bevel=0.01, center=(ax, 0.42, -0.02), axis='y', mat_id=2)
    arm_R.add_beveled_block(0.36, 0.34, 0.40, chamfer=0.05, center=(ax, 0.42, -0.02), R=rot_z(0.08), mat_id=0)
    arm_R.add_beveled_block(0.38, 0.08, 0.42, chamfer=0.015, center=(ax, 0.30, -0.02), R=rot_z(0.08), mat_id=4)
    arm_R.add_cylinder(0.19, 0.19, 0.40, segs=24, bevel=0.02, center=(ax-0.02, 0.12, 0.0), axis='x', mat_id=2)
    arm_R.add_cylinder(0.12, 0.12, 0.44, segs=20, bevel=0.01, center=(ax-0.02, 0.12, 0.0), axis='x', mat_id=3)

    R_fa = rot_x(0.22) @ rot_z(0.06)
    fa_c = np.array([ax-0.04, -0.24, 0.08], dtype=np.float32)
    arm_R.add_cylinder(0.26, 0.24, 0.54, segs=24, bevel=0.04, center=fa_c, axis='y', R=R_fa, mat_id=0)
    arm_R.add_beveled_block(0.46, 0.44, 0.48, chamfer=0.09, taper_top=(0.90, 0.90), center=fa_c, R=R_fa, mat_id=1)
    wrist_c = fa_c + R_fa @ np.array([0, -0.28, 0], dtype=np.float32)
    arm_R.add_tube(0.25, 0.19, 0.08, segs=24, center=wrist_c, axis='y', R=R_fa, mat_id=4)
    chuck_c = fa_c + R_fa @ np.array([0, -0.37, 0], dtype=np.float32)
    arm_R.add_cylinder(0.24, 0.21, 0.14, segs=24, bevel=0.02, center=chuck_c, axis='y', R=R_fa, mat_id=2)

    # Outer-Forearm Sleek Energy Shield Projector + Glowing Ice-Blue Triangular Crystal Emitter
    sh_c = fa_c + R_fa @ np.array([-0.24, 0.02, 0.02], dtype=np.float32)
    arm_R.add_beveled_block(0.16, 0.52, 0.30, chamfer=0.04, taper_top=(0.80, 0.85), center=sh_c, R=R_fa, mat_id=0)
    arm_R.add_beveled_block(0.18, 0.36, 0.22, chamfer=0.03, center=sh_c + R_fa @ np.array([-0.02, 0.04, 0.0]), R=R_fa, mat_id=1)
    cry_c = fa_c + R_fa @ np.array([-0.28, -0.18, 0.04], dtype=np.float32)
    arm_R.add_beveled_block(0.08, 0.24, 0.16, chamfer=0.02, taper_top=(1.4, 1.3), center=cry_c, R=R_fa @ rot_z(-0.15), mat_id=6)

    # 3-Fingered Articulated Seismic Crusher Claw (Connected kinematic chains with zero gaps!)
    for ci in range(3):
        ca = ci * (2*np.pi / 3.0) + 0.35
        R_jaw = R_fa @ rot_y(ca)
        p_knuckle = chuck_c + R_jaw @ np.array([0.14, -0.03, 0.0], dtype=np.float32)
        p_mid     = chuck_c + R_jaw @ np.array([0.27, -0.27, 0.0], dtype=np.float32)
        p_tip     = chuck_c + R_jaw @ np.array([0.11, -0.55, 0.0], dtype=np.float32)
        p_pist0   = chuck_c + R_jaw @ np.array([0.08, -0.05, 0.0], dtype=np.float32)
        p_pist1   = chuck_c + R_jaw @ np.array([0.18, -0.26, 0.0], dtype=np.float32)

        # Knuckle hinge block + chrome pivot pin
        arm_R.add_beveled_block(0.12, 0.12, 0.14, chamfer=0.02, center=p_knuckle, R=R_jaw, mat_id=2)
        arm_R.add_cylinder(0.040, 0.040, 0.16, segs=14, bevel=0.004, center=p_knuckle, axis='z', R=R_jaw, mat_id=3)
        # Connected proximal jaw beam (p_knuckle -> p_mid)
        arm_R.add_limb_segment(p_knuckle, p_mid, 0.065, 0.070, 0.060, 0.065, mat_id=1)
        # Middle hinge cylinder at p_mid
        arm_R.add_cylinder(0.045, 0.045, 0.16, segs=14, bevel=0.004, center=p_mid, axis='z', R=R_jaw, mat_id=2)
        arm_R.add_cylinder(0.030, 0.030, 0.18, segs=12, bevel=0.003, center=p_mid, axis='z', R=R_jaw, mat_id=3)
        # Connected distal curved talon (p_mid -> p_tip, tapering to a sharp industrial pincer blade!)
        arm_R.add_limb_segment(p_mid, p_tip, 0.058, 0.065, 0.018, 0.045, mat_id=3)
        # Inner hydraulic actuator rod
        arm_R.add_limb_segment(p_pist0, p_pist1, 0.022, 0.022, 0.022, 0.022, mat_id=3)
    parts['arm_R'] = arm_R

    # --------------------------------------------------------------------------
    # E. LEFT ARM (+X): TWIN-BARREL ELECTROMAGNETIC RAIL-CANNON
    # --------------------------------------------------------------------------
    arm_L = HighPolyPart('arm_L', pivot=(1.14, 0.62, 0.0))
    lx = 1.16
    arm_L.add_cylinder(0.16, 0.15, 0.44, segs=20, bevel=0.01, center=(lx, 0.42, -0.02), axis='y', mat_id=2)
    arm_L.add_beveled_block(0.36, 0.34, 0.40, chamfer=0.05, center=(lx, 0.42, -0.02), R=rot_z(-0.08), mat_id=0)
    arm_L.add_beveled_block(0.38, 0.08, 0.42, chamfer=0.015, center=(lx, 0.30, -0.02), R=rot_z(-0.08), mat_id=4)
    arm_L.add_cylinder(0.19, 0.19, 0.40, segs=24, bevel=0.02, center=(lx+0.02, 0.12, 0.0), axis='x', mat_id=2)
    arm_L.add_cylinder(0.12, 0.12, 0.44, segs=20, bevel=0.01, center=(lx+0.02, 0.12, 0.0), axis='x', mat_id=3)

    # Rail-Cannon aimed forward, slightly down & slightly outward (+X) so full barrel length shows in front-3/4 view!
    R_gun = rot_x(0.34) @ rot_y(0.14)
    gun_o = np.array([lx+0.06, -0.10, 0.18], dtype=np.float32)

    arm_L.add_beveled_block(0.40, 0.42, 0.72, chamfer=0.06, center=gun_o, R=R_gun, mat_id=0)
    arm_L.add_beveled_block(0.42, 0.24, 0.44, chamfer=0.04, center=gun_o + R_gun @ np.array([0, 0.02, 0.08]), R=R_gun, mat_id=1)
    arm_L.add_beveled_block(0.44, 0.08, 0.28, chamfer=0.01, center=gun_o + R_gun @ np.array([0, 0.06, 0.14]), R=R_gun, mat_id=4)

    for bi in range(11):
        ang = -0.6 + bi * 0.28
        bx_l = -0.04
        by_l = -0.22 - 0.18 * math.sin(ang)
        bz_l = -0.10 + 0.22 * math.cos(ang)
        seg_c = gun_o + R_gun @ np.array([bx_l, by_l, bz_l], dtype=np.float32)
        arm_L.add_beveled_block(0.16, 0.045, 0.09, chamfer=0.008, center=seg_c, R=R_gun @ rot_x(-ang),
                                mat_id=2 if bi % 2 == 0 else 1)

    for by_off in [0.095, -0.095]:
        core_c = gun_o + R_gun @ np.array([0, by_off, 0.68], dtype=np.float32)
        arm_L.add_cylinder(0.052, 0.052, 0.68, segs=18, bevel=0.002, center=core_c, axis='z', R=R_gun, mat_id=5)
        for ri in range(14):
            rz_p = 0.38 + ri * 0.044
            r_pos = gun_o + R_gun @ np.array([0, by_off, rz_p], dtype=np.float32)
            arm_L.add_tube(0.062, 0.048, 0.018, segs=18, center=r_pos, axis='z', R=R_gun, mat_id=2)
        mz_c = gun_o + R_gun @ np.array([0, by_off, 1.12], dtype=np.float32)
        arm_L.add_tube(0.076, 0.042, 0.24, segs=22, center=mz_c, axis='z', R=R_gun, mat_id=1)
        arm_L.add_tube(0.080, 0.044, 0.05, segs=22, center=mz_c + R_gun @ np.array([0,0,0.08]), axis='z', R=R_gun, mat_id=3)
        arm_L.add_cylinder(0.042, 0.042, 0.20, segs=16, bevel=0.002, center=mz_c, axis='z', R=R_gun, mat_id=7)

    for sy_r, h_r in [(0.175, 0.04), (0.0, 0.035), (-0.175, 0.04)]:
        rl_c = gun_o + R_gun @ np.array([0, sy_r, 0.68], dtype=np.float32)
        arm_L.add_beveled_block(0.16, h_r, 0.72, chamfer=0.01, center=rl_c, R=R_gun, mat_id=2)
    cl_c = gun_o + R_gun @ np.array([0, 0.0, 0.98], dtype=np.float32)
    arm_L.add_beveled_block(0.20, 0.38, 0.07, chamfer=0.015, center=cl_c, R=R_gun, mat_id=1)
    parts['arm_L'] = arm_L

    # --------------------------------------------------------------------------
    # F. POWERFUL SCULPTED BIPEDAL LEGS
    # --------------------------------------------------------------------------
    for side, sx in [('L', 1), ('R', -1)]:
        leg = HighPolyPart(f'leg_{side}', pivot=(sx*0.54, -0.12, 0.0))
        R_thigh = rot_z(-sx*0.06) @ rot_x(-0.16)
        th_c = np.array([sx*0.58, -0.44, 0.04], dtype=np.float32)

        leg.add_beveled_block(0.46, 0.74, 0.56, chamfer=0.08, taper_top=(0.88, 0.90), center=th_c, R=R_thigh, mat_id=0)
        fend_c = th_c + R_thigh @ np.array([sx*0.14, 0.24, 0.02], dtype=np.float32)
        leg.add_beveled_block(0.22, 0.42, 0.48, chamfer=0.05, taper_top=(0.75, 0.82), center=fend_c, R=R_thigh, mat_id=1)
        fth_c = th_c + R_thigh @ np.array([0.0, 0.02, 0.25], dtype=np.float32)
        leg.add_beveled_block(0.32, 0.52, 0.12, chamfer=0.04, center=fth_c, R=R_thigh, mat_id=1)
        for vi in range(3):
            v_p = fth_c + R_thigh @ np.array([sx*0.10, -0.06 + vi*0.06, 0.05], dtype=np.float32)
            leg.add_beveled_block(0.08, 0.02, 0.03, chamfer=0.003, center=v_p, R=R_thigh, mat_id=7)

        for h_sx in [-1, 1]:
            p_pos = th_c + R_thigh @ np.array([h_sx*0.21, -0.04, -0.14], dtype=np.float32)
            leg.add_cylinder(0.055, 0.055, 0.36, segs=14, bevel=0.005, center=p_pos, axis='y', R=R_thigh, mat_id=2)
            leg.add_cylinder(0.038, 0.038, 0.58, segs=14, bevel=0.003, center=p_pos, axis='y', R=R_thigh, mat_id=3)

        kn_c = np.array([sx*0.62, -0.86, 0.12], dtype=np.float32)
        leg.add_cylinder(0.20, 0.20, 0.48, segs=24, bevel=0.02, center=kn_c, axis='x', mat_id=2)
        leg.add_cylinder(0.13, 0.13, 0.52, segs=20, bevel=0.01, center=kn_c, axis='x', mat_id=3)
        kp_c = np.array([sx*0.62, -0.84, 0.32], dtype=np.float32)
        leg.add_beveled_block(0.36, 0.36, 0.22, chamfer=0.06, taper_top=(0.82, 0.88), center=kp_c, R=rot_x(0.08), mat_id=1)
        leg.add_beveled_block(0.24, 0.24, 0.24, chamfer=0.04, center=kp_c, R=rot_x(0.08), mat_id=0)
        leg.add_beveled_block(0.20, 0.055, 0.04, chamfer=0.008, center=kp_c + np.array([0, -0.12, 0.11]), mat_id=4)

        R_shin = rot_z(-sx*0.03) @ rot_x(0.10)
        shn_c = np.array([sx*0.64, -1.34, 0.02], dtype=np.float32)
        leg.add_beveled_block(0.54, 0.82, 0.64, chamfer=0.09, taper_top=(0.82, 0.85), center=shn_c, R=R_shin, mat_id=0)
        fsh_c = shn_c + R_shin @ np.array([0.0, -0.02, 0.28], dtype=np.float32)
        leg.add_beveled_block(0.36, 0.64, 0.20, chamfer=0.05, taper_top=(0.85, 0.90), center=fsh_c, R=R_shin, mat_id=1)
        for c_sx in [-1, 1]:
            cf_c = shn_c + R_shin @ np.array([c_sx*0.24, -0.06, -0.02], dtype=np.float32)
            leg.add_beveled_block(0.14, 0.58, 0.46, chamfer=0.04, center=cf_c, R=R_shin @ rot_z(-c_sx*0.12), mat_id=1)
        for ox in [-0.12, 0.12]:
            st_c = shn_c + R_shin @ np.array([ox, 0.0, -0.30], dtype=np.float32)
            leg.add_cylinder(0.048, 0.048, 0.64, segs=14, bevel=0.004, center=st_c, axis='y', R=R_shin, mat_id=3)
            leg.add_cylinder(0.068, 0.068, 0.30, segs=14, bevel=0.005, center=st_c + np.array([0,-0.12,0]), axis='y', R=R_shin, mat_id=2)

        fy = -1.84
        fx = sx * 0.66
        leg.add_cylinder(0.20, 0.24, 0.20, segs=20, bevel=0.015, center=(fx, fy+0.12, 0.02), axis='y', mat_id=2)
        leg.add_beveled_block(0.34, 0.20, 0.22, chamfer=0.04, center=(fx, fy+0.10, 0.22), R=rot_x(0.20), mat_id=1)
        leg.add_beveled_block(0.58, 0.16, 0.62, chamfer=0.04, center=(fx, fy, 0.04), mat_id=0)

        toe_configs = [
            (-0.19, 0.16, 0.38,  0.14),
            ( 0.00, 0.17, 0.42,  0.00),
            ( 0.19, 0.16, 0.38, -0.14),
        ]
        for tx_o, tw, tl, tyaw in toe_configs:
            R_toe = rot_y(tyaw)
            tc1 = np.array([fx + tx_o, fy - 0.01, 0.40], dtype=np.float32)
            leg.add_beveled_block(tw, 0.18, tl, chamfer=0.03, taper_top=(0.82, 0.85), center=tc1, R=R_toe @ rot_x(0.14), mat_id=1)
            tc2 = np.array([fx + tx_o*1.08, fy - 0.04, 0.60], dtype=np.float32)
            leg.add_beveled_block(tw*0.86, 0.12, 0.18, chamfer=0.02, taper_top=(0.75, 0.80), center=tc2, R=R_toe @ rot_x(0.28), mat_id=2)

        leg.add_beveled_block(0.38, 0.16, 0.32, chamfer=0.035, taper_top=(0.80, 0.80),
                              center=(fx, fy-0.02, -0.34), R=rot_x(-0.18), mat_id=1)

        parts[f'leg_{side}'] = leg

    return parts

# ==============================================================================
# 3. ASSEMBLE POSED MESH & COMPUTE SMOOTH/CREASED VERTEX NORMALS
# ==============================================================================
def assemble_posed_dreadnought(parts, pose='standing_ref'):
    all_v, all_f, all_m, all_b = [], [], [], []
    v_off = 0

    if pose == 'standing_ref':
        # Matches left figure on reference: torso slightly turned so BOTH claw & railgun barrels show!
        pelvis_R, pelvis_T = rot_y(0.06), (0, 0, 0)
        torso_R,  torso_T  = rot_y(0.08) @ rot_x(0.04), (0, 0, 0)
        arm_L_R = rot_x(-0.08) @ rot_z(0.08)
        arm_R_R = rot_x(-0.06) @ rot_z(-0.06)
        leg_L_R = rot_x(0.0)
        leg_R_R = rot_x(0.0)
    elif pose == 'combat_ref':
        # Dynamic combat pose: torso twisted, railgun raised aiming forward, claw poised!
        pelvis_R, pelvis_T = rot_y(-0.20), (0, -0.04, 0)
        torso_R,  torso_T  = rot_y(0.22) @ rot_x(0.08), (0, -0.04, 0)
        arm_L_R = rot_x(-0.35) @ rot_y(0.12)
        arm_R_R = rot_x(-0.34) @ rot_z(-0.22)
        leg_L_R = rot_x(-0.22) @ rot_z(0.05)
        leg_R_R = rot_x(0.20) @ rot_z(-0.05)

    def apply_xform(v, pivot, R_loc, p_piv=None, R_par=None, T_root=(0,0,0)):
        p = np.asarray(pivot, dtype=np.float32)
        vo = (v - p) @ R_loc.T + p
        if R_par is not None and p_piv is not None:
            pp = np.asarray(p_piv, dtype=np.float32)
            vo = (vo - pp) @ R_par.T + pp
        return vo + np.asarray(T_root, dtype=np.float32)

    p_pelvis = parts['pelvis'].pivot
    p_torso  = parts['torso'].pivot

    for name, part in parts.items():
        v, f, m, b = part.finalize()
        piv = part.pivot
        if name == 'pelvis':
            v = apply_xform(v, piv, pelvis_R, T_root=pelvis_T)
        elif name == 'torso':
            v = apply_xform(v, piv, torso_R, T_root=torso_T)
        elif name in ('shoulder_L', 'shoulder_R'):
            v = apply_xform(v, piv, np.eye(3, dtype=np.float32), p_torso, torso_R, T_root=torso_T)
        elif name == 'arm_L':
            v = apply_xform(v, piv, arm_L_R, p_torso, torso_R, T_root=torso_T)
        elif name == 'arm_R':
            v = apply_xform(v, piv, arm_R_R, p_torso, torso_R, T_root=torso_T)
        elif name == 'leg_L':
            v = apply_xform(v, piv, leg_L_R, p_pelvis, pelvis_R, T_root=pelvis_T)
        elif name == 'leg_R':
            v = apply_xform(v, piv, leg_R_R, p_pelvis, pelvis_R, T_root=torso_T)

        all_v.append(v)
        all_f.append(f + v_off)
        all_m.append(m)
        all_b.append(b)
        v_off += len(v)

    V = np.vstack(all_v)
    F = np.vstack(all_f)
    M = np.concatenate(all_m)
    B = np.concatenate(all_b)

    v0, v1, v2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    fn_len = np.linalg.norm(fn, axis=1, keepdims=True)
    fn = fn / np.maximum(fn_len, 1e-8)

    vn = np.zeros_like(V)
    np.add.at(vn, F[:, 0], fn)
    np.add.at(vn, F[:, 1], fn)
    np.add.at(vn, F[:, 2], fn)
    vn_len = np.linalg.norm(vn, axis=1, keepdims=True)
    vn = vn / np.maximum(vn_len, 1e-8)

    return V, F, M, B, fn, vn

# ==============================================================================
# 4. PBR STUDIO Z-BUFFER RENDERER WITH SMOOTH BEVEL SHADING & EDGE WEAR
# ==============================================================================
def render_pbr_viewport(V, F, M, B, fn, vn, width=960, height=700, yaw=-0.24, pitch=0.12, dist=8.1,
                        target=(0, -0.10, 0), light_bg=True, wireframe=False):
    W, H = width * 2, height * 2
    img = np.zeros((H, W, 3), dtype=np.uint8)
    glow_layer = np.zeros((H, W, 3), dtype=np.uint8)
    zbuf = np.full((H, W), np.inf, dtype=np.float32)

    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W * 0.5, H * 0.49
    rad = np.sqrt(((xx - cx) / (W * 0.75))**2 + ((yy - cy) / (H * 0.75))**2)
    if light_bg:
        bg = np.clip(184 - rad * 38, 130, 188).astype(np.uint8)
        img[:, :, 0] = bg + 2
        img[:, :, 1] = bg + 2
        img[:, :, 2] = bg
    else:
        bg = np.clip(48 - rad * 24, 18, 52).astype(np.uint8)
        img[:, :, 0] = bg + 5
        img[:, :, 1] = bg + 2
        img[:, :, 2] = bg

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
    fov_scale = (H * 0.5) / math.tan(math.radians(34.0) * 0.5)

    def project_pts(pts_3d):
        vc = (pts_3d - cam_pos) @ R_view.T
        z = -vc[:, 2]
        z_safe = np.maximum(z, 0.1)
        sx = cx + (vc[:, 0] / z_safe) * fov_scale
        sy = cy - (vc[:, 1] / z_safe) * fov_scale
        return np.stack([sx, sy, z], axis=1)

    grid_y = -1.94
    if light_bg:
        for foot_x, foot_z in [(-0.66, 0.10), (0.66, 0.10), (0.0, 0.0)]:
            rad_s = 0.65 if foot_x != 0 else 1.15
            strength = 0.28 if foot_x != 0 else 0.14
            sh_c = project_pts(np.array([[foot_x, grid_y, foot_z]], dtype=np.float32))[0]
            if sh_c[2] > 0.5:
                rx_p = int((rad_s / sh_c[2]) * fov_scale)
                ry_p = int(rx_p * max(0.18, math.sin(max(0.15, pitch))))
                overlay = img.copy()
                cv2.ellipse(overlay, (int(sh_c[0]), int(sh_c[1])), (rx_p, ry_p), 0, 0, 360, (80, 80, 80), -1)
                overlay = cv2.GaussianBlur(overlay, (71, 71), 0)
                img = cv2.addWeighted(overlay, strength, img, 1.0 - strength, 0)

    for gi in range(-5, 6):
        g_step = 0.55
        p1 = np.array([[gi*g_step, grid_y, -5*g_step], [gi*g_step, grid_y, 5*g_step]], dtype=np.float32)
        p2 = np.array([[-5*g_step, grid_y, gi*g_step], [5*g_step, grid_y, gi*g_step]], dtype=np.float32)
        for seg in (p1, p2):
            ps = project_pts(seg)
            if np.all(ps[:, 2] > 0.5):
                col = (148, 148, 145) if light_bg else (62, 58, 54)
                cv2.line(img, (int(ps[0,0]), int(ps[0,1])), (int(ps[1,0]), int(ps[1,1])), col, 1, cv2.LINE_AA)

    proj = project_pts(V)
    centroids = (V[F[:, 0]] + V[F[:, 1]] + V[F[:, 2]]) / 3.0
    to_cam = cam_pos - centroids
    view_dirs = to_cam / np.maximum(np.linalg.norm(to_cam, axis=1, keepdims=True), 1e-6)
    facing = np.sum(fn * view_dirs, axis=1)
    valid_idx = np.where((facing > -0.02) & (proj[F[:, 0], 2] > 0.5))[0]

    L_key  = np.array([-0.45, 0.75, 0.48], dtype=np.float32); L_key  /= np.linalg.norm(L_key)
    L_fill = np.array([ 0.68, 0.28, 0.67], dtype=np.float32); L_fill /= np.linalg.norm(L_fill)
    L_rim  = np.array([ 0.15, 0.65,-0.74], dtype=np.float32); L_rim  /= np.linalg.norm(L_rim)

    wire_edges = []

    for fi in valid_idx:
        tri = F[fi]
        p0, p1, p2 = proj[tri[0]], proj[tri[1]], proj[tri[2]]

        min_x = max(0, int(math.floor(min(p0[0], p1[0], p2[0]))))
        max_x = min(W - 1, int(math.ceil(max(p0[0], p1[0], p2[0]))))
        min_y = max(0, int(math.floor(min(p0[1], p1[1], p2[1]))))
        max_y = min(H - 1, int(math.ceil(max(p0[1], p1[1], p2[1]))))
        if min_x > max_x or min_y > max_y:
            continue

        denom = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(denom) < 1e-5:
            continue
        inv_d = 1.0 / denom

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
        if not np.any(vis):
            continue

        z_sub[vis] = z_pix[vis]

        f_n = fn[fi]
        n0 = 0.62 * f_n + 0.38 * vn[tri[0]] if np.dot(f_n, vn[tri[0]]) > 0.55 else f_n
        n1 = 0.62 * f_n + 0.38 * vn[tri[1]] if np.dot(f_n, vn[tri[1]]) > 0.55 else f_n
        n2 = 0.62 * f_n + 0.38 * vn[tri[2]] if np.dot(f_n, vn[tri[2]]) > 0.55 else f_n

        curv0 = (1.0 - max(0.0, float(np.dot(f_n, vn[tri[0]])))) * B[tri[0]]
        curv1 = (1.0 - max(0.0, float(np.dot(f_n, vn[tri[1]])))) * B[tri[1]]
        curv2 = (1.0 - max(0.0, float(np.dot(f_n, vn[tri[2]])))) * B[tri[2]]

        vw0 = w0[vis]
        vw1 = w1[vis]
        vw2 = w2[vis]

        nx = vw0 * n0[0] + vw1 * n1[0] + vw2 * n2[0]
        ny = vw0 * n0[1] + vw1 * n1[1] + vw2 * n2[1]
        nz = vw0 * n0[2] + vw1 * n1[2] + vw2 * n2[2]
        n_inv = 1.0 / np.maximum(np.sqrt(nx*nx + ny*ny + nz*nz), 1e-6)
        nx *= n_inv; ny *= n_inv; nz *= n_inv

        edge_w = np.clip((vw0 * curv0 + vw1 * curv1 + vw2 * curv2) * 2.2, 0.0, 1.0)

        mat_props = MATERIALS[int(M[fi])]
        mr, mg, mb, metallic, rough, emit, wear_str = mat_props
        v_d = view_dirs[fi]

        if emit > 0.5:
            r_out = np.full_like(nx, min(1.0, mr * 1.15 + 0.12))
            g_out = np.full_like(nx, min(1.0, mg * 1.15 + 0.10))
            b_out = np.full_like(nx, min(1.0, mb * 1.15 + 0.08))
        else:
            wx = vw0 * V[tri[0], 0] + vw1 * V[tri[1], 0] + vw2 * V[tri[2], 0]
            wy = vw0 * V[tri[0], 1] + vw1 * V[tri[1], 1] + vw2 * V[tri[2], 1]
            wz = vw0 * V[tri[0], 2] + vw1 * V[tri[1], 2] + vw2 * V[tri[2], 2]
            grunge = 0.96 + 0.04 * (np.sin(wx*37.0 + wy*23.0) * np.cos(wy*41.0 + wz*29.0))

            wear_mix = edge_w * wear_str
            albedo_r = (mr * (1.0 - wear_mix) + 0.62 * wear_mix) * grunge
            albedo_g = (mg * (1.0 - wear_mix) + 0.65 * wear_mix) * grunge
            albedo_b = (mb * (1.0 - wear_mix) + 0.69 * wear_mix) * grunge

            ndotl_k = np.maximum(0.0, nx*L_key[0]  + ny*L_key[1]  + nz*L_key[2])
            ndotl_f = np.maximum(0.0, nx*L_fill[0] + ny*L_fill[1] + nz*L_fill[2])
            ndotl_r = np.maximum(0.0, nx*L_rim[0]  + ny*L_rim[1]  + nz*L_rim[2])

            hx_v = L_key[0] + v_d[0]; hy_v = L_key[1] + v_d[1]; hz_v = L_key[2] + v_d[2]
            h_len = max(math.sqrt(hx_v*hx_v + hy_v*hy_v + hz_v*hz_v), 1e-6)
            hx_v /= h_len; hy_v /= h_len; hz_v /= h_len
            ndoth = np.maximum(0.0, nx*hx_v + ny*hy_v + nz*hz_v)
            spec_pow = 28.0 / max(rough, 0.15)
            spec = (ndoth ** spec_pow) * (0.45 + 0.55 * metallic + 0.45 * wear_mix)

            ao = np.clip((wy + 2.1) / 3.4, 0.68, 1.06)
            diff = (0.34 + 0.72 * ndotl_k + 0.28 * ndotl_f) * ao
            rim = (0.24 + 0.20 * metallic) * (ndotl_r ** 2.2)

            r_out = np.clip(albedo_r * diff + spec * 0.98 + rim * 0.78, 0.0, 1.0)
            g_out = np.clip(albedo_g * diff + spec * 0.95 + rim * 0.84, 0.0, 1.0)
            b_out = np.clip(albedo_b * diff + spec * 0.90 + rim * 0.92, 0.0, 1.0)

        bgr_pix = np.stack([
            (b_out * 255.0).astype(np.uint8),
            (g_out * 255.0).astype(np.uint8),
            (r_out * 255.0).astype(np.uint8)
        ], axis=-1)

        img_sub = img[min_y:max_y+1, min_x:max_x+1]
        img_sub[vis] = bgr_pix

        glow_sub = glow_layer[min_y:max_y+1, min_x:max_x+1]
        if emit > 0.5:
            glow_sub[vis] = bgr_pix
        else:
            glow_sub[vis] = 0

        if wireframe:
            wire_edges.append((p0, p1, p2))

    if wireframe:
        for p0, p1, p2 in wire_edges:
            mid_z = (p0[2] + p1[2] + p2[2]) / 3.0
            mx = min(W-1, max(0, int((p0[0]+p1[0]+p2[0])/3.0)))
            my = min(H-1, max(0, int((p0[1]+p1[1]+p2[1])/3.0)))
            if mid_z <= zbuf[my, mx] + 0.08:
                pts2d = np.array([[int(p0[0]), int(p0[1])], [int(p1[0]), int(p1[1])], [int(p2[0]), int(p2[1])]], dtype=np.int32)
                cv2.polylines(img, [pts2d], True, (110, 185, 235), 1, cv2.LINE_AA)

    if np.any(glow_layer > 0):
        b1 = cv2.GaussianBlur(glow_layer, (19, 19), 0)
        b2 = cv2.GaussianBlur(glow_layer, (41, 41), 0)
        img = np.clip(img.astype(np.int32) + (b1.astype(np.int32)*0.42) + (b2.astype(np.int32)*0.24), 0, 255).astype(np.uint8)

    out = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)

# ==============================================================================
# 5. BUILD & RENDER SIDE-BY-SIDE REFERENCE POSE SHEET + TECH VIEWS
# ==============================================================================
parts = build_reference_dreadnought()
V1, F1, M1, B1, fn1, vn1 = assemble_posed_dreadnought(parts, pose='standing_ref')
V2, F2, M2, B2, fn2, vn2 = assemble_posed_dreadnought(parts, pose='combat_ref')

print(f"High-Detail Reference Dreadnought Built: {len(V1):,} vertices, {len(F1):,} triangles.")

p1 = render_pbr_viewport(V1, F1, M1, B1, fn1, vn1, 960, 700, yaw=-0.18, pitch=0.11, dist=8.1, target=(0, -0.10, 0), light_bg=True)
p2 = render_pbr_viewport(V2, F2, M2, B2, fn2, vn2, 960, 700, yaw=-0.34, pitch=0.11, dist=8.1, target=(0, -0.10, 0), light_bg=True)
p3 = render_pbr_viewport(V1, F1, M1, B1, fn1, vn1, 960, 700, yaw=0.35,  pitch=0.14, dist=8.1, target=(0, -0.10, 0), light_bg=False, wireframe=True)
p4 = render_pbr_viewport(V1, F1, M1, B1, fn1, vn1, 960, 700, yaw=2.52,  pitch=0.16, dist=8.1, target=(0, -0.10, 0), light_bg=False, wireframe=False)

sheet = Image.new('RGB', (1920, 1480), (22, 25, 30))
sheet.paste(Image.fromarray(p1), (0, 80))
sheet.paste(Image.fromarray(p2), (960, 80))
sheet.paste(Image.fromarray(p3), (0, 780))
sheet.paste(Image.fromarray(p4), (960, 780))

draw = ImageDraw.Draw(sheet)
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 23)
    font_label = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 17)
    font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 14)
except Exception:
    font_title = font_label = font_sub = ImageFont.load_default()

draw.rectangle([0, 0, 1920, 78], fill=(24, 28, 34))
draw.text((28, 24), "3D-МОДЕЛЬ ПО РЕФЕРЕНСУ: ТЯЖЕЛЫЙ ДРЕДНОУТ (HIGH-DETAIL HARD-SURFACE MESH)", fill=(235, 240, 245), font=font_title)
stats_txt = f"Вершин: {len(V1):,}   |   Треугольников: {len(F1):,}   |   Сглаженные фаски + PBR потертости граней"
draw.text((1050, 28), stats_txt, fill=(245, 165, 65), font=font_sub)

draw.line([(960, 80), (960, 1480)], fill=(65, 72, 82), width=3)
draw.line([(0, 780), (1920, 780)], fill=(65, 72, 82), width=3)
draw.line([(0, 78), (1920, 78)], fill=(215, 120, 40), width=2)

# Place HUD caption bars cleanly at the bottom-left of each viewport so nothing ever overlaps the top of the model!
badges = [
    (20, 712,  "РАКУРС 01 // СТОЙКА С РЕФЕРЕНСА (STUDIO PBR RENDER)", "Цельный кожух оптики, трехпалая клешня с энергощитом и спаренный рельсотрон"),
    (980, 712, "РАКУРС 02 // БОЕВАЯ СТОЙКА С РЕФЕРЕНСА (COMBAT POSE)", "Разворот корпуса, наведение рельсотрона и открытые люки ракетных кассет"),
    (20, 1412, "РАКУРС 03 // ПЛОТНАЯ 3D-СЕТКА (WIREFRAME TOPOLOGY)", f"Детализированная геометрия ({len(F1):,} треугольников, фаски и шарниры)"),
    (980, 1412,"РАКУРС 04 // ВИД СЗАДИ 3/4 (РЕАКТОРЫ И ГИДРАВЛИКА)", "Турбореакторы в защитной обрешетке, радиаторные жалюзи и поршни ног"),
]
for bx, by, title, sub in badges:
    draw.rounded_rectangle([bx, by, bx+680, by+56], radius=6, fill=(20, 24, 30))
    draw.text((bx+14, by+7), title, fill=(250, 175, 75), font=font_label)
    draw.text((bx+14, by+31), sub, fill=(185, 195, 208), font=font_sub)

out_path = "artifacts/file_generation/ttl=63d/output/dreadnought_3d_screenshots_v2.png"
sheet.save(out_path)
print("Saved updated v2 screenshot sheet to", out_path)
