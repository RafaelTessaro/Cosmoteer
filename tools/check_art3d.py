"""Confere a arte 3D de uma peca sem gravar o mod: meta.json, arquivos e geracao das regras.

    python3 tools/check_art3d.py <id_curto>
    python3 tools/check_art3d.py todos        # todas as pastas de art3d/
"""
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


def main():
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
