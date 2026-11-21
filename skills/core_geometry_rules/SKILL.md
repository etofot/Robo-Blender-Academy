---
name: core_geometry_rules
description: "Static core geometry rules for Blender 3D procedural generation. Governs size=2 cube primitive scaling, bmesh directional beam creation, scale transform application, verified bound measurements, and subsurf shrinkage compensation. Static core rule set for all mesh operations."
---

# Core Geometry Rules

Standard geometry generation rules for procedural 3D model creation in Blender.

## Rules

### Rule 1: Always Use `size=2` for Cube Primitives
A cube primitive created with `size=S` places vertices at `±S/2`. With `size=2`, vertex bounds are `±1.0`. Scaling by `(sx, sy, sz)` directly sets half-extents to `(sx, sy, sz)`.
```python
# CORRECT: size=2 sets half-extents directly
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
obj.scale = (0.60, 0.30, 0.02)  # Box full size: 1.2m x 0.6m x 0.04m
```

### Rule 2: Directional Geometry via bmesh (`make_beam`)
Do not rotate cylinders using Euler angles to connect two points. Use `make_beam(name, start, end, hw, hh)` from `scripts/geometry_utils.py`.

### Rule 3: Immediate Transform Apply Inside Loops
Always execute `bpy.ops.object.transform_apply(scale=True)` immediately after setting `obj.scale`.

### Rule 4: Derive Dimensions from `verify_bounds`
Measure bounds of neighboring parts with `verify_bounds(name)` before calculating lengths of bridging geometry.

### Rule 5: Subsurf Shrinkage & Bevel Alternative
Subdivision surfaces pull mesh bounds inward by 10-15%. Extend bounds by 10-15% or use `BEVEL` modifiers for mechanical/hard-surface models.

## Helper Functions
Functions are available in `scripts/geometry_utils.py`:
- `make_beam(name, start, end, hw, hh)`
- `verify_bounds(name)`
- `verify_overlap(name_a, name_b, axis, min_overlap)`
- `finalize(name)`
- `audit_all()`
