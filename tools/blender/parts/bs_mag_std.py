"""Carregador HE (bs_mag_std, 2.0) - municao padrao Alto-Explosivo dos canhoes; pilha de 6.

REWORK futurista (USER_NOTES 2026-10-21; SPEC 2.0 art_assets.assets.resources): caixa de carregador blindada da
familia 2.0 (parts/_bs2_itens_helpers.magazine, exoesqueleto: bandeja de nucleo escuro, bochechas claras em cunha,
placa traseira clara de bisel duplo com pega embutida e pastilhas ambar, vao em DIVISA com a fenda de LED AMBAR) e 3
granadas HE do nivel S (as do Tambor 2.0: luva de composito clara com junta escura, faixa ambar, ogiva grafite e
espoleta de aco de ponta chata com o anel do sensor) deitadas na bandeja, a do meio adiantada (a ponta vira seta).
A ID e a da 1.x (Carregador Padrao); so a arte muda. A pilha (MAG_LAYOUT): 1 no centro, 2 lado a lado, 3 e 4 em
duas fileiras de costas uma para a outra, 5 e 6 com a camada de cima deitada sobre as placas traseiras.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

AMMO = "he"
PART = IT.mag_part("rafaeltessaro.bs_mag_std", AMMO, 6)


def item(M, T="item"):
    IT.magazine(M, IT.X(M), (T,), AMMO)
