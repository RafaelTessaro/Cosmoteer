"""Carregador Padrao (Standard Magazine) - municao empacotada pela prensa e levada pela tripulacao.

Caixa de carregador blindada no estilo da familia: casco claro chanfrado sobre nucleo escuro, janela
de contagem com cartuchos aparentes, contador de LEDs ambar e alca de transporte.
Unidade modelada centrada na origem, cabendo em ~1 x 1 (o renderizador escala para a pilha).
"""

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_mag_std",
    "kind": "resource",
    "accent": "amber",
    "unit_scale": 0.44,
}


def item(M, T="item"):
    tags = (T,)
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    # corpo: nucleo escuro + carcaca clara em duas metades com vao no meio
    B.plate("mag_core", B.rpoly(0, 0, 0.62, 0.92, 0, chamfer=0.08), 0.0, 0.30, K, slope=0.03, tags=tags)
    for side, y0, y1 in (("f", 0.06, 0.44), ("b", -0.44, -0.06)):
        poly = B.rpoly(0, (y0 + y1) / 2, 0.66, y1 - y0, 0, chamfer=0.07)
        _, pnl = B.shard(f"mag_shell_{side}", poly, 0.05, 0.36, A, slope=0.05, groove=0.03, panel_h=0.025, tags=tags)
        if pnl is not None:
            B.cut(pnl, [B.rbox(f"mag_pl_{side}", 0.18, (y0 + y1) / 2, 0.014, (y1 - y0) * 0.7, 0.37, 0.6, K, bevel=0.0)])
    # janela com a ponta dos cartuchos (latao) na frente
    B.box("mag_win", -0.08, 0.25, 0.32, 0.12, 0.36, 0.40, M["black"], bevel=0.0, tags=tags)
    brass = B.mat_metal("brass", (0.62, 0.42, 0.12), rough=0.3, metal=1.0)
    for i in range(4):
        B.cyl(f"mag_round{i}", -0.20 + i * 0.08, 0.25, 0.395, 0.026, 0.02, brass, axis="Z", verts=10, bevel=0.0,
              tags=tags)
    # contador de LEDs no vao central
    for i in range(5):
        B.box(f"mag_led{i}", -0.20 + i * 0.1, 0.0, 0.05, 0.03, 0.30, 0.32, M["glow"] if i < 4 else M["black"],
              bevel=0.0, tags=tags)
    # alca de transporte
    B.box("mag_handle", 0.0, -0.25, 0.36, 0.06, 0.40, 0.46, S, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        B.box(f"mag_hpost{sx}", sx * 0.17, -0.25, 0.04, 0.06, 0.36, 0.44, S, bevel=0.005, tags=tags)
