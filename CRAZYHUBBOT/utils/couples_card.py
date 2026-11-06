"""
couples_card.py - template-based "LOVE FOREVER" couples card.
Template image ke 2 circles me user DP + naam.

make_couple_card(p1, p2, name1, name2, date_text, out, template, font_path)
"""
import unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageChops

# Template (1672x941) ke circles: (center_x, center_y, radius)
LEFT = (381, 482, 287)
RIGHT = (1318, 478, 280)
S = 3  # supersampling for smooth edges


def _render(font, ch):
    im = Image.new("L", (80, 80), 0)
    ImageDraw.Draw(im).text((10, 10), ch, font=font, fill=255)
    return im.tobytes()


def _supports(font, ch):
    """Font me glyph hai ya nahi (missing glyph = same box as .notdef)."""
    try:
        return _render(font, ch) != _render(font, "\ue000")
    except Exception:
        return False


def clean_name(name, font, limit=16):
    name = unicodedata.normalize("NFKC", name or "")
    out = "".join(c for c in name if c == " " or (_supports(font, c) and unicodedata.category(c)[0] in "LNPS"))
    out = " ".join(out.split()).strip(" ._-")
    if not out:
        out = "User"
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "…"


def _avatar(path, r):
    im = Image.open(path).convert("RGB")
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width - s) // 2 + s, (im.height - s) // 2 + s))
    d = r * 2
    im = im.resize((d, d), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.12)
    # neon-theme blend: edges thoda dark + pink tint
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    rad = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    dark = np.clip((rad - 0.72) / 0.28, 0, 1) ** 1.6
    a = np.asarray(im).astype(np.float32)
    a *= (1 - 0.55 * dark)[..., None]
    a += dark[..., None] * np.array([70, 0, 30], dtype=np.float32) * 0.5
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    m = Image.new("L", (d * S, d * S), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * S - 1, d * S - 1), fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def _glow_text(base, xy, text, font, fill, glow, blur=7):
    w, h = base.size
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, text, font=font, fill=glow)
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur / 3)))
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill)


def _name_plate(base, cx, cy, text, font):
    w, h = base.size
    tw = font.getlength(text)
    pw, ph = max(tw + 90, 250), 66
    x0, y0, x1, y1 = cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((x0, y0, x1, y1), ph / 2, outline=(255, 50, 110, 255), width=7)
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
    pl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pl)
    pd.rounded_rectangle((x0, y0, x1, y1), ph / 2, fill=(24, 0, 16, 190), outline=(255, 120, 170, 255), width=3)
    base.alpha_composite(pl)
    asc, desc = font.getmetrics()
    _glow_text(base, (cx - tw / 2, cy - (asc + desc) / 2 - 1), text, font, (255, 255, 255, 255), (255, 60, 120, 255), 6)


TEMPLATE = "CRAZYHUBBOT/assets/couples_love_forever.png"
FONT = "CRAZYHUBBOT/assets/assets/font3.ttf"


def make_couple_card(p1, p2, name1, name2, date_text, out, template=TEMPLATE, font_path=FONT):
    base = Image.open(template).convert("RGBA")
    f_name = ImageFont.truetype(font_path, 40)
    f_date = ImageFont.truetype(font_path, 23)
    n1, n2 = clean_name(name1, f_name), clean_name(name2, f_name)

    for (cx, cy, r), path in ((LEFT, p1), (RIGHT, p2)):
        av = _avatar(path, r)
        base.alpha_composite(av, (cx - r, cy - r))
        # seam ko neon edge se chhupao
        edge = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(edge).ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 90, 150, 200), width=4)
        base.alpha_composite(edge.filter(ImageFilter.GaussianBlur(3)))

    _name_plate(base, LEFT[0], LEFT[1] + LEFT[2] - 62, n1, f_name)
    _name_plate(base, RIGHT[0], RIGHT[1] + RIGHT[2] - 62, n2, f_name)

    # date: neeche beech me
    txt = f"NEXT COUPLE  \u2022  {date_text}"
    sp = 4
    tw = sum(f_date.getlength(c) for c in txt) + sp * (len(txt) - 1)
    cx, cy = base.width / 2, 912
    pill = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((cx - tw / 2 - 34, cy - 24, cx + tw / 2 + 34, cy + 24), 24,
                                           fill=(20, 0, 14, 170), outline=(255, 190, 120, 230), width=2)
    base.alpha_composite(pill)
    x = cx - tw / 2
    for c in txt:
        _glow_text(base, (x, cy - 16), c, f_date, (255, 232, 190, 255), (255, 170, 90, 255), 4)
        x += f_date.getlength(c) + sp

    base.convert("RGB").save(out, quality=93)
    return out
