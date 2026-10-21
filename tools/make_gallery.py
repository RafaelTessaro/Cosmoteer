"""Galerias da arte 3D (para o README e para mostrar o mod), com o DATA 2.0 (bs_data).

    python3 tools/make_gallery.py [--out DIR] [armas] [fabricas] [layered]

Gera em DIR (padrao docs/preview/3d/):
  galeria_armas_3d.png     - armas, defesas, PEM e lancadores de conves por fase (inicio / meio / fim), como aparecem
                             no jogo (pasta de arte = art3d_dir: a Boiuna le art3d/bs_boiuna_ac)
  galeria_fabricas_3d.png  - fabricas F1-F6 (interior trabalhando + teto pintado com a placa de modo) com a municao
                             que produzem (pilha cheia + icone)
  galeria_layered_3d.png   - pecas "layered": o Tupa montado (carregador + 4 canos + ponta), os paiois 1x1/2x2/3x3
                             por familia e a Fita, interior e teto (tools/blender/compose_preview.make_layered faz a
                             previa animada de cada pasta)
Sem argumentos de galeria, gera as tres.
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
FAMILIAS = {"cartuchos": "Cartuchos", "celulas": "Células", "misseis": "Mísseis", "projeteis": "Projéteis"}


def _has(d):
    return os.path.exists(os.path.join(ART, d, "meta.json"))


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
    rows = [(t, items) for t, items in rows if items]
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


def art_dir(x):
    return x.get("art3d_dir") or x.get("short") or x["id"].split(".", 1)[1]


def weapons_gallery(out=OUT):
    rows = []
    launchers = D.LAUNCHERS or [dict(lch, short=lch["id"].split(".", 1)[1]) for lch in D.MSPEC.get("launchers", [])]
    for tier, title in TIERS:
        # armas, defesas (Tatu, Tamandua, Pororoca) e PEM por area; os lancadores no fim de cada fileira
        items = [(art_dir(g), g.get("codename") or g["name_pt"], g["size"][0] * g["size"][1])
                 for g in D.GUNS + D.DEFENSES + list(getattr(D, "PEM", [])) if g.get("tier") == tier]
        items.sort(key=lambda t: t[2])
        items += [(art_dir(m), m.get("codename") or m["short"], 0) for m in launchers if m.get("tier") == tier]
        rows.append((title, [(weapon_tile(s), name) for s, name, _ in items if _has(s)]))
    sheet = _sheet(rows, _font(34), _font(20))
    sheet.save(os.path.join(out, "galeria_armas_3d.png"))
    return sheet


def factory_tile(fac, res):
    fm = json.load(open(os.path.join(ART, fac, "meta.json")))
    rm = json.load(open(os.path.join(ART, res, "meta.json")))
    frames = fm["machine"]["frames"]
    inner = CF._interior(fac, fm, frames[len(frames) // 2])
    roof = CF.plate_on_roof(CF._roof_tint(CF._load(fac, fm["hull"]["roof"])), fm)
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


def factories_gallery(out=OUT):
    items = []
    for f in D.FACTORIES:
        fac = art_dir(f)
        r = D.RES_BY_ID.get(f["recipes"][0]["output_resource"]) or {}
        res = r.get("art3d_dir") or r.get("dir")
        if not (res and _has(fac) and _has(res)):
            continue
        items.append((factory_tile(fac, res), f"{f['code']} {f['name_pt']} → {r.get('name_pt', res)}"))
    rows = [("FÁBRICAS E MUNIÇÕES", items[:3]), ("", items[3:])] if len(items) > 3 else [("FÁBRICAS E MUNIÇÕES", items)]
    sheet = _sheet(rows, _font(34), _font(18))
    sheet.save(os.path.join(out, "galeria_fabricas_3d.png"))
    return sheet


def _layered_img(d, sub=None, roof=True, pick=None):
    meta = json.load(open(os.path.join(ART, d, "meta.json"), encoding="utf-8"))
    m = CP.layered_part(meta, sub)
    return CP.layered_composite(os.path.join(ART, d), m, pick=pick, roof=roof, paint=PAINT,
                                hide=CP._exclusive_hidden(m))


def tupa_assembled(n_canos=4, roof=True):
    """O Tupa montado como no jogo (boca para cima): ponta 3x4 em cima, n canos 3x3, carregador 5x5 embaixo (os
    canos encaixam nos quadros x 1..4 do carregador). Niveis cheios (carga/trilhos no maximo)."""
    if not all(_has(x) for x in ("bs_rail_loader", "bs_rail_barrel", "bs_rail_muzzle")):
        return None

    def full(d):
        meta = json.load(open(os.path.join(ART, d, "meta.json"), encoding="utf-8"))
        return {n: len(e["files"]) - 1 for n, e in meta["layers"].items() if "levels" in e}
    mz = _layered_img("bs_rail_muzzle", roof=roof, pick=full("bs_rail_muzzle"))
    br = _layered_img("bs_rail_barrel", roof=roof, pick=full("bs_rail_barrel"))
    ld = _layered_img("bs_rail_loader", roof=roof, pick=full("bs_rail_loader"))
    W = ld.width
    H = mz.height + n_canos * br.height + ld.height
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = 64
    img.alpha_composite(mz, (x, 0))
    for i in range(n_canos):
        img.alpha_composite(br, (x, mz.height + i * br.height))
    img.alpha_composite(ld, (0, mz.height + n_canos * br.height))
    return img


def _on_hull(img):
    bg = CP.hull_tiles(img.width + 64, img.height + 64, PAINT)
    bg.alpha_composite(img, (32, 32))
    return bg


def layered_gallery(out=OUT):
    rows = []
    # niveis no maximo (tupa_assembled): o rotulo diz, como o railgun_montado.png aprovado
    tu = [(tupa_assembled(4, roof=False), "Tupã: interior · carga cheia"),
          (tupa_assembled(4, roof=True), "Tupã: com teto · carga cheia")]
    tu = [(_on_hull(im), lab) for im, lab in tu if im is not None]
    if tu:
        rows.append(("RAILGUN TUPÃ (CARREGADOR 5x5 + 4 CANOS + PONTA)", tu))
    pa = []
    pdir = D.PAIOL_ART["dir"]
    if _has(pdir):
        meta = json.load(open(os.path.join(ART, pdir, "meta.json"), encoding="utf-8"))
        for sub in sorted(meta.get("parts") or {}):
            m = meta["parts"][sub]
            fams = (m.get("layers", {}).get("roof") or {}).get("variants") or [None]
            for i, fam in enumerate(fams):
                # placa de tipo (1o tipo da familia) entra pelo layered_composite; digitos ficam fora (switch
                # paiol_counter desligado nos builds), como no logistica_paiois.png aprovado
                img = _layered_img(pdir, sub, roof=True, pick={"roof": i, "gauge": i * 2})
                pf = ((m.get("plate") or {}).get("files") or {}).get(fam) or []
                tp = f" · placa {pf[0][6:-4].upper().replace('_', ' ')}" if pf else ""
                pa.append((_on_hull(img), f"{sub} {FAMILIAS.get(fam, fam)}{tp}"))
    if pa:
        rows.append(("PAIÓIS (1x1, 2x2, 3x3 x FAMÍLIA)", pa[:6]))
        rows.append(("", pa[6:]))
    fi = []
    if _has("bs_fita"):
        fi.append((_on_hull(_layered_img("bs_fita", roof=True)), "Fita"))
        fi.append((_on_hull(_layered_img("bs_fita", roof=False)), "Fita: interior"))
    if fi:
        rows.append(("FITA DE ALIMENTAÇÃO", fi))
    rows = [(t, [(im.resize((im.width * K, im.height * K), Image.NEAREST), lab) for im, lab in items])
            for t, items in rows]
    sheet = _sheet(rows, _font(30), _font(18))
    sheet.save(os.path.join(out, "galeria_layered_3d.png"))
    return sheet


def main(argv):
    out = OUT
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
        argv = [a for a in argv if a not in ("--out", out)]
    os.makedirs(out, exist_ok=True)
    fns = {"armas": weapons_gallery, "fabricas": factories_gallery, "layered": layered_gallery}
    want = [a for a in argv if a in fns] or list(fns)
    for k in want:
        s = fns[k](out)
        print(fns[k].__name__, s.size, os.path.join(out, f"galeria_{k}_3d.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
