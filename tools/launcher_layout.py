"""Layout das celulas dos lancadores de misseis (compartilhado pelo gerador do mod e pelo renderizador 3D).

Entrada: o bloco "cells" do PART meta do lancador (tools/spec/bullet_strike_missiles.json,
launchers[].art.part_meta.cells, ou o PART["cells"] do modelo 3D) e o nome do layout do modo
(launchers[].modes[].layout). Coordenadas de entrada na CABECA (x direita, y frente, tiles a partir do pivo);
saida na TORRE (x = frente, y = direita), como as posicoes de emissores do jogo.

Casulos: grade "cols" x "rows" (pitch [x, y]) ou padrao de fileiras "pattern" (ex.: "3-2-3" = fileiras de 3, 2 e
3 tubos, de tras para a frente, cada fileira centrada). Ordem de enchimento: casulo a casulo (na ordem da lista),
fileiras de tras para a frente (row_major_bottom_up), da esquerda para a direita.

Layouts (unidade do rack = o que 1 missil do modo ocupa; "form" diz como a arte desenha o nariz carregado):
  "cassette"        pares de tubos lado a lado (Tocandira: 6 cassetes = 12 tubos)        form "tube" (1 nariz por tubo)
  "fine*"           1 tubo = 1 unidade (Caipora 3-2-3 x 2 = 16, Mula 3x4 x 4 = 48)        form "tube"
  "heavy*"          1 fileira inteira de um casulo = 1 unidade (Mula: 4 fileiras x 4 = 16)  form "heavy" (1 nariz longo)
  "torpedo<N>"      1 unidade por casulo, no centro da face (Caipora 2, Mula 4)            form "torpedo" (1 nariz grande)
  "torpedo<N>_inner" so os N casulos mais internos; os outros ficam com a persiana fechada (Mula nuclear: 2)
Para "heavy"/"torpedo" cada unidade traz "box" = [largura lateral, profundidade] do nariz em tiles.
"""

import re


def _pod_rows(pod, who):
    """Fileiras do casulo (de tras para a frente): lista de quantidades de tubos por fileira."""
    if "cols" in pod:
        return [pod["cols"]] * pod["rows"]
    pat = pod.get("pattern")
    if pat and re.fullmatch(r"\d+(-\d+)*", pat):
        return [int(n) for n in pat.split("-")]
    raise NotImplementedError(f"{who}: padrao de casulo {pat!r} desconhecido")


def _pod_tubes(pod, who):
    """[(fileira, [[fwd, lat], ...]), ...] nas coordenadas da torre, na ordem de enchimento."""
    cx, cy = pod["center"]
    px, py = pod["pitch"]
    rows = _pod_rows(pod, who)
    out = []
    for r, n in enumerate(rows):                     # de tras para a frente (row_major_bottom_up)
        y = cy + (r - (len(rows) - 1) / 2) * py
        out.append([[round(y, 4), round(cx + (c - (n - 1) / 2) * px, 4)] for c in range(n)])
    return out


def _pod_box(pod, tube_r, who):
    """Face do casulo (largura lateral, profundidade) em tiles: a area que um nariz de torpedo cobre."""
    rows = _pod_rows(pod, who)
    px, py = pod["pitch"]
    return [round((max(rows) - 1) * px + 2 * tube_r, 4), round((len(rows) - 1) * py + 2 * tube_r, 4)]


def _mean(pts):
    return [round(sum(p[0] for p in pts) / len(pts), 4), round(sum(p[1] for p in pts) / len(pts), 4)]


def cell_layout(cells, layout, rack_units=None, who="lancador"):
    units, pods, shutters = [], [], []
    tube_r = cells.get("tube_r", 0.09)
    all_pods = cells["pods"]
    if layout == "cassette" or layout.startswith("fine"):
        per_unit = 2 if (cells.get("units") == "pairs" or layout == "cassette") else 1
        for p_i, pod in enumerate(all_pods):
            start = len(units)
            for row in _pod_tubes(pod, who):
                for c0 in range(0, len(row), per_unit):
                    tubes = row[c0:c0 + per_unit]
                    units.append({"pos": _mean(tubes), "tubes": tubes, "pod": p_i, "form": "tube"})
            pods.append({"index": p_i, "range": [start, len(units)], "center": [pod["center"][1], pod["center"][0]]})
    elif layout.startswith("heavy"):
        for p_i, pod in enumerate(all_pods):
            start = len(units)
            px = pod["pitch"][0]
            py = pod["pitch"][1]
            for row in _pod_tubes(pod, who):
                box = [round((len(row) - 1) * px + 2 * tube_r, 4), round(min(py * 0.96, 4 * tube_r), 4)]
                units.append({"pos": _mean(row), "tubes": row, "pod": p_i, "form": "heavy", "box": box})
            pods.append({"index": p_i, "range": [start, len(units)], "center": [pod["center"][1], pod["center"][0]]})
    elif layout.startswith("torpedo"):
        m = re.fullmatch(r"torpedo(\d+)(_inner)?", layout)
        if not m:
            raise NotImplementedError(f"{who}: layout {layout} desconhecido")
        n = int(m.group(1))
        chosen = list(range(len(all_pods)))
        if m.group(2):
            inner = sorted(chosen, key=lambda i: (abs(all_pods[i]["center"][0]), i))[:n]
            chosen = sorted(inner)
        for p_i in range(len(all_pods)):
            pod = all_pods[p_i]
            c = [round(pod["center"][1], 4), round(pod["center"][0], 4)]
            box = _pod_box(pod, tube_r, who)
            if p_i not in chosen:
                shutters.append({"pod": p_i, "center": c, "box": box})
                continue
            start = len(units)
            units.append({"pos": c, "tubes": [c], "pod": p_i, "form": "torpedo", "box": box})
            pods.append({"index": p_i, "range": [start, len(units)], "center": c})
    else:
        raise NotImplementedError(f"{who}: layout {layout} desconhecido")
    if rack_units is not None and len(units) != rack_units:
        raise ValueError(f"{who}: layout {layout} gera {len(units)} unidades, o spec pede rack_units = {rack_units}")
    return {"units": units, "pods": pods, "tubes_per_unit": len(units[0]["tubes"]), "tube_r": tube_r,
            "form": units[0]["form"], "shutters": shutters}
