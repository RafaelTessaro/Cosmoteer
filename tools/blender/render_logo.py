"""Imagem heroi do logo do Bullet Strike: cena cinematografica 3D montada com os modelos das armas do mod.

    <venv-com-bpy>/bin/python tools/blender/render_logo.py [--out ARQ.png] [--quick] [--res N] [--samples N]
                                                           [--raw ARQ.exr] [--comp-only]

Nada e remodelado: a cena importa os modulos de tools/blender/parts/ e chama as funcoes de modelagem como o
render_part.py (roof/head/barrel/cell), so que todas numa cena unica, em perspectiva:
  * Torre Naval Tripla 406 mm (Mapinguari) em primeiro plano, disparando a salva (clarao emissivo nas bocas e
    nas portas do freio, luz do clarao, fumaca volumetrica, freios em brasa);
  * Bateria de Misseis Mula-sem-Cabeca atras, com os narizes carregados nos tubos e um missil saindo do casulo
    (chama, luz e rastro de fumaca);
  * Canhao de Plasma Curupira ao fundo (destaque ciano);
  * conves blindado escuro da nave (placas chanfradas por tile, escotilhas e luzes em recessos, borda do casco)
    e espaco profundo (estrelas e nebulosa) composto depois do render.

O render sai em EXR linear (pre-multiplicado); a composicao (fundo, brilho/bloom, curva de tom, vinheta) e
feita em numpy e grava um PNG RGB quadrado. --comp-only refaz so a composicao a partir do EXR de --raw.
O titulo e o subtitulo NAO ficam aqui: tools/make_art.py logo() reduz esta imagem para 512 e escreve o texto.
"""

import importlib
import math
import os
import random
import sys
import tempfile

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
# armas: "at" = canto (x0, y0) da peca na grade do conves (tiles inteiros), yaw = giro da torre (graus, anti-horario;
# 0 = cano para +Y), elev = elevacao dos canos (graus)
WEAPONS = [
    {"mod": "bs_naval_406", "at": (-3, -3), "yaw": -128.0, "elev": 7.0, "recoil": 0.18, "fire": True},
    {"mod": "bs_msl_quad", "alt": "bs_msl_twin", "at": (-14, 6), "yaw": 52.0, "missile": True},
    {"mod": "bs_plasma_heavy", "at": (8, 11), "yaw": -150.0, "elev": 4.0},
]
DECK_X = (-26, 26)          # extensao do conves (tiles)
DECK_Y = (-14, 30)
CAM_LOC = (-7.0, -15.5, 7.2)
CAM_AIM = (0.6, 3.2, 1.4)
CAM_LENS = 38.0
HEAD_LIFT = 0.10            # a cabeca fica um pouco acima do teto (como no render 3/4 do 76 mm)
PAINT = (0.055, 0.068, 0.092)   # pintura do casco (troca o verde do teto)

QUICK = False
OUT = os.path.join(HERE, "logo_hero.png")


# ============================================================================ utilidades
def _novos(antes):
    return [o for o in bpy.context.scene.objects if o.name not in antes]


def _raizes(objs):
    return [o for o in objs if o.parent is None]


def _cena():
    return set(o.name for o in bpy.context.scene.objects)


def _empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = tuple(math.radians(a) for a in rot)
    if parent is not None:
        e.parent = parent
    return e


def _construir(fn, parent):
    """Roda uma funcao de modelagem e prende os objetos novos (raizes) no Empty 'parent'."""
    antes = _cena()
    fn()
    novos = _novos(antes)
    for o in _raizes(novos):
        if o is not parent:
            o.parent = parent
    return novos


def _tag(objs, tag):
    for o in objs:
        o[tag] = True


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
    if isinstance(mat, (list, tuple)):
        for m in mat:
            ob.data.materials.append(m)
    else:
        ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


# ============================================================================ materiais de efeito
def _nt(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def mat_flame(name, hot=(1.0, 0.86, 0.55), mid=(1.0, 0.38, 0.06), strength=40.0, power=1.6):
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
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (*mid, 1)
    Lk(sep.outputs[1], ramp.inputs[0])
    # intensidade: (1 - y)^power * bordas suaves (camada de facing)
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    Lk(sep.outputs[1], inv.inputs[1])
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = power
    Lk(inv.outputs[0], pw.inputs[0])
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = 0.5
    edge = N.new("ShaderNodeMath")
    edge.operation = "SUBTRACT"
    edge.inputs[0].default_value = 1.0
    Lk(lw.outputs["Facing"], edge.inputs[1])
    edge2 = N.new("ShaderNodeMath")
    edge2.operation = "POWER"
    edge2.inputs[1].default_value = 1.5
    Lk(edge.outputs[0], edge2.inputs[0])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    Lk(pw.outputs[0], mul.inputs[0])
    Lk(edge2.outputs[0], mul.inputs[1])
    st = N.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = strength
    Lk(mul.outputs[0], st.inputs[0])
    em = N.new("ShaderNodeEmission")
    Lk(ramp.outputs[0], em.inputs["Color"])
    Lk(st.outputs[0], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    add = N.new("ShaderNodeAddShader")
    Lk(tr.outputs[0], add.inputs[0])
    Lk(em.outputs[0], add.inputs[1])
    Lk(add.outputs[0], out.inputs["Surface"])
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
    fall.inputs[2].default_value = 0.35
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
    nmr.inputs[1].default_value = 0.42
    nmr.inputs[2].default_value = 0.72
    Lk(noise.outputs["Fac"], nmr.inputs[0])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    Lk(fall.outputs[0], mul.inputs[0])
    Lk(nmr.outputs[0], mul.inputs[1])
    dens = N.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = density
    Lk(mul.outputs[0], dens.inputs[0])
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Anisotropy"].default_value = 0.25
    Lk(dens.outputs[0], vol.inputs["Density"])
    if emit:
        # brasa no miolo da fumaca (perto do clarao)
        vol.inputs["Emission Color"].default_value = (*emit[0], 1)
        em = N.new("ShaderNodeMath")
        em.operation = "MULTIPLY"
        em.inputs[1].default_value = emit[1]
        Lk(mul.outputs[0], em.inputs[0])
        Lk(em.outputs[0], vol.inputs["Emission Strength"])
    Lk(vol.outputs[0], out.inputs["Volume"])
    return m


def mat_heat(base, strength=1.6, color=(1.0, 0.13, 0.015)):
    """Copia o material da blindagem e soma brasa (freio quente depois do tiro)."""
    m = base.copy()
    m.name = base.name + "_quente"
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


# ============================================================================ geometria de efeito
def _lathe(bm, prof, axis_m, verts=16):
    """Solido de revolucao no eixo +Y (perfil [(raio, y)]) transformado por axis_m, dentro de um bmesh."""
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


def flame(name, length, radius, mat, spikes=6, seed=1, cone=26.0, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Clarao de boca: fuso principal ao longo de +Y + pontas (jatos finos) abertas em leque."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    prof = [(0.0, 0.0)]
    for k in range(1, 15):
        t = k / 14
        r = radius * (min(1.0, t / 0.22) ** 0.6) * (1 - max(0.0, (t - 0.22) / 0.78)) ** 1.25
        prof.append((max(r, 0.0), t * length))
    prof[-1] = (0.0, length)
    _lathe(bm, prof, Matrix.Identity(4), 14)
    for s in range(spikes):
        a = rnd.uniform(0, math.tau)
        tilt = math.radians(rnd.uniform(cone * 0.35, cone))
        L = length * rnd.uniform(0.45, 0.8)
        rr = radius * rnd.uniform(0.18, 0.32)
        m = Matrix.Rotation(a, 4, "Y") @ Matrix.Rotation(tilt, 4, "X")
        p = [(0.0, 0.0), (rr * 0.7, L * 0.08), (rr, L * 0.3), (rr * 0.45, L * 0.7), (0.0, L)]
        _lathe(bm, p, Matrix.Translation((0, length * 0.05, 0)) @ m, 8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _mesh_obj(name, bm, mat, smooth=True)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    ob.rotation_euler = tuple(math.radians(a) for a in rot)
    return ob


def smoke_ball(name, loc, radius, mat, parent=None, squash=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    ob = _mesh_obj(name, bm, mat, smooth=True)
    if parent is not None:
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
    if parent is not None:
        o.parent = parent
    o.location = loc
    return o


# ============================================================================ conves da nave
def deck(skip, M):
    """Conves escuro: uma placa chanfrada com painel interno por tile (malha unica), laje escura por baixo,
    escotilhas/respiros esparsos com luz ambar em recesso e a borda do casco com luzes de posicao."""
    paint = B.mat_paint("deck_paint", PAINT, rough=0.42, metal=0.45, wear=0.18, grime=0.25, scale=3)
    paint2 = B.mat_paint("deck_paint2", tuple(c * 0.82 for c in PAINT), rough=0.46, metal=0.45, wear=0.15,
                         grime=0.3, scale=3)
    x0, x1 = DECK_X
    y0, y1 = DECK_Y
    tags = ("deck",)
    B.box("deck_slab", (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, -0.12, 0.0, M["core"], bevel=0.0, tags=tags)
    bm = bmesh.new()
    rnd = random.Random(11)

    def prism(poly, z0, z1, slope, mi):
        top = B.offset_poly(poly, slope)
        poly = B._ccw(poly)
        top = B._ccw(top)
        vb = [bm.verts.new((x, y, z0)) for x, y in poly]
        vt = [bm.verts.new((x, y, z1)) for x, y in top]
        f = bm.faces.new(vt)
        f.material_index = mi
        n = len(poly)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
            f.material_index = mi

    def inside(tx, ty):
        return any(a <= tx < c and b <= ty < d for a, b, c, d in skip)

    g = 0.035
    specials = []
    for tx in range(x0, x1):
        for ty in range(y0, y1):
            if inside(tx, ty):
                continue
            mi = 1 if rnd.random() < 0.18 else 0
            poly = B.rpoly(tx + 0.5, ty + 0.5, 1 - 2 * g, 1 - 2 * g, 0, chamfer=0.08)
            prism(poly, 0.0, 0.06, 0.028, mi)
            inner = B.offset_poly(poly, 0.085)
            prism(inner, 0.056, 0.078, 0.012, mi)
            if rnd.random() < 0.035 and abs(tx) > 2:
                specials.append((tx + 0.5, ty + 0.5))
    ob = _mesh_obj("deck_plates", bm, [paint, paint2], tags=tags)
    # escotilhas e respiros com luz em recesso (detalhe esparso)
    for k, (cx, cy) in enumerate(specials):
        if k % 2 == 0:
            v = B.box(f"dk_vent{k}", cx, cy, 0.56, 0.34, 0.07, 0.12, M["core_mid"], bevel=0.01, slope=0.015, tags=tags)
            B.cut(v, [B.box(f"dk_vc{k}{i}", cx, cy - 0.11 + i * 0.075, 0.46, 0.03, 0.10, 0.2, M["core"], bevel=0.0)
                      for i in range(4)])
            B.box(f"dk_led{k}", cx, cy + 0.23, 0.16, 0.035, 0.07, 0.10, M["glow_dim"], bevel=0.0, tags=tags)
        else:
            hatch = B.rpoly(cx, cy, 0.62, 0.62, 0, chamfer=0.12)
            B.plate(f"dk_hatch{k}", hatch, 0.07, 0.11, M["armor_mid"], slope=0.02, tags=tags)
            B.box(f"dk_hh{k}", cx, cy - 0.16, 0.26, 0.05, 0.11, 0.14, M["steel"], bevel=0.01, tags=tags)
    # borda do casco: amurada chanfrada no fim do conves com luzes de posicao em recesso
    for side, (cx, cy, sx, sy) in {"far": ((x0 + x1) / 2, y1 + 0.35, x1 - x0 + 1.4, 0.7),
                                   "left": (x0 - 0.35, (y0 + y1) / 2, 0.7, y1 - y0),
                                   "right": (x1 + 0.35, (y0 + y1) / 2, 0.7, y1 - y0)}.items():
        B.box(f"rim_{side}", cx, cy, sx, sy, -0.6, 0.22, M["armor_mid"], bevel=0.04, slope=0.12, tags=tags)
    for i in range(x0 + 1, x1, 3):
        B.box(f"rimled{i}", i, y1 + 0.12, 0.30, 0.05, 0.16, 0.235, M["glow"], bevel=0.0, tags=tags)
    return ob


# ============================================================================ armas
def _mod(name, alt=None):
    try:
        return importlib.import_module(f"parts.{name}")
    except Exception as e:  # o modulo pode estar sendo editado por outro agente
        if not alt:
            raise
        print(f"AVISO: parts.{name} falhou ({e}); usando parts.{alt}")
        return importlib.import_module(f"parts.{alt}")


def weapon(spec, fx):
    mod = _mod(spec["mod"], spec.get("alt"))
    P = mod.PART
    accent = P.get("accent", "amber")
    M = _mats(accent)
    W, H = P["size"]
    pv = P["pivot"]
    ax, ay = spec["at"]
    cx, cy = ax + W / 2, ay + H / 2
    part = _empty(f"part_{spec['mod']}", (cx, cy, 0))
    ring = P.get("ring_r", P["turret_box"] * 0.45)
    if getattr(mod, "roof", None):
        _construir(lambda: mod.roof(M, "roof"), part)
    else:
        _construir(lambda: Mo.hull_roof(M, W, H, pv, ring, "roof"), part)
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    head = _empty(f"head_{spec['mod']}", (px, py, HEAD_LIFT), (0, 0, spec.get("yaw", 0.0)), parent=part)
    _construir(lambda: mod.head(M, "head", 0.0), head)
    info = {"mod": mod, "M": M, "head": head, "barrels": []}
    bar = P.get("barrels")
    if bar:
        bz = getattr(mod, "BZ", 0.6)
        L = bar["length"]
        for i, ys in enumerate(bar["ys"]):
            piv = _empty(f"bpiv_{spec['mod']}{i}", (ys, bar["root"] - spec.get("recoil", 0.0), bz),
                         (spec.get("elev", 0.0), 0, 0), parent=head)
            off = _empty(f"boff_{spec['mod']}{i}", (0, 0, -bz), parent=piv)
            objs = _construir(lambda: mod.barrel(M, L, "barrel", 0.0), off)
            info["barrels"].append((off, L, bz, objs))
    if P.get("kind") == "launcher" and spec.get("missile"):
        launcher_fx(mod, M, head, fx)
    return info


# ---------------------------------------------------------------------------- salva do 406
def fire_406(info, fx):
    """Clarao nas 3 bocas + jatos laterais nas portas do freio, luz laranja, fumaca e freio em brasa."""
    heat = {}
    for k, (off, L, bz, objs) in enumerate(info["barrels"]):
        for o in objs:
            if o.get("hot") and o.type == "MESH" and o.data.materials:
                m0 = o.data.materials[0]
                if m0.name not in heat:
                    heat[m0.name] = mat_heat(m0)
                o.data.materials[0] = heat[m0.name]
        flame(f"flash{k}", 2.4, 0.42, fx["flame"], spikes=7, seed=3 + k, parent=off, loc=(0, L - 0.04, bz))
        # jatos das portas do freio (para os lados)
        for j, (y, w) in enumerate(((3.33, 0.30), (3.69, 0.355))):
            for sx in (-1, 1):
                flame(f"sidejet{k}{j}{sx}", 0.85 if j else 0.65, 0.16, fx["flame_side"], spikes=3, seed=20 + k * 7 + j,
                      cone=18, parent=off, loc=(sx * (w - 0.02), y, bz), rot=(0, 0, -90 * sx))
        point_light(f"flashlight{k}", (0, L + 0.7, bz + 0.1), 900.0, (1.0, 0.5, 0.16), radius=0.4, parent=off)
        # fumaca: nuvens que se abrem a frente da boca e sobem um pouco
        for j, (d, r, up, side) in enumerate(((1.1, 0.55, 0.05, 0.0), (2.0, 0.85, 0.18, 0.12),
                                              (3.1, 1.15, 0.38, -0.2), (4.3, 1.45, 0.7, 0.3))):
            smoke_ball(f"smoke{k}{j}", (side * (1 if k % 2 else -1), L + d, bz + up), r, fx["smoke"][(k + j) % 3], parent=off,
                       squash=(1.0, 0.8, 0.85))
        for sx in (-1, 1):
            smoke_ball(f"sidesmoke{k}{sx}", (sx * 0.9, 3.55, bz + 0.1), 0.45, fx["smoke"][(k + 1) % 3], parent=off,
                       squash=(1.2, 0.7, 0.8))


# ---------------------------------------------------------------------------- lancador: narizes + missil
def launcher_fx(mod, M, head, fx):
    pods = getattr(mod, "POD_XS", None)
    pitch = getattr(mod, "PITCH", 40.0)
    rx = math.radians(pitch - 90.0)
    tubes = getattr(mod, "TUBES", [])
    if pods is None:
        px = getattr(mod, "POD_X", 0.85)
        pods = (-px, px)
    pod_y = getattr(mod, "POD_Y", 0.9)
    z0 = getattr(mod, "Z0", 1.0)
    fired = {(1, 1), (1, 4), (2, 0), (2, 7)}       # tubos vazios (ja dispararam)
    launch = (1, 1)                                 # tubo de onde sai o missil da cena

    def mouth(cx, u, v):
        return Vector((cx + u, pod_y + v * math.cos(rx), z0 + v * math.sin(rx)))

    if hasattr(mod, "cell"):
        for i, cx in enumerate(pods):
            for k, (u, v) in enumerate(tubes):
                if (i, k) in fired:
                    continue
                at = _empty(f"nose_at{i}_{k}", tuple(mouth(cx, u, v)), parent=head)
                _construir(lambda: mod.cell(M, "he", "head", form="tube"), at)
    i, k = launch
    u, v = tubes[k] if tubes else (0.0, 0.0)
    m0 = mouth(pods[i], u, v)
    axis = Vector((0, -math.sin(rx), math.cos(rx)))
    missile(M, head, m0, axis, fx)


def missile(M, head, m0, axis, fx):
    """Missil em voo (objeto de cena, nao e arma): corpo escuro, ogiva clara, anel ambar, aletas, chama e rastro."""
    # trajetoria: sai pelo eixo do tubo e curva um pouco para cima
    def path(s):
        up = Vector((0, 0, 1))
        return m0 + axis * s + up * (0.035 * s * s)

    s_tail = 3.4
    tail = path(s_tail)
    d = (path(s_tail + 0.1) - tail).normalized()
    q = d.to_track_quat("Y", "Z")
    emp = _empty("missile", tuple(tail), parent=head)
    emp.rotation_mode = "QUATERNION"
    emp.rotation_quaternion = q
    R = 0.078
    bm = bmesh.new()
    prof = [(0.0, -0.02), (0.05, -0.02), (0.062, 0.05), (R, 0.08), (R, 0.86)]
    _lathe(bm, prof + [(0.0, 0.86)], Matrix.Identity(4), 16)
    body = _mesh_obj("msl_body", bm, M["core_mid"], tags=("fx",), smooth=True)
    body.parent = emp
    bm = bmesh.new()
    rho = (R * R + 0.3 * 0.3) / (2 * R)
    nose = [(R, 0.86)]
    for kk in range(1, 11):
        t = kk / 10
        x = 0.3 * t
        r = math.sqrt(max(0.0, rho * rho - x * x)) + R - rho
        nose.append((max(r, 0.0), 0.86 + x))
    nose[-1] = (0.0, 1.16)
    _lathe(bm, nose, Matrix.Identity(4), 16)
    ob = _mesh_obj("msl_nose", bm, M["armor"], tags=("fx",), smooth=True)
    ob.parent = emp
    band = B.cyl("msl_band", 0, 0.80, 0, R + 0.004, 0.04, M["glow"], axis="Y", verts=16, bevel=0.0, tags=("fx",))
    band.parent = emp
    for kk in range(4):
        # aleta: trapezio fino no plano que contem o eixo (casco convexo dos 8 vertices)
        a = math.radians(45 + 90 * kk)
        ca, sa = math.cos(a), math.sin(a)
        bm = bmesh.new()
        for side in (-0.007, 0.007):
            for r, y in ((R - 0.01, 0.02), (R + 0.11, 0.05), (R + 0.11, 0.15), (R - 0.01, 0.32)):
                bm.verts.new((r * ca - side * sa, y, r * sa + side * ca))
        bmesh.ops.convex_hull(bm, input=list(bm.verts))
        fin = _mesh_obj(f"msl_fin{kk}", bm, M["armor_mid"], tags=("fx",))
        fin.parent = emp
    flame("msl_flame", 1.15, 0.13, fx["flame"], spikes=4, seed=9, cone=12, parent=emp, loc=(0, -0.02, 0),
          rot=(0, 0, 180))
    point_light("msl_light", (0, -0.35, 0), 260.0, (1.0, 0.5, 0.16), radius=0.2, parent=emp)
    # rastro: bolas de fumaca ao longo do caminho, finas perto do missil e largas perto do casulo
    n = 16
    for j in range(n):
        s = s_tail - 0.25 - (s_tail - 0.1) * (j / (n - 1))
        p = path(s)
        r = 0.12 + 0.30 * (j / (n - 1)) ** 0.8
        hot = j < 3
        smoke_ball(f"trail{j}", tuple(p), r, fx["trail_hot"] if hot else fx["smoke"][j % 3], parent=head,
                   squash=(1, 1, 1))


# ============================================================================ luzes, camera e render
def lights_and_world():
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)

    def aim(o, frm, to):
        o.location = frm
        o.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()

    # chave: spot quente-neutro vindo de cima/esquerda/frente, centrado no 406 (o resto do conves cai no escuro)
    key = bpy.data.lights.new("key", "SPOT")
    key.energy = 52000.0
    key.color = (1.0, 0.93, 0.84)
    key.spot_size = math.radians(48)
    key.spot_blend = 0.85
    key.shadow_soft_size = 1.6
    ko = bpy.data.objects.new("key", key)
    sc.collection.objects.link(ko)
    aim(ko, (-16.0, -14.0, 22.0), (0.5, 2.0, 0.0))
    # contraluz fria (sol baixo vindo de tras): desenha a silhueta das placas contra o espaco
    rim = bpy.data.lights.new("rim", "SUN")
    rim.energy = 3.2
    rim.color = (0.55, 0.72, 1.0)
    rim.angle = math.radians(4)
    ro = bpy.data.objects.new("rim", rim)
    sc.collection.objects.link(ro)
    ro.rotation_euler = Vector((-0.55, -1.0, -0.42)).to_track_quat("-Z", "Y").to_euler()
    # preenchimento fraco do lado da camera
    fill = bpy.data.lights.new("fill", "SUN")
    fill.energy = 0.35
    fill.color = (0.7, 0.78, 1.0)
    fill.angle = math.radians(30)
    fo = bpy.data.objects.new("fill", fill)
    sc.collection.objects.link(fo)
    fo.rotation_euler = Vector((0.3, 1.0, -0.6)).to_track_quat("-Z", "Y").to_euler()
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.012, 0.016, 0.03, 1)
    bg.inputs[1].default_value = 1.0


def camera(res):
    sc = bpy.context.scene
    cam = bpy.data.objects.new("hero_cam", bpy.data.cameras.new("hero_cam"))
    cam.data.lens = CAM_LENS
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.1
    cam.data.clip_end = 400
    sc.collection.objects.link(cam)
    cam.location = CAM_LOC
    cam.rotation_euler = (Vector(CAM_AIM) - Vector(CAM_LOC)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    return cam


def build_scene(res, samples):
    sc = B.reset()
    sc.cycles.samples = samples
    sc.cycles.max_bounces = 6
    sc.cycles.volume_bounces = 0
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    fx = {
        "flame": mat_flame("fx_flame", strength=60.0),
        "flame_side": mat_flame("fx_flame_side", strength=35.0, power=1.9),
        "smoke": [mat_smoke(f"fx_smoke{i}", density=5.0, seed=i * 3.1, emit=((1.0, 0.3, 0.05), 0.25)) for i in range(3)],
        "trail_hot": mat_smoke("fx_trail_hot", color=(0.2, 0.15, 0.1), density=4.0, seed=7.7, emit=((1.0, 0.4, 0.08), 6.0)),
    }
    skip = []
    infos = []
    for spec in WEAPONS:
        info = weapon(spec, fx)
        infos.append((spec, info))
        W, H = info["mod"].PART["size"]
        ax, ay = spec["at"]
        skip.append((ax, ay, ax + W, ay + H))
        if spec.get("fire"):
            fire_406(info, fx)
    M = _mats("amber")
    deck(skip, M)
    # teto verde das pecas -> pintura do casco
    paint = B.mat_paint("hull_paint", PAINT, rough=0.42, metal=0.45, wear=0.18, grime=0.25, scale=3)
    for o in sc.objects:
        if o.type != "MESH":
            continue
        for i, m in enumerate(o.data.materials):
            if m and m.name.startswith("roof_green"):
                o.data.materials[i] = paint
    lights_and_world()
    camera(res)
    B.show_only(["roof", "head", "barrel", "deck", "fx"])
    return sc


def render_exr(path):
    sc = bpy.context.scene
    st = sc.render.image_settings
    st.file_format = "OPEN_EXR"
    st.color_mode = "RGBA"
    st.color_depth = "16"
    st.exr_codec = "ZIP"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_exr(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)[::-1].copy()


# ============================================================================ composicao (numpy)
def _blur_axis(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, r):
    """Desfoque quase gaussiano (3 caixas)."""
    r = max(1, int(round(r / 1.7)))
    for _ in range(3):
        a = _blur_axis(_blur_axis(a, r, 0), r, 1)
    return a


def _value_noise(h, w, cells, rnd):
    g = rnd.random((cells + 3, cells + 3)).astype(np.float32)
    im = Image.fromarray(g, "F").resize((w + w // cells * 2, h + h // cells * 2), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32)
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
    """Espaco profundo linear: degrade azul-noite, nebulosa violeta/azul-petroleo em faixa diagonal e estrelas."""
    rnd = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = yy / h
    u = xx / w
    bg = np.zeros((h, w, 3), np.float32)
    top = np.array([0.006, 0.008, 0.022], np.float32)
    bot = np.array([0.002, 0.0025, 0.006], np.float32)
    bg += top * (1 - v[..., None]) + bot * v[..., None]
    n1 = fbm(h, w, 3, 6, rnd)
    n2 = fbm(h, w, 5, 5, rnd)
    band = np.exp(-((v - (0.18 + 0.32 * u)) / 0.2) ** 2)          # faixa diagonal (alto-esquerda -> meio-direita)
    neb = np.clip((n1 - 0.42) * 2.6, 0, 1) ** 1.6 * band
    neb2 = np.clip((n2 - 0.5) * 3.0, 0, 1) ** 2 * band
    bg += neb[..., None] * np.array([0.05, 0.016, 0.07], np.float32)        # violeta
    bg += neb2[..., None] * np.array([0.006, 0.03, 0.045], np.float32)      # azul-petroleo
    # brilho quente distante (eco do ambar do mod) no canto de cima a direita
    warm = np.exp(-(((u - 0.92) / 0.35) ** 2 + ((v - 0.05) / 0.3) ** 2))
    bg += (warm * (0.4 + 0.6 * n2))[..., None] * np.array([0.03, 0.011, 0.003], np.float32)
    # estrelas: muitas fracas, poucas fortes (com halo), mais densas na faixa da nebulosa
    stars = np.zeros((h, w), np.float32)
    n = int(h * w / 900)
    sy = rnd.integers(0, h, n)
    sx = rnd.integers(0, w, n)
    keep = rnd.random(n) < (0.35 + 0.65 * band[sy, sx])
    sy, sx = sy[keep], sx[keep]
    mag = rnd.pareto(2.6, len(sy)).astype(np.float32) * 0.12 + 0.03
    np.add.at(stars, (sy, sx), np.minimum(mag, 3.0))
    soft = blur(stars, max(1.0, w / 900))
    stars = stars * 0.6 + soft * 2.5
    tint = np.where(rnd.random((h, w)) < 0.5, 1.0, 0.0).astype(np.float32)[..., None]
    col = np.array([0.85, 0.9, 1.0], np.float32) * tint + np.array([1.0, 0.92, 0.8], np.float32) * (1 - tint)
    bg += stars[..., None] * col
    return bg


def tonemap(lin):
    """Curva de tom: linear ate 0.72, ombro suave; luzes muito fortes viram branco (miolo do clarao)."""
    k = 0.72
    x = np.maximum(lin, 0)
    y = np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))
    lum = x.max(axis=-1, keepdims=True)
    hot = np.clip((lum - 1.2) / 5.0, 0, 1) ** 0.8
    y = y * (1 - hot) + hot * 0.98
    s = np.where(y <= 0.0031308, y * 12.92, 1.055 * np.power(np.clip(y, 0.0031308, None), 1 / 2.4) - 0.055)
    return np.clip(s, 0, 1)


def compose(raw, out_png):
    h, w = raw.shape[:2]
    rgb, a = raw[..., :3], raw[..., 3:4]
    lin = rgb + space_bg(h, w) * (1 - np.clip(a, 0, 1))
    # bloom: so o que passa de 1 (clarao, chama, LEDs fortes) em 4 escalas
    br = np.maximum(lin - 0.9, 0)
    bloom = np.zeros_like(lin)
    for r, wgt in ((w / 300, 0.35), (w / 110, 0.3), (w / 40, 0.22), (w / 14, 0.16)):
        bloom += blur(br, r) * wgt
    lin = lin + bloom * 0.9
    # vinheta suave (centro do quadro um pouco acima do meio)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx / w - 0.52) / 0.75) ** 2 + ((yy / h - 0.42) / 0.7) ** 2)
    lin = lin * (1 - 0.55 * np.clip(d - 0.35, 0, 1) ** 1.4)[..., None]
    img = (tonemap(lin) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(img, "RGB").save(out_png)
    print("OK", out_png, img.shape)


# ============================================================================ principal
def main():
    global QUICK, OUT
    args = sys.argv[1:]
    QUICK = "--quick" in args
    if "--out" in args:
        OUT = os.path.abspath(args[args.index("--out") + 1])
    res = int(args[args.index("--res") + 1]) if "--res" in args else (384 if QUICK else 1024)
    samples = int(args[args.index("--samples") + 1]) if "--samples" in args else (16 if QUICK else 160)
    raw = args[args.index("--raw") + 1] if "--raw" in args else None
    tmp = raw is None
    if tmp:
        raw = os.path.join(tempfile.gettempdir(), f"bs_logo_{os.getpid()}.exr")
    if "--comp-only" not in args:
        build_scene(res, samples)
        render_exr(raw)
    data = load_exr(raw)
    compose(data, OUT)
    if tmp and os.path.exists(raw):
        os.remove(raw)


if __name__ == "__main__":
    main()
