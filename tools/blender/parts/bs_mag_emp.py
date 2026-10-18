"""Carregador EMP (EMP Magazine) - municao de pulso eletromagnetico; pilha de 4.

Mesma familia do Carregador Padrao e do Perfurante (nucleo escuro um pouco maior que as cascas, casca clara
chanfrada com bisel duplo, contador de 4 LEDs numa fenda escura), mas com cara de peca eletrica e silhueta e cor
proprias (o Padrao tem janela de balas + alca; o Perfurante tem 3 pontas afiadas + tampa clara):
  * cabeca clara em cunha (frente = +Y, chanfros grandes) com linhas de painel e a fenda vertical escura
    mostrando a celula capacitora em pe (cilindro azul aceso, 2 aneis escuros de segmento, tampas de aco), no
    lugar das balas de latao;
  * dois pinos de contato curtos e rombudos, juntos na ponta da cunha (garfo de "taser"): bloco isolante
    escuro, hastes de aco e pontas de cobre;
  * contador de 4 LEDs AZUIS no vao entre a cabeca e o corpo;
  * corpo azul-marinho (cor propria da linha EMP) abracado por duas bobinas de cobre (2 espiras grossas cada)
    que passam alem do contorno dos dois lados: costelas de cobre na silhueta; parafusos na faixa do meio;
  * pe azul-marinho chanfrado com borne de aco (sem alca e sem tampa clara: a base da unidade fica escura).
Os brilhos usam forca baixa (azul eletrico sem estourar em ciano/branco).
Unidade modelada centrada na origem (eixo longo em Y, ~0.74 x 1.04), cabendo em 1 x 1; o renderizador escala
para a pilha (stack_layout igual ao do Perfurante: lado a lado, piramide e 2 x 2).
A fabrica (parts/bs_factory_mag_emp.py) usa esta unidade em miniatura no berco de carga e os mesmos materiais.
"""

import bs3d as B
import models as Mo  # noqa: F401  (contrato dos modelos)

PART = {
    "id": "rafaeltessaro.bs_mag_emp",
    "kind": "resource",
    "accent": "blue",
    "unit_scale": 0.40,
    "icon_scale": 0.78,
    # pilha organizada: 1 no centro, 2 lado a lado, 3 em piramide, 4 em 2 x 2 (costelas de cobre sem encostar)
    "stack_layout": {
        1: [(0, 0, 0)],
        2: [(-0.17, 0, 0), (0.17, 0, 0)],
        3: [(-0.17, -0.222, 0), (0.17, -0.222, 0), (0, 0.222, 0)],
        4: [(-0.17, -0.222, 0), (0.17, -0.222, 0), (-0.17, 0.222, 0), (0.17, 0.222, 0)],
    },
    "stack_rot": [0, 1.5, -1.5, 1, -2, 2],
}

NAVY = (0.055, 0.095, 0.21)        # casca azul-marinho da linha EMP
COPPER = (0.90, 0.45, 0.22)        # cobre das bobinas
BLUE = (0.18, 0.42, 1.0)           # azul eletrico (LEDs, celula)

# geometria compartilhada (a fabrica conta com estas medidas)
HALF_W = 0.37                      # meia largura nas costelas de cobre


def mats():
    """Materiais da linha EMP (os mesmos nomes na fabrica: o cache do bs3d devolve o mesmo material)."""
    return {
        # pitfall: desgaste de quina em malha pequena clareia a pintura escura inteira -> wear 0
        "navy": B.mat_paint("emp_navy", NAVY, rough=0.40, metal=0.35, wear=0.0, grime=0.03, scale=5),
        "copper": B.mat_metal("copper", COPPER, rough=0.22, metal=1.0),
        "silver": B.mat_metal("silver", (0.80, 0.82, 0.86), rough=0.16, metal=1.0),
        # azul eletrico SEM saturar (forca baixa: o canal G nao estoura e o azul nao vira ciano/branco)
        "cell": B.mat_glow("emp_cell", (0.15, 0.38, 1.0), 0.8),
        "led": B.mat_glow("emp_led", BLUE, 1.5),
        "led_dim": B.mat_glow("emp_led_dim", BLUE, 0.55),
    }


def _band(name, cy, X, M, tags):
    """Bobina de cobre abracando o corpo: base escura + 2 espiras grossas (cilindros em X) que passam do contorno
    dos dois lados (costelas de cobre na silhueta)."""
    B.box(name + "_core", 0, cy, 2 * HALF_W - 0.03, 0.105, 0.03, 0.272, M["core_mid"], bevel=0.006, tags=tags)
    for k, dy in enumerate((-0.026, 0.026)):
        B.cyl(f"{name}_t{k}", 0, cy + dy, 0.292, 0.025, 2 * HALF_W, X["copper"], axis="X", verts=16, bevel=0.0,
              tags=tags)


def item(M, T="item"):
    tags = (T,)
    X = mats()
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    # nucleo escuro so um pouco maior que as cascas: moldura escura fina, cabeca em cunha, pe chanfrado
    core = [(-0.25, -0.505), (0.25, -0.505), (0.32, -0.435), (0.32, 0.20), (0.14, 0.425), (-0.14, 0.425),
            (-0.32, 0.20), (-0.32, -0.435)]
    B.plate("emp_core", core, 0.0, 0.27, K, slope=0.012, tags=tags)

    # ---- cabeca clara em cunha (bisel duplo) com a fenda vertical da celula capacitora
    head = [(-0.295, 0.035), (0.295, 0.035), (0.295, 0.19), (0.125, 0.405), (-0.125, 0.405), (-0.295, 0.19)]
    ha, hp = B.shard("emp_head", head, 0.04, 0.33, A, slope=0.03, groove=0.015, panel_h=0.025, tags=tags)
    win = B.rpoly(0, 0.215, 0.13, 0.25, 0, chamfer=0.02)
    for t, k in ((ha, "a"), (hp, "b")):
        B.cut(t, [B.loft(f"emp_win{k}", win, win, 0.26, 0.8, K, bevel=0.0)])
    B.loft("emp_winbed", win, win, 0.255, 0.262, M["black"], bevel=0.0, tags=tags)
    # linhas de painel: diagonais paralelas aos chanfros da cunha e cortes nos cantos de baixo
    # (corta casca e painel ate perto do leito: o fundo fica escuro e a linha le nos 64 px)
    for t, k in ((ha, "a"), (hp, "b")):
        if t is not None:
            B.cut(t, [B.rbox(f"emp_hpl{k}{sx}", sx * 0.185, 0.235, 0.024, 0.13, 0.27, 0.6, K, rot=sx * 38,
                             bevel=0.0) for sx in (-1, 1)] +
                  [B.rbox(f"emp_hpb{k}{sx}", sx * 0.205, 0.085, 0.10, 0.024, 0.27, 0.6, K, bevel=0.0)
                   for sx in (-1, 1)])
    # celula capacitora em pe na fenda: cilindro azul aceso, 2 aneis escuros de segmento, tampas de aco
    cz, cy = 0.285, 0.215
    B.cyl("emp_cell", 0, cy, cz, 0.045, 0.21, X["cell"], axis="Y", verts=16, bevel=0.0, tags=tags)
    for k, y in enumerate((cy - 0.037, cy + 0.037)):
        B.cyl(f"emp_cring{k}", 0, y, cz, 0.05, 0.018, KM, axis="Y", verts=16, bevel=0.0, tags=tags)
    for sy in (-1, 1):
        B.cyl(f"emp_ccap{sy}", 0, cy + sy * 0.112, cz, 0.054, 0.026, S, axis="Y", verts=16, bevel=0.004, tags=tags)

    # ---- 2 pinos de contato rombudos e juntos na ponta da cunha (garfo de "taser"): bloco isolante escuro,
    # hastes de aco e pontas de cobre
    B.box("emp_nose", 0, 0.418, 0.20, 0.05, 0.12, 0.31, KM, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        px = sx * 0.062
        B.box(f"emp_prong{sx}", px, 0.475, 0.052, 0.09, 0.17, 0.27, X["silver"], bevel=0.008, tags=tags)
        B.box(f"emp_ptip{sx}", px, 0.53, 0.052, 0.026, 0.17, 0.27, X["copper"], bevel=0.008, tags=tags)

    # ---- vao com o contador de 4 LEDs azuis
    gy = 0.0
    B.box("emp_gapbed", 0, gy, 0.46, 0.04, 0.27, 0.276, M["black"], bevel=0.0, tags=tags)
    for i in range(4):
        B.box(f"emp_led{i}", -0.15 + i * 0.10, gy, 0.058, 0.028, 0.276, 0.286, X["led"], bevel=0.0, tags=tags)

    # ---- corpo azul-marinho abracado por 2 bobinas de cobre (o azul-marinho aparece entre elas)
    body = B.rpoly(0, -0.215, 0.60, 0.36, 0, chamfer=0.03)
    ba, bp = B.shard("emp_body", body, 0.04, 0.27, X["navy"], slope=0.025, groove=0.012, panel_h=0.02, tags=tags)
    _band("emp_bandA", -0.115, X, M, tags)
    _band("emp_bandB", -0.30, X, M, tags)
    # parafusos de aco na faixa azul-marinho entre as bobinas
    B.bolts("emp_bb", [(-0.20, -0.2075), (0.20, -0.2075)], 0.30, 0.016, S, tags=tags)

    # ---- pe azul-marinho chanfrado com borne de aco num recesso escuro
    foot = [(-0.235, -0.49), (0.235, -0.49), (0.30, -0.425), (0.30, -0.405), (-0.30, -0.405), (-0.30, -0.425)]
    fa, fp = B.shard("emp_foot", foot, 0.04, 0.27, X["navy"], slope=0.02, groove=0.012, panel_h=0.015, tags=tags)
    B.box("emp_fterm", 0, -0.447, 0.20, 0.04, 0.27, 0.31, S, bevel=0.008, tags=tags)
