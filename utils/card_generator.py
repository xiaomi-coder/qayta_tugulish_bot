"""
QAYTA TUG'ILISH — Ovqat Ratsion Kartochka Generatori
Pillow bilan chiroyli PNG kartochkalar yasaydi.
"""
from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging

logger = logging.getLogger(__name__)

# ── Font yuklovchi ────────────────────────────────────────
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    suffix_bold = "-Bold"
    suffix_reg  = ""
    candidates = [
        # Ubuntu / Debian
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix_bold if bold else suffix_reg}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/ubuntu/Ubuntu-{'B' if bold else 'R'}.ttf",
        f"/usr/share/fonts/truetype/freefont/FreeSans{'Bold' if bold else ''}.ttf",
        # macOS
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    logger.warning(f"Font topilmadi (size={size}, bold={bold}), default ishlatilmoqda")
    return ImageFont.load_default()


# ── Matnni qatorlarga bo'lish ─────────────────────────────
def _wrap(text: str, font, max_w: int) -> list:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        try:
            length = font.getlength(test)
        except AttributeError:
            length = len(test) * (font.size if hasattr(font, "size") else 10)
        if length <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


# ── Har bir ovqat vaqtiga mos rang ──────────────────────────
ACCENTS = [
    (255, 140,  0),   # Nonushta    — oltin
    ( 46, 204, 113),  # Tushlik     — yashil
    ( 52, 152, 219),  # Oraliq      — ko'k
    (155,  89, 182),  # Kechki      — binafsha
    ( 26, 188, 156),  # Yotishdan ol— moviy-yashil
]

W   = 900     # karta kengligi
PAD = 55      # chetdan masofa


# ── Asosiy kartochka yaratuvchi ───────────────────────────
def create_meal_card(meal: dict, idx: int, total: int, category: str) -> bytes:
    """
    Bitta ovqat uchun PNG kartochka.
    Qaytaradi: bytes (PNG)
    """
    accent = ACCENTS[idx % len(ACCENTS)]

    # ── Balandlikni hisoblash ──
    f_body = _font(42)
    foods  = meal.get("foods", [])
    note   = meal.get("note", "")
    food_lines  = sum(len(_wrap(f, f_body, W - PAD * 2 - 55)) for f in foods)
    f_note_font = _font(36)
    note_lines  = len(_wrap(note, f_note_font, W - PAD * 2 - 30)) if note else 0

    H = (
        240                          # sarlavha bloqi
        + food_lines * 64            # har bir qator
        + (note_lines * 44 + 90 if note else 0)  # izoh
        + 250                        # makro
        + 80                         # footer
    )
    H = max(H, 920)

    # ── Rasm va chizish ──
    img  = Image.new("RGB", (W, H), (12, 12, 25))
    draw = ImageDraw.Draw(img)

    # Gradient fon
    for y in range(H):
        t = y / H
        draw.line(
            [(0, y), (W, y)],
            fill=(int(12 + 10 * t), int(12 + 10 * t), int(25 + 20 * t))
        )

    # ── Ustki aktsent chizig'i ──
    draw.rectangle([0, 0, W, 14], fill=accent)

    # ── Kategoriya chipi ──
    f_chip = _font(34)
    try:
        cw = int(f_chip.getlength(category)) + 44
    except AttributeError:
        cw = len(category) * 20 + 44
    draw.rounded_rectangle([PAD, 28, PAD + cw, 78], radius=18, fill=accent)
    draw.text((PAD + cw // 2, 53), category, fill=(0, 0, 0), font=f_chip, anchor="mm")

    # ── Ovqat nomi ──
    f_title = _font(66, bold=True)
    draw.text((PAD, 92), meal["name"], fill=(255, 255, 255), font=f_title)

    # ── Vaqt ──
    f_time = _font(40)
    draw.text((PAD, 172), meal["time"], fill=accent, font=f_time)

    # ── Separator ──
    y = 232
    draw.rectangle([PAD, y, W - PAD, y + 2], fill=(*accent, 70))
    y += 24

    # ── "MAHSULOTLAR" sarlavhasi ──
    f_lbl = _font(33)
    draw.text((PAD, y), "MAHSULOTLAR:", fill=(130, 130, 165), font=f_lbl)
    y += 50

    # ── Ovqat qatorlari ──
    for food in foods:
        wraps = _wrap(food, f_body, W - PAD * 2 - 55)
        for li, line in enumerate(wraps):
            if li == 0:
                # Bullet doira
                draw.ellipse([PAD, y + 15, PAD + 18, y + 33], fill=accent)
                draw.text((PAD + 32, y), line, fill=(225, 225, 238), font=f_body)
            else:
                draw.text((PAD + 32, y), line, fill=(225, 225, 238), font=f_body)
            y += 64

    # ── Izoh (note) ──
    if note:
        y += 14
        note_wraps = _wrap(note, f_note_font, W - PAD * 2 - 40)
        box_h = len(note_wraps) * 44 + 28
        draw.rounded_rectangle([PAD, y, W - PAD, y + box_h], radius=12, fill=(22, 42, 95))
        draw.rectangle([PAD, y, PAD + 5, y + box_h], fill=accent)  # chap chiziq
        ny = y + 14
        for line in note_wraps:
            draw.text((PAD + 20, ny), line, fill=(155, 175, 215), font=f_note_font)
            ny += 44
        y += box_h + 22

    # ── Makro-elementlar ──
    y_m = H - 222
    draw.rectangle([PAD, y_m - 12, W - PAD, y_m - 10], fill=(*accent, 55))

    macros = [
        (str(meal.get("cal", 0)),         "KALORIYA", "kkal",  (255, 107,  53)),
        (str(meal.get("protein", 0))+"g", "OQSIL",    "g",     ( 46, 204, 113)),
        (str(meal.get("carbs",   0))+"g", "UGLEVOD",  "g",     ( 52, 152, 219)),
        (str(meal.get("fat",     0))+"g", "YOG'",     "g",     (155,  89, 182)),
    ]
    bw = (W - PAD * 2 - 30) // 4
    f_val  = _font(50, bold=True)
    f_unit = _font(28)
    f_lbl2 = _font(28)
    for i, (val, label, unit, color) in enumerate(macros):
        bx = PAD + i * (bw + 10)
        draw.rounded_rectangle([bx, y_m, bx + bw, y_m + 145], radius=14, fill=(20, 20, 48))
        draw.rectangle([bx, y_m, bx + bw, y_m + 7], fill=color)   # ustki rang chizig'i
        draw.text((bx + bw // 2, y_m + 62), val,   fill=(255, 255, 255), font=f_val,  anchor="mm")
        draw.text((bx + bw // 2, y_m + 100), label, fill=color,           font=f_lbl2, anchor="mm")
        draw.text((bx + bw // 2, y_m + 130), unit,  fill=(100, 100, 135), font=f_unit, anchor="mm")

    # ── Progress nuqtalar ──
    y_dot = H - 65
    dot_start = W // 2 - (total * 22) // 2
    for i in range(total):
        c = accent if i == idx else (38, 38, 62)
        draw.ellipse(
            [dot_start + i * 22, y_dot, dot_start + i * 22 + 13, y_dot + 13],
            fill=c
        )

    # ── Footer ──
    draw.rectangle([0, H - 42, W, H], fill=(8, 8, 20))
    f_br = _font(29)
    draw.text(
        (W // 2, H - 22),
        "@QaytaTugulishBot  |  Qayta Tug'ilish Marafon",
        fill=(70, 70, 100), font=f_br, anchor="mm"
    )
    draw.rectangle([0, H - 5, W, H], fill=accent)

    # ── Bytes ──
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


# ── Suv norma kartochkasi ────────────────────────────────
def create_water_card(water_text: str, category: str) -> bytes:
    W2, H2 = 900, 420
    img  = Image.new("RGB", (W2, H2), (8, 20, 40))
    draw = ImageDraw.Draw(img)

    for y in range(H2):
        t = y / H2
        draw.line([(0, y), (W2, y)],
                  fill=(int(8 + 12*t), int(20 + 30*t), int(40 + 50*t)))

    accent = (26, 188, 156)
    draw.rectangle([0, 0, W2, 12], fill=accent)

    f_chip = _font(34)
    cw = int(f_chip.getlength(category)) + 44 if hasattr(f_chip, "getlength") else 260
    draw.rounded_rectangle([PAD, 28, PAD + cw, 76], radius=18, fill=accent)
    draw.text((PAD + cw // 2, 52), category, fill=(0, 0, 0), font=f_chip, anchor="mm")

    draw.text((PAD, 95),  "KUNLIK SUV NORMASINI",  fill=(255, 255, 255), font=_font(54, bold=True))
    draw.text((PAD, 162), "UNUTMANG!",              fill=accent,          font=_font(54, bold=True))

    draw.text((PAD, 240), f"Kuniga {water_text} ichish SHART!", fill=(200, 220, 240), font=_font(46))

    draw.text((PAD, 315), "Suv yog'larni eritadi, ovqat hazm qilishni", fill=(120, 140, 170), font=_font(34))
    draw.text((PAD, 355), "yaxshilaydi va detoks qiladi.",              fill=(120, 140, 170), font=_font(34))

    draw.rectangle([0, H2 - 40, W2, H2], fill=(6, 6, 18))
    draw.text((W2 // 2, H2 - 20), "@QaytaTugulishBot",
              fill=(70, 70, 100), font=_font(28), anchor="mm")
    draw.rectangle([0, H2 - 5, W2, H2], fill=accent)

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
