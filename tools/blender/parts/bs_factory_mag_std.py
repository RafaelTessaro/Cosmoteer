"""Prensa de Carregadores (Magazine Press) 2x2 - empacota municao de canhao em carregadores padrao.

Layout vanilla factory_ammo: fileira de cima = maquinario (bloqueado); embaixo, entrada (esquerda) e
saida (direita), onde o jogo desenha as pilhas de recursos. Coordenadas centradas na peca, +Y = frente.
A animacao (phase 0..1) sobe e desce o martelo da prensa e corre a esteira.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_factory_mag_std",
    "kind": "factory",
    "size": [2, 2],
    "accent": "amber",
    "machine_frames": 4,
    "machine_interval": 0.12,
}


def floor(M, T="floor"):
    tags = (T,)
    K, KM, A, AM = M["core"], M["core_mid"], M["armor"], M["armor_mid"]
    B.box("fl_base", 0, 0, 2, 2, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(2):
        for ty in range(2):
            cx, cy = tx - 0.5, 0.5 - ty
            B.plate(f"fl{tx}{ty}", B.rpoly(cx, cy, 0.92, 0.92, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.01,
                    tags=tags)
    # bases das grades de entrada/saida (onde o jogo desenha as pilhas): moldura com cantoneiras ambar
    for sx, name in ((-0.5, "in"), (0.5, "out")):
        B.plate(f"pad_{name}", B.rpoly(sx, -0.5, 0.78, 0.78, 0, chamfer=0.05), 0.03, 0.045, AM, slope=0.01,
                tags=tags)
        for cx in (-1, 1):
            for cy in (-1, 1):
                B.rbox(f"padc_{name}{cx}{cy}", sx + cx * 0.33, -0.5 + cy * 0.33, 0.1, 0.025, 0.045, 0.055,
                       M["glow_dim"], rot=0 if cx * cy > 0 else 90, bevel=0.0, tags=tags)
    # seta de fluxo entre entrada e saida
    B.loft("flow", [(-0.12, -0.56), (0.04, -0.56), (0.04, -0.62), (0.14, -0.5), (0.04, -0.38), (0.04, -0.44),
                    (-0.12, -0.44)], None or [(-0.12, -0.56), (0.04, -0.56), (0.04, -0.62), (0.14, -0.5),
                                              (0.04, -0.38), (0.04, -0.44), (-0.12, -0.44)],
           0.03, 0.04, M["glow_dim"], bevel=0.0, tags=tags)


def machine(M, T="machine", phase=0.0):
    """Maquinario na fileira de cima: corpo da prensa, martelo animado, esteira e painel."""
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # carcaca da maquina (bisel duplo), aberta no meio para ver o martelo
    for sx in (-1, 1):
        poly = [(sx * 0.95, 0.06), (sx * 0.38, 0.06), (sx * 0.30, 0.16), (sx * 0.30, 0.86), (sx * 0.40, 0.95),
                (sx * 0.88, 0.95), (sx * 0.95, 0.88)]
        _, pnl = B.shard(f"mc_shell{sx}", poly, 0.0, 0.42, A, slope=0.05, groove=0.03, panel_h=0.025, tags=tags)
        Mo.slot_with_pips(f"mc_slot{sx}", sx * 0.78, 0.30, 0.70, 0.06, 0.445, 4, M, tags, target=pnl, depth=0.03)
    # poco da prensa (nucleo escuro) e martelo que desce/sobe
    B.box("mc_pit", 0, 0.5, 0.56, 0.84, 0.0, 0.22, K, bevel=0.0, tags=tags)
    z_ram = 0.30 + 0.14 * (0.5 + 0.5 * math.cos(phase * math.tau))
    B.plate("mc_ram", B.rpoly(0, 0.52, 0.42, 0.42, 0, chamfer=0.06), z_ram, z_ram + 0.12, AM, slope=0.03,
            tags=tags)
    B.cyl("mc_piston", 0, 0.52, z_ram + 0.2, 0.06, 0.16, S, axis="Z", verts=12, tags=tags)
    # esteira com taliscas que andam com a fase
    B.box("mc_belt", 0, 0.12, 0.56, 0.16, 0.0, 0.08, KM, bevel=0.0, tags=tags)
    for i in range(5):
        x = -0.24 + ((i * 0.12 + phase * 0.12) % 0.6)
        B.box(f"mc_slat{i}", x, 0.12, 0.03, 0.14, 0.08, 0.1, S, bevel=0.0, tags=tags)
    # luz de ciclo
    B.box("mc_led", 0, 0.9, 0.2, 0.03, 0.22, 0.25, M["glow"] if phase < 0.5 else M["glow_dim"], bevel=0.0, tags=tags)


def roof(M, T="roof"):
    tags = (T,)
    green = B.mat_roof_green()
    B.box("rf_under", 0, 0, 2, 2, -0.05, 0.02, M["core"], bevel=0.0, tags=tags)
    for tx in range(2):
        for ty in range(2):
            cx, cy = tx - 0.5, 0.5 - ty
            B.shard(f"rf{tx}{ty}", B.rpoly(cx, cy, 0.94, 0.94, 0, chamfer=0.07), 0.0, 0.06, green, slope=0.025,
                    groove=0.05, panel_h=0.02, tags=tags)
    # respiro da prensa e escotilha
    v = B.box("rf_vent", 0, 0.5, 0.7, 0.36, 0.06, 0.11, M["core_mid"], bevel=0.01, slope=0.015, tags=tags)
    B.cut(v, [B.box(f"rf_vc{i}", 0, 0.38 + i * 0.08, 0.6, 0.03, 0.09, 0.2, M["core"], bevel=0.0) for i in range(4)])
    B.box("rf_led", 0, 0.24, 0.16, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)
