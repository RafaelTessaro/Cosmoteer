"""Fabrica de Celulas de Plasma (Plasma Cell Factory) 3x3 - usina de confinamento magnetico.

Layout vanilla factory_he (tools/bsgen/factory.py): fileira de cima + tile central = maquinario (bloqueado);
entradas no meio das laterais: tile (0,1) esquerda = enxofre, tile (2,1) direita = bobina; saida = fileira de
baixo inteira. O jogo desenha as pilhas nesses 5 tiles, entao eles ficam livres de maquinario e o piso mostra
bases escuras marcadas (cantoneiras, labio fino, setas ciano em recesso). Coordenadas centradas na peca,
+Y = frente (topo da imagem), 1 unidade = 1 tile.

Maquina (mesma familia das armas: cascas claras chanfradas com bisel duplo sobre nucleo escuro, ciano so em
fendas e recessos escuros):
  * anel de confinamento toroidal no tile de cima do meio: toro escuro blindado sobre base octogonal, coberto
    por 6 blocos de bobina claros (setores com bisel duplo e ranhuras de enrolamento); o plasma ciano aparece
    so pelas fendas estreitas vazadas no meio de cada bloco e anda em volta do anel (blocos acendendo em
    sequencia, sentido horario); cubo central escuro com o solenoide;
  * ionizador de enxofre a esquerda: casca clara com janela octogonal em degrau mostrando o funil escuro com
    graos de enxofre amarelos girando ate a saida, onde o anel ionizador ciano pulsa; duto ate a fenda
    esquerda do anel; boca de entrada com setas ciano para cima (vem da base de enxofre embaixo);
  * injetor de bobina a direita (espelho): janela com o carretel de fio de cobre girando (3 raios de aco) e
    o fio entrando pelo duto ate a fenda direita do anel; boca de entrada com setas (vem da base de bobina);
  * berco de enchimento no tile central: capuzes claros em U (respiros dos dois lados, tunel de saida
    embaixo com setas para a saida), trilhos de aco, garras que prendem a celula; o bico injetor desce do
    pescoco do anel e encaixa no terminal da celula.
Animacao (12 quadros): 0 celula vazia no berco, bico recolhido (= sprite desligado); 1 bico desce; 2 encaixa
(anel de contato); 3-6 a celula enche (tubo ciano subindo, LEDs 1..4, jato no bico); 7 lampejo dos respiros e
o bico sobe; 8 garras abrem; 9-11 a celula cheia desce para o tunel de saida enquanto a proxima celula vazia
entra pelo capuz direito (vem do injetor de bobina). O plasma do anel anda um bloco por quadro.
A celula e o proprio modelo do recurso (parts/bs_plasma_cell.py) em miniatura.
Teto: placas verdes (pintura) com o emblema do toro sem pintura (anel de 6 segmentos claros com fenda ciano
fina e cubo), espinha do injetor com pips, escotilha em capsula sobre o berco (a celula: janela com 4 pips),
setas embutidas das entradas (para cima) e da saida (para baixo), respiros nas placas das pontas.
"""

import math

import bs3d as B
import models as Mo
from parts import bs_plasma_cell as CELL

PART = {
    "id": "rafaeltessaro.bs_factory_plasma",
    "kind": "factory",
    "size": [3, 3],
    "accent": "cyan",
    "machine_frames": 12,
    "machine_interval": 0.12,
}

NF = PART["machine_frames"]
RC = (0.0, 0.975)          # centro do anel toroidal
RING_R = 0.295             # raio maior do toro (eixo do tubo de plasma)
SEG_R0, SEG_R1 = 0.185, 0.405  # blocos de bobina (raio interno / externo)
CR_Y = 0.12                # centro da celula sentada no berco
MINI = 0.36                # escala da celula no berco (0.17 x 0.35 tile)
CELL_Z = 0.08              # apoio da celula (topo dos trilhos)
HOUSE_C = (1.03, 1.125)    # centro (|x|, y) das janelas das cascas laterais
WIN_R = 0.19               # raio da janela octogonal


# ============================================================================ utilidades
def _extra():
    """Materiais proprios (plasma em 3 niveis, lampejo, enxofre, cobre)."""
    cm = CELL._mats()
    return {
        "pl_lo": B.mat_glow("pl_lo", Mo.CYAN, 0.42),
        "pl_mid": cm["plasma"],
        "pl_hi": B.mat_glow("pl_hi", (0.45, 0.93, 1.0), 2.6),
        "flash": B.mat_glow("vent_flash", (0.55, 0.95, 1.0), 2.2),
        "copper": cm["copper"],
        "sulfur": B.mat_metal("sulfur", (0.80, 0.62, 0.07), rough=0.62, metal=0.0),
        "sulfur2": B.mat_metal("sulfur2", (0.62, 0.45, 0.05), rough=0.7, metal=0.0),
    }


def _rot(pts, ang, cx=0.0, cy=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def _octo(cx, cy, r, a0=22.5):
    return [(cx + r * math.cos(math.radians(a0 + 45 * i)), cy + r * math.sin(math.radians(a0 + 45 * i)))
            for i in range(8)]


def _pol(cx, cy, r, a):
    return (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))


def _sector(cx, cy, r0, r1, ac, hs, c=0.0, n=3):
    """Setor de coroa (angulo central ac, meia abertura hs, graus) facetado, cantos chanfrados em c."""
    a0, a1 = ac - hs, ac + hs
    out = []
    if c > 0:
        out.append(_pol(cx, cy, r1 - c, a0))
        da = math.degrees(c / r1)
        for k in range(n + 1):
            out.append(_pol(cx, cy, r1, a0 + da + (a1 - a0 - 2 * da) * k / n))
        out.append(_pol(cx, cy, r1 - c, a1))
        db = math.degrees(c / r0)
        out.append(_pol(cx, cy, r0 + c, a1))
        out.append(_pol(cx, cy, r0, a1 - db))
        out.append(_pol(cx, cy, r0, a0 + db))
        out.append(_pol(cx, cy, r0 + c, a0))
    else:
        for k in range(n + 1):
            out.append(_pol(cx, cy, r1, a0 + (a1 - a0) * k / n))
        for k in range(n + 1):
            out.append(_pol(cx, cy, r0, a1 - (a1 - a0) * k / n))
    return out


def _flip(sx):
    return (lambda p: p) if sx < 0 else Mo.mirror


def _chevron(name, cx, cy, ang, M, tags, z=0.03, s=1.0, mat=None):
    """Seta (chevron) apontando para ang (graus), em LED fraco."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    B.loft(name, _rot(pts, ang, cx, cy), _rot(pts, ang, cx, cy), z, z + 0.006, mat or M["glow_dim"], bevel=0.0,
           tags=tags)


def _ledslot(name, cx, cy, sx, sy, z_bed, n, M, tags, targets, vertical=True, pip_mat=None, pw=None, pips=None):
    """Fenda de LEDs VAZADA nas pecas (armadilha b: sem filete do bisel sobre o leito), leito preto em z_bed e
    n pips. pips = lista de materiais por pip (opcional)."""
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{k}", cx, cy, sx, sy, z_bed - 0.02, z_bed + 0.8, M["black"], bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, z_bed, z_bed + 0.008, M["black"], bevel=0.0, tags=tags)
    L = sy if vertical else sx
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        px, py = (cx, cy + t * L) if vertical else (cx + t * L, cy)
        a, b = ((pw or sx * 0.55, L / n * 0.55) if vertical else (L / n * 0.55, pw or sy * 0.55))
        mat = pips[i] if pips else (pip_mat or M["glow"])
        B.box(f"{name}_pip{i}", px, py, a, b, z_bed + 0.008, z_bed + 0.02, mat, bevel=0.0, tags=tags)


def _bezel(prefix, poly_out, poly_in, z0, z1, M, tags, targets):
    """Janela com moldura em degrau: abre poly_out nas pecas e assenta um labio de aco no alto."""
    K, S = M["core"], M["steel"]
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.loft(f"{prefix}_c{k}", poly_out, poly_out, z0, 0.9, K, bevel=0.0)])
    lip = B.plate(prefix + "_lip", poly_out, z1 - 0.05, z1, S, slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft(prefix + "_lc", poly_in, poly_in, z1 - 0.2, z1 + 0.2, K, bevel=0.0)])
    B.loft(prefix + "_bed", poly_out, poly_out, z0 - 0.02, z0, M["black"], bevel=0.0, tags=tags)


def _mini_cell(name, x, y, M, tags, level, leds):
    """Celula de Plasma em miniatura: o proprio modelo do recurso (bs_plasma_cell.cell) preso a um Empty."""
    sc = B.bpy.context.scene
    before = set(o.name for o in sc.objects)
    CELL.cell(M, tags, level=level, leds=leds, name=name)
    emp = B.bpy.data.objects.new(name + "_emp", None)
    sc.collection.objects.link(emp)
    for o in [o for o in sc.objects if o.name not in before and o.parent is None and o is not emp]:
        o.parent = emp
    emp.location = (x, y, CELL_Z)
    emp.scale = (MINI, MINI, MINI)
    return emp


def _state(phase):
    """Estado do ciclo no quadro (ver docstring do modulo)."""
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        "arm": {1: 0.5, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 0.45}.get(i, 0.0),
        "level": {3: 0.25, 4: 0.5, 5: 0.75}.get(i, 1.0 if 6 <= i <= 10 else 0.0),
        "flow": 3 <= i <= 6,
        "contact": i == 2,
        "vent": {7: 1.0, 8: 0.4}.get(i, 0.0),
        "clamp": 1.0 if 8 <= i <= 10 else (0.5 if i == 11 else 0.0),
        # celula cheia saindo (y do centro) e celula vazia entrando (x do centro)
        "out_y": {9: -0.02, 10: -0.16}.get(i),
        "in_x": {10: 0.25, 11: 0.12}.get(i),
        "cell_y": CR_Y if i <= 8 else None,
    }


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso opaco: leito escuro do maquinario + bases escuras marcadas das entradas e da saida."""
    tags = (T,)
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    B.box("fl_base", 0, 0, 3, 3, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(3):
        for ty in range(3):
            cx, cy = tx - 1.0, 1.0 - ty
            p = B.plate(f"fl{tx}{ty}", B.rpoly(cx, cy, 0.94, 0.94, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.012,
                        tags=tags)
            if ty == 0 or (tx, ty) == (1, 1):
                # leito do maquinario: grade de fendas escuras
                B.cut(p, [B.box(f"flg{tx}{ty}{i}", cx - 0.3 + i * 0.15, cy, 0.04, 0.7, 0.015, 0.1, K, bevel=0.0)
                          for i in range(5)])
    # trilho da saida: moldura escura unica sob as 3 bases
    B.plate("out_rail", B.rpoly(0, -1.0, 2.86, 0.88, 0, chamfer=0.1), 0.03, 0.045, K, slope=0.01, tags=tags)
    # bases: (nome, centro, seta no lado de cima?, angulo da seta): as entradas sobem para o ionizador / injetor,
    # a saida do meio recebe do tunel do berco (seta para baixo)
    pads = (("in0", -1.0, 0.0, True, 90), ("in1", 1.0, 0.0, True, 90), ("out0", -1.0, -1.0, False, None),
            ("out1", 0.0, -1.0, True, 270), ("out2", 1.0, -1.0, False, None))
    for name, cx, cy, arrow, ang in pads:
        fr = B.plate(f"pad_{name}", B.rpoly(cx, cy, 0.86, 0.86, 0, chamfer=0.10), 0.03, 0.062, KM, slope=0.016,
                     tags=tags)
        hole = B.rpoly(cx, cy, 0.70, 0.70, 0, chamfer=0.07)
        cuts = [B.loft(f"pad_h{name}", hole, hole, 0.02, 0.3, K, bevel=0.0)]
        if arrow:
            ex, ey = cx, cy + 0.39
            cuts.append(B.box(f"pad_n{name}", ex, ey, 0.30, 0.14, 0.042, 0.3, K, bevel=0.0))
            B.box(f"pad_nb{name}", ex, ey, 0.28, 0.10, 0.036, 0.043, M["black"], bevel=0.0, tags=tags)
            for k, dx in enumerate((-0.07, 0.07)):
                _chevron(f"chv_{name}{k}", ex + dx, ey, ang, M, tags, z=0.043, s=0.55)
        B.cut(fr, cuts)
        # labio fino claro na borda do poco
        lip = B.plate(f"padlip_{name}", B.rpoly(cx, cy, 0.73, 0.73, 0, chamfer=0.075), 0.035, 0.056, AM,
                      slope=0.005, bevel=0.004, tags=tags)
        inner = B.rpoly(cx, cy, 0.69, 0.69, 0, chamfer=0.066)
        B.cut(lip, [B.loft(f"padlip_h{name}", inner, inner, 0.02, 0.3, K, bevel=0.0)])
        B.loft(f"padwell_{name}", inner, inner, 0.03, 0.04, K, bevel=0.0, tags=tags)
        B.box(f"padgv_{name}", cx, cy, 0.012, 0.58, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        B.box(f"padgh_{name}", cx, cy, 0.58, 0.012, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        # cantoneiras em L nos 4 cantos do poco
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.325, cy + qy * 0.325
                poly = [(ox, oy), (ox - qx * 0.16, oy), (ox - qx * 0.16, oy - qy * 0.045),
                        (ox - qx * 0.045, oy - qy * 0.045), (ox - qx * 0.045, oy - qy * 0.16), (ox, oy - qy * 0.16)]
                B.plate(f"padbr_{name}{qx}{qy}", poly, 0.04, 0.058, AM, slope=0.008, bevel=0.004, tags=tags)
        pts = [(cx + 0.39 * dx, cy + 0.39 * dy) for dx, dy in ((1, 0), (-1, 0), (0, -1))] + \
              ([] if arrow else [(cx, cy + 0.39)])
        B.bolts(f"pbolt_{name}", pts, 0.066, 0.014, S, tags=tags)


# ============================================================================ maquina: anel toroidal
SEQ = [1, 0, 5, 4, 3, 2]   # ordem horaria dos blocos (k do angulo 30 + 60k): 90, 30, 330, 270, 210, 150


def _ring(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    cx, cy = RC
    i = st["i"]
    # base octogonal escura do anel + parafusos nas pontas laterais
    B.plate("rg_base", _octo(cx, cy, 0.47), 0.03, 0.10, K, slope=0.02, tags=tags)
    B.bolts("rg_bolt", [p for p in _octo(cx, cy, 0.44) if abs(p[1] - cy) < 0.3], 0.105, 0.016, S, tags=tags)
    # toro escuro blindado (o tubo de plasma corre por dentro)
    B.torus("rg_torus", cx, cy, 0.17, RING_R, 0.085, KM, tags=tags)
    # nivel do plasma em cada bloco: o da frente forte, o de tras medio, o resto fraco (quadro 0 = repouso)
    lead = (i - 1) % 6 if i > 0 else None
    for k in range(6):
        a = 30 + 60 * k
        poly = _sector(cx, cy, SEG_R0, SEG_R1, a, 24.5, c=0.035)
        ba, bp = B.shard(f"rg_blk{k}", poly, 0.10, 0.32, A, slope=0.035, groove=0.018, panel_h=0.022, tags=tags)
        # fenda tangencial vazada no meio do bloco: mostra o tubo de plasma em cima do toro
        slit = _sector(cx, cy, RING_R - 0.017, RING_R + 0.017, a, 15.5, n=4)
        for t in (ba, bp):
            if t is not None:
                B.cut(t, [B.loft(f"rg_sc{k}{t.name[-3:]}", slit, slit, -0.1, 0.8, K, bevel=0.0)])
        s = SEQ.index(k)
        if lead is None:
            mat = X["pl_mid"]
        elif s == lead:
            mat = X["pl_hi"]
        elif s == (lead - 1) % 6:
            mat = X["pl_mid"]
        else:
            mat = X["pl_mid"] if st["flow"] else X["pl_lo"]
        core = _sector(cx, cy, RING_R - 0.011, RING_R + 0.011, a, 14.0, n=4)
        B.loft(f"rg_pl{k}", core, core, 0.245, 0.256, mat, bevel=0.0, tags=tags)
        # ranhuras de enrolamento: 2 linhas radiais no painel de cada lado da fenda
        if bp is not None:
            cuts = []
            for j, da in enumerate((-17.5, 17.5)):
                p0 = _pol(cx, cy, (SEG_R0 + SEG_R1) / 2, a + da)
                cuts.append(B.rbox(f"rg_gr{k}{j}", p0[0], p0[1], 0.014, 0.13, 0.30, 0.6, K, rot=a + da - 90,
                                   bevel=0.0))
            B.cut(bp, cuts)
    # cubo central: solenoide (octogono medio + aco) com olho ciano fraco num recesso
    B.plate("rg_hub", _octo(cx, cy, 0.125), 0.10, 0.22, AM, slope=0.025, tags=tags)
    hub2 = B.plate("rg_hub2", _octo(cx, cy, 0.075, 0), 0.22, 0.26, S, slope=0.012, tags=tags)
    B.cut(hub2, [B.loft("rg_hubc", _octo(cx, cy, 0.035, 0), _octo(cx, cy, 0.035, 0), 0.20, 0.5, K, bevel=0.0)])
    B.loft("rg_hubbed", _octo(cx, cy, 0.035, 0), _octo(cx, cy, 0.035, 0), 0.215, 0.225, M["black"], bevel=0.0,
           tags=tags)
    B.cyl("rg_hubeye", cx, cy, 0.228, 0.017, 0.006, X["pl_hi"] if st["flow"] else M["glow_dim"], axis="Z",
          verts=8, bevel=0.0, tags=tags)


def _ducts(M, X, tags):
    """Dutos das cascas laterais ate as fendas laterais do anel (enxofre ionizado a esquerda, fio de cobre a
    direita), no vao escuro entre as cascas e o anel."""
    KM, S = M["core_mid"], M["steel"]
    cx, cy = RC
    for sx in (-1, 1):
        x0, x1 = sx * 0.66, sx * (SEG_R1 - 0.02)
        xm, ln = (x0 + x1) / 2, abs(x1 - x0)
        B.cyl(f"dc{sx}", xm, cy, 0.20, 0.05, ln, KM, axis="X", verts=8, bevel=0.006, tags=tags)
        for j, f in enumerate((0.2, 0.75)):
            ring_m = X["copper"] if sx > 0 else S
            B.cyl(f"dc_r{sx}{j}", x0 + (x1 - x0) * f, cy, 0.20, 0.058, 0.026, ring_m, axis="X", verts=8, bevel=0.004,
                  tags=tags)
        # tira escura com o fluxo (ciano fraco = enxofre ionizado; cobre = fio da bobina)
        B.box(f"dc_bed{sx}", xm, cy, ln - 0.06, 0.03, 0.245, 0.252, M["black"], bevel=0.0, tags=tags)
        B.box(f"dc_flow{sx}", xm, cy, ln - 0.10, 0.012, 0.252, 0.256, M["glow_dim"] if sx < 0 else X["copper"],
              bevel=0.0, tags=tags)


# ============================================================================ maquina: cascas laterais
MAIN = [(-1.40, 1.27), (-1.28, 1.39), (-0.78, 1.39), (-0.66, 1.27), (-0.66, 0.94), (-0.75, 0.85), (-1.28, 0.85),
        (-1.40, 0.97)]
BLADE = [(-1.40, 0.785), (-0.88, 0.785), (-0.58, 0.60), (-0.64, 0.555), (-1.30, 0.555), (-1.40, 0.655)]


def _housing(prefix, sx, M, tags):
    """Casca lateral (lado sx): bloco principal com a janela octogonal (devolvido) e lamina com a boca de entrada."""
    f = _flip(sx)
    K, A, S, KM = M["core"], M["armor"], M["steel"], M["core_mid"]
    ma, mp = B.shard(prefix + "_main", f(MAIN), 0.0, 0.44, A, slope=0.07, groove=0.035, panel_h=0.03, tags=tags)
    ba, bp = B.shard(prefix + "_blade", f(BLADE), 0.0, 0.30, A, slope=0.06, groove=0.028, panel_h=0.025, tags=tags)
    wx, wy = sx * HOUSE_C[0], HOUSE_C[1]
    _bezel(prefix + "_win", _octo(wx, wy, WIN_R), _octo(wx, wy, WIN_R - 0.026), 0.26, 0.47, M, tags, (ma, mp))
    # fenda vertical de 3 pips ciano no lado de fora da janela
    _ledslot(prefix + "_sl", sx * 1.315, 1.12, 0.05, 0.24, 0.12, 3, M, tags, [ma, mp], pip_mat=M["glow_dim"],
             pw=0.026)
    # linhas de painel: diagonal no chanfro de baixo de dentro e horizontal sob a janela
    if mp is not None:
        B.cut(mp, [B.rbox(prefix + "_pl1", sx * 0.74, 0.93, 0.022, 0.10, 0.40, 0.8, K, rot=sx * 45, bevel=0.0),
                   B.rbox(prefix + "_pl2", sx * 1.03, 0.905, 0.22, 0.02, 0.40, 0.8, K, bevel=0.0)])
    # lamina: boca de entrada (vem da base de baixo) com 3 setas ciano para cima + linha de painel na ponta
    _ledslot(prefix + "_in", sx * 1.10, 0.67, 0.30, 0.075, 0.12, 0, M, tags, [ba, bp], vertical=False)
    for k in range(3):
        _chevron(f"{prefix}_inchv{k}", sx * (1.00 + k * 0.10), 0.67, 90, M, tags, z=0.128, s=0.40)
    if bp is not None:
        B.cut(bp, [B.rbox(prefix + "_pl3", sx * 0.80, 0.665, 0.022, 0.12, 0.26, 0.8, K, rot=sx * 58, bevel=0.0)])
    B.bolts(prefix + "_bolt", [(sx * 1.33, 1.33), (sx * 0.73, 1.33), (sx * 1.33, 0.91)], 0.47, 0.017, S, tags=tags)
    # mangueira no vao entre a lamina e o bloco principal
    B.cyl(prefix + "_hose", sx * 1.05, 0.82, 0.10, 0.03, 0.46, KM, axis="X", verts=8, bevel=0.005, tags=tags)
    return ma, mp


def _ionizer(M, X, tags, st):
    """Ionizador de enxofre (tile de cima a esquerda): funil escuro com graos amarelos girando para a saida,
    anel ionizador ciano em volta do bocal."""
    KM, S = M["core_mid"], M["steel"]
    _housing("ion", -1, M, tags)
    wx, wy = -HOUSE_C[0], HOUSE_C[1]
    rin = WIN_R - 0.026
    # funil: bloco escuro com tronco invertido recortado (paredes inclinadas para o bocal)
    fn = B.loft("ion_fun", _octo(wx, wy, rin), _octo(wx, wy, rin), 0.24, 0.40, KM, bevel=0.0, tags=tags)
    B.cut(fn, [B.loft("ion_func", _octo(wx, wy, 0.045), _octo(wx, wy, rin - 0.012), 0.255, 0.405, KM, bevel=0.0)])
    # graos de enxofre nas paredes do funil, girando para o bocal (1/12 de volta por quadro)
    i = st["i"]
    rot = -i * 30.0
    for k in range(14):
        a = rot + k * (360 / 14) + (k % 3) * 9
        rr = 0.07 + (k * 37 % 7) / 7 * 0.075
        z = 0.255 + (rr - 0.045) / (rin - 0.057) * 0.15
        px, py = _pol(wx, wy, rr, a)
        sz = 0.034 + (k % 4) * 0.006
        B.rbox(f"ion_g{k}", px, py, sz, sz * 0.8, z - 0.01, z + 0.02, X["sulfur"] if k % 3 else X["sulfur2"],
               rot=a * 1.7 + k * 23, bevel=0.006, tags=tags)
    # bocal com o anel ionizador (pulsa: forte nos quadros pares)
    B.cyl("ion_noz", wx, wy, 0.255, 0.04, 0.02, M["black"], axis="Z", verts=12, bevel=0.0, tags=tags)
    B.torus("ion_ring", wx, wy, 0.27, 0.05, 0.011, X["pl_hi"] if i % 2 == 0 else X["pl_mid"], tags=tags)


def _coil(M, X, tags, st):
    """Injetor de bobina (tile de cima a direita): carretel de fio de cobre girando na janela."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    _housing("coil", 1, M, tags)
    wx, wy = HOUSE_C[0], HOUSE_C[1]
    i = st["i"]
    B.cyl("coil_disk", wx, wy, 0.30, 0.150, 0.08, X["copper"], axis="Z", verts=24, bevel=0.006, tags=tags)
    for j, R in enumerate((0.118, 0.083)):
        B.torus(f"coil_gr{j}", wx, wy, 0.34, R, 0.007, K, tags=tags)
    B.cyl("coil_hub", wx, wy, 0.355, 0.05, 0.03, S, axis="Z", verts=8, bevel=0.006, tags=tags)
    B.cyl("coil_hub2", wx, wy, 0.372, 0.02, 0.006, K, axis="Z", verts=8, bevel=0.0, tags=tags)
    ang = -i * 30.0
    for k in range(3):
        a = ang + k * 120
        px, py = _pol(wx, wy, 0.098, a)
        B.rbox(f"coil_sp{k}", px, py, 0.095, 0.022, 0.34, 0.365, S, rot=a, bevel=0.004, tags=tags)
    # fio saindo do carretel para o duto (lado de dentro da janela)
    B.box("coil_wire", wx - 0.155, wy - 0.05, 0.05, 0.014, 0.33, 0.342, X["copper"], bevel=0.0, tags=tags)


# ============================================================================ maquina: berco de enchimento
LHOOD = [(-0.47, 0.36), (-0.37, 0.46), (-0.26, 0.46), (-0.215, 0.415), (-0.215, -0.035), (-0.29, -0.11),
         (-0.47, -0.11)]
BHOOD = [(-0.47, -0.165), (-0.33, -0.165), (-0.255, -0.12), (0.255, -0.12), (0.33, -0.165), (0.47, -0.165),
         (0.47, -0.37), (0.37, -0.475), (-0.37, -0.475), (-0.47, -0.37)]
NECK = [(-0.135, 0.63), (0.135, 0.63), (0.135, 0.52), (0.06, 0.45), (-0.06, 0.45), (-0.135, 0.52)]


def _cradle(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    i = st["i"]
    # bloco de maquina do tile central e leito do berco
    B.plate("cr_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.035, K, slope=0.012, tags=tags)
    B.plate("cr_bed", B.rpoly(0, 0.16, 0.40, 0.62, 0, chamfer=0.07), 0.03, 0.06, KM, slope=0.012, tags=tags)
    B.box("cr_bedk", 0, 0.16, 0.13, 0.52, 0.06, 0.064, M["black"], bevel=0.0, tags=tags)
    # trilhos de aco (descem ate o tunel de saida) e trilho de entrada vindo do capuz direito
    for sx in (-1, 1):
        B.box(f"cr_rail{sx}", sx * 0.105, 0.12, 0.022, 0.62, 0.04, CELL_Z, S, bevel=0.004, tags=tags)
    for k, dy in enumerate((-0.10, 0.10)):
        B.box(f"cr_feed{k}", 0.17, CR_Y + dy, 0.12, 0.016, 0.04, CELL_Z - 0.005, S, bevel=0.003, tags=tags)
    # capuzes claros em U: respiros nos dois lados, tunel de saida embaixo
    for sx in (-1, 1):
        f = _flip(sx)
        ha, hp = B.shard(f"hood{sx}", f(LHOOD), 0.0, 0.30, A, slope=0.05, groove=0.025, panel_h=0.025, tags=tags)
        vx = sx * 0.345
        vfl = st["vent"]
        for k, t in enumerate((ha, hp)):
            if t is not None:
                B.cut(t, [B.box(f"hv_c{sx}{k}", vx, 0.20, 0.12, 0.30, -0.1, 0.8, K, bevel=0.0)])
        B.box(f"hv_bed{sx}", vx, 0.20, 0.12, 0.30, 0.03, 0.04, M["black"], bevel=0.0, tags=tags)
        for k in range(5):
            y = 0.08 + k * 0.06
            B.box(f"hv_l{sx}{k}", vx, y, 0.11, 0.022, 0.04, 0.27, KM, bevel=0.004, tags=tags)
            if vfl > 0 and k < 4:
                B.box(f"hv_f{sx}{k}", vx, y + 0.03, 0.09 if vfl > 0.5 else 0.06, 0.014, 0.10, 0.11,
                      X["flash"] if vfl > 0.5 else M["glow_dim"], bevel=0.0, tags=tags)
        # linha de painel diagonal no canto de cima de fora + parafusos
        if hp is not None:
            B.cut(hp, [B.rbox(f"hd_pl{sx}", sx * 0.41, 0.405, 0.02, 0.09, 0.27, 0.8, K, rot=sx * 45, bevel=0.0)])
        B.bolts(f"hd_b{sx}", [(sx * 0.43, -0.06), (sx * 0.255, 0.40)], 0.325, 0.014, S, tags=tags)
    ba, bp = B.shard("hood_b", BHOOD, 0.0, 0.31, A, slope=0.05, groove=0.025, panel_h=0.025, tags=tags)
    # boca do tunel de saida (labio claro por cima da fenda escura) e 3 setas para a saida
    _ledslot("hb_mouth", 0.0, -0.175, 0.22, 0.05, 0.02, 0, M, tags, [ba, bp], vertical=False)
    _ledslot("hb_arr", 0.0, -0.335, 0.30, 0.08, 0.12, 0, M, tags, [ba, bp], vertical=False)
    for k in range(3):
        _chevron(f"hb_chv{k}", -0.09 + k * 0.09, -0.335, 270, M, tags, z=0.128, s=0.45)
    if bp is not None:
        B.cut(bp, [B.rbox(f"hb_pl{sx}", sx * 0.36, -0.40, 0.02, 0.10, 0.27, 0.8, K, rot=sx * -45, bevel=0.0)
                   for sx in (-1, 1)])
    B.bolts("hb_b", [(-0.40, -0.23), (0.40, -0.23)], 0.335, 0.014, S, tags=tags)

    # garras que prendem a celula (abrem para soltar / receber)
    o = 0.07 * st["clamp"]
    for sx in (-1, 1):
        jaw = [(0.062 + o, CR_Y - 0.032), (0.21 + o, CR_Y - 0.062), (0.21 + o, CR_Y + 0.062), (0.062 + o, CR_Y + 0.032)]
        if sx < 0:
            jaw = Mo.mirror(jaw)
        B.plate(f"jaw{sx}", jaw, 0.06, 0.16, AM, slope=0.02, bevel=0.006, tags=tags)
        B.box(f"jawpad{sx}", sx * (0.072 + o), CR_Y, 0.02, 0.05, 0.06, 0.15, K, bevel=0.0, tags=tags)

    # celulas: a do berco (enchendo), a cheia saindo para o tunel e a vazia entrando pelo capuz direito
    lv = st["level"]
    if st["cell_y"] is not None:
        _mini_cell("cel", 0.0, st["cell_y"], M, tags, lv, int(round(lv * 4)))
    if st["out_y"] is not None:
        _mini_cell("celo", 0.0, st["out_y"], M, tags, 1.0, 4)
    if st["in_x"] is not None:
        _mini_cell("celi", st["in_x"], CR_Y, M, tags, 0.0, 0)

    # pescoco do injetor (sob o bloco de baixo do anel) e bico telescopico
    na, np_ = B.shard("neck", NECK, 0.06, 0.30, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
    _ledslot("neck_sl", 0.0, 0.565, 0.13, 0.04, 0.12, 3, M, tags, [na, np_], vertical=False,
             pip_mat=X["pl_hi"] if st["flow"] else M["glow_dim"], pw=0.02)
    yb = 0.40 - 0.10 * st["arm"]         # base do bico: 0.40 recolhido, 0.30 encaixado no terminal
    rod = 0.50 - (yb + 0.075)
    B.cyl("noz_rod", 0, yb + 0.075 + rod / 2, 0.20, 0.024, rod, S, axis="Y", verts=10, bevel=0.0, tags=tags)
    B.rbox("noz_head", 0, yb + 0.04, 0.10, 0.08, 0.13, 0.25, KM, chamfer=0.022, bevel=0.006, tags=tags)
    B.box("noz_slot", 0, yb + 0.045, 0.03, 0.05, 0.25, 0.255, M["black"], bevel=0.0, tags=tags)
    B.box("noz_jet", 0, yb + 0.045, 0.012, 0.04, 0.255, 0.26, X["pl_hi"] if st["flow"] else M["glow_dim"],
          bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"noz_ear{sx}", sx * 0.058, yb + 0.05, 0.02, 0.05, 0.13, 0.23, S, bevel=0.004, tags=tags)
    if st["contact"] or st["flow"]:
        # anel de contato no terminal (bico encaixado)
        B.box("noz_tip", 0, yb + 0.004, 0.07, 0.01, 0.16, 0.168, X["pl_hi"] if st["contact"] else X["pl_mid"],
              bevel=0.0, tags=tags)


def machine(M, T="machine", phase=0.0):
    """Maquinario (fileira de cima + tile central); transparente nos tiles de entrada e saida."""
    tags = (T,)
    X = _extra()
    st = _state(phase)
    K = M["core"]
    # leito escuro de toda a fileira de cima
    B.plate("mc_bed", B.rpoly(0, 0.975, 2.90, 0.90, 0, chamfer=0.08), 0.0, 0.05, K, slope=0.01, tags=tags)
    _ring(M, X, tags, st)
    _ducts(M, X, tags)
    _ionizer(M, X, tags, st)
    _coil(M, X, tags, st)
    _cradle(M, X, tags, st)


# ============================================================================ teto
def _inlay(name, poly, targets, z1, green, tags, gap=0.03):
    """Placa em seta embutida: abre um furo (contorno + vao) nas placas de base e assenta a seta no fundo escuro."""
    hole = B.offset_poly(poly, -gap)
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_h{k}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    return B.shard(name, poly, 0.0, z1, green, slope=0.05, groove=0.03, panel_h=0.018, tags=tags)


def roof(M, T="roof"):
    """Teto verde com o emblema do toro (sem pintura) sobre o anel, espinha do injetor e escotilha em capsula."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    B.box("rf_under", 0, 0, 3, 3, -0.05, 0.02, K, bevel=0.0, tags=tags)
    cx, cy = RC

    # ---- placas verdes de cada tile (as do tile de cima do meio e do centro ficam sob o emblema)
    for tx in range(3):
        for ty in range(3):
            px, py = tx - 1.0, 1.0 - ty
            if (tx, ty) == (1, 0):
                continue
            pa, pp = B.shard(f"rf{tx}{ty}", B.rpoly(px, py, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green,
                             slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
            if (tx, ty) in ((0, 0), (2, 0)):
                sx = -1 if tx == 0 else 1
                # placa de canto: respiro de persianas no canto de fora + lamina clara em diagonal para o anel
                rv = B.box(f"rf_sv{sx}", sx * 1.14, 1.20, 0.30, 0.26, 0.07, 0.125, KM, bevel=0.008, slope=0.012,
                           tags=tags)
                B.cut(rv, [B.box(f"rf_svc{sx}{k}", sx * 1.14, 1.11 + k * 0.06, 0.22, 0.026, 0.105, 0.3, K,
                                 bevel=0.0) for k in range(4)])
                blade = [(-1.36, 0.92), (-1.20, 0.92), (-0.64, 0.66), (-0.70, 0.60), (-1.36, 0.62)]
                bl = _flip(sx)(blade)
                B.plate(f"rf_blk{sx}", B.offset_poly(bl, -0.03), 0.06, 0.10, K, slope=0.01, tags=tags)
                ba, bp = B.shard(f"rf_bl{sx}", bl, 0.09, 0.20, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
                _ledslot(f"rf_bls{sx}", sx * 1.17, 0.74, 0.20, 0.05, 0.10, 3, M, tags, [ba, bp], vertical=False,
                         pw=0.026)
                if pp is not None:
                    B.cut(pp, [B.rbox(f"rf_cpl{sx}", sx * 0.70, 1.20, 0.022, 0.24, 0.04, 0.3, K, bevel=0.0)])
                B.bolts(f"rf_cb{sx}", [(sx * 1.36, 1.36), (sx * 0.64, 1.36)], 0.095, 0.016, S, tags=tags)
            elif ty == 1 and tx != 1:
                sx = -1 if tx == 0 else 1
                # entradas: placa em seta embutida apontando para cima (o insumo sobe para a casca de cima)
                arrow = [(px - 0.24, -0.30), (px + 0.24, -0.30), (px + 0.24, 0.08), (px, 0.32), (px - 0.24, 0.08)]
                aa, ap = _inlay(f"rf_arr{sx}", arrow, (pa, pp), 0.13, green, tags)
                _ledslot(f"rf_ap{sx}", px, -0.10, 0.075, 0.24, 0.02, 3, M, tags, [aa, ap], pw=0.032)
                B.bolts(f"rf_mb{sx}", [(px + dx, dy) for dx in (-0.37, 0.37) for dy in (-0.37, 0.37)], 0.095, 0.016, S,
                        tags=tags)
            elif ty == 2:
                if tx == 1:
                    arrow = [(-0.28, -0.66), (0.28, -0.66), (0.28, -1.02), (0.0, -1.28), (-0.28, -1.02)]
                    aa, ap = _inlay("rf_barr", arrow, (pa, pp), 0.14, green, tags)
                    _ledslot("rf_bpips", 0.0, -0.84, 0.27, 0.075, 0.02, 3, M, tags, [aa, ap], vertical=False,
                             pw=0.032)
                else:
                    sx = -1 if tx == 0 else 1
                    B.cut(pp, [B.rbox(f"rf_bl{tx}a", px, -0.80, 0.62, 0.022, 0.04, 0.3, K, bevel=0.0),
                               B.rbox(f"rf_bl{tx}c", px - sx * 0.22, -1.24, 0.022, 0.26, 0.04, 0.3, K,
                                      rot=sx * 45, bevel=0.0)])
                    rv = B.box(f"rf_bv{tx}", px + sx * 0.08, -1.02, 0.30, 0.24, 0.07, 0.125, KM, bevel=0.008,
                               slope=0.012, tags=tags)
                    B.cut(rv, [B.box(f"rf_bvc{tx}{k}", px + sx * 0.08, -1.10 + k * 0.055, 0.22, 0.024, 0.105, 0.3, K,
                                     bevel=0.0) for k in range(4)])
                    B.bolts(f"rf_bb{tx}", [(px - 0.36, -1.36), (px + 0.36, -1.36), (px - sx * 0.36, -0.66)], 0.095,
                            0.016, S, tags=tags)

    # ---- emblema do toro (tile de cima do meio): base octogonal escura, 6 segmentos claros com vaos e fenda
    # anelar ciano fina, cubo com tampa; placa verde por baixo (cantos do tile)
    pa, pp = B.shard("rf10", B.rpoly(0, 1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green, slope=0.03, groove=0.05,
                     panel_h=0.022, tags=tags)
    hole = _octo(cx, cy, 0.47)
    B.cut(pa, [B.loft("rf_emb_h", hole, hole, -0.01, 0.5, K, bevel=0.0)])
    if pp is not None:
        B.cut(pp, [B.loft("rf_emb_h2", hole, hole, -0.01, 0.5, K, bevel=0.0)])
    B.plate("em_base", _octo(cx, cy, 0.455), 0.02, 0.11, K, slope=0.02, tags=tags)
    for k in range(6):
        a = 30 + 60 * k
        sa, sp = B.shard(f"em_seg{k}", _sector(cx, cy, 0.215, 0.43, a, 25.0, c=0.035), 0.09, 0.22, A, slope=0.035,
                         groove=0.018, panel_h=0.02, tags=tags)
        if sp is not None:
            p0 = _pol(cx, cy, 0.335, a)
            B.cut(sp, [B.rbox(f"em_gr{k}", p0[0], p0[1], 0.014, 0.12, 0.20, 0.6, K, rot=a - 90, bevel=0.0)])
        B.bolts(f"em_b{k}", [_pol(cx, cy, 0.385, a + 15)], 0.245, 0.014, S, tags=tags)
    # fenda anelar com o anel de plasma fino (o toro)
    B.torus("em_glow", cx, cy, 0.105, 0.195, 0.008, X["pl_mid"], tags=tags)
    B.plate("em_hub", _octo(cx, cy, 0.15), 0.09, 0.19, AM, slope=0.025, tags=tags)
    B.plate("em_hub2", _octo(cx, cy, 0.085, 0), 0.19, 0.23, S, slope=0.012, tags=tags)
    B.bolts("em_hb", B.ring_points(cx, cy, 0.118, 6, math.radians(30)), 0.195, 0.012, S, tags=tags)
    B.cyl("em_eye", cx, cy, 0.232, 0.025, 0.006, M["glow_dim"], axis="Z", verts=8, bevel=0.0, tags=tags)

    # ---- espinha do injetor: do anel ate a escotilha do berco, com 3 pips
    spine = [(-0.12, 0.62), (0.12, 0.62), (0.12, 0.46), (0.07, 0.40), (-0.07, 0.40), (-0.12, 0.46)]
    sa, sp = B.shard("sp", spine, 0.06, 0.22, A, slope=0.035, groove=0.018, panel_h=0.02, tags=tags)
    _ledslot("sp_sl", 0.0, 0.52, 0.05, 0.16, 0.10, 3, M, tags, [sa, sp], pw=0.024)

    # ---- escotilha em capsula sobre o berco (tile central): placa verde em volta + capsula clara com a janela
    # de 4 pips (a celula), garras escuras dos lados e trincos de aco
    ca, cp = B.shard("rf11", B.rpoly(0, 0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green, slope=0.03, groove=0.05,
                     panel_h=0.022, tags=tags)
    cap = [(-0.10, -0.40), (0.10, -0.40), (0.20, -0.30), (0.20, 0.30), (0.10, 0.40), (-0.10, 0.40), (-0.20, 0.30),
           (-0.20, -0.30)]
    for sx in (-1, 1):
        clamp = [(0.23, -0.20), (0.36, -0.28), (0.40, -0.24), (0.40, 0.24), (0.36, 0.28), (0.23, 0.20)]
        cl = clamp if sx > 0 else Mo.mirror(clamp)
        B.plate(f"hc_cl{sx}", B.offset_poly(cl, -0.025), 0.06, 0.10, K, slope=0.01, tags=tags)
        B.shard(f"hc_clamp{sx}", cl, 0.09, 0.17, AM, slope=0.03, groove=0.015, panel_h=0.015, tags=tags)
        B.bolts(f"hc_cb{sx}", [(sx * 0.33, -0.16), (sx * 0.33, 0.16)], 0.19, 0.014, S, tags=tags)
    B.plate("hc_core", B.offset_poly(cap, -0.03), 0.06, 0.12, K, slope=0.012, tags=tags)
    ha, hp = B.shard("hc", cap, 0.10, 0.24, A, slope=0.045, groove=0.022, panel_h=0.025, tags=tags)
    _ledslot("hc_win", 0.0, 0.0, 0.07, 0.36, 0.12, 4, M, tags, [ha, hp], pw=0.034)
    for sy in (-1, 1):
        B.box(f"hc_band{sy}", 0, sy * 0.235, 0.44, 0.045, 0.10, 0.215, S, bevel=0.008, tags=tags)

    # o verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nas bordas claras)
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False
