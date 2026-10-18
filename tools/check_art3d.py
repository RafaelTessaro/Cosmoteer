"""Confere a arte 3D de uma peca sem gravar o mod: meta.json, arquivos e geracao das regras.

    python3 tools/check_art3d.py <id_curto>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import art3d as A3  # noqa: E402


def main():
    short = sys.argv[1]
    meta = A3.load_meta(short)
    if not meta:
        sys.exit(f"ERRO: art3d/{short}/meta.json nao existe")
    import bs_data as D  # carrega o meta e confere o numero de canos
    from bsgen import guns, ciws, factory
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
            top, info = ciws.build_ciws(part, "x.rules", "y.rules" if part.get("oc") else None)
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
            for ov in mm["overlays"]:
                for f in ov["files"]:
                    o = Image.open(A3.path(short, f))
                    if o.size != im.size:
                        errs.append(f"{f}: {o.size} difere do quadro do casulo {im.size}")
        for f in meta["files"]:
            if f.endswith(".png"):
                Image.open(A3.path(short, f)).verify()
        print(f"regras geradas: {len(text.splitlines())} linhas; modos {[m['type'] for m in lch['modes']]}")
    elif meta["kind"] == "factory":
        f = next((x for x in D.FACTORIES if x["short"] == short), None)
        top, info = factory.build_factory(f, {r["id"]: r["max_stack"] for r in D.RESOURCES})
        render(top, "teste")
    if errs:
        print("PROBLEMAS:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("OK", short)


if __name__ == "__main__":
    main()
