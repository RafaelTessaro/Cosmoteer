"""Kit das fabricas 2.0 do Bullet Strike (F1-F6): piso de grade, teto, insumos/produtos em miniatura e camadas extras.

Modulo do grupo "fabricas" (spec 2.0, art_assets.assets.factories). Nao altera o kit compartilhado (bs3d.py,
models.py, render_part.py): so importa de la. Cada fabrica continua sendo um modelo kind "factory"
(tools/blender/parts/bs_factory_<x>.py, renderizado por render_part.py); este modulo da a ela:

  * GRADE: as celulas da peca (x para a direita, y para BAIXO, como as regras) com o papel de cada uma
    (maquina, entrada, saida). Centro de uma celula em coordenadas do modelo = cell_xy(W, H, i, j).
  * floor_grid(): piso opaco com o poco escuro da maquina e as bases (pads) de entrada/saida, livres de
    maquinario (o jogo desenha as pilhas ali e a tripulacao precisa chegar em todas). Setas de LED fraco em
    recesso apontam o fluxo; as saidas das fabricas com seletor levam a pastilha pintada da municao (chip).
  * roof_deck() / roof_hatch() / plate_slot(): teto verde (pintura da nave) com escotilhas de entrada/saida em
    seta embutida e o encaixe da placa de modo (a placa placa_<modo>.png vem da pasta compartilhada bs_placas e
    e desenhada em roof_doodads por cima deste encaixe).
  * mini_*(): os produtos e insumos dentro das maquinas (carregadores HE/AP/SAP/AC/FRAG, celulas plasma/PEM,
    cargas de missil, ogiva nuclear, projetil da railgun, graos de enxofre, lingotes), com as cores da paleta
    2.0 (art_assets.palette) e o mesmo desenho dos recursos 2.0 (art_assets.assets.resources: caixa blindada
    com narizes e faixa de LED, cilindro com janela, bobinas de cobre...).
  * pecas de maquina da familia (cascas claras com bisel duplo, frestas escuras, LEDs em recessos): ledslot,
    bezel, chevron, vent, cylinder, chute.

Camadas extras (fora do contrato "factory" do render_part): uma fabrica pode declarar
    EXTRA_LAYERS = [{...}]      # mesmo esquema das camadas do render_layered.py (name, fn, game_layer, rect...)
e META_EXTRA = {...} (chaves somadas ao meta.json: mode_plate, overlays, grid, art3d_dir, notes). Depois do
render_part.py rode, com o Python do Blender:

    <venv>/bin/python tools/blender/parts/_bs2_fabricas_helpers.py <id_curto> [--out DIR] [--quick]

que renderiza as camadas extras com render_layered.render_layer (camera recortada no rect, normais, so emissao
com halo) e junta tudo no meta.json da fabrica ("overlays": {nome: {game_layer, rect, files, normals, frames,
interval, blend, gate}}). Sem EXTRA_LAYERS ele so grava META_EXTRA. O check_art3d le "hull" e "machine" como
antes; as chaves novas sao para o gerador 2.0 (bsgen/factory.py).
"""

import math
import os
import sys

if __name__ == "__main__":   # rodado como script: o kit (bs3d, models, render_layered) fica em tools/blender
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import bpy  # noqa: F401  (o bpy registra o bmesh que o bs3d importa)

import bs3d as B
import models as Mo

# ============================================================================ paleta 2.0 (sRGB -> linear)


def lin(c):
    """sRGB 0..255 -> linear do Blender."""
    out = []
    for v in c:
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# art_assets.palette (chip/band) e as cores ja aprovadas dos misseis 2.0 (bs_missiles2: Piranha amarelo-limao)
CHIP = {
    "he": (255, 190, 60), "ap": (215, 230, 255), "sap": (255, 140, 50), "ac": (230, 40, 80), "ac_gold": (255, 200, 80),
    "frag": (120, 210, 200), "plasma": (60, 220, 255), "pem": (60, 200, 255), "msl_he": (255, 150, 30),
    "msl_cluster": (255, 232, 80), "msl_emp": (40, 150, 255), "nuke": (90, 255, 40), "slug": (150, 105, 255),
    "rail_gold": (255, 200, 90), "pem_cu": (200, 110, 50),
    # pastilha/seta da saida HE da Fabrica de Misseis: laranja do casco do msl_he (palette.msl_he.hull), longe do
    # amarelo-limao da Piranha (o ambar da faixa HE se confundia com ele a 1x, 6x2 px)
    "msl_he_pad": (255, 96, 12),
}
VIOLET = (0.30, 0.135, 1.0)          # violeta do Tupa 1a versao (parts/bs_rail.py VIOLET)
RAIL_BLUE = (0.026, 0.171, 1.0)      # azul eletrico da Tupa nova (parts/bs_rail.py BLUE; USER_NOTES: referencia)
SULFUR = (0.62, 0.46, 0.035)         # enxofre (amarelo fosco em monte facetado: nao le como LED ambar)
IRON = (0.33, 0.30, 0.28)            # ferro bruto (lingote fosco)
URANIUM = (0.10, 0.20, 0.07)         # uranio bruto (pedra escura esverdeada)
TRISTEEL = (0.62, 0.66, 0.74)        # tristeel (barra azulada clara)


def _matte(name, color, rough=0.85, spec=0.2):
    """Material fosco sem desgaste (material a granel: enxofre, minerio)."""
    m = B.mat_metal(name, color, rough=rough, metal=0.0)
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = spec
    return m


def X(M):
    """Materiais extras do kit (nomes unicos: o cache do bs3d e por nome)."""
    return {
        "sulfur": _matte("f2_sulfur", SULFUR),
        "sulfur_dk": _matte("f2_sulfur_dk", tuple(v * 0.45 for v in SULFUR)),
        "iron": B.mat_paint("f2_iron", IRON, rough=0.6, metal=0.6, wear=0.2, grime=0.2, scale=8),
        "uranium": B.mat_paint("f2_uranium", URANIUM, rough=0.7, metal=0.2, wear=0.0, grime=0.2, scale=10),
        "tristeel": B.mat_metal("f2_tristeel", TRISTEEL, rough=0.22, metal=1.0),
        "silver": B.mat_metal("f2_silver", (0.80, 0.82, 0.86), rough=0.18, metal=1.0),
        "tungsten": B.mat_metal("f2_tungsten", (0.56, 0.58, 0.62), rough=0.26, metal=1.0),
        "gold": B.mat_metal("f2_gold", (1.0, 0.62, 0.16), rough=0.24, metal=1.0),
        "brass": B.mat_metal("f2_brass", (0.62, 0.42, 0.12), rough=0.3, metal=1.0),
        "copper": Mo.copper_mat(),
        "graphite": B.mat_paint("f2_graphite", (0.085, 0.088, 0.096), rough=0.42, metal=0.45, wear=0.25, grime=0.05),
        "nose": Mo.nose_paint("f2_nose", Mo.NOSE_LIGHT),
        "lens": B.mat_metal("f2_lens", (0.012, 0.016, 0.022), rough=0.08, metal=0.3),
        "glass_g": B.mat_metal("f2_glass_g", (0.010, 0.040, 0.012), rough=0.05, metal=0.25),
        "armor_r": B.mat_paint("f2_armor_mid_rough", Mo.ARMOR_MID, rough=0.72, metal=0.12, wear=0.3, grime=0.1),
    }


def chip_mat(kind, emit=0.12):
    """Tinta da faixa/pastilha da municao (nao e LED: emissao bem fraca para nao apagar na sombra, como
    Mo.band_mat)."""
    c = lin(CHIP[kind])
    m = B.mat_metal(f"f2_chip_{kind}", tuple(v * 0.82 for v in c), rough=0.6, metal=0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.1
    b.inputs["Emission Color"].default_value = (*c, 1)
    b.inputs["Emission Strength"].default_value = emit
    m["bs_glow"] = emit
    return m


def led(kind, s=1.0):
    """LED da cor da municao/destaque com forca s (lente escura quando apagado)."""
    c = lin(CHIP[kind]) if isinstance(kind, str) else kind
    nm = kind if isinstance(kind, str) else "c%02d%02d%02d" % tuple(int(v * 99) for v in kind)
    return B.mat_glow(f"f2_led_{nm}_{int(round(s * 100)):03d}", c, s)


def glow(color, s, name):
    return B.mat_glow(f"f2_{name}_{int(round(s * 100)):03d}", color, s)


# ============================================================================ grade
def cell_xy(W, H, i, j):
    """Centro da celula (i, j) (x para a direita, y para BAIXO, como as regras) em coordenadas do modelo."""
    return i + 0.5 - W / 2, H / 2 - j - 0.5


def rot(pts, ang, cx=0.0, cy=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def octo(cx, cy, r, a0=22.5, sy=1.0):
    return [(cx + r * math.cos(math.radians(a0 + 45 * i)), cy + sy * r * math.sin(math.radians(a0 + 45 * i)))
            for i in range(8)]


def flip(sx):
    """Poligono desenhado para o lado esquerdo -> lado sx (espelho em x no direito)."""
    return (lambda p: p) if sx < 0 else Mo.mirror


def shift(poly, dx, dy):
    return [(x + dx, y + dy) for x, y in poly]


# ============================================================================ pecas de maquina
def chevron(name, cx, cy, ang, mat, tags, z=0.03, s=1.0, th=0.006):
    """Seta (chevron) apontando para ang (graus: 0 = +x, 90 = +y)."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    return B.loft(name, rot(pts, ang, cx, cy), rot(pts, ang, cx, cy), z, z + th, mat, bevel=0.0, tags=tags)


def ledslot(name, cx, cy, sx, sy, z_bed, n, M, tags, targets, vertical=True, pip_mat=None, pw=None, pips=None,
            ang=0.0):
    """Fenda de LEDs VAZADA nas pecas alvo (sem filete do bisel sobre o leito, STYLE 9), leito preto em z_bed e n
    pips. pips = lista de materiais por pip (None = apagado)."""
    poly = B.rpoly(cx, cy, sx, sy, ang)
    for k, t in enumerate(targets or []):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_c{k}", poly, poly, z_bed - 0.02, z_bed + 0.8, M["black"], bevel=0.0)])
    B.loft(name + "_bed", poly, poly, z_bed, z_bed + 0.008, M["black"], bevel=0.0, tags=tags)
    L = sy if vertical else sx
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        px, py = (0.0, t * L) if vertical else (t * L, 0.0)
        px, py = rot([(px, py)], ang, cx, cy)[0]
        a, b = ((pw or sx * 0.55, L / n * 0.55) if vertical else (L / n * 0.55, pw or sy * 0.55))
        mat = (pips[i] if pips else (pip_mat or M["glow"]))
        if mat is None:
            mat = M["core_mid"]
        B.rbox(f"{name}_pip{i}", px, py, a, b, z_bed + 0.008, z_bed + 0.02, mat, rot=ang, bevel=0.0, tags=tags)


def groove(name, cx, cy, sx, sy, z_top, targets, M, tags, depth=0.05, rot=0.0, mat=None):
    """Linha de painel ESCURA: vala cortada nas pecas alvo (painel + corpo, profundidade > panel_h, STYLE 9) com um
    leito escuro (core) no fundo, para a linha ler a 1x tambem sobre placa clara ou pintada (STYLE 1.8). Um corte
    raso so no painel deixa o fundo claro/verde e a linha some no casco branco."""
    zb = z_top - depth
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.rbox(f"{name}_c{k}", cx, cy, sx, sy, zb, z_top + 0.5, M["core"], rot=rot, bevel=0.0)])
    return B.rbox(name + "_bed", cx, cy, sx, sy, zb - 0.006, zb + 0.002, mat or M["core"], rot=rot, bevel=0.0,
                  tags=tags)


def bezel(prefix, poly_out, poly_in, z0, z1, M, tags, targets, bed=True):
    """Janela com moldura em degrau: abre poly_out nas pecas e assenta um labio de aco no alto."""
    K, S = M["core"], M["steel"]
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.loft(f"{prefix}_c{k}", poly_out, poly_out, z0, 0.9, K, bevel=0.0)])
    lip = B.plate(prefix + "_lip", poly_out, z1 - 0.045, z1, S, slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft(prefix + "_lc", poly_in, poly_in, z1 - 0.2, z1 + 0.2, K, bevel=0.0)])
    if bed:
        B.loft(prefix + "_bed", poly_out, poly_out, z0 - 0.02, z0, M["black"], bevel=0.0, tags=tags)
    return lip


def vent(name, cx, cy, sx, sy, z0, z1, M, tags, n=4, vertical=False, targets=None):
    """Baia de respiro: recesso preto com venezianas escuras (corta as pecas alvo)."""
    K, KM = M["core"], M["core_mid"]
    for k, t in enumerate(targets or []):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{k}", cx, cy, sx, sy, z0, 0.9, K, bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, z0 - 0.01, z0, M["black"], bevel=0.0, tags=tags)
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        if vertical:
            B.box(f"{name}_lv{i}", cx + t * sx, cy, sx / n * 0.42, sy - 0.02, z0, z1, KM, bevel=0.003, tags=tags)
        else:
            B.box(f"{name}_lv{i}", cx, cy + t * sy, sx - 0.02, sy / n * 0.42, z0, z1, KM, bevel=0.003, tags=tags)


def hcyl(name, x0, x1, y, z, r, M, tags, mat=None, axis="X", ch=True, led_mat=None, collars=2):
    """Cilindro hidraulico facetado (8 lados, topo plano como os canos) entre x0 e x1 (ou y0, y1 com axis Y), com
    canal escuro em cima, colares de aco e LED no canal."""
    A, K, S = mat or M["armor"], M["core"], M["steel"]
    L = abs(x1 - x0)
    c = (x0 + x1) / 2
    cx, cy = (c, y) if axis == "X" else (y, c)
    ob = B.cyl(name, cx, cy, z, r, L, A, axis=axis, verts=8, bevel=0.01, tags=tags)
    if ch:
        sx, sy = (L - 0.06, r * 0.36) if axis == "X" else (r * 0.36, L - 0.06)
        B.cut(ob, [B.box(name + "_ch", cx, cy, sx, sy, z + r * 0.62, z + 0.6, K, bevel=0.0)])
        B.box(name + "_chb", cx, cy, sx, sy, z + r * 0.55, z + r * 0.66, M["black"], bevel=0.0, tags=tags)
        if led_mat is not None:
            lx, ly = (sx * 0.6, sy * 0.4) if axis == "X" else (sx * 0.4, sy * 0.6)
            B.box(name + "_led", cx, cy, lx, ly, z + r * 0.66, z + r * 0.70, led_mat, bevel=0.0, tags=tags)
    for k in range(collars):
        t = (k + 0.5) / collars - 0.5 if collars > 1 else 0.0
        t *= 0.8
        px, py = (c + t * L, y) if axis == "X" else (y, c + t * L)
        B.cyl(f"{name}_col{k}", px, py, z, r * 1.08, 0.03, S, axis=axis, verts=8, bevel=0.004, tags=tags)
    return ob


def chute(name, cx, cy, ang, M, tags, w=0.24, d=0.12, z1=0.07, led_mat=None, guides=True):
    """Boca de entrada/saida na borda de uma celula de maquina: calha escura com guias de aco e seta de LED.
    ang = sentido do fluxo (90 = sobe para a maquina, 270 = desce para a base de saida)."""
    K, S = M["core"], M["steel"]
    a = math.radians(ang)
    poly = rot([(-d / 2, -w / 2), (d / 2, -w / 2), (d / 2, w / 2), (-d / 2, w / 2)], ang, cx, cy)
    B.loft(name, poly, poly, 0.0, z1, K, bevel=0.006, tags=tags)
    if guides:
        for g in (-1, 1):
            gx, gy = cx - math.sin(a) * g * (w / 2 + 0.012), cy + math.cos(a) * g * (w / 2 + 0.012)
            B.rbox(f"{name}_g{g}", gx, gy, d + 0.01, 0.024, 0.0, z1 + 0.03, S, rot=ang, bevel=0.004, tags=tags)
    chevron(name + "_ar", cx, cy, ang, led_mat or M["glow_dim"], tags, z=z1, s=0.75)


def grains(name, pts, z, r, mat, tags, seed=0, mat2=None):
    """Graos/torroes (enxofre, minerio): cada um e um aglomerado de 2 octaedros achatados de tamanhos diferentes
    (le como material a granel, nao como LED). mat2 = tom escuro do segundo octaedro."""
    import random
    rnd = random.Random(seed)
    for k, (x, y) in enumerate(pts):
        rr = r * (0.8 + 0.4 * rnd.random())
        B.cyl(f"{name}{k}", x, y, z + rr * 0.35, rr, rr * 0.7, mat, axis="Z", verts=5, bevel=0.0, tags=tags,
              r2=rr * 0.45).rotation_euler.z = rnd.random() * 6.28
        a = rnd.random() * 6.28
        r2 = rr * (0.5 + 0.2 * rnd.random())
        B.cyl(f"{name}{k}b", x + math.cos(a) * rr * 0.8, y + math.sin(a) * rr * 0.8, z + r2 * 0.3, r2, r2 * 0.6,
              mat2 or mat, axis="Z", verts=5, bevel=0.0, tags=tags, r2=r2 * 0.4)


def heap(name, cx, cy, z, rx, ry, h, mat, tags, mat2=None, n=14, seed=7):
    """Monte de material a granel: torroes facetados (piramides de 5 lados) de tamanhos variados, mais altos no
    meio, cobrindo uma elipse rx x ry (le como pilha de cristais, com luz e sombra em cada faceta)."""
    import random
    rnd = random.Random(seed)
    B.cyl(name + "_bed", cx, cy, z + h * 0.15, rx * 0.95, h * 0.3, mat2 or mat, axis="Z", verts=10, bevel=0.0,
          tags=tags).scale.y = ry / rx
    for k in range(n):
        a = rnd.random() * 6.283
        d = math.sqrt(rnd.random()) * 0.85
        x, y = cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d
        rr = (0.30 + 0.25 * rnd.random()) * min(rx, ry) * (1.15 - 0.5 * d)
        hh = h * (1.0 - 0.6 * d) * (0.7 + 0.3 * rnd.random())
        ob = B.cyl(f"{name}{k}", x, y, z + hh / 2, rr, hh, mat if k % 3 else (mat2 or mat), axis="Z", verts=5,
                   bevel=0.0, tags=tags, r2=rr * 0.12)
        ob.rotation_euler.z = rnd.random() * 6.283


def rotor(name, cx, cy, z, r, ang, M, tags, blades=3, w=0.026, mat=None):
    """Rotor de pas (gira com ang em graus) e cubo escuro."""
    for b in range(blades):
        a = ang + b * 360.0 / blades
        B.rbox(f"{name}{b}", cx + math.cos(math.radians(a)) * r * 0.5, cy + math.sin(math.radians(a)) * r * 0.5,
               r, w, z, z + 0.025, mat or M["steel"], rot=a, bevel=0.004, tags=tags)
    B.cyl(f"{name}_hub", cx, cy, z + 0.03, w, 0.025, M["core_mid"], axis="Z", verts=12, bevel=0.004, tags=tags)


def parent_new(name, before, loc, scale=1.0, rz=0.0):
    """Prende a um Empty os objetos criados depois de 'before' e posiciona o conjunto."""
    sc = B.bpy.context.scene
    emp = B.bpy.data.objects.new(name, None)
    sc.collection.objects.link(emp)
    for o in [o for o in sc.objects if o.name not in before and o.parent is None and o is not emp]:
        o.parent = emp
    emp.location = loc
    emp.scale = (scale, scale, scale)
    emp.rotation_euler.z = math.radians(rz)
    return emp


def snapshot():
    return set(o.name for o in B.bpy.context.scene.objects)


# ============================================================================ produtos em miniatura
# Cada mini_* desenha UMA unidade na origem (frente = +Y) e devolve o Empty posicionado. s = escala (1 = o
# tamanho natural do recurso dentro da maquina, ~0.3 quadro).

MAG_KIND = {"he": "he", "ap": "ap", "sap": "sap", "ac": "ac", "frag": "frag", "blank": None}


def _mag(M, Xm, tags, kind, n=3, lit=True, cast=0.0):
    """Carregador 2.0 (caixa blindada, frente = +Y): bandeja de nucleo escuro com as 3 municoes de nivel S deitadas a
    mostra, laterais claras com bisel duplo, travessa traseira com a faixa da municao e os LEDs num recesso.
    kind None = carcaca neutra (sem faixa). cast = 0..1 brasa nas pontas (recem-fundido)."""
    K, KM, A, S = M["core"], M["core_mid"], M["armor"], M["steel"]
    B.box("mg_tray", 0, -0.01, 0.27, 0.19, 0.0, 0.045, K, bevel=0.006, tags=tags)
    hot = glow((1.0, 0.25, 0.03), 1.2 * cast, "cast") if cast > 0 else None
    for i in range(n):
        x = (i - (n - 1) / 2) * 0.056
        B.cyl(f"mg_rd{i}", x, -0.005, 0.058, 0.022, 0.13, Xm["nose"], axis="Y", verts=8, bevel=0.0, tags=tags)
        B.cyl(f"mg_rb{i}", x, -0.06, 0.058, 0.0235, 0.012, KM, axis="Y", verts=8, bevel=0.0, tags=tags)
        if kind == "ap":
            B.cyl(f"mg_tp{i}", x, 0.095, 0.058, 0.019, 0.07, Xm["silver"], axis="Y", verts=8, bevel=0.0, tags=tags,
                  r2=0.003)
        elif kind == "sap":
            B.cyl(f"mg_tp{i}", x, 0.074, 0.058, 0.022, 0.028, chip_mat("sap"), axis="Y", verts=8, bevel=0.0,
                  tags=tags, r2=0.014)
        elif kind == "ac":
            B.cyl(f"mg_tp{i}", x, 0.085, 0.058, 0.020, 0.05, Xm["gold"], axis="Y", verts=8, bevel=0.0, tags=tags,
                  r2=0.004)
            B.box(f"mg_fn{i}", x, 0.03, 0.05, 0.014, 0.075, 0.083, Xm["gold"], bevel=0.0, tags=tags)
        elif kind == "frag":
            B.cyl(f"mg_tp{i}", x, 0.07, 0.058, 0.023, 0.02, KM, axis="Y", verts=8, bevel=0.0, tags=tags, r2=0.017)
            for g in range(2):
                B.cyl(f"mg_tr{i}{g}", x, 0.01 + g * 0.03, 0.058, 0.0235, 0.014, chip_mat("frag"), axis="Y", verts=8,
                      bevel=0.0, tags=tags)
        else:
            B.cyl(f"mg_tp{i}", x, 0.08, 0.058, 0.022, 0.04, hot or Xm["nose"], axis="Y", verts=8, bevel=0.0,
                  tags=tags, r2=0.008)
    side = [(0.098, -0.105), (0.15, -0.105), (0.15, 0.045), (0.12, 0.085), (0.098, 0.085)]
    for sx in (-1, 1):
        B.shard(f"mg_side{sx}", side if sx > 0 else Mo.mirror(side), 0.0, 0.105, A, slope=0.016, groove=0.008,
                panel_h=0.01, tags=tags)
    back = [(-0.15, -0.115), (0.15, -0.115), (0.15, -0.05), (-0.15, -0.05)]
    ba, bp = B.shard("mg_back", back, 0.0, 0.11, A, slope=0.016, groove=0.008, panel_h=0.01, tags=tags)
    # trava da frente (barra de aco escura sobre as municoes)
    B.box("mg_bar", 0, 0.035, 0.21, 0.018, 0.07, 0.088, KM, bevel=0.004, tags=tags)
    # faixa da municao + LEDs num recesso da travessa traseira
    for k, t in enumerate((ba, bp)):
        if t is not None:
            B.cut(t, [B.box(f"mg_bc{k}", 0, -0.0825, 0.25, 0.034, 0.075, 0.5, K, bevel=0.0)])
    B.box("mg_bbed", 0, -0.0825, 0.25, 0.034, 0.07, 0.076, M["black"], bevel=0.0, tags=tags)
    if kind:
        B.box("mg_band", 0, -0.0825, 0.23, 0.022, 0.076, 0.086, chip_mat(kind), bevel=0.0, tags=tags)
        if lit:
            for i in range(3):
                B.box(f"mg_bl{i}", -0.065 + i * 0.065, -0.0825, 0.03, 0.012, 0.086, 0.09,
                      led(kind, 1.2 if kind != "ap" else 0.9), bevel=0.0, tags=tags)
    else:
        B.box("mg_band", 0, -0.0825, 0.23, 0.022, 0.076, 0.084, M["steel"], bevel=0.0, tags=tags)
    if kind == "ac":
        # tampas de canto em ouro (estojo premium da Alta Capacidade)
        for qx in (-1, 1):
            for qy, yy in ((1, 0.062), (-1, -0.098)):
                B.box(f"mg_gc{qx}{qy}", qx * 0.128, yy, 0.05, 0.04, 0.0, 0.118, Xm["gold"], bevel=0.006, tags=tags)


def mini_mag(name, x, y, z, M, Xm, tags, kind="he", s=1.0, rz=0.0, lit=True, cast=0.0):
    before = snapshot()
    _mag(M, Xm, tags, MAG_KIND.get(kind, kind), lit=lit, cast=cast)
    return parent_new(name, before, (x, y, z), s, rz)


def _cell(M, Xm, tags, kind, level=1.0, lit=True):
    """Celula 2.0 deitada ao longo de Y: plasma = cilindro sextavado blindado com janela ciano num recesso;
    PEM = mesma carcaca com 3 aneis de cobre e faixa de LED azul baixa. level = 0..1 enchimento (janela)."""
    K, KM, A, S = M["core"], M["core_mid"], M["armor"], M["steel"]
    body = B.cyl("cl_body", 0, 0, 0.07, 0.068, 0.30, A, axis="Y", verts=6, bevel=0.006, tags=tags)
    for sy in (-1, 1):
        B.cyl(f"cl_cap{sy}", 0, sy * 0.155, 0.07, 0.058, 0.03, KM, axis="Y", verts=6, bevel=0.004, tags=tags)
        B.cyl(f"cl_term{sy}", 0, sy * 0.178, 0.07, 0.026, 0.02, S, axis="Y", verts=8, bevel=0.0, tags=tags)
    win = B.box("cl_wc", 0, 0, 0.05, 0.19, 0.11, 0.3, K, bevel=0.0)
    B.cut(body, [win])
    B.box("cl_wbed", 0, 0, 0.05, 0.19, 0.105, 0.112, M["black"], bevel=0.0, tags=tags)
    if kind == "plasma":
        n = int(round(level * 4))
        for i in range(4):
            on = lit and i < n
            B.box(f"cl_core{i}", 0, -0.07 + i * 0.047, 0.03, 0.038, 0.112, 0.118,
                  glow(lin(CHIP["plasma"]), 1.1, "plcore") if on else KM, bevel=0.0, tags=tags)
    else:
        for i, yy in enumerate((-0.085, 0.0, 0.085)):
            B.cyl(f"cl_cu{i}", 0, yy, 0.07, 0.074, 0.04, Xm["copper"], axis="Y", verts=12, bevel=0.0, tags=tags)
        n = int(round(level * 2))
        for i, yy in enumerate((-0.043, 0.043)):
            on = lit and i < n
            B.box(f"cl_bl{i}", 0, yy, 0.03, 0.03, 0.112, 0.118, glow(lin(CHIP["pem"]), 0.9, "pemled") if on else KM,
                  bevel=0.0, tags=tags)


def mini_cell(name, x, y, z, M, Xm, tags, kind="plasma", s=1.0, rz=0.0, level=1.0, lit=True):
    before = snapshot()
    _cell(M, Xm, tags, kind, level, lit)
    return parent_new(name, before, (x, y, z), s, rz)


def _missile(M, Xm, tags, kind, part="all", lit=True):
    """Carga de missil deitada ao longo de Y (nariz +Y): corpo claro com costuras de luva, faixa da cor do tipo,
    aletas na cauda. kind msl_he | msl_cluster (nariz em 4 petalas) | msl_emp (bobinas de cobre + LED azul).
    part: "body" (sem nariz), "nose" (so o nariz/ogiva) ou "all"."""
    K, KM, A, S = M["core"], M["core_mid"], M["armor"], M["steel"]
    R = 0.045
    if part in ("all", "body"):
        B.cyl("ms_body", 0, -0.04, R, R, 0.26, A, axis="Y", verts=8, bevel=0.004, tags=tags)
        for k, yy in enumerate((-0.12, -0.02)):
            B.cyl(f"ms_seam{k}", 0, yy, R, R * 1.03, 0.008, K, axis="Y", verts=8, bevel=0.0, tags=tags)
        B.cyl("ms_tail", 0, -0.185, R, R * 0.8, 0.03, KM, axis="Y", verts=8, bevel=0.0, tags=tags, r2=R * 0.6)
        for sx in (-1, 1):
            fin = [(R * 0.6, -0.17), (R * 1.9, -0.19), (R * 1.9, -0.155), (R * 0.6, -0.10)]
            fin = fin if sx > 0 else Mo.mirror(fin)
            B.loft(f"ms_fin{sx}", fin, fin, R * 0.9, R * 1.15, KM, bevel=0.0, tags=tags)
        if kind == "msl_emp":
            for k, yy in enumerate((-0.07, 0.01)):
                B.cyl(f"ms_cu{k}", 0, yy, R, R * 1.07, 0.035, Xm["copper"], axis="Y", verts=12, bevel=0.0, tags=tags)
        B.cyl("ms_band", 0, 0.06, R, R * 1.04, 0.022, chip_mat(kind), axis="Y", verts=8, bevel=0.0, tags=tags)
        if lit:
            B.box("ms_led", 0, -0.06, 0.016, 0.03, 2 * R - 0.002, 2 * R + 0.004, led(kind, 1.0), bevel=0.0, tags=tags)
    if part in ("all", "nose"):
        y0 = 0.09
        if kind == "msl_cluster":
            B.cyl("ms_nose", 0, y0 + 0.035, R, R, 0.07, Xm["nose"], axis="Y", verts=8, bevel=0.0, tags=tags,
                  r2=R * 0.55)
            for k in range(4):
                a = 45 + 90 * k
                B.rbox(f"ms_pet{k}", math.cos(math.radians(a)) * R * 0.5, y0 + 0.05, 0.012, 0.06, R + 0.01,
                       R + 0.03 + 0.01 * (k % 2), K, rot=0, bevel=0.0, tags=tags)
            B.cyl("ms_tip", 0, y0 + 0.078, R, R * 0.5, 0.02, chip_mat("msl_cluster"), axis="Y", verts=8, bevel=0.0,
                  tags=tags, r2=R * 0.2)
        else:
            B.cyl("ms_nose", 0, y0 + 0.045, R, R, 0.09, Xm["nose"], axis="Y", verts=8, bevel=0.0, tags=tags,
                  r2=R * 0.18)
            B.cyl("ms_seek", 0, y0 + 0.086, R, R * 0.3, 0.014, Xm["lens"], axis="Y", verts=8, bevel=0.0, tags=tags,
                  r2=R * 0.1)


def mini_missile(name, x, y, z, M, Xm, tags, kind="msl_he", s=1.0, rz=0.0, part="all", lit=True):
    before = snapshot()
    _missile(M, Xm, tags, kind, part, lit)
    return parent_new(name, before, (x, y, z), s, rz)


def _warhead(M, Xm, tags, stage=3, lit=True, glow_k=1.0):
    """Ogiva nuclear 2.0 deitada ao longo de Y (nariz +Y), no desenho do recurso bs_msl_nuke: corpo claro alongado,
    nariz arredondado com o disco verde e o trevo escuro de 3 cunhas, 2 faixas verdes, janela escura com o nucleo
    verde aceso no meio, base com aneis. Sem divisas e sem amarelo (o trevo e permitido no recurso nuclear, STYLE 7).
    stage: 1 = carcaca aberta (miolo escuro a mostra), 2 = com o nucleo verde, 3 = fechada."""
    K, KM, A, S = M["core"], M["core_mid"], M["armor"], M["steel"]
    R = 0.085
    zc = R
    green = glow((0.32, 1.0, 0.0), 0.75, "nuled")
    B.cyl("wh_base", 0, -0.165, zc, R * 0.92, 0.04, KM, axis="Y", verts=12, bevel=0.004, tags=tags)
    for k, yy in enumerate((-0.19, -0.14)):
        B.cyl(f"wh_ring{k}", 0, yy, zc, R * 1.0, 0.012, S, axis="Y", verts=12, bevel=0.0, tags=tags)
    body = B.cyl("wh_body", 0, -0.02, zc, R, 0.24, A, axis="Y", verts=12, bevel=0.006, tags=tags)
    # janela escura do nucleo (vazada no topo do corpo) com as faixas verdes acima e abaixo
    B.cut(body, [B.box("wh_wc", 0, -0.03, 0.10, 0.12, zc + R * 0.55, zc + 0.3, K, bevel=0.0)])
    B.box("wh_wbed", 0, -0.03, 0.10, 0.12, zc + R * 0.50, zc + R * 0.58, M["black"], bevel=0.0, tags=tags)
    if stage >= 2:
        B.box("wh_core", 0, -0.03, 0.04, 0.09, zc + R * 0.58, zc + R * 0.64,
              glow((0.30, 1.0, 0.12), 1.0 * glow_k, "nucore") if lit else KM, bevel=0.0, tags=tags)
        for k in range(4):
            B.box(f"wh_coil{k}", 0, -0.065 + k * 0.023, 0.06, 0.008, zc + R * 0.64, zc + R * 0.67, KM, bevel=0.0,
                  tags=tags)
    for k, yy in enumerate((-0.105, 0.045)):
        B.cyl(f"wh_band{k}", 0, yy, zc, R * 1.02, 0.024, chip_mat("nuke", 0.25), axis="Y", verts=12, bevel=0.0,
              tags=tags)
    if stage >= 3:
        B.cyl("wh_nose", 0, 0.16, zc, R, 0.10, A, axis="Y", verts=12, bevel=0.006, tags=tags, r2=R * 0.55)
        B.cyl("wh_tip", 0, 0.222, zc, R * 0.55, 0.025, A, axis="Y", verts=12, bevel=0.004, tags=tags, r2=R * 0.15)
        zt = zc + R * 0.92
        B.cyl("wh_tdisk", 0, 0.155, zt, 0.046, 0.012, chip_mat("nuke", 0.25), axis="Z", verts=16, bevel=0.0,
              tags=tags)
        for k in range(3):
            a = 90 + 120 * k
            pts = [(0.0, 0.0)] + [(math.cos(math.radians(a + d)) * 0.040, math.sin(math.radians(a + d)) * 0.040)
                                  for d in (-30, -15, 0, 15, 30)]
            pts = [(px * 0.95 + math.cos(math.radians(a)) * 0.007, py * 0.95 + math.sin(math.radians(a)) * 0.007)
                   for px, py in pts]
            B.loft(f"wh_tw{k}", shift(pts, 0, 0.155), shift(pts, 0, 0.155), zt + 0.006, zt + 0.011, K, bevel=0.0,
                   tags=tags)
    else:
        # carcaca aberta: o anel da boca e o poco escuro (a tampa entra depois)
        op = B.cyl("wh_open", 0, 0.13, zc, R, 0.05, A, axis="Y", verts=12, bevel=0.004, tags=tags)
        B.cut(op, [B.cyl("wh_oc", 0, 0.13, zc, R * 0.70, 0.2, K, axis="Y", verts=12, bevel=0.0)])
        B.cyl("wh_pit", 0, 0.11, zc, R * 0.72, 0.03, K, axis="Y", verts=12, bevel=0.0, tags=tags)
    if lit:
        B.box("wh_led", 0, -0.165, 0.04, 0.014, zc + R * 0.9, zc + R * 0.96, green, bevel=0.0, tags=tags)


def mini_warhead(name, x, y, z, M, Xm, tags, s=1.0, rz=0.0, stage=3, lit=True, glow_k=1.0):
    before = snapshot()
    _warhead(M, Xm, tags, stage, lit, glow_k)
    return parent_new(name, before, (x, y, z), s, rz)


def _slug(M, Xm, tags, collars=4, heat=0.0, lit=True, rod_only=False):
    """Projetil da railgun deitado ao longo de Y (ponta +Y), no desenho da Tupa nova (bs_shells2 'slug' e o recurso
    bs_slug_rail): haste de tungstenio, aletas curtas na cauda, colares EM azul anodizado com o filete de LED azul
    (collars = quantos ja foram cravados), colar laranja atras do penetrador e ponta de metal claro azulado.
    heat = 0..1 brasa da haste (forno)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    r = 0.022
    # brasa: vermelho-laranja fraco esfriando -> laranja-ouro forte no forno (forca e cor sobem com o calor)
    hc = (1.0, 0.16 + 0.34 * heat, 0.02 + 0.10 * heat)
    hot = glow(hc, 0.18 + 1.25 * heat ** 1.3, f"rodhot{int(heat * 20):02d}") if heat > 0.05 else None
    rod_m = B.mat_metal("f2_rod", (0.30, 0.31, 0.34), rough=0.3, metal=0.9)
    B.cyl("sg_rod", 0, 0.0, r, r, 0.40, hot or rod_m, axis="Y", verts=8, bevel=0.0, tags=tags)
    if rod_only:
        return
    tipm = B.mat_metal("f2_tipblue", (0.30, 0.37, 0.48), rough=0.32, metal=0.5)
    B.cyl("sg_tip", 0, 0.225, r, r, 0.05, tipm, axis="Y", verts=8, bevel=0.0, tags=tags, r2=0.003)
    orange = B.mat_paint("f2_railorange", (0.60, 0.25, 0.020), rough=0.36, metal=0.3, wear=0.0, grime=0.0, scale=6)
    B.cyl("sg_oc", 0, 0.185, r, r * 1.35, 0.016, orange, axis="Y", verts=8, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        poly = [(sx * r * 0.7, -0.20), (sx * r * 2.6, -0.21), (sx * r * 2.6, -0.17), (sx * r * 0.7, -0.13)]
        poly = poly if sx > 0 else list(reversed(poly))
        B.loft(f"sg_fin{sx}", poly, poly, r * 0.6, r * 1.3, KM, bevel=0.0, tags=tags)
    blue = B.mat_metal("f2_railblue", (0.018, 0.075, 0.40), rough=0.35, metal=0.4)
    for k in range(min(collars, 4)):
        yy = -0.10 + k * 0.075
        B.cyl(f"sg_col{k}", 0, yy, r, r * 1.6, 0.02, blue, axis="Y", verts=8, bevel=0.0, tags=tags)
        if lit:
            B.box(f"sg_cl{k}", 0, yy, 0.02, 0.008, r * 2.55, r * 2.65, glow(RAIL_BLUE, 0.9, "slugcol_b"), bevel=0.0,
                  tags=tags)


def mini_slug(name, x, y, z, M, Xm, tags, s=1.0, rz=0.0, collars=4, heat=0.0, lit=True, rod_only=False):
    before = snapshot()
    _slug(M, Xm, tags, collars, heat, lit, rod_only)
    return parent_new(name, before, (x, y, z), s, rz)


# ============================================================================ piso
def floor_grid(M, W, H, machine, pads, T="floor", chips=None, copper=(), rail_rows=()):
    """Piso opaco de uma fabrica 2.0.

    machine: celulas (i, j) do maquinario (poco escuro com grade de fendas). pads: {(i, j): ang | (ang, lado)} das
    bases de entrada/saida: ang = sentido da seta (graus) ou None (sem seta); lado = angulo do lado da moldura com o
    recesso da seta (o lado da maquina; padrao = ang, o caso das entradas; saida: (270, 90) = seta para baixo
    num recesso no lado de cima).
    chips: {(i, j): kind} pastilha pintada da municao na moldura da base (saidas com seletor). copper: celulas com
    a grade de cobre no poco (insumo cobre). rail_rows: fileiras j de saida com moldura escura continua sob as
    bases (a fileira de saida "inteira" das regras)."""
    tags = (T,)
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    Xm = X(M)
    B.box("fl_base", 0, 0, W, H, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for i in range(W):
        for j in range(H):
            cx, cy = cell_xy(W, H, i, j)
            p = B.plate(f"fl{i}_{j}", B.rpoly(cx, cy, 0.95, 0.95, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.012,
                        tags=tags)
            if (i, j) in machine:
                B.cut(p, [B.box(f"flg{i}_{j}_{k}", cx, cy - 0.3 + k * 0.15, 0.72, 0.04, 0.015, 0.1, K, bevel=0.0)
                          for k in range(5)])
    for j in rail_rows:
        cells = sorted(i for (i, jj) in pads if jj == j)
        if cells:
            x0 = cell_xy(W, H, cells[0], j)[0] - 0.47
            x1 = cell_xy(W, H, cells[-1], j)[0] + 0.47
            cy = cell_xy(W, H, 0, j)[1]
            B.plate(f"out_rail{j}", B.rpoly((x0 + x1) / 2, cy, x1 - x0, 0.90, 0, chamfer=0.1), 0.03, 0.045, K,
                    slope=0.01, tags=tags)
    for (i, j), ang in pads.items():
        cx, cy = cell_xy(W, H, i, j)
        nm = f"{i}{j}"
        notch = ang
        if isinstance(ang, (tuple, list)):
            ang, notch = ang
        fr = B.plate(f"pad_{nm}", B.rpoly(cx, cy, 0.86, 0.86, 0, chamfer=0.10), 0.03, 0.062, KM, slope=0.016,
                     tags=tags)
        hole = B.rpoly(cx, cy, 0.70, 0.70, 0, chamfer=0.07)
        cuts = [B.loft(f"pad_h{nm}", hole, hole, 0.02, 0.3, K, bevel=0.0)]
        side = None
        if ang is not None:
            # recesso na moldura do lado de onde vem/para onde vai o fluxo (o lado da maquina)
            a = ang % 360
            # o recesso fica do lado da maquina (notch); entrada: a seta aponta para ele, saida: aponta para fora
            dx, dy = round(math.cos(math.radians(notch)), 3), round(math.sin(math.radians(notch)), 3)
            if abs(dx) > 0.5 and abs(dy) > 0.5:
                ex, ey = cx + dx * 0.33, cy + dy * 0.33   # diagonal: recesso no canto
                sx_, sy_ = 0.14, 0.14
            else:
                ex, ey = cx + dx * 0.39, cy + dy * 0.39
                sx_, sy_ = (0.14, 0.30) if abs(dx) > 0.5 else (0.30, 0.14)
            side = (round(dx), round(dy))
            cuts.append(B.box(f"pad_n{nm}", ex, ey, sx_, sy_, 0.042, 0.3, K, bevel=0.0))
            B.box(f"pad_nb{nm}", ex, ey, sx_ - 0.02, sy_ - 0.02, 0.036, 0.043, M["black"], bevel=0.0, tags=tags)
            chevron("chv_" + nm, ex, ey, a, M["glow_dim"], tags, z=0.043, s=0.62)
        if chips and (i, j) in chips:
            # pastilha pintada da municao na borda de baixo da moldura (num recesso, com lista escura)
            kx, ky = cx, cy - 0.39
            cuts.append(B.box(f"pad_k{nm}", kx, ky, 0.40, 0.10, 0.045, 0.3, K, bevel=0.0))
            B.box(f"pad_kb{nm}", kx, ky, 0.40, 0.10, 0.038, 0.045, M["black"], bevel=0.0, tags=tags)
            B.box(f"pad_kc{nm}", kx, ky, 0.34, 0.05, 0.045, 0.056, chip_mat(chips[(i, j)], 0.25), bevel=0.004,
                  tags=tags)
        B.cut(fr, cuts)
        lip = B.plate(f"padlip_{nm}", B.rpoly(cx, cy, 0.73, 0.73, 0, chamfer=0.075), 0.035, 0.056, AM, slope=0.005,
                      bevel=0.004, tags=tags)
        inner = B.rpoly(cx, cy, 0.69, 0.69, 0, chamfer=0.066)
        B.cut(lip, [B.loft(f"padlip_h{nm}", inner, inner, 0.02, 0.3, K, bevel=0.0)])
        B.loft(f"padwell_{nm}", inner, inner, 0.03, 0.04, K, bevel=0.0, tags=tags)
        if (i, j) in copper:
            # grade de cobre escurecido (o insumo cobre fica sobre ela; nao pode competir com as pilhas)
            cu = B.mat_metal("f2_copper_dk", (0.42, 0.19, 0.08), rough=0.45, metal=0.9)
            for k in range(7):
                B.box(f"cug_{nm}{k}", cx - 0.27 + k * 0.09, cy, 0.016, 0.62, 0.04, 0.048, cu, bevel=0.0, tags=tags)
            for k in range(2):
                B.box(f"cuh_{nm}{k}", cx, cy - 0.15 + k * 0.30, 0.62, 0.016, 0.04, 0.05, cu, bevel=0.0, tags=tags)
        else:
            B.box(f"padgv_{nm}", cx, cy, 0.012, 0.58, 0.04, 0.046, KM, bevel=0.0, tags=tags)
            B.box(f"padgh_{nm}", cx, cy, 0.58, 0.012, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.325, cy + qy * 0.325
                poly = [(ox, oy), (ox - qx * 0.16, oy), (ox - qx * 0.16, oy - qy * 0.045),
                        (ox - qx * 0.045, oy - qy * 0.045), (ox - qx * 0.045, oy - qy * 0.16), (ox, oy - qy * 0.16)]
                B.plate(f"padbr_{nm}{qx}{qy}", poly if qx * qy > 0 else list(reversed(poly)), 0.04, 0.058,
                        AM, slope=0.008, bevel=0.004, tags=tags)
        pts = [(cx + 0.39 * dx, cy + 0.39 * dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if (dx, dy) != side and not (chips and (i, j) in chips and (dx, dy) == (0, -1))]
        B.bolts(f"pbolt_{nm}", pts, 0.066, 0.014, S, tags=tags)


# ============================================================================ teto
def roof_green():
    return B.mat_roof_green()


def roof_deck(M, W, H, skip=(), T="roof", gap=0.04, diag=True):
    """Placas verdes (pintura) de cada celula, menos as de skip. Devolve {(i, j): (base, painel)}."""
    tags = (T,)
    green = roof_green()
    K = M["core"]
    B.box("rf_under", 0, 0, W, H, -0.05, 0.02, K, bevel=0.0, tags=tags)
    out = {}
    for i in range(W):
        for j in range(H):
            if (i, j) in skip:
                continue
            cx, cy = cell_xy(W, H, i, j)
            pa, pp = B.shard(f"rf{i}_{j}", B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.10), 0.0, 0.07,
                             green, slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
            out[(i, j)] = (pa, pp)
    return out


def inlay(name, poly, targets, z1, tags, gap=0.03, mat=None):
    """Placa embutida (seta, emblema): abre um furo (contorno + vao) nas placas de base e assenta a placa no fundo
    escuro."""
    green = mat or roof_green()
    hole = B.offset_poly(poly, -gap)
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_h{k}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    return B.shard(name, poly, 0.0, z1, green, slope=0.05, groove=0.03, panel_h=0.018, tags=tags)


def roof_hatch(name, M, cx, cy, ang, targets, T="roof", led_mat=None, chip=None, s=1.0):
    """Escotilha de base em seta embutida (traseira em V) apontando para ang, com fenda de 3 pips no meio.
    chip: pastilha pintada da municao (saidas com seletor) na ponta da seta."""
    tags = (T,)
    arrow = [(-0.27, -0.23), (-0.27, 0.07), (0.0, 0.29), (0.27, 0.07), (0.27, -0.23), (0.0, -0.13)]
    arrow = [(x * s, y * s) for x, y in arrow]
    poly = rot(arrow, ang - 90, cx, cy)
    aa, ap = inlay(name, poly, targets, 0.13, tags)
    c = rot([(0.0, -0.01 * s)], ang - 90, cx, cy)[0]
    ledslot(name + "_p", c[0], c[1], 0.065 * s, 0.17 * s, 0.02, 3, M, tags, [aa, ap], pw=0.030,
            pip_mat=led_mat or M["glow_dim"], ang=ang - 90)
    if chip:
        k = rot([(0.0, 0.205 * s)], ang - 90, cx, cy)[0]
        cut = rot([(-0.07, -0.03), (0.07, -0.03), (0.07, 0.03), (-0.07, 0.03)], ang - 90, k[0], k[1])
        for q, t in enumerate((aa, ap)):
            if t is not None:
                B.cut(t, [B.loft(f"{name}_kc{q}", cut, cut, 0.08, 0.5, M["core"], bevel=0.0)])
        B.loft(f"{name}_kb", cut, cut, 0.075, 0.085, M["black"], bevel=0.0, tags=tags)
        kp = rot([(-0.055, -0.018), (0.055, -0.018), (0.055, 0.018), (-0.055, 0.018)], ang - 90, k[0], k[1])
        B.loft(f"{name}_kp", kp, kp, 0.085, 0.10, chip_mat(chip, 0.25), bevel=0.003, tags=tags)
    return aa, ap


def plate_slot(name, M, cx, cy, size, targets, T="roof", z1=0.14):
    """Encaixe da placa de modo (placa_<modo>.png, 48 px, desenhada pelo jogo em roof_doodads com Size = size):
    moldura clara chanfrada um pouco maior que a placa e fundo escuro com 4 parafusos nos cantos. A placa cobre o
    miolo; a moldura aparece em volta (~0.05 quadro)."""
    tags = (T,)
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    out = B.rpoly(cx, cy, size + 0.14, size + 0.14, 0, chamfer=0.09)
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_h{k}", B.offset_poly(out, -0.025), B.offset_poly(out, -0.025), -0.01, 0.5, K,
                             bevel=0.0)])
    fa, fp = B.shard(name, out, 0.0, z1, A, slope=0.03, groove=0.018, panel_h=0.016, tags=tags)
    inner = B.rpoly(cx, cy, size + 0.02, size + 0.02, 0, chamfer=0.06)
    for k, t in enumerate((fa, fp)):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_ic{k}", inner, inner, z1 - 0.06, 0.6, K, bevel=0.0)])
    B.loft(name + "_bed", inner, inner, z1 - 0.07, z1 - 0.055, KM, bevel=0.0, tags=tags)
    h = size / 2 - 0.06
    B.bolts(name + "_b", [(cx + dx * h, cy + dy * h) for dx in (-1, 1) for dy in (-1, 1)], z1 - 0.055, 0.02, S,
            tags=tags)
    # tracos de indice (onde a placa encaixa) nos 4 lados da moldura
    for k, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        e = size / 2 + 0.045
        B.box(f"{name}_ix{k}", cx + dx * e, cy + dy * e, 0.02 if dx else 0.12, 0.12 if dx else 0.02, z1 - 0.004,
              z1 + 0.006, K, bevel=0.0, tags=tags)
    return fa, fp


def roof_unpaint(T="roof"):
    """O verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nos biseis claros:
    o shader do jogo pinta por g - max(r, b))."""
    green = roof_green()
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False


# ============================================================================ camadas extras (render)
LIGHTS_TARGET = 64     # pico do lights.png (as fabricas 1.x aprovadas ficam em 49-73)


def _lights_gain(out, target=LIGHTS_TARGET, cap=3.0):
    """O render_factory monta o lights.png do quadro 1 com um desfoque de 6 px: os LEDs pequenos das fabricas 2.0
    (so em recessos, STYLE 1.6) saem com pico 20-50 e nao florescem nas naves escuras. Sobe o ganho ate o pico
    chegar perto do nivel 1.x (target), no maximo cap x. O sprite da maquina (e a area acesa dele) nao muda.
    Marca o PNG (texto bs_lights_gain) para nao aplicar duas vezes."""
    import numpy as np
    from PIL import Image, PngImagePlugin
    p = os.path.join(out, "lights.png")
    if not os.path.exists(p):
        return None
    im = Image.open(p)
    if "bs_lights_gain" in im.info:
        return float(im.info["bs_lights_gain"])
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    peak = float(a[..., :3].max())
    g = 1.0 if peak <= 0 or peak >= target else min(cap, target / peak)
    a[..., :3] = np.clip(a[..., :3] * g, 0, 255)
    info = PngImagePlugin.PngInfo()
    info.add_text("bs_lights_gain", f"{g:.3f}")
    Image.fromarray(a.astype(np.uint8), "RGBA").save(p, pnginfo=info)
    print(f"lights.png: pico {peak:.0f} -> {min(255.0, peak * g):.0f} (ganho {g:.2f})")
    return g


def _main():
    """Renderiza EXTRA_LAYERS de uma fabrica e junta META_EXTRA/overlays no meta.json dela."""
    import importlib
    import json
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.dirname(os.path.dirname(here))
    sys.path.insert(0, here)
    sys.path.insert(0, os.path.join(root, "tools"))
    import render_layered as RL
    args = sys.argv[1:]
    short = args[0]
    out = os.path.join(root, "art3d", short)
    if "--out" in args:
        out = args[args.index("--out") + 1]
    RL.QUICK = "--quick" in args
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else set()
    mod = importlib.import_module(f"parts.{short}")
    P = mod.PART
    mp = os.path.join(out, "meta.json")
    meta = json.load(open(mp))
    overlays = dict(meta.get("overlays", {}))
    files = set(meta.get("files", []))
    for layer in getattr(mod, "EXTRA_LAYERS", []):
        if only and layer["name"] not in only:
            continue
        ent = RL.render_layer(mod, P, layer, out)
        for k in ("gate", "notes", "anchor"):
            if k in layer:
                ent[k] = layer[k]
        overlays[layer["name"]] = ent
        files |= set(ent["files"]) | set(ent.get("normals") or [])
    if overlays:
        meta["overlays"] = overlays
    meta.update(getattr(mod, "META_EXTRA", {}))
    g = _lights_gain(out, getattr(mod, "LIGHTS_TARGET", LIGHTS_TARGET))
    if g is not None:
        meta["lights_gain"] = round(g, 3)
    meta["files"] = sorted(files)
    json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False)
    print("OK extras", short, out, sorted(overlays))


if __name__ == "__main__":
    _main()
