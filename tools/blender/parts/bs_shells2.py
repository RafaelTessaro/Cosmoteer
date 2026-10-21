"""Projeteis 2.0 (kind "shells", 128 px/tile): escada futurista das granadas, PEM e slug da railgun.

REQ 11 do usuario: "calibre maior = mais futurista". As granadas navais viram municoes de ficcao cientifica, cada
calibre com a sua propria textura (a 1.x reaproveitava 3 texturas em todos os calibres). Chaves e telas = a
shell_ladder do spec de arte 2.0 (design/art/spec_art.json):

  nivel s  Tambor 76 mm      he_s ap_s sap_s ac_s   luva de composito lisa + 1 faixa de LED (a HE tem ainda o
                                                    anel escuro do sensor na espoleta)
  nivel m  Trovao 155 mm     he_m ap_m sap_m ac_m   luvas em divisa (Mo.chevron_sleeve) + anel de LED + fendas
                                                    de trilho em V (varridas para o nariz, borda de dentro acesa) no
                                                    ombro da ogiva (a AC fica sem: ali estao os canards)
  nivel l  Mapinguari 406 mm he_l ap_l sap_l ac_l   blindagem segmentada com paineis de chanfro duplo + nariz
                                                    sensor (domo de lente escura) + anel aceso na base
  nivel h  Boiuna (obuseiro) he_h ac_h              o nivel l GORDO, com unidade de base-bleed ambar (sem trevo,
                                                    sem verde)
  PEM      Tuvira / Treme-Treme / Mae-do-Ouro       pem_s pem_m pem_l: capsula escura + bobinas de fio de cobre
                                                    (espiras redondas com brilho, como as do Poraque; assinatura da
                                                    familia PEM) + luz ciano; pem_m com o brilho ciano que pula entre
                                                    as bobinas, pem_l com o nucleo segmentado
  railgun  Tupa                                     slug: dardo APFSDS longo e FINO de tungstenio CLARO (haste de
                                                    ~0.19 quadro), penetrador conico com a ponta quente
                                                    branco-azulada e o colar LARANJA atras dela, 4 colares EM AZUIS
                                                    (3 acesos por quadro) e um feixe compacto de 6 aletas curtas na
                                                    cauda (NUNCA cobre, NUNCA chama de foguete). Cores = a referencia
                                                    do usuario para o Tupa (azul eletrico, branco-azulado, laranja).
                                                    O spec pedia trilhos + armadura clara; a critica r1 mostrou que a
                                                    sela da armadura lia como asa de missil (Jararaca/Mula), entao
                                                    os colares EM fazem o papel das sapatas de trilho

Municao pela COR e pela SILHUETA (a mesma em todos os niveis):
  * HE (Alto-Explosivo, ambar): ogiva curta com espoleta de ponta chata (no nivel l/h a espoleta vira o nariz
    sensor ESCALONADO e estreito: colar, degrau escuro, colar fino e a lente pequena);
  * AP (Perfurante, azul-gelo): ogiva longa com capuz balistico ESCURO (grafite azulado, metade do tom das luvas)
    com o filete claro de aco gelo no contorno (chanfro duplo: a ogiva pontuda le no espaco sob o halo), anel gelo
    na divisa capuz/corpo e a ponta do penetrador de aco exposta;
  * SAP (Semiperfurante, laranja): capuz rombudo largo (mais chato que o da HE e o da AP; no l/h ainda mais largo
    e chato) e colar da espoleta de base atras;
  * AC (Alta Capacidade, carmim + ouro): GUIADA, corpo mais fino, 4 aletas na cauda + 4 canards de OURO maiores
    no nariz (em +: 2 de lado e a dorsal de quina vista de cima), buscador que pisca na ponta dentro de um anel de
    ouro largo, faixa carmim (mascara) entre dois aneis de ouro pintados no difuso.
Cauda e obturador do s/m em grafite escuro (a traseira das luvas claras nao some sob o clarao da base); uma
"espinha" escura por dentro de tudo fecha as frestas entre pecas que so encostam (o alfa do corpo fica 100% opaco).
A faixa da municao e a mascara (T, "mask"), tingida no jogo com palette[municao].band; no difuso ela e cinza claro
neutro (Mo.NOSE_LIGHT). Os LEDs do atlas ja saem na cor da municao (cada municao tem o seu sprite).

Cores para ler no espaco escuro E no casco branco: luvas de composito claro (sRGB ~170) sobre nucleo escuro
(frestas pretas desenham o contorno no casco branco), ogiva grafite media, ponta/penetrador de aco claro.
Emissivos so em recessos escuros, <= 3% do corpo por quadro (STYLE 11.4); forcas <= ~1.3 (a vista Standard
estoura acima de ~1.5, STYLE 9). Sem cobre nas granadas de canhao (cobre = PEM; a cinta de forcamento virou um
obturador de aco escuro com labios claros: so as faixas da municao tem cor).

Telas que diferem da shell_ladder (proporcao da tela = proporcao do corpo no jogo, senao o jogo estica o sprite):
  ac_h  [2.0, 0.89] (spec 0.80): o corpo no jogo 2.2 x 0.983 tem proporcao 2.24; com 0.80 (2.5) esticava 12% em Y;
  pem_s [2.0, 0.80] (spec 0.70): corpo 0.5 x 0.2 (2.5); com 0.70 (2.86) esticava 14%;
  pem_m [2.0, 0.75] (spec 0.70): corpo 0.75 x 0.28 (2.68); com 0.70 esticava 7%.
As outras telas batem com o corpo em ate 3,2% (nivel s 2.857 x corpo 2.77 = 3,2%; ac_s 2.5 x 2.42 = 3,1%).

    $PY tools/blender/render_part.py bs_shells2 --quick --out <rascunho> [--only he_s,slug]
    $PY tools/blender/render_part.py bs_shells2          # final em art3d/bs_shells2/
    python3 tools/check_art3d.py bs_shells2
"""

import math

import bs3d as B
import models as Mo


def _it(L, W, frames, fps, nozzle_x=-0.97, mask=True, anchors=None):
    return {"canvas_tiles": [L, W], "frames": frames, "fps": fps, "wrap": None, "nozzle_x": nozzle_x, "mask": mask,
            "anchors": anchors or {}}


SEEK = {"seeker": [0.9, 0.0]}
PART = {
    "id": "rafaeltessaro.bs_shells2",
    "kind": "shells",
    "px_per_tile": 128,
    "accent": "amber",
    # halo do atlas de luzes (px da tela de 128 px/tile): curto, para o orcamento de 3% (o halo forte conta)
    "halo_px": 2.6,
    "items": {
        "he_s": _it(2.0, 0.70, 2, 4), "ap_s": _it(2.0, 0.70, 2, 4), "sap_s": _it(2.0, 0.70, 2, 4),
        "ac_s": _it(2.0, 0.80, 2, 4, anchors=SEEK),
        "he_m": _it(2.0, 0.70, 2, 4), "ap_m": _it(2.0, 0.70, 2, 4), "sap_m": _it(2.0, 0.70, 2, 4),
        "ac_m": _it(2.0, 0.80, 2, 4, anchors=SEEK),
        "he_l": _it(2.0, 0.70, 4, 6), "ap_l": _it(2.0, 0.70, 4, 6), "sap_l": _it(2.0, 0.70, 4, 6),
        "ac_l": _it(2.0, 0.80, 4, 6, anchors=SEEK),
        "he_h": _it(2.0, 0.78, 4, 6),
        "ac_h": _it(2.0, 0.89, 4, 6, anchors=SEEK),
        "pem_s": _it(2.0, 0.80, 2, 6, mask=False),
        "pem_m": _it(2.0, 0.75, 4, 10, mask=False),
        "pem_l": _it(2.0, 0.70, 4, 12, mask=False),
        "slug": _it(3.0, 0.80, 4, 12, nozzle_x=-1.47, mask=False, anchors={"tip": [1.45, 0.0]}),
    },
}

A0 = math.pi / 8                    # octogono de topo plano
COS8 = math.cos(math.pi / 8)        # apotema / raio (face de cima e meia largura vista de cima)
TOPW = 2 * math.sin(math.pi / 8)    # largura da face de cima / raio
X0, X1 = -0.97, 0.97                # base e ponta das telas de 2.0 (0.03 de folga)

# ---- cores (nomes proprios "s2_*": o cache de materiais do bs3d e por nome)
COMP = (0.34, 0.352, 0.375)         # composito claro das luvas (sRGB ~170: le no espaco e no casco branco)
COMP_D = (0.17, 0.175, 0.185)       # composito medio (ogivas, cauda)
GRAPH = (0.085, 0.09, 0.10)         # grafite (capuz da AP, cauda)
CORE = (0.030, 0.032, 0.037)        # nucleo quase preto
STEEL = (0.50, 0.52, 0.55)          # aco claro (espoleta, labios, penetrador)
TUNG = (0.36, 0.37, 0.39)           # tungstenio claro do slug
GOLD = (0.80, 0.47, 0.07)           # ouro da AC (palette.ac.band2_gold 255,200,80)
PEM_BODY = (0.050, 0.053, 0.060)    # capsula escura da PEM
APCAP = (0.085, 0.095, 0.125)       # capuz da AP (grafite azulado medio)
APEDGE = (0.50, 0.58, 0.70)         # filete de aco gelo no contorno do capuz
ICE = (0.42, 0.60, 0.92)            # anel gelo da AP (palette.ap.band 215,230,255 mais saturado)

# ---- LEDs por municao (emissao; na vista Standard forca 1.0 sai ~ a cor do palette)
LED = {"he": (1.0, 0.45, 0.05), "ap": (0.45, 0.70, 1.0), "sap": (1.0, 0.22, 0.03), "ac": (1.0, 0.025, 0.09),
       "amber": (1.0, 0.40, 0.025), "pem": (0.05, 0.60, 1.0), "violet": (0.24, 0.07, 1.0),
       "rail": (0.04, 0.22, 1.0),
       "hot": (1.0, 0.85, 0.55), "seek": (1.0, 0.10, 0.12)}


def _spec(m, v):
    """Reflexo especular baixo (luz axial: a face de cima nao pode sair mais escura que as facetas)."""
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = v
    return m


def _mats(M):
    lens = _spec(B.mat_metal("s2_lens", (0.010, 0.012, 0.018), rough=0.14, metal=0.0), 0.7)
    return {
        "comp": B.mat_paint("s2_comp", COMP, rough=0.40, metal=0.15, wear=0.0, grime=0.03, scale=5),
        "comp_d": _spec(B.mat_metal("s2_comp_d", COMP_D, rough=0.45, metal=0.3), 0.25),
        "graph": _spec(B.mat_metal("s2_graph", GRAPH, rough=0.45, metal=0.35), 0.25),
        "core": _spec(B.mat_metal("s2_core", CORE, rough=0.62, metal=0.0), 0.05),
        "steel": _spec(B.mat_metal("s2_steel", STEEL, rough=0.36, metal=0.55), 0.3),
        "tung": _spec(B.mat_metal("s2_tung", TUNG, rough=0.38, metal=0.5), 0.25),
        "lens": lens,
        # capuz balistico da AP: grafite azulado MEDIO (sRGB ~90 no topo, metade das luvas ~170: ainda le escuro no
        # casco branco) com o filete de aco gelo no contorno (octo_edge: le no espaco escuro sob o halo da 2.0)
        "apcap": _spec(B.mat_metal("s2_apcap", APCAP, rough=0.40, metal=0.25), 0.3),
        "apedge": _spec(B.mat_metal("s2_apedge", APEDGE, rough=0.30, metal=0.45), 0.4),
        # anel gelo pintado na divisa capuz/corpo da AP (a cor da municao no nariz, nao emissivo)
        "ice": _spec(B.mat_paint("s2_ice", ICE, rough=0.38, metal=0.2, wear=0.0, grime=0.0, scale=5), 0.3),
        "band": Mo.nose_paint("s2_band", Mo.NOSE_LIGHT),
        "gold": _spec(B.mat_metal("s2_gold", GOLD, rough=0.32, metal=0.45), 0.3),
        # cobre das bobinas PEM = o do Poraque (Mo.copper_mat: metal 1.0, rough 0.22) nas espiras redondas
        "copper": Mo.copper_mat(),
        "pem": _spec(B.mat_metal("s2_pem_body", PEM_BODY, rough=0.5, metal=0.2), 0.12),
        # slug do Tupa (referencia do usuario): azul eletrico anodizado dos colares EM, ponta de metal claro azulado
        # (difuso; o brilho vem do atlas) e o colar laranja pintado atras do penetrador
        "railblue": _spec(B.mat_metal("s2_railblue", (0.018, 0.075, 0.40), rough=0.35, metal=0.4), 0.3),
        "tipblue": _spec(B.mat_metal("s2_tipblue", (0.30, 0.37, 0.48), rough=0.32, metal=0.5), 0.3),
        "railorange": _spec(B.mat_paint("s2_railorange", (0.42, 0.125, 0.012), rough=0.36, metal=0.3, wear=0.0,
                                        grime=0.0, scale=6), 0.3),
        "black": M["black"],
    }


# lente escura com um tom da cor (o azul do slug do Tupa e o antigo violeta: o anel EM le na cor ate apagado, sobre o
# tungstenio claro)
LENS_TINT = {"violet": 0.09, "rail": 0.09}


def _lt(LT, s):
    """Tags de um LED com forca s neste quadro: apagado (s = 0) sai SEM a tag "lights" (vira Holdout no atlas =
    transparente, em vez de pixels pretos opacos); no difuso nada muda (a lente escura continua la)."""
    return LT if s > 1e-6 else LT[:1]


def _led(color, s, name=None):
    """LED/brilho: emissao na cor com forca s; no difuso sai como LENTE ESCURA (cor base quase preta, STYLE 11.5).
    s = 0: apagado neste quadro (use _lt(LT, s) nas tags: sai transparente no atlas)."""
    nm = name or f"s2_led_{color}_{int(round(s * 100)):03d}"
    m = B.mat_glow(nm, LED[color], s)
    b = m.node_tree.nodes["Principled BSDF"]
    c = LED[color]
    k = LENS_TINT.get(color, 0.012)
    b.inputs["Base Color"].default_value = (c[0] * k, c[1] * k, c[2] * k, 1)
    b.inputs["Roughness"].default_value = 0.45
    return m


# ============================================================================ geometria basica
def octo(name, prof, mat, tags, zc=0.0):
    """Solido de revolucao octogonal de topo plano no eixo X (perfil [(raio, x)], faces planas)."""
    return Mo.lathe(name, prof, mat, tags, verts=8, axis="X", zc=zc, a0=A0, smooth=False)


def octo_edge(name, prof, mat, edge_mat, tags, t=0.5):
    """octo() com um FILETE de outro material no contorno visto de cima (chanfro duplo claro/escuro: STYLE 1).

    Cada faceta de 45 graus de cima (a que vai do vertice de 67.5 ao de 22.5 graus, e o espelho) e dividida numa
    linha reta, sem quebrar a face plana: a fracao t de fora (junto do contorno, |y| de 0.924 r ate
    0.924 r - t * 0.54 r) e as facetas verticais saem em edge_mat; o topo e o resto em mat. Ex.: o capuz escuro da
    AP com o filete claro no contorno (le no espaco escuro sob o halo) e a haste clara do slug com o filete escuro
    (le no casco cinza claro)."""
    import bmesh
    import bpy
    ang = [A0 + i * math.pi / 4 for i in range(8)]
    V = [(math.cos(a), math.sin(a)) for a in ang]          # (y, z) do octogono de raio 1
    pts, emat = [], []                                      # pontos do anel e material do segmento que COMECA nele
    for i in range(8):
        a, b = V[i], V[(i + 1) % 8]
        pts.append(a)
        if i == 0:              # 22.5 -> 67.5 (faceta de cima, +y): filete de fora = comeco do segmento
            emat += [1]
            pts.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            emat += [0]
        elif i == 2:            # 112.5 -> 157.5 (faceta de cima, -y): filete de fora = fim do segmento
            emat += [0]
            pts.append((b[0] + t * (a[0] - b[0]), b[1] + t * (a[1] - b[1])))
            emat += [1]
        else:                   # topo e fundo: mat; verticais (157.5 -> 202.5 e 337.5 -> 22.5): filete
            emat += [1 if i in (3, 7) else 0]
    n = len(pts)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, x in prof:
        if r < 1e-5:
            rings.append([bm.verts.new((x, 0.0, 0.0))])
        else:
            rings.append([bm.verts.new((x, r * y, r * z)) for y, z in pts])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            if len(rb) == 1:
                f = bm.faces.new((ra[i], ra[j], rb[0]))
            elif len(ra) == 1:
                f = bm.faces.new((ra[0], rb[j], rb[i]))
            else:
                f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
            f.material_index = emat[i]
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(list(rings[-1]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob.data.materials.append(edge_mat)
    for tg in tags:
        ob[tg] = True
    return ob


def smooth(name, prof, mat, tags, verts=24):
    return Mo.lathe(name, prof, mat, tags, verts=verts, axis="X", smooth=True)


def ring(name, xa, xb, r, mat, tags, ch=0.0):
    """Anel octogonal de xa a xb no raio r; ch = chanfro (raio menor nas pontas)."""
    if ch > 0:
        ch = min(ch, (xb - xa) * 0.45)
        return octo(name, [(r - ch, xa), (r, xa + ch), (r, xb - ch), (r - ch, xb)], mat, tags)
    return octo(name, [(r, xa), (r, xb)], mat, tags)


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
    """Ogiva tangente do raio R (em x0) ao raio rf exatamente em x0 + Lv (copia local de bs_shells._ogive_to)."""
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


def led_groove(name, x, w, r, color, s, X, tags, LT, full=False, lw=0.62, lh=0.86):
    """Faixa de LED: anel escuro rebaixado (raio r, entre pecas de raio maior) com a tira acesa na face de cima
    (full=True: anel aceso inteiro, visto de cima atravessa a largura toda). lw/lh: comprimento (fracao de w) e
    largura (fracao da face de cima) da tira."""
    ring(name + "_k", x - w / 2, x + w / 2, r, X["core"], tags)
    if full:
        ring(name + "_l", x - w * 0.32, x + w * 0.32, r * 1.012, _led(color, s), _lt(LT, s))
    else:
        zt = r * COS8
        hw = r * TOPW / 2 * lh
        B.box(name + "_l", x, 0, w * lw, 2 * hw, zt - 0.004, zt + 0.006, _led(color, s), bevel=0.0,
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
    """slot() girado de rot graus no plano XY (fendas em diagonal)."""
    zf = ztop - depth
    for j, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.rbox(f"{name}_c{j}", cx, cy, L, w, zf, ztop + 0.3, X["black"], rot=rot, bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, L, w, zf - 0.008, zf + 0.001, X["black"], rot=rot, bevel=0.0, tags=tags)
    return zf


def top_panel(name, x0, x1, r, mat, tags, th=0.010, inset=0.022):
    """Painel elevado na face de cima de um prisma de 8 lados de raio r (chanfro duplo: a fresta em volta e a
    linha de painel). Pontas da frente chanfradas apontando para o nariz."""
    zt = r * COS8
    hw = r * TOPW / 2 - inset * 0.6
    c = min(hw * 0.6, 0.03)
    poly = [(x0, -hw + c * 0.5), (x0 + c * 0.5, -hw), (x1 - c, -hw), (x1, -hw + c), (x1, hw - c), (x1 - c, hw),
            (x0 + c * 0.5, hw), (x0, hw - c * 0.5)]
    return B.plate(name, poly, zt - 0.003, zt + th, mat, slope=0.006, bevel=0.003, tags=tags)


def side_panels(name, x0, x1, r, mat, tags, th=0.010, inset=0.022):
    """Paineis nas duas facetas de 45 graus (ombros) de um prisma de 8 lados: o painel de cima girado +-45."""
    out = []
    for s in (1, -1):
        p = top_panel(f"{name}{'l' if s > 0 else 'r'}", x0, x1, r, mat, tags, th, inset)
        p.rotation_euler = (math.radians(45 * s), 0.0, 0.0)
        out.append(p)
    return out


def fin(name, poly, z, th, mat, tags):
    """Aleta plana em lasca (chanfro duplo) no plano XY, poligono no lado +y espelhado em -y (as 2 de lado)."""
    out = []
    for s, nm in ((1, "l"), (-1, "r")):
        p = [(x, s * y) for x, y in poly]
        out.append(B.shard(f"{name}_{nm}", p, z - th / 2, z + th / 2, mat, slope=0.008, groove=0.006,
                           panel_h=0.006, tags=tags))
    return out


def dorsal(name, x0, x1, ztop, h, mat, tags, w=0.022, sweep=0.0):
    """Aleta dorsal (a de cima de uma cruz '+'), vista de quina: uma lamina fina ao longo do eixo."""
    poly_b = [(x0, -w / 2), (x1, -w / 2), (x1, w / 2), (x0, w / 2)]
    poly_t = [(x0 - sweep, -w / 2), (x1 - sweep * 0.5, -w / 2), (x1 - sweep * 0.5, w / 2), (x0 - sweep, w / 2)]
    return B.loft(name, poly_b, poly_t, ztop - 0.03, ztop + h, mat, bevel=0.004, tags=tags)


# ============================================================================ granadas de canhao
TIER_R = {"s": 0.335, "m": 0.335, "l": 0.335, "h": 0.40}
AC_R = {"s": 0.275, "m": 0.275, "l": 0.275, "h": 0.355}


def _visor(name, prof, xv, X, tags, LT, col, k, hw=0.042):
    """Visor do sensor (niveis l/h): faixa de LENTE escura rebaixada em volta da ogiva em xv, com o 'scanner' de 3
    LEDs que vai e volta na face de cima (4 quadros: esquerda, meio, direita, meio). prof = trecho de perfil que
    contem [xv - hw, xv + hw]. Devolve (perfil antes, perfil depois) para tornear o resto em volta."""
    a, b = _split(prof, xv - hw)
    vis, c = _split(b, xv + hw)
    octo(name, [(r * 0.972, x) for r, x in vis], X["lens"], tags)
    rv = _r_at(prof, xv) * 0.972
    zv = rv * COS8
    pos = (0, 1, 2, 1)[k % 4]
    for j, y in enumerate((-1, 0, 1)):
        on = 1.15 if j == pos else 0.0
        B.box(f"{name}_p{j}", xv, y * rv * 0.25, 0.042, rv * 0.17, zv - 0.012, zv + 0.003, _led(col, on),
              bevel=0.0, tags=_lt(LT, on))
    return a, c


def _rail_slits(name, obj, prof, xa, xb, X, tags, LT, col, on):
    """2 fendas de trilho na face de cima de um trecho de ogiva (nivel m), varridas para a frente (convergem para
    o nariz, em V como as luvas em divisa): rebaixo escuro de paredes verticais fundo o bastante para passar da
    superficie inclinada e a borda de dentro acesa (fraca no quadro 0, forte no quadro 1: le como trilho, nao
    como um '=' pintado)."""
    ra, rb = _r_at(prof, xa), _r_at(prof, xb)
    zt = ra * COS8
    depth = (ra - rb) * COS8 + 0.04
    y0 = min(0.092, ra * TOPW / 2 - 0.028)        # tras: perto da borda da face de cima
    y1 = min(0.040, rb * TOPW / 2 - 0.035)        # frente: perto do eixo
    _vslits(name, [obj], xa, xb, y0, y1, zt, depth, X, tags, LT, col, on)


def _vslits(name, targets, xa, xb, y0, y1, zt, depth, X, tags, LT, col, on, w=0.036, lw=0.011):
    """Par de fendas em V (y0 atras -> y1 na frente, espelhadas em +-y): rebaixo escuro com a tira acesa (largura
    lw) na borda de dentro."""
    L = math.hypot(xb - xa, y0 - y1)
    for j, s in enumerate((-1, 1)):
        rot = math.degrees(math.atan2(s * (y1 - y0), xb - xa))
        cx, cy = (xa + xb) / 2, s * (y0 + y1) / 2
        zf = rslot(targets, f"{name}{j}", cx, cy, L, w, rot, zt, depth, X, tags)
        # tira acesa na borda de DENTRO do rebaixo (lado do eixo)
        a = math.radians(rot)
        off = (w - lw) / 2 - 0.003
        nx, ny = -math.sin(a) * (-s), math.cos(a) * (-s)     # normal no plano apontando para o eixo
        B.rbox(f"{name}{j}_l", cx + nx * off, cy + ny * off, L - 0.024, lw, zf + 0.001, zf + 0.009,
               _led(col, on), rot=rot, bevel=0.0, tags=_lt(LT, on))


def _ogive2(name, og, X, tags, tier, LT, col, k, frac=0.52, front_mat=None, slits=True, edge_mat=None,
            seam_mat=None, seam_w=0.022):
    """Ogiva em dois tons: tras em composito medio, frente escura (grafite, ou o capuz da AP), com um anel claro de
    aco na divisa (seam_mat/seam_w: o anel gelo mais largo da AP). edge_mat: filete claro no contorno da frente
    (octo_edge). Nivel m: linha de painel + 2 fendas de trilho em V no ombro (borda de dentro acesa: fraca no
    quadro 0, forte no 1); nivel l/h: visor do sensor com o scanner de LEDs. Devolve x da divisa."""
    xa, xe = og[0][1], og[-1][1]
    xs = xa + (xe - xa) * frac
    rear, front = _split(og, xs)
    if edge_mat is not None:
        octo_edge(name + "_f", front, front_mat or X["graph"], edge_mat, tags, t=0.42)
    else:
        octo(name + "_f", front, front_mat or X["graph"], tags)
    if tier in ("l", "h"):
        xv = xa + (xs - xa) * 0.45
        r1, r2 = _visor(name + "_vis", rear, xv, X, tags, LT, col, k)
        octo(name + "_r1", r1, X["comp_d"], tags)
        octo(name + "_r2", r2, X["comp_d"], tags)
    else:
        ro = octo(name + "_r", rear, X["comp_d"], tags)
        if tier == "m":
            xp = xa + (xs - xa) * 0.80
            ring(name + "_pl", xp - 0.008, xp + 0.008, _r_at(og, xp) * 1.012, X["black"], tags)
            if slits:
                _rail_slits(name + "_rs", ro, og, xa + 0.03, xp - 0.025, X, tags, LT, col,
                            1.1 if k == 1 else 0.30)
    h = seam_w / 2
    ring(name + "_seam", xs - h + 0.001, xs + h + 0.001, _r_at(og, xs) * 1.035, seam_mat or X["steel"], tags,
         ch=0.004)
    return xs


def _nose(X, M, T, LT, ammo, tier, R, xo, k, phase):
    """Ogiva + nariz da municao a partir de xo (fim do corpo) ate X1. Devolve (perfil da ogiva, x do inicio)."""
    tags = (T,)
    sensor = tier in ("l", "h")
    if ammo == "he":
        lf = 0.21 if tier != "h" else 0.20
        rf = 0.42 * R
        xf = X1 - lf
        og = _ogive_to(R, xf - xo, rf, xo)
        _ogive2("he_og", og, X, tags, tier, LT, ammo, k, frac=0.50)
        # anel claro de assento da espoleta (le como a borda do nariz no 155/406)
        ring("fz_seat", xf - 0.012, xf + 0.018, rf * 1.10, X["steel"], tags, ch=0.004)
        if not sensor:
            # espoleta de ponta chata: corpo de aco claro, anel escuro rebaixado ("anel do sensor") e ponta
            octo("fz_body", [(rf, xf + 0.018), (rf * 0.94, xf + 0.09), (rf * 0.80, X1 - 0.03), (rf * 0.62, X1)],
                 X["steel"], tags)
            ring("fz_sens", xf + 0.085, xf + 0.125, rf * 0.97, X["black"], tags)
        else:
            # nariz sensor ESCALONADO e estreito (a 1x nao pode ler como o capuz rombudo e largo da SAP do nivel):
            # colar de aco, degrau escuro, colar de aco mais fino e a lente pequena e pontuda na frente
            octo("fz_col", [(rf * 0.86, xf + 0.018), (rf * 0.84, xf + 0.065)], X["steel"], tags)
            ring("fz_step", xf + 0.060, xf + 0.085, rf * 0.70, X["black"], tags)
            octo("fz_col2", [(rf * 0.64, xf + 0.083), (rf * 0.60, xf + 0.125)], X["steel"], tags)
            smooth("fz_lens", _dome(xf + 0.12, X1, rf * 0.52, p=1.6, n=10), X["lens"], tags)
        return og
    if ammo == "ap":
        # ogiva longa: base clara (composito) + capuz balistico escuro + ponta do penetrador de triaco exposta
        og = _ogive_to(R, X1 - 0.07 - xo, 0.20 * R, xo, n=14)
        # capuz ESCURO em todos os niveis (grafite azulado, sRGB ~90: metade das luvas) com o FILETE de aco gelo no
        # contorno de cima e de baixo (chanfro duplo claro: a ogiva longa e pontuda le no espaco escuro sob o halo
        # da 2.0, que clareia o espaco em volta ate ~50; com o capuz de lente, ~52, a AP lia como um cilindro
        # cortado com um ponto solto na frente) e o anel gelo na divisa capuz/corpo
        xc = _ogive2("ap_og", og, X, tags, tier, LT, ammo, k, frac=0.50, front_mat=X["apcap"],
                     edge_mat=X["apedge"], seam_mat=X["ice"], seam_w=0.034)
        rt = og[-1][0]
        # penetrador: espinho de aco claro saindo do capuz (maior que 2 px a 76 mm)
        octo("ap_pen", [(rt * 0.95, X1 - 0.075), (rt * 0.80, X1 - 0.05), (rt * 0.35, X1 - 0.005), (0.0, X1)],
             X["steel"], tags)
        if sensor:
            # anel de sensor no capuz (lente): fresta escura e anel de aco
            xs = xc + 0.10
            ring("ap_sring", xs - 0.010, xs + 0.010, _r_at(og, xs) * 1.03, X["steel"], tags)
        return og
    if ammo == "sap":
        # ogiva media e capuz rombudo LARGO e chato (grafite; no l/h vira domo de lente): no s/m o capuz fica mais
        # largo e mais curto (p 3.2) para a SAP nao ler como a HE a 1x (a cor ambar x laranja e proxima)
        sm = not sensor
        # (l/h: capuz ainda mais largo e chato que o da r2, contra o nariz sensor fino e escalonado da HE)
        xcap = X1 - (0.14 if sm else 0.12)
        og = _ogive_to(R, xcap - xo, (0.66 if sm else 0.64) * R, xo)
        _ogive2("sap_og", og, X, tags, tier, LT, ammo, k, frac=0.55)
        rc = og[-1][0]
        ring("sap_crimp", xcap - 0.016, xcap + 0.012, rc * 1.07, X["steel"], tags, ch=0.004)
        prof = _dome(xcap + 0.01, X1, rc * 1.0, p=3.2, n=10)
        if sensor:
            smooth("sap_cap", prof, X["lens"], tags)
        else:
            octo("sap_cap", prof, X["graph"], tags)
        return og
    raise KeyError(ammo)


def _body_tier(X, M, T, LT, ammo, tier, R, xs0, xs1, k, phase, n_frames, core0=None):
    """Luvas do nivel entre xs0 e xs1 (corpo cilindrico). Devolve a lista de luvas (alvos de recesso).
    core0: inicio do nucleo escuro (padrao xs0 - 0.02); a AC passa o fim do obturador, que fica antes das luvas."""
    tags = (T,)
    col = "ac" if ammo == "ac" else ammo
    rc = R * 0.90
    rg = R * 0.945                       # fundo das faixas de LED: entre o nucleo (0.90 R) e as luvas (R)
    # nucleo escuro de ponta a ponta (aparece nas frestas)
    ring("core", xs0 - 0.02 if core0 is None else core0, xs1 + 0.01, rc, X["core"], tags)
    sleeves = []
    if tier == "s":
        # luva de composito lisa em 2 trechos com a faixa de LED (2 quadros: aceso / fraco) no meio. Critica r2: a
        # 1x (46 px) o 76 mal se distinguia da granada antiga -> valores mais separados: rebaixo do LED mais largo
        # (2.5 px a 1x), tira acesa maior e mais forte, chanfros das pontas das luvas maiores (as frestas escuras
        # das emendas aparecem a 1x)
        xl = xs0 + (xs1 - xs0) * 0.36
        sleeves.append(ring("sl0", xs0, xl - 0.058, R, X["comp"], tags, ch=0.020))
        sleeves.append(ring("sl1", xl + 0.058, xs1, R, X["comp"], tags, ch=0.020))
        led_groove("led", xl, 0.108, rg, col, 1.3 if k == 0 else 0.30, X, tags, LT, lw=0.74, lh=0.94)
        return sleeves
    if tier == "m":
        # anel de LED fino logo atras do obturador (aceso no quadro 0, fraco no 1) e luvas em divisa (escamas
        # apontando para o nariz), a da frente mais longa
        xl = xs0 + 0.035
        led_groove("led", xl, 0.032, rg, col, 1.05 if k == 0 else 0.22, X, tags, LT, full=True)
        a0 = xl + 0.03
        dv = 0.07
        g = 0.03
        span = xs1 - a0
        n = 3 if span > 0.50 else 2
        fl = span * (0.44 if n == 3 else 0.58)          # luva da frente (a mais longa)
        rl = (span - fl - g * (n - 1)) / (n - 1)
        xs_ = [a0 + i * (rl + g) for i in range(n - 1)] + [a0 + (n - 1) * (rl + g)]
        for i in range(n):
            a = xs_[i]
            b = (a + rl) if i < n - 1 else (xs1 - dv)
            sleeves.append(Mo.chevron_sleeve(f"sl{i}", a, b, R, X["comp"], tags, dv=dv, rear=i > 0, verts=8))
        # (HE/AP/SAP levam as fendas de trilho em V no ombro da ogiva, _ogive2. A AC NAO tem fendas: o ombro da
        # ogiva e dos canards e a luva da frente e curta demais, as fendas saiam como cacos soltos; a AC do nivel m
        # le pelas luvas em divisa + anel de LED + o kit guiado)
        return sleeves
    # l / h: blindagem segmentada (aneis com chanfro) com paineis de chanfro duplo no topo e nos ombros
    gap = 0.028
    a0 = xs0
    n = max(3, min(5, int(round((xs1 - a0) / (0.17 if tier == "l" else 0.15)))))
    segL = (xs1 - a0 - gap * (n - 1)) / n
    for i in range(n):
        a = a0 + i * (segL + gap)
        b = a + segL
        sl = ring(f"sl{i}", a, b, R, X["comp"], tags, ch=0.014)
        sleeves.append(sl)
        top_panel(f"pn{i}", a + 0.035, b - 0.03, R, X["comp"], tags)
        side_panels(f"ps{i}", a + 0.035, b - 0.03, R, X["comp"], tags)
    return sleeves


def _base(X, M, T, LT, ammo, tier, R, k, phase):
    """Cauda (boat tail) + obturador; no l anel aceso na base, no h unidade de base-bleed ambar. Devolve x do
    inicio das luvas."""
    tags = (T,)
    col = "ac" if ammo == "ac" else ammo
    if tier in ("s", "m"):
        xt = X0 + 0.15
        # cauda em GRAFITE (escura): a silhueta de tras das luvas claras nao some sob o clarao da base a 1x
        octo("tail", [(R * 0.80, X0), (R * 0.90, X0 + 0.02), (R * 0.97, xt)], X["graph"], tags)
        # obturador de aco escuro com dois labios claros (no lugar da cinta de cobre: cobre = PEM)
        ring("ob_l0", xt - 0.004, xt + 0.025, R * 1.02, X["steel"], tags, ch=0.006)
        ring("ob_k", xt + 0.02, xt + 0.065, R * 0.99, X["graph"], tags)
        ring("ob_l1", xt + 0.06, xt + 0.085, R * 1.02, X["steel"], tags, ch=0.006)
        return xt + 0.10
    if tier == "l":
        xt = X0 + 0.13
        octo("tail", [(R * 0.82, X0), (R * 0.92, X0 + 0.02), (R * 0.97, xt)], X["comp_d"], tags)
        # anel aceso da base (respira 0.6 / 0.85 / 1.0 / 0.85) no rebaixo atras do obturador
        br = (0.62, 0.85, 1.0, 0.85)[k % 4]
        led_groove("bring", xt + 0.03, 0.044, R * 0.90, col, 1.05 * br, X, tags, LT, full=True)
        # (as pecas se sobrepoem 0.002..0.004: encostar exato deixava uma fresta semitransparente no difuso)
        ring("ob_l0", xt + 0.049, xt + 0.08, R * 1.02, X["steel"], tags, ch=0.006)
        ring("ob_k", xt + 0.075, xt + 0.115, R * 0.99, X["graph"], tags)
        ring("ob_l1", xt + 0.11, xt + 0.135, R * 1.02, X["steel"], tags, ch=0.006)
        return xt + 0.15
    # h (Boiuna): unidade de base-bleed GRANDE: cilindro grafite com 2 respiros longos com a brasa ambar acesa no
    # fundo e o anel ambar aceso, depois o obturador (o degrau proprio do obuseiro sobre o nivel l)
    xt = X0 + 0.25
    bb = octo("bbleed", [(R * 0.84, X0), (R * 0.90, X0 + 0.02), (R * 0.90, xt - 0.06), (R * 0.95, xt)],
              X["graph"], tags)
    zt = R * 0.90 * COS8
    br = (0.62, 0.85, 1.0, 0.85)[k % 4]
    for j, y in enumerate((-0.085, 0.085)):
        zf = slot([bb], f"bvent{j}", X0 + 0.10, y, 0.13, 0.062, zt, 0.04, X, tags)
        s = 0.95 * (0.75 + 0.25 * br)
        B.box(f"bvent{j}_l", X0 + 0.10, y, 0.10, 0.024, zf + 0.001, zf + 0.009, _led("amber", s), bevel=0.0,
              tags=_lt(LT, s))
    # anel ambar mais fino que o do nivel l (a brasa dos respiros divide o orcamento de 3%)
    led_groove("bring", xt + 0.02, 0.033, R * 0.90, "amber", 1.05 * br, X, tags, LT, full=True)
    ring("ob_l0", xt + 0.041, xt + 0.07, R * 1.02, X["steel"], tags, ch=0.006)
    ring("ob_k", xt + 0.065, xt + 0.105, R * 0.99, X["graph"], tags)
    ring("ob_l1", xt + 0.10, xt + 0.125, R * 1.02, X["steel"], tags, ch=0.006)
    return xt + 0.14


def _ammo_band(X, T, xa, xb, R, ac=False):
    """Faixa da municao (mascara tingida no jogo). AC: faixa carmim (mascara) entre dois aneis de ouro pintados."""
    tags = (T,)
    if not ac:
        ring("aband", xa, xb, R * 1.02, X["band"], (T, "mask"), ch=0.005)
        return
    g = 0.03
    ring("gold0", xa, xa + g, R * 1.03, X["gold"], tags, ch=0.005)
    ring("aband", xa + g, xb - g, R * 1.02, X["band"], (T, "mask"), ch=0.004)
    ring("gold1", xb - g, xb, R * 1.03, X["gold"], tags, ch=0.005)


def _gun_shell(M, X, T, key, phase, n_frames):
    ammo, tier = key.split("_")
    LT = (T, "lights")
    k = int(round(phase * n_frames)) % n_frames
    if ammo == "ac":
        return _ac(M, X, T, tier, phase, n_frames)
    R = TIER_R[tier]
    xs0 = _base(X, M, T, LT, ammo, tier, R, k, phase)
    body_end = {"he": 0.56, "ap": 0.44, "sap": 0.50}[ammo]
    if tier == "h":
        body_end += 0.02
    xo = X0 + body_end * (X1 - X0)
    # espinha escura de dentro (abaixo de todas as pecas): onde duas pecas so encostam, a fresta mostra o nucleo
    # escuro em vez de deixar o alfa vazar (o sprite continua 100% opaco por dentro)
    ring("spine", X0 + 0.025, xo + 0.03, R * 0.78, X["core"], (T,))
    _nose(X, M, T, LT, ammo, tier, R, xo, k, phase)
    # faixa da municao logo atras da ogiva, depois as luvas do nivel
    xb1 = xo - 0.012
    xb0 = xb1 - (0.11 if tier in ("s", "m") else 0.10)
    _ammo_band(X, T, xb0, xb1, R)
    ring("bandk", xb0 - 0.02, xo + 0.02, R * 0.95, X["core"], (T,))
    _body_tier(X, M, T, LT, ammo, tier, R, xs0, xb0 - 0.022, k, phase, n_frames)
    if ammo == "sap":
        # colar da espoleta de base: anel de aco claro na cauda com o rasgo escuro (a base da SAP sai clara)
        xc0 = X0 + (0.03 if tier != "h" else 0.06)
        ring("sap_bcol", xc0, xc0 + 0.075, R * (0.93 if tier != "h" else 0.95), X["steel"], (T,), ch=0.008)
        ring("sap_bcolk", xc0 + 0.03, xc0 + 0.045, R * (0.94 if tier != "h" else 0.96), X["black"], (T,))


# ============================================================================ AC (Alta Capacidade, guiada)
def _ac(M, X, T, tier, phase, n_frames):
    tags = (T,)
    LT = (T, "lights")
    k = int(round(phase * n_frames)) % n_frames
    R = AC_R[tier]
    half = PART["items"][f"ac_{tier}"]["canvas_tiles"][1] / 2
    span = half - 0.016                      # ponta das aletas (folga de 2 px)
    # cauda + obturador do nivel
    if tier in ("s", "m"):
        xt = X0 + 0.20
        octo("tail", [(R * 0.78, X0), (R * 0.86, X0 + 0.02), (R * 0.97, xt)], X["graph"], tags)
        ring("ob_l0", xt - 0.004, xt + 0.025, R * 1.03, X["steel"], tags, ch=0.006)
        ring("ob_k", xt + 0.02, xt + 0.06, R * 0.99, X["graph"], tags)
        xs0 = xt + 0.07
        core0 = xt + 0.03                    # o nucleo das luvas comeca DENTRO do obturador (sem fresta)
    elif tier == "l":
        xt = X0 + 0.20
        octo("tail", [(R * 0.80, X0), (R * 0.88, X0 + 0.02), (R * 0.97, xt)], X["comp_d"], tags)
        br = (0.62, 0.85, 1.0, 0.85)[k % 4]
        led_groove("bring", xt + 0.025, 0.045, R * 0.90, "ac", 1.0 * br, X, tags, LT, full=True)
        ring("ob_l0", xt + 0.044, xt + 0.072, R * 1.03, X["steel"], tags, ch=0.006)
        xs0 = xt + 0.085
        core0 = xt + 0.06
    else:
        xt = X0 + 0.22
        octo("bbleed", [(R * 0.82, X0), (R * 0.90, X0 + 0.02), (R * 0.90, xt - 0.06), (R * 0.95, xt)],
             X["graph"], tags)
        br = (0.62, 0.85, 1.0, 0.85)[k % 4]
        led_groove("bring", xt + 0.022, 0.045, R * 0.90, "amber", 1.0 * br, X, tags, LT, full=True)
        ring("ob_l0", xt + 0.041, xt + 0.07, R * 1.03, X["steel"], tags, ch=0.006)
        xs0 = xt + 0.08
        core0 = xt + 0.06
    # 4 aletas na cauda em '+': 2 de lado (chanfro duplo) + a dorsal vista de quina
    zt_tail = R * 0.92 * COS8
    fx0, fx1 = X0 + 0.02, X0 + 0.34
    fin("tfin", [(fx1, R * 0.55), (fx0 + 0.10, span), (fx0, span), (fx0 - 0.005, R * 0.55)], 0.0, 0.03,
        X["comp"], tags)
    dorsal("tdors", fx0 + 0.02, fx1 - 0.04, zt_tail, 0.05, X["comp"], tags)
    # ogiva longa e lisa com o buscador na ponta (domo de lente escura + pupila que pisca)
    xo = X0 + 0.60 * (X1 - X0)
    xsk = X1 - 0.075
    # espinha escura de dentro (ver _gun_shell): fecha as frestas entre cauda, obturador e luvas
    ring("spine", X0 + 0.025, xo + 0.03, R * 0.74, X["core"], tags)
    og = _ogive_to(R, xsk - xo, 0.40 * R, xo, n=12)
    if tier in ("l", "h"):
        # visor do sensor com o scanner (frente dos canards), como as outras municoes do nivel
        o1, o2 = _visor("ac_vis", og, xo + 0.40 * (xsk - xo), X, tags, LT, "ac", k, hw=0.036)
        octo("ac_og1", o1, X["comp_d"], tags)
        octo("ac_og2", o2, X["comp_d"], tags)
    else:
        octo("ac_og", og, X["comp_d"], tags)
    rs = og[-1][0]
    # anel de OURO largo no nariz (toque premium que le a 1x) em volta do buscador
    ring("sk_seat", xsk - 0.022, xsk + 0.014, rs * 1.13, X["gold"], tags, ch=0.005)
    smooth("sk_lens", _dome(xsk + 0.008, X1, rs * 0.95, p=1.9, n=10), X["lens"], tags)
    if n_frames == 2:
        on = 1.25 if k == 0 else 0.0
    else:
        on = (1.25, 0.0, 0.55, 0.0)[k % 4]
    zl = rs * 0.95 * COS8
    B.box("sk_pupil", xsk + 0.03, 0.0, 0.034, 0.032, zl - 0.02, zl + 0.004, _led("seek", on), bevel=0.0,
          tags=_lt(LT, on))
    # 4 canards no nariz (2 de lado + dorsal), logo a frente do inicio da ogiva
    cx0 = xo + 0.05
    rcn = _r_at(og, cx0 + 0.08)
    cspan = min(span - 0.02, rcn + 0.125)
    # canards de OURO maiores (toque premium; ~4 px a 1x no 76 mm em vez de 2-3)
    fin("canard", [(cx0 + 0.18, rcn * 0.6), (cx0 + 0.06, cspan), (cx0, cspan), (cx0 - 0.012, rcn * 0.6)], 0.0,
        0.026, X["gold"], tags)
    dorsal("cdors", cx0, cx0 + 0.14, _r_at(og, cx0 + 0.07) * COS8, 0.04, X["gold"], tags, w=0.022)
    # faixas carmim + ouro logo atras da ogiva; luvas do nivel no resto do corpo
    xb1 = xo - 0.012
    xb0 = xb1 - 0.15
    _ammo_band(X, T, xb0, xb1, R, ac=True)
    ring("bandk", xb0 - 0.02, xo + 0.02, R * 0.95, X["core"], tags)
    _body_tier(X, M, T, LT, "ac", tier, R, max(xs0, fx1 - 0.05), xb0 - 0.022, k, phase, n_frames, core0=core0)


# ============================================================================ PEM
def _capsule(X, T, x0, x1, R, nose=0.22, tail=0.12, mat=None):
    """Capsula octogonal: cauda chanfrada, corpo reto e nariz arredondado, com um filete MEDIO no contorno
    (octo_edge, composito medio): as pontas da capsula escura nao somem dentro da propria bainha ciano no espaco
    (critica r2: contraste da tampa ~8-12)."""
    prof = [(R * 0.70, x0), (R * 0.92, x0 + tail * 0.4), (R, x0 + tail)]
    prof += [(R, x1 - nose)] + _dome(x1 - nose, x1, R, p=2.2, n=8)[1:]
    return octo_edge("cap", prof, mat or X["pem"], X["comp_d"], (T,), t=0.32)


def _coil(X, T, name, xc, w, R, turns=3):
    """Bobina de FIO de cobre: 'turns' espiras redondas (perfil de fio, 16 lados lisos, o cobre metalico do
    Poraque: Mo.copper_mat) sobre um carretel escuro. O brilho corre pelo topo de cada espira (le como fio
    enrolado, nao como listra pintada)."""
    tags = (T,)
    ring(name + "_k", xc - w / 2, xc + w / 2, R * 1.012, X["core"], tags)
    pw = w / turns
    for i in range(turns):
        a = xc - w / 2 + i * pw + pw * 0.08
        b = a + pw * 0.84
        h = R * 0.05
        prof = [(R * 1.0, a)] + [(R * 1.0 + h * math.sin(math.pi * t / 6), a + (b - a) * t / 6) for t in range(1, 6)]
        prof += [(R * 1.0, b)]
        smooth(f"{name}_{i}", prof, X["copper"], tags, verts=16)


def _lit_band(X, name, x, w, R, color, s, tags, LT, lip=None, lip_r=1.045):
    """Faixa acesa num rebaixo: anel aceso (raio 1.005 R) entre dois labios escuros mais altos (lip_r * R).
    lip = None: sem labios (o rebaixo ja e formado pelas pecas vizinhas mais altas, ex.: bobinas).
    s = 0: o anel fica na geometria (lente escura no difuso) mas sai transparente no atlas."""
    if lip:
        ring(name + "_a", x - w / 2 - lip, x - w / 2, R * lip_r, X["graph"], tags, ch=0.004)
        ring(name + "_b", x + w / 2, x + w / 2 + lip, R * lip_r, X["graph"], tags, ch=0.004)
    ring(name + "_l", x - w / 2, x + w / 2, R * 1.005, _led(color, s), _lt(LT, s))


def _pem(M, X, T, key, phase, n_frames):
    tags = (T,)
    LT = (T, "lights")
    k = int(round(phase * n_frames)) % n_frames
    half = PART["items"][key]["canvas_tiles"][1] / 2
    R = (half - 0.016) / 1.05               # as espiras REDONDAS (pico 1.05 R) cabem na tela com 2 px de folga
    if key == "pem_s":
        _capsule(X, T, X0, X1, R, nose=0.30, tail=0.16)
        # ponta de aco claro (le no espaco escuro) e anel de base claro
        smooth("nose_t", _dome(X1 - 0.12, X1, R * 0.55, p=2.0, n=8), X["steel"], tags)
        ring("tail_l", X0 + 0.16, X0 + 0.21, R * 1.03, X["steel"], tags, ch=0.006)
        _coil(X, T, "coil0", -0.44, 0.22, R, 2)
        _coil(X, T, "coil1", 0.34, 0.22, R, 2)
        # faixa ciano num rebaixo entre labios escuros, no meio (pisca: acesa / fraca)
        _lit_band(X, "led", -0.05, 0.034, R, "pem", 0.9 if k == 0 else 0.22, tags, LT, lip=0.04)
        return
    if key == "pem_m":
        _capsule(X, T, X0, X1, R, nose=0.28, tail=0.16)
        smooth("nose_t", _dome(X1 - 0.10, X1, R * 0.50, p=2.0, n=8), X["steel"], tags)
        ring("tail_l", X0 + 0.16, X0 + 0.21, R * 1.03, X["steel"], tags, ch=0.006)
        xs = (-0.50, -0.10, 0.30)
        for i, xc in enumerate(xs):
            _coil(X, T, f"coil{i}", xc, 0.18, R, 3)
        # brilho ciano que PULA entre as bobinas: uma faixa acesa larga no meio de cada vao (rebaixo entre labios
        # escuros) e o anel do nariz; a carga corre vao 1 -> vao 2 -> nariz -> repouso (um anel aceso por quadro:
        # o corpo da Treme-Treme e alto e cada anel cheio custa ~2.5% do orcamento). No lugar dos arcos em
        # zigue-zague, que liam como clip-art no zoom e sumiam a 1x
        pat = ((1.05, 0.0, 0.0), (0.0, 1.05, 0.0), (0.0, 0.0, 1.0), (0.45, 0.0, 0.0))[k]
        for i in range(2):
            xg = (xs[i] + xs[i + 1]) / 2
            _lit_band(X, f"gap{i}", xg, 0.026, R, "pem", pat[i], tags, LT, lip=0.026)
        _lit_band(X, "led", 0.57, 0.020, R, "pem", pat[2], tags, LT, lip=0.035)
        return
    # pem_l (Mae-do-Ouro): nucleo segmentado com aneis de cobre e frestas ciano que acendem em onda
    _capsule(X, T, X0, X1, R, nose=0.30, tail=0.14, mat=X["pem"])
    smooth("nose_t", _dome(X1 - 0.13, X1, R * 0.56, p=2.0, n=8), X["lens"], tags)
    ring("nose_r", X1 - 0.155, X1 - 0.12, R * 0.66, X["steel"], tags)
    ring("tail_l", X0 + 0.14, X0 + 0.19, R * 1.03, X["steel"], tags, ch=0.006)
    xs = [-0.66 + i * 0.235 for i in range(6)]
    for i, xc in enumerate(xs):
        _coil(X, T, f"coil{i}", xc, 0.13, R, 2)
    # frestas ciano entre as bobinas (5): a onda sobe da base para o nariz, 1 forte + a de tras media por quadro
    # (frente da onda nas frestas 0, 1, 2, 4: no maximo 2 acesas por quadro, orcamento de 3%)
    lead = (0, 1, 2, 4)[k % 4]
    for i in range(5):
        xg = (xs[i] + xs[i + 1]) / 2
        on = 1.0 if i == lead else (0.30 if i == lead - 1 else 0.0)
        _lit_band(X, f"gap{i}", xg, 0.018, R, "pem", on, tags, LT)


# ============================================================================ slug da railgun (Tupa)
def _hot(name, color, s, base):
    """Emissivo com cor de base CLARA (a ponta quente do slug: no difuso, com a emissao apagada, sai metal claro
    dourado em vez de lente preta; no atlas brilha na cor)."""
    m = B.mat_glow(f"s2_{name}_{int(round(s * 100)):03d}", color, s)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*base, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
    return m


SLUG_HOT = (0.13, 0.43, 1.0)        # azul claro da ponta quente (100, 175, 255) na vista Standard com forca 1
SLUG_WHITE = (0.62, 0.80, 1.0)      # nucleo branco-azulado (205, 228, 255): o ponto quente da ponta


def _slug(M, X, T, phase, n_frames):
    """Dardo APFSDS da railgun: haste fina e longa de tungstenio claro, penetrador conico com a ponta quente
    branco-azulada e um colar laranja atras dela, 4 colares EM azuis (3 acesos por quadro, a onda corre da cauda
    para a ponta) e um feixe compacto de 6 aletas curtas e finas na cauda (a 30/90/150 graus: de cima, 2 de lado
    em planta + 2 em escorco por cima da haste). Sem trilhos laterais, sem armadura em sela, sem cobre, sem chama.
    Cores da referencia do usuario para o Tupa (azul eletrico + branco-azulado + detalhe laranja)."""
    tags = (T,)
    LT = (T, "lights")
    k = int(round(phase * n_frames)) % n_frames
    R = 0.10                                 # haste de ~0.185 quadro entre faces (0.15-0.20 pedido)
    xa, xc, xt = -1.40, 1.10, 1.47           # cauda da haste, inicio do cone do penetrador, ponta
    # haste de tungstenio CLARO (octogono de topo plano, cauda chanfrada) com o filete MEDIO no contorno (critica
    # r2: no casco cinza claro sob a luz violeta a haste ~165 encostava na placa ~186; o filete desenha o dardo) +
    # base escura
    rod = octo_edge("rod", [(R * 0.78, xa), (R, xa + 0.03), (R, xc)], X["tung"], X["comp_d"], tags, t=0.40)
    ring("base", xa - 0.03, xa + 0.012, R * 0.82, X["graph"], tags)
    # penetrador conico: cone de tungstenio, colar escuro fino, ponta quente ouro (atlas) e ponto branco-quente
    xh = xt - 0.115
    rh = R * (xt - xh) / (xt - xc)
    octo("pen", [(R, xc - 0.002), (rh * 1.02, xh + 0.004)], X["tung"], tags)
    ring("pen_c", xh - 0.022, xh + 0.006, rh * 1.18, X["railorange"], tags)
    hot = (1.0, 0.86, 0.95, 0.80)[k % 4]
    # ponta inteira em metal claro azulado no difuso (le clara a 1x mesmo sem o atlas); so a frente brilha:
    # azul claro e, na pontinha, o branco-azulado (o orcamento de 3% vai quase todo para os colares EM)
    xg = xt - 0.095
    rg = rh * (xt - xg) / (xt - xh)
    octo("tipb", [(rh, xh), (rg * 1.01, xg + 0.003)], X["tipblue"], tags)
    octo("tip", [(rg, xg), (0.0, xt)], _hot("tipb", SLUG_HOT, 1.15 * hot, (0.28, 0.34, 0.44)), LT)
    xw = xt - 0.04
    octo("tipw", [(rg * (xt - xw) / (xt - xg) * 1.12, xw), (0.0, xt + 0.002)],
         _hot("tipwb", SLUG_WHITE, 1.3 * hot, (0.40, 0.46, 0.54)), LT)
    # 4 colares EM: 2 labios de metal AZUL anodizado que saltam da haste (o azul le a 1x no difuso, sem
    # depender do halo) com o anel aceso fino no rebaixo entre eles; quadro k: colar k forte, k-1 medio, k-2
    # fraco, k+1 apagado (3 acesos por quadro, a onda corre da cauda para a ponta)
    xs = [-0.80, -0.30, 0.20, 0.70]
    for i, x in enumerate(xs):
        d = (i - k) % 4
        s = (1.25, 0.0, 0.50, 0.85)[d]
        ring(f"em{i}_a", x - 0.007 - 0.028, x - 0.007, R * 1.32, X["railblue"], tags, ch=0.005)
        ring(f"em{i}_b", x + 0.007, x + 0.007 + 0.028, R * 1.32, X["railblue"], tags, ch=0.005)
        ring(f"em{i}_k", x - 0.009, x + 0.009, R * 1.0, X["black"], tags)
        ring(f"em{i}_l", x - 0.007, x + 0.007, R * 1.02, _led("rail", s), _lt(LT, s))
    # feixe de 6 aletas curtas, baixas e finas na cauda (aco claro, bordo de ataque bem varrido: pena de dardo,
    # nao asa de missil)
    r0, rf = R * 0.80, 0.19
    poly = [(xa + 0.38, r0), (xa + 0.10, rf), (xa - 0.04, rf), (xa - 0.04, r0)]
    for j, th in enumerate((30, 90, 150, 210, 270, 330)):
        a_, b_ = B.shard(f"fin{j}", poly, -0.008, 0.008, X["steel"], slope=0.003, groove=0.003, panel_h=0.004,
                         tags=tags)
        for ob in (a_, b_):
            if ob is not None:
                ob.rotation_euler = (math.radians(90 - th), 0.0, 0.0)
    return rod


def model(M, key, T="body", phase=0.0):
    X = _mats(M)
    n = PART["items"][key]["frames"]
    if key.startswith("pem_"):
        _pem(M, X, T, key, phase, n)
    elif key == "slug":
        _slug(M, X, T, phase, n)
    else:
        _gun_shell(M, X, T, key, phase, n)
