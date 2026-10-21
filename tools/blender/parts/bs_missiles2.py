"""Misseis 2.0 do Bullet Strike (kind "missiles", 64 px/tile): a escada futurista dos misseis em voo.

Pedido do usuario (2026-10-21): "os misseis tambem estao sendo refeitos ne? para deixa-los com aparencia mais
futurista". Mesma familia das granadas 2.0 (tools/blender/parts/bs_shells2.py): nucleo escuro + luvas de COMPOSITO
claro (sRGB ~170, le no espaco escuro E no casco branco) com frestas pretas, faixas de LED em recessos, narizes
sensores de lente escura, luvas segmentadas; quanto maior o missil (s -> m -> l), mais futurista.

Conjunto 2.0 (design/art/spec_art.json -> assets.missiles; design/missiles/spec_missiles.json). Os tipos removidos
(napalm, lapa, torpedo isca, iscas) NAO existem aqui:

  Jararaca (HE, ambar)      he_s  Muricoca micro (Tocandira): luva lisa partida por 1 faixa de LED ambar, ogiva clara
                                  com o domo do buscador de LENTE escura, 2 aletas
                            he_m  (Caipora): luvas em divisa, anel de LED na cauda, fendas de trilho em V acesas no
                                  ombro da ogiva, canards, buscador de lente
                            he_l  (Mula): 2 estagios; reforco segmentado com aletas grandes e anel de separacao com 3
                                  LEDs que correm; sustentador de blindagem segmentada (paineis de chanfro duplo),
                                  estrakes, faixa dupla, nariz sensor com visor de lente e scanner de 3 LEDs
  Piranha (cluster, amarela) cluster_m / cluster_l  PORTADOR gordo (estilo "Sunflower"/Transformers): baias com
                                  JANELAS onde se veem os narizes dos mini-misseis enfileirados, LEDs de armar que
                                  correm de baia em baia ate o nariz, faixa amarela e o nariz em 4 PETALAS (4 cascas
                                  separadas por frestas pretas que convergem na ponta, dobradicas na base, olho escuro
                                  na ponta). O l tem paineis de chanfro duplo nos ombros e canards.
                            cluster_mini  mini-misseil teleguiado (0.5 x 0.19 quadro = 32 x 12 px): corpo claro, nariz
                                  escuro, faixa amarela, aletas e o COLAR LARANJA do propulsor pintado (sem atlas de
                                  luzes; as regras nao usam as normais dele)
                            atlas de particulas bs_petals_m / bs_petals_l (+ _normals): as 4 petalas do nariz,
                                  256 x 256 = 4 x 4 de 64 px (fileira = petala com o seu giro proprio, coluna =
                                  inclinacao 0/30/55/75 graus), formato do debris_def.rules do jogo
  Poraque (PEM, azul-ciano) emp_m / emp_l  corpo ENROLADO em bobinas de fio de cobre (Mo.copper_mat, assinatura PEM)
                                  sobre a capsula escura, frestas ciano entre as bobinas por onde a carga corre ate o
                                  emissor do nariz (olho ciano); barbatanas-fita da enguia; o l ganha mais bobinas,
                                  blindagem segmentada na cauda, anel ciano na base e o garfo emissor de 2 pontas.
                                  Sem faixa de ogiva, sem listras
  Iara (nuclear, verde)     nuclear_l (estagio) / nuclear_wh_l (ogiva): continua INCONFUNDIVEL (o unico missil de
                                  blindagem escura): ogiva gorda blindada com o trevo grande (cunhas pretas sobre
                                  disco verde), DOIS aneis de faixa de perigo verde/preto em divisas emoldurando a
                                  ogiva, JANELAS DE CONTENCAO verdes acesas nos ombros (com grade de aco), faixas
                                  verdes largas que respiram, janela do nucleo, nariz sensor de lente com anel verde,
                                  blindagem segmentada, bocal triplo com aneis verdes, 4 aletas escuras de bordo claro;
                                  o estagio leva 2 propulsores laterais segmentados. Nunca amarelo/preto.

Telas, quadros/fps, bocais e ancoras = os da tabela de arte dos misseis da Fase B (bs_missiles), menos os itens
removidos; cluster_mini e novo (0.5 x 0.19, estatico). Emissivos so em recessos, <= 3% do corpo no quadro 0
(Iara 4%); forcas baixas (a vista Standard estoura acima de ~1.5; azul/verde com cores proprias).

Cores de tipo (faixa + LEDs): HE ambar (Mo.band_mat("he")), Piranha AMARELA (Mo.band_mat("cluster"), o mesmo
"yellow petal cap" dos narizes da Piranha nos casulos e o amarelo do escapamento da Fase B: o laranja
palette.cluster.band do spec de arte (255,150,40) fica a ~10 graus de matiz do ambar da HE e nao se distingue a 1x),
Poraque ciano-azul (palette.pem), Iara verde.

    $PY tools/blender/render_part.py bs_missiles2 --quick --out <rascunho> [--only he_m,cluster_l]
    $PY tools/blender/render_part.py bs_missiles2            # final em art3d/bs_missiles2/
    $PY tools/blender/parts/bs_missiles2.py --atlases [--quick] [--out DIR]   # petalas (depois do render: o
                                                                                # meta.json ganha "atlases")
    python3 tools/check_art3d.py art3d/bs_missiles2
"""

import math
import os
import sys

if __name__ == "__main__":                 # --atlases: roda direto (python com bpy), precisa do kit no caminho
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import bpy  # noqa: F401  (o bpy carrega o bmesh que o bs3d importa)

import bs3d as B  # noqa: E402
import models as Mo  # noqa: E402


def _it(L, W, frames, fps, nozzle_x, anchors=None):
    return {"canvas_tiles": [L, W], "frames": frames, "fps": fps, "wrap": None, "nozzle_x": nozzle_x, "mask": False,
            "anchors": anchors or {}}


PART = {
    "id": "rafaeltessaro.bs_missiles2",
    "kind": "missiles",
    "px_per_tile": 64,
    "accent": "amber",
    # halo do atlas de luzes (px): curto, os LEDs ficam nitidos e o orcamento de 3% inclui o halo forte
    "halo_px": 1.8,
    "items": {
        "he_s": _it(1.0, 0.375, 2, 4, -0.47, {"seeker": [0.46, 0.0]}),
        "he_m": _it(1.75, 0.625, 2, 4, -0.86, {"seeker": [0.83, 0.0]}),
        "he_l": _it(2.5, 0.875, 3, 6, -1.18, {"seeker": [1.20, 0.0]}),
        "cluster_m": _it(1.75, 0.75, 3, 8, -0.86, {"seeker": [0.83, 0.0]}),
        "cluster_l": _it(2.5, 1.0, 4, 8, -1.18, {"seeker": [1.20, 0.0]}),
        # mini-missil: estatico (sem atlas), 32 x 12 px; a Mula usa x1.2 (size_mul nas regras)
        "cluster_mini": _it(0.5, 0.19, 1, 0, -0.23, {"seeker": [0.22, 0.0]}),
        "emp_m": _it(1.75, 0.75, 4, 12, -0.86, {"seeker": [0.80, 0.0]}),
        "emp_l": _it(2.5, 1.0, 4, 12, -1.18, {"seeker": [1.10, 0.0]}),
        "nuclear_l": _it(3.75, 1.5, 4, 6, -1.86, {"seeker": [1.83, 0.0], "warhead": [0.995, 0.0],
                                                  "radiation": [0.995, 0.0]}),
        "nuclear_wh_l": _it(3.1, 1.5, 4, 6, -1.53, {"seeker": [1.50, 0.0], "warhead": [0.67, 0.0],
                                                    "radiation": [0.67, 0.0]}),
    },
    # atlas de particulas das petalas (nao e item: render_part ignora; --atlases neste arquivo renderiza)
    "atlases": {
        "petals_m": {"file": "bs_petals_m.png", "normals": "bs_petals_m_normals.png", "tier": "m",
                     "texture_px": 256, "sprite_px": 64, "per_row": 4, "count": 16},
        "petals_l": {"file": "bs_petals_l.png", "normals": "bs_petals_l_normals.png", "tier": "l",
                     "texture_px": 256, "sprite_px": 64, "per_row": 4, "count": 16},
    },
}

A0 = math.pi / 8                    # octogono de topo plano
COS8 = math.cos(math.pi / 8)        # apotema / raio
TOPW = 2 * math.sin(math.pi / 8)    # largura da face de cima / raio

# ---- cores (as mesmas das granadas 2.0; nomes proprios "m2_*": o cache de materiais do bs3d e por nome)
COMP = (0.34, 0.352, 0.375)         # composito claro das luvas (sRGB ~170)
COMP_D = (0.17, 0.175, 0.185)       # composito medio
GRAPH = (0.085, 0.09, 0.10)         # grafite
CORE = (0.030, 0.032, 0.037)        # nucleo quase preto
STEEL = (0.50, 0.52, 0.55)          # aco claro
PEM_BODY = (0.050, 0.053, 0.060)    # capsula escura do Poraque
IARA_DARK = (0.060, 0.063, 0.070)   # blindagem escura da Iara
IARA_PLATE = (0.15, 0.155, 0.165)   # placas da Iara (composito medio escuro: contorno no espaco)
ORANGE = (0.95, 0.30, 0.03)         # colar quente do mini-missil (tinta)

# ---- LEDs por tipo (emissao; forca ~1 sai ~ a cor do palette na vista Standard)
LED = {"he": (1.0, 0.45, 0.05), "cluster": (1.0, 0.85, 0.10), "emp": (0.02, 0.72, 1.0),
       "nuke": (0.15, 1.0, 0.01)}
# BS_M2_CLUSTER=palette: variante so para a prev/decisao (laranja palette.cluster.band 255,150,40 do spec de arte);
# o padrao e o AMARELO-limao (o mesmo amarelo dos narizes da Piranha nos casulos e do escapamento da Fase B)
CLUSTER_PALETTE = os.environ.get("BS_M2_CLUSTER", "") == "palette"
if CLUSTER_PALETTE:
    LED["cluster"] = (1.0, 0.305, 0.021)

# faixas pintadas por tipo (o mesmo material dos narizes carregados nos casulos)
BAND_LOOK = {"he": "he", "cluster": "cluster", "emp": "emp", "nuke": "nuclear"}


def _spec(m, v):
    """Reflexo especular baixo (luz axial: a face de cima nao pode sair mais escura que as facetas)."""
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = v
    return m


def _mats(M):
    return {
        "comp": B.mat_paint("m2_comp", COMP, rough=0.40, metal=0.15, wear=0.0, grime=0.03, scale=5),
        "comp_d": _spec(B.mat_metal("m2_comp_d", COMP_D, rough=0.45, metal=0.3), 0.25),
        "graph": _spec(B.mat_metal("m2_graph", GRAPH, rough=0.45, metal=0.35), 0.25),
        "core": _spec(B.mat_metal("m2_core", CORE, rough=0.62, metal=0.0), 0.05),
        "steel": _spec(B.mat_metal("m2_steel", STEEL, rough=0.36, metal=0.55), 0.3),
        "lens": _spec(B.mat_metal("m2_lens", (0.010, 0.012, 0.018), rough=0.14, metal=0.0), 0.7),
        "nose": Mo.nose_paint("nose", Mo.NOSE_LIGHT),       # tinta clara dos narizes (minis nas baias)
        "pem": _spec(B.mat_metal("m2_pem_body", PEM_BODY, rough=0.5, metal=0.2), 0.12),
        "copper": Mo.copper_mat(),
        "dark": B.mat_paint("m2_iara_dark", IARA_DARK, rough=0.42, metal=0.45, wear=0.0, grime=0.03, scale=5),
        "plate": B.mat_paint("m2_iara_plate", IARA_PLATE, rough=0.40, metal=0.35, wear=0.0, grime=0.03, scale=5),
        "orange": B.mat_paint("m2_orange", ORANGE, rough=0.45, metal=0.1, wear=0.0, grime=0.0, scale=5),
        "black": M["black"],
    }


def _band(look):
    if look == "cluster" and CLUSTER_PALETTE:
        m = B.mat_metal("m2_band_cluster_pal", (0.80, 0.244, 0.017), rough=0.65, metal=0.0)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Specular IOR Level"].default_value = 0.0
        b.inputs["Emission Color"].default_value = (1.0, 0.305, 0.021, 1)
        b.inputs["Emission Strength"].default_value = 0.12
        m["bs_glow"] = 0.12
        return m
    return Mo.band_mat(BAND_LOOK[look])


def _lt(LT, s):
    """Tags de um LED com forca s neste quadro: apagado (s = 0) sai SEM a tag "lights" (vira Holdout no atlas =
    transparente); no difuso a lente escura continua la."""
    return LT if s > 1e-6 else LT[:1]


def _led(color, s):
    """LED: emissao na cor com forca s; no difuso sai como LENTE ESCURA levemente tingida (STYLE 11.5)."""
    m = B.mat_glow(f"m2_led_{color}_{int(round(s * 100)):03d}", LED[color], s)
    b = m.node_tree.nodes["Principled BSDF"]
    c = LED[color]
    b.inputs["Base Color"].default_value = (c[0] * 0.02, c[1] * 0.02, c[2] * 0.02, 1)
    b.inputs["Roughness"].default_value = 0.45
    return m


# ============================================================================ geometria basica
def octo(name, prof, mat, tags, zc=0.0, y=0.0):
    """Solido de revolucao octogonal de topo plano no eixo X (perfil [(raio, x)], faces planas)."""
    ob = Mo.lathe(name, prof, mat, tags, verts=8, axis="X", zc=zc, a0=A0, smooth=False)
    if y:
        ob.location = (0.0, y, 0.0)
    return ob


def poly16(name, prof, mat, tags, y=0.0):
    """Solido de 16 lados facetado (bobinas, corpos redondos grandes)."""
    ob = Mo.lathe(name, prof, mat, tags, verts=16, axis="X", a0=math.pi / 16, smooth=False)
    if y:
        ob.location = (0.0, y, 0.0)
    return ob


def smooth(name, prof, mat, tags, verts=24, y=0.0):
    ob = Mo.lathe(name, prof, mat, tags, verts=verts, axis="X", smooth=True)
    if y:
        ob.location = (0.0, y, 0.0)
    return ob


def ring(name, xa, xb, r, mat, tags, ch=0.0, y=0.0):
    """Anel octogonal de xa a xb no raio r; ch = chanfro (raio menor nas pontas)."""
    if ch > 0:
        ch = min(ch, (xb - xa) * 0.45)
        return octo(name, [(r - ch, xa), (r, xa + ch), (r, xb - ch), (r - ch, xb)], mat, tags, y=y)
    return octo(name, [(r, xa), (r, xb)], mat, tags, y=y)


def _r_at(prof, x):
    for (ra, xa), (rb, xb) in zip(prof, prof[1:]):
        if xa <= x <= xb:
            return ra + (rb - ra) * (x - xa) / max(1e-9, xb - xa)
    return prof[-1][0] if x > prof[-1][1] else prof[0][0]


def _split(prof, x):
    rc = _r_at(prof, x)
    a = [p for p in prof if p[1] < x - 1e-6] + [(rc, x)]
    b = [(rc, x)] + [p for p in prof if p[1] > x + 1e-6]
    return a, b


def _ogive_to(R, Lv, rf, x0, n=10):
    """Ogiva tangente do raio R (em x0) ao raio rf exatamente em x0 + Lv."""
    rf = min(max(rf, 1e-4), R * 0.999)

    def s_f(Lo):
        rho = (R * R + Lo * Lo) / (2 * R)
        return math.sqrt(max(0.0, rho * rho - (rf - R + rho) ** 2))
    lo, hi = Lv, Lv * 20 + 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if s_f(mid) < Lv:
            lo = mid
        else:
            hi = mid
    Lo = (lo + hi) / 2
    rho = (R * R + Lo * Lo) / (2 * R)
    return [(math.sqrt(max(0.0, rho * rho - s * s)) + R - rho, x0 + s) for s in (Lv * k / n for k in range(n + 1))]


def _dome(x0, x1, r0, p=2.0, n=8, r_end=0.0):
    """Perfil eliptico de x0 (raio r0) ate x1 (raio r_end)."""
    out = []
    for k in range(n + 1):
        t = k / n
        r = r0 * max(0.0, 1 - t ** p) ** (1 / p)
        out.append((max(r, r_end) if k < n else r_end, x0 + (x1 - x0) * t))
    return out


def lens_tip(name, x0, x1, r, X, tags, y=0.0):
    """Domo do buscador: LENTE escura brilhante (le preta no casco branco, reflexo claro no espaco)."""
    return smooth(name, _dome(x0, x1, r, p=1.8, n=10), X["lens"], tags, y=y)


def led_groove(name, x, w, r, color, s, X, tags, LT, full=False):
    """Faixa de LED: anel escuro rebaixado (raio r, entre pecas de raio maior) com a tira acesa na face de cima
    (full=True: o anel aceso inteiro, visto de cima atravessa a largura toda)."""
    ring(name + "_k", x - w / 2, x + w / 2, r, X["core"], tags)
    if full:
        ring(name + "_l", x - w * 0.32, x + w * 0.32, r * 1.012, _led(color, s), _lt(LT, s))
    else:
        zt = r * COS8
        hw = r * TOPW / 2 * 0.86
        B.box(name + "_l", x, 0, w * 0.62, 2 * hw, zt - 0.004, zt + 0.006, _led(color, s), bevel=0.0,
              tags=_lt(LT, s))


def slot(targets, name, cx, cy, sx, sy, ztop, depth, X, tags):
    """Recesso de paredes verticais (corte nos alvos) com leito preto; devolve a altura do fundo."""
    zf = ztop - depth
    for j, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{j}", cx, cy, sx, sy, zf, ztop + 0.3, X["black"], bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, zf - 0.008, zf + 0.001, X["black"], bevel=0.0, tags=tags)
    return zf


def rslot(targets, name, cx, cy, L, w, rot, ztop, depth, X, tags):
    """slot() girado de rot graus no plano XY."""
    zf = ztop - depth
    for j, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.rbox(f"{name}_c{j}", cx, cy, L, w, zf, ztop + 0.3, X["black"], rot=rot, bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, L, w, zf - 0.008, zf + 0.001, X["black"], rot=rot, bevel=0.0, tags=tags)
    return zf


def top_panel(name, x0, x1, r, mat, tags, th=0.010, inset=0.018):
    """Painel elevado (chanfro duplo) na face de cima de um prisma de 8 lados de raio r; pontas da frente
    chanfradas apontando para o nariz."""
    zt = r * COS8
    hw = r * TOPW / 2 - inset * 0.6
    c = min(hw * 0.6, 0.025)
    poly = [(x0, -hw + c * 0.5), (x0 + c * 0.5, -hw), (x1 - c, -hw), (x1, -hw + c), (x1, hw - c), (x1 - c, hw),
            (x0 + c * 0.5, hw), (x0, hw - c * 0.5)]
    return B.plate(name, poly, zt - 0.003, zt + th, mat, slope=0.005, bevel=0.002, tags=tags)


def side_panels(name, x0, x1, r, mat, tags, th=0.010, inset=0.018):
    """Paineis nas duas facetas de 45 graus (ombros) de um prisma de 8 lados."""
    out = []
    for s in (1, -1):
        p = top_panel(f"{name}{'l' if s > 0 else 'r'}", x0, x1, r, mat, tags, th, inset)
        p.rotation_euler = (math.radians(45 * s), 0.0, 0.0)
        out.append(p)
    return out


def fin(name, poly, z, th, mat, tags, slope=0.007, groove=0.005, ph=0.005, panel_mat=None):
    """Par de aletas planas em lasca (chanfro duplo), poligono no lado +y espelhado em -y."""
    out = []
    for s, nm in ((1, "l"), (-1, "r")):
        p = [(x, s * y) for x, y in poly]
        out.append(B.shard(f"{name}_{nm}", p, z - th / 2, z + th / 2, mat, slope=slope, groove=groove,
                           panel_h=ph, panel_mat=panel_mat, tags=tags))
    return out


def dorsal(name, x0, x1, ztop, h, mat, tags, w=0.022):
    """Aleta dorsal vista de quina: lamina fina ao longo do eixo."""
    poly = [(x0, -w / 2), (x1, -w / 2), (x1, w / 2), (x0, w / 2)]
    return B.loft(name, poly, poly, ztop - 0.03, ztop + h, mat, bevel=0.003, tags=tags)


def _vslits(name, targets, xa, xb, y0, y1, zt, depth, X, tags, LT, col, on, w=0.030, lw=0.010):
    """Par de fendas em V (y0 atras -> y1 na frente, espelhadas): rebaixo escuro com a tira acesa (largura lw) na
    borda de dentro (lado do eixo)."""
    L = math.hypot(xb - xa, y0 - y1)
    for j, s in enumerate((-1, 1)):
        rot = math.degrees(math.atan2(s * (y1 - y0), xb - xa))
        cx, cy = (xa + xb) / 2, s * (y0 + y1) / 2
        zf = rslot(targets, f"{name}{j}", cx, cy, L, w, rot, zt, depth, X, tags)
        a = math.radians(rot)
        off = (w - lw) / 2 - 0.002
        nx, ny = -math.sin(a) * (-s), math.cos(a) * (-s)
        B.rbox(f"{name}{j}_l", cx + nx * off, cy + ny * off, L - 0.02, lw, zf + 0.001, zf + 0.009,
               _led(col, on), rot=rot, bevel=0.0, tags=_lt(LT, on))


def _visor(name, prof, xv, X, tags, LT, col, k, hw=0.030, n_led=3):
    """Visor do nariz sensor: faixa de LENTE escura rebaixada em volta da ogiva em xv com o scanner de LEDs na face
    de cima (quadro k acende o LED k). Devolve (perfil antes, perfil depois)."""
    a, b = _split(prof, xv - hw)
    vis, c = _split(b, xv + hw)
    octo(name, [(r * 0.965, x) for r, x in vis], X["lens"], tags)
    rv = _r_at(prof, xv) * 0.965
    zv = rv * COS8
    for j in range(n_led):
        y = (j - (n_led - 1) / 2) * rv * 0.26
        on = 1.15 if j == k % n_led else 0.0
        B.box(f"{name}_p{j}", xv, y, hw * 1.15, rv * 0.18, zv - 0.012, zv + 0.003, _led(col, on), bevel=0.0,
              tags=_lt(LT, on))
    return a, c


def _nozzle(X, tags, x0, rb, rt, length, y=0.0, pre="noz"):
    """Bocal: sino de aco com o labio claro + garganta escura (o feixe do jogo sai daqui)."""
    octo(pre, [(rb, x0), (rb * 0.97, x0 + length * 0.35), (rt, x0 + length)], X["steel"], tags, y=y)
    ring(pre + "_k", x0 - 0.002, x0 + 0.012, rb * 0.72, X["black"], tags, y=y)


# ============================================================================ Jararaca (HE, ambar)
def _he(M, X, T, LT, k, tier):
    tags = (T,)
    band = _band("he")
    if tier == "s":
        # Muricoca micro: luva lisa partida pela faixa de LED, ogiva clara + domo de lente, 2 aletas
        R = 0.056
        _nozzle(X, tags, -0.48, 0.036, 0.044, 0.035)
        octo("tail", [(R * 0.74, -0.452), (R * 0.97, -0.37)], X["graph"], tags)
        ring("spine", -0.40, 0.25, R * 0.86, X["core"], tags)
        ring("sl0", -0.375, -0.08, R, X["comp"], tags, ch=0.010)
        led_groove("led", -0.042, 0.066, R * 0.92, "he", 1.2 if k == 0 else 0.22, X, tags, LT)
        ring("sl1", -0.006, 0.19, R, X["comp"], tags, ch=0.010)
        ring("band", 0.186, 0.232, R * 1.03, band, tags, ch=0.004)
        og = _ogive_to(R, 0.425 - 0.230, R * 0.46, 0.230)
        octo("og", og, X["comp"], tags)
        ring("seat", 0.415, 0.432, R * 0.50, X["steel"], tags)
        lens_tip("lens", 0.428, 0.478, R * 0.46, X, tags)
        fin("fin", [(-0.26, R * 0.5), (-0.36, 0.163), (-0.445, 0.163), (-0.447, R * 0.5)], 0.0, 0.020,
            X["comp"], tags)
        return
    if tier == "m":
        # Jararaca: anel de LED na cauda, 3 luvas em divisa, ogiva clara com fendas de trilho em V acesas,
        # canards, domo de lente
        R = 0.078
        _nozzle(X, tags, -0.855, 0.048, 0.058, 0.05)
        octo("tail", [(R * 0.72, -0.815), (R * 0.97, -0.665)], X["graph"], tags)
        ring("spine", -0.82, 0.32, R * 0.86, X["core"], tags)
        ring_on = 1.1 if k == 0 else 0.22
        led_groove("ring", -0.638, 0.034, R * 0.92, "he", ring_on, X, tags, LT, full=True)
        a0, xs1, dv, g = -0.615, 0.25, 0.05, 0.03
        span = xs1 - a0
        fl = span * 0.40
        rl = (span - fl - g * 2) / 2
        starts = [a0, a0 + rl + g, a0 + 2 * (rl + g)]
        for i, a in enumerate(starts):
            b = (a + rl) if i < 2 else (xs1 - dv)
            Mo.chevron_sleeve(f"sl{i}", a, b, R, X["comp"], tags, dv=dv, rear=i > 0, verts=8)
        ring("band", 0.255, 0.305, R * 1.03, band, tags, ch=0.004)
        ring("bandk", 0.24, 0.32, R * 0.95, X["core"], tags)
        xo, xl = 0.30, 0.795
        og = _ogive_to(R, xl - xo, R * 0.44, xo, n=12)
        ob = octo("og", og, X["comp"], tags)
        # fendas de trilho em V no ombro da ogiva (borda de dentro acesa no quadro 1)
        xa, xb = xo + 0.08, xo + 0.27
        ra, rb = _r_at(og, xa), _r_at(og, xb)
        _vslits("rs", [ob], xa, xb, min(0.044, ra * TOPW / 2 + 0.006), 0.012, ra * COS8,
                (ra - rb) * COS8 + 0.035, X, tags, LT, "he", 1.1 if k == 1 else 0.0, w=0.026, lw=0.010)
        ring("seat", xl - 0.012, xl + 0.006, R * 0.48, X["steel"], tags)
        lens_tip("lens", xl, 0.855, R * 0.46, X, tags)
        # aletas da cauda (delta cortada) com garras escuras na raiz; canards pequenos no ombro do nariz
        fin("fin", [(-0.47, R * 0.55), (-0.69, 0.29), (-0.795, 0.29), (-0.81, R * 0.55)], 0.0, 0.024,
            X["comp"], tags)
        for s in (1, -1):
            B.box(f"claw{s}", -0.64, s * R * 0.98, 0.22, 0.028, -0.03, 0.032, X["graph"], bevel=0.004, tags=tags)
        fin("can", [(0.47, R * 0.6), (0.40, 0.155), (0.36, 0.155), (0.36, R * 0.6)], 0.0, 0.016, X["comp"], tags)
        return
    # he_l: DOIS ESTAGIOS. Reforco segmentado (aletas grandes, garras), anel de separacao com 3 LEDs que correm;
    # sustentador de blindagem segmentada com paineis de chanfro duplo, estrakes, faixa dupla, nariz sensor
    Rb, R = 0.106, 0.092
    _nozzle(X, tags, -1.23, 0.070, 0.082, 0.07)
    octo("btail", [(Rb * 0.78, -1.17), (Rb * 0.97, -1.07)], X["graph"], tags)
    bspine = ring("bspine", -1.17, -0.40, Rb * 0.86, X["core"], tags)
    xs = [-1.07, -0.82, -0.62]
    ends = [-0.84, -0.64, -0.49]
    for i, (a, b) in enumerate(zip(xs, ends)):
        ring(f"bseg{i}", a, b, Rb, X["comp"], tags, ch=0.012)
        top_panel(f"bpn{i}", a + 0.03, b - 0.025, Rb, X["comp"], tags)
    fin("bfin", [(-0.80, Rb * 0.6), (-1.05, 0.415), (-1.165, 0.415), (-1.17, Rb * 0.6)], 0.0, 0.03, X["comp"],
        tags)
    for s in (1, -1):
        B.box(f"bclaw{s}", -0.99, s * Rb * 0.98, 0.30, 0.034, -0.035, 0.038, X["graph"], bevel=0.005, tags=tags)
    sep = ring("sep", -0.485, -0.405, Rb * 1.02, X["graph"], tags)
    zf = slot([sep, bspine], "seps", -0.445, 0.0, 0.050, 0.12, Rb * 1.02 * COS8, 0.026, X, tags)
    for i in range(3):
        on = 1.2 if i == k else 0.0
        B.box(f"spip{i}", -0.445, (i - 1) * 0.04, 0.036, 0.028, zf + 0.0005, zf + 0.008, _led("he", on), bevel=0.0,
              tags=_lt(LT, on))
    # sustentador: as "escamas" da Jararaca (luvas em divisa encaixadas, como no he_m) agora blindadas, cada uma
    # com paineis de chanfro duplo em cima e nos ombros
    ring("spine", -0.42, 0.74, R * 0.86, X["core"], tags)
    a0, xs1, dv, g, n = -0.395, 0.60, 0.06, 0.035, 3
    rl = (xs1 - dv - a0 - g * (n - 1)) / n
    for i in range(n):
        a = a0 + i * (rl + g)
        b = a + rl
        Mo.chevron_sleeve(f"seg{i}", a, b, R, X["comp"], tags, dv=dv, rear=i > 0, verts=8)
        p0 = a + (dv if i > 0 else 0.0) + 0.03
        top_panel(f"pn{i}", p0, b - 0.025, R, X["comp"], tags)
        side_panels(f"ps{i}", p0, b - 0.025, R, X["comp"], tags)
    fin("strake", [(0.40, R * 0.6), (0.16, 0.118), (-0.22, 0.118), (-0.31, R * 0.6)], -0.01, 0.014, X["comp_d"],
        tags)
    ring("band0", 0.63, 0.665, R * 1.03, band, tags, ch=0.004)
    ring("band1", 0.685, 0.715, R * 1.03, band, tags, ch=0.004)
    ring("bandk", 0.62, 0.73, R * 0.95, X["core"], tags)
    xo, xl = 0.715, 1.165
    og = _ogive_to(R, xl - xo, R * 0.46, xo, n=12)
    o1, o2 = _visor("vis", og, xo + 0.15, X, tags, LT, "he", k, hw=0.026)
    octo("og1", o1, X["comp"], tags)
    octo("og2", o2, X["comp"], tags)
    ring("seat", xl - 0.012, xl + 0.006, R * 0.50, X["steel"], tags)
    lens_tip("lens", xl, 1.228, R * 0.48, X, tags)


# ============================================================================ Piranha (cluster, amarela)
def _petal_ring(prof_r, x, a_from, a_to):
    """Pontos (x, y, z) da superficie do octogono (vertices em 22.5 + 45k graus) de raio prof_r entre os angulos
    a_from e a_to (graus), com os vertices do octogono no meio."""
    angs = [a_from]
    v = 22.5 - 360.0                       # vertices tambem nos angulos negativos (petala centrada em 0 graus)
    while v < a_to - 1e-6:
        if v > a_from + 1e-6:
            angs.append(v)
        v += 45.0
    angs.append(a_to)
    pts = []
    for a in angs:
        k = math.floor((a - 22.5) / 45.0)
        va, vb = math.radians(22.5 + 45 * k), math.radians(22.5 + 45 * (k + 1))
        t = (math.radians(a) - va) / (vb - va)
        ya, za = math.cos(va), math.sin(va)
        yb, zb = math.cos(vb), math.sin(vb)
        pts.append((x, prof_r * (ya + (yb - ya) * t), prof_r * (za + (zb - za) * t)))
    return pts


def petal_mesh(name, prof, a_c, half, X, tags, thick=0.82):
    """UMA petala do nariz da Piranha: casca do octogono entre a_c - half e a_c + half graus (faces planas), com a
    face de fora em composito e a de dentro em grafite (espessura = raio x (1 - thick)). prof = [(raio, x)] da base
    para a ponta."""
    import bmesh
    import bpy
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    outer, inner = [], []
    for r, x in prof:
        o = _petal_ring(r, x, a_c - half, a_c + half)
        outer.append([bm.verts.new(p) for p in o])
        inner.append([bm.verts.new((p[0], p[1] * thick, p[2] * thick)) for p in o])
    n = len(outer[0])
    faces = []
    for ra, rb, ia, ib in zip(outer, outer[1:], inner, inner[1:]):
        for i in range(n - 1):
            faces.append((bm.faces.new((ra[i], ra[i + 1], rb[i + 1], rb[i])), 0))
            faces.append((bm.faces.new((ia[i + 1], ia[i], ib[i], ib[i + 1])), 1))
        # paredes laterais (as frestas)
        faces.append((bm.faces.new((ia[0], ra[0], rb[0], ib[0])), 1))
        faces.append((bm.faces.new((ra[n - 1], ia[n - 1], ib[n - 1], rb[n - 1])), 1))
    # tampas da base e da ponta
    faces.append((bm.faces.new([*reversed(outer[0]), *inner[0]]), 1))
    faces.append((bm.faces.new([*outer[-1], *reversed(inner[-1])]), 1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f, mi in faces:
        f.material_index = mi
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(X["comp"])
    ob.data.materials.append(X["graph"])
    for t in tags:
        ob[t] = True
    return ob


CL = {
    # R, bocal, fim da cauda, baias (de, ate), n baias, nariz, envergadura das aletas, minis por janela
    "m": {"R": 0.150, "x0": -0.855, "xt": -0.62, "bays": (-0.595, 0.215), "nb": 3, "xn": 0.855, "span": 0.352,
          "nmini": 3, "gap": 20.0},
    "l": {"R": 0.200, "x0": -1.23, "xt": -0.92, "bays": (-0.895, 0.385), "nb": 4, "xn": 1.23, "span": 0.48,
          "nmini": 3, "gap": 16.0},
}


def cluster_nose_profile(tier):
    """Perfil da casca de petalas (base -> ponta) e x da base, o mesmo no missil e no atlas de particulas."""
    c = CL[tier]
    R, xn = c["R"], c["xn"]
    sc = R / 0.15
    xo = c["bays"][1] + 0.055 * sc
    xe = xn - 0.045 * sc
    og = _ogive_to(R * 0.985, xe - xo, R * 0.20, xo, n=12)
    return og, xo, xe


def _mini_in_bay(name, x_tip, y, zbed, r, length, X, tags):
    """Mini-missil deitado no fundo da janela, apontando para +X: corpo escuro, faixa amarela, nariz claro."""
    zc = zbed + r * 0.95
    lc = r * 3.0
    bw = max(0.016, r * 0.55)
    octo(name + "_b", [(r, x_tip - length), (r, x_tip - lc - bw)], X["graph"], tags, zc=zc, y=y)
    octo(name + "_band", [(r * 1.02, x_tip - lc - bw), (r * 1.02, x_tip - lc)], _band("cluster"), tags, zc=zc, y=y)
    octo(name + "_n", [(r, x_tip - lc), (r * 0.80, x_tip - lc * 0.55), (r * 0.30, x_tip)], X["nose"], tags, zc=zc,
         y=y)


def _cluster(M, X, T, LT, k, tier):
    tags = (T,)
    c = CL[tier]
    R, x0, xt, (b0, b1), nb, xn = c["R"], c["x0"], c["xt"], c["bays"], c["nb"], c["xn"]
    sc = R / 0.15
    # cauda: bocal, cone de grafite, 2 aletas de lado + dorsal de quina
    _nozzle(X, tags, x0, R * 0.42, R * 0.50, 0.06 * sc)
    octo("tail", [(R * 0.56, x0 + 0.05 * sc), (R * 0.96, xt)], X["graph"], tags)
    spine = ring("spine", xt - 0.02, b1 + 0.06 * sc, R * 0.86, X["core"], tags)
    fin("fin", [(xt + 0.02, R * 0.7), (xt - 0.08 * sc, c["span"]), (x0 + 0.06 * sc, c["span"]),
                (x0 + 0.055 * sc, R * 0.7)], 0.0, 0.026 * sc, X["comp"], tags)
    dorsal("dors", x0 + 0.08 * sc, xt - 0.01, R * 0.80 * COS8, 0.05 * sc, X["comp"], tags, w=0.024 * sc)
    # baias com janelas: os narizes dos minis enfileirados aparecem no fundo escuro
    g = 0.034 * sc
    blen = (b1 - b0 - g * (nb - 1)) / nb
    zt = R * COS8
    ww = R * (0.98 if tier == "m" else 0.82)
    for i in range(nb):
        a = b0 + i * (blen + g)
        b = a + blen
        bay = ring(f"bay{i}", a, b, R, X["comp"], tags, ch=0.014 * sc)
        cx = (a + b) / 2
        wl = blen * 0.66
        zf = slot([bay, spine], f"win{i}", cx, 0.0, wl, ww, zt, 0.045 * sc, X, tags)
        n = c["nmini"]
        pitch = ww / n
        rm = pitch * 0.40
        for j in range(n):
            y = (j - (n - 1) / 2) * pitch
            # os do meio um pouco a frente (fileira em divisa, como um cardume)
            xtip = cx + wl / 2 - 0.012 * sc - (0.0 if j == (n - 1) / 2 else 0.018 * sc)
            _mini_in_bay(f"mini{i}{j}", xtip, y, zf, rm, wl * 0.9, X, tags)
        if tier == "l":
            side_panels(f"ps{i}", a + 0.03, b - 0.03, R, X["comp"], tags)
    # LEDs de armar: tiras acesas nas frestas entre as baias e na base do nariz; correm para a frente
    n_led = nb
    xs_led = [b0 + (i + 1) * (blen + g) - g / 2 for i in range(nb - 1)] + [b1 + 0.022 * sc]
    for i, xl in enumerate(xs_led[:n_led]):
        on = 1.15 if i == k % n_led else 0.0
        if i < nb - 1:
            led_groove(f"led{i}", xl, g * 1.02, R * 0.90, "cluster", on, X, tags, LT)
    if tier == "l":
        # canards na ultima baia
        fin("can", [(b1 - 0.03, R * 0.8), (b1 - 0.13, R + 0.12), (b1 - 0.20, R + 0.12), (b1 - 0.21, R * 0.8)], 0.0,
            0.022, X["comp"], tags)
    # faixa amarela + anel da dobradica (escuro) com o LED de armar do nariz
    xb = b1 + 0.004
    ring("band", xb, xb + 0.032 * sc, R * 1.03, _band("cluster"), tags, ch=0.004)
    og, xo, xe = cluster_nose_profile(tier)
    on = 1.15 if (nb - 1) == k % n_led else 0.0
    led_groove("ledn", (xb + 0.032 * sc + xo) / 2, xo - xb - 0.032 * sc + 0.004, R * 0.90, "cluster", on, X, tags,
               LT)
    # nariz em 4 petalas: casca de composito em 4 pedacos (petalas centradas em 90/0/270/180 graus, frestas a 45)
    # sobre a ogiva interna preta; dobradicas de aco na base de cada fresta visivel; olho escuro na ponta
    gap = c["gap"]
    for j, ac in enumerate((90.0, 0.0, 180.0, 270.0)):
        petal_mesh(f"petal{j}", og, ac, 45.0 - gap / 2, X, tags)
    octo("og_in", [(r * 0.84, x) for r, x in og], X["black"], tags)
    # LEDs de armar DENTRO das 2 frestas vistas de cima (45 e 135 graus), no fundo preto entre as petalas: acendem
    # junto com o LED da base do nariz (o "vai abrir")
    xa, xb = xo + 0.025 * sc, xo + 0.135 * sc
    rr = _r_at(og, xb) * 0.84 * math.cos(math.pi / 8)
    for j, ang in enumerate((-45.0, 45.0)):
        pip = B.box(f"seam{j}", (xa + xb) / 2, 0.0, xb - xa, 0.020 * sc, rr - 0.004, rr + 0.010 * sc, _led("cluster", on),
                    bevel=0.0, tags=_lt(LT, on))
        pip.rotation_euler = (math.radians(ang), 0.0, 0.0)
    rt = og[-1][0]
    lens_tip("eye", xe - 0.004, xn, rt * 1.02, X, tags)
    for s in (1, -1):
        a = math.radians(45)
        rr = R * COS8 * 0.99
        B.box(f"hinge{s}", xo + 0.028 * sc, s * rr * math.cos(a), 0.046 * sc, 0.026 * sc, rr * math.sin(a) - 0.014,
              rr * math.sin(a) + 0.014 * sc, X["steel"], bevel=0.003, tags=tags)


def _mini(M, X, T):
    """Mini-missil teleguiado (32 x 12 px): 4 elementos legiveis a 1x: colar laranja do propulsor (tinta), corpo
    claro, faixa amarela, nariz escuro; 2 aletas pequenas (>= 2 px)."""
    tags = (T,)
    R = 0.036
    octo("collar", [(R * 0.80, -0.226), (R * 0.95, -0.210), (R * 0.95, -0.188)], X["orange"], tags)
    ring("collar_k", -0.229, -0.221, R * 0.62, X["black"], tags)
    ring("body", -0.19, 0.105, R, X["comp"], tags, ch=0.006)
    ring("band", 0.100, 0.132, R * 1.04, _band("cluster"), tags)
    og = _ogive_to(R, 0.20 - 0.130, R * 0.50, 0.130, n=8)
    octo("og", og, X["graph"], tags)
    lens_tip("eye", 0.198, 0.228, R * 0.50, X, tags)
    fin("fin", [(-0.10, R * 0.55), (-0.160, 0.072), (-0.205, 0.072), (-0.205, R * 0.55)], 0.0, 0.014, X["comp"],
        tags, slope=0.004, groove=0.003, ph=0.003)


# ============================================================================ Poraque (PEM, ciano)
def _coil(X, T, name, xc, w, R, turns=3):
    """Bobina de FIO de cobre: espiras redondas (16 lados lisos, o cobre do Poraque) sobre um carretel escuro."""
    tags = (T,)
    ring(name + "_k", xc - w / 2, xc + w / 2, R * 1.0, X["core"], tags)
    pw = w / turns
    for i in range(turns):
        a = xc - w / 2 + i * pw + pw * 0.08
        b = a + pw * 0.84
        h = R * 0.08
        prof = [(R * 1.0, a)] + [(R * 1.0 + h * math.sin(math.pi * t / 6), a + (b - a) * t / 6) for t in range(1, 6)]
        prof += [(R * 1.0, b)]
        smooth(f"{name}_{i}", prof, X["copper"], tags, verts=16)


def _lit_band(X, name, x, w, R, color, s, tags, LT, lip=None, lip_r=1.06):
    """Faixa acesa num rebaixo: anel aceso entre dois labios escuros mais altos (lip_r * R)."""
    if lip:
        ring(name + "_a", x - w / 2 - lip, x - w / 2, R * lip_r, X["graph"], tags, ch=0.004)
        ring(name + "_b", x + w / 2, x + w / 2 + lip, R * lip_r, X["graph"], tags, ch=0.004)
    ring(name + "_l", x - w / 2, x + w / 2, R * 1.005, _led(color, s), _lt(LT, s))


def _eel_fins(name, x0, x1, r0, h0, h1, n, X, tags, th=0.016):
    """Barbatana-fita da enguia: n escamas varridas (cada uma uma lasca de chanfro duplo), mais altas na frente,
    que encostam no corpo (alfa conectado)."""
    L = (x1 - x0) / n
    for k in range(n):
        t = (k + 0.5) / n
        h = h0 + (h1 - h0) * t
        xa = x1 - k * L
        # lamina varrida para tras: bordo de ataque longo, ponta curta, bordo de fuga varrido (dente de serra)
        poly = [(xa, r0 * 0.6), (xa - L * 0.78, r0 + h), (xa - L * 1.08, r0 + h), (xa - L * 0.88, r0 * 0.6)]
        fin(f"{name}{k}", poly, 0.004 * (n - k), th, X["comp"], tags)


def _emp(M, X, T, LT, k, tier):
    tags = (T,)
    late = tier == "l"
    if not late:
        R, x0, xn = 0.088, -0.855, 0.855
        x_sl0, x_sl1 = -0.70, -0.08
        coils = [0.03, 0.205, 0.38]
        cw, turns = 0.12, 3
        x_nose0 = 0.48
    else:
        R, x0, xn = 0.104, -1.23, 1.105
        x_sl0, x_sl1 = -1.03, -0.30
        coils = [-0.20, -0.01, 0.18, 0.37, 0.56]
        cw, turns = 0.13, 3
        x_nose0 = 0.665
    sc = R / 0.088
    _nozzle(X, tags, x0, R * 0.52, R * 0.62, 0.055 * sc)
    octo("tail", [(R * 0.66, x0 + 0.045 * sc), (R * 0.97, x_sl0)], X["graph"], tags)
    spine = ring("spine", x_sl0 - 0.02, x_nose0 + 0.02, R * 0.86, X["core"], tags)
    # cauda: blindagem de composito (m: luva em divisa com 2 LEDs ciano; l: 3 segmentos com paineis e o anel
    # ciano da base) e as barbatanas-fita da enguia
    lit = []          # (nome, funcao que desenha com a forca s): a carga corre na ordem da lista
    if not late:
        sl = Mo.chevron_sleeve("sl", x_sl0, x_sl1 - 0.05 * sc, R, X["comp"], tags, dv=0.05 * sc, rear=False)
        cxs = (x_sl0 + x_sl1) / 2 - 0.04
        zf = slot([sl, spine], "sled", cxs, 0.0, 0.11, 0.032, R * COS8, 0.042, X, tags)

        def rear(s, zf=zf, cxs=cxs):
            for i in range(2):
                B.box(f"sled_p{i}", cxs + (i - 0.5) * 0.05, 0.0, 0.032, 0.022, zf + 0.0005, zf + 0.008,
                      _led("emp", s), bevel=0.0, tags=_lt(LT, s))
        lit.append(rear)
        _eel_fins("rib", x0 + 0.06, -0.10, R, 0.05, 0.13, 4, X, tags)
    else:
        def rear(s):
            led_groove("bring", x_sl0 + 0.03, 0.036, R * 0.92, "emp", s, X, tags, LT, full=True)
        lit.append(rear)
        segs = [(x_sl0 + 0.06, -0.78), (-0.75, -0.53), (-0.50, x_sl1)]
        for i, (a, b) in enumerate(segs):
            ring(f"seg{i}", a, b, R, X["comp"], tags, ch=0.012)
            top_panel(f"pn{i}", a + 0.03, b - 0.03, R, X["comp"], tags)
            side_panels(f"ps{i}", a + 0.03, b - 0.03, R, X["comp"], tags)
        _eel_fins("rib", x0 + 0.08, -0.38, R, 0.07, 0.19, 5, X, tags, th=0.018)
    # capsula escura sob as bobinas
    ring("cap", x_sl1 - 0.01, coils[-1] + cw / 2 + 0.04, R * 0.97, X["pem"], tags)
    for i, xc in enumerate(coils):
        _coil(X, T, f"coil{i}", xc, cw, R, turns)
    # frestas ciano entre as bobinas (com labios escuros): a carga corre da cauda para o nariz
    for i in range(len(coils) - 1):
        xg = (coils[i] + coils[i + 1]) / 2
        gw = coils[i + 1] - coils[i] - cw

        def gap(s, i=i, xg=xg, gw=gw):
            _lit_band(X, f"gap{i}", xg, gw * 0.56, R, "emp", s, tags, LT, lip=gw * 0.20)
        lit.append(gap)
    # emissor do nariz: colar de aco, cone escuro com 2 aneis de aco, olho ciano na lente da ponta
    xc1 = coils[-1] + cw / 2 + 0.01
    ring("ncol", xc1, xc1 + 0.035, R * 1.04, X["steel"], tags, ch=0.004)
    xo = xc1 + 0.03
    xl = xn - 0.07 * sc
    og = _ogive_to(R, xl - xo, R * 0.48, xo, n=10)
    octo("og", og, X["pem"], tags)
    for j, t in enumerate((0.35, 0.70)):
        xx = xo + (xl - xo) * t
        ring(f"nring{j}", xx, xx + 0.026, _r_at(og, xx + 0.013) * 1.07, X["steel"], tags, ch=0.004)

    def eye(s):
        _lit_band(X, "eye", xl - 0.018, 0.022, _r_at(og, xl - 0.018), "emp", s, tags, LT)
    lit.append(eye)
    lens_tip("lens", xl - 0.004, xn, R * 0.48, X, tags)
    if late:
        # garfo emissor: 2 pontas de aco paralelas ao nariz com as pontas ciano (>= 2 px)
        yp = 0.104
        x_pr0 = xo + 0.03
        for s in (1, -1):
            B.box(f"prong{s}", (x_pr0 + 1.20) / 2, s * yp, 1.20 - x_pr0, 0.034, -0.014, 0.022, X["steel"],
                  bevel=0.004, tags=tags)
            B.box(f"pbrace{s}", x_pr0 + 0.03, s * (yp + R) / 2 * 0.98, 0.05, yp - R * 0.6, -0.012, 0.02,
                  X["graph"], bevel=0.003, tags=tags)
        ptip = 1.2 if k == 3 else 0.35

        def tips(s):
            for sy in (1, -1):
                B.box(f"ptip{sy}", 1.213, sy * yp, 0.030, 0.034, -0.01, 0.024, _led("emp", s), bevel=0.0,
                      tags=_lt(LT, s))
        tips(ptip)
    # a onda: o elemento k forte, o anterior medio, o resto apagado (no l, 2 frestas por quadro)
    n = len(lit)
    pos = [round(i * (n - 1) / 3) for i in range(4)]
    lead = pos[k % 4]
    for i, fn in enumerate(lit):
        s = 1.05 if i == lead else (0.32 if i == lead - 1 else 0.0)
        fn(s)


# ============================================================================ Iara (nuclear, verde)
def _iara(M, X, T, LT, k, xt, xn, boosters):
    tags = (T,)
    D, P, S, BLK, K = X["dark"], X["plate"], X["steel"], X["black"], X["core"]
    chev = Mo.chevron_mat("m2_iara_chev", scale=7.0)
    paint = _band("nuke")
    # respiracao 0.55/0.8/1.0/0.8 do brilho PERCEBIDO (forcas lineares ~0.27/0.58/0.94/0.58, verde "nuke" com
    # pouco vermelho: nunca amarela)
    br = (0.24, 0.50, 0.78, 0.50)[k % 4]
    R, RW = 0.20, 0.28
    ap, apw = R * COS8, RW * COS8
    # ---- ogiva gorda blindada
    xw0, xw1 = xn - 1.40, xn - 0.36
    core = ring("wh", xw0, xw1, RW, D, tags)
    octo("whcol", [(R, xn - 1.50), (RW, xw0 + 0.002)], D, tags)
    # 2 aneis de faixa de perigo verde/preto (divisas para o nariz) emoldurando a ogiva, com aros de aco
    for j, (a, b) in enumerate(((xw0 + 0.005, xw0 + 0.105), (xw1 - 0.095, xw1 - 0.005))):
        ring(f"haz{j}", a, b, RW * 1.012, chev, tags)
        ring(f"haza{j}", a - 0.012, a + 0.004, RW * 1.03, S, tags, ch=0.003)
        ring(f"hazb{j}", b - 0.004, b + 0.012, RW * 1.03, S, tags, ch=0.003)
    # faixa verde larga que respira logo depois do anel de tras (tinta + tira acesa no meio)
    xg0, xg1 = xw0 + 0.125, xw0 + 0.175
    ring("gband_p", xg0, xg1, RW * 1.006, paint, tags)
    ring("gband_k", xg0 + 0.010, xg1 - 0.010, RW * 1.010, BLK, tags)
    ring("gband", xg0 + 0.013, xg1 - 0.013, RW * 1.016, _led("nuke", br), LT)
    # placa de cima: miolo escuro com aro claro e o TREVO grande (cunhas pretas sobre disco verde)
    px0, px1 = xg1 + 0.03, xw1 - 0.13
    hw = 0.142
    c1, c2 = 0.035, 0.075
    poly = [(px0, -hw + c1), (px0 + c1, -hw), (px1 - c2, -hw), (px1, -hw + c2), (px1, hw - c2), (px1 - c2, hw),
            (px0 + c1, hw), (px0, hw - c1)]
    ta, tp = B.shard("top", poly, apw - 0.004, apw + 0.026, P, slope=0.020, groove=0.011, panel_h=0.014,
                     panel_mat=D, tags=tags)
    cx = (px0 + px1) / 2
    ztp = apw + 0.026 + 0.014
    Mo.trefoil_inlay("tref", [ta, tp], cx, 0.0, ztp, 0.094, 0.026, M, tags, wedge_mat=BLK, disc_mat=paint,
                     disc_r=0.120, hub_mat=BLK, a0=0.0, depth=0.03)
    B.bolts("tbolt", [(px0 + 0.02, 0.10), (px0 + 0.02, -0.10), (px1 - 0.03, 0.07), (px1 - 0.03, -0.07)],
            ztp + 0.002, 0.012, S, tags=tags)
    # placas dos ombros com as JANELAS DE CONTENCAO (3 por lado): recesso cortado na placa ainda deitada em cima,
    # leito preto, tira verde acesa e 1 barra de aco; depois a placa e tudo dela giram 45 graus para o ombro
    nwin = 3
    wl = (px1 - px0 - 0.06) / nwin - 0.03
    wglow = _led("nuke", 0.80 * br + 0.12)
    for s in (1, -1):
        sh = top_panel(f"sh{s}", px0 - 0.01, px1 + 0.01, RW, P, tags, th=0.022, inset=0.012)
        zt = apw + 0.022
        made = [sh]
        for j in range(nwin):
            wx = px0 + 0.045 + wl / 2 + j * (wl + 0.03)
            nm = f"win{j}{s}"
            zf = slot([sh], nm, wx, 0.0, wl, 0.048, zt, 0.030, X, tags)
            made.append(B.box(nm + "_l", wx, 0.0, wl - 0.016, 0.026, zf + 0.0005, zf + 0.008, wglow, bevel=0.0,
                              tags=LT))
            made.append(B.box(nm + "_bar", wx, 0.0, 0.014, 0.052, zt - 0.012, zt + 0.002, S, bevel=0.002,
                              tags=tags))
            import bpy
            made.append(bpy.data.objects[nm + "_bed"])
        for ob in made:
            ob.rotation_euler = (math.radians(45 * s), 0.0, 0.0)
    # ---- nariz blindado: colar de grafite + domo de LENTE com o anel verde do sensor
    xc0 = xw1 + 0.008
    octo("cap", [(RW * 0.985, xc0), (RW * 0.95, xc0 + 0.08), (RW * 0.80, xc0 + 0.17), (RW * 0.60, xn - 0.10)],
         X["graph"], tags)
    ring("capr", xc0 + 0.03, xc0 + 0.05, RW * 1.0, S, tags, ch=0.003)
    rs = RW * 0.60
    ring("sring_k", xn - 0.105, xn - 0.075, rs * 0.97, BLK, tags)
    ring("sring", xn - 0.10, xn - 0.08, rs * 0.99, _led("nuke", br), LT)
    lens_tip("lens", xn - 0.082, xn, rs * 0.92, X, tags)
    # ---- corpo do meio: escuro, segmentos com placas dos ombros e a janela do nucleo (grade de aco)
    xm0, xm1 = xn - 2.30, xn - 1.50
    mid = ring("mid", xm0, xm1 + 0.01, R, D, tags)
    for i, (a, b) in enumerate(((xm0 + 0.03, xm0 + 0.37), (xm0 + 0.43, xm1 - 0.03))):
        side_panels(f"msh{i}", a, b, R, P, tags, th=0.012)
    wc = (xm0 + xm1) / 2
    zf = slot([mid], "core_w", wc, 0.0, 0.40, 0.078, ap, 0.036, X, tags)
    B.box("core_l", wc, 0.0, 0.37, 0.024, zf + 0.0005, zf + 0.007, _led("nuke", br), bevel=0.0, tags=LT)
    for j in range(4):
        xx = wc - 0.15 + j * 0.10
        B.box(f"core_bar{j}", xx, 0.0, 0.016, 0.086, ap - 0.02, ap - 0.004, S, bevel=0.003, tags=tags)
    for s in (1, -1):
        B.box(f"core_rail{s}", wc, s * 0.045, 0.42, 0.012, ap - 0.012, ap + 0.004, S, bevel=0.002, tags=tags)
    # ---- secao do motor: segmentos escuros com paineis, costuras; cauda com aletas e bocal triplo
    xe0 = xt + 0.47
    ring("eng", xe0, xm0 + 0.01, R, D, tags)
    nseg = max(2, int(round((xm0 - xe0) / 0.30)))
    sl = (xm0 - xe0 - 0.03 * (nseg - 1)) / nseg
    for i in range(nseg):
        a = xe0 + i * (sl + 0.03)
        b = a + sl
        if i:
            ring(f"eseam{i}", a - 0.03, a, R * 1.012, BLK, tags)
        top_panel(f"etp{i}", a + 0.03, b - 0.03, R, P, tags, th=0.012)
        side_panels(f"esh{i}", a + 0.03, b - 0.03, R, P, tags, th=0.012)
    octo("tc", [(0.125, xt + 0.13), (R, xe0 + 0.01)], D, tags)
    finp = [(xt + 0.49, 0.12), (xt + 0.29, 0.64), (xt + 0.165, 0.64), (xt + 0.16, 0.12)]
    fin("fin", finp, 0.0, 0.028, D, tags, slope=0.014, groove=0.010, ph=0.010, panel_mat=P)
    from_ = [(xt + 0.475, 0.15), (xt + 0.298, 0.615)]
    for sy in (1, -1):
        pts = [(x, sy * y) for x, y in from_]
        dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * 0.0095, dx / L * 0.0095
        strip = [(pts[0][0] + nx, pts[0][1] + ny), (pts[1][0] + nx, pts[1][1] + ny), (pts[1][0] - nx, pts[1][1] - ny),
                 (pts[0][0] - nx, pts[0][1] - ny)]
        B.plate(f"fle{sy}", strip, 0.008, 0.026, X["comp"], slope=0.006, bevel=0.002, tags=tags)
    fin("bar", [(xt + 0.15, 0.245), (xt + 0.39, 0.245), (xt + 0.415, 0.27), (xt + 0.39, 0.30), (xt + 0.15, 0.30)],
        0.0, 0.09, P, tags, slope=0.012, groove=0.008, ph=0.01)
    B.box("dors", xt + 0.33, 0.0, 0.30, 0.024, 0.10, R + 0.06, P, bevel=0.004, tags=tags)
    for j, yy in enumerate((-0.15, 0.0, 0.15)):
        octo(f"nz{j}", [(0.055, xt), (0.053, xt + 0.025), (0.047, xt + 0.055)], S, tags, y=yy)
        ring(f"nzk{j}", xt - 0.002, xt + 0.012, 0.038, BLK, tags, y=yy)
        ring(f"nzr{j}", xt + 0.055, xt + 0.085, 0.049, _led("nuke", br), LT, y=yy)
        ring(f"nzt{j}", xt + 0.085, xt + 0.20, 0.036, X["graph"], tags, y=yy)
    if boosters:
        # estagio 1: 2 propulsores laterais segmentados (composito medio escuro), nariz de grafite, bocal de aco
        x0b, x1b = xt + 0.52, xn - 2.50
        for sy in (1, -1):
            yy = sy * 0.335
            ring(f"bo{sy}", x0b, x1b, 0.085, D, tags, y=yy)
            nb = 3
            bl = (x1b - x0b - 0.03 * (nb - 1)) / nb
            for i in range(nb):
                a = x0b + i * (bl + 0.03)
                ring(f"bos{sy}{i}", a, a + bl, 0.088, P, tags, ch=0.008, y=yy)
            octo(f"bon{sy}", _ogive_to(0.085, 0.16, 0.02, x1b, n=8) + [(0.0, x1b + 0.165)], X["graph"], tags, y=yy)
            ring(f"bocol{sy}", x1b - 0.02, x1b + 0.005, 0.09, S, tags, ch=0.003, y=yy)
            octo(f"boz{sy}", [(0.05, x0b - 0.06), (0.062, x0b + 0.01)], S, tags, y=yy)
            for i, xx in enumerate((x0b + 0.18, x1b - 0.22)):
                B.box(f"bobr{sy}{i}", xx, sy * 0.25, 0.09, 0.14, -0.035, 0.05, X["graph"], bevel=0.006, tags=tags)
    return core


# ============================================================================ entrada
def model(M, key, T="body", phase=0.0):
    LT = (T, "lights")
    n = max(1, int(PART["items"][key].get("frames", 1)))
    k = int(round(phase * n)) % n
    X = _mats(M)
    if key in ("he_s", "he_m", "he_l"):
        _he(M, X, T, LT, k, key[-1])
    elif key in ("cluster_m", "cluster_l"):
        _cluster(M, X, T, LT, k, key[-1])
    elif key == "cluster_mini":
        _mini(M, X, T)
    elif key in ("emp_m", "emp_l"):
        _emp(M, X, T, LT, k, key[-1])
    elif key == "nuclear_l":
        _iara(M, X, T, LT, k, -1.855, 1.855, True)
    elif key == "nuclear_wh_l":
        _iara(M, X, T, LT, k, -1.53, 1.53, False)
    else:
        raise KeyError(f"bs_missiles2: item desconhecido {key}")


# ============================================================================ atlas das petalas
TILTS = (0.0, 30.0, 55.0, 75.0)          # colunas: inclinacao (giro em torno de Y: a petala "cai" para a camera)
ROLLS = (0.0, 70.0, 180.0, 250.0)        # fileiras: cada petala com o seu giro em torno do proprio eixo


def petal_atlas(M, tier, T="body"):
    """As 4 petalas do nariz da Piranha (fileiras) em 4 inclinacoes (colunas), cada uma centrada na sua celula de
    1 x 1 quadro de uma grade 4 x 4 centrada na origem (celula (fil, col) em x = col - 1.5, y = 1.5 - fil). Mesma
    geometria das petalas do missil (cluster_nose_profile + petal_mesh)."""
    import bpy
    from mathutils import Euler, Matrix, Vector
    X = _mats(M)
    tags = (T,)
    og, xo, xe = cluster_nose_profile(tier)
    gap = CL[tier]["gap"]
    for r in range(4):
        for c in range(4):
            ob = petal_mesh(f"pt{r}{c}", og, 90.0, 45.0 - gap / 2, X, tags)
            # dobradica de aco na base da petala (vai junto com a petala)
            me = ob.data
            vs = [v.co.copy() for v in me.vertices]
            cen = sum(vs, Vector()) / len(vs)
            rot = Euler((math.radians(ROLLS[r]), math.radians(TILTS[c]), math.radians(8.0 * (r - 1.5))),
                        "XYZ").to_matrix().to_4x4()
            tr = Matrix.Translation(Vector((c - 1.5, 1.5 - r, 0.25)))
            ob.matrix_world = tr @ rot @ Matrix.Translation(-cen)
            hz = B.box(f"ph{r}{c}", xo + 0.03, 0.0, 0.05, 0.05, _r_at(og, xo) * 0.82, _r_at(og, xo) * 1.0,
                       X["steel"], bevel=0.003, tags=tags)
            hz.matrix_world = tr @ rot @ Matrix.Translation(-cen) @ hz.matrix_world
    bpy.context.view_layer.update()


def render_atlases(out, quick=False):
    """Renderiza bs_petals_<m|l>.png + _normals.png (256 x 256) em out e registra em out/meta.json ("atlases")."""
    import json
    B.reset("axial")
    for key, at in PART["atlases"].items():
        B.reset("axial")
        M = Mo.mats(PART.get("accent", "amber"))
        B.camera(4.0, 4.0, (0, 0), px=at["sprite_px"])
        import bpy
        bpy.context.scene.cycles.samples = 12 if quick else 48
        petal_atlas(M, at["tier"])
        B.show_only(["body"])
        base = os.path.join(out, at["file"][:-4])
        B.render_set(base, (at["texture_px"], at["texture_px"]), glow_halo=False, normals=True, off=False,
                     glow=False)
        print(f"atlas {key}: {at['file']} + {at['normals']}")
    mp = os.path.join(out, "meta.json")
    meta = json.load(open(mp)) if os.path.exists(mp) else {"version": 1, "kind": "missiles", "id": PART["id"],
                                                           "px_per_tile": PART["px_per_tile"], "items": {},
                                                           "files": []}
    meta["atlases"] = {k: {"file": a["file"], "normals": a["normals"], "texture_px": a["texture_px"],
                           "sprite_px": a["sprite_px"], "per_row": a["per_row"], "count": a["count"],
                           "rows": "petala (giro proprio %s graus)" % "/".join(str(int(v)) for v in ROLLS),
                           "cols": "inclinacao %s graus" % "/".join(str(int(v)) for v in TILTS)}
                       for k, a in PART["atlases"].items()}
    files = set(meta.get("files", []))
    for a in PART["atlases"].values():
        files |= {a["file"], a["normals"]}
    meta["files"] = sorted(files)
    json.dump(meta, open(mp, "w"), indent=1)


if __name__ == "__main__":
    args = sys.argv[1:]
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    out_dir = args[args.index("--out") + 1] if "--out" in args else os.path.join(root, "art3d", "bs_missiles2")
    if "--atlases" not in args:
        sys.exit("uso: bs_missiles2.py --atlases [--quick] [--out DIR]")
    os.makedirs(out_dir, exist_ok=True)
    render_atlases(out_dir, quick="--quick" in args)
