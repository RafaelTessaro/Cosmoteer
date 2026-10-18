"""Layout das celulas dos lancadores de misseis (compartilhado pelo gerador do mod e pelo renderizador 3D).

Entrada: o bloco "cells" do PART meta do lancador (tools/spec/bullet_strike_missiles.json,
launchers[].art.part_meta.cells, ou o PART["cells"] do modelo 3D) e o nome do layout do modo
(launchers[].modes[].layout). Coordenadas de entrada na CABECA (x direita, y frente, tiles a partir do pivo);
saida na TORRE (x = frente, y = direita), como as posicoes de emissores do jogo.

Layouts gerados: "cassette" (pares de tubos lado a lado = 1 unidade do rack) e "fine*" (1 tubo = 1 unidade),
em grades cols x rows por casulo, enchendo de tras para a frente (row_major_bottom_up) e casulo a casulo.
Os demais layouts do projeto (3-2-3, heavy16, torpedo*) entram no estagio 2.
"""


def cell_layout(cells, layout, rack_units=None, who="lancador"):
    units, pods = [], []
    if layout == "cassette" or layout.startswith("fine"):
        per_unit = 2 if (cells.get("units") == "pairs" or layout == "cassette") else 1
        for p_i, pod in enumerate(cells["pods"]):
            if "cols" not in pod:
                raise NotImplementedError(f"{who}: padrao de casulo {pod.get('pattern')} ainda nao gerado")
            cx, cy = pod["center"]
            px, py = pod["pitch"]
            cols, rows = pod["cols"], pod["rows"]
            start = len(units)
            for r in range(rows):                       # de tras para a frente (row_major_bottom_up)
                y = cy + (r - (rows - 1) / 2) * py
                for c0 in range(0, cols, per_unit):
                    tubes = []
                    for c in range(c0, min(cols, c0 + per_unit)):
                        x = cx + (c - (cols - 1) / 2) * px
                        tubes.append([round(y, 4), round(x, 4)])
                    fwd = round(sum(t[0] for t in tubes) / len(tubes), 4)
                    lat = round(sum(t[1] for t in tubes) / len(tubes), 4)
                    units.append({"pos": [fwd, lat], "tubes": tubes, "pod": p_i})
            pods.append({"index": p_i, "range": [start, len(units)], "center": [cy, cx]})
    else:
        raise NotImplementedError(f"{who}: layout {layout} ainda nao gerado (estagio 2)")
    if rack_units is not None and len(units) != rack_units:
        raise ValueError(f"{who}: layout {layout} gera {len(units)} unidades, o spec pede rack_units = {rack_units}")
    return {"units": units, "pods": pods, "tubes_per_unit": len(units[0]["tubes"]), "tube_r": cells.get("tube_r", 0.09)}
