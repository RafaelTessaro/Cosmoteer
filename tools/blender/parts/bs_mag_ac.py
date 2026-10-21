"""Carregador AC - Alta Capacidade (bs_mag_ac, 2.0, NOVO); pilha de 3.

Estojo premium da familia (parts/_bs2_itens_helpers.magazine): tampas de canto de OURO nos 4 cantos, fenda de LED e
pastilhas CARMIM (palette.ac) e so 2 granadas AC guiadas do nivel S (mais gordas): faixa carmim entre dois aneis de
ouro, canards de ouro no ombro da ogiva e o anel de ouro do buscador com a lente escura na ponta.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

AMMO = "ac"
PART = IT.mag_part("rafaeltessaro.bs_mag_ac", AMMO, 3)


def item(M, T="item"):
    IT.magazine(M, IT.X(M), (T,), AMMO)
