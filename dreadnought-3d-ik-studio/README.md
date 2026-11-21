# Dreadnought MK-IV TITAN — 3D Procedural Mech & IK Animation Studio

Interactive single-file WebGL / Three.js procedural 3D mech studio featuring **conformal topology UV mapping**, **in-memory procedural PBR CanvasTextures** (weld seams, rivets, edge wear, military stencils, and 3D bump relief), **analytical 2-bone Inverse Kinematics (Zero-Drift Foot IK)**, **11 full-body animations**, **synthesized WebAudio SFX**, and **3D export (`.GLTF`, `.OBJ`, `.STL`)**.

## Repository Structure

* `index.html` / `dreadnought_3d_studio.html` — Complete interactive 3D studio (zero external asset dependencies; runs immediately in any browser or GitHub Pages).
* `SKILL.md` & `skills/procedural-3d-mech-animator/SKILL.md` — Portable AI Agent Skill definition following standard `SKILL.md` frontmatter and workflow specifications so other AI agents can build procedural 3D mechs, conformal UVs, and IK animations.
* `docs/ANIMATION_AND_IK_GUIDE_RU.md` — Detailed engineering guide (in Russian) covering conformal UV math, procedural PBR canvas generation, pivot compensation, analytical 2-bone IK, and 4-phase combat animation principles.
* `scripts/` — Python procedural mesh generation scripts used for initial prototyping.
* `previews/` — High-resolution multi-angle studio render sheets.

## Quick Start (GitHub Pages / Local)

1. Unpack this archive into your GitHub repository folder.
2. Open `index.html` directly in any modern browser, or push to GitHub and enable **GitHub Pages** on the root directory.
3. Use the bottom animation bar to switch between **11 procedural animations** (including *Claw Smash*, *All-Out Combo Attack*, *Energy Shield*, *Heavy Walk*, *Combat Run*, and *Dance Groove*), or drag the **IK & Rig Sliders** on the right panel.
