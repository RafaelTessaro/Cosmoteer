"""Placas de tipo (2.0): placa_<tipo>.png, 48 x 48, roof_doodads (com luz do jogo, sem emissao).

    $PY tools/blender/render_layered.py bs_placas [--quick] [--out DIR]

Spec de arte assets.plates: "one Blender bezel (dark recessed frame, 2 bolts) rendered once; PIL pastes the ui_icons
silhouette of the kind recoloured to palette[kind] band/chip (not the UI blue) into the bezel".

  * moldura: aro ESCURO de grafite (core_mid) com bisel duplo, campo preto rebaixado e 2 parafusos de aco nos cantos
    opostos (os outros 2 cantos com um entalhe). Escura de proposito: no encaixe claro do paiol a silhueta colorida
    salta, sem o anel branco de "adesivo";
  * silhueta: a MESMA dos botoes do seletor 2.0. As mascaras vem das proprias funcoes de tools/bsgen/ui_icons.py
    (icon_ammo2 / icon_cell / icon_missile2 / icon_slug): o Pen e trocado por um que devolve as mascaras em vez de
    pintar o azul da interface, entao a placa do paiol e sempre o botao que o jogador acabou de clicar;
  * cor: corpo = cor do tipo (palette[tipo]), destaque do icone = 2a cor, e regioes do corpo com cor propria
    (bobinas de cobre do P.E.M. e do Poraque, minimisseis da submunicao, cauda laranja do slug), helpers.KIND;
    baixo relevo com a luz de cima-esquerda (como as torres) e sombra curta;
  * paint_safe(): nenhum pixel fica na chave de pintura do jogo (STYLE.md 9), nem nas bordas do verde nuclear.

Usadas por: paiois (MostradorTipo_<k>, uma por modo do seletor; projeteis = placa fixa) no encaixe do teto (1x1 0,42 /
2x2 0,66 / 3x3 0,92 quadro), tremonha (reserva) 0,42 e placas de modo das fabricas F2/F3/F4 0,8. Leitura minima:
27 px (paiol 1x1) -> campo grande (0,60 de 0,75) e as formas cheias dos icones.

Os 12 tipos (ordem do spec): he, ap, sap, ac, frag, plasma, pem, msl_he, msl_cluster, msl_emp, msl_nuke, slug.
"""

import os
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import bs3d as B
import models as Mo
from parts import _bs2_logistica_helpers as LG

PX_PLATE = 48
SIDE = PX_PLATE / 64.0                # 0,75 quadro
FIELD = 0.60                          # lado do campo escuro (quadros, de SIDE): 38 px de 48
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
        "Silhuetas = os icones 2.0 do seletor (tools/bsgen/ui_icons.py, art3d/bs_ui_icons2), na cor do tipo: he ambar, "
        "ap branco-azulado, sap laranja + estrela clara, ac carmim + ouro, frag verde-agua, plasma ciano, pem azul + "
        "bobinas de cobre, missil HE ambar, submunicao laranja + minimisseis ouro, missil PEM azul + cobre, ogiva "
        "nuclear verde com o trevo ao lado, slug branco-azulado + aneis EM azuis + cauda laranja (paleta nova do Tupa).",
        "Moldura escura (grafite) de bisel duplo, campo preto e 2 parafusos (spec: 'dark recessed frame, 2 bolts'). "
        "Nenhum pixel na chave de pintura (helpers.paint_safe).",
        "Se tools/bsgen/ui_icons.py mudar, re-renderize NESTA ordem: bs_placas, bs_paiol (os icones do editor colam a "
        "placa padrao) e as previas da logistica (e as placas de modo das fabricas F2/F3/F4, que tambem usam estas "
        "placas). A conferencia da logistica compara cada placa com o simbolo refeito do ui_icons atual e falha se "
        "a placa ficou velha.",
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
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    B.camera(SIDE, SIDE, (0, 0))
    bpy.context.scene.cycles.samples = 64
    tags = ("bezel",)
    s = SIDE - 0.03
    # aro escuro de grafite com bisel duplo (o chanfro de fora pega a luz: contorno fino claro em volta)
    fa, fp = B.shard("frame", B.rpoly(0, 0, s, s, 0, chamfer=0.07), 0.0, 0.05, KM, slope=0.018, groove=0.010,
                     panel_h=0.012, tags=tags)
    hole = B.rpoly(0, 0, FIELD + 0.012, FIELD + 0.012, 0, chamfer=0.05)
    for t in (fa, fp):
        if t is not None:
            B.cut(t, [B.loft(f"hole{t.name}", hole, hole, 0.010, 0.5, K, bevel=0.0)])
    field = B.rpoly(0, 0, FIELD + 0.02, FIELD + 0.02, 0, chamfer=0.05)
    B.loft("field", field, field, 0.0, 0.012, B.mat_metal("lg_plate_field", (0.008, 0.009, 0.011), rough=0.6,
                                                           metal=0.2), bevel=0.0, tags=tags)
    for k, (sx, sy) in enumerate(((-1, 1), (1, -1))):
        c = (s / 2 - 0.040)
        B.cyl(f"bolt{k}", sx * c, sy * c, 0.066, 0.017, 0.014, S, axis="Z", verts=10, bevel=0.004, tags=tags)
    # 2 entalhes nos cantos sem parafuso (linha de painel curta)
    if fp is not None:
        B.cut(fp, [B.rbox(f"nick{k}", sx * (s / 2 - 0.04), sy * (s / 2 - 0.04), 0.008, 0.05, 0.05, 0.5, K,
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


# ============================================================================ silhuetas (os icones 2.0)
ICON_FN = {
    "he": lambda U: U.icon_ammo2("he"), "ap": lambda U: U.icon_ammo2("ap"), "sap": lambda U: U.icon_ammo2("sap"),
    "ac": lambda U: U.icon_ammo2("ac"), "frag": lambda U: U.icon_ammo2("frag"),
    "plasma": lambda U: U.icon_cell("plasma"), "pem": lambda U: U.icon_cell("pem"),
    "msl_he": lambda U: U.icon_missile2("he"), "msl_cluster": lambda U: U.icon_missile2("cluster"),
    "msl_emp": lambda U: U.icon_missile2("emp"), "msl_nuke": lambda U: U.icon_missile2("nuclear"),
    "slug": lambda U: U.icon_slug(),
}


def icon_pen(kind):
    """Roda a funcao do icone 2.0 do tipo com um Pen que guarda as mascaras (corpo, destaque) em vez de pintar o azul
    da interface. Devolve (ui_icons, pen)."""
    from bsgen import ui_icons as U

    class _Capture(U.Pen):
        def render(self, acc_color=None):
            return self

    orig = U.Pen
    U.Pen = _Capture
    try:
        p = ICON_FN[kind](U)
    finally:
        U.Pen = orig
    p.at()
    return U, p


def _region(p, rects):
    """Mascara L (mesmo tamanho das do Pen) dos retangulos dados em coordenadas do icone (0..96, y para baixo)."""
    m = Image.new("L", p.m["body"].size, 0)
    d = ImageDraw.Draw(m)
    for x0, y0, x1, y1 in rects:
        d.polygon(p._xf([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), fill=255)
    return m


def layers(kind):
    """[(mascara L, cor)] do tipo, de baixo para cima: corpo, regioes do corpo com cor propria, destaque."""
    _, p = icon_pen(kind)
    col = LG.KIND[kind]
    body = np.asarray(p.m["body"], np.float32)
    acc = np.asarray(p.m["acc"], np.float32)
    out = []
    rest = body.copy()
    parts = []
    for _kind, rects, c in col.get("parts", []):
        reg = np.asarray(_region(p, rects), np.float32) / 255.0
        part = body * reg
        rest = rest * (1 - reg)
        parts.append((part, c))
    out.append((rest, col["body"]))
    out += parts
    if col.get("acc") is not None and acc.max() > 0:
        out.append((acc, col["acc"]))
    elif acc.max() > 0:                               # destaque sem cor propria: cor do corpo
        out.append((acc, col["body"]))
    return [(Image.fromarray(np.clip(m, 0, 255).astype(np.uint8)), c) for m, c in out]


def silhouette(kind):
    """(corpo, destaque) do icone 2.0 do tipo (mascaras L do Pen), para conferencias."""
    _, p = icon_pen(kind)
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
    lay = layers(kind)
    big = size * SSF
    union = np.zeros_like(np.asarray(lay[0][0], np.float32))
    for m, _ in lay:
        union = np.maximum(union, np.asarray(m, np.float32))
    bb = Image.fromarray(union.astype(np.uint8)).getbbox()
    side = max(bb[2] - bb[0], bb[3] - bb[1])
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    box = (int(cx - side / 2), int(cy - side / 2), int(cx + side / 2), int(cy + side / 2))
    out = np.zeros((big, big, 4), np.float32)
    for m, c in lay:
        mm = m.crop(box).resize((big, big), Image.LANCZOS)
        rgb, a = _relief(mm, c)
        k = a[..., None]
        out[..., :3] = out[..., :3] * (1 - k) + rgb * k
        out[..., 3] = np.maximum(out[..., 3], a * 255)
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
    fpx = int(round(FIELD * 64))                              # 38 px de campo
    sym = symbol(variant, fpx - 3)
    o = (PX_PLATE - sym.width) // 2
    img.alpha_composite(sym, (o, o))
    img, _ = LG.paint_safe(img)
    return img
