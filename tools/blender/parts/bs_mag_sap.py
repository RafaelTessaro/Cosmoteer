"""Carregador SAP (bs_mag_sap, 2.0, NOVO) - Semiperfurante; pilha de 5.

A mesma caixa da familia (parts/_bs2_itens_helpers.magazine) com a fenda de LED e as pastilhas LARANJA (palette.sap)
e 3 granadas SAP do nivel S: ogiva curta com capuz ROMBUDO largo de grafite e colar de aco (a ponta chata e larga
separa a SAP da HE, cuja cor ambar e proxima). Pilha de 5: 2 x 2 + uma deitada no meio da camada de cima.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

AMMO = "sap"
PART = IT.mag_part("rafaeltessaro.bs_mag_sap", AMMO, 5)


def item(M, T="item"):
    IT.magazine(M, IT.X(M), (T,), AMMO)
