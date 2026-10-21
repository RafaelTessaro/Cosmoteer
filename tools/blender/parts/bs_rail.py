"""Railgun Tupa (2.0): carregador, cano e ponta, tipo "layered" (tools/blender/render_layered.py).

    $PY tools/blender/render_layered.py bs_rail [--part bs_rail_barrel] [--only roof,trilhos] [--quick] [--out DIR]

Pedido do usuario: "canhao blindado naval-futurista no mesmo estilo das nossas armas; 3 partes como o railgun do
jogo: carregador, cano e ponta; FIXO; energia e municao so pelo carregador; 2 tripulantes; animacao do projetil
entrando no cano e do canhao carregando ate disparar; projetil enorme". Spec de arte: assets.railgun +
palette.rail (blindagem GRAFITE + nucleo ouro-branco + aneis EM violeta, NUNCA cobre).

Linguagem visual (STYLE.md secao 1, adaptada a uma arma fixa de espinha):
  * blindagem de grafite com bisel duplo CLARO (B.shard: base clara + painel grafite elevado): placas de bochecha
    ao longo do canal, pontes de travamento, culatra e coroa da boca;
  * casco pintado (verde = pintura da nave) nas laterais de fora, placas de um quadro com bisel duplo;
  * canal ABERTO no teto (x 1.10-1.90 da peca) mostrando o trilho, os aneis EM e o projetil claro;
  * aneis EM violeta que acendem em onda da culatra para a boca (trilhos1..9, carga1..8 aditivos), nucleo ouro-branco
    na carga cheia; LEDs so em recessos escuros.

Juncao entre canos sem emenda no canal: tudo o que cruza a emenda (fundo do canal, nervuras, trilhos, labio do
canal, placas de bochecha das pontas, planos de carga) e periodico em y com periodo que divide 3 e passa da borda
da camera (a borda nunca ganha chanfro). As paredes ficam abertas em x 1.0-2.0 nas bordas do canal.

Coordenadas do modelo: centradas na peca, +X direita, +Y frente (topo da imagem), 1 unidade = 1 quadro.
"""

import math

import bs3d as B
import models as Mo

# ============================================================================ paleta (palette.rail)
VIOLET = (0.30, 0.135, 1.0)          # (150, 105, 255) na vista Standard com forca ~1
GOLD = (1.0, 0.58, 0.10)             # (255, 200, 90)
CORE_W = (1.0, 0.87, 0.58)           # (255, 240, 200)
GRAPH = (0.021, 0.022, 0.026)        # grafite da blindagem (painel)
GRAPH_D = (0.026, 0.027, 0.031)      # grafite escuro (estrutura sob as placas)
EDGE = (0.36, 0.37, 0.39)            # bisel claro das placas de grafite
TROUGH = (0.085, 0.088, 0.096)       # fundo do canal (mais claro que o prototipo: licao 1)
RAIL = (0.50, 0.51, 0.53)            # trilho de aco claro
TUNG = (0.36, 0.37, 0.39)            # tungstenio claro (igual ao slug de bs_shells2)

# geometria comum (quadros, centrada na peca)
CH = 0.40                            # meia largura do canal aberto no teto (x 1.10-1.90 da peca)
RAIL_IN, RAIL_OUT = 0.215, 0.305     # faces do trilho
RING_IN, RING_OUT = 0.335, 0.635     # blocos laterais dos aneis EM
TR = 0.43                            # meia largura do fundo do canal
CHEEK_OUT = 0.86                     # bochecha de grafite do teto: x CH..CHEEK_OUT
BRIDGE_Y = 0.95                      # pontes de travamento do cano (y 0.55 e 2.45 da peca)
BRIDGE_HW = 0.15
CANO_RINGS = (-0.5, 0.0, 0.5)        # 3 aneis EM por cano (de tras para a frente)
GLOW_HW = 0.62                       # meia largura dos planos de carga (identica em todas as pecas)
EXT = 0.14                           # o que passa da borda da camera (sem chanfro na emenda)

# ============================================================================ pecas (PARTS)
_LOADER_ICON = {"size": [69, 92], "layers": ["floor", "projeteis", "capacitores", "weapon", "roof"],
                "pick": {"projeteis": 5, "capacitores": 2}}
PARTS = {
    "bs_rail_loader": {
        "id": "rafaeltessaro.bs_rail_loader", "kind": "layered", "size": [3, 4], "accent": "violet",
        "walls": {"open": [["top", 1.0, 2.0]]},
        "crew_pos": [[0.6, 1.6], [2.4, 1.6]],
        "layers": [
            {"name": "floor", "fn": "loader_floor", "game_layer": "floors", "opaque": True},
            {"name": "projeteis", "fn": "loader_magazine", "game_layer": "doodads_low", "rect": [0.6, 2.8, 1.8, 1.0],
             "file": "projeteis{i}.png", "levels": 6, "islands": True},
            {"name": "consola", "fn": "loader_console", "game_layer": "walls", "rect": [0.1, 1.1, 1.0, 1.0],
             "file": "consola{i}.png", "frames": 4, "interval": 0.1, "islands": True},
            {"name": "culatra_abre", "fn": "loader_jaws", "game_layer": "walls", "rect": [1.0, 0.0, 1.0, 1.0],
             "file": "culatra_abre{i}.png", "frames": 3, "interval": 0.0666, "islands": True},
            {"name": "culatra_carrega", "fn": "loader_load", "game_layer": "walls", "rect": [1.0, 0.0, 1.0, 2.0],
             "file": "culatra_carrega{i}.png", "frames": 6, "interval": 0.2, "islands": True},
            {"name": "weapon", "fn": "loader_breech", "game_layer": "weapons", "rect": [0.0, 0.0, 3.0, 1.0],
             "normals": True, "islands": True},
            {"name": "capacitores", "fn": "loader_caps", "game_layer": "doodads_high", "rect": [0.0, 2.1, 3.0, 1.0],
             "file": "capacitores{i}.png", "levels": 3, "islands": True},
            {"name": "luz_culatra", "fn": "pil:glow_loader", "game_layer": "lights_add", "rect": [0.0, 0.0, 3.0, 1.0],
             "file": "luz_culatra{i}.png", "levels": 2, "blend": "add"},
            {"name": "roof", "fn": "loader_roof", "game_layer": "roofs", "normals": True, "islands": True},
        ],
        "icon": _LOADER_ICON,
        "blueprint_layers": ["weapon", "roof"],
    },
    "bs_rail_barrel": {
        "id": "rafaeltessaro.bs_rail_barrel", "kind": "layered", "size": [3, 3], "accent": "violet",
        "walls": {"open": [["top", 1.0, 2.0], ["bottom", 1.0, 2.0]]},
        "layers": [
            {"name": "floor", "fn": "cano_floor", "game_layer": "floors", "opaque": True},
            {"name": "trilhos", "fn": "cano_rails", "game_layer": "doodads_low", "file": "trilhos{i}.png",
             "levels": 9, "islands": True},
            {"name": "carga", "fn": "pil:glow_cano", "game_layer": "lights_add", "file": "carga{i}.png", "levels": 8,
             "blend": "add"},
            {"name": "roof", "fn": "cano_roof", "game_layer": "roofs", "normals": True, "islands": True},
        ],
        "icon": {"size": [69, 69], "layers": ["floor", "trilhos", "roof"]},
        "blueprint_layers": ["trilhos", "roof"],
    },
    "bs_rail_muzzle": {
        "id": "rafaeltessaro.bs_rail_muzzle", "kind": "layered", "size": [3, 4], "accent": "violet",
        "walls": {"open": [["bottom", 1.0, 2.0]]},
        "layers": [
            {"name": "floor", "fn": "ponta_floor", "game_layer": "floors", "opaque": True},
            {"name": "trilhos", "fn": "ponta_rails", "game_layer": "doodads_low", "islands": True},
            {"name": "weapon", "fn": "ponta_crown", "game_layer": "weapons", "rect": [0.0, 0.0, 3.0, 1.5],
             "normals": True, "islands": True},
            {"name": "carga", "fn": "pil:glow_ponta", "game_layer": "lights_add", "file": "carga{i}.png", "levels": 6,
             "blend": "add"},
            {"name": "roof", "fn": "ponta_roof", "game_layer": "roofs", "normals": True, "islands": True},
            # o projetil dentro do cano (ChainedTo Projectile): o mesmo objeto do slug em voo (bs_shells2)
            {"name": "slug", "fn": "slug_sprite", "game_layer": "walls", "rect": [1.1, 0.5, 0.8, 3.0],
             "samples": 64},
            {"name": "slug_glow", "fn": "pil:glow_slug", "game_layer": "lights_add", "rect": [0.9, 0.3, 1.2, 3.4],
             "blend": "add"},
        ],
        "icon": {"size": [69, 92], "layers": ["floor", "trilhos", "weapon", "roof"]},
        "blueprint_layers": ["weapon", "roof"],
    },
}


# ============================================================================ materiais
def _spec(m, v):
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = v
    return m


def mats(M):
    """Materiais do Tupa (nomes "rl_*": o cache do bs3d e por nome)."""
    return {
        "graph": _spec(B.mat_paint("rl_graph", GRAPH, rough=0.40, metal=0.30, wear=0.10, grime=0.05, scale=5), 0.35),
        "graph_d": _spec(B.mat_metal("rl_graph_d", GRAPH_D, rough=0.45, metal=0.6), 0.3),
        "edge": _spec(B.mat_paint("rl_edge", EDGE, rough=0.34, metal=0.12, wear=0.10, grime=0.03, scale=4), 0.4),
        "trough": _spec(B.mat_metal("rl_trough", TROUGH, rough=0.42, metal=0.75), 0.35),
        "rail": B.mat_metal("rl_rail", RAIL, rough=0.26, metal=0.85),
        "rib": _spec(B.mat_metal("rl_rib", (0.12, 0.125, 0.135), rough=0.40, metal=0.7), 0.3),
        "tung": _spec(B.mat_metal("rl_tung", TUNG, rough=0.38, metal=0.5), 0.3),
        "lens": _spec(B.mat_metal("rl_lens", (0.030, 0.012, 0.085), rough=0.12, metal=0.0), 0.8),
        "tipgold": _spec(B.mat_metal("rl_tipgold", (0.46, 0.36, 0.19), rough=0.32, metal=0.5), 0.3),
        "vio_paint": _spec(B.mat_metal("rl_vio_paint", (0.11, 0.045, 0.36), rough=0.35, metal=0.4), 0.3),
        "green": B.mat_roof_green(),
        "core": M["core"], "core_mid": M["core_mid"], "steel": M["steel"], "black": M["black"],
        "armor_mid": M["armor_mid"], "armor": M["armor"],
    }


def violet(s, name=None):
    """Emissor violeta com forca s (0 = lente apagada). Cor de base = lente escura violeta (STYLE 11.5)."""
    if s <= 1e-4:
        return B.mat_metal("rl_lens", (0.030, 0.012, 0.085), rough=0.12, metal=0.0)
    m = B.mat_glow(name or f"rl_vio_{int(round(s * 100)):03d}", VIOLET, s)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.030, 0.012, 0.085, 1)
    return m


def hot(color, s, base, name):
    m = B.mat_glow(f"rl_{name}_{int(round(s * 100)):03d}", color, s)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*base, 1)
    return m


def amber(s=1.0):
    return B.mat_glow(f"rl_amber_{int(round(s * 100)):03d}", (1.0, 0.42, 0.04), s)


# ============================================================================ utilidades de forma
def gplate(name, poly, z0, z1, X, tags, slope=0.05, groove=0.028, panel_h=0.03, panel=None):
    """Placa de blindagem de grafite com bisel duplo CLARO: base clara chanfrada + painel grafite elevado."""
    return B.shard(name, poly, z0, z1, X["edge"], slope=slope, groove=groove, panel_h=panel_h,
                   panel_mat=panel or X["graph"], tags=tags)


def mirror_x(poly):
    return [(-x, y) for x, y in reversed(poly)]


def chamfer_rect(x0, y0, x1, y1, c=(0.08, 0.08, 0.08, 0.08)):
    """Retangulo com chanfros por canto (c = [baixo-esq, baixo-dir, cima-dir, cima-esq]); 0 = canto vivo."""
    bl, br, tr, tl = c
    pts = []
    pts += [(x0, y0 + bl), (x0 + bl, y0)] if bl else [(x0, y0)]
    pts += [(x1 - br, y0), (x1, y0 + br)] if br else [(x1, y0)]
    pts += [(x1, y1 - tr), (x1 - tr, y1)] if tr else [(x1, y1)]
    pts += [(x0 + tl, y1), (x0, y1 - tl)] if tl else [(x0, y1)]
    return pts


def ledslot(name, cx, cy, sx, sy, z_top, n, X, tags, targets, mat, vertical=True, depth=0.06, pip=0.55):
    """Fenda passante escura (recortada nos alvos) com leito preto e n pips emissivos no fundo (STYLE 9:
    fendas estreitas = furo passante + leito na peca de baixo)."""
    for j, t in enumerate(targets if isinstance(targets, (list, tuple)) else [targets]):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{j}", cx, cy, sx, sy, z_top - depth, z_top + 0.3, X["black"], bevel=0.0)])
    zb = z_top - depth
    B.box(name + "_bed", cx, cy, sx, sy, zb - 0.012, zb + 0.002, X["black"], bevel=0.0, tags=tags)
    L = sy if vertical else sx
    for i in range(n):
        t = (i + 0.5) / n
        if vertical:
            px, py, w, h = cx, cy - sy / 2 + t * sy, sx * pip, L / n * pip
        else:
            px, py, w, h = cx - sx / 2 + t * sx, cy, L / n * pip, sy * pip
        B.box(f"{name}_p{i}", px, py, w, h, zb, zb + 0.012, mat, bevel=0.0, tags=tags)


def bolts(prefix, pts, z, X, tags, r=0.018):
    B.bolts(prefix, pts, z, r, X["steel"], tags=tags)


def ring_levels(level, n_levels=9, n_rings=3):
    """Intensidade (0..1) de cada anel EM no nivel (1 = frio): a onda acende da culatra (anel 0) para a boca."""
    c = (level - 1) / (n_levels - 1)
    return [max(0.0, min(1.0, c * n_rings - i)) for i in range(n_rings)]


# ============================================================================ pecas do canal (comuns)
def channel_floor(name, y0, y1, X, tags, hw=TR, ribs=True, rib_y0=None):
    """Fundo do canal (sob o projetil): calha de aco medio com nervuras transversais a cada 0.25 (periodo 3/12)
    e o sulco-guia central. y0/y1 passam da camera nas emendas."""
    B.box(name + "_bed", 0, (y0 + y1) / 2, 2 * hw, y1 - y0, -0.02, 0.012, X["trough"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        # degrau escuro nas bordas da calha (desenha o canal no piso)
        B.box(f"{name}_lip{sx}", sx * (hw + 0.03), (y0 + y1) / 2, 0.06, y1 - y0, -0.02, 0.02, X["black"], bevel=0.0,
              tags=tags)
    B.box(name + "_groove", 0, (y0 + y1) / 2, 0.05, y1 - y0, 0.010, 0.016, X["graph_d"], bevel=0.0, tags=tags)
    if ribs:
        start = (rib_y0 if rib_y0 is not None else -1.5 + 0.125)
        k = 0
        y = start
        while y < y1 - 0.02:
            if y > y0 + 0.02:
                B.box(f"{name}_rib{k}", 0, y, 2 * hw - 0.04, 0.045, 0.012, 0.026, X["rib"], bevel=0.004, tags=tags)
                B.box(f"{name}_ribs{k}", 0, y - 0.03, 2 * hw - 0.04, 0.012, 0.012, 0.016, X["black"], bevel=0.0,
                      tags=tags)
            y += 0.25
            k += 1


def rails(name, y0, y1, X, tags):
    """Os 2 trilhos de aco claro sobre a base isolante escura (passam da camera nas emendas)."""
    for sx in (-1, 1):
        xm = sx * (RAIL_IN + RAIL_OUT) / 2
        B.box(f"{name}_base{sx}", sx * (RAIL_IN + RAIL_OUT) / 2, (y0 + y1) / 2, RAIL_OUT - RAIL_IN + 0.05, y1 - y0,
              -0.01, 0.035, X["graph_d"], bevel=0.0, tags=tags)
        B.box(f"{name}_rail{sx}", xm, (y0 + y1) / 2, RAIL_OUT - RAIL_IN, y1 - y0, 0.035, 0.115, X["rail"],
              bevel=0.012, tags=tags)
        # fresta escura no topo do trilho (le como 2 barras: trilho de duas laminas)
        B.box(f"{name}_slit{sx}", xm, (y0 + y1) / 2, 0.012, y1 - y0, 0.112, 0.118, X["black"], bevel=0.0, tags=tags)


def rail_clips(name, ys, X, tags):
    for i, y in enumerate(ys):
        for sx in (-1, 1):
            B.box(f"{name}{i}{sx}", sx * (RAIL_OUT + 0.03), y, 0.06, 0.07, 0.03, 0.10, X["steel"], bevel=0.008,
                  tags=tags)


def em_ring(name, y, e, X, tags, hw_out=RING_OUT, th=0.18):
    """Anel EM visto de cima: 2 blocos de grafite com bisel claro dos lados do canal (emissor violeta num recesso
    na face de dentro) e a banda escura que cruza o fundo do canal sob os trilhos (fenda violeta acesa).
    e = intensidade 0..1 (0 = lente apagada)."""
    s = 1.45 * e
    vm = violet(s)
    for sx in (-1, 1):
        poly = chamfer_rect(RING_IN, y - th / 2, hw_out, y + th / 2, (0.0, 0.08, 0.08, 0.0))
        if sx < 0:
            poly = mirror_x(poly)
        a, p = gplate(f"{name}_blk{sx}", poly, 0.0, 0.20, X, tags, slope=0.035, groove=0.02, panel_h=0.025)
        # emissor: recesso preto na borda de dentro com a lente violeta
        xr = sx * (RING_IN + 0.045)
        B.cut(a, [B.box(f"{name}_ec{sx}", xr, y, 0.05, th - 0.07, 0.12, 0.5, X["black"], bevel=0.0)])
        if p is not None:
            B.cut(p, [B.box(f"{name}_ec2{sx}", xr, y, 0.05, th - 0.07, 0.12, 0.5, X["black"], bevel=0.0)])
        B.box(f"{name}_ebed{sx}", xr, y, 0.05, th - 0.07, 0.105, 0.12, X["black"], bevel=0.0, tags=tags)
        B.box(f"{name}_em{sx}", xr, y, 0.03, th - 0.10, 0.12, 0.135, vm, bevel=0.0, tags=tags)
        # parafusos na ponta de fora
        bolts(f"{name}_b{sx}", [(sx * (hw_out - 0.07), y - 0.05), (sx * (hw_out - 0.07), y + 0.05)], 0.235, X,
              tags, r=0.014)
    # banda sob o canal (os trilhos passam por cima)
    B.box(f"{name}_band", 0, y, 2 * RING_IN + 0.02, 0.09, -0.01, 0.034, X["graph_d"], bevel=0.004, tags=tags)
    B.box(f"{name}_bandl", 0, y, 2 * RING_IN - 0.04, 0.03, 0.030, 0.040, vm, bevel=0.0, tags=tags)


# ============================================================================ CANO (3x3)
def cano_floor(M, T="floor"):
    X = mats(M)
    tags = (T,)
    B.box("fl_base", 0, 0, 3.3, 3.3, -0.06, -0.02, X["core"], bevel=0.0, tags=tags)
    channel_floor("ch", -1.5 - EXT, 1.5 + EXT, X, tags)
    for sx in (-1, 1):
        # duto de barramento ao longo do canal (continuo nas emendas)
        B.box(f"bus{sx}", sx * 0.70, 0, 0.08, 3.0 + 2 * EXT, -0.02, 0.05, X["steel"], bevel=0.01, tags=tags)
        B.box(f"busk{sx}", sx * 0.70, 0, 0.02, 3.0 + 2 * EXT, 0.05, 0.056, X["black"], bevel=0.0, tags=tags)
        for k, yc in enumerate((-1.0, 0.0, 1.0)):
            # placa de piso de cada quadro lateral + modulo de capacitor do acionador da bobina
            B.box(f"fp{sx}{k}", sx * 1.10, yc, 0.74, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)
            mod = chamfer_rect(0.86, yc - 0.34, 1.36, yc + 0.34, (0.06, 0.06, 0.06, 0.06))
            if sx < 0:
                mod = mirror_x(mod)
            a, p = gplate(f"cap{sx}{k}", mod, 0.0, 0.12, X, tags, slope=0.03, groove=0.02, panel_h=0.02)
            fins = [B.box(f"capf{sx}{k}{i}", sx * 1.11, yc - 0.20 + i * 0.08, 0.36, 0.022, 0.10, 0.4, X["black"],
                          bevel=0.0) for i in range(6)]
            B.cut(p if p is not None else a, fins)
            B.box(f"capled{sx}{k}", sx * 1.11, yc + 0.26, 0.20, 0.03, 0.10, 0.145, violet(0.7), bevel=0.0,
                  tags=tags)
            # cabo do modulo ao barramento
            B.box(f"cab{sx}{k}", sx * 0.79, yc, 0.14, 0.06, 0.0, 0.04, X["graph_d"], bevel=0.008, tags=tags)


def cano_rails(M, T="trilhos", level=1):
    X = mats(M)
    tags = (T,)
    rails("r", -1.5 - EXT, 1.5 + EXT, X, tags)
    rail_clips("clip", (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25), X, tags)
    for i, (y, e) in enumerate(zip(CANO_RINGS, ring_levels(level))):
        em_ring(f"ring{i}", y, e, X, tags)
    # sapatas sob as pontes do teto (aparecem no interior; seguram os trilhos)
    for j, y in enumerate((-BRIDGE_Y, BRIDGE_Y)):
        for sx in (-1, 1):
            B.box(f"shoe{j}{sx}", sx * 0.50, y, 0.26, 0.22, 0.0, 0.10, X["graph_d"], bevel=0.012, tags=tags)
            B.box(f"shoet{j}{sx}", sx * 0.50, y, 0.18, 0.14, 0.10, 0.12, X["steel"], bevel=0.008, tags=tags)


def _deck_plates(prefix, x0, x1, ys, X, tags, vent_at=None):
    """Placas do casco pintado (verde) com bisel duplo, uma por quadro, entre x0 e x1 (um lado)."""
    for k, (yc, hy) in enumerate(ys):
        poly = B.rpoly((x0 + x1) / 2, yc, x1 - x0 - 0.06, hy - 0.06, 0, chamfer=0.07)
        _, pnl = B.shard(f"{prefix}{k}", poly, 0.0, 0.06, X["green"], slope=0.025, groove=0.05, panel_h=0.02,
                         tags=tags)
        if pnl is not None and k % 2 == 0:
            B.cut(pnl, [B.rbox(f"{prefix}dl{k}", (x0 + x1) / 2 + 0.10, yc - 0.18, 0.012, 0.42, 0.07, 0.2, X["core"],
                               rot=45, bevel=0.0)])
        if vent_at is not None and k == vent_at and pnl is not None:
            cx = (x0 + x1) / 2
            v = B.box(f"{prefix}v{k}", cx, yc, 0.26, 0.40, 0.05, 0.10, X["core_mid"], bevel=0.008, tags=tags)
            B.cut(v, [B.box(f"{prefix}vc{k}{i}", cx, yc - 0.14 + i * 0.07, 0.20, 0.025, 0.08, 0.2, X["core"],
                            bevel=0.0) for i in range(5)])


def cheek(name, y0, y1, X, tags, c0=0.10, c1=0.10, x_out=CHEEK_OUT, z1=0.13, leds=0):
    """Placa de bochecha de grafite ao longo do canal (os dois lados). c0/c1 = chanfro de fora em baixo/em cima
    (0 = reta: a placa passa da camera e continua no cano vizinho)."""
    out = []
    for sx in (-1, 1):
        poly = chamfer_rect(CH + 0.02, y0, x_out, y1, (0.0, c0, c1, 0.0))
        if sx < 0:
            poly = mirror_x(poly)
        a, p = gplate(f"{name}{sx}", poly, 0.0, z1, X, tags)
        out.append((a, p))
        if leds and p is not None and y1 - y0 > 0.8:
            xm = sx * (CH + x_out) / 2 + sx * 0.06
            ledslot(f"{name}_led{sx}", xm, (y0 + y1) / 2, 0.06, min(0.9, y1 - y0 - 0.5), z1 + 0.03, leds, X, tags,
                    [p, a], violet(0.55))
    return out


def coaming(name, y0, y1, X, tags, z=0.13):
    """Labio de aco claro na borda do canal (desenha o canal a 1x no espaco e no casco branco)."""
    for sx in (-1, 1):
        B.box(f"{name}{sx}", sx * (CH + 0.018), (y0 + y1) / 2, 0.036, y1 - y0, 0.0, z + 0.02, X["rail"], bevel=0.008,
              tags=tags)


def bridge(name, y, X, tags, hw=0.96, hy=BRIDGE_HW, z0=0.10, z1=0.27):
    """Ponte de travamento blindada sobre o canal (esconde o projetil por um instante: 'dentro do cano')."""
    poly = [(-hw, y - hy + 0.06), (-hw + 0.06, y - hy), (hw - 0.06, y - hy), (hw, y - hy + 0.06),
            (hw, y + hy - 0.06), (hw - 0.06, y + hy), (-hw + 0.06, y + hy), (-hw, y + hy - 0.06)]
    B.box(f"{name}_under", 0, y, 2 * hw - 0.1, 2 * hy - 0.06, 0.0, z0 + 0.02, X["graph_d"], bevel=0.0, tags=tags)
    a, p = gplate(name, poly, z0, z1, X, tags, slope=0.04, groove=0.024, panel_h=0.03)
    # recesso central com 3 pips violeta (estado da trava) e garras das pontas
    ledslot(f"{name}_led", 0, y, 0.34, 0.05, z1 + 0.03, 3, X, tags, [p, a], violet(0.6), vertical=False)
    for sx in (-1, 1):
        B.cut(p if p is not None else a, [B.box(f"{name}_n{sx}", sx * 0.58, y, 0.016, 2 * hy, z1 - 0.02, z1 + 0.3,
                                                 X["black"], bevel=0.0)])
        bolts(f"{name}_b{sx}", [(sx * (hw - 0.10), y - 0.06), (sx * (hw - 0.10), y + 0.06)], z1 + 0.035, X, tags,
              r=0.016)
    return a


def chevron_plate(name, y0, y1, X, tags, x_in=0.50, x_out=0.79, lean=0.16, z0=0.13, z1=0.21, leds=0):
    """Placa de cima das bochechas (os dois lados): paralelogramo inclinado para a FRENTE e para o centro; as duas
    juntas formam uma divisa apontando para a boca (STYLE 1.2: formas apontando para a frente)."""
    out = []
    for sx in (-1, 1):
        poly = [(x_in, y0 + lean), (x_out, y0), (x_out, y1 - lean), (x_in, y1)]
        if sx < 0:
            poly = mirror_x(poly)
        a, p = gplate(f"{name}{sx}", poly, z0, z1, X, tags, slope=0.035, groove=0.022, panel_h=0.025)
        out.append((a, p))
        if leds and p is not None:
            xm = sx * (x_in + x_out) / 2
            ledslot(f"{name}_led{sx}", xm, (y0 + y1) / 2, 0.055, (y1 - y0) - 2 * lean - 0.12, z1 + 0.025, leds, X,
                    tags, [p, a], violet(0.55))
    return out


def cano_roof(M, T="roof"):
    X = mats(M)
    tags = (T,)
    for sx in (-1, 1):
        B.box(f"under{sx}", sx * (CH + 1.5) / 2, 0, 1.5 - CH, 3.0 + 2 * EXT, -0.06, 0.0, X["core"], bevel=0.0,
              tags=tags)
        _deck_plates(f"dk{sx}", CHEEK_OUT if sx > 0 else -1.5, 1.5 if sx > 0 else -CHEEK_OUT,
                     [(1.0, 1.0), (0.0, 1.0), (-1.0, 1.0)], X, tags, vent_at=1)
    # bochechas de grafite: o trecho do meio (entre as pontes) e as pontas (continuam no cano vizinho)
    yb0, yb1 = BRIDGE_Y - BRIDGE_HW, BRIDGE_Y + BRIDGE_HW
    cheek("chk_m", -yb0 + 0.02, yb0 - 0.02, X, tags, c0=0.12, c1=0.12)
    chevron_plate("chv", -yb0 + 0.10, yb0 - 0.10, X, tags, leds=3)
    cheek("chk_t", yb1 - 0.02, 1.5 + EXT, X, tags, c0=0.12, c1=0.0)
    cheek("chk_b", -1.5 - EXT, -yb1 + 0.02, X, tags, c0=0.0, c1=0.12)
    coaming("coam", -1.5 - EXT, 1.5 + EXT, X, tags)
    bridge("br_t", BRIDGE_Y, X, tags)
    bridge("br_b", -BRIDGE_Y, X, tags)


# ============================================================================ brilhos (PIL, aditivos)
def _np():
    import numpy as np
    return np


def _plane(px, rect_tiles, part_h, y_lo, y_hi, k_core, edge=0.16, rings=(), ring_gain=0.0, hw=GLOW_HW,
           bore=None, core_gain=1.0, base_gain=1.0):
    """Plano aditivo de carga (RGB sobre preto, opaco). y em coordenadas da peca (centrada, +y para cima): o plano
    cobre y_lo..y_hi com uma frente suave de largura 'edge' em y_hi (a onda) e borda reta em y_lo (emenda).
    Perfil em x igual em todas as pecas: violeta nos trilhos e no canal ate GLOW_HW, mais forte no meio;
    k_core > 0 soma o nucleo ouro-branco no centro (carga quase cheia). bore(y) -> meia largura maxima (coroa)."""
    np = _np()
    from PIL import Image
    w, h = px
    x0t, y0t, wt, ht = rect_tiles
    xs = (np.arange(w) + 0.5) / w * wt + x0t - 1.5            # x da peca centrada (todas tem 3 de largura)
    ys = part_h / 2 - ((np.arange(h) + 0.5) / h * ht + y0t)   # y da peca centrada, +y para cima
    X, Y = np.meshgrid(xs, ys)
    ax = np.abs(X)
    # perfil lateral: patamar no canal, pico nos trilhos, cai ate GLOW_HW
    prof = np.clip(1 - (ax - 0.30) / (hw - 0.30), 0, 1) ** 1.6
    prof = np.where(ax < 0.30, 0.78 + 0.22 * np.exp(-((ax - 0.26) / 0.05) ** 2), prof)
    prof = prof + 0.35 * np.exp(-((ax - 0.26) / 0.04) ** 2)
    if bore is not None:
        lim = np.vectorize(bore)(Y)
        prof = prof * np.clip((lim - ax) / 0.06 + 1, 0, 1)
    # cobertura em y: frente suave no topo (y_hi), corte reto no fundo
    cov = np.clip((y_hi - Y) / edge, 0, 1) * (Y >= y_lo - 1e-6)
    front = np.exp(-((Y - (y_hi - edge * 0.6)) / (edge * 0.7)) ** 2) * (Y >= y_lo - 1e-6)
    ringb = np.zeros_like(Y)
    for ry in rings:
        ringb += np.exp(-((Y - ry) / 0.06) ** 2)
    amt = cov * prof * base_gain * (1 + ring_gain * ringb) + 0.35 * front * prof
    vio = np.array([150, 105, 255], np.float32) / 255.0
    rgb = amt[..., None] * vio * 0.62
    if k_core > 0:
        core = np.exp(-(X / 0.075) ** 2) * cov * k_core * core_gain
        halo = np.exp(-(X / 0.20) ** 2) * cov * k_core * core_gain * 0.45
        gw = np.array([255, 225, 150], np.float32) / 255.0
        rgb = rgb + core[..., None] * gw + halo[..., None] * np.array([255, 200, 90], np.float32) / 255.0 * 0.6
    rgb = np.clip(rgb, 0, 1)
    return Image.fromarray(np.dstack([rgb * 255, np.full((h, w), 255.0)]).astype(np.uint8), "RGBA")


def glow_cano(P, layer, px, level=1):
    """carga1..8 do cano: o nivel k cobre os k/8 de baixo (lado da culatra); violeta ate 6, nucleo ouro-branco
    em 7 e 8. A largura do plano e a mesma em todas as pecas (as emendas casam)."""
    H = P["size"][1]
    y_hi = -1.5 + 3.0 * level / 8
    if level == 8:
        y_hi = 1.5 + 0.5           # cheio: sem frente dentro do cano (continua no vizinho)
    k_core = {7: 0.55, 8: 1.0}.get(level, 0.0)
    return _plane(px, layer.get("rect", [0, 0, 3, 3]), H, -1.5, y_hi, k_core, rings=CANO_RINGS, ring_gain=0.9)


def glow_loader(P, layer, px, level=1):
    """luz_culatra1..2 (3x1 na fileira da culatra): primeiro trecho da onda; 2 = com o nucleo ouro-branco."""
    H = P["size"][1]
    k_core = {1: 0.0, 2: 0.85}[level]
    return _plane(px, layer["rect"], H, 1.0, 2.0 + 0.5, k_core, rings=(LOADER_RING,), ring_gain=1.2,
                  base_gain=0.75 if level == 1 else 1.0)


def glow_ponta(P, layer, px, level=1):
    """carga1..6 da ponta (3x4): a onda sobe da emenda ate a coroa; na coroa o plano fica so no furo e nos
    emissores (bore); 5 e 6 com o nucleo ouro-branco."""
    H = P["size"][1]
    y_lo = -2.0
    y_hi = -2.0 + 4.0 * level / 6
    if level == 6:
        y_hi = 2.0 + 0.4
    k_core = {5: 0.6, 6: 1.0}.get(level, 0.0)
    img = _plane(px, layer.get("rect", [0, 0, 3, 4]), H, y_lo, y_hi, k_core, rings=PONTA_RINGS + CROWN_RINGS,
                 ring_gain=1.0, bore=_ponta_bore)
    if y_hi > CROWN_RING_Y + 0.05:
        # sulco emissor do anel da coroa: faixa violeta de lado a lado (ouro-branca no meio na carga cheia)
        np = _np()
        from PIL import Image
        a = np.asarray(img, dtype=np.float32) / 255.0
        w, h = px
        xs = (np.arange(w) + 0.5) / w * 3.0 - 1.5
        ys = H / 2 - (np.arange(h) + 0.5) / h * 4.0
        Xg, Yg = np.meshgrid(xs, ys)
        band = np.exp(-((Yg - CROWN_RING_Y) / 0.035) ** 2) * np.clip((1.12 - np.abs(Xg)) / 0.1, 0, 1)
        halo = np.exp(-((Yg - CROWN_RING_Y) / 0.09) ** 2) * np.clip((1.12 - np.abs(Xg)) / 0.3, 0, 1) * 0.35
        vio = np.array([150, 105, 255], np.float32) / 255.0
        a[..., :3] += (band * 0.85 + halo)[..., None] * vio
        if k_core:
            a[..., :3] += (band * np.exp(-(Xg / 0.5) ** 2) * k_core * 0.7)[..., None] * \
                np.array([255, 225, 150], np.float32) / 255.0
        a = np.clip(a, 0, 1)
        img = Image.fromarray((a * 255).astype(np.uint8), "RGBA")
    return img


def glow_slug(P, layer, px, level=None):
    """Halo do projetil dentro do cano (lights_add, 1.2 x 3.4, ChainedTo Projectile): halo violeta em volta da
    haste + ponta ouro-branca na frente (topo)."""
    np = _np()
    from PIL import Image
    w, h = px
    x0t, y0t, wt, ht = layer["rect"]
    xs = (np.arange(w) + 0.5) / w * wt - wt / 2
    ys = ht / 2 - (np.arange(h) + 0.5) / h * ht           # 0 = centro do projetil, +y = ponta
    X, Y = np.meshgrid(xs, ys)
    L = 1.47                                                # ponta do slug (bs_shells2: xt = 1.47)
    along = np.clip(1 - (np.abs(Y + 0.0) - 1.30) / 0.30, 0, 1)
    body = np.exp(-(X / 0.17) ** 2) * along
    wide = np.exp(-(X / 0.42) ** 2) * np.clip(1 - (np.abs(Y) - 1.1) / 0.6, 0, 1)
    tip = np.exp(-((X / 0.13) ** 2 + ((Y - L + 0.06) / 0.16) ** 2))
    tipw = np.exp(-((X / 0.05) ** 2 + ((Y - L + 0.03) / 0.07) ** 2))
    vio = np.array([150, 105, 255], np.float32) / 255.0
    rgb = (body * 0.55 + wide * 0.30)[..., None] * vio + tip[..., None] * np.array([255, 200, 90]) / 255.0 * 0.95 \
        + tipw[..., None] * np.array([255, 240, 200]) / 255.0
    rgb = np.clip(rgb, 0, 1)
    return Image.fromarray(np.dstack([rgb * 255, np.full((h, w), 255.0)]).astype(np.uint8), "RGBA")


# placeholders preenchidos mais abaixo (carregador e ponta)
LOADER_RING = 1.78
PONTA_RINGS = (-1.0, -0.5, 0.0)
CROWN_RINGS = (1.25, 1.50, 1.75)          # bandas emissoras na garganta


def _ponta_bore(y):
    """Meia largura maxima do plano de carga na ponta: livre no canal; na coroa, so a garganta e os emissores
    das faces de dentro das pontas (o anel da coroa ganha a sua faixa propria em glow_ponta)."""
    return 9.0 if y < RING_Y0 else BORE + 0.09


# ============================================================================ projetil curto (carregador)
def slug_round(name, cx, cy, L, R, X, tags, tip_glow=0.9):
    """Projetil do Tupa como municao: haste de tungstenio CLARO octogonal ao longo de +Y (ponta para a frente), base
    de sabot escura, 2 colares violeta anodizados e ponta ouro (o mesmo visual do slug de bs_shells2, curto)."""
    yb, yt = cy - L / 2, cy + L / 2
    lt = min(0.16, L * 0.2)
    B.cyl(f"{name}_base", cx, yb + 0.04, 0.16, R * 1.30, 0.08, X["graph_d"], axis="Y", verts=8, bevel=0.004,
          tags=tags)
    B.cyl(f"{name}_rod", cx, (yb + 0.08 + yt - lt) / 2, 0.16, R, yt - lt - yb - 0.08, X["tung"], axis="Y", verts=8,
          bevel=0.004, tags=tags)
    for i, f in enumerate((0.36, 0.62)):
        B.cyl(f"{name}_col{i}", cx, yb + L * f, 0.16, R * 1.28, max(0.03, L * 0.05), X["vio_paint"], axis="Y",
              verts=8, bevel=0.003, tags=tags)
    B.cyl(f"{name}_tip", cx, yt - lt / 2, 0.16, R, lt, X["tipgold"], axis="Y", verts=8, bevel=0.0, r2=R * 0.35,
          tags=tags)
    if tip_glow > 0:
        B.cyl(f"{name}_hot", cx, yt - 0.025, 0.16, R * 0.40, 0.05, hot(GOLD, tip_glow, (0.42, 0.34, 0.20), "tip"),
              axis="Y", verts=8, bevel=0.0, r2=R * 0.12, tags=tags)


# ============================================================================ CARREGADOR (3x4)
# fileira 0 (y 1..2) = culatra; fileiras 1-2 = 2 postos da tripulacao + banco de capacitores; fileira 3 = paiol
CREW = ((-0.9, 0.4), (0.9, 0.4))         # (0.6, 1.6) e (2.4, 1.6) da peca
JAW_W = 0.36                            # meia largura da camara / folha da culatra fechada
JAW_OPEN = 0.30                         # curso de cada folha ao abrir
CHAMBER_Y = 1.50                        # centro do projetil assentado na camara
TRAY_Y = 0.48                           # centro do projetil quando sobe do elevador para a bandeja
ROUND_L, ROUND_R = 0.92, 0.085          # projetil na camara
MAG_N, MAG_PITCH = 12, 0.14             # paiol interno: 12 projeteis em pe
MAG_Y, MAG_L, MAG_R = -1.30, 0.80, 0.055
CAP_YS = (-0.27, -0.60, -0.93)          # celulas do banco de capacitores (de frente para tras)


def _mag_x(j):
    return -MAG_PITCH * (MAG_N - 1) / 2 + j * MAG_PITCH


def _mag_order():
    """Ordem de enchimento do paiol: do meio para fora, alternando os lados (fica simetrico a cada nivel)."""
    return sorted(range(MAG_N), key=lambda j: (abs(_mag_x(j)), _mag_x(j)))


def loader_floor(M, T="floor"):
    X = mats(M)
    tags = (T,)
    B.box("fl_base", 0, 0, 3.3, 4.3, -0.06, -0.02, X["core"], bevel=0.0, tags=tags)
    # placas do piso dos quadros laterais
    for sx in (-1, 1):
        for k, yc in enumerate((1.5, 0.5, -0.5, -1.5)):
            B.box(f"fp{sx}{k}", sx * 1.0, yc, 0.92, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)
    B.box("fpc", 0, -0.2, 1.0, 1.6, -0.02, 0.005, X["core_mid"], bevel=0.01, tags=tags)
    # camara + bandeja: a calha do canal continua do cano ate a culatra (nervuras no mesmo passo)
    channel_floor("ch", 1.0, 2.0 + EXT, X, tags, rib_y0=1.125)
    rails("r", 1.08, 2.0 + EXT, X, tags)
    for sx in (-1, 1):
        B.box(f"ranch{sx}", sx * (RAIL_IN + RAIL_OUT) / 2, 1.07, 0.13, 0.08, 0.0, 0.14, X["steel"], bevel=0.01,
              tags=tags)
    em_ring("ring0", LOADER_RING, 0.0, X, tags)
    # bandeja do soquete (rammer) do elevador ate a camara
    B.box("tray", 0, 0.12, 0.44, 1.76, -0.02, 0.015, X["trough"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"tray_l{sx}", sx * 0.245, 0.12, 0.05, 1.76, -0.02, 0.03, X["black"], bevel=0.0, tags=tags)
        B.box(f"tray_g{sx}", sx * 0.13, 0.12, 0.035, 1.76, 0.015, 0.06, X["rail"], bevel=0.006, tags=tags)
    B.box("tray_slot", 0, 0.12, 0.05, 1.76, 0.010, 0.016, X["graph_d"], bevel=0.0, tags=tags)
    # elevador (plataforma que sobe do paiol)
    lift = B.box("lift", 0, -0.72, 0.52, 0.30, 0.0, 0.05, X["steel"], bevel=0.01, tags=tags)
    B.cut(lift, [B.box(f"liftc{i}", -0.18 + i * 0.12, -0.72, 0.05, 0.22, 0.03, 0.2, X["black"], bevel=0.0)
                 for i in range(4)])
    # berco do paiol: 12 encaixes escuros com separadores de aco
    cradle = B.box("cradle", 0, MAG_Y, 1.78, 0.96, 0.0, 0.05, X["graph_d"], bevel=0.01, tags=tags)
    B.cut(cradle, [B.box(f"slot{j}", _mag_x(j), MAG_Y, 0.11, 0.86, 0.02, 0.2, X["black"], bevel=0.0)
                   for j in range(MAG_N)])
    for j in range(MAG_N):
        B.box(f"slotb{j}", _mag_x(j), MAG_Y, 0.11, 0.86, 0.0, 0.022, X["black"], bevel=0.0, tags=tags)
    for e, y in enumerate((MAG_Y - 0.47, MAG_Y + 0.47)):
        B.box(f"cradle_bar{e}", 0, y, 1.80, 0.04, 0.04, 0.08, X["steel"], bevel=0.006, tags=tags)
    # bancos de capacitores: encaixes vazios nas laterais (as celulas sao a camada capacitores)
    for sx in (-1, 1):
        bay = B.box(f"bay{sx}", sx * 1.27, -0.60, 0.36, 1.00, 0.0, 0.04, X["graph_d"], bevel=0.01, tags=tags)
        B.cut(bay, [B.box(f"bayc{sx}{i}", sx * 1.27, y, 0.30, 0.26, 0.02, 0.2, X["black"], bevel=0.0)
                    for i, y in enumerate(CAP_YS)])
        for i, y in enumerate(CAP_YS):
            B.box(f"bayb{sx}{i}", sx * 1.27, y, 0.30, 0.26, 0.0, 0.022, X["black"], bevel=0.0, tags=tags)
            B.box(f"bayk{sx}{i}", sx * 1.27, y, 0.10, 0.04, 0.02, 0.03, X["steel"], bevel=0.0, tags=tags)
        # barramento dos capacitores ate a culatra
        B.box(f"bus{sx}", sx * 0.70, 0.45, 0.07, 1.30, -0.02, 0.05, X["steel"], bevel=0.01, tags=tags)
        B.box(f"busk{sx}", sx * 0.70, 0.45, 0.02, 1.30, 0.05, 0.056, X["black"], bevel=0.0, tags=tags)
        B.box(f"busc{sx}", sx * 0.95, -0.12, 0.55, 0.06, -0.02, 0.04, X["graph_d"], bevel=0.008, tags=tags)
        # assento da tripulacao (o console fica na camada walls)
        cx, cy = CREW[0 if sx < 0 else 1]
        B.box(f"seat{sx}", cx, cy - 0.12, 0.30, 0.26, 0.0, 0.12, X["armor_mid"], bevel=0.04, tags=tags)
        B.box(f"seatb{sx}", cx, cy - 0.28, 0.30, 0.06, 0.0, 0.18, X["graph_d"], bevel=0.02, tags=tags)
        # entradas da fita nos cantos de tras (portas rafaeltessaro.bs_belt em [0,3]/[2,3])
        for k, (px_, py_, w_, h_) in enumerate(((sx * 1.40, -1.50, 0.12, 0.42), (sx * 1.0, -1.90, 0.42, 0.12))):
            fr = B.box(f"port{sx}{k}", px_, py_, w_, h_, 0.0, 0.05, X["steel"], bevel=0.008, tags=tags)
            B.cut(fr, [B.box(f"portc{sx}{k}", px_, py_, w_ * 0.6 if w_ > h_ else w_ * 0.5,
                             h_ * 0.5 if w_ > h_ else h_ * 0.6, 0.02, 0.2, X["black"], bevel=0.0)])
            B.box(f"portb{sx}{k}", px_, py_, w_ * 0.6, h_ * 0.6, 0.0, 0.025, X["black"], bevel=0.0, tags=tags)


def loader_magazine(M, T="projeteis", level=1):
    X = mats(M)
    tags = (T,)
    for n, j in enumerate(_mag_order()[:2 * level]):
        slug_round(f"mr{j}", _mag_x(j), MAG_Y, MAG_L, MAG_R, X, tags, tip_glow=0.0)


def loader_console(M, T="consola", phase=0.0, frame=1):
    """Console de um posto (o mesmo sprite nos 2 postos: simetrico). Mesa em arco na frente do tripulante (para a
    culatra), 2 telas com barras violeta que correm e uma fileira de LEDs (perseguicao) a cada quadro."""
    X = mats(M)
    tags = (T,)
    cx, cy = CREW[0]
    k = frame - 1
    desk = [(-0.42, 0.10), (-0.20, 0.20), (0.20, 0.20), (0.42, 0.10), (0.46, 0.30), (0.26, 0.45), (-0.26, 0.45),
            (-0.46, 0.30)]
    desk = [(cx + x, cy + y) for x, y in desk]
    a, p = gplate("desk", desk, 0.0, 0.20, X, tags, slope=0.03, groove=0.02, panel_h=0.02)
    # telas: recessos pretos com barras de luz
    for i, sx in enumerate((-1, 1)):
        scx, scy = cx + sx * 0.17, cy + 0.33
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.rbox(f"scrc{i}{t.name}", scx, scy, 0.20, 0.10, 0.15, 0.6, X["black"], rot=-sx * 14,
                                 bevel=0.0)])
        B.rbox(f"scrb{i}", scx, scy, 0.20, 0.10, 0.14, 0.155, X["black"], rot=-sx * 14, bevel=0.0, tags=tags)
        for b in range(4):
            hgt = 0.25 + 0.75 * ((b * 3 + k * (2 if i else 1)) % 4) / 3
            bx = scx - 0.06 + b * 0.04
            B.rbox(f"bar{i}{b}", bx, scy - 0.03 + 0.025 * hgt, 0.022, 0.05 * hgt, 0.155, 0.165,
                   violet(0.9) if b != (k % 4) else hot(CORE_W, 0.9, (0.3, 0.28, 0.22), "scrw"), rot=-sx * 14,
                   bevel=0.0, tags=tags)
    # fileira de LEDs na borda da mesa (um corre por quadro) + LED ambar de estado
    for t in (a, p):
        if t is not None:
            B.cut(t, [B.box(f"ledc{t.name}", cx, cy + 0.155, 0.30, 0.045, 0.14, 0.6, X["black"], bevel=0.0)])
    B.box("ledbed", cx, cy + 0.155, 0.30, 0.045, 0.13, 0.142, X["black"], bevel=0.0, tags=tags)
    for i in range(4):
        s = 1.2 if i == k else 0.25
        B.box(f"led{i}", cx - 0.105 + i * 0.07, cy + 0.155, 0.035, 0.022, 0.142, 0.150, violet(s), bevel=0.0,
              tags=tags)
    B.box("ledamb", cx + 0.36, cy + 0.17, 0.035, 0.035, 0.0, 0.215, amber(0.9 if k % 2 == 0 else 0.35), bevel=0.0,
          tags=tags)


def _jaws(X, tags, off, name="jaw"):
    """As 2 folhas da culatra (deslizam para os lados). off = 0 fechada .. JAW_OPEN aberta."""
    for sx in (-1, 1):
        x0, x1 = off + 0.004, off + JAW_W
        poly = chamfer_rect(x0, 1.08, x1, 1.92, (0.08, 0.0, 0.0, 0.08))
        if sx < 0:
            poly = mirror_x(poly)
        a, p = gplate(f"{name}{sx}", poly, 0.0, 0.22, X, tags, slope=0.03, groove=0.02, panel_h=0.025)
        # dentes de encaixe (recortes escuros na borda de dentro) e a lente da bobina da culatra
        cuts = [B.box(f"{name}_t{sx}{i}", sx * (x0 + 0.03), y, 0.06, 0.09, 0.08, 0.6, X["black"], bevel=0.0)
                for i, y in enumerate((1.30, 1.70))]
        B.cut(a, cuts)
        if p is not None:
            B.cut(p, [B.box(f"{name}_t2{sx}{i}", sx * (x0 + 0.03), y, 0.06, 0.09, 0.08, 0.6, X["black"], bevel=0.0)
                      for i, y in enumerate((1.30, 1.70))])
        lx = sx * (x0 + 0.12)
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.box(f"{name}_lc{sx}{t.name}", lx, 1.50, 0.05, 0.62, 0.14, 0.6, X["black"], bevel=0.0)])
        B.box(f"{name}_lb{sx}", lx, 1.50, 0.05, 0.62, 0.13, 0.145, X["black"], bevel=0.0, tags=tags)
        B.box(f"{name}_ll{sx}", lx, 1.50, 0.028, 0.56, 0.145, 0.152, X["lens"], bevel=0.0, tags=tags)
        # nervuras de pega na parte de fora
        for i in range(3):
            B.box(f"{name}_r{sx}{i}", sx * (x1 - 0.07), 1.30 + i * 0.2, 0.07, 0.03, 0.22, 0.25, X["steel"],
                  bevel=0.006, tags=tags)


def loader_jaws(M, T="culatra_abre", phase=0.0, frame=1):
    """culatra_abre1..3: 1 = fechada, 3 = aberta (o jogo toca ao contrario para fechar)."""
    X = mats(M)
    _jaws(X, (T,), JAW_OPEN * (frame - 1) / 2)


_LOAD_S = (0.0, 0.10, 0.32, 0.62, 0.88, 1.0)


def loader_load(M, T="culatra_carrega", phase=0.0, frame=1):
    """culatra_carrega1..6: o projetil sobe do elevador e o soquete o empurra pela bandeja ate a camara (folhas
    abertas, iguais a culatra_abre3)."""
    X = mats(M)
    tags = (T,)
    _jaws(X, tags, JAW_OPEN)
    y = TRAY_Y + (CHAMBER_Y - TRAY_Y) * _LOAD_S[frame - 1]
    slug_round("round", 0, y, ROUND_L, ROUND_R, X, tags, tip_glow=0.9)
    # soquete: cabeca de aco atras da base + haste telescopica escura ate a borda de baixo do sprite
    yb = y - ROUND_L / 2
    B.box("ram_head", 0, yb - 0.04, 0.24, 0.06, 0.06, 0.22, X["steel"], bevel=0.01, tags=tags)
    if yb - 0.07 > 0.0:
        B.box("ram_rod", 0, (yb - 0.07) / 2, 0.08, yb - 0.07, 0.10, 0.18, X["graph_d"], bevel=0.008, tags=tags)
        B.box("ram_rodk", 0, (yb - 0.07) / 2, 0.03, yb - 0.07, 0.18, 0.19, X["steel"], bevel=0.0, tags=tags)


def loader_breech(M, T="weapon"):
    """weapon.png [0,0,3,1]: bloco da culatra dos 2 lados da camara (a camara fica vazia: as folhas e o projetil
    estao na camada walls, abaixo desta)."""
    X = mats(M)
    tags = (T,)
    for sx in (-1, 1):
        poly = [(JAW_W, 1.02), (1.24, 1.02), (1.42, 1.16), (1.42, 1.72), (1.18, 1.97), (JAW_W, 1.97)]
        if sx < 0:
            poly = mirror_x(poly)
        B.box(f"core{sx}", sx * 0.9, 1.5, 1.0, 0.9, 0.0, 0.10, X["graph_d"], bevel=0.0, tags=tags)
        a, p = gplate(f"blk{sx}", poly, 0.0, 0.30, X, tags, slope=0.05, groove=0.026, panel_h=0.03)
        # recesso do pistao hidraulico da folha (mecanismo so no vao escuro)
        rec = [B.box(f"prc{sx}", sx * 0.80, 1.45, 0.62, 0.22, 0.14, 0.6, X["black"], bevel=0.0)]
        B.cut(a, rec)
        if p is not None:
            B.cut(p, [B.box(f"prc2{sx}", sx * 0.80, 1.45, 0.62, 0.22, 0.14, 0.6, X["black"], bevel=0.0)])
        B.box(f"pbed{sx}", sx * 0.80, 1.45, 0.62, 0.22, 0.12, 0.145, X["core"], bevel=0.0, tags=tags)
        B.cyl(f"pcyl{sx}", sx * 0.92, 1.45, 0.20, 0.07, 0.36, X["graph_d"], axis="X", verts=8, bevel=0.006,
              tags=tags)
        B.cyl(f"prod{sx}", sx * 0.62, 1.45, 0.20, 0.035, 0.30, X["rail"], axis="X", verts=8, bevel=0.004, tags=tags)
        B.cyl(f"pend{sx}", sx * 1.12, 1.45, 0.20, 0.08, 0.05, X["steel"], axis="X", verts=8, bevel=0.004, tags=tags)
        # emissor da bobina da culatra no canto da frente de dentro (lente violeta num recesso)
        ex = sx * (JAW_W + 0.05)
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.box(f"ec{sx}{t.name}", ex, LOADER_RING, 0.06, 0.20, 0.18, 0.6, X["black"], bevel=0.0)])
        B.box(f"eb{sx}", ex, LOADER_RING, 0.06, 0.20, 0.16, 0.185, X["black"], bevel=0.0, tags=tags)
        B.box(f"el{sx}", ex, LOADER_RING, 0.035, 0.16, 0.185, 0.195, X["lens"], bevel=0.0, tags=tags)
        # LEDs de estado e parafusos
        if p is not None:
            ledslot(f"st{sx}", sx * 0.80, 1.80, 0.36, 0.05, 0.33, 4, X, tags, [p, a], violet(0.55), vertical=False)
        bolts(f"bo{sx}", [(sx * 1.30, 1.25), (sx * 1.30, 1.62), (sx * 0.50, 1.12), (sx * 0.50, 1.88)], 0.335, X,
              tags, r=0.016)


def loader_caps(M, T="capacitores", level=1):
    """Banco de capacitores (bateria do carregador): o nivel k poe k celulas carregadas de cada lado."""
    X = mats(M)
    tags = (T,)
    for sx in (-1, 1):
        for i, y in enumerate(CAP_YS[:level]):
            poly = chamfer_rect(sx * 1.27 - 0.14, y - 0.12, sx * 1.27 + 0.14, y + 0.12, (0.07, 0.07, 0.07, 0.07))
            a, p = gplate(f"cell{sx}{i}", poly, 0.0, 0.20, X, tags, slope=0.025, groove=0.016, panel_h=0.02)
            for t in (a, p):
                if t is not None:
                    B.cut(t, [B.box(f"cc{sx}{i}{t.name}", sx * 1.27, y, 0.16, 0.08, 0.14, 0.6, X["black"],
                                    bevel=0.0)])
            B.box(f"cb{sx}{i}", sx * 1.27, y, 0.16, 0.08, 0.13, 0.145, X["black"], bevel=0.0, tags=tags)
            B.box(f"cl{sx}{i}", sx * 1.27, y, 0.12, 0.045, 0.145, 0.152, violet(1.1), bevel=0.0, tags=tags)
            B.box(f"ct{sx}{i}", sx * (1.27 - 0.10), y, 0.04, 0.16, 0.20, 0.23, X["steel"], bevel=0.005, tags=tags)


def loader_roof(M, T="roof"):
    """Teto do carregador: casa da culatra de grafite (continua as bochechas do cano) com a FENDA aberta sobre a
    camara (x 1.0-2.0, y 0.1-0.9 da peca), espinha com janela de sensor, casco pintado nas laterais com escotilhas
    sobre os postos, respiros dos capacitores e a porta blindada do paiol atras."""
    X = mats(M)
    tags = (T,)
    SX, SY0, SY1 = 0.5, 1.10, 1.90           # fenda
    # base escura (sem a fenda)
    B.box("u_back", 0, -0.45, 3.0, 2.9, -0.06, 0.0, X["core"], bevel=0.0, tags=tags)
    B.box("u_rear", 0, SY0 - 0.075 + 0.0, 1.0, 0.15, -0.06, 0.0, X["core"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"u_side{sx}", sx * 1.0, 1.55, 1.0, 1.1 + 2 * EXT, -0.06, 0.0, X["core"], bevel=0.0, tags=tags)
    B.box("u_front", 0, (SY1 + 2.0 + EXT) / 2, 1.0, 2.0 + EXT - SY1, -0.06, 0.0, X["core"], bevel=0.0, tags=tags)
    # casco pintado: coluna de fora (3 placas por lado; a fileira da culatra e o anel blindado)
    for sx in (-1, 1):
        _deck_plates(f"dk{sx}", CHEEK_OUT + 0.02 if sx > 0 else -1.5, 1.5 if sx > 0 else -CHEEK_OUT - 0.02,
                     [(0.5, 1.0), (-0.5, 1.0), (-1.5, 1.0)], X, tags)
    # ANEL DA CULATRA: colar de largura inteira na frente (fecha o canal na culatra; passa da camera e encosta no
    # 1o cano) + ombros macicos dos dois lados da fenda, com garras inclinadas para a frente e respiros
    a, p = gplate("collar", chamfer_rect(-1.46, SY1 + 0.02, 1.46, 2.0 + EXT, (0.12, 0.12, 0.0, 0.0)),
                  0.0, 0.17, X, tags, slope=0.045, groove=0.024)
    if p is not None:
        ledslot("col_led", 0, SY1 + 0.075, 0.40, 0.045, 0.20, 5, X, tags, [p, a], violet(0.6), vertical=False)
        for sx in (-1, 1):
            ledslot(f"col_amb{sx}", sx * 1.18, SY1 + 0.075, 0.22, 0.045, 0.20, 2, X, tags, [p, a], amber(0.8),
                    vertical=False)
    for sx in (-1, 1):
        poly = chamfer_rect(SX + 0.02, SY0 - 0.06, 1.46, SY1 - 0.01, (0.0, 0.20, 0.14, 0.0))
        if sx < 0:
            poly = mirror_x(poly)
        a2, p2 = gplate(f"slotblk{sx}", poly, 0.0, 0.24, X, tags, slope=0.05, groove=0.026)
        if p2 is not None:
            vents = [B.box(f"sbv{sx}{i}", sx * 1.20, 1.26 + i * 0.10, 0.30, 0.05, 0.18, 0.6, X["black"], bevel=0.0)
                     for i in range(4)]
            B.cut(p2, vents)
            B.cut(a2, [B.box(f"sbva{sx}{i}", sx * 1.20, 1.26 + i * 0.10, 0.30, 0.05, 0.18, 0.6, X["black"],
                             bevel=0.0) for i in range(4)])
            for i in range(4):
                B.box(f"sbvb{sx}{i}", sx * 1.20, 1.26 + i * 0.10, 0.30, 0.05, 0.16, 0.185, X["core"], bevel=0.0,
                      tags=tags)
        claw = [(SX + 0.08, SY0 + 0.22), (0.98, SY0 + 0.02), (0.98, SY1 - 0.24), (SX + 0.08, SY1 - 0.06)]
        if sx < 0:
            claw = mirror_x(claw)
        ca, cp = gplate(f"claw{sx}", claw, 0.24, 0.33, X, tags, slope=0.03, groove=0.02, panel_h=0.022)
        if cp is not None:
            ledslot(f"claw_led{sx}", sx * 0.76, 1.47, 0.05, 0.30, 0.355, 3, X, tags, [cp, ca], violet(0.6))
        bolts(f"sbb{sx}", [(sx * 1.36, 1.12), (sx * 1.36, 1.80)], 0.275, X, tags, r=0.017)
        # labio claro na borda da fenda
        B.box(f"slip{sx}", sx * (SX + 0.012), (SY0 + SY1) / 2, 0.024, SY1 - SY0, 0.0, 0.26, X["rail"], bevel=0.006,
              tags=tags)
    B.box("slip_r", 0, SY0 - 0.012, 2 * SX + 0.05, 0.024, 0.0, 0.20, X["rail"], bevel=0.006, tags=tags)
    B.box("slip_f", 0, SY1 + 0.012, 2 * SX + 0.05, 0.024, 0.0, 0.18, X["rail"], bevel=0.006, tags=tags)
    # placa de tras da fenda + espinha com janela de sensor
    a3, p3 = gplate("rearhouse", chamfer_rect(-CHEEK_OUT, -0.32, CHEEK_OUT, SY0 - 0.03, (0.20, 0.20, 0.0, 0.0)),
                    0.0, 0.16, X, tags, slope=0.045, groove=0.024)
    spine = [(-0.30, -0.24), (0.30, -0.24), (0.30, 0.70), (0.0, 0.98), (-0.30, 0.70)]
    sa, sp = gplate("spine", spine, 0.16, 0.30, X, tags, slope=0.04, groove=0.022, panel_h=0.03)
    for t in (sa, sp):
        if t is not None:
            B.cut(t, [B.box(f"win{t.name}", 0, 0.42, 0.26, 0.10, 0.24, 0.8, X["black"], bevel=0.0)])
    B.box("win_bed", 0, 0.42, 0.26, 0.10, 0.22, 0.245, X["black"], bevel=0.0, tags=tags)
    B.box("win_slit", 0, 0.42, 0.16, 0.022, 0.245, 0.252, violet(1.0), bevel=0.0, tags=tags)
    if sp is not None:
        B.cut(sp, [B.box(f"spl{i}", 0, -0.05 + i * 0.12, 0.40, 0.016, 0.28, 0.6, X["black"], bevel=0.0)
                   for i in range(2)])
    for sx in (-1, 1):
        if p3 is not None:
            ledslot(f"rh_led{sx}", sx * 0.58, 0.40, 0.05, 0.62, 0.19, 4, X, tags, [p3, a3], violet(0.55))
        # escotilha sobre o posto da tripulacao (casco pintado)
        hx, hy = sx * 1.18, 0.40
        hatch = B.rpoly(hx, hy, 0.46, 0.46, 0, chamfer=0.10)
        B.plate(f"hatch{sx}", hatch, 0.06, 0.10, X["armor_mid"], slope=0.02, tags=tags)
        B.box(f"hatch_h{sx}", hx, hy - 0.12, 0.20, 0.045, 0.10, 0.13, X["steel"], bevel=0.01, tags=tags)
        # respiro do banco de capacitores com 3 pips violeta
        vx, vy = sx * 1.18, -0.62
        v = B.box(f"cvent{sx}", vx, vy, 0.42, 0.50, 0.05, 0.11, X["core_mid"], bevel=0.008, tags=tags)
        B.cut(v, [B.box(f"cvc{sx}{i}", vx, vy - 0.16 + i * 0.08, 0.34, 0.03, 0.09, 0.3, X["core"], bevel=0.0)
                  for i in range(4)])
        B.box(f"cvl_bed{sx}", vx, vy + 0.19, 0.30, 0.05, 0.10, 0.112, X["black"], bevel=0.0, tags=tags)
        for i in range(3):
            B.box(f"cvl{sx}{i}", vx - 0.09 + i * 0.09, vy + 0.19, 0.05, 0.026, 0.112, 0.118, violet(0.7),
                  bevel=0.0, tags=tags)
    # porta blindada do paiol (2 folhas em divisa para a frente) entre as colunas pintadas
    B.box("magframe", 0, -1.18, 1.72, 1.56, 0.0, 0.08, X["graph_d"], bevel=0.01, tags=tags)
    for j, sx in enumerate((-1, 1)):
        leaf = [(0.02, -1.90), (0.80, -1.90), (0.80, -0.62), (0.62, -0.46), (0.02, -0.66)]
        if sx < 0:
            leaf = mirror_x(leaf)
        la, lp = gplate(f"leaf{j}", leaf, 0.08, 0.17, X, tags, slope=0.035, groove=0.022, panel_h=0.025)
        if lp is not None:
            B.cut(lp, [B.box(f"lg{j}{i}", sx * 0.42, -1.70 + i * 0.16, 0.50, 0.018, 0.15, 0.5, X["black"], bevel=0.0)
                       for i in range(5)])
        B.box(f"lhinge{j}", sx * 0.77, -1.30, 0.05, 0.40, 0.17, 0.20, X["steel"], bevel=0.008, tags=tags)
    B.box("mlatch", 0, -1.25, 0.06, 0.70, 0.17, 0.215, X["steel"], bevel=0.01, tags=tags)
    ledslot("mag_led", 0, -1.82, 0.36, 0.045, 0.20, 4, X, tags, [], violet(0.6), vertical=False, depth=0.03)
    coaming("coam", SY1 + 0.02, 2.0 + EXT, X, tags, z=0.13)


# ============================================================================ PONTA (3x4)
# coroa (weapon.png) em y 0.5..2 (fileiras 0-1.5 da peca); teto com o canal aberto de -2 ate a coroa
CROWN_Y0 = 0.52
PONTA_BRIDGE = -2.0 + 0.55
BORE = 0.20                               # meia largura do furo (garganta) entre as pontas da coroa
RING_Y0, RING_Y1 = 0.56, 0.98             # anel EM da coroa
CROWN_RING_Y = 0.77                       # sulco emissor do anel


def ponta_floor(M, T="floor"):
    X = mats(M)
    tags = (T,)
    B.box("fl_base", 0, 0, 3.3, 4.3, -0.06, -0.02, X["core"], bevel=0.0, tags=tags)
    channel_floor("ch", -2.0 - EXT, CROWN_Y0 + 0.05, X, tags, rib_y0=-1.875)
    channel_floor("bore", CROWN_Y0 + 0.05, 2.0 + EXT, X, tags, hw=BORE - 0.02, rib_y0=-1.875 + 0.25 * 10)
    # garganta: o fundo escurece para a boca (a "boca" do canhao le escura a 1x)
    for i, (ya, yb_, m) in enumerate(((1.30, 1.62, X["graph_d"]), (1.62, 2.0 + EXT, X["black"]))):
        B.box(f"throat{i}", 0, (ya + yb_) / 2, 2 * BORE - 0.04, yb_ - ya, 0.026, 0.032, m, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"bus{sx}", sx * 0.70, -0.75, 0.08, 2.5 + EXT, -0.02, 0.05, X["steel"], bevel=0.01, tags=tags)
        B.box(f"busk{sx}", sx * 0.70, -0.75, 0.02, 2.5 + EXT, 0.05, 0.056, X["black"], bevel=0.0, tags=tags)
        for k, yc in enumerate((-1.5, -0.5)):
            B.box(f"fp{sx}{k}", sx * 1.10, yc, 0.74, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)
            mod = chamfer_rect(0.86, yc - 0.34, 1.36, yc + 0.34, (0.06, 0.06, 0.06, 0.06))
            if sx < 0:
                mod = mirror_x(mod)
            a, p = gplate(f"cap{sx}{k}", mod, 0.0, 0.12, X, tags, slope=0.03, groove=0.02, panel_h=0.02)
            B.cut(p if p is not None else a, [B.box(f"capf{sx}{k}{i}", sx * 1.11, yc - 0.20 + i * 0.08, 0.36,
                                                     0.022, 0.10, 0.4, X["black"], bevel=0.0) for i in range(6)])
            B.box(f"capled{sx}{k}", sx * 1.11, yc + 0.26, 0.20, 0.03, 0.10, 0.145, violet(0.7), bevel=0.0,
                  tags=tags)
        for k, yc in enumerate((0.5, 1.5)):
            B.box(f"fq{sx}{k}", sx * 0.92, yc, 1.08, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)


def ponta_rails(M, T="trilhos"):
    X = mats(M)
    tags = (T,)
    rails("r", -2.0 - EXT, 1.90, X, tags)
    for sx in (-1, 1):
        B.box(f"rend{sx}", sx * (RAIL_IN + RAIL_OUT) / 2, 1.90, 0.12, 0.06, 0.0, 0.14, X["steel"], bevel=0.01,
              tags=tags)
    rail_clips("clip", (-1.75, -1.25, -0.75, -0.25, 0.25), X, tags)
    for i, y in enumerate(PONTA_RINGS):
        em_ring(f"ring{i}", y, 0.0, X, tags)
    # emissores da coroa: bandas finas sob o furo (acendem na carga)
    for i, y in enumerate(CROWN_RINGS):
        B.box(f"cband{i}", 0, y, 2 * BORE + 0.06, 0.07, -0.01, 0.034, X["graph_d"], bevel=0.004, tags=tags)
        B.box(f"cbandl{i}", 0, y, 2 * BORE - 0.04, 0.03, 0.034, 0.044, X["lens"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"shoe{sx}", sx * 0.50, PONTA_BRIDGE, 0.26, 0.22, 0.0, 0.10, X["graph_d"], bevel=0.012, tags=tags)


def ponta_crown(M, T="weapon"):
    """weapon.png [0,0,3,1.5]: a BOCA. Anel EM da coroa (largo, octogonal) cruzando o furo com o sulco emissor
    violeta, orelhas de freio com venezianas dos lados, e as duas PONTAS blindadas com dentes (os trilhos saem como
    garfo) emoldurando a garganta escura; emissores violeta nas faces de dentro das pontas, num recesso."""
    X = mats(M)
    tags = (T,)
    zr = 0.34
    # anel da coroa (atravessa o furo: o projetil passa por baixo)
    ring = chamfer_rect(-1.44, RING_Y0, 1.44, RING_Y1, (0.16, 0.16, 0.12, 0.12))
    B.box("ring_core", 0, (RING_Y0 + RING_Y1) / 2, 2.6, RING_Y1 - RING_Y0 - 0.1, 0.0, 0.12, X["graph_d"], bevel=0.0,
          tags=tags)
    ra, rp = gplate("ring", ring, 0.0, zr, X, tags, slope=0.06, groove=0.03, panel_h=0.035)
    for t in (ra, rp):
        if t is not None:
            B.cut(t, [B.box(f"rg{t.name}", 0, CROWN_RING_Y, 2.30, 0.10, zr - 0.12, 0.9, X["black"], bevel=0.0)])
    B.box("rg_bed", 0, CROWN_RING_Y, 2.30, 0.10, zr - 0.14, zr - 0.115, X["black"], bevel=0.0, tags=tags)
    B.box("rg_lens", 0, CROWN_RING_Y, 2.20, 0.046, zr - 0.115, zr - 0.105, X["lens"], bevel=0.0, tags=tags)
    for i, x in enumerate((-0.72, -0.24, 0.24, 0.72)):
        B.box(f"rg_tie{i}", x, CROWN_RING_Y, 0.05, 0.10, zr - 0.14, zr - 0.04, X["steel"], bevel=0.006, tags=tags)
    bolts("rb", [(sx * 1.30, y) for sx in (-1, 1) for y in (RING_Y0 + 0.10, RING_Y1 - 0.08)], zr + 0.035, X, tags,
          r=0.017)
    for sx in (-1, 1):
        # orelha do freio (venezianas transversais)
        ear = [(0.66, RING_Y1 - 0.02), (1.44, RING_Y1 - 0.02), (1.44, 1.20), (1.20, 1.44), (0.66, 1.44)]
        if sx < 0:
            ear = mirror_x(ear)
        B.box(f"ear_core{sx}", sx * 1.02, 1.18, 0.70, 0.44, 0.0, 0.10, X["graph_d"], bevel=0.0, tags=tags)
        ea, ep = gplate(f"ear{sx}", ear, 0.0, 0.26, X, tags, slope=0.05, groove=0.026, panel_h=0.03)
        louv = lambda tag: [B.box(f"lv{tag}{sx}{i}", sx * 0.98, 1.06 + i * 0.09, 0.46, 0.045, 0.14, 0.8,
                                  X["black"], bevel=0.0) for i in range(4)]  # noqa: E731
        B.cut(ea, louv("a"))
        if ep is not None:
            B.cut(ep, louv("p"))
        for i in range(4):
            B.box(f"lvb{sx}{i}", sx * 0.98, 1.06 + i * 0.09, 0.46, 0.045, 0.12, 0.145, X["core"], bevel=0.0,
                  tags=tags)
        bolts(f"eb{sx}", [(sx * 1.32, 1.08), (sx * 0.74, 1.36)], 0.295, X, tags, r=0.015)
        # ponta (dente duplo na borda de fora, ponta chanfrada para dentro)
        prong = [(BORE, RING_Y1 - 0.03), (0.62, RING_Y1 - 0.03), (0.62, 1.44), (0.56, 1.50), (0.56, 1.74),
                 (0.44, 1.98), (BORE, 1.98)]
        if sx < 0:
            prong = mirror_x(prong)
        pa, pp = gplate(f"prong{sx}", prong, 0.0, 0.40, X, tags, slope=0.05, groove=0.026, panel_h=0.03)
        ex = sx * (BORE + 0.045)
        for t in (pa, pp):
            if t is not None:
                B.cut(t, [B.box(f"pe{sx}{t.name}", ex, 1.46, 0.06, 0.92, 0.20, 0.9, X["black"], bevel=0.0)])
        B.box(f"peb{sx}", ex, 1.46, 0.06, 0.92, 0.18, 0.205, X["black"], bevel=0.0, tags=tags)
        B.box(f"pel{sx}", ex, 1.46, 0.034, 0.86, 0.205, 0.214, X["lens"], bevel=0.0, tags=tags)
        if pp is not None:
            ledslot(f"pl{sx}", sx * 0.46, 1.36, 0.05, 0.30, 0.43, 3, X, tags, [pp, pa], violet(0.55))
        bolts(f"pb{sx}", [(sx * 0.50, 1.10)], 0.435, X, tags, r=0.015)


def ponta_roof(M, T="roof"):
    X = mats(M)
    tags = (T,)
    y0 = -2.0 - EXT
    for sx in (-1, 1):
        B.box(f"under{sx}", sx * (CH + 1.5) / 2, (y0 + CROWN_Y0) / 2, 1.5 - CH, CROWN_Y0 - y0, -0.06, 0.0,
              X["core"], bevel=0.0, tags=tags)
        _deck_plates(f"dk{sx}", 1.12 if sx > 0 else -1.5, 1.5 if sx > 0 else -1.12,
                     [(-1.5, 1.0), (-0.5, 1.0)], X, tags)
        # placa pintada da fileira da coroa (ao lado do colar) e o ombro pintado em volta das pontas
        sh = [(0.67, 1.48), (1.22, 1.48), (1.47, 1.23), (1.47, 1.97), (0.67, 1.97)]
        if sx < 0:
            sh = mirror_x(sh)
        B.shard(f"shoulder{sx}", sh, 0.0, 0.06, X["green"], slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
        B.loft(f"shu{sx}", sh, sh, -0.06, 0.0, X["core"], bevel=0.0, tags=tags)
        sq = chamfer_rect(1.12, 0.03, 1.47, RING_Y0 - 0.03, (0.09, 0.09, 0.0, 0.0))
        if sx < 0:
            sq = mirror_x(sq)
        B.shard(f"sq{sx}", sq, 0.0, 0.06, X["green"], slope=0.025, groove=0.04, panel_h=0.02, tags=tags)
    # bochecha da emenda (continua o cano de tras), ponte, e o capuz da boca (bochechas largas e altas)
    yb1 = PONTA_BRIDGE + BRIDGE_HW
    cheek("chk_b", y0, PONTA_BRIDGE - BRIDGE_HW + 0.02, X, tags, c0=0.0, c1=0.12)
    bridge("br", PONTA_BRIDGE, X, tags)
    out = []
    for sx in (-1, 1):
        poly = [(CH + 0.02, yb1 - 0.02), (0.86, yb1 - 0.02), (1.10, yb1 + 0.30), (1.10, CROWN_Y0 + 0.04),
                (CH + 0.02, CROWN_Y0 + 0.04)]
        if sx < 0:
            poly = mirror_x(poly)
        out.append(gplate(f"shroud{sx}", poly, 0.0, 0.16, X, tags))
    chevron_plate("chv", yb1 + 0.12, CROWN_Y0 - 0.06, X, tags, x_in=0.50, x_out=0.98, lean=0.22, z0=0.16,
                  z1=0.25, leds=4)
    for sx in (-1, 1):
        bolts(f"sb{sx}", [(sx * 1.02, yb1 + 0.50), (sx * 1.02, CROWN_Y0 - 0.10)], 0.19, X, tags, r=0.016)
    coaming("coam", y0, CROWN_Y0 + 0.04, X, tags, z=0.16)


def slug_sprite(M, T="slug"):
    """slug.png (0.8 x 3, ChainedTo Projectile, camada walls): o MESMO modelo do slug em voo
    (parts/bs_shells2.py, item "slug"), de pe (ponta para +Y), na luz das pecas."""
    import bpy
    from parts import bs_shells2
    sc = bpy.context.scene
    before = set(o.name for o in sc.objects)
    bs_shells2.model(M, "slug", T, 0.0)
    emp = bpy.data.objects.new("slug_root", None)
    sc.collection.objects.link(emp)
    for o in [o for o in sc.objects if o.name not in before and o.parent is None and o is not emp]:
        o.parent = emp
    emp.rotation_euler.z = math.radians(90)
    emp.location = (0.0, 0.0, 0.0)
