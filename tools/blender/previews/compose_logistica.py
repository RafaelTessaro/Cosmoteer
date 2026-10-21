"""Montagem das pecas da logistica 2.0 como no jogo (camadas na ordem do jogo, teto pintado) para as previas.

So le PNGs (art3d/ ou uma pasta de rascunho); nao usa bpy. Funcoes:
  paiol(n, fam, level, kind, ...)  paiol montado (piso, paredes, teto pintado, medidor, placa, digitos)
  fita(...)                         a Fita (teto/piso, luz verde)
  hull_field / sheet                casco da nave em volta e folha com titulos/legendas em pt-BR
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# copia no repositorio (ADDENDUM G13): caminhos relativos a esta pasta (tools/blender/previews/)
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ART = os.path.join(REPO, "art3d")
PX = 64
BG = (7, 9, 14)
PAINT = (46, 58, 74)
WHITE = (232, 234, 238)
GOLD = (255, 196, 70)
TEXT = (220, 226, 236)
DIM = (150, 160, 176)
NEWC = (120, 200, 255)
GREENC = (120, 235, 110)
_C = {}


def font(sz, bold=False):
    p = "/usr/share/fonts/opentype/inter/" + ("Inter-Bold.otf" if bold else "Inter-Medium.otf")
    return ImageFont.truetype(p, sz)


def load(d, name):
    k = os.path.join(d, name)
    if k not in _C:
        _C[k] = Image.open(k).convert("RGBA")
    return _C[k].copy()


def paint_roof(img, paint):
    """O jogo troca o verde puro pela pintura (mesmo teste do shader: verde acima de r/b e |r - b| < 64)."""
    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = np.clip((g - np.maximum(r, b) - 8) / 40.0, 0, 1) * (np.abs(r - b) < 64)
    lum = g / 217.0
    out = a.copy()
    for i in range(3):
        out[..., i] = a[..., i] * (1 - mask) + np.clip(paint[i] * lum * 1.05, 0, 255) * mask
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def add_light(base, spr, xy, gain=1.0):
    """Soma aditiva (lights_add: RGB sobre preto) so onde a base ja tem alfa."""
    x, y = xy
    W, H = base.size
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + spr.width), min(H, y + spr.height)
    if x1 <= x0 or y1 <= y0:
        return base
    b = np.asarray(base, dtype=np.float32).copy()
    s = np.asarray(spr, dtype=np.float32)[y0 - y:y1 - y, x0 - x:x1 - x]
    add = s[..., :3] * (s[..., 3:4] / 255.0) * gain
    b[y0:y1, x0:x1, :3] = np.clip(b[y0:y1, x0:x1, :3] + add * (b[y0:y1, x0:x1, 3:4] / 255.0), 0, 255)
    return Image.fromarray(b.astype(np.uint8), "RGBA")


def place(dst, spr, rect, ppt=PX):
    """Desenha spr no retangulo rect (quadros) como o jogo: escalado para rect x ppt."""
    x, y, w, h = rect
    W, H = int(round(w * ppt)), int(round(h * ppt))
    if spr.size != (W, H):
        spr = spr.resize((W, H), Image.LANCZOS)
    dst.alpha_composite(spr, (int(round(x * ppt)), int(round(y * ppt))))


# ============================================================================ paiol
def paiol_meta(root=ART):
    return json.load(open(os.path.join(root, "bs_paiol", "meta.json")))


def paiol(n, fam, level=0, kind=None, paint=PAINT, roof=True, digits=None, root=ART, scale=1):
    """Paiol n (1x1/2x2/3x3) da familia fam; level = nivel do medidor (0 = vazio); kind = placa (padrao: o 1o tipo
    da familia); digits = texto de 4 digitos ou None (switch paiol_counter desligado)."""
    d = os.path.join(root, "bs_paiol")
    m = paiol_meta(root)["parts"][n]
    W, H = m["size"]
    img = Image.new("RGBA", (W * PX, H * PX), (0, 0, 0, 0))
    img.alpha_composite(load(d, m["layers"]["floor"]["files"][0]))
    img.alpha_composite(load(d, m["walls"]))
    if not roof:
        return _scale(img, scale)
    fi = m["layers"]["roof"]["variants"].index(fam)
    img.alpha_composite(paint_roof(load(d, m["layers"]["roof"]["files"][fi]), paint))
    if level > 0:
        g = m["layers"]["gauge"]
        place(img, load(d, g["files"][level - 1]), g["rect"])
    pl = m["plate"]
    kind = kind or pl["files"][fam][0][6:-4]
    place(img, load(os.path.join(root, "bs_placas"), f"placa_{kind}.png"), pl["rect"])
    if digits and m.get("digits"):
        for ch, r in zip(digits.rjust(4), m["digits"]["rects"]):
            if ch != " ":
                place(img, load(d, f"digito{ch}.png"), r)
    return _scale(img, scale)


def _scale(img, scale):
    if scale == 1:
        return img
    return img.resize((img.width * scale, img.height * scale), Image.LANCZOS)


# ============================================================================ fita
def fita(paint=PAINT, linked=True, roof=True, root=ART, scale=1):
    d = os.path.join(root, "bs_fita")
    img = Image.new("RGBA", (PX, PX), (0, 0, 0, 0))
    img.alpha_composite(load(d, "floor.png"))
    if not roof:
        if linked:
            img = add_light(img, load(d, "luz_grudada.png"), (0, 0))
        return _scale(img, scale)
    img.alpha_composite(paint_roof(load(d, "roof.png"), paint))
    if linked:
        img.alpha_composite(load(d, "luz_grudada_teto.png"))
    return _scale(img, scale)


# ============================================================================ casco e folha
def hull_field(w, h, paint, ox=0, oy=0):
    """Casco da nave: placas de 1 quadro na pintura com juntas finas (grade alinhada em ox, oy)."""
    im = Image.new("RGBA", (w, h), tuple(paint) + (255,))
    dr = ImageDraw.Draw(im)
    dark = tuple(int(c * 0.80) for c in paint) + (255,)
    lite = tuple(min(255, int(c * 1.05 + 6)) for c in paint) + (255,)
    for x in range(ox % PX - PX, w, PX):
        dr.line([(x, 0), (x, h)], fill=dark)
        dr.line([(x + 1, 0), (x + 1, h)], fill=lite)
    for y in range(oy % PX - PX, h, PX):
        dr.line([(0, y), (w, y)], fill=dark)
        dr.line([(0, y + 1), (w, y + 1)], fill=lite)
    return im


def on_hull(part, paint, margin=0.5, scale=1):
    """A peca (ja montada a 1x) sobre um pedaco de casco pintado com margem em quadros."""
    m = int(margin * PX)
    W, H = part.width + 2 * m, part.height + 2 * m
    bg = hull_field(W, H, paint, m, m)
    bg.alpha_composite(part, (m, m))
    return _scale(bg, scale)


def on_space(part, pad=8, scale=1):
    bg = Image.new("RGBA", (part.width + 2 * pad, part.height + 2 * pad), BG + (255,))
    bg.alpha_composite(part, (pad, pad))
    return _scale(bg, scale)


def sheet(header, rows, pad=22, cap_font=None, title_font=None, min_w=0):
    """header: [(texto, fonte, cor)]; rows: [(titulo, subtitulo, [(imagem, legenda, cor)])] -> folha com as figuras
    alinhadas pela base e legendas centradas embaixo (mesmo formato das previas armas_*.png)."""
    cap_font = cap_font or font(15)
    title_font = title_font or font(22, True)
    sub_font = font(15)
    dr0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    widths = []
    for _, _, items in rows:
        x = pad
        for im, lab, _ in items:
            tw = max(dr0.textlength(t, font=cap_font) for t in lab.split("\n"))
            x += max(im.width, int(tw)) + pad
        widths.append(x)
    hw = max(int(dr0.textlength(t, font=f)) + 2 * pad for t, f, _ in header)
    W = max(max(widths), hw, min_w)
    H = pad + sum(f.size + 8 for _, f, _ in header) + pad // 2
    for title, sub, items in rows:
        nl = max(len(lab.split("\n")) for _, lab, _ in items)
        H += title_font.size + 10 + (sub_font.size + 8 if sub else 0) + max(im.height for im, _, _ in items) + \
            nl * (cap_font.size + 4) + 8 + pad
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    y = pad
    for t, f, col in header:
        dr.text((pad, y), t, font=f, fill=col)
        y += f.size + 8
    y += pad // 2
    for title, sub, items in rows:
        dr.text((pad, y), title, font=title_font, fill=GOLD)
        y += title_font.size + 10
        if sub:
            dr.text((pad, y), sub, font=sub_font, fill=DIM)
            y += sub_font.size + 8
        rh = max(im.height for im, _, _ in items)
        x = pad
        for im, lab, col in items:
            lines = lab.split("\n")
            tw = int(max(dr.textlength(t, font=cap_font) for t in lines))
            cw = max(im.width, tw)
            img.paste(im.convert("RGB"), (x + (cw - im.width) // 2, y + rh - im.height))
            for k, t in enumerate(lines):
                lw = dr.textlength(t, font=cap_font)
                dr.text((x + (cw - lw) / 2, y + rh + 6 + k * (cap_font.size + 4)), t, font=cap_font, fill=col or TEXT)
            x += cw + pad
        nl = max(len(lab.split("\n")) for _, lab, _ in items)
        y += rh + nl * (cap_font.size + 4) + 8 + pad
    return img


# ============================================================================ cena de nave (camadas do jogo)
GAME = ["structure", "floors", "turrets", "doodads_low", "walls_stencil", "external_walls", "walls", "doors",
        "weapons", "doodads_high", "lights_add", "fire", "roofs", "roof_doodads", "roof_turrets", "roof_lights_fancy"]
ROOF_LAYERS = ("roofs", "roof_doodads", "roof_lights_fancy")


class Scene:
    """Pedaco de nave W x H quadros: casco pintado + pecas em (x, y) de quadro. add_* empilham sprites por camada do
    jogo; render() monta na ordem do jogo (lights_add soma por cima do que esta abaixo do teto)."""

    def __init__(self, W, H, paint=PAINT, hull=None, root=ART):
        self.W, self.H, self.paint, self.root = W, H, paint, root
        self.hull = hull if hull is not None else {(x, y) for x in range(W) for y in range(H)}
        self.st = {g: [] for g in GAME}

    def put(self, layer, img, x, y, mode="alpha"):
        """img com o canto de cima-esquerda em (x, y) quadros (pode ser fracionario)."""
        self.st[layer].append((img, int(round(x * PX)), int(round(y * PX)), mode))

    def put_center(self, layer, img, cx, cy, mode="alpha"):
        self.st[layer].append((img, int(round(cx * PX - img.width / 2)), int(round(cy * PX - img.height / 2)), mode))

    # ---------------------------------------------------------------- pecas
    def add_paiol(self, n, fam, x, y, level=0, kind=None, digits=None):
        d = os.path.join(self.root, "bs_paiol")
        m = paiol_meta(self.root)["parts"][n]
        self.put("floors", load(d, m["layers"]["floor"]["files"][0]), x, y)
        self.put("walls", load(d, m["walls"]), x, y)
        fi = m["layers"]["roof"]["variants"].index(fam)
        self.put("roofs", paint_roof(load(d, m["layers"]["roof"]["files"][fi]), self.paint), x, y)
        if level > 0:
            g = m["layers"]["gauge"]
            gx, gy, gw, gh = g["rect"]
            spr = load(d, g["files"][level - 1]).resize((int(round(gw * PX)), int(round(gh * PX))), Image.LANCZOS)
            self.put("roof_doodads", spr, x + gx, y + gy)
        pl = m["plate"]
        kind = kind or pl["files"][fam][0][6:-4]
        px_, py_, s, _ = pl["rect"]
        self.put("roof_doodads", load(os.path.join(self.root, "bs_placas"), f"placa_{kind}.png").resize(
            (int(round(s * PX)), int(round(s * PX))), Image.LANCZOS), x + px_, y + py_)
        if digits and m.get("digits"):
            for ch, r in zip(digits.rjust(4), m["digits"]["rects"]):
                if ch != " ":
                    self.put("roof_doodads", load(d, f"digito{ch}.png").resize(
                        (int(round(r[2] * PX)), int(round(r[3] * PX))), Image.LANCZOS), x + r[0], y + r[1])
        return m["size"]

    def add_fita(self, x, y, linked=True):
        d = os.path.join(self.root, "bs_fita")
        self.put("floors", load(d, "floor.png"), x, y)
        self.put("roofs", paint_roof(load(d, "roof.png"), self.paint), x, y)
        if linked:
            self.put("lights_add", load(d, "luz_grudada.png"), x, y, "add")
            self.put("roof_doodads", load(d, "luz_grudada_teto.png"), x, y)

    def add_factory(self, short, x, y, frame=0, working=False):
        d = os.path.join(self.root if os.path.exists(os.path.join(self.root, short)) else ART, short)
        m = json.load(open(os.path.join(d, "meta.json")))
        h = m["hull"]
        self.put("floors", load(d, h["floor"]), x, y)
        mf = m["machine"]["frames"][frame % len(m["machine"]["frames"])] if working else m["machine"]["off"]
        self.put("walls", load(d, mf), x, y)
        self.put("walls", load(d, h["walls"]), x, y)
        if working and "lights" in h:
            self.put("lights_add", load(d, h["lights"]), x, y, "add")
        self.put("roofs", paint_roof(load(d, h["roof"]), self.paint), x, y)
        return m["size"]

    def add_gun(self, short, x, y, angle=0.0, bframes=None, fx=None):
        import sys
        sys.path.insert(0, os.path.join(REPO, "tools", "blender"))
        import compose_preview as CP
        d = os.path.join(ART, short)
        m = json.load(open(os.path.join(d, "meta.json")))
        h = m["hull"]
        self.put("floors", load(d, h["floor"]), x, y)
        self.put("walls", load(d, h["walls"]), x, y)
        self.put("lights_add", load(d, h["lights"]), x, y, "add")
        self.put("roofs", paint_roof(load(d, h["roof"]), self.paint), x, y)
        br = m["barrel"]
        lay = CP.turret_layer(d, m, bframes or [br["rest"]] * len(br["ys"]), 0, fx)
        lay = CP.rotate_about_center(lay, angle)
        pvx, pvy = m["pivot"]
        self.put_center("roof_turrets", CP.shadow_of(lay), x + pvx, y + pvy)
        self.put_center("roof_turrets", lay, x + pvx, y + pvy)
        return m

    # ---------------------------------------------------------------- montagem
    def render(self, roof=True, space=BG, margin=0.0):
        m = int(margin * PX)
        img = Image.new("RGBA", (self.W * PX + 2 * m, self.H * PX + 2 * m), space + (255,))
        hull = hull_field(self.W * PX, self.H * PX, self.paint)
        mask = Image.new("L", hull.size, 0)
        dm = ImageDraw.Draw(mask)
        for (tx, ty) in self.hull:
            dm.rectangle([tx * PX, ty * PX, tx * PX + PX - 1, ty * PX + PX - 1], fill=255)
        img.paste(hull, (m, m), mask)
        for g in GAME:
            if not roof and g in ROOF_LAYERS:
                continue
            for spr, x, y, mode in self.st[g]:
                if mode == "add":
                    img = add_light(img, spr, (x + m, y + m))
                else:
                    img.alpha_composite(spr, (x + m, y + m)) if x + m >= 0 and y + m >= 0 else \
                        _paste_clip(img, spr, x + m, y + m)
        return img


def _paste_clip(dst, spr, x, y):
    x0, y0 = max(0, -x), max(0, -y)
    dst.alpha_composite(spr.crop((x0, y0, spr.width, spr.height)), (x + x0, y + y0))
