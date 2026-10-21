"""Carga de Missil HE (bs_msl_he, 2.0, NOVO) - municao dos lancadores (Jararaca/Muricoca); pilha de 10.

SPEC 2.0 ("small missile charge in a cradle, amber band, sleeve seams"): o missil HE 2.0 (Jararaca) em miniatura num
berco (parts/_bs2_itens_helpers.charge): luvas claras em divisa com frestas escuras, faixa AMBAR (Mo.band_mat("he"),
a mesma tinta do missil em voo e dos narizes nos lancadores), ogiva clara com o domo escuro do buscador e o anel
ambar, 2 aletas em flecha, LED ambar num rebaixo da luva de tras; berco = treno escuro + 2 garras claras.
Pilha (spec stack_layout_7_10): fileira de 5 (passo 0,14) e a 2a camada desencontrada por cima.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

KIND = "msl_he"
PART = IT.charge_part("rafaeltessaro.bs_msl_he", KIND, "amber")


def item(M, T="item"):
    IT.charge(M, IT.X(M), (T,), KIND)
