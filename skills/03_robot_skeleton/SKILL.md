---
name: robot_skeleton
description: "Процедурный скелет и риг робота/механических узлов / Create or generate robot skeleton, mechanical armature, turret rotation constraints. Trigger when user asks to create robot rig, mechanical armature, turret pivot constraints, or mech skeleton."
depends_on: [core_geometry_rules]
---

# Robot Skeleton Skill

## Purpose
Generates rigid mechanical armatures and bone constraints for robots, mechs, turrets, and mechanical vehicles.

## Rules

### Rule 1: Mechanical Node Naming
Use functional names (`turret_base`, `turret_barrel`, `hinge_shoulder.L`, `piston_leg.L`) rather than organic anatomical labels.

### Rule 2: Empty Pivot Constraints for Rotating Parts
For turrets or rotating barrels: create an `Empty` pivot object at the center of rotation, parent rotating parts to the Empty, and animate the Empty's rotation axis.

### Rule 3: Rigid Binary Weights (100% / 0%)
Mechanical parts do not deform smoothly. Assign binary vertex weights (1.0 or 0.0) without smooth weight painting transitions.

### Rule 4: Bone Limits (Limit Rotation)
Apply `LIMIT_ROTATION` bone constraints to prevent mechanical parts from rotating beyond realistic physical bounds.
