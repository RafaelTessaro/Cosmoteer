"""Railgun Tupa (2.0): carregador, cano e ponta, tipo "layered" (tools/blender/render_layered.py).

    $PY tools/blender/render_layered.py bs_rail [--part bs_rail_barrel] [--only roof,trilhos] [--quick] [--out DIR]

Pedido do usuario: "canhao blindado naval-futurista no mesmo estilo das nossas armas; 3 partes como o railgun do
jogo: carregador, cano e ponta; FIXO; energia e municao so pelo carregador; 2 tripulantes; animacao do projetil
entrando no cano e do canhao carregando ate disparar; projetil enorme".

REFERENCIA DO USUARIO (r4): depois da versao violeta aprovada, o usuario mandou uma imagem de referencia ("achei muito
estiloso e combina com o que estamos usando, acho que poderia fazer algo baseado nisso"): as 3 partes empilhadas,
boca em cima. O Tupa foi refeito a partir dela, mantendo o contrato do jogo (tamanhos, arquivos, camadas, rects e
quadros do spec e do kit de teste):
  * BLINDAGEM BRANCA FIXA (placas claras de bisel duplo; nao e pintura) sobre um nucleo de GRAFITE (gunmetal);
  * energia AZUL ELETRICO PROFUNDO (45, 115, 255) com o nucleo BRANCO-AZULADO (205, 228, 255) na carga cheia,
    separado do ciano + cobre da familia PEM (aqui NUNCA cobre);
  * detalhes pequenos LARANJA (tinta: tampas das capsulas, molas, insertos, cabecas de parafuso, trava do paiol);
  * carregador: coluna de CAPSULAS azuis acesas no meio (o paiol, visto por uma janela no teto), molas laranja dos
    dois lados, placas brancas nas laterais, a trava laranja embaixo;
  * cano: corpo estreito (o carregador e mais largo, como na referencia), trilhos brancos nas bordas, o canal aberto
    no meio e 3 CINTAS EM segmentadas (uma por quadro) cruzando o canal; a do meio com a garra lateral (bloco branco
    + inserto laranja);
  * ponta: cabeca em forma de escudo, o canal AZUL aberto na frente com o clarao na garganta, as grandes cunhas
    brancas dos lados e a fenda estreita do nucleo atras.
O brilho "sempre aceso" da referencia virou as luzes do jogo: apagado em repouso (lentes escuras), a onda de carga
(trilhos1..9 + carga1..8 no cano, carga1..6 na ponta, luz_culatra1..2) acende o canal em azul e a carga cheia
traz o nucleo branco-azulado e o clarao da boca. Teto: o verde (pintura da nave) fica nos cantos e faixas FORA
da blindagem; as placas brancas nao sao pintadas.

Linguagem visual (STYLE.md secao 1): nucleo escuro + blindagem clara de bisel duplo (B.shard), frestas pretas entre
as placas, LEDs so em recessos escuros, emissivos pequenos no teto (o resto e luz de carga, aditiva, que apaga).

Juncao entre canos sem emenda: tudo o que cruza a emenda (fundo do canal, trilhos, labio do canal, base escura) e
periodico em y com periodo que divide 3 e passa da borda da camera; as placas (bochechas, trilhos brancos, convés)
terminam com chanfro numa fresta que fica identica dos dois lados da emenda. Cintas EM a cada 1 quadro (y -1, 0, 1
do cano): a fresta da emenda cai no meio entre duas cintas, com o mesmo passo de dentro do cano.

Coordenadas do modelo: centradas na peca, +X direita, +Y frente (topo da imagem), 1 unidade = 1 quadro.
"""

import math

import bs3d as B

# ============================================================================ paleta (referencia do usuario)
BLUE = (0.026, 0.171, 1.0)           # azul eletrico profundo (45, 115, 255) na vista Standard com forca 1
BLUE_HI = (0.13, 0.43, 1.0)          # azul claro (100, 175, 255): bobinas acesas, o anel da garganta
CORE_W = (0.62, 0.80, 1.0)           # nucleo branco-azulado (205, 228, 255) da carga cheia
ORANGE = (1.0, 0.42, 0.035)          # LED laranja de estado (fraco), puxado para o laranja-ouro da referencia
# critica ref-r1: o laranja (166, 99, 45; matiz 27 graus) caia no cobre da familia PEM (matiz 26). A referencia e
# laranja-OURO (matiz ~37): a tinta e a mola foram para o ouro mais claro (NUNCA cobre)
ORANGE_P = (0.60, 0.25, 0.020)       # tinta laranja-ouro (~215, 145, 40 com a luz da cena; matiz ~36 graus)
SPRING_C = (0.80, 0.44, 0.030)       # mola: laranja-ouro claro (brilho ~235, 185, 50 em cima; matiz ~40 graus)
LENS_B = (0.004, 0.010, 0.050)       # lente azul apagada (STYLE 11.5)
GRAPH_D = (0.020, 0.021, 0.025)      # grafite escuro (estrutura sob as placas)
# canal em repouso: AZUL PROFUNDO (critica ref-r1: o canal apagado lia como fenda cinza/preta; a identidade da
# referencia e o canal azul): o leito ~ (20, 35, 80) no difuso, sem emissao (a luz e so a carga)
TROUGH = (0.007, 0.018, 0.085)       # leito do canal (aco anodizado azul profundo)
LANE_B = (0.004, 0.011, 0.060)       # faixa central do leito (caminho do projetil): lente azul mais escura
RAIL = (0.30, 0.31, 0.33)            # trilho de aco medio (sob a carga vira azul, nao ciano)
TUNG = (0.36, 0.37, 0.39)            # tungstenio claro (igual ao slug de bs_shells2)
JAWFACE = (0.13, 0.135, 0.145)       # face das folhas da culatra (le sobre a camara preta)
GROOVE_MAX = 0.016                   # anel plano entre o chanfro e o painel (fino: sem "contorno" a 1x)

# cores das camadas PIL (lights_add, sRGB 0..255)
P_BLUE = (30, 100, 255)
P_BLUE_HI = (95, 160, 255)
P_CORE = (200, 225, 255)
# nucleo do eixo nos planos de carga (critica ref-r1: o nucleo cheio somado ao azul estourava o verde e saia
# (196, 255, 255), ciano = familia PEM): parcelas com menos verde para a SOMA dar ~ (205, 228, 255)
P_CORE_AX = (212, 196, 255)
P_HALO_AX = (60, 115, 255)

# geometria comum (quadros, centrada na peca)
CH = 0.40                            # meia largura do canal aberto no teto do cano (x 1.10-1.90 da peca)
RAIL_IN, RAIL_OUT = 0.215, 0.305     # faces do trilho
RING_IN, RING_OUT = 0.335, 0.64      # blocos laterais dos aneis EM (trilhos, sob as cintas do teto)
TR = 0.43                            # meia largura do fundo do canal
LANE = 0.13                          # meia largura da faixa central escura do fundo (caminho do projetil)
GLOW_HW = 0.62                       # meia largura dos planos de carga (identica em todas as pecas)
EXT = 0.14                           # o que passa da borda da camera (sem chanfro na emenda)
# cano: corpo estreito (referencia: o carregador e mais largo que o cano)
CHEEK_IN, CHEEK_OUT = CH + 0.035, 0.765  # bochecha de grafite ao lado do canal
FR_IN, FR_OUT = 0.795, 0.895         # moldura interna de grafite (a barra escura da referencia antes do trilho branco)
WR_IN, WR_OUT = 0.925, 1.10          # trilho branco (blindagem clara fixa) na borda do corpo: estreito (referencia)
DECK_IN = 1.145                      # convés pintado (verde) de DECK_IN ate a borda da peca
CLAMP_YS = (-1.0, 0.0, 1.0)          # cintas EM do cano (periodo 1: a emenda cai no meio entre duas)
# cinta = TAMBOR compacto de grafite escuro (critica ref-r1: as cintas largas e claras liam como escada): so um
# pouco mais larga que o canal (as bochechas escuras aparecem dos 2 lados), 3 bandas roliças segmentadas por
# nervuras e as 2 COSTURAS entre elas transparentes (a luz azul da bobina e da carga vaza por elas)
CLAMP_HW, CLAMP_HY = 0.50, 0.20      # meia largura / meia altura do tambor
BAND_DY, BAND_R = 0.110, 0.038       # passo e raio das 3 bandas do tambor
DRUM_SEAM = 0.055                    # y das 2 costuras (entre as bandas) e a meia altura delas
SEAM_HY, SEAM_HX = 0.017, 0.40
WIN_X = 0.35                         # emissor da bobina (bloco do trilho) visto na ponta das costuras
SEAM = 0.025                         # meia fresta das placas na emenda dos canos

# ============================================================================ pecas (PARTS)
# icone: a culatra ABERTA com o dardo assentado aparece pela fenda do teto e a coluna de capsulas pela janela
_LOADER_ICON = {"size": [69, 92], "layers": ["floor", "projeteis", "capacitores", "weapon", "culatra_carrega", "roof"],
                "pick": {"projeteis": 5, "capacitores": 2, "culatra_carrega": 5}}
_NOTE_TOGGLE = ("culatra_abre e culatra_carrega ficam na MESMA camada (walls) e no mesmo lugar: ligue uma OU outra "
                "(toggle), nunca as duas juntas (a ordem de desenho dentro de uma camada nao e garantida); "
                "culatra_carrega1..6 ja traz as folhas abertas.")
_NOTE_SLUG = ("culatra_projetil.png = o dardo assentado na camara, em doodads_low (ABAIXO das folhas da culatra, que "
              "estao em walls), rect [1,0,1,2]: ResourceSprites de LoadedAmmo (1 nivel, HasZeroResourceSprite) dentro "
              "de um ToggledComponents com AmmoHideToggle invertido (como MunicaoNaCulatra, kit de teste "
              "bs2t_rail_carregador.rules:667-691). E o mesmo dardo, no mesmo lugar, de culatra_carrega6 (pixels do "
              "dardo identicos): quando a carga termina e a culatra fecha (culatra_abre ao contrario), as folhas fecham "
              "POR CIMA dele; o AmmoHideToggle o esconde quando o tiro sai. Todos os dardos do Tupa sao o MESMO "
              "objeto (o modelo 'slug' de bs_shells2: haste de tungstenio claro, 6 aletas, 4 colares EM azuis, ponta "
              "branco-azulada, colar laranja): 1,78 quadro na camara (culatra_*), 2,9 no cano (slug.png) e em voo. "
              "culatra_carrega1..6 e culatra_projetil somem suavemente nos 0,12 quadro de baixo do rect (o dardo "
              "sobe do elevador em vez de sair cortado).")
_NOTE_MAG = ("projeteis1..6 (doodads_low [0.6,2.8,1.8,1.0], ResourceSprites do SlugMagazine 12 -> 2 dardos por nivel): "
             "a COLUNA DE CAPSULAS da referencia do usuario. Cada capsula de contencao (luva azul acesa, tampas "
             "laranja, o filete branco-azulado = os dardos dentro) leva 2 dardos: nivel k = k capsulas, empurradas "
             "para a frente (o lado do elevador) pela placa seguidora; aparecem pela janela do teto. Nivel 0 = "
             "nenhum sprite (o poco vazio do piso).")
_NOTE_PALETTE = ("Paleta nova (referencia do usuario, substitui palette.rail violeta/ouro): azul [45,115,255], azul "
                 "claro [100,175,255], nucleo branco-azulado [205,228,255], laranja [230,135,40] so em detalhes "
                 "pintados e LEDs fracos de estado; NUNCA cobre. light_blob do projetil (roof_lights_fancy): "
                 "VertexColor sugerido [0.10, 0.32, 1.0] (pouco vermelho e verde: nao lava o casco branco).")
_NOTE_WAKE = ("DESCARGA (critica r2: o climax nao pode murchar): carga1..8 + trilhos (canos), carga1..6 (ponta) e "
              "luz_culatra NAO apagam todos no ProjectileStartTrigger. Cada cano SEGURA a carga cheia (trilhos9 + "
              "carga8) ate a PONTA do dardo entrar nele e entao descarrega (trilhos1, carga escondida): o canal escuro "
              "atras e o rastro que persegue o dardo, o cano a frente continua carregado ate o dardo chegar e o "
              "dardo claro corre sempre no canal escuro (licao 1: sob a carga cheia ele some). luz_culatra e o 1o "
              "cano descarregam no ProjectileStartTrigger (a ponta do dardo ja esta no 1o cano); a ponta (carga + "
              "clarao da garganta) descarrega junto com o clarao (EmissionTriggered / ProjectileFinished). Ligacao "
              "(variante 'delay' de rail.charge_wave): em cada cano um DelayTrigger iniciado pelo ProjectileStartTrigger "
              "desliga um toggle 'CargaRetida' que segura o nivel cheio; Delay_i = t(3i - 4) para o cano i (1 = junto "
              "da culatra), com t(d) = (-6 + sqrt(36 + 88 d / T)) / (44 / T) (t(d <= 0) = 0), T = (3N + 4) / 28 s "
              "(cinematica do RailgunProjectile 6 -> 50 quadros/s em 3N + 4 quadros = barrel_anim_s do spec). Tabela "
              "(s, cano 1..N): N1 [0]; N2 [0, 0.14]; N3 [0, 0.15, 0.27]; N4 [0, 0.16, 0.29, 0.38]; N5 [0, 0.17, 0.31, "
              "0.41, 0.50]; N6 [0, 0.18, 0.33, 0.44, 0.53, 0.61]. O cano sabe i pela corrente do carregador e N - i + 1 "
              "pela corrente reversa da ponta. Minimo aceitavel se o atraso por cano nao der: segurar trilhos e carga "
              "acesos ate o EmissionTriggered e apagar tudo junto com o clarao. Nunca reacender um plano de carga "
              "depois do disparo (nem a ponta).")
PARTS = {
    "bs_rail_loader": {
        "id": "rafaeltessaro.bs_rail_loader", "kind": "layered", "size": [3, 4], "accent": "blue",
        "walls": {"open": [["top", 1.0, 2.0]]},
        "crew_pos": [[0.6, 1.6], [2.4, 1.6]],
        "layers": [
            {"name": "floor", "fn": "loader_floor", "game_layer": "floors", "opaque": True},
            {"name": "projeteis", "fn": "loader_magazine", "game_layer": "doodads_low", "rect": [0.6, 2.8, 1.8, 1.0],
             "file": "projeteis{i}.png", "levels": 6, "islands": True},
            {"name": "culatra_projetil", "fn": "loader_chambered", "game_layer": "doodads_low",
             "rect": [1.0, 0.0, 1.0, 2.0], "file": "culatra_projetil.png", "islands": True,
             "fade": {"bottom": 0.12}, "same_as": {"layer": "culatra_carrega", "index": 6}},
            # o mesmo console nos 2 postos (simetrico): rects no meta.json
            {"name": "consola", "fn": "loader_console", "game_layer": "walls", "rect": [0.1, 1.1, 1.0, 1.0],
             "at": [[0.1, 1.1], [1.9, 1.1]], "file": "consola{i}.png", "frames": 4, "interval": 0.1, "islands": True},
            {"name": "culatra_abre", "fn": "loader_jaws", "game_layer": "walls", "rect": [1.0, 0.0, 1.0, 1.0],
             "file": "culatra_abre{i}.png", "frames": 3, "interval": 0.0666, "islands": True},
            {"name": "culatra_carrega", "fn": "loader_load", "game_layer": "walls", "rect": [1.0, 0.0, 1.0, 2.0],
             "file": "culatra_carrega{i}.png", "frames": 6, "interval": 0.2, "islands": True,
             "fade": {"bottom": 0.12}},
            {"name": "weapon", "fn": "loader_breech", "game_layer": "weapons", "rect": [0.0, 0.0, 3.0, 1.0],
             "normals": True, "islands": True},
            {"name": "capacitores", "fn": "loader_caps", "game_layer": "doodads_high", "rect": [0.0, 2.1, 3.0, 1.0],
             "file": "capacitores{i}.png", "levels": 3, "islands": True},
            {"name": "luz_culatra", "fn": "pil:glow_loader", "game_layer": "lights_add", "rect": [0.0, 0.0, 3.0, 1.0],
             "file": "luz_culatra{i}.png", "levels": 2, "blend": "add"},
            {"name": "roof", "fn": "loader_roof", "game_layer": "roofs", "normals": True, "islands": True,
             "despill": True},
        ],
        "icon": _LOADER_ICON,
        "blueprint_layers": ["weapon", "roof"],
        "notes": [_NOTE_PALETTE, _NOTE_TOGGLE, _NOTE_SLUG, _NOTE_MAG, _NOTE_WAKE,
                  "consola: o mesmo sprite nos 2 postos da tripulacao (rects [0.1,1.1] e [1.9,1.1], crew_pos).",
                  "roof.png: 2 janelas TRANSPARENTES - a fenda da culatra (x 1.0-2.0, y 0.1-0.9 da peca: a "
                  "abertura/carga/fechamento da culatra) e a JANELA ALTA (x 1.1-1.9, y 1.04-3.76): embaixo a coluna "
                  "de capsulas (nivel do paiol), acima o elevador e a bandeja por onde o dardo sobe na carga "
                  "(culatra_carrega). O verde fica so nos cantos, fora da blindagem.",
                  "luz_culatra1..2 (lights_add [0,0,3,1]): so a costura das folhas, as lentes das folhas e os emissores "
                  "da camara acendem (mascarado: nada e somado sobre a blindagem); 2 = nucleo branco-azulado."],
    },
    "bs_rail_barrel": {
        "id": "rafaeltessaro.bs_rail_barrel", "kind": "layered", "size": [3, 3], "accent": "blue",
        "walls": {"open": [["top", 1.0, 2.0], ["bottom", 1.0, 2.0]]},
        "layers": [
            {"name": "floor", "fn": "cano_floor", "game_layer": "floors", "opaque": True},
            {"name": "trilhos", "fn": "cano_rails", "game_layer": "doodads_low", "file": "trilhos{i}.png",
             "levels": 9, "islands": True},
            {"name": "carga", "fn": "pil:glow_cano", "game_layer": "lights_add", "file": "carga{i}.png", "levels": 8,
             "blend": "add"},
            {"name": "roof", "fn": "cano_roof", "game_layer": "roofs", "normals": True, "islands": True,
             "despill": True},
        ],
        "icon": {"size": [69, 69], "layers": ["floor", "trilhos", "roof"], "pick": {"trilhos": 6},
                 "lights": {"carga": [5, 0.8]}},
        "blueprint_layers": ["trilhos", "roof"],
        "notes": [_NOTE_PALETTE, _NOTE_WAKE,
                  "roof.png: canal aberto x 1.10-1.90 em todo o comprimento, cruzado por 3 CINTAS EM (y 0.5, 1.5 e 2.5 "
                  "da peca; referencia do usuario: aneis segmentados a cada 1 quadro) que escondem o dardo por um "
                  "instante ('dentro do cano'). Cada cinta tem 3 janelas TRANSPARENTES no anel do meio: "
                  "o nucleo da carga e as bobinas dos trilhos1..9 acendem por elas.",
                  "carga1..8: plano aditivo de largura identica em todos os canos (as emendas casam); mais forte nas 3 "
                  "bobinas (y 0.5, 1.5, 2.5 da peca)."],
    },
    "bs_rail_muzzle": {
        "id": "rafaeltessaro.bs_rail_muzzle", "kind": "layered", "size": [3, 4], "accent": "blue",
        "walls": {"open": [["bottom", 1.0, 2.0], ["top", 0.92, 2.08]]},
        "layers": [
            {"name": "floor", "fn": "ponta_floor", "game_layer": "floors", "opaque": True},
            {"name": "trilhos", "fn": "ponta_rails", "game_layer": "doodads_low", "islands": True},
            {"name": "weapon", "fn": "ponta_crown", "game_layer": "weapons", "rect": [0.0, 0.0, 3.0, 1.5],
             "normals": True, "islands": True},
            {"name": "carga", "fn": "pil:glow_ponta", "game_layer": "lights_add", "file": "carga{i}.png", "levels": 6,
             "blend": "add"},
            {"name": "roof", "fn": "ponta_roof", "game_layer": "roofs", "normals": True, "islands": True,
             "despill": True},
            # o projetil dentro do cano (ChainedTo Projectile): o mesmo objeto do slug em voo (bs_shells2)
            {"name": "slug", "fn": "slug_sprite", "game_layer": "walls", "rect": [1.1, 0.5, 0.8, 3.0],
             "samples": 64},
            {"name": "slug_glow", "fn": "pil:glow_slug", "game_layer": "lights_add", "rect": [0.9, 0.3, 1.2, 3.4],
             "blend": "add"},
        ],
        "icon": {"size": [69, 92], "layers": ["floor", "trilhos", "weapon", "roof"], "lights": {"carga": [4, 0.8]}},
        "blueprint_layers": ["weapon", "roof"],
        "notes": [_NOTE_PALETTE, _NOTE_WAKE,
                  "weapon.png [0,0,3,1.5] = a frente em escudo: a BOCA aberta (x 1.13-1.87 na frente, garganta "
                  "estreita atras) e TRANSPARENTE (o dardo sai por ela; o fundo, os trilhos e o emissor da garganta "
                  "estao no piso/trilhos); paredes de grafite, tiras brancas, bochechas e ombros brancos.",
                  "roof.png: canal largo so na emenda (x 1.1-1.9), a cinta EM em y 3.5 da peca e depois a FENDA "
                  "estreita do nucleo (x 1.34-1.66) ate a boca, entre os segmentos de grafite e as cunhas brancas.",
                  "walls.png da ponta: aberta embaixo (emenda com o cano) e em cima na boca (x 0.92-2.08), por onde o "
                  "projetil sai; a moldura nao atravessa a boca.",
                  "carga1..6: a onda sobe da emenda ate a boca; na boca o plano fica DENTRO da abertura; 5 e 6 enchem "
                  "a boca de azul e acendem o clarao branco-azulado da garganta (y 1.38 da peca).",
                  "slug.png (walls) e slug_glow.png (lights_add): ChainedTo Projectile; o halo e oco para o projetil "
                  "claro continuar legivel."],
    },
}


# ============================================================================ materiais
def _spec(m, v):
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = v
    return m


LIGHT_XY = (-0.7071, 0.7071)         # direcao (vista de cima) de onde vem a luz principal das torres: cima-esquerda


def lit_mat(name, flat, lit, mid, dark, rough=0.40, metal=0.25, spec=0.35, grime=0.05, scale=5.0, chips=0.0,
            chip_scale=15.0, chip_tint=(0.60, 0.56, 0.50)):
    """Blindagem com o bisel "pintado pela luz" (estrutura de valores da familia, critica r2): a cor de base depende
    da normal de cada face. Face de cima (plana) = flat; chanfro virado para a luz (cima/esquerda) = lit; de lado
    para a luz = mid; virado para longe (baixo/direita) = dark. A luz da cena (sol de cima-esquerda) reforca o
    mesmo sentido. Funciona com booleanas e bisel (le a normal no shader), sem material por face."""
    import bpy
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], sep.inputs[0])
    dot = N.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (LIGHT_XY[0], LIGHT_XY[1], 0.0)
    L.new(geo.outputs["Normal"], dot.inputs[0])
    sq = N.new("ShaderNodeMath")
    sq.operation = "MULTIPLY"
    L.new(sep.outputs[2], sq.inputs[0])
    L.new(sep.outputs[2], sq.inputs[1])
    om = N.new("ShaderNodeMath")
    om.operation = "SUBTRACT"
    om.inputs[0].default_value = 1.0
    L.new(sq.outputs[0], om.inputs[1])
    tt = N.new("ShaderNodeMath")
    tt.operation = "SQRT"
    tt.use_clamp = True
    L.new(om.outputs[0], tt.inputs[0])
    tmax = N.new("ShaderNodeMath")
    tmax.operation = "MAXIMUM"
    tmax.inputs[1].default_value = 1e-3
    L.new(tt.outputs[0], tmax.inputs[0])
    cos = N.new("ShaderNodeMath")
    cos.operation = "DIVIDE"
    L.new(dot.outputs["Value"], cos.inputs[0])
    L.new(tmax.outputs[0], cos.inputs[1])
    u = N.new("ShaderNodeMath")
    u.operation = "MULTIPLY_ADD"
    u.use_clamp = True
    u.inputs[1].default_value = 0.5
    u.inputs[2].default_value = 0.5
    L.new(cos.outputs[0], u.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.18, (*dark, 1)
    els[1].position, els[1].color = 0.82, (*lit, 1)
    e = els.new(0.5)
    e.color = (*mid, 1)
    L.new(u.outputs[0], ramp.inputs[0])
    w = N.new("ShaderNodeMapRange")
    w.inputs[1].default_value = 0.20
    w.inputs[2].default_value = 0.55
    L.new(tt.outputs[0], w.inputs[0])
    fl = N.new("ShaderNodeRGB")
    fl.outputs[0].default_value = (*flat, 1)
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(w.outputs[0], mix.inputs[0])
    L.new(fl.outputs[0], mix.inputs[6])
    L.new(ramp.outputs[0], mix.inputs[7])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6
    g = N.new("ShaderNodeMapRange")
    g.inputs[3].default_value = 1.0
    g.inputs[4].default_value = 1.0 - grime
    L.new(noise.outputs["Fac"], g.inputs[0])
    mul = N.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    L.new(mix.outputs[2], mul.inputs[6])
    L.new(g.outputs[0], mul.inputs[7])
    out = mul.outputs[2]
    if chips > 0:
        # desgaste leve: lascas pequenas e esparsas (ruido na posicao do mundo, ~3-5 px a 1x) num cinza quente
        # (g <= r: o shader de pintura do jogo nunca as toma por verde)
        cn = N.new("ShaderNodeTexNoise")
        cn.inputs["Scale"].default_value = chip_scale
        cn.inputs["Detail"].default_value = 3
        L.new(geo.outputs["Position"], cn.inputs["Vector"])
        cf = N.new("ShaderNodeMapRange")
        cf.inputs[1].default_value = 0.60
        cf.inputs[2].default_value = 0.66
        cf.inputs[3].default_value = 0.0
        cf.inputs[4].default_value = chips
        cf.clamp = True
        L.new(cn.outputs["Fac"], cf.inputs[0])
        ch = N.new("ShaderNodeMix")
        ch.data_type = "RGBA"
        ch.blend_type = "MULTIPLY"
        L.new(cf.outputs[0], ch.inputs[0])
        L.new(out, ch.inputs[6])
        ch.inputs[7].default_value = (*chip_tint, 1)
        out = ch.outputs[2]
    L.new(out, b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    return m


# grafite (gunmetal): critica ref-r1 (estrutura de valores): o Tupa lia cinza-e-branco (mediana do cano 98 contra 68
# na referencia, 24% de escuro contra 43%). O painel de grafite desceu para o gunmetal ESCURO da referencia (face
# ~60-70); os chanfros do bisel duplo continuam acesos (STYLE 1: chanfro claro ~195-215, sombra ~60-80, frestas < 25)
EDGE_V = dict(flat=(0.020, 0.021, 0.024), lit=(0.72, 0.73, 0.76), mid=(0.20, 0.205, 0.215),
              dark=(0.050, 0.052, 0.058))
GRAPH_V = dict(flat=(0.032, 0.033, 0.038), lit=(0.30, 0.305, 0.32), mid=(0.070, 0.072, 0.079),
               dark=(0.016, 0.017, 0.019))
# gunmetal mais escuro ainda: corpo dos tambores das cintas, moldura do paiol, alojamentos das molas
GM_V = dict(flat=(0.022, 0.023, 0.026), lit=(0.26, 0.265, 0.28), mid=(0.050, 0.052, 0.057),
            dark=(0.010, 0.010, 0.012))
# bandas roliças dos tambores e tampas cilindricas das molas: a face de cima escura, o flanco de cima aceso (a luz
# vem de cima-esquerda), o de baixo quase preto: le como cilindro, nao como barra chapada
DRUM_V = dict(flat=(0.018, 0.019, 0.022), lit=(0.10, 0.102, 0.11), mid=(0.032, 0.033, 0.037),
              dark=(0.005, 0.005, 0.006))
# blindagem BRANCA fixa (referencia): face ~200-210, chanfro aceso ~240, chanfro na sombra ~95; neutra (g <= r: o
# shader de pintura do jogo nunca a toma por verde)
WHITE_V = dict(flat=(0.50, 0.496, 0.485), lit=(0.80, 0.795, 0.78), mid=(0.33, 0.327, 0.318),
               dark=(0.12, 0.119, 0.116))
WHITE_E = dict(flat=(0.37, 0.367, 0.358), lit=(0.95, 0.945, 0.93), mid=(0.36, 0.357, 0.347),
               dark=(0.070, 0.069, 0.067))
# faceta LATERAL das placas brancas em cunha (referencia: face de cima clara + lado sombreado = cunha grossa, nao
# porta chapada): branco na sombra, ~110-165 conforme o lado
WHITE_S = dict(flat=(0.24, 0.238, 0.232), lit=(0.38, 0.376, 0.366), mid=(0.24, 0.238, 0.232),
               dark=(0.155, 0.153, 0.149))


def mats(M):
    """Materiais do Tupa (nomes "rl_*": o cache do bs3d e por nome)."""
    return {
        "graph": lit_mat("rl_graph_l2", **GRAPH_V, rough=0.40, metal=0.30, spec=0.30),
        "gm": lit_mat("rl_gm_l", **GM_V, rough=0.42, metal=0.30, spec=0.28, grime=0.06),
        "drum": lit_mat("rl_drum_l", **DRUM_V, rough=0.30, metal=0.35, spec=0.30, grime=0.03, scale=4),
        "graph_d": _spec(B.mat_metal("rl_graph_d2", GRAPH_D, rough=0.45, metal=0.6), 0.3),
        "edge": lit_mat("rl_edge_l", **EDGE_V, rough=0.34, metal=0.12, spec=0.4, grime=0.03, scale=4),
        # desgaste leve (lascas) nas placas brancas: mais forte no bisel (a borda), fraco no painel
        "white": lit_mat("rl_white_l2", **WHITE_V, rough=0.36, metal=0.08, spec=0.30, grime=0.07, scale=3.5,
                         chips=0.22, chip_scale=17.0),
        "white_e": lit_mat("rl_white_e2", **WHITE_E, rough=0.34, metal=0.08, spec=0.30, grime=0.05, scale=3.5,
                           chips=0.45, chip_scale=13.0),
        "white_s": lit_mat("rl_white_s", **WHITE_S, rough=0.38, metal=0.08, spec=0.25, grime=0.06, scale=3.5,
                           chips=0.30, chip_scale=15.0),
        "gap": _spec(B.mat_metal("rl_gap", (0.003, 0.003, 0.004), rough=0.9, metal=0.0), 0.05),
        "trough": _spec(B.mat_metal("rl_trough2", TROUGH, rough=0.40, metal=0.35), 0.35),
        "lane": _spec(B.mat_metal("rl_lane", LANE_B, rough=0.20, metal=0.0), 0.6),
        "rail": B.mat_metal("rl_rail", RAIL, rough=0.26, metal=0.85),
        "rib": _spec(B.mat_metal("rl_rib2", (0.040, 0.050, 0.085), rough=0.40, metal=0.5), 0.3),
        "spring": _spec(B.mat_metal("rl_spring", SPRING_C, rough=0.28, metal=0.55), 0.45),
        "tung": _spec(B.mat_metal("rl_tung", TUNG, rough=0.38, metal=0.5), 0.3),
        "lens": _spec(B.mat_metal("rl_lens_b", LENS_B, rough=0.12, metal=0.0), 0.8),
        "orange": _spec(B.mat_paint("rl_orange2", ORANGE_P, rough=0.36, metal=0.30, wear=0.0, grime=0.05, scale=6),
                        0.35),
        "void": _spec(B.mat_metal("rl_void", (0.002, 0.002, 0.003), rough=1.0, metal=0.0), 0.0),
        "jawface": _spec(B.mat_paint("rl_jawface", JAWFACE, rough=0.36, metal=0.25, wear=0.10, grime=0.04, scale=4),
                         0.4),
        "green": B.mat_roof_green(),
        "core": M["core"], "core_mid": M["core_mid"], "steel": M["steel"], "black": M["black"],
        "armor_mid": M["armor_mid"], "armor": M["armor"],
    }


def blue(s, name=None):
    """Emissor azul com forca s (0 = lente apagada). Cor de base = lente escura azul (STYLE 11.5)."""
    if s <= 1e-4:
        return _spec(B.mat_metal("rl_lens_b", LENS_B, rough=0.12, metal=0.0), 0.8)
    m = B.mat_glow(name or f"rl_blue_{int(round(s * 100)):03d}", BLUE, s)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*LENS_B, 1)
    return m


def hot(color, s, base, name):
    m = B.mat_glow(f"rl_{name}_{int(round(s * 100)):03d}", color, s)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*base, 1)
    return m


def orange_led(s=1.0):
    """LED laranja de estado (fraco): o Tupa e azul; o laranja e so detalhe."""
    m = B.mat_glow(f"rl_orled_{int(round(s * 100)):03d}", ORANGE, s)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.02, 0.004, 1)
    return m


# ============================================================================ utilidades de forma
def gplate(name, poly, z0, z1, X, tags, slope=0.056, groove=0.028, panel_h=0.03, panel=None):
    """Placa de grafite com bisel duplo: base chanfrada clara + painel grafite elevado."""
    return B.shard(name, poly, z0, z1, X["edge"], slope=slope, groove=min(groove, GROOVE_MAX), panel_h=panel_h,
                   panel_mat=panel or X["graph"], tags=tags)


def wplate(name, poly, z0, z1, X, tags, slope=0.05, groove=0.016, panel_h=0.03):
    """Placa de blindagem BRANCA fixa com bisel duplo (a referencia do usuario): base clara + painel branco."""
    return B.shard(name, poly, z0, z1, X["white_e"], slope=slope, groove=min(groove, GROOVE_MAX), panel_h=panel_h,
                   panel_mat=X["white"], tags=tags)


def wwedge(name, outline, top, z0, z1, X, tags, panel_h=0.03):
    """Placa BRANCA em CUNHA (referencia: face de cima clara + faceta lateral sombreada = cunha grossa, nao porta
    chapada): loft do contorno (embaixo) ate a face de cima (mesmo numero de vertices; os vertices de fora entram)
    no branco de sombra (white_s) e, por cima, a face branca de bisel duplo. Devolve (lado, base, painel)."""
    side = B.loft(name + "_side", outline, top, z0, z1, X["white_s"], bevel=0.006, seg=1, tags=tags)
    a, p = B.shard(name, top, z1 - 0.004, z1 + 0.02, X["white_e"], slope=0.022, groove=0.012, panel_h=panel_h,
                   panel_mat=X["white"], tags=tags)
    return side, a, p


def mirror_x(poly):
    return [(-x, y) for x, y in reversed(poly)]


def sides(poly):
    """[(sx, poly espelhado se sx < 0)] para os 2 lados."""
    return [(1, list(poly)), (-1, mirror_x(poly))]


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
        m = mat[i] if isinstance(mat, (list, tuple)) else mat
        B.box(f"{name}_p{i}", px, py, w, h, zb, zb + 0.012, m, bevel=0.0, tags=tags)


def recess(name, cx, cy, sx, sy, z_top, X, tags, targets, depth=0.06, bed=None, rot=0.0):
    """Recesso escuro passante nos alvos com leito na peca de baixo (vent, janela, alojamento)."""
    for j, t in enumerate(targets if isinstance(targets, (list, tuple)) else [targets]):
        if t is not None:
            B.cut(t, [B.rbox(f"{name}_c{j}", cx, cy, sx, sy, z_top - depth, z_top + 0.4, X["black"], rot=rot,
                             bevel=0.0)])
    zb = z_top - depth
    B.rbox(name + "_bed", cx, cy, sx, sy, zb - 0.012, zb + 0.002, bed or X["black"], rot=rot, bevel=0.0, tags=tags)
    return zb


def bolts(prefix, pts, z, X, tags, r=0.018, mat=None):
    B.bolts(prefix, pts, z, r, mat or X["steel"], tags=tags)


def panel_lines(target, prefix, lines, z, X):
    """Linhas de painel (caixas finas, rotacionadas) cortadas no painel: [(cx, cy, comprimento, rot)]."""
    if target is None:
        return
    B.cut(target, [B.rbox(f"{prefix}{i}", cx, cy, L, 0.016, z, z + 0.6, X["black"], rot=rot, bevel=0.0)
                   for i, (cx, cy, L, rot) in enumerate(lines)])


def helix(name, cx, y0, y1, cz, R, wire, turns, mat, tags, steps=18):
    """Mola helicoidal (tubo) ao longo de Y, vista de cima: espiras inclinadas com sombreado de tubo."""
    import bpy
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = wire
    cu.bevel_resolution = 2
    cu.fill_mode = "FULL"
    sp = cu.splines.new("POLY")
    n = int(turns * steps)
    sp.points.add(n)
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        sp.points[i].co = (cx + R * math.cos(a), y0 + (y1 - y0) * t, cz + R * math.sin(a), 1.0)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def ring_levels(level, n_levels=9, n_rings=3):
    """Intensidade (0..1) de cada anel EM no nivel (1 = frio): a onda acende da culatra (anel 0) para a boca."""
    c = (level - 1) / (n_levels - 1)
    return [max(0.0, min(1.0, c * n_rings - i)) for i in range(n_rings)]


# ============================================================================ pecas do canal (comuns)
def channel_floor(name, y0, y1, X, tags, hw=TR, ribs=True, rib_y0=None, bed=None):
    """Fundo do canal (sob o projetil): calha de aco medio com nervuras transversais a cada 0.25 (periodo 3/12),
    a faixa central escura sob o caminho do projetil e o sulco-guia. y0/y1 passam da camera nas emendas."""
    B.box(name + "_bed", 0, (y0 + y1) / 2, 2 * hw, y1 - y0, -0.02, 0.012, bed or X["trough"], bevel=0.0, tags=tags)
    B.box(name + "_lane", 0, (y0 + y1) / 2, 2 * LANE, y1 - y0, 0.006, 0.014, X["lane"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"{name}_lip{sx}", sx * (hw + 0.03), (y0 + y1) / 2, 0.06, y1 - y0, -0.02, 0.02, X["black"], bevel=0.0,
              tags=tags)
    B.box(name + "_groove", 0, (y0 + y1) / 2, 0.035, y1 - y0, 0.014, 0.018, X["graph_d"], bevel=0.0, tags=tags)
    if ribs:
        start = (rib_y0 if rib_y0 is not None else -1.5 + 0.125)
        k = 0
        y = start
        while y < y1 - 0.02:
            if y > y0 + 0.02:
                w = hw - 0.02 - LANE
                for sx in (-1, 1):
                    xm = sx * (LANE + w / 2)
                    B.box(f"{name}_rib{k}{sx}", xm, y, w, 0.045, 0.012, 0.026, X["rib"], bevel=0.004, tags=tags)
                    B.box(f"{name}_ribs{k}{sx}", xm, y - 0.03, w, 0.012, 0.012, 0.016, X["black"], bevel=0.0,
                          tags=tags)
            y += 0.25
            k += 1


def rails(name, y0, y1, X, tags):
    """Os 2 trilhos de aco claro sobre a base isolante escura (passam da camera nas emendas)."""
    for sx in (-1, 1):
        xm = sx * (RAIL_IN + RAIL_OUT) / 2
        B.box(f"{name}_base{sx}", xm, (y0 + y1) / 2, RAIL_OUT - RAIL_IN + 0.05, y1 - y0, -0.01, 0.035, X["graph_d"],
              bevel=0.0, tags=tags)
        B.box(f"{name}_rail{sx}", xm, (y0 + y1) / 2, RAIL_OUT - RAIL_IN, y1 - y0, 0.035, 0.115, X["rail"],
              bevel=0.012, tags=tags)
        B.box(f"{name}_slit{sx}", xm, (y0 + y1) / 2, 0.012, y1 - y0, 0.112, 0.118, X["black"], bevel=0.0, tags=tags)


def rail_clips(name, ys, X, tags):
    for i, y in enumerate(ys):
        for sx in (-1, 1):
            B.box(f"{name}{i}{sx}", sx * (RAIL_OUT + 0.03), y, 0.06, 0.07, 0.03, 0.10, X["steel"], bevel=0.008,
                  tags=tags)


def em_ring(name, y, e, X, tags):
    """Bobina EM (camada trilhos, sob o tambor da cinta do teto): 2 blocos de grafite dos lados do canal com o emissor
    azul num recesso na face de dentro (x = WIN_X: aparece na ponta das costuras do tambor) e a banda escura que cruza
    o fundo do canal sob os trilhos com as 2 FENDAS azuis alinhadas com as 2 costuras transparentes do tambor (a luz
    azul que vaza entre as bandas, como na referencia). e = intensidade 0..1 (0 = lente azul apagada)."""
    s = 1.35 * e
    vm = blue(s)
    for sx in (-1, 1):
        poly = chamfer_rect(RING_IN, y - 0.15, RING_OUT, y + 0.15, (0.0, 0.07, 0.07, 0.0))
        if sx < 0:
            poly = mirror_x(poly)
        a, p = gplate(f"{name}_blk{sx}", poly, 0.0, 0.20, X, tags, slope=0.035, groove=0.02, panel_h=0.025)
        xr = sx * WIN_X
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.box(f"{name}_ec{sx}{t.name}", xr, y, 0.05, 0.17, 0.10, 0.5, X["black"], bevel=0.0)])
        B.box(f"{name}_ebed{sx}", xr, y, 0.05, 0.17, 0.085, 0.10, X["black"], bevel=0.0, tags=tags)
        B.box(f"{name}_em{sx}", xr, y, 0.03, 0.14, 0.10, 0.115, vm, bevel=0.0, tags=tags)
        bolts(f"{name}_b{sx}", [(sx * (RING_OUT - 0.07), y - 0.07), (sx * (RING_OUT - 0.07), y + 0.07)], 0.235, X,
              tags, r=0.014)
    B.box(f"{name}_band", 0, y, 2 * RING_IN + 0.02, 2 * (DRUM_SEAM + 0.045), -0.01, 0.034, X["graph_d"], bevel=0.004,
          tags=tags)
    for k, dy in enumerate((-DRUM_SEAM, DRUM_SEAM)):
        B.box(f"{name}_bandl{k}", 0, y + dy, 2 * RING_IN - 0.03, 0.040, 0.030, 0.040, vm, bevel=0.0, tags=tags)


def coaming(name, y0, y1, X, tags, z=0.13, x=CH):
    """Labio ESCURO na borda do canal (o canal se desenha pelo contraste entre os chanfros das bochechas)."""
    for sx in (-1, 1):
        B.box(f"{name}{sx}", sx * (x + 0.010), (y0 + y1) / 2, 0.020, y1 - y0, 0.0, z * 0.6, X["gap"], bevel=0.0,
              tags=tags)


def clamp(name, y, X, tags, z0=0.06, z1=0.215, hw=CLAMP_HW, hy=CLAMP_HY):
    """Cinta EM do teto = TAMBOR compacto da referencia (critica ref-r1: as cintas largas, claras e chapadas liam
    como escada / dormentes de trilho): so um pouco mais largo que o canal, corpo de gunmetal ESCURO com luz so nos
    chanfros, 3 BANDAS roliças (cilindros deitados: flanco de cima aceso, de baixo escuro) segmentadas por nervuras
    verticais, e as 2 COSTURAS entre as bandas TRANSPARENTES no teto: por elas vazam a luz azul da bobina (trilhos)
    e a da carga, e o nucleo cheio aparece como 2 pontos claros no tambor. Cada tambor tem nas 2 pontas um inserto
    LARANJA (3 x 5 px a 1x) e 2 parafusos. Esconde o dardo por um instante ('dentro do cano')."""
    sh = B.box(f"{name}_sh", 0, y, 2 * hw + 0.05, 2 * hy + 0.05, -0.02, z0 + 0.005, X["gap"], bevel=0.0, tags=tags)
    poly = chamfer_rect(-hw, y - hy, hw, y + hy, (0.085, 0.085, 0.085, 0.085))
    a, p = B.shard(name, poly, z0, z1, X["graph"], slope=0.035, groove=0.010, panel_h=0.02, panel_mat=X["gm"],
                   tags=tags)
    out = [sh, a, p]
    bands = []
    for k, dy in enumerate((-BAND_DY, 0.0, BAND_DY)):
        w = hw - 0.085
        c = B.cyl(f"{name}_bd{k}", 0, y + dy, z1 + 0.006, BAND_R, 2 * w, X["drum"], axis="X", verts=16, bevel=0.0,
                  tags=tags)
        bands.append(c)
    # nervuras verticais (segmentos do tambor): fendas escuras finas atravessando as 3 bandas
    for c in bands:
        B.cut(c, [B.box(f"{c.name}_r{i}", rx, y, 0.016, 0.40, -0.5, 1.5, X["black"], bevel=0.0)
                  for i, rx in enumerate((-0.30, -0.13, 0.13, 0.30))])
    # costuras transparentes entre as bandas (sobre o canal)
    for t in out:
        if t is not None:
            B.cut(t, [B.box(f"{t.name}_s{k}", 0, y + dy, 2 * SEAM_HX, 2 * SEAM_HY, -0.5, 1.5, X["black"], bevel=0.0)
                      for k, dy in enumerate((-DRUM_SEAM, DRUM_SEAM))])
    # insertos laranja nas pontas da banda do meio + parafusos de aco nas bordas
    for sx in (-1, 1):
        xo = sx * (hw - 0.055)
        if p is not None:
            B.cut(p, [B.box(f"{name}_oc{sx}", xo, y, 0.06, 0.10, z1 - 0.03, 1.0, X["black"], bevel=0.0)])
        B.cut(a, [B.box(f"{name}_oca{sx}", xo, y, 0.06, 0.10, z1 - 0.03, 1.0, X["black"], bevel=0.0)])
        B.box(f"{name}_ob{sx}", xo, y, 0.06, 0.10, z1 - 0.045, z1 - 0.03, X["black"], bevel=0.0, tags=tags)
        B.box(f"{name}_oi{sx}", xo, y, 0.044, 0.080, z1 - 0.04, z1 + 0.035, X["orange"], bevel=0.008, tags=tags)
        bolts(f"{name}_b{sx}", [(sx * (hw - 0.16), y - hy + 0.032), (sx * (hw - 0.16), y + hy - 0.032)],
              z1 + 0.02, X, tags, r=0.020)
    return out


def bracket(name, y, X, tags):
    """Garra lateral da cinta do meio (referencia: suporte de grafite que sai do corpo, bloco branco sobre o trilho
    branco e o inserto laranja num recesso na ponta de fora)."""
    for sx, poly in sides([(0.78, y - 0.27), (1.22, y - 0.27), (1.37, y - 0.15), (1.37, y + 0.15), (1.22, y + 0.27),
                           (0.78, y + 0.27)]):
        a, p = gplate(f"{name}{sx}", poly, 0.0, 0.25, X, tags, slope=0.045, groove=0.016, panel_h=0.025)
        wb = chamfer_rect(0.91, y - 0.19, 1.14, y + 0.19, (0.05, 0.05, 0.05, 0.05))
        wa, wp = wplate(f"{name}_w{sx}", wb if sx > 0 else mirror_x(wb), 0.25, 0.37, X, tags, slope=0.04,
                        panel_h=0.025)
        zb = recess(f"{name}_or{sx}", sx * 1.265, y, 0.09, 0.20, 0.275, X, tags, [a, p], depth=0.08)
        B.box(f"{name}_ori{sx}", sx * 1.265, y, 0.06, 0.16, zb, zb + 0.05, X["orange"], bevel=0.006, tags=tags)
        panel_lines(wp, f"{name}_wl{sx}", [(sx * 1.025, y, 0.20, 0)], 0.34, X)


def seam_clip(name, ys, X, tags):
    """Meia-garra do trilho branco na emenda dos canos (critica ref-r1: a referencia tem garras com laranja em cima,
    no meio e embaixo do cano): ys = +1 (borda de cima) ou -1 (de baixo). Termina reta na fresta da emenda e a outra
    metade vem do cano vizinho (identica, espelhada): emendados, os 2 canos formam uma garra inteira cortada pela
    fresta, sem emenda visivel; com 1 cano, as pontas viram garras de fim. Inserto laranja num recesso."""
    e = ys * (1.5 - SEAM)
    i = ys * (1.5 - SEAM - 0.20)
    m = ys * (1.5 - SEAM - 0.09)
    for sx, poly in sides([(0.78, i), (1.20, i), (1.30, i + ys * 0.10), (1.30, e), (0.78, e)]):
        a, p = gplate(f"{name}{sx}", poly, 0.0, 0.25, X, tags, slope=0.035, groove=0.010, panel_h=0.025)
        zb = recess(f"{name}_or{sx}", sx * 1.20, m, 0.07, 0.10, 0.275, X, tags, [a, p], depth=0.08)
        B.box(f"{name}_ori{sx}", sx * 1.20, m, 0.05, 0.075, zb, zb + 0.05, X["orange"], bevel=0.006, tags=tags)
        bolts(f"{name}_bo{sx}", [(sx * 0.86, m)], 0.27, X, tags, r=0.018)


# ============================================================================ CANO (3x3)
def cap_module(name, sx, yc, X, tags):
    """Modulo de capacitor do acionador da bobina (piso do cano e da ponta): placa de grafite com aletas e 3 LEDs
    azuis numa fenda com leito preto (STYLE 1.6)."""
    mod = chamfer_rect(0.86, yc - 0.34, 1.36, yc + 0.34, (0.06, 0.06, 0.06, 0.06))
    if sx < 0:
        mod = mirror_x(mod)
    a, p = gplate(name, mod, 0.0, 0.12, X, tags, slope=0.03, groove=0.02, panel_h=0.02)
    B.cut(p if p is not None else a, [B.box(f"{name}f{i}", sx * 1.11, yc - 0.25 + i * 0.08, 0.36, 0.022, 0.10, 0.4,
                                            X["black"], bevel=0.0) for i in range(6)])
    ledslot(f"{name}led", sx * 1.11, yc + 0.235, 0.22, 0.05, 0.14, 3, X, tags, [p, a], blue(0.7), vertical=False,
            depth=0.06)


def cano_floor(M, T="floor"):
    X = mats(M)
    tags = (T,)
    B.box("fl_base", 0, 0, 3.3, 3.3, -0.06, -0.02, X["core"], bevel=0.0, tags=tags)
    channel_floor("ch", -1.5 - EXT, 1.5 + EXT, X, tags)
    for sx in (-1, 1):
        B.box(f"bus{sx}", sx * 0.70, 0, 0.08, 3.0 + 2 * EXT, -0.02, 0.05, X["steel"], bevel=0.01, tags=tags)
        B.box(f"busk{sx}", sx * 0.70, 0, 0.02, 3.0 + 2 * EXT, 0.05, 0.056, X["black"], bevel=0.0, tags=tags)
        for k, yc in enumerate((-1.0, 0.0, 1.0)):
            B.box(f"fp{sx}{k}", sx * 1.10, yc, 0.74, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)
            cap_module(f"cap{sx}{k}", sx, yc, X, tags)
            B.box(f"cab{sx}{k}", sx * 0.79, yc, 0.14, 0.06, 0.0, 0.04, X["graph_d"], bevel=0.008, tags=tags)


def cano_rails(M, T="trilhos", level=1):
    X = mats(M)
    tags = (T,)
    rails("r", -1.5 - EXT, 1.5 + EXT, X, tags)
    rail_clips("clip", (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25), X, tags)
    for i, (y, e) in enumerate(zip(CLAMP_YS, ring_levels(level))):
        em_ring(f"ring{i}", y, e, X, tags)


def deck_plate(name, poly, X, tags, slope=0.025, groove=0.05, panel_h=0.02):
    """Placa de convés pintado (verde = pintura da nave) com bisel duplo; poligonos pequenos so com chanfro."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    if min(max(xs) - min(xs), max(ys) - min(ys)) < 0.17:
        return B.plate(name, poly, 0.0, 0.06, X["green"], slope=0.015, tags=tags), None
    return B.shard(name, poly, 0.0, 0.06, X["green"], slope=slope, groove=groove, panel_h=panel_h, tags=tags)


def cano_roof(M, T="roof"):
    """Teto do cano (referencia): corpo estreito com o canal aberto no meio (x 1.10-1.90 da peca), bochechas de
    gunmetal escuro com bisel claro, a moldura interna escura, TRILHOS BRANCOS estreitos (blindagem clara fixa) nas
    bordas do corpo, 3 TAMBORES EM compactos e escuros (um por quadro) cruzando o canal (costuras transparentes), a
    garra lateral no tambor do meio e as meias-garras das emendas (bloco branco / inserto laranja) e o convés pintado
    (verde) por fora. Frestas pretas; as placas terminam com chanfro na emenda."""
    X = mats(M)
    tags = (T,)
    y0, y1 = -1.5 + SEAM, 1.5 - SEAM
    for sx in (-1, 1):
        B.box(f"under{sx}", sx * (CH + 1.5) / 2, 0, 1.5 - CH, 3.0 + 2 * EXT, -0.06, 0.0, X["gap"], bevel=0.0,
              tags=tags)
        # convés pintado: uma placa por quadro (periodo 1)
        for k, yc in enumerate((-1.0, 0.0, 1.0)):
            pl = chamfer_rect(DECK_IN, yc - 0.475, 1.485, yc + 0.475, (0.06, 0.06, 0.06, 0.06))
            deck_plate(f"dk{sx}{k}", pl if sx > 0 else mirror_x(pl), X, tags)
    for sx, poly in sides(chamfer_rect(CHEEK_IN, y0, CHEEK_OUT, y1, (0.0, 0.06, 0.06, 0.0))):
        # bochecha de gunmetal ao lado do canal: painel com linhas, LEDs azuis e parafusos (um par laranja)
        a, p = gplate(f"chk{sx}", poly, 0.0, 0.17, X, tags, slope=0.05, groove=0.016, panel_h=0.03)
        panel_lines(p, f"chkl{sx}", [(sx * 0.60, yy, 0.30, 0) for yy in (-1.30, 1.30)], 0.14, X)
        for j, yy in enumerate((-0.5, 0.5)):
            ledslot(f"chk_led{sx}{j}", sx * 0.60, yy, 0.055, 0.26, 0.20, 2, X, tags, [p, a], blue(0.45))
            bolts(f"chk_bo{sx}{j}", [(sx * 0.68, yy - 0.27), (sx * 0.68, yy + 0.27)], 0.205, X, tags, r=0.016,
                  mat=X["orange"] if j == 0 else None)
    for sx, poly in sides(chamfer_rect(FR_IN, y0, FR_OUT, y1, (0.03, 0.03, 0.03, 0.03))):
        # moldura interna (a barra de aco da referencia entre o nucleo e o trilho branco): barra simples de grafite
        # com o chanfro aceso, juntas a cada quadro
        fa = B.plate(f"fr{sx}", poly, 0.0, 0.21, X["graph"], slope=0.022, tags=tags)
        panel_lines(fa, f"frl{sx}", [(sx * 0.845, yy, 0.12, 0) for yy in (-0.5, 0.5)], 0.19, X)
    for sx, poly in sides(chamfer_rect(WR_IN, y0, WR_OUT, y1, (0.04, 0.04, 0.04, 0.04))):
        # trilho branco: blindagem clara fixa (nao e pintura), com juntas a cada quadro (periodo 1)
        wa, wp = wplate(f"wr{sx}", poly, 0.0, 0.20, X, tags, slope=0.04, panel_h=0.03)
        panel_lines(wp, f"wrl{sx}", [(sx * 1.0125, yy, 0.12, 0) for yy in (-0.5, 0.5)], 0.17, X)
        bolts(f"wr_bo{sx}", [(sx * 1.0125, yy) for yy in (-0.75, 0.75)], 0.235, X, tags, r=0.016)
    for i, yc in enumerate(CLAMP_YS):
        clamp(f"cl{i}", yc, X, tags)
    bracket("brk", 0.0, X, tags)
    seam_clip("sct", 1, X, tags)
    seam_clip("scb", -1, X, tags)
    coaming("coam", -1.5 - EXT, 1.5 + EXT, X, tags)


# ============================================================================ brilhos (PIL, aditivos)
def _np():
    import numpy as np
    return np


def _grid(px, rect_tiles, part_h):
    """Coordenadas da peca centrada (+y para cima) de cada pixel de um sprite no rect."""
    np = _np()
    w, h = px
    x0t, y0t, wt, ht = rect_tiles
    xs = (np.arange(w) + 0.5) / w * wt + x0t - 1.5            # x da peca centrada (todas tem 3 de largura)
    ys = part_h / 2 - ((np.arange(h) + 0.5) / h * ht + y0t)   # y da peca centrada, +y para cima
    return np.meshgrid(xs, ys)


def _soft_box(X, Y, x_hw, y0, y1, e=0.02):
    """1 dentro do retangulo |x| < x_hw, y0 < y < y1 (borda suave de largura e), 0 fora."""
    np = _np()
    fx = np.clip((x_hw - np.abs(X)) / e + 0.5, 0, 1)
    fy = np.clip((Y - y0) / e + 0.5, 0, 1) * np.clip((y1 - Y) / e + 0.5, 0, 1)
    return fx * fy


def _to_img(rgb):
    np = _np()
    from PIL import Image
    rgb = np.clip(rgb, 0, 1)
    h, w = rgb.shape[:2]
    return Image.fromarray(np.dstack([rgb * 255, np.full((h, w), 255.0)]).astype(np.uint8), "RGBA")


def _c(rgb):
    np = _np()
    return np.array(rgb, np.float32) / 255.0


def _plane(px, rect_tiles, part_h, y_lo, y_hi, k_core, edge=0.30, rings=(), ring_gain=0.0, hw=GLOW_HW,
           mask=None, core_gain=1.0, base_gain=1.0, as_array=False):
    """Plano aditivo de carga (RGB sobre preto, opaco). y em coordenadas da peca (centrada, +y para cima): o plano
    cobre y_lo..y_hi com uma frente suave de largura 'edge' em y_hi (a onda) e borda reta em y_lo (emenda).
    Perfil em x igual em todas as pecas: azul nos trilhos e no canal ate GLOW_HW, mais forte no meio; k_core > 0
    soma o nucleo branco-azulado no eixo (carga quase cheia). mask(X, Y) -> fator 0..1."""
    np = _np()
    X, Y = _grid(px, rect_tiles, part_h)
    ax = np.abs(X)
    prof = np.clip(1 - (ax - 0.30) / (hw - 0.30), 0, 1) ** 1.6
    prof = np.where(ax < 0.30, 0.62 + 0.38 * np.exp(-((ax - 0.26) / 0.05) ** 2), prof)
    prof = prof * 0.80 + 0.10 * np.exp(-((ax - 0.26) / 0.04) ** 2) + 0.35 * np.exp(-(ax / 0.10) ** 2)
    cov = np.clip((y_hi - Y) / edge, 0, 1) * (Y >= y_lo - 1e-6)
    front = np.exp(-((Y - (y_hi - edge * 0.6)) / (edge * 0.7)) ** 2) * (Y >= y_lo - 1e-6)
    ringb = np.zeros_like(Y)
    for ry in rings:
        ringb += np.exp(-((Y - ry) / 0.07) ** 2)
    amt = cov * prof * base_gain * (1 + ring_gain * ringb) + 0.35 * front * prof
    rgb = amt[..., None] * _c(P_BLUE) * 0.64
    if k_core > 0:
        # nucleo branco-azulado fino no eixo + bainha azul clara (a linha acesa da referencia)
        core = np.exp(-(X / 0.045) ** 2) * cov * k_core * core_gain
        halo = np.exp(-(X / 0.13) ** 2) * cov * k_core * core_gain
        rgb = rgb * (1 - 0.50 * np.clip(halo, 0, 1)[..., None]) + core[..., None] * _c(P_CORE_AX) * 0.80 + \
            halo[..., None] * _c(P_HALO_AX) * 0.32
    if mask is not None:
        rgb = rgb * mask(X, Y)[..., None]
    return np.clip(rgb, 0, 1) if as_array else _to_img(rgb)


def glow_cano(P, layer, px, level=1):
    """carga1..8 do cano: o nivel k cobre os k/8 de baixo (lado da culatra); azul ate 6, nucleo branco-azulado
    em 7 e 8; mais forte nas 3 bobinas. A largura do plano e a mesma em todas as pecas (as emendas casam)."""
    H = P["size"][1]
    y_hi = -1.5 + 3.0 * level / 8
    if level == 8:
        y_hi = 1.5 + 0.5           # cheio: sem frente dentro do cano (continua no vizinho)
    k_core = {7: 0.55, 8: 1.0}.get(level, 0.0)
    return _plane(px, layer.get("rect", [0, 0, 3, 3]), H, -1.5, y_hi, k_core, rings=CLAMP_YS, ring_gain=0.9)


def glow_loader(P, layer, px, level=1):
    """luz_culatra1..2 (3x1 na fileira da culatra, lights_add POR CIMA das folhas e do bloco): so o que fica
    DENTRO acende: a costura entre as folhas fechadas, as lentes da bobina nos recessos das folhas e os emissores
    da camara nos cantos do bloco. 1 = azul; 2 = mais forte + nucleo branco-azulado na costura."""
    np = _np()
    from PIL import ImageFilter
    H = P["size"][1]
    X, Y = _grid(px, layer["rect"], H)
    g = {1: 0.80, 2: 1.0}[level]
    lens_x = 0.004 + 0.12                                     # lentes das folhas fechadas (_jaws: x0 + 0.12)
    m_lens = _soft_box(X - lens_x, Y, 0.016, 1.21, 1.79, 0.012) + _soft_box(X + lens_x, Y, 0.016, 1.21, 1.79, 0.012)
    m_seam = _soft_box(X, Y, 0.010, 1.10, 1.90, 0.012)
    ex = JAW_W + 0.05                                         # emissores da camara (loader_breech)
    m_em = _soft_box(X - ex, Y, 0.016, LOADER_RING - 0.075, LOADER_RING + 0.075, 0.012) + \
        _soft_box(X + ex, Y, 0.016, LOADER_RING - 0.075, LOADER_RING + 0.075, 0.012)
    rgb = (m_lens * 0.85 + m_seam * 0.55 + m_em * 1.0)[..., None] * _c(P_BLUE_HI) * g
    if level == 2:
        rgb = rgb + (m_seam * 0.9 + m_lens * 0.15)[..., None] * _c(P_CORE)
    img = _to_img(rgb)
    halo = np.asarray(img.filter(ImageFilter.GaussianBlur(2.0)), np.float32)[..., :3] / 255.0
    return _to_img(rgb + halo * 0.55)


# ---- ponta: geometria da boca (compartilhada pelo modelo e pelos brilhos)
CROWN_Y0 = 0.50                          # o teto da ponta termina aqui; a frente (weapon) comeca
THROAT = 0.16                            # meia largura da fenda do nucleo (teto) e da garganta da boca
MOUTH = 0.37                             # meia largura da boca aberta
MOUTH_Y1 = 0.66                          # a garganta abre ate MOUTH em y = MOUTH_Y1
FLARE_Y = 0.62                           # clarao da garganta (y 1.38 da peca)
PONTA_CLAMP = -1.5                       # cinta EM da ponta (mesmo passo das cintas do cano)
NECK_Y = -1.60                           # o canal largo (CH) da emenda afina para THROAT depois da cinta
CROWN_SIL = [(-1.24, CROWN_Y0 - 0.06), (1.24, CROWN_Y0 - 0.06), (1.24, 0.84), (0.90, 1.20), (0.90, 1.66), (0.58, 1.985),
             (-0.58, 1.985), (-0.90, 1.66), (-0.90, 1.20), (-1.24, 0.84)]


def mouth_hw(y):
    """Meia largura da abertura (garganta THROAT ate CROWN_Y0, abre linear ate MOUTH em MOUTH_Y1)."""
    if y <= CROWN_Y0:
        return THROAT
    if y >= MOUTH_Y1:
        return MOUTH
    return THROAT + (MOUTH - THROAT) * (y - CROWN_Y0) / (MOUTH_Y1 - CROWN_Y0)


def _mouth_hw_np(Y):
    np = _np()
    t = np.clip((Y - CROWN_Y0) / (MOUTH_Y1 - CROWN_Y0), 0, 1)
    return THROAT + (MOUTH - THROAT) * t


def _ponta_mask(X, Y):
    """mask() da ponta: livre atras da frente (o teto cobre o que nao e canal); na frente (weapon), so DENTRO da
    boca (a blindagem nao acende)."""
    np = _np()
    inside = np.clip((_mouth_hw_np(Y) - 0.02 - np.abs(X)) / 0.03 + 0.5, 0, 1)
    return np.where(Y >= CROWN_Y0, inside, 1.0)


def glow_ponta(P, layer, px, level=1):
    """carga1..6 da ponta (3x4): a onda sobe da emenda ate a boca; na boca o plano fica DENTRO da abertura (a
    blindagem nao acende); 5 e 6 enchem a boca de azul e acendem o clarao branco-azulado na garganta (o ponto
    quente da referencia), com o nucleo no eixo."""
    np = _np()
    from PIL import ImageFilter
    H = P["size"][1]
    y_lo = -2.0
    y_hi = -2.0 + 4.0 * level / 6
    if level == 6:
        y_hi = 2.0 + 0.4
    k_core = {5: 0.6, 6: 1.0}.get(level, 0.0)
    rect = layer.get("rect", [0, 0, 3, 4])
    rgb = _plane(px, rect, H, y_lo, y_hi, k_core, rings=(PONTA_CLAMP,), ring_gain=0.9, mask=_ponta_mask,
                 as_array=True)
    fill_k = {5: 0.6, 6: 1.0}.get(level, 0.0)
    if fill_k:
        X, Y = _grid(px, rect, H)
        inside = _ponta_mask(X, Y) * (Y >= CROWN_Y0)
        # boca cheia de azul (mais forte junto da garganta) + estrias dos trilhos
        grad = 0.55 + 0.45 * np.clip(1 - (Y - FLARE_Y) / 1.3, 0, 1)
        fill = inside * grad * fill_k
        rgb = rgb + fill[..., None] * _c(P_BLUE) * 0.40
        # clarao da garganta: nucleo branco-azulado + halo azul claro (no eixo, um pouco alongado para a frente)
        r_core = (X / 0.13) ** 2 + ((Y - FLARE_Y) / 0.10) ** 2
        r_halo = (X / 0.30) ** 2 + ((Y - FLARE_Y - 0.08) / 0.30) ** 2
        flare = np.exp(-r_core) * fill_k ** 1.5
        fh = np.exp(-r_halo) * fill_k * _ponta_mask(X, Y)
        rgb = rgb + flare[..., None] * _c(P_CORE_AX) * 1.0 + fh[..., None] * _c(P_HALO_AX) * 0.60
        # raios curtos do clarao para a frente (a "explosao" da referencia), so dentro da boca
        rays = np.exp(-(X / 0.035) ** 2) * np.exp(-((Y - FLARE_Y - 0.25) / 0.30) ** 2) * fill_k * inside
        rgb = rgb + rays[..., None] * _c(P_CORE_AX) * 0.45
        img = _to_img(rgb)
        halo = np.asarray(img.filter(ImageFilter.GaussianBlur(2.2)), np.float32)[..., :3] / 255.0
        rgb = rgb + halo * 0.18 * _ponta_mask(X, Y)[..., None]
    # critica ref-r1: o feixe parava num corte reto na borda da frente; alguns px de queda suave na boca
    X, Y = _grid(px, rect, H)
    rgb = rgb * (np.clip((2.0 - Y) / 0.11, 0, 1) ** 0.8)[..., None]
    return _to_img(rgb)


def glow_slug(P, layer, px, level=None):
    """Halo do projetil dentro do cano (lights_add, 1.2 x 3.4, ChainedTo Projectile). A camada lights_add fica POR
    CIMA do projetil (walls): o halo e OCO (forte dos lados da haste, fraco sobre ela) para o tungstenio claro
    continuar legivel; ponta branco-azulada na frente (topo) e um rastro azul curto atras das aletas."""
    np = _np()
    from PIL import Image
    w, h = px
    x0t, y0t, wt, ht = layer["rect"]
    xs = (np.arange(w) + 0.5) / w * wt - wt / 2
    ys = ht / 2 - (np.arange(h) + 0.5) / h * ht           # 0 = centro do projetil, +y = ponta
    X, Y = np.meshgrid(xs, ys)
    L = 1.47                                                # ponta do slug (bs_shells2: xt = 1.47)
    along = np.clip((1.36 - np.abs(Y)) / 0.25, 0, 1)
    side = (np.exp(-((np.abs(X) - 0.15) / 0.06) ** 2) * 0.55 + np.exp(-(X / 0.36) ** 2) * 0.22) * along
    hole = 1 - 0.85 * np.exp(-(X / 0.075) ** 2)
    wake = np.exp(-(X / 0.10) ** 2) * np.clip((Y + 1.70) / 0.25, 0, 1) * np.clip((-1.36 - Y) / 0.05 + 1, 0, 1) * \
        np.clip(1 - (-1.36 - Y) / 0.34, 0, 1) * 0.6
    tip = np.exp(-((X / 0.12) ** 2 + ((Y - L + 0.05) / 0.14) ** 2))
    tipw = np.exp(-((X / 0.045) ** 2 + ((Y - L + 0.02) / 0.06) ** 2))
    rgb = (side * hole + wake)[..., None] * _c(P_BLUE) * 1.05 + tip[..., None] * _c(P_BLUE_HI) * 0.85 \
        + tipw[..., None] * _c(P_CORE) * 0.95
    rgb = np.clip(rgb, 0, 1)
    return Image.fromarray(np.dstack([rgb * 255, np.full((h, w), 255.0)]).astype(np.uint8), "RGBA")


# ============================================================================ o dardo (o mesmo objeto em toda parte)
SLUG_X0, SLUG_X1 = -1.44, 1.47          # extensao do modelo "slug" de bs_shells2 (aletas .. ponta), eixo X


def dart(name, M, T, cx, cy, length, radial, z=0.12, phase=0.0):
    """O dardo do Tupa: o MESMO modelo do projetil em voo (parts/bs_shells2.py, item "slug" = slug.png): haste fina
    de tungstenio claro, 6 aletas curtas na cauda, 4 colares EM azuis e a ponta quente branco-azulada. De pe (ponta
    para +Y), centrado em (cx, cy), com o comprimento total 'length' (quadros) e a escala radial 'radial' (1 = a
    grossura do slug.png). Critica r2: o projetil que entra na culatra e o mesmo que corre pelo cano e voa."""
    import bpy
    from parts import bs_shells2
    sc = bpy.context.scene
    before = set(o.name for o in sc.objects)
    bs_shells2.model(M, "slug", T, phase)
    emp = bpy.data.objects.new(name + "_root", None)
    sc.collection.objects.link(emp)
    for o in [o for o in sc.objects if o.name not in before and o.parent is None and o is not emp]:
        o.parent = emp
    k = length / (SLUG_X1 - SLUG_X0)
    emp.scale = (k, radial, radial)            # X local = eixo do projetil
    emp.rotation_euler.z = math.radians(90)
    emp.location = (cx, cy - (SLUG_X0 + SLUG_X1) / 2 * k, z)
    return emp


# ============================================================================ CARREGADOR (3x4)
# fileira 0 (y 1..2) = culatra; fileiras 1-2 = 2 postos da tripulacao + banco de capacitores; fileira 3 = paiol
CREW = ((-0.9, 0.4), (0.9, 0.4))         # (0.6, 1.6) e (2.4, 1.6) da peca
JAW_W = 0.36                            # meia largura da camara / folha da culatra fechada
JAW_OPEN = 0.30                         # curso de cada folha ao abrir
ROUND_L, ROUND_R = 1.78, 0.75          # dardo na camara: comprimento (quadros) e escala radial (1 = slug.png)
CHAMBER_Y = 1.91 - ROUND_L / 2          # centro do dardo assentado (ponta na fenda do teto, y 1.10-1.90; cauda 0.13)
TRAY_Y = -0.25                          # centro do dardo no 1o quadro da carga (sai de baixo da borda do sprite)
LOADER_RING = 1.78
CAP_YS = (-0.27, -0.60, -0.93)          # celulas do banco de capacitores (de frente para tras)
# paiol: coluna de capsulas (referencia) vista pela janela do teto
MAG_N, MAG_Y0, MAG_P = 6, -0.885, 0.155  # 6 capsulas (2 dardos cada), centro da 1a (frente), passo
CAP_L, CAP_R = 0.54, 0.056              # comprimento da luva acesa e raio da capsula
WIN_Y0, WIN_Y1, WIN_HX = -1.76, -0.80, 0.40  # paiol: poco do piso (y de tras, y da frente) e meia largura da janela
# critica ref-r1 (ponto focal): a janela alta (paiol + bandeja) virou 2 janelas separadas no teto: a JANELA DO PAIOL
# (so a coluna de capsulas, com a moldura grossa e escura) e, acima, a FENDA DE ALIMENTACAO estreita (o dardo sobe
# por ela na carga: culatra_carrega continua visivel)
MAG_TOP = -0.775                        # topo da janela do paiol no teto (a frente da coluna de capsulas)
FEED_Y0, FEED_Y1, FEED_HX = 0.0, 0.98, 0.16  # fenda de alimentacao (o rect de culatra_carrega comeca em y 0)
SLOT_Y0, SLOT_Y1, SLOT_HX = 1.10, 1.90, 0.50  # fenda da culatra no teto (spec: 1.0 x 0.8)


def loader_floor(M, T="floor"):
    X = mats(M)
    tags = (T,)
    B.box("fl_base", 0, 0, 3.3, 4.3, -0.06, -0.02, X["core"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        for k, yc in enumerate((1.5, 0.5, -0.5, -1.5)):
            B.box(f"fp{sx}{k}", sx * 1.0, yc, 0.92, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)
    B.box("fpc", 0, -0.2, 1.0, 1.6, -0.02, 0.005, X["core_mid"], bevel=0.01, tags=tags)
    # camara + bandeja: a calha do canal continua do cano ate a culatra (nervuras no mesmo passo)
    channel_floor("ch", 1.0, 2.0 + EXT, X, tags, rib_y0=1.125, bed=X["graph_d"])
    rails("r", 1.08, 2.0 + EXT, X, tags)
    for sx in (-1, 1):
        B.box(f"ranch{sx}", sx * (RAIL_IN + RAIL_OUT) / 2, 1.07, 0.13, 0.08, 0.0, 0.14, X["steel"], bevel=0.01,
              tags=tags)
    em_ring("ring0", LOADER_RING, 0.0, X, tags)
    # bandeja do soquete (rammer) do elevador ate a camara
    B.box("tray", 0, 0.12, 0.44, 1.76, -0.02, 0.015, X["trough"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"tray_l{sx}", sx * 0.245, 0.12, 0.05, 1.76, -0.02, 0.03, X["black"], bevel=0.0, tags=tags)
        B.box(f"tray_g{sx}", sx * 0.13, 0.12, 0.035, 1.76, 0.015, 0.06, X["rib"], bevel=0.006, tags=tags)
    B.box("tray_slot", 0, 0.12, 0.05, 1.76, 0.010, 0.016, X["graph_d"], bevel=0.0, tags=tags)
    # elevador (plataforma que leva o dardo da capsula da frente para a bandeja)
    lift = B.box("lift", 0, -0.63, 0.52, 0.22, 0.0, 0.05, X["steel"], bevel=0.01, tags=tags)
    B.cut(lift, [B.box(f"liftc{i}", -0.18 + i * 0.12, -0.63, 0.05, 0.15, 0.03, 0.2, X["black"], bevel=0.0)
                 for i in range(4)])
    # poco do paiol (a coluna de capsulas): recesso preto com 2 guias de aco e o batente de tras
    wy = (WIN_Y0 + WIN_Y1) / 2 - 0.02
    well = B.box("well", 0, wy, 0.94, 1.08, 0.0, 0.05, X["graph_d"], bevel=0.01, tags=tags)
    B.cut(well, [B.box("wellc", 0, wy, 0.80, 1.00, 0.02, 0.2, X["black"], bevel=0.0)])
    B.box("well_b", 0, wy, 0.80, 1.00, 0.0, 0.022, X["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"well_g{sx}", sx * 0.385, wy, 0.022, 1.00, 0.0, 0.06, X["steel"], bevel=0.004, tags=tags)
    for j in range(MAG_N):
        # assentos das capsulas (marcas escuras no fundo do poco: o paiol vazio continua lendo como paiol)
        B.box(f"seat_m{j}", 0, MAG_Y0 - j * MAG_P, 0.62, 0.05, 0.0, 0.026, X["graph_d"], bevel=0.0, tags=tags)
    # bancos de capacitores: encaixes vazios nas laterais (as celulas sao a camada capacitores)
    for sx in (-1, 1):
        bay = B.box(f"bay{sx}", sx * 1.27, -0.60, 0.36, 1.00, 0.0, 0.04, X["graph_d"], bevel=0.01, tags=tags)
        B.cut(bay, [B.box(f"bayc{sx}{i}", sx * 1.27, y, 0.30, 0.26, 0.02, 0.2, X["black"], bevel=0.0)
                    for i, y in enumerate(CAP_YS)])
        for i, y in enumerate(CAP_YS):
            B.box(f"bayb{sx}{i}", sx * 1.27, y, 0.30, 0.26, 0.0, 0.022, X["black"], bevel=0.0, tags=tags)
            B.box(f"bayk{sx}{i}", sx * 1.27, y, 0.10, 0.04, 0.02, 0.03, X["steel"], bevel=0.0, tags=tags)
        B.box(f"bus{sx}", sx * 0.70, 0.45, 0.07, 1.30, -0.02, 0.05, X["steel"], bevel=0.01, tags=tags)
        B.box(f"busk{sx}", sx * 0.70, 0.45, 0.02, 1.30, 0.05, 0.056, X["black"], bevel=0.0, tags=tags)
        B.box(f"busc{sx}", sx * 0.95, -0.12, 0.55, 0.06, -0.02, 0.04, X["graph_d"], bevel=0.008, tags=tags)
        cx, cy = CREW[0 if sx < 0 else 1]
        B.box(f"seat{sx}", cx, cy - 0.12, 0.30, 0.26, 0.0, 0.12, X["armor_mid"], bevel=0.04, tags=tags)
        B.box(f"seatb{sx}", cx, cy - 0.28, 0.30, 0.06, 0.0, 0.18, X["graph_d"], bevel=0.02, tags=tags)
        # entradas da fita nos cantos de tras (portas rafaeltessaro.bs_belt em [0,3]/[2,3])
        for k, (px_, py_, w_, h_) in enumerate(((sx * 1.40, -1.50, 0.12, 0.42), (sx * 1.0, -1.90, 0.42, 0.12))):
            fr = B.box(f"port{sx}{k}", px_, py_, w_, h_, 0.0, 0.05, X["steel"], bevel=0.008, tags=tags)
            B.cut(fr, [B.box(f"portc{sx}{k}", px_, py_, w_ * 0.6 if w_ > h_ else w_ * 0.5,
                             h_ * 0.5 if w_ > h_ else h_ * 0.6, 0.02, 0.2, X["black"], bevel=0.0)])
            B.box(f"portb{sx}{k}", px_, py_, w_ * 0.6, h_ * 0.6, 0.0, 0.025, X["black"], bevel=0.0, tags=tags)


def capsule(name, cx, cy, X, tags, s=0.78, z=0.075):
    """Capsula de contencao deitada (eixo X, a referencia): luva de vidro azul aceso (azul medio, ~60, 130, 230:
    critica ref-r1, o paiol nao pode ser o ponto mais claro da arma em repouso nem passar do orcamento de
    emissivo), o filete azul claro no eixo (os 2 dardos dentro), 2 cintas escuras, tampas LARANJA e pontas de aco."""
    r, L = CAP_R, CAP_L
    B.box(name + "_sh", cx, cy, L + 0.20, 2 * r + 0.03, 0.0, 0.012, X["black"], bevel=0.0, tags=tags)
    B.cyl(name + "_g", cx, cy, z, r, L, blue(s, f"rl_capg_{int(round(s * 100)):03d}"), axis="X", verts=12,
          bevel=0.0, tags=tags)
    B.box(name + "_c", cx, cy, L - 0.14, 0.014, z + r - 0.006, z + r + 0.004,
          hot(BLUE_HI, 0.60, (0.20, 0.26, 0.36), "capcore"), bevel=0.0, tags=tags)
    for i, dx in enumerate((-0.13, 0.13)):
        B.cyl(f"{name}_b{i}", cx + dx, cy, z, r * 1.08, 0.028, X["graph_d"], axis="X", verts=12, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"{name}_cap{sx}", cx + sx * (L / 2 + 0.036), cy, z, r * 1.14, 0.072, X["orange"], axis="X", verts=12,
              bevel=0.006, tags=tags)
        B.cyl(f"{name}_tip{sx}", cx + sx * (L / 2 + 0.088), cy, z, r * 0.68, 0.032, X["steel"], axis="X", verts=10,
              bevel=0.004, tags=tags)


def loader_magazine(M, T="projeteis", level=1):
    """projeteis1..6: a coluna de capsulas (referencia), nivel k = k capsulas EMPURRADAS PARA A FRENTE (lado do
    elevador) pela placa seguidora de grafite com a faixa laranja."""
    X = mats(M)
    tags = (T,)
    for j in range(level):
        capsule(f"cap{j}", 0.0, MAG_Y0 - j * MAG_P, X, tags)
    yf = MAG_Y0 - (level - 1) * MAG_P - 0.105
    a, p = gplate("follow", chamfer_rect(-0.37, yf - 0.03, 0.37, yf + 0.03, (0.02, 0.02, 0.02, 0.02)), 0.0, 0.10,
                  X, tags, slope=0.02, groove=0.01, panel_h=0.015)
    B.box("follow_o", 0, yf, 0.40, 0.022, 0.10, 0.125, X["orange"], bevel=0.004, tags=tags)


def loader_console(M, T="consola", phase=0.0, frame=1):
    """Console de um posto (o mesmo sprite nos 2 postos: simetrico). Mesa em arco na frente do tripulante (para a
    culatra), 2 telas com barras azuis que correm, uma fileira de 4 LEDs (perseguicao) num recesso cortado na
    borda de tras da mesa e um LED laranja fraco de estado num recesso da asa direita (STYLE 1.6)."""
    X = mats(M)
    tags = (T,)
    cx, cy = CREW[0]
    k = frame - 1
    desk = [(-0.44, 0.08), (-0.22, 0.13), (0.22, 0.13), (0.44, 0.08), (0.48, 0.30), (0.28, 0.47), (-0.28, 0.47),
            (-0.48, 0.30)]
    desk = [(cx + x, cy + y) for x, y in desk]
    a, p = gplate("desk", desk, 0.0, 0.20, X, tags, slope=0.03, groove=0.02, panel_h=0.02)
    for i, sx in enumerate((-1, 1)):
        scx, scy = cx + sx * 0.17, cy + 0.345
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.rbox(f"scrc{i}{t.name}", scx, scy, 0.20, 0.10, 0.15, 0.6, X["black"], rot=-sx * 14,
                                 bevel=0.0)])
        B.rbox(f"scrb{i}", scx, scy, 0.20, 0.10, 0.14, 0.155, X["black"], rot=-sx * 14, bevel=0.0, tags=tags)
        B.rbox(f"scrf{i}", scx, scy, 0.17, 0.075, 0.155, 0.158, blue(0.70, "rl_scr_fill"), rot=-sx * 14, bevel=0.0,
               tags=tags)
        for b in range(3):
            hgt = 0.35 + 0.65 * ((b * 2 + k * (2 if i else 1)) % 4) / 3
            bx = b * 0.05 - 0.05
            ca, sa = math.cos(math.radians(-sx * 14)), math.sin(math.radians(-sx * 14))
            px_, py_ = scx + bx * ca, scy + bx * sa
            B.rbox(f"bar{i}{b}", px_, py_ - 0.03 + 0.03 * hgt, 0.032, 0.06 * hgt, 0.158, 0.166,
                   blue(1.15) if b != (k % 3) else hot(CORE_W, 1.0, (0.22, 0.26, 0.32), "scrw"), rot=-sx * 14,
                   bevel=0.0, tags=tags)
    ledslot("led", cx, cy + 0.215, 0.30, 0.05, 0.22, 4, X, tags, [p, a],
            [blue(1.2 if i == k else 0.25) for i in range(4)], vertical=False, depth=0.07)
    ledslot("ledor", cx + 0.37, cy + 0.215, 0.06, 0.06, 0.22, 1, X, tags, [p, a],
            orange_led(0.60 if k % 2 == 0 else 0.25), depth=0.07, pip=0.6)


def _jaws(X, tags, off, name="jaw", lens=0.55, edge=0.0):
    """As 2 folhas da culatra (deslizam para os lados). off = 0 fechada .. JAW_OPEN aberta. lens = forca da lente
    azul da bobina na face de dentro (mais forte com a culatra aberta: a recarga le pela fenda do teto a 1x)."""
    for sx in (-1, 1):
        x0, x1 = off + 0.004, off + JAW_W
        poly = chamfer_rect(x0, 1.08, x1, 1.92, (0.08, 0.0, 0.0, 0.08))
        if sx < 0:
            poly = mirror_x(poly)
        a, p = gplate(f"{name}{sx}", poly, 0.0, 0.22, X, tags, slope=0.03, groove=0.02, panel_h=0.025,
                      panel=X["jawface"])
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
        B.box(f"{name}_ll{sx}", lx, 1.50, 0.028, 0.56, 0.145, 0.152, blue(lens), bevel=0.0, tags=tags)
        ex = sx * (x0 + 0.036)
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.box(f"{name}_ec{sx}{t.name}", ex, 1.50, 0.026, 0.26, 0.15, 0.6, X["black"], bevel=0.0)])
        B.box(f"{name}_eb{sx}", ex, 1.50, 0.026, 0.26, 0.135, 0.15, X["black"], bevel=0.0, tags=tags)
        B.box(f"{name}_el{sx}", ex, 1.50, 0.016, 0.22, 0.15, 0.156, blue(edge), bevel=0.0, tags=tags)
        # nervuras de pega na parte de fora; a do meio com a tinta laranja (marca de manuseio)
        for i in range(3):
            B.box(f"{name}_r{sx}{i}", sx * (x1 - 0.07), 1.30 + i * 0.2, 0.07, 0.03, 0.22, 0.25,
                  X["orange"] if i == 1 else X["steel"], bevel=0.006, tags=tags)


def loader_jaws(M, T="culatra_abre", phase=0.0, frame=1):
    """culatra_abre1..3: 1 = fechada, 3 = aberta (o jogo toca ao contrario para fechar)."""
    X = mats(M)
    _jaws(X, (T,), JAW_OPEN * (frame - 1) / 2, lens=(0.55, 1.15, 1.5)[frame - 1], edge=(0.0, 1.0, 1.5)[frame - 1])


_LOAD_S = (0.0, 0.10, 0.32, 0.62, 0.88, 1.0)


def loader_chambered(M, T="culatra_projetil"):
    """culatra_projetil.png (doodads_low, [1,0,1,2]): o projetil assentado na camara, IGUAL ao de culatra_carrega6
    (mesmo modelo, mesmo lugar, sem o soquete). Fica abaixo das folhas (walls): a culatra fecha por cima dele."""
    dart("round", M, T, 0, CHAMBER_Y, ROUND_L, ROUND_R)


def loader_load(M, T="culatra_carrega", phase=0.0, frame=1):
    """culatra_carrega1..6: o projetil sobe do elevador e o soquete o empurra pela bandeja ate a camara (folhas
    abertas, iguais a culatra_abre3)."""
    X = mats(M)
    tags = (T,)
    _jaws(X, tags, JAW_OPEN, lens=1.5, edge=1.5)
    y = TRAY_Y + (CHAMBER_Y - TRAY_Y) * _LOAD_S[frame - 1]
    dart("round", M, T, 0, y, ROUND_L, ROUND_R)
    yb = y - ROUND_L / 2
    B.box("ram_head", 0, yb - 0.04, 0.24, 0.06, 0.06, 0.22, X["steel"], bevel=0.01, tags=tags)
    if yb - 0.07 > 0.0:
        B.box("ram_rod", 0, (yb - 0.07) / 2, 0.08, yb - 0.07, 0.10, 0.18, X["graph_d"], bevel=0.008, tags=tags)
        B.box("ram_rodk", 0, (yb - 0.07) / 2, 0.03, yb - 0.07, 0.18, 0.19, X["steel"], bevel=0.0, tags=tags)


def loader_breech(M, T="weapon"):
    """weapon.png [0,0,3,1]: bloco da culatra dos 2 lados da camara (a camara fica vazia: as folhas e o projetil
    estao na camada walls, abaixo desta). Sob o teto: aparece pela fenda (a borda de dentro) e no interior."""
    X = mats(M)
    tags = (T,)
    for sx in (-1, 1):
        poly = [(JAW_W, 1.02), (1.24, 1.02), (1.42, 1.16), (1.42, 1.72), (1.18, 1.97), (JAW_W, 1.97)]
        if sx < 0:
            poly = mirror_x(poly)
        B.box(f"core{sx}", sx * 0.9, 1.5, 1.0, 0.9, 0.0, 0.10, X["graph_d"], bevel=0.0, tags=tags)
        a, p = gplate(f"blk{sx}", poly, 0.0, 0.30, X, tags, slope=0.05, groove=0.026, panel_h=0.03)
        rec = [B.box(f"prc{sx}", sx * 0.80, 1.45, 0.62, 0.22, 0.14, 0.6, X["black"], bevel=0.0)]
        B.cut(a, rec)
        if p is not None:
            B.cut(p, [B.box(f"prc2{sx}", sx * 0.80, 1.45, 0.62, 0.22, 0.14, 0.6, X["black"], bevel=0.0)])
        B.box(f"pbed{sx}", sx * 0.80, 1.45, 0.62, 0.22, 0.12, 0.145, X["core"], bevel=0.0, tags=tags)
        B.cyl(f"pcyl{sx}", sx * 0.92, 1.45, 0.20, 0.07, 0.36, X["graph_d"], axis="X", verts=8, bevel=0.006,
              tags=tags)
        B.cyl(f"prod{sx}", sx * 0.62, 1.45, 0.20, 0.035, 0.30, X["rail"], axis="X", verts=8, bevel=0.004, tags=tags)
        B.cyl(f"pend{sx}", sx * 1.12, 1.45, 0.20, 0.08, 0.05, X["orange"], axis="X", verts=8, bevel=0.004, tags=tags)
        ex = sx * (JAW_W + 0.05)
        for t in (a, p):
            if t is not None:
                B.cut(t, [B.box(f"ec{sx}{t.name}", ex, LOADER_RING, 0.06, 0.20, 0.18, 0.6, X["black"], bevel=0.0)])
        B.box(f"eb{sx}", ex, LOADER_RING, 0.06, 0.20, 0.16, 0.185, X["black"], bevel=0.0, tags=tags)
        B.box(f"el{sx}", ex, LOADER_RING, 0.035, 0.16, 0.185, 0.195, X["lens"], bevel=0.0, tags=tags)
        if p is not None:
            ledslot(f"st{sx}", sx * 0.80, 1.80, 0.36, 0.05, 0.33, 4, X, tags, [p, a], blue(0.55), vertical=False)
        bolts(f"bo{sx}", [(sx * 1.30, 1.25), (sx * 1.30, 1.62), (sx * 0.50, 1.12), (sx * 0.50, 1.88)], 0.335, X,
              tags, r=0.016)


def loader_caps(M, T="capacitores", level=1):
    """Banco de capacitores (bateria do carregador): o nivel k poe k celulas carregadas de cada lado."""
    X = mats(M)
    tags = (T,)
    for sx in (-1, 1):
        for i, y in enumerate(CAP_YS[:level]):
            poly = chamfer_rect(sx * 1.27 - 0.15, y - 0.13, sx * 1.27 + 0.15, y + 0.13, (0.07, 0.07, 0.07, 0.07))
            a, p = gplate(f"cell{sx}{i}", poly, 0.0, 0.20, X, tags, slope=0.025, groove=0.016, panel_h=0.02)
            for t in (a, p):
                if t is not None:
                    B.cut(t, [B.box(f"cc{sx}{i}{t.name}", sx * 1.27, y, 0.14, 0.06, 0.14, 0.6, X["black"],
                                    bevel=0.0)])
            B.box(f"cb{sx}{i}", sx * 1.27, y, 0.14, 0.06, 0.13, 0.145, X["black"], bevel=0.0, tags=tags)
            B.box(f"cl{sx}{i}", sx * 1.27, y, 0.08, 0.022, 0.145, 0.152, blue(1.1), bevel=0.0, tags=tags)
            B.box(f"ct{sx}{i}", sx * (1.27 - 0.10), y, 0.04, 0.16, 0.20, 0.23, X["orange"], bevel=0.005, tags=tags)


def spring_housing(name, cx, y0, y1, X, tags):
    """Alojamento da mola do paiol (referencia: molas LARANJA-OURO curtas e gordas, poucas espiras grossas, entre 2
    tampas cilindricas escuras, ao lado da coluna de capsulas e na mesma altura). Critica ref-r1: a mola fina de
    muitas espiras cor de cobre num rasgo estreito lia como a bobina de cobre da familia PEM; agora: fio grosso,
    ~6 espiras, laranja-ouro claro com brilho por cima, tampas roliças de gunmetal com flange e anel laranja."""
    w = 0.27
    cap_l = 0.20
    B.box(f"{name}_rec", cx, (y0 + y1) / 2, w, y1 - y0, 0.0, 0.02, X["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"{name}_side{sx}", cx + sx * (w / 2 - 0.012), (y0 + y1) / 2, 0.024, y1 - y0 - 2 * cap_l, 0.0, 0.07,
              X["graph"], bevel=0.006, tags=tags)
    ym0, ym1 = y0 + cap_l, y1 - cap_l
    B.cyl(f"{name}_rod", cx, (ym0 + ym1) / 2, 0.10, 0.024, ym1 - ym0 + 0.04, X["rail"], axis="Y", verts=10,
          bevel=0.0, tags=tags)
    helix(f"{name}_spr", cx, ym0 + 0.01, ym1 - 0.01, 0.10, 0.088, 0.031, (ym1 - ym0) / 0.125, X["spring"], tags,
          steps=24)
    for k, (yc, inner) in enumerate(((y0 + cap_l / 2, ym0), (y1 - cap_l / 2, ym1))):
        B.cyl(f"{name}_cap{k}", cx, yc, 0.10, 0.125, cap_l - 0.01, X["drum"], axis="Y", verts=20, bevel=0.008,
              tags=tags)
        dy = 1 if inner > yc else -1
        B.cyl(f"{name}_fl{k}", cx, inner - dy * 0.018, 0.10, 0.138, 0.030, X["graph"], axis="Y", verts=20,
              bevel=0.004, tags=tags)
        B.cyl(f"{name}_or{k}", cx, yc - dy * 0.045, 0.10, 0.130, 0.024, X["orange"], axis="Y", verts=20,
              bevel=0.003, tags=tags)


def loader_roof(M, T="roof"):
    """Teto do carregador (referencia; critica ref-r1: o ponto focal e a COLUNA DE CAPSULAS): bloco largo blindado
    com 3 janelas transparentes: a JANELA DO PAIOL embaixo (so a coluna de capsulas azuis, numa MOLDURA GROSSA,
    escura e arredondada de gunmetal com o aro de bisel claro e a trava laranja embaixo), a FENDA DE ALIMENTACAO
    estreita e escura acima dela (o dardo sobe por ela na carga) e a FENDA da culatra em cima (spec: 1.0 x 0.8). As
    MOLAS LARANJA-OURO em alojamentos escuros com tampas cilindricas ficam logo ao lado da moldura, na altura das
    capsulas; colunas de gunmetal (pistao, respiros, LEDs) ao lado da fenda; placas BRANCAS em cunha nas laterais
    (o ombro alto, que se projeta, com a fenda de visao do posto; a de baixo, recuada: o contorno de escudo da
    referencia); convés pintado (verde) so nos cantos, fora da blindagem."""
    X = mats(M)
    tags = (T,)
    # ---- base escura (sem as 3 janelas)
    B.box("u_front", 0, (SLOT_Y1 + 2.0 + EXT) / 2, 3.0, 2.0 + EXT - SLOT_Y1, -0.06, 0.0, X["gap"], bevel=0.0,
          tags=tags)
    for sx in (-1, 1):
        B.box(f"u_slot{sx}", sx * (SLOT_HX + 1.5) / 2, (SLOT_Y0 + SLOT_Y1) / 2, 1.5 - SLOT_HX, SLOT_Y1 - SLOT_Y0,
              -0.06, 0.0, X["gap"], bevel=0.0, tags=tags)
        B.box(f"u_feed{sx}", sx * (FEED_HX + 1.5) / 2, (FEED_Y0 + FEED_Y1) / 2, 1.5 - FEED_HX, FEED_Y1 - FEED_Y0,
              -0.06, 0.0, X["gap"], bevel=0.0, tags=tags)
        B.box(f"u_mag{sx}", sx * (WIN_HX + 1.5) / 2, (WIN_Y0 + MAG_TOP) / 2, 1.5 - WIN_HX, MAG_TOP - WIN_Y0, -0.06,
              0.0, X["gap"], bevel=0.0, tags=tags)
    B.box("u_bar", 0, (FEED_Y1 + SLOT_Y0) / 2, 3.0, SLOT_Y0 - FEED_Y1, -0.06, 0.0, X["gap"], bevel=0.0, tags=tags)
    B.box("u_mid", 0, (MAG_TOP + FEED_Y0) / 2, 3.0, FEED_Y0 - MAG_TOP, -0.06, 0.0, X["gap"], bevel=0.0, tags=tags)
    B.box("u_back", 0, (-2.0 + WIN_Y0) / 2, 3.0, WIN_Y0 + 2.0, -0.06, 0.0, X["gap"], bevel=0.0, tags=tags)
    # ---- convés pintado nos cantos (fora da blindagem)
    for sx in (-1, 1):
        for k, poly in enumerate(([(1.22, 1.40), (1.485, 1.13), (1.485, 1.985), (1.22, 1.985)],
                                  [(1.41, -1.985), (1.485, -1.985), (1.485, -0.66), (1.41, -0.66)],
                                  [(1.24, -1.985), (1.38, -1.985), (1.38, -1.86)])):
            deck_plate(f"dk{sx}{k}", poly if sx > 0 else mirror_x(poly), X, tags)
        tri = [(1.33, -0.62), (1.485, -0.47), (1.485, -0.62)]
        B.plate(f"dkt{sx}", tri if sx > 0 else mirror_x(tri), 0.0, 0.06, X["green"], slope=0.012, tags=tags)
    # ---- colar da frente (encosta no 1o cano) + bloco da moldura em cima da fenda
    ca, cp = gplate("collar", chamfer_rect(-1.18, SLOT_Y1 + 0.035, 1.18, 2.0 + EXT, (0.06, 0.06, 0.0, 0.0)), 0.0,
                    0.15, X, tags, slope=0.04, groove=0.016, panel_h=0.025)
    panel_lines(cp, "coll", [(sx * 0.90, 1.965, 0.36, 0) for sx in (-1, 1)], 0.12, X)
    gplate("fcap", chamfer_rect(-0.64, SLOT_Y1 + 0.035, 0.64, 2.0 + EXT, (0.05, 0.05, 0.0, 0.0)), 0.15, 0.28, X, tags,
           slope=0.04, groove=0.014, panel_h=0.025)
    B.box("fcap_or", 0, 1.965, 0.30, 0.03, 0.30, 0.32, X["orange"], bevel=0.004, tags=tags)
    # ---- moldura da fenda da culatra (lados) e ombros de grafite com respiros
    for sx, poly in sides(chamfer_rect(SLOT_HX + 0.015, FEED_Y1 + 0.10, 0.64, SLOT_Y1 + 0.03, (0.0, 0.03, 0.0, 0.0))):
        gplate(f"sfr{sx}", poly, 0.0, 0.27, X, tags, slope=0.035, groove=0.012, panel_h=0.025)
        B.box(f"slip{sx}", sx * (SLOT_HX + 0.008), (SLOT_Y0 + SLOT_Y1) / 2, 0.016, SLOT_Y1 - SLOT_Y0, 0.0, 0.16,
              X["gap"], bevel=0.0, tags=tags)
    for sx, poly in sides([(0.68, 1.36), (1.06, 1.36), (1.18, 1.48), (1.18, SLOT_Y1 + 0.005), (0.68, SLOT_Y1 + 0.005)]):
        a, p = gplate(f"sh{sx}", poly, 0.0, 0.21, X, tags, slope=0.045, groove=0.016, panel_h=0.028)
        for i in range(3):
            recess(f"shv{sx}{i}", sx * 0.92, 1.50 + i * 0.12, 0.34, 0.05, 0.24, X, tags, [a, p], depth=0.08,
                   bed=X["gap"])
        bolts(f"shb{sx}", [(sx * 0.74, 1.43), (sx * 1.10, 1.84)], 0.245, X, tags, r=0.016)
        bolts(f"shbo{sx}", [(sx * 0.74, 1.84)], 0.245, X, tags, r=0.016, mat=X["orange"])
    # ---- FENDA DE ALIMENTACAO: estreita, numa placa de gunmetal (respiros e marca laranja embaixo)
    fa, fp = gplate("feed", chamfer_rect(-0.30, -0.56, 0.30, FEED_Y1 + 0.075, (0.05, 0.05, 0.04, 0.04)), 0.0, 0.24,
                    X, tags, slope=0.035, groove=0.012, panel_h=0.022, panel=X["gm"])
    hole = chamfer_rect(-FEED_HX, FEED_Y0, FEED_HX, FEED_Y1, (0.03, 0.03, 0.03, 0.03))
    for t in (fa, fp):
        if t is not None:
            B.cut(t, [B.loft(f"fdc{t.name}", hole, hole, -0.5, 1.5, X["black"], bevel=0.0)])
    for sx in (-1, 1):
        B.box(f"flip{sx}", sx * (FEED_HX + 0.008), (FEED_Y0 + FEED_Y1) / 2, 0.016, FEED_Y1 - FEED_Y0, 0.0, 0.16,
              X["gap"], bevel=0.0, tags=tags)
    for i in range(3):
        recess(f"fdv{i}", 0, -0.42 + i * 0.11, 0.36, 0.045, 0.26, X, tags, [fa, fp], depth=0.08, bed=X["gap"])
    zf = recess("fdo", 0, -0.10, 0.20, 0.06, 0.26, X, tags, [fa, fp], depth=0.07)
    B.box("fdo_o", 0, -0.10, 0.14, 0.035, zf, zf + 0.05, X["orange"], bevel=0.006, tags=tags)
    bolts("fdb", [(sx * 0.23, yy) for sx in (-1, 1) for yy in (-0.48, 0.92)], 0.265, X, tags, r=0.015)
    # ---- MOLDURA DO PAIOL: grossa, escura e arredondada (referencia), aro de bisel claro em volta da janela
    fr = chamfer_rect(-0.64, -1.95, 0.64, -0.60, (0.17, 0.17, 0.12, 0.12))
    wa, wp = gplate("mframe", fr, 0.0, 0.27, X, tags, slope=0.045, groove=0.014, panel_h=0.025, panel=X["gm"])
    hole = chamfer_rect(-WIN_HX, WIN_Y0, WIN_HX, MAG_TOP, (0.07, 0.07, 0.07, 0.07))
    rim = B.plate("mrim", chamfer_rect(-WIN_HX - 0.075, WIN_Y0 - 0.075, WIN_HX + 0.075, MAG_TOP + 0.075,
                                       (0.12, 0.12, 0.12, 0.12)), 0.27, 0.32, X["graph"], slope=0.035, tags=tags)
    for t in (wa, wp, rim):
        if t is not None:
            B.cut(t, [B.loft(f"mfc{t.name}", hole, hole, -0.5, 1.5, X["black"], bevel=0.0)])
    for sx in (-1, 1):
        B.box(f"mlip{sx}", sx * (WIN_HX + 0.008), (WIN_Y0 + MAG_TOP) / 2, 0.016, MAG_TOP - WIN_Y0, 0.0, 0.18,
              X["gap"], bevel=0.0, tags=tags)
        # insertos laranja nas laterais da moldura (as manchas laranja da referencia) e parafusos nos cantos
        zc = recess(f"mclip{sx}", sx * 0.555, -1.27, 0.06, 0.16, 0.30, X, tags, [wa, wp], depth=0.08)
        B.box(f"mclipo{sx}", sx * 0.555, -1.27, 0.04, 0.12, zc, zc + 0.05, X["orange"], bevel=0.004, tags=tags)
        bolts(f"mfb{sx}", [(sx * 0.545, -1.82), (sx * 0.545, -0.72)], 0.30, X, tags, r=0.017)
    zl = recess("latch", 0, -1.875, 0.24, 0.085, 0.30, X, tags, [wa, wp], depth=0.08)
    B.box("latch_o", 0, -1.875, 0.17, 0.055, zl, zl + 0.06, X["orange"], bevel=0.008, tags=tags)
    # ---- MOLAS laranja-ouro dos lados da moldura, na altura das capsulas
    for sx in (-1, 1):
        spring_housing(f"spr{sx}", sx * 0.835, -1.90, -0.66, X, tags)
    # ---- colunas de gunmetal ao lado da fenda: a de dentro com o pistao, a de fora com respiros e LEDs
    for sx, poly in sides(chamfer_rect(0.34, -0.56, 0.64, FEED_Y1 + 0.075, (0.0, 0.03, 0.03, 0.0))):
        a, p = gplate(f"pcol{sx}", poly, 0.0, 0.21, X, tags, slope=0.04, groove=0.014, panel_h=0.025)
        zb = recess(f"pcr{sx}", sx * 0.49, 0.30, 0.10, 1.20, 0.235, X, tags, [a, p], depth=0.10)
        B.cyl(f"prd{sx}", sx * 0.49, 0.30, zb + 0.03, 0.03, 1.16, X["rail"], axis="Y", verts=10, bevel=0.0, tags=tags)
        B.box(f"prdk{sx}", sx * 0.49, 0.80, 0.08, 0.05, zb, zb + 0.07, X["orange"], bevel=0.006, tags=tags)
        bolts(f"pcb{sx}", [(sx * 0.49, -0.44)], 0.235, X, tags, r=0.015)
    for sx, poly in sides([(0.68, -0.60), (1.05, -0.60), (1.05, 1.28), (1.00, 1.33), (0.68, 1.33)]):
        a, p = gplate(f"scol{sx}", poly, 0.0, 0.21, X, tags, slope=0.04, groove=0.014, panel_h=0.025)
        for i in range(3):
            recess(f"spv{sx}{i}", sx * 0.865, 0.92 + i * 0.11, 0.22, 0.045, 0.235, X, tags, [a, p], depth=0.07,
                   bed=X["gap"])
        ledslot(f"sp_led{sx}", sx * 0.865, 0.30, 0.05, 0.30, 0.235, 3, X, tags, [p, a], blue(0.5))
        zb = recess(f"smo{sx}", sx * 0.865, -0.30, 0.05, 0.20, 0.235, X, tags, [a, p], depth=0.07)
        B.box(f"smoi{sx}", sx * 0.865, -0.30, 0.03, 0.15, zb, zb + 0.045, X["orange"], bevel=0.004, tags=tags)
        bolts(f"spb{sx}", [(sx * 0.865, -0.52), (sx * 0.865, 0.72)], 0.245, X, tags, r=0.015)
    # ---- placas BRANCAS em cunha: o ombro alto (projeta para fora; fenda de visao do posto) e a de baixo, recuada
    sh_o = [(1.08, -0.64), (1.28, -0.64), (1.47, -0.45), (1.47, 1.06), (1.24, 1.30), (1.08, 1.30)]
    sh_t = [(1.08, -0.56), (1.24, -0.56), (1.34, -0.46), (1.34, 1.02), (1.20, 1.16), (1.08, 1.16)]
    lo_o = [(1.00, -1.96), (1.24, -1.96), (1.38, -1.82), (1.38, -0.84), (1.30, -0.76), (1.00, -0.76)]
    lo_t = [(1.00, -1.86), (1.20, -1.86), (1.29, -1.77), (1.29, -0.88), (1.25, -0.84), (1.00, -0.84)]
    for sx in (-1, 1):
        f = (lambda q: q) if sx > 0 else mirror_x
        sd, a, p = wwedge(f"wo{sx}", f(sh_o), f(sh_t), 0.0, 0.23, X, tags)
        zb = recess(f"wov{sx}", sx * 1.20, 0.40, 0.05, 0.26, 0.27, X, tags, [a, p, sd], depth=0.10)
        B.box(f"wovl{sx}", sx * 1.20, 0.40, 0.024, 0.20, zb, zb + 0.008, X["lens"], bevel=0.0, tags=tags)
        panel_lines(p, f"wol{sx}", [(sx * 1.20, yy, 0.16, 0) for yy in (-0.10, 0.90)], 0.24, X)
        bolts(f"wob{sx}", [(sx * 1.16, -0.44), (sx * 1.16, 1.06)], 0.27, X, tags, r=0.017, mat=X["orange"])
        sd, a, p = wwedge(f"wi{sx}", f(lo_o), f(lo_t), 0.0, 0.23, X, tags)
        zb = recess(f"wiv{sx}", sx * 1.14, -1.32, 0.05, 0.28, 0.27, X, tags, [a, p, sd], depth=0.10)
        B.box(f"wivo{sx}", sx * 1.14, -1.32, 0.03, 0.10, zb, zb + 0.04, X["orange"], bevel=0.004, tags=tags)
        bolts(f"wib{sx}", [(sx * 1.12, -0.94), (sx * 1.12, -1.74)], 0.27, X, tags, r=0.016)


# ============================================================================ PONTA (3x4)
# frente (weapon.png, y CROWN_Y0..2) em forma de escudo com a BOCA aberta no meio; o teto (y -2..CROWN_Y0) traz as
# cunhas brancas, os segmentos do nucleo em volta da fenda estreita, os blocos de tras e a cinta EM da emenda.
def ponta_floor(M, T="floor"):
    X = mats(M)
    tags = (T,)
    B.box("fl_base", 0, 0, 3.3, 4.3, -0.06, -0.02, X["core"], bevel=0.0, tags=tags)
    # calha do canal ate a frente: e o fundo da boca (nervuras + faixa escura: estrias da referencia sob a luz)
    channel_floor("ch", -2.0 - EXT, 2.0 + EXT, X, tags, rib_y0=-1.875)
    for sx in (-1, 1):
        B.box(f"bus{sx}", sx * 0.70, -0.75, 0.08, 2.5 + EXT, -0.02, 0.05, X["steel"], bevel=0.01, tags=tags)
        B.box(f"busk{sx}", sx * 0.70, -0.75, 0.02, 2.5 + EXT, 0.05, 0.056, X["black"], bevel=0.0, tags=tags)
        for k, yc in enumerate((-1.5, -0.5)):
            B.box(f"fp{sx}{k}", sx * 1.10, yc, 0.74, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)
            cap_module(f"cap{sx}{k}", sx, yc, X, tags)
        for k, yc in enumerate((0.5, 1.5)):
            B.box(f"fq{sx}{k}", sx * 1.04, yc, 0.84, 0.92, -0.02, 0.01, X["core_mid"], bevel=0.01, tags=tags)


def ponta_rails(M, T="trilhos"):
    X = mats(M)
    tags = (T,)
    rails("r", -2.0 - EXT, 1.90, X, tags)
    for sx in (-1, 1):
        B.box(f"rend{sx}", sx * (RAIL_IN + RAIL_OUT) / 2, 1.90, 0.12, 0.06, 0.0, 0.14, X["steel"], bevel=0.01,
              tags=tags)
    rail_clips("clip", (-1.75, -1.25, -0.75, -0.25, 0.25, 1.00, 1.50), X, tags)
    em_ring("ring0", PONTA_CLAMP, 0.0, X, tags)
    # emissor da garganta (o clarao da referencia): carcaca escura atravessando o canal com a lente azul apagada
    # entre os trilhos (acende pela carga5..6)
    B.box("thr_h", 0, FLARE_Y, 2 * (MOUTH + 0.04), 0.14, -0.01, 0.05, X["graph_d"], bevel=0.006, tags=tags)
    B.box("thr_b", 0, FLARE_Y, 2 * RAIL_IN - 0.03, 0.08, 0.05, 0.058, X["black"], bevel=0.0, tags=tags)
    B.box("thr_l", 0, FLARE_Y, 2 * RAIL_IN - 0.07, 0.04, 0.058, 0.066, X["lens"], bevel=0.0, tags=tags)
    # bobinas da boca: aneis escuros finos atravessando o fundo da boca (as estrias da luz azul)
    for i, y in enumerate((0.95, 1.30, 1.65)):
        B.box(f"mc{i}", 0, y, 2 * MOUTH - 0.02, 0.05, -0.01, 0.03, X["graph_d"], bevel=0.004, tags=tags)


def ponta_crown(M, T="weapon"):
    """weapon.png [0,0,3,1.5]: a frente em ESCUDO da referencia. Base escura com a BOCA cortada (garganta estreita
    atras que abre para a frente; a boca fica transparente: o dardo, os trilhos e o emissor da garganta estao embaixo);
    paredes de grafite com bisel claro dos dois lados da boca, TIRAS BRANCAS ao lado delas, bochechas de grafite na
    frente (chanfradas, LEDs azuis e inserto laranja) e os OMBROS BRANCOS (o topo das cunhas brancas do teto)."""
    X = mats(M)
    tags = (T,)
    mouth = [(-THROAT, CROWN_Y0 - 0.2), (THROAT, CROWN_Y0 - 0.2), (THROAT, CROWN_Y0), (MOUTH, MOUTH_Y1),
             (MOUTH, 2.3), (-MOUTH, 2.3), (-MOUTH, MOUTH_Y1), (-THROAT, CROWN_Y0)]
    base = B.plate("cr_base", CROWN_SIL, 0.0, 0.10, X["graph_d"], slope=0.03, tags=tags)
    B.cut(base, [B.loft("cr_mouth", mouth, mouth, -0.5, 1.0, X["black"], bevel=0.0)])
    # paredes da boca (grafite com bisel claro): da garganta ate a frente
    for sx, poly in sides([(THROAT + 0.015, CROWN_Y0 + 0.012), (0.47, CROWN_Y0 + 0.012), (0.47, 1.965),
                           (MOUTH + 0.015, 1.965), (MOUTH + 0.015, MOUTH_Y1 + 0.01)]):
        a, p = gplate(f"mw{sx}", poly, 0.05, 0.26, X, tags, slope=0.03, groove=0.012, panel_h=0.02)
        for i, yy in enumerate((0.95, 1.30, 1.65)):
            recess(f"mwr{sx}{i}", sx * 0.43, yy, 0.05, 0.10, 0.27, X, tags, [a, p], depth=0.06)
    # tiras brancas ao lado das paredes (a referencia: a linha branca que desce ao lado do canal azul)
    for sx, poly in sides([(0.50, CROWN_Y0 + 0.06), (0.62, CROWN_Y0 + 0.06), (0.62, 1.89), (0.565, 1.95),
                           (0.50, 1.95)]):
        wplate(f"ws{sx}", poly, 0.05, 0.30, X, tags, slope=0.035, panel_h=0.025)
    # bochechas de grafite da frente (chanfradas como o escudo)
    for sx, poly in sides([(0.66, 1.24), (0.87, 1.24), (0.87, 1.635), (0.66, 1.86)]):
        a, p = gplate(f"ck{sx}", poly, 0.05, 0.24, X, tags, slope=0.04, groove=0.014, panel_h=0.025)
        ledslot(f"ck_led{sx}", sx * 0.765, 1.42, 0.05, 0.22, 0.265, 2, X, tags, [p, a], blue(0.55))
        zb = recess(f"cko{sx}", sx * 0.765, 1.28, 0.12, 0.05, 0.265, X, tags, [a, p], depth=0.07)
        B.box(f"ckoi{sx}", sx * 0.765, 1.28, 0.09, 0.03, zb, zb + 0.05, X["orange"], bevel=0.004, tags=tags)
    # pontas das cunhas brancas (continuam as do teto depois da fresta em y CROWN_Y0): AFINAM para a frente ate uma
    # ponta junto da parede da boca (referencia: bochecha em cunha, face de cima clara + faceta lateral sombreada)
    sh_o = [(0.66, CROWN_Y0 + 0.045), (1.21, CROWN_Y0 + 0.045), (1.21, 0.80), (0.76, 1.19), (0.66, 1.19)]
    sh_t = [(0.68, CROWN_Y0 + 0.045), (0.92, CROWN_Y0 + 0.045), (0.92, 0.72), (0.71, 0.93), (0.68, 0.93)]
    for sx in (-1, 1):
        f = (lambda q: q) if sx > 0 else mirror_x
        sd, a, p = wwedge(f"wsh{sx}", f(sh_o), f(sh_t), 0.05, 0.30, X, tags)
        zb = recess(f"wshv{sx}", sx * 1.10, 0.64, 0.06, 0.16, 0.24, X, tags, [sd], depth=0.12, bed=X["gap"])
        bolts(f"wshb{sx}", [(sx * 0.80, 0.62)], 0.335, X, tags, r=0.018, mat=X["orange"])


def ponta_roof(M, T="roof"):
    """Teto da ponta (referencia): o canal largo so na emenda, a cinta EM (mesmo passo das cintas do cano) e depois a
    FENDA ESTREITA do nucleo ate a boca, entre os SEGMENTOS de grafite; as grandes CUNHAS BRANCAS dos lados (vent
    escuro, parafusos laranja), os blocos de grafite de tras e o convés pintado nas bordas e nos cantos da frente
    (fora do escudo)."""
    X = mats(M)
    tags = (T,)
    y0 = -2.0 - EXT
    yt = CROWN_Y0
    for sx in (-1, 1):
        B.box(f"u_neck{sx}", sx * (CH + 1.5) / 2, (y0 + NECK_Y) / 2, 1.5 - CH, NECK_Y - y0, -0.06, 0.0, X["gap"],
              bevel=0.0, tags=tags)
        q = [(CH, NECK_Y), (1.5, NECK_Y), (1.5, NECK_Y + 0.2), (THROAT, NECK_Y + 0.2)]
        B.loft(f"u_tap{sx}", q if sx > 0 else mirror_x(q), q if sx > 0 else mirror_x(q), -0.06, 0.0, X["gap"],
               bevel=0.0, tags=tags)
        B.box(f"u_core{sx}", sx * (THROAT + 1.5) / 2, (NECK_Y + 0.2 + yt) / 2, 1.5 - THROAT, yt - NECK_Y - 0.2, -0.06,
              0.0, X["gap"], bevel=0.0, tags=tags)
    # convés pintado: faixas das bordas, cantos de tras e cantos da frente (fora do escudo da frente)
    deck = [[(1.29, -0.985), (1.485, -0.985), (1.485, -0.015), (1.29, -0.015)],
            [(1.29, 0.015), (1.485, 0.015), (1.485, 0.98), (1.29, 0.98)],
            [(1.29, -1.985), (1.485, -1.985), (1.485, -1.015), (1.29, -1.015)],
            [(1.14, -1.985), (1.265, -1.985), (1.265, -1.63), (1.14, -1.76)],
            [(1.13, 1.02), (1.485, 1.02), (1.485, 1.985), (0.636, 1.985), (0.94, 1.68), (0.94, 1.215)]]
    for sx in (-1, 1):
        for k, poly in enumerate(deck):
            deck_plate(f"dk{sx}{k}", poly if sx > 0 else mirror_x(poly), X, tags)
    # segmentos do nucleo em volta da fenda (referencia: o nucleo escuro segmentado com pontos azuis)
    n = 7
    ys = [(-1.30 + i * (yt - 0.02 + 1.30) / n, -1.30 + (i + 1) * (yt - 0.02 + 1.30) / n - 0.025) for i in range(n)]
    for i, (a0, a1) in enumerate(ys):
        for sx, poly in sides(chamfer_rect(THROAT + 0.035, a0, 0.42, a1, (0.0, 0.03, 0.03, 0.0))):
            a, p = gplate(f"seg{sx}{i}", poly, 0.0, 0.19, X, tags, slope=0.03, groove=0.012, panel_h=0.02)
            if i % 2 == 1:
                ledslot(f"seg_led{sx}{i}", sx * 0.33, (a0 + a1) / 2, 0.07, 0.05, 0.21, 1, X, tags, [p, a], blue(0.6),
                        depth=0.06, pip=0.6)
    coaming("coam_n", NECK_Y + 0.15, yt, X, tags, z=0.16, x=THROAT)
    coaming("coam_w", y0, NECK_Y, X, tags, z=0.16, x=CH)
    # cunhas BRANCAS (a peca dominante da referencia)
    # critica ref-r1: as cunhas eram lajes brancas chapadas (liam como portas). Agora sao CUNHAS: a face de cima
    # branca (a metade de dentro) e a faceta lateral larga sombreada (white_s) por fora e na diagonal de tras, com a
    # fresta de respiro escura na faceta (a referencia)
    wd_o = [(0.46, yt - 0.03), (1.21, yt - 0.03), (1.25, yt - 0.07), (1.25, -0.50), (0.70, -1.28), (0.46, -1.28)]
    wd_t = [(0.48, yt - 0.03), (0.90, yt - 0.03), (0.93, yt - 0.06), (0.93, -0.42), (0.62, -1.10), (0.48, -1.10)]
    for sx in (-1, 1):
        f = (lambda q: q) if sx > 0 else mirror_x
        sd, a, p = wwedge(f"wd{sx}", f(wd_o), f(wd_t), 0.0, 0.26, X, tags, panel_h=0.032)
        zb = recess(f"wdv{sx}", sx * 1.09, -0.02, 0.07, 0.40, 0.17, X, tags, [sd], depth=0.12)
        for i in range(4):
            B.box(f"wdvl{sx}{i}", sx * 1.09, -0.17 + i * 0.10, 0.06, 0.025, zb, zb + 0.04, X["graph"], bevel=0.004,
                  tags=tags)
        panel_lines(p, f"wdl{sx}", [(sx * 0.70, -0.20, 0.36, 0)], 0.27, X)
        bolts(f"wdb{sx}", [(sx * 0.56, 0.36), (sx * 0.56, -0.98)], 0.295, X, tags, r=0.018, mat=X["orange"])
        bolts(f"wdb2{sx}", [(sx * 0.84, 0.36)], 0.295, X, tags, r=0.017)
    # blocos de grafite de tras (abaixo da diagonal das cunhas) + o pescoco que encosta no cano
    for sx, poly in sides([(0.70, -1.74), (1.10, -1.74), (1.25, -1.58), (1.25, -0.585), (0.70, -1.32)]):
        a, p = gplate(f"bb{sx}", poly, 0.0, 0.20, X, tags, slope=0.045, groove=0.014, panel_h=0.028)
        ledslot(f"bb_led{sx}", sx * 1.08, -1.30, 0.05, 0.30, 0.225, 3, X, tags, [p, a], blue(0.55))
        bolts(f"bbb{sx}", [(sx * 1.17, -1.60), (sx * 0.82, -1.62)], 0.225, X, tags, r=0.016)
    for sx, poly in sides([(0.70, -1.985), (1.10, -1.985), (1.10, -1.78), (0.70, -1.78)]):
        a, p = gplate(f"nk{sx}", poly, 0.0, 0.17, X, tags, slope=0.03, groove=0.012, panel_h=0.02)
        zb = recess(f"nko{sx}", sx * 0.90, -1.88, 0.14, 0.05, 0.19, X, tags, [a, p], depth=0.06)
        B.box(f"nkoi{sx}", sx * 0.90, -1.88, 0.10, 0.03, zb, zb + 0.045, X["orange"], bevel=0.004, tags=tags)
    for sx, poly in sides([(CH + 0.04, -1.985), (0.66, -1.985), (0.66, -1.70), (CH + 0.04, -1.70)]):
        gplate(f"nki{sx}", poly, 0.0, 0.15, X, tags, slope=0.03, groove=0.012, panel_h=0.02)
    clamp("cl", PONTA_CLAMP, X, tags)


def slug_sprite(M, T="slug"):
    """slug.png (0.8 x 3, ChainedTo Projectile, camada walls): o MESMO modelo do slug em voo
    (parts/bs_shells2.py, item "slug"), de pe (ponta para +Y), na luz das pecas, escala 1."""
    dart("slug", M, T, 0.0, (SLUG_X0 + SLUG_X1) / 2, SLUG_X1 - SLUG_X0, 1.0, z=0.0)
