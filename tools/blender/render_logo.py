"""Imagem heroi do logo do Bullet Strike: cena cinematografica 3D montada com os modelos das armas do mod.

    <venv-com-bpy>/bin/python tools/blender/render_logo.py [--out ARQ.png] [--quick] [--res N] [--samples N]
                                                           [--raw ARQ.exr] [--comp-only] [--cache ARQ.blend]

Nada e remodelado: a cena importa os modulos de tools/blender/parts/ e chama as funcoes de modelagem como o
render_part.py (roof/head/barrel/cell), so que todas numa cena unica, em perspectiva:
  * Torre Naval Tripla 406 mm (Mapinguari) em primeiro plano, disparando a salva (clarao emissivo nas bocas e
    nas portas do freio, luz do clarao, fumaca volumetrica, freios em brasa);
  * Bateria de Misseis Mula-sem-Cabeca atras, com os narizes carregados nos tubos e um missil saindo do casulo
    (chama, luz e rastro de fumaca);
  * Canhao de Plasma Curupira ao fundo (destaque ciano);
  * conves blindado escuro da nave (placas chanfradas por tile, escotilhas e luzes em recessos, borda do casco)
    e espaco profundo (estrelas e nebulosa) composto depois do render.

Etapas: (1) geometria das armas, cada uma montada na origem dentro de Empties (lenta: muitas booleanas);
(2) disposicao (posicao/giro/elevacao), conves, efeitos, luzes e camera; (3) render em EXR linear
(pre-multiplicado); (4) composicao em numpy (fundo, bloom, curva de tom, vinheta) -> PNG RGB quadrado.
Padrao: 1024 px e 128 amostras, saida em tools/blender/logo_hero.png (~5 min de modelagem + render na CPU);
--quick = 384 px e 16 amostras (rascunho). --raw guarda o EXR (e o passe de profundidade <raw>_depth.exr);
sem --raw eles vao para um arquivo temporario apagado no fim.
--cache guarda a etapa 1 num .blend (so para iterar camera/luz/efeitos; a chave inclui o codigo dos modelos).
--comp-only refaz so a etapa 4 a partir do EXR de --raw.
O titulo e o subtitulo NAO ficam aqui: tools/make_art.py logo() reduz esta imagem para 512 e escreve o texto.
"""

import hashlib
import importlib
import json
import math
import os
import random
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (o bpy tem que vir antes do bmesh)
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image  # noqa: E402

import bs3d as B  # noqa: E402
import models as Mo  # noqa: E402

# ============================================================================ parametros da cena
# armas: "at" = canto (x0, y0) da peca na grade do conves (tiles inteiros); yaw = giro da torre (graus,
# anti-horario; 0 = cano para +Y); elev = elevacao dos canos (graus); recoil = recuo dos canos (tiles)
WEAPONS = [
    {"mod": "bs_naval_406", "at": (-3, -3), "yaw": -76.0, "elev": 14.0, "recoil": 0.15, "fire": True},
    # msl_s: ponto do caminho do missil (tiles desde o tubo) em que ele aparece
    {"mod": "bs_msl_quad", "alt": "bs_msl_twin", "at": (-3, 7), "yaw": 150.0, "missile": True, "msl_s": 2.2},
    {"mod": "bs_plasma_heavy", "at": (3, 8), "yaw": -45.0, "elev": 18.0, "charge": True},
]
DECK_X = (-24, 26)          # extensao do conves (tiles): passa das bordas laterais do quadro; so a borda do
DECK_Y = (-18, 14)          # fundo aparece, logo atras das armas do fundo, como horizonte contra o espaco
# camera em coordenadas esfericas em volta do alvo: azimute (graus, 0 = +X), altura (graus acima do conves),
# distancia e lente. Quase alinhada com a grade do conves (a borda do fundo fica um horizonte baixo) e 3/4 por
# tras-direita do 406: os tres canos sobem para a direita, separados, e o corpo fica grande a esquerda.
CAM_AIM = (1.6, 0.4, 0.6)
CAM_AZ = -108.0
CAM_EL = 30.0
CAM_DIST = 11.0
CAM_LENS = 35.0
CAM_FSTOP = 1.0             # profundidade de campo leve (cena em metros: f/1 so desfoca de leve o conves da frente)
FLASH = 0.72                # escala do clarao da salva (bola de fogo, jatos, fagulhas)
VIG_C = (0.40, 0.48)        # centro da vinheta (fracao da imagem): em cima do corpo do 406
HEAD_LIFT = 0.10            # a cabeca fica um pouco acima do teto (como no render 3/4 do 76 mm)
PAINT = (0.020, 0.025, 0.036)   # pintura escura do casco (troca o verde do teto)
STATIC_VERSION = 3          # mude ao alterar a etapa 1 (invalida o --cache)

OUT = os.path.join(HERE, "logo_hero.png")
QUICK_OUT = os.path.join(tempfile.gettempdir(), "logo_hero_quick.png")   # rascunho do --quick sem --out


def cam_loc():
    az, el = math.radians(CAM_AZ), math.radians(CAM_EL)
    return (CAM_AIM[0] + CAM_DIST * math.cos(el) * math.cos(az),
            CAM_AIM[1] + CAM_DIST * math.cos(el) * math.sin(az),
            CAM_AIM[2] + CAM_DIST * math.sin(el))


def _log(msg, t0=[time.time()]):
    print(f"[logo {time.time() - t0[0]:6.1f}s] {msg}", flush=True)


# ============================================================================ utilidades
def _cena():
    return set(o.name for o in bpy.context.scene.objects)


def _empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
    e.location = loc
    e.rotation_euler = tuple(math.radians(a) for a in rot)
    return e


def _construir(fn, parent):
    """Roda uma funcao de modelagem e prende os objetos novos (raizes) no Empty 'parent'."""
    antes = _cena()
    fn()
    novos = [o for o in bpy.context.scene.objects if o.name not in antes]
    for o in novos:
        if o.parent is None and o is not parent:
            o.parent = parent
    return novos


_ACCENT = [None]


def _mats(accent):
    """Materiais do kit; trocar o acento exige materiais novos (o cache do bs3d e por nome)."""
    if _ACCENT[0] is not None and _ACCENT[0] != accent:
        B._MATS.clear()
    _ACCENT[0] = accent
    return Mo.mats(accent)


def _mesh_obj(name, bm, mat, tags=("fx",), smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in (mat if isinstance(mat, (list, tuple)) else [mat]):
        ob.data.materials.append(m)
    for t in tags:
        ob[t] = True
    return ob


def _lathe(bm, prof, axis_m, verts=16):
    """Solido de revolucao no eixo +Y (perfil [(raio, y)], raio 0 = ponta) transformado por axis_m."""
    rings = []
    for r, y in prof:
        if r < 1e-5:
            rings.append([bm.verts.new(axis_m @ Vector((0.0, y, 0.0)))])
        else:
            rings.append([bm.verts.new(axis_m @ Vector((r * math.cos(a), y, r * math.sin(a))))
                          for a in (i / verts * math.tau for i in range(verts))])
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1:
            for i in range(verts):
                bm.faces.new((ra[0], rb[(i + 1) % verts], rb[i]))
        elif len(rb) == 1:
            for i in range(verts):
                bm.faces.new((ra[i], ra[(i + 1) % verts], rb[0]))
        else:
            for i in range(verts):
                j = (i + 1) % verts
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))


def _mod(name, alt=None):
    try:
        return importlib.import_module(f"parts.{name}")
    except Exception as e:  # o modulo pode estar sendo editado por outro agente
        if not alt:
            raise
        print(f"AVISO: parts.{name} falhou ({e}); usando parts.{alt}")
        return importlib.import_module(f"parts.{alt}")


# ============================================================================ etapa 1: geometria das armas
def build_weapon(spec):
    """Teto + cabeca + canos (+ narizes e missil nos lancadores), tudo na origem, em Empties com nome fixo:
    part_<k> (centro da peca) > head_<k> (pivo; recebe o giro) > bpiv_<k><i> (raiz; recebe elevacao/recuo)."""
    mod = _mod(spec["mod"], spec.get("alt"))
    key = spec["mod"]
    P = mod.PART
    M = _mats(P.get("accent", "amber"))
    W, H = P["size"]
    pv = P["pivot"]
    part = _empty(f"part_{key}")
    part["bs_mod"] = mod.__name__
    ring = P.get("ring_r", P["turret_box"] * 0.45)
    if getattr(mod, "roof", None):
        _construir(lambda: mod.roof(M, "roof"), part)
    else:
        _construir(lambda: Mo.hull_roof(M, W, H, pv, ring, "roof"), part)
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    head = _empty(f"head_{key}", (px, py, HEAD_LIFT), parent=part)
    _construir(lambda: mod.head(M, "head", 0.0), head)
    bar = P.get("barrels")
    if bar:
        bz = getattr(mod, "BZ", 0.6)
        L = bar["length"]
        for i, ys in enumerate(bar["ys"]):
            piv = _empty(f"bpiv_{key}{i}", (ys, bar["root"], bz), parent=head)
            off = _empty(f"boff_{key}{i}", (0, 0, -bz), parent=piv)
            for o in _construir(lambda: mod.barrel(M, L, "barrel", 0.0), off):
                if o.get("hot"):
                    o["fx_hot"] = key
            # ancora do clarao: boca do cano (referencial do cano: +Y para a frente)
            _empty(f"fxa_muzzle_{key}{i}", (0, L - 0.04, bz), parent=off)
    if P.get("kind") == "launcher" and spec.get("missile"):
        launcher_load(mod, M, head, key)


def launcher_load(mod, M, head, key):
    """Narizes carregados nos tubos (cell() do modelo, copiados) menos os que ja dispararam + missil em voo."""
    pods = getattr(mod, "POD_XS", None)
    if pods is None:
        px = getattr(mod, "POD_X", 0.85)
        pods = (-px, px)
    pitch = getattr(mod, "PITCH", 40.0)
    rx = math.radians(pitch - 90.0)
    tubes = getattr(mod, "TUBES", [(0.0, 0.0)])
    pod_y = getattr(mod, "POD_Y", 0.9)
    z0 = getattr(mod, "Z0", 1.0)
    fired = {(1, 1), (1, 4), (2, 0), (2, 7), (0, 10)}      # tubos vazios (ja dispararam)
    launch = (1, 1)                                         # tubo de onde sai o missil da cena

    def mouth(cx, u, v):
        return Vector((cx + u, pod_y + v * math.cos(rx), z0 + v * math.sin(rx)))

    if hasattr(mod, "cell"):
        proto = None
        for i, cx in enumerate(pods):
            for k, (u, v) in enumerate(tubes):
                if (i, k) in fired:
                    continue
                at = _empty(f"nose_at{i}_{k}", tuple(mouth(cx, u, v)), parent=head)
                if proto is None:
                    proto = _construir(lambda: mod.cell(M, "he", "head", form="tube"), at)
                    continue
                # copia rapida do primeiro nariz (malhas compartilhadas)
                twin = {}
                for o in proto:
                    c = o.copy()
                    bpy.context.scene.collection.objects.link(c)
                    twin[o.name] = c
                for o in proto:
                    c = twin[o.name]
                    c.parent = twin[o.parent.name] if o.parent and o.parent.name in twin else at
    i, k = launch
    u, v = tubes[k % len(tubes)]
    m0 = mouth(pods[min(i, len(pods) - 1)], u, v)
    axis = Vector((0, -math.sin(rx), math.cos(rx)))
    missile(M, head, m0, axis, key)


def missile(M, head, m0, axis, key):
    """Missil em voo (objeto de cena, nao e arma): corpo escuro, ogiva clara, anel ambar e aletas.
    A chama, a luz e o rastro entram na etapa 2 (ancora fxa_msl_<k> e pontos do rastro em head['fx_trail'])."""
    def path(s):
        return m0 + axis * s + Vector((0, 0, 0.05 * s * s))

    s_tail = 3.6
    tail = path(s_tail)
    d = (path(s_tail + 0.1) - tail).normalized()
    emp = _empty(f"fxa_msl_{key}", tuple(tail), parent=head)
    emp.rotation_mode = "QUATERNION"
    emp.rotation_quaternion = d.to_track_quat("Y", "Z")
    R = 0.078
    bm = bmesh.new()
    _lathe(bm, [(0.0, -0.02), (0.05, -0.02), (0.062, 0.05), (R, 0.08), (R, 0.86), (0.0, 0.86)], Matrix.Identity(4), 16)
    _mesh_obj("msl_body", bm, M["core_mid"], tags=("fx",), smooth=True).parent = emp
    bm = bmesh.new()
    rho = (R * R + 0.3 * 0.3) / (2 * R)
    nose = [(R, 0.86)]
    for kk in range(1, 11):
        x = 0.3 * kk / 10
        nose.append((max(math.sqrt(max(0.0, rho * rho - x * x)) + R - rho, 0.0), 0.86 + x))
    nose[-1] = (0.0, 1.16)
    _lathe(bm, nose, Matrix.Identity(4), 16)
    _mesh_obj("msl_nose", bm, M["armor"], tags=("fx",), smooth=True).parent = emp
    B.cyl("msl_band", 0, 0.80, 0, R + 0.004, 0.04, M["glow"], axis="Y", verts=16, bevel=0.0, tags=("fx",)).parent = emp
    for kk in range(4):
        # aleta: trapezio fino no plano que contem o eixo (casco convexo dos 8 vertices)
        a = math.radians(45 + 90 * kk)
        ca, sa = math.cos(a), math.sin(a)
        bm = bmesh.new()
        for side in (-0.007, 0.007):
            for r, y in ((R - 0.01, 0.02), (R + 0.11, 0.05), (R + 0.11, 0.15), (R - 0.01, 0.32)):
                bm.verts.new((r * ca - side * sa, y, r * sa + side * ca))
        bmesh.ops.convex_hull(bm, input=list(bm.verts))
        _mesh_obj(f"msl_fin{kk}", bm, M["armor_mid"], tags=("fx",)).parent = emp
    # rastro: pontos do caminho (finos perto do missil, largos perto do casulo), em coordenadas da cabeca
    n = 18
    trail = []
    for j in range(n):
        t = j / (n - 1)
        s = s_tail - 0.3 - (s_tail - 0.15) * t
        p = path(s)
        trail.append([p.x, p.y, p.z, 0.10 + 0.34 * t ** 0.9])
    head["fx_trail"] = json.dumps(trail)


def build_static():
    B.reset()
    for spec in WEAPONS:
        _log(f"modelando {spec['mod']}")
        build_weapon(spec)
    _log("modelagem pronta")


def _static_key():
    h = hashlib.sha1(str(STATIC_VERSION).encode())
    for spec in WEAPONS:
        h.update(repr((spec["mod"], spec.get("alt"), spec.get("missile"))).encode())
        for nm in (spec["mod"], spec.get("alt")):
            if nm:
                p = os.path.join(HERE, "parts", nm + ".py")
                if os.path.exists(p):
                    h.update(open(p, "rb").read())
    for nm in ("bs3d.py", "models.py"):
        h.update(open(os.path.join(HERE, nm), "rb").read())
    return h.hexdigest()


def load_or_build(cache):
    key = _static_key()
    if cache and os.path.exists(cache):
        bpy.ops.wm.open_mainfile(filepath=cache)
        if bpy.context.scene.get("bs_logo_key") == key:
            _log(f"geometria do cache {cache}")
            return
        _log("cache desatualizado: modelando de novo")
    build_static()
    if cache:
        bpy.context.scene["bs_logo_key"] = key
        bpy.ops.wm.save_as_mainfile(filepath=cache, copy=True)


# ============================================================================ etapa 2: disposicao, conves, efeitos
def layout():
    """Posiciona as pecas na grade do conves, gira as torres e eleva/recua os canos."""
    sc = bpy.context.scene
    rects = []
    pivots, muzzles = [], []
    for spec in WEAPONS:
        key = spec["mod"]
        part = sc.objects[f"part_{key}"]
        mod = importlib.import_module(part["bs_mod"])
        P = mod.PART
        W, H = P["size"]
        ax, ay = spec["at"]
        part.location = (ax + W / 2, ay + H / 2, 0.0)
        yaw = math.radians(spec.get("yaw", 0.0))
        sc.objects[f"head_{key}"].rotation_euler = (0, 0, yaw)
        pvx, pvy = ax + P["pivot"][0], ay + H - P["pivot"][1]     # pivo no conves (y da peca e para baixo)
        pivots.append((key, pvx, pvy, P["turret_box"] / 2))
        bar = P.get("barrels")
        if bar:
            el = math.radians(spec.get("elev", 0.0))
            for i, ys in enumerate(bar["ys"]):
                piv = sc.objects[f"bpiv_{key}{i}"]
                piv.location.y = bar["root"] - spec.get("recoil", 0.0)
                piv.rotation_euler = (el, 0, 0)
                # boca do cano no conves: pivo + R(yaw) . (ys, raiz + comprimento)
                fy = bar["root"] - spec.get("recoil", 0.0) + bar["length"] * math.cos(el)
                muzzles.append((key, pvx + ys * math.cos(yaw) - fy * math.sin(yaw),
                                pvy + ys * math.sin(yaw) + fy * math.cos(yaw)))
        rects.append((ax, ay, ax + W, ay + H))
    # nenhuma boca pode cair dentro (ou a menos de 0.5 tile) do quadrado de giro de outra arma
    for key, mx, my in muzzles:
        for other, px, py, r in pivots:
            if other != key:
                d = math.hypot(mx - px, my - py)
                assert d > r + 0.5, f"boca de {key} a {d:.2f} tiles do pivo de {other} (minimo {r + 0.5:.2f})"
    return rects


def mat_deck(name, color, rough=0.4, seed=0.0, spec=0.25, metal=0.3):
    """Placa do conves: metal pintado escuro e fosco (rugosidade com ruido, especular baixo: a luz do clarao
    vira uma mancha suave e nao um campo de teclas brilhantes), com manchas leves (sem desgaste por
    Pointiness, que deixaria as placas sem bisel inteiras claras)."""
    m = _new_mat(name)
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links.new
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.9
    noise.inputs["Detail"].default_value = 8
    noise.noise_dimensions = "4D"
    for sk in noise.inputs:
        if sk.name == "W":
            sk.default_value = seed
    Lk(tc.outputs["Object"], noise.inputs["Vector"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs[3].default_value = rough - 0.12
    rr.inputs[4].default_value = rough + 0.14
    Lk(noise.outputs["Fac"], rr.inputs[0])
    Lk(rr.outputs[0], b.inputs["Roughness"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*color, 1)
    mix.inputs[7].default_value = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6, 1)
    Lk(noise.outputs["Fac"], mix.inputs[0])
    Lk(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    return m


def _placas(x0, x1, y0, y1, ocupado, rnd):
    """Divide a grade em placas de casco (3x2, 2x2, 2x1 ... tiles), gananciosa em ordem fixa, sem invadir as
    pecas. Devolve [(tx, ty, largura, altura)]."""
    livre = {(tx, ty) for tx in range(x0, x1) for ty in range(y0, y1) if not ocupado(tx, ty)}
    formas = [((3, 2), 0.30), ((2, 2), 0.28), ((2, 3), 0.12), ((3, 1), 0.08), ((2, 1), 0.10), ((1, 2), 0.08),
              ((1, 1), 0.04)]
    out = []
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            if (tx, ty) not in livre:
                continue
            resto = list(formas)
            ordem = []
            while resto:
                r = rnd.random() * sum(p for _, p in resto)
                for k, (f, p) in enumerate(resto):
                    r -= p
                    if r <= 0:
                        ordem.append(f)
                        resto.pop(k)
                        break
                else:
                    ordem.append(resto.pop()[0])
            for bw, bh in ordem + [(1, 1)]:
                cells = [(tx + i, ty + j) for i in range(bw) for j in range(bh)]
                if all(c in livre for c in cells):
                    livre.difference_update(cells)
                    out.append((tx, ty, bw, bh))
                    break
    return out


def deck(skip):
    """Conves: placas de casco grandes (2x2, 3x2 ...) chanfradas com painel interno (malha unica), laje escura
    por baixo, detalhes esparsos nas placas (respiros com venezianas, escotilhas, fendas escuras com luz ambar
    em recesso) e a amurada do casco ao fundo com luzes de posicao."""
    M = _mats("amber")
    paint = mat_deck("deck_paint", PAINT, rough=0.66)
    paint2 = mat_deck("deck_paint2", tuple(c * 0.75 for c in PAINT), rough=0.72, seed=3.0)
    x0, x1 = DECK_X
    y0, y1 = DECK_Y
    tags = ("deck",)
    B.box("deck_slab", (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, -0.12, 0.0, M["core"], bevel=0.0, tags=tags)
    rnd = random.Random(11)

    def prism(bm, poly, z0, z1, slope, mi):
        top = B._ccw(B.offset_poly(poly, slope)) if slope else B._ccw(poly)
        poly = B._ccw(poly)
        vb = [bm.verts.new((x, y, z0)) for x, y in poly]
        vt = [bm.verts.new((x, y, z1)) for x, y in top]
        f = bm.faces.new(vt)
        f.material_index = mi
        n = len(poly)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
            f.material_index = mi

    def ocupado(tx, ty, m=0):
        return any(a - m <= tx < c + m and b - m <= ty < d + m for a, b, c, d in skip)

    g = 0.04
    bm = bmesh.new()
    det = bmesh.new()     # detalhes: 0 preto, 1 nucleo, 2 luz fraca, 3 blindagem media, 4 aco
    ZP = 0.082            # topo do painel interno
    for tx, ty, bw, bh in _placas(x0, x1, y0, y1, ocupado, rnd):
        cx, cy = tx + bw / 2, ty + bh / 2
        mi = 1 if rnd.random() < 0.22 else 0
        poly = B.rpoly(cx, cy, bw - 2 * g, bh - 2 * g, 0, chamfer=0.12)
        prism(bm, poly, 0.0, 0.06, 0.025, mi)
        prism(bm, B.offset_poly(poly, 0.16), 0.056, ZP, 0.014, mi)
        if bw * bh < 2 or ocupado(tx, ty, 1) or ocupado(tx + bw - 1, ty + bh - 1, 1):
            continue
        r = rnd.random()
        lx, ly = (bw - 0.5, 0.0) if bw >= bh else (0.0, bh - 0.5)   # eixo comprido da placa
        if r < 0.16:
            # fenda escura com filete de luz ambar em recesso, perto de uma das bordas compridas
            s = rnd.choice((-1, 1))
            if bw >= bh:
                ex, ey, sx, sy = cx, cy + s * (bh / 2 - 0.36), min(1.4, lx), 0.10
            else:
                ex, ey, sx, sy = cx + s * (bw / 2 - 0.36), cy, 0.10, min(1.4, ly)
            prism(det, B.rpoly(ex, ey, sx + 0.08, sy + 0.08, 0), ZP - 0.004, ZP + 0.012, 0.0, 0)
            prism(det, B.rpoly(ex, ey, sx * 0.55, sy * 0.4, 0), ZP - 0.004, ZP + 0.006, 0.0, 2)
        elif r < 0.26:
            # respiro: fundo preto com venezianas e um pip ambar
            prism(det, B.rpoly(cx, cy, 0.9, 0.5, 0), ZP - 0.004, ZP + 0.03, 0.0, 0)
            for i in range(5):
                prism(det, B.rpoly(cx, cy - 0.17 + i * 0.085, 0.8, 0.04, 0), ZP, ZP + 0.04, 0.0, 1)
            prism(det, B.rpoly(cx + 0.33, cy + 0.33, 0.14, 0.04, 0), ZP - 0.004, ZP + 0.02, 0.0, 2)
        elif r < 0.33:
            # escotilha chanfrada com puxador
            prism(det, B.rpoly(cx, cy, 0.78, 0.78, 0, chamfer=0.16), ZP - 0.004, ZP + 0.03, 0.02, 3)
            prism(det, B.rpoly(cx, cy - 0.2, 0.3, 0.06, 0), ZP + 0.03, ZP + 0.05, 0.0, 4)
    _mesh_obj("deck_plates", bm, [paint, paint2], tags=tags)
    _mesh_obj("deck_details", det, [M["black"], M["core_mid"], M["glow_dim"], M["armor_mid"], M["steel"]], tags=tags)
    # amurada do casco no fim do conves, com luzes de posicao em recesso
    for side, (cx, cy, sx, sy) in {"far": ((x0 + x1) / 2, y1 + 0.35, x1 - x0 + 1.4, 0.7),
                                   "left": (x0 - 0.35, (y0 + y1) / 2, 0.7, y1 - y0),
                                   "right": (x1 + 0.35, (y0 + y1) / 2, 0.7, y1 - y0)}.items():
        B.box(f"rim_{side}", cx, cy, sx, sy, -0.6, 0.22, M["armor_mid"], bevel=0.04, slope=0.12, tags=tags)
    for i in range(x0 + 1, x1, 3):
        B.box(f"rimled{i}", i, y1 + 0.12, 0.30, 0.05, 0.16, 0.235, M["glow"], bevel=0.0, tags=tags)
    for j in range(y0 + 1, y1, 3):
        B.box(f"rimledr{j}", x1 + 0.12, j, 0.05, 0.30, 0.16, 0.235, M["glow"], bevel=0.0, tags=tags)
    # teto verde das pecas -> mesma pintura do conves
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            for i, m in enumerate(o.data.materials):
                if m and m.name.startswith("roof_green"):
                    o.data.materials[i] = paint


# ---------------------------------------------------------------------------- materiais de efeito
def _new_mat(name):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:     # Blender < 5 (no 5.x o material ja nasce com nos; use_nodes esta obsoleto)
        m.use_nodes = True
    return m


def _nt(name):
    m = _new_mat(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def _math(nt, op, a=None, b=None, va=None, vb=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    if a is not None:
        nt.links.new(a, n.inputs[0])
    elif va is not None:
        n.inputs[0].default_value = va
    if b is not None:
        nt.links.new(b, n.inputs[1])
    elif vb is not None:
        n.inputs[1].default_value = vb
    return n.outputs[0]


def mat_flame(name, hot=(1.0, 0.82, 0.48), mid=(1.0, 0.36, 0.05), strength=20.0, power=1.6):
    """Chama aditiva (transparente + emissao): branco-amarelo na raiz, laranja no meio, some na ponta e nas bordas.
    A malha cresce em +Y local de 0 ate o comprimento (coordenada Generated y = 0..1)."""
    m, nt, out = _nt(name)
    N, Lk = nt.nodes, nt.links.new
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hot, 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (*mid, 1)
    Lk(sep.outputs[1], ramp.inputs[0])
    along = _math(nt, "POWER", _math(nt, "SUBTRACT", None, sep.outputs[1], va=1.0), None, vb=power)
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = 0.5
    edge = _math(nt, "POWER", _math(nt, "SUBTRACT", None, lw.outputs["Facing"], va=1.0), None, vb=1.4)
    inten = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", along, edge), None, vb=strength)
    em = N.new("ShaderNodeEmission")
    Lk(ramp.outputs[0], em.inputs["Color"])
    Lk(inten, em.inputs["Strength"])
    add = N.new("ShaderNodeAddShader")
    Lk(N.new("ShaderNodeBsdfTransparent").outputs[0], add.inputs[0])
    Lk(em.outputs[0], add.inputs[1])
    Lk(add.outputs[0], out.inputs["Surface"])
    return m


def mat_spark(name, color=(1.0, 0.55, 0.15), strength=30.0):
    m, nt, out = _nt(name)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def mat_smoke(name, color=(0.05, 0.048, 0.046), density=6.0, scale=2.2, seed=0.0, emit=None):
    """Fumaca volumetrica numa esfera unitaria (coordenadas do objeto): ruido * queda radial."""
    m, nt, out = _nt(name)
    N, Lk = nt.nodes, nt.links.new
    tc = N.new("ShaderNodeTexCoord")
    ln = N.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    Lk(tc.outputs["Object"], ln.inputs[0])
    fall = N.new("ShaderNodeMapRange")
    fall.interpolation_type = "SMOOTHSTEP"
    fall.inputs[1].default_value = 1.0
    fall.inputs[2].default_value = 0.3
    Lk(ln.outputs["Value"], fall.inputs[0])
    off = N.new("ShaderNodeVectorMath")
    off.operation = "ADD"
    off.inputs[1].default_value = (seed, seed * 1.7, seed * 0.6)
    Lk(tc.outputs["Object"], off.inputs[0])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.6
    Lk(off.outputs[0], noise.inputs["Vector"])
    nmr = N.new("ShaderNodeMapRange")
    nmr.inputs[1].default_value = 0.40
    nmr.inputs[2].default_value = 0.70
    Lk(noise.outputs["Fac"], nmr.inputs[0])
    mul = _math(nt, "MULTIPLY", fall.outputs[0], nmr.outputs[0])
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Anisotropy"].default_value = 0.3
    Lk(_math(nt, "MULTIPLY", mul, None, vb=density), vol.inputs["Density"])
    if emit:
        vol.inputs["Emission Color"].default_value = (*emit[0], 1)
        Lk(_math(nt, "MULTIPLY", mul, None, vb=emit[1]), vol.inputs["Emission Strength"])
    Lk(vol.outputs[0], out.inputs["Volume"])
    return m


def mat_heat(base, strength=1.2, color=(1.0, 0.13, 0.015)):
    """Copia o material da blindagem e soma brasa (freio quente depois do tiro)."""
    m = base.copy()
    m.name = base.name + "_quente"
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


# ---------------------------------------------------------------------------- geometria de efeito
def flame(name, length, radius, mat, spikes=6, seed=1, cone=26.0, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Clarao: fuso principal ao longo de +Y + jatos finos abertos em leque."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    prof = [(0.0, 0.0)]
    for k in range(1, 15):
        t = k / 14
        r = radius * (min(1.0, t / 0.22) ** 0.6) * (1 - max(0.0, (t - 0.22) / 0.78)) ** 1.25
        prof.append((max(r, 0.0), t * length))
    prof[-1] = (0.0, length)
    _lathe(bm, prof, Matrix.Identity(4), 14)
    for _ in range(spikes):
        a = rnd.uniform(0, math.tau)
        tilt = math.radians(rnd.uniform(cone * 0.35, cone))
        L = length * rnd.uniform(0.45, 0.8)
        rr = radius * rnd.uniform(0.18, 0.32)
        m = Matrix.Rotation(a, 4, "Y") @ Matrix.Rotation(tilt, 4, "X")
        _lathe(bm, [(0.0, 0.0), (rr * 0.7, L * 0.08), (rr, L * 0.3), (rr * 0.45, L * 0.7), (0.0, L)],
               Matrix.Translation((0, length * 0.05, 0)) @ m, 8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _mesh_obj(name, bm, mat, smooth=True)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = tuple(math.radians(a) for a in rot)
    return ob


def fireball(name, length, radius, mat, parent=None, loc=(0, 0, 0), seed=0):
    """Bola de fogo do disparo: elipsoide irregular ao longo de +Y (a cor vem do mesmo degrade da chama)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    prof = [(0.0, 0.0)]
    for k in range(1, 12):
        t = k / 12
        prof.append((radius * math.sin(math.pi * t) ** 0.8 * (1 + 0.12 * rnd.uniform(-1, 1)), t * length))
    prof.append((0.0, length))
    _lathe(bm, prof, Matrix.Identity(4), 18)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _mesh_obj(name, bm, mat, smooth=True)
    ob.parent = parent
    ob.location = loc
    return ob


def sparks(name, mat, parent, seed=0, n=10, scale=1.0):
    """Fagulhas: tracos finos emissivos saindo da boca em leque (uma malha)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    for _ in range(n):
        yaw = math.radians(rnd.uniform(-55, 55))
        pit = math.radians(rnd.uniform(-15, 40))
        d = Vector((math.sin(yaw) * math.cos(pit), math.cos(yaw) * math.cos(pit), math.sin(pit)))
        p0 = d * rnd.uniform(0.6, 2.2) * scale
        L = rnd.uniform(0.25, 0.6) * scale
        m = Matrix.Translation(p0) @ d.to_track_quat("Y", "Z").to_matrix().to_4x4()
        _lathe(bm, [(0.0, 0.0), (0.012, L * 0.2), (0.008, L * 0.7), (0.0, L)], m, 5)
    ob = _mesh_obj(name, bm, mat, smooth=True)
    ob.parent = parent
    return ob


def smoke_ball(name, loc, radius, mat, parent=None, squash=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    ob = _mesh_obj(name, bm, mat, smooth=True)
    ob.parent = parent
    ob.location = loc
    ob.scale = (radius * squash[0], radius * squash[1], radius * squash[2])
    return ob


def point_light(name, loc, power, color, radius=0.25, parent=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = power
    ld.color = color
    ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    o.location = loc
    return o


def missile_slide(emp, pts, s_new, s_tail=3.6):
    """Leva o missil (e o rastro) para outro ponto s do mesmo caminho, sem refazer a etapa 1. O caminho
    p(s) = m0 + eixo * s + (0, 0, 0.05 s^2) e recuperado das pontas do rastro gravado (s = s_tail - 0.3 ... 0.15)."""
    sa, sb = s_tail - 0.3, 0.15
    qa = Vector(pts[0][:3]) - Vector((0, 0, 0.05 * sa * sa))
    qb = Vector(pts[-1][:3]) - Vector((0, 0, 0.05 * sb * sb))
    axis = (qa - qb) / (sa - sb)
    m0 = qb - axis * sb

    def path(s):
        return m0 + axis * s + Vector((0, 0, 0.05 * s * s))

    emp.location = path(s_new)
    emp.rotation_quaternion = (path(s_new + 0.1) - path(s_new)).normalized().to_track_quat("Y", "Z")
    n = len(pts)
    out = []
    for j in range(n):
        t = j / (n - 1)
        p = path(s_new - 0.3 - (s_new - 0.15) * t)
        out.append([p.x, p.y, p.z, 0.10 + 0.34 * t ** 0.9])
    return out


def effects():
    """Salva do 406 (clarao, jatos do freio, luz, fumaca, freio em brasa), chama/luz/rastro do missil e a carga
    ciano nas bocas do canhao de plasma."""
    sc = bpy.context.scene
    F = FLASH
    fx = {
        "flame": mat_flame("fx_flame", strength=9.0),
        "flame_side": mat_flame("fx_flame_side", strength=8.0, power=1.9),
        "msl": mat_flame("fx_msl", strength=22.0, power=1.1),
        "spark": mat_spark("fx_spark", strength=18.0),
        "ball": mat_flame("fx_ball", hot=(1.0, 0.62, 0.26), mid=(1.0, 0.24, 0.02), strength=3.2, power=1.2),
        "plasma": mat_flame("fx_plasma", hot=(0.75, 0.95, 1.0), mid=(0.12, 0.62, 1.0), strength=7.0, power=1.3),
        # fumaca cinza fria e mais rala; a barriga pega o laranja da luz do clarao
        "smoke": [mat_smoke(f"fx_smoke{i}", color=(0.11, 0.115, 0.125), density=4.5, seed=i * 3.1,
                            emit=((1.0, 0.30, 0.05), 0.25)) for i in range(3)],
        "trail": [mat_smoke(f"fx_trail{i}", color=(0.20, 0.205, 0.21), density=d, scale=3.2, seed=10 + i * 2.3)
                  for i, d in enumerate((4.5, 2.8, 1.6))],
        "trail_hot": mat_smoke("fx_trail_hot", color=(0.25, 0.18, 0.12), density=8.0, seed=7.7,
                               emit=((1.0, 0.42, 0.08), 4.0)),
    }
    for spec in WEAPONS:
        key = spec["mod"]
        if spec.get("fire"):
            heat = {}
            for o in sc.objects:
                if o.get("fx_hot") == key and o.type == "MESH" and o.data.materials:
                    m0 = o.data.materials[0]
                    if m0.name not in heat:
                        heat[m0.name] = mat_heat(m0, strength=0.55)
                    o.data.materials[0] = heat[m0.name]
            anchors = sorted([o for o in sc.objects if o.name.startswith(f"fxa_muzzle_{key}")], key=lambda o: o.name)
            for k, a in enumerate(anchors):
                flame(f"flash{k}", 2.6 * F, 0.42 * F, fx["flame"], spikes=8, seed=3 + k, parent=a)
                fireball(f"fireball{k}", 1.8 * F, 0.75 * F, fx["ball"], parent=a, loc=(0, 0.3 * F, 0.02), seed=40 + k)
                if key == "bs_naval_406":
                    # jatos das portas do freio (para os lados): portas em y = 3.33 e 3.69 do cano de 4.0
                    for j, (dy, w) in enumerate(((-0.63, 0.30), (-0.27, 0.355))):
                        for sx in (-1, 1):
                            flame(f"sidejet{k}{j}{sx}", (0.75 if j else 0.55) * F, 0.15 * F, fx["flame_side"],
                                  spikes=3, seed=20 + k * 7 + j, cone=18, parent=a, loc=(sx * (w - 0.02), dy, 0),
                                  rot=(0, 0, -90 * sx))
                point_light(f"flashlight{k}", (0, 0.9 * F, 0.15), 260.0, (1.0, 0.5, 0.16), radius=0.6, parent=a)
                sparks(f"sparks{k}", fx["spark"], a, seed=60 + k, scale=F)
                # fumaca: nuvem em volta da boca que sobe e se abre (fica no quadro, nao so a frente do cano)
                sg = 1 if k % 2 else -1
                S = 0.5 + 0.5 * F
                for j, (x, d, up, r) in enumerate(((0.0, 0.9, 0.2, 0.55), (0.6 * sg, 1.5, 0.5, 0.75),
                                                   (-0.5 * sg, 1.1, 0.75, 0.6), (0.2 * sg, 2.1, 0.95, 0.95),
                                                   (-0.2 * sg, 0.15, 0.75, 0.5))):
                    smoke_ball(f"smoke{k}{j}", (x * S, d * S, up * S), r * S, fx["smoke"][(k + j) % 3], parent=a,
                               squash=(1.0, 0.85, 0.85))
                for sx in (-1, 1):
                    smoke_ball(f"sidesmoke{k}{sx}", (sx * 0.85 * S, -0.45, 0.1), 0.42 * S, fx["smoke"][(k + 1) % 3],
                               parent=a, squash=(1.2, 0.7, 0.8))
        if spec.get("charge"):
            # plasma carregando: lingua ciano curta em cada boca + luz ciano fraca (le como arma de plasma)
            for k, a in enumerate(sorted([o for o in sc.objects if o.name.startswith(f"fxa_muzzle_{key}")],
                                         key=lambda o: o.name)):
                flame(f"plasma{k}", 0.55, 0.13, fx["plasma"], spikes=3, seed=70 + k, cone=14, parent=a)
                point_light(f"plasmalight{k}", (0, 0.25, 0.1), 25.0, (0.3, 0.8, 1.0), radius=0.15, parent=a)
        if spec.get("missile") and f"fxa_msl_{key}" in sc.objects:
            emp = sc.objects[f"fxa_msl_{key}"]
            head = sc.objects[f"head_{key}"]
            pts = json.loads(head["fx_trail"])
            if spec.get("msl_s"):
                pts = missile_slide(emp, pts, spec["msl_s"])
            emp.scale = (1.35, 1.35, 1.35)     # missil um pouco maior que a escala do casulo (le na miniatura)
            flame("msl_flame", 1.5, 0.13, fx["msl"], spikes=4, seed=9, cone=10, parent=emp, loc=(0, -0.02, 0),
                  rot=(0, 0, 180))
            point_light("msl_light", (0, -0.35, 0), 220.0, (1.0, 0.5, 0.16), radius=0.2, parent=emp)
            rnd = random.Random(23)
            for j, (x, y, z, r) in enumerate(pts):
                # rastro irregular: bolas desencontradas, cada vez mais ralas perto do casulo (a fumaca se desfaz)
                t = j / max(1, len(pts) - 1)
                r = (r * 1.6 + 0.04) * rnd.uniform(0.8, 1.25)
                jit = r * 0.35 * t
                p = (x + rnd.uniform(-jit, jit), y + rnd.uniform(-jit, jit), z + rnd.uniform(-jit, jit) + 0.25 * t * t)
                mat = fx["trail_hot"] if j < 3 else fx["trail"][min(2, int(t * 3))]
                smoke_ball(f"trail{j}", p, r, mat, parent=head)


def lights_and_world():
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == "LIGHT" and not o.parent]:
        bpy.data.objects.remove(o, do_unlink=True)

    def add(name, kind, energy, color, frm, to, **kw):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        for k, v in kw.items():
            setattr(ld, k, v)
        o = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(o)
        o.location = frm
        o.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        return o

    def sph(az, el, d, alvo):
        a, e = math.radians(az), math.radians(el)
        return (alvo[0] + d * math.cos(e) * math.cos(a), alvo[1] + d * math.cos(e) * math.sin(a),
                alvo[2] + d * math.sin(e))

    alvo = (1.0, 1.2, 0.6)
    # chave: spot neutro-quente rasante (~30 graus) da esquerda da camera: cada grupo de lascas ganha uma quina
    # clara e as frestas caem no nucleo escuro (o resto do conves cai no escuro)
    add("key", "SPOT", 9000.0, (1.0, 0.94, 0.86), sph(CAM_AZ - 42, 30, 22, alvo), alvo,
        spot_size=math.radians(30), spot_blend=0.95, shadow_soft_size=1.2)
    # contraluz fria e baixa de tras-direita (em relacao a camera): recorta a silhueta das armas contra o espaco.
    # Ligacao de luz: so as armas e os efeitos recebem (no conves ela acenderia a quina de cada placa)
    rim = add("rim", "SUN", 7.0, (0.62, 0.78, 1.0), sph(CAM_AZ + 145, 14, 20, (0, 0, 0)), (0.0, 0.0, 0.0),
              angle=math.radians(4))
    recv = bpy.data.collections.new("bs_rim_recv")
    for o in sc.objects:
        if o.type == "MESH" and not o.get("deck"):
            recv.objects.link(o)
    rim.light_linking.receiver_collection = recv
    # preenchimento fraco do lado da camera
    add("fill", "SUN", 0.15, (0.7, 0.78, 1.0), sph(CAM_AZ + 10, 30, 10, (0, 0, 0)), (0.0, 0.0, 0.0),
        angle=math.radians(30))
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.006, 0.008, 0.017, 1)
    bg.inputs[1].default_value = 1.0


def camera(res):
    sc = bpy.context.scene
    cam = bpy.data.objects.new("hero_cam", bpy.data.cameras.new("hero_cam"))
    cam.data.lens = CAM_LENS
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.1
    cam.data.clip_end = 400
    sc.collection.objects.link(cam)
    loc = cam_loc()
    cam.location = loc
    cam.rotation_euler = (Vector(CAM_AIM) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if CAM_FSTOP:
        # foco no pivo do 406 (primeira arma): o conves da frente desfoca de leve
        w = WEAPONS[0]
        P = importlib.import_module(sc.objects[f"part_{w['mod']}"]["bs_mod"]).PART
        foco = Vector((w["at"][0] + P["pivot"][0], w["at"][1] + P["size"][1] - P["pivot"][1], 0.9))
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = (foco - Vector(loc)).length
        cam.data.dof.aperture_fstop = CAM_FSTOP
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100


def setup(res, samples, cache=None):
    load_or_build(cache)
    rects = layout()
    _log("conves e efeitos")
    deck(rects)
    effects()
    lights_and_world()
    camera(res)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.max_bounces = 6
    sc.cycles.volume_bounces = 0
    sc.cycles.volume_biased = True       # volumes ~50x mais rapidos (marcha de raio)
    sc.cycles.volume_step_rate = 2.0
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    B.show_only(["roof", "head", "barrel", "deck", "fx"])


def render_exr(path):
    sc = bpy.context.scene
    st = sc.render.image_settings
    st.file_format = "OPEN_EXR"
    st.color_mode = "RGBA"
    st.color_depth = "16"
    st.exr_codec = "ZIP"
    sc.render.filepath = path
    _log("render")
    bpy.ops.render.render(write_still=True)
    _log("render pronto")


def render_depth(path):
    """Passe rapido de profundidade: emissao = distancia ate a camera / 100 (sem fumaca nem chamas)."""
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    m, nt, out = _nt("__depth")
    cd = nt.nodes.new("ShaderNodeCameraData")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(_math(nt, "MULTIPLY", cd.outputs["View Distance"], None, vb=0.01), em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    hidden = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and
              any(m_ and m_.name.startswith(("fx_", "__")) for m_ in o.data.materials)]
    for o in hidden:
        o.hide_render = True
    prev = (sc.cycles.samples, sc.cycles.use_denoising)
    sc.cycles.samples, sc.cycles.use_denoising = 1, False
    dof = sc.camera.data.dof.use_dof
    sc.camera.data.dof.use_dof = False       # 1 amostra: a profundidade tem que sair nitida
    vl.material_override = m
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    vl.material_override = None
    sc.cycles.samples, sc.cycles.use_denoising = prev
    sc.camera.data.dof.use_dof = dof
    for o in hidden:
        o.hide_render = False
    _log("profundidade pronta")


def load_exr(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)[::-1].copy()


# ============================================================================ etapa 4: composicao (numpy)
def _blur_axis(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, r):
    """Desfoque quase gaussiano (3 caixas) de raio ~r px."""
    r = max(1, int(round(r / 1.7)))
    for _ in range(3):
        a = _blur_axis(_blur_axis(a, r, 0), r, 1)
    return a


def _value_noise(h, w, cells, rnd):
    g = rnd.random((cells + 3, cells + 3)).astype(np.float32)
    big = Image.fromarray(g, "F").resize((w + 2 * (w // cells), h + 2 * (h // cells)), Image.BICUBIC)
    a = np.asarray(big, dtype=np.float32)
    return a[h // cells:h // cells + h, w // cells:w // cells + w]


def fbm(h, w, base, octaves, rnd):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += _value_noise(h, w, base * 2 ** o, rnd) * amp
        tot += amp
        amp *= 0.55
    return out / tot


def space_bg(h, w, seed=5):
    """Espaco profundo (linear): degrade azul-noite, nebulosa violeta/azul-petroleo em faixa diagonal, estrelas."""
    rnd = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v, u = yy / h, xx / w
    bg = np.array([0.006, 0.008, 0.022], np.float32) * (1 - v[..., None]) + \
        np.array([0.002, 0.0025, 0.006], np.float32) * v[..., None]
    n1 = fbm(h, w, 3, 6, rnd)
    n2 = fbm(h, w, 5, 5, rnd)
    band = np.exp(-((v - (0.30 - 0.22 * u)) / 0.2) ** 2)          # faixa diagonal (meio-esquerda -> alto-direita)
    bg = bg + (np.clip((n1 - 0.42) * 2.6, 0, 1) ** 1.6 * band)[..., None] * np.array([0.06, 0.018, 0.085], np.float32)
    bg = bg + (np.clip((n2 - 0.5) * 3.0, 0, 1) ** 2 * band)[..., None] * np.array([0.008, 0.036, 0.055], np.float32)
    # mancha fria azul-petroleo no alto a esquerda, atras das armas do fundo (separa as silhuetas do violeta)
    teal = np.exp(-(((u - 0.22) / 0.24) ** 2 + ((v - 0.24) / 0.13) ** 2))
    bg = bg + (teal * (0.35 + 0.65 * n1))[..., None] * np.array([0.004, 0.026, 0.036], np.float32)
    # brilho quente distante (eco do ambar do mod) no alto a direita
    warm = np.exp(-(((u - 0.9) / 0.35) ** 2 + ((v - 0.05) / 0.28) ** 2))
    bg = bg + (warm * (0.4 + 0.6 * n2))[..., None] * np.array([0.028, 0.010, 0.003], np.float32)
    stars = np.zeros((h, w), np.float32)
    n = int(h * w / 700)
    sy, sx = rnd.integers(0, h, n), rnd.integers(0, w, n)
    keep = rnd.random(n) < (0.35 + 0.65 * band[sy, sx])
    sy, sx = sy[keep], sx[keep]
    mag = np.minimum(rnd.pareto(2.4, len(sy)).astype(np.float32) * 0.14 + 0.03, 3.0)
    np.add.at(stars, (sy, sx), mag)
    stars = stars * 0.6 + blur(stars, max(1.0, w / 900)) * 2.5
    warm_t = (rnd.random((h, w)) < 0.4).astype(np.float32)[..., None]
    col = np.array([0.85, 0.9, 1.0], np.float32) * (1 - warm_t) + np.array([1.0, 0.9, 0.75], np.float32) * warm_t
    return bg + stars[..., None] * col


def tonemap(lin):
    """Curva de tom que preserva o matiz: o ombro suave age no maior canal e a cor escala junto (o laranja do
    clarao continua laranja em vez de virar amarelo/branco); so o miolo muito forte desatura para branco-amarelo.
    Sai em sRGB."""
    k = 0.72
    x = np.maximum(lin, 0)
    m = x.max(axis=-1, keepdims=True)
    mt = np.where(m < k, m, k + (1 - k) * (1 - np.exp(-(m - k) / (1 - k))))
    y = x * (mt / np.maximum(m, 1e-6))
    hot = np.clip((m - 4.0) / 14.0, 0, 1) ** 0.9
    y = y * (1 - hot) + hot * mt * np.array([1.0, 0.96, 0.86], np.float32)
    s = np.where(y <= 0.0031308, y * 12.92, 1.055 * np.power(np.clip(y, 0.0031308, None), 1 / 2.4) - 0.055)
    return np.clip(s, 0, 1)


def compose(raw, out_png, depth=None):
    h, w = raw.shape[:2]
    rgb, a = raw[..., :3], np.clip(raw[..., 3:4], 0, 1)
    if depth is not None:
        # nevoa de distancia: o conves e as pecas longe somem no escuro (profundidade em unidades/100)
        dist = depth[..., 0] / np.maximum(depth[..., 3], 1e-4) * 100.0
        fog = (np.clip((dist - 20.0) / 22.0, 0, 1) ** 1.3 * 0.8 * np.clip(depth[..., 3], 0, 1))[..., None]
        rgb = rgb * (1 - fog) + np.array([0.003, 0.004, 0.009], np.float32) * fog * a
    lin = rgb + space_bg(h, w) * (1 - a)
    # bloom: so o que passa de ~1 (clarao, chama, LEDs fortes) em 4 escalas
    br = np.maximum(lin - 1.0, 0)
    bloom = np.zeros_like(lin)
    for r, wgt in ((w / 320, 0.4), (w / 120, 0.3), (w / 45, 0.2), (w / 16, 0.1)):
        bloom += blur(br, r) * wgt
    lin = lin + bloom * 0.6
    # vinheta centrada no corpo do 406 e mais forte para a direita e para baixo (o conves iluminado pelo clarao
    # nao compete com a torre, que fica a maior massa clara que nao e luz)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    d = np.sqrt(((u - VIG_C[0]) / np.where(u > VIG_C[0], 0.62, 0.8)) ** 2 +
                ((v - VIG_C[1]) / np.where(v > VIG_C[1], 0.5, 0.75)) ** 2)
    lin = lin * (1 - 0.7 * np.clip(d - 0.3, 0, 1) ** 1.3)[..., None]
    img = (tonemap(lin) * 255 + 0.5).astype(np.uint8)
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    Image.fromarray(img, "RGB").save(out_png)
    _log(f"OK {out_png} {img.shape[1]}x{img.shape[0]}")


# ============================================================================ principal
def main():
    global OUT
    args = sys.argv[1:]
    quick = "--quick" in args

    def opt(name, default=None):
        if name not in args:
            return default
        i = args.index(name)
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            sys.exit(f"ERRO: {name} precisa de um valor")
        return args[i + 1]

    # --quick sem --out vai para um rascunho temporario: nunca sobrescreve a arte final com um rascunho
    OUT = os.path.abspath(opt("--out", QUICK_OUT if quick else OUT))
    res = int(opt("--res", 384 if quick else 1024))
    samples = int(opt("--samples", 16 if quick else 128))
    raw = opt("--raw")
    comp_only = "--comp-only" in args
    if comp_only and (raw is None or not os.path.exists(raw)):
        sys.exit("ERRO: --comp-only precisa de --raw ARQ.exr de um render anterior (feito com --raw)")
    tmp = raw is None
    if tmp:
        raw = os.path.join(tempfile.gettempdir(), f"bs_logo_{os.getpid()}.exr")
    depth = raw[:-4] + "_depth.exr"
    if not comp_only:
        setup(res, samples, opt("--cache"))
        render_exr(raw)
        render_depth(depth)
    compose(load_exr(raw), OUT, load_exr(depth) if os.path.exists(depth) else None)
    if tmp:
        for p in (raw, depth):
            if os.path.exists(p):
                os.remove(p)
    if quick and OUT == QUICK_OUT:
        print(f"rascunho (--quick): {OUT}  (a arte final {os.path.join(HERE, 'logo_hero.png')} nao foi tocada)")


if __name__ == "__main__":
    main()
