"""Texturas proprias dos efeitos de plasma (Boitata e Curupira), geradas com numpy + PIL a cada build.

Quase todas sao aditivas (TargetBlendMode SourceAlpha/One): o RGB e a cor e o alfa e a intensidade, entao a luz
somada na tela e rgb * a. Cada funcao monta a "luz" L (float, 0..1+) e _encode() separa cor e intensidade. A
excecao e bs_plasma_shade[_heavy].png, de mistura alfa comum (ver shade()). Orientacao igual a das texturas vanilla de
projetil (pd_shot.png, laser_bolt_large.png): a FRENTE e +X (direita).

  bs_plasma_lance.png         256x64          nucleo das duas armas: ponta de lanca, agulha branca longa que afina
                                              para tras (no Curupira a Sprite e mais grossa: lanca pesada)
  bs_plasma_corona.png        256x64          Boitata: corona afunilada (branca, tingida pelo VertexColor): ponta de
                                              lanca na frente e um corpo que afina para tras, sem cabeca redonda
  bs_plasma_corona_heavy.png  256x64          Curupira: a mesma corona, mais cheia e com a traseira larga (~55% da
                                              largura maxima): emenda na esteira sem fechar num oval
  bs_plasma_shade[_heavy].png 256x64          sombra azul-petroleo (mistura alfa comum, NAO aditiva) por baixo do
                                              raio, um pouco mais larga que as camadas aditivas e com perfil de
                                              plato: sobre casco branco o raio le como lanca com contorno escuro
                                              (_heavy: mais larga ~1,5 tile atras do nariz, como a corona pesada)
  bs_plasma_tail[_oc].png     8 x 512x64      Boitata: corpo de serpente de fogo grosso que afina da cabeca a ponta,
                                              ondulacao suave que NAO cresce na ponta, labaredas e escamas de luz
  bs_plasma_wake[_oc].png     8 x 512x64      Curupira: esteira ionizada reta e grossa que AFINA da cabeca a ponta,
                                              com 3 aneis de pulso discretos so da metade de tras (2 por linha)
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
def _smooth(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def lance(w=256, h=64, nose=0.9, hot=1.0):
    """Nucleo das duas armas: agulha branco-quente em ponta de lanca. Nariz curto e afiado em u = nose, corpo branco
    longo que afina para tras (nada de gota redonda: a cabeca do raio e uma lanca, nao um ovo) e borda ciano fina.
    Sem halo: a corona afunilada (corona()) faz o brilho em volta."""
    x, y = _grid(w, h)
    u = x / w
    v = (y - h / 2) / (h / 2)
    dx = u - nose
    back = dx < 0
    sx = np.where(back, 0.40, 0.035)
    sy = 0.27 * np.where(back, np.exp(dx / 0.5), 1.0)
    core = np.exp(-(dx / sx) ** 2 - (v / sy) ** 2)
    sx2 = np.where(back, 0.55, 0.055)
    sy2 = 0.52 * np.where(back, np.exp(dx / 0.55), 1.0)
    rim = np.exp(-(dx / sx2) ** 2 - (v / sy2) ** 2)
    L = core[..., None] * WHITE * 3.0 * hot + rim[..., None] * (CYAN * 0.8 + ICE * 0.2) * 1.1
    L = _soft(L, 1.4)
    edge = np.clip(np.minimum(np.minimum(u, 1 - u) / 0.05, np.minimum(1 - abs(v), 1) / 0.12), 0, 1)
    return _encode(L * edge[..., None])


def _taper(w, h, nose, peak, wmax, rear_w, rear_fade, power=2.0):
    """Forma afunilada (0..1) em ponta de lanca: largura maxima wmax (fracao da meia altura) em u = peak, nariz
    arredondado-pontudo ate u = nose (raiz quadrada) e corpo que afina ate rear_w * wmax em u = 0, apagando nos
    ultimos rear_fade do comprimento. power = 2: perfil gaussiano (corona); power > 2: perfil de "plato" com borda
    mais definida (sombra: escurece por igual debaixo do corpo e acaba num contorno, sem cauda longa)."""
    x, y = _grid(w, h)
    u = x / w
    v = (y - h / 2) / (h / 2)
    front = np.sqrt(np.clip((nose - u) / (nose - peak), 0, 1))
    back = rear_w + (1 - rear_w) * np.clip(u / peak, 0, 1) ** 1.3
    wv = wmax * np.where(u >= peak, front, back)
    a = np.exp(-0.5 * (np.abs(v) / np.maximum(wv * 0.5, 1e-3)) ** power) * (wv > 1e-3)
    a = a * _smooth(0.0, rear_fade, u) * (0.5 + 0.5 * np.clip(u / peak, 0, 1))
    a = _box(a, 2)
    edge = np.clip(np.minimum(np.minimum(u, 1 - u) / 0.03, np.minimum(1 - abs(v), 1) / 0.1), 0, 1)
    return a * edge


def corona(w=256, h=64, nose=0.95, peak=0.74, wmax=0.66, rear_w=0.34, rear_fade=0.45):
    """Corona afunilada (branca: a cor vem do VertexColor da Sprite, como no blob.png vanilla). Ponta de lanca na
    frente e um corpo que afina para tras e emenda na cauda: a silhueta e um corpo so, sem cabeca redonda. Boitata:
    os valores padrao; Curupira (bs_plasma_corona_heavy.png): mais cheia e com a traseira larga (rear_w maior), que
    entra na esteira com ~55% da largura em vez de fechar num oval."""
    a = _taper(w, h, nose, peak, wmax, rear_w, rear_fade)
    return _encode(a[..., None] * WHITE)


def shade(w=256, h=64, nose=0.97, peak=0.86, wmax=0.62, rear_w=0.35, rear_fade=0.55, alpha=0.5,
          col=(0.0, 0.2, 0.28), power=2.0):
    """Sombra por baixo do raio (Sprite SEM TargetBlendMode = mistura alfa comum, como a Sprite do missil
    missile_he.rules e a fumaca chaingun_shoot_smoke.rules, que fica num balde de cima). Sobre casco branco o ciano
    aditivo quase some (branco + ciano = branco); esta sombra azul-petroleo escurece o casco DEBAIXO do raio e o
    ciano volta a aparecer. Ela e um pouco MAIS LARGA que a corona e o comeco da cauda (power > 2: plato que
    escurece por igual debaixo do corpo e acaba num contorno de borda suave): a faixa que sobra de cada lado e o
    contorno escuro que desenha a lanca sobre casco branco (com a sombra mais estreita que o corpo, o ciano aditivo
    re-saturava tudo e o raio virava uma folha clara). Mais larga perto do nariz (peak), onde o corpo aditivo e mais
    forte, e afinando/apagando na traseira (rear_w, rear_fade): nada de faixa escura atras da cauda fina. A cor e um
    azul-petroleo, nao preto: a borda le como borda fria do plasma, nao como sujeira; sobre o espaco ela vira so um
    halo azul-petroleo fraco.
    RGB = cor x forma (a / alpha), entao RGB = 0 onde o alfa e 0: nunca soma cor fora da sombra, seja a mistura alfa
    simples ou pre-multiplicada (na simples, o padrao das Sprites sem TargetBlendMode, a cor sai um pouco mais
    escura: col x forma x alfa)."""
    a = _taper(w, h, nose, peak, wmax, rear_w, rear_fade, power) * alpha
    rgb = np.asarray(col)[None, None, :] * (a / alpha)[..., None]
    out = np.dstack([rgb, a])
    return Image.fromarray(np.round(np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")


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


def _serpent_y(d, f, frames, half, amp, waves, jit):
    """Linha central do corpo da Boitata na posicao d (0 = cabeca, 1 = ponta) no quadro f: cobra nadando. A
    amplitude e 0 ate d ~ 0,12 (o corpo sai reto da lanca, num traco so, sem forquilha onde a corona acaba), sobe
    suave ate um pico em d ~ 0,5 e depois CAI ~35% ate a ponta: corpo de serpente em S suave, nunca um flagelo que
    chicoteia mais na ponta. A onda corre para tras (1 volta por ciclo de animacao) e e um pouco mais longa no fim
    (fase ~ d^0,9)."""
    d = np.clip(d, 0, 1)
    env = _smooth(0.12, 0.5, d) * (1 - 0.35 * _smooth(0.5, 1.0, d))
    ph = 2 * math.pi * f / frames + jit
    return amp * half * env * np.sin(2 * math.pi * waves * d ** 0.9 - ph)


def tail(frames=8, fw=512, fh=64, body0=11.0, body1=2.6, amp=0.28, waves=1.1, licks=3.2, lick_px=1.5,
         segs=10, seg_gain=0.18, seg_mid=0.1, spine=0.9, gain=1.0, whiten=0.0, seed=5):
    """Atlas da cauda da Boitata (a serpente de fogo): um CORPO de plasma grosso que sai da lanca e afina ate a
    ponta (sigma body0 px na cabeca -> body1 px na ponta; a 30% do comprimento ainda tem ~3/4 da largura da
    cabeca), brilho que cai devagar (~40% em d = 0,7) e uma espinha branca que continua o nucleo da lanca. O corpo
    ondula em S suave (_serpent_y: amplitude <= amp * meia altura, maior no meio do corpo e menor na ponta). Por
    DENTRO do corpo correm duas labaredas finas e claras (fase oposta, amplitude <= meia largura do corpo: nada de
    fio solto fora da silhueta) e faixas de luz em V que lembram escamas e escorrem para tras (contraste seg_gain,
    mais seg_mid so no meio do corpo, d ~ 0,2-0,6: as escamas aparecem na escala de batalha sem mexer na ponta
    nem na amplitude). Por quadro o corpo anda 1 volta / frames e as labaredas e escamas 2 e 1 voltas / frames: a
    animacao fecha o ciclo. Um tremor pequeno de fase por quadro (seed fixa) tira a cara de mola."""
    per_row = 2
    rows = int(math.ceil(frames / per_row))
    atlas = np.zeros((rows * fh, per_row * fw, 3))
    x, y = _grid(fw, fh)
    half = fh / 2
    yc = y - half
    stops = _stops(whiten)
    rng = np.random.default_rng(seed)
    jit = [(rng.uniform(-0.12, 0.12), rng.uniform(-0.3, 0.3)) for _ in range(frames)]

    d = 1.0 - x / fw
    dd = 1.0 / fw
    col = _lerp_col(stops, d ** 0.85)
    hot = col * 0.35 + WHITE * 0.65
    # a frente do corpo fica DENTRO da corona: largura e brilho do corpo entram devagar (d ~ 0-0,12) em vez de
    # comecar num "paredao" vertical logo atras do nariz (aparecia como um degrau claro no zoom de perto)
    lead = _smooth(0.0, 0.12, d)
    wch = (body1 + (body0 - body1) * (1 - d) ** 1.15) * (0.6 + 0.4 * lead)
    bright = (1 - d) ** 0.8 * _head_fade(d, fw)
    lick_env = _smooth(0.02, 0.2, d) * (1 - d) ** 0.6
    seg_k = seg_gain + seg_mid * _smooth(0.12, 0.22, d) * (1 - _smooth(0.55, 0.68, d))
    for f in range(frames):
        jb, jl = jit[f]
        yb = _serpent_y(d, f, frames, half, amp, waves, jb)
        yb2 = _serpent_y(d + dd, f, frames, half, amp, waves, jb)
        dist = (yc - yb) / np.sqrt(1 + (yb2 - yb) ** 2)
        ad = np.abs(dist)
        L = np.exp(-0.5 * (ad / wch) ** 2)[..., None] * col * (0.95 * (0.3 + 0.7 * lead))[..., None]
        L += np.exp(-0.5 * (ad / (wch * 0.32)) ** 2)[..., None] * hot * (spine * (1 - d) ** 2.2)[..., None]
        pl = 4 * math.pi * f / frames + jl
        for s_, k in ((0, 1.0), (1, 0.55)):
            off = wch * 0.5 * np.sin(2 * math.pi * licks * d - pl + s_ * math.pi)
            th = lick_px * (1 - 0.4 * d)
            L += np.exp(-0.5 * ((dist - off) / th) ** 2)[..., None] * hot * (0.55 * k * lick_env)[..., None]
        ps = 2 * math.pi * f / frames
        seg = 1 + seg_k * np.cos(2 * math.pi * segs * (d + 1.2 * ad / fw) - ps)
        L = _soft(L * (bright * seg)[..., None] * gain, 1.3)
        vfade = np.clip((half - np.abs(yc)) / 3.0, 0, 1)
        _atlas_put(atlas, f, per_row, fw, fh, L * vfade[..., None])
    return _encode(atlas)


def wake(frames=8, fw=512, fh=64, rings=3, core_px=4.0, chan_px=10.5, gain=1.0, whiten=0.0, ring_gain=0.35,
         ring_from=0.45, fade_k=0.7, taper=0.6):
    """Atlas da cauda do Curupira: esteira ionizada RETA e grossa (os canos dele sao trilhos, nao a serpente da
    Boitata) que continua a corona pesada como o corpo de um cometa: nucleo branco e canal ciano que AFINAM da
    cabeca para a ponta (sigma do canal chan_px * 1,25 na cabeca -> * (1,25 - taper) na ponta; taper 0,8: a
    traseira fica fina, para o brilho espalhado nao virar uma faixa clara sobre casco branco) com o brilho caindo
    devagar perto da cabeca ((1 - d)^fade_k), entao a largura visivel so diminui, sem pescoco atras da cabeca.
    `rings` aneis de pulso (elipses finas vistas de lado, frente mais clara, altura presa a largura do canal) so
    na parte de tras (d >= ring_from, longe da cabeca: nenhum "no" marca um pescoco) correm para o fim da cauda
    apagando. Por quadro cada anel anda (1 - ring_from) / (rings * frames) do comprimento: a animacao fecha o
    ciclo. Um tremor lento no brilho do canal da a cara de plasma ionizado. ring_gain: forca dos aneis (discretos,
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
    fade = (1 - d) ** fade_k * _head_fade(d, fw)

    def chan(dd):
        return chan_px * (1.25 - taper * dd)
    # a frente da esteira fica DENTRO da corona: o canal largo entra devagar (largura e brilho sobem em d ~ 0-0,2)
    # em vez de comecar num "paredao" vertical logo atras do nariz; so o nucleo branco (que continua a lanca) entra
    # no ritmo normal do _head_fade
    lead = _smooth(0.0, 0.2, d)
    th = core_px * (1 - 0.55 * d)
    core = np.exp(-0.5 * (yc / th) ** 2)
    glow = np.exp(-0.5 * (yc / (chan(d) * (0.6 + 0.4 * lead))) ** 2) * (0.25 + 0.75 * lead)
    for f in range(frames):
        ph = f / frames
        shimmer = 1 + 0.12 * np.sin(2 * math.pi * (3 * d - ph)) + 0.08 * np.sin(2 * math.pi * (7 * d + 2 * ph))
        L = core[..., None] * hot * 1.6 * ((1 - d) ** 1.2)[..., None]
        L += glow[..., None] * col * 0.75 * shimmer[..., None]
        for k in range(rings):
            p = ring_from + (1 - ring_from) * (k + ph) / rings     # posicao do anel ao longo da cauda (0 = cabeca)
            xr = fw * (1 - p)
            rx = 2.5 + 3.5 * p
            ry = min(half - 5, chan(p) * 1.45)
            e = np.sqrt(((x - xr) / rx) ** 2 + (yc / ry) ** 2)
            ring = np.exp(-0.5 * ((e - 1) * ry / 2.0) ** 2)
            front = 0.55 + 0.45 * np.tanh((x - xr) / rx)
            band = np.exp(-0.5 * ((x - xr) / (rx * 1.4)) ** 2) * glow
            amp = (1 - p) ** 1.1 * min(1.0, (p - ring_from) / 0.1)
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
    from bsgen import plasma_fx as PFX          # posicoes do nariz que bolt_components() tambem usa
    return {
        "bs_plasma_lance.png": lance(nose=PFX.LANCE_NOSE),
        "bs_plasma_corona.png": corona(nose=PFX.CORONA_NOSE),
        "bs_plasma_corona_heavy.png": corona(nose=PFX.CORONA_NOSE, peak=0.68, wmax=0.8, rear_w=0.55, rear_fade=0.35),
        "bs_plasma_shade.png": shade(nose=PFX.SHADE_NOSE, peak=0.8, wmax=1.2, rear_w=0.45, rear_fade=0.5,
                                     alpha=0.6, col=(0.0, 0.22, 0.32), power=4),
        "bs_plasma_shade_heavy.png": shade(nose=PFX.SHADE_NOSE, peak=0.75, wmax=1.2, rear_w=0.5, rear_fade=0.45,
                                           alpha=0.62, col=(0.0, 0.22, 0.32), power=4),
        "bs_plasma_tail.png": tail(),
        "bs_plasma_tail_oc.png": tail(body0=11.5, gain=1.15, whiten=0.3, spine=1.1),
        "bs_plasma_wake.png": wake(taper=0.8),
        "bs_plasma_wake_oc.png": wake(core_px=4.6, chan_px=11.5, gain=1.15, whiten=0.3, taper=0.8),
        "bs_plasma_burst.png": burst(),
        "bs_plasma_splash.png": splash(),
        "bs_plasma_shock.png": shock_ring(),
    }
