"""Confere a arte 3D (art3d/) sem gravar o mod: meta.json, arquivos, tamanhos, alfa, normais, emissivo e, com o
modulo de dados integrado, a geracao das regras com o meta (spec 2.0 art_assets.check_art3d_scopes; dono WP10).

    python3 tools/check_art3d.py todos [--estrito]          # todas as pastas de art3d/
    python3 tools/check_art3d.py --pacote WPxx [--estrito]  # so as pastas do dono WPxx (art3d_owner_map)
    python3 tools/check_art3d.py <pasta> [<pasta> ...]      # pastas de art3d/ pelo nome (ex.: bs_boiuna_ac)
    python3 tools/check_art3d.py <caminho>                  # rascunho fora de art3d/ (projeteis ou layered)

ERRO = defeito real de arte (arquivo do meta faltando, px do sprite, normais, alfa, emissivo, conjunto incompleto,
id do meta diferente da peca) ou, com o modulo de dados integrado (API >= 2), divergencia com o DATA (o gerador das
regras falha com o meta). AVISO (sai 0) = pasta legado 1.x, pasta cujo modulo de dados ainda nao esta integrado (so
a arte e conferida, com o tamanho do SPEC), lacunas de arte com dono (art_gaps do addendum: AC s/m/l guiadas,
celulas cluster8/heavy8, buff_fita...) e numeros do meta diferentes do spec (o meta vence: addendum G0).
--estrito (WP14b) trata todo AVISO como ERRO. Nada aqui chama sys.exit dentro do laco: uma excecao numa pasta
vira ERRO daquela pasta e o laco segue. Sai com 1 se houver ERRO.

Tipos (meta "kind"): gun (armas, defesas, PEM), launcher, factory, resource, missiles/shells (projeteis em voo,
CONTRATOS secao 3 / STYLE.md 8.4, 10, 11), layered (render_layered.py: Tupa, paiois [meta shared], Fita, FX da Fita,
placas) e ui_icons (art3d/bs_ui_icons2/icons.json, 96 x 96). A peca de cada pasta vem do DATA (bs_data): GUNS /
DEFENSES / PEM por art3d_dir (bs_boiuna_ac -> rafaeltessaro.bs_nuke_howitzer), LAUNCHERS, RESOURCES, FACTORIES
(F2 = bs_factory_special), RAIL (SPEC.railgun.parts) e paiol/Fita (SPEC.paiol / fita_teleporte). Pasta sem entrada no
art3d_owner_map do spec = ERRO.
"""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import art3d as A3  # noqa: E402

PX = 64


def _size(short, name):
    return Image.open(A3.path(short, name)).size


def _solid_bbox(img):
    return img.convert("RGBA").getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()


# ============================================================================ spec / dados (carga preguicosa)
_CACHE = {}


def data():
    """bs_data (DATA 2.0 do WP01). Importado so quando preciso (projeteis num rascunho nao precisam)."""
    if "D" not in _CACHE:
        import bs_data as D
        _CACHE["D"] = D
    return _CACHE["D"]


def art2():
    """SPEC.art_assets (tools/spec/bullet_strike_art2.json, gerado pelo tools/spec2_split.py)."""
    if "A2" not in _CACHE:
        p = os.path.join(A3.ROOT, "tools", "spec", "bullet_strike_art2.json")
        with open(p, encoding="utf-8") as fh:
            _CACHE["A2"] = json.load(fh)["art_assets"]
    return _CACHE["A2"]


def owner_map():
    """{pasta: entrada do art3d_owner_map} (dono, tipo, dados, legado, sai_em)."""
    if "OM" not in _CACHE:
        om = {}
        for e in art2().get("art3d_owner_map", {}).get("entries", []):
            for d in e["dirs"]:
                om[d] = e
        _CACHE["OM"] = om
    return _CACHE["OM"]


def module_api(name):
    """API do modulo de dados (0 = nao existe; -1 = nao importa; 1 = 1.x)."""
    key = ("api", name)
    if key not in _CACHE:
        import importlib
        import importlib.util
        try:
            if importlib.util.find_spec(name) is None:
                _CACHE[key] = 0
            else:
                _CACHE[key] = int(getattr(importlib.import_module(name), "API", 1) or 1)
        except Exception:  # noqa: BLE001
            _CACHE[key] = -1
    return _CACHE[key]


def data_modules(entry):
    """Modulos 'bsgen.<x>' citados em 'dados' da entrada do owner map."""
    import re
    return re.findall(r"bsgen\.[a-z_]+", (entry or {}).get("dados", ""))


def integrated(entry):
    """(True, '') se todo modulo de dados da pasta tem API >= 2 (e os lancadores estao no DATA); senao (False,
    motivo)."""
    mods = data_modules(entry)
    why = [f"{m} API {module_api(m)}" for m in mods if module_api(m) < 2]
    if "D.LAUNCHERS" in (entry or {}).get("dados", "") and not data().LAUNCHERS:
        why.append("D.LAUNCHERS == []")
    return (not why), ", ".join(why)


class AnyPaths(dict):
    """shot_paths de mentira para os geradores (qualquer chave -> 'x.rules')."""

    def __missing__(self, k):
        return "x.rules"

    def get(self, k, default=None):
        return "x.rules"


def try_build(fn, *args):
    """Chama um gerador das regras com o meta e renderiza; devolve (linhas, None) ou (None, erro). Assinatura que
    nao aceita estes argumentos (gerador 2.0 com outra API) = (None, "assinatura: ...") e quem chama AVISA (as regras
    ficam com o selfcheck do proprio modulo)."""
    import inspect
    from rules_dsl import render
    try:
        inspect.signature(fn).bind(*args)
    except TypeError as e:
        return None, f"assinatura: {getattr(fn, '__module__', '')}.{getattr(fn, '__name__', fn)}{e}"
    except ValueError:
        pass
    try:
        res = fn(*args)
        top = res[0] if isinstance(res, tuple) else res
        return len(render(top, "teste").splitlines()), None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


class Report:
    """Erros e avisos de uma pasta (o aviso vira erro com --estrito)."""

    def __init__(self, name):
        self.name = name
        self.errs, self.warns, self.notes = [], [], []

    def err(self, msg):
        self.errs.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def note(self, msg):
        self.notes.append(msg)


# ============================================================================ recursos
def check_resource(short, meta, D, errs):
    """Recurso: icone/nugget 64 x 64, overlay 128 x 128, stack_1..MaxStackSize, nugget do tamanho de uma unidade
    da pilha (o tripulante carrega uma unidade; o nugget nao pode ser maior que a unidade empilhada)."""
    r = next((x for x in D.RESOURCES if (x.get("art3d_dir") or x["dir"]) == short or x["dir"] == short), None)
    if r is None:
        errs.append(f"{short} nao e recurso do spec")
        return
    for n in ("icon.png", "nugget.png", "nugget_normals.png"):
        if n not in meta["files"]:
            errs.append(f"falta {n}")
        elif _size(short, n) != (64, 64):
            errs.append(f"{n}: {_size(short, n)}, esperado (64, 64)")
    if "overlay.png" not in meta["files"]:
        errs.append("falta overlay.png")
    elif _size(short, "overlay.png") != (128, 128):
        errs.append(f"overlay.png: {_size(short, 'overlay.png')}, esperado (128, 128)")
    want = {f"stack_{i}.png" for i in range(1, r["max_stack"] + 1)}
    have = {n for n in meta["files"] if n.startswith("stack_")}
    if want != have:
        errs.append(f"pilhas {sorted(have)} diferem de stack_1..stack_{r['max_stack']} (MaxStackSize)")
    for n in sorted(want & have):
        if _size(short, n) != (64, 64):
            errs.append(f"{n}: {_size(short, n)}, esperado (64, 64)")
    if "stack_1.png" in have and "nugget.png" in meta["files"]:
        nug = Image.open(A3.path(short, "nugget.png"))
        f = A3.nugget_factor(short, meta)
        if f:
            print(f"nota: nugget renderizado com icon_scale; o build reduz a {f:.2f} (re-renderize o recurso)")
            nug = A3.scaled_center(nug, f)
        nb, sb = _solid_bbox(nug), _solid_bbox(Image.open(A3.path(short, "stack_1.png")))
        if nb and sb:
            nw, nh = nb[2] - nb[0], nb[3] - nb[1]
            sw, sh = sb[2] - sb[0], sb[3] - sb[1]
            if max(nw, nh) > 1.15 * max(sw, sh) + 2:
                errs.append(f"nugget {nw}x{nh} px maior que a unidade da pilha {sw}x{sh} px")
    if meta.get("id") and meta["id"] != r["id"]:
        errs.append(f"id do meta {meta['id']} difere do recurso {r['id']}")
    print(f"recurso: pilha {r['max_stack']}, arquivos {len(meta['files'])}")


def _resource(short, meta, rep):
    D = data()
    r = next((x for x in D.RESOURCES if (x.get("art3d_dir") or x["dir"]) == short), None)
    if r is None:
        sp = next((x for x in D.SPEC.get("resources", []) if x["id"].split(".", 1)[1] == short), None)
        if sp is None:
            rep.err(f"{short} nao e recurso do spec")
        else:
            rep.warn(f"recurso {sp['id']} fora do DATA deste build (switches); so a arte")
        return
    check_resource(short, meta, D, rep.errs)
    want = next((a.get("files") for a in art2()["assets"].get("resources", []) if a.get("id") == r["id"]), None)
    if want and sorted(want) != sorted(meta["files"]):
        rep.warn(f"arquivos {sorted(set(meta['files']) ^ set(want))} diferem de art_assets.assets.resources "
                 f"(o meta vence)")


# ============================================================================ fabricas
def _cells(rect):
    x, y, w, h = rect
    return [(x + i, y + j) for i in range(w) for j in range(h)]


def check_factory(short, meta, D, errs, rep=None):
    """Fabrica: casco (piso, paredes, teto, normais, luzes) do tamanho da peca, quadros da maquina iguais, camadas
    extras (overlays: px = rect x 64, normais, quadros), placa de modo (mode_plate) e grade (grid) dentro da peca."""
    import numpy as np
    rep = rep or Report(short)
    f = next((x for x in D.FACTORIES if (x.get("art3d_dir") or x["short"]) == short), None)
    if f is None:
        errs.append(f"{short} nao e fabrica do spec")
        return
    W, H = f["size"]
    if list(meta.get("size", [])) != [W, H]:
        errs.append(f"tamanho {meta.get('size')} difere do spec {f['size']}")
        return
    if meta.get("id") != f["id"]:
        errs.append(f"id do meta {meta.get('id')} difere da fabrica {f['id']}")
    for key, n in meta.get("hull", {}).items():
        if _size(short, n) != (W * PX, H * PX):
            errs.append(f"{n} ({key}): {_size(short, n)}, esperado {(W * PX, H * PX)}")
    hull = meta.get("hull", {})
    if hull.get("roof") and hull.get("roof_normals"):
        a = np.asarray(Image.open(A3.path(short, hull["roof"])).convert("RGBA"))[..., 3].astype(int)
        b = np.asarray(Image.open(A3.path(short, hull["roof_normals"])).convert("RGBA"))[..., 3].astype(int)
        if a.shape == b.shape and (np.abs(a - b) > 8).mean() > 0.01:
            errs.append("alfa de roof_normals difere do alfa de roof")
    mc = meta["machine"]
    mw, mh = mc.get("size", [W, H])
    frames = list(mc["frames"]) + [mc["off"]]
    sizes = {n: _size(short, n) for n in frames}
    if len(set(sizes.values())) != 1:
        errs.append(f"quadros da maquina com tamanhos diferentes: {sorted(set(sizes.values()))}")
    if (mw * PX, mh * PX) not in sizes.values():
        errs.append(f"quadros da maquina {sorted(set(sizes.values()))}, esperado {(mw * PX, mh * PX)}")
    for name, ov in (meta.get("overlays") or {}).items():
        _x, _y, w, h = ov["rect"]
        want = (int(round(w * PX)), int(round(h * PX)))
        for fn in ov["files"]:
            sz = _size(short, fn)
            if abs(sz[0] - want[0]) > 1 or abs(sz[1] - want[1]) > 1:
                errs.append(f"overlay {name}: {fn} {sz} difere do rect {want}")
        for fn, nf in zip(ov["files"], ov.get("normals") or []):
            a = np.asarray(Image.open(A3.path(short, fn)).convert("RGBA"))[..., 3].astype(int)
            b = np.asarray(Image.open(A3.path(short, nf)).convert("RGBA"))[..., 3].astype(int)
            if a.shape == b.shape and (np.abs(a - b) > 8).mean() > 0.01:
                errs.append(f"overlay {name}: alfa de {nf} difere de {fn}")
        n_want = ov.get("frames") or ov.get("levels")
        if n_want and len(ov["files"]) != int(n_want):
            errs.append(f"overlay {name}: {len(ov['files'])} arquivos, esperado {n_want}")
        r = ov["rect"]
        if r[0] < -1e-6 or r[1] < -1e-6 or r[0] + r[2] > W + 1e-6 or r[1] + r[3] > H + 1e-6:
            errs.append(f"overlay {name}: rect {r} fora da fabrica {W}x{H}")
    mp = meta.get("mode_plate")
    if mp:
        cx, cy = mp["rect_centre"]
        s = float(mp.get("size", 0.8))
        if cx - s / 2 < -1e-6 or cy - s / 2 < -1e-6 or cx + s / 2 > W + 1e-6 or cy + s / 2 > H + 1e-6:
            errs.append(f"mode_plate em {mp['rect_centre']} (size {s}) sai da fabrica {W}x{H}")
        pl = A3.load_meta("bs_placas")
        have = set((pl or {}).get("files", []))
        miss = [m for m in mp.get("modes", []) if f"placa_{m}.png" not in have]
        if miss:
            errs.append(f"mode_plate: art3d/bs_placas sem placa_{miss[0]}.png ({miss})")
    elif f.get("selector"):
        rep.warn(f"fabrica com seletor ({f['selector'] if isinstance(f['selector'], str) else 'modos'}) sem "
                 f"mode_plate no meta")
    grid = meta.get("grid") or {}
    for what, rects in (("bloqueada", [[c[0], c[1], 1, 1] for c in grid.get("blocked", [])]),
                        ("entrada", list((grid.get("inputs") or {}).values())),
                        ("saida", list((grid.get("outputs") or {}).values()))):
        for r in rects:
            if r[0] < 0 or r[1] < 0 or r[0] + r[2] > W or r[1] + r[3] > H:
                errs.append(f"grid: celula {what} {r} fora da fabrica {W}x{H}")
    if grid:
        blocked = {tuple(c) for c in grid.get("blocked", [])}
        pads = list((grid.get("inputs") or {}).values()) + list((grid.get("outputs") or {}).values())
        for r in pads:
            hit = [c for c in _cells(r) if c in blocked]
            if hit:
                errs.append(f"grid: entrada/saida {r} sobre celula bloqueada {hit}")
        # bases livres: o jogo desenha as pilhas nas celulas de entrada/saida e a tripulacao precisa chegar nelas;
        # o maquinario (todos os quadros) nao pode cobrir mais de 1 % de cada uma (STYLE.md 6)
        if [mw, mh] == [W, H] and list(mc.get("offset", [0, 0])) == [0, 0]:
            alphas = [np.asarray(Image.open(A3.path(short, n)).convert("RGBA"))[..., 3] for n in frames]
            worst = 0.0
            for r in pads:
                for cx, cy in _cells(r):
                    x0, y0 = cx * PX + 3, cy * PX + 3
                    cov = max(float((a[y0:y0 + PX - 6, x0:x0 + PX - 6] > 60).mean()) for a in alphas)
                    worst = max(worst, cov)
                    if cov > 0.01:
                        errs.append(f"maquina cobre {cov:.1%} da celula de entrada/saida [{cx},{cy}]")
            rep.note(f"bases livres: cobertura maxima da maquina {worst:.2%}")
    ad = meta.get("art3d_dir")
    if ad and ad != short:
        errs.append(f"meta.art3d_dir {ad} difere da pasta {short}")
    sa = (art2()["assets"].get("factories") or {}).get(f["code"]) or {}
    if sa.get("machine_frames") and sa["machine_frames"] != len(mc["frames"]):
        rep.warn(f"{len(mc['frames'])} quadros de maquina, o spec diz {sa['machine_frames']} (o meta vence)")
    if sa.get("machine_interval_s") and abs(sa["machine_interval_s"] - mc.get("interval", 0)) > 1e-6:
        rep.warn(f"intervalo da maquina {mc.get('interval')}, o spec diz {sa['machine_interval_s']} (o meta vence)")
    print(f"fabrica {f['code']}: {len(mc['frames'])} quadros de maquina, casco {W}x{H}, "
          f"camadas extras {sorted(meta.get('overlays') or {})}, placa {'sim' if mp else 'nao'}")


def _factory(short, meta, rep, entry):
    D = data()
    f = next((x for x in D.FACTORIES if (x.get("art3d_dir") or x["short"]) == short), None)
    if f is None:
        rep.err(f"{short} nao e fabrica do DATA (F1-F6 por art3d_dir)")
        return
    check_factory(short, meta, D, rep.errs, rep)
    ok, why = integrated(entry)
    if not ok:
        rep.warn(f"modulo de dados nao integrado ({why}): so a arte")
        return
    from bsgen import factory
    stacks = {r["id"]: r["max_stack"] for r in D.RESOURCES}
    fn = getattr(factory, "build_factory", None)
    if fn is None:
        rep.warn("bsgen.factory sem build_factory(): regras nao conferidas aqui (selfcheck do modulo)")
        return
    f2 = dict(f, art3d=meta)
    n, e = try_build(fn, f2, stacks)
    if e and e.startswith("assinatura"):
        rep.warn(f"regras da fabrica nao conferidas aqui ({e}); ficam com o selfcheck do bsgen.factory")
    elif e:
        rep.err(f"bsgen.factory.build_factory falhou com este meta: {e}")
    else:
        print(f"regras geradas: {n} linhas")


# ============================================================================ projeteis
PROJ_KINDS = ("missiles", "shells")
PROJ_PPT = {"missiles": 64, "shells": 128}
PROJ_NAMES = {"missiles": ("msl_{k}.png", "msl_{k}_normals.png", "msl_{k}_lights.png", None),
              "shells": ("bs_shell_{k}.png", "bs_shell_{k}_normals.png", "bs_shell_{k}_lights.png",
                         "bs_shell_band_{k}.png")}
PROJ_IDS = {"missiles": ("rafaeltessaro.bs_missiles", "rafaeltessaro.bs_missiles2"),
            "shells": ("rafaeltessaro.bs_shells", "rafaeltessaro.bs_shells2")}
SHELL_KEYS = ("he", "ap", "nuke")          # 1.x (art3d/bs_shells, sai no WP14b)
ALPHA_SOLID = 100           # alfa que conta como "corpo" (STYLE.md 9, ilhas flutuantes)
EMISSIVE_MAX = 0.03         # area acesa do quadro 0 / area do corpo
EMISSIVE_MAX_NUCLEAR = 0.04  # Iara / granada nuclear: faixas largas que respiram
ANCHORS = ("seeker", "warhead", "radiation", "tip")
AC_GUIDED_GAP = ("ac_s", "ac_m", "ac_l")   # art_gaps do addendum (dono WP11): ainda guiadas no BASE


def shell_keys_2():
    """As 18 chaves 2.0 das granadas (SPEC.art_assets.shell_ladder.items)."""
    return list(art2()["shell_ladder"]["items"])


def _components(mask):
    """Tamanhos dos componentes conectados (vizinhanca de 8) de uma mascara booleana (sem scipy)."""
    m = mask.tolist()
    h, w = len(m), len(m[0]) if m else 0
    seen = [[False] * w for _ in range(h)]
    sizes = []
    for y in range(h):
        for x in range(w):
            if m[y][x] and not seen[y][x]:
                seen[y][x] = True
                stack, n = [(y, x)], 0
                while stack:
                    cy, cx = stack.pop()
                    n += 1
                    for ny in (cy - 1, cy, cy + 1):
                        if 0 <= ny < h:
                            row, srow = m[ny], seen[ny]
                            for nx in (cx - 1, cx, cx + 1):
                                if 0 <= nx < w and row[nx] and not srow[nx]:
                                    srow[nx] = True
                                    stack.append((ny, nx))
                sizes.append(n)
    return sorted(sizes, reverse=True)


def _nuclear(key, it):
    return bool(it.get("nuclear")) or key.startswith("nuclear") or key == "nuke"


def _proj_table(kind, mid=None):
    """Tabela de arte do spec: misseis 2.0 = art_assets.assets.missiles.items; misseis 1.x =
    tools/spec/bullet_strike_missile_fx.json; granadas 2.0 = art_assets.shell_ladder.items."""
    if kind == "shells":
        return shell_ladder_table() if mid == "rafaeltessaro.bs_shells2" else None
    if mid == "rafaeltessaro.bs_missiles2":
        # os itens do spec 2.0 sao textos (descricao do trabalho de arte): toda chave conta para a
        # conferencia de chaves; px/luzes so sao conferidos quando o item e um dict
        its = (art2()["assets"].get("missiles") or {}).get("items") or {}
        return {k: ({"canvas_px": v.get("canvas_px") or v.get("px"), "lights": v.get("lights")}
                    if isinstance(v, dict) else None) for k, v in its.items()} or None
    p = os.path.join(A3.ROOT, "tools", "spec", "bullet_strike_missile_fx.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        t = json.load(fh)
    return t.get("items") or t.get("art", {}).get("items")


def shell_ladder_table():
    out = {}
    for k, v in art2()["shell_ladder"]["items"].items():
        lt = v.get("lights") or {}
        # 'anchors' = o contrato 2.0 (None/{} = sem ancora: AC s/m/l nao guiadas); 'anchors_meta' = o que o
        # meta do BASE tinha (so registro)
        nf = int(lt.get("frames") or 0)
        out[k] = {"canvas_px": v.get("canvas_px") or v.get("px"),
                  # 1 quadro com fps 0 = atlas parado (AC s/m/l, WP11); 1 quadro sem fps 0 = sem atlas
                  "lights": lt if nf > 1 or (nf == 1 and lt.get("fps") == 0) else None,
                  "mask": v.get("mask"), "anchors": v.get("anchors") or {}}
    return out


def check_projectiles(d, meta, errs, warns=None):
    """Folha de projeteis (misseis 64 px/tile, granadas 128 px/tile) na pasta d. warns: lista de AVISOS (meta
    diferente do spec, lacunas com dono); sem ela os avisos so sao impressos."""
    import numpy as np
    warns = warns if warns is not None else []
    kind = meta["kind"]
    ppt = meta.get("px_per_tile")
    if ppt != PROJ_PPT[kind]:
        errs.append(f"px_per_tile {ppt}, o contrato pede {PROJ_PPT[kind]} para '{kind}'")
        ppt = ppt or PROJ_PPT[kind]
    for k in ("version", "id", "items", "files"):
        if k not in meta:
            errs.append(f"meta.json sem '{k}'")
    files = set(meta.get("files", []))
    for f in sorted(files):
        if not os.path.exists(os.path.join(d, f)):
            errs.append(f"meta.files cita {f}, que nao existe")
    nf, nn, nl, nm = PROJ_NAMES[kind]
    items = meta.get("items", {})
    mid = meta.get("id")
    canon = mid in PROJ_IDS[kind]
    v2 = mid in ("rafaeltessaro.bs_shells2", "rafaeltessaro.bs_missiles2")
    table = _proj_table(kind, mid) if canon else None
    if canon and kind == "shells":
        want = shell_keys_2() if v2 else list(SHELL_KEYS)
        miss = [k for k in want if k not in items]
        if miss:
            errs.append(f"faltam as granadas {miss} (contrato {'2.0: shell_ladder.items' if v2 else '1.x'})")
    if canon and kind == "missiles":
        if table is None:
            print("nota: sem tabela de arte dos misseis; chaves/quadros nao conferidos")
        else:
            miss = sorted(set(table) - set(items))
            if miss:
                errs.append(f"faltam os misseis {miss} (tabela de arte)")
    used = set()

    def img(name, what):
        if not name:
            return None
        used.add(name)
        if name not in files:
            errs.append(f"{what}: {name} nao esta em meta.files")
        p = os.path.join(d, name)
        if not os.path.exists(p):
            errs.append(f"{what}: {name} nao existe")
            return None
        return Image.open(p).convert("RGBA")
    report = []
    for key, it in items.items():
        tag = f"{key}"
        L, W = it["size"]
        pw, ph = it["px"]
        if abs(pw - L * ppt) > 1 or abs(ph - W * ppt) > 1:
            errs.append(f"{tag}: px {it['px']} difere de size {it['size']} x {ppt}")
        for fld, pat in (("file", nf), ("normals", nn)):
            if it.get(fld) != pat.format(k=key):
                errs.append(f"{tag}: {fld} = {it.get(fld)}, o contrato pede {pat.format(k=key)}")
        dif = img(it.get("file"), tag)
        nor = img(it.get("normals"), tag + " normais")
        if dif is None:
            continue
        if dif.size != (pw, ph):
            errs.append(f"{tag}: {it['file']} tem {dif.size}, esperado {(pw, ph)}")
        a = np.asarray(dif, dtype=np.uint8)[..., 3]
        solid = a > ALPHA_SOLID
        if not solid.any():
            errs.append(f"{tag}: sprite vazio")
            continue
        comps = _components(solid)
        big = [c for c in comps if c >= 3]
        if len(big) != 1:
            errs.append(f"{tag}: {len(big)} componentes de alfa (tamanhos {big[:6]}); o sprite precisa ser UMA peca")
        elif len(comps) > 1:
            print(f"nota: {tag}: {len(comps) - 1} pixel(s) solto(s) de alfa > {ALPHA_SOLID} (antisserrilhado)")
        ys, xs = np.where(a > 40)
        if xs.min() == 0 or xs.max() == pw - 1:
            print(f"nota: {tag}: o sprite encosta na lateral da tela (bbox x {xs.min()}..{xs.max()} de {pw}); "
                  f"nariz/bocal cortado?")
        if ys.min() == 0 or ys.max() == ph - 1:
            print(f"nota: {tag}: o sprite encosta em cima/embaixo da tela (bbox y {ys.min()}..{ys.max()} de {ph})")
        if nor is not None:
            if nor.size != dif.size:
                errs.append(f"{tag}: normais {nor.size} difere do difuso {dif.size}")
            else:
                na = np.asarray(nor, dtype=np.int16)[..., 3]
                if (np.abs(na - a.astype(np.int16)) > 8).mean() > 0.01:
                    errs.append(f"{tag}: o alfa das normais nao e o do difuso")
        lit = int((a >= 128).sum())
        lt = it.get("lights")
        frac = 0.0
        if lt:
            if lt.get("file") != nl.format(k=key):
                errs.append(f"{tag}: lights.file = {lt.get('file')}, o contrato pede {nl.format(k=key)}")
            n = int(lt.get("frames", 0))
            fw, fh = lt.get("frame_px", [0, 0])
            per = lt.get("per_row")
            # atlas PARADO de 1 quadro (fps 0; WP11: AC s/m/l de bs_shells2, SPEC shell_ladder.items.ac_s.lights) =
            # sprite aditivo parado no jogo (fxkit.art_sprite_components); fora isso, 1 quadro = lights null
            static = n == 1 and lt.get("fps") == 0
            if n < 2 and not static:
                errs.append(f"{tag}: lights com {n} quadro(s); com 1 quadro o atlas e omitido (lights = null)")
            if [fw, fh] != [pw, ph]:
                errs.append(f"{tag}: lights.frame_px {lt.get('frame_px')} difere de px {it['px']}")
            if per != n:
                errs.append(f"{tag}: lights.per_row {per} (o atlas e UMA fileira: per_row = frames = {n})")
            if not static and (not lt.get("fps") or lt["fps"] <= 0):
                errs.append(f"{tag}: lights.fps invalido ({lt.get('fps')})")
            if lt.get("wrap") not in (None, "Clamp"):
                errs.append(f"{tag}: lights.wrap = {lt.get('wrap')} (null ou \"Clamp\")")
            at = img(lt.get("file"), tag + " luzes")
            if at is not None:
                want = (n * pw, ph)
                if at.size != want:
                    errs.append(f"{tag}: atlas {at.size}, esperado {want} (n x w)")
                else:
                    f0 = np.asarray(at.crop((0, 0, pw, ph)), dtype=np.uint8)
                    on = (f0[..., 3] >= 128) & (f0[..., :3].max(axis=2) > 16)
                    frac = on.sum() / max(1, lit)
                    lim = EMISSIVE_MAX_NUCLEAR if _nuclear(key, it) else EMISSIVE_MAX
                    if frac > lim:
                        errs.append(f"{tag}: quadro 0 com {frac:.1%} de area acesa (limite {lim:.0%}; STYLE.md 11)")
                    for k in range(n):
                        if not at.crop((k * pw, 0, (k + 1) * pw, ph)).getchannel("A").getbbox():
                            print(f"nota: {tag}: quadro {k + 1} do atlas de luzes esta vazio (tudo apagado)")
        if it.get("mask"):
            if not nm:
                errs.append(f"{tag}: mascara de faixa so existe em granadas")
            elif it["mask"] != nm.format(k=key):
                errs.append(f"{tag}: mask = {it['mask']}, o contrato pede {nm.format(k=key)}")
            mk = img(it["mask"], tag + " mascara")
            if mk is not None:
                if mk.size != dif.size:
                    errs.append(f"{tag}: mascara {mk.size} difere do difuso {dif.size}")
                else:
                    m = np.asarray(mk, dtype=np.int16)
                    vis = m[..., 3] > 8
                    if not vis.any():
                        errs.append(f"{tag}: mascara vazia")
                    elif not (m[..., 3] == 0).any():
                        errs.append(f"{tag}: mascara sem fundo transparente")
                    else:
                        rgb = m[..., :3][vis]
                        if (rgb.max(axis=1) - rgb.min(axis=1)).max() > 6:
                            errs.append(f"{tag}: mascara colorida (precisa ser cinza/branca; o jogo tinge com "
                                        f"VertexColor)")
                        elif rgb.mean() < 200:
                            errs.append(f"{tag}: mascara escura (media {rgb.mean():.0f}; precisa ser branca)")
                        out = (m[..., 3] > ALPHA_SOLID) & (a <= 8)
                        if out.sum() > 0.02 * max(1, (m[..., 3] > ALPHA_SOLID).sum()):
                            errs.append(f"{tag}: mascara fora do corpo do projetil")
        noz = it.get("nozzle")
        if not (isinstance(noz, list) and len(noz) == 2 and all(isinstance(v, (int, float)) for v in noz)):
            errs.append(f"{tag}: nozzle {noz} (precisa ser [x, 0])")
        elif abs(noz[0]) > L / 2 + 0.05:
            print(f"nota: {tag}: nozzle x {noz[0]} fora da tela (meio comprimento {L / 2})")
        for an, v in (it.get("anchors") or {}).items():
            if an not in ANCHORS:
                warns.append(f"{tag}: ancora '{an}' fora do contrato ({', '.join(ANCHORS)})")
            if abs(v[0]) > L / 2 + 0.05 or abs(v[1]) > W / 2 + 0.05:
                print(f"nota: {tag}: ancora '{an}' {v} fora da tela")
        if table and table.get(key):
            tr = table[key]
            gap = kind == "shells" and v2 and key in AC_GUIDED_GAP
            pre = "LACUNA WP11 (AC s/m/l ainda guiada): " if gap else ""
            if tr.get("canvas_px") and list(tr["canvas_px"]) != list(it["px"]):
                warns.append(f"{pre}{tag}: px {it['px']} difere do spec {tr.get('canvas_px')} (o meta vence)")
            tl = tr.get("lights")
            if bool(tl) != bool(lt):
                fr = lambda x: f"{x.get('frames')} quadros" if x else "1 quadro, sem atlas"  # noqa: E731
                warns.append(f"{pre}{tag}: atlas de luzes {'ausente' if tl else 'sobrando'} "
                             f"(spec: {fr(tl)}; meta: {fr(lt)})")
            elif tl and (tl.get("frames") != lt.get("frames") or tl.get("fps") != lt.get("fps") or
                         (tl.get("WrapMode") or tl.get("wrap")) != lt.get("wrap")):
                warns.append(f"{pre}{tag}: luzes {lt.get('frames')} quadros / {lt.get('fps')} fps / {lt.get('wrap')} "
                             f"diferem do spec {tl.get('frames')} / {tl.get('fps')} / "
                             f"{tl.get('WrapMode') or tl.get('wrap')}")
            if kind == "shells" and v2:
                want_an = set((tr.get("anchors") or {}).keys())
                have_an = set((it.get("anchors") or {}).keys())
                if want_an != have_an:
                    warns.append(f"{pre}{tag}: ancoras {sorted(have_an)} diferem do spec {sorted(want_an)}")
                if tr.get("mask") and not it.get("mask"):
                    errs.append(f"{tag}: falta a mascara da faixa ({nm.format(k=key)}; shell_ladder.items.mask)")
        if canon and not v2 and kind == "shells" and key == "nuke" and lt and (lt.get("frames") != 4 or
                                                                              lt.get("fps") != 6):
            errs.append(f"{tag}: o contrato pede 4 quadros a 6 fps no atlas da granada nuclear")
        if canon and not v2 and kind == "shells" and key in ("he", "ap") and not it.get("mask"):
            errs.append(f"{tag}: falta a mascara da faixa ({nm.format(k=key)})")
        report.append(f"{key} {pw}x{ph}" + (f" luzes {lt['frames']}q {frac:.1%}" if lt else "") +
                      (" mascara" if it.get("mask") else ""))
    _check_atlases(d, meta, errs, used)
    extra = sorted(files - used)
    if extra:
        print(f"nota: arquivos em meta.files que nenhum item usa: {extra[:6]}")
    print(f"{kind}: {len(items)} itens ({'; '.join(report)})")


def _check_atlases(d, meta, errs, used):
    """Bloco "atlases" (bs_missiles2.py --atlases: petalas da Piranha, formato debris_def do jogo): textura
    quadrada texture_px = per_row x sprite_px, count = per_row^2 (ou menos), normais com o alfa do difuso."""
    import numpy as np
    for name, at in (meta.get("atlases") or {}).items():
        tp, sp, per = int(at.get("texture_px", 0)), int(at.get("sprite_px", 0)), int(at.get("per_row", 0))
        if tp != per * sp or not tp:
            errs.append(f"atlas {name}: texture_px {tp} != per_row {per} x sprite_px {sp}")
        if int(at.get("count", 0)) > per * per or int(at.get("count", 0)) < 1:
            errs.append(f"atlas {name}: count {at.get('count')} fora de 1..{per * per}")
        ims = []
        for fld in ("file", "normals"):
            fn = at.get(fld)
            used.add(fn)
            p = os.path.join(d, fn or "")
            if not fn or not os.path.exists(p):
                errs.append(f"atlas {name}: {fld} {fn} nao existe")
                continue
            im = Image.open(p).convert("RGBA")
            if im.size != (tp, tp):
                errs.append(f"atlas {name}: {fn} {im.size}, esperado {(tp, tp)}")
            ims.append(im)
        if len(ims) == 2 and ims[0].size == ims[1].size:
            a = np.asarray(ims[0])[..., 3].astype(int)
            b = np.asarray(ims[1])[..., 3].astype(int)
            if (np.abs(a - b) > 8).mean() > 0.01:
                errs.append(f"atlas {name}: alfa das normais difere do difuso")


# ============================================================================ kind "layered"
LAYERED_EMISSIVE_MAX = 0.02       # spec render_kinds.layered.check_art3d: <= 2 % nas camadas iluminadas
# Tolerancias APROVADAS por (pasta, camada): arte ja aprovada pelo usuario e pelos revisores que passa dos 2 % neste
# estimador. Valor = pior caso de TODOS os arquivos da camada (medido no WP10, rodada 2) com uma folga pequena. Arte
# aprovada nunca e re-renderizada para caber; um re-render que acenda MAIS que a tolerancia volta a dar ERRO. A pasta
# casa pelo nome da pasta ou pelo id do meta (rascunho fora de art3d/). Documentado no STYLE.md secao 12.
LAYERED_EMISSIVE_ALLOW = {
    ("bs_rail_loader", "projeteis"): (0.03, "dardos do pente com as faixas azuis do Tupa; projeteis6 2,90 %"),
    ("bs_placas", "placa"): (0.065, "cor do codigo do tipo de municao na placa; placa_sap 6,03 %"),
}


def _glow_frac(img, denom=None, chips=()):
    """Fracao de pixels muito claros e saturados (luz acesa) no sprite (denominador: o corpo do sprite ou
    `denom` px). A pintura (verde) nao conta; as cores de `chips` (+-40 por canal) tambem nao: so o chip de familia
    pintado no teto do paiol (_roof_chips). Nas outras camadas nada e isento: o azul do Tupa (45, 115, 255) e o ambar
    HE (255, 170, 60) caem a menos de 40 dos chips e sao luz de verdade."""
    import numpy as np
    a = np.asarray(img.convert("RGBA"), dtype=np.float32)
    solid = a[..., 3] > 128
    rgb = a[..., :3]
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    paint = (g - np.maximum(r, b) > 12) & (np.abs(r - b) < 64)
    chip = np.zeros_like(paint)
    for c in chips:
        chip |= (np.abs(rgb - np.array(c[:3], np.float32)).max(axis=2) < 40)
    hot = solid & (mx >= 235) & (sat >= 0.45) & ~paint & ~chip
    return hot.sum() / max(1, denom if denom else solid.sum())


def _roof_chips(m, L, i):
    """Cores isentas na conta do emissivo do arquivo i da camada L: SO no teto (game_layer roofs) de um meta que
    declara family_chip (o paiol: o chip e tinta, sem emissao) e so o chip da familia da variante (+ a ponta,
    family_chip_tip). Variante sem chip no meta: os chips do meta. Qualquer outra camada: nenhuma."""
    fc = m.get("family_chip") or {}
    if L.get("game_layer") != "roofs" or not isinstance(fc, dict) or not fc:
        return ()
    tip = m.get("family_chip_tip") or {}
    vs = L.get("variants") or []
    fam = vs[i] if i < len(vs) else None
    cores = ([fc[fam]] + ([tip[fam]] if fam in tip else [])) if fam in fc else list(fc.values()) + list(tip.values())
    return tuple(tuple(c) for c in cores if isinstance(c, (list, tuple)) and len(c) >= 3)


def _emissive_limit(keys, name):
    """(limite, motivo) do emissivo da camada `name`: a tolerancia aprovada de LAYERED_EMISSIVE_ALLOW para a
    primeira pasta de `keys` que casar, senao (LAYERED_EMISSIVE_MAX, None)."""
    for k in keys:
        if (k, name) in LAYERED_EMISSIVE_ALLOW:
            return LAYERED_EMISSIVE_ALLOW[(k, name)]
    return LAYERED_EMISSIVE_MAX, None


def _paint_keyed(img):
    """Pixels (alfa > 0) na chave de pintura do jogo (verde acima do vermelho e do azul com |r - b| < 64)."""
    import numpy as np
    a = np.asarray(img.convert("RGBA"), dtype=np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    return int(((al > 0) & (g > np.maximum(r, b)) & (np.abs(r - b) < 64)).sum())


def check_layered_part(d, m, rep, tag="", keys=None):
    """Uma peca layered (meta normal ou parts.<sub> de uma pasta shared): arquivos, px = rect x 64 (+-1) ou o px
    da camada, rects dentro da peca, conjuntos completos, alfa (lights_add opaco; componente unico sem islands;
    pisos opacos), normais com o alfa do difuso, chave de pintura fora dos tetos, emissivo <= 2 % em TODO arquivo
    (niveis, quadros e variantes; pior caso por camada; tolerancia aprovada por pasta/camada em
    LAYERED_EMISSIVE_ALLOW, `keys` = nomes da pasta), tranco e flags."""
    import numpy as np
    W, H = m["size"]
    keys = tuple(keys or (os.path.basename(os.path.normpath(d)),))
    for f in m.get("files", []):
        if not os.path.exists(os.path.join(d, f)):
            rep.err(f"{tag}{f}: listado no meta e nao existe")
    if m.get("walls"):
        p = os.path.join(d, m["walls"])
        if os.path.exists(p) and Image.open(p).size != (W * PX, H * PX):
            rep.err(f"{tag}{m['walls']}: {Image.open(p).size}, esperado {(W * PX, H * PX)}")
    lay = m.get("layers") or {}
    if not lay:
        rep.err(f"{tag}meta layered sem camadas")
    for name, L in lay.items():
        gl = L.get("game_layer")
        if gl not in ("structure", "floors", "turrets", "doodads_low", "walls_stencil", "external_walls", "walls",
                      "doors", "weapons", "doodads_high", "lights_add", "fire", "roofs", "roof_doodads",
                      "roof_turrets", "roof_lights_fancy"):
            rep.err(f"{tag}{name}: camada do jogo desconhecida {gl}")
        _x, _y, w, h = L["rect"]
        want = tuple(L["px"]) if L.get("px") else (round(w * PX), round(h * PX))
        for r in L.get("rects") or [L["rect"]]:
            if r[0] < -1e-6 or r[1] < -1e-6 or r[0] + r[2] > W + 1e-6 or r[1] + r[3] > H + 1e-6:
                rep.err(f"{tag}{name}: rect {r} fora da peca {W}x{H}")
            if abs(r[2] - w) > 1e-6 or abs(r[3] - h) > 1e-6:
                rep.err(f"{tag}{name}: copia {r} com tamanho diferente do rect {L['rect']}")
        n_want = L.get("levels") or L.get("frames") or len(L.get("variants") or L.get("situations") or [None])
        if len(L["files"]) != int(n_want):
            rep.err(f"{tag}{name}: {len(L['files'])} arquivos, esperado {n_want} (conjunto incompleto)")
        if len(set(L["files"])) != len(L["files"]):
            rep.err(f"{tag}{name}: arquivos repetidos no conjunto")
        nrm = L.get("normals") or []
        if nrm and len(nrm) != len(L["files"]):
            rep.err(f"{tag}{name}: {len(nrm)} normais para {len(L['files'])} sprites")
        dirty_total = 0
        glow = []                          # [(emissivo estimado, arquivo)] de todos os arquivos medidos da camada
        for i, f in enumerate(L["files"]):
            p = os.path.join(d, f)
            if not os.path.exists(p):
                rep.err(f"{tag}{name}: {f} nao existe")
                continue
            im = Image.open(p).convert("RGBA")
            if abs(im.size[0] - want[0]) > 1 or abs(im.size[1] - want[1]) > 1:
                rep.err(f"{tag}{name}: {f} tem {im.size}, esperado {want} (rect x 64)")
            a = np.asarray(im)[..., 3]
            if gl == "lights_add" and L.get("blend", "add") == "add":
                if (a < 255).any():
                    rep.err(f"{tag}{name}: {f} (lights_add) nao e opaco sobre preto")
                continue
            if L.get("emission_only"):
                continue
            if not (a > 8).any():
                if L.get("islands") or L.get("levels") or L.get("frames"):
                    rep.note(f"{name}: {f} vazio (quadro/nivel vazio)")
                else:
                    rep.err(f"{tag}{name}: {f} vazio")
                continue
            if L.get("opaque"):
                if (a < 255).any():
                    rep.err(f"{tag}{name}: {f} deveria ser opaco (piso)")
            else:
                rgb = np.asarray(im)[..., :3]
                dirty_total += int(((a == 0) & (rgb.max(axis=2) > 0)).sum())
                if not L.get("islands"):
                    big = [c for c in _components(a > ALPHA_SOLID) if c >= 3]
                    if len(big) > 1:
                        rep.err(f"{tag}{name}: {f} com {len(big)} componentes de alfa {big[:5]} (islands = false)")
            if gl == "roof_doodads":
                nk = _paint_keyed(im)
                if nk:
                    rep.err(f"{tag}{name}: {f} com {nk} pixels na chave de pintura (verde com |r - b| < 64)")
            if gl != "lights_add":
                big_surface = gl in ("roofs", "floors")
                glow.append((_glow_frac(im, None if big_surface else W * H * PX * PX, _roof_chips(m, L, i)), f))
            nf = f[:-4] + "_normals.png"
            if nrm:
                if nf not in nrm:
                    rep.err(f"{tag}{name}: normais {nf} fora do meta")
                elif not os.path.exists(os.path.join(d, nf)):
                    rep.err(f"{tag}{name}: {nf} nao existe")
                else:
                    nm = np.asarray(Image.open(os.path.join(d, nf)).convert("RGBA"), dtype=np.int16)
                    if nm.shape[:2] != a.shape:
                        rep.err(f"{tag}{name}: {nf} com tamanho diferente do difuso")
                    elif (np.abs(nm[..., 3] - a.astype(np.int16)) > 8).mean() > 0.01:
                        rep.err(f"{tag}{name}: {nf} com alfa diferente do difuso")
        if dirty_total:
            rep.note(f"{name}: {dirty_total} px de alfa 0 com RGB != 0 (franja no bilinear)")
        if glow:
            gw, fw = max(glow)
            lim, why = _emissive_limit(keys, name)
            rep.note(f"{tag}{name}: emissivo estimado pior caso {gw:.2%} em {fw} ({len(glow)} arquivo(s)"
                     + ("" if gl in ("roofs", "floors") else ", fracao da peca") + ")")
            if why:
                rep.note(f"{tag}{name}: tolerancia APROVADA de emissivo {lim:.1%} (LAYERED_EMISSIVE_ALLOW, STYLE.md 12:"
                         f" {why})" + ("; sobrando: o pior caso ja cabe nos 2 %, tire a tolerancia"
                                       if gw <= LAYERED_EMISSIVE_MAX else ""))
            bad = sorted(((g, f) for g, f in glow if g > lim), reverse=True)
            if bad:
                rep.err(f"{tag}{name}: {len(bad)} de {len(glow)} arquivo(s) com emissivo estimado acima de {lim:.1%}"
                        f"{' (tolerancia aprovada)' if why else ''}: "
                        + ", ".join(f"{f} {g:.1%}" for g, f in bad[:5]) + (" ..." if len(bad) > 5 else ""))
    for k in ("icon", "blueprints"):
        v = m.get(k)
        for f in (v if isinstance(v, list) else [v] if v else []):
            if not os.path.exists(os.path.join(d, f)):
                rep.err(f"{tag}{k}: {f} nao existe")
    for name, tr in (m.get("tranco") or {}).items():
        L = lay.get(name)
        if L is None:
            rep.err(f"{tag}tranco.{name}: camada inexistente")
            continue
        order = tr.get("AnimationFiles_order") or []
        if sorted(order) != sorted(L["files"]):
            rep.err(f"{tag}tranco.{name}: AnimationFiles_order nao e uma permutacao dos quadros da camada")
        for k in ("offset_px_by_file", "offset_px_play_order"):
            if k in tr and len(tr[k]) != len(L["files"]):
                rep.err(f"{tag}tranco.{name}.{k}: {len(tr[k])} valores para {len(L['files'])} quadros")
        if order and order[-1] != L["files"][0]:
            rep.warn(f"{tag}tranco.{name}: o ultimo quadro da animacao ({order[-1]}) nao e o repouso "
                     f"({L['files'][0]})")
    for name, fl in (m.get("layer_flags") or {}).items():
        if name not in lay:
            rep.err(f"{tag}layer_flags.{name}: camada inexistente")
        for k in ("exclusive_with", "required_with"):
            if fl.get(k) and fl[k] not in lay:
                rep.err(f"{tag}layer_flags.{name}.{k}: camada {fl[k]} inexistente")


def _layered_spec_checks(short, meta, rep):
    """Nomes, tamanhos e ids do spec por pasta (Fita, FX, placas, paiol, Tupa)."""
    D = data()
    A2 = art2()["assets"]
    allf = set(meta.get("files", []))

    def expect(want, what):
        miss = sorted(set(want) - allf)
        if miss:
            rep.err(f"{what}: faltam {miss[:8]}{' ...' if len(miss) > 8 else ''}")
    if short == "bs_fita":
        expect(["floor.png", "roof.png", "roof_normals.png", "luz_grudada.png", "icon.png", "blueprints.png"],
               "spec fita")
        if "icon.png" in allf and _size(short, "icon.png") != (32, 32):
            rep.err(f"icon.png {_size(short, 'icon.png')}, spec: EditorIcon 32 px")
        if meta.get("id") != D.FITA_PART.get("id"):
            rep.err(f"id {meta.get('id')} difere da Fita {D.FITA_PART.get('id')}")
        if list(meta.get("size") or []) != list(D.FITA_PART.get("size") or [1, 1]):
            rep.err(f"tamanho {meta.get('size')} difere do spec {D.FITA_PART.get('size')}")
    elif short == "bs_fita_fx":
        want = [f"{a}_{b}{i}.png" for a in ("cartucho", "brilho") for b in ("sai", "entra") for i in range(1, 9)]
        expect(want, "spec fita_fx")
    elif short == "bs_placas":
        want = list((A2.get("plates") or {}).get("files") or [])
        expect(want, "spec placas")
        px = tuple((A2.get("plates") or {}).get("px") or (48, 48))
        for f in want:
            if f in allf and _size(short, f) != px:
                rep.err(f"{f}: {_size(short, f)} (spec {px})")
    elif short == (D.SPEC.get("paiol", {}).get("art3d_dir") or "bs_paiol"):
        pub = D.SPEC["paiol"].get("published_dir") or "bs_paiol_comum"
        if meta.get("id") != f"rafaeltessaro.{pub}":
            rep.err(f"id {meta.get('id')} (esperado rafaeltessaro.{pub})")
        if not meta.get("shared"):
            rep.err("pasta do paiol sem meta shared (parts.<1x1|2x2|3x3>)")
        ids = {p["id"]: p for p in D.SPEC["paiol"]["parts"]}
        for sub, m in A3.sub_metas(meta):
            for fam, pid in (m.get("ids") or {}).items():
                sp = ids.get(pid)
                if sp is None:
                    rep.err(f"[{sub}] ids.{fam} = {pid} nao e paiol do spec")
                elif list(sp["size"]) != list(m["size"]):
                    rep.err(f"[{sub}] {pid}: tamanho {m['size']} difere do spec {sp['size']}")
            gl = m.get("gauge_levels")
            g = (m.get("layers") or {}).get("gauge")
            if g and gl and int(g.get("levels", 0)) != int(gl):
                rep.err(f"[{sub}] gauge com {g.get('levels')} niveis, gauge_levels {gl}")
            pl = m.get("plate") or {}
            pm = A3.load_meta(pl.get("source") or "bs_placas") or {}
            for fam, fl in (pl.get("files") or {}).items():
                miss = [f for f in fl if f not in set(pm.get("files", []))]
                if miss:
                    rep.err(f"[{sub}] placa de {fam}: {miss} fora de art3d/{pl.get('source')}")
        want_ids = {p["id"] for p in D.SPEC["paiol"]["parts"]}
        have_ids = {pid for _s, m in A3.sub_metas(meta) for pid in (m.get("ids") or {}).values()}
        if want_ids - have_ids:
            rep.err(f"paiois do spec sem arte: {sorted(want_ids - have_ids)}")
    rail = {p["id"]: p for p in (D.SPEC.get("railgun", {}).get("parts") or {}).values() if isinstance(p, dict)}
    pid = meta.get("id")
    if pid in rail:
        if list(rail[pid]["size"]) != list(meta.get("size") or []):
            rep.err(f"tamanho {meta.get('size')} difere do spec {rail[pid]['size']} (SPEC.railgun.parts)")
        need = {"rafaeltessaro.bs_rail_loader": ["culatra_tranco"], "rafaeltessaro.bs_rail_barrel": ["tambores_tranco"],
                "rafaeltessaro.bs_rail_muzzle": ["weapon_tranco", "tambor_tranco"]}.get(pid, [])
        miss = [n for n in need if n not in (meta.get("layers") or {})]
        if miss:
            rep.err(f"camadas do tranco faltando: {miss} (base_required_outputs.content_checks_addendum)")
        if short != pid.split(".", 1)[1]:
            rep.err(f"pasta {short} difere do id {pid}")


def check_layered(d, meta, rep):
    """Pasta layered (normal ou shared): todas as pecas + o meta de topo."""
    if meta.get("kind") != "layered":
        rep.err(f"kind {meta.get('kind')} (esperado layered)")
        return
    for f in meta.get("files", []):
        if not os.path.exists(os.path.join(d, f)):
            rep.err(f"{f}: listado no meta e nao existe")
    # nomes da pasta para as tolerancias de emissivo: a pasta e o id do meta (rascunho fora de art3d/)
    keys = (os.path.basename(os.path.normpath(d)), str(meta.get("id") or "").split(".", 1)[-1])
    if meta.get("shared"):
        union = set()
        for sub, m in sorted((meta.get("parts") or {}).items()):
            check_layered_part(d, m, rep, tag=f"[{sub}] ", keys=keys)
            union |= set(m.get("files", []))
        if union - set(meta.get("files", [])):
            rep.err(f"meta shared: 'files' sem {sorted(union - set(meta.get('files', [])))[:5]}")
        print(f"layered shared: {len(meta.get('parts') or {})} pecas, {len(meta.get('files', []))} arquivos")
    else:
        check_layered_part(d, meta, rep, keys=keys)
        print(f"layered: {len(meta.get('layers') or {})} camadas, {len(meta.get('files', []))} arquivos")


def _layered(short, meta, rep, entry):
    check_layered(os.path.join(A3.ART3D, short), meta, rep)
    _layered_spec_checks(short, meta, rep)
    ok, why = integrated(entry)
    if not ok:
        rep.warn(f"modulo de dados nao integrado ({why}): so a arte")


# ============================================================================ icones de interface
def _ui_icons(short, meta, rep):
    """icons.json: arquivos existem, 96 x 96 RGBA com fundo transparente; os icones que o build usa (SPEC.toggles,
    slug, grupo, buff da Fita) e que faltam = AVISO (lacuna com dono; o placeholder do WP01 cobre)."""
    W, H = meta.get("size") or [96, 96]
    for rel, f in sorted(meta["publish"].items()):
        p = A3.path(short, f)
        if not os.path.exists(p):
            rep.err(f"{rel} -> {f} nao existe")
            continue
        im = Image.open(p)
        if im.size != (W, H):
            rep.err(f"{f}: {im.size}, esperado {(W, H)}")
        if im.mode != "RGBA":
            rep.err(f"{f}: modo {im.mode} (precisa de alfa)")
        elif im.getchannel("A").getextrema()[0] != 0:
            rep.err(f"{f}: sem fundo transparente")
        if not rel.startswith("gui/"):
            rep.err(f"{rel}: icone de interface publicado fora de gui/")
    for rel in meta.get("drop_1x") or []:
        if rel in meta["publish"]:
            rep.err(f"{rel} esta em drop_1x e ainda e publicado")
    try:
        import make_art
        want = make_art.wanted_icons(data())
    except Exception as e:  # noqa: BLE001
        rep.warn(f"lista de icones do build nao conferida ({type(e).__name__}: {e})")
        return
    miss = sorted(want - set(meta["publish"]))
    for rel in miss:
        rep.warn(f"LACUNA: {rel} nao esta em icons.json (placeholder do WP01 no build; buff_fita = WP11)")
    print(f"ui_icons: {len(meta['publish'])} icones {W}x{H}")


# ============================================================================ armas, defesas, PEM e lancadores
def _gun_art(short, meta, rep, size_spec=None):
    """So a arte de uma torre (kind gun): tamanho da torre, bordas do sprite, canos e PNGs."""
    if size_spec is not None and list(size_spec) != list(meta["size"]):
        rep.err(f"tamanho {meta['size']} difere do spec {list(size_spec)}")
    ts = meta["turret_size"]
    im = Image.open(A3.path(short, meta["turret"]["frames"][0]))
    if abs(im.width - round(ts * PX)) > 1:
        rep.err(f"turret.png tem {im.width}px, esperado {round(ts * PX)}")
    solid = lambda img: img.split()[-1].point(lambda v: 255 if v > 40 else 0)  # noqa: E731
    bb = solid(im).getbbox()
    if bb and (bb[0] <= 0 or bb[1] <= 0 or bb[2] >= im.width or bb[3] >= im.height):
        rep.err(f"a cabeca encosta na borda do sprite da torre (bbox {bb} em {im.size}): aumente turret_box")
    br = meta["barrel"]
    for f in set(br["frames"]):
        b = Image.open(A3.path(short, f))
        bbx = solid(b).getbbox()
        if bbx and (bbx[0] <= 0 or bbx[2] >= b.width):
            rep.err(f"{f}: o cano encosta nas laterais do sprite (bbox {bbx}, largura {b.width}): aumente width")
        if bbx and bbx[3] >= b.height:
            rep.err(f"{f}: o cano encosta embaixo do sprite no recuo (bbox {bbx}): aumente pad")
    ys = sorted(br["ys"])
    for a, b2 in zip(ys, ys[1:]):
        if b2 - a < br["sprite_w"] - 1e-6:
            rep.err(f"canos sobrepostos: ys {a} e {b2} estao a {b2 - a:.3f} e o sprite tem {br['sprite_w']} de largura")
    cg = meta["turret"].get("charge_glow")
    if cg:
        for f in cg.get("frames", []):
            if Image.open(A3.path(short, f)).size != im.size:
                rep.err(f"{f}: {Image.open(A3.path(short, f)).size} difere do quadro da torre {im.size}")
    for f in meta["files"]:
        if f.endswith(".png"):
            Image.open(A3.path(short, f)).verify()
    print(f"torre {ts} q, canos visiveis {len(br['ys'])}, quadros do cano {len(br['frames'])}"
          + (f", charge_glow {len(cg['frames'])}" if cg else ""))


def _gun(short, meta, rep, entry):
    D = data()
    part = next((p for p in D.GUNS + D.DEFENSES if (p.get("art3d_dir") or p["short"]) == short), None)
    pem = next((p for p in getattr(D, "PEM", []) if (p.get("art3d_dir") or p["short"]) == short), None)
    if part is None and pem is None:
        rep.err(f"{short} nao e arma/defesa/PEM do DATA (por art3d_dir)")
        _gun_art(short, meta, rep)
        return
    p = part or pem
    if meta.get("id") != p["id"]:
        rep.err(f"id do meta {meta.get('id')} difere da peca {p['id']}")
    _gun_art(short, meta, rep, p["size"])
    nb = (p.get("barrels") or {}).get("count") if isinstance(p.get("barrels"), dict) else p.get("barrels")
    if nb and len(meta["barrel"]["ys"]) != int(nb):
        rep.err(f"o render tem {len(meta['barrel']['ys'])} cano(s) visiveis; o DATA espera {nb}")
    crew = int(p.get("crew") or 0)
    if crew and len(meta.get("crew_pos") or []) < crew:
        rep.err(f"crew_pos com {len(meta.get('crew_pos') or [])} postos para {crew} tripulantes")
    if pem is not None:
        pg = [v for v in (art2()["assets"].get("pem_guns") or {}).values() if isinstance(v, dict)]
        sp = next((v for v in pg if v.get("id") == pem["id"]), {})
        if sp.get("charge_glow") and not meta["turret"].get("charge_glow"):
            rep.err(f"{pem['id']}: o spec pede charge_glow1..4 (render_kinds.gun.new_option) e o meta nao tem")
        elif sp.get("charge_glow") and len(meta["turret"]["charge_glow"].get("frames", [])) != 4:
            rep.err(f"{pem['id']}: charge_glow com {len(meta['turret']['charge_glow'].get('frames', []))} quadros "
                    f"(spec: 4)")
    ok, why = integrated(entry)
    if not ok:
        rep.warn(f"modulo de dados nao integrado ({why}): so a arte")
        return
    if part in D.GUNS:
        from bsgen import guns
        n, e = try_build(guns.build_gun, dict(part, art3d=meta), AnyPaths())
    elif part is not None:
        from bsgen import ciws
        n, e = try_build(ciws.build_ciws, dict(part, art3d=meta), "x.rules",
                         "y.rules" if part.get("beam_oc") else None)
    else:
        from bsgen import pem as PM
        fn = getattr(PM, "build_pem", None)
        if fn is None:
            from bsgen import guns
            fn = guns.build_gun
        n, e = try_build(fn, dict(pem, art3d=meta), AnyPaths())
    if e and e.startswith("assinatura"):
        rep.warn(f"regras nao conferidas aqui ({e}); ficam com o selfcheck do modulo")
    elif e:
        rep.err(f"o gerador das regras falhou com este meta: {e}")
    else:
        print(f"regras geradas: {n} linhas")


def _launcher(short, meta, rep, entry):
    D = data()
    lspec = next((l for l in D.MSPEC.get("launchers", []) if l["id"].split(".", 1)[1] == short), None)
    if lspec is None:
        rep.err(f"{short} nao e lancador do spec de misseis")
        return
    if list(lspec["size"]) != list(meta["size"]):
        rep.err(f"tamanho {meta['size']} difere do spec {lspec['size']}")
    if meta.get("id") != lspec["id"]:
        rep.err(f"id do meta {meta.get('id')} difere do lancador {lspec['id']}")
    ts = meta["turret_size"]
    im = Image.open(A3.path(short, meta["turret"]["frames"][0]))
    if abs(im.width - round(ts * PX)) > 1:
        rep.err(f"turret.png tem {im.width}px, esperado {round(ts * PX)}")
    for look, mm in meta["modes"].items():
        for ov in mm["overlays"]:
            rect = ov.get("rect")
            want = (rect[2] - rect[0], rect[3] - rect[1]) if rect else im.size
            for f in ov["files"]:
                o = Image.open(A3.path(short, f))
                if o.size != want:
                    rep.err(f"{f}: {o.size} difere do retangulo do casulo {want}")
        if mm.get("shutters"):
            o = Image.open(A3.path(short, mm["shutters"]["file"]))
            if o.size != im.size:
                rep.err(f"{mm['shutters']['file']}: {o.size} difere do quadro do casulo {im.size}")
    if meta["turret"].get("oc_glow"):
        o = Image.open(A3.path(short, meta["turret"]["oc_glow"]))
        if o.size != im.size:
            rep.err(f"{meta['turret']['oc_glow']}: {o.size} difere do quadro do casulo {im.size}")
        elif not o.split()[-1].getbbox():
            rep.err(f"{meta['turret']['oc_glow']}: imagem vazia (oc_glow sem objetos emissivos)")
    want_looks = [m["missile_type"] for m in lspec["modes"]]
    for m in lspec["modes"]:
        mm = meta["modes"].get(m["missile_type"])
        if mm is None:
            rep.warn(f"LACUNA WP13: modo {m['missile_type']} ({m['layout']}) sem celulas renderizadas")
            continue
        nu = int(m.get("rack_units") or 0)
        if nu and len(mm["units"]) != nu:
            rep.warn(f"LACUNA WP13: modo {m['missile_type']} com {len(mm['units'])} unidades no meta; o layout "
                     f"{m['layout']} pede {nu} (re-render --only cells)")
    extra = sorted(set(meta["modes"]) - set(want_looks))
    if extra:
        rep.warn(f"LACUNA WP13: celulas 1.x ainda na pasta: {extra} (apagar)")
    for f in meta["files"]:
        if f.endswith(".png"):
            Image.open(A3.path(short, f)).verify()
    ok, why = integrated(entry)
    if not ok:
        rep.warn(f"modulo de dados nao integrado ({why}): so a arte")
        return
    lch = next((x for x in D.LAUNCHERS if x["short"] == short), None)
    if lch is None:
        rep.err(f"{short} nao esta em D.LAUNCHERS")
        return
    from bsgen import launchers
    n, e = try_build(launchers.build_launcher, dict(lch, art3d=meta), AnyPaths())
    if e and e.startswith("assinatura"):
        rep.warn(f"regras do lancador nao conferidas aqui ({e}); ficam com o selfcheck do bsgen.launchers")
    elif e:
        rep.err(f"bsgen.launchers.build_launcher falhou com este meta: {e}")
    else:
        print(f"regras geradas: {n} linhas")


def _legacy(short, meta, rep, entry):
    """Pasta 1.x que sai (legado): so a arte (arquivos do meta e PNGs validos) e um AVISO."""
    for f in meta.get("files", []):
        p = A3.path(short, f)
        if not os.path.exists(p):
            rep.warn(f"legado: {f} listado e nao existe")
        elif f.endswith(".png"):
            Image.open(p).verify()
    rep.warn(f"pasta legado 1.x (dono {entry.get('dono')}; sai em {entry.get('sai_em')})")


# ============================================================================ laco
def check_folder(short):
    """Confere uma pasta de art3d/; devolve o Report (nunca sai do processo)."""
    rep = Report(short)
    entry = owner_map().get(short)
    try:
        meta = A3.load_meta(short)
    except Exception as e:  # noqa: BLE001
        rep.err(f"meta invalido: {e}")
        return rep
    if meta is None:
        rep.err(f"art3d/{short} sem meta.json (nem icons.json)")
        return rep
    if entry is None:
        rep.err("pasta sem entrada em SPEC.art_assets.art3d_owner_map (de um dono a ela)")
    try:
        if entry and entry.get("legado"):
            _legacy(short, meta, rep, entry)
            return rep
        kind = meta.get("kind")
        tipo = (entry or {}).get("tipo")
        if tipo and kind != tipo and not (tipo == "ui_icons" and kind == "ui_icons"):
            rep.err(f"kind {kind} difere do tipo {tipo} do art3d_owner_map")
        if kind in PROJ_KINDS:
            check_projectiles(os.path.join(A3.ART3D, short), meta, rep.errs, rep.warns)
        elif kind == "layered":
            _layered(short, meta, rep, entry)
        elif kind == "ui_icons":
            _ui_icons(short, meta, rep)
        elif kind == "gun":
            _gun(short, meta, rep, entry)
        elif kind == "launcher":
            _launcher(short, meta, rep, entry)
        elif kind == "factory":
            _factory(short, meta, rep, entry)
        elif kind == "resource":
            _resource(short, meta, rep)
        else:
            rep.err(f"tipo desconhecido no meta: {kind}")
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc().strip().splitlines()
        rep.err(f"excecao na conferencia: {type(e).__name__}: {e} ({tb[-3].strip() if len(tb) > 2 else ''})")
    return rep


def folders():
    return sorted(s for s in os.listdir(A3.ART3D) if os.path.isdir(os.path.join(A3.ART3D, s)) and
                  A3.meta_path(s) is not None)


def _print(rep, strict):
    entry = owner_map().get(rep.name)
    if entry is not None:
        print(f"   dono {entry.get('dono', '?')}; tipo {entry.get('tipo', 'legado' if entry.get('legado') else '?')}")
    for n in rep.notes:
        print(f"   nota: {n}")
    for w in rep.warns:
        print(f"   {'ERRO (estrito)' if strict else 'AVISO'}: {w}")
    for e in rep.errs:
        print(f"   ERRO: {e}")
    bad = rep.errs or (strict and rep.warns)
    print(f"   {'PROBLEMAS' if bad else 'OK'} {rep.name}")
    return bool(bad)


def palette_guard():
    """Paleta 2.0 do spec (art_assets.palette): o Tupa e o chip dos paiois de projeteis sao AZUL eletrico (USER_NOTES:
    referencia do usuario; violeta/ouro removidos). Devolve um Report (ERRO se alguma dessas cores cair no violeta,
    matiz 245-320 graus)."""
    import colorsys
    rep = Report("paleta 2.0 (art_assets.palette)")
    pal = art2().get("palette") or {}
    cores = {f"rail.{k}": v for k, v in (pal.get("rail") or {}).items()
             if k in ("blue", "glow", "core", "hull", "chip") and isinstance(v, list)}
    fc = pal.get("family_chip") or {}
    if isinstance(fc.get("projeteis"), list):
        cores["family_chip.projeteis"] = fc["projeteis"]
    for k, c in sorted(cores.items()):
        h, _l, sat = colorsys.rgb_to_hls(*(v / 255.0 for v in c[:3]))
        if sat > 0.2 and 245 <= h * 360 <= 320:
            rep.err(f"palette.{k} = {c} e violeta (matiz {h * 360:.0f} graus); a 2.0 usa o AZUL eletrico do Tupa")
    if not cores:
        rep.warn("palette.rail / family_chip.projeteis ausentes no spec de arte")
    print(f"paleta: {len(cores)} cores do Tupa/projeteis conferidas")
    return rep


def run(names, strict=False, title="todos"):
    bad, n_err, n_warn = [], 0, 0
    if title == "todos":
        print("== paleta")
        prep = palette_guard()
        if _print(prep, strict):
            bad.append("paleta")
        n_err += len(prep.errs)
        n_warn += len(prep.warns)
    for short in names:
        print(f"== {short}")
        rep = check_folder(short)
        if _print(rep, strict):
            bad.append(short)
        n_err += len(rep.errs)
        n_warn += len(rep.warns)
    print(f"{title}: {len(names)} pastas, {n_err} erro(s), {n_warn} aviso(s){' (estrito)' if strict else ''}")
    if bad:
        print(f"PROBLEMAS em: {', '.join(bad)}")
        return 1
    print(f"OK {title}")
    return 0


def check_dir(d):
    """Confere uma pasta qualquer (rascunho: projeteis ou layered); devolve True quando ha problemas."""
    p = os.path.join(d, "meta.json")
    if not os.path.exists(p):
        print(f"ERRO: {p} nao existe")
        return True
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    rep = Report(d)
    if meta.get("kind") in PROJ_KINDS:
        check_projectiles(d, meta, rep.errs, rep.warns)
    elif meta.get("kind") == "layered":
        check_layered(d, meta, rep)
    else:
        print(f"ERRO: por caminho so se conferem projeteis e layered (kind {meta.get('kind')}); use o nome da pasta")
        return True
    for n in rep.notes:
        print(f"   nota: {n}")
    for w in rep.warns:
        print(f"   AVISO: {w}")
    if rep.errs:
        print("PROBLEMAS:")
        for e in rep.errs:
            print(" -", e)
        return True
    print("OK", d)
    return False


def check_one(short):
    """Compatibilidade (scripts dos jobs de arte): confere uma pasta; True quando ha ERRO."""
    rep = check_folder(short)
    return _print(rep, False)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    strict = "--estrito" in args
    args = [a for a in args if a != "--estrito"]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--pacote":
        wp = args[1].upper() if len(args) > 1 else ""
        names = [s for s in folders() if (owner_map().get(s) or {}).get("dono", "").upper().startswith(wp)]
        if not names:
            print(f"ERRO: nenhuma pasta com dono {wp} no art3d_owner_map")
            return 1
        return run(names, strict, f"pacote {wp}")
    if args[0] in ("todos", "--all"):
        return run(folders(), strict, "todos")
    names, rc = [], 0
    for a in args:
        ab = os.path.abspath(a)
        if os.path.isdir(ab) and os.path.dirname(ab) != A3.ART3D and os.path.exists(os.path.join(ab, "meta.json")):
            rc |= 1 if check_dir(ab) else 0
            continue
        short = os.path.basename(ab) if os.path.dirname(ab) == A3.ART3D else a
        names.append(short)
    if names:
        rc |= run(names, strict, " ".join(names) if len(names) < 4 else f"{len(names)} pastas")
    return rc


if __name__ == "__main__":
    sys.exit(main())
