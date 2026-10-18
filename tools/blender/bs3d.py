"""Biblioteca de modelagem/renderizacao 3D (Blender 5.x, modulo bpy) para os sprites do Bullet Strike.

Convencoes (iguais as do Cosmoteer):
  * 1 unidade do Blender = 1 tile = 64 px no sprite final.
  * Camera ortografica olhando de cima (-Z). Imagem: +X = direita, +Y = CIMA (o cano aponta para +Y).
  * Mapa de normais: R = +x, G = +y (para cima), B = +z (para fora da tela); plano = (127,127,255).
  * Renderiza em SS vezes a resolucao final e reduz com LANCZOS (antisserrilhado limpo).

Uso: este modulo roda dentro do Python do Blender (python3.11 + pip install bpy).
"""

import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageFilter

PX = 64
SS = 2
B_HALO = 0.9  # raio do halo de brilho em px por tile de largura

# ============================================================================ cena


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()  # os materiais antigos morrem com a cena
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.threads_mode = "AUTO"
    world = bpy.data.worlds.new("world")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.66, 0.74, 1)
    bg.inputs[1].default_value = 0.55
    _lights()
    return sc


def _lights():
    sc = bpy.context.scene

    def sun(name, energy, rot, color=(1, 1, 1), angle=8):
        l = bpy.data.lights.new(name, "SUN")
        l.energy = energy
        l.color = color
        l.angle = math.radians(angle)
        o = bpy.data.objects.new(name, l)
        o.rotation_euler = [math.radians(a) for a in rot]
        sc.collection.objects.link(o)
        return o

    # luz principal vinda de cima-esquerda (padrao dos sprites do jogo), contra-luz fria e preenchimento
    sun("key", 3.2, (38, 0, -135), (1.0, 0.97, 0.92), 6)
    sun("rim", 1.4, (62, 0, 45), (0.65, 0.78, 1.0), 12)
    sun("fill", 0.6, (20, 0, 90), (1, 1, 1), 30)


def camera(w_tiles, h_tiles, center=(0, 0)):
    sc = bpy.context.scene
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w_tiles, h_tiles)
    cam.data.clip_start = 0.1
    cam.data.clip_end = 200
    cam.location = (center[0], center[1], 50)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x = int(round(w_tiles * PX * SS))
    sc.render.resolution_y = int(round(h_tiles * PX * SS))
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1
    return cam


# ============================================================================ materiais
_MATS = {}


def _principled(m):
    m.use_nodes = True
    return m.node_tree.nodes["Principled BSDF"], m.node_tree


def mat_paint(name, color, rough=0.42, metal=0.55, wear=0.55, grime=0.35, scale=6.0):
    """Blindagem pintada com desgaste nas quinas (Pointiness) e sujeira (ruido)."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    b, nt = _principled(m)
    N = nt.nodes
    geo = N.new("ShaderNodeNewGeometry")
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.52
    ramp.color_ramp.elements[1].position = 0.60
    nt.links.new(geo.outputs["Pointiness"], ramp.inputs[0])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8
    nramp = N.new("ShaderNodeValToRGB")
    nramp.color_ramp.elements[0].position = 0.35
    nramp.color_ramp.elements[1].position = 0.75
    nt.links.new(noise.outputs["Fac"], nramp.inputs[0])
    base = N.new("ShaderNodeRGB")
    base.outputs[0].default_value = (*color, 1)
    dirty = N.new("ShaderNodeMix")
    dirty.data_type = "RGBA"
    dirty.inputs[7].default_value = (color[0] * 0.55, color[1] * 0.55, color[2] * 0.55, 1)
    nt.links.new(base.outputs[0], dirty.inputs[6])
    m1 = N.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    m1.inputs[1].default_value = grime
    nt.links.new(nramp.outputs[0], m1.inputs[0])
    nt.links.new(m1.outputs[0], dirty.inputs[0])
    worn = N.new("ShaderNodeMix")
    worn.data_type = "RGBA"
    worn.inputs[7].default_value = (0.62, 0.63, 0.64, 1)
    nt.links.new(dirty.outputs[2], worn.inputs[6])
    m2 = N.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    m2.inputs[1].default_value = wear
    nt.links.new(ramp.outputs[0], m2.inputs[0])
    nt.links.new(m2.outputs[0], worn.inputs[0])
    nt.links.new(worn.outputs[2], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metal
    rr = N.new("ShaderNodeMapRange")
    rr.inputs[3].default_value = rough - 0.1
    rr.inputs[4].default_value = rough + 0.15
    nt.links.new(noise.outputs["Fac"], rr.inputs[0])
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    _MATS[name] = m
    return m


def mat_metal(name, color, rough=0.3, metal=0.95):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    b, nt = _principled(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    _MATS[name] = m
    return m


def mat_glow(name, color, strength=12.0):
    """Material emissivo. A forca e guardada para poder apagar (sprite 'desligado')."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    b, nt = _principled(m)
    b.inputs["Base Color"].default_value = (color[0] * 0.08, color[1] * 0.08, color[2] * 0.08, 1)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 0.3
    m["bs_glow"] = strength
    _MATS[name] = m
    return m


def mat_stripes(name, c1=(0.95, 0.62, 0.05), c2=(0.02, 0.02, 0.02), scale=10.0):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    b, nt = _principled(m)
    N = nt.nodes
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    add = N.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(sep.outputs[0], add.inputs[0])
    nt.links.new(sep.outputs[1], add.inputs[1])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = scale
    nt.links.new(add.outputs[0], mul.inputs[0])
    fr = N.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(mul.outputs[0], fr.inputs[0])
    gt = N.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    nt.links.new(fr.outputs[0], gt.inputs[0])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*c2, 1)
    mix.inputs[7].default_value = (*c1, 1)
    nt.links.new(gt.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    _MATS[name] = m
    return m


def mat_roof_green(name="roof_green", rough=0.5):
    """Teto da peca: verde puro (o jogo troca o verde pela cor da pintura da nave)."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    b, nt = _principled(m)
    b.inputs["Base Color"].default_value = (0.0, 0.85, 0.0, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.15
    _MATS[name] = m
    return m


def set_glow(on=True, factor=1.0):
    for m in bpy.data.materials:
        if "bs_glow" in m.keys():
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Emission Strength"].default_value = (m["bs_glow"] * factor) if on else 0.0


# ============================================================================ modelagem
def _link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def _ccw(poly):
    s = 0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += (x2 - x1) * (y2 + y1)
    return poly if s < 0 else list(reversed(poly))


def loft(name, bottom, top, z0, z1, mat, bevel=0.03, seg=2, tags=()):
    """Prisma com laterais inclinadas: poligono de baixo -> poligono de cima (mesmo numero de vertices)."""
    bottom = _ccw(bottom)
    top = _ccw(top)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, z0)) for x, y in bottom]
    vt = [bm.verts.new((x, y, z1)) for x, y in top]
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    n = len(bottom)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = _link(bpy.data.objects.new(name, me))
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = seg
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
        md.harden_normals = False
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def inset(poly, d):
    """Encolhe um poligono em direcao ao centroide (aprox. para lados inclinados)."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        vx, vy = x - cx, y - cy
        L = math.hypot(vx, vy) or 1
        out.append((x - vx / L * d, y - vy / L * d))
    return out


def offset_poly(poly, d, max_miter=3.0):
    """Desloca as arestas do poligono para DENTRO por d (com esquadria), funciona em poligonos concavos."""
    poly = _ccw(poly)
    n = len(poly)
    lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / L, dx / L  # normal a esquerda = para dentro (anti-horario)
        lines.append(((x1 + nx * d, y1 + ny * d), (dx / L, dy / L)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        ox, oy = poly[i]
        if abs(den) < 1e-6:
            q = p2
        else:
            t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
            q = (p1[0] + d1[0] * t, p1[1] + d1[1] * t)
        vx, vy = q[0] - ox, q[1] - oy
        L = math.hypot(vx, vy)
        if L > abs(d) * max_miter:
            q = (ox + vx / L * abs(d) * max_miter, oy + vy / L * abs(d) * max_miter)
        out.append(q)
    return out


def offset_ok(poly, d):
    """Deslocamento valido = nenhuma aresta inverteu de sentido (senao o poligono se cruzou)."""
    src = _ccw(poly)
    dst = offset_poly(poly, d)
    n = len(src)
    for i in range(n):
        ax, ay = src[(i + 1) % n][0] - src[i][0], src[(i + 1) % n][1] - src[i][1]
        bx, by = dst[(i + 1) % n][0] - dst[i][0], dst[(i + 1) % n][1] - dst[i][1]
        if ax * bx + ay * by <= 0:
            return False
    return True


def safe_offset(poly, d):
    while d > 0.004 and not offset_ok(poly, d):
        d *= 0.8
    return d


def plate(name, poly, z0, z1, mat, slope=0.06, bevel=0.018, seg=1, tags=()):
    """Placa com laterais chanfradas (facetas iluminadas/sombreadas) e quina viva."""
    slope = safe_offset(poly, slope)
    return loft(name, poly, offset_poly(poly, slope), z0, z1, mat, bevel, seg, tags)


def robust_offset(poly, d):
    """Deslocamento para dentro que funde arestas curtas que se inverteriam (degraus pequenos somem)."""
    src = _ccw(list(poly))
    for _ in range(len(poly)):
        if len(src) < 3:
            return None
        dst = offset_poly(src, d)
        n = len(src)
        bad = None
        for i in range(n):
            ax, ay = src[(i + 1) % n][0] - src[i][0], src[(i + 1) % n][1] - src[i][1]
            bx, by = dst[(i + 1) % n][0] - dst[i][0], dst[(i + 1) % n][1] - dst[i][1]
            if ax * bx + ay * by <= 0:
                bad = i
                break
        if bad is None:
            return dst
        j = (bad + 1) % n
        mid = ((src[bad][0] + src[j][0]) / 2, (src[bad][1] + src[j][1]) / 2)
        src = [p for k, p in enumerate(src) if k not in (bad, j)]
        src.insert(min(bad, len(src)), mid)
    return None


def shard(name, poly, z0, z1, mat, slope=0.08, groove=0.035, panel_h=0.03, panel_mat=None, tags=()):
    """Placa de blindagem com bisel duplo: base chanfrada + painel interno elevado (linha de painel)."""
    a = plate(name, poly, z0, z1, mat, slope=slope, tags=tags)
    d = slope + groove
    inner = robust_offset(poly, d)
    if inner is None or robust_offset(poly, d + 0.012) is None:
        return a, None  # placa fina demais para ter painel interno
    b = plate(name + "_pnl", inner, z1 - 0.004, z1 + panel_h, panel_mat or mat, slope=0.012, bevel=0.008, tags=tags)
    return a, b


def rpoly(cx, cy, sx, sy, rot_deg=0.0, chamfer=0.0):
    """Retangulo (opcionalmente com cantos chanfrados) girado em torno do centro."""
    hx, hy = sx / 2, sy / 2
    c = min(chamfer, hx * 0.9, hy * 0.9)
    if c > 0:
        pts = [(-hx + c, -hy), (hx - c, -hy), (hx, -hy + c), (hx, hy - c), (hx - c, hy), (-hx + c, hy), (-hx, hy - c),
               (-hx, -hy + c)]
    else:
        pts = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def rbox(name, cx, cy, sx, sy, z0, z1, mat, rot=0.0, chamfer=0.0, slope=0.0, bevel=0.008, tags=()):
    poly = rpoly(cx, cy, sx, sy, rot, chamfer)
    top = offset_poly(poly, slope) if slope else poly
    return loft(name, poly, top, z0, z1, mat, bevel, 1, tags)


def box(name, cx, cy, sx, sy, z0, z1, mat, bevel=0.02, slope=0.0, tags=()):
    poly = [(cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2), (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)]
    if slope:
        return loft(name, poly, inset(poly, slope), z0, z1, mat, bevel, 2, tags)
    return loft(name, poly, poly, z0, z1, mat, bevel, 2, tags)


def cyl(name, x, y, z, r, length, mat, axis="Y", verts=32, bevel=0.01, tags=(), r2=None, yaw=0.0):
    """Cilindro (ou tronco de cone se r2) deitado no eixo dado, centrado em (x,y,z). yaw gira o eixo Y no plano."""
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r if r2 is None else r2, depth=length,
                                    location=(x, y, z))
    ob = bpy.context.object
    ob.name = name
    if axis == "Y":
        ob.rotation_euler = (math.radians(-90), 0, math.radians(yaw))
    elif axis == "X":
        ob.rotation_euler = (0, math.radians(90), 0)
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
    ob.data.materials.append(mat)
    # suaviza so a lateral; as tampas (normal no eixo local Z) ficam planas, senao o mapa de normais vira cupula
    for p in ob.data.polygons:
        p.use_smooth = verts >= 16 and abs(p.normal.z) < 0.5
    for t in tags:
        ob[t] = True
    return ob


def cut(target, cutters, solver="EXACT"):
    """Recorta (booleana) os objetos cutters do alvo; o bisel e reaplicado depois do recorte.

    Os cortadores nao recebem tags, entao nao aparecem no render (show_only os esconde)."""
    if target is None:
        for c in cutters:
            bpy.data.objects.remove(c, do_unlink=True)
        return None
    bev = target.modifiers.get("bevel")
    params = None
    if bev:
        params = (bev.width, bev.segments, bev.limit_method, bev.angle_limit)
        target.modifiers.remove(bev)
    bpy.context.view_layer.update()
    for c in cutters:
        # o cortador vira filho do alvo: se o alvo se mover (recuo, montagem), o recorte vai junto
        c.parent = target
        c.matrix_parent_inverse = target.matrix_world.inverted()
        md = target.modifiers.new("cut_" + c.name, "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.object = c
        md.solver = solver
        c.hide_render = True
        c.display_type = "WIRE"
        for k in list(c.keys()):
            del c[k]
    if params:
        md = target.modifiers.new("bevel", "BEVEL")
        md.width, md.segments, md.limit_method, md.angle_limit = params
    return target


def torus(name, x, y, z, R, r, mat, tags=()):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64, minor_segments=12,
                                     location=(x, y, z))
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    for t in tags:
        ob[t] = True
    return ob


def bolts(prefix, pts, z, r, mat, tags=()):
    for i, (x, y) in enumerate(pts):
        cyl(f"{prefix}{i}", x, y, z, r, r * 0.8, mat, axis="Z", verts=10, bevel=r * 0.25, tags=tags)


def ring_points(cx, cy, R, n, a0=0.0):
    return [(cx + math.cos(a0 + i / n * math.tau) * R, cy + math.sin(a0 + i / n * math.tau) * R) for i in range(n)]


def text(name, s, x, y, z, size, mat, rot=0.0, tags=()):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = 0.004
    ob = _link(bpy.data.objects.new(name, cu))
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, math.radians(rot))
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


# ============================================================================ render
def objects_with(tag):
    return [o for o in bpy.context.scene.objects if o.get(tag)]


def show_only(tags):
    """Esconde do render tudo que nao tem pelo menos uma das tags (cameras/luzes ficam)."""
    for o in bpy.context.scene.objects:
        if o.type in ("CAMERA", "LIGHT"):
            continue
        o.hide_render = o.display_type == "WIRE" or not any(o.get(t) for t in tags)


def _normal_material():
    if "bs_normals" in bpy.data.materials:
        return bpy.data.materials["bs_normals"]
    m = bpy.data.materials.new("bs_normals")
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial")
    em = N.new("ShaderNodeEmission")
    geo = N.new("ShaderNodeNewGeometry")
    vm = N.new("ShaderNodeVectorMath")
    vm.operation = "MULTIPLY_ADD"
    vm.inputs[1].default_value = (0.5, 0.5, 0.5)
    vm.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(geo.outputs["Normal"], vm.inputs[0])
    nt.links.new(vm.outputs[0], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def render_to(path_png, final_size_px):
    sc = bpy.context.scene
    tmp = path_png + ".raw.png"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = Image.open(tmp).convert("RGBA")
    os.remove(tmp)
    im = im.resize(final_size_px, Image.LANCZOS)
    im.save(path_png)
    return im


def render_set(base, final_size_px, glow_halo=True, normals=True, off=True):
    """Renderiza <base>.png (aceso), <base>_off.png (apagado), <base>_normals.png e devolve as imagens."""
    sc = bpy.context.scene
    set_glow(True)
    beauty = render_to(base + ".png", final_size_px)
    out = {"on": beauty}
    if glow_halo:
        # passe so de emissao: apaga luzes/ambiente e soma um halo borrado (brilho)
        lights = [o for o in sc.objects if o.type == "LIGHT"]
        for l in lights:
            l.hide_render = True
        strength = sc.world.node_tree.nodes["Background"].inputs[1].default_value
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
        em = render_to(base + "_em.png", final_size_px)
        for l in lights:
            l.hide_render = False
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = strength
        os.remove(base + "_em.png")
        halo = em.filter(ImageFilter.GaussianBlur(max(1.5, B_HALO * final_size_px[0] / 64)))
        arr = np.asarray(beauty, dtype=np.float32)
        h = np.asarray(halo, dtype=np.float32)
        a = arr[..., 3:4] / 255.0
        add = h[..., :3] * (h[..., 3:4] / 255.0) * 0.55
        rgb = np.clip(arr[..., :3] + add * a, 0, 255)
        beauty = Image.fromarray(np.dstack([rgb, arr[..., 3]]).astype(np.uint8), "RGBA")
        beauty.save(base + ".png")
        out["on"] = beauty
    if off:
        set_glow(False)
        out["off"] = render_to(base + "_off.png", final_size_px)
        set_glow(True)
    if normals:
        vl = bpy.context.view_layer
        prev_vt = sc.view_settings.view_transform
        prev_s = sc.cycles.samples
        prev_dn = sc.cycles.use_denoising
        sc.view_settings.view_transform = "Raw"
        sc.cycles.samples = 16
        sc.cycles.use_denoising = False
        vl.material_override = _normal_material()
        n = render_to(base + "_normals.png", final_size_px)
        vl.material_override = None
        sc.view_settings.view_transform = prev_vt
        sc.cycles.samples = prev_s
        sc.cycles.use_denoising = prev_dn
        # garante o formato do jogo e alpha da silhueta
        arr = np.asarray(n, dtype=np.float32)
        arr[..., 3] = np.asarray(out["on"], dtype=np.float32)[..., 3]
        out["normals"] = Image.fromarray(arr.astype(np.uint8), "RGBA")
        out["normals"].save(base + "_normals.png")
    return out
