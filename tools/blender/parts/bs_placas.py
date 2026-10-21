"""Placas de tipo (2.0): placa_<tipo>.png, 48 x 48, roof_doodads (com luz do jogo, sem emissao).

    $PY tools/blender/render_layered.py bs_placas [--quick] [--out DIR]

Spec de arte assets.plates: uma moldura 3D (moldura clara de bisel duplo com campo escuro rebaixado e 2 parafusos)
renderizada UMA vez; em PIL a silhueta do tipo e colada no campo, pintada na cor do tipo (palette[tipo] band/chip,
nunca o azul da interface), em baixo relevo (luz de cima-esquerda, como as torres). Usadas por:
  * paiois (MostradorTipo_<k>, uma por modo do seletor; projeteis = placa fixa), no tamanho do encaixe do teto
    (1x1 0,42 / 2x2 0,66 / 3x3 0,92 quadro);
  * tremonha (reserva) 0,42 e placas de modo das fabricas F2/F3/F4 0,8.
As silhuetas seguem as descricoes dos icones 2.0 (art_assets.ui_icons) e usam as primitivas de
tools/bsgen/ui_icons.py (Pen, shell, missile, bolt, star, trefoil): o mesmo desenho dos icones do seletor, so que
em cor de tipo e em relevo. Tamanho minimo de leitura: 27 px (paiol 1x1) -> formas cheias, nada mais fino que ~2 px.

Os 12 tipos (ordem do spec): he, ap, sap, ac, frag, plasma, pem, msl_he, msl_cluster, msl_emp, msl_nuke, slug.
"""

import math
import os
import tempfile

import numpy as np
from PIL import Image, ImageFilter

import bs3d as B
import models as Mo
from parts import _bs2_logistica_helpers as LG

PX_PLATE = 48
SIDE = PX_PLATE / 64.0                # 0,75 quadro
FIELD = 0.54                          # lado do campo escuro (quadros, de SIDE)
SSF = 4                               # superamostragem do simbolo

PART = {
    "id": "rafaeltessaro.bs_placas", "kind": "layered", "size": [1, 1], "accent": "amber",
    "walls": "none",
    "layers": [
        {"name": "placa", "fn": "pil:plate", "game_layer": "roof_doodads", "rect": [0.0, 0.0, SIDE, SIDE],
         "file": "placa_{v}.png", "variants": list(LG.KIND_ORDER)},
    ],
    "notes": [
        "placa_<tipo>.png: 48 x 48 px, desenhada pelas regras com Size = o tamanho do encaixe (paiol 1x1 0,42 / 2x2 "
        "0,66 / 3x3 0,92 quadro; tremonha 0,42; fabricas 0,8); camada roof_doodads, sem emissao (o jogo ilumina). "
        "O 'rect' do meta e so o tamanho nativo (0,75 quadro = 48 px); size [1, 1] e nominal.",
        "Cores: palette[tipo] band/chip do SPEC_2.0 (he ambar, ap branco-azulado, sap laranja, ac carmim + ouro, frag "
        "verde-agua, plasma ciano, pem azul + cobre, missil HE ambar, submunicao laranja, missil PEM azul, ogiva "
        "nuclear verde com trevo escuro, slug violeta + ouro).",
    ],
}

_CACHE = {}


# ============================================================================ moldura 3D (renderizada uma vez)
def _bezel():
    if "bezel" in _CACHE:
        return _CACHE["bezel"]
    import bpy
    B.reset()
    M = Mo.mats("amber")
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    B.camera(SIDE, SIDE, (0, 0))
    bpy.context.scene.cycles.samples = 64
    tags = ("bezel",)
    s = SIDE - 0.03
    fa, fp = B.shard("frame", B.rpoly(0, 0, s, s, 0, chamfer=0.075), 0.0, 0.06, A, slope=0.022, groove=0.014,
                     panel_h=0.016, tags=tags)
    hole = B.rpoly(0, 0, FIELD + 0.02, FIELD + 0.02, 0, chamfer=0.05)
    for t in (fa, fp):
        if t is not None:
            B.cut(t, [B.loft(f"hole{t.name}", hole, hole, 0.012, 0.5, K, bevel=0.0)])
    field = B.rpoly(0, 0, FIELD + 0.03, FIELD + 0.03, 0, chamfer=0.05)
    B.loft("field", field, field, 0.0, 0.016, B.mat_metal("lg_plate_field", (0.012, 0.013, 0.016), rough=0.55,
                                                           metal=0.3), bevel=0.0, tags=tags)
    for k, (sx, sy) in enumerate(((-1, 1), (1, -1))):
        c = (s / 2 - 0.052)
        B.cyl(f"bolt{k}", sx * c, sy * c, 0.078, 0.021, 0.018, S, axis="Z", verts=10, bevel=0.005, tags=tags)
    # 2 entalhes na moldura (cantos sem parafuso): linha de painel curta
    if fp is not None:
        B.cut(fp, [B.rbox(f"nick{k}", sx * (s / 2 - 0.05), sy * (s / 2 - 0.05), 0.010, 0.06, 0.07, 0.5, K,
                          rot=-sx * sy * 45, bevel=0.0) for k, (sx, sy) in enumerate(((1, 1), (-1, -1)))])
    B.show_only(["bezel"])
    tmp = tempfile.mkdtemp(prefix="bs_placas_")
    res = B.render_set(os.path.join(tmp, "bezel"), (PX_PLATE, PX_PLATE), glow_halo=False, normals=False, off=False)
    img = res["on"].copy()
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    _CACHE["bezel"] = img
    return img


# ============================================================================ silhuetas (Pen dos icones 2.0)
def _pen():
    from bsgen import ui_icons as U
    return U, U.Pen()


def _capsule(p, cx, top, bottom, w, layer="body"):
    r = w / 2
    pts = []
    for i in range(13):
        a = math.pi + math.pi * i / 12
        pts.append((cx + r * math.cos(a), top + r + r * math.sin(a)))
    for i in range(13):
        a = math.pi * i / 12
        pts.append((cx + r * math.cos(a), bottom - r + r * math.sin(a)))
    p.poly(pts, layer)


def silhouette(kind):
    """Mascaras (corpo, destaque) do tipo, Image 'L' em 96 x 96 x SS (as do Pen)."""
    U, p = _pen()
    if kind == "he":
        U.shell(p, 48, 10, 86, 32, tip=0.42, sharp=0.9)
        p.gap(30, 60, 66, 62.8)                              # fresta da luva
    elif kind == "ap":
        cx = 48
        p.poly([(cx, 6), (cx + 6, 26), (cx + 6, 50), (cx - 6, 50), (cx - 6, 26)])
        p.poly([(cx - 13, 46), (cx + 13, 46), (cx + 15, 53), (cx - 15, 53)])
        p.rect(cx - 14, 53, cx + 14, 84)
        p.rect(cx - 16, 84, cx + 16, 90)
        p.gap(cx - 17, 53, cx + 17, 55.6)
        p.gap(cx - 17, 68, cx + 17, 70.4)
        p.gap(cx - 17, 81.2, cx + 17, 83.4)
    elif kind == "sap":
        U.shell(p, 42, 16, 86, 30, tip=0.30, sharp=0.15)     # ponta rombuda
        p.gap(24, 60, 60, 62.6)
        U.star(p, 68, 30, 6.5, 15, n=7, rot=8)
    elif kind == "ac":
        cx = 48
        U.shell(p, cx, 8, 86, 26, tip=0.42, sharp=1.1)
        for s in (-1, 1):                                    # canards (frente) e aletas (cauda)
            p.poly([(cx + s * 12, 34), (cx + s * 22, 42), (cx + s * 22, 46), (cx + s * 12, 44)])
            p.poly([(cx + s * 13, 64), (cx + s * 24, 76), (cx + s * 24, 84), (cx + s * 13, 82)])
        p.rect(cx - 13.5, 50, cx + 13.5, 57, "acc")          # faixa dourada
        p.gap(cx - 14, 49, cx + 14, 50.2)
    elif kind == "frag":
        cx = 48
        U.shell(p, cx, 46, 88, 30, tip=0.36, sharp=0.6)
        p.gap(30, 70, 66, 72.4)
        for i, ang in enumerate((-60, -40, -20, 0, 20, 40, 60)):   # leque de 7 tracos para a frente
            a = math.radians(ang)
            r0, r1 = 14, 31 if i % 2 == 0 else 26
            x0, y0 = cx + math.sin(a) * r0, 46 - math.cos(a) * r0
            x1, y1 = cx + math.sin(a) * r1, 46 - math.cos(a) * r1
            nx, ny = math.cos(a) * 2.6, math.sin(a) * 2.6
            p.poly([(x0 - nx, y0 - ny), (x0 + nx, y0 + ny), (x1 + nx * 0.6, y1 + ny * 0.6), (x1 - nx * 0.6, y1 - ny * 0.6)],
                   "acc")
    elif kind == "plasma":
        _capsule(p, 48, 8, 88, 36)
        p.gap(26, 22, 70, 24.4)
        p.gap(26, 72, 70, 74.4)
        p.rect(38, 30, 58, 66, "acc")                        # janela do nucleo
        p.gap(36, 28, 60, 30.6)
        p.gap(36, 65.6, 60, 68)
    elif kind == "pem":
        _capsule(p, 38, 8, 88, 32)
        for y in (26, 44, 62):                               # 3 aneis de bobina (cobre)
            p.rect(21, y, 55, y + 8, "acc")
            p.gap(20, y - 2, 56, y - 0.4)
        U.bolt(p, 58, 14, 1.0, "body")
    elif kind == "msl_he":
        U.missile(p, 48, 6, 90, 22)
        for y in (38, 52):
            p.gap(34, y, 62, y + 2.4)
    elif kind == "msl_cluster":
        U.missile(p, 48, 58, 92, 20, fin=0.8, nose=0.05)
        for sd in (-1, 1):
            p.poly([(48 + sd * 10, 60), (48 + sd * 4, 60), (48 + sd * 14, 50), (48 + sd * 18, 53)])
        for ang, r in ((-50, 25), (-17, 30), (17, 30), (50, 25), (-34, 45), (0, 47), (34, 45)):
            p.at(48 + r * math.sin(math.radians(ang)), 56 - r * math.cos(math.radians(ang)), ang)
            p.poly([(0, -10), (5, 6), (0, 3), (-5, 6)], "acc")
            p.at()
    elif kind == "msl_emp":
        U.missile(p, 40, 8, 90, 20)
        for y in (40, 50, 60):                               # bobinas
            p.gap(28, y, 52, y + 2.2)
        U.bolt(p, 52, 18, 1.15)
    elif kind == "msl_nuke":
        w = 30
        left, right = U.ogive(48, 8, 40, w, sharp=0.15)
        p.poly(left + [(48 - w / 2, 80), (48 + w / 2, 80)] + right[::-1])
        for s in (-1, 1):
            p.poly([(48 + s * w / 2, 62), (48 + s * (w / 2 + 8), 74), (48 + s * (w / 2 + 8), 88),
                    (48 + s * w / 2, 82)])
        p.poly([(40, 80), (56, 80), (58, 90), (38, 90)])
        # trevo ESCURO recortado na ogiva (cunhas transparentes)
        for k in range(3):
            a0 = math.radians(-90 + k * 120 - 30)
            a1 = math.radians(-90 + k * 120 + 30)
            r, cx, cy = 11.5, 48, 46
            pts = [(cx + r * 0.30 * math.cos(a0), cy + r * 0.30 * math.sin(a0))]
            pts += [(cx + r * math.cos(a0 + (a1 - a0) * i / 10), cy + r * math.sin(a0 + (a1 - a0) * i / 10))
                    for i in range(11)]
            pts.append((cx + r * 0.30 * math.cos(a1), cy + r * 0.30 * math.sin(a1)))
            p.poly(pts, "body", 0)
            p.poly(pts, "acc", 0)
        p.circle(48, 46, 2.2, "body", 0)
    elif kind == "slug":
        cx = 48
        p.poly([(cx, 4), (cx + 7, 18), (cx + 7, 86), (cx - 7, 86), (cx - 7, 18)])
        for s in (-1, 1):                                    # 3 aletas da cauda
            p.poly([(cx + s * 7, 66), (cx + s * 18, 80), (cx + s * 18, 90), (cx + s * 7, 86)])
        for y in (26, 40, 54):                               # aneis da armadura (ouro)
            p.rect(cx - 13, y, cx + 13, y + 6, "acc")
    else:
        raise ValueError(kind)
    return p.m["body"], p.m["acc"]


def _relief(mask, color, light=0.42):
    """Cor + baixo relevo: borda de cima-esquerda clara, de baixo-direita escura, leve degrade vertical."""
    a = np.asarray(mask, dtype=np.float32) / 255.0
    h, w = a.shape
    d = max(1, int(round(w / 48)))
    sh_dr = np.zeros_like(a)
    sh_dr[d:, d:] = a[:-d, :-d]
    sh_ul = np.zeros_like(a)
    sh_ul[:-d, :-d] = a[d:, d:]
    hi = np.clip(a - sh_dr, 0, 1)
    lo = np.clip(a - sh_ul, 0, 1)
    grad = np.linspace(1.08, 0.88, h)[:, None]
    base = np.array(color, dtype=np.float32)[None, None, :]
    rgb = base * grad[..., None] * (1 + light * hi[..., None] - 0.55 * lo[..., None])
    rgb = rgb + 255 * 0.18 * hi[..., None]
    return np.clip(rgb, 0, 255), a


def symbol(kind, size):
    """Simbolo colorido em relevo (RGBA size x size) do tipo."""
    body, acc = silhouette(kind)
    big = size * SSF
    # o Pen desenha em 96 x SS; a area util (FIT 0,78) e recortada pela caixa das mascaras
    both = Image.fromarray(np.maximum(np.asarray(body), np.asarray(acc)))
    bb = both.getbbox()
    side = max(bb[2] - bb[0], bb[3] - bb[1])
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    box = (int(cx - side / 2), int(cy - side / 2), int(cx + side / 2), int(cy + side / 2))
    body = body.crop(box).resize((big, big), Image.LANCZOS)
    acc = acc.crop(box).resize((big, big), Image.LANCZOS)
    col = LG.KIND[kind]
    rgb_b, a_b = _relief(body, col["body"])
    out = np.zeros((big, big, 4), np.float32)
    out[..., :3] = rgb_b
    out[..., 3] = a_b * 255
    if col["acc"] is not None:
        rgb_a, a_a = _relief(acc, col["acc"])
        k = a_a[..., None]
        out[..., :3] = out[..., :3] * (1 - k) + rgb_a * k
        out[..., 3] = np.maximum(out[..., 3], a_a * 255)
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    # sombra curta (relevo): mascara escura deslocada para baixo-direita
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sa = np.asarray(im.split()[-1], dtype=np.float32) * 0.85
    shadow.putalpha(Image.fromarray(sa.astype(np.uint8)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(SSF * 0.6))
    base = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    base.alpha_composite(shadow, (SSF, SSF))
    base.alpha_composite(im)
    return base.resize((size, size), Image.LANCZOS)


def plate(P, layer, px, variant="he", **kw):
    img = _bezel().copy()
    fpx = int(round(FIELD * 64))                              # 32 px de campo
    sym = symbol(variant, fpx - 2)
    o = (PX_PLATE - sym.width) // 2
    img.alpha_composite(sym, (o, o))
    return img
