---
name: robot_animation
description: "Анимация робота, механизмов, турелей, пулемета / Animate robot, turret rotation, mechanical mechanisms, linear keyframing. Trigger on requests to animate robot parts, turret spinning, machine guns, or mechanical loops."
depends_on: [robot_skeleton]
---

# Robot Animation Skill

## Purpose
Controls mechanical animation, turret rotations, piston movements, and cyclic looping keyframe curves.

## Rules

### Rule 1: Empty-Pivot Turret Animation Pattern
When asked to animate turrets/barrels: match target object by pattern (`*turret*`/`*barrel*`), parent geometry to an Empty pivot object, and keyframe `rotation_euler.z` on the Empty.

### Rule 2: Linear Interpolation for Mechanical Motion
Always set keyframe interpolation to `'LINEAR'` (`kp.interpolation = 'LINEAR'`) for mechanical parts to avoid unwanted Bezier easing / springiness.

### Rule 3: Cyclic Looping via F-Curve Modifier
Use F-Curve Cycles modifiers (`fc.modifiers.new('CYCLES')`) instead of duplicating keyframe points to create endless rotation loops.
