import os
from PIL import Image, ImageDraw, ImageFont

ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

ref_img_path = os.path.join(ART_DIR, ".user_uploaded", "media_1794170243573_e02bfbb9.jpg")
side_render_path = os.path.join(ART_DIR, "master_leg_v2_1_side_ortho.png")
hero_render_path = os.path.join(ART_DIR, "master_leg_v2_2_hero_34.png")
knee_render_path = os.path.join(ART_DIR, "master_leg_v2_3_knee_closeup.png")
wire_render_path = os.path.join(ART_DIR, "master_leg_v2_4_wire_ortho.png")

img_ref = Image.open(ref_img_path).convert('RGB')
img_side = Image.open(side_render_path).convert('RGB')
img_hero = Image.open(hero_render_path).convert('RGB')
img_knee = Image.open(knee_render_path).convert('RGB')
img_wire = Image.open(wire_render_path).convert('RGB')

# Standard tile height
target_h = 1000

def resize_to_h(img, h):
    ratio = h / img.height
    w = int(img.width * ratio)
    return img.resize((w, h), Image.Resampling.LANCZOS)

t_ref = resize_to_h(img_ref, target_h)
t_side = resize_to_h(img_side, target_h)
t_hero = resize_to_h(img_hero, target_h)
t_knee = resize_to_h(img_knee, target_h)
t_wire = resize_to_h(img_wire, target_h)

# 2-Row layout:
# Top row: [User Reference] | [Procedural Master Leg V2 Side Profile]
# Bottom row: [Hero 3/4 View] | [Knee Knuckle Broken Lines Closeup] | [Wireframe Topology]

total_w = t_ref.width + t_side.width
top_row = Image.new('RGB', (total_w, target_h))
top_row.paste(t_ref, (0, 0))
top_row.paste(t_side, (t_ref.width, 0))

# Bottom row with 3 tiles scaled to fit total_w
bot_h = 750
b_hero = resize_to_h(t_hero, bot_h)
b_knee = resize_to_h(t_knee, bot_h)
b_wire = resize_to_h(t_wire, bot_h)

bot_w_actual = b_hero.width + b_knee.width + b_wire.width
# Re-scale bot row to match top_row width
scale_bot = total_w / bot_w_actual
b_hero = b_hero.resize((int(b_hero.width * scale_bot), int(bot_h * scale_bot)), Image.Resampling.LANCZOS)
b_knee = b_knee.resize((int(b_knee.width * scale_bot), int(bot_h * scale_bot)), Image.Resampling.LANCZOS)
b_wire = b_wire.resize((int(b_wire.width * scale_bot), int(bot_h * scale_bot)), Image.Resampling.LANCZOS)

final_bot_h = b_hero.height
header_h = 110
final_canvas_h = header_h + target_h + 40 + final_bot_h + 40
sheet = Image.new('RGB', (total_w, final_canvas_h), color=(14, 18, 24))
draw = ImageDraw.Draw(sheet)

# Header
draw.rectangle([(0, 0), (total_w, header_h)], fill=(22, 28, 38))
try:
    font_title = ImageFont.truetype("arialbd.ttf", 34)
    font_sub = ImageFont.truetype("arial.ttf", 20)
    font_tag = ImageFont.truetype("arialbd.ttf", 22)
except Exception:
    font_title = font_sub = font_tag = ImageFont.load_default()

draw.text((30, 20), "ADVANCED HARD-SURFACE MECH LEG STUDY: MASTER-GRADE GENERATION V2", fill=(255, 215, 0), font=font_title)
draw.text((30, 68), "Broken-line double knuckle joint, multi-tier terraced thigh armor, twin aero deflector fins & 4-claw arched foot", fill=(180, 200, 220), font=font_sub)

# Paste Top Row
sheet.paste(top_row, (0, header_h + 10))

# Tags for top row
draw.rectangle([(20, header_h + 25), (420, header_h + 65)], fill=(180, 40, 40))
draw.text((35, header_h + 30), "[REFERENCE] Target Mech Leg", fill=(255, 255, 255), font=font_tag)

draw.rectangle([(t_ref.width + 20, header_h + 25), (t_ref.width + 620, header_h + 65)], fill=(30, 140, 60))
draw.text((t_ref.width + 35, header_h + 30), "[GENERATION V2] Procedural Hard-Surface", fill=(255, 255, 255), font=font_tag)

# Paste Bottom Row
y_bot = header_h + 10 + target_h + 25
sheet.paste(b_hero, (0, y_bot))
sheet.paste(b_knee, (b_hero.width, y_bot))
sheet.paste(b_wire, (b_hero.width + b_knee.width, y_bot))

# Tags for bottom row
draw.rectangle([(20, y_bot + 15), (320, y_bot + 55)], fill=(35, 75, 140))
draw.text((35, y_bot + 22), "Hero 3/4 Perspective", fill=(255, 255, 255), font=font_tag)

draw.rectangle([(b_hero.width + 20, y_bot + 15), (b_hero.width + 480, y_bot + 55)], fill=(120, 45, 140))
draw.text((b_hero.width + 35, y_bot + 22), "Stepped Knuckle (Broken Lines)", fill=(255, 255, 255), font=font_tag)

draw.rectangle([(b_hero.width + b_knee.width + 20, y_bot + 15), (b_hero.width + b_knee.width + 380, y_bot + 55)], fill=(40, 110, 130))
draw.text((b_hero.width + b_knee.width + 35, y_bot + 22), "Wireframe Edge Topology", fill=(255, 255, 255), font=font_tag)

out_sheet_p1 = os.path.join(OUT_DIR, "master_hardsurface_comparison_sheet_v2.png")
out_sheet_p2 = os.path.join(ART_DIR, "master_hardsurface_comparison_sheet_v2.png")

sheet.save(out_sheet_p1, quality=95)
sheet.save(out_sheet_p2, quality=95)
print(f"Comparison sheet saved to {out_sheet_p1} and {out_sheet_p2}")

