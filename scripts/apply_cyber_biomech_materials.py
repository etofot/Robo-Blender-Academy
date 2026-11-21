import bpy
import math

def clear_material(mat):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    for n in list(nodes):
        nodes.remove(n)
    return nodes, mat.node_tree.links

# -------------------------------------------------------------------------
# 1. B1_Plate: LUXURY AEROSPACE CARBON FIBER (TWILL WEAVE + SUBTLE SCUFFS)
# -------------------------------------------------------------------------
def setup_carbon_plate_material(mat_name="B1_Plate"):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nodes, links = clear_material(mat)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (850, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (550, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1300, 0)
    
    # 45-degree rotated mapping for diagonal carbon twill
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-1100, 150)
    mapping.inputs['Rotation'].default_value = (0.0, 0.0, math.radians(45.0))
    mapping.inputs['Scale'].default_value = (280.0, 280.0, 280.0)
    links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
    
    # Alternating Twill Weave Bands
    wave_x = nodes.new('ShaderNodeTexWave')
    wave_x.location = (-850, 300)
    wave_x.wave_type = 'BANDS'
    wave_x.bands_direction = 'X'
    wave_x.inputs['Scale'].default_value = 1.0
    wave_x.inputs['Distortion'].default_value = 0.1
    links.new(mapping.outputs['Vector'], wave_x.inputs['Vector'])
    
    wave_y = nodes.new('ShaderNodeTexWave')
    wave_y.location = (-850, 100)
    wave_y.wave_type = 'BANDS'
    wave_y.bands_direction = 'Y'
    wave_y.inputs['Scale'].default_value = 1.0
    wave_y.inputs['Distortion'].default_value = 0.1
    links.new(mapping.outputs['Vector'], wave_y.inputs['Vector'])
    
    # Checker modulation for twill 2x2 weave
    mix_weave = nodes.new('ShaderNodeMix')
    mix_weave.location = (-600, 200)
    mix_weave.data_type = 'FLOAT'
    mix_weave.inputs['Factor'].default_value = 0.5
    links.new(wave_x.outputs['Color'], mix_weave.inputs[2])
    links.new(wave_y.outputs['Color'], mix_weave.inputs[3])
    
    # Tactile Carbon Weave Bump (Subtle 0.3mm micro-weave)
    bump_weave = nodes.new('ShaderNodeBump')
    bump_weave.location = (-300, 200)
    bump_weave.inputs['Distance'].default_value = 0.0004
    bump_weave.inputs['Strength'].default_value = 0.28
    links.new(mix_weave.outputs[0], bump_weave.inputs['Height'])
    
    # Sparse Battle Scratches Mask
    # 1. Mask noise: scratches only occur in random clusters, not everywhere!
    noise_mask = nodes.new('ShaderNodeTexNoise')
    noise_mask.location = (-1100, -300)
    noise_mask.inputs['Scale'].default_value = 3.0
    noise_mask.inputs['Detail'].default_value = 2.0
    links.new(tex_coord.outputs['Object'], noise_mask.inputs['Vector'])
    
    ramp_mask = nodes.new('ShaderNodeValToRGB')
    ramp_mask.location = (-850, -300)
    ramp_mask.color_ramp.elements[0].position = 0.45
    ramp_mask.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0) # No scratches
    ramp_mask.color_ramp.elements[1].position = 0.65
    ramp_mask.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0) # Scratches allowed
    links.new(noise_mask.outputs['Fac'], ramp_mask.inputs['Fac'])
    
    # 2. Razor scratch lines
    scratch_vor = nodes.new('ShaderNodeTexVoronoi')
    scratch_vor.location = (-850, -550)
    scratch_vor.feature = 'DISTANCE_TO_EDGE'
    scratch_vor.inputs['Scale'].default_value = 32.0
    links.new(tex_coord.outputs['Object'], scratch_vor.inputs['Vector'])
    
    ramp_scratch = nodes.new('ShaderNodeValToRGB')
    ramp_scratch.location = (-600, -550)
    # Razor thin scratch line: only distance < 0.008
    ramp_scratch.color_ramp.elements[0].position = 0.006
    ramp_scratch.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    ramp_scratch.color_ramp.elements[1].position = 0.015
    ramp_scratch.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    links.new(scratch_vor.outputs['Distance'], ramp_scratch.inputs['Fac'])
    
    # Multiply scratch by mask so it's sparse
    math_scratch_final = nodes.new('ShaderNodeMath')
    math_scratch_final.location = (-350, -400)
    math_scratch_final.operation = 'MULTIPLY'
    links.new(ramp_mask.outputs['Color'], math_scratch_final.inputs[0])
    links.new(ramp_scratch.outputs['Color'], math_scratch_final.inputs[1])
    
    # Chained Bump for Scratches
    bump_scratch = nodes.new('ShaderNodeBump')
    bump_scratch.location = (100, 150)
    bump_scratch.inputs['Distance'].default_value = 0.0008
    bump_scratch.inputs['Strength'].default_value = 0.40
    links.new(math_scratch_final.outputs['Value'], bump_scratch.inputs['Height'])
    links.new(bump_weave.outputs['Normal'], bump_scratch.inputs['Normal'])
    links.new(bump_scratch.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Carbon Fiber Color (Deep charcoal graphite base with subtle fiber sheen)
    mix_color = nodes.new('ShaderNodeMix')
    mix_color.location = (0, -100)
    mix_color.data_type = 'RGBA'
    links.new(mix_weave.outputs[0], mix_color.inputs['Factor'])
    # Deep anthracite black
    mix_color.inputs[6].default_value = (0.022, 0.024, 0.028, 1.0)
    # Slightly lighter graphite fiber
    mix_color.inputs[7].default_value = (0.038, 0.040, 0.046, 1.0)
    
    # Scratched Color Mix
    mix_scratch_col = nodes.new('ShaderNodeMix')
    mix_scratch_col.location = (250, -100)
    mix_scratch_col.data_type = 'RGBA'
    links.new(math_scratch_final.outputs['Value'], mix_scratch_col.inputs['Factor'])
    links.new(mix_color.outputs[2], mix_scratch_col.inputs[6])
    mix_scratch_col.inputs[7].default_value = (0.12, 0.12, 0.14, 1.0) # Subtle scuff
    links.new(mix_scratch_col.outputs[2], bsdf.inputs['Base Color'])
    
    # Roughness
    mix_rough = nodes.new('ShaderNodeMix')
    mix_rough.location = (250, -300)
    mix_rough.data_type = 'FLOAT'
    links.new(math_scratch_final.outputs['Value'], mix_rough.inputs['Factor'])
    mix_rough.inputs[2].default_value = 0.22 # Smooth resin gloss
    mix_rough.inputs[3].default_value = 0.55 # Scuffed scratch
    links.new(mix_rough.outputs[0], bsdf.inputs['Roughness'])
    
    bsdf.inputs['Metallic'].default_value = 0.12
    bsdf.inputs['Coat Weight'].default_value = 0.90
    bsdf.inputs['Coat Roughness'].default_value = 0.10
    return mat

# -------------------------------------------------------------------------
# 2. B1_Chitin: LUSTROUS ALIEN OBSIDIAN CARAPACE (HIGH SPECULAR, MICRO-PORES)
# -------------------------------------------------------------------------
def setup_chitin_obsidian_material(mat_name="B1_Chitin"):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nodes, links = clear_material(mat)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (850, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (550, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1200, 0)
    
    # Micro Chitin Cuticle Pores
    vor_pores = nodes.new('ShaderNodeTexVoronoi')
    vor_pores.location = (-900, 150)
    vor_pores.feature = 'F1'
    vor_pores.inputs['Scale'].default_value = 110.0
    links.new(tex_coord.outputs['Object'], vor_pores.inputs['Vector'])
    
    bump_pores = nodes.new('ShaderNodeBump')
    bump_pores.location = (-600, 150)
    bump_pores.inputs['Distance'].default_value = 0.0003
    bump_pores.inputs['Strength'].default_value = 0.16
    links.new(vor_pores.outputs['Distance'], bump_pores.inputs['Height'])
    
    # Organic Muscle Flow Striations
    noise_flow = nodes.new('ShaderNodeTexNoise')
    noise_flow.location = (-900, -100)
    noise_flow.inputs['Scale'].default_value = 4.0
    noise_flow.inputs['Detail'].default_value = 3.0
    noise_flow.inputs['Roughness'].default_value = 0.5
    links.new(tex_coord.outputs['Object'], noise_flow.inputs['Vector'])
    
    bump_flow = nodes.new('ShaderNodeBump')
    bump_flow.location = (-300, 100)
    bump_flow.inputs['Distance'].default_value = 0.0015
    bump_flow.inputs['Strength'].default_value = 0.22
    links.new(noise_flow.outputs['Fac'], bump_flow.inputs['Height'])
    links.new(bump_pores.outputs['Normal'], bump_flow.inputs['Normal'])
    links.new(bump_flow.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Deep Obsidian Black
    bsdf.inputs['Base Color'].default_value = (0.012, 0.013, 0.016, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.30
    bsdf.inputs['Roughness'].default_value = 0.12 # Sleek glossy chitin
    bsdf.inputs['IOR'].default_value = 1.62
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.05
    return mat

# -------------------------------------------------------------------------
# 3. B1_Eye: CYBERNETIC SAPPHIRE OPTICS WITH INTERNAL DIGITAL CORE GLOW
# -------------------------------------------------------------------------
def setup_eye_sapphire_glow_material(mat_name="B1_Eye"):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nodes, links = clear_material(mat)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (850, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (550, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1200, 0)
    
    # Internal Digital Scanning Grid
    vor_cells = nodes.new('ShaderNodeTexVoronoi')
    vor_cells.location = (-900, 100)
    vor_cells.feature = 'F1'
    vor_cells.inputs['Scale'].default_value = 35.0
    links.new(tex_coord.outputs['Object'], vor_cells.inputs['Vector'])
    
    scan_ramp = nodes.new('ShaderNodeValToRGB')
    scan_ramp.location = (-650, 100)
    scan_ramp.color_ramp.elements[0].position = 0.0
    scan_ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    scan_ramp.color_ramp.elements[1].position = 0.35
    scan_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    links.new(vor_cells.outputs['Distance'], scan_ramp.inputs['Fac'])
    
    math_mult = nodes.new('ShaderNodeMath')
    math_mult.location = (-400, 100)
    math_mult.operation = 'MULTIPLY'
    math_mult.inputs[1].default_value = 3.6
    links.new(scan_ramp.outputs['Color'], math_mult.inputs[0])
    
    # Electric Cyan Plasma Emission
    bsdf.inputs['Emission Color'].default_value = (0.05, 0.60, 1.0, 1.0)
    links.new(math_mult.outputs['Value'], bsdf.inputs['Emission Strength'])
    
    # Deep Sapphire Crystal
    bsdf.inputs['Base Color'].default_value = (0.015, 0.045, 0.16, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.20
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['IOR'].default_value = 1.58
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.02
    return mat

# -------------------------------------------------------------------------
# 4. B1_Steel: MACHINED AEROSPACE TITANIUM STEEL (MICRO-BRUSHED ANISOTROPY)
# -------------------------------------------------------------------------
def setup_steel_machined_material(mat_name="B1_Steel"):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nodes, links = clear_material(mat)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (850, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (550, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1200, 0)
    
    # Fine Lathe/Milling Micro-grooves
    noise_brush = nodes.new('ShaderNodeTexNoise')
    noise_brush.location = (-850, 150)
    noise_brush.inputs['Scale'].default_value = 140.0
    noise_brush.inputs['Detail'].default_value = 3.0
    noise_brush.inputs['Roughness'].default_value = 0.65
    links.new(tex_coord.outputs['Object'], noise_brush.inputs['Vector'])
    
    bump_brush = nodes.new('ShaderNodeBump')
    bump_brush.location = (-550, 150)
    bump_brush.inputs['Distance'].default_value = 0.0003
    bump_brush.inputs['Strength'].default_value = 0.18
    links.new(noise_brush.outputs['Fac'], bump_brush.inputs['Height'])
    links.new(bump_brush.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Gleaming Titanium Steel
    bsdf.inputs['Base Color'].default_value = (0.64, 0.66, 0.70, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.18
    return mat

# -------------------------------------------------------------------------
# 5. B1_Dark: TACTICAL BRAIDED KEVLAR CONDUIT
# -------------------------------------------------------------------------
def setup_dark_kevlar_material(mat_name="B1_Dark"):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nodes, links = clear_material(mat)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (850, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (550, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1200, 0)
    
    wave_diag = nodes.new('ShaderNodeTexWave')
    wave_diag.location = (-800, 150)
    wave_diag.wave_type = 'BANDS'
    wave_diag.inputs['Scale'].default_value = 90.0
    wave_diag.inputs['Distortion'].default_value = 0.4
    links.new(tex_coord.outputs['Object'], wave_diag.inputs['Vector'])
    
    bump_weave = nodes.new('ShaderNodeBump')
    bump_weave.location = (-500, 100)
    bump_weave.inputs['Distance'].default_value = 0.001
    bump_weave.inputs['Strength'].default_value = 0.35
    links.new(wave_diag.outputs['Color'], bump_weave.inputs['Height'])
    links.new(bump_weave.outputs['Normal'], bsdf.inputs['Normal'])
    
    bsdf.inputs['Base Color'].default_value = (0.016, 0.016, 0.019, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.05
    bsdf.inputs['Roughness'].default_value = 0.50
    return mat

# -------------------------------------------------------------------------
# 6. B1_SensorLED: GLOWING OPTICAL SENSOR CORE (TEMPLE PIVOTS)
# -------------------------------------------------------------------------
def setup_sensor_led_material(mat_name="B1_SensorLED"):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nodes, links = clear_material(mat)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (0.01, 0.03, 0.08, 1.0)
    bsdf.inputs['Emission Color'].default_value = (0.06, 0.80, 1.0, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 6.0
    bsdf.inputs['Roughness'].default_value = 0.10
    return mat

def apply_all_materials():
    print("Building refined procedural PBR shader network...")
    setup_carbon_plate_material("B1_Plate")
    setup_chitin_obsidian_material("B1_Chitin")
    setup_eye_sapphire_glow_material("B1_Eye")
    setup_steel_machined_material("B1_Steel")
    setup_dark_kevlar_material("B1_Dark")
    setup_sensor_led_material("B1_SensorLED")
    
    for name in ['Cylinder.002', 'Cylinder.005']:
        o = bpy.data.objects.get(name)
        if o and hasattr(o.data, 'materials'):
            if len(o.data.materials) > 0:
                o.data.materials[0] = bpy.data.materials['B1_SensorLED']
            else:
                o.data.materials.append(bpy.data.materials['B1_SensorLED'])
            print(f"Assigned B1_SensorLED to {name}")
            
    print("Refined materials applied successfully.")

if __name__ == '__main__':
    apply_all_materials()
