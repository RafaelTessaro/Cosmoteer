#!/usr/bin/env python3
"""Gera docs/ARMAS.md (pt-BR) com a tabela de armas, municoes e fabricas a partir de tools/bs_data.py."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bs_data as D  # noqa: E402

TIER = {"early": "Início", "mid": "Meio", "late": "Fim"}
AMMO = {"bullet": "Munição avulsa (vanilla)", "std": "Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP)",
        "plasma": "Células de plasma", "nuclear": "Projéteis nucleares"}
RES_NAME = {r["id"]: r["name_pt"] for r in D.RESOURCES}
RES_NAME.update({"bullet": "munição", "sulfur": "enxofre", "iron": "ferro", "copper": "cobre", "steel": "aço",
                 "coil": "bobina", "coil2": "hiperbobina", "tristeel": "tri-aço", "enriched_uranium": "urânio enriquecido",
                 "uranium": "urânio", "carbon": "carbono", "gold": "ouro", "diamond": "diamante", "hyperium": "hiperium"})


def fmt(n):
    if isinstance(n, float):
        return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{n:,}".replace(",", ".")


def main():
    lines = ["# Bullet Strike: armas, munições e fábricas", "",
             "> Gerado automaticamente por `tools/make_docs.py` a partir de `tools/spec/bullet_strike_spec.json`.",
             "> DPS = dano por segundo com munição padrão, sem overclock (explosões contam inteiras).", ""]
    for tier in ("early", "mid", "late"):
        lines += [f"## {TIER[tier]} de jogo", "",
                  "| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |",
                  "|---|---|---|---|---|---|---|---|"]
        for g in D.GUNS + D.DEFENSES:
            if g["tier"] != tier:
                continue
            w = g["spec"]
            if g in D.DEFENSES:
                ap = w["anti_projectile"]
                dps = f"{fmt(round(ap['damage_vs_shots'] * w['fire_rate_shots_per_s']))}/s contra projéteis"
                ammo = "Carregador padrão" if g["ammo"]["res"] != "bullet" else AMMO["bullet"]
            else:
                dps = fmt(round(w["computed"].get("dps_hull_std", 0)))
                a = g["modes"][0]["ammo"]
                ammo = AMMO["std"] if len(g["modes"]) > 1 else AMMO.get(a, a)
            oc = "sim" if g.get("oc") else "-"
            lines.append(f"| **{g['name_pt']}** | {g.get('codename', '')} | {w['size'][0]}x{w['size'][1]} | {w['crew']} | "
                         f"{w['range_m']} m | {dps} | {ammo} | {oc} |")
        lines.append("")
    lines += ["## Munições", "", "| Recurso | Pilha por tile | Observação |", "|---|---|---|"]
    for r in D.RESOURCES:
        lines.append(f"| **{r['name_pt']}** | {r['max_stack']} | {r['note']} |")
    lines += ["", "## Fábricas", "", "| Fábrica | Entrada | Saída | Tempo | Energia |", "|---|---|---|---|---|"]
    for f in D.FACTORIES:
        ins = " + ".join(f"{q} {RES_NAME.get(r, r)}" for r, q in f["inputs"])
        out = f"{f['output'][1]} {RES_NAME.get(f['output'][0], f['output'][0])}"
        pw = f"{f['power'] / 1000:g} bateria/ciclo" if f.get("power") else "não usa"
        lines.append(f"| **{f['name_pt']}** | {ins} | {out} | {f['interval']:g} s | {pw} |")
    lines += ["", "## Tipos de munição (seletor das armas de meio/fim de jogo)", "",
              "| Tipo | Para que serve |", "|---|---|"]
    from bs_strings import AMMO_DESC, AMMO_NAMES
    for a in ("std", "ap", "aphe", "emp"):
        lines.append(f"| **{AMMO_NAMES[a][1]}** | {AMMO_DESC[a][1]} |")
    lines.append("")
    path = os.path.join(HERE, "..", "docs", "ARMAS.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("docs/ARMAS.md gerado")


if __name__ == "__main__":
    main()
