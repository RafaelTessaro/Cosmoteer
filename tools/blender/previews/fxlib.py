"""Biblioteca de desenho dos mocks de calibre (PIL + numpy). Texturas do jogo lidas de $COSMOTEER_DATA (game_tex.py).

Tudo em quadros de jogo (1 quadro = P px). Desenho sobre uma tela float (aditivo de verdade para luz/brilho).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# copia no repositorio (ADDENDUM G13): caminhos relativos a esta pasta (tools/blender/previews/)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ART = os.path.join(REPO, "art3d")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "blender"))
import compose_preview as CP  # noqa: E402  (so le os PNGs da arte aprovada)
import game_tex  # noqa: E402  (texturas do jogo pelo nome, nunca commitadas)

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONTS = {}


def font(sz, bold=False):
    k = (sz, bold)
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(FB if bold else F, sz)
    return _FONTS[k]


_TEX = {}


def tex(name):
    if name not in _TEX:
        _TEX[name] = Image.open(game_tex.find(name)).convert("RGBA")
    return _TEX[name]


def additive_to_rgba(img):
    """Textura de fundo preto (aditiva) -> RGBA com alfa = brilho."""
    a = np.asarray(img, dtype=np.float32)
    lum = a[..., :3].max(axis=2)
    out = np.zeros_like(a)
    nz = lum > 0
    out[..., :3][nz] = a[..., :3][nz] / lum[nz][:, None] * 255
    out[..., 3] = lum
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def cell(name, fw, fh, per_row, i, additive=False):
    im = tex(name)
    x, y = (i % per_row) * fw, (i // per_row) * fh
    c = im.crop((x, y, x + fw, y + fh))
    return additive_to_rgba(c) if additive else c


def tint(img, rgb, k=1.0):
    a = np.asarray(img, dtype=np.float32).copy()
    for i in range(3):
        a[..., i] *= rgb[i] / 255.0 * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def fade(img, k):
    a = np.asarray(img, dtype=np.float32).copy()
    a[..., 3] *= k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def fit(img, w, h, rot=0.0):
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    im = img.resize((w, h), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    return im


class Canvas:
    def __init__(self, w, h, bg=(9, 11, 17)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 3), np.float32)
        self.a[:] = bg

    def _box(self, img, cx, cy):
        x0, y0 = int(round(cx - img.width / 2)), int(round(cy - img.height / 2))
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + img.width), min(self.h, y0 + img.height)
        if X1 <= X0 or Y1 <= Y0:
            return None
        s = np.asarray(img, dtype=np.float32)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        return X0, Y0, X1, Y1, s

    def add(self, img, cx, cy, gain=1.0):
        b = self._box(img, cx, cy)
        if not b:
            return
        X0, Y0, X1, Y1, s = b
        self.a[Y0:Y1, X0:X1] += s[..., :3] * (s[..., 3:4] / 255.0) * gain

    def over(self, img, cx, cy, opacity=1.0):
        b = self._box(img, cx, cy)
        if not b:
            return
        X0, Y0, X1, Y1, s = b
        al = s[..., 3:4] / 255.0 * opacity
        self.a[Y0:Y1, X0:X1] = self.a[Y0:Y1, X0:X1] * (1 - al) + s[..., :3] * al

    def rect(self, x0, y0, x1, y1, col):
        self.a[max(0, y0):y1, max(0, x0):x1] = col

    def image(self):
        return Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8), "RGB")

    def paste_image(self, im, x, y):
        a = np.asarray(im.convert("RGB"), dtype=np.float32)
        self.a[y:y + a.shape[0], x:x + a.shape[1]] = a


def hull(cv, x0, y0, wt, ht, P, col=(52, 62, 80), line=(34, 41, 54)):
    """Pedaco de casco em quadros de 1 m (como o fundo dos mocks dos misseis)."""
    w, h = int(wt * P), int(ht * P)
    cv.rect(x0, y0, x0 + w, y0 + h, col)
    for i in range(int(wt) + 1):
        x = x0 + int(i * P)
        cv.rect(x - 1, y0, x + 1, y0 + h, line)
    for j in range(int(ht) + 1):
        y = y0 + int(j * P)
        cv.rect(x0, y - 1, x0 + w, y + 1, line)


def stars(cv, n=160, seed=3):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = int(rng.integers(0, cv.w)), int(rng.integers(0, cv.h))
        v = float(rng.uniform(40, 120))
        cv.a[y, x] = np.maximum(cv.a[y, x], v)


# ----------------------------------------------------------------------------- sprites basicos
def blob(wpx, hpx, rgb, rot=0.0):
    return tint(fit(tex("blob.png"), wpx, hpx, rot), rgb)


def spark_img(px, rgb):
    return tint(fit(tex("spark.png"), px, px), rgb)


def smoke_puff(px, seed, grey=150, alpha=0.5):
    i = seed % 8
    c = cell("smoke.png", 256, 256, 2, i)
    c = tint(c, (grey, grey, grey))
    return fade(fit(c, px, px, rot=(seed * 47) % 360), alpha)


# ----------------------------------------------------------------------------- granadas (texturas propostas)
def shell_sprite(Lpx, Wpx, kind="he", band=(255, 190, 60), body=(92, 98, 104), nuke=False, pulse=1.0):
    """Mock da textura proposta bs_shell_*.png (nariz para +x), desenhada a 4x e reduzida."""
    S = 4
    L, W = max(8, int(Lpx * S)), max(4, int(Wpx * S))
    im = Image.new("RGBA", (L, W), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    r = W / 2
    cy = W / 2
    nose = {"he": 0.32, "ap": 0.42, "nuke": 0.30}[kind]
    tail = 0.10
    xb = L * tail
    xn = L * (1 - nose)
    pts = [(xb, cy - r * 0.86), (L * 0.16, cy - r), (xn, cy - r)]
    steps = 16
    for i in range(1, steps + 1):
        t = i / steps
        if kind == "ap":
            yy = r * (1 - t) ** 1.35
        else:
            yy = r * math.sqrt(max(0.0, 1 - t ** 1.8))
        tipx = xn + (L - 1 - xn) * t
        if kind == "he" and t > 0.88:
            yy = max(yy, r * 0.22)          # espoleta rombuda
        if kind == "nuke" and t > 0.9:
            yy = max(yy, r * 0.28)
        pts.append((tipx, cy - yy))
    lower = [(x, 2 * cy - y) for x, y in reversed(pts)]
    poly = pts + lower + [(0, cy + r * 0.62), (0, cy - r * 0.62)]
    base = body if not nuke else (196, 200, 204)
    dr.polygon(poly, fill=base + (255,))
    # sombreamento cilindrico (luz de cima)
    a = np.asarray(im, dtype=np.float32)
    ys = (np.arange(W)[:, None] - cy) / r
    shade = np.clip(1.25 - 0.55 * (ys + 0.35) ** 2 - 0.35 * ys, 0.35, 1.45)
    a[..., :3] *= shade[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    dr = ImageDraw.Draw(im)
    # cinta de cobre perto da base
    bx = L * 0.2
    dr.rectangle((bx, cy - r * 1.02, bx + L * 0.05, cy + r * 1.02), fill=(184, 104, 52, 255))
    dr.rectangle((bx, cy - r * 1.02, bx + L * 0.05, cy - r * 0.7), fill=(226, 150, 92, 255))
    if not nuke:
        # faixa pintada da municao na ogiva
        fx = xn - L * 0.02
        dr.rectangle((fx, cy - r * 0.97, fx + L * 0.05, cy + r * 0.97), fill=tuple(band) + (255,))
        if kind == "ap":
            # capuz balistico escuro
            dr.polygon([(L * 0.86, cy - r * 0.42), (L - 1, cy), (L * 0.86, cy + r * 0.42)], fill=(40, 42, 46, 255))
    else:
        g = tuple(int(min(255, c * pulse)) for c in (110, 255, 70))
        for fx in (0.36, 0.5):
            dr.rectangle((L * fx, cy - r * 1.0, L * (fx + 0.045), cy + r * 1.0), fill=g + (255,))
        # listras amarelo/preto antes da ogiva
        x0 = xn - L * 0.1
        for k in range(6):
            col = (240, 200, 30, 255) if k % 2 == 0 else (25, 25, 25, 255)
            dr.rectangle((x0 + k * L * 0.014, cy - r * 0.98, x0 + (k + 1) * L * 0.014, cy + r * 0.98), fill=col)
        # trevo preto num disco amarelo na ogiva (simbolo de radiacao)
        d = r * 1.15
        x0d = int(xn + L * 0.035)
        dr.ellipse((x0d, cy - d / 2, x0d + d, cy + d / 2), fill=(250, 210, 40, 255))
        tre = tint(additive_to_rgba(fit(tex("radiation_small.png"), d * 0.9, d * 0.9)), (20, 20, 20))
        im.alpha_composite(tre, (int(x0d + d * 0.05), int(cy - d * 0.45)))
    # base escura (tracante fica atras)
    dr.rectangle((0, cy - r * 0.62, L * 0.025, cy + r * 0.62), fill=(40, 40, 44, 255))
    return im.resize((max(1, int(Lpx)), max(1, int(Wpx))), Image.LANCZOS)


def sabot_sprite(px, frame=4):
    return fit(cell("bullet_large.png", 256, 256, 4, frame), px, px)


# ----------------------------------------------------------------------------- efeitos de boca
def draw_muzzle_item(cv, src, s, mx, my, P, opts=None, seed=0, breech=None, oc=False, age=0.0):
    """Um item (fonte vanilla, escala) do bloco de boca, na boca (mx,my), atirando para +x."""
    o = opts or {}
    n = o.get("n", 1.0)
    rng = np.random.default_rng(seed)
    if o.get("at") == "breech" and breech is not None:
        mx, my = breech
    if src == "CD":
        w, h = 9 * s * P, 4.5 * s * P
        fr = int(min(40, 4 + age * 48))
        fl = fit(cell("cannon_shoot_large.png", 256, 128, 4, fr), w, h)
        cx = mx + (0.5 - 0.06) * w + age * 2 * s * P
        cv.over(fl, cx, my, 0.9 * (1 - age) ** 0.5)
        cv.add(fl, cx, my, 0.22 * (1 - age))
    elif src == "CDF":
        cv.add(blob(3 * s * P * 3.2, 1.5 * s * P * 3.2, (255, 170, 80)), mx + 0.6 * s * P, my, 0.22)
        cv.add(blob(3 * s * P * 0.7, 1.5 * s * P * 0.6, (255, 240, 200)), mx + 0.4 * s * P, my, 0.9)
    elif src == "RADF":
        r = fit(tex("radiation.png"), 10 * s * P, 10 * s * P)
        cv.add(tint(additive_to_rgba(r), (110, 255, 70)), mx - 1.5 * P, my, 0.55)
    elif src == "CDR":
        k = max(4, int(30 * n * (0.5 if s < 0.5 else 1)))
        for i in range(k):
            ang = rng.normal(0, 12)
            d = rng.uniform(0.2, 2.6) * s * P
            x = mx + d * math.cos(math.radians(ang))
            y = my + d * math.sin(math.radians(ang)) * 1.4
            sz = rng.uniform(0.35, 0.8) * s * P
            cv.add(blob(sz * 2.2, sz * 0.7, (255, 150, 60), rot=-ang), x, y, 0.7)
    elif src == "CDS":
        k = max(3, int(10 * n))
        spread = (2.2 if o.get("at") != "breech" else 0.9) * s * P * o.get("speed", 1.0) ** 0.3
        lifek = o.get("life", 1.0)
        for i in range(k):
            ang = rng.uniform(0, 360)
            d = rng.uniform(0.3, 1.0) * spread
            x = mx + d * math.cos(math.radians(ang)) + (0.8 * s * P if o.get("at") != "breech" else 0)
            y = my + d * math.sin(math.radians(ang))
            px = 1.5 * s * P * rng.uniform(1.0, 2.0) * (1.6 if lifek > 1.5 else 1.2)
            cv.over(smoke_puff(px, seed + i, grey=150, alpha=0.32 if lifek <= 1.5 else 0.42), x, y)
    elif src == "RGD":
        w, h = 3.0 * s * P * 1.4, 3.0 * s * P
        ring = Image.new("RGBA", (int(w) + 4, int(h) + 4), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((2, 2, w, h), outline=(200, 215, 235, 110), width=max(1, int(0.12 * s * P)))
        ring = ring.filter(ImageFilter.GaussianBlur(max(1, 0.06 * s * P)))
        cv.add(ring, mx + 0.9 * s * P, my, 0.9)
    elif src == "CG":
        w = 1.0 * s * P * 3.0
        fl = fit(cell("chaingun_shoot.png", 128, 128, 4, 1, additive=True), w, w * 0.85)
        cv.add(fl, mx + 0.32 * w, my, 1.5)
    elif src == "CGF":
        cv.add(blob(5 * s * P, 5 * s * P, (255, 190, 110)), mx, my, 0.18)
        cv.add(blob(0.9 * s * P, 0.9 * s * P, (255, 245, 220)), mx + 0.1 * s * P, my, 0.8)
    elif src == "CGS":
        x = mx - 0.45 * s * P if o.get("at") != "breech" else mx
        cv.over(smoke_puff(3.0 * s * P, seed + 7, grey=170, alpha=0.38), x + 0.3 * s * P, my)
    elif src == "FF":
        cv.add(blob(5 * s * P, 5 * s * P, (255, 200, 140)), mx, my, 0.2)
        cv.add(blob(1.1 * s * P, 0.8 * s * P, (255, 240, 210)), mx + 0.2 * s * P, my, 0.9)
    elif src == "FS":
        for i in range(5):
            cv.over(smoke_puff(2.0 * s * P, seed + i, grey=120, alpha=0.35),
                    mx + rng.uniform(0, 1.5) * s * P, my + rng.uniform(-0.8, 0.8) * s * P)


def draw_muzzle(cv, items, mx, my, P, seed=0, breech=None, age=0.0):
    order = {"CDS": 0, "CGS": 0, "FS": 0, "RGD": 1, "CD": 2, "CG": 2, "CDR": 3, "CDF": 4, "CGF": 4, "FF": 4, "RADF": 5}
    for it in sorted(items, key=lambda t: order.get(t[0], 9)):
        src, s = it[0], it[1]
        opts = it[2] if len(it) > 2 else None
        if age > 0.3 and src in ("CDF", "CGF", "FF", "RADF", "CDR", "RGD"):
            continue
        draw_muzzle_item(cv, src, s, mx, my, P, opts, seed=seed + sum(map(ord, src)), breech=breech, age=age)


# ----------------------------------------------------------------------------- torres
def turret(short, P, n_barrel_frame=None):
    """Torre + canos (arte aprovada) apontando para +x na escala P px/quadro. Retorna (img, bocas, culatras)."""
    d = os.path.join(ART, short)
    import json
    meta = json.load(open(os.path.join(d, "meta.json")))
    br = meta["barrel"]
    bf = [br["rest"]] * len(br["ys"])
    lay = CP.turret_layer(d, meta, bf)
    lay = lay.rotate(-90, resample=Image.BICUBIC, expand=False)
    k = P / 64.0
    lay = lay.resize((max(1, int(lay.width * k)), max(1, int(lay.height * k))), Image.LANCZOS)
    c = lay.width / 2
    muzzles = [(c + br["muzzle"] * P, c + y * P) for y in br["ys"]]
    breeches = [(c + br["root"] * P, c + y * P) for y in br["ys"]]
    return lay, muzzles, breeches, meta


# ----------------------------------------------------------------------------- projeteis
def draw_tracer(cv, x, y, P, pr, colors, gain=1.0):
    """Risco + nucleo + (cabeca) + (borrao) + brilho; cabeca do projetil em (x,y), voando para +x."""
    L, W = pr["streak"]
    cl, cw = pr["core"]
    gl, gw = pr["glow"]
    cv.add(blob(gl * P, gw * P, colors["glow"]), x - 0.4 * L * P, y, 0.22 * gain)
    if pr.get("smear"):
        sl, sw = pr["smear"]["wh"]
        cv.add(blob(sl * P, max(2, sw * P * 2.2), colors["tracer"]), x - 0.55 * sl * P, y, pr["smear"]["alpha"] * gain)
    cv.add(blob(L * P, max(2.0, W * P * 2.2), colors["tracer"]), x - 0.4375 * L * P, y, 1.25 * gain)
    cv.add(blob(cl * P, max(1.5, cw * P * 2.2), colors["core"]), x - 0.35 * cl * P, y, 1.6 * gain)
    if pr.get("head"):
        h = pr["head"] * P
        cv.add(blob(h * 1.6, h * 1.6, (255, 250, 235)), x, y, 1.5 * gain)


def draw_trail_puffs(cv, x, y, P, length, width, rgb, n=14, gain=0.7):
    for i in range(n):
        t = i / (n - 1)
        px = x - t * length * P
        w = width * P * (1 - 0.6 * t)
        cv.add(blob(w * 2.2, w * 1.3, rgb), px, y, gain * (1 - t) ** 1.4)


def draw_smoke_wake(cv, x, y, P, length, size, n=18, grey=120, alpha=0.32, seed=5, tintg=None):
    rng = np.random.default_rng(seed)
    for i in range(n):
        t = i / (n - 1)
        px = x - (0.6 + t * length) * P
        s = size * P * (0.7 + 0.8 * t)
        im = smoke_puff(s, seed + i, grey=grey, alpha=alpha * (1 - t) ** 0.8)
        if tintg:
            im = tint(im, tintg)
        cv.over(im, px, y + rng.normal(0, 0.15 * size * P))


def draw_shell(cv, x, y, P, pr, colors, kind="he", nuke=False, frame=0, spin=0.0):
    L, W = pr["body"]
    tl, tw = pr["tracer"]
    gl, gw = pr["glow"]
    tr = pr.get("trail") or {}
    trail_len = pr.get("trail_len", 4)
    tcol = colors["tracer"] if not nuke else (140, 255, 90)
    # brilho IsLight (fraco sobre o espaco)
    cv.add(blob(gl * P, gw * P, colors["glow"]), x - 0.45 * L * P, y, 0.14 if not nuke else 0.2)
    if pr.get("smoke_trail"):
        st = pr["smoke_trail"]
        draw_smoke_wake(cv, x - 0.5 * L * P, y, P, 14 if not nuke else 11, (st["scale"][0] + st["scale"][1]) / 2 * 0.55,
                        grey=110 if not nuke else 95, tintg=(170, 220, 160) if nuke else None)
    draw_trail_puffs(cv, x - 0.6 * L * P, y, P, trail_len, max(0.25, W * 0.8), tcol, n=18, gain=0.6)
    if nuke:
        big = pr["spin_big"]
        r = fit(tex("radiation.png"), big["size"] * P, big["size"] * P, rot=spin)
        cv.add(tint(additive_to_rgba(r), (110, 255, 70)), x - 0.1 * L * P, y, 0.35)
    # tracante na base (cor da municao)
    cv.add(blob(tl * P, tw * P * 1.4, tcol), x - 0.55 * L * P - 0.4375 * tl * P, y, 1.2)
    cv.add(blob(tl * P * 0.45, tw * P * 0.8, (255, 250, 230) if not nuke else (225, 255, 210)),
           x - 0.55 * L * P - 0.1 * tl * P, y, 1.2)
    pulse = 1.0 if not nuke else (0.75 + 0.35 * math.sin(frame * 1.6))
    sh = shell_sprite(L * P, W * P, kind="nuke" if nuke else kind, band=colors.get("band", (255, 190, 60)),
                      nuke=nuke, pulse=pulse)
    cv.over(sh, x - 0.5 * L * P, y)
    if nuke:
        cv.add(blob(L * P * 0.5, W * P * 1.6, (110, 255, 70)), x - 0.43 * L * P, y, 0.45 * pulse)
        sm = pr["spin_small"]
        tre = fit(tex("radiation_small.png"), sm["size"] * P, sm["size"] * P, rot=spin * 2)
        cv.add(tint(additive_to_rgba(tre), (120, 255, 70)), x - 0.25 * L * P, y, 0.9)


# ----------------------------------------------------------------------------- impactos
def _sparks(cv, x, y, P, n, length, rgb, seed, cone=(100, 260), gain=0.9, speed=1.0):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        ang = rng.uniform(*cone)
        d = rng.uniform(0.2, 1.0) * length * P * speed
        sx = x + d * math.cos(math.radians(ang))
        sy = y + d * math.sin(math.radians(ang))
        ln = rng.uniform(0.4, 1.0) * length * P * 0.35
        cv.add(blob(max(2, ln), max(1.5, ln * 0.18), rgb, rot=-ang), sx, sy, gain)


def _fireball(cv, x, y, quad_px, frame=6, gain_add=0.45):
    im = fit(cell("missile_he_hit.png", 256, 256, 4, frame), quad_px, quad_px)
    cv.over(im, x, y, 0.92)
    cv.add(im, x, y, gain_add * 0.5)


def _hitpuff(cv, x, y, quad_px, frame=4):
    im = fit(cell("bullet_hit_large.png", 256, 256, 4, frame), quad_px, quad_px)
    cv.over(im, x, y, 0.95)
    cv.add(im, x, y, 0.3)


def _spray(cv, x, y, px, seed=0):
    im = fit(cell("chaingun_hit.png", 256, 256, 4, seed % 3, additive=True), px, px, rot=180)
    cv.add(im, x - px * 0.18, y, 1.2)


def _smoke_cloud(cv, x, y, P, n, size, spread, seed, grey=110, alpha=0.4):
    rng = np.random.default_rng(seed)
    for i in range(n):
        cv.over(smoke_puff(size * P * rng.uniform(0.7, 1.3), seed + i, grey=grey, alpha=alpha),
                x + rng.normal(0, spread * P) - 0.3 * spread * P, y + rng.normal(0, spread * P))


def _debris(cv, x, y, P, n, dist, seed):
    rng = np.random.default_rng(seed)
    deb = tex("debris.png")
    for i in range(n):
        ang = rng.uniform(100, 260)
        d = rng.uniform(0.5, 1.0) * dist * P
        s = rng.uniform(0.25, 0.5) * P
        c = deb.crop(((i % 4) * 64, ((i // 4) % 4) * 64, (i % 4) * 64 + 64, ((i // 4) % 4) * 64 + 64))
        cv.over(fit(c, s, s, rot=rng.uniform(0, 360)), x + d * math.cos(math.radians(ang)),
                y + d * math.sin(math.radians(ang)))


def _ring(cv, x, y, rpx, rgb, width, alpha=0.6, blur=1.5):
    s = int(rpx * 2 + width * 4 + 4)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    c = s / 2
    ImageDraw.Draw(im).ellipse((c - rpx, c - rpx, c + rpx, c + rpx), outline=tuple(rgb) + (int(255 * alpha),),
                               width=max(1, int(width)))
    im = im.filter(ImageFilter.GaussianBlur(blur))
    cv.add(im, x, y, 1.0)


def draw_hit(cv, preset, mes, x, y, P, seed=0, tracer=(255, 170, 60)):
    """Impacto (ponto de acerto na borda do casco em x,y; projetil veio da esquerda)."""
    m = mes
    if preset in ("MG", "SH_MG"):
        _sparks(cv, x, y, P, 4, 1.2 * m, (255, 220, 150), seed, gain=1.0)
        cv.add(blob(5 * m * P * 0.6, 5 * m * P * 0.6, (255, 200, 130)), x, y, 0.16)
        cv.add(blob(0.5 * m * P, 0.5 * m * P, (255, 245, 220)), x, y, 0.9)
    elif preset == "MGH":
        _spray(cv, x, y, 1.6 * m * P, seed)
        _sparks(cv, x, y, P, 5, 1.4 * m, (255, 220, 150), seed, gain=1.0)
        cv.add(blob(3 * m * P, 3 * m * P, (255, 200, 130)), x, y, 0.18)
    elif preset in ("AC", "AC_FAST", "SH_AC"):
        if preset != "SH_AC":
            _spray(cv, x, y, 2.0 * m * P, seed)
        _sparks(cv, x, y, P, 12 if preset == "AC" else 5, 1.6 * m, (255, 210, 140), seed, gain=0.9)
        cv.add(blob(5 * m * P * 0.6, 5 * m * P * 0.6, (255, 190, 120)), x, y, 0.2)
        cv.add(blob(0.8 * m * P, 0.8 * m * P, (255, 240, 210)), x, y, 0.9)
    elif preset == "HE_POP":
        _fireball(cv, x - 0.2 * P * m, y, 3 * m * P, frame=5)
        cv.add(blob(1.2 * m * P, 1.2 * m * P, (255, 230, 180)), x, y, 0.8)
    elif preset in ("L", "D"):
        base = 3.0 if preset == "L" else 4.5
        bs = 1.0 if preset == "L" else 1.5
        _smoke_cloud(cv, x - 0.3 * base * m * P, y, P, 7, 1.6 * bs * m, 0.5 * bs * m, seed, grey=120, alpha=0.35)
        _hitpuff(cv, x - 0.05 * base * m * P, y, base * m * P, frame=5)
        _sparks(cv, x, y, P, 18, 2.0 * bs * m, (255, 200, 130), seed + 1, gain=0.8)
        cv.add(blob(7 * bs * m * P * 0.55, 7 * bs * m * P * 0.55, (255, 180, 110)), x, y, 0.2)
    elif preset in ("SH_L", "SH_D"):
        bs = 1.0 if preset == "SH_L" else 1.5
        _sparks(cv, x, y, P, 16, 2.0 * bs * m, (255, 220, 170), seed + 1, gain=0.8)
        cv.add(blob(7 * bs * m * P * 0.4, 7 * bs * m * P * 0.4, (255, 220, 170)), x, y, 0.35)
        _ring(cv, x, y, 1.3 * 9 * m * 0.12 * P * bs, (190, 210, 255), 0.08 * P * m * bs + 1, alpha=0.5)
    elif preset in ("HE", "HE_BIG", "SH_HE"):
        q = 8.5 * m * P
        if preset != "SH_HE":
            _smoke_cloud(cv, x - 0.4 * q, y, P, 10, 3.2 * m, 1.1 * m, seed, grey=95, alpha=0.4)
        _fireball(cv, x - 0.1 * q, y, q, frame=7, gain_add=0.35)
        cv.add(blob(q * 1.1, q * 1.1, (255, 170, 90)), x - 0.1 * q, y, 0.22)
        if preset == "HE_BIG":
            _debris(cv, x - 0.1 * q, y, P, 14, 4.5 * m, seed)
            _ring(cv, x - 0.1 * q, y, q * 0.62, (220, 225, 240), 0.1 * P, alpha=0.35, blur=3)
    elif preset in ("EMP", "EMP_FAST"):
        cv.add(blob(2.6 * m * P, 2.6 * m * P, (80, 150, 255)), x - 0.3 * m * P, y, 0.9)
        cv.add(blob(1.0 * m * P, 1.0 * m * P, (220, 235, 255)), x - 0.3 * m * P, y, 1.0)
        if preset == "EMP":
            rng = np.random.default_rng(seed)
            for _ in range(6):
                img = Image.new("RGBA", (int(4 * m * P) + 4, int(4 * m * P) + 4), (0, 0, 0, 0))
                dr = ImageDraw.Draw(img)
                c = img.width / 2
                pts = [(c, c)]
                ang = rng.uniform(0, 2 * math.pi)
                for k in range(5):
                    rr = (k + 1) * 0.35 * m * P
                    ang += rng.normal(0, 0.5)
                    pts.append((c + rr * math.cos(ang), c + rr * math.sin(ang)))
                dr.line(pts, fill=(150, 200, 255, 230), width=max(1, int(0.06 * m * P)))
                cv.add(img.filter(ImageFilter.GaussianBlur(1)), x - 0.3 * m * P, y, 1.0)
    elif preset in ("NUKE", "NUKE_V"):
        q = 10 * m * P
        cx = x - 0.05 * q
        cv.add(blob(q * 4.0, q * 4.0, (255, 245, 225)), cx, y, 0.32)        # clarao (20 quadros x MES)
        _ring(cv, cx, y, q * 1.25, (230, 235, 255), 0.14 * P, alpha=0.45, blur=6)   # onda de choque
        if preset == "NUKE":
            cv.add(blob(q * 2.6, q * 2.6, (110, 255, 70)), cx, y, 0.28)     # brilho residual verde
            _ring(cv, cx, y, q * 0.9, (110, 255, 70), 0.22 * P, alpha=0.8, blur=4)  # anel verde
        im = fit(cell("missile_nuke_hit.png", 256, 256, 4, 8), q, q)
        cv.over(im, cx, y, 0.95)
        cv.add(im, cx, y, 0.3)
    elif preset in ("FLAK_L", "FLAK_H"):
        q = 4 * m * P
        _smoke_cloud(cv, x, y, P, 6, 2.2 * m, 0.6 * m, seed, grey=70, alpha=0.45)
        cv.add(blob(q * 1.4, q * 1.4, (255, 170, 90)), x, y, 0.35)
        cv.add(blob(q * 0.35, q * 0.35, (255, 240, 210)), x, y, 1.0)
        nsh = 34 if preset == "FLAK_L" else 110
        rng = np.random.default_rng(seed)
        for _ in range(nsh):
            ang = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(0.2, 1.0) * q * 0.75
            cv.add(blob(3, 3, (255, 200, 120)), x + d * math.cos(ang), y + d * math.sin(ang), 0.9)


def label(img, x, y, text, sz=13, col=(220, 225, 235), bold=False):
    ImageDraw.Draw(img).text((x, y), text, fill=col, font=font(sz, bold))
