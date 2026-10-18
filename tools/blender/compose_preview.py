"""Monta as previas de uma arma a partir dos sprites renderizados (so Pillow + numpy).

    python3 tools/blender/compose_preview.py <pasta_sprites> [--paint R,G,B]

Gera na mesma pasta:
    preview_ingame.png  -> peca montada na escala do jogo (64 px/tile) e ampliada 3x
    preview_fire.gif    -> torre girando, 3 disparos ("tum, tum, tum") com recuo, clarao e calor
Lancadores (meta kind "launcher"): o casulo com o rack cheio (1x e 3x) e um GIF com a salva em LIFO tubo a tubo
(o nivel do rack cai uma unidade por lancamento, clarao no tubo e baforada de sopro) e a recarga unidade a unidade.
"""

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PX = 64


def load(d, name):
    return Image.open(os.path.join(d, name)).convert("RGBA")


def paint_roof(img, paint):
    """Simula a pintura da nave: o jogo troca o verde puro do teto pela cor escolhida."""
    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = np.clip((g - np.maximum(r, b) - 8) / 40.0, 0, 1)
    lum = g / 217.0
    out = a.copy()
    for i in range(3):
        out[..., i] = a[..., i] * (1 - mask) + np.clip(paint[i] * lum * 1.05, 0, 255) * mask
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def paste_center(dst, src, cx, cy):
    dst.alpha_composite(src, (int(round(cx - src.width / 2)), int(round(cy - src.height / 2))))


def turret_layer(d, meta, bframes, tframe=0, fx=None):
    """Torre + canos num quadrado centrado no pivo, ainda sem girar.

    bframes: um nome de PNG por cano (quadro atual de cada cano). fx: [(img, x_frente, y_lado, aditivo)]."""
    ts = meta["turret_size"]
    br = meta["barrel"]
    reach = br["root"] + br["length"] + 1.4
    side = int(math.ceil(2 * max(reach, ts / 2) * PX)) + 4
    lay = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    c = side / 2
    tf = meta["turret"]["frames"]
    paste_center(lay, load(d, tf[tframe % len(tf)]), c, c)
    for y, name in zip(br["ys"], bframes):
        paste_center(lay, load(d, name), c + y * PX, c - br["center"] * PX)
    for img, fwd, lat, additive in (fx or []):
        if additive:
            add_center(lay, img, c + lat * PX, c - fwd * PX, gain=1.2)
            paste_center(lay, _fade(img, 0.35), c + lat * PX, c - fwd * PX)
        else:
            paste_center(lay, img, c + lat * PX, c - fwd * PX)
    return lay


def shadow_of(layer, off=6, blur=4, op=0.5):
    a = np.asarray(layer.split()[-1], dtype=np.float32) * op
    sh = Image.fromarray(a.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.putalpha(sh)
    shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shifted.alpha_composite(out, (off, off))
    return shifted


def _flame(dr, cx, cy, L, W, ang_deg, col, steps=24):
    """Chama em gota: base arredondada em (cx,cy), ponta a L de distancia na direcao ang (0 = para cima)."""
    a = math.radians(ang_deg)
    ux, uy = math.sin(a), -math.cos(a)      # eixo da chama
    vx, vy = -uy, ux                         # perpendicular
    pts = []
    for i in range(steps + 1):
        t = i / steps
        hw = W * (1 - t) ** 0.9 * min(1.0, 0.45 + t * 5)
        pts.append((cx + ux * L * t + vx * hw, cy + uy * L * t + vy * hw))
    for i in range(steps, -1, -1):
        t = i / steps
        hw = W * (1 - t) ** 0.9 * min(1.0, 0.45 + t * 5)
        pts.append((cx + ux * L * t - vx * hw, cy + uy * L * t - vy * hw))
    dr.polygon(pts, fill=col)


FIRE_COLS = [(255, 90, 10, 140), (255, 150, 40, 200), (255, 215, 120, 240), (255, 250, 225, 255)]
PLASMA_COLS = [(20, 140, 255, 140), (40, 200, 255, 200), (150, 240, 255, 240), (240, 255, 255, 255)]


def flash(scale, t, seed=0, cols=None):
    """Clarao de boca: lingua de fogo para frente + jatos laterais saindo das fendas do freio de boca."""
    S = 4
    U = PX * scale * S
    w = h = int(3.0 * U)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    k = (1 - t) ** 0.8
    rng = np.random.default_rng(seed)
    cols = cols or FIRE_COLS
    for i, col in enumerate(cols):
        f = 1 - i * 0.2
        _flame(dr, cx, cy, U * (1.35 + 0.3 * rng.random()) * k * f, U * 0.27 * k * f, rng.uniform(-4, 4), col)
        for sx in (-1, 1):
            for j in range(3):  # tres fendas de cada lado
                _flame(dr, cx + sx * U * 0.12, cy + U * (0.10 - j * 0.09), U * (0.55 - j * 0.08) * k * f,
                       U * 0.08 * k * f, sx * (78 + j * 6), col)
    im = im.resize((w // S, h // S), Image.LANCZOS)
    glow = im.filter(ImageFilter.GaussianBlur(7 * scale))
    return Image.alpha_composite(glow, im)


def smoke(scale, t, seed=0):
    S = 2
    w = int(2.4 * PX * scale * S)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    U = PX * scale * S
    for _ in range(9):
        ang = rng.uniform(-1.9, 1.9)
        dist = U * (0.15 + 0.7 * t) * rng.uniform(0.6, 1.2)
        x = w / 2 + math.sin(ang) * dist
        y = w / 2 - math.cos(ang) * dist * 0.9
        r = U * (0.10 + 0.35 * t) * rng.uniform(0.7, 1.2)
        a = int(110 * (1 - t) ** 1.5)
        g = int(rng.uniform(95, 140))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(g, g, g + 6, a))
    im = im.filter(ImageFilter.GaussianBlur(5 * scale * S / 2)).resize((w // S, w // S), Image.LANCZOS)
    return im


def add_center(dst, src, cx, cy, gain=1.0):
    """Mistura aditiva (luz): soma cor*alpha da imagem no destino."""
    x0, y0 = int(round(cx - src.width / 2)), int(round(cy - src.height / 2))
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(dst.width, x0 + src.width), min(dst.height, y0 + src.height)
    if X1 <= X0 or Y1 <= Y0:
        return
    d = np.asarray(dst, dtype=np.float32).copy()
    s_ = np.asarray(src, dtype=np.float32)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    d[Y0:Y1, X0:X1, :3] += s_[..., :3] * (s_[..., 3:4] / 255.0) * gain
    d[Y0:Y1, X0:X1, 3] = np.maximum(d[Y0:Y1, X0:X1, 3], s_[..., 3])
    dst.paste(Image.fromarray(np.clip(d, 0, 255).astype(np.uint8), "RGBA"))


def rotate_about_center(img, deg):
    return img.rotate(deg, resample=Image.BICUBIC, expand=False)


def _fade(img, k):
    a = np.asarray(img, dtype=np.float32).copy()
    a[..., 3] *= k
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def crop_content(img, bg, pad=12):
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    diff = np.abs(a - np.array(bg, dtype=np.int16)).sum(axis=2) > 6
    ys, xs = np.where(diff)
    return img.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(img.width, xs.max() + pad),
                     min(img.height, ys.max() + pad)))


def assemble(d, meta, roof, bframes=None, tframe=0, angle=0.0, fx=None, scale=1, bg=(7, 9, 14)):
    """Monta a peca inteira (teto, sombra, torre, canos, efeitos) num quadro."""
    W, H = meta["size"]
    pvx, pvy = meta["pivot"]
    br = meta["barrel"]
    bframes = bframes or [br["rest"]] * len(br["ys"])
    reach = br["root"] + br["length"] + 1.4
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * PX), int((H + top + 0.4) * PX)
    canvas = Image.new("RGBA", (cw, ch), bg + (255,))
    ox, oy = int(side * PX), int(top * PX)
    canvas.alpha_composite(roof, (ox, oy))
    lay = turret_layer(d, meta, bframes, tframe, fx)
    lay = rotate_about_center(lay, angle)
    px, py = ox + pvx * PX, oy + pvy * PX
    paste_center(canvas, shadow_of(lay), px, py)
    paste_center(canvas, lay, px, py)
    if scale != 1:
        canvas = canvas.resize((cw * scale, ch * scale), Image.LANCZOS)
    return canvas


def _crop_frames(frames, bg=(7, 9, 14)):
    boxes = []
    for f in frames:
        a = np.asarray(f.convert("RGB"), dtype=np.int16)
        ys, xs = np.where(np.abs(a - np.array(bg, dtype=np.int16)).sum(axis=2) > 6)
        boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
    bx = (max(0, min(b[0] for b in boxes) - 16), max(0, min(b[1] for b in boxes) - 16),
          min(frames[0].width, max(b[2] for b in boxes) + 16), min(frames[0].height, max(b[3] for b in boxes) + 16))
    return [f.crop(bx) for f in frames]


def make_all(d, paint=(46, 58, 74), scale=2):
    meta = json.load(open(os.path.join(d, "meta.json")))
    if meta.get("kind") == "launcher":
        return make_all_launcher(d, meta, paint, scale)
    roof = paint_roof(load(d, "roof.png"), paint)
    br = meta["barrel"]
    nb = len(br["ys"])

    # vista do jogo: 1x e 3x lado a lado
    one = crop_content(assemble(d, meta, roof), (7, 9, 14))
    three = one.resize((one.width * 3, one.height * 3), Image.LANCZOS)
    sheet = Image.new("RGBA", (one.width + three.width + 48, three.height + 32), (7, 9, 14, 255))
    sheet.alpha_composite(one, (16, 16 + three.height - one.height))
    sheet.alpha_composite(three, (one.width + 32, 16))
    sheet.convert("RGB").save(os.path.join(d, "preview_ingame.png"))

    # GIF: gira para mirar, dispara, esfria e volta
    pattern = meta.get("preview_pattern", "single")
    seq = br["frames"]                      # ordem do jogo: quadros de tiro ... repouso
    spin = br["anim"] == "spin"
    frames, durs = [], []
    aim = -28.0
    tf = 0
    ntf = len(meta["turret"]["frames"])
    for i in range(10):
        t = (i + 1) / 10
        frames.append(assemble(d, meta, roof, tframe=tf, angle=aim * (1 - math.cos(t * math.pi)) / 2, scale=scale))
        durs.append(40)
        tf += 1 if ntf > 1 else 0
    if pattern in ("single", "volley"):
        groups = [list(range(nb))] * 3
    elif pattern == "pairs":
        half = max(1, nb // 2)
        groups = [[i for i in range(nb) if i % half == k % half] for k in range(6)]
    elif pattern == "rotary":
        groups = [[0]] * 24
    else:  # alternate
        groups = [[k % nb] for k in range(max(4, nb * 2))]
    # canhoes lentos: espera o calor esfriar entre os tiros; rotativos/metralhadoras: rajada rapida
    small = br["sprite_w"] < 0.3 and not spin   # metralhadoras: tiro rapido ("tatata"), nao cadencia de canhao
    gap = max(10, len(seq) + 2) if pattern in ("single", "volley") and not small else (2 if pattern == "rotary" else (3 if small else 4))
    if small and pattern in ("single", "volley"):
        groups = [list(range(nb))] * 10
    # tamanho do clarao/fumaca pelo calibre (largura do sprite do cano; 0.46 = 76 mm)
    fsc = 0.55 if spin else min(2.2, max(0.3, br["sprite_w"] / 0.46))
    plasma = meta.get("preview_fx") == "plasma" or meta.get("accent") == "cyan"
    state = [len(seq) - 1] * nb             # indice do quadro atual de cada cano (comeca em repouso)
    shot_fx = []                            # (barril, idade)
    smokes = []
    step = 0
    total = len(groups) * gap + 16
    for t in range(total):
        if t % gap == 0 and t // gap < len(groups):
            for bi in groups[t // gap]:
                state[bi] = 0
                shot_fx.append([bi, 0])
                smokes.append([bi, 0, step])
                step += 1
        fx = []
        for item in shot_fx:
            bi, age = item
            if age < 3:
                fx.append((flash(fsc, age / 3, seed=step * 7 + age, cols=PLASMA_COLS if plasma else None),
                           br["muzzle"] - 0.14 * fsc, br["ys"][bi], True))
            item[1] += 1
        for item in smokes:
            bi, age, sd = item
            if 0 < age < 9 and not plasma:   # plasma nao solta fumaca
                fx.append((smoke(max(0.6, fsc * 0.9), age / 9, seed=sd), br["muzzle"] + 0.25 * fsc + age * 0.03,
                           br["ys"][bi], False))
            item[1] += 1
        shot_fx = [x for x in shot_fx if x[1] < 3]
        smokes = [x for x in smokes if x[1] < 9]
        if spin and t < len(groups) * gap:
            bnames = [seq[t % len(seq)]] * nb   # giro uniforme: quadros borrados + repouso, como no jogo
        else:
            bnames = [seq[min(st, len(seq) - 1)] for st in state]
        frames.append(assemble(d, meta, roof, bframes=bnames, tframe=tf, angle=aim, fx=fx, scale=scale))
        durs.append(40)
        state = [min(st + 1, len(seq) - 1) for st in state]
        tf += 1 if ntf > 1 else 0
    for i in range(10):
        t = (i + 1) / 10
        frames.append(assemble(d, meta, roof, tframe=tf, angle=aim * (1 + math.cos(t * math.pi)) / 2, scale=scale))
        durs.append(40)
        tf += 1 if ntf > 1 else 0
    frames = _crop_frames(frames)
    # pecas grandes: limita o tamanho do GIF (envio maximo ~30 MB)
    k = min(1.0, 760 / max(frames[0].size))
    if k < 1:
        frames = [f.resize((int(f.width * k), int(f.height * k)), Image.LANCZOS) for f in frames]
    pal = [f.convert("RGB").quantize(colors=200, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
           for f in frames]
    pal[0].save(os.path.join(d, "preview_fire.gif"), save_all=True, append_images=pal[1:], duration=durs, loop=0,
                optimize=True, disposal=1)
    return len(frames)



# ============================================================================ lancadores de misseis
LAUNCH_REACH = 1.9      # tiles a frente do pivo mostrados no GIF (voo dos misseis), no minimo


def _reach(meta):
    return max(LAUNCH_REACH, meta["turret_size"] / 2 + 1.0)


_TFRAMES = {}


def _turret_frame(d, meta, i, thr=8):
    """Quadro i da animacao da torre para a previa: pixels que so diferem do 1o quadro pelo ruido do render
    (<= thr niveis) ficam iguais aos do 1o quadro, entao o GIF guarda so o que anima de verdade (brasa, olho)."""
    tf = meta["turret"]["frames"]
    key = (d, i % len(tf))
    if key not in _TFRAMES:
        im = load(d, tf[key[1]])
        if key[1]:
            a0 = np.asarray(_turret_frame(d, meta, 0), dtype=np.int16)
            a = np.asarray(im, dtype=np.int16).copy()
            if a.shape == a0.shape:
                keep = np.abs(a - a0).max(axis=2) <= thr
                a[keep] = a0[keep]
                im = Image.fromarray(a.astype(np.uint8), "RGBA")
        _TFRAMES[key] = im
    return _TFRAMES[key]


def _launcher_layer(d, meta, look, level, tframe=0, fx=None, side=None, oc=False):
    """Casulo + nivel do rack (ResourceSprites) num quadrado centrado no pivo, ainda sem girar.

    level: unidades carregadas (0..N). fx: [(img, frente, lado, aditivo)] em coordenadas da torre.
    oc: soma o brilho do overclock (turret_oc.png, OverclockGlowGraphics) por cima."""
    ts = meta["turret_size"]
    T = int(round(ts * PX))
    side = side or int(math.ceil(2 * _reach(meta) * PX)) + 4
    lay = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    c = side / 2
    x0, y0 = int(round(c - T / 2)), int(round(c - T / 2))
    lay.alpha_composite(_turret_frame(d, meta, tframe), (x0, y0))
    for ov in meta["modes"][look]["overlays"]:
        a, b = ov["range"]
        n = max(0, min(b - a, level - a))
        r = ov.get("rect") or [0, 0, T, T]
        lay.alpha_composite(load(d, ov["files"][n]), (x0 + r[0], y0 + r[1]))
    sh = meta["modes"][look].get("shutters")
    if sh:                      # persianas fechadas dos casulos sem unidade neste modo (quadro da torre)
        lay.alpha_composite(load(d, sh["file"]), (x0, y0))
    if oc and meta["turret"].get("oc_glow"):
        lay.alpha_composite(load(d, meta["turret"]["oc_glow"]), (x0, y0))
    for img, fwd, lat, additive in (fx or []):
        if additive:
            add_center(lay, img, c + lat * PX, c - fwd * PX, gain=1.2)
            paste_center(lay, _fade(img, 0.35), c + lat * PX, c - fwd * PX)
        else:
            paste_center(lay, img, c + lat * PX, c - fwd * PX)
    return lay


def _launcher_frame(d, meta, roof, look, level, tframe=0, angle=0.0, fx=None, scale=1, bg=(7, 9, 14), oc=False):
    """Peca inteira: teto, sombra do casulo, casulo + rack + efeitos girados juntos (ChainedTo Turret)."""
    W, H = meta["size"]
    pvx, pvy = meta["pivot"]
    reach = _reach(meta)
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * PX), int((H + top + 0.4) * PX)
    canvas = Image.new("RGBA", (cw, ch), bg + (255,))
    ox, oy = int(side * PX), int(top * PX)
    canvas.alpha_composite(roof, (ox, oy))
    px, py = ox + pvx * PX, oy + pvy * PX
    base = rotate_about_center(_launcher_layer(d, meta, look, level, tframe), angle)
    paste_center(canvas, shadow_of(base), px, py)
    lay = rotate_about_center(_launcher_layer(d, meta, look, level, tframe, fx, oc=oc), angle) if (fx or oc) \
        else base
    paste_center(canvas, lay, px, py)
    if scale != 1:
        canvas = canvas.resize((cw * scale, ch * scale), Image.LANCZOS)
    return canvas


def tube_flash(scale, t, seed=0):
    """Clarao pequeno na boca do tubo (missile_launcher_shoot_flash): nucleo claro + lingua curta para frente."""
    S = 4
    U = PX * scale * S
    w = int(1.2 * U)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    k = (1 - t) ** 0.8
    rng = np.random.default_rng(seed)
    for i, col in enumerate(FIRE_COLS):
        f = 1 - i * 0.22
        _flame(dr, w / 2, w / 2 + U * 0.04, U * (0.42 + 0.1 * rng.random()) * k * f, U * 0.10 * k * f,
               rng.uniform(-6, 6), col)
        r = U * 0.11 * k * f
        dr.ellipse([w / 2 - r, w / 2 - r, w / 2 + r, w / 2 + r], fill=col)
    im = im.resize((w // S, w // S), Image.LANCZOS)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(3 * scale)), im)


def micro_missile(scale, age):
    """Micromissil em voo (frente para cima): corpo claro, nariz e pluma ambar que cresce."""
    S = 4
    U = PX * scale * S
    w, h = int(0.5 * U), int(1.3 * U)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = w / 2, h * 0.30
    L, R = U * 0.24, U * 0.035
    pl = U * (0.18 + 0.12 * min(age, 3))
    for i, col in enumerate(FIRE_COLS):
        f = 1 - i * 0.2
        _flame(dr, cx, cy + L / 2, pl * f, R * 1.6 * f, 180, col)
    dr.rounded_rectangle([cx - R, cy - L / 2, cx + R, cy + L / 2], radius=R, fill=(205, 208, 214, 255))
    dr.polygon([(cx - R, cy - L / 2 + R), (cx + R, cy - L / 2 + R), (cx, cy - L / 2 - R * 1.6)], fill=(232, 234, 238, 255))
    dr.rectangle([cx - R, cy - L / 2 + R * 1.2, cx + R, cy - L / 2 + R * 2.0], fill=(255, 176, 0, 255))
    im = im.resize((w // S, h // S), Image.LANCZOS)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(2 * scale)), im)


def backblast_puff(scale, t, seed=0):
    """Baforada de sopro atras do casulo (chaingun_shoot_smoke): leque de fumaca clara indo para tras (baixo)."""
    S = 2
    w = int(1.8 * PX * scale * S)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    U = PX * scale * S
    for _ in range(10):
        ang = rng.uniform(-1.2, 1.2)
        dist = U * (0.05 + 0.55 * t) * rng.uniform(0.5, 1.1)
        x = w / 2 + math.sin(ang) * dist
        y = w / 2 + math.cos(ang) * dist * 0.8
        r = U * (0.08 + 0.26 * t) * rng.uniform(0.7, 1.2)
        a = int(165 * (1 - t) ** 1.3)
        g = int(rng.uniform(150, 190))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(g, g, g + 6, a))
    return im.filter(ImageFilter.GaussianBlur(4 * scale)).resize((w // S, w // S), Image.LANCZOS)


def make_all_launcher(d, meta, paint=(46, 58, 74), scale=2):
    """Previas do lancador: casulo com o rack cheio (1x e 3x) e GIF girando, salva em LIFO tubo a tubo (o nivel
    do rack cai uma unidade por lancamento, clarao em cada tubo + baforada de sopro atras), recarga unidade
    a unidade e, no fim, o rack cheio dos outros modos com unidade diferente (pesado, torpedo, persianas)."""
    roof = paint_roof(load(d, "roof.png"), paint)
    looks = list(meta["modes"])
    look = looks[0]
    units = len(meta["modes"][look]["units"])
    bg = (7, 9, 14)

    # vista do jogo: 3x com o rack cheio do 1o modo + grade 1x com todos os modos (rack cheio) e, se houver,
    # o 1o modo em overclock (turret_oc.png por cima); a grade cresce em colunas e nunca sai da folha
    def still(lk, oc=False):
        c = _launcher_frame(d, meta, roof, lk, len(meta["modes"][lk]["units"]), oc=oc)
        return crop_content(c, bg)
    one = still(look)
    smalls = [one] + [still(lk) for lk in looks[1:]]
    if meta["turret"].get("oc_glow"):
        smalls.append(still(look, oc=True))
    three = one.resize((one.width * 3, one.height * 3), Image.LANCZOS)
    cw_, ch_ = max(s.width for s in smalls), max(s.height for s in smalls)
    rows = max(1, (three.height + 12) // (ch_ + 12))
    cols = -(-len(smalls) // rows)
    left_w = cols * (cw_ + 12) - 12
    sheet = Image.new("RGBA", (left_w + three.width + 48, max(three.height, rows * (ch_ + 12) - 12) + 32),
                      bg + (255,))
    for i, im in enumerate(smalls):
        sheet.alpha_composite(im, (16 + (i // rows) * (cw_ + 12), 16 + (i % rows) * (ch_ + 12)))
    sheet.alpha_composite(three, (left_w + 32, 16))
    sheet.convert("RGB").save(os.path.join(d, "preview_ingame.png"))

    # GIF (40 ms por quadro): mira, salva em ripple (4/30 s ~ 3 quadros; 2o tubo do cassete 2/30 s ~ 2 quadros
    # depois do 1o), recarga unidade a unidade, volta
    ntf = len(meta["turret"]["frames"])
    tf_every = max(1, int(round(meta["turret"].get("interval", 0.12) / 0.04))) if ntf > 1 else 0
    tubes = meta["modes"][look]["tubes"]
    upods = meta["modes"][look].get("unit_pods") or [0] * units
    bb = (meta.get("backblast") or [[-0.5, 0.0]])
    reach = _reach(meta)
    frames, durs = [], []
    aim = -28.0
    clock = [0]

    def tfr():
        return (clock[0] // tf_every) % ntf if tf_every else 0

    def push(img):
        frames.append(img)
        durs.append(40)
        clock[0] += 1

    for i in range(10):
        t = (i + 1) / 10
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim * (1 - math.cos(t * math.pi)) / 2, scale=scale))
    for _ in range(3):
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim, scale=scale))
    # racks grandes (Mula: 48): ripple de 2 quadros (~2/30 s do jogo) e recarga mais curta por unidade, senao o
    # GIF passa de ~15 MB
    big = units > 24
    ripple, burst = (2 if big else 3), 2
    events = []                 # (quadro, unidade, tubo)
    for k in range(units):
        u = units - 1 - k       # LIFO: a ultima unidade carregada sai primeiro
        for j in range(len(tubes[u])):
            events.append((k * ripple + j * burst, u, j))
    fsc = max(0.5, min(1.4, meta["turret_size"] / 2.0))
    last = max(e[0] for e in events)
    level = units
    for f in range(last + 12):
        fx = []
        for (f0, u, j) in events:
            age = f - f0
            if age == 0 and j == 0:
                level = u       # o rack perde a unidade no 1o tiro do cassete
            if age < 0:
                continue
            fwd, lat = tubes[u][j]
            if age < 8:         # missil saindo do tubo e acelerando para frente
                s = 0.10 + 0.22 * age + 0.06 * age * age
                if fwd + s < reach - 0.2:
                    fx.append((micro_missile(scale=1, age=age), fwd + s + 0.12, lat, False))
            if age < 3:
                fx.append((tube_flash(fsc, age / 3, seed=f0 * 5 + j), fwd + 0.08, lat, True))
            if age < 9 and j == 0:
                # uma baforada no ponto de sopro do casulo que disparou (so fumaca: as regras nao poem chama ali)
                b = bb[upods[u]] if upods[u] < len(bb) else bb[0]
                fx.append((backblast_puff(fsc, age / 9, seed=f0 + 3), b[0] - 0.08 - age * 0.03, b[1], False))
        push(_launcher_frame(d, meta, roof, look, level, tfr(), aim, fx=fx, scale=scale))
    for lv in range(units + 1):       # recarga: uma unidade por vez
        for _ in range(2 if big else 4):
            push(_launcher_frame(d, meta, roof, look, lv, tfr(), aim, scale=scale))
    for _ in range(4):
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim, scale=scale))
    for i in range(10):
        t = (i + 1) / 10
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim * (1 + math.cos(t * math.pi)) / 2, scale=scale))
    # fecho: rack cheio dos outros modos com unidade diferente (pesado, torpedo, persianas), ~0.5 s cada
    seen = {units}
    for lk in looks[1:]:
        n = len(meta["modes"][lk]["units"])
        if n in seen:
            continue
        seen.add(n)
        for _ in range(13):
            push(_launcher_frame(d, meta, roof, lk, n, tfr(), 0.0, scale=scale))
    frames = _crop_frames(frames)
    k = min(1.0, (640 if big else 760) / max(frames[0].size))
    if k < 1:
        frames = [f.resize((int(f.width * k), int(f.height * k)), Image.LANCZOS) for f in frames]
    _save_gif_shared(frames, durs, os.path.join(d, "preview_fire.gif"))
    return len(frames)


def _save_gif_shared(frames, durs, path, colors=255):
    """GIF com UMA paleta para todos os quadros (amostrada de varios quadros, inclusive os de clarao): as areas
    paradas ficam identicas entre quadros e o Pillow grava so o retangulo que mudou (paleta por quadro mudava
    a imagem inteira e o GIF do lancador de 48 tubos passava de 30 MB)."""
    step = max(1, len(frames) // 32)
    samples = [f.convert("RGB").resize((max(1, f.width // 2), max(1, f.height // 2)), Image.BILINEAR)
               for f in frames[::step]]
    sheet = Image.new("RGB", (samples[0].width, sum(s.height for s in samples)))
    y = 0
    for s_ in samples:
        sheet.paste(s_, (0, y))
        y += s_.height
    pal = sheet.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=False, disposal=1)


def main():
    d = sys.argv[1]
    paint = (46, 58, 74)
    if "--paint" in sys.argv:
        paint = tuple(int(v) for v in sys.argv[sys.argv.index("--paint") + 1].split(","))
    print("OK", make_all(d, paint), "quadros")


if __name__ == "__main__":
    main()
