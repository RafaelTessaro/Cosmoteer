"""Carregador AP (bs_mag_ap, 2.0) - Perfurante; pilha de 4.

REWORK futurista (USER_NOTES 2026-10-21; SPEC 2.0): a mesma caixa da familia (parts/_bs2_itens_helpers.magazine) com
a fenda de LED e as pastilhas BRANCO-AZULADAS (palette.ap) e 3 granadas AP do nivel S mais finas e mais a frente:
ogiva com capuz escuro e anel gelo e as AGULHAS de triaco (penetradores finos de ~1 px, ~5 px alem do capuz) bem
passando da boca: o "pente de espinhos" separa a AP das outras pela SILHUETA a 1x, nao so pela cor.
A ID e a da 1.x; so a arte muda.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

AMMO = "ap"
PART = IT.mag_part("rafaeltessaro.bs_mag_ap", AMMO, 4)


def item(M, T="item"):
    IT.magazine(M, IT.X(M), (T,), AMMO)
