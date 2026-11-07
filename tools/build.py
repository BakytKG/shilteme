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


_UNBOUNDED_CHARS = None


def display_font(text, size):
    """Unbounded'да кыргыз тамгалары (ң, ө, ү) жок. Андай аттар PT Sans Bold менен жазылат."""
    global _UNBOUNDED_CHARS
    if _UNBOUNDED_CHARS is None:
        from fontTools.ttLib import TTFont
        _UNBOUNDED_CHARS = set(TTFont(str(FONTS / "Unbounded.ttf")).getBestCmap())
    if all(ord(c) in _UNBOUNDED_CHARS for c in text if not c.isspace()):
        return font("Unbounded.ttf", size, "Bold")
    return font("PT_Sans-Web-Bold.ttf", int(size * 1.2))


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
    photo_path = ROOT / "photos" / f"{t['slug']}.jpg"
    d = ImageDraw.Draw(card)
    if photo_path.exists():
        photo = ImageOps.fit(
            Image.open(photo_path).convert("RGB"),
            (PHOTO_W, H),
            method=Image.LANCZOS,
            centering=(0.5, 0.3),
        )
        card.paste(photo, (0, 0))
    else:
        # Сүрөт али жок: аты-жөнүнүн баш тамгалары бар жашыл тегерек.
        d.rectangle([0, 0, PHOTO_W, H], fill=(34, 64, 28))
        cx, cy, r = PHOTO_W // 2, H // 2, 150
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        parts = t["name"].split()
        if len(parts) >= 3 and parts[1].lower() in ("кызы", "уулу"):
            parts = [parts[0], parts[2]]  # «Замир кызы Ардак» → «ЗА»
        initials = "".join(w[0] for w in parts[:2]).upper()
        d.text((cx, cy), initials, font=display_font(initials, 88), fill=BG, anchor="mm")
    d.rectangle([PHOTO_W, 0, PHOTO_W + 10, H], fill=GREEN)

    x = PHOTO_W + 64
    text_w = W - x - 56

    small = font("PT_Sans-Web-Bold.ttf", 26)
    d.text((x, 66), "БИЛИМ ЖОЛУ МЕКТЕБИ", font=small, fill=GREEN, spacing=4)

    size = 50
    name_font = display_font(t["name"], size)
    lines = wrap(d, t["name"], name_font, text_w)
    while len(lines) > 3 and size > 34:
        size -= 4
        name_font = display_font(t["name"], size)
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


def initials_of(name):
    parts = name.split()
    if len(parts) >= 3 and parts[1].lower() in ("кызы", "уулу"):
        parts = [parts[0], parts[2]]
    return "".join(w[0] for w in parts[:2]).upper()


def make_index_card():
    """Жалпы шилтеменин WhatsApp карточкасы (бардык класстар үчүн)."""
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 18, H], fill=GREEN)
    x = 96
    d.text((x, 92), "БИЛИМ ЖОЛУ МЕКТЕБИ", font=font("PT_Sans-Web-Bold.ttf", 30), fill=GREEN)
    title_font = display_font("Класс жетекчиңизге баа бериңиз", 64)
    y = 160
    for ln in wrap(d, "Класс жетекчиңизге баа бериңиз", title_font, W - x - 80):
        d.text((x, y), ln, font=title_font, fill=WHITE)
        y += 86
    d.text((x, y + 18), "1–4-класстардын ата-энелери үчүн. Балаңыздын классын тандаңыз.",
           font=font("PT_Sans-Web-Regular.ttf", 32), fill=SOFT)
    cta_font = font("PT_Sans-Web-Bold.ttf", 32)
    cta = "Классты тандоо"
    tw = d.textlength(cta, font=cta_font)
    bx, by, bh = x, H - 70 - 72, 72
    arrow_w = 30
    bw = tw + 32 + 18 + arrow_w + 32
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=36, fill=GREEN)
    d.text((bx + 32, by + bh / 2), cta, font=cta_font, fill=BG, anchor="lm")
    ax, ay = bx + 32 + tw + 18, by + bh / 2
    d.line([(ax, ay), (ax + arrow_w, ay)], fill=BG, width=4)
    d.line([(ax + arrow_w - 11, ay - 11), (ax + arrow_w, ay), (ax + arrow_w - 11, ay + 11)], fill=BG, width=4, joint="curve")
    d.text((bx + bw + 32, by + bh / 2), "5 суроо · 1 мүнөт · атыңыз жазылбайт",
           font=font("PT_Sans-Web-Regular.ttf", 24), fill=SOFT, anchor="lm")
    card.save(ROOT / "og" / "index.jpg", quality=85, optimize=True, progressive=True)


INDEX = """<!doctype html>
<html lang="ky">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Класс жетекчиңизге баа бериңиз</title>
<meta name="robots" content="noindex">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Билим Жолу мектеби">
<meta property="og:title" content="Класс жетекчиңизге баа бериңиз">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#182e14">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;background:#182e14;color:#fff}}
body{{font:17px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
padding:max(20px,env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) max(28px,env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left))}}
main{{max-width:460px;margin:0 auto;display:flex;flex-direction:column;gap:18px}}
.school{{font-size:13px;font-weight:700;letter-spacing:.08em;color:#7cc242}}
h1{{margin:0;font-size:26px;line-height:1.2;text-wrap:balance}}
.lead{{margin:0;color:#c4d6bc}}
h2{{margin:8px 0 0;font-size:13px;font-weight:700;letter-spacing:.08em;color:#9fb59a;text-transform:uppercase}}
ul{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}}
a.row{{display:flex;align-items:center;gap:14px;padding:10px 14px 10px 10px;border-radius:16px;
background:#22401c;color:#fff;text-decoration:none;min-height:68px}}
a.row:active{{background:#2c5224}}
a.row:focus-visible{{outline:3px solid #7cc242;outline-offset:2px}}
.av{{width:48px;height:48px;border-radius:50%;flex:none;object-fit:cover;object-position:center 22%;background:#7cc242;
display:grid;place-items:center;color:#182e14;font-weight:800;font-size:17px}}
.txt{{min-width:0;flex:1}}
.cls{{display:block;font-weight:800;font-size:20px}}
.who{{display:block;font-size:14px;color:#c4d6bc}}
.go{{flex:none;color:#7cc242;font-size:22px}}
.note{{margin:4px 0 0;text-align:center;font-size:14px;color:#9fb59a}}
</style>
</head>
<body>
<main>
<div class="school">БИЛИМ ЖОЛУ МЕКТЕБИ</div>
<h1>Класс жетекчиңизге баа бериңиз</h1>
<p class="lead">Балаңыздын классын тандаңыз. 5 суроо, 1 мүнөт. Атыңыз жазылбайт.</p>
{groups}
<p class="note">Эки балаңыз ар башка класста окуса, ар бир класс жетекчиге өзүнчө баа бериңиз.</p>
</main>
</body>
</html>
"""


def class_key(c):
    grade, rest = c.split("-", 1)
    return (int(grade), rest)


def make_index(teachers):
    make_index_card()
    rows = []
    for t in teachers:
        for c in t["classes"]:
            rows.append((c, t))
    rows.sort(key=lambda r: class_key(r[0]))
    groups, current = [], None
    for c, t in rows:
        grade = c.split("-", 1)[0]
        if grade != current:
            if current is not None:
                groups.append("</ul>")
            groups.append(f"<h2>{grade}-класстар</h2>\n<ul>")
            current = grade
        if (ROOT / "photos" / f"{t['slug']}.jpg").exists():
            av = f'<img class="av" src="photos/{t["slug"]}.jpg" alt="" width="48" height="48" loading="lazy">'
        else:
            av = f'<span class="av" aria-hidden="true">{html.escape(initials_of(t["name"]))}</span>'
        groups.append(
            f'<li><a class="row" href="{html.escape(t["form"])}">{av}'
            f'<span class="txt"><span class="cls">{html.escape(c)}</span>'
            f'<span class="who">{html.escape(t["name"])}</span></span>'
            f'<span class="go" aria-hidden="true">›</span></a></li>'
        )
    groups.append("</ul>")
    (ROOT / "index.html").write_text(
        INDEX.format(
            desc="1–4-класстардын ата-энелери үчүн. Балаңыздын классын тандап, класс жетекчиге баа бериңиз.",
            url=f"{SITE_URL}/",
            image=f"{SITE_URL}/og/index.jpg",
            groups="\n".join(groups),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 5–9-класстар: окуучулар предметтик мугалимдерге баа берет.
# Маалымат upper.json файлында. Ар бир класска бир барак (/<класс>/),
# анда ошол класстын мугалимдери тизмеленет, ар бири өз формасына алып барат.
# ---------------------------------------------------------------------------

def avatar(card, d, slug, name, cx, cy, r, ring=BG):
    """Тегерек сүрөт (болбосо баш тамгалар) + кочкул жашыл алкак."""
    d.ellipse([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5], fill=ring)
    photo_path = ROOT / "photos" / f"{slug}.jpg"
    if photo_path.exists():
        size = 2 * r
        ph = ImageOps.fit(Image.open(photo_path).convert("RGB"), (size, size),
                          method=Image.LANCZOS, centering=(0.5, 0.25))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
        card.paste(ph, (cx - r, cy - r), mask)
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        ini = initials_of(name)
        d.text((cx, cy), ini, font=font("PT_Sans-Web-Bold.ttf", int(r * 0.78)), fill=BG, anchor="mm")


def cta(d, x, y, label, note):
    cta_font = font("PT_Sans-Web-Bold.ttf", 32)
    tw = d.textlength(label, font=cta_font)
    arrow_w, bh = 30, 72
    bw = tw + 32 + 18 + arrow_w + 32
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=36, fill=GREEN)
    d.text((x + 32, y + bh / 2), label, font=cta_font, fill=BG, anchor="lm")
    ax, ay = x + 32 + tw + 18, y + bh / 2
    d.line([(ax, ay), (ax + arrow_w, ay)], fill=BG, width=4)
    d.line([(ax + arrow_w - 11, ay - 11), (ax + arrow_w, ay), (ax + arrow_w - 11, ay + 11)],
           fill=BG, width=4, joint="curve")
    if note:
        d.text((x + bw + 28, y + bh / 2), note, font=font("PT_Sans-Web-Regular.ttf", 24), fill=SOFT, anchor="lm")


def split_class(name):
    """«7-А (12)» → («7-А», «(12)»)."""
    if " " in name:
        a, b = name.split(" ", 1)
        return a, b
    return name, ""


def make_class_card(c, people):
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    # Сол жак: класстын аты
    d.rectangle([0, 0, PHOTO_W, H], fill=(34, 64, 28))
    d.rectangle([PHOTO_W, 0, PHOTO_W + 10, H], fill=GREEN)
    big, small = split_class(c["name"])
    d.text((PHOTO_W / 2, H / 2 - (34 if small else 0)), big,
           font=font("Unbounded.ttf", 128, "Bold"), fill=WHITE, anchor="mm")
    if small:
        d.text((PHOTO_W / 2, H / 2 + 92), small, font=font("PT_Sans-Web-Bold.ttf", 52), fill=GREEN, anchor="mm")
    d.text((PHOTO_W / 2, 66), "КЛАСС", font=font("PT_Sans-Web-Bold.ttf", 26), fill=GREEN, anchor="mm")

    x = PHOTO_W + 64
    d.text((x, 66), "БИЛИМ ЖОЛУ МЕКТЕБИ", font=font("PT_Sans-Web-Bold.ttf", 26), fill=GREEN)
    title = "Мугалимдериңизге баа бериңиз"
    tf = display_font(title, 50)
    y = 118
    for ln in wrap(d, title, tf, W - x - 56):
        d.text((x, y), ln, font=tf, fill=WHITE)
        y += 66
    # Мугалимдердин тегерек сүрөттөрү (бири-биринин үстүнө)
    r, step = 31, 68
    shown = people[:9]
    ay = y + 60
    for i, (slug, t) in enumerate(shown):
        avatar(card, d, slug, t["name"], x + r + i * step, ay, r)
    cta(d, x, H - 66 - 72, "Баа берүү", f"{len(people)} мугалим · 1 мүнөттөн")
    card.save(ROOT / "og" / f"{c['slug']}.jpg", quality=85, optimize=True, progressive=True)


CLASS_PAGE = """<!doctype html>
<html lang="ky">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{cls}: мугалимдериңизге баа бериңиз</title>
<meta name="robots" content="noindex">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Билим Жолу мектеби">
<meta property="og:title" content="{cls}: мугалимдериңизге баа бериңиз">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#182e14">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;background:#182e14;color:#fff}}
body{{font:17px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
padding:max(20px,env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) max(28px,env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left))}}
main{{max-width:460px;margin:0 auto;display:flex;flex-direction:column;gap:16px}}
.school{{font-size:13px;font-weight:700;letter-spacing:.08em;color:#7cc242}}
.head{{display:flex;align-items:center;gap:14px}}
.badge{{flex:none;min-width:64px;height:64px;padding:0 10px;border-radius:18px;background:#7cc242;color:#182e14;
display:grid;place-items:center;font-weight:800;font-size:22px;line-height:1;text-align:center}}
.badge small{{display:block;font-size:12px;font-weight:700}}
h1{{margin:0;font-size:24px;line-height:1.2;text-wrap:balance}}
.lead{{margin:0;color:#c4d6bc}}
.prog{{display:flex;align-items:center;gap:12px;font-size:14px;color:#9fb59a}}
.prog .bar{{flex:1;height:6px;border-radius:3px;background:#2c4a25;overflow:hidden}}
.prog .bar i{{display:block;height:100%;width:0;background:#7cc242;transition:width .3s}}
ul{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}}
a.row{{display:flex;align-items:center;gap:14px;padding:10px 14px 10px 10px;border-radius:16px;
background:#22401c;color:#fff;text-decoration:none;min-height:72px}}
a.row:active{{background:#2c5224}}
a.row:focus-visible{{outline:3px solid #7cc242;outline-offset:2px}}
.av{{width:52px;height:52px;border-radius:50%;flex:none;object-fit:cover;object-position:center 22%;background:#7cc242;
display:grid;place-items:center;color:#182e14;font-weight:800;font-size:17px}}
.txt{{min-width:0;flex:1}}
.subj{{display:block;font-weight:800;font-size:18px}}
.who{{display:block;font-size:14px;color:#c4d6bc}}
.go{{flex:none;font-size:14px;font-weight:700;color:#182e14;background:#7cc242;border-radius:999px;padding:6px 12px}}
.row.done{{background:#1d3618}}
.row.done .go{{background:transparent;color:#7cc242;padding:6px 4px}}
.row.done .subj,.row.done .who{{opacity:.7}}
.note{{margin:4px 0 0;text-align:center;font-size:14px;color:#9fb59a}}
.note a{{color:#c4d6bc}}
</style>
</head>
<body>
<main>
<div class="school">БИЛИМ ЖОЛУ МЕКТЕБИ</div>
<div class="head"><div class="badge">{badge}</div><h1>Мугалимдериңизге баа бериңиз</h1></div>
<p class="lead">Ар бир мугалимди басып, 5 суроого жооп бериңиз. Атыңыз жазылбайт. Бүткөндөн кийин ушул баракка кайтып, кийинки мугалимди тандаңыз.</p>
<div class="prog" aria-live="polite"><div class="bar"><i id="pb"></i></div><span id="pt">0 / {n}</span></div>
<ul>
{rows}
</ul>
<p class="note">Башка класстасызбы? <a href="../okuuchular/">Классыңызды тандаңыз</a></p>
</main>
<script>
(function(){{
  var KEY = "bj-baa:{slug}:" + new Date().toISOString().slice(0,7);
  function load(){{ try {{ return JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch(e) {{ return {{}}; }} }}
  function save(v){{ try {{ localStorage.setItem(KEY, JSON.stringify(v)); }} catch(e) {{}} }}
  function paint(){{
    var done = load(), rows = document.querySelectorAll("a.row"), k = 0;
    rows.forEach(function(a){{
      var on = !!done[a.dataset.t];
      a.classList.toggle("done", on);
      a.querySelector(".go").textContent = on ? "✓ Берилди" : "Баа берүү";
      if (on) k++;
    }});
    document.getElementById("pt").textContent = k + " / " + rows.length;
    document.getElementById("pb").style.width = (rows.length ? 100 * k / rows.length : 0) + "%";
  }}
  document.querySelectorAll("a.row").forEach(function(a){{
    a.addEventListener("click", function(){{ var d = load(); d[a.dataset.t] = 1; save(d); }});
  }});
  window.addEventListener("pageshow", paint);
  paint();
}})();
</script>
</body>
</html>
"""


def class_people(c, upper):
    """Класстагы мугалимдер (бир мугалим эки предмет окутса, бир жолу көрсөтүлөт)."""
    order, subj = [], {}
    for s, slug in c["subjects"]:
        t = upper["teachers"].get(slug)
        if not t or not t.get("form"):
            continue
        if slug not in subj:
            order.append(slug)
            subj[slug] = []
        subj[slug].append(s)
    return [(slug, upper["teachers"][slug], subj[slug]) for slug in order]


def make_class_page(c, upper):
    people = class_people(c, upper)
    make_class_card(c, [(s, t) for s, t, _ in people])
    rows = []
    for slug, t, subjects in people:
        if (ROOT / "photos" / f"{slug}.jpg").exists():
            av = f'<img class="av" src="../photos/{slug}.jpg" alt="" width="52" height="52" loading="lazy">'
        else:
            av = f'<span class="av" aria-hidden="true">{html.escape(initials_of(t["name"]))}</span>'
        rows.append(
            f'<li><a class="row" data-t="{slug}" href="{html.escape(t["form"])}">{av}'
            f'<span class="txt"><span class="subj">{html.escape(", ".join(subjects))}</span>'
            f'<span class="who">{html.escape(t["name"])}</span></span>'
            f'<span class="go">Баа берүү</span></a></li>'
        )
    big, small = split_class(c["name"])
    badge = html.escape(big) + (f"<small>{html.escape(small)}</small>" if small else "")
    out = ROOT / c["slug"] / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        CLASS_PAGE.format(
            cls=html.escape(c["name"]),
            desc=html.escape(f"{c['name']} класстын окуучулары үчүн. {len(people)} мугалим, ар бирине 5 суроо. Атыңыз жазылбайт."),
            url=f"{SITE_URL}/{c['slug']}/",
            image=f"{SITE_URL}/og/{c['slug']}.jpg",
            badge=badge,
            n=len(people),
            rows="\n".join(rows),
            slug=c["slug"],
        ),
        encoding="utf-8",
    )


def make_hub_card():
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 18, H], fill=GREEN)
    x = 96
    d.text((x, 92), "БИЛИМ ЖОЛУ МЕКТЕБИ", font=font("PT_Sans-Web-Bold.ttf", 30), fill=GREEN)
    tf = display_font("Мугалимдериңизге баа бериңиз", 64)
    y = 160
    for ln in ("Мугалимдериңизге", "баа бериңиз"):
        d.text((x, y), ln, font=tf, fill=WHITE)
        y += 86
    d.text((x, y + 18), "5–9-класстардын окуучулары үчүн. Классыңызды тандаңыз.",
           font=font("PT_Sans-Web-Regular.ttf", 32), fill=SOFT)
    cta(d, x, H - 70 - 72, "Классты тандоо", "5 суроо · 1 мүнөт · атыңыз жазылбайт")
    card.save(ROOT / "og" / "okuuchular.jpg", quality=85, optimize=True, progressive=True)


HUB = """<!doctype html>
<html lang="ky">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Мугалимдериңизге баа бериңиз</title>
<meta name="robots" content="noindex">
<meta name="description" content="5–9-класстардын окуучулары үчүн. Классыңызды тандап, мугалимдериңизге баа бериңиз.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Билим Жолу мектеби">
<meta property="og:title" content="Мугалимдериңизге баа бериңиз">
<meta property="og:description" content="5–9-класстардын окуучулары үчүн. Классыңызды тандап, мугалимдериңизге баа бериңиз.">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#182e14">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;background:#182e14;color:#fff}}
body{{font:17px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
padding:max(20px,env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) max(28px,env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left))}}
main{{max-width:460px;margin:0 auto;display:flex;flex-direction:column;gap:18px}}
.school{{font-size:13px;font-weight:700;letter-spacing:.08em;color:#7cc242}}
h1{{margin:0;font-size:26px;line-height:1.2;text-wrap:balance}}
.lead{{margin:0;color:#c4d6bc}}
h2{{margin:8px 0 0;font-size:13px;font-weight:700;letter-spacing:.08em;color:#9fb59a;text-transform:uppercase}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}}
.grid a{{display:flex;flex-direction:column;justify-content:center;min-height:76px;padding:12px 14px;border-radius:16px;
background:#22401c;color:#fff;text-decoration:none}}
.grid a:active{{background:#2c5224}}
.grid a:focus-visible{{outline:3px solid #7cc242;outline-offset:2px}}
.grid b{{font-size:24px;font-weight:800}}
.grid span{{font-size:13px;color:#c4d6bc}}
</style>
</head>
<body>
<main>
<div class="school">БИЛИМ ЖОЛУ МЕКТЕБИ</div>
<h1>Мугалимдериңизге баа бериңиз</h1>
<p class="lead">5–9-класстардын окуучулары үчүн. Классыңызды тандаңыз. Ар бир мугалимге 5 суроо, атыңыз жазылбайт.</p>
{groups}
</main>
</body>
</html>
"""


def make_hub(upper):
    make_hub_card()
    groups, current = [], None
    for c in sorted(upper["classes"], key=lambda c: class_key(c["name"])):
        grade = c["name"].split("-", 1)[0]
        if grade != current:
            if current is not None:
                groups.append("</div>")
            groups.append(f"<h2>{grade}-класстар</h2>\n<div class=\"grid\">")
            current = grade
        n = len(class_people(c, upper))
        groups.append(f'<a href="../{c["slug"]}/"><b>{html.escape(c["name"])}</b><span>{n} мугалим</span></a>')
    groups.append("</div>")
    out = ROOT / "okuuchular" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(HUB.format(url=f"{SITE_URL}/okuuchular/", image=f"{SITE_URL}/og/okuuchular.jpg",
                              groups="\n".join(groups)), encoding="utf-8")


def main():
    teachers = json.loads((ROOT / "teachers.json").read_text(encoding="utf-8"))
    for t in teachers:
        make_card(t)
        make_page(t)
        print(f"{SITE_URL}/{t['slug']}/")
    make_index(teachers)
    print(f"{SITE_URL}/  (жалпы шилтеме)")

    upper_path = ROOT / "upper.json"
    if upper_path.exists():
        upper = json.loads(upper_path.read_text(encoding="utf-8"))
        for c in upper["classes"]:
            make_class_page(c, upper)
            print(f"{SITE_URL}/{c['slug']}/  ({c['name']}, {len(class_people(c, upper))} мугалим)")
        make_hub(upper)
        print(f"{SITE_URL}/okuuchular/  (5–9-класстар, жалпы шилтеме)")


if __name__ == "__main__":
    main()
