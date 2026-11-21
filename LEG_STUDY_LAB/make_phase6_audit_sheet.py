import os
from PIL import Image, ImageDraw, ImageFont

ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

p_old_top = os.path.join(ART_DIR, ".user_uploaded", "media_1794175454797_b161df46.jpg")
p_new_top = os.path.join(ART_DIR, "step41_step46_foot_top_ortho.png")
p_macro = os.path.join(ART_DIR, "step41_step46_foot_macro_closeup.png")
p_full = os.path.join(ART_DIR, "step41_step46_full_leg_pbr_side.png")

img_old = Image.open(p_old_top).convert('RGB')
img_new = Image.open(p_new_top).convert('RGB')
img_macro = Image.open(p_macro).convert('RGB')
img_full = Image.open(p_full).convert('RGB')

target_h = 920
def resize_to_h(im, h):
    ratio = h / im.height
    return im.resize((int(im.width * ratio), h), Image.Resampling.LANCZOS)

t_old = resize_to_h(img_old, target_h)
t_new = resize_to_h(img_new, target_h)
t_macro = resize_to_h(img_macro, target_h)
t_full = resize_to_h(img_full, target_h)

total_w = t_old.width + t_new.width + t_macro.width + t_full.width
header_h = 110
canvas_h = header_h + target_h + 30

sheet = Image.new('RGB', (total_w, canvas_h), color=(14, 18, 24))
draw = ImageDraw.Draw(sheet)

# Header
draw.rectangle([(0, 0), (total_w, header_h)], fill=(22, 28, 38))
try:
    f_title = ImageFont.truetype("arialbd.ttf", 32)
    f_sub = ImageFont.truetype("arial.ttf", 20)
    f_tag = ImageFont.truetype("arialbd.ttf", 22)
except Exception:
    f_title = f_sub = f_tag = ImageFont.load_default()

draw.text((30, 20), "50-STEP LEG EVOLUTION: PHASE VI AUDIT (STEPS 41 - 46)", fill=(255, 215, 0), font=f_title)
draw.text((30, 68), "Articulated Foot Gimbal, Splayed Outrigger Claws with Hydraulic Struts, Arched Bridge Clearance & Tread Pads", fill=(180, 200, 220), font=f_sub)

# Paste Images
cur_x = 0
sheet.paste(t_old, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 360, header_h + 60)], fill=(180, 40, 40))
draw.text((cur_x + 35, header_h + 26), "Photo 1: Old Crude Foot", fill=(255, 255, 255), font=f_tag)

cur_x += t_old.width
sheet.paste(t_new, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 480, header_h + 60)], fill=(30, 140, 60))
draw.text((cur_x + 35, header_h + 26), "Steps 41-46: New Articulated Foot", fill=(255, 255, 255), font=f_tag)

cur_x += t_new.width
sheet.paste(t_macro, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 440, header_h + 60)], fill=(35, 120, 180))
draw.text((cur_x + 35, header_h + 26), "Macro: Gimbal & Struts", fill=(255, 255, 255), font=f_tag)

cur_x += t_macro.width
sheet.paste(t_full, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 460, header_h + 60)], fill=(160, 100, 30))
draw.text((cur_x + 35, header_h + 26), "Full Leg: Hip to Ground", fill=(255, 255, 255), font=f_tag)

out_p1 = os.path.join(OUT_DIR, "phase6_audit_contact_sheet.png")
out_p2 = os.path.join(ART_DIR, "phase6_audit_contact_sheet.png")
sheet.save(out_p1, quality=95)
sheet.save(out_p2, quality=95)
print(f"Saved Phase 6 Audit Sheet: {out_p1} and {out_p2}")

