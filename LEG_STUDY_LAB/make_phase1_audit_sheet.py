import os
from PIL import Image, ImageDraw, ImageFont

ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
OUT_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

p_ref = os.path.join(ART_DIR, ".user_uploaded", "media_1794175549536_cfddcffb.jpg")
p_idmap = os.path.join(ART_DIR, "step03_layer_color_coded_id_map.png")
p_deck = os.path.join(ART_DIR, "step04_step05_pelvis_deck_audit.png")

img_ref = Image.open(p_ref).convert('RGB')
img_idmap = Image.open(p_idmap).convert('RGB')
img_deck = Image.open(p_deck).convert('RGB')

target_h = 1000
def resize_to_h(im, h):
    ratio = h / im.height
    return im.resize((int(im.width * ratio), h), Image.Resampling.LANCZOS)

t_ref = resize_to_h(img_ref, target_h)
t_idmap = resize_to_h(img_idmap, target_h)
t_deck = resize_to_h(img_deck, target_h)

total_w = t_ref.width + t_idmap.width + t_deck.width
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

draw.text((30, 20), "50-STEP LEG EVOLUTION: PHASE I AUDIT (STEPS 01 - 05)", fill=(255, 215, 0), font=f_title)
draw.text((30, 68), "DoF Extraction, 4-Layer Decomposition (53 Master Parts), and Procedural Cantilever Pelvis Deck", fill=(180, 200, 220), font=f_sub)

# Paste Images
sheet.paste(t_ref, (0, header_h))
sheet.paste(t_idmap, (t_ref.width, header_h))
sheet.paste(t_deck, (t_ref.width + t_idmap.width, header_h))

# Badges
draw.rectangle([(20, header_h + 20), (320, header_h + 60)], fill=(180, 40, 40))
draw.text((35, header_h + 26), "Photo 4 Master Ref", fill=(255, 255, 255), font=f_tag)

draw.rectangle([(t_ref.width + 20, header_h + 20), (t_ref.width + 420, header_h + 60)], fill=(30, 140, 180))
draw.text((t_ref.width + 35, header_h + 26), "Step 03: 4-Layer ID Map", fill=(255, 255, 255), font=f_tag)

draw.rectangle([(t_ref.width + t_idmap.width + 20, header_h + 20), (t_ref.width + t_idmap.width + 510, header_h + 60)], fill=(40, 140, 60))
draw.text((t_ref.width + t_idmap.width + 35, header_h + 26), "Step 04-05: Pelvis Deck (Audit)", fill=(255, 255, 255), font=f_tag)

out_p1 = os.path.join(OUT_DIR, "phase1_audit_contact_sheet.png")
out_p2 = os.path.join(ART_DIR, "phase1_audit_contact_sheet.png")
sheet.save(out_p1, quality=95)
sheet.save(out_p2, quality=95)
print(f"Saved Phase 1 Audit Sheet: {out_p1} and {out_p2}")

