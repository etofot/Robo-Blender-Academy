import os
from PIL import Image, ImageDraw, ImageFont

ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

p_ref = os.path.join(ART_DIR, ".user_uploaded", "media_1794175549536_cfddcffb.jpg")
p_chute = os.path.join(ART_DIR, "step06_step08_cable_chute_audit.png")
p_knee = os.path.join(ART_DIR, "step09_step10_knee_sunburst_audit.png")
p_full = os.path.join(ART_DIR, "steps_01_12_full_skeletal_assembly.png")

img_ref = Image.open(p_ref).convert('RGB')
img_chute = Image.open(p_chute).convert('RGB')
img_knee = Image.open(p_knee).convert('RGB')
img_full = Image.open(p_full).convert('RGB')

target_h = 900
def resize_to_h(im, h):
    ratio = h / im.height
    return im.resize((int(im.width * ratio), h), Image.Resampling.LANCZOS)

t_ref = resize_to_h(img_ref, target_h)
t_chute = resize_to_h(img_chute, target_h)
t_knee = resize_to_h(img_knee, target_h)
t_full = resize_to_h(img_full, target_h)

total_w = t_ref.width + t_chute.width + t_knee.width + t_full.width
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

draw.text((30, 20), "50-STEP LEG EVOLUTION: PHASE II AUDIT (STEPS 06 - 12)", fill=(255, 215, 0), font=f_title)
draw.text((30, 68), "Armored Cable Chute, 24-Tooth Knee Sunburst Gear Hub, Ankle Hub & Asymmetric Dogbone Linkage", fill=(180, 200, 220), font=f_sub)

# Paste Images
cur_x = 0
sheet.paste(t_ref, (cur_x, header_h))
# Badge 1
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 320, header_h + 60)], fill=(180, 40, 40))
draw.text((cur_x + 35, header_h + 26), "Photo 4 Master Ref", fill=(255, 255, 255), font=f_tag)

cur_x += t_ref.width
sheet.paste(t_chute, (cur_x, header_h))
# Badge 2
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 480, header_h + 60)], fill=(35, 120, 180))
draw.text((cur_x + 35, header_h + 26), "Steps 06-08: Armored Chute", fill=(255, 255, 255), font=f_tag)

cur_x += t_chute.width
sheet.paste(t_knee, (cur_x, header_h))
# Badge 3
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 490, header_h + 60)], fill=(180, 140, 30))
draw.text((cur_x + 35, header_h + 26), "Steps 09-10: Sunburst Hub", fill=(255, 255, 255), font=f_tag)

cur_x += t_knee.width
sheet.paste(t_full, (cur_x, header_h))
# Badge 4
draw.rectangle([(cur_x + 20, header_h + 20), (cur_x + 460, header_h + 60)], fill=(40, 140, 60))
draw.text((cur_x + 35, header_h + 26), "Steps 01-12: Skeletal Frame", fill=(255, 255, 255), font=f_tag)

out_p1 = os.path.join(OUT_DIR, "phase2_audit_contact_sheet.png")
out_p2 = os.path.join(ART_DIR, "phase2_audit_contact_sheet.png")
sheet.save(out_p1, quality=95)
sheet.save(out_p2, quality=95)
print(f"Saved Phase 2 Audit Sheet: {out_p1} and {out_p2}")

