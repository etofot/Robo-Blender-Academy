import os
from PIL import Image, ImageDraw, ImageFont

ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

p_ref = os.path.join(ART_DIR, ".user_uploaded", "media_1794175549536_cfddcffb.jpg")
p_can = os.path.join(ART_DIR, "step25_step26_finned_canisters_audit.png")
p_damp = os.path.join(ART_DIR, "step28_travel_stop_damper_audit.png")
p_hero = os.path.join(ART_DIR, "steps_25_32_subsystems_hero_audit.png")

img_ref = Image.open(p_ref).convert('RGB')
img_can = Image.open(p_can).convert('RGB')
img_damp = Image.open(p_damp).convert('RGB')
img_hero = Image.open(p_hero).convert('RGB')

target_h = 900
def resize_to_h(im, h):
    ratio = h / im.height
    return im.resize((int(im.width * ratio), h), Image.Resampling.LANCZOS)

t_ref = resize_to_h(img_ref, target_h)
t_can = resize_to_h(img_can, target_h)
t_damp = resize_to_h(img_damp, target_h)
t_hero = resize_to_h(img_hero, target_h)

total_w = t_ref.width + t_can.width + t_damp.width + t_hero.width
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

draw.text((30, 20), "50-STEP LEG EVOLUTION: PHASE IV AUDIT (STEPS 25 - 32)", fill=(255, 215, 0), font=f_title)
draw.text((30, 68), "H-Bracket Finned Canisters, Disc Spring Travel-Stop Damper, Sensor Junction Box & Debris Shield", fill=(180, 200, 220), font=f_sub)

# Paste Images
cur_x = 0
sheet.paste(t_ref, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 320, header_h + 60)], fill=(180, 40, 40))
draw.text((cur_x + 35, header_h + 26), "Photo 4 Master Ref", fill=(255, 255, 255), font=f_tag)

cur_x += t_ref.width
sheet.paste(t_can, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 480, header_h + 60)], fill=(200, 80, 20))
draw.text((cur_x + 35, header_h + 26), "Steps 25-26: Finned H-Block", fill=(255, 255, 255), font=f_tag)

cur_x += t_can.width
sheet.paste(t_damp, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 480, header_h + 60)], fill=(35, 120, 180))
draw.text((cur_x + 35, header_h + 26), "Step 28: Travel-Stop Damper", fill=(255, 255, 255), font=f_tag)

cur_x += t_damp.width
sheet.paste(t_hero, (cur_x, header_h))
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 480, header_h + 60)], fill=(40, 140, 60))
draw.text((cur_x + 35, header_h + 26), "Steps 25-32: Subsystems Hero", fill=(255, 255, 255), font=f_tag)

out_p1 = os.path.join(OUT_DIR, "phase4_audit_contact_sheet.png")
out_p2 = os.path.join(ART_DIR, "phase4_audit_contact_sheet.png")
sheet.save(out_p1, quality=95)
sheet.save(out_p2, quality=95)
print(f"Saved Phase 4 Audit Sheet: {out_p1} and {out_p2}")

