"""Renderizador generico dos sprites 3D do Bullet Strike.

    <venv-com-bpy>/bin/python tools/blender/render_part.py <id_curto> [--out DIR] [--quick] [--preview]
                                                          [--only turret,barrel,hull,cells]
    (fabricas: --only hull | machine | f1,f8 = so esses quadros da maquina;
     projeteis: --only he_m,nuclear_l = so esses itens)
    <id_curto> tambem pode ser o caminho de um arquivo .py de modelo fora de parts/ (testes); use --out.

Carrega o modelo de tools/blender/parts/<id_curto>.py (dicionario PART + funcoes de modelagem) e grava
em art3d/<id_curto>/ (ou --out) os PNGs no formato do jogo e um meta.json que o gerador do mod
(tools/build_mod.py) usa para posicionar tudo nas regras.

Tipos de peca (PART["kind"]):
  "gun"      torre de convés: head(M, T, phase) + barrel(M, L, T, phase); opcionais roof/floor
  "factory"  fabrica: floor(M, T), machine(M, T, phase), roof(M, T)
  "resource" municao: item(M, T) (uma unidade, centrada na origem, cabe num tile)
  "launcher" lancador de misseis de convés: head(M, T, phase) = casulo com as bocas VAZIAS +
             cell(M, look, T[, form, box]) = UM nariz carregado na origem; os niveis do rack sao compostos aqui;
             shutter(M, T, box) = persiana fechada (layouts *_inner); oc_glow(M, T) = brilho do overclock (opcional)
  "missiles" / "shells"  projeteis em voo (misseis 64 px/tile, granadas 128 px/tile): model(M, key, T, phase) =
             UM projetil, nariz +X, centrado, eixo X; emissivos (T, "lights"), mascara da faixa (T, "mask", so
             granadas); luz axissimetrica; meta.json no esquema de CONTRATOS secao 3 (render_projectiles)

Contrato completo e convencoes: tools/blender/STYLE.md.
"""

import importlib
import importlib.util
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import bs3d as B  # noqa: E402
import models as Mo  # noqa: E402

PX = B.PX
QUICK = False


# ============================================================================ utilidades
def samples(n):
    bpy.context.scene.cycles.samples = max(8, n // 4) if QUICK else n


def spec_entry(pid):
    spec = json.load(open(os.path.join(ROOT, "tools", "spec", "bullet_strike_spec.json"), encoding="utf-8"))
    for key in ("weapons", "factories", "resources"):
        for e in spec.get(key, []):
            if e["id"] == pid:
                return e
    return launcher_entry(pid)


def launcher_entry(pid):
    """Lancador de misseis no spec proprio (tools/spec/bullet_strike_missiles.json)."""
    spec = json.load(open(os.path.join(ROOT, "tools", "spec", "bullet_strike_missiles.json"), encoding="utf-8"))
    for e in spec.get("launchers", []):
        if e["id"] == pid:
            return e
    return {}


def fresh(accent, light_rig="default"):
    B.reset(light_rig)
    return Mo.mats(accent)


def _holdout_mat():
    """Material Holdout: tampa o que esta atras mas sai transparente (alpha 0) com film_transparent."""
    m = bpy.data.materials.get("__holdout_clear")
    if m is None:
        m = bpy.data.materials.new("__holdout_clear")
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    return m


def emission_pass(path, size, keep_tag=None, holdout=False):
    """Renderiza so a luz emitida (sem luzes nem ambiente). keep_tag: objetos sem a tag viram preto opaco
    (holdout=True: viram Holdout, tampam o brilho mas ficam transparentes)."""
    sc = bpy.context.scene
    lights = [o for o in sc.objects if o.type == "LIGHT"]
    for lo in lights:
        lo.hide_render = True
    bg = sc.world.node_tree.nodes["Background"].inputs[1]
    old = bg.default_value
    bg.default_value = 0.0
    swapped = {}
    if keep_tag:
        blk = _holdout_mat() if holdout else B.mat_metal("__holdout_black", (0, 0, 0), rough=1.0, metal=0.0)
        for o in sc.objects:
            if o.type == "MESH" and not o.hide_render and not o.get(keep_tag):
                swapped[o.name] = list(o.data.materials)
                o.data.materials.clear()
                o.data.materials.append(blk)
    im = B.render_to(path, size)
    for name, mats in swapped.items():
        o = sc.objects[name]
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)
    bg.default_value = old
    for lo in lights:
        lo.hide_render = False
    os.remove(path)
    return im


SHADOW_MARGIN = 8  # px de cada lado: a sombra fica maior que a torre e nao e cortada


def warn_empty(tag):
    """Avisa quando um objeto com a tag some depois das booleanas (malha vazia = recorte que engoliu a peca)."""
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.hide_render or not o.get(tag):
            continue
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        n = len(me.vertices)
        eo.to_mesh_clear()
        if n == 0:
            print(f"AVISO: '{o.name}' ficou vazio depois das booleanas (confira o poligono/recortes)")


def shadow_from(img, offset_px=5, blur_px=4, opacity=0.55, margin=SHADOW_MARGIN):
    """Sombra projetada (deslocada para baixo-direita, borrada) num quadro com margem extra."""
    a = np.asarray(img.split()[-1], dtype=np.float32)
    w, h = img.size
    W, H = w + 2 * margin, h + 2 * margin
    big = np.zeros((H, W), np.float32)
    big[margin + offset_px:margin + offset_px + h, margin + offset_px:margin + offset_px + w] = a[:H - margin - offset_px,
                                                                                                    :W - margin - offset_px]
    im = Image.fromarray(big.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur_px))
    sa = (np.asarray(im, dtype=np.float32) * opacity).astype(np.uint8)
    return Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), sa]), "RGBA")


def walls_png(w, h, color=(64, 67, 71)):
    """Moldura de parede de 7 px com sombra interna (formato vanilla, ver notes/08 secao 5.2)."""
    W, H = w * PX, h * PX
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, col in enumerate([(22, 22, 22), (33, 33, 33)] + [color] * 4 + [(40, 42, 44)]):
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=col + (255,))
    for k in range(7):
        a = int(115 * (1 - k / 7) ** 1.5)
        d.rectangle([7 + k, 7 + k, W - 8 - k, H - 8 - k], outline=(0, 0, 0, a))
    return im


def heat_composite(frame, heat_rgba, f):
    """Soma o brilho de calor (f = 0..1) sobre um quadro do cano, so onde o cano existe."""
    if f <= 0:
        return frame
    a = np.asarray(frame, dtype=np.float32)
    h = np.asarray(heat_rgba, dtype=np.float32)
    ha = h[..., 3:4] / 255.0 * f
    # puxa a cor para o laranja do calor (sem clarear demais armaduras claras) e soma um pouco de luz
    rgb = a[..., :3] * (1 - ha * 0.7) + h[..., :3] * ha * 0.7 + h[..., :3] * ha * 0.22
    out = np.dstack([np.clip(rgb, 0, 255), a[..., 3]])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ============================================================================ pecas comuns (cabeca e casco)
def _render_head(mod, out, P, only):
    """Cabeca da torre / casulo do lancador: turret*.png (+ animacao), turret_off, normais e sombra."""
    ts = P["turret_box"]
    accent = P.get("accent", "amber")
    tsz = (int(round(ts * PX)), int(round(ts * PX)))

    # ---------------------------------------------------------------- torre (com animacao opcional)
    tanim = P.get("turret_anim")
    nfr = tanim["frames"] if tanim else 1
    tnames, tnorms = [], []
    if not only or "turret" in only:
        for i in range(nfr):
            M = fresh(accent)
            B.camera(ts, ts, (0, 0))
            samples(64)
            mod.head(M, "head", i / nfr)
            B.show_only(["head"])
            if i == 0:
                warn_empty("head")
            base = os.path.join(out, "turret" if nfr == 1 else f"turret{i + 1}")
            res = B.render_set(base, tsz, glow_halo=True, normals=True, off=(i == 0))
            if i == 0:
                if nfr > 1:
                    os.replace(base + "_off.png", os.path.join(out, "turret_off.png"))
                shadow_from(res["on"]).save(os.path.join(out, "turret_shadow.png"))
                # normais do quadro "desligado" = normais do quadro 1
    for i in range(nfr):
        tnames.append("turret.png" if nfr == 1 else f"turret{i + 1}.png")
        tnorms.append("turret_normals.png" if nfr == 1 else f"turret{i + 1}_normals.png")
    tmeta = {"frames": tnames, "normals": tnorms, "interval": tanim["interval"] if tanim else 0,
             "off": "turret_off.png", "off_normals": tnorms[0], "shadow": "turret_shadow.png",
             "shadow_size": round(ts + 2 * SHADOW_MARGIN / PX, 4)}
    return tmeta, tnames + tnorms + ["turret_off.png", "turret_shadow.png"]


def _render_hull(mod, out, P, only):
    """Casco (teto verde, piso com assentos, paredes, luzes internas). Retorna (crew_pos, meta_hull, arquivos)."""
    W, H = P["size"]
    pv = P["pivot"]
    ts = P["turret_box"]
    accent = P.get("accent", "amber")
    pid = P["id"]
    crew_n = int(spec_entry(pid).get("crew") or P.get("crew", 1))
    if "crew_pos" in P:
        crew = [list(c) for c in P["crew_pos"]]
    else:
        from bsgen.common import crew_positions
        crew = [list(c) for c in crew_positions(W, H, crew_n, pv)]
    if not only or "hull" in only:
        M = fresh(accent)
        B.camera(W, H, (0, 0))
        samples(48)
        ring = P.get("ring_r", ts * 0.45)
        (getattr(mod, "roof", None) or (lambda M_, T: Mo.hull_roof(M_, W, H, pv, ring, T)))(M, "roof")
        (getattr(mod, "floor", None) or (lambda M_, T: Mo.hull_floor(M_, W, H, pv, ring, crew, T)))(M, "floor")
        size = (W * PX, H * PX)
        B.show_only(["roof"])
        B.render_set(os.path.join(out, "roof"), size, glow_halo=True, off=False)
        B.show_only(["floor"])
        fl = B.render_set(os.path.join(out, "floor"), size, glow_halo=True, off=False, normals=False)
        # piso opaco (o jogo espera alpha 255) e luzes do interior (lights_add, aditivo)
        base = Image.new("RGBA", size, (18, 19, 21, 255))
        base.alpha_composite(fl["on"])
        base.save(os.path.join(out, "floor.png"))
        em = emission_pass(os.path.join(out, "lights_raw.png"), size)
        glow = em.filter(ImageFilter.GaussianBlur(6))
        arr = np.asarray(glow, dtype=np.float32)
        rgb = np.clip(arr[..., :3] * (arr[..., 3:4] / 255.0) * 1.6, 0, 255)
        Image.fromarray(np.dstack([rgb, np.full(rgb.shape[:2], 255.0)]).astype(np.uint8), "RGBA").save(
            os.path.join(out, "lights.png"))
        walls_png(W, H).save(os.path.join(out, "walls.png"))
    hull = {"floor": "floor.png", "walls": "walls.png", "roof": "roof.png", "roof_normals": "roof_normals.png",
            "lights": "lights.png"}
    return crew, hull, ["floor.png", "walls.png", "roof.png", "roof_normals.png", "lights.png"]


# ============================================================================ armas (torres de convés)
def _render_charge_glow(mod, out, P, only):
    """Opcional (so com PART["charge_glow"] = {"frames": n, "interval": s, "color": rgb, "blend", "layer"} e
    charge_glow() no modelo): charge_glow1..n.png no quadro da torre, so a emissao dos objetos de
    charge_glow(M, T, phase) (phase = k/n, a carga sobe) com a cabeca como Holdout, mais halo (_oc_glow_sprite).
    --only turret ou charge."""
    cg = P["charge_glow"]
    ts = P["turret_box"]
    tsz = (int(round(ts * PX)), int(round(ts * PX)))
    names = [f"charge_glow{i + 1}.png" for i in range(int(cg.get("frames", 4)))]
    if not only or "turret" in only or "charge" in only:
        for i, nm in enumerate(names):
            M = fresh(P.get("accent", "amber"))
            B.camera(ts, ts, (0, 0))
            samples(32)
            mod.head(M, "head", 0.0)
            mod.charge_glow(M, "charge", (i + 1) / len(names))
            B.show_only(["charge", "head"])
            em = emission_pass(os.path.join(out, "charge_raw.png"), tsz, keep_tag="charge", holdout=True)
            _oc_glow_sprite(em).save(os.path.join(out, nm))
    # blend/layer (opcionais): como o gerador deve desenhar os quadros (ex.: "alpha", "above_barrels")
    extra = {k: cg[k] for k in ("blend", "layer") if k in cg}
    return {"frames": names, "interval": cg.get("interval", 0.125), "color": cg.get("color"), **extra}, names


def render_gun(mod, out, only):
    P = mod.PART
    W, H = P["size"]
    pv = P["pivot"]
    ts = P["turret_box"]
    accent = P.get("accent", "amber")
    bar = P["barrels"]
    meta = {"version": 1, "id": P["id"], "kind": "gun", "size": [W, H], "pivot": list(pv), "turret_size": ts,
            "collider": P.get("collider", round(ts * 0.45, 3))}
    files = []
    meta["turret"], tfiles = _render_head(mod, out, P, only)
    files += tfiles
    if P.get("charge_glow") and hasattr(mod, "charge_glow"):   # opcional (padrao desligado): brilho de carga
        meta["turret"]["charge_glow"], cfiles = _render_charge_glow(mod, out, P, only)
        files += cfiles

    # ---------------------------------------------------------------- cano(s)
    L, root, pad, bw = bar["length"], bar["root"], bar.get("pad", 0.3), bar["width"]
    top = bar.get("top_margin", 0.06)   # folga acima da boca (o bisel do freio nao e cortado)
    anim = bar.get("anim", "recoil")
    hlen = L + pad + top
    bsz = (int(round(bw * PX)), int(round(hlen * PX)))
    if anim == "spin":
        # nspin+1 quadros de giro (fases 1/(n+1) .. 1 = volta completa entre canos) todos "quentes", e o
        # repouso frio separado: em tiro continuo o jogo reinicia a animacao a cada tiro e o repouso nunca aparece,
        # entao o calor nao pisca
        nspin = bar.get("spin_frames", 3) + 1
        names = [f"barrel_spin{i + 1}.png" for i in range(nspin)] + ["barrel1.png"]
        norms = [f"barrel_spin_normals{i + 1}.png" for i in range(nspin)] + ["barrel_normals1.png"]
        phases = [(i + 1) / nspin for i in range(nspin)] + [0.0]
        recoils = [bar.get("spin_recoil", 0.0)] * nspin + [0.0]
        hl = list(bar.get("heat", [])) or [0.0]
        heats = [hl[min(i, len(hl) - 1)] for i in range(nspin)] + [0.0]
    elif anim == "recoil":
        rec = list(bar["recoil"])
        heat = list(bar.get("heat", []))
        n = max(len(rec), len(heat))
        rec += [0.0] * (n - len(rec))
        heat += [0.0] * (n - len(heat))
        names = [f"barrel{i + 2}.png" for i in range(n)] + ["barrel1.png"]
        norms = [f"barrel_normals{i + 2}.png" if rec[i] else "barrel_normals1.png" for i in range(n)] + \
                ["barrel_normals1.png"]
        phases = [0.0] * (n + 1)
        recoils = rec + [0.0]
        heats = heat + [0.0]
    else:  # estatico
        names, norms, phases, recoils, heats = ["barrel1.png"], ["barrel_normals1.png"], [0.0], [0.0], [0.0]
    if not only or "barrel" in only:
        # cada fase de giro e um modelo novo; recuo so desloca os objetos
        done_phase = {}
        for k, (nm, nn, ph, r, ht) in enumerate(zip(names, norms, phases, recoils, heats)):
            key = round(ph, 4)
            if key not in done_phase:
                M = fresh(accent)
                B.camera(bw, hlen, (0, (L + top - pad) / 2))
                samples(48)
                mod.barrel(M, L, "barrel", ph)
                objs = B.objects_with("barrel")
                warn_empty("barrel")
                done_phase = {key: {o.name: o.location.y for o in objs}}
            base_y = done_phase[key]
            for o in B.objects_with("barrel"):
                o.location.y = base_y[o.name] - r
            B.show_only(["barrel"])
            stem = os.path.join(out, nm[:-4])
            res = B.render_set(stem, bsz, glow_halo=False, normals=True, off=False)
            # normais: quadros sem recuo reaproveitam as do repouso (barrel_normals1)
            if nn == "barrel_normals1.png" and nm != "barrel1.png":
                os.remove(stem + "_normals.png")
            else:
                os.replace(stem + "_normals.png", os.path.join(out, nn))
            if ht > 0 and B.objects_with("hot"):
                heat_composite(res["on"], _heat_layer(stem, bsz, L, bar.get("heat_color", HEAT_COLOR),
                                                      bar.get("heat_ramp")), ht).save(stem + ".png")
            for o in B.objects_with("barrel"):
                o.location.y = base_y[o.name]
    meta["barrel"] = {
        "ys": list(bar["ys"]), "root": root, "length": L, "pad": pad, "sprite_w": bw, "sprite_len": hlen,
        "center": round(root + (L + top - pad) / 2, 4), "muzzle": round(root + L - 0.05, 4), "anim": anim,
        "frames": names[:-1] + [names[-1]] if anim != "static" else names, "normals": norms,
        "interval": bar.get("interval", 0.05 if anim == "spin" else 0.06), "rest": "barrel1.png",
        "rest_normals": "barrel_normals1.png",
    }
    files += sorted(set(names + norms))

    # ---------------------------------------------------------------- casco (teto, piso, paredes, luzes)
    meta["crew_pos"], meta["hull"], hfiles = _render_hull(mod, out, P, only)
    files += hfiles

    # luzes dinamicas: coordenadas da cabeca (x direita, y frente) -> torre (x frente, y direita)
    meta["lights"] = [{"loc": [l["at"][1], l["at"][0]], "size": l.get("size", 1.2), "color": l.get("color", [255, 120, 30]),
                       "z": l.get("z", 1.0)} for l in P.get("lights", [])]
    meta["preview_pattern"] = P.get("preview_pattern", "alternate" if len(bar["ys"]) > 1 else "single")
    meta["accent"] = accent if isinstance(accent, str) else "amber"
    meta["preview_fx"] = P.get("preview_fx", "plasma" if meta["accent"] == "cyan" else "fire")
    meta["files"] = sorted(set(files))
    return meta


HEAT_COLOR = (1.0, 0.13, 0.015)  # laranja de metal quente (padrao); plasma usa heat_color ciano


def _heat_layer(stem, size, L, color=HEAT_COLOR, heat_ramp=None):
    """Brilho de calor das partes marcadas 'hot', mais forte perto da boca. heat_ramp (opcional,
    PART["barrels"]["heat_ramp"] = (inicio, largura) em fracao da altura a partir da base; padrao (0.35, 0.55)):
    as bobinas PEM usam uma rampa curta, brilho eletrico por igual na bobina e nao calor so perto da boca."""
    r0, rw = heat_ramp or (0.35, 0.55)
    heat_m = B.mat_glow("__heat", tuple(color), 1.25)
    sc = bpy.context.scene
    hot = [o for o in sc.objects if o.get("hot") and not o.hide_render]
    keep = {o.name: list(o.data.materials) for o in hot}
    for o in hot:
        o.data.materials.clear()
        o.data.materials.append(heat_m)
    em = emission_pass(stem + "_heatraw.png", size, keep_tag="hot")
    for o in hot:
        o.data.materials.clear()
        for m in keep[o.name]:
            o.data.materials.append(m)
    arr = np.asarray(em, dtype=np.float32).copy()
    hpx = size[1]
    ys = np.linspace(1.0, 0.0, hpx)[:, None]           # 1 = topo da imagem (boca)
    ramp = np.clip((ys - r0) / rw, 0, 1) ** 1.4  # (h, 1)
    lum = arr[..., :3].max(axis=2, keepdims=True) / 255.0
    arr[..., 3] = np.clip(lum[..., 0] * 1.4, 0, 1) * ramp * 255
    img = Image.fromarray(arr.astype(np.uint8), "RGBA")
    halo = img.filter(ImageFilter.GaussianBlur(2))
    return Image.alpha_composite(halo, img)


# ============================================================================ lancadores de misseis
def _oc_glow_sprite(em, blur_px=3.0, gain=1.1):
    """turret_oc.png: emissao + halo como LUZ. O desfoque e feito na cor premultiplicada (a borda transparente e
    preta no PNG: desfocar a cor crua escurecia o halo) e a opacidade do halo segue o brilho dele."""
    a = np.asarray(em, dtype=np.float32) / 255.0
    al = a[..., 3:4]
    pm = a[..., :3] * al

    def blur(arr):
        im = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "RGB")
        return np.asarray(im.filter(ImageFilter.GaussianBlur(blur_px)), dtype=np.float32) / 255.0
    hc = blur(pm) * gain
    ha = np.clip(hc.max(axis=2, keepdims=True) * 1.6, 0, 1)
    out_pm = pm + hc * (1 - al)
    out_a = al + ha * (1 - al)
    rgb = np.where(out_a > 1e-4, out_pm / np.maximum(out_a, 1e-4), 0)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, out_a * 255]).astype(np.uint8), "RGBA")


def render_launcher(mod, out, only):
    """Lancador de misseis de convés (STYLE.md secao 8).

    head(M, T, phase): o casulo girando, com as bocas dos tubos VAZIAS (camada roof_doodads).
    cell(M, look, T): UM nariz de missil carregado, centrado na origem, inclinado como o casulo.
    As posicoes das celulas e a ordem de enchimento vem de tools/launcher_layout.py com os layouts por modo do
    spec (launchers[].modes[].layout); cada nivel do rack (cells_<tipo>_p<casulo>_<n>.png, no retangulo do casulo
    recortado do quadro da torre, launcher_layout.overlay_rect) e composto aqui colando o nariz renderizado nas
    primeiras n unidades do casulo."""
    from launcher_layout import cell_layout, overlay_rect
    P = mod.PART
    W, H = P["size"]
    ts = P["turret_box"]
    accent = P.get("accent", "amber")
    L = launcher_entry(P["id"])
    if not L:
        raise SystemExit(f"{P['id']}: lancador nao existe em tools/spec/bullet_strike_missiles.json")
    pm = L["art"]["part_meta"]
    if list(P["size"]) != list(L["size"]):
        raise SystemExit(f"{P['id']}: PART size {P['size']} difere do spec {L['size']}")
    meta = {"version": 1, "id": P["id"], "kind": "launcher", "size": [W, H], "pivot": list(P["pivot"]),
            "turret_size": ts, "collider": P.get("collider", pm.get("collider", round(ts * 0.45, 3)))}
    files = []
    meta["turret"], tfiles = _render_head(mod, out, P, only)
    files += tfiles
    cells = P.get("cells") or pm["cells"]
    T = int(round(ts * PX))
    cw = cells.get("tube_r", 0.09) * 5                     # quadro do nariz (tiles); overlay_rect usa o mesmo
    cpx = max(8, int(round(cw * PX)))
    looks = P.get("looks", pm.get("looks", []))
    noses = {}
    modes = {}
    tmp = []

    def piece(key, fn_draw, tag, wh):
        """Renderiza uma peca solta (nariz / persiana) num quadro wh (tiles) e devolve (img, normais, px)."""
        stem = os.path.join(out, key)
        px = (max(8, int(round(wh[0] * PX))), max(8, int(round(wh[1] * PX))))
        if not only or "cells" in only:
            M = fresh(accent)
            B.camera(wh[0], wh[1], (0, 0))
            samples(48)
            fn_draw(M)
            B.show_only([tag])
            B.render_set(stem, px, glow_halo=False, normals=True, off=False)
        tmp.append(stem)
        if not os.path.exists(stem + ".png"):
            return None
        return Image.open(stem + ".png").convert("RGBA"), Image.open(stem + "_normals.png").convert("RGBA"), px

    def paste(cv, nv, pc, pos, origin=None):
        """Cola a peca centrada em pos (coordenadas da torre); origin = canto do recorte do casulo no quadro da
        torre (sobreposicoes do rack: a peca tem que caber inteira no recorte)."""
        img, nrm, px = pc
        x, y = int(round(T / 2 + pos[1] * PX - px[0] / 2)), int(round(T / 2 - pos[0] * PX - px[1] / 2))
        if origin is not None:
            x, y = x - origin[0], y - origin[1]
            if x < 0 or y < 0 or x + px[0] > cv.size[0] or y + px[1] > cv.size[1]:
                raise SystemExit(f"{P['id']}: nariz fora do retangulo do casulo (launcher_layout.overlay_rect)")
        cv.alpha_composite(img, (x, y))
        nv.alpha_composite(nrm, (x, y))

    for m in L["modes"]:
        look = m["missile_type"]
        if look not in looks:
            raise SystemExit(f"{P['id']}: PART['looks'] precisa cobrir o modo {look}")
        lay = cell_layout(cells, m["layout"], m["rack_units"], f"{P['id']}/{look}")
        form = lay["form"]
        if form == "tube":
            key = (look, form)
            if key not in noses:
                noses[key] = piece(f"cell_{look}", lambda M: mod.cell(M, look, "cell"), "cell", (cw, cw))
        else:
            # nariz "heavy" (fileira inteira, calibre duplo) ou "torpedo" (face do casulo): cell(..., form, box)
            box = lay["units"][0]["box"]
            key = (look, form)
            if key not in noses:
                fr = (box[0] * 1.15, box[1] * 1.15)
                noses[key] = piece(f"cell_{look}_{form}",
                                   lambda M: mod.cell(M, look, "cell", form=form, box=box), "cell", fr)
        nose = noses[key]
        overlays = []
        for pod in lay["pods"]:
            a, b = pod["range"]
            fn = [f"cells_{look}_p{pod['index']}_{j}.png" for j in range(b - a + 1)]
            nn = [f"cells_{look}_p{pod['index']}_{j}_normals.png" for j in range(b - a + 1)]
            # quadro do nivel = retangulo do casulo no quadro da torre (STYLE.md 8.1), nao a torre inteira
            rect = overlay_rect(lay["units"][a:b], lay["tube_r"], ts)
            rw, rh = rect[2] - rect[0], rect[3] - rect[1]
            if nose:
                for j in range(b - a + 1):
                    cv = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
                    nv = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
                    for u in lay["units"][a:a + j]:
                        for t in (u["tubes"] if form == "tube" else [u["pos"]]):
                            paste(cv, nv, nose, t, origin=(rect[0], rect[1]))
                    cv.save(os.path.join(out, fn[j]))
                    nv.save(os.path.join(out, nn[j]))
            overlays.append({"range": [a, b], "files": fn, "normals": nn, "rect": rect})
            files += fn + nn
        modes[look] = {"units": [u["pos"] for u in lay["units"]], "unit_pods": [u["pod"] for u in lay["units"]],
                       "tubes": [u["tubes"] for u in lay["units"]], "overlays": overlays}
        if lay["shutters"]:
            # casulos sem celula neste modo (Iara: casulos externos): persiana fechada, uma imagem por modo
            if not hasattr(mod, "shutter"):
                raise SystemExit(f"{P['id']}: o layout {m['layout']} precisa de shutter(M, T, box) no modelo")
            sbox = lay["shutters"][0]["box"]
            sp = piece(f"shutter_{look}", lambda M: mod.shutter(M, "shutter", box=sbox), "shutter",
                       (sbox[0] * 1.15, sbox[1] * 1.15))
            sf, sn = f"shutters_{look}.png", f"shutters_{look}_normals.png"
            if sp:
                cv = Image.new("RGBA", (T, T), (0, 0, 0, 0))
                nv = Image.new("RGBA", (T, T), (0, 0, 0, 0))
                for sh in lay["shutters"]:
                    paste(cv, nv, sp, sh["center"])
                cv.save(os.path.join(out, sf))
                nv.save(os.path.join(out, sn))
            modes[look]["shutters"] = {"file": sf, "normals": sn, "pods": [sh["pod"] for sh in lay["shutters"]]}
            files += [sf, sn]
    for stem in tmp:
        for suf in (".png", "_normals.png"):
            if os.path.exists(stem + suf):
                os.remove(stem + suf)
    if P.get("oc_glow") and hasattr(mod, "oc_glow"):
        # brilho do overclock (olho/colar em brasa) no quadro da torre, so emissao + halo (roof_turrets)
        if not only or "turret" in only:
            M = fresh(accent)
            B.camera(ts, ts, (0, 0))
            samples(32)
            mod.head(M, "head", 0.0)
            mod.oc_glow(M, "oc")
            # PART["oc_occlude"]: a cabeca entra como Holdout (tampa o brilho que fica atras dela, sem cor)
            occl = bool(P.get("oc_occlude"))
            B.show_only(["oc", "head"] if occl else ["oc"])
            warn_empty("oc")
            for o in B.objects_with("oc"):
                if o.type == "MESH" and not any(m is not None and "bs_glow" in m.keys() for m in o.data.materials):
                    print(f"AVISO: '{o.name}' (tag oc) nao e emissivo: sai preto por cima da torre (STYLE.md 9)")
            em = emission_pass(os.path.join(out, "oc_raw.png"), (T, T), keep_tag="oc" if occl else None,
                               holdout=occl)
            _oc_glow_sprite(em).save(os.path.join(out, "turret_oc.png"))
        meta["turret"]["oc_glow"] = "turret_oc.png"
        files.append("turret_oc.png")
    meta["modes"] = modes
    meta["crew_pos"], meta["hull"], hfiles = _render_hull(mod, out, P, only)
    files += hfiles
    # cabeca (x direita, y frente) -> torre (x frente, y direita)
    meta["backblast"] = [[b[1], b[0]] for b in P.get("backblast", pm.get("backblast", []))]
    meta["lights"] = [{"loc": [l["at"][1], l["at"][0]], "size": l.get("size", 1.2), "color": l.get("color", [255, 120, 30]),
                       "z": l.get("z", 1.0)} for l in P.get("lights", [])]
    meta["preview_pattern"] = P.get("preview_pattern", "ripple")
    meta["files"] = sorted(set(files))
    return meta


# ============================================================================ fabricas
def render_factory(mod, out, only):
    P = mod.PART
    W, H = P["size"]
    accent = P.get("accent", "amber")
    size = (W * PX, H * PX)
    nfr = P.get("machine_frames", 4)
    meta = {"version": 1, "id": P["id"], "kind": "factory", "size": [W, H]}
    files = []
    M = fresh(accent)
    B.camera(W, H, (0, 0))
    samples(48)
    # --only hull (teto, chao e paredes) / machine (todos os quadros) / f1,f8 (so esses quadros da maquina)
    sel = {int(t[1:]) for t in only if t[:1] == "f" and t[1:].isdigit()}
    if not only or "hull" in only:
        mod.floor(M, "floor")
        mod.roof(M, "roof")
        warn_empty("roof")
        warn_empty("floor")
        B.show_only(["roof"])
        B.render_set(os.path.join(out, "roof"), size, glow_halo=True, off=False)
        B.show_only(["floor"])
        fl = B.render_set(os.path.join(out, "floor"), size, glow_halo=True, off=False, normals=False)
        base = Image.new("RGBA", size, (18, 19, 21, 255))
        base.alpha_composite(fl["on"])
        base.save(os.path.join(out, "floor.png"))
        walls_png(W, H).save(os.path.join(out, "walls.png"))
    files += ["roof.png", "roof_normals.png", "floor.png", "walls.png"]
    names = []
    for i in range(nfr):
        names.append(f"machine_on{i + 1}.png")
        if only and "machine" not in only and (i + 1) not in sel:
            continue
        M = fresh(accent)
        B.camera(W, H, (0, 0))
        samples(48)
        mod.machine(M, "machine", i / nfr)
        if i == 0:
            warn_empty("machine")
        B.show_only(["machine"])
        stem = os.path.join(out, f"machine_on{i + 1}")
        B.render_set(stem, size, glow_halo=True, off=(i == 0), normals=False)
        if i == 0:
            os.replace(stem + "_off.png", os.path.join(out, "machine_off.png"))
        if i == 0:
            em = emission_pass(os.path.join(out, "lights_raw.png"), size)
            glow = em.filter(ImageFilter.GaussianBlur(6))
            arr = np.asarray(glow, dtype=np.float32)
            rgb = np.clip(arr[..., :3] * (arr[..., 3:4] / 255.0) * 1.6, 0, 255)
            Image.fromarray(np.dstack([rgb, np.full(rgb.shape[:2], 255.0)]).astype(np.uint8), "RGBA").save(
                os.path.join(out, "lights.png"))
    files += names + ["machine_off.png", "lights.png"]
    meta["machine"] = {"frames": names, "off": "machine_off.png", "interval": P.get("machine_interval", 0.12),
                       "size": [W, H], "offset": [0, 0]}
    meta["hull"] = {"floor": "floor.png", "walls": "walls.png", "roof": "roof.png", "roof_normals": "roof_normals.png",
                    "lights": "lights.png"}
    meta["files"] = sorted(set(files))
    return meta


# ============================================================================ municoes (recursos)
STACK_LAYOUT = {  # posicoes (x, y, z) dentro de um tile para k unidades empilhadas
    1: [(0, 0, 0)],
    2: [(-0.2, 0, 0), (0.2, 0, 0)],
    3: [(-0.2, -0.17, 0), (0.2, -0.17, 0), (0, 0.19, 0)],
    4: [(-0.2, -0.2, 0), (0.2, -0.2, 0), (-0.2, 0.2, 0), (0.2, 0.2, 0)],
    5: [(-0.2, -0.2, 0), (0.2, -0.2, 0), (-0.2, 0.2, 0), (0.2, 0.2, 0), (0, 0, 0.16)],
    6: [(-0.2, -0.2, 0), (0.2, -0.2, 0), (-0.2, 0.2, 0), (0.2, 0.2, 0), (-0.1, 0, 0.16), (0.1, 0, 0.16)],
}
# pilhas 7..10 (spec 2.0 render_kinds.resource.stack_layout_7_10.missile_charges: carga comprida deitada em X,
# 2 camadas de 5; unit_scale 0,5 e stack_rot 90 +-2 = STACK_ROT_CHARGES). STACK_LAYOUT_CHARGES = o leiaute
# inteiro 1..10 do spec (PART["stack_layout"] = "charges"). Os itens 2.0 aprovados (art3d/bs_msl_*) trazem o proprio
# stack_layout (parts/_bs2_itens_helpers.py MSL_LAYOUT, desvio consciente registrado la): nada muda para eles.
_ROW0 = [(-0.28, 0.0, 0.0), (-0.14, 0.0, 0.0), (0.0, 0.0, 0.0), (0.14, 0.0, 0.0), (0.28, 0.0, 0.0)]
_ROW1 = [(-0.21, 0.0, 0.14), (-0.07, 0.0, 0.14), (0.07, 0.0, 0.14), (0.21, 0.0, 0.14), (0.35, 0.0, 0.14)]
STACK_LAYOUT_CHARGES = {k: (_ROW0 + _ROW1)[:k] for k in range(1, 11)}
STACK_ROT_CHARGES = [90, 92, 88, 91, 89, 90, 92, 88, 91, 89]
for _k in range(7, 11):
    STACK_LAYOUT[_k] = STACK_LAYOUT_CHARGES[_k]


def _place_item(mod, M, at, scale, rot_deg, name):
    """Cria uma unidade (mod.item) presa a um Empty e posiciona/escala/gira o conjunto."""
    sc = bpy.context.scene
    before = set(o.name for o in sc.objects)
    mod.item(M, "item")
    emp = bpy.data.objects.new(name, None)
    sc.collection.objects.link(emp)
    for o in [o for o in sc.objects if o.name not in before and o.parent is None and o is not emp]:
        o.parent = emp
    emp.location = at
    emp.scale = (scale, scale, scale)
    emp.rotation_euler.z = math.radians(rot_deg)
    return emp


def render_resource(mod, out, only):
    P = mod.PART
    accent = P.get("accent", "amber")
    stack = int(spec_entry(P["id"]).get("max_stack_size") or P.get("max_stack", 4))
    meta = {"version": 1, "id": P["id"], "kind": "resource", "stack": stack}
    files = []
    unit = P.get("unit_scale", 0.42)  # tamanho de uma unidade dentro da pilha (tiles)
    for k in range(1, stack + 1):
        M = fresh(accent)
        B.camera(1, 1, (0, 0))
        samples(48)
        sl = P.get("stack_layout", STACK_LAYOUT)
        if sl == "charges":
            sl = STACK_LAYOUT_CHARGES
        lay = sl.get(k) or sl.get(str(k)) or STACK_LAYOUT.get(k) or STACK_LAYOUT[max(STACK_LAYOUT)]
        rots = P.get("stack_rot", [0, 8, -6, 4, -10, 6])
        for j, (x, y, z) in enumerate(lay):
            rot = rots[j % len(rots)]                 # listas de 6 (os itens 2.0) ficam iguais a antes
            _place_item(mod, M, (x, y, z), unit, rot, f"unit{j}")
        B.show_only(["item"])
        B.render_set(os.path.join(out, f"stack_{k}"), (PX, PX), glow_halo=True, off=False, normals=False)
        files.append(f"stack_{k}.png")
    # icone e silhueta (unidade grande, icon_scale)
    M = fresh(accent)
    B.camera(1, 1, (0, 0))
    samples(64)
    _place_item(mod, M, (0, 0, 0), P.get("icon_scale", 0.8), P.get("icon_rot", 0), "unit_icon")
    warn_empty("item")
    B.show_only(["item"])
    res = B.render_set(os.path.join(out, "icon_src"), (PX, PX), glow_halo=True, off=False, normals=False)
    res["on"].save(os.path.join(out, "icon.png"))
    os.remove(os.path.join(out, "icon_src.png"))
    big = B.render_set(os.path.join(out, "overlay_src"), (128, 128), glow_halo=False, off=False, normals=False)
    # silhueta branca com halo suave, como os overlay.png vanilla (resources/bullet/overlay.png)
    import art3d as A3
    A3.overlay_glow(big["on"].split()[-1]).save(os.path.join(out, "overlay.png"))
    meta["overlay_glow"] = True
    os.remove(os.path.join(out, "overlay_src.png"))
    # unidade solta (nugget, o que o tripulante carrega) com normais: do tamanho de uma unidade da pilha
    # (unit_scale), como as pecas vanilla; com icon_scale o carregador crescia ao ser pego do deposito
    M = fresh(accent)
    B.camera(1, 1, (0, 0))
    samples(64)
    _place_item(mod, M, (0, 0, 0), unit, P.get("icon_rot", 0), "unit_nugget")
    B.show_only(["item"])
    B.render_set(os.path.join(out, "nugget"), (PX, PX), glow_halo=True, off=False, normals=True)
    meta["nugget_scale"] = unit
    files += ["nugget.png", "nugget_normals.png", "icon.png", "overlay.png"]
    meta["files"] = sorted(set(files))
    return meta


# ============================================================================ projeteis (misseis e granadas)
PROJ_KINDS = ("missiles", "shells")
PROJ_PPT = {"missiles": 64, "shells": 128}          # px por tile do sprite (CONTRATOS secao 3)
PROJ_FILES = {                                       # nomes dos PNGs por tipo (CONTRATOS secao 3)
    "missiles": {"file": "msl_{k}.png", "normals": "msl_{k}_normals.png", "lights": "msl_{k}_lights.png",
                 "mask": None},
    "shells": {"file": "bs_shell_{k}.png", "normals": "bs_shell_{k}_normals.png", "lights": "bs_shell_{k}_lights.png",
               "mask": "bs_shell_band_{k}.png"},
}


def _mask_mat():
    """Emissao branca pura (forca 1 = 255 na vista Standard) para a mascara da faixa."""
    m = bpy.data.materials.get("__mask_white")
    if m is None:
        m = bpy.data.materials.new("__mask_white")
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1, 1, 1, 1)
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    return m


def _mask_pass(path, size):
    """Mascara da faixa: os objetos (T, "mask") saem brancos, o resto do projetil vira Holdout (tampa a faixa onde
    ela fica atras de outra peca e sai transparente). RGB = branco em todo o quadro (sem franja escura no filtro
    do jogo); alfa = cobertura. None quando nao ha objeto de mascara visivel."""
    sc = bpy.context.scene
    masks = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and o.get("mask")]
    if not masks:
        return None
    keep = {o.name: list(o.data.materials) for o in masks}
    white = _mask_mat()
    for o in masks:
        o.data.materials.clear()
        o.data.materials.append(white)
    em = emission_pass(path, size, keep_tag="mask", holdout=True)
    for o in masks:
        o.data.materials.clear()
        for m in keep[o.name]:
            o.data.materials.append(m)
    arr = np.asarray(em, dtype=np.uint8).copy()
    arr[..., :3] = 255
    return Image.fromarray(arr, "RGBA")


def _warn_lights(tag="lights"):
    """Objetos marcados 'lights' que nao sao emissivos saem pretos no atlas (e nao somam nada no jogo)."""
    for o in B.objects_with(tag):
        if o.type == "MESH" and not o.hide_render and \
                not any(m is not None and "bs_glow" in m.keys() for m in o.data.materials):
            print(f"AVISO: '{o.name}' (tag {tag}) nao e emissivo: sai preto no atlas de luzes (STYLE.md 11)")


def render_projectiles(mod, out, only):
    """Folhas de sprite de projeteis (STYLE.md 8.4, 10 e 11; esquema em CONTRATOS secao 3).

    Por item de PART["items"] (filtro --only k1,k2):
      difuso com os emissivos APAGADOS (LEDs = lentes escuras), 48 amostras (--quick: 12), luz axissimetrica;
      normais com o alfa do difuso;
      atlas de luzes (so quando frames > 1): um quadro por fase k/n (a cena e refeita com phase = k/n), so a
      emissao dos objetos (T, "lights") com o resto em Holdout + halo suave (_oc_glow_sprite), quadros lado a lado
      (n*w x h, per_row = n);
      granadas com "mask": mascara da faixa (objetos (T, "mask")) em branco sobre transparente."""
    P = mod.PART
    kind = P["kind"]
    ppt = P.get("px_per_tile", PROJ_PPT[kind])
    if ppt != PROJ_PPT[kind]:
        raise SystemExit(f"{P['id']}: px_per_tile {ppt} difere do contrato ({PROJ_PPT[kind]} para '{kind}')")
    accent = P.get("accent", "amber")
    names = PROJ_FILES[kind]
    keys = list(P["items"])
    if only:
        bad = sorted(set(only) - set(keys))
        if bad:
            raise SystemExit(f"{P['id']}: --only com itens que nao existem: {bad} (itens: {', '.join(keys)})")
        keys = [k for k in keys if k in only]
    halo = P.get("halo_px", 2.5 * ppt / 64)
    items, files = {}, []
    for key in keys:
        it = P["items"][key]
        t0 = time.time()
        L, W = it["canvas_tiles"]
        px = (int(round(L * ppt)), int(round(W * ppt)))
        n = int(it.get("frames", 1))
        if it.get("mask") and not names["mask"]:
            raise SystemExit(f"{P['id']}/{key}: mascara de faixa so existe em granadas (kind 'shells')")
        f_diff, f_norm = names["file"].format(k=key), names["normals"].format(k=key)
        # ---- difuso (emissivos apagados) + normais + mascara: a mesma cena
        M = fresh(accent, "axial")
        B.camera(L, W, (0, 0), px=ppt)
        samples(48)
        mod.model(M, key, "body", 0.0)
        B.show_only(["body"])
        warn_empty("body")
        _warn_lights()
        B.render_set(os.path.join(out, f_diff[:-4]), px, glow_halo=False, normals=True, off=False, glow=False)
        files += [f_diff, f_norm]
        f_mask = None
        if it.get("mask"):
            f_mask = names["mask"].format(k=key)
            mk = _mask_pass(os.path.join(out, f_mask[:-4] + "_raw.png"), px)
            if mk is None:
                raise SystemExit(f"{P['id']}/{key}: 'mask' ligado mas nenhum objeto (T, 'mask') no modelo")
            mk.save(os.path.join(out, f_mask))
            files.append(f_mask)
        # ---- atlas de luzes: um quadro por fase
        lights = None
        if n > 1:
            atlas = Image.new("RGBA", (n * px[0], px[1]), (0, 0, 0, 0))
            f_lt = names["lights"].format(k=key)
            for k in range(n):
                if k:
                    M = fresh(accent, "axial")
                    B.camera(L, W, (0, 0), px=ppt)
                    mod.model(M, key, "body", k / n)
                    B.show_only(["body"])
                samples(32)
                B.set_glow(True)
                em = emission_pass(os.path.join(out, f_lt[:-4] + f"_raw{k}.png"), px, keep_tag="lights", holdout=True)
                atlas.alpha_composite(_oc_glow_sprite(em, blur_px=halo, gain=1.1), (k * px[0], 0))
            atlas.save(os.path.join(out, f_lt))
            files.append(f_lt)
            lights = {"file": f_lt, "frames": n, "frame_px": [px[0], px[1]], "per_row": n,
                      "fps": it.get("fps", 0), "wrap": it.get("wrap")}
        items[key] = {"size": [L, W], "px": [px[0], px[1]], "file": f_diff, "normals": f_norm, "lights": lights,
                      "mask": f_mask, "nozzle": [it.get("nozzle_x", round(-L / 2, 4)), 0],
                      "anchors": {a: list(v) for a, v in it.get("anchors", {}).items()}}
        print(f"item {key}: {px[0]}x{px[1]} px, {n} quadro(s) de luz, {time.time() - t0:.1f} s")
    return {"version": 1, "kind": kind, "id": P["id"], "px_per_tile": ppt, "items": items,
            "files": sorted(set(files))}


# ============================================================================ principal
def main():
    global QUICK
    args = sys.argv[1:]
    short = args[0]
    QUICK = "--quick" in args
    src = None
    if short.endswith(".py") and os.path.isfile(short):
        # modelo fora de parts/ (testes do kit): carrega pelo caminho
        src = os.path.abspath(short)
        short = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(ROOT, "art3d", short)
    if "--out" in args:
        out = args[args.index("--out") + 1]
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else set()
    os.makedirs(out, exist_ok=True)
    if src:
        spec = importlib.util.spec_from_file_location(f"bs_ext_part_{short}", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        mod = importlib.import_module(f"parts.{short}")
    kind = mod.PART["kind"]
    fn = {"gun": render_gun, "factory": render_factory, "resource": render_resource,
          "launcher": render_launcher, "missiles": render_projectiles, "shells": render_projectiles}[kind]
    meta = fn(mod, out, only)
    mp = os.path.join(out, "meta.json")
    if kind in PROJ_KINDS and not only and os.path.exists(mp):
        # PART["atlases"] (bs_missiles2.py --atlases: petalas da Piranha) nao e item: o render completo nao refaz o
        # atlas, entao o bloco "atlases" do meta antigo e os PNGs dele ficam (antes o render completo apagava o
        # bloco e era preciso rodar bs_missiles2.py --meta-only)
        old = json.load(open(mp))
        atl = old.get("atlases") if old.get("kind") == kind else None
        if atl:
            meta["atlases"] = atl
            keep = {f for a in atl.values() for f in (a.get("file"), a.get("normals"))
                    if f and os.path.exists(os.path.join(out, f))}
            meta["files"] = sorted(set(meta["files"]) | keep)
    if only and os.path.exists(mp):
        old = json.load(open(mp))
        if kind in PROJ_KINDS and old.get("kind") == kind:
            # projeteis: --only troca so os itens renderizados; a ordem segue PART["items"]
            items = dict(old.get("items", {}))
            items.update(meta["items"])
            order = [k for k in mod.PART["items"] if k in items] + [k for k in items if k not in mod.PART["items"]]
            old.update({k: v for k, v in meta.items() if k not in ("files", "items")})
            old["items"] = {k: items[k] for k in order}
        else:
            old.update({k: v for k, v in meta.items() if k != "files"})
        old["files"] = sorted(set(old.get("files", [])) | set(meta["files"]))
        meta = old
    json.dump(meta, open(mp, "w"), indent=1)
    if kind in PROJ_KINDS and mod.PART.get("atlases") and hasattr(mod, "register_atlases"):
        mod.register_atlases(out)        # formato do proprio modelo (bs_missiles2): idempotente
    if "--preview" in args and kind in ("gun", "launcher"):
        import compose_preview
        compose_preview.make_all(out)
    elif "--preview" in args and kind in PROJ_KINDS:
        import compose_preview
        compose_preview.make_projectiles(out)
    elif "--preview" in args and kind == "factory":
        print("previa de fabrica: python3 tools/blender/compose_factory.py <fabrica> <recurso> <nome>")
    print("OK", short, out)


if __name__ == "__main__":
    main()
