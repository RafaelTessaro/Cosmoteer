"""Carregadora de Carregadores EMP (EMP Magazine Charger) 3x3 - carrega Carregadores Padrao com pulso EMP.

Layout vanilla factory_he (tools/bsgen/factory.py): fileira de cima + tile central = maquinario (bloqueado);
entradas no meio das laterais: tile (0,1) esquerda = Carregador Padrao, tile (2,1) direita = cobre; saida =
fileira de baixo inteira. O jogo desenha as pilhas de recursos nesses 5 tiles, entao eles ficam livres de
maquinario e o piso mostra bases escuras marcadas (cantoneiras cinza, labio fino, setas azuis em recesso; a do
cobre com um tracinho de fio de cobre). Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade =
1 tile.

E uma CARREGADORA, nao uma prensa (mesma familia das armas: cascas claras chanfradas com bisel duplo sobre
nucleo escuro, LEDs em recessos, linhas de painel):
  * fileira de cima = banco de capacitores: nos tiles das pontas, carcacas claras com janela em degrau e 4
    capacitores altos (capa azul em anel, tampa de aluminio, borne sextavado), coluna de 5 LEDs azuis de nivel e
    lamina embaixo com pips de fluxo; no tile do meio, o capacitor principal (maior) num anel claro segmentado,
    ligado aos bancos por barramentos de cobre (barras chatas aparafusadas sobre isoladores, no vao escuro) que
    descem por dutos de cobre ate caixas de juncao; embaixo do anel, duas garras (fenda de 4 pips de nivel)
    abracam o alimentador de roletes onde o proximo Carregador Padrao (LEDs ambar) espera; cabos de potencia
    descem das garras ate as bobinas;
  * tile central = estacao de carga: portico de duas travessas claras (em cima o medidor de carga de 4 pips, em
    baixo as setas de saida) em volta do berco claro (leito escuro com 2 trilhos de contato e pastilhas de cobre);
    o carregador deitado (pinos para a direita) entra e sai por baixo das travessas pelos roletes; duas cabecas
    de bobina (casca clara em cunha, janela escura alta com 5 espiras de cobre horizontais sobre o tambor escuro,
    polo de aco com colar isolante, 2 chifres de descarga de aco nos cantos de dentro) correm em trilhos,
    empurradas por atuadores hidraulicos nos cantos de baixo, e apertam o carregador pelos dois lados (os polos
    encostam nas pontas dele). Tudo fica em |x| <= 0.485: nada invade os tiles de entrada.
Animacao (10 quadros, 0,1 s): 0 repouso (Carregador Padrao no berco, bobinas abertas, nivel 1 = sprite
desligado), 1-2 as bobinas fecham (curso 0.08) e os niveis sobem, 3 nivel cheio (capas dos capacitores acendem
fraco) e pulso descendo pelos cabos, 4-5 descarga: as espiras energizam (vao entre elas acende azul), arcos azuis
quebrados saem dos chifres e caem sobre o carregador (formas diferentes nos 2 quadros), o carregador comeca a
brilhar com os LEDs ja azuis (4) e vira Carregador EMP no lampejo (5) e os niveis caem, 6 brilho residual, 7 as
bobinas abrem, 8 o Carregador EMP desce para a saida enquanto o proximo Carregador Padrao sai do alimentador,
9 ele chega ao berco e o seguinte cai no alimentador.
Os brilhos grandes (arco, aro do carregador, espiras) so aparecem nos quadros 3-7; o lights.png (feito do
quadro 1) fica com os LEDs fixos, o nivel 1 e o anel azul fraco e fixo em volta do capacitor principal.
Teto: placas verdes (pintura) com o trilho de capacitores sem pintura na fileira de cima (3 tampas octogonais
com respiro em cruz em colares octogonais claros, carcacas claras entre elas com a barra de cobre numa fenda
escura, chevron com 2 pips azuis sob a tampa do meio, laminas em garra com 4 pips azuis nos tiles das pontas),
emblema de raio em 3 laminas claras sobre octogono escuro cercado por um anel de 8 laminas claras, com bornes de
cobre, no tile central (placa verde lisa em volta; 3 pips azuis na lamina do meio) e setas pintadas das entradas
e da saida com pips azuis; linhas de painel do teto sempre vazadas (fundo escuro), nunca cortes rasos.
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
CY = 0.0                   # centro do berco (tile central)
MAG_S = 0.27               # escala do carregador no berco (deitado, pinos para +X: 0.28 x 0.20)
MAG_HX = 0.52 * MAG_S      # meio comprimento do carregador deitado (ponta dos pinos)
TIP_C, TIP_O = MAG_HX + 0.01, 0.23   # |x| da ponta do polo: fechada (encosta no carregador) / aberta (curso 0.08)
SHELL_W = 0.25             # casca da bobina: |x| de fora = ponta + SHELL_W (aberta: 0.48, dentro do tile)
LANE = 0.14                # meia largura do canal de roletes
MAIN_Y = 1.06              # y do capacitor principal (e dos barramentos)
FEED_Y = 0.64              # y do carregador esperando no alimentador


# ============================================================================ utilidades
def _extra():
    """Materiais desta fabrica (os da linha EMP vem de parts/bs_mag_emp.py: mesmo nome = mesmo material)."""
    X = EMP.mats()
    X.update({
        # capa azul dos capacitores (pintura sem desgaste: malha pequena clareia inteira com wear)
        "sleeve": B.mat_paint("cap_sleeve", (0.05, 0.13, 0.42), rough=0.35, metal=0.2, wear=0.0, grime=0.02,
                              scale=5),
        "alu": B.mat_metal("cap_alu", (0.60, 0.62, 0.66), rough=0.30, metal=1.0),
        # capa com carga cheia: azul fraco aceso (so no quadro de nivel cheio)
        "sleeve_hot": B.mat_glow("cap_sleeve_hot", (0.10, 0.30, 1.0), 0.3),
        # arco: nucleo branco-azulado fino (estoura em branco frio, halo azul pequeno)
        "arc": B.mat_glow("emp_arc", (0.55, 0.78, 1.0), 2.4),
        "cell_hot": B.mat_glow("emp_cell_hot", (0.30, 0.58, 1.0), 1.4),
        # LED de nivel apagado: azul bem fraco (a coluna continua legivel e o aceso sobe nela)
        "led_low": B.mat_glow("emp_led_low", (0.18, 0.42, 1.0), 0.16),
        # tambor das bobinas energizado: o vao entre as espiras acende azul (forte / residual)
        "drum_hot": B.mat_glow("coil_drum_hot", (0.12, 0.34, 1.0), 0.55),
        "drum_warm": B.mat_glow("coil_drum_warm", (0.12, 0.34, 1.0), 0.22),
        # anel fixo e fraco em volta do capacitor principal (luz ambiente do lights.png)
        "ring_glow": B.mat_glow("emp_ring_glow", (0.15, 0.40, 1.0), 0.35),
        # LEDs ambar do Carregador Padrao no berco (forca baixa: acima de ~1.5 o ambar satura em amarelo)
        "amber": B.mat_glow("std_amber", Mo.AMBER, 1.8),
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
    """Estado do ciclo (dicionario): clamp = fechamento das bobinas (0..1), level = nivel dos capacitores
    (0..5), arc = forma do arco (None/0/1), glow = brilho do carregador (0..1), mags = carregadores na estacao
    [(tipo, y)], feed = y do carregador no alimentador (None = vazio), pulse = pulso nos cabos (0 = apagado, 1..2),
    energ = espiras energizadas (0, 1 residual, 2 forte)."""
    i = int(round(phase * NF)) % NF
    mags = [[("std", 0.0)], [("std", 0.0)], [("std", 0.0)], [("std", 0.0)], [("std_blue", 0.0)], [("emp", 0.0)],
            [("emp", 0.0)], [("emp", 0.0)], [("emp", -0.17), ("std", 0.40)], [("std", 0.12)]][i]
    return {
        "i": i,
        "clamp": [0.0, 0.55, 1.0, 1.0, 1.0, 1.0, 1.0, 0.45, 0.0, 0.0][i],
        "level": [1, 2, 4, 5, 3, 1, 0, 0, 0, 1][i],
        "arc": [None, None, None, None, 0, 1, None, None, None, None][i],
        "glow": [0.0, 0.0, 0.0, 0.0, 0.55, 1.0, 0.5, 0.2, 0.0, 0.0][i],
        "mags": mags,
        "feed": ([FEED_Y] * 8 + [None, FEED_Y + 0.09])[i],
        "pulse": [0, 0, 0, 1, 2, 0, 0, 0, 0, 0][i],
        "energ": [0, 0, 0, 0, 2, 2, 1, 0, 0, 0][i],
    }


def _chevron(name, cx, cy, ang, mat, tags, z=0.03, s=1.0):
    """Seta de fluxo (chevron) apontando para ang (graus)."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    B.loft(name, _rot(pts, ang, cx, cy), _rot(pts, ang, cx, cy), z, z + 0.006, mat, bevel=0.0, tags=tags)


def _ledslot(name, cx, cy, sx, sy, z_bed, n, M, tags, targets, vertical=True, pip_mats=None, pw=None):
    """Fenda de LEDs VAZADA nas pecas (o bisel reaplicado nao cria filete que tampe o leito) com leito preto e
    n pips em cima de z_bed (de baixo para cima / da esquerda para a direita); pip_mats = lista ou material."""
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
    """Materiais de uma coluna de n pips com 'lit' acesos (de baixo para cima); os outros ficam bem fracos."""
    return [X["led"] if i < lit else X["led_low"] for i in range(n)]


def _bezel(prefix, poly_out, poly_in, z0, z1, M, tags, targets):
    """Janela com moldura em degrau: abre poly_out nas pecas e assenta um labio de aco (poly_out - poly_in)."""
    K, S = M["core"], M["steel"]
    for k, t in enumerate(targets):
        B.cut(t, [B.loft(f"{prefix}_c{k}", poly_out, poly_out, z0, 0.9, K, bevel=0.0)])
    lip = B.plate(prefix + "_lip", poly_out, z1 - 0.06, z1, S, slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft(prefix + "_lc", poly_in, poly_in, z1 - 0.2, z1 + 0.2, K, bevel=0.0)])
    B.loft(prefix + "_bed", poly_out, poly_out, z0 - 0.02, z0, M["black"], bevel=0.0, tags=tags)


def _vent(name, top, x, y, rt, z, ang, M, w):
    """Respiro em cruz VAZADO na tampa (cortes passantes: a vedacao escura aparece embaixo, sem filete)."""
    L = 2 * rt + 0.04
    B.cut(top, [B.rbox(f"{name}_v{k}", x, y, L, w, z - 0.05, z + 0.2, M["black"], rot=ang + 90 * k, bevel=0.0)
                for k in range(2)])


def _can(name, x, y, r, z0, z1, M, X, tags, sleeve=None, vent=0.0, term=False):
    """Capacitor alto visto de cima: corpo escuro, capa azul em anel largo, vedacao escura em anel fino, tampa
    de aluminio com respiro em cruz vazado (vent = angulo da cruz) e, se term, borne central sextavado."""
    B.cyl(name + "_body", x, y, (z0 + z1) / 2 - 0.04, r * 0.96, z1 - z0 - 0.08, M["core_mid"], axis="Z", verts=24,
          bevel=0.0, tags=tags)
    B.cyl(name + "_sl", x, y, z1 - 0.04, r, 0.08, sleeve or X["sleeve"], axis="Z", verts=24, bevel=0.006, tags=tags)
    B.cyl(name + "_seal", x, y, z1 + 0.004, r * 0.78, 0.008, M["core"], axis="Z", verts=24, bevel=0.0, tags=tags)
    rt = r * 0.64
    top = B.cyl(name + "_top", x, y, z1 + 0.017, rt, 0.026, X["alu"], axis="Z", verts=24, bevel=0.006, tags=tags)
    _vent(name, top, x, y, rt, z1 + 0.017, vent, M, max(0.016, r * 0.11))
    if term:
        B.cyl(name + "_t", x, y, z1 + 0.04, r * 0.2, 0.024, M["steel"], axis="Z", verts=6, bevel=0.005, tags=tags)


def _ocan(name, x, y, r, z1, M, X, tags):
    """Capacitor do teto (sem circulos no teto): capa azul OCTOGONAL alinhada com o colar, vedacao escura
    octogonal e tampa de aluminio octogonal com respiro em cruz vazado."""
    B.plate(name + "_sl", _octo(x, y, r, a0=0.0), z1 - 0.08, z1, X["sleeve"], slope=0.012, bevel=0.005, tags=tags)
    B.plate(name + "_seal", _octo(x, y, r * 0.80, a0=0.0), z1 - 0.004, z1 + 0.008, M["core"], slope=0.004,
            bevel=0.0, tags=tags)
    rt = r * 0.68
    top = B.plate(name + "_top", _octo(x, y, rt, a0=0.0), z1 + 0.004, z1 + 0.032, X["alu"], slope=0.012,
                  bevel=0.005, tags=tags)
    _vent(name, top, x, y, rt, z1 + 0.018, 0.0, M, 0.018 if r < 0.2 else 0.022)


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
    kind 'std' = Carregador Padrao (LEDs ambar), 'std_blue' = Padrao no inicio da carga (LEDs ja azuis),
    'emp' = Carregador EMP (hot: celula acesa forte)."""
    sc = B.bpy.context.scene
    before = set(o.name for o in sc.objects)
    if kind in ("std", "std_blue"):
        M2 = dict(M)
        M2["glow"] = X["amber"] if kind == "std" else X["led"]
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


def _stroke(name, a, b, w, z, mat, tags):
    (ax, ay), (bx, by) = a, b
    ln = math.hypot(bx - ax, by - ay)
    ang = math.degrees(math.atan2(by - ay, bx - ax))
    B.rbox(name, (ax + bx) / 2, (ay + by) / 2, ln + w * 0.7, w, z, z + 0.006, mat, rot=ang, bevel=0.0, tags=tags)


def _arc(name, p0, p1, seed, z, mat, tags, amp=0.033, n=4, w=0.016, fork=False):
    """Arco eletrico: linha quebrada de n trechos finos (n-1 dobras em zigue-zague com amplitude ~2 px) entre
    p0 e p1 (>= 0.10 de comprimento para ler nos 64 px); fork = forquilha curta de 2 px na ponta p1."""
    rnd = random.Random(seed)
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    pts = [(x0, y0)]
    sgn = rnd.choice((-1, 1))
    for k in range(1, n):
        o = rnd.uniform(0.65, 1.0) * amp * sgn
        sgn = -sgn
        t = k / n + rnd.uniform(-0.05, 0.05)
        pts.append((x0 + dx * t + nx * o, y0 + dy * t + ny * o))
    pts.append((x1, y1))
    for k in range(n):
        _stroke(f"{name}_s{k}", pts[k], pts[k + 1], w, z, mat, tags)
    if fork:
        base = math.atan2(y1 - pts[-2][1], x1 - pts[-2][0])
        for j, da in enumerate((-0.7, 0.7)):
            a = base + da
            _stroke(f"{name}_f{j}", (x1, y1), (x1 + math.cos(a) * 0.03, y1 + math.sin(a) * 0.03), w * 0.85, z, mat,
                    tags)


def _horn_tip(sx, sy, x0):
    """Ponta do chifre de descarga da bobina sx (canto sy) com a face de dentro em |x| = x0."""
    return sx * (x0 - 0.012), CY + sy * 0.128


def _coil(sx, clamp, pulse, energ, M, X, tags):
    """Cabeca de bobina do lado sx: carro escuro nos trilhos, casca clara em cunha (bisel duplo) com janela
    escura alta mostrando 5 espiras de cobre HORIZONTAIS (tambor de eixo Y) com vao escuro de ~2 px entre elas,
    polo de aco com colar isolante e ponta chanfrada, 2 chifres de descarga de aco nos cantos de dentro, cabo de
    potencia entrando por cima. Devolve |x| da face de dentro (onde o atuador prende)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    f = _flip(sx)
    tip = TIP_O - (TIP_O - TIP_C) * clamp
    x0, x1 = tip + 0.04, tip + SHELL_W       # face de dentro / de fora da casca (|x|); aberta x1 = 0.48
    B.box(f"cl_car{sx}", sx * (x0 + x1) / 2, CY, x1 - x0, 0.38, 0.04, 0.11, KM, bevel=0.01, tags=tags)
    shell = [(-x1, CY - 0.195), (-x1 + 0.03, CY - 0.225), (-x0 - 0.075, CY - 0.225), (-x0, CY - 0.12),
             (-x0, CY + 0.12), (-x0 - 0.075, CY + 0.225), (-x1 + 0.03, CY + 0.225), (-x1, CY + 0.195)]
    ha, hp = B.shard(f"cl_shell{sx}", f(shell), 0.08, 0.37, A, slope=0.045, groove=0.022, panel_h=0.025,
                     tags=tags)
    wx0, wx1 = x0 + 0.05, x1 - 0.045
    ww = wx1 - wx0
    win = B.rpoly(sx * (wx0 + wx1) / 2, CY, ww, 0.31, 0, chamfer=0.02)
    for t, k in ((ha, "a"), (hp, "b")):
        if t is not None:
            B.cut(t, [B.loft(f"cl_win{sx}{k}", win, win, 0.14, 0.9, K, bevel=0.0)])
    B.loft(f"cl_wbed{sx}", win, win, 0.13, 0.14, M["black"], bevel=0.0, tags=tags)
    # tambor (eixo Y): nucleo escuro (energizado: acende azul no vao entre as espiras) + 5 espiras de cobre
    # deitadas em X, passo de 4 px, com reflexo no meio de cada uma
    cxd = sx * (wx0 + wx1) / 2
    drum = {0: K, 1: X["drum_warm"], 2: X["drum_hot"]}[energ]
    B.box(f"cl_drum{sx}", cxd, CY, ww - 0.008, 0.30, 0.13, 0.16, drum, bevel=0.0, tags=tags)
    for k in range(5):
        B.cyl(f"cl_turn{sx}{k}", cxd, CY + (k - 2) * 0.0625, 0.185, 0.0175, ww - 0.016, X["copper"], axis="X",
              verts=12, bevel=0.0, tags=tags)
    # polo: colar isolante escuro na face, haste de aco octogonal e ponta chanfrada para o carregador
    B.cyl(f"cl_col{sx}", sx * (x0 - 0.006), CY, 0.24, 0.07, 0.024, KM, axis="X", verts=8, bevel=0.005, tags=tags)
    B.cyl(f"cl_pole{sx}", sx * (tip + 0.026), CY, 0.24, 0.046, 0.032, S, axis="X", verts=8, bevel=0.004, tags=tags)
    r1, r2 = (0.026, 0.046) if sx > 0 else (0.046, 0.026)   # raio 1 em -X, raio 2 em +X
    B.cyl(f"cl_tip{sx}", sx * (tip + 0.005), CY, 0.24, r1, 0.012, X["silver"], axis="X", verts=8, bevel=0.0,
          tags=tags, r2=r2)
    # chifres de descarga: dedos de aco nos cantos de dentro da casca, apontando para o carregador (de onde
    # saltam os arcos), sobre um bloco isolante escuro
    for sy in (-1, 1):
        bx_, by_ = sx * (x0 + 0.052), CY + sy * 0.188
        tx_, ty_ = _horn_tip(sx, sy, x0)
        B.box(f"cl_hins{sx}{sy}", bx_, by_, 0.05, 0.05, 0.33, 0.40, KM, bevel=0.008, tags=tags)
        B.rbox(f"cl_horn{sx}{sy}", (bx_ + tx_) / 2, (by_ + ty_) / 2, math.hypot(tx_ - bx_, ty_ - by_) + 0.01, 0.024,
               0.375, 0.405, X["silver"], rot=math.degrees(math.atan2(ty_ - by_, tx_ - bx_)), bevel=0.005,
               tags=tags)
    # parafusos nos cantos de fora (faixa clara acima e abaixo da janela)
    B.bolts(f"cl_b{sx}", [(sx * (x1 - 0.055), CY + 0.19), (sx * (x1 - 0.055), CY - 0.19)], 0.395, 0.014, S,
            tags=tags)
    # cabo de potencia: desce da garra da fileira de cima e entra por cima na casca
    kx = sx * (x1 - 0.07)
    y0c, y1c = CY + 0.21, 0.53
    B.cyl(f"cl_cable{sx}", kx, (y0c + y1c) / 2, 0.30, 0.034, y1c - y0c, KM, axis="Y", verts=10, bevel=0.0, tags=tags)
    for k, y in enumerate((CY + 0.245, 0.45)):
        B.cyl(f"cl_cclamp{sx}{k}", kx, y, 0.30, 0.043, 0.024, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    if pulse:
        # pulso de carga descendo pelo cabo: anel azul aceso
        py = 0.40 if pulse == 1 else CY + 0.31
        B.cyl(f"cl_pulse{sx}", kx, py, 0.30, 0.04, 0.03, X["led"], axis="Y", verts=10, bevel=0.0, tags=tags)
    return x0


def _actuator(sx, x_in, M, X, tags, lit):
    """Atuador hidraulico do aperto (canto de baixo do tile central): casca clara pequena com o cilindro e a haste
    prateada empurrando o suporte preso ao carro da bobina."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    ay = CY - 0.335
    hb = B.rpoly(sx * 0.41, ay, 0.14, 0.16, 0, chamfer=0.035)   # 0.34..0.48: fora dos tiles de entrada
    ha, hp = B.shard(f"ac_house{sx}", hb, 0.04, 0.24, A, slope=0.035, groove=0.016, panel_h=0.018, tags=tags)
    Mo.slot_with_pips(f"ac_sl{sx}", sx * 0.41, ay - 0.035, ay + 0.035, 0.03, 0.258, 2, M, tags, target=[ha, hp],
                      depth=0.07, pip_mat=X["led"] if lit else X["led_low"])
    # haste prateada saindo da face de dentro ate o suporte no carro da bobina
    xr0 = 0.335
    xb = x_in + 0.05
    L = xr0 - xb
    if L > 0.005:
        B.cyl(f"ac_rod{sx}", sx * (xb + L / 2), ay + 0.01, 0.13, 0.018, L + 0.01, X["silver"], axis="X", verts=10,
              bevel=0.0, tags=tags)
    B.cyl(f"ac_gland{sx}", sx * (xr0 + 0.005), ay + 0.01, 0.13, 0.03, 0.02, S, axis="X", verts=8, bevel=0.004,
          tags=tags)
    B.box(f"ac_brk{sx}", sx * xb, ay + 0.07, 0.045, 0.17, 0.04, 0.15, KM, bevel=0.008, tags=tags)
    B.cyl(f"ac_pin{sx}", sx * xb, ay + 0.01, 0.155, 0.016, 0.012, S, axis="Z", verts=8, bevel=0.0, tags=tags)


def _station(M, X, tags, st):
    """Estacao de carga no tile central: berco entre duas travessas claras (portico), roletes de entrada e
    saida, bobinas nos trilhos com atuadores, carregador(es), arcos e brilho."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    clamp, arc, glow, level = st["clamp"], st["arc"], st["glow"], st["level"]
    B.plate("st_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.04, K, slope=0.015, tags=tags)
    # canal de roletes curto em cima (vem do alimentador) e embaixo (vai para a saida)
    for nm, (y0, y1) in (("t", (0.30, 0.50)), ("b", (-0.488, -0.30))):
        B.box(f"st_lane{nm}", 0, (y0 + y1) / 2, 2 * LANE, y1 - y0, 0.035, 0.05, M["black"], bevel=0.0, tags=tags)
        for sx in (-1, 1):
            B.box(f"st_guide{nm}{sx}", sx * (LANE + 0.012), (y0 + y1) / 2, 0.022, y1 - y0, 0.035, 0.10, S,
                  bevel=0.005, tags=tags)
        for k in range(3):
            y = y0 + 0.035 + k * 0.065
            B.cyl(f"st_roll{nm}{k}", 0, y, 0.07, 0.02, 2 * LANE - 0.01, KM, axis="X", verts=10, bevel=0.0, tags=tags)
    # trilhos das bobinas (aparecem quando as cabecas abrem); terminam em |x| = 0.47 (dentro do tile)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box(f"st_rail{sx}{sy}", sx * 0.33, CY + sy * 0.13, 0.28, 0.026, 0.04, 0.08, S, bevel=0.005,
                  tags=tags)
    # berco claro (bisel duplo) com leito escuro na forma do carregador
    cradle = B.rpoly(0, CY, 0.345, 0.30, 0, chamfer=0.06)
    ca, cp = B.shard("st_cradle", cradle, 0.05, 0.11, A, slope=0.02, groove=0.012, panel_h=0.012, tags=tags)
    bed = B.rpoly(0, CY, 0.30, 0.215, 0, chamfer=0.02)
    for t, k in ((ca, "a"), (cp, "b")):
        if t is not None:
            B.cut(t, [B.loft(f"st_bedc{k}", bed, bed, 0.09, 0.5, K, bevel=0.0)])
    B.loft("st_bed", bed, bed, 0.085, 0.092, M["black"], bevel=0.0, tags=tags)
    # leito: 2 trilhos de contato de aco e pastilhas de cobre nas pontas (o berco vazio continua lendo berco)
    for sy in (-1, 1):
        B.box(f"st_crail{sy}", 0, CY + sy * 0.058, 0.20, 0.022, 0.09, 0.102, S, bevel=0.004, tags=tags)
    for sx in (-1, 1):
        B.box(f"st_cpad{sx}", sx * 0.122, CY, 0.026, 0.10, 0.09, 0.104, X["copper"], bevel=0.004, tags=tags)
    # carregador(es) na estacao (deitados, pinos para a direita) e o brilho azul em volta do que carrega
    if glow > 0:
        rim = B.mat_glow(f"emp_rim{int(glow * 100)}", (0.15, 0.40, 1.0), 1.2 * glow)
        rp = B.rpoly(0, CY, 0.325, 0.235, 0, chamfer=0.04)
        B.loft("st_rim", rp, rp, 0.092, 0.098, rim, bevel=0.0, tags=tags)
    for j, (kind, dy) in enumerate(st["mags"]):
        _mini(f"st_mag{j}", kind, 0.0, CY + dy, 0.095, M, X, tags, hot=glow >= 0.9)
    # portico: travessas claras em cima (medidor de carga de 4 pips) e embaixo (setas de saida); o carregador
    # entra e sai por baixo delas
    bar = [(-0.19, -0.075), (0.19, -0.075), (0.22, -0.045), (0.22, 0.045), (0.19, 0.075), (-0.19, 0.075),
           (-0.22, 0.045), (-0.22, -0.045)]
    for nm, by in (("t", CY + 0.24), ("b", CY - 0.24)):
        poly = [(x, y + by) for x, y in bar]
        ga, gp = B.shard(f"st_bar{nm}", poly, 0.06, 0.30, A, slope=0.03, groove=0.014, panel_h=0.02, tags=tags)
        if nm == "t":
            _ledslot("st_meter", 0, by, 0.26, 0.05, 0.24, 4, M, tags, [ga, gp], vertical=False,
                     pip_mats=_levels(4, max(0, level - 1), X), pw=0.032)
        else:
            _ledslot("st_out", 0, by, 0.25, 0.05, 0.24, 0, M, tags, [ga, gp], vertical=False)
            for k, x in enumerate((-0.07, 0.0, 0.07)):
                _chevron(f"st_outchv{k}", x, by, 270, X["led_dim"], tags, z=0.248, s=0.30)
        for sx in (-1, 1):
            B.cut(gp, [B.rbox(f"st_barpl{nm}{sx}", sx * 0.165, by, 0.02, 0.10, 0.27, 0.6, K, bevel=0.0)])
    x_in = 0.0
    for sx in (-1, 1):
        x_in = _coil(sx, clamp, st["pulse"], st["energ"], M, X, tags)
        _actuator(sx, x_in, M, X, tags, lit=clamp > 0.3)
    # arcos azuis quebrados (>= 0.12 de comprimento, ~1 px de traco): saltam dos chifres das bobinas e caem
    # sobre o carregador; quadro 4 = 2 arcos em diagonal (inicio), quadro 5 = 4 arcos (pico), formas diferentes
    if arc is not None:
        legs = ((-1, 1), (1, -1)) if arc == 0 else ((-1, -1), (1, 1))
        for j, (sx, sy) in enumerate(legs):
            rnd = random.Random(31 + 7 * arc + j)
            end = (sx * rnd.uniform(0.035, 0.07), CY + sy * rnd.uniform(0.035, 0.065))
            _arc(f"arc{arc}{j}", _horn_tip(sx, sy, x_in), end, 101 + 13 * arc + 5 * j, 0.42, X["arc"], tags,
                 fork=(j % 2 == arc % 2))
    # labio de aco na boca da saida
    B.box("st_outlip", 0, -0.47, 2 * LANE + 0.08, 0.04, 0.035, 0.12, KM, bevel=0.01, tags=tags)


def _bank(sx, level, pulse, M, X, tags):
    """Banco de capacitores de um tile de ponta: carcaca clara com janela em degrau e 4 capacitores altos,
    coluna de 5 LEDs de nivel na borda de dentro, lamina embaixo apontando para a estacao (pips de fluxo)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    f = _flip(sx)
    house = [(-1.42, 1.30), (-1.30, 1.42), (-0.60, 1.42), (-0.60, 0.87), (-0.71, 0.76), (-1.30, 0.76),
             (-1.42, 0.88)]
    ha, hp = B.shard(f"bk_house{sx}", f(house), 0.0, 0.46, A, slope=0.07, groove=0.035, panel_h=0.03, tags=tags)
    win = [(-1.32, 0.86), (-0.94, 0.86), (-0.88, 0.92), (-0.88, 1.32), (-1.32, 1.32)]
    win_in = B.offset_poly(win, 0.024)
    _bezel(f"bk_win{sx}", f(win), f(win_in), 0.28, 0.46, M, tags, (ha, hp))
    sleeve = X["sleeve_hot"] if level >= 5 else X["sleeve"]
    for k, (cx, cy) in enumerate(((-1.21, 1.205), (-0.99, 1.205), (-1.21, 0.975), (-0.99, 0.975))):
        _can(f"bk_can{sx}{k}", cx if sx < 0 else -cx, cy, 0.102, 0.26, 0.47, M, X, tags, sleeve=sleeve)
    # coluna de nivel (5 pips azuis de 3 px acesos de baixo para cima) entre a janela e a borda de dentro
    _ledslot(f"bk_lv{sx}", sx * 0.785, 1.10, 0.072, 0.42, 0.40, 5, M, tags, [ha, hp], pip_mats=_levels(5, level, X),
             pw=0.046)
    # linha de painel diagonal no chanfro de baixo + parafusos
    B.cut(hp, [B.rbox(f"bk_pl{sx}", sx * 0.74, 0.86, 0.022, 0.11, 0.42, 0.8, K, rot=sx * 45, bevel=0.0)])
    B.bolts(f"bk_bolt{sx}", [(sx * 1.36, 1.24), (sx * 0.68, 1.36)], 0.49, 0.017, S, tags=tags)
    # lamina embaixo, apontando para a estacao; os pips correm de fora para dentro durante o pulso
    blade = [(-1.42, 0.72), (-0.80, 0.72), (-0.56, 0.635), (-0.60, 0.53), (-1.30, 0.53), (-1.42, 0.60)]
    ba, bp = B.shard(f"bk_blade{sx}", f(blade), 0.0, 0.30, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
    flow = [X["led"] if (pulse and k < 2 * pulse) else X["led_low"] for k in range(4)]
    _ledslot(f"bk_bsl{sx}", sx * 1.03, 0.625, 0.30, 0.04, 0.24, 4, M, tags, [ba, bp], vertical=False,
             pip_mats=flow if sx < 0 else flow[::-1], pw=0.022)
    B.cut(bp, [B.rbox(f"bk_bpl{sx}", sx * 0.74, 0.625, 0.02, 0.12, 0.27, 0.8, K, rot=sx * -30, bevel=0.0)])
    # isolador + borne na borda de dentro da carcaca (onde chega o barramento)
    B.box(f"bk_term{sx}", sx * 0.64, MAIN_Y, 0.10, 0.11, 0.30, 0.56, KM, bevel=0.012, tags=tags)
    # duto vertical de cobre no vao entre o banco e a garra (desce do borne para a estacao), com 2 bracadeiras
    B.box(f"bk_vbus{sx}", sx * 0.553, 0.86, 0.042, 0.30, 0.20, 0.225, X["copper"], bevel=0.006, tags=tags)
    B.box(f"bk_vbus_s{sx}", sx * 0.553, 0.86, 0.056, 0.32, 0.03, 0.20, KM, bevel=0.008, tags=tags)
    B.box(f"bk_vbus_h{sx}", sx * 0.60, 1.005, 0.12, 0.04, 0.20, 0.225, X["copper"], bevel=0.006, tags=tags)
    for k, y in enumerate((0.80, 0.94)):
        B.box(f"bk_vbus_c{sx}{k}", sx * 0.553, y, 0.07, 0.024, 0.18, 0.24, S, bevel=0.005, tags=tags)
    # caixa de juncao escura na ponta de baixo do duto, com pip de fluxo
    B.box(f"bk_jbox{sx}", sx * 0.553, 0.725, 0.078, 0.07, 0.03, 0.25, KM, bevel=0.012, tags=tags)
    B.box(f"bk_jled{sx}", sx * 0.553, 0.712, 0.03, 0.016, 0.25, 0.256, X["led"] if pulse else X["led_low"],
          bevel=0.0, tags=tags)


def _busbar(name, x0, x1, y, z, M, X, tags, w=0.06):
    """Barramento de cobre chato com parafusos de aco nas pontas e um isolador escuro no meio."""
    L = abs(x1 - x0)
    cx = (x0 + x1) / 2
    B.box(name, cx, y, L, w, z, z + 0.025, X["copper"], bevel=0.006, tags=tags)
    B.bolts(f"{name}_b", [(x0 + (0.03 if x1 > x0 else -0.03), y), (x1 - (0.03 if x1 > x0 else -0.03), y)],
            z + 0.03, 0.015, M["steel"], tags=tags)
    # isolador no meio (bloco escuro com tampa de aco sob a barra)
    B.box(name + "_ins", cx, y, 0.07, w + 0.05, 0.03, z, M["core_mid"], bevel=0.01, tags=tags)
    B.box(name + "_insc", cx, y, 0.05, w + 0.07, z, z + 0.035, M["armor_mid"], bevel=0.008, tags=tags)


def _main(M, X, tags, level, pulse, feed):
    """Tile de cima do meio: capacitor principal num poco escuro ligado aos bancos por barramentos de cobre;
    embaixo, duas garras abracando o anel do poco em volta do alimentador de roletes (com o proximo Carregador
    Padrao esperando em y = feed, None = vazio) que desce para o berco."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # leito escuro de toda a fileira de cima
    B.plate("mc_bed", B.rpoly(0, 0.98, 2.90, 0.92, 0, chamfer=0.08), 0.0, 0.05, K, slope=0.01, tags=tags)
    # poco octogonal do capacitor principal (anel claro com bisel duplo) e o capacitor
    B.plate("mn_well", _octo(0, MAIN_Y, 0.30), 0.03, 0.12, KM, slope=0.02, tags=tags)
    for q in range(4):
        a0 = 90 * q + 14
        seg = [(math.cos(math.radians(a0 + 31 * j)) * 0.30, MAIN_Y + math.sin(math.radians(a0 + 31 * j)) * 0.30)
               for j in range(3)] + \
              [(math.cos(math.radians(a0 + 31 * j)) * 0.235, MAIN_Y + math.sin(math.radians(a0 + 31 * j)) * 0.235)
               for j in (2, 1, 0)]
        B.shard(f"mn_ring{q}", seg, 0.10, 0.30, A, slope=0.025, groove=0.014, panel_h=0.014, tags=tags)
    # anel azul fraco e FIXO no fundo do poco, em volta do capacitor (luz ambiente estatica do lights.png)
    B.cyl("mn_glowring", 0.0, MAIN_Y, 0.123, 0.232, 0.006, X["ring_glow"], axis="Z", verts=32, bevel=0.0, tags=tags)
    _can("mn_can", 0.0, MAIN_Y, 0.20, 0.10, 0.56, M, X, tags, vent=45.0, term=True)
    # barramentos de cobre: bornes dos bancos -> borne do capacitor principal
    for sx in (-1, 1):
        _busbar(f"bus{sx}", sx * 0.66, sx * 0.06, MAIN_Y, 0.62, M, X, tags)
    # garras: abracam o chanfro de baixo do anel e descem em ponta ate os cabos das bobinas; fenda de 4 pips
    claw = [(-0.30, 0.95), (-0.45, 0.95), (-0.50, 0.90), (-0.50, 0.68), (-0.42, 0.52), (-0.31, 0.465),
            (-0.265, 0.56), (-0.265, 0.74), (-0.22, 0.80), (-0.22, 0.86)]
    for sx in (-1, 1):
        ca, cp = B.shard(f"claw{sx}", _flip(sx)(claw), 0.0, 0.44, A, slope=0.055, groove=0.025, panel_h=0.03,
                         tags=tags)
        _ledslot(f"cw_sl{sx}", sx * 0.385, 0.74, 0.052, 0.22, 0.36, 4, M, tags, [ca, cp],
                 pip_mats=_levels(4, max(0, level - 1), X), pw=0.034)
        B.cut(cp, [B.rbox(f"cw_pl{sx}", sx * 0.40, 0.575, 0.02, 0.12, 0.42, 0.8, K, rot=sx * 35, bevel=0.0)])
        B.bolts(f"cw_b{sx}", [(sx * 0.44, 0.895)], 0.475, 0.016, S, tags=tags)
    # alimentador de roletes entre as garras com o proximo Carregador Padrao esperando
    B.box("mn_feed", 0, 0.645, 2 * LANE + 0.04, 0.31, 0.03, 0.06, M["black"], bevel=0.0, tags=tags)
    for k in range(4):
        B.cyl(f"mn_roll{k}", 0, 0.52 + k * 0.08, 0.075, 0.02, 2 * LANE - 0.01, KM, axis="X", verts=10, bevel=0.0,
              tags=tags)
    for sx in (-1, 1):
        B.box(f"mn_lip{sx}", sx * (LANE + 0.012), 0.645, 0.022, 0.31, 0.03, 0.12, S, bevel=0.005, tags=tags)
    if feed is not None:
        _mini("mn_next", "std", 0.0, feed, 0.085, M, X, tags)
    if pulse == 1:
        # lampejo curto no borne do principal no inicio da descarga
        B.cyl("mn_pulse", 0, MAIN_Y, 0.66, 0.035, 0.01, X["led"], axis="Z", verts=12, bevel=0.0, tags=tags)


def machine(M, T="machine", phase=0.0):
    """Maquinario (fileira de cima + tile central); transparente nos tiles de entrada e saida."""
    tags = (T,)
    X = _extra()
    st = _state(phase)
    _main(M, X, tags, st["level"], st["pulse"], st["feed"])
    for sx in (-1, 1):
        _bank(sx, st["level"], st["pulse"], M, X, tags)
    _station(M, X, tags, st)


# ============================================================================ teto
def _inlay(name, poly, targets, z1, green, tags, gap=0.03):
    """Placa embutida: abre um furo (contorno + vao) nas placas de base e assenta a placa no fundo escuro."""
    hole = B.offset_poly(poly, -gap)
    for k, t in enumerate(targets):
        B.cut(t, [B.loft(f"{name}_h{k}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    return B.shard(name, poly, 0.0, z1, green, slope=0.05, groove=0.03, panel_h=0.018, tags=tags)


def _collar(name, cx, cy, r, w, z0, z1, A, tags, gap_deg=14):
    """Colar octogonal claro em 4 segmentos com bisel duplo (vaos nas direcoes cardeais). w >= 0.09: o painel
    de dentro fica com >= 0.03 de largura (painel mais fino depois do chanfro vira triangulos pretos)."""
    def seg(ro, ri, a0, a1):
        ang = [math.radians(a0 + (a1 - a0) * j / 2) for j in range(3)]
        return [(cx + math.cos(a) * ro, cy + math.sin(a) * ro) for a in ang] + \
               [(cx + math.cos(a) * ri, cy + math.sin(a) * ri) for a in reversed(ang)]

    out = []
    span = 90 - gap_deg
    for q in range(4):
        a0 = 90 * q + gap_deg / 2
        # base chanfrada + painel interno desenhado a mao (o offset automatico do painel deixava um risco preto
        # num dos segmentos: triangulos sobrepostos no vertice concavo)
        a = B.plate(f"{name}{q}", seg(r, r - w, a0, a0 + span), z0, z1, A, slope=0.018, tags=tags)
        p = B.plate(f"{name}{q}_pnl", seg(r - 0.03, r - w + 0.03, a0 + 5, a0 + span - 5), z1 - 0.004, z1 + 0.012, A,
                    slope=0.006, bevel=0.004, tags=tags)
        out.append((a, p))
    return out


def _octring(name, cx, cy, ro, ri, z0, z1, mat, tags, gap=0.014):
    """Anel octogonal claro em 8 laminas trapezoidais (vao fino nos vertices), sem booleanas."""
    for k in range(8):
        a, b = math.radians(22.5 + 45 * k), math.radians(22.5 + 45 * (k + 1))
        po = [(cx + ro * math.cos(t), cy + ro * math.sin(t)) for t in (a, b)]
        pi = [(cx + ri * math.cos(t), cy + ri * math.sin(t)) for t in (b, a)]
        ux, uy = po[1][0] - po[0][0], po[1][1] - po[0][1]
        L = math.hypot(ux, uy)
        ux, uy = ux / L * gap / 2, uy / L * gap / 2
        poly = [(po[0][0] + ux, po[0][1] + uy), (po[1][0] - ux, po[1][1] - uy),
                (pi[0][0] - ux, pi[0][1] - uy), (pi[1][0] + ux, pi[1][1] + uy)]
        B.plate(f"{name}{k}", poly, z0, z1, mat, slope=0.01, bevel=0.005, tags=tags)


# raio do emblema em 3 laminas (de cima para baixo), centrado no tile central (escala 0.80: cabe dentro do
# labio do octogono com folga)
EMB_S = 0.80
BOLT = [[(x * EMB_S, y * EMB_S) for x, y in poly] for poly in (
    [(0.03, 0.40), (0.24, 0.40), (0.06, 0.12), (-0.15, 0.12)],
    [(-0.21, 0.07), (0.14, 0.07), (0.20, 0.01), (0.03, -0.06), (-0.27, -0.06), (-0.27, 0.01)],
    [(-0.04, -0.11), (0.15, -0.11), (-0.10, -0.42)],
)]


def roof(M, T="roof"):
    """Teto verde (pintura da nave) com a galeria de capacitores sem pintura na fileira de cima, o emblema de
    raio no tile central e setas pintadas das entradas (meio) e da saida (embaixo)."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    B.box("rf_under", 0, 0, 3, 3, -0.05, 0.02, K, bevel=0.0, tags=tags)

    # ---- fileira de cima: placas verdes com as tampas dos capacitores em colares octogonais claros
    cy = 1.04
    tops = []
    for k, cx in enumerate((-1.0, 0.0, 1.0)):
        ta, tp = B.shard(f"rf_top{k}", B.rpoly(cx, 1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green,
                         slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
        r = 0.31 if k == 1 else 0.25
        hole = _octo(cx, cy, r + 0.035)
        for t, nm in ((ta, "a"), (tp, "b")):
            B.cut(t, [B.loft(f"rf_tph{k}{nm}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
        B.plate(f"rf_cbase{k}", _octo(cx, cy, r + 0.015), 0.0, 0.10, K, slope=0.015, tags=tags)
        _collar(f"rf_col{k}", cx, cy, r, 0.09, 0.08, 0.18, A, tags)
        _ocan(f"rf_can{k}", cx, cy, r - 0.095, 0.17, M, X, tags)
        tops.append((ta, tp))
    # carcacas claras do barramento entre as tampas (sem pintura): fenda escura com a barra de cobre dentro
    for sx in (-1, 1):
        x0, x1 = sx * 0.325, sx * 0.745
        hb = [(x0, cy - 0.05), (x0 + sx * 0.05, cy - 0.085), (x1 - sx * 0.05, cy - 0.085), (x1, cy - 0.05),
              (x1, cy + 0.05), (x1 - sx * 0.05, cy + 0.085), (x0 + sx * 0.05, cy + 0.085), (x0, cy + 0.05)]
        hole = B.offset_poly(hb, -0.025)
        for k in (1, 1 + sx):
            for t in tops[k]:
                B.cut(t, [B.loft(f"rf_bh{sx}{k}{id(t) % 97}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
        B.loft(f"rf_bhb{sx}", hole, hole, 0.0, 0.03, K, bevel=0.0, tags=tags)
        ha, hp = B.shard(f"rf_bush{sx}", hb, 0.02, 0.15, A, slope=0.03, groove=0.014, panel_h=0.016, tags=tags)
        slot = B.rpoly((x0 + x1) / 2, cy, abs(x1 - x0) - 0.12, 0.05, 0, chamfer=0.0)
        for t, nm in ((ha, "a"), (hp, "b")):
            if t is not None:
                B.cut(t, [B.loft(f"rf_bsl{sx}{nm}", slot, slot, 0.08, 0.5, K, bevel=0.0)])
        B.loft(f"rf_bslb{sx}", slot, slot, 0.07, 0.08, M["black"], bevel=0.0, tags=tags)
        B.box(f"rf_bcu{sx}", (x0 + x1) / 2, cy, abs(x1 - x0) - 0.13, 0.034, 0.08, 0.11, X["copper"], bevel=0.006,
              tags=tags)
        B.bolts(f"rf_bb{sx}", [((x0 + x1) / 2 - 0.16, cy), ((x0 + x1) / 2 + 0.16, cy)], 0.115, 0.013, S, tags=tags)
    # chevron claro sob a tampa do meio apontando para o emblema, com 2 pips azuis
    chev = [(-0.17, 0.705), (0.17, 0.705), (0.17, 0.655), (0.0, 0.535), (-0.17, 0.655)]
    hole = B.offset_poly(chev, -0.025)
    for t in tops[1]:
        B.cut(t, [B.loft(f"rf_chh{id(t) % 97}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    B.loft("rf_chb", hole, hole, 0.0, 0.03, K, bevel=0.0, tags=tags)
    cha, chp = B.shard("rf_chev", chev, 0.02, 0.13, A, slope=0.03, groove=0.014, panel_h=0.016, tags=tags)
    _ledslot("rf_chsl", 0.0, 0.655, 0.12, 0.034, 0.07, 2, M, tags, [cha, chp], vertical=False, pip_mats=X["led"],
             pw=0.018)
    # laminas em garra nos tiles das pontas, embaixo dos colares, apontando para o emblema do centro
    blade = [(-1.38, 0.75), (-1.38, 0.60), (-0.70, 0.535), (-0.60, 0.565), (-0.66, 0.645), (-1.10, 0.75)]
    for sx in (-1, 1):
        bl = _flip(sx)(blade)
        B.plate(f"rf_bl_core{sx}", B.offset_poly(bl, -0.03), 0.06, 0.10, K, slope=0.01, tags=tags)
        ba, bp = B.shard(f"rf_bl{sx}", bl, 0.09, 0.20, A, slope=0.035, groove=0.016, panel_h=0.018, tags=tags)
        _ledslot(f"rf_blsl{sx}", sx * 1.06, 0.655, 0.26, 0.032, 0.15, 4, M, tags, [ba, bp], vertical=False,
                 pip_mats=X["led"], pw=0.018)
        # respiro de persianas no canto de fora de cima (sem pintura)
        vx = sx * 1.28
        rv = B.box(f"rf_sv{sx}", vx, 1.26, 0.12, 0.24, 0.07, 0.125, KM, bevel=0.008, slope=0.012, tags=tags)
        B.cut(rv, [B.box(f"rf_svc{sx}{k}", vx, 1.185 + k * 0.05, 0.08, 0.022, 0.105, 0.3, K, bevel=0.0)
                   for k in range(4)])

    # ---- tile central: emblema de raio em 3 laminas claras sobre octogono escuro com anel de 8 laminas claras.
    # A placa verde e lisa (sem painel interno: o painel e o furo do octogono se cruzavam e deixavam um anel
    # serrilhado); o segundo degrau do bisel e o proprio anel claro sobre o contorno escuro (sem booleana no verde)
    B.plate("rf_mid", B.rpoly(0, 0, 0.92, 0.92, 0, chamfer=0.14), 0.0, 0.07, green, slope=0.03, tags=tags)
    B.plate("rf_embk", _octo(0, 0, 0.448), 0.03, 0.085, K, slope=0.008, tags=tags)
    B.plate("rf_emb", _octo(0, 0, 0.385), 0.04, 0.095, K, slope=0.01, tags=tags)
    _octring("rf_emblip", 0, 0, 0.425, 0.378, 0.05, 0.115, A, tags)
    B.bolts("rf_mcb", [(qx * 0.355, qy * 0.355) for qx in (-1, 1) for qy in (-1, 1)], 0.08, 0.015, S, tags=tags)
    bolts = []
    for k, poly in enumerate(BOLT):
        bolts.append(B.shard(f"rf_bolt{k}", poly, 0.08, 0.20, A, slope=0.025, groove=0.015, panel_h=0.015,
                             tags=tags))
    # fenda de 3 pips azuis atravessando a lamina do meio do raio
    _ledslot("rf_bsl", -0.034, 0.004, 0.21, 0.038, 0.09, 3, M, tags, list(bolts[1]), vertical=False,
             pip_mats=X["led"], pw=0.018)
    # parafusos no labio (meio das faces de cima/baixo/lados) e bornes de cobre nas diagonais do octogono
    B.bolts("rf_embb", [(0, 0.371), (0, -0.371), (0.371, 0), (-0.371, 0)], 0.12, 0.013, S, tags=tags)
    for qx in (-1, 1):
        for qy in (-1, 1):
            B.cyl(f"rf_embt{qx}{qy}", qx * 0.22, qy * 0.22, 0.105, 0.028, 0.03, X["copper"], axis="Z", verts=6,
                  bevel=0.005, tags=tags)

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

    # ---- fileira de baixo (saida): 3 placas; a do meio com seta para baixo, as laterais com respiro
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
            # linhas de painel VAZADAS na placa e no painel (o fundo escuro e o rf_under): o corte raso so no
            # painel reaplicava o bisel e virava uma cunha escura num lado so
            for t, nm in ((ba, "p"), (bp, "q")):
                if t is not None:
                    B.cut(t, [B.rbox(f"rf_bl{k}a{nm}", cx, -0.70, 0.62, 0.022, -0.01, 0.3, K, bevel=0.0),
                              B.rbox(f"rf_bl{k}c{nm}", cx + sx * 0.25, -1.25, 0.022, 0.13, -0.01, 0.3, K,
                                     rot=sx * -45, bevel=0.0)])
            vx = cx - sx * 0.08
            rv = B.box(f"rf_bv{k}", vx, -1.02, 0.36, 0.24, 0.07, 0.125, KM, bevel=0.008, slope=0.012, tags=tags)
            B.cut(rv, [B.box(f"rf_bvc{k}{i}", vx, -1.095 + i * 0.05, 0.28, 0.022, 0.105, 0.3, K, bevel=0.0)
                       for i in range(4)])
            B.bolts(f"rf_bb{k}", [(cx - 0.36, -1.36), (cx + 0.36, -1.36), (cx + sx * 0.36, -0.66)], 0.095, 0.016,
                    S, tags=tags)

    # o verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nas bordas claras)
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False
