"""FX da Fita (2.0, primario): cartuchos saindo / entrando de uma maquina ligada a fita (teletransporte).

    $PY tools/blender/render_layered.py bs_fita_fx [--quick] [--out DIR]

Spec de arte assets.fita_fx: um so conjunto para TODAS as maquinas e TODOS os tipos (o cassete e neutro), 1 quadro
no centro da maquina, 8 quadros x 0,075 s = 0,6 s (o Timer das maquinas: SaindoRecente / EntrandoRecente).
  * cartucho_sai1..8.png (roof_doodads, alfa): 2 cassetes selados neutros (capsula escura + faixa de latao + 1 pip
    ambar) sobem do centro, deslizam para as bordas e SOMEM no teletransporte (linhas de varredura, tom ciano, o
    cassete se espreme numa linha vertical ciano e apaga);
  * cartucho_entra1..8.png: o inverso exato (entra_k = sai_(9 - k)): aparecem na borda como uma linha ciano que se
    abre no cassete, deslizam para o centro e descem para dentro da maquina;
  * brilho_sai1..8.png / brilho_entra1..8.png (lights_add, aditivo opaco sobre preto): rastro ciano BAIXO sob os
    cassetes (canal mais fraco 0, nunca branco) e o lampejo fraco do teletransporte na borda.
Em envio continuo (a cada 0,1 s) o Timer fica ligado e a animacao roda em laco: o quadro 8 (cassetes sumindo nas
bordas) emenda no quadro 1 (novos cassetes surgindo no centro).

O cassete e um modelo 3D (parts/_bs2_logistica_helpers.cassette, o mesmo das estantes do piso dos paiois),
renderizado uma vez em alta resolucao; os quadros sao montados em PIL (posicao com subpixel, escala, sombra e o
efeito do teletransporte), por isso as camadas sao "pil:".
"""

import math
import os
import tempfile

import numpy as np
from PIL import Image, ImageFilter

import bs3d as B
import models as Mo
from parts import _bs2_logistica_helpers as LG

N = 8
INTERVAL = 0.075
HI = 8                                # superamostragem dos quadros (o cassete e renderizado a 64 x HI px por quadro)

PART = {
    "id": "rafaeltessaro.bs_fita_fx", "kind": "layered", "size": [1, 1], "accent": "amber",
    "walls": "none",
    "layers": [
        {"name": "cartucho_sai", "fn": "pil:cassettes_out", "game_layer": "roof_doodads", "file": "cartucho_sai{i}.png",
         "frames": N, "interval": INTERVAL, "islands": True},
        {"name": "cartucho_entra", "fn": "pil:cassettes_in", "game_layer": "roof_doodads",
         "file": "cartucho_entra{i}.png", "frames": N, "interval": INTERVAL, "islands": True},
        {"name": "brilho_sai", "fn": "pil:glow_out", "game_layer": "lights_add", "file": "brilho_sai{i}.png",
         "frames": N, "interval": INTERVAL, "blend": "add", "islands": True},
        {"name": "brilho_entra", "fn": "pil:glow_in", "game_layer": "lights_add", "file": "brilho_entra{i}.png",
         "frames": N, "interval": INTERVAL, "blend": "add", "islands": True},
    ],
    "notes": [
        "Um conjunto so para todas as maquinas e tipos: Graphics com Location = centro da maquina e Size [1, 1]; "
        "cartucho_* em roof_doodads (OperationalRoofDoodad), brilho_* em lights_add (OperationalLighting), "
        "AnimationInterval 0,075 (8 quadros = 0,6 s = o Timer SaindoRecente / EntrandoRecente).",
        "Em envio continuo a animacao roda em laco: o quadro 8 emenda no quadro 1.",
        "brilho_*: aditivo opaco sobre preto (como os PNGs de luz vanilla), ciano puro com o canal vermelho 0 "
        "(canal mais fraco <= 25, spec) e pico baixo (~ 120).",
    ],
}

_CACHE = {}


# ============================================================================ cassete renderizado (uma vez)
def _cassette_sprite():
    """Cassete visto de cima (eixo longo vertical), renderizado a 64 x HI px por quadro; tela 0,40 x 0,40."""
    if "spr" in _CACHE:
        return _CACHE["spr"]
    B.reset()
    M = Mo.mats("amber")
    X = LG.mats(M)
    side = 0.40
    B.camera(side, side, (0, 0), px=64 * HI)
    bpy_samples(48)
    LG.cassette("cass", 0, 0, 0.0, M, X, ("cass",))
    B.show_only(["cass"])
    tmp = tempfile.mkdtemp(prefix="bs_fita_fx_")
    px = int(round(side * 64 * HI))
    res = B.render_set(os.path.join(tmp, "cass"), (px, px), glow_halo=True, normals=False, off=False)
    spr = res["on"].copy()
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    _CACHE["spr"] = spr
    return spr


def bpy_samples(n):
    import bpy
    bpy.context.scene.cycles.samples = n


# ============================================================================ quadros
def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def _state(k):
    """Estado do quadro k (1..8) da SAIDA: deslocamento x (quadros), escala, alfa, esmagamento (largura), tom ciano,
    linhas de varredura e linha do teletransporte."""
    t = (k - 1) / (N - 1)
    off = 0.085 + 0.285 * _smooth(t / 0.78)
    scale = 0.80 + 0.20 * _smooth(t / 0.30)
    lift = _smooth(t / 0.35)                      # sombra cresce enquanto o cassete sobe
    tele = _smooth((t - 0.50) / 0.50)             # 0 -> 1 no teletransporte
    squeeze = 1.0 - 0.92 * _smooth((t - 0.62) / 0.38)
    alpha = 1.0 - 0.80 * tele
    return {"off": off, "scale": scale, "lift": lift, "tele": tele, "squeeze": squeeze, "alpha": alpha, "t": t}


def _frame_cassettes(k):
    spr = _cassette_sprite()
    st = _state(k)
    W = 64 * HI
    out = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    for sx in (-1, 1):
        s = st["scale"]
        w = max(2, int(round(spr.width * s * st["squeeze"])))
        h = max(2, int(round(spr.height * s)))
        im = spr.resize((w, h), Image.LANCZOS)
        a = np.asarray(im, dtype=np.float32).copy()
        tele = st["tele"]
        if tele > 0:
            # tom ciano + linhas de varredura horizontais (holograma desfazendo) + borda clara
            cy = np.array([0.0, 200.0, 235.0])
            a[..., :3] = a[..., :3] * (1 - 0.65 * tele) + cy * 0.65 * tele
            rows = (np.arange(h) // max(1, HI // 2)) % 2 == 0
            a[rows, :, 3] *= (1 - 0.75 * tele)
        a[..., 3] *= st["alpha"]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        cx = W / 2 + sx * st["off"] * 64 * HI
        cy_ = W / 2
        # sombra (o cassete sobe da maquina): escura, deslocada para baixo-direita, borrada
        if st["lift"] > 0.05 and st["tele"] < 0.9:
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
            al = np.asarray(im.split()[-1], dtype=np.float32) * 0.45 * st["lift"] * (1 - st["tele"])
            sh.putalpha(Image.fromarray(al.astype(np.uint8)))
            sh = sh.filter(ImageFilter.GaussianBlur(1.6 * HI))
            d = int(round((0.025 + 0.03 * st["lift"]) * 64 * HI))
            out.alpha_composite(sh, (int(round(cx - im.width / 2 + d)), int(round(cy_ - im.height / 2 + d))))
        out.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy_ - im.height / 2))))
        # linha do teletransporte (vertical, ciano) no fim
        if st["tele"] > 0.35:
            ln = Image.new("RGBA", (W, W), (0, 0, 0, 0))
            la = np.zeros((W, W), np.float32)
            hh = h * (0.55 + 0.45 * st["tele"])
            y0, y1 = int(cy_ - hh / 2), int(cy_ + hh / 2)
            lw = max(2, int(0.022 * 64 * HI * (1.2 - 0.6 * st["tele"])))
            x0 = int(round(cx - lw / 2))
            prof = np.sin(np.linspace(0, math.pi, y1 - y0)) ** 0.6
            la[y0:y1, x0:x0 + lw] = (prof[:, None] * 255 * min(1.0, (st["tele"] - 0.35) * 2.2) *
                                     (1.0 if k < N else 0.55))
            ln = Image.fromarray(np.dstack([np.full((W, W), 150, np.uint8), np.full((W, W), 235, np.uint8),
                                            np.full((W, W), 255, np.uint8), la.astype(np.uint8)]), "RGBA")
            out.alpha_composite(ln.filter(ImageFilter.GaussianBlur(0.6 * HI)))
            out.alpha_composite(ln)
    return out.resize((64, 64), Image.LANCZOS)


def _frame_glow(k):
    """Rastro ciano baixo sob os cassetes (aditivo, opaco sobre preto)."""
    st = _state(k)
    W = 64 * HI
    a = np.zeros((W, W), np.float32)
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32) / (64 * HI) - 0.5     # quadros, centro = 0
    for sx in (-1, 1):
        x = sx * st["off"]
        # rastro do centro ate o cassete (faixa horizontal fina que esmaece para o centro)
        lo, hi = (0.0, x) if sx > 0 else (x, 0.0)
        u = np.clip((xx - lo) / max(1e-3, hi - lo), 0, 1)
        u = u if sx > 0 else 1 - u
        band = np.exp(-(yy / 0.055) ** 2) * (u ** 1.5) * ((xx >= lo) & (xx <= hi))
        a += band * 0.55 * (1 - 0.5 * st["tele"])
        # brilho sob o cassete e lampejo do teletransporte
        blob = np.exp(-(((xx - x) / 0.10) ** 2 + (yy / 0.16) ** 2))
        a += blob * (0.35 + 0.65 * st["tele"]) * (1.0 if k < N else 0.5)
    a = np.clip(a, 0, 1.2)
    peak = 120.0
    rgb = np.dstack([np.zeros_like(a), a * peak * 0.86, a * peak]).clip(0, 255)
    im = Image.fromarray(np.dstack([rgb, np.full((W, W), 255.0)]).astype(np.uint8), "RGBA")
    return im.filter(ImageFilter.GaussianBlur(1.2 * HI)).resize((64, 64), Image.LANCZOS)


def cassettes_out(P, layer, px, frame=1, **kw):
    return _frame_cassettes(frame)


def cassettes_in(P, layer, px, frame=1, **kw):
    return _frame_cassettes(N + 1 - frame)


def glow_out(P, layer, px, frame=1, **kw):
    return _frame_glow(frame)


def glow_in(P, layer, px, frame=1, **kw):
    return _frame_glow(N + 1 - frame)
