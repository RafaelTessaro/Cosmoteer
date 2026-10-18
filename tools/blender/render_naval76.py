"""Renderiza os sprites 3D do Canhao Naval Automatico 76 mm (bs_naval_76).

Rodar com o Python que tem o modulo bpy (Blender 5.x):
    <venv>/bin/python tools/blender/render_naval76.py <pasta_saida> [--quick]

Gera na pasta de saida:
    turret.png / turret_off.png / turret_normals.png / turret_shadow.png
    barrel1..5.png (+ barrel_normals1..5.png) = quadros de recuo (1 = repouso)
    barrel_heat.png = sobreposicao de calor no freio de boca (apos disparar)
    roof.png / roof_normals.png (verde = pintura da nave), floor.png
    showcase.png = vista ampliada (4x) com teto pintado, para avaliacao
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402

import bs3d as B  # noqa: E402
import models as Mo  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "out_naval76"
QUICK = "--quick" in sys.argv
os.makedirs(OUT, exist_ok=True)

# geometria da peca (coordenadas da peca: x para a direita, y para BAIXO, em tiles)
W, H = 3, 4
PIVOT = (1.5, 1.65)
TURRET_BOX = 2.9            # lado do quadrado do sprite da torre (tiles)
BARREL_ROOT = 0.88          # distancia pivo -> raiz do cano (tiles)
BARREL_L = 2.6              # comprimento do cano (raiz -> boca)
BARREL_W = 0.46             # largura do sprite do cano
RECOIL = [0.0, 0.26, 0.18, 0.10, 0.04]   # quadros 1..5 (1 = repouso, 2 = recuo maximo)
RECOIL_PAD = 0.30           # espaco atras da raiz para o recuo
CREW = [(0.5, 3.55, 0), (1.5, 3.55, 0), (2.5, 3.55, 0)]


def P(name):
    return os.path.join(OUT, name)


def samples(n):
    bpy.context.scene.cycles.samples = 12 if QUICK else n


def shadow_from(alpha_img, offset_px, blur_px, opacity=0.55):
    a = np.asarray(alpha_img.split()[-1], dtype=np.float32)
    w, h = alpha_img.size
    pad = int(offset_px + blur_px * 3)
    big = np.zeros((h + pad * 2, w + pad * 2), np.float32)
    big[pad + offset_px:pad + offset_px + h, pad + offset_px:pad + offset_px + w] = a
    im = Image.fromarray(big.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur_px))
    im = im.crop((pad, pad, pad + w, pad + h))
    sa = (np.asarray(im, dtype=np.float32) * opacity).astype(np.uint8)
    return Image.fromarray(np.dstack([np.zeros((h, w, 3), np.uint8), sa]), "RGBA")


# ============================================================================ torre
def render_turret(M):
    B.camera(TURRET_BOX, TURRET_BOX, (0, 0))
    samples(64)
    Mo.naval_76_head(M, "head")
    B.show_only(["head"])
    px = int(round(TURRET_BOX * B.PX))
    out = B.render_set(P("turret"), (px, px))
    shadow_from(out["on"], 5, 4).save(P("turret_shadow.png"))
    return out


# ============================================================================ cano
def render_barrel(M):
    # o cano e modelado com raiz em y=0; o sprite cobre de -RECOIL_PAD ate BARREL_L
    h_tiles = BARREL_L + RECOIL_PAD
    B.camera(BARREL_W, h_tiles, (0, (BARREL_L - RECOIL_PAD) / 2))
    samples(48)
    Mo.naval_76_barrel(M, BARREL_L, "barrel")
    objs = B.objects_with("barrel")
    base_y = {o.name: o.location.y for o in objs}
    size = (int(round(BARREL_W * B.PX)), int(round(h_tiles * B.PX)))
    B.show_only(["barrel"])
    for i, r in enumerate(RECOIL, start=1):
        for o in objs:
            o.location.y = base_y[o.name] - r
        B.render_set(P(f"barrel{i}"), size, glow_halo=False, off=False)
        os.replace(P(f"barrel{i}_normals.png"), P(f"barrel_normals{i}.png"))
    for o in objs:
        o.location.y = base_y[o.name]
    # calor: so a emissao do freio aquecido (quadro de repouso), somado por cima no jogo
    heat = B.mat_glow("heat", (1.0, 0.30, 0.05), 6.0)
    hot = [o for o in objs if o.name.startswith(("b_brake", "b_slot", "b_bore", "b_sleeve"))]
    keep = {o.name: list(o.data.materials) for o in hot}
    for o in hot:
        o.data.materials.clear()
        o.data.materials.append(heat)
    # gradiente: o freio fica mais quente que a luva
    sc = bpy.context.scene
    for l in [o for o in sc.objects if o.type == "LIGHT"]:
        l.hide_render = True
    bg = sc.world.node_tree.nodes["Background"].inputs[1]
    old = bg.default_value
    bg.default_value = 0.0
    em = B.render_to(P("barrel_heat_raw.png"), size)
    bg.default_value = old
    for l in [o for o in sc.objects if o.type == "LIGHT"]:
        l.hide_render = False
    for o in hot:
        o.data.materials.clear()
        for m in keep[o.name]:
            o.data.materials.append(m)
    os.remove(P("barrel_heat_raw.png"))
    arr = np.asarray(em, dtype=np.float32)
    hpx = size[1]
    # rampa vertical: 0 na raiz da luva -> 1 na boca (y da imagem cresce para baixo)
    ys = np.linspace(1.0, 0.0, hpx)[:, None]
    tip = np.clip((ys - 0.55) / 0.35, 0, 1) ** 1.6
    arr[..., 3] *= tip
    glow = Image.fromarray(arr.astype(np.uint8), "RGBA")
    halo = glow.filter(ImageFilter.GaussianBlur(3))
    Image.alpha_composite(halo, glow).save(P("barrel_heat.png"))


# ============================================================================ casco (teto/piso)
def render_hull(M):
    B.camera(W, H, (0, 0))
    samples(48)
    ring_r = 1.30
    Mo.hull_roof(M, W, H, PIVOT, ring_r, "roof")
    Mo.hull_floor(M, W, H, PIVOT, ring_r, CREW, "floor")
    size = (W * B.PX, H * B.PX)
    B.show_only(["roof"])
    B.render_set(P("roof"), size, glow_halo=True, off=False)
    B.show_only(["floor"])
    B.render_set(P("floor"), size, glow_halo=True, off=False, normals=False)


# ============================================================================ vitrine ampliada
def render_showcase(M, scale=4):
    """Torre + cano + teto juntos, teto pintado (cinza-azulado) e luz unica: para o usuario avaliar."""
    paint = B.mat_paint("ship_paint", (0.11, 0.14, 0.19), rough=0.4, metal=0.4, wear=0.2, grime=0.1)
    for o in B.objects_with("roof"):
        for i, m in enumerate(o.data.materials):
            if m and m.name.startswith("roof_green"):
                o.data.materials[i] = paint
    head = B.objects_with("head")
    barrel = B.objects_with("barrel")
    lift = 0.10
    for o in head:
        o.location.z += lift
    for o in barrel:
        o.location.y += BARREL_ROOT
        o.location.z += lift
    # pivo da torre em coordenadas centradas na peca
    px, py = PIVOT[0] - W / 2, H / 2 - PIVOT[1]
    for o in head + barrel:
        o.location.x += px
        o.location.y += py
    top = py + BARREL_ROOT + BARREL_L + 0.1
    bot = -H / 2 - 0.1
    cy = (top + bot) / 2
    h_t = top - bot
    w_t = W + 0.4
    sc = bpy.context.scene
    cam = B.camera(w_t, h_t, (0, cy))
    sc.render.resolution_x = int(w_t * 64 * scale)
    sc.render.resolution_y = int(h_t * 64 * scale)
    samples(96)
    B.show_only(["roof", "head", "barrel"])
    B.set_glow(True)
    sc.render.film_transparent = False
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.014, 0.02, 1)
    sc.render.filepath = P("showcase.png")
    bpy.ops.render.render(write_still=True)
    sc.render.film_transparent = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.66, 0.74, 1)
    del cam


def main():
    B.reset()
    M = Mo.mats()
    render_turret(M)
    B.reset()
    M = Mo.mats()
    render_barrel(M)
    B.reset()
    M = Mo.mats()
    render_hull(M)
    # vitrine: monta tudo de novo numa cena so
    B.reset()
    M = Mo.mats()
    Mo.hull_roof(M, W, H, PIVOT, 1.30, "roof")
    Mo.naval_76_head(M, "head")
    Mo.naval_76_barrel(M, BARREL_L, "barrel")
    render_showcase(M)
    meta = {"part_size": [W, H], "pivot": list(PIVOT), "turret_size": TURRET_BOX, "barrel_root": BARREL_ROOT,
            "barrel_len": BARREL_L, "barrel_w": BARREL_W, "recoil_pad": RECOIL_PAD, "recoil": RECOIL}
    with open(P("meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("OK", OUT)


if __name__ == "__main__":
    main()
