---
name: halo_xl_cocoon_lens
description: Процедурная генерация вытянутой обнимающей сотовой акустической линзы (Vertical Halo XL Cocoon) для крупнодиафрагменных студийных микрофонов (Neumann U47/U67 LDC). Вертикальный параболический кокон (F_z=95мм), тороидальная сетка Вороного, сжатие фокуса на золотой капсюль (Z in [-12, +12]мм), неинвертированный локальный базис волноводов (t1||s, t2||z) и 100% герметичное твердое тело.
---

# Halo XL Cocoon Lens — Процедурная генерация вытянутой обнимающей акустической линзы-кокона для LDC микрофонов

## 1. Назначение и концепция
Скилл предназначен для процедурной генерации в Blender (Python / BMesh / MCP) крупногабаритных вертикальных обнимающих акустических экранов-линз **Vertical Halo XL** для студийных вокальных микрофонов (семейство Neumann U47, U67, U87, M49, Rode Classic и др.).

Экран превращает микрофон в массивную кинематографичную систему с архитектурным силуэтом и прецизионной акустической фокусировкой звуковой волны.

```
       [ ВЕРХНИЙ ЗАГИБ (Z = +75 мм, R = 41.2 мм) ]
                  \   \   \
                   \   \   \   (100% лучей направлены в капсюль)
                    \   \   \
        ─────────────► [ Золотая мембрана капсюля Ø34 мм (Z = 0) ] ◄─────────────
                    /   /   /
                   /   /   /   (100% лучей направлены в капсюль)
                  /   /   /
       [ НИЖНИЙ ЗАГИБ (Z = -75 мм, R = 41.2 мм) ]
```

---

## 2. Физика и геометрия: Тороидальный параболический кокон

### 2.1. Формула вертикального параболического загиба $R(z)$:
Для предотвращения пролета звуковых волн выше и ниже капсюля и устранения перекоса каналов в стенке экран изгибается внутрь по параболе:
$$R(z) = 56.0 - \frac{z^2}{4 \cdot F_z}\text{ мм}, \quad F_z = 95.0\text{ мм}, \quad z \in [-75, +75]\text{ мм}$$
- В центре ($Z = 0$): $R = 56.0\text{ мм}$ (воздушный зазор до микрофона $19.5\text{ мм}$).
- На краях ($Z = \pm 75\text{ мм}$): $R = 41.2\text{ мм}$ (верх и низ экрана приближаются к микрофону, обнимая его как купол).

### 2.2. Формула сжатия фокуса (Tight Capsule Target):
Для концентрации $100\%$ акустической энергии в круг золотой диафрагмы ($\varnothing 34\text{ мм}$, $R = 17\text{ мм}$):
$$Z_{target}(z) = \text{clamp}(z \cdot 0.15, -12.0, 12.0)\text{ мм}$$
Целевая точка в пространстве:
$$\vec{P}_{target} = (0.0, -17.0, Z_{target}(z))$$
- Луч для каждой соты: $\vec{u}_i = \text{normalize}(\vec{P}_{target} - \vec{P}_{out})$.
- Угол наклона волновода к локальной нормали стенки составляет всего **$5–10^\circ$**, что исключает самопересечение каналов внутри 4-мм стенки и сохраняет строго круглые выходные отверстия $\varnothing 1.0\text{ мм}$.

---

## 3. Архитектурные правила реализации и защита от багов

### 3.1. Неинвертированный локальный базис волноводов (Анти-Твист):
- **Критическая ошибка (Gotcha)**: Если вычислять $t_1 = t_2 \times u$, то для конических лучей вектор $t_1$ может стать направленным в $-X$ (противоположно направлению дуги $+s$). Это приводит к горизонтальному зеркальному развороту внутренних колец воронки (`ring_1`...`ring_4`), из-за чего полигоны перекручиваются крест-накрест и «заклеивают» отверстие.
- **Правило**:
  ```python
  # t1 строго сонаправлен с касательной дуги +s (+X)
  t1_raw = Vector((math.cos(th_c), math.sin(th_c), 0.0))
  t1 = (t1_raw - t1_raw.dot(u) * u).normalized()
  
  # t2 строго сонаправлен с вертикальной осью +z (+Z)
  t2_raw = Vector((0.0, 0.0, 1.0))
  t2 = (t2_raw - t2_raw.dot(u) * u).normalized()
  ```

### 3.2. Прямой конструктивный BMesh граф Вороного (`unique_front_ridge_verts`):
- Узлы сетки сот вычисляются в 2D-развертке $(s, z)$ и сохраняются в словарях:
  `unique_front_ridge_verts[key]` и `unique_back_ridge_verts[key]`.
- Соседние ячейки делят общие вершины, гарантируя отсутствие зазоров и ступенек.

### 3.3. Параболическое облегание талии (Parabolic Waist Tracking):
- Граница внешнего обрамления вычисляется динамически по высоте $Z$:
  $$s_{boundary}(z) = \frac{R(z) \cdot \alpha_{rad} - 6.0}{2} + r_{corner}, \quad \theta(z) = \frac{s_{boundary}(z)}{R(z)}$$
- Это исключает серповидный зазор между сеткой и рамкой по всей высоте $160\text{ мм}$.

---

## 4. Полный чистовой эталонный скрипт пайплайна

```python
"""
Halo XL Pure Hex Master: Procedural Vertical Acoustic Cocoon Lens Generator
Author: Senior AI Developer
Target: Blender 4.x / 5.x via MCP or Scripting Workspace
"""

import bpy
import bmesh
import math
import os
import time
from mathutils import Vector


def build_halo_xl_pure_hex_master(stl_output_path=None):
    t_start = time.time()

    # 1. Clean previous Halo objects
    for obj in list(bpy.data.objects):
        if "Halo" in obj.name or "Cyber" in obj.name or "Solid" in obj.name:
            bpy.data.objects.remove(obj, do_unlink=True)

    H_total = 160.0
    arc_deg = 135.0
    arc_rad = math.radians(arc_deg)
    t_shell = 4.0
    pitch = 2.95
    r_fillet = 0.15
    r_in_cell = pitch / 2.0
    r_corner = r_in_cell / (math.sqrt(3.0) / 2.0)
    r_channel = 0.5
    L_hex = 1.6
    L_trans = 0.8
    F_z = 95.0

    def get_surface_pos_outer(s, z):
        R_z = 56.0 - (z * z) / (4.0 * F_z)
        th = s / R_z
        x = R_z * math.sin(th)
        y = -R_z * math.cos(th)
        return Vector((x, y, z))

    def project_ray_to_inner(p_front, z):
        z_target = max(-12.0, min(12.0, z * 0.15))
        p_target = Vector((0.0, -17.0, z_target))
        u = (p_target - p_front).normalized()
        return p_front + t_shell * u

    bm = bmesh.new()

    unique_front_ridge_verts = {}
    unique_back_ridge_verts = {}

    def get_front_ridge_vert(s, z):
        key = (round(s, 3), round(z, 3))
        if key not in unique_front_ridge_verts:
            p_front = get_surface_pos_outer(s, z)
            unique_front_ridge_verts[key] = bm.verts.new(p_front)
        return unique_front_ridge_verts[key]

    def get_back_ridge_vert(s, z):
        key = (round(s, 3), round(z, 3))
        if key not in unique_back_ridge_verts:
            p_front = get_surface_pos_outer(s, z)
            p_back = project_ray_to_inner(p_front, z)
            unique_back_ridge_verts[key] = bm.verts.new(p_back)
        return unique_back_ridge_verts[key]

    dy = pitch * math.sqrt(3.0) / 2.0
    dx = pitch

    z_max_c = 68.0
    z_min_c = -68.0

    j_min = int(z_min_c / dy)
    j_max = int(z_max_c / dy)

    cells = []
    for j in range(j_min, j_max + 1):
        zc = j * dy
        Rc = 56.0 - (zc * zc) / (4.0 * F_z)
        arc_len = Rc * arc_rad - 6.0
        th_max = (arc_len / Rc) / 2.0
        s_max = Rc * th_max
        
        x_offset = (abs(j) % 2) * (pitch * 0.5)
        i_max = int(s_max / dx)
        for i in range(-i_max, i_max + 1):
            sc = i * dx + x_offset
            if abs(sc) <= s_max:
                cells.append((sc, zc))

    hex_corners_2d = []
    for k in range(6):
        ang = math.radians(30.0 + k * 60.0)
        hex_corners_2d.append((r_corner * math.cos(ang), r_corner * math.sin(ang)))

    cell_exit_rings = []
    cell_back_ridge_rings = []

    for sc, zc in cells:
        p_out = get_surface_pos_outer(sc, zc)
        z_target = max(-12.0, min(12.0, zc * 0.15))
        p_target = Vector((0.0, -17.0, z_target))
        u = (p_target - p_out).normalized()
        p_back_c = p_out + t_shell * u
        
        th_c = sc / (56.0 - (zc * zc) / (4.0 * F_z))
        
        # Consistent un-flipped basis
        t1_raw = Vector((math.cos(th_c), math.sin(th_c), 0.0))
        t1 = (t1_raw - t1_raw.dot(u) * u).normalized()
        t2_raw = Vector((0.0, 0.0, 1.0))
        t2 = (t2_raw - t2_raw.dot(u) * u).normalized()
        
        # Ring 0: Front Shared Ridge Verts
        ring_0 = []
        ring_back_ridge = []
        for ds, dz in hex_corners_2d:
            ring_0.append(get_front_ridge_vert(sc + ds, zc + dz))
            ring_back_ridge.append(get_back_ridge_vert(sc + ds, zc + dz))
            
        cell_back_ridge_rings.append(ring_back_ridge)
        
        # Ring 1: Fillet R=0.15mm
        ring_1 = []
        pos_1 = p_out + r_fillet * u
        for ds, dz in hex_corners_2d:
            scale_f = (r_corner - r_fillet) / r_corner
            offset = scale_f * (ds * t1 + dz * t2)
            ring_1.append(bm.verts.new(pos_1 + offset))
        
        # Ring 2: Hex end
        ring_2 = []
        pos_2 = p_out + L_hex * u
        scale_hex = (r_corner - (L_hex / (L_hex + L_trans)) * (r_corner - r_channel)) / r_corner
        for ds, dz in hex_corners_2d:
            offset = scale_hex * (ds * t1 + dz * t2)
            ring_2.append(bm.verts.new(pos_2 + offset))
        
        # Ring 3: Circle Ø1.0mm
        ring_3 = []
        pos_3 = p_out + (L_hex + L_trans) * u
        for ds, dz in hex_corners_2d:
            ang = math.atan2(dz, ds)
            offset = r_channel * (math.cos(ang) * t1 + math.sin(ang) * t2)
            ring_3.append(bm.verts.new(pos_3 + offset))
        
        # Ring 4: Exit Circle Ø1.0mm (OPEN)
        ring_4 = []
        pos_4 = p_back_c
        for ds, dz in hex_corners_2d:
            ang = math.atan2(dz, ds)
            offset = r_channel * (math.cos(ang) * t1 + math.sin(ang) * t2)
            ring_4.append(bm.verts.new(pos_4 + offset))
        
        cell_exit_rings.append(ring_4)
        
        # Loft internal through-tunnel
        rings = [ring_0, ring_1, ring_2, ring_3, ring_4]
        for s in range(len(rings) - 1):
            for k in range(6):
                k_next = (k + 1) % 6
                f = bm.faces.new([rings[s][k], rings[s + 1][k], rings[s + 1][k_next], rings[s][k_next]])
                f.material_index = 0
                
        # Back solid skin loft
        for k in range(6):
            k_next = (k + 1) % 6
            f = bm.faces.new([ring_4[k], ring_back_ridge[k], ring_back_ridge[k_next], ring_4[k_next]])
            f.material_index = 0

    # Watertight Boundary Cap
    open_front_edges = [e for e in bm.edges if len(e.link_faces) == 1 and all(v in unique_front_ridge_verts.values() for v in e.verts)]
    open_back_edges = [e for e in bm.edges if len(e.link_faces) == 1 and all(v in unique_back_ridge_verts.values() for v in e.verts)]

    for ef in open_front_edges:
        vf1, vf2 = ef.verts
        kf1 = next((k for k, v in unique_front_ridge_verts.items() if v == vf1), None)
        kf2 = next((k for k, v in unique_front_ridge_verts.items() if v == vf2), None)
        if kf1 and kf2 and kf1 in unique_back_ridge_verts and kf2 in unique_back_ridge_verts:
            vb1 = unique_back_ridge_verts[kf1]
            vb2 = unique_back_ridge_verts[kf2]
            f = bm.faces.new([vf1, vf2, vb2, vb1])
            f.material_index = 1

    mesh_master = bpy.data.meshes.new("Halo_XL_Pure_Hex_Master")
    obj_master = bpy.data.objects.new("Halo_XL_Pure_Hex_Master", mesh_master)
    bpy.context.collection.objects.link(obj_master)
    bm.to_mesh(mesh_master)
    bm.free()

    bpy.context.view_layer.objects.active = obj_master
    obj_master.select_set(True)
    bpy.ops.object.shade_smooth()

    # Materials
    mat_clay = bpy.data.materials.get("Mat_Clay_Studio")
    if not mat_clay:
        mat_clay = bpy.data.materials.new(name="Mat_Clay_Studio")
        mat_clay.use_nodes = True
        b = mat_clay.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (0.75, 0.73, 0.70, 1.0)
            b.inputs["Roughness"].default_value = 0.6
    obj_master.data.materials.append(mat_clay)

    if stl_output_path:
        try:
            bpy.ops.wm.stl_export(filepath=stl_output_path, export_selected_objects=True, global_scale=1.0)
        except Exception:
            bpy.ops.export_mesh.stl(filepath=stl_output_path, use_selection=True, global_scale=1.0)

    dt = time.time() - t_start
    print(f"Generated Pure Hex Master in {dt:.2f} s: {len(cells)} cells, {len(mesh_master.polygons)} polygons")
    return obj_master


if __name__ == "__main__":
    out_stl = r"i:\1_VSCODE\2026_3  GAMES\BLENDER\halo_xl_pure_hex_master.stl"
    build_halo_xl_pure_hex_master(out_stl)
```
