---
name: human_mesh
description: "Процедурная генерация меша человека / Create or generate procedural human body mesh, character low-poly topology. Trigger on requests to build human mesh, character body geometry, or RTS human unit mesh."
depends_on: [core_geometry_rules]
---

# Human Mesh Skill

## Purpose
Generates procedural low-poly human character mesh topology optimized for RTS games and Rigify skinning.

## Rules

### Rule 1: Proportions Standard
Base height on 8 head units (`HEAD_UNIT = 0.23m` for 1.84m total height).

### Rule 2: Assembly via `make_beam`
Construct limbs and torso segments using `make_beam()` from `core_geometry_rules` rather than rotating primitive cylinders via Euler angles.

### Rule 3: Weld Duplicate Vertices
Execute `mesh.remove_doubles(threshold=0.001)` in Edit mode before export to prevent open seams at limb joints.

### Rule 4: Pre-rigging UV Projection
Generate UV coordinates via `bpy.ops.uv.smart_project(island_margin=0.05)` before skinning to prepare for texturing and normal mapping.

### Rule 5: RTS Polycount Constraint
Target polycount under 3,000 triangles for standard RTS infantry units to ensure high performance with multiple units on screen.

### Rule 6: Modular Anatomical Head Topology & Loose Parts Decomposition (Aniimo Standard)
Monolithic character head/face OBJ exports contain multiple unmerged anatomical subsystems packed as loose mesh components within a single object:
1. **`MAIN_SKIN` (Outer Cranium & Open Eye Sockets)**:
   - Contains forehead, cheeks, nose, jaw, neck seam, and open eye apertures.
   - UV coordinates occupy the full $[0.0, 1.0] \times [0.0, 1.0]$ atlas.
   - Material Slot: `M_Face` (Skin PBR).
2. **`ORAL_CAVITY` (Mouth Interior & Throat)**:
   - Positioned at $Z \in [1.23, 1.26]\text{ m}$, extending backwards along $+Y$ into the throat ($Y \in [-0.061, +0.010]\text{ m}$, width $\sim 5\text{ cm}$).
   - UV coordinates map to the upper boundary strip of the face texture ($U \in [0.16, 0.22]$, $V \in [0.95, 1.00]$).
3. **`EYE_OCCLUSION_RIM` & Tear Ducts**:
   - Left and right eyelid perimeter flanges ($Z \in [1.286, 1.309]\text{ m}$).
   - UV coordinates map to the upper right border of the face texture ($U \in [0.78, 0.84]$, $V \in [0.97, 1.00]$).
4. **`CORNEA_LENS` (Convex Cornea Shells & Highlights)**:
   - Two convex shells sitting directly in the eye apertures ($X \approx \pm 0.03\text{ m}$, $Y \in [-0.061, -0.049]\text{ m}$, $Z \in [1.289, 1.307]\text{ m}$).
   - Vertex counts: 84–85 per eye (LOD1) or 210–217 per eye (LOD0).
   - UV coordinates: Mapped with tile offset $U \in [1.07, 1.93]$ (or dedicated $[0, 1]$ lens atlas).
   - **Critical Rule**: When importing raw compound OBJ heads, the Cornea Lens shells must NEVER share the opaque skin material `M_Face`. If assigned to `M_Face`, texture coordinate wrapping projects the mouth/nostrils onto the cornea shells directly in front of the eyes (the "mini-face on eyeballs" artifact).
   - **Resolution**: Separate the Cornea Lens shells via BMesh into a dedicated `Lens_<Kit>` object or assign them to Material Slot 1 (`M_Lens`) with PBR glass transmission (`Transmission = 0.85`, `Roughness = 0.02`, `Blend Mode = BLEND`). This opens the eye apertures and renders the 3D anime eyeballs beneath with realistic cornea gloss.

### Rule 7: Unity Variant Hash Suffix Matching
When importing modular kit components extracted from Unity bundles (Face, Eyeball, Lens, Eyebrow, Teeth), all components for a given head setup MUST share the identical numerical hash suffix (e.g. `-286867459`).
- Mismatching hash suffixes (such as pairing a `-286867459` Face with a `-1017614748` Lens) results in physical spatial offsets of $1.5$–$2.5\text{ mm}$ along X/Y/Z, causing visible misalignment of cornea shells and clipping through the eyeball or eyelid. Always sort and match candidate OBJs by identical hash tags.

### Rule 8: Modular Compound Hair Architecture (Multi-Submesh Partitioning)
In stylized anime engines (such as Aniimo / Unity), character hair models containing hair accessories (e.g. `Hair_Node` with headband, bandana, ribbons, or hairpins) are packaged as a single composite mesh with discrete submesh polygon index ranges:
1. **Submesh 0 (Hair Strands)**:
   - Primary hair volume, bangs, ponytails, and locks (e.g. polygons $0 \dots 16\,417$).
   - Must be mapped to Material Slot 0 (`M_Hair_Strands`) using the character's base hair gradient texture (`T_Avatar_*_Hair_*_CA.png`) and multiplied with the character root dye tint (`_RootColor`).
2. **Submesh 1+ (Bandanas & Headbands)**:
   - Accessory geometry (e.g. polygons $16\,418 \dots 25\,947$).
   - Must be mapped to Material Slot 1 (`M_Hair_Accessory` / `M_Bandana`) using the accessory print texture containing graphics, logos, or patterns.
- **Critical Rule**: Never assign a single material slot across composite hair meshes; assigning the bandana texture globally wraps star patterns and logos across the hair strands, while assigning the hair gradient to the bandana renders the headband as flat untextured hair.

### Rule 9: Full-Stack Modular Wardrobe Organization & Viewport Optimization
When assembling comprehensive character wardrobe studios (combining bodies, heads, dozens of tops, bottoms, shoes, and hairstyles):
1. **LOD0 Purity**: Filter all imported mesh assets using regex `^((?!lod[1-9]).)*$` to strictly exclude low-poly LOD1, LOD2, and LOD3 models.
2. **Hierarchical Collection Outliner Schema**:
   - `00_RIG_MASTER`: Single master root armature.
   - `01_DEFAULT_OUTFIT`: Complete default assembled character visible at launch.
   - `02_HEAD_KITS`: Modular switchable head kits.
   - `03_HAIRSTYLES`, `04_OUTFITS_SETS`, `05_OUTFITS_TOPS`, `06_OUTFITS_BOTTOMS`, `07_FOOTWEAR`, `08_SOCKS_GLOVES`, `09_ACCESSORIES`.
3. **Viewport Optimization (60+ FPS)**: Set `collection.hide_viewport = True` and `collection.hide_render = True` for all non-active wardrobe collections. This ensures scenes containing 400+ production meshes load in $<2$ seconds without memory spikes or shader compilation freezing.

### Rule 10: Anatomical Coordinate Grids & Age Archetypes
Never mix facial components across different character archetypes:
- **Anime Girl Archetype (`G100xx` / Nicole)**: Compact facial height ($Z \in [1.22, 1.35]\text{ m}$), wide ocular aperture ($X \approx \pm 0.03\text{ m}$), compact jaw. Eyelashes and eyebrows have dedicated curvature matching this socket.
- **Adult Female Archetype (`F100xx` / `F101xx`)**: Elongated facial structure ($Z \in [1.35, 1.55]\text{ m}$), narrower ocular spacing, mature jawline. Eyelash assets from adult female models (e.g. `F10102`) are scaled 15% larger and shifted vertically by $+8\text{ cm}$, causing gross misalignment if placed onto `G100xx` character faces. Always verify archetype compatibility before asset binding.
