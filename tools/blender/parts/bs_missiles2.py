"""Misseis 2.0 do Bullet Strike (kind "missiles", 64 px/tile): a escada futurista dos misseis em voo.

Pedido do usuario (2026-10-21): "os misseis tambem estao sendo refeitos ne? para deixa-los com aparencia mais
futurista". Mesma familia das granadas 2.0 (tools/blender/parts/bs_shells2.py): DOIS TONS, nucleo / estrakes /
nariz de GRAFITE contra blindagem de COMPOSITO claro com paineis de chanfro duplo mais claros (topo ~220) e filetes
de aco claro nos bordos de ataque e nos aros (~230), frestas pretas, faixas de LED em recessos, narizes sensores de
lente escura com reflexo; quanto maior o missil (s -> m -> l), mais futurista e mais luz.

r3 (critica da r2: "os mesmos misseis, mais apagados"): contraste de volta a faixa das granadas (p95 ~225), uma
mudanca de SILHUETA por tipo legivel a 1x, domo escuro do buscador na Jararaca, nariz da Piranha girado 45 graus
(fresta acesa no eixo), Jararaca G a mais iluminada das tres.

Conjunto 2.0 (design/art/spec_art.json -> assets.missiles; design/missiles/spec_missiles.json). Os tipos removidos
(napalm, lapa, torpedo isca, iscas) NAO existem aqui:

  Jararaca (HE, ambar)      he_s  Muricoca micro (Tocandira): cauda de grafite, luva clara partida por 1 faixa de LED,
                                  faixa ambar com aros, ogiva clara com a frente de grafite e o DOMO DO BUSCADOR de
                                  lente escura (~40% do nariz) com anel ambar e reflexo; 2 aletas cortadas com entalhe
                            he_m  (Caipora): anel de LED na cauda, 3 luvas em divisa claras com paineis sobre o nucleo
                                  escuro, ESTRAKES de grafite (asa-corpo) da raiz das aletas ate a 3a luva, aletas em
                                  flecha quebrada com filete de aco, fendas de trilho em V acesas no ombro da ogiva,
                                  frente de grafite + domo do buscador (sem os canards da Fase B)
                            he_l  (Mula): flecha de 5 segmentos de blindagem clara (paineis em cima e nos ombros) com
                                  frestas pretas de 2.5 px, ESTRAKES de grafite do meio do corpo ate as aletas em flecha
                                  quebrada (ponta cortada, entalhe), com a FENDA AMBAR acesa em todos os quadros; faixa
                                  ambar com aros; nariz sensor: visor com scanner de 3 LEDs, frente de grafite, domo de
                                  lente com o anel do buscador (o 2o estagio da Fase B saiu). Luzes (3 quadros):
                                  fendas fortes -> anel da cauda + visor -> buscador forte
  Piranha (cluster, amarela) cluster_m / cluster_l  PORTADOR gordo (estilo "Sunflower"/Transformers): baias claras
                                  com paineis nos ombros e JANELAS onde se veem os narizes dos mini-misseis, LEDs de
                                  armar que correm de baia em baia, faixa amarela com aros, aletas em flecha quebrada e
                                  o nariz em 4 PETALAS centradas a 45/135/225/315 graus: a fresta de CIMA corre no
                                  EIXO (labios de grafite + tira amarela acesa: fina e fraca em todos os quadros, larga
                                  e forte no ultimo, o "vai abrir"), dobradicas de aco na base de cada fresta (as de
                                  lado saem da silhueta), olho escuro na ponta. O l tem canards.
                            cluster_mini  mini-misseil teleguiado (0.5 x 0.19 quadro = 32 x 12 px): corpo claro, nariz
                                  escuro, faixa amarela, aletas e o COLAR LARANJA do propulsor pintado (sem atlas de
                                  luzes)
                            atlas de particulas bs_petals_m / bs_petals_l (+ _normals): as 4 petalas do nariz,
                                  256 x 256 = 4 x 4 de 64 px (fileira = petala com o seu giro proprio: 0 = casca de fora
                                  larga, 2 = face de dentro; coluna = inclinacao 0/30/55/75 graus), formato do
                                  debris_def.rules do jogo
  Poraque (PEM, azul-ciano) emp_m / emp_l  NUCLEO ESCURO na cauda com a fita baixa da enguia e 3 LAMINAS longas,
                                  finas e bem varridas (painel claro, filete de aco), colar de blindagem clara, bobinas
                                  de FIO de cobre (Mo.copper_mat) que saem da silhueta sobre a capsula escura, frestas
                                  entre as bobinas tingidas de CIANO no difuso (a cor le a 1x entre os pulsos) por onde
                                  a carga corre ate o emissor do nariz (ogiva escura com aneis de aco, anel ciano e
                                  lente); o l ganha 5 bobinas e os CHIFRES do emissor (2 bracos de aco que abrem e
                                  fecham na frente, pontas ciano viradas uma para a outra). Sem faixa de ogiva, sem
                                  listras
  Iara (nuclear, verde)     nuclear_l (estagio) / nuclear_wh_l (ogiva): continua INCONFUNDIVEL (o unico missil de
                                  blindagem escura): ogiva gorda blindada com o trevo grande (cunhas pretas sobre
                                  disco verde), DOIS aneis de faixa de perigo verde/preto em divisas emoldurando a
                                  ogiva, JANELAS DE CONTENCAO verdes acesas nos ombros (com grade de aco), faixas
                                  verdes largas que respiram, janela do nucleo, blindagem segmentada, bocal triplo com
                                  aneis verdes; r3: nariz SENSOR escuro e pontudo (colar de aco claro, ogiva facetada
                                  quase preta, domo de lente com anel verde aceso e reflexo, no lugar da tampa cinza
                                  rombuda) e 4 aletas em flecha quebrada com filete de aco; o estagio leva 2
                                  propulsores laterais segmentados. Nunca amarelo/preto.

Telas, quadros/fps, bocais e ancoras = os da tabela de arte dos misseis da Fase B (bs_missiles), menos os itens
removidos; cluster_mini e novo (0.5 x 0.19, estatico). Emissivos so em recessos, <= 3% do corpo no quadro 0
(Iara 4%); forcas baixas (a vista Standard estoura acima de ~1.5; azul/verde com cores proprias).

Cores de tipo (faixa + LEDs): HE ambar (Mo.band_mat("he"), LED sRGB ~(255,179,63), matiz 36), Piranha
AMARELO-limao (Mo.band_mat("cluster"), LED ~(255,237,89), matiz ~54: o mesmo "yellow petal cap" dos narizes da
Piranha nos casulos e o amarelo do escapamento da Fase B), Poraque CIANO (LED ~(39,222,255)), Iara verde. O laranja
palette.cluster.band do spec de arte (255,150,40, matiz 31) fica a ~5 graus da HE e nao se distingue a 1x: e uma
DECISAO mostrada ao usuario (docs/preview/3d/v2/misseis_futuristas.png, fim da folha); para renderizar a variante
laranja (so previas): BS_M2_CLUSTER=palette $PY tools/blender/render_part.py bs_missiles2 --out <rascunho>
--only cluster_m,cluster_l,cluster_mini.

Materiais: copias com nome proprio "m2_*" dos "s2_*" de bs_shells2.py (COMP, COMP_D, GRAPH, CORE, STEEL, lente,
PEM_BODY com os MESMOS valores; o cache de materiais do bs3d e por nome, entao os dois arquivos nunca se pisam).
Proprios dos misseis: COMP_L (paineis claros), RIM (filetes de aco claro), GLINT (reflexo da lente). Divergencias de
proposito: LED["emp"] (0.02, 0.72, 1.0) e mais ciano que o LED "pem" das granadas (0.05, 0.60, 1.0) (na cor do
Poraque o azul lia "azul generico" no casco branco); LED["cluster"] nao existe nas granadas. Na ligacao 2.0, se as
granadas mudarem COMP/GRAPH/etc., copie os valores para ca.

    $PY tools/blender/render_part.py bs_missiles2 --quick --out <rascunho> [--only he_m,cluster_l]
    $PY tools/blender/render_part.py bs_missiles2            # final em art3d/bs_missiles2/
    $PY tools/blender/parts/bs_missiles2.py --atlases [--quick] [--out DIR]   # petalas + bloco "atlases" no meta
    $PY tools/blender/parts/bs_missiles2.py --meta-only [--out DIR]           # so regrava o bloco "atlases"
    python3 tools/check_art3d.py art3d/bs_missiles2

Atlas das petalas (ligacao 2.0, WP10): o render_part.py completo (sem --only) GUARDA o bloco "atlases" do meta antigo
(e os PNGs dele) e no fim chama register_atlases(out) deste modelo, que regrava o bloco (idempotente); com --only o
meta antigo e mesclado e o bloco fica. `--atlases` (re-renderiza as petalas) e `--meta-only` (so regrava o bloco)
servem so para refazer as petalas a mao.

Notas para a ligacao 2.0 (regras):
  - o spec_missiles.json (visuals / cluster_sunflower) chama as texturas das petalas de "cluster_petal_m/l"; o spec
    de arte e esta entrega usam bs_petals_m.png / bs_petals_l.png (+ _normals): use os nomes do meta.json;
  - cluster_mini tem msl_cluster_mini_normals.png (o contrato do kit pede normais em todo item), mas o
    per_minis_components do spec diz SEM normais: nos 12-20 minis por portadora NAO ligue NormalsTexture/IsLit;
  - ancora "seeker" do Poraque mudou em relacao a Fase B (emp_m 0.6 -> 0.80, emp_l 0.85 -> 1.10: o emissor novo do
    nariz / o meio dos chifres); regenere a tabela de FX 2.0 com estas ancoras.
"""

import importlib
import math
import os
import sys

if __name__ == "__main__":                 # --atlases: roda direto (python com bpy), precisa do kit no caminho
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    importlib.import_module("bpy")         # o bpy carrega o bmesh que o bs3d importa

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
# r3 (critica: o conjunto lia como "os mesmos misseis" mais apagados): placas CLARAS de blindagem sobre o composito
# e filetes de aco claro nos bordos (o chanfro duplo claro das granadas 2.0: o topo dos paineis sai ~215-225 e os
# bordos ~225-235, contra o nucleo/nariz de grafite ~60-90)
COMP_L = (0.62, 0.64, 0.675)        # painel claro de chanfro duplo (topo dos paineis de blindagem)
RIM = (0.78, 0.81, 0.86)            # filete de aco claro (bordos de ataque, aros)
GLINT = (0.90, 0.93, 0.97)          # reflexo da lente do buscador (tinta: le no difuso)

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
        "comp_l": B.mat_paint("m2_comp_l", COMP_L, rough=0.38, metal=0.12, wear=0.0, grime=0.02, scale=5),
        "rim": _spec(B.mat_paint("m2_rim", RIM, rough=0.30, metal=0.20, wear=0.0, grime=0.0, scale=5), 0.3),
        "glint": B.mat_paint("m2_glint", GLINT, rough=0.25, metal=0.0, wear=0.0, grime=0.0, scale=5),
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


def _led(color, s, tint=0.02):
    """LED: emissao na cor com forca s; no difuso sai como LENTE ESCURA levemente tingida (STYLE 11.5). tint > 0.02:
    lente tingida na cor do tipo (as frestas do Poraque leem ciano a 1x mesmo entre os pulsos)."""
    m = B.mat_glow(f"m2_led_{color}_{int(round(s * 100)):03d}" + (f"_t{int(tint * 100):02d}" if tint != 0.02 else ""),
                   LED[color], s)
    b = m.node_tree.nodes["Principled BSDF"]
    c = LED[color]
    b.inputs["Base Color"].default_value = (c[0] * tint, c[1] * tint, c[2] * tint, 1)
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


# ============================================================================ pecas comuns da r3 (dois tons)
def armor(name, a, b, R, X, tags, ch=0.012, sides=True, inset=0.018):
    """Segmento de BLINDAGEM CLARA: anel de composito chanfrado + paineis claros de chanfro duplo em cima (e nos
    ombros): topo do painel ~220, chanfro ~170, fresta preta, nucleo escuro entre os segmentos."""
    sl = ring(name, a, b, R, X["comp"], tags, ch=ch)
    if b - a > 0.08:
        top_panel(name + "_t", a + 0.022, b - 0.020, R, X["comp_l"], tags, inset=inset)
        if sides:
            side_panels(name + "_s", a + 0.022, b - 0.020, R, X["comp_l"], tags, inset=inset)
    return sl


def edge(name, pts, w, z0, z1, X, tags, mat=None):
    """Filete claro de aco ao longo da polilinha pts (lado +y, espelhado em -y): o bordo de ataque claro das aletas e
    estrakes (o chanfro duplo claro das granadas 2.0, le no espaco escuro)."""
    for s in (1, -1):
        for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
            L = math.hypot(x1 - x0, y1 - y0)
            nx, ny = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
            strip = [(x0 + nx, s * (y0 + ny)), (x1 + nx, s * (y1 + ny)), (x1 - nx, s * (y1 - ny)),
                     (x0 - nx, s * (y0 - ny))]
            B.plate(f"{name}{i}{'l' if s > 0 else 'r'}", strip, z0, z1, mat or X["rim"], slope=0.002, bevel=0.001,
                    tags=tags)


def _strip(name, pts, mat, tags, th=0.007):
    """Tira fina que segue uma curva no plano XZ: pts = [(x, z_topo, largura)] (fresta acesa ao longo da ogiva)."""
    import bmesh
    import bpy
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    for x, z, w in pts:
        rows.append([bm.verts.new(v) for v in ((x, -w / 2, z), (x, w / 2, z), (x, w / 2, z - th), (x, -w / 2, z - th))])
    for ra, rb in zip(rows, rows[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def seeker(name, x0, x1, r, X, tags, LT, col, s, ring_w=0.018, glint=True):
    """Domo do buscador escuro: anel de LED do sensor (rebaixado, cor do tipo, forca s) + LENTE de vidro escuro com
    o reflexo claro (glint) no topo, um pouco atras da ponta."""
    ring(name + "_k", x0 - 0.004, x0 + ring_w + 0.004, r * 0.92, X["black"], tags)
    ring(name + "_l", x0, x0 + ring_w, r * 0.97, _led(col, s), _lt(LT, s))
    xl = x0 + ring_w
    lens_tip(name, xl, x1, r, X, tags)
    if glint:
        t = 0.32
        zs = r * max(0.0, 1 - t ** 1.8) ** (1 / 1.8)
        B.box(name + "_gl", xl + (x1 - xl) * t, 0.0, min(0.030, max(0.018, r * 0.50)), min(0.024, max(0.016, r * 0.42)),
              zs - 0.012, zs + 0.004,
              X["glint"], bevel=0.0, tags=tags)


def dark_nose(name, og, xs, X, tags, rear_mat=None):
    """Ogiva em DOIS TONS (familia das granadas 2.0): tras clara (composito) ate xs, aro de aco na divisa e a frente
    escura de grafite. Devolve (objeto de tras, objeto da frente)."""
    rear, front = _split(og, xs)
    ro = octo(name + "_r", rear, rear_mat or X["comp"], tags)
    fo = octo(name + "_f", front, X["graph"], tags)
    rs = _r_at(og, xs)
    ring(name + "_seam", xs - 0.009, xs + 0.009, rs * 1.035, X["rim"], tags, ch=0.003)
    return ro, fo


def type_band(name, xa, xb, R, mat, X, tags):
    """Faixa do tipo num colar escuro com aros de aco claro nas 2 bordas."""
    ring(name + "_k", xa - 0.012, xb + 0.012, R * 0.96, X["graph"], tags)
    ring(name, xa, xb, R * 1.025, mat, tags, ch=0.003)
    ring(name + "_a", xa - 0.012, xa, R * 1.035, X["rim"], tags, ch=0.003)
    ring(name + "_b", xb, xb + 0.012, R * 1.035, X["rim"], tags, ch=0.003)


# ============================================================================ Jararaca (HE, ambar)
def _he(M, X, T, LT, k, tier):
    """r3: dois tons (nucleo/estrakes/nariz de grafite x blindagem clara de chanfro duplo), domo do buscador de
    LENTE escura com reflexo e anel ambar em todos os niveis, aletas em flecha quebrada com filete de aco; o m e o l
    ganham ESTRAKES escuros (asa-corpo) da raiz das aletas ate o meio do corpo (silhueta nova a 1x)."""
    tags = (T,)
    band = _band("he")
    if tier == "s":
        # Muricoca micro: cauda de grafite, luva clara partida pela faixa de LED, faixa ambar, ogiva clara com o
        # domo escuro do buscador (40% da frente), 2 aletas cortadas com entalhe
        R = 0.056
        _nozzle(X, tags, -0.48, 0.036, 0.044, 0.035)
        octo("tail", [(R * 0.74, -0.452), (R * 0.98, -0.37)], X["graph"], tags)
        ring("spine", -0.40, 0.25, R * 0.86, X["core"], tags)
        ring("sl0", -0.372, -0.08, R, X["comp"], tags, ch=0.010)
        top_panel("pn0", -0.35, -0.10, R, X["comp_l"], tags, inset=0.012)
        led_groove("led", -0.042, 0.066, R * 0.92, "he", 1.2 if k == 0 else 0.22, X, tags, LT)
        ring("sl1", -0.006, 0.17, R, X["comp"], tags, ch=0.010)
        top_panel("pn1", 0.014, 0.15, R, X["comp_l"], tags, inset=0.012)
        type_band("band", 0.183, 0.219, R, band, X, tags)
        og = _ogive_to(R, 0.425 - 0.232, R * 0.50, 0.232)
        dark_nose("og", og, 0.355, X, tags)
        seeker("lens", 0.418, 0.480, R * 0.52, X, tags, LT, "he", 0.45 if k == 0 else 1.1, ring_w=0.014)
        fp = [(-0.25, R * 0.5), (-0.345, 0.118), (-0.392, 0.166), (-0.442, 0.166), (-0.425, 0.115), (-0.450, R * 0.5)]
        fin("fin", fp, 0.0, 0.020, X["comp"], tags)
        edge("fle", fp[:3], 0.012, -0.004, 0.016, X, tags)
        return
    if tier == "m":
        # Jararaca: anel de LED na cauda, 3 luvas em divisa (claras, com paineis) sobre o nucleo escuro, ESTRAKES de
        # grafite da raiz das aletas ate a 2a luva, faixa ambar com aros de aco, ogiva clara com as fendas de trilho
        # em V acesas e o domo escuro do buscador
        R = 0.078
        _nozzle(X, tags, -0.855, 0.048, 0.058, 0.05)
        octo("tail", [(R * 0.72, -0.815), (R * 0.98, -0.685)], X["graph"], tags)
        ring("spine", -0.82, 0.32, R * 0.86, X["core"], tags)
        led_groove("ring", -0.660, 0.036, R * 0.92, "he", 1.1 if k == 0 else 0.20, X, tags, LT, full=True)
        a0, xs1, dv, g = -0.632, 0.235, 0.05, 0.042
        span = xs1 - a0
        fl = span * 0.40
        rl = (span - fl - g * 2) / 2
        starts = [a0, a0 + rl + g, a0 + 2 * (rl + g)]
        for i, a in enumerate(starts):
            b = (a + rl) if i < 2 else (xs1 - dv)
            Mo.chevron_sleeve(f"sl{i}", a, b, R, X["comp"], tags, dv=dv, rear=i > 0, verts=8)
            p0 = a + (dv if i > 0 else 0.0) + 0.02
            top_panel(f"pn{i}", p0, b - 0.018, R, X["comp_l"], tags, inset=0.014)
        type_band("band", 0.250, 0.290, R, band, X, tags)
        xo, xl = 0.302, 0.792
        og = _ogive_to(R, xl - xo, R * 0.50, xo, n=12)
        ob, _ = dark_nose("og", og, 0.630, X, tags)
        # fendas de trilho em V no ombro claro da ogiva (borda de dentro acesa: fraca no quadro 0, forte no 1)
        xa, xb = xo + 0.06, xo + 0.25
        ra, rb = _r_at(og, xa), _r_at(og, xb)
        _vslits("rs", [ob], xa, xb, min(0.044, ra * TOPW / 2 + 0.006), 0.012, ra * COS8,
                (ra - rb) * COS8 + 0.035, X, tags, LT, "he", 1.1 if k == 1 else 0.0, w=0.026, lw=0.010)
        seeker("lens", xl - 0.004, 0.858, R * 0.50, X, tags, LT, "he", 0.30 if k == 0 else 1.1, ring_w=0.016)
        # estrakes escuros (asa-corpo): saem das aletas e morrem na 3a luva
        yb = R * COS8
        sk = [(0.16, R * 0.80), (-0.575, yb + 0.050), (-0.60, yb + 0.050), (-0.62, R * 0.80)]
        fin("strake", sk, -0.006, 0.016, X["graph"], tags, slope=0.004, groove=0.003, ph=0.003)
        edge("ske", sk[:2], 0.010, -0.004, 0.006, X, tags)
        # aletas da cauda em flecha quebrada, ponta cortada e entalhe no bordo de fuga; filete de aco no bordo de
        # ataque; garras escuras na raiz
        fp = [(-0.585, R * 0.7), (-0.585, yb + 0.046), (-0.712, 0.290), (-0.790, 0.290), (-0.772, 0.205),
              (-0.818, R * 0.7)]
        fin("fin", fp, 0.0, 0.024, X["comp"], tags, panel_mat=X["comp_l"])
        edge("fle", fp[1:4], 0.013, -0.004, 0.018, X, tags)
        for s in (1, -1):
            B.box(f"claw{s}", -0.67, s * R * 0.98, 0.20, 0.028, -0.03, 0.032, X["graph"], bevel=0.004, tags=tags)
        return
    # he_l (Mula): flecha de blindagem SEGMENTADA clara sobre o nucleo escuro (5 segmentos, frestas pretas de 2.5 px),
    # ESTRAKES de grafite com fenda ambar acesa do meio do corpo ate as aletas grandes em flecha quebrada (filete de
    # aco), faixa ambar com aros, nariz sensor: visor com scanner de 3 LEDs na parte clara, frente de grafite e domo
    # de lente com o anel do buscador aceso. Luzes que correm (3 quadros): fendas dos estrakes fortes -> anel da
    # cauda + visor -> buscador forte; as fendas e o buscador nunca apagam (a mais iluminada das 3 Jararacas, <= 3%)
    R = 0.092
    _nozzle(X, tags, -1.232, 0.066, 0.078, 0.068)
    octo("tail", [(R * 0.76, -1.175), (R * 0.98, -1.075)], X["graph"], tags)
    ring("spine", -1.08, 0.63, R * 0.86, X["core"], tags)
    on_ring = (0.0, 1.15, 0.30)[k % 3]
    on_slit = (1.15, 0.55, 0.55)[k % 3]
    on_seek = (0.50, 0.50, 1.15)[k % 3]
    led_groove("ring", -1.052, 0.036, R * 0.92, "he", on_ring, X, tags, LT, full=True)
    segs = [(-1.028, -0.770), (-0.730, -0.470), (-0.430, -0.170), (-0.130, 0.170), (0.210, 0.500)]
    for i, (a, b) in enumerate(segs):
        armor(f"seg{i}", a, b, R, X, tags)
    type_band("band", 0.535, 0.590, R, band, X, tags)
    xo, xl = 0.615, 1.172
    og = _ogive_to(R, xl - xo, R * 0.50, xo, n=14)
    xs = 0.985
    o1, o2 = _visor("vis", og[:], xo + 0.135, X, tags, LT, "he", k, hw=0.026)
    # (o visor parte o perfil; a parte clara vai ate xs e a escura dai ate a lente)
    r2a, r2b = _split(o2, xs)
    octo("og1", o1, X["comp"], tags)
    octo("og2", r2a, X["comp"], tags)
    octo("og3", r2b, X["graph"], tags)
    ring("og_seam", xs - 0.010, xs + 0.010, _r_at(og, xs) * 1.035, X["rim"], tags, ch=0.003)
    seeker("lens", xl - 0.004, 1.226, R * 0.50, X, tags, LT, "he", on_seek, ring_w=0.018)
    # estrakes de grafite (asa-corpo) com a fenda ambar no bordo de fora
    yb = R * COS8
    sk = [(0.30, R * 0.80), (-0.835, yb + 0.074), (-0.87, yb + 0.074), (-0.89, R * 0.80)]
    fin("strake", sk, -0.008, 0.018, X["graph"], tags, slope=0.004, groove=0.003, ph=0.003)
    edge("ske", sk[:2], 0.010, -0.004, 0.008, X, tags)
    for s in (1, -1):
        # fenda acesa: rebaixo preto + tira ambar paralela ao bordo do estrake (de -0.58 a -0.16)
        (x0, y0), (x1, y1) = sk[1], sk[0]
        xa_, xb_ = -0.73, -0.46
        ya = y1 + (y0 - y1) * (x1 - xa_) / (x1 - x0) - 0.022
        yb_ = y1 + (y0 - y1) * (x1 - xb_) / (x1 - x0) - 0.022
        rot = math.degrees(math.atan2(s * (yb_ - ya), xb_ - xa_))
        Ls = math.hypot(xb_ - xa_, yb_ - ya)
        cx, cy = (xa_ + xb_) / 2, s * (ya + yb_) / 2
        B.rbox(f"sks{s}", cx, cy, Ls, 0.028, 0.004, 0.0125, X["black"], rot=rot, bevel=0.0, tags=tags)
        B.rbox(f"sksl{s}", cx, cy, Ls - 0.02, 0.016, 0.010, 0.0150, _led("he", on_slit), rot=rot, bevel=0.0,
               tags=_lt(LT, on_slit))
    # aletas grandes em flecha quebrada (ponta cortada, entalhe no bordo de fuga), painel claro, filete de aco
    fp = [(-0.855, R * 0.7), (-0.855, yb + 0.070), (-1.012, 0.405), (-1.100, 0.405), (-1.078, 0.290),
          (-1.165, R * 0.7)]
    fin("fin", fp, 0.0, 0.030, X["comp"], tags, panel_mat=X["comp_l"])
    edge("fle", fp[1:4], 0.016, -0.004, 0.022, X, tags)
    for s in (1, -1):
        B.box(f"claw{s}", -1.00, s * R * 0.98, 0.24, 0.034, -0.035, 0.038, X["graph"], bevel=0.005, tags=tags)


# ============================================================================ Piranha (cluster, amarela)
def _oct_pt(r, a):
    """Ponto (y, z) da superficie do octogono de topo plano (vertices em 22.5 + 45k graus) de raio r no angulo a."""
    k = math.floor((a - 22.5) / 45.0)
    va, vb = math.radians(22.5 + 45 * k), math.radians(22.5 + 45 * (k + 1))
    t = (math.radians(a) - va) / (vb - va)
    ya, za = math.cos(va), math.sin(va)
    yb, zb = math.cos(vb), math.sin(vb)
    return r * (ya + (yb - ya) * t), r * (za + (zb - za) * t)


def _petal_angles(a_from, a_to, extra=()):
    """Angulos de amostra de uma petala: as pontas, os vertices do octogono no meio e os extras (bordas dos labios)."""
    angs = {round(a_from, 6), round(a_to, 6)}
    angs |= {round(e, 6) for e in extra if a_from + 1e-6 < e < a_to - 1e-6}
    v = 22.5 - 360.0
    while v < a_to - 1e-6:
        if v > a_from + 1e-6:
            angs.add(round(v, 6))
        v += 45.0
    return sorted(angs)


def petal_mesh(name, prof, a_c, half, X, tags, thick=0.82, lip=8.0):
    """UMA petala do nariz da Piranha: casca do octogono entre a_c - half e a_c + half graus (faces planas). Face de
    fora em composito CLARO (comp_l) com LABIOS de grafite de `lip` graus junto das frestas (r3: a fresta escura fica
    larga e le a 1x), face de dentro e paredes em grafite (espessura = raio x (1 - thick)). prof = [(raio, x)] da
    base para a ponta."""
    import bmesh
    import bpy
    a0, a1 = a_c - half, a_c + half
    angs = _petal_angles(a0, a1, (a0 + lip, a1 - lip))
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    outer, inner = [], []
    for r, x in prof:
        pts = [_oct_pt(r, a) for a in angs]
        outer.append([bm.verts.new((x, y, z)) for y, z in pts])
        inner.append([bm.verts.new((x, y * thick, z * thick)) for y, z in pts])
    n = len(angs)
    lipm = [(0.5 * (angs[i] + angs[i + 1]) < a0 + lip - 1e-6) or (0.5 * (angs[i] + angs[i + 1]) > a1 - lip + 1e-6)
            for i in range(n - 1)]
    faces = []
    for ra, rb, ia, ib in zip(outer, outer[1:], inner, inner[1:]):
        for i in range(n - 1):
            faces.append((bm.faces.new((ra[i], ra[i + 1], rb[i + 1], rb[i])), 1 if lipm[i] else 0))
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
    ob.data.materials.append(X["comp_l"])
    ob.data.materials.append(X["graph"])
    for t in tags:
        ob[t] = True
    return ob


CL = {
    # R, bocal, fim da cauda, baias (de, ate), n baias, nariz, envergadura das aletas, minis por janela, fresta das
    # petalas (graus)
    "m": {"R": 0.150, "x0": -0.855, "xt": -0.62, "bays": (-0.595, 0.215), "nb": 3, "xn": 0.855, "span": 0.352,
          "nmini": 3, "gap": 20.0},
    "l": {"R": 0.200, "x0": -1.23, "xt": -0.92, "bays": (-0.895, 0.385), "nb": 4, "xn": 1.23, "span": 0.465,
          "nmini": 3, "gap": 16.0},
}
# petalas centradas a 45/135/225/315 graus (r3): a fresta de CIMA corre no eixo (vista de cima: 2 petalas claras e a
# linha escura acesa no meio); as frestas de lado ficam no contorno, marcadas pelas dobradicas que saem da silhueta
PETAL_C = (45.0, 135.0, 225.0, 315.0)


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
    """r3: portador de DOIS TONS (baias claras com paineis de chanfro duplo sobre o nucleo escuro), aletas em flecha
    quebrada com filete de aco, e o nariz em 4 petalas girado 45 graus: a fresta de cima corre no EIXO (labios de
    grafite + tira amarela acesa fraca em todos os quadros e forte no ultimo, o "vai abrir"), dobradicas de aco na
    base de cada fresta (as de lado saem da silhueta: entalhes legiveis a 1x)."""
    tags = (T,)
    c = CL[tier]
    R, x0, xt, (b0, b1), nb, xn = c["R"], c["x0"], c["xt"], c["bays"], c["nb"], c["xn"]
    sc = R / 0.15
    n_frames = PART["items"][f"cluster_{tier}"]["frames"]
    arm = (k % n_frames) == n_frames - 1
    # cauda: bocal, cone de grafite, 2 aletas em flecha quebrada (ponta cortada, entalhe) + dorsal de quina
    _nozzle(X, tags, x0, R * 0.42, R * 0.50, 0.06 * sc)
    octo("tail", [(R * 0.56, x0 + 0.05 * sc), (R * 0.96, xt)], X["graph"], tags)
    spine = ring("spine", xt - 0.02, b1 + 0.06 * sc, R * 0.86, X["core"], tags)
    sp = c["span"]
    fp = [(xt + 0.03 * sc, R * 0.7), (xt - 0.05 * sc, R * COS8 + 0.05 * sc), (x0 + 0.13 * sc, sp),
          (x0 + 0.06 * sc, sp), (x0 + 0.075 * sc, sp - 0.07 * sc), (x0 + 0.055 * sc, R * 0.7)]
    fin("fin", fp, 0.0, 0.026 * sc, X["comp"], tags, panel_mat=X["comp_l"])
    edge("fle", fp[1:4], 0.014 * sc, -0.004, 0.020 * sc, X, tags)
    dorsal("dors", x0 + 0.08 * sc, xt - 0.01, R * 0.80 * COS8, 0.05 * sc, X["graph"], tags, w=0.024 * sc)
    # baias com janelas: os narizes dos minis enfileirados aparecem no fundo escuro; paineis claros nos ombros
    g = 0.040 * sc
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
        side_panels(f"ps{i}", a + 0.02 * sc, b - 0.02 * sc, R, X["comp_l"], tags, inset=0.014 * sc)
    # LEDs de armar: tiras acesas nas frestas entre as baias; correm para a frente
    n_led = nb
    xs_led = [b0 + (i + 1) * (blen + g) - g / 2 for i in range(nb - 1)]
    for i, xl in enumerate(xs_led):
        on = 1.15 if i == k % n_led else 0.0
        led_groove(f"led{i}", xl, g * 1.02, R * 0.90, "cluster", on, X, tags, LT)
    if tier == "l":
        # canards na ultima baia (flecha, filete de aco)
        cp = [(b1 - 0.03, R * 0.8), (b1 - 0.12, R + 0.12), (b1 - 0.19, R + 0.12), (b1 - 0.21, R * 0.8)]
        fin("can", cp, 0.0, 0.022, X["comp"], tags, panel_mat=X["comp_l"])
        edge("cle", cp[:3], 0.014, -0.004, 0.016, X, tags)
    # faixa amarela com aros de aco + anel da dobradica (escuro) com o LED de armar do nariz
    xb = b1 + 0.004
    og, xo, xe = cluster_nose_profile(tier)
    type_band("band", xb + 0.012, xb + 0.012 + 0.030 * sc, R, _band("cluster"), X, tags)
    on = 1.15 if (nb - 1) == k % n_led else 0.0
    xbe = xb + 0.024 + 0.030 * sc
    if xo - xbe > 0.012:
        led_groove("ledn", (xbe + xo) / 2, xo - xbe + 0.004, R * 0.90, "cluster", on, X, tags, LT)
    # nariz em 4 petalas sobre a ogiva interna preta, frestas a 0/90/180/270 graus
    gap = c["gap"]
    for j, ac in enumerate(PETAL_C):
        petal_mesh(f"petal{j}", og, ac, 45.0 - gap / 2, X, tags)
    octo("og_in", [(r * 0.84, x) for r, x in og], X["black"], tags)
    # fresta de cima (no eixo) ACESA: tira amarela no fundo preto entre as petalas, da base ate perto da ponta,
    # fraca em todos os quadros e forte no ultimo ("vai abrir")
    # (fraca = tira fina de ~0.6 px: cobre pouco e cabe no orcamento de 3% do quadro 0; forte = a tira larga)
    s_seam = 1.15 if arm else 0.45
    xa = xo + 0.02 * sc
    xz = xe - 0.05 * sc
    w0 = 0.019 * sc if arm else 0.0095
    pts = [(x, _r_at(og, x) * 0.84 * COS8 + 0.003, max(0.0095, w0 * (1.0 - 0.5 * (x - xa) / (xz - xa))))
           for x in (xa + (xz - xa) * j / 10 for j in range(11))]
    _strip("seam", pts, _led("cluster", s_seam), _lt(LT, s_seam))
    rt = og[-1][0]
    lens_tip("eye", xe - 0.004, xn, rt * 1.02, X, tags)
    # dobradicas de aco na base das frestas: a de cima (no eixo) e as 2 de lado, que saem da silhueta
    rr = _r_at(og, xo + 0.03 * sc)
    hl = 0.050 * sc
    B.box("hinge_t", xo + 0.028 * sc, 0.0, hl, 0.040 * sc, rr * COS8 - 0.012, rr * COS8 + 0.010 * sc, X["rim"],
          bevel=0.003, tags=tags)
    for s in (1, -1):
        # dobradica de lado: bloco de aco que sai ~2 px da silhueta, com a fenda escura do pino no meio
        yh = rr * COS8 + 0.010 * sc
        B.box(f"hinge{s}", xo + 0.030 * sc, s * yh, hl * 1.25, 0.044 * sc, -0.024 * sc, 0.024 * sc, X["rim"],
              bevel=0.003, tags=tags)
        B.box(f"hingek{s}", xo + 0.030 * sc, s * (yh + 0.004 * sc), hl * 0.32, 0.046 * sc, -0.026 * sc,
              0.026 * sc, X["graph"], bevel=0.0, tags=tags)


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
def _coil(X, T, name, xc, w, R, turns=3, h=0.13):
    """Bobina de FIO de cobre: espiras redondas (16 lados lisos, o cobre do Poraque) sobre um carretel escuro. h =
    altura das espiras / R (r3: 0.13, as bobinas saem da silhueta: corpo "enrolado" legivel a 1x)."""
    tags = (T,)
    ring(name + "_k", xc - w / 2, xc + w / 2, R * 1.0, X["core"], tags)
    pw = w / turns
    for i in range(turns):
        a = xc - w / 2 + i * pw + pw * 0.08
        b = a + pw * 0.84
        hh = R * h
        prof = [(R * 1.0, a)] + [(R * 1.0 + hh * math.sin(math.pi * t / 6), a + (b - a) * t / 6) for t in range(1, 6)]
        prof += [(R * 1.0, b)]
        smooth(f"{name}_{i}", prof, X["copper"], tags, verts=16)


def _lit_band(X, name, x, w, R, color, s, tags, LT, lip=None, lip_r=1.06, tint=0.02):
    """Faixa acesa num rebaixo: anel aceso entre dois labios escuros mais altos (lip_r * R)."""
    if lip:
        ring(name + "_a", x - w / 2 - lip, x - w / 2, R * lip_r, X["graph"], tags, ch=0.004)
        ring(name + "_b", x + w / 2, x + w / 2 + lip, R * lip_r, X["graph"], tags, ch=0.004)
    ring(name + "_l", x - w / 2, x + w / 2, R * 1.005, _led(color, s, tint), _lt(LT, s))


def _blades(name, roots, r0, L, hs, X, tags, th=0.016):
    """Laminas da enguia (r3): poucas (3), LONGAS, finas e bem varridas sobre o nucleo escuro, com painel claro e
    filete de aco no bordo de ataque (no lugar das 4-5 escamas em dente de serra, que liam "espinha de peixe")."""
    # fita escura baixa da enguia ligando as raizes (as laminas saem dela: um sistema so, nao varetas soltas)
    hr = 0.030
    rib = [(roots[0] + 0.02, r0 * 0.80), (roots[0] - 0.06, r0 + hr), (roots[-1] - L * 0.80, r0 + hr),
           (roots[-1] - L * 0.95, r0 * 0.80)]
    fin(name + "_rib", rib, -0.004, th * 0.9, X["graph"], tags, slope=0.004, groove=0.003, ph=0.003)
    for i, (xr, h) in enumerate(zip(roots, hs)):
        yt = r0 + h
        poly = [(xr, r0 * 0.72), (xr - L, yt), (xr - L - 0.035, yt), (xr - L * 0.58, r0 * 0.72)]
        fin(f"{name}{i}", poly, 0.003 * (len(roots) - i), th, X["comp_d"], tags, slope=0.005, groove=0.004,
            panel_mat=X["comp_l"])
        edge(f"{name}{i}e", poly[:2], 0.012, -0.004, th / 2 + 0.004, X, tags)


def _emp(M, X, T, LT, k, tier):
    """r3: nucleo escuro com 3 laminas longas varridas (claras, filete de aco), bobinas de cobre que saem da
    silhueta com as frestas tingidas de CIANO no difuso (a cor le a 1x entre os pulsos), nariz emissor escuro com o
    anel ciano e a lente; o l ganha 2 segmentos de blindagem clara e os CHIFRES do emissor (abrem e fecham na
    frente: o arco salta entre as pontas ciano)."""
    tags = (T,)
    late = tier == "l"
    if not late:
        R, x0, xn = 0.088, -0.855, 0.855
        x_c0, x_c1 = -0.72, -0.10
        coils = [0.03, 0.205, 0.38]
        cw, turns = 0.12, 3
        roots, Lb, hs = [-0.16, -0.36, -0.56], 0.21, [0.10, 0.15, 0.20]
    else:
        R, x0, xn = 0.104, -1.23, 1.06
        x_c0, x_c1 = -1.06, -0.36
        coils = [-0.155, 0.02, 0.195, 0.37, 0.545]
        cw, turns = 0.13, 3
        roots, Lb, hs = [-0.44, -0.67, -0.90], 0.27, [0.14, 0.21, 0.29]
    sc = R / 0.088
    _nozzle(X, tags, x0, R * 0.52, R * 0.62, 0.055 * sc)
    octo("tail", [(R * 0.66, x0 + 0.045 * sc), (R * 0.97, x_c0)], X["graph"], tags)
    ring("core", x_c0 - 0.01, x_c1 + 0.01, R * 0.90, X["pem"], tags)
    lit = []          # funcoes que desenham com a forca s: a carga corre na ordem da lista
    tint = 0.45       # lente tingida de ciano no difuso

    def rear(s):
        _lit_band(X, "bring", x_c0 + 0.035, 0.030, R * 0.93, "emp", s, tags, LT, lip=0.014, lip_r=1.02 / 0.93,
                  tint=tint)
    lit.append(rear)
    # a cauda escura com aneis de aco finos (costuras) e as laminas
    for j, xx in enumerate([x_c0 + 0.09 + (x_c1 - x_c0 - 0.12) * t for t in (0.33, 0.66)]):
        ring(f"cseam{j}", xx - 0.008, xx + 0.008, R * 0.95, X["steel"], tags, ch=0.003)
    _blades("bl", roots, R * COS8, Lb, hs, X, tags, th=0.016 * sc)
    if late:
        for i, (a, b) in enumerate(((x_c1 - 0.01, -0.21),)):
            armor(f"arm{i}", a, b, R, X, tags)
    else:
        armor("arm0", x_c1 - 0.01, -0.01, R, X, tags, sides=False)
    # capsula escura sob as bobinas
    xa_cap = (-0.21 if late else -0.01)
    ring("cap", xa_cap, coils[-1] + cw / 2 + 0.04, R * 0.97, X["pem"], tags)
    for i, xc in enumerate(coils):
        _coil(X, T, f"coil{i}", xc, cw, R, turns)
    # frestas ciano entre as bobinas (com labios escuros): a carga corre da cauda para o nariz
    gaps = [(coils[i] + coils[i + 1]) / 2 for i in range(len(coils) - 1)]
    gw = coils[1] - coils[0] - cw
    for i, xg in enumerate(gaps):
        def gap(s, i=i, xg=xg):
            _lit_band(X, f"gap{i}", xg, gw * 0.56, R, "emp", s, tags, LT, lip=gw * 0.20, tint=tint)
        lit.append(gap)
    # emissor do nariz: colar de aco, ogiva escura com 2 aneis de aco, anel ciano e lente com reflexo
    xc1 = coils[-1] + cw / 2 + 0.01
    ring("ncol", xc1, xc1 + 0.035, R * 1.04, X["rim"], tags, ch=0.004)
    xo = xc1 + 0.03
    xl = xn - 0.07 * sc
    og = _ogive_to(R, xl - xo, R * 0.50, xo, n=10)
    octo("og", og, X["pem"], tags)
    for j, t in enumerate((0.35, 0.70)):
        xx = xo + (xl - xo) * t
        ring(f"nring{j}", xx, xx + 0.026, _r_at(og, xx + 0.013) * 1.07, X["steel"], tags, ch=0.004)
    eye_s = []

    def eye(s):
        eye_s.append(s)
    lit.append(eye)
    if late:
        # CHIFRES do emissor: 2 bracos de aco que abrem do colar e fecham na frente, pontas ciano viradas uma para a
        # outra (o arco do PEM salta no meio, onde fica a ancora "seeker" 1.10)
        yb = R * COS8
        P0, P1, P2 = (xo + 0.01, yb - 0.01), (0.86, 0.205), (1.165, 0.088)
        for s in (1, -1):
            for j, (pa, pb) in enumerate(((P0, P1), (P1, P2))):
                L = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) + 0.03
                rot = math.degrees(math.atan2(s * (pb[1] - pa[1]), pb[0] - pa[0]))
                B.rbox(f"horn{j}{s}", (pa[0] + pb[0]) / 2, s * (pa[1] + pb[1]) / 2, L, 0.036, -0.016, 0.022,
                       X["steel"], rot=rot, chamfer=0.010, bevel=0.004, tags=tags)
                B.rbox(f"hornp{j}{s}", (pa[0] + pb[0]) / 2, s * (pa[1] + pb[1]) / 2, L * 0.70, 0.016, 0.018, 0.026,
                       X["graph"], rot=rot, bevel=0.0, tags=tags)
            B.box(f"elbow{s}", P1[0], s * P1[1], 0.050, 0.050, -0.020, 0.028, X["graph"], bevel=0.006, tags=tags)
        ptip = 1.2 if k == 3 else 0.30

        def tips(s):
            for sy in (1, -1):
                B.box(f"ptip{sy}", P2[0] + 0.012, sy * (P2[1] - 0.012), 0.040, 0.026, -0.010, 0.026,
                      _led("emp", s, tint), bevel=0.0, tags=_lt(LT, s))
        tips(ptip)
    # a onda: o elemento k forte, o anterior medio, o resto apagado (no l, 2 frestas por quadro)
    n = len(lit)
    pos = [round(i * (n - 1) / 3) for i in range(4)]
    lead = pos[k % 4]
    for i, fn in enumerate(lit):
        s = 1.05 if i == lead else (0.32 if i == lead - 1 else 0.0)
        fn(s)
    s_eye = max(eye_s[0] if eye_s else 0.0, 0.30)
    seeker("lens", xl - 0.004, xn, R * 0.50, X, tags, LT, "emp", s_eye, ring_w=0.020)


# ============================================================================ Iara (nuclear, verde)
def _iara(M, X, T, LT, k, xt, xn, boosters):
    tags = (T,)
    D, P, S, BLK = X["dark"], X["plate"], X["steel"], X["black"]
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
    # ---- nariz SENSOR (r3, familia das granadas 2.0): colar de aco claro, ogiva facetada ESCURA mais pontuda (a
    # tampa cinza rombuda da Fase B saiu) e o domo de LENTE grande com o anel verde aceso e o reflexo
    xc0 = xw1 + 0.008
    xs0 = xn - 0.13
    octo("cap", [(RW * 0.985, xc0), (RW * 0.92, xc0 + 0.05), (RW * 0.64, xc0 + 0.17), (RW * 0.42, xs0)],
         X["core"], tags)
    ring("capr", xc0 + 0.022, xc0 + 0.046, RW * 1.0, X["rim"], tags, ch=0.003)
    xm = xc0 + 0.105
    ring("capr2", xm - 0.009, xm + 0.009, _r_at([(RW * 0.92, xc0 + 0.05), (RW * 0.64, xc0 + 0.17)], xm) * 1.03,
         S, tags, ch=0.003)
    seeker("lens", xs0, xn, RW * 0.42, X, tags, LT, "nuke", br, ring_w=0.024)
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
    # aletas em flecha QUEBRADA (r3): raiz longa e baixa, painel de fora mais em pe, ponta cortada e entalhe no bordo
    # de fuga; filete de aco claro no bordo de ataque
    finp = [(xt + 0.56, 0.12), (xt + 0.36, 0.34), (xt + 0.27, 0.64), (xt + 0.15, 0.64), (xt + 0.20, 0.44),
            (xt + 0.13, 0.12)]
    fin("fin", finp, 0.0, 0.028, D, tags, slope=0.014, groove=0.010, ph=0.010, panel_mat=P)
    edge("fle", finp[:3], 0.020, 0.006, 0.026, X, tags)
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
            ring(f"bocol{sy}", x1b - 0.02, x1b + 0.005, 0.09, X["rim"], tags, ch=0.003, y=yy)
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
                       X["rim"], bevel=0.003, tags=tags)
            hz.matrix_world = tr @ rot @ Matrix.Translation(-cen) @ hz.matrix_world
    bpy.context.view_layer.update()


def register_atlases(out):
    """Grava (ou regrava) o bloco "atlases" e os arquivos das petalas no out/meta.json. Idempotente: pode rodar
    quantas vezes quiser. O render_part.py completo guarda o bloco antigo e chama esta funcao no fim (o bloco fica
    ou e atualizado); `bs_missiles2.py --meta-only` / `--atlases` so sao precisos para refazer as petalas a mao."""
    import json
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
    missing = [f for a in PART["atlases"].values() for f in (a["file"], a["normals"])
               if not os.path.exists(os.path.join(out, f))]
    if missing:
        print(f"AVISO: meta.json cita atlas que ainda nao existem em {out}: {missing} (rode --atlases)")


def render_atlases(out, quick=False):
    """Renderiza bs_petals_<m|l>.png + _normals.png (256 x 256) em out e registra em out/meta.json ("atlases")."""
    import bpy
    for key, at in PART["atlases"].items():
        B.reset("axial")
        M = Mo.mats(PART.get("accent", "amber"))
        B.camera(4.0, 4.0, (0, 0), px=at["sprite_px"])
        bpy.context.scene.cycles.samples = 12 if quick else 48
        petal_atlas(M, at["tier"])
        B.show_only(["body"])
        base = os.path.join(out, at["file"][:-4])
        B.render_set(base, (at["texture_px"], at["texture_px"]), glow_halo=False, normals=True, off=False,
                     glow=False)
        print(f"atlas {key}: {at['file']} + {at['normals']}")
    register_atlases(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    out_dir = args[args.index("--out") + 1] if "--out" in args else os.path.join(root, "art3d", "bs_missiles2")
    if "--atlases" not in args and "--meta-only" not in args:
        sys.exit("uso: bs_missiles2.py --atlases [--quick] [--out DIR]   |   bs_missiles2.py --meta-only [--out DIR]")
    os.makedirs(out_dir, exist_ok=True)
    if "--atlases" in args:
        render_atlases(out_dir, quick="--quick" in args)
    else:
        register_atlases(out_dir)
