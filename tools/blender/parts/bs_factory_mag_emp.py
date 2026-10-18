"""Carregadora de Carregadores EMP (EMP Magazine Charger) 3x3 - carrega Carregadores Padrao com pulso EMP.

Layout vanilla factory_he (tools/bsgen/factory.py): fileira de cima + tile central = maquinario (bloqueado);
entradas no meio das laterais: tile (0,1) esquerda = Carregador Padrao, tile (2,1) direita = cobre; saida =
fileira de baixo inteira. O jogo desenha as pilhas de recursos nesses 5 tiles, entao eles ficam livres de
maquinario e o piso mostra bases escuras marcadas (cantoneiras cinza, labio fino, setas azuis em recesso).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 tile.

E uma CARREGADORA, nao uma prensa (mesma familia das armas: cascas claras chanfradas com bisel duplo sobre
nucleo escuro, LEDs em recessos, linhas de painel):
  * fileira de cima = banco de capacitores: nos tiles das pontas, carcacas claras com janela em degrau e 4
    capacitores altos em cada (tampa de aluminio com ranhura de alivio em Y, capa azul, borne), coluna de 5
    LEDs azuis de nivel; no tile do meio, o capacitor principal (maior) num poco escuro entre duas bochechas
    em garra, medidor de carga de 5 pips e a boca do alimentador que desce para o berco;
  * barramentos de cobre (barras chatas com parafusos) nos vaos escuros ligando os bancos ao principal e cabos
    de potencia descendo das bochechas ate as bobinas;
  * tile central = estacao de carga: canal vertical (alimentador em cima -> saida embaixo) com o berco claro no
    meio; duas cabecas de bobina (casca clara em cunha, janela escura com as espiras de cobre, polo de aco)
    correm em trilhos e apertam o carregador deitado (pinos para a direita) pelos dois lados;
Animacao (10 quadros, 0,1 s): 0 repouso (Carregador Padrao no berco, bobinas abertas, nivel 1 = sprite
desligado), 1-2 as bobinas fecham e o nivel sobe, 3 nivel cheio (pulso descendo pelos cabos), 4-5 descarga:
arcos azuis curtos e quebrados entre os polos e o carregador, que brilha azul (vira Carregador EMP no
lampejo) e os niveis caem, 6 brilho residual, 7 as bobinas abrem, 8 o Carregador EMP desce para a saida,
9 o proximo Carregador Padrao desce do alimentador.
Teto: placas verdes (pintura) com a galeria de capacitores sem pintura (3 tampas em colares octogonais claros
ligadas por uma ponte com 5 pips azuis), emblema de raio em 3 laminas claras no tile central e setas pintadas
das entradas e da saida com pips azuis.
"""

import math
import random

import bs3d as B
import models as Mo
from parts import bs_mag_emp as EMP
from parts import bs_mag_std as STD

PART = {
    "id": "rafaeltessaro.bs_factory_mag_emp",
    "kind": "factory",
    "size": [3, 3],
    "accent": "blue",
    "machine_frames": 10,
    "machine_interval": 0.1,
}

NF = PART["machine_frames"]
CY = -0.02                 # centro do berco (tile central)
MAG_S = 0.30               # escala do carregador no berco (deitado, pinos para +X: 0.31 x 0.22)
TIP_C, TIP_O = 0.205, 0.255    # |x| da ponta do polo com a bobina fechada / aberta
LANE = 0.175               # meia largura do canal vertical do berco
BANK_X = 1.05              # |x| do centro do banco de capacitores das pontas
BANK_Y = 1.08              # y do centro do banco


# ============================================================================ utilidades
def _extra():
    """Materiais desta fabrica (os da linha EMP vem de parts/bs_mag_emp.py: mesmo nome = mesmo material)."""
    X = EMP.mats()
    X.update({
        # capa azul dos capacitores (pintura sem desgaste: malha pequena clareia inteira com wear)
        "sleeve": B.mat_paint("cap_sleeve", (0.05, 0.13, 0.42), rough=0.35, metal=0.2, wear=0.0, grime=0.02,
                              scale=5),
        "alu": B.mat_metal("cap_alu", (0.60, 0.62, 0.66), rough=0.30, metal=1.0),
        # arco: nucleo branco-azulado fino (estoura em branco frio, halo azul pequeno)
        "arc": B.mat_glow("emp_arc", (0.55, 0.78, 1.0), 2.4),
        "cell_hot": B.mat_glow("emp_cell_hot", (0.30, 0.58, 1.0), 1.8),
        # LEDs ambar do Carregador Padrao no berco (antes da carga)
        "amber": B.mat_glow("std_amber", Mo.AMBER, 9.0),
        "led_off": B.mat_metal("emp_led_off", (0.015, 0.03, 0.07), rough=0.4, metal=0.3),
    })
    return X


def _rot(pts, ang, cx=0.0, cy=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def _octo(cx, cy, r, a0=22.5):
    return [(cx + r * math.cos(math.radians(a0 + 45 * i)), cy + r * math.sin(math.radians(a0 + 45 * i)))
            for i in range(8)]


def _flip(sx):
    """Poligono do lado esquerdo -> lado sx (espelho em x para o lado direito)."""
    return (lambda p: p) if sx < 0 else Mo.mirror


def _state(phase):
    """Estado do ciclo: quadro, fechamento das bobinas (0..1), nivel dos capacitores (0..5), arco (None/0/1),
    brilho do carregador (0..1), (tipo, deslize em y) do carregador e pulso nos cabos (0 = apagado, 1..3)."""
    i = int(round(phase * NF)) % NF
    clamp = [0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 0.45, 0.0, 0.0][i]
    level = [1, 2, 3, 4, 5, 2, 0, 0, 0, 1][i]
    arc = [None, None, None, None, 0, 1, None, None, None, None][i]
    glow = [0.0, 0.0, 0.0, 0.0, 0.55, 1.0, 0.5, 0.2, 0.0, 0.0][i]
    mag = [("std", 0.0)] * 5 + [("emp", 0.0)] * 3 + [("emp", -0.13), ("std", 0.13)]
    pulse = [0, 0, 0, 1, 2, 0, 0, 0, 0, 0][i]
    return i, clamp, level, arc, glow, mag[i], pulse


def _chevron(name, cx, cy, ang, mat, tags, z=0.03, s=1.0):
    """Seta de fluxo (chevron) apontando para ang (graus)."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    B.loft(name, _rot(pts, ang, cx, cy), _rot(pts, ang, cx, cy), z, z + 0.006, mat, bevel=0.0, tags=tags)


def _ledslot(name, cx, cy, sx, sy, z_bed, n, M, tags, targets, vertical=True, pip_mats=None, pw=None):
    """Fenda de LEDs VAZADA nas pecas (o bisel reaplicado nao cria filete que tampe o leito) com leito preto e
    n pips em cima de z_bed; pip_mats = material de cada pip (lista) ou um so material."""
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{k}", cx, cy, sx, sy, z_bed - 0.02, z_bed + 0.8, M["black"], bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, z_bed, z_bed + 0.008, M["black"], bevel=0.0, tags=tags)
    L = sy if vertical else sx
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        px, py = (cx, cy + t * L) if vertical else (cx + t * L, cy)
        a, b = ((pw or sx * 0.55, L / n * 0.55) if vertical else (L / n * 0.55, pw or sy * 0.55))
        mat = pip_mats[i] if isinstance(pip_mats, (list, tuple)) else pip_mats
        B.box(f"{name}_pip{i}", px, py, a, b, z_bed + 0.008, z_bed + 0.02, mat, bevel=0.0, tags=tags)


def _levels(n, lit, X):
    """Materiais de uma coluna de n pips com 'lit' acesos (de baixo para cima)."""
    return [X["led"] if i < lit else X["led_off"] for i in range(n)]


def _bezel(prefix, poly_out, poly_in, z0, z1, M, tags, targets):
    """Janela com moldura em degrau: abre poly_out nas pecas e assenta um labio de aco (poly_out - poly_in)."""
    K, S = M["core"], M["steel"]
    for k, t in enumerate(targets):
        B.cut(t, [B.loft(f"{prefix}_c{k}", poly_out, poly_out, z0, 0.9, K, bevel=0.0)])
    lip = B.plate(prefix + "_lip", poly_out, z1 - 0.06, z1, S, slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft(prefix + "_lc", poly_in, poly_in, z1 - 0.2, z1 + 0.2, K, bevel=0.0)])
    B.loft(prefix + "_bed", poly_out, poly_out, z0 - 0.02, z0, M["black"], bevel=0.0, tags=tags)


def _can(name, x, y, r, z0, z1, M, X, tags, vent=True):
    """Capacitor alto visto de cima: corpo escuro, capa azul aparecendo em anel, tampa de aluminio com ranhura
    de alivio em Y (3 riscos escuros) e borne central."""
    B.cyl(name + "_body", x, y, (z0 + z1) / 2 - 0.03, r * 0.96, z1 - z0 - 0.06, M["core_mid"], axis="Z", verts=24,
          bevel=0.0, tags=tags)
    B.cyl(name + "_sl", x, y, z1 - 0.045, r, 0.07, X["sleeve"], axis="Z", verts=24, bevel=0.004, tags=tags)
    B.cyl(name + "_top", x, y, z1 + 0.0, r * 0.84, 0.03, X["alu"], axis="Z", verts=24, bevel=0.006, tags=tags)
    if vent:
        for k in range(3):
            a = 90 + 120 * k
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            B.rbox(f"{name}_v{k}", x + ca * r * 0.36, y + sa * r * 0.36, r * 0.62, 0.012, z1 + 0.014, z1 + 0.018,
                   M["black"], rot=a, bevel=0.0, tags=tags)
    B.cyl(name + "_term", x, y, z1 + 0.022, r * 0.22, 0.02, M["steel"], axis="Z", verts=8, bevel=0.004, tags=tags)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso opaco: leito escuro do maquinario + bases escuras e discretas das entradas e da saida."""
    tags = (T,)
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    X = _extra()
    dim = X["led_dim"]
    B.box("fl_base", 0, 0, 3, 3, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(3):
        for ty in range(3):
            cx, cy = tx - 1.0, 1.0 - ty
            p = B.plate(f"fl{tx}{ty}", B.rpoly(cx, cy, 0.94, 0.94, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.012,
                        tags=tags)
            if ty == 0 or (tx, ty) == (1, 1):
                # leito do maquinario: grade de fendas escuras
                B.cut(p, [B.box(f"flg{tx}{ty}{i}", cx, cy - 0.3 + i * 0.15, 0.7, 0.04, 0.015, 0.1, K, bevel=0.0)
                          for i in range(5)])
    # trilho da saida: moldura escura unica sob as 3 bases
    B.plate("out_rail", B.rpoly(0, -1.0, 2.86, 0.88, 0, chamfer=0.1), 0.03, 0.045, K, slope=0.01, tags=tags)
    # bases: (nome, centro, lado da seta, angulo da seta): carregador -> berco (leste), cobre -> bobina direita
    # (oeste), berco -> saida do meio (para baixo)
    pads = (("in0", -1.0, 0.0, "e", 0), ("in1", 1.0, 0.0, "w", 180), ("out0", -1.0, -1.0, None, None),
            ("out1", 0.0, -1.0, "n", 270), ("out2", 1.0, -1.0, None, None))
    for name, cx, cy, side, ang in pads:
        fr = B.plate(f"pad_{name}", B.rpoly(cx, cy, 0.86, 0.86, 0, chamfer=0.10), 0.03, 0.062, KM, slope=0.016,
                     tags=tags)
        hole = B.rpoly(cx, cy, 0.70, 0.70, 0, chamfer=0.07)
        cuts = [B.loft(f"pad_h{name}", hole, hole, 0.02, 0.3, K, bevel=0.0)]
        if side:
            # recesso escuro atravessando a moldura para a seta (LED fora da blindagem clara)
            ex, ey = {"e": (cx + 0.39, cy), "w": (cx - 0.39, cy), "n": (cx, cy + 0.39)}[side]
            sx_, sy_ = (0.14, 0.30) if side in ("e", "w") else (0.30, 0.14)
            cuts.append(B.box(f"pad_n{name}", ex, ey, sx_, sy_, 0.042, 0.3, K, bevel=0.0))
            B.box(f"pad_nb{name}", ex, ey, sx_ - 0.02 if side == "n" else 0.10, sy_ - 0.02 if side != "n" else 0.10,
                  0.036, 0.043, M["black"], bevel=0.0, tags=tags)
            if name == "in1":
                # cobre: seta para a bobina + tracinho de cobre (fio) no mesmo recesso escuro
                _chevron("chv_" + name, ex + 0.03, ey, ang, dim, tags, z=0.043, s=0.62)
                B.box("fl_cu", ex - 0.045, ey, 0.016, 0.07, 0.043, 0.052, X["copper"], bevel=0.0, tags=tags)
            else:
                _chevron("chv_" + name, ex, ey, ang, dim, tags, z=0.043, s=0.62)
        B.cut(fr, cuts)
        # labio fino claro na borda do poco (marca a base sem pesar)
        lip = B.plate(f"padlip_{name}", B.rpoly(cx, cy, 0.73, 0.73, 0, chamfer=0.075), 0.035, 0.056, AM,
                      slope=0.005, bevel=0.004, tags=tags)
        inner = B.rpoly(cx, cy, 0.69, 0.69, 0, chamfer=0.066)
        B.cut(lip, [B.loft(f"padlip_h{name}", inner, inner, 0.02, 0.3, K, bevel=0.0)])
        B.loft(f"padwell_{name}", inner, inner, 0.03, 0.04, K, bevel=0.0, tags=tags)
        B.box(f"padgv_{name}", cx, cy, 0.012, 0.58, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        B.box(f"padgh_{name}", cx, cy, 0.58, 0.012, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.325, cy + qy * 0.325
                poly = [(ox, oy), (ox - qx * 0.16, oy), (ox - qx * 0.16, oy - qy * 0.045),
                        (ox - qx * 0.045, oy - qy * 0.045), (ox - qx * 0.045, oy - qy * 0.16), (ox, oy - qy * 0.16)]
                B.plate(f"padbr_{name}{qx}{qy}", poly, 0.04, 0.058, AM, slope=0.008, bevel=0.004, tags=tags)
        pts = [(cx + 0.39 * dx, cy + 0.39 * dy) for dx, dy, sd in ((1, 0, "e"), (-1, 0, "w"), (0, 1, "n"),
                                                                    (0, -1, "s")) if sd != side]
        B.bolts(f"pbolt_{name}", pts, 0.066, 0.014, S, tags=tags)


# ============================================================================ maquina
def _mini(name, kind, x, y, z, M, X, tags, hot=False):
    """Carregador no berco (o proprio modelo do recurso em miniatura), deitado com a frente para +X.
    kind 'std' = Carregador Padrao (LEDs ambar), 'emp' = Carregador EMP (hot: celula acesa forte)."""
    sc = B.bpy.context.scene
    before = set(o.name for o in sc.objects)
    if kind == "std":
        M2 = dict(M)
        M2["glow"] = X["amber"]
        STD.item(M2, tags[0])
    else:
        EMP.item(M, tags[0])
    new = [o for o in sc.objects if o.name not in before]
    emp = B.bpy.data.objects.new(name, None)
    sc.collection.objects.link(emp)
    for o in new:
        if o.parent is None:
            o.parent = emp
        if hot and o.name.split(".")[0] == "emp_cell":
            o.data.materials[0] = X["cell_hot"]
    emp.location = (x, y, z)
    emp.scale = (MAG_S, MAG_S, MAG_S)
    emp.rotation_euler.z = math.radians(-90)
    return emp


def _arc(name, x0, y0, x1, y1, seed, z, mat, tags, amp=0.016, n=4):
    """Arco eletrico curto: linha quebrada de n trechos finos entre (x0,y0) e (x1,y1), com um galho curto."""
    rnd = random.Random(seed)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    pts = [(x0, y0)]
    for k in range(1, n):
        t = k / n
        o = rnd.uniform(-amp, amp) * (1 if k % 2 else -1)
        pts.append((x0 + dx * t + nx * o, y0 + dy * t + ny * o))
    pts.append((x1, y1))
    for k in range(n):
        (ax, ay), (bx, by) = pts[k], pts[k + 1]
        ln = math.hypot(bx - ax, by - ay)
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        B.rbox(f"{name}_s{k}", (ax + bx) / 2, (ay + by) / 2, ln + 0.006, 0.010, z, z + 0.006, mat, rot=ang,
               bevel=0.0, tags=tags)
    # galho curto saindo do meio
    mx, my = pts[n // 2]
    ga = math.degrees(math.atan2(dy, dx)) + rnd.choice((-1, 1)) * rnd.uniform(40, 65)
    gl = L * 0.35
    B.rbox(f"{name}_g", mx + math.cos(math.radians(ga)) * gl / 2, my + math.sin(math.radians(ga)) * gl / 2, gl, 0.008,
           z, z + 0.006, mat, rot=ga, bevel=0.0, tags=tags)


def _station(M, X, tags, clamp, arc, glow, mag, pulse):
    """Estacao de carga no tile central: canal, berco, bobinas nos trilhos, carregador, arcos e brilho."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # bloco de maquina do tile central
    B.plate("st_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.04, K, slope=0.015, tags=tags)
    # canal vertical (alimentador em cima -> saida embaixo) com guias de aco
    B.box("st_lane", 0, 0, 2 * LANE, 0.98, 0.035, 0.05, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"st_guide{sx}", sx * (LANE + 0.012), 0.0, 0.022, 0.98, 0.035, 0.085, S, bevel=0.005, tags=tags)
    # trilhos das bobinas (aparecem quando as cabecas abrem)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box(f"st_rail{sx}{sy}", sx * 0.34, CY + sy * 0.12, 0.30, 0.025, 0.04, 0.075, S, bevel=0.005,
                  tags=tags)
    # berco claro (bisel duplo) com leito escuro na forma do carregador
    cradle = B.rpoly(0, CY, 0.36, 0.30, 0, chamfer=0.05)
    ca, cp = B.shard("st_cradle", cradle, 0.05, 0.11, A, slope=0.02, groove=0.012, panel_h=0.012, tags=tags)
    bed = B.rpoly(0, CY, 0.30, 0.22, 0, chamfer=0.02)
    for t, k in ((ca, "a"), (cp, "b")):
        if t is not None:
            B.cut(t, [B.loft(f"st_bedc{k}", bed, bed, 0.09, 0.5, K, bevel=0.0)])
    B.loft("st_bed", bed, bed, 0.085, 0.092, M["black"], bevel=0.0, tags=tags)
    # carregador no berco (deitado, pinos para a direita)
    kind, dy = mag
    if glow > 0:
        # brilho azul em volta do carregador (aro fino acima do leito: so a borda aparece)
        rim = B.mat_glow(f"emp_rim{int(glow * 100)}", (0.15, 0.40, 1.0), 1.4 * glow)
        B.loft("st_rim", B.rpoly(0, CY + dy, 0.345, 0.255, 0, chamfer=0.04),
               B.rpoly(0, CY + dy, 0.345, 0.255, 0, chamfer=0.04), 0.092, 0.098, rim, bevel=0.0, tags=tags)
    _mini("st_mag", kind, 0.0, CY + dy, 0.095, M, X, tags, hot=glow >= 0.9)

    # cabecas de bobina (esquerda e direita): carro escuro nos trilhos, casca clara em cunha com janela das
    # espiras de cobre, polo de aco apontando para o carregador, cabo de potencia saindo para cima
    tip = TIP_O - (TIP_O - TIP_C) * clamp
    xi = tip + 0.045          # face de dentro da casca
    xo = xi + 0.205           # face de fora
    for sx in (-1, 1):
        f = _flip(sx)
        B.box(f"cl_car{sx}", sx * (xi + xo) / 2 + sx * 0.01, CY, xo - xi, 0.30, 0.04, 0.10, KM, bevel=0.01,
              tags=tags)
        shell = [(-xo, CY - 0.165), (-xi - 0.06, CY - 0.165), (-xi, CY - 0.10), (-xi, CY + 0.10),
                 (-xi - 0.06, CY + 0.165), (-xo, CY + 0.165)]
        ha, hp = B.shard(f"cl_shell{sx}", f(shell), 0.08, 0.36, A, slope=0.045, groove=0.022, panel_h=0.025,
                         tags=tags)
        wx0, wx1 = xi + 0.05, xo - 0.035
        win = B.rpoly(sx * (wx0 + wx1) / 2, CY, wx1 - wx0, 0.20, 0, chamfer=0.02)
        for t, k in ((ha, "a"), (hp, "b")):
            if t is not None:
                B.cut(t, [B.loft(f"cl_win{sx}{k}", win, win, 0.16, 0.9, K, bevel=0.0)])
        B.loft(f"cl_wbed{sx}", win, win, 0.15, 0.16, M["black"], bevel=0.0, tags=tags)
        # espiras de cobre no tambor escuro (eixo X, apontando para o carregador)
        cx_ = sx * (wx0 + wx1) / 2
        B.cyl(f"cl_drum{sx}", cx_, CY, 0.22, 0.075, wx1 - wx0 - 0.01, KM, axis="X", verts=16, bevel=0.0, tags=tags)
        nturn = 5
        pitch = (wx1 - wx0 - 0.02) / nturn
        for k in range(nturn):
            x = sx * (wx0 + 0.01 + pitch * (k + 0.5))
            B.cyl(f"cl_turn{sx}{k}", x, CY, 0.22, 0.088, pitch * 0.78, X["copper"], axis="X", verts=16, bevel=0.0,
                  tags=tags)
        # polo de aco (octogono) com colar isolante escuro e ponta chanfrada
        B.cyl(f"cl_col{sx}", sx * (xi + 0.008), CY, 0.24, 0.062, 0.03, KM, axis="X", verts=8, bevel=0.004,
              tags=tags)
        B.cyl(f"cl_pole{sx}", sx * (xi - 0.012), CY, 0.24, 0.045, 0.03, S, axis="X", verts=8, bevel=0.004, tags=tags)
        # cone da ponta (raio 1 fica em -X, raio 2 em +X): o lado fino aponta para o carregador
        r1, r2 = (0.028, 0.045) if sx > 0 else (0.045, 0.028)
        B.cyl(f"cl_tipc{sx}", sx * (tip + 0.008), CY, 0.24, r1, 0.016, X["silver"], axis="X", verts=8, bevel=0.0,
              tags=tags, r2=r2)
        # parafusos e cabo de potencia (sai do canto de fora, sobe ate a fileira de cima)
        B.bolts(f"cl_b{sx}", [(sx * (xo - 0.022), CY + 0.13), (sx * (xo - 0.022), CY - 0.13)], 0.385, 0.014, S,
                tags=tags)
        kx = sx * (xo - 0.06)
        B.cyl(f"cl_cable{sx}", kx, (CY + 0.15 + 0.52) / 2, 0.30, 0.032, 0.52 - CY - 0.15, KM, axis="Y", verts=10,
              bevel=0.0, tags=tags)
        for k, y in enumerate((CY + 0.20, 0.42)):
            B.cyl(f"cl_cclamp{sx}{k}", kx, y, 0.30, 0.04, 0.025, S, axis="Y", verts=8, bevel=0.004, tags=tags)
        if pulse:
            # pulso descendo pelo cabo: anel azul aceso
            py = 0.40 if pulse == 1 else CY + 0.26
            B.cyl(f"cl_pulse{sx}", kx, py, 0.30, 0.036, 0.03, X["led"], axis="Y", verts=10, bevel=0.0, tags=tags)
    # arcos azuis curtos entre os polos e as pontas do carregador
    if arc is not None:
        mx = 0.155 * MAG_S / 0.30
        for sx in (-1, 1):
            for j, oy in enumerate((-0.03, 0.035)):
                _arc(f"arc{sx}{j}", sx * TIP_C, CY + oy * 0.4, sx * mx, CY + oy, 11 + 7 * arc + 3 * j + sx, 0.30,
                     X["arc"], tags)
    # tampa da saida (labio de aco e setas azuis na borda de baixo do canal)
    B.box("st_outlip", 0, -0.445, 2 * LANE + 0.06, 0.05, 0.035, 0.15, KM, bevel=0.01, tags=tags)
    B.box("st_outlip2", 0, -0.425, 2 * LANE + 0.02, 0.012, 0.15, 0.158, S, bevel=0.0, tags=tags)
    for k, x in enumerate((-0.07, 0.0, 0.07)):
        _chevron(f"st_outchv{k}", x, -0.465, 270, X["led_dim"], tags, z=0.15, s=0.32)


def _bank(sx, level, M, X, tags):
    """Banco de capacitores de um tile de ponta: carcaca clara com janela em degrau e 4 capacitores altos,
    coluna de 5 LEDs de nivel na borda de dentro, lamina embaixo com barramento de cobre."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    f = _flip(sx)
    house = [(-1.42, 1.30), (-1.30, 1.42), (-0.60, 1.42), (-0.60, 0.87), (-0.71, 0.76), (-1.30, 0.76),
             (-1.42, 0.88)]
    ha, hp = B.shard(f"bk_house{sx}", f(house), 0.0, 0.46, A, slope=0.07, groove=0.035, panel_h=0.03, tags=tags)
    win = [(-1.32, 0.86), (-0.94, 0.86), (-0.88, 0.92), (-0.88, 1.32), (-1.32, 1.32)]
    win_in = B.offset_poly(win, 0.024)
    _bezel(f"bk_win{sx}", f(win), f(win_in), 0.28, 0.46, M, tags, (ha, hp))
    for k, (cx, cy) in enumerate(((-1.21, 1.205), (-0.99, 1.205), (-1.21, 0.975), (-0.99, 0.975))):
        _can(f"bk_can{sx}{k}", cx if sx < 0 else -cx, cy, 0.10, 0.26, 0.49, M, X, tags)
    # coluna de nivel (5 pips azuis acesos de baixo para cima) entre a janela e a borda de dentro
    _ledslot(f"bk_lv{sx}", sx * 0.79, 1.10, 0.045, 0.40, 0.40, 5, M, tags, [ha, hp], pip_mats=_levels(5, level, X),
             pw=0.024)
    # linha de painel diagonal no chanfro de baixo + parafusos
    B.cut(hp, [B.rbox(f"bk_pl{sx}", sx * 0.74, 0.86, 0.022, 0.11, 0.42, 0.8, K, rot=sx * 45, bevel=0.0)])
    B.bolts(f"bk_bolt{sx}", [(sx * 1.36, 1.24), (sx * 0.68, 1.36)], 0.49, 0.017, S, tags=tags)
    # lamina embaixo, apontando para a estacao, com fenda de luz fraca
    blade = [(-1.42, 0.705), (-0.78, 0.705), (-0.56, 0.62), (-0.60, 0.535), (-1.30, 0.535), (-1.42, 0.60)]
    ba, bp = B.shard(f"bk_blade{sx}", f(blade), 0.0, 0.30, A, slope=0.035, groove=0.018, panel_h=0.02, tags=tags)
    _ledslot(f"bk_bsl{sx}", sx * 1.02, 0.62, 0.30, 0.04, 0.24, 4, M, tags, [ba, bp], vertical=False,
             pip_mats=X["led_dim"], pw=0.02)


def _busbar(name, x0, x1, y, z, M, X, tags, w=0.05):
    """Barramento de cobre chato com parafusos de aco nas pontas, sobre suportes escuros."""
    L = abs(x1 - x0)
    cx = (x0 + x1) / 2
    for k, x in enumerate((x0, x1)):
        B.box(f"{name}_sup{k}", x, y, 0.07, w + 0.03, 0.02, z, M["core_mid"], bevel=0.006, tags=tags)
    B.box(name, cx, y, L, w, z, z + 0.025, X["copper"], bevel=0.006, tags=tags)
    B.bolts(f"{name}_b", [(x0, y), (x1, y)], z + 0.03, 0.014, M["steel"], tags=tags)


def _main(M, X, tags, level, pulse):
    """Tile de cima do meio: capacitor principal num poco escuro entre duas bochechas em garra, medidor de carga
    de 5 pips e a boca do alimentador que desce para o berco."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # leito escuro de toda a fileira de cima
    B.plate("mc_bed", B.rpoly(0, 0.98, 2.90, 0.92, 0, chamfer=0.08), 0.0, 0.05, K, slope=0.01, tags=tags)
    # bochechas em garra: descem dos cantos de cima e terminam em ponta sobre os cabos das bobinas
    cheek = [(-0.22, 1.31), (-0.44, 1.31), (-0.50, 1.25), (-0.50, 0.78), (-0.42, 0.56), (-0.30, 0.50),
             (-0.27, 0.62), (-0.29, 0.86), (-0.22, 0.93)]
    for sx in (-1, 1):
        ca, cp = B.shard(f"cheek{sx}", _flip(sx)(cheek), 0.0, 0.50, A, slope=0.07, groove=0.035, panel_h=0.03,
                         tags=tags)
        _ledslot(f"ck_sl{sx}", sx * 0.395, 1.04, 0.045, 0.30, 0.42, 4, M, tags, [ca, cp], pip_mats=X["led_dim"],
                 pw=0.026)
        B.cut(cp, [B.rbox(f"ck_pl{sx}", sx * 0.39, 0.70, 0.022, 0.20, 0.47, 0.8, K, rot=sx * -20, bevel=0.0)])
        B.bolts(f"ck_b{sx}", [(sx * 0.40, 1.24)], 0.53, 0.017, S, tags=tags)
    # poco do capacitor principal e o capacitor (maior que os dos bancos)
    B.plate("mn_well", _octo(0, 1.10, 0.215), 0.03, 0.10, KM, slope=0.02, tags=tags)
    _can("mn_can", 0.0, 1.10, 0.17, 0.10, 0.56, M, X, tags)
    # medidor de carga principal: 5 pips azuis numa fenda escura sob o capacitor
    mb = B.box("mn_meterbase", 0, 0.81, 0.34, 0.10, 0.03, 0.30, AM, bevel=0.012, tags=tags)
    _ledslot("mn_meter", 0, 0.81, 0.26, 0.045, 0.27, 5, M, tags, [mb], vertical=False,
             pip_mats=_levels(5, level, X), pw=0.022)
    # boca do alimentador: o Carregador Padrao desce dela para o berco (labio de aco, setas azuis)
    B.box("mn_feed", 0, 0.62, 2 * LANE + 0.06, 0.14, 0.03, 0.20, KM, bevel=0.012, tags=tags)
    B.box("mn_feedm", 0, 0.585, 2 * LANE - 0.01, 0.06, 0.18, 0.21, M["black"], bevel=0.0, tags=tags)
    for k, x in enumerate((-0.07, 0.0, 0.07)):
        _chevron(f"mn_fchv{k}", x, 0.64, 270, X["led_dim"], tags, z=0.20, s=0.32)
    # barramentos de cobre: bancos -> capacitor principal, por cima das bochechas, ate o borne central
    for sx in (-1, 1):
        _busbar(f"bus{sx}", sx * 0.64, sx * 0.10, 1.375, 0.55, M, X, tags)
    B.box("bus_join", 0, 1.375, 0.16, 0.09, 0.03, 0.60, KM, bevel=0.01, tags=tags)
    B.bolts("bus_jb", [(-0.04, 1.375), (0.04, 1.375)], 0.605, 0.016, S, tags=tags)
    # pulso saindo do principal para os cabos
    if pulse == 1:
        B.cyl("mn_pulse", 0, 1.10, 0.60, 0.05, 0.01, X["led"], axis="Z", verts=12, bevel=0.0, tags=tags)


def machine(M, T="machine", phase=0.0):
    """Maquinario (fileira de cima + tile central); transparente nos tiles de entrada e saida."""
    tags = (T,)
    X = _extra()
    i, clamp, level, arc, glow, mag, pulse = _state(phase)
    _main(M, X, tags, level, pulse)
    for sx in (-1, 1):
        _bank(sx, level, M, X, tags)
    _station(M, X, tags, clamp, arc, glow, mag, pulse)


# ============================================================================ teto
def _inlay(name, poly, targets, z1, green, tags, gap=0.03):
    """Placa embutida: abre um furo (contorno + vao) nas placas de base e assenta a placa no fundo escuro."""
    hole = B.offset_poly(poly, -gap)
    for k, t in enumerate(targets):
        B.cut(t, [B.loft(f"{name}_h{k}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    return B.shard(name, poly, 0.0, z1, green, slope=0.05, groove=0.03, panel_h=0.018, tags=tags)


# raio do emblema em 3 laminas (de cima para baixo), centrado no tile central
BOLT = [
    [(0.03, 0.40), (0.24, 0.40), (0.06, 0.12), (-0.15, 0.12)],
    [(-0.21, 0.07), (0.14, 0.07), (0.20, 0.01), (0.03, -0.06), (-0.27, -0.06), (-0.27, 0.01)],
    [(-0.04, -0.11), (0.15, -0.11), (-0.10, -0.42)],
]


def roof(M, T="roof"):
    """Teto verde (pintura da nave) com a galeria de capacitores sem pintura na fileira de cima, o emblema de
    raio no tile central e setas pintadas das entradas (meio) e da saida (embaixo)."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    B.box("rf_under", 0, 0, 3, 3, -0.05, 0.02, K, bevel=0.0, tags=tags)

    # ---- fileira de cima: placas verdes + 3 tampas de capacitor em colares octogonais claros
    for k, cx in enumerate((-1.0, 0.0, 1.0)):
        ta, tp = B.shard(f"rf_top{k}", B.rpoly(cx, 1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green,
                         slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
        r = 0.30 if k == 1 else 0.24
        cy = 1.02
        ring = _octo(cx, cy, r + 0.04)
        for t, nm in ((ta, "a"), (tp, "b")):
            B.cut(t, [B.loft(f"rf_tph{k}{nm}", ring, ring, -0.01, 0.5, green, bevel=0.0)])
        B.plate(f"rf_cbase{k}", _octo(cx, cy, r + 0.02), 0.0, 0.10, K, slope=0.015, tags=tags)
        # colar em 4 segmentos claros (vaos nas diagonais)
        for q in range(4):
            a0 = 90 * q + 12
            seg = [(cx + math.cos(math.radians(a0 + 33 * j)) * r, cy + math.sin(math.radians(a0 + 33 * j)) * r)
                   for j in range(3)] + \
                  [(cx + math.cos(math.radians(a0 + 33 * j)) * (r - 0.075),
                    cy + math.sin(math.radians(a0 + 33 * j)) * (r - 0.075)) for j in (2, 1, 0)]
            B.shard(f"rf_col{k}{q}", seg, 0.08, 0.17, A, slope=0.02, groove=0.012, panel_h=0.012, tags=tags)
        _can(f"rf_can{k}", cx, cy, r - 0.085, 0.05, 0.19, M, X, tags)

    # ponte clara ligando os 3 capacitores, com o medidor de 5 pips azuis
    bridge = [(-0.74, 1.36), (0.74, 1.36), (0.80, 1.30), (0.80, 1.25), (-0.80, 1.25), (-0.80, 1.30)]
    # (a ponte fica atras dos colares, so as pontas aparecem entre eles)
    ba, bp = B.shard("rf_bridge", bridge, 0.06, 0.15, A, slope=0.03, groove=0.015, panel_h=0.015, tags=tags)

    # ---- tile central: emblema de raio em 3 laminas claras sobre base escura chanfrada
    ea, ep = B.shard("rf_mid", B.rpoly(0, 0, 0.92, 0.92, 0, chamfer=0.14), 0.0, 0.07, green, slope=0.03,
                     groove=0.05, panel_h=0.022, tags=tags)
    emb = _octo(0, 0, 0.44)
    B.cut(ea, [B.loft("rf_embc", B.offset_poly(emb, -0.02), B.offset_poly(emb, -0.02), -0.01, 0.5, green,
                      bevel=0.0)])
    B.cut(ep, [B.loft("rf_embc2", B.offset_poly(emb, -0.02), B.offset_poly(emb, -0.02), -0.01, 0.5, green,
                      bevel=0.0)])
    B.plate("rf_emb", emb, 0.0, 0.09, K, slope=0.02, tags=tags)
    for k, poly in enumerate(BOLT):
        B.shard(f"rf_bolt{k}", poly, 0.08, 0.20, A, slope=0.025, groove=0.015, panel_h=0.015, tags=tags)
    B.bolts("rf_embb", [(0, 0.38), (0, -0.38), (0.38, 0), (-0.38, 0)], 0.10, 0.016, S, tags=tags)

    # ---- meio: placas laterais (sobre as entradas) com seta embutida apontando para o centro
    for sx in (-1, 1):
        ma, mp = B.shard(f"rf_side{sx}", B.rpoly(sx * 1.0, 0.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.06, green,
                         slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
        arrow = [(sx * 1.32, 0.24), (sx * 0.98, 0.24), (sx * 0.74, 0.0), (sx * 0.98, -0.24), (sx * 1.32, -0.24)]
        aa, ap = _inlay(f"rf_arr{sx}", arrow, (ma, mp), 0.13, green, tags)
        _ledslot(f"rf_ap{sx}", sx * 1.165, 0.0, 0.075, 0.20, 0.02, 2, M, tags, [aa, ap], pip_mats=X["led"],
                 pw=0.034)
        B.bolts(f"rf_mb{sx}", [(sx * 1.0 + dx, dy) for dx in (-0.37, 0.37) for dy in (-0.37, 0.37)], 0.08, 0.016,
                S, tags=tags)

    # ---- fileira de baixo (saida): 3 placas; a do meio com seta para baixo
    for k, cx in enumerate((-1.0, 0.0, 1.0)):
        ba, bp = B.shard(f"rf_bot{k}", B.rpoly(cx, -1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green,
                         slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
        if k == 1:
            arrow = [(-0.28, -0.66), (0.28, -0.66), (0.28, -1.02), (0.0, -1.28), (-0.28, -1.02)]
            aa, ap = _inlay("rf_barr", arrow, (ba, bp), 0.14, green, tags)
            _ledslot("rf_bpips", 0.0, -0.84, 0.27, 0.075, 0.02, 3, M, tags, [aa, ap], vertical=False,
                     pip_mats=X["led"], pw=0.034)
        else:
            sx = -1 if cx < 0 else 1
            B.cut(bp, [B.rbox(f"rf_bl{k}a", cx, -0.80, 0.62, 0.022, 0.04, 0.3, K, bevel=0.0),
                       B.rbox(f"rf_bl{k}b", cx + sx * 0.22, -1.30, 0.022, 0.16, 0.04, 0.3, K, rot=sx * -45,
                              bevel=0.0)])
            B.bolts(f"rf_bb{k}", [(cx - 0.36, -1.36), (cx + 0.36, -1.36)], 0.095, 0.016, S, tags=tags)

    # o verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nas bordas claras)
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False
