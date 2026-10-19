"""Texturas proprias dos efeitos de plasma (Boitata e Curupira), geradas com numpy + PIL a cada build.

Todas sao aditivas (TargetBlendMode SourceAlpha/One): o RGB e a cor e o alfa e a intensidade, entao a luz somada
na tela e rgb * a. Cada funcao monta a "luz" L (float, 0..1+) e _encode() separa cor e intensidade.
Orientacao igual a das texturas vanilla de projetil (pd_shot.png, laser_bolt_large.png): a FRENTE e +X (direita).

  bs_plasma_bolt.png          256x64          nucleo branco-quente em gota com borda ciano (cabeca a direita)
  bs_plasma_tail[_oc].png     8 x 512x64      Boitata: cauda de serpente, um fio dominante e outro mais fraco e
                                              fino que ondulam com amplitude crescendo para a ponta (2 por linha)
  bs_plasma_wake[_oc].png     8 x 512x64      Curupira: esteira ionizada reta e grossa com 3 aneis de pulso
                                              discretos correndo para tras (2 por linha)
  bs_plasma_burst.png         8 x 128x128     descarga de boca: ponta de lanca para frente + faiscas na base
  bs_plasma_splash.png        8 x 128x128     respingo de impacto: clarao + gotas e borrifos jogados para tras
  bs_plasma_shock.png         256x256         anel fino de choque (branco, tingivel), centro transparente

Nas texturas em atlas a cabeca de cada quadro termina num vao transparente de ~10 px (GUTTER): com MipLevels =
max e amostragem Linear o quadro vizinho nao vaza para a ponta da cauda quando o zoom se afasta. Nos texels de
alfa 0 o RGB recebe a cor do vizinho mais proximo (_encode), senao o mipmap misturaria branco nas bordas ciano.
"""

import math

import numpy as np
from PIL import Image

WHITE = np.array([1.0, 1.0, 1.0])
ICE = np.array([0.72, 1.0, 1.0])
CYAN = np.array([0.05, 0.88, 1.0])
TEAL = np.array([0.0, 0.55, 0.82])
DEEP = np.array([0.0, 0.32, 0.6])
GUTTER = 10            # px transparentes na borda da cabeca de cada quadro dos atlas de cauda


def _box(a, r):
    """Media movel separavel de raio r px (borda replicada); a pode ter canais (H, W[, C])."""
    k = 2 * r + 1
    pad = ((r, r), (r, r)) + ((0, 0),) * (a.ndim - 2)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=0)
    c = np.concatenate([np.zeros_like(c[:1]), c], axis=0)
    p = (c[k:] - c[:-k]) / k
    c = np.cumsum(p, axis=1)
    c = np.concatenate([np.zeros_like(c[:, :1]), c], axis=1)
    return (c[:, k:] - c[:, :-k]) / k


def _encode(L):
    """Luz (H, W, 3) -> RGBA aditivo: alfa = canal mais forte, RGB = cor normalizada (rgb * a = luz).
    Texels vazios (alfa 0) ganham a cor media dos vizinhos com luz (raios crescentes), nao branco: o mipmap
    (media simples de RGB) nao clareia as bordas ciano quando o zoom se afasta."""
    L = np.clip(L, 0.0, 1.0)
    a = L.max(axis=2)
    rgb = L / np.maximum(a[..., None], 1e-6)
    empty = a < 0.5 / 255
    for r in (2, 6, 16, 48, 128):
        if not empty.any():
            break
        den = _box(a, r)
        num = _box(L, r)
        ok = empty & (den > 1e-6)
        col = num / np.maximum(den[..., None], 1e-6)
        col = col / np.maximum(col.max(axis=2, keepdims=True), 1e-6)
        rgb[ok] = col[ok]
        empty &= ~ok
    rgb[empty] = CYAN / CYAN.max()
    out = np.dstack([rgb, a])
    return Image.fromarray(np.round(np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")


def _soft(L, k=1.0):
    """Compressao suave dos picos (o centro estoura para branco sem degrau)."""
    return 1.0 - np.exp(-k * L)


def _lerp_col(stops, t):
    """Gradiente de cor por t (0..1) em paradas igualmente espacadas; t pode ser array."""
    t = np.clip(np.asarray(t, dtype=float), 0, 1) * (len(stops) - 1)
    i = np.minimum(t.astype(int), len(stops) - 2)
    f = (t - i)[..., None]
    s = np.array(stops)
    return s[i] * (1 - f) + s[i + 1] * f


def _grid(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    return x + 0.5, y + 0.5


def _segment(px, py, x0, y0, x1, y1):
    """Distancia de cada pixel ao segmento (x0,y0)-(x1,y1) e a posicao t (0..1) ao longo dele."""
    dx, dy = x1 - x0, y1 - y0
    ll = max(1e-6, dx * dx + dy * dy)
    t = np.clip(((px - x0) * dx + (py - y0) * dy) / ll, 0, 1)
    qx, qy = x0 + t * dx, y0 + t * dy
    return np.hypot(px - qx, py - qy), t


# ----------------------------------------------------------------------------- nucleo do raio
def bolt(w=256, h=64, hot=1.0):
    """Gota branco-quente: nariz curto e cheio a direita (x = 0,8 w), cauda afinando para tras, borda ciano."""
    x, y = _grid(w, h)
    u = x / w
    v = (y - h / 2) / (h / 2)
    dx = u - 0.80
    back = dx < 0
    # nucleo branco: nariz arredondado, afina para tras
    sx = np.where(back, 0.26, 0.055)
    sy = 0.30 * np.where(back, np.exp(dx / 0.34), 1.0)
    core = np.exp(-(dx / sx) ** 2 - (v / sy) ** 2)
    # borda ciano mais larga e mais longa
    sx2 = np.where(back, 0.34, 0.075)
    sy2 = 0.55 * np.where(back, np.exp(dx / 0.42), 1.0)
    rim = np.exp(-(dx / sx2) ** 2 - (v / sy2) ** 2)
    # halo largo e fraco (some antes das bordas da textura)
    halo = np.exp(-((u - 0.72) / 0.30) ** 2 - (v / 0.75) ** 2)
    L = (core[..., None] * WHITE * 3.2 * hot + rim[..., None] * CYAN * 1.2
         + halo[..., None] * TEAL * 0.35)
    L = _soft(L, 1.4)
    edge = np.clip(np.minimum(np.minimum(u, 1 - u) / 0.06, np.minimum(1 - abs(v), 1) / 0.12), 0, 1)
    return _encode(L * edge[..., None])


# ----------------------------------------------------------------------------- caudas (atlas)
def _head_fade(d, fw, gutter=GUTTER, ramp_px=18):
    """Peso 0 nos ultimos `gutter` px da cabeca (borda direita do quadro) subindo ate 1 em `ramp_px` px."""
    g0 = gutter / fw
    return np.clip((d - g0) / (ramp_px / fw), 0, 1) ** 1.5


def _stops(whiten):
    return [ICE * (1 - whiten) + WHITE * whiten, CYAN * (1 - whiten) + ICE * whiten,
            TEAL * (1 - whiten) + CYAN * whiten, DEEP * (1 - whiten) + TEAL * whiten]


def _atlas_put(atlas, f, per_row, fw, fh, L):
    r, c = divmod(f, per_row)
    atlas[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw] = L


def _tail_curves(d, f, s, frames, half, body, body_waves, amp, waves, jit_b, jit_s, amp_j, orbit=(0.6, 1.0)):
    """Centro do corpo e do fio s (0/1) da cauda da Boitata na posicao d (0 = cabeca, 1 = fim), quadro f.
    O corpo ondula devagar (1 volta / frames por quadro) e os fios em helice (2 voltas / frames), com um tremor
    de fase/amplitude por quadro (jit_b, jit_s, amp_j). A amplitude dos fios CRESCE para a ponta (a cabeca segue
    firme e o rabo chicoteia, como uma cobra nadando) e a onda fica mais longa para o fim (fase ~ d^0,85).
    orbit: quanto cada fio se afasta do corpo (o dominante fica colado na espinha, o fraco gira mais longe)."""
    d = np.clip(d, 0, 1)
    conv = 1 - np.exp(-d / 0.07)                     # tudo converge na cabeca
    pb = 2 * math.pi * f / frames + jit_b
    ps = 4 * math.pi * f / frames + jit_s
    yb = body * half * conv * (0.35 + 0.65 * d) * np.sin(2 * math.pi * body_waves * d ** 0.9 - pb)
    grow = 0.22 + 0.78 * d ** 0.8                    # amplitude cresce da cabeca para a ponta
    env = amp * amp_j * half * conv * grow * orbit[s]
    return yb, yb + env * np.sin(2 * math.pi * waves * d ** 0.85 - ps + s * math.pi)


def tail(frames=8, fw=512, fh=64, waves=3.0, amp=0.40, body=0.26, body_waves=1.15, core_px=1.7, glow_px=4.5,
         chan_px=6.0, gain=1.0, whiten=0.0, second=0.3, seed=5):
    """Atlas da cauda da Boitata (a serpente de fogo): um corpo de plasma que ondula devagar e dois fios em helice
    (fase oposta) em volta dele. Para parecer cobra e nao DNA/mola: a amplitude dos fios cresce da cabeca para a
    ponta, a onda fica mais longa para o fim, cada quadro tem um tremor pequeno de fase e de amplitude (seed fixa:
    a textura e sempre a mesma) e um fio domina: ele fica perto da espinha do corpo, e o outro, com `second` da
    intensidade e mais fino, gira mais longe como uma chama solta. Por quadro o
    corpo anda 1 volta / frames e os fios 2 voltas / frames: a animacao fecha o ciclo e a onda corre para tras."""
    per_row = 2
    rows = int(math.ceil(frames / per_row))
    atlas = np.zeros((rows * fh, per_row * fw, 3))
    x, y = _grid(fw, fh)
    half = fh / 2
    yc = y - half
    stops = _stops(whiten)
    rng = np.random.default_rng(seed)
    jit = [(rng.uniform(-0.18, 0.18), rng.uniform(-0.4, 0.4), rng.uniform(0.88, 1.1)) for _ in range(frames)]

    d = 1.0 - x / fw
    dd = 1.0 / fw
    fade = (1 - d) ** 1.3 * _head_fade(d, fw)
    col = _lerp_col(stops, d ** 0.8)
    hot = col * 0.4 + WHITE * 0.6
    for f in range(frames):
        jb, js, ja = jit[f]

        def cv(dv, s_):
            return _tail_curves(dv, f, s_, frames, half, body, body_waves, amp, waves, jb, js, ja)

        yb, _ = cv(d, 0)
        yb2, _ = cv(d + dd, 0)
        dist_b = np.abs(yc - yb) / np.sqrt(1 + (yb2 - yb) ** 2)
        wch = chan_px * (1 - 0.5 * d)
        L = np.exp(-0.5 * (dist_b / wch) ** 2)[..., None] * col * 0.45
        L += np.exp(-0.5 * (dist_b / (wch * 0.35)) ** 2)[..., None] * hot * 0.3 * ((1 - d) ** 2)[..., None]
        for s_, k in ((0, 1.0), (1, second)):
            _, c = cv(d, s_)
            _, c2 = cv(d + dd, s_)
            dist = np.abs(yc - c) / np.sqrt(1 + (c2 - c) ** 2)
            th = core_px * (1 - 0.35 * d) * (1.0 if s_ == 0 else 0.7)
            L += np.exp(-0.5 * (dist / th) ** 2)[..., None] * hot * 1.4 * k
            L += np.exp(-0.5 * (dist / (glow_px * (1.0 if s_ == 0 else 0.8))) ** 2)[..., None] * col * 0.5 * k
        L = _soft(L * fade[..., None] * gain, 1.25)
        vfade = np.clip((half - np.abs(yc)) / 3.0, 0, 1)
        _atlas_put(atlas, f, per_row, fw, fh, L * vfade[..., None])
    return _encode(atlas)


def wake(frames=8, fw=512, fh=64, rings=3, core_px=3.6, chan_px=8.5, gain=1.0, whiten=0.0, ring_gain=0.5):
    """Atlas da cauda do Curupira: esteira ionizada RETA e grossa (os canos dele sao trilhos, nao a serpente da
    Boitata). Nucleo branco que afina para tras, canal ciano que se espalha um pouco no fim e `rings` aneis de
    pulso (elipses finas vistas de lado, frente mais clara) que nascem atras da cabeca e correm para o fim da
    cauda apagando. Por quadro cada anel anda 1 / (rings * frames) do comprimento: a animacao fecha o ciclo.
    Um tremor lento no brilho do canal da a cara de plasma ionizado. ring_gain: forca dos aneis (0,5: discretos,
    para nao lerem como as "penas" de flecha / assinatura do railgun vanilla)."""
    per_row = 2
    rows = int(math.ceil(frames / per_row))
    atlas = np.zeros((rows * fh, per_row * fw, 3))
    x, y = _grid(fw, fh)
    half = fh / 2
    yc = y - half
    d = 1.0 - x / fw
    stops = _stops(whiten)
    col = _lerp_col(stops, d ** 0.8)
    hot = col * 0.35 + WHITE * 0.65
    fade = (1 - d) ** 1.1 * _head_fade(d, fw)
    th = core_px * (1 - 0.5 * d)
    wg = chan_px * (0.85 + 0.5 * d)
    core = np.exp(-0.5 * (yc / th) ** 2)
    glow = np.exp(-0.5 * (yc / wg) ** 2)
    for f in range(frames):
        ph = f / frames
        shimmer = 1 + 0.12 * np.sin(2 * math.pi * (3 * d - ph)) + 0.08 * np.sin(2 * math.pi * (7 * d + 2 * ph))
        L = core[..., None] * hot * 1.6 * ((1 - d) ** 1.2)[..., None]
        L += glow[..., None] * col * 0.75 * shimmer[..., None]
        for k in range(rings):
            p = (k + ph) / rings                      # posicao do anel ao longo da cauda (0 = cabeca)
            xr = fw * (1 - p)
            rx = 3.0 + 4.0 * p
            ry = min(half - 5, chan_px * 2.3 * (0.9 + 0.35 * p))
            e = np.sqrt(((x - xr) / rx) ** 2 + (yc / ry) ** 2)
            ring = np.exp(-0.5 * ((e - 1) * ry / 2.0) ** 2)
            front = 0.55 + 0.45 * np.tanh((x - xr) / rx)
            band = np.exp(-0.5 * ((x - xr) / (rx * 1.4)) ** 2) * glow
            amp = (1 - p) ** 1.1 * min(1.0, p / 0.08)
            L += (ring * front)[..., None] * (hot * 0.6 + col * 0.4) * 1.6 * amp * ring_gain
            L += band[..., None] * hot * 1.3 * amp * (0.4 + 0.6 * ring_gain)
        L = _soft(L * fade[..., None] * gain, 1.25)
        vfade = np.clip((half - np.abs(yc)) / 3.0, 0, 1)
        _atlas_put(atlas, f, per_row, fw, fh, L * vfade[..., None])
    return _encode(atlas)


# ----------------------------------------------------------------------------- descarga de boca
def burst(frames=8, fs=128, cx=40, seed=7):
    """Atlas da descarga: clarao branco na boca (x = cx), ponta de lanca branca-ciano para frente (+X) que se
    alonga e some, faiscas finas na base e um anel fraco. 4 quadros por linha."""
    per_row = 4
    rows = int(math.ceil(frames / per_row))
    atlas = np.zeros((rows * fs, per_row * fs, 3))
    x, y = _grid(fs, fs)
    cy = fs / 2
    rx, ry = x - cx, y - cy
    rng = np.random.default_rng(seed)
    rays = [(a + rng.uniform(-6, 6), rng.uniform(0.75, 1.0)) for a in (32, -32, 68, -68, 118, -118, 160, -160)]
    for f in range(frames):
        t = f / frames
        L = np.zeros((fs, fs, 3))
        r2 = rx ** 2 + ry ** 2
        sc = 6.5 * (1 - 0.45 * t)
        L += np.exp(-r2 / (2 * sc ** 2))[..., None] * WHITE * 2.2 * (1 - t) ** 1.5
        sh = 15 * (1 + 0.35 * t)
        L += np.exp(-r2 / (2 * sh ** 2))[..., None] * CYAN * 0.75 * (1 - t) ** 1.3
        # ponta de lanca (cone) para frente
        Ls = 80 * (0.55 + 0.45 * math.sqrt(t))
        xf = np.clip(rx / Ls, 0, 1)
        wid = 9.5 * (1 - xf) ** 0.9 + 0.6
        base = np.clip((rx + 4) / 6, 0, 1)
        spear = base * np.exp(-(ry / wid) ** 2) * (1 - xf) ** 0.5
        inner = base * np.exp(-(ry / (wid * 0.36)) ** 2) * (1 - xf) ** 0.8
        L += spear[..., None] * CYAN * 1.6 * (1 - t) ** 1.1 + inner[..., None] * WHITE * 2.0 * (1 - t) ** 1.3
        # faiscas na base
        for ang, ln in rays:
            a = math.radians(ang)
            length = 26 * ln * (0.55 + 0.7 * t)
            dist, tt = _segment(x, y, cx, cy, cx + math.cos(a) * length, cy + math.sin(a) * length)
            ray = np.exp(-0.5 * (dist / 1.1) ** 2) * (1 - tt) ** 0.7
            L += ray[..., None] * ICE * 1.1 * (1 - t) ** 1.8
        # anel de choque achatado (disco visto de lado) logo a frente da boca
        rr = 7 + 20 * t
        ell = np.sqrt(((rx - 6 - 14 * t) / (rr * 0.42)) ** 2 + (ry / rr) ** 2)
        ring = np.exp(-0.5 * ((ell - 1) * rr / 1.6) ** 2)
        L += ring[..., None] * CYAN * 0.55 * (1 - t) ** 1.5 * (t > 0)
        L = _soft(L, 1.3)
        edge = np.clip(np.minimum(np.minimum(x, fs - x), np.minimum(y, fs - y)) / 6, 0, 1)
        r, c = divmod(f, per_row)
        atlas[r * fs:(r + 1) * fs, c * fs:(c + 1) * fs] = L * edge[..., None]
    return _encode(atlas)


# ----------------------------------------------------------------------------- respingo de impacto
def splash(frames=8, fs=128, cx=76, seed=11, n_drops=9, n_dots=10):
    """Atlas do impacto (o raio vinha de -X para +X e bateu em cx): clarao branco, brilho ciano e um borrifo
    jogado para tras (-X), como plasma espirrando de uma superficie. Poucas gotas (n_drops) de espessura,
    comprimento e duracao diferentes, cada uma afinando e apagando da cabeca para a base (soltas do centro, nada
    de raios de pente), mais gotinhas (n_dots) que aparecem depois e um arco de choque quebrado."""
    per_row = 4
    rows = int(math.ceil(frames / per_row))
    atlas = np.zeros((rows * fs, per_row * fs, 3))
    x, y = _grid(fs, fs)
    cy = fs / 2
    rx, ry = x - cx, y - cy
    r = np.hypot(rx, ry)
    th = np.arctan2(ry, rx)
    rng = np.random.default_rng(seed)
    # angulos espalhados de forma irregular no semicirculo de tras
    base = np.linspace(-78, 78, n_drops) + rng.uniform(-9, 9, n_drops)
    drops = [dict(ang=math.radians(180 + b), v=rng.uniform(0.45, 1.0), w=rng.uniform(0.8, 2.3),
                  ln=rng.uniform(0.6, 1.4), tf=rng.uniform(0.55, 1.0)) for b in base]
    drops += [dict(ang=math.radians(sg * rng.uniform(98, 120)), v=rng.uniform(0.35, 0.55), w=rng.uniform(0.7, 1.2),
                   ln=rng.uniform(0.5, 0.8), tf=rng.uniform(0.45, 0.7)) for sg in (-1, 1)]
    dots = [dict(ang=math.radians(180 + rng.uniform(-95, 95)), v=rng.uniform(0.5, 1.1), w=rng.uniform(0.7, 1.3),
                 t0=rng.uniform(0.08, 0.35)) for _ in range(n_dots)]
    back = np.clip((-np.cos(th) + 0.25) / 0.6, 0, 1)        # peso do arco: para tras
    p1, p2 = rng.uniform(0, 2 * math.pi, 2)
    broken = np.clip(0.55 + 0.45 * np.sin(5 * th + p1) + 0.3 * np.sin(9 * th + p2), 0, 1)
    for f in range(frames):
        t = f / frames
        L = np.zeros((fs, fs, 3))
        s1 = 6 * (1 + 0.5 * t)
        L += np.exp(-r ** 2 / (2 * s1 ** 2))[..., None] * WHITE * 2.4 * (1 - t) ** 2
        s2 = 17 * (1 + 0.6 * t)
        L += np.exp(-r ** 2 / (2 * s2 ** 2))[..., None] * CYAN * 0.7 * (1 - t) ** 1.2
        colr = ICE * (1 - t) + CYAN * t
        for g in drops:
            life = max(0.0, 1 - t / g["tf"]) ** 1.3
            if life <= 0:
                continue
            rr = g["v"] * (6 + 56 * t)
            ln = (4 + 14 * t * g["v"]) * g["ln"]
            r0 = max(rr - ln, 2 + 10 * t)
            if rr <= r0:
                continue
            ca, sa = math.cos(g["ang"]), math.sin(g["ang"])
            dist, tt = _segment(x, y, cx + ca * r0, cy + sa * r0, cx + ca * rr, cy + sa * rr)
            wid = g["w"] * (0.35 + 0.65 * tt)                      # grossa na cabeca, fina na base
            dr = np.exp(-0.5 * (dist / wid) ** 2) * tt ** 1.3
            hx, hy = cx + ca * rr, cy + sa * rr
            bead = np.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * (g["w"] * 0.9) ** 2))
            L += (dr * 1.6 + bead * 0.6)[..., None] * colr * life * (0.6 + 0.4 * g["v"])
        for g in dots:
            if t < g["t0"]:
                continue
            u = (t - g["t0"]) / (1 - g["t0"])
            rr = g["v"] * (10 + 48 * u)
            hx, hy = cx + math.cos(g["ang"]) * rr, cy + math.sin(g["ang"]) * rr
            dot = np.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * g["w"] ** 2))
            L += dot[..., None] * colr * 0.7 * (1 - u) ** 1.3
        rad = 5 + 36 * t
        arc = np.exp(-0.5 * ((r - rad) / (1.6 + 2.0 * t)) ** 2) * back * broken
        L += arc[..., None] * (CYAN * 0.7 + ICE * 0.3) * 0.6 * (1 - t) ** 1.8
        L = _soft(L, 1.3)
        edge = np.clip(np.minimum(np.minimum(x, fs - x), np.minimum(y, fs - y)) / 6, 0, 1)
        rr_, c = divmod(f, per_row)
        atlas[rr_ * fs:(rr_ + 1) * fs, c * fs:(c + 1) * fs] = L * edge[..., None]
    return _encode(atlas)


# ----------------------------------------------------------------------------- anel de choque
def shock_ring(s=256, radius=0.86, rim_px=2.4, inner=0.12, inner_w=0.10):
    """Anel fino de onda de choque, branco (tingido pela cor da particula): aro nitido de ~2-4 px, um veu fraco
    so na beirada de dentro e o centro TRANSPARENTE (le como anel de pressao, nao como disco/bolha)."""
    x, y = _grid(s, s)
    rr = np.hypot(x - s / 2, y - s / 2) / (s / 2)
    rim = np.exp(-0.5 * ((rr - radius) * (s / 2) / rim_px) ** 2)
    veil = np.where(rr < radius, inner * np.exp(-((radius - rr) / inner_w) ** 2), 0)
    a = np.clip(rim + veil, 0, 1) * np.clip((0.99 - rr) / 0.04, 0, 1)
    out = np.dstack([np.ones((s, s, 3)), a])
    return Image.fromarray(np.round(out * 255).astype(np.uint8), "RGBA")


# nome do arquivo -> imagem (parametros por arma; ver plasma_fx.CFG)
def all_textures():
    return {
        "bs_plasma_bolt.png": bolt(),
        "bs_plasma_tail.png": tail(core_px=2.1, glow_px=5.0, chan_px=6.5),
        "bs_plasma_tail_oc.png": tail(core_px=2.4, glow_px=5.4, chan_px=7.0, gain=1.2, whiten=0.3),
        "bs_plasma_wake.png": wake(),
        "bs_plasma_wake_oc.png": wake(core_px=4.2, chan_px=9.5, gain=1.15, whiten=0.3),
        "bs_plasma_burst.png": burst(),
        "bs_plasma_splash.png": splash(),
        "bs_plasma_shock.png": shock_ring(),
    }
