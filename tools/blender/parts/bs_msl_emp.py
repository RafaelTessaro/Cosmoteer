"""Carga de Missil PEM (bs_msl_emp, 2.0, NOVO) - Poraque; pilha de 10.

SPEC 2.0 ("charge with copper coil bands and blue LED"): o Poraque 2.0 em miniatura no berco de prateleira das
cargas (parts/_bs2_itens_helpers.charge: treno escuro + trilhos claros na frente): corpo ESCURO com 3 bobinas de
COBRE (2 espiras redondas cada: a assinatura PEM), 2 LEDs AZUIS em rebaixos entre as bobinas, 2 laminas longas e
varridas claras, faixa azul (Mo.band_mat("emp")) e o nariz escuro com o olho azul aceso.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

KIND = "msl_emp"
PART = IT.charge_part("rafaeltessaro.bs_msl_emp", KIND, "blue")


def item(M, T="item"):
    IT.charge(M, IT.X(M), (T,), KIND)
