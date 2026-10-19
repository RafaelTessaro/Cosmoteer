"""Confere a arte 3D de uma peca sem gravar o mod: meta.json, arquivos e geracao das regras.

    python3 tools/check_art3d.py <id_curto>
    python3 tools/check_art3d.py todos        # todas as pastas de art3d/
    python3 tools/check_art3d.py <pasta>      # folha de projeteis fora de art3d/ (rascunhos, testes do kit)

Projeteis (meta kind "missiles" / "shells", esquema de CONTRATOS secao 3 / STYLE.md 8.4, 10 e 11): arquivos,
tamanhos (px = size x px_per_tile, atlas = n x w), um so componente de alfa por sprite, orcamento de emissivo do
quadro 0 e mascaras brancas sobre transparente.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import art3d as A3  # noqa: E402


def _size(short, name):
    return Image.open(A3.path(short, name)).size


def _solid_bbox(img):
    return img.convert("RGBA").getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()


def check_resource(short, meta, D, errs):
    """Recurso: icone/nugget 64 x 64, overlay 128 x 128, stack_1..MaxStackSize, nugget do tamanho de uma unidade
    da pilha (o tripulante carrega uma unidade; o nugget nao pode ser maior que a unidade empilhada)."""
    r = next((x for x in D.RESOURCES if x["dir"] == short), None)
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
            print(f"aviso: nugget renderizado com icon_scale; o build reduz a {f:.2f} (re-renderize o recurso)")
            nug = A3.scaled_center(nug, f)
        nb, sb = _solid_bbox(nug), _solid_bbox(Image.open(A3.path(short, "stack_1.png")))
        if nb and sb:
            nw, nh = nb[2] - nb[0], nb[3] - nb[1]
            sw, sh = sb[2] - sb[0], sb[3] - sb[1]
            if max(nw, nh) > 1.15 * max(sw, sh) + 2:
                errs.append(f"nugget {nw}x{nh} px maior que a unidade da pilha {sw}x{sh} px")
    print(f"recurso: pilha {r['max_stack']}, arquivos {len(meta['files'])}")


def check_factory(short, meta, D, errs):
    """Fabrica: casco (piso, paredes, teto, normais, luzes) do tamanho da peca e quadros da maquina iguais."""
    from bsgen import factory
    from rules_dsl import render
    f = next((x for x in D.FACTORIES if x["short"] == short), None)
    if f is None:
        errs.append(f"{short} nao e fabrica do spec")
        return
    top, info = factory.build_factory(f, {r["id"]: r["max_stack"] for r in D.RESOURCES})
    render(top, "teste")
    W, H = f["size"]
    if list(meta.get("size", [])) != [W, H]:
        errs.append(f"tamanho {meta.get('size')} difere do spec {f['size']}")
    for key, n in meta.get("hull", {}).items():
        if _size(short, n) != (W * 64, H * 64):
            errs.append(f"{n} ({key}): {_size(short, n)}, esperado {(W * 64, H * 64)}")
    mc = meta["machine"]
    mw, mh = mc.get("size", [W, H])
    frames = list(mc["frames"]) + [mc["off"]]
    sizes = {n: _size(short, n) for n in frames}
    if len(set(sizes.values())) != 1:
        errs.append(f"quadros da maquina com tamanhos diferentes: {sorted(set(sizes.values()))}")
    if (mw * 64, mh * 64) not in sizes.values():
        errs.append(f"quadros da maquina {sorted(set(sizes.values()))}, esperado {(mw * 64, mh * 64)}")
    print(f"fabrica: {len(mc['frames'])} quadros de maquina, casco {W}x{H}")


# ============================================================================ projeteis
PROJ_KINDS = ("missiles", "shells")
PROJ_PPT = {"missiles": 64, "shells": 128}
PROJ_NAMES = {"missiles": ("msl_{k}.png", "msl_{k}_normals.png", "msl_{k}_lights.png", None),
              "shells": ("bs_shell_{k}.png", "bs_shell_{k}_normals.png", "bs_shell_{k}_lights.png",
                         "bs_shell_band_{k}.png")}
PROJ_IDS = {"missiles": "rafaeltessaro.bs_missiles", "shells": "rafaeltessaro.bs_shells"}
SHELL_KEYS = ("he", "ap", "nuke")
ALPHA_SOLID = 100           # alfa que conta como "corpo" (STYLE.md 9, ilhas flutuantes)
EMISSIVE_MAX = 0.03         # area acesa do quadro 0 / area do corpo
EMISSIVE_MAX_NUCLEAR = 0.04  # Iara / granada nuclear: faixas largas que respiram
ANCHORS = ("seeker", "warhead", "radiation")


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


def _proj_table(kind):
    """Tabela de arte dos misseis copiada para o spec (tools/spec/bullet_strike_missile_fx.json), se existir."""
    if kind != "missiles":
        return None
    p = os.path.join(A3.ROOT, "tools", "spec", "bullet_strike_missile_fx.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        t = json.load(fh)
    return t.get("items") or t.get("art", {}).get("items")


def check_projectiles(d, meta, errs):
    """Folha de projeteis (misseis 64 px/tile, granadas 128 px/tile) na pasta d."""
    import numpy as np
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
    canon = meta.get("id") == PROJ_IDS[kind]
    table = _proj_table(kind) if canon else None
    if canon and kind == "shells":
        miss = [k for k in SHELL_KEYS if k not in items]
        if miss:
            errs.append(f"faltam as granadas {miss} (contrato: he, ap, nuke)")
    if canon and kind == "missiles":
        if table is None:
            print("aviso: sem tools/spec/bullet_strike_missile_fx.json; chaves/quadros dos misseis nao conferidos")
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
            print(f"aviso: {tag}: {len(comps) - 1} pixel(s) solto(s) de alfa > {ALPHA_SOLID} (antisserrilhado)")
        ys, xs = np.where(a > 40)
        if xs.min() == 0 or xs.max() == pw - 1:
            print(f"aviso: {tag}: o sprite encosta na lateral da tela (bbox x {xs.min()}..{xs.max()} de {pw}); "
                  f"nariz/bocal cortado?")
        if ys.min() == 0 or ys.max() == ph - 1:
            print(f"aviso: {tag}: o sprite encosta em cima/embaixo da tela (bbox y {ys.min()}..{ys.max()} de {ph})")
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
            if n < 2:
                errs.append(f"{tag}: lights com {n} quadro(s); com 1 quadro o atlas e omitido (lights = null)")
            if [fw, fh] != [pw, ph]:
                errs.append(f"{tag}: lights.frame_px {lt.get('frame_px')} difere de px {it['px']}")
            if per != n:
                errs.append(f"{tag}: lights.per_row {per} (o atlas e UMA fileira: per_row = frames = {n})")
            if not lt.get("fps") or lt["fps"] <= 0:
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
                            print(f"aviso: {tag}: quadro {k + 1} do atlas de luzes esta vazio (tudo apagado)")
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
            print(f"aviso: {tag}: nozzle x {noz[0]} fora da tela (meio comprimento {L / 2})")
        for an, v in (it.get("anchors") or {}).items():
            if an not in ANCHORS:
                print(f"aviso: {tag}: ancora '{an}' fora do contrato ({', '.join(ANCHORS)})")
            if abs(v[0]) > L / 2 + 0.05 or abs(v[1]) > W / 2 + 0.05:
                print(f"aviso: {tag}: ancora '{an}' {v} fora da tela")
        if table and key in table:
            tr = table[key]
            if list(tr.get("canvas_px", it["px"])) != list(it["px"]):
                errs.append(f"{tag}: px {it['px']} difere da tabela {tr.get('canvas_px')}")
            tl = tr.get("lights")
            if bool(tl) != bool(lt):
                errs.append(f"{tag}: atlas de luzes {'ausente' if tl else 'sobrando'} (tabela: {tl and tl.get('frames')})")
            elif tl and (tl.get("frames") != lt.get("frames") or tl.get("fps") != lt.get("fps") or
                         (tl.get("WrapMode") or tl.get("wrap")) != lt.get("wrap")):
                errs.append(f"{tag}: luzes {lt.get('frames')} quadros / {lt.get('fps')} fps / {lt.get('wrap')} diferem "
                            f"da tabela {tl.get('frames')} / {tl.get('fps')} / {tl.get('WrapMode') or tl.get('wrap')}")
        if canon and kind == "shells" and key == "nuke" and lt and (lt.get("frames") != 4 or lt.get("fps") != 6):
            errs.append(f"{tag}: o contrato pede 4 quadros a 6 fps no atlas da granada nuclear")
        if canon and kind == "shells" and key in ("he", "ap") and not it.get("mask"):
            errs.append(f"{tag}: falta a mascara da faixa ({nm.format(k=key)})")
        report.append(f"{key} {pw}x{ph}" + (f" luzes {lt['frames']}q {frac:.1%}" if lt else "") +
                      (" mascara" if it.get("mask") else ""))
    extra = sorted(files - used)
    if extra:
        print(f"aviso: arquivos em meta.files que nenhum item usa: {extra[:6]}")
    print(f"{kind}: {len(items)} itens ({'; '.join(report)})")


def check_dir(d):
    """Confere uma folha de projeteis numa pasta qualquer (rascunho); devolve True quando ha problemas."""
    p = os.path.join(d, "meta.json")
    if not os.path.exists(p):
        sys.exit(f"ERRO: {p} nao existe")
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    if meta.get("kind") not in PROJ_KINDS:
        sys.exit(f"ERRO: por caminho so se conferem projeteis (kind {meta.get('kind')}); use o id curto")
    errs = []
    check_projectiles(d, meta, errs)
    return _report(errs, d)


def _report(errs, name):
    if errs:
        print("PROBLEMAS:")
        for e in errs:
            print(" -", e)
        return True
    print("OK", name)
    return False


def main():
    arg = sys.argv[1]
    if arg not in ("todos", "--all") and os.path.isdir(arg) and os.path.exists(os.path.join(arg, "meta.json")):
        ab = os.path.abspath(arg)
        if os.path.dirname(ab) == A3.ART3D:
            arg = os.path.basename(ab)          # art3d/<id_curto> passado como caminho
        else:
            if check_dir(arg):
                sys.exit(1)
            return
        sys.argv[1] = arg
    if sys.argv[1] in ("todos", "--all"):
        bad = []
        for short in sorted(os.listdir(A3.ART3D)):
            if not os.path.exists(os.path.join(A3.ART3D, short, "meta.json")):
                continue
            print(f"== {short}")
            if check_one(short):
                bad.append(short)
        if bad:
            sys.exit(f"PROBLEMAS em: {', '.join(bad)}")
        print("OK todos")
        return
    if check_one(sys.argv[1]):
        sys.exit(1)


def check_one(short):
    """Confere uma peca; devolve True quando ha problemas."""
    meta = A3.load_meta(short)
    if not meta:
        sys.exit(f"ERRO: art3d/{short}/meta.json nao existe")
    if meta.get("kind") in PROJ_KINDS:
        # projeteis: so arte (as regras usam o meta pelos modulos opcionais, CONTRATOS secao 2)
        errs = []
        check_projectiles(os.path.join(A3.ART3D, short), meta, errs)
        return _report(errs, short)
    import bs_data as D  # carrega o meta e confere o numero de canos
    from bsgen import guns, ciws
    from rules_dsl import render
    errs = []
    part = next((p for p in D.GUNS + D.DEFENSES if p["short"] == short), None)
    if meta["kind"] == "gun":
        if part is None:
            sys.exit(f"ERRO: {short} nao e arma/defesa do spec")
        if part in D.GUNS:
            sp = {}
            for m in part["modes"]:
                sp[(m["mode"], False)] = "x.rules"
                sp[(m["mode"], True)] = "x.rules"
            top, info = guns.build_gun(part, sp)
        else:
            top, info = ciws.build_ciws(part, "x.rules", "y.rules" if part.get("beam_oc") else None)
        text = render(top, "teste")
        W, H = meta["size"]
        if list(part["size"]) != list(meta["size"]):
            errs.append(f"tamanho {meta['size']} difere do spec {part['size']}")
        ts = meta["turret_size"]
        im = Image.open(A3.path(short, meta["turret"]["frames"][0]))
        if abs(im.width - round(ts * 64)) > 1:
            errs.append(f"turret.png tem {im.width}px, esperado {round(ts * 64)}")
        solid = lambda img: img.split()[-1].point(lambda v: 255 if v > 40 else 0)  # noqa: E731
        bb = solid(im).getbbox()
        if bb and (bb[0] <= 0 or bb[1] <= 0 or bb[2] >= im.width or bb[3] >= im.height):
            errs.append(f"a cabeca encosta na borda do sprite da torre (bbox {bb} em {im.size}): aumente turret_box")
        br = meta["barrel"]
        for f in set(br["frames"]):
            b = Image.open(A3.path(short, f))
            bbx = solid(b).getbbox()
            if bbx and (bbx[0] <= 0 or bbx[2] >= b.width):
                errs.append(f"{f}: o cano encosta nas laterais do sprite (bbox {bbx}, largura {b.width}): aumente width")
            if bbx and bbx[3] >= b.height:
                errs.append(f"{f}: o cano encosta embaixo do sprite no recuo (bbox {bbx}): aumente pad")
        ys = sorted(br["ys"])
        for a, b2 in zip(ys, ys[1:]):
            if b2 - a < br["sprite_w"] - 1e-6:
                errs.append(f"canos sobrepostos: ys {a} e {b2} estao a {b2 - a:.3f} e o sprite tem {br['sprite_w']} de largura")
        for f in meta["files"]:
            if f.endswith(".png"):
                Image.open(A3.path(short, f)).verify()
        print(f"regras geradas: {len(text.splitlines())} linhas; canos visiveis {len(br['ys'])}; quadros {len(br['frames'])}")
    elif meta["kind"] == "launcher":
        from bsgen import launchers
        lch = next((x for x in D.LAUNCHERS if x["short"] == short), None)
        if lch is None:
            sys.exit(f"ERRO: {short} nao e lancador gerado (bs_data.BUILD_LAUNCHERS)")
        top, info = launchers.build_launcher(lch, {m["type"]: "x.rules" for m in lch["modes"]})
        text = render(top, "teste")
        if list(lch["size"]) != list(meta["size"]):
            errs.append(f"tamanho {meta['size']} difere do spec {lch['size']}")
        ts = meta["turret_size"]
        im = Image.open(A3.path(short, meta["turret"]["frames"][0]))
        if abs(im.width - round(ts * 64)) > 1:
            errs.append(f"turret.png tem {im.width}px, esperado {round(ts * 64)}")
        solid = lambda img: img.split()[-1].point(lambda v: 255 if v > 40 else 0)  # noqa: E731
        bb = solid(im).getbbox()
        if bb and (bb[0] <= 0 or bb[1] <= 0 or bb[2] >= im.width or bb[3] >= im.height):
            errs.append(f"o casulo encosta na borda do sprite (bbox {bb} em {im.size}): aumente turret_box")
        for m in lch["modes"]:
            mm = meta["modes"][m["type"]]
            extra = [mm["shutters"]["file"]] if mm.get("shutters") else []
            if m["geo"].get("shutters") and not extra:
                errs.append(f"modo {m['type']}: o layout {m['layout']} pede shutters_{m['type']}.png (shutter())")
            # niveis do rack: quadro = retangulo do casulo ("rect" no meta, STYLE.md 8.1); persianas: quadro da torre
            for ov in mm["overlays"]:
                rect = ov.get("rect")
                want = (rect[2] - rect[0], rect[3] - rect[1]) if rect else im.size
                if not rect:
                    print(f"aviso: modo {m['type']}: overlay sem 'rect' (quadro inteiro da torre; re-renderize)")
                for f in ov["files"]:
                    o = Image.open(A3.path(short, f))
                    if o.size != want:
                        errs.append(f"{f}: {o.size} difere do retangulo do casulo {want}")
            for f in extra:
                o = Image.open(A3.path(short, f))
                if o.size != im.size:
                    errs.append(f"{f}: {o.size} difere do quadro do casulo {im.size}")
        if lch.get("oc_glow") and not meta["turret"].get("oc_glow"):
            print("aviso: sem turret_oc.png (oc_glow); as regras ficam sem o brilho de overclock")
        if meta["turret"].get("oc_glow"):
            # OverclockGlowGraphics desenha a imagem com Size = [turret_size, turret_size]: mesmo quadro da torre
            o = Image.open(A3.path(short, meta["turret"]["oc_glow"]))
            if o.size != im.size:
                errs.append(f"{meta['turret']['oc_glow']}: {o.size} difere do quadro do casulo {im.size}")
            elif not o.split()[-1].getbbox():
                errs.append(f"{meta['turret']['oc_glow']}: imagem vazia (oc_glow sem objetos emissivos)")
        for f in meta["files"]:
            if f.endswith(".png"):
                Image.open(A3.path(short, f)).verify()
        print(f"regras geradas: {len(text.splitlines())} linhas; modos {[m['type'] for m in lch['modes']]}")
    elif meta["kind"] == "factory":
        check_factory(short, meta, D, errs)
    elif meta["kind"] == "resource":
        check_resource(short, meta, D, errs)
    else:
        errs.append(f"tipo desconhecido no meta.json: {meta['kind']}")
    if errs:
        print("PROBLEMAS:")
        for e in errs:
            print(" -", e)
        return True
    print("OK", short)
    return False


if __name__ == "__main__":
    main()
