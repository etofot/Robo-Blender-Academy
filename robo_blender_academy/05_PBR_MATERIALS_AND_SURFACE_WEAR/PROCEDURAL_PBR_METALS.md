# 05. Процедурные PBR Металлы, Броня и Износ

Для техники критически важна реалистичная фактура закаленной стали, сколов краски и потертостей на острых углах.

---

## 1. Базовый Шейдер Танковой Брони в Node Editor

```python
import bpy

def create_procedural_armor_material(name, base_color=(0.12, 0.14, 0.13)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Узлы
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.90 # Твердая сталь
    
    # Генерация неоднородной шероховатости (Roughness)
    noise.inputs["Scale"].default_value = 25.0
    noise.inputs["Detail"].default_value = 8.0
    
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1.0) # полированный металл
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.65, 0.65, 0.65, 1.0) # матовая окалина
    
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat
```

---

## 2. Сколы на ребрах через ноду Geometry (Pointiness / Bevel)
Для выявления ребер брони в шейдере используется вектор нормали геометрии (`ShaderNodeBevel` в Cycles или `Geometry.Pointiness`), который подмешивает светлый серебристый цвет сбитой до голого металла краски на выступающих углах.
