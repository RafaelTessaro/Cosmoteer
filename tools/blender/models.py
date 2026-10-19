"""Kit compartilhado dos modelos 3D do Bullet Strike: paleta, materiais e pecas comuns (casco, piso).

Linguagem visual aprovada (canhao naval 76 mm, ver tools/blender/STYLE.md): nucleo mecanico escuro +
placas de blindagem claras e angulares por cima, com vaos onde o nucleo aparece; "garras" que envolvem
a raiz do cano; espinha central com sensor; baia de exaustao traseira com luzes; canos longos com canal
escuro, colares e freio de boca. Brilhos pequenos e poucos.

Coordenadas: origem no pivo da torre, +X = direita, +Y = frente (direcao do cano), +Z = para cima,
unidades = tiles. Cada arma fica em tools/blender/parts/<id>.py.

Projeteis (misseis em voo e granadas, kind "missiles"/"shells", STYLE.md secoes 8.4, 10 e 11): nariz em +X,
centrados na origem, eixo = X. Funcoes no fim deste arquivo (lathe, ogive, band_mat, shell_profile,
trefoil_inlay, chevron_sleeve, chevron_mat).
"""

import math

import bmesh
import bpy

import bs3d as B

# paleta (valores lineares do Blender)
ARMOR = (0.52, 0.535, 0.55)        # cinza naval claro
ARMOR_MID = (0.20, 0.205, 0.215)
CORE = (0.016, 0.017, 0.02)
CORE_MID = (0.045, 0.046, 0.05)
STEEL = (0.30, 0.31, 0.33)
AMBER = (1.0, 0.42, 0.04)
CYAN = (0.15, 0.85, 1.0)           # plasma
GREEN = (0.40, 1.0, 0.18)          # nuclear
BLUE = (0.25, 0.50, 1.0)           # EMP / radar
RED = (1.0, 0.10, 0.06)            # alerta / radar
ACCENTS = {"amber": AMBER, "cyan": CYAN, "green": GREEN, "blue": BLUE, "red": RED}


def mats(accent=AMBER):
    """Materiais padrao. accent = cor das luzes (tupla RGB ou nome em ACCENTS)."""
    if isinstance(accent, str):
        accent = ACCENTS[accent]
    return {
        "armor": B.mat_paint("armor", ARMOR, rough=0.32, metal=0.25, wear=0.25, grime=0.06, scale=4),
        "armor_mid": B.mat_paint("armor_mid", ARMOR_MID, rough=0.38, metal=0.35, wear=0.3, grime=0.1),
        "core": B.mat_metal("core", CORE, rough=0.45, metal=0.7),
        "core_mid": B.mat_metal("core_mid", CORE_MID, rough=0.35, metal=0.85),
        "steel": B.mat_metal("steel", STEEL, rough=0.28, metal=0.95),
        "black": B.mat_metal("black", (0.004, 0.004, 0.005), rough=0.6, metal=0.2),
        "glow": B.mat_glow("glow", accent, 9.0),
        "glow_dim": B.mat_glow("glow_dim", accent, 3.0),
        "lens": B.mat_glow("lens", (1.0, 0.18, 0.05), 6.0),
        "ember": B.mat_glow("ember", (1.0, 0.16, 0.02), 0.35),
        "red": B.mat_glow("red_led", RED, 6.0),
        "screen": B.mat_glow("screen", (0.25, 0.65, 1.0), 6.0),
    }


def mirror(poly):
    return [(-x, y) for x, y in reversed(poly)]


# ============================================================================ 76 mm naval
def slot_with_pips(name, x, y0, y1, w, ztop, n, M, tags, target=None, depth=0.05, vertical=True, pip_mat=None):
    """Fenda escura (recortada no alvo, se houver) com uma fileira de n pips ambar no fundo."""
    cx, cy = (x, (y0 + y1) / 2) if vertical else ((y0 + y1) / 2, x)
    sx, sy = (w, abs(y1 - y0)) if vertical else (abs(y1 - y0), w)
    for t in (target if isinstance(target, (list, tuple)) else [target]):
        if t is not None:
            c = B.box(name + "_cut", cx, cy, sx, sy, ztop - depth, ztop + 0.2, M["black"], bevel=0.0)
            B.cut(t, [c])
    B.box(name + "_bed", cx, cy, sx, sy, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], bevel=0.0, tags=tags)
    L = abs(y1 - y0)
    for i in range(n):
        t = (i + 0.5) / n
        px, py = (x, min(y0, y1) + t * L) if vertical else (min(y0, y1) + t * L, x)
        B.box(f"{name}_pip{i}", px, py, (w * 0.55) if vertical else L / n * 0.55, (L / n * 0.55) if vertical else w * 0.55,
              ztop - depth, ztop - depth + 0.012, pip_mat or M["glow"], bevel=0.0, tags=tags)


def hull_roof(M, w, h, pivot, ring_r, T="roof"):
    """Teto da peca (verde = pintura da nave) em coordenadas centradas na peca."""
    tags = (T,)
    green = B.mat_roof_green()
    px, py = pivot[0] - w / 2, h / 2 - pivot[1]
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, M["core"], bevel=0.0, tags=tags)
    # placas do convés: uma por tile, cantos chanfrados e painel interno (bisel duplo)
    for tx in range(w):
        for ty in range(h):
            cx, cy = tx + 0.5 - w / 2, h / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            # linha de painel diagonal em placas alternadas
            if (tx + ty) % 2 == 0 and pnl is not None:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, M["core"], rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura): colar escuro com parafusos
    B.torus("ringbear", px, py, 0.08, ring_r + 0.02, 0.055, M["core_mid"], tags=tags)
    B.cyl("ringhole", px, py, 0.05, ring_r - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    # parafusos do anel: so os que ficam dentro da peca (pecas estreitas)
    pts = [(x, y) for x, y in B.ring_points(px, py, ring_r + 0.11, 32)
           if abs(x) < w / 2 - 0.06 and abs(y) < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, M["steel"], tags=tags)
    if h < 2:
        return  # peca de 1 fileira: nao sobra fileira de tras livre
    # fileira de tras: escotilha no meio (pecas com 3+ de largura) e respiros com luz nos tiles das pontas
    hy = -h / 2 + 0.5
    if w >= 3:
        # largura impar: uma escotilha no tile do meio; par: uma em cada tile central (nao cai na emenda)
        for k, hx in enumerate([0.0] if w % 2 else [-0.5, 0.5]):
            hatch = B.rpoly(hx, hy, 0.62, 0.62, 0, chamfer=0.12)
            B.plate(f"hatch{k}", hatch, 0.06, 0.10, M["armor_mid"], slope=0.02, tags=tags)
            B.box(f"hatch_h{k}", hx, hy - 0.16, 0.26, 0.05, 0.10, 0.13, M["steel"], bevel=0.01, tags=tags)
    vents = [0.0] if w == 1 else [sx * (w / 2 - 0.5) for sx in (-1, 1)]
    for k, cx in enumerate(vents):
        if math.hypot(cx - px, hy - py) < ring_r + 0.25:
            continue  # o respiro cairia dentro do anel da torre (pecas pequenas)
        v = B.box(f"hvent{k}", cx, hy, 0.56, 0.34, 0.05, 0.11, M["core_mid"], bevel=0.01, slope=0.015, tags=tags)
        B.cut(v, [B.box(f"hvc{k}{i}", cx, hy - 0.11 + i * 0.075, 0.46, 0.03, 0.09, 0.2, M["core"], bevel=0.0)
                  for i in range(4)])
        B.box(f"hled{k}", cx, hy + 0.23, 0.14, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)


def hull_floor(M, w, h, pivot, ring_r, crew, T="floor"):
    tags = (T,)
    px, py = pivot[0] - w / 2, h / 2 - pivot[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, M["core"], bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            x0, y1 = tx - w / 2 + 0.04, h / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, M["core_mid"], bevel=0.01, tags=tags)
    # anel giratorio com setas
    B.torus("fl_ring", px, py, 0.05, ring_r * 0.85, 0.05, M["armor_mid"], tags=tags)
    B.cyl("fl_hub", px, py, 0.05, ring_r * 0.32, 0.08, M["armor"], axis="Z", verts=48, tags=tags)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * ring_r * 0.6, py + math.sin(a) * ring_r * 0.6
        B.box(f"fl_chev{k}", cx, cy, 0.16, 0.16, 0.05, 0.08, M["armor"], bevel=0.01, tags=tags)
    B.box("fl_led_t", px, py + ring_r * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    B.box("fl_led_b", px, py - ring_r * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # estantes de carregadores na fileira de tras + estacoes da tripulacao
    for tx in range(w):
        x = tx - w / 2 + 0.5
        B.box(f"rack{tx}", x, -h / 2 + 0.13, 0.78, 0.18, 0.0, 0.16, M["armor_mid"], bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.16, 0.12, 0.16, 0.24, M["core_mid"],
                  bevel=0.01, tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, M["armor"], bevel=0.04, tags=tags)
        # console na frente do assento; se cair sobre o anel do piso, vai para o lado de fora do assento
        kx, ky, sxz, syz = x, y + 0.30, 0.42, 0.12
        if math.hypot(kx - px, ky - py) < ring_r * 0.85 + 0.12:
            side = 1 if x >= px else -1
            kx, ky, sxz, syz = x + side * 0.30, y + 0.04, 0.12, 0.36
        B.box(f"console{i}", kx, ky, sxz, syz, 0.0, 0.22, M["core_mid"], bevel=0.02, tags=tags)
        B.box(f"screen{i}", kx, ky, max(0.06, sxz - 0.10), max(0.06, syz - 0.10) if syz > 0.2 else 0.06, 0.22, 0.24,
              M["screen"], bevel=0.0, tags=tags)


# ============================================================================ projeteis (misseis e granadas)
# Copias de tools/blender/parts/bs_msl_quad.py com os MESMOS nomes e valores: o cache de materiais do bs3d e
# por nome ("band_<tipo>"), entao o missil em voo e o nariz carregado no lancador saem com a mesma tinta.
BAND = {"he": (0.80, 0.327, 0.0), "cluster": (0.80, 0.62, 0.086), "limpet": (0.80, 0.035, 0.024),
        "napalm": (0.80, 0.11, 0.0093), "emp": (0.062, 0.437, 0.80), "torpedo": (0.62, 0.64, 0.70),
        "nuclear": (0.16, 0.80, 0.11)}
BAND_GLOW = {"he": (1.0, 0.473, 0.0), "cluster": (1.0, 0.78, 0.11), "limpet": (1.0, 0.044, 0.03),
             "napalm": (1.0, 0.186, 0.0155), "emp": (0.078, 0.546, 1.0), "torpedo": (0.9, 0.93, 1.0),
             "nuclear": (0.20, 1.0, 0.147)}
NOSE_LIGHT = (0.64, 0.65, 0.66)      # tinta clara dos narizes (todas as formas)
COPPER = (0.90, 0.45, 0.22)          # cobre das bobinas (copia de parts/bs_mag_emp.py COPPER)


def copper_mat():
    """Cobre da familia P.E.M. com o MESMO nome e valores de bs_mag_emp ("copper", rough 0.22, metal 1.0): bobinas
    do Poraque e cinta de forcamento das granadas."""
    return B.mat_metal("copper", COPPER, rough=0.22, metal=1.0)


def band_mat(look):
    """Faixa do nariz: TINTA na cor do missil com uma emissao fraca (nao apaga na sombra). Copia de
    bs_msl_quad._band_mat (mesmo nome de material e mesmos valores)."""
    name = f"band_{look}"
    m = B.mat_metal(name, BAND[look], rough=0.65, metal=0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.0
    b.inputs["Emission Color"].default_value = (*BAND_GLOW[look], 1)
    b.inputs["Emission Strength"].default_value = 0.12
    m["bs_glow"] = 0.12
    return m


def nose_paint(name, color):
    """Tinta clara dos narizes (copia de bs_msl_quad._nose_paint)."""
    return B.mat_paint(name, color, rough=0.3, metal=0.15, wear=0.08, grime=0.02, scale=6)


def lathe(name, prof, mat, tags, verts=24, sy=1.0, axis="Z", zc=0.0, a0=0.0, smooth=True):
    """Solido de revolucao (copia de bs_msl_quad._lathe, com o mesmo resultado nos argumentos padrao).

    prof = [(raio, z)] ao longo do eixo (raio 0 = ponta); sy estica o eixo Y local.
    axis="X" (projeteis): o eixo do solido vira o X do mundo (nariz em +X), centrado na altura zc; sy estica a
    largura (Y do mundo) vista de cima e o fim do perfil ganha tampa. a0 gira o anel (a0 = pi/verts com verts=8
    deixa uma face plana em cima, como os canos da familia). smooth=False deixa todas as faces planas."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-5:
            p = [(0.0, 0.0, z)]
        elif axis == "X":
            p = [(r * math.cos(a), r * math.sin(a), z) for a in (a0 + i / verts * math.tau for i in range(verts))]
        else:
            p = [(r * math.cos(a), r * math.sin(a) * sy, z) for a in (a0 + i / verts * math.tau for i in range(verts))]
        if axis == "X":
            # (x, y, z) local -> (z, x, y) no mundo: permutacao ciclica = giro proprio (o sentido das faces fica);
            # depois estica a largura (Y) por sy
            p = [(zz, xx * sy, yy + zc) for xx, yy, zz in p]
        rings.append([bm.verts.new(v) for v in p])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            if len(rb) == 1:
                bm.faces.new((ra[i], ra[j], rb[0]))
            elif len(ra) == 1:
                bm.faces.new((ra[0], rb[j], rb[i]))
            else:
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if axis == "X" and len(rings[-1]) > 1:
        bm.faces.new(list(rings[-1]))       # tampa do fim (o original deixa aberto quando nao termina em ponta)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth and len(p.vertices) != verts
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def ogive(R, L, z0, tip_r=0.016):
    """Perfil de ogiva tangente (raio R, comprimento L) a partir de z0; para no raio da ponta de aco. Copia de
    bs_msl_quad._ogive; o perfil [(raio, z)] serve direto no lathe (axis="X": z = posicao em X)."""
    rho = (R * R + L * L) / (2 * R)
    prof = []
    for k in range(13):
        xt = L * (1 - k / 12)
        r = math.sqrt(max(0.0, rho * rho - (L - xt) ** 2)) + R - rho
        if r < tip_r:
            break
        prof.append((r, z0 + L - xt))
    return prof


def _ogive_to(R, Lv, rf, x0, n=10):
    """Ogiva tangente que vai do raio R (em x0) ao raio rf exatamente em x0 + Lv (truncada antes da ponta):
    acha por bisseccao o comprimento Lo da ogiva inteira cuja secao de raio rf cai em Lv."""
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


SHELL_KINDS = {
    # fracoes do comprimento total a partir da base: cauda (boat tail), fim do corpo cilindrico, comprimento da
    # espoleta / capuz; raios em fracoes do raio do corpo R
    "he": {"boat": 0.11, "tail_r": 0.80, "body_end": 0.56, "fuze": 0.085, "rf": 0.36, "tip_r": 0.45,
           "band": (0.135, 0.20), "band_r": 1.05},
    "ap": {"boat": 0.09, "tail_r": 0.84, "body_end": 0.47, "cap": 0.56, "tip_r": 0.06,
           "band": (0.115, 0.17), "band_r": 1.05},
}


def shell_profile(L, R, kind="he", x0=None, **kw):
    """Perfis de torno de uma granada de canhao deitada no eixo X (nariz em +X), centrada na origem por padrao.

    kind "he": base com cauda afinada (boat tail), corpo cilindrico, ogiva tangente truncada e espoleta curta de
    ponta chata. kind "ap": cauda curta, corpo mais curto e ogiva longa e pontuda; a frente da ogiva (fracao
    "cap") vira o capuz balistico escuro. kw troca qualquer valor de SHELL_KINDS[kind].
    Devolve {"segs": {"tail", "body", "ogive", "fuze" | "cap": [(raio, x)]}, "band": (xa, xb, raio),
    "x0", "x1", "R", "kind"}: cada segmento vai num lathe(..., axis="X") com o seu material; os segmentos
    vizinhos dividem o mesmo anel. A cinta de forcamento (band) e um anel um pouco mais largo que o corpo:
    cobre (cinta de cobre) e, nas granadas com mascara, o objeto marcado (T, "mask")."""
    p = dict(SHELL_KINDS[kind])
    p.update(kw)
    x0 = -L / 2 if x0 is None else x0
    x1 = x0 + L
    xb = x0 + p["boat"] * L
    xo = x0 + p["body_end"] * L
    segs = {"tail": [(p["tail_r"] * R, x0), (R, xb)], "body": [(R, xb), (R, xo)]}
    if "cap" in p:
        og = _ogive_to(R, x1 - xo, p["tip_r"] * R, xo, n=12)
        k = max(1, min(len(og) - 2, int(round((1 - p["cap"]) * (len(og) - 1)))))
        segs["ogive"] = og[:k + 1]
        segs["cap"] = og[k:]
    else:
        lf = p["fuze"] * L
        rf = p["rf"] * R
        segs["ogive"] = _ogive_to(R, x1 - lf - xo, rf, xo)
        xf = x1 - lf
        segs["fuze"] = [(rf, xf), (rf * 0.94, xf + 0.40 * lf), (rf * p["tip_r"], x1 - 0.05 * lf),
                        (rf * p["tip_r"] * 0.85, x1)]
    ba, bb = p["band"]
    return {"segs": segs, "band": (x0 + ba * L, x0 + bb * L, p["band_r"] * R), "x0": x0, "x1": x1, "R": R,
            "kind": kind}


def shell_parts(prefix, sp, mats, tags, verts=24, zc=0.0, smooth=True, mask_tags=None):
    """Torneia os segmentos de shell_profile() que tem material em mats ({"tail": m, "body": m, ...,
    "band": m}); a cinta (band) recebe mask_tags (ex.: (T, "mask")) quando dado. Devolve {nome: objeto}."""
    out = {}
    for name, prof in sp["segs"].items():
        if name in mats:
            out[name] = lathe(f"{prefix}_{name}", prof, mats[name], tags, verts=verts, axis="X", zc=zc,
                              smooth=smooth)
    if "band" in mats:
        xa, xb, rb = sp["band"]
        out["band"] = lathe(f"{prefix}_band", [(rb * 0.97, xa), (rb, xa + 0.15 * (xb - xa)), (rb, xb - 0.15 * (xb - xa)),
                                               (rb * 0.97, xb)], mats["band"], mask_tags or tags, verts=verts,
                            axis="X", zc=zc, smooth=smooth)
    return out


def trefoil_polys(cx, cy, ro, ri, a0=0.0):
    """3 cunhas do trevo nuclear (60 graus cada, a 120 graus) entre os raios ri e ro, no plano XY.
    a0 = direcao da 1a cunha em graus (0 = +X, o nariz do projetil; o recurso bs_shell_nuke usa 90)."""
    out = []
    for k in range(3):
        a = a0 + 120 * k
        inner = [(cx + ri * math.cos(math.radians(a + s)), cy + ri * math.sin(math.radians(a + s))) for s in (-24, 24)]
        arc = [(cx + ro * math.cos(math.radians(a + s)), cy + ro * math.sin(math.radians(a + s)))
               for s in (-30, -10, 10, 30)]
        out.append([inner[0]] + arc + [inner[1]])
    return out


def trefoil_inlay(name, targets, cx, cy, ztop, ro, ri, M, tags, wedge_mat=None, disc_mat=None, disc_r=None,
                  hub_mat=None, a0=0.0, depth=0.03, surface_r=None):
    """Trevo nuclear EMBUTIDO (tinta, nao emissivo) no topo de um projetil, visto de cima.

    Recorta um recesso de paredes verticais nos alvos (lista; a borda do recesso e a borda do desenho) ate um
    fundo plano em ztop - depth e poe as pecas planas la dentro: com disc_mat, um disco (raio disc_r, padrao
    ro * 1.25) e as 3 cunhas (wedge_mat, padrao M["black"]) por cima; sem disc_mat, so as cunhas recortadas.
    hub_mat = cubo no centro (opcional). surface_r = raio da superficie curva do alvo no ponto (lathe): o fundo
    desce o bastante para ficar abaixo da curva em toda a area do desenho.
    Armadilhas da secao 9 do STYLE: o fundo do cortador nunca fica coplanar com outra face (fundo sempre abaixo
    da superficie, topo bem acima) e as cunhas sao placas inteiras (nao ha ponta fina depois de chanfro)."""
    wedge_mat = wedge_mat or M["black"]
    targets = [t for t in (targets if isinstance(targets, (list, tuple)) else [targets]) if t is not None]
    rr = (disc_r or ro * 1.25) if disc_mat is not None else ro
    if surface_r:
        depth = max(depth, surface_r - math.sqrt(max(0.0, surface_r ** 2 - rr ** 2)) + 0.012)
    zf = ztop - depth
    zc_top = ztop + 0.5
    wedges = trefoil_polys(cx, cy, ro, ri, a0)
    for j, t in enumerate(targets):
        if disc_mat is not None:
            cutters = [B.cyl(f"{name}_dc{j}", cx, cy, (zf + zc_top) / 2, rr, zc_top - zf, M["black"], axis="Z",
                             verts=32, bevel=0.0)]
        else:
            cutters = [B.loft(f"{name}_wc{j}{k}", w, w, zf, zc_top, M["black"], bevel=0.0) for k, w in enumerate(wedges)]
        B.cut(t, cutters)
    objs = []
    if disc_mat is not None:
        objs.append(B.cyl(f"{name}_disc", cx, cy, zf - 0.003, rr, 0.014, disc_mat, axis="Z", verts=32, bevel=0.0,
                          tags=tags))
        zw0, zw1 = zf + 0.002, zf + 0.008
    else:
        zw0, zw1 = zf - 0.01, zf + 0.004
    for k, w in enumerate(wedges):
        objs.append(B.loft(f"{name}_w{k}", w, w, zw0, zw1, wedge_mat, bevel=0.0, tags=tags))
    if hub_mat is not None:
        objs.append(B.cyl(f"{name}_hub", cx, cy, zw1 + 0.001, ri * 0.62, 0.006, hub_mat, axis="Z", verts=16,
                          bevel=0.0, tags=tags))
    return objs


def chevron_sleeve(name, x0, x1, r, mat, tags, dv=None, front=True, rear=True, verts=8, zc=0.0, sy=1.0,
                   bevel=0.004, dv_rear=None):
    """Luva de blindagem em divisa ("escamas de vibora") em volta do corpo de um projetil, eixo X.

    Prisma de verts lados (topo plano, como os canos) de x0 a x1, raio r (sy estica a largura). A borda da frente
    vira uma divisa rasa apontando para +X (ponta dv a frente de x1, no meio) e a de tras um entalhe igual
    (dv_rear, padrao dv) onde encaixa a divisa da luva de tras. As divisas sao feitas NA MALHA (os vertices de
    cada anel andam em X conforme |y|), sem booleana: nao ha corte raso, fundo coplanar, ponta fina depois de
    chanfro nem malha vazia (STYLE secao 9). Como o deslocamento e so em X, toda face lateral continua plana e as
    tampas viram paredes verticais em V (invisiveis de cima). Para cortar fendas/LEDs depois, use profundidade
    >= 0.04 (B.cut reaplica o bisel)."""
    dv = r * 0.55 if dv is None else min(dv, r * 1.2)
    dvr = dv if dv_rear is None else min(dv_rear, r * 1.2)
    if x1 - x0 < 0.03 + max(0.0, (dvr if rear else 0.0) - (dv if front else 0.0)):
        raise ValueError(f"chevron_sleeve '{name}': curta demais para o entalhe ({x1 - x0:.3f})")
    # secao (y, z) anti-horaria: poligono de topo plano + vertices no meio do topo e do fundo (ponta da divisa)
    sec = []
    for i in range(verts):
        a = math.pi / verts + i / verts * math.tau
        sec.append((r * math.cos(a) * sy, r * math.sin(a)))
    top = r * math.cos(math.pi / verts)
    # insere o meio do topo entre os 2 vertices de cima e o meio do fundo entre os 2 de baixo
    ups = sorted(range(verts), key=lambda i: -sec[i][1])[:2]
    downs = sorted(range(verts), key=lambda i: sec[i][1])[:2]
    pts = []
    for i in range(verts):
        pts.append(sec[i])
        j = (i + 1) % verts
        if {i, j} == set(ups):
            pts.append((0.0, top))
        elif {i, j} == set(downs):
            pts.append((0.0, -top))
    ymax = max(abs(y) for y, _ in pts)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rear_v = [bm.verts.new((x0 + (dvr if rear else 0.0) * (1 - abs(y) / ymax), y, z + zc)) for y, z in pts]
    front_v = [bm.verts.new((x1 + (dv if front else 0.0) * (1 - abs(y) / ymax), y, z + zc)) for y, z in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((rear_v[i], rear_v[j], front_v[j], front_v[i]))
    # tampas em leque ate o centro (as tampas em V nao sao planas): centro na ponta da divisa, na altura do eixo
    cr = bm.verts.new((x0 + (dvr if rear else 0.0), 0.0, zc))
    cf = bm.verts.new((x1 + (dv if front else 0.0), 0.0, zc))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((rear_v[j], rear_v[i], cr))
        bm.faces.new((front_v[i], front_v[j], cf))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 1
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def chevron_mat(name, c1=(0.16, 0.80, 0.11), c2=(0.004, 0.004, 0.005), scale=8.0, slope=1.0, rough=0.5, metal=0.2):
    """Tinta em divisas apontando para +X (o nariz) nas coordenadas do objeto: listras c1/c2 ao longo de
    x + slope*|y|. Padrao verde/preto (Iara e granada nuclear: NUNCA amarelo/preto, regra do mod desde a
    Boiuna). scale = pares de listras por tile. E tinta (sem emissao); o nome entra no cache de materiais."""
    if name in B._MATS:
        return B._MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ab = N.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sep.outputs[1], ab.inputs[0])
    mad = N.new("ShaderNodeMath")
    mad.operation = "MULTIPLY_ADD"
    mad.inputs[1].default_value = slope
    nt.links.new(ab.outputs[0], mad.inputs[0])
    nt.links.new(sep.outputs[0], mad.inputs[2])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = scale
    nt.links.new(mad.outputs[0], mul.inputs[0])
    fr = N.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(mul.outputs[0], fr.inputs[0])
    gt = N.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    nt.links.new(fr.outputs[0], gt.inputs[0])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*c2, 1)
    mix.inputs[7].default_value = (*c1, 1)
    nt.links.new(gt.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    B._MATS[name] = m
    return m
