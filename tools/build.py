"""Ар бир мугалим үчүн шилтеме барагын жана WhatsApp карточкасын түзөт.

Колдонуу:
    python3 tools/build.py

Керектүү нерселер:
    teachers.json      — мугалимдердин тизмеси (slug, name, role, form)
    photos/<slug>.jpg  — мугалимдин сүрөтү (3:4, мисалы 600x800)
    tools/fonts/       — PT Sans жана Unbounded шрифттери

Натыйжа:
    og/<slug>.jpg         — WhatsApp'та көрүнгөн карточка (1200x630)
    <slug>/index.html     — форманы дароо ачкан барак
"""
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
SITE_URL = "https://bakytkg.github.io/shilteme"

W, H = 1200, 630
PHOTO_W = 472
BG = (24, 46, 20)          # кочкул жашыл
GREEN = (124, 194, 66)     # мектептин жашыл тилкеси
WHITE = (255, 255, 255)
SOFT = (196, 214, 188)


def font(name, size, variation=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:
            pass
    return f


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=fnt) <= width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def make_card(t):
    card = Image.new("RGB", (W, H), BG)
    photo = ImageOps.fit(
        Image.open(ROOT / "photos" / f"{t['slug']}.jpg").convert("RGB"),
        (PHOTO_W, H),
        method=Image.LANCZOS,
        centering=(0.5, 0.3),
    )
    card.paste(photo, (0, 0))
    d = ImageDraw.Draw(card)
    d.rectangle([PHOTO_W, 0, PHOTO_W + 10, H], fill=GREEN)

    x = PHOTO_W + 64
    text_w = W - x - 56

    small = font("PT_Sans-Web-Bold.ttf", 26)
    d.text((x, 66), "БИЛИМ ЖОЛУ МЕКТЕБИ", font=small, fill=GREEN, spacing=4)

    size = 50
    name_font = font("Unbounded.ttf", size, "Bold")
    lines = wrap(d, t["name"], name_font, text_w)
    while len(lines) > 3 and size > 34:
        size -= 4
        name_font = font("Unbounded.ttf", size, "Bold")
        lines = wrap(d, t["name"], name_font, text_w)
    y = 128
    for ln in lines:
        d.text((x, y), ln, font=name_font, fill=WHITE)
        y += int(size * 1.28)

    role_font = font("PT_Sans-Web-Regular.ttf", 32)
    d.text((x, y + 14), t["role"], font=role_font, fill=SOFT)

    cta_font = font("PT_Sans-Web-Bold.ttf", 32)
    cta = "Баа бериңиз"
    tw = d.textlength(cta, font=cta_font)
    arrow_w = 30
    bx, by, bh = x, H - 66 - 72, 72
    bw = tw + 32 + 18 + arrow_w + 32
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=36, fill=GREEN)
    d.text((bx + 32, by + bh / 2), cta, font=cta_font, fill=BG, anchor="lm")
    ax, ay = bx + 32 + tw + 18, by + bh / 2
    d.line([(ax, ay), (ax + arrow_w, ay)], fill=BG, width=4)
    d.line([(ax + arrow_w - 11, ay - 11), (ax + arrow_w, ay), (ax + arrow_w - 11, ay + 11)], fill=BG, width=4, joint="curve")

    note_font = font("PT_Sans-Web-Regular.ttf", 24)
    d.text((bx + bw + 32, by + bh / 2), "5 суроо · 1 мүнөт", font=note_font, fill=SOFT, anchor="lm")

    out = ROOT / "og" / f"{t['slug']}.jpg"
    out.parent.mkdir(exist_ok=True)
    card.save(out, quality=85, optimize=True, progressive=True)


PAGE = """<!doctype html>
<html lang="ky">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="robots" content="noindex">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Билим Жолу мектеби">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#182e14">
<meta http-equiv="refresh" content="{refresh}; url={form}">
<link rel="preload" as="image" href="../photos/{slug}.jpg">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;background:#182e14;color:#fff}}
body{{font:17px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;min-height:100vh;
display:flex;justify-content:center;
padding:max(20px,env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) max(24px,env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left))}}
main{{width:100%;max-width:420px;display:flex;flex-direction:column;gap:16px}}
.school{{font-size:13px;font-weight:700;letter-spacing:.08em;color:#7cc242}}
.photo{{width:100%;height:min(48vh,420px);object-fit:cover;object-position:center 22%;border-radius:20px;
background:#22401c;display:block;border-bottom:6px solid #7cc242}}
h1{{margin:0;font-size:24px;line-height:1.2;text-wrap:balance}}
.role{{margin:0;color:#c4d6bc}}
.bar{{height:6px;border-radius:3px;background:#2c4a25;overflow:hidden}}
.bar i{{display:block;height:100%;width:0;background:#7cc242;animation:fill {delay}ms linear forwards}}
@keyframes fill{{to{{width:100%}}}}
.go{{display:flex;align-items:center;justify-content:center;min-height:56px;border-radius:16px;
background:#7cc242;color:#102008;font-weight:700;font-size:18px;text-decoration:none}}
.go:focus-visible{{outline:3px solid #fff;outline-offset:3px}}
.note{{margin:0;text-align:center;font-size:14px;color:#9fb59a}}
@media (prefers-reduced-motion:reduce){{.bar i{{animation:none;width:100%}}}}
</style>
</head>
<body>
<main>
<div class="school">БИЛИМ ЖОЛУ МЕКТЕБИ</div>
<img class="photo" src="../photos/{slug}.jpg" alt="{name}" width="600" height="800">
<h1>{name}</h1>
<p class="role">{role}</p>
<div class="bar" aria-hidden="true"><i></i></div>
<a class="go" href="{form}">Баа берүү</a>
<p class="note">5 суроо, 1 мүнөт. Атыңыз жазылбайт.</p>
</main>
<script>setTimeout(function(){{location.replace({form_js});}}, {delay});</script>
</body>
</html>
"""

# 0 = шилтеме дароо формага өтөт (сүрөт WhatsApp карточкасында көрүнөт).
# Мисалы 3000 коюлса, адегенде мугалимдин сүрөтү бар барак 3 секунд көрүнөт.
DELAY_MS = 0


def make_page(t):
    url = f"{SITE_URL}/{t['slug']}/"
    title = f"{t['name']}: баа бериңиз"
    desc = f"{t['role']}. 5 суроо, 1 мүнөт. Атыңыз жазылбайт."
    out = ROOT / t["slug"] / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        PAGE.format(
            title=html.escape(title),
            desc=html.escape(desc),
            url=url,
            image=f"{SITE_URL}/og/{t['slug']}.jpg",
            form=html.escape(t["form"]),
            form_js=json.dumps(t["form"]),
            slug=t["slug"],
            name=html.escape(t["name"]),
            role=html.escape(t["role"]),
            delay=DELAY_MS,
            refresh=DELAY_MS // 1000,
        ),
        encoding="utf-8",
    )


def main():
    teachers = json.loads((ROOT / "teachers.json").read_text(encoding="utf-8"))
    for t in teachers:
        make_card(t)
        make_page(t)
        print(f"{SITE_URL}/{t['slug']}/")


if __name__ == "__main__":
    main()
