"""Galerias da arte 3D (para o README e para mostrar o mod).

    python3 tools/make_gallery.py

Gera em docs/preview/3d/:
  galeria_armas_3d.png     - armas, defesas e lancadores de convés por fase (inicio / meio / fim), como aparecem no jogo
  galeria_fabricas_3d.png  - fabricas (interior trabalhando + teto pintado) com a municao que produzem (pilha cheia + icone)
"""

import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "blender"))

import bs_data as D  # noqa: E402
import compose_preview as CP  # noqa: E402
import compose_factory as CF  # noqa: E402
from make_art import _font  # noqa: E402

ART = os.path.join(ROOT, "art3d")
OUT = os.path.join(ROOT, "docs", "preview", "3d")
BG = (7, 9, 14)
GOLD = (255, 196, 70)
TEXT = (220, 226, 236)
TIERS = [("early", "INÍCIO"), ("mid", "MEIO"), ("late", "FIM")]
PAINT = (46, 58, 74)
K = 2  # ampliacao dos sprites (pixel do jogo -> 2 px)


def weapon_tile(short):
    d = os.path.join(ART, short)
    meta = json.load(open(os.path.join(d, "meta.json")))
    roof = CP.paint_roof(CP.load(d, "roof.png"), PAINT)
    if meta["kind"] == "launcher":
        look = list(meta["modes"])[0]
        img = CP._launcher_frame(d, meta, roof, look, len(meta["modes"][look]["units"]), bg=BG)
    else:
        img = CP.assemble(d, meta, roof, bg=BG)
    img = CP.crop_content(img, BG)
    return img.resize((img.width * K, img.height * K), Image.LANCZOS)


def _sheet(rows, title_font, label_font, pad=20):
    """rows: [(titulo, [(imagem, legenda), ...])] -> folha com as figuras alinhadas pela base."""
    lab_h = label_font.size + 10
    tit_h = title_font.size + 12
    W = max(pad + sum(im.width + pad for im, _ in items) for _, items in rows)
    H = sum(tit_h + max(im.height for im, _ in items) + lab_h + pad for _, items in rows) + pad
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    y = pad // 2
    for title, items in rows:
        dr.text((pad, y), title, font=title_font, fill=GOLD)
        y += tit_h
        rh = max(im.height for im, _ in items)
        x = pad
        for im, lab in items:
            sheet.paste(im.convert("RGB"), (x, y + rh - im.height))
            tw = dr.textlength(lab, font=label_font)
            dr.text((x + (im.width - tw) / 2, y + rh + 4), lab, font=label_font, fill=TEXT)
            x += im.width + pad
        y += rh + lab_h + pad
    return sheet


def weapons_gallery():
    rows = []
    for tier, title in TIERS:
        # armas e defesas (Tatu, Tamandua, Pororoca) por area; os lancadores no fim de cada fileira
        items = [(g["short"], g["codename"], g["size"][0] * g["size"][1]) for g in D.GUNS + D.DEFENSES
                 if g["tier"] == tier]
        items.sort(key=lambda t: t[2])
        items += [(m["short"], m["codename"], 0) for m in D.LAUNCHERS if m.get("tier") == tier]
        rows.append((title, [(weapon_tile(s), name) for s, name, _ in items
                             if os.path.exists(os.path.join(ART, s, "meta.json"))]))
    sheet = _sheet(rows, _font(34), _font(20))
    sheet.save(os.path.join(OUT, "galeria_armas_3d.png"))
    return sheet


def factory_tile(fac, res):
    fm = json.load(open(os.path.join(ART, fac, "meta.json")))
    rm = json.load(open(os.path.join(ART, res, "meta.json")))
    frames = fm["machine"]["frames"]
    inner = CF._interior(fac, fm, frames[len(frames) // 2])
    roof = CF._roof_tint(CF._load(fac, fm["hull"]["roof"]))
    stack = CF._load(res, f"stack_{rm.get('stack', 4)}.png")
    icon = CF._load(res, "icon.png")
    s = 2
    a, b = inner.resize((inner.width * s, inner.height * s), Image.NEAREST), roof.resize((roof.width * s, roof.height * s),
                                                                                         Image.NEAREST)
    cell = 64 * s
    gap = 10
    W = a.width + gap + b.width
    H = a.height + gap + cell
    img = Image.new("RGBA", (W, H), BG + (255,))
    img.alpha_composite(a, (0, 0))
    img.alpha_composite(b, (a.width + gap, 0))
    tile_bg = (48, 52, 62, 255)
    for i, im in enumerate((stack, icon)):
        x = i * (cell + gap)
        ImageDraw.Draw(img).rectangle([x, a.height + gap, x + cell - 1, a.height + gap + cell - 1], fill=tile_bg)
        img.alpha_composite(im.resize((cell, cell), Image.NEAREST), (x, a.height + gap))
    return img


def factories_gallery():
    res_name = {r["id"]: r.get("name_ptbr", r["id"]) for r in D.SPEC["resources"]}
    items = []
    for f in D.SPEC["factories"]:
        fac = f["id"].split(".", 1)[1]
        res = f["output"][0].split(".", 1)[1]
        if not (os.path.exists(os.path.join(ART, fac, "meta.json")) and os.path.exists(os.path.join(ART, res, "meta.json"))):
            continue
        items.append((factory_tile(fac, res), f"{f['name_ptbr']} → {res_name.get(f['output'][0], res)}"))
    # duas fileiras: prensas em cima, municoes especiais embaixo
    rows = [("FÁBRICAS E MUNIÇÕES", items[:3]), ("", items[3:])] if len(items) > 3 else [("FÁBRICAS E MUNIÇÕES", items)]
    sheet = _sheet(rows, _font(34), _font(18))
    sheet.save(os.path.join(OUT, "galeria_fabricas_3d.png"))
    return sheet


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn in (weapons_gallery, factories_gallery):
        s = fn()
        print(fn.__name__, s.size)
