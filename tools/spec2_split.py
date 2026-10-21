#!/usr/bin/env python3
"""Divide o SPEC_2.0.json nos arquivos que o gerador le (tools/spec/), seguindo SPEC['generator_mapping'].

Funciona em dois lugares (o WP01 copia este arquivo para tools/spec2_split.py):
  - no repositorio:  tools/spec2_split.py le tools/spec/SPEC_2.0.json e escreve em tools/spec/
  - no design:       design/final/scripts/split_spec.py le ../SPEC_2.0.json e escreve em ../spec_split/

Uso:
    python3 tools/spec2_split.py                     # escreve os 3 JSON do gerador
    python3 tools/spec2_split.py --out <dir>         # escreve em outra pasta
    python3 tools/spec2_split.py --check <dir>       # confere se os arquivos de <dir> batem com o SPEC_2.0 (sai 1 se divergir)
    python3 tools/spec2_split.py --spec <arquivo>    # outro SPEC_2.0.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_SPEC = os.path.join(HERE, "spec", "SPEC_2.0.json")          # layout do repositorio (tools/)
DESIGN_SPEC = os.path.join(os.path.dirname(HERE), "SPEC_2.0.json")  # layout do design (scripts/..)


def defaults():
    if os.path.isfile(REPO_SPEC):
        return REPO_SPEC, os.path.join(HERE, "spec")
    return DESIGN_SPEC, os.path.join(os.path.dirname(HERE), "spec_split")


def parts(spec):
    out = {}
    for target, keys in spec["generator_mapping"]["split_files"].items():
        if not target.startswith("tools/spec/"):
            continue
        name = os.path.basename(target)
        out[name] = {"_generated_from": "tools/spec/SPEC_2.0.json (tools/spec2_split.py)", "version": spec["version"]}
        for k in keys:
            out[name][k] = spec[k]
    return out


def main():
    spec_default, out_default = defaults()
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=spec_default)
    ap.add_argument("--out", default=out_default)
    ap.add_argument("--check", default=None)
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    files = parts(spec)
    if a.check:
        bad = 0
        for name, data in files.items():
            p = os.path.join(a.check, name)
            if not os.path.isfile(p):
                print(f"FALTA {p}")
                bad += 1
                continue
            with open(p, encoding="utf-8") as fh:
                have = json.load(fh)
            for k, v in data.items():
                if k.startswith("_"):
                    continue
                if have.get(k) != v:
                    print(f"DIVERGE {name}:{k}")
                    bad += 1
        print("spec2_split --check:", "OK" if not bad else f"{bad} divergencia(s)")
        sys.exit(1 if bad else 0)
    os.makedirs(a.out, exist_ok=True)
    for name, data in files.items():
        with open(os.path.join(a.out, name), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("escrito", os.path.join(a.out, name), os.path.getsize(os.path.join(a.out, name)), "bytes")


if __name__ == "__main__":
    main()
