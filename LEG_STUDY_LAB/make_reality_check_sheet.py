import os, shutil
from PIL import Image, ImageDraw, ImageFont

ART_DIR = r"C:\Users\blizz\.gemini\antigravity\brain\b3191c3c-f222-4e9c-90a8-ee8425eeff49"
LAB_DIR = r"I:\1_VSCODE\2026_3  GAMES\ROBOt2_5d\ROBO_FACTORY\LEG_STUDY_LAB"

user_scr_p = os.path.join(ART_DIR, ".user_uploaded", "media_1794180495639_73923a3d.jpg")
real_ref_p = os.path.join(LAB_DIR, "real_reference_perspective.png")
proc_match_p = os.path.join(LAB_DIR, "user_viewpoint_match.png")

shutil.copy2(real_ref_p, os.path.join(ART_DIR, "real_reference_perspective.png"))
shutil.copy2(proc_match_p, os.path.join(ART_DIR, "user_viewpoint_match.png"))

# Create 3-panel comparative image
img_user = Image.open(user_scr_p)
img_ref = Image.open(real_ref_p)
img_match = Image.open(proc_match_p)

W, H = 800, 900
canvas = Image.new("RGB", (W * 3 + 40, H + 100), (18, 22, 28))
draw = ImageDraw.Draw(canvas)

try:
    font = ImageFont.truetype("arialbd.ttf", 26)
    font_sub = ImageFont.truetype("arial.ttf", 16)
except:
    font = ImageFont.load_default()
    font_sub = ImageFont.load_default()

draw.text((20, 20), "BRUTAL REALITY CHECK: WHAT YOU SEE IN BLENDER VS THE ACTUAL TARGET", fill=(255, 255, 255), font=font)
draw.text((20, 55), "Left: User's Viewport | Center: The Procedural Model in Perspective | Right: The Real Reference Mech_gameready Leg", fill=(160, 180, 210), font=font_sub)

panels = [
    (img_user, "1. USER'S BLENDER VIEWPORT", "Flat trapezoid hulls, floating boxes/plates, crude blockout"),
    (img_match, "2. PROCEDURAL MODEL (3/4 Persp)", "Proves the disconnect: armor blocks are simple low-poly prisms"),
    (img_ref, "3. REAL TARGET REFERENCE LEG", "Isolated 53-part Mech_gameready CAD geometry")
]

for i, (im, title, sub) in enumerate(panels):
    x = 10 + i * (W + 10)
    y = 90
    draw.rectangle([x, y, x + W, y + H], fill=(26, 32, 42), outline=(60, 80, 110), width=2)
    draw.rectangle([x, y, x + W, y + 50], fill=(36, 44, 58))
    draw.text((x + 15, y + 10), title, fill=(255, 255, 255), font=font)
    draw.text((x + 15, y + 32), sub, fill=(140, 170, 210), font=font_sub)
    
    # Fit
    cw, ch = W - 4, H - 54
    aspect = im.width / im.height
    if aspect > cw / ch:
        nw = cw
        nh = int(nw / aspect)
    else:
        nh = ch
        nw = int(nh * aspect)
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(resized, (x + 2 + (cw - nw)//2, y + 52 + (ch - nh)//2))

out_sheet = os.path.join(ART_DIR, "BRUTAL_VIEWPORT_DISCONNECT_AUDIT.png")
canvas.save(out_sheet, quality=95)
print(f"Saved audit comparison: {out_sheet}")

