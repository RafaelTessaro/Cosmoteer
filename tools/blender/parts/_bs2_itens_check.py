"""Confere os 12 recursos 2.0 do grupo "itens" com as MESMAS regras do tools/check_art3d.check_resource, mas com as
pilhas do SPEC 2.0 (o bs_data 1.x ainda nao lista os recursos novos: a ligacao vem depois) e os arquivos pedidos em
art_assets.assets.resources. Sem bpy.

    python3 tools/blender/parts/_bs2_itens_check.py --spec <SPEC_2.0.json> [id_curto ...]

Sem ids: confere os 12 (ITENS). O caminho do spec tambem pode vir de BS_SPEC2; o padrao e
tools/spec/bullet_strike_spec_2_0.json (onde a ligacao deve guardar o spec 2.0). Sai com 1 se algum falhar.
"""
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))                 # tools/blender/parts
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))    # raiz do repo
sys.path.insert(0, os.path.join(ROOT, "tools"))
import art3d as A3  # noqa: E402
import check_art3d as C  # noqa: E402

ITENS = ["bs_mag_std", "bs_mag_ap", "bs_mag_sap", "bs_mag_ac", "bs_mag_frag", "bs_plasma_cell", "bs_cell_emp",
         "bs_msl_he", "bs_msl_cluster", "bs_msl_emp", "bs_msl_nuke", "bs_slug_rail"]


def main(argv):
    spec_path = os.environ.get("BS_SPEC2") or os.path.join(ROOT, "tools", "spec", "bullet_strike_spec_2_0.json")
    if "--spec" in argv:
        i = argv.index("--spec")
        spec_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if not os.path.exists(spec_path):
        sys.exit(f"spec 2.0 nao encontrado: {spec_path} (use --spec ou BS_SPEC2)")
    spec = json.load(open(spec_path, encoding="utf-8"))
    D = types.SimpleNamespace(RESOURCES=[{"id": r["id"], "dir": r["id"].split(".")[1], "max_stack": r["max_stack_size"]}
                                         for r in spec["resources"]])
    assets = {r["id"]: r for r in spec["art_assets"]["assets"]["resources"]}
    bad = []
    for short in argv or ITENS:
        meta = A3.load_meta(short)
        errs = []
        if meta.get("id") != f"rafaeltessaro.{short}":
            errs.append(f"id do meta {meta.get('id')} difere da peca")
        want = assets.get(meta.get("id"), {}).get("files")
        if want is None:
            errs.append("recurso fora de art_assets.assets.resources do spec")
        elif sorted(want) != sorted(meta["files"]):
            errs.append(f"arquivos {sorted(meta['files'])} diferem do spec {sorted(want)}")
        C.check_resource(short, meta, D, errs)
        print(("PROBLEMAS " + short + ": " + "; ".join(errs)) if errs else f"OK {short} (spec 2.0)")
        if errs:
            bad.append(short)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
