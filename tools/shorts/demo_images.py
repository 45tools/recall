"""紹介ショート・note用の架空の教材画像を作る（実在の教材は使わない）。
python3 demo_images.py → demo/ に page1.jpg（ワーク1ページ）、c1〜c5.jpg（切り抜き）、remind.jpg（持ち物）
"""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo"); os.makedirs(OUT, exist_ok=True)
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
RED = (214, 40, 40); BLUE = (40, 70, 160); INK = (35, 35, 40)


def paper(w, h, seed=1):
    random.seed(seed)
    im = Image.new("RGB", (w, h), (250, 248, 242)); d = ImageDraw.Draw(im)
    for _ in range(4000):
        x, y = random.randrange(w), random.randrange(h); c = random.randint(236, 246)
        d.point((x, y), fill=(c, c - 1, c - 5))
    return im, d


def hand(d, xy, text, size=46, color=BLUE):
    d.text(xy, text, font=F(DJ, size), fill=color)


def cross(d, cx, cy, r=34):
    d.line((cx - r, cy - r, cx + r, cy + r), fill=RED, width=9); d.line((cx - r, cy + r, cx + r, cy - r), fill=RED, width=9)


def circle(d, cx, cy, r=40):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED, width=8)


def page1():
    W, H = 1200, 1600
    im, d = paper(W, H)
    d.rectangle((70, 70, W - 70, 190), outline=INK, width=4)
    d.text((100, 92), "MATH  Unit 3   Linear Equations", font=F(SANS_B, 52), fill=INK)
    d.text((W - 260, 205), "p. 24", font=F(SERIF, 40), fill=INK)
    probs = [("(1)", "x + 7 = 15", "x = 8", True), ("(2)", "3x = 21", "x = 7", True),
             ("(3)", "2x − 5 = 3x + 4", "x = 9", False, "x = −9"), ("(4)", "4(x − 2) = 2x + 6", "x = 1", False, "x = 7"),
             ("(5)", "x / 3 + 2 = 6", "x = 12", True), ("(6)", "5x + 3 = 2x − 9", "x = −4", True)]
    y = 300
    for i, (n, q, a, ok, *fix) in enumerate(probs):
        d.text((110, y), n, font=F(SERIF, 50), fill=INK); d.text((210, y), q, font=F(SERIF, 54), fill=INK)
        hand(d, (230, y + 90), a, 52)
        if ok: circle(d, 1040, y + 60, 46)
        else: cross(d, 1040, y + 60, 46)
        if not ok: d.text((760, y + 100), "→ " + fix[0], font=F(DJ, 44), fill=RED)
        d.line((100, y + 185, W - 100, y + 185), fill=(215, 210, 200), width=2)
        y += 205
    im = im.rotate(-0.6, resample=Image.BICUBIC, fillcolor=(60, 60, 60))
    bg = Image.new("RGB", (W + 80, H + 80), (92, 84, 74)); bg.paste(im, (40, 40))
    bg = bg.resize((W, int(H * W / (W + 80))))
    bg.filter(ImageFilter.SMOOTH).save(os.path.join(OUT, "page1.jpg"), quality=90)


def crop_card(name, lines, mark, seed):
    W, H = 900, 480
    im, d = paper(W, H, seed)
    y = 50
    for kind, txt in lines:
        if kind == "q": d.text((50, y), txt, font=F(SERIF, 50), fill=INK); y += 90
        elif kind == "a": hand(d, (80, y), txt, 48); y += 85
        elif kind == "r": d.text((80, y), txt, font=F(DJ, 44), fill=RED); y += 80
    cross(d, W - 90, 90, 44) if mark == "x" else None
    im.save(os.path.join(OUT, name), quality=88)


def cards():
    crop_card("c1.jpg", [("q", "(3)  2x − 5 = 3x + 4"), ("a", "x = 9"), ("r", "→  x = −9")], "x", 2)
    crop_card("c2.jpg", [("q", "I (go) to the zoo"), ("q", "    last Sunday."), ("a", "goed"), ("r", "→ went")], "x", 3)
    crop_card("c3.jpg", [("q", "√12 × √3 = ?"), ("a", "√15"), ("r", "→ 6")], "x", 4)
    crop_card("c4.jpg", [("q", "H₂O  :  ?"), ("a", "oxygen"), ("r", "→ water")], "x", 5)
    crop_card("c5.jpg", [("q", "Area of a circle"), ("q", "  r = 3 cm"), ("a", "6π"), ("r", "→ 9π cm²")], "x", 6)


def remind():
    W, H = 900, 900
    im = Image.new("RGB", (W, H), (226, 236, 246)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 640, 840, 860), 30, fill=(205, 190, 165))
    # 体操服（Tシャツ）
    d.polygon([(250, 220), (360, 170), (540, 170), (650, 220), (760, 340), (680, 400), (620, 350), (620, 700), (280, 700), (280, 350), (220, 400), (140, 340)], fill=(255, 255, 255), outline=(170, 180, 195))
    d.ellipse((395, 150, 505, 230), fill=(226, 236, 246), outline=(170, 180, 195), width=3)
    d.rectangle((280, 600, 620, 640), fill=(46, 110, 220))
    d.rounded_rectangle((390, 380, 510, 470), 12, outline=(46, 110, 220), width=5)
    # 上ばき
    for x in (100, 690):
        d.rounded_rectangle((x, 720, x + 130, 800), 40, fill=(255, 255, 255), outline=(170, 180, 195), width=3)
        d.rectangle((x + 10, 760, x + 120, 776), fill=(220, 60, 60))
    im.save(os.path.join(OUT, "remind.jpg"), quality=88)


if __name__ == "__main__":
    page1(); cards(); remind(); print("ok", os.listdir(OUT))
