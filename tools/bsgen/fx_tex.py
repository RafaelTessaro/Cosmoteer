"""Texturas compartilhadas dos efeitos 2.0 (WP03), geradas com numpy + PIL a cada build (deterministico: sementes
fixas), no idioma de bsgen/plasma_tex.py (luz L float -> RGBA aditivo por plasma_tex._encode: alfa = canal mais
forte, RGB = cor normalizada). Saida: BulletStrike/shots/bs_fx_tex/ (SPEC.art_assets.assets.fx_textures).

  bs_ring_thin.png    256x256          anel fino BRANCO (aro de 6 px, borda suave de 3 px, centro transparente):
                                       tingido por uso (AC dourado, PEM ciano, Tupa glow azul, FRAG radial); o
                                       railgun_shoot.png vanilla e ciano e nao recolore por multiplicacao
  bs_rail_streak.png  512x384 (8 x 256x96, 2 por linha)  risco do slug da Tupa: nucleo branco-azulado
                                       (palette.rail.core), franja azul (palette.rail.blue) e 2 bojos de anel
                                       (palette.rail.glow) andando para tras; AnimatedSprite 30 qps (WP09)
  bs_pem_sheath.png   512x192 (4 x 256x96)   bainha de plasma ciano que tremula em volta da granada PEM (WP08)
  bs_pem_trail.png    1024x256 (8 x 512x64, 2 por linha) cauda de raio bifurcado da granada PEM pesada (formato da
                                       cauda do plasma, plasma_fx: FrameSize [512, 64], 2 por linha) (WP08)
  bs_frag_cone.png    128x128          leque aditivo de ~44 graus com riscos radiais, vertice no centro da borda
                                       esquerda (+x = para a frente): o cone de fragmentos da FRAG (art.frag_cone)

Orientacao igual a das texturas vanilla de projetil: a FRENTE e +X (direita). Nos atlas a cabeca de cada quadro
termina num vao transparente (plasma_tex.GUTTER) para o quadro vizinho nao vazar com MipLevels = max.
Cores: assadas da paleta 2.0 (tools/spec/bullet_strike_art2.json via fxkit.palette()); o rail e AZUL (nada de
ouro/violeta, ADDENDUM G2/WP09).

Modulo de CONTEUDO do registro do build_mod (API 2, gancho write): nunca desligado pelo BS_FX_EXT (a linha PEM e a
Tupa usam estas texturas mesmo num build sem os efeitos por calibre).
"""

import os

import numpy as np
from PIL import Image

from bsgen import fxkit as FXK
from bsgen import plasma_tex as PT

API = 2
DIR = "shots/bs_fx_tex"
GUTTER = PT.GUTTER


def ref(name, frm="shot"):
    """Caminho da textura visto de um .rules gerado: frm "shot" (shots/<pasta>/x.rules) -> ../bs_fx_tex/<name>;
    "part" (parts/<id>/x.rules) -> ../../shots/bs_fx_tex/<name>."""
    if frm == "shot":
        return f"../{DIR.split('/', 1)[1]}/{name}"
    if frm == "part":
        return f"../../{DIR}/{name}"
    raise ValueError(f"frm deve ser 'shot' ou 'part', veio {frm!r}")


def _c(rgb):
    return np.array(rgb, dtype=float) / 255.0


def _white_alpha(a):
    """Textura branca tingivel: RGB = 1, alfa = a (0..1)."""
    a = np.clip(a, 0, 1)
    out = np.dstack([np.ones(a.shape + (3,)), a])
    return Image.fromarray(np.round(out * 255).astype(np.uint8), "RGBA")


# ----------------------------------------------------------------------------- anel fino
def ring_thin(s=256, radius_px=110.0, core_px=3.0, soft_px=3.0):
    """Anel branco: alfa 1 numa faixa de 2 x core_px (6 px) em volta do raio, caindo a 0 em soft_px (3 px) de cada
    lado; centro e cantos transparentes."""
    x, y = PT._grid(s, s)
    d = np.abs(np.hypot(x - s / 2, y - s / 2) - radius_px)
    a = 1.0 - PT._smooth(core_px, core_px + soft_px, d)
    return _white_alpha(a)


# ----------------------------------------------------------------------------- risco do slug (Tupa)
def rail_streak(frames=8, fw=256, fh=96, per_row=2):
    """Risco do slug: nucleo fino branco-azulado que afina para tras, franja azul mais larga e 2 bojos de anel
    (elipses finas, glow) que andam da cabeca para a cauda ao longo dos quadros."""
    pal = FXK.pal("rail")
    core, blue, glow = _c(pal["core"]), _c(pal["blue"]), _c(pal["glow"])
    rows = -(-frames // per_row)
    atlas = np.zeros((rows * fh, per_row * fw, 3))
    x, y = PT._grid(fw, fh)
    u = x / fw                      # 0 = cauda (esquerda), 1 = cabeca (direita)
    v = (y - fh / 2) / (fh / 2)
    head = 1.0 - (GUTTER + 6) / fw
    d = np.clip((head - u) / head, 0, 1)        # 0 na cabeca, 1 na cauda
    on = (u <= head + 0.004).astype(float) * PT._smooth(0.0, 0.06, u)
    for f in range(frames):
        w_core = 0.06 * (1 - 0.7 * d) + 0.012
        core_l = np.exp(-(v / w_core) ** 2) * (1 - d) ** 1.4
        w_fr = 0.24 * (1 - 0.5 * d) + 0.03
        fringe = np.exp(-(v / w_fr) ** 2) * (1 - d) ** 1.1 * 0.55
        rings = np.zeros_like(u)
        for k in range(2):
            ph = ((f / frames) + k * 0.5) % 1.0          # posicao do bojo: anda para tras
            cx = head - (0.12 + 0.72 * ph) * head
            rx, ry = 0.022 + 0.02 * ph, 0.55 + 0.35 * ph
            rr = np.hypot((u - cx) / rx, v / ry)
            rings += np.exp(-((rr - 1.0) / 0.22) ** 2) * (1 - ph) ** 1.2 * 0.8
        L = core_l[..., None] * (core * 1.8) + fringe[..., None] * blue + rings[..., None] * glow
        L = PT._soft(L, 1.3) * on[..., None]
        PT._atlas_put(atlas, f, per_row, fw, fh, L)
    return PT._encode(atlas)


# ----------------------------------------------------------------------------- PEM: bainha e cauda
def pem_sheath(frames=4, fw=256, fh=96, per_row=2, seed=23):
    """Bainha de plasma ciano em volta da capsula: casca eliptica com brilho na borda e fiapos que tremulam
    (ruido por quadro)."""
    pal = FXK.pal("pem")
    core, band, glow = _c(pal["core"]), _c(pal["band"]), _c(pal["glow"])
    rng = np.random.default_rng(seed)
    rows = -(-frames // per_row)
    atlas = np.zeros((rows * fh, per_row * fw, 3))
    x, y = PT._grid(fw, fh)
    u = (x - fw / 2) / (fw / 2)
    v = (y - fh / 2) / (fh / 2)
    for f in range(frames):
        ang = np.arctan2(v, u)
        wob = 0.025 * np.sin(5 * ang + rng.uniform(0, 6.3)) + 0.015 * np.sin(11 * ang + rng.uniform(0, 6.3))
        rr = np.hypot(u / 0.82, v / 0.72) - wob
        shell = np.exp(-((rr - 0.78) / 0.10) ** 2)
        inner = np.exp(-(rr / 0.62) ** 2) * 0.25
        fil = np.zeros_like(u)
        for _ in range(5):
            a0 = rng.uniform(-np.pi, np.pi)
            da = np.angle(np.exp(1j * (ang - a0)))
            fil += np.exp(-(da / 0.09) ** 2) * np.exp(-((rr - 0.86) / 0.16) ** 2) * rng.uniform(0.4, 0.9)
        L = shell[..., None] * band * 0.9 + fil[..., None] * (core * 0.6 + glow * 0.4) + inner[..., None] * glow
        edge = np.clip(np.minimum((1 - np.abs(u)) / 0.06, (1 - np.abs(v)) / 0.08), 0, 1)
        PT._atlas_put(atlas, f, per_row, fw, fh, PT._soft(L, 1.2) * edge[..., None])
    return PT._encode(atlas)


def _bolt_path(rng, n, x0, x1, y0, amp):
    """Polilinha em zigue-zague de x0 a x1 (px) em torno de y0."""
    xs = np.linspace(x0, x1, n)
    ys = y0 + np.cumsum(rng.normal(0, amp, n))
    ys -= np.linspace(0, ys[-1] - y0, n) * 0.6
    return list(zip(xs, ys))


def _draw_path(px, py, pts, width):
    best = np.full(px.shape, 1e9)
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        dist, _t = PT._segment(px, py, xa, ya, xb, yb)
        best = np.minimum(best, dist)
    return np.exp(-(best / width) ** 2)


def pem_trail(frames=8, fw=512, fh=64, per_row=2, seed=31):
    """Cauda de raio bifurcado: um raio principal em zigue-zague da cabeca (direita) para tras, com 1-2 galhos,
    branco-ciano perto da cabeca e azul apagando na cauda; cada quadro um raio diferente (8 quadros, 30 qps)."""
    pal = FXK.pal("pem")
    core, band, glow = _c(pal["core"]), _c(pal["band"]), _c(pal["glow"])
    rng = np.random.default_rng(seed)
    rows = -(-frames // per_row)
    atlas = np.zeros((rows * fh, per_row * fw, 3))
    x, y = PT._grid(fw, fh)
    head = fw - GUTTER - 4
    d = np.clip((head - x) / head, 0, 1)
    for f in range(frames):
        main = _bolt_path(rng, 22, head, head * 0.08, fh / 2, 2.6)
        L = _draw_path(x, y, main, 1.3)[..., None] * core * 1.6 + _draw_path(x, y, main, 4.0)[..., None] * band * 0.7
        for _ in range(int(rng.integers(1, 3))):
            i = int(rng.integers(3, 12))
            xs, ys = main[i]
            br = _bolt_path(rng, 8, xs, xs - rng.uniform(60, 150), ys, 3.2)
            L += _draw_path(x, y, br, 1.0)[..., None] * (core * 0.5 + glow * 0.6)
        L *= ((1 - d) ** 1.3)[..., None]
        L *= PT._head_fade(1 - x / fw, fw)[..., None]
        PT._atlas_put(atlas, f, per_row, fw, fh, PT._soft(L, 1.2))
    return PT._encode(atlas)


# ----------------------------------------------------------------------------- FRAG: leque
def frag_cone(s=128, half_deg=22.0, seed=41, n_streaks=14):
    """Leque aditivo branco: vertice no centro da borda esquerda, abertura 2 x half_deg (44 graus), riscos radiais
    (um por fragmento, mais um veu fraco) que apagam ate a borda direita."""
    rng = np.random.default_rng(seed)
    x, y = PT._grid(s, s)
    dx, dy = x, y - s / 2
    r = np.hypot(dx, dy) / s
    ang = np.degrees(np.arctan2(dy, np.maximum(dx, 1e-6)))
    wedge = 1.0 - PT._smooth(half_deg - 4, half_deg + 1, np.abs(ang))
    veil = wedge * 0.22
    streaks = np.zeros_like(r)
    for a0 in np.linspace(-half_deg + 2, half_deg - 2, n_streaks) + rng.uniform(-1.2, 1.2, n_streaks):
        streaks += np.exp(-((ang - a0) / 0.9) ** 2) * rng.uniform(0.55, 1.0)
    a = (veil + np.clip(streaks, 0, 1) * wedge) * np.clip(r / 0.06, 0, 1) * (1 - PT._smooth(0.55, 0.98, r))
    return _white_alpha(a)


TEXTURES = {
    "bs_ring_thin.png": ((256, 256), ring_thin),
    "bs_rail_streak.png": ((512, 384), rail_streak),
    "bs_pem_sheath.png": ((512, 192), pem_sheath),
    "bs_pem_trail.png": ((1024, 256), pem_trail),
    "bs_frag_cone.png": ((128, 128), frag_cone),
}


def all_textures():
    """{nome: imagem} das 5 texturas (tamanhos conferidos)."""
    out = {}
    for name, (size, fn) in TEXTURES.items():
        im = fn()
        if im.size != size:
            raise ValueError(f"fx_tex {name}: {im.size} != {size}")
        out[name] = im
    return out


def write(out, header):
    """Gancho write (registro do build_mod, WP01): grava as texturas em shots/bs_fx_tex/ (sempre: PIL e rapido)."""
    for name, im in all_textures().items():
        out.image(f"{DIR}/{name}", im)


def selfcheck(mod_dir, spec):
    probs = []
    for name, (size, _fn) in TEXTURES.items():
        p = os.path.join(mod_dir, DIR, name)
        if not os.path.isfile(p):
            probs.append(f"{DIR}/{name} nao foi escrita")
            continue
        with Image.open(p) as im:
            if im.size != size or im.mode != "RGBA":
                probs.append(f"{DIR}/{name}: {im.size} {im.mode} (esperado {size} RGBA)")
    return probs
