"""Icones provisorios (PIL 96x96) dos seletores e dos buffs do Bullet Strike 2.0 (dono: WP01).

ensure(out, SPEC) desenha, so quando o arquivo ainda NAO existe no mod, cada icone citado em SPEC.toggles
(gui/ammo_*.png, gui/cell_*.png, gui/missile_*.png), gui/slug_rail.png e gui/buff_fita.png; nunca sobrescreve (os
icones reais vem de art3d/bs_ui_icons2 pelo make_art.misc_art, WP10/WP11). Devolve a lista do que desenhou: o
spec2_check lista e o WP14b exige zero.
"""

import os

from PIL import Image, ImageDraw, ImageFont

SIZE = 96
# icones extras alem dos de SPEC.toggles: rotulo e cor
EXTRA = {"gui/slug_rail.png": ("RAIL", (100, 175, 255)), "gui/buff_fita.png": ("FITA", (110, 230, 120))}


def _font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
              "C:/Windows/Fonts/arialbd.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def draw(label, rgb):
    """Silhueta clara com halo azul (o estilo dos icones de interface do jogo) e o rotulo no meio."""
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, SIZE - 7, SIZE - 7], radius=16, fill=(24, 36, 56, 230), outline=tuple(rgb) + (255,),
                        width=5)
    f = _font(30 if len(label) <= 3 else 22)
    tw, th = d.textbbox((0, 0), label, font=f)[2:]
    d.text(((SIZE - tw) / 2, (SIZE - th) / 2 - 2), label, font=f, fill=(235, 242, 255, 255))
    return im


def wanted(spec):
    """{caminho gui/...png: (rotulo, cor)} de todos os icones que o mod usa."""
    pal = (spec.get("art_assets") or {}).get("palette") or {}
    out = {}
    for tid, t in spec["toggles"].items():
        chs = t.get("choices") if isinstance(t, dict) else None
        if not isinstance(chs, list):
            continue
        for c in chs:
            icon = c.get("icon")
            if not icon:
                continue
            key = c.get("key") or icon.rsplit("/", 1)[-1].split("_", 1)[-1].split(".")[0]
            label = (c.get("label") or c.get("label_ptbr") or key).upper()[:5]
            col = ((pal.get(key) or {}).get("chip") or (pal.get(f"msl_{key}") or {}).get("chip") or [150, 190, 255])
            out[icon] = (label, tuple(col))
    out.update(EXTRA)
    return out


def ensure(out, spec, art2=None):
    """Desenha o que faltar em <mod>/gui/; nunca sobrescreve. spec = SPEC (bullet_strike_spec.json); art2 =
    SPEC.art_assets (paleta, opcional). Devolve [caminhos desenhados]."""
    sp = dict(spec)
    if art2 is not None:
        sp["art_assets"] = art2
    made = []
    for rel, (label, rgb) in sorted(wanted(sp).items()):
        p = os.path.join(out.root, rel)
        if os.path.exists(p):
            continue
        out.image(rel, draw(label, rgb))
        made.append(rel)
    return made
