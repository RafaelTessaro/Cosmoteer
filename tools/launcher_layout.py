"""Layout das celulas dos lancadores de misseis (compartilhado pelo gerador do mod e pelo renderizador 3D).

Entrada: o bloco "cells" do PART meta do lancador (tools/spec/bullet_strike_missiles.json,
launchers[].art.part_meta.cells, ou o PART["cells"] do modelo 3D) e o nome do layout do modo
(launchers[].modes[].layout). Coordenadas de entrada na CABECA (x direita, y frente, tiles a partir do pivo);
saida na TORRE (x = frente, y = direita), como as posicoes de emissores do jogo.

Casulos: grade "cols" x "rows" (pitch [x, y]) ou padrao de fileiras "pattern" (ex.: "3-2-3" = fileiras de 3, 2 e
3 tubos, de tras para a frente, cada fileira centrada). Ordem de enchimento: casulo a casulo (na ordem da lista),
fileiras de tras para a frente (row_major_bottom_up), da esquerda para a direita.

Layouts 2.0 (unidade do rack = o que 1 missil do modo ocupa; "form" diz como a arte desenha o nariz carregado):
  "cassette"        pares de tubos lado a lado (Tocandira: 6 cassetes = 12 tubos)        form "tube" (1 nariz por tubo)
  "fine*"           1 tubo = 1 unidade (Caipora 3-2-3 x 2 = 16, Mula 3x4 x 4 = 48)        form "tube"
  "cluster<N>"      portador da Piranha nas 4 celulas de CANTO de cada casulo 3-2-3 (Caipora: 4 x 2 = 8); as 4
                    celulas do meio de cada casulo ficam com tampa fixa (shutters de kind "cap", tamanho de 1 tubo)
                    form "tube" (1 nariz gordo por tubo de canto; o quadro do nariz e o de sempre, 5 x tube_r)
  "heavy<N>"        bloco de fileiras inteiras de um casulo = 1 unidade; fileiras por unidade = fileiras de todos
                    os casulos / N (Mula: heavy16 = 1 fileira x 4 por casulo; heavy8 = bloco 3x2, 2 por casulo)
                    form "heavy" (1 nariz longo; "box" cobre o bloco)
  "torpedo<N>_inner" so os N casulos mais internos, 1 unidade no centro da face; os outros ficam com a persiana
                    fechada (shutters de kind "pod"; Mula nuclear, Iara: 2)                form "torpedo"
Para "heavy"/"torpedo" cada unidade traz "box" = [largura lateral, profundidade] do nariz em tiles. Cada shutter traz
{"pod", "center" (torre), "box", "kind"}; dentro de um layout todos tem o mesmo box (o renderizador desenha um so).

Sobreposicoes do rack: overlay_rect() da o retangulo de cada casulo (recorte das imagens dos niveis) e
rect_placement() a posicao/tamanho do ResourceSprites correspondente.

Conferencia: `python3 tools/launcher_layout.py` roda selftest() em todo modo de todo lancador do spec.
"""

import math
import re

PX = 64            # pixels por tile (bsgen/art.py PX), igual no gerador de regras e nos dois renderizadores


def overlay_rect(units, tube_r, turret_box, pad_px=2):
    """Retangulo (pixels [x0, y0, x1, y1] no quadro da torre, lado round(turret_box * 64), frente para cima) que
    contem todos os narizes das unidades de UMA sobreposicao (um casulo de um modo). As imagens dos niveis do rack
    sao recortadas nele (contrato STYLE.md secao 8.1) e o ResourceSprites usa o centro/tamanho dele.

    Cobre o maior desenho dos dois renderizadores: o nariz 3D (render_part.py: quadro de 5 x tube_r por tubo;
    heavy/torpedo: box x 1.15 centrado na unidade) e o placeholder procedural (bsgen/sprites.py, menor)."""
    T = int(round(turret_box * PX))
    xs0, xs1, ys0, ys1 = [], [], [], []
    for u in units:
        if u.get("form") in ("heavy", "torpedo"):
            hw, hh = 0.575 * u["box"][0], 0.575 * u["box"][1]
            if u["form"] == "heavy":
                # nariz pesado procedural: a tampa redonda da ponta cresce com a profundidade do bloco (heavy8 =
                # 2 fileiras); com 1 fileira (heavy16) o valor e o de sempre
                hw = max(hw, 0.42 * u["box"][0] + 0.36 * u["box"][1])
            pts = [u["pos"]]
        else:
            hw = hh = 2.5 * tube_r
            pts = u["tubes"]
        for fwd, lat in pts:
            x, y = T / 2 + lat * PX, T / 2 - fwd * PX
            xs0.append(x - hw * PX)
            xs1.append(x + hw * PX)
            ys0.append(y - hh * PX)
            ys1.append(y + hh * PX)
    return [max(0, math.floor(min(xs0)) - pad_px), max(0, math.floor(min(ys0)) - pad_px),
            min(T, math.ceil(max(xs1)) + pad_px), min(T, math.ceil(max(ys1)) + pad_px)]


def rect_placement(rect, turret_box):
    """Retangulo em pixels -> (Location [frente, direita] no quadro da torre, Size [largura, altura]) em tiles,
    para um sprite ChainedTo = Turret com Rotation = 90d (imagem com a frente para cima, como turret.png)."""
    T = int(round(turret_box * PX))
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    loc = [round((T / 2 - cy) / PX, 7), round((cx - T / 2) / PX, 7)]
    return [0 if v == 0 else v for v in loc], [round((x1 - x0) / PX, 7), round((y1 - y0) / PX, 7)]


def _pod_rows(pod, who):
    """Fileiras do casulo (de tras para a frente): lista de quantidades de tubos por fileira."""
    if "cols" in pod:
        return [pod["cols"]] * pod["rows"]
    pat = pod.get("pattern")
    if pat and re.fullmatch(r"\d+(-\d+)*", pat):
        return [int(n) for n in pat.split("-")]
    raise NotImplementedError(f"{who}: padrao de casulo {pat!r} desconhecido")


def _pod_tubes(pod, who):
    """[[[fwd, lat], ...] por fileira] nas coordenadas da torre, na ordem de enchimento."""
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


def _layout_count(layout, prefix):
    """N de '<prefixo><N>' (None sem numero)."""
    m = re.fullmatch(prefix + r"(\d*)", layout)
    if not m:
        return None, False
    return (int(m.group(1)) if m.group(1) else None), True


def cell_layout(cells, layout, rack_units=None, who="lancador"):
    """Unidades do rack em ORDEM DE ENCHIMENTO (coordenadas da torre) para um layout de modo.

    Devolve {units: [{pos, tubes, pod, form[, box]}], pods: [{index, range, center}], tubes_per_unit, tube_r, form,
    shutters: [{pod, center, box, kind}]}."""
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
    elif layout.startswith("cluster"):
        n, ok = _layout_count(layout, "cluster")
        if not ok:
            raise NotImplementedError(f"{who}: layout {layout} desconhecido")
        cap = [round(2 * tube_r, 4), round(2 * tube_r, 4)]
        for p_i, pod in enumerate(all_pods):
            rows = _pod_tubes(pod, who)
            if len(rows) < 2 or min(len(r) for r in (rows[0], rows[-1])) < 2:
                raise NotImplementedError(f"{who}: {layout} precisa de casulos com fileiras de tras e da frente >= 2")
            corners = {(0, 0), (0, len(rows[0]) - 1), (len(rows) - 1, 0), (len(rows) - 1, len(rows[-1]) - 1)}
            start = len(units)
            for r, row in enumerate(rows):
                for c, t in enumerate(row):
                    if (r, c) in corners:
                        units.append({"pos": list(t), "tubes": [list(t)], "pod": p_i, "form": "tube"})
                    else:
                        # celula do meio: tampa fixa (o portador gordo ocupa o espaco dela)
                        shutters.append({"pod": p_i, "center": list(t), "box": list(cap), "kind": "cap"})
            pods.append({"index": p_i, "range": [start, len(units)], "center": [pod["center"][1], pod["center"][0]]})
        if n is not None and len(units) != n:
            raise ValueError(f"{who}: layout {layout} gera {len(units)} portadores (4 cantos por casulo)")
    elif layout.startswith("heavy"):
        n, ok = _layout_count(layout, "heavy")
        if not ok:
            raise NotImplementedError(f"{who}: layout {layout} desconhecido")
        total_rows = sum(len(_pod_rows(p, who)) for p in all_pods)
        if n is None:
            rpu = 1
        elif n <= 0 or total_rows % n:
            raise ValueError(f"{who}: layout {layout}: {total_rows} fileiras nao dividem em {n} unidades")
        else:
            rpu = total_rows // n
        for p_i, pod in enumerate(all_pods):
            start = len(units)
            px, py = pod["pitch"]
            rows = _pod_tubes(pod, who)
            if len(rows) % rpu:
                raise ValueError(f"{who}: layout {layout}: casulo {p_i} com {len(rows)} fileiras, bloco de {rpu}")
            for r0 in range(0, len(rows), rpu):
                block = rows[r0:r0 + rpu]
                tubes = [t for row in block for t in row]
                w = max(len(row) for row in block)
                box = [round((w - 1) * px + 2 * tube_r, 4),
                       round((rpu - 1) * py + min(py * 0.96, 4 * tube_r), 4)]
                units.append({"pos": _mean(tubes), "tubes": tubes, "pod": p_i, "form": "heavy", "box": box})
            pods.append({"index": p_i, "range": [start, len(units)], "center": [pod["center"][1], pod["center"][0]]})
    elif layout.startswith("torpedo"):
        # so a Iara: N casulos internos com o nariz grande, os externos com a persiana fechada
        m = re.fullmatch(r"torpedo(\d+)_inner", layout)
        if not m:
            raise NotImplementedError(f"{who}: layout {layout} desconhecido (na 2.0 so existe torpedo<N>_inner)")
        n = int(m.group(1))
        inner = sorted(range(len(all_pods)), key=lambda i: (abs(all_pods[i]["center"][0]), i))[:n]
        chosen = sorted(inner)
        for p_i in range(len(all_pods)):
            pod = all_pods[p_i]
            c = [round(pod["center"][1], 4), round(pod["center"][0], 4)]
            box = _pod_box(pod, tube_r, who)
            if p_i not in chosen:
                shutters.append({"pod": p_i, "center": c, "box": box, "kind": "pod"})
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


# ----------------------------------------------------------------------------- conferencia
def _all_tubes(cells, who):
    out = set()
    for pod in cells["pods"]:
        for row in _pod_tubes(pod, who):
            for t in row:
                out.add((round(t[0], 4), round(t[1], 4)))
    return out


def check_layout(cells, layout, rack_units, turret_box, who="lancador"):
    """Problemas (lista vazia = OK) de um modo: contagem, posicoes unicas, unidades dentro dos casulos, retangulos
    das sobreposicoes dentro do quadro da torre e cobrindo os narizes, tampas sem tubo de unidade, box nos nariz
    heavy/torpedo."""
    errs = []
    try:
        lay = cell_layout(cells, layout, rack_units, who)
    except (ValueError, NotImplementedError) as e:
        return [str(e)]
    units = lay["units"]
    tubes = _all_tubes(cells, who)
    T = int(round(turret_box * PX))
    pos = [tuple(u["pos"]) for u in units]
    if len(set(pos)) != len(pos):
        errs.append(f"{who}/{layout}: unidades com a mesma posicao")
    used = set()
    for i, u in enumerate(units):
        for t in u["tubes"]:
            k = (round(t[0], 4), round(t[1], 4))
            if u["form"] != "torpedo" and k not in tubes:
                errs.append(f"{who}/{layout}: unidade {i} fora dos tubos do casulo")
            if k in used and u["form"] != "torpedo":
                errs.append(f"{who}/{layout}: tubo {k} em duas unidades")
            used.add(k)
        if u["form"] in ("heavy", "torpedo") and not (u.get("box") and min(u["box"]) > 0):
            errs.append(f"{who}/{layout}: unidade {i} ({u['form']}) sem box")
    for sh in lay["shutters"]:
        k = (round(sh["center"][0], 4), round(sh["center"][1], 4))
        if sh["kind"] == "cap" and k in used:
            errs.append(f"{who}/{layout}: tampa em cima do tubo de uma unidade {k}")
    if len({tuple(sh["box"]) for sh in lay["shutters"]}) > 1:
        errs.append(f"{who}/{layout}: tampas com box diferentes (o renderizador desenha uma so)")
    covered = 0
    for pod in lay["pods"]:
        a, b = pod["range"]
        rect = overlay_rect(units[a:b], lay["tube_r"], turret_box)
        if not (0 <= rect[0] < rect[2] <= T and 0 <= rect[1] < rect[3] <= T):
            errs.append(f"{who}/{layout}: retangulo do casulo {pod['index']} {rect} fora do quadro {T}")
        for u in units[a:b]:
            if u["pod"] != pod["index"]:
                errs.append(f"{who}/{layout}: unidade fora do casulo {pod['index']}")
            x, y = T / 2 + u["pos"][1] * PX, T / 2 - u["pos"][0] * PX
            if not (rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]):
                errs.append(f"{who}/{layout}: unidade em ({x:.1f}, {y:.1f}) fora do retangulo {rect}")
        covered += b - a
    if covered != len(units):
        errs.append(f"{who}/{layout}: as faixas dos casulos cobrem {covered} de {len(units)} unidades")
    return errs


def selftest(mspec=None):
    """Confere todo modo de todo lancador do spec (tools/spec/bullet_strike_missiles.json): lista de problemas."""
    if mspec is None:
        import json
        import os
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec", "bullet_strike_missiles.json")
        with open(p, encoding="utf-8") as fh:
            mspec = json.load(fh)
    errs = []
    for L in mspec["launchers"]:
        pm = L["art"]["part_meta"]
        for m in L["modes"]:
            errs += check_layout(pm["cells"], m["layout"], m["rack_units"], pm["turret_box"],
                                 f"{L['codename']}/{m['missile_type']}")
    # layouts removidos na 2.0 tem que falhar (so torpedo<N>_inner fica, para a Iara)
    probe = {"pods": [{"center": [0, 0], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}], "tube_r": 0.09}
    for gone in ("torpedo2", "torpedo4"):
        try:
            cell_layout(probe, gone)
            errs.append(f"layout {gone} ainda existe")
        except NotImplementedError:
            pass
    return errs


if __name__ == "__main__":
    import sys
    probs = selftest()
    for p in probs:
        print(f"ERRO: {p}")
    print("launcher_layout selftest: " + ("OK" if not probs else f"{len(probs)} problema(s)"))
    sys.exit(1 if probs else 0)
