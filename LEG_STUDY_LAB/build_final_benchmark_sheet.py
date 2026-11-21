import os
import shutil
from PIL import Image, ImageDraw, ImageFont

ARTIFACT_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
LAB_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

# Copy primary renders to artifact dir
renders = [
    "step50_master_leg_side_ortho.png",
    "step50_master_leg_hero_perspective.png",
    "step50_master_knee_gear_closeup.png",
    "step50_master_leg_wireframe.png"
]

for r in renders:
    src = os.path.join(LAB_DIR, r)
    dst = os.path.join(ARTIFACT_DIR, r)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied {r} to artifact dir.")

# Create Grand Master Benchmark 6-Panel Poster
# Grid: 3 columns x 2 rows
# Row 1:
#   Col 1: Photo 4 (Target Reference)
#   Col 2: Our Final Ortho Side Profile (Step 50)
#   Col 3: Our Final Wireframe Inspection (Step 50)
# Row 2:
#   Col 1: Initial Naive "1-2%" Model (User Photo 2)
#   Col 2: Our Final Hero 3/4 Perspective (Step 50)
#   Col 3: Macro Engineering Closeups (Knee Sunburst + Foot Gimbal)

ref_img_path = os.path.join(ARTIFACT_DIR, ".user_uploaded", "media_1794175549536_cfddcffb.jpg")
old_img_path = os.path.join(ARTIFACT_DIR, ".user_uploaded", "media_1794175472781_3f3e5d12.jpg")

side_img_path = os.path.join(LAB_DIR, "step50_master_leg_side_ortho.png")
wire_img_path = os.path.join(LAB_DIR, "step50_master_leg_wireframe.png")
hero_img_path = os.path.join(LAB_DIR, "step50_master_leg_hero_perspective.png")
knee_img_path = os.path.join(LAB_DIR, "step50_master_knee_gear_closeup.png")
foot_img_path = os.path.join(LAB_DIR, "step41_step46_foot_macro_closeup.png")

# Target panel dimensions: 800 x 950
PANEL_W = 800
PANEL_H = 950
HEADER_H = 120
FOOTER_H = 80
TOTAL_W = PANEL_W * 3 + 40
TOTAL_H = HEADER_H + PANEL_H * 2 + 30 + FOOTER_H

canvas = Image.new("RGB", (TOTAL_W, TOTAL_H), (15, 18, 24))
draw = ImageDraw.Draw(canvas)

# Fonts
try:
    font_title = ImageFont.truetype("arialbd.ttf", 36)
    font_subtitle = ImageFont.truetype("arial.ttf", 20)
    font_panel = ImageFont.truetype("arialbd.ttf", 24)
    font_subpanel = ImageFont.truetype("arial.ttf", 16)
except:
    font_title = ImageFont.load_default()
    font_subtitle = ImageFont.load_default()
    font_panel = ImageFont.load_default()
    font_subpanel = ImageFont.load_default()

# Header
draw.text((30, 25), "MECH LEG HARD-SURFACE SYNTHESIS: 50-STEP MASTER AUDIT", fill=(255, 255, 255), font=font_title)
draw.text((30, 75), "Comparison of Target Master Reference vs. Initial Naive Blockout vs. Final Procedural Architecture", fill=(160, 180, 205), font=font_subtitle)

# Helper to place panel
def place_panel(img, col, row, title, subtitle, border_color=(60, 80, 110)):
    x = 15 + col * (PANEL_W + 10)
    y = HEADER_H + row * (PANEL_H + 15)
    
    # Draw panel container
    draw.rectangle([x, y, x + PANEL_W, y + PANEL_H], fill=(22, 27, 36), outline=border_color, width=2)
    draw.rectangle([x, y, x + PANEL_W, y + 60], fill=(30, 38, 52))
    draw.text((x + 15, y + 10), title, fill=(255, 255, 255), font=font_panel)
    draw.text((x + 15, y + 36), subtitle, fill=(140, 170, 210), font=font_subpanel)
    
    # Resize & fit image in content area
    content_y = y + 62
    content_h = PANEL_H - 64
    content_w = PANEL_W - 4
    
    aspect = img.width / img.height
    target_aspect = content_w / content_h
    
    if aspect > target_aspect:
        new_w = content_w
        new_h = int(new_w / aspect)
    else:
        new_h = content_h
        new_w = int(new_h * aspect)
        
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    offset_x = x + 2 + (content_w - new_w) // 2
    offset_y = content_y + (content_h - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))

# Load Images
img_ref = Image.open(ref_img_path)
img_old = Image.open(old_img_path)
img_side = Image.open(side_img_path)
img_wire = Image.open(wire_img_path)
img_hero = Image.open(hero_img_path)

# Build Split Macro Image for Col 3 Row 2
img_knee = Image.open(knee_img_path)
img_foot = Image.open(foot_img_path)
macro_split = Image.new("RGB", (PANEL_W, PANEL_H - 64), (18, 22, 30))
# Top half: Knee
knee_resized = img_knee.resize((PANEL_W, (PANEL_H - 64) // 2), Image.Resampling.LANCZOS)
macro_split.paste(knee_resized, (0, 0))
# Bottom half: Foot
foot_resized = img_foot.resize((PANEL_W, (PANEL_H - 64) // 2), Image.Resampling.LANCZOS)
macro_split.paste(foot_resized, (0, (PANEL_H - 64) // 2))

# Row 1
place_panel(img_ref, 0, 0, "1. MASTER REFERENCE (Photo 4)", "Industrial CAD/Hard-surface reference model (Mech_gameready)", border_color=(40, 160, 220))
place_panel(img_side, 1, 0, "2. FINAL PROCEDURAL ORTHO (Step 50)", "Exact 4-tier assembly: Sunburst Hubs, Hydraulics, Subsystems, Monocoque", border_color=(60, 220, 120))
place_panel(img_wire, 2, 0, "3. TOPOLOGY & MESH AUDIT", "Clean manifold quad loops, non-destructive bevels, zero black voids", border_color=(120, 200, 255))

# Row 2
place_panel(img_old, 0, 1, "4. INITIAL NAIVE ATTEMPT (Photo 2)", "Critique: 1-2% fidelity, flat extruded soap-bar, hollow coffin, primitive oval", border_color=(200, 60, 60))
place_panel(img_hero, 1, 1, "5. FINAL HERO 3/4 PERSPECTIVE (Step 50)", "Believable scale, load-bearing architecture, structural PCD fasteners", border_color=(60, 220, 120))
place_panel(macro_split, 2, 1, "6. MACRO ENGINEERING SUBSYSTEMS", "Top: 24-tooth Sunburst Knee Hub | Bottom: 4-toe arched suspension claw", border_color=(240, 180, 50))

# Footer
footer_y = TOTAL_H - 60
draw.text((30, footer_y), "PIPELINE COMPLETED: Steps 01 to 50 across 7 Functional Phases | Architecture Saved: MASTER_LEG_50_STEPS_COMPLETE.blend", fill=(180, 200, 220), font=font_subpanel)
draw.text((30, footer_y + 24), "Reusable Skills Exported: mech-hardsurface-components (Sunburst Gears, PCD Bolt Arrays, Cable Chutes, Finned Blocks, Articulated Foot)", fill=(100, 210, 140), font=font_subpanel)

final_contact_sheet_path = os.path.join(ARTIFACT_DIR, "MASTER_LEG_FINAL_BENCHMARK_50.png")
canvas.save(final_contact_sheet_path, quality=95)
print(f"Master benchmark contact sheet saved to {final_contact_sheet_path}")

