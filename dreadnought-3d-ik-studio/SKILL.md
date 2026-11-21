---
name: procedural-3d-mech-animator
description: Build procedural hard-surface 3D robots, mechs, and articulated rigs in Three.js with conformal topology UV mapping, in-memory CanvasTexture PBR materials, analytical 2-bone Inverse Kinematics (Zero-Drift Foot IK), and multi-phase full-body kinetic animations. Use when asked to create a 3D robot, mech, walker, procedural 3D character, IK rig, or physics-grounded combat/locomotion animations in WebGL or Three.js.
---
# Procedural 3D Mech Animator

Build production-grade, single-file or modular 3D hard-surface robots and mechs in Three.js with conformal UV mapping, procedural in-memory PBR textures, analytical 2-bone Inverse Kinematics (Zero-Drift Foot IK), and multi-phase full-body animations.

## When to Use

* Creating procedural 3D mechs, robots, walkers, or hard-surface vehicles in Three.js without external `.glb` assets.
* Implementing analytical 2-bone Inverse Kinematics (IK) so feet remain planted on the ground during squats, lunges, walks, dances, or combat strikes.
* Designing multi-phase kinetic combat or locomotion animations with anticipation, kinetic chain lag, impact shockwaves, and recovery.
* Generating topology-conforming UV coordinates and in-memory `THREE.CanvasTexture` PBR materials (weld seams, rivets, edge wear, bump maps, stencils) without external image dependencies.

## Step 1: Procedural Loft Geometry and Conformal UV Mapping

Avoid world-space planar UV projection on 3D characters or mechs, as world-space projection makes patterns look like flat wallpaper or a tracksuit stretched across joints. Always compute **conformal topology-aligned UV coordinates** directly inside the loft and tube builders:

* Parameterize `u` (`0.0` to `1.0`) continuously around the cross-sectional perimeter ring (`i / nPts`).
* Parameterize `v` (`0.0` to `1.0`) along the longitudinal loft slices from bottom chamfer to top chamfer (`r / (numRings - 1)`).
* Map end-cap triangles radially around `(0.5, 0.5)`.

```javascript
function buildLoftGeometry(slices, capBot = true, capTop = true) {
  const numRings = slices.length;
  const nPts = slices[0].length;
  const positions = [];
  const uvs = [];

  for (let r = 0; r < numRings - 1; r++) {
    const v0 = r / (numRings - 1);
    const v1 = (r + 1) / (numRings - 1);
    for (let i = 0; i < nPts; i++) {
      const u0 = i / nPts;
      const u1 = (i + 1) / nPts;
      const p00 = slices[r][i];
      const p10 = slices[r][(i + 1) % nPts];
      const p01 = slices[r + 1][i];
      const p11 = slices[r + 1][(i + 1) % nPts];

      positions.push(...p00, ...p10, ...p11);
      uvs.push(u0, v0, u1, v0, u1, v1);

      positions.push(...p00, ...p11, ...p01);
      uvs.push(u0, v0, u1, v1, u0, v1);
    }
  }
  // Add radial caps if capBot / capTop are true, then computeVertexNormals()
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geo.computeVertexNormals();
  return geo;
}
```

## Step 2: In-Memory Procedural PBR Textures via HTML5 Canvas

Never embed multi-megabyte Base64 strings that bloat HTML files or risk missing variable references. Generate Albedo, Bump, Hazard, Decal, and Shield textures in memory at startup using HTML5 2D Canvas and `THREE.CanvasTexture`:

* **Conformal Seam Alignment**: For an 8-sided chamfered block (`nPts = 8`), place vertical seam trenches and edge-wear highlights at `u = 0.0, 0.25, 0.50, 0.75`. Place horizontal chamfer seams, scalloped weld beads, and bolt rows near `v = 0.02..0.08` (bottom border) and `v = 0.92..0.98` (top border).
* **3D Bump Relief**: Fill the bump canvas with neutral `#808080` (`128`), draw deep seam trenches in `#181818`, raised weld beads in `#dcdcdc`, and bolt heads in `#f5f5f5` with `#1c1c1c` shadow rings. Set `bumpScale: 0.055` to `0.065` on `THREE.MeshStandardMaterial`.

## Step 3: Articulated Pivot-Compensation Hierarchy

When building meshes in global model coordinates, convert each body part into a local pivot group so rotations occur cleanly around the anatomical joint center `(px, py, pz)`:

```javascript
function createLocalPartGroup(name, pivotX, pivotY, pivotZ, parentGroup) {
  const joint = new THREE.Group();
  joint.name = name;
  joint.position.set(pivotX, pivotY, pivotZ);
  parentGroup.add(joint);

  const offsetGroup = new THREE.Group();
  offsetGroup.position.set(-pivotX, -pivotY, -pivotZ);
  joint.add(offsetGroup);
  return { joint, space: offsetGroup };
}
```

### Standard Mech Kinematic Tree

* `root` -> `pelvis` `[0, 0.00, 0]`
  * `torso` `[0, 0.10, 0]` (rotates relative to pelvis)
    * `sensorPod` `[0, 1.08, 0.42]` (counter-rotates to keep optics locked on target)
    * `hatchL` / `hatchR` `[±0.42, 1.44, -0.05]` -> `missilePodL` / `missilePodR`
    * `shoulderL` `[+0.98, 0.92, 0]` -> `armL` -> `elbowL` `[+1.26, 0.36, 0]` (Railgun assembly)
    * `shoulderR` `[-0.98, 0.92, 0]` -> `armR` -> `elbowR` `[-1.26, 0.36, 0]` -> `wristChuck` -> `claw1..3`
  * `legL` `[+0.54, -0.12, 0]` -> `kneeL` `[+0.62, -0.86, 0.12]` -> `ankleL` `[+0.66, -1.72, 0.02]`
  * `legR` `[-0.54, -0.12, 0]` -> `kneeR` `[-0.62, -0.86, 0.12]` -> `ankleR` `[-0.66, -1.72, 0.02]`

## Step 4: Analytical 2-Bone Leg IK Solver (Zero-Drift Foot Lock)

If pelvis height or rotation is animated using Forward Kinematics (FK) alone, the feet will sink through the floor or slide unnaturally. Always drive the legs with an analytical 2-bone Inverse Kinematics solver (`solveLegIK`) evaluated **every frame after setting pelvis transforms**:

1. **Rigid Bone Lock**: Keep `ankleJoint.position` fixed at the exact tip of the shin bone so the foot never detaches from the leg.
2. **World-to-Pelvis Target Transform**: Convert the desired world-space ankle position `targetWorldVec` into `pelvis.children[0]` local space using `worldToLocal()`.
3. **Reach Clamping**: Measure distance `D` from the hip pivot `[sx * 0.54, -0.12, 0]` to the local target. Clamp `D` to `maxReach = L1 + L2 - 0.003` so the leg extends smoothly without NaN errors when the pelvis stretches far away.
4. **Law of Cosines for Knee Bend**:
   * Compute interior knee angle: `cosB = clamp((L1*L1 + L2*L2 - D*D) / (2 * L1 * L2), -1, 1)`
   * Set knee X rotation: `kx = (Math.PI - Math.acos(cosB)) - REST_KNEE_OFFSET`
5. **Quaternion Hip Aiming**:
   * Rotate the unrotated shin vector by `kx` around X, add the thigh vector to get `_vHipToAnkleUnrot`, and align it with the local target direction `[dx, dy, dz]` via `_qAim.setFromUnitVectors(_vHipToAnkleUnrot.normalize(), _vTargetLocal.normalize())`.
6. **World-Space Foot Orientation**:
   * Compute the parent knee world quaternion `_qParentWorld`, build the desired world foot quaternion `_qDesiredFoot` from `(footPitch, footYaw, footRoll)`, and set `ankleJoint.quaternion.copy(_qParentWorld).invert().multiply(_qDesiredFoot)` so the sole stays flat on the floor regardless of hip/knee angles.

## Step 5: Principles of Full-Body Procedural Animation

Never animate a single limb in isolation (which looks robotic and weightless). Every animation must engage the full kinetic chain:

### 1. 4-Phase Combat Strike Pattern (e.g. Claw Smash & Combo Attack)

Break heavy melee or weapon animations into four distinct normalized phases over cycle `u in [0, 1]`:

* **Phase 1: Anticipation & Coil (`0.00 - 0.42`)**:
  * Step the lead foot forward along an arc (`stepLift = Math.sin(stepU * Math.PI) * 0.28`) and plant it wide.
  * Shift pelvis weight onto the rear anchor leg and coil hips + torso backward (`-70 deg` combined yaw).
  * Counter-rotate the head/sensor pod (`+85 deg`) so the eyes stay locked on the target.
  * Cock the striking shoulder and elbow high behind the back, swing the opposite arm across the chest as a counterweight, spin up the wrist chuck, and open the claw to 100%.
* **Phase 2: Explosive Lunge & Whip (`0.42 - 0.58`)**:
  * Keep both feet locked to the floor via `solveLegIK` while driving the pelvis forward (`+0.62m` Z) and down (`-0.27m` Y).
  * Sequence the kinetic chain with **whip lag**: hips snap forward first (`smoothstep(0.0, 0.85, u)`), torso follows, and the striking arm accelerates non-linearly (`Math.pow(smoothstep(0.08, 1.0, u), 1.35)`) along a wide outward circular arc (`Math.sin(armWhip * Math.PI)`).
* **Phase 3: Impact, Clamp & Hit-Stop (`0.58 - 0.72`)**:
  * Snap the claw shut (`clawVal = 0.05`) at the moment of impact.
  * Trigger procedural camera shake, radial shockwave rings, high-frequency structural shudder (`Math.sin(u * Math.PI * 10) * Math.exp(-u * 5)`), and synthesized impact audio.
* **Phase 4: Hydraulic Recovery (`0.72 - 1.00`)**:
  * Smoothly return the lead foot and pelvis back to neutral stance using `1.0 - smoothstep(0.0, 1.0, u)`.

### 2. Multi-Action Combo Sequencing (`all_out_attack`)

Chain multiple combat stages across a longer timeline (e.g. `10.0s` period):

* **Stage A (`0.00 - 0.24`)**: Heavy Claw Smash with forward lunge and spark burst.
* **Stage B (`0.24 - 0.50`)**: Torso snap-aim, twin Railgun recoil (`armL` kicks back along barrel axis while torso twists from recoil impulse), and high-velocity projectile bolt spawn.
* **Stage C (`0.50 - 0.78`)**: Brace stance, open roof missile hatches (`setHatchState(1)`), elevate launcher pods, and fire staggered salvo of arching ballistic missiles with smoke trails.
* **Stage D (`0.78 - 1.00`)**: Activate hexagonal plasma dome shield (`rig.shieldDome.visible = true`) with pulsing shockwaves while cooling down systems.

### 3. Locomotion & Dance Dynamics

* **Heavy Walk / Run**: Use opposite phase offsets (`phaseL = cycle * 2 * Math.PI`, `phaseR = phaseL + Math.PI`). Lift the swinging foot only when `Math.sin(phase) > 0`, shift pelvis lateral sway (`cos(phase)`) over the planted stance leg, and counter-swing the arms (`armL` moves with `legR`).
* **Dance Groove**: Lock both feet to the floor via `solveLegIK` while driving rhythmic figure-8 hip sway, double-time knee bounces (`Math.abs(Math.sin(beat * 2))`), alternating shoulder pops, and spinning claw flourishes.

## Verification Checklist

1. Run syntax validation on the generated script (`node -e "new Function(code)"`) to confirm zero syntax or undeclared-variable errors.
2. Verify that `solveLegIK('L', ...)` and `solveLegIK('R', ...)` are called at the end of `evaluateAnimation(t, dt)` after all pelvis position/rotation updates.
3. Include a top-level `window.onerror` diagnostic banner in the HTML so any runtime error is immediately visible on screen.
