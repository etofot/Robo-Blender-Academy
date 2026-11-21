---
name: human_texture
description: "Текстурирование человека, PBR материалы кожи и одежды / Texture human character, PBR skin, clothing shader. Trigger on requests for character texturing, skin shader setup, or clothing materials."
depends_on: [human_mesh]
---

# Human Texture Skill

## Purpose
Sets up PBR materials, non-color data nodes, and texture slot assignments for organic character meshes.

## Rules

### Rule 1: Non-Color Space for Data Maps
Always set `image.colorspace_settings.name = 'Non-Color'` for Roughness, Metallic, and Normal Map image textures to prevent gamma distortion.

### Rule 2: Programmatic PBR Shader Graphs
Construct shader networks by linking `ShaderNodeTexImage` nodes directly to `Principled BSDF` sockets via Python.

### Rule 3: Material Slot Partitioning
Separate skin, apparel, and eyes into discrete material slots assigned to specific polygon selections on a shared UV atlas.

### Rule 4: Face Multi-Material Slot Architecture (Skin vs Cornea Lens)
Compound game head meshes require distinct material slots:
1. **Slot 0 (`M_Face`)**: Outer skin, oral cavity, and eye occlusion rims.
   - Nodes: `ShaderNodeTexImage` (`T_Avatar_*_Face_*_CA.png`) -> `Principled BSDF` `Base Color`.
   - Settings: `Roughness = 0.58`, `Subsurface Weight = 0.08`, `Specular IOR Level = 0.25`.
   - Alpha Mode: `image.alpha_mode = 'NONE'` to prevent EEVEE diffuse black-crush.
2. **Slot 1 (`M_Lens_Master`)**: Cornea lens convex shells sitting in the eye apertures.
   - Nodes: `Principled BSDF` with `Base Color = (1.0, 1.0, 1.0, 1.0)`, `Alpha = 0.08`, `Roughness = 0.05`, `Specular IOR Level = 0.7`.
   - Settings: `Transmission Weight = 0.0`, `IOR = 1.0` (eliminates screen-space refraction distortion across the iris).
   - Blend Mode: `material.blend_method = 'BLEND'`, `material.surface_render_method = 'BLENDED'`.
   - *Never allow Cornea Lens polygons to use `M_Face`*, as this causes the "mini-face on eyeballs" artifact.

### Rule 5: Eyelashes & Eyebrows Alpha-Stencil Rule
Anime game eyelash and eyebrow textures (`*_Eyelash_*_CA.png`, `*_Eyebrow_*_CA.png`) store contour shapes in the Alpha channel, while the RGB channels contain a uniform flat gray/white base (RGB $\approx 188$ or $125$).
- **Requirement 1 (Alpha Channel Preservation)**: The image texture node MUST have `image.alpha_mode = 'STRAIGHT'` (or `'CHANNEL_PACKED'`). NEVER set `alpha_mode = 'NONE'` on eyelash/eyebrow textures, as doing so strips the alpha transparency and forces the entire polygon quad to render as an opaque white cardboard strip.
- **Requirement 2 (Base Color Disconnection)**: Never link texture `Color` directly to `Base Color` on lash/brow shaders; this renders eyelashes stark white/gray.
- **Node Setup**:
  1. Connect texture `Alpha` output directly to `Principled BSDF` `Alpha`.
  2. Set `Principled BSDF` `Base Color` default value directly to pitch black `(0.010, 0.008, 0.008, 1.0)` for eyelashes, or warm dark brown `(0.045, 0.030, 0.022, 1.0)` for eyebrows.
  3. Set `Specular IOR Level = 0.0` and `Roughness = 0.95` to eliminate harsh white specular glare along transparent polygon edges.
  4. Enable `blend_method = 'BLEND'` / `surface_render_method = 'BLENDED'`.

### Rule 6: Selective Diffuse vs Stencil Alpha Mode Classification
- **Diffuse Textures (`Face`, `Body`, `Eyeball`, `Outfit`)**: Textures extracted from Unity packages with `_CA` naming often store packed shader masks or zero values in their Alpha channel. In Blender 4.x/5.x, importing these textures with default `alpha_mode = 'STRAIGHT'` causes Blender to premultiply/zero out colors, rendering characters pitch black in EEVEE. For these textures, execute `image.alpha_mode = 'NONE'` so Blender samples raw RGB color values uncorrupted.
- **Stencil / Mask Textures (`Eyelash`, `Eyebrow`, `Lace`, `Hair Alpha`)**: These textures rely on non-zero alpha transparency to carve out hair strands. For these textures, execute `image.alpha_mode = 'STRAIGHT'`.

### Rule 7: Cornea Lens Reflection Glass Architecture (Zero Refraction Distortion)
In real-time anime character rendering, cornea eye shells must NOT use physical dielectric glass refraction (`IOR = 1.45`, `Transmission > 0.5`).
- **Prismatic Seam Artifact**: Because the cornea shell is an extremely thin, curved meniscus situated $0.5$–$1.5\text{ mm}$ in front of the flat iris disc, physical screen-space refraction creates artificial prismatic refraction seams and visual double-contours across the pupil.
- **Resolution**: Use pure specular reflection shading:
  - `Transmission Weight = 0.0` (or `IOR = 1.0`).
  - `Roughness = 0.05` for ultra-sharp specular glints.
  - `Specular IOR Level = 0.7`–$0.8$.
  - `Base Color = (1.0, 1.0, 1.0, 1.0)`.
  - `Alpha = 0.05`–$0.08$ with `blend_method = 'BLEND'`.
  This allows 100% undistorted visual clarity of the 3D anime eyeball beneath while providing a wet, glossy eye highlight that tracks camera movement.

### Rule 8: Multi-Submesh Material Splitting for Compound Hair & Apparel
When a character component (such as `Hair_Node`) contains both volumetric hair geometry and rigid fabric accessories (bandanas, hair ribbons, headbands):
1. **Material Partitioning by Submesh Index**:
   - `Slot 0` (`M_Hair_Strands`): Assigned to strand polygons (e.g. index $< 16\,418$). Uses base hair gradient texture (`T_Avatar_*_Hair_*_CA.png`) blended via `ShaderNodeMix` (Multiply mode, Factor 1.0) with character root dye color `_RootColor = (1.0, 0.65, 0.72)`.
   - `Slot 1` (`M_Bandana` / `M_Accessory`): Assigned to accessory polygons (e.g. index $\ge 16\,418$). Uses the patterned print texture (`T_Avatar_*_Hair_*_CA` containing graphics, logos, stars).
2. **Preventing Texture Cross-Contamination**:
   - Never apply the accessory texture to hair strands (renders hair as blue fabric with logos).
   - Never apply the hair gradient to accessories (renders headbands as solid bald patches).

### Rule 9: Eyeball Composite UV Mapping
Character eyeball meshes utilize a hemispherical UV projection where the pupil and iris center exactly at UV coordinate $(0.5, 0.5)$.
- The eyeball material must be assigned a composite texture (`Eyeball_Composite_*.png` or `T_Avatar_Girl_Eyeball_Composite_*.png`) containing sclera, iris, and pupil.
- Eyeball shader parameters: `Roughness = 0.05`, `Specular IOR Level = 0.7` for glassy wet ocular reflections.
