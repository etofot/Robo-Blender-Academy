# 03. Прецизионная Нарезка Панелей и Фонарей Кабины через `bisect_plane`

Вместо сложного полигонального моделирования щелей и кабин используй алгоритм секущей плоскости BMesh:

```python
import bpy, bmesh
from mathutils import Vector

def slice_cockpit_glass(obj, y_front=1.58, y_rear=1.05, slot_glass=1):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    
    # 1. Срез передней кромки фонаря
    bmesh.ops.bisect_plane(
        bm,
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        plane_co=Vector((0, y_front, 0)),
        plane_no=Vector((0, 1, 0)),
        clear_outer=False, clear_inner=False
    )
    
    # 2. Срез задней кромки фонаря
    bmesh.ops.bisect_plane(
        bm,
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        plane_co=Vector((0, y_rear, 0)),
        plane_no=Vector((0, 1, 0)),
        clear_outer=False, clear_inner=False
    )
    
    # 3. Назначение стеклянного материала на вырезанную зону
    for f in bm.faces:
        c = f.calc_center_median()
        if y_rear <= c.y <= y_front and c.z > 0.05 and abs(c.x) < 0.35 and f.normal.z > 0.15:
            f.material_index = slot_glass
            
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
```
