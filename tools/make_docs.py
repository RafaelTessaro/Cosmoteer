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


RES_SHORT = {"missile_part_he": "peça de míssil A.E.", "missile_part_thermal": "peça de míssil T.C.",
             "missile_part_emp": "peça de míssil PEM", "missile_part_nuke": "peça de míssil nuclear"}


def fmt_t(x):
    """Tempo/valor com ate 3 casas (1,39 / 0,264 / 9,073)."""
    return f"{x:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def _missile_section():
    """Seção de mísseis: lançadores, modos, tipos de míssil, arquivos de projétil e techs."""
    from bs_strings import MISSILE_TXT
    L_BY = {L["id"]: L for L in D.MSPEC["launchers"]}
    out = ["## Mísseis de convés", "",
           "> Projeto completo em `docs/MISSEIS_PROJETO.md` (spec `tools/spec/bullet_strike_missiles.json`). "
           "Gerado por `tools/bsgen/launchers.py` e `tools/bsgen/shots.py`.", "",
           "**Como funciona (igual nos três lançadores):** a tripulação leva as peças de míssil do jogo base até um "
           "paiol interno por família (A.E., térmica, PEM, nuclear). Um autocarregador passa um míssil por vez do "
           "paiol para as células visíveis, **só com tripulação no posto**. Com o rack cheio sai a salva em "
           "sequência (a última célula carregada dispara primeiro); depois a recarga recomeça. Trocar o tipo de "
           "míssil custa uma recarga completa do tipo novo; com o paiol vazio, o rack parcial dispara mesmo assim. "
           "Sem energia. Carregado, o lançador explode junto com o estoque quando pega fogo ou é destruído.", "",
           "### Lançadores", "",
           "| Lançador | Codinome | Fase | Tamanho | Trip. | CP | Vida | Custo | Salva HE | Ciclo HE | Alcance | "
           "DPS efetivo/tile (OC) | Overclock | Limite |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for lch in D.LAUNCHERS:
        L = L_BY[lch["id"]]
        c = L["computed_he"]
        oc = L["overclock"]
        oc_txt = f"{oc['name_ptbr']}" + ("" if lch.get("oc") else " (desligado)")
        oc_dps = c["oc"]["eff_dps_per_tile"] if c.get("oc") else None
        dps = fmt(c["eff_dps_per_tile"]) + (f" ({fmt(oc_dps)})" if oc_dps else "")
        lim = f"{L['per_ship_limit']} por nave (vaga nuclear, com a Boiúna)" if L.get("per_ship_limit") else "-"
        out.append(f"| **{lch['name_pt']}** | {lch['codename']} | {TIER[lch['tier']]} | {lch['size'][0]}x{lch['size'][1]} | "
                   f"{lch['crew']} | {lch['cp']} | {fmt(lch['hp'])} | {fmt(L['build_cost_credits'])} cr | "
                   f"{c['missiles_per_salvo']} em {fmt_t(c['salvo_duration_s'])} s | {fmt_t(c['cycle_s'])} s | "
                   f"{L['range_m']['he']} m | {dps} | {oc_txt} | {lim} |")
    out += ["", "### Modos de cada lançador", "",
            "> Ciclo = recarga do rack inteiro + salva. Paiol = capacidade da família, em peças. "
            "OC = ciclo com overclock (recarga ÷ 1,5; PEM ÷ 1,2; o nuclear nunca acelera).", "",
            "| Lançador | Míssil | Células | Peças por míssil | Recarga por célula | Salva | Ciclo (OC) | "
            "DPS efetivo/tile | Paiol | Descarte em OC |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for lch in D.LAUNCHERS:
        mags = {f["key"]: f["mag"] for f in lch["families"]}
        for m in lch["modes"]:
            c = m["computed"]
            cyc = fmt_t(c["cycle_s"]) + " s"
            if lch.get("oc") and m["oc_factor"] and c.get("oc"):
                cyc += f" ({fmt_t(c['oc']['cycle_s'])} s)"
            elif lch.get("oc"):
                cyc += " (sem OC)"
            per = m["parts"] / m["mpu"]
            per_txt = (fmt_t(per) if per != int(per) else str(int(per))) + " " + \
                (RES_SHORT[m["res"]].replace("peça ", "peças ", 1) if per > 1 else RES_SHORT[m["res"]])
            vent = f"{m['vent']} peças/salva" if (lch.get("oc") and m["vent"]) else "-"
            out.append(f"| {lch['codename']} | {m['name_pt']} ({m['codename']}) | {m['cells']}"
                       f"{' cassetes' if m['mpu'] > 1 else ''} | {per_txt} | "
                       f"{fmt_t(m['reload'])} s | {c['missiles_per_salvo']} em {fmt_t(c['salvo_duration_s'])} s | {cyc} | "
                       f"{fmt(c['eff_dps_per_tile'])} | {mags[m['family']]} | {vent} |")
    out += ["", "### Tipos de míssil (seletor do lançador)", "",
            "| # | Codinome | Míssil | Recurso | Lançadores | O que faz |", "|---|---|---|---|---|---|"]
    for mt in D.MSPEC["missile_types"]:
        lnames = ", ".join(L_BY[v["launcher"]]["codename"] for v in mt["variants"])
        out.append(f"| {mt['toggle_index']} | **{mt['codename']}** | {mt['name_ptbr']} | {RES_SHORT[mt['ammo_resource']]} | "
                   f"{lnames} | {MISSILE_TXT[mt['id']][3]} |")
    out += ["", "### Arquivos de projétil", "",
            "> Um arquivo por tipo de míssil e por lançador (`missile_types[].variants[].files`). Dano efetivo = "
            "direto + 50 % das explosões (convenção do spec).", "",
            "| Míssil | Codinome | Lançador | HP | Velocidade / acel. / giro | Alcance | Dano explosivo | Efetivo | Arquivos |",
            "|---|---|---|---|---|---|---|---|---|"]
    for s_ in D.MISSILES:
        lname = L_BY[s_["launcher"]]["codename"]
        files = ", ".join(f"`{f}`" for f in [s_["file"]] + [c_["file"] for c_ in s_["children"]])
        out.append(f"| {s_['name_pt']} | {s_['codename']} | {lname} | {fmt(s_['hp'])} | "
                   f"{s_['speed']} / {s_['accel']} / {s_['turn']}° | {s_['range']} m | {fmt(s_['alpha'])} | "
                   f"{fmt(s_['eff'])} | {files} |")
    out += ["", "### Techs da Carreira", "", "| Tech | Custo | Pré-requisitos | Libera |", "|---|---|---|---|"]
    built = {lch["id"] for lch in D.LAUNCHERS}
    for t in D.MSPEC["career_techs"]:
        if t.get("enabled") is False:
            continue
        unl = []
        for u in t["unlocks"]:
            if u.startswith("missile:"):
                mt = D.MISSILE_TYPES[u.split(":", 1)[1]]
                names = []
                for v in mt["variants"]:
                    if v["variant_codename"] not in names:
                        names.append(v["variant_codename"])
                unl.append(f"{mt['name_ptbr'].split(' (')[0]} ({'/'.join(names)})")
            elif u.startswith("overclock:"):
                unl.append(f"overclock da {L_BY[u.split(':', 1)[1]]['codename']}")
            elif u in built:
                unl.append(L_BY[u]["codename"])
        out.append(f"| `{t['id']}` | {fmt(int(t['cost_credits']))} | {', '.join(f'`{p}`' for p in t['prerequisites'])} | "
                   f"{', '.join(unl)} |")
    out += ["", "No **Build & Battle** a Tocandira já vem liberada (lista branca) e a Caipora e a Mula-sem-Cabeça "
            "são techs de 5000 (com o overclock à parte), que também liberam as peças de míssil das suas famílias.", ""]
    return out


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
    if D.LAUNCHERS:
        lines += _missile_section()
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
