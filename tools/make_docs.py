#!/usr/bin/env python3
"""Gera docs/ARMAS.md (pt-BR) com a tabela de armas, municoes e fabricas a partir de tools/bs_data.py."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bs_data as D  # noqa: E402

TIER = {"early": "Início", "mid": "Meio", "late": "Fim"}
AMMO = {"bullet": "Munição avulsa (jogo base)", "std": "Carregadores (Padrão/Perfurante/Perf.-Explosiva/P.E.M.)",
        "plasma": "Células de plasma", "nuclear": "Projéteis nucleares"}
# arma de modo unico com carregador padrao (Saci): sem seletor, so o Carregador Padrao
AMMO_ONE = {"std": "Carregador Padrão (sem seletor)"}
RES_NAME = {r["id"]: r["name_pt"] for r in D.RESOURCES}
RES_NAME.update({"bullet": "munição", "sulfur": "enxofre", "iron": "ferro", "copper": "cobre", "steel": "aço",
                 "coil": "bobina", "coil2": "hiperbobina", "tristeel": "triaço", "enriched_uranium": "urânio enriquecido",
                 "uranium": "urânio", "carbon": "carbono", "gold": "ouro", "diamond": "diamante", "hyperium": "hipério"})
# pilha da municao do jogo base (resources/bullet/bullet.rules MaxStackSize)
BULLET_STACK = 20


def fmt(n):
    if isinstance(n, float):
        return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{n:,}".replace(",", ".")


# nomes das pecas de missil como o jogo base mostra em pt-br (strings/pt-br.rules Resource/MissilePart*)
RES_SHORT = {"missile_part_he": "peça de míssil A.E.", "missile_part_thermal": "peça de míssil T.",
             "missile_part_emp": "peça de míssil P.E.M.", "missile_part_nuke": "peça de míssil nuclear"}


def fmt_t(x):
    """Tempo/valor com ate 3 casas (1,39 / 0,264 / 9,073)."""
    return f"{x:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def _missile_section():
    """Secao de misseis: lancadores, modos, tipos de missil, arquivos de projetil e techs."""
    from bs_strings import MISSILE_TXT
    L_BY = {L["id"]: L for L in D.MSPEC["launchers"]}
    out = ["## Mísseis de convés", "",
           "> Projeto completo em `docs/MISSEIS_PROJETO.md` (spec `tools/spec/bullet_strike_missiles.json`). "
           "Gerado por `tools/bsgen/launchers.py` e `tools/bsgen/shots.py`.", "",
           "**Como funciona (igual nos três lançadores):** a tripulação leva as peças de míssil do jogo base até um "
           "paiol interno por família (A.E., T., P.E.M., nuclear). Um autocarregador passa um míssil por vez do "
           "paiol para as células visíveis, **só com tripulação no posto**. Com todas as células carregadas sai a "
           "salva em sequência (a última célula carregada dispara primeiro); depois a recarga recomeça. Trocar o "
           "tipo de míssil custa uma recarga completa do tipo novo (com overclock, se as células já estavam cheias "
           "na troca, a primeira salva espera a recarga normal, sem overclock); se o paiol ficar uma recarga inteira "
           "sem receber peças, as células já carregadas disparam mesmo assim (uma entrega atrasada não quebra a "
           "salva cheia). Sem energia. Carregado, o lançador explode junto com o estoque quando pega fogo ou é "
           "destruído: cada peça guardada (no paiol ou já nas células) soma a mesma força à explosão.", "",
           "### Lançadores", "",
           "| Lançador | Codinome | Fase | Tamanho | Trip. | Pontos de comando | Vida | Custo | Salva A.E. | Ciclo A.E. | Alcance | "
           "DPS efetivo por quadro (OC) | Overclock | Limite |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for lch in D.LAUNCHERS:
        L = L_BY[lch["id"]]
        c = L["computed_he"]
        oc = L["overclock"]
        oc_txt = f"{oc['name_ptbr']}" + ("" if lch.get("oc") else " (desligado)")
        # DPS com overclock so quando o overclock existe no jogo (o da Tocandira esta desligado)
        oc_dps = c["oc"]["eff_dps_per_tile"] if (c.get("oc") and lch.get("oc")) else None
        dps = fmt(c["eff_dps_per_tile"]) + (f" ({fmt(oc_dps)})" if oc_dps else "")
        lim = f"{L['per_ship_limit']} por nave (vaga nuclear, com a Boiúna)" if L.get("per_ship_limit") else "-"
        out.append(f"| **{lch['name_pt']}** | {lch['codename']} | {TIER[lch['tier']]} | {lch['size'][0]}x{lch['size'][1]} | "
                   f"{lch['crew']} | {lch['cp']} | {fmt(lch['hp'])} | {fmt(L['build_cost_credits'])} cr | "
                   f"{c['missiles_per_salvo']} em {fmt_t(c['salvo_duration_s'])} s | {fmt_t(c['cycle_s'])} s | "
                   f"{L['range_m']['he']} m | {dps} | {oc_txt} | {lim} |")
    out += ["", "### Modos de cada lançador", "",
            "> Ciclo = recarga de todas as células + salva. Paiol = capacidade da família, em peças. "
            "OC = ciclo com overclock (recarga ÷ 1,5; P.E.M. ÷ 1,2; o nuclear nunca acelera).", "",
            "| Lançador | Míssil | Células | Peças por míssil | Recarga por célula | Salva | Ciclo (OC) | "
            "DPS efetivo por quadro | Paiol | Descarte em OC |",
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
            "direto + 50% das explosões (convenção do spec).", "",
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
    out += ["", "No modo **Construir e Batalhar** a Tocandira já vem liberada (lista branca), mas as peças de míssil A.E. e T. "
            "dela vêm da tech `rafaeltessaro.bs_bb_bs_msl_box_ammo` (5.000, sempre oferecida), porque o jogo base só "
            "libera esses recursos com as techs dos lançadores do jogo base; a Caipora e a Mula-sem-Cabeça são techs de "
            "5.000 (com o overclock à parte), que também liberam as peças de míssil das suas famílias.", ""]
    return out


def fmt2(x):
    """Numero com ate 2 casas em pt-br (0,35 / 1,6 / 11,25)."""
    return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")


# ----------------------------------------------------------------------------- logistica
# producao de cada recurso: (fabrica, unidades/s sem bonus); a municao do jogo base vem da Fabrica de Municao
# para Canhao vanilla (bs_strings.VANILLA_AMMO_PER_S, factory_ammo.rules: 1 a cada 0,5 s)
PROD = {f["output"][0]: (f, f["output"][1] / f["interval"]) for f in D.FACTORIES}
STACK = {r["id"]: r["max_stack"] for r in D.RESOURCES}
STACK["bullet"] = BULLET_STACK
FAC_PT = "Fábrica de munição para canhão"


def _chain(res, per_s, acc):
    """Soma em acc {fabrica: quantidade} o que sustenta per_s unidades/s de res, descendo a cadeia
    (municao -> Carregador Padrao -> carregador especial / projetil nuclear). Insumos vanilla (triaco, cobre,
    enxofre, bobina, uranio) nao entram."""
    from bs_strings import VANILLA_AMMO_PER_S
    if res == "bullet":
        acc[FAC_PT] = acc.get(FAC_PT, 0) + per_s / VANILLA_AMMO_PER_S
        return
    f, rate = PROD[res]
    acc[f["name_pt"]] = acc.get(f["name_pt"], 0) + per_s / rate
    for r, q in f["inputs"]:
        if r == "bullet" or r in PROD:
            _chain(r, per_s * q / f["output"][1], acc)


def _plural_fac(name):
    """'Prensa de Carregadores' -> 'Prensas de Carregadores', 'Fundicao de ...' -> 'Fundicoes de ...'."""
    head, _, rest = name.partition(" ")
    head = head[:-3] + "ções" if head.endswith("ção") else head + "s"
    return f"{head} {rest}".strip()


def _feed(g):
    """(recurso, disparos por unidade, unidades/s em fogo continuo) com a municao padrao (modo 0).
    fire_rate_shots_per_s e a cadencia sustentada (nas armas que aceleram, ja na rotacao maxima)."""
    a = g["ammo"] if g in D.DEFENSES else g["modes"][0]
    per = a["shots_per_unit"] / a["units_per_shot"]
    return a["res"], per, g["spec"]["fire_rate_shots_per_s"] / per


def _res_q(r, q):
    """Quantidade + nome do recurso, no plural quando passa de 1 (ex.: 2 Carregadores Padrao, 5 municoes)."""
    from bs_strings import PLURAL_PT
    name = RES_NAME.get(r, r)
    if q > 1:
        name = "munições" if r == "bullet" else PLURAL_PT.get(name, name)
    return f"{fmt_t(q)} {name}"


def _res_label(r):
    return "Munição" if r == "bullet" else RES_NAME.get(r, r)


def _per_txt(g, per, res):
    """Disparos por unidade do recurso (ex.: 50 disparos, 1 disparo, 5 explosoes aereas, 2 carregadores por disparo)."""
    if per >= 1:
        one, many = ("explosão aérea", "explosões aéreas") if g in D.DEFENSES else ("disparo", "disparos")
        return f"{fmt2(per)} {one if per == 1 else many}"
    noun = {"bullet": "munições"}.get(res) or ("carregadores" if "_mag_" in res else "unidades")
    return f"{int(round(1 / per))} {noun} por disparo"


def _logistics_section():
    out = ["## Logística por arma", "",
           "> Fogo contínuo com munição Padrão (nas armas que aceleram, na rotação máxima), sem overclock e sem "
           "bônus de fábrica vizinha. Viagens = viagens de tripulação por minuto com a pilha cheia. As fábricas "
           "contam a cadeia inteira (munição -> Carregador Padrão -> munição especial); insumos do jogo base "
           "(triaço, cobre, enxofre, bobina, urânio enriquecido) ficam de fora.", "",
           "| Arma | Codinome | Recurso | Disparos por unidade | Consumo | Viagens/min | Fábricas de munição para "
           "canhão | Fábricas do Bullet Strike |",
           "|---|---|---|---|---|---|---|---|"]
    for tier in ("early", "mid", "late"):
        for g in D.GUNS + D.DEFENSES:
            if g["tier"] != tier:
                continue
            res, per, ups = _feed(g)
            acc = {}
            _chain(res, ups, acc)
            van = acc.pop(FAC_PT, 0)
            bs = ", ".join(f"{fmt2(n)} {_plural_fac(name) if n >= 2 else name}" for name, n in acc.items()) or "-"
            out.append(f"| {g['name_pt']} | **{g['codename']}** | {_res_label(res)} | "
                       f"{_per_txt(g, per, res)} | {fmt2(ups)}/s | {fmt2(ups * 60 / STACK[res])} | "
                       f"{fmt2(van) if van else '-'} | {bs} |")
    return out + [""]


def _resources_section():
    """Municoes: pilha por viagem, onde e feita e quem usa (disparos por unidade), em pt-br."""
    users = {}
    for g in D.GUNS + D.DEFENSES:
        modes = [g["ammo"]] if g in D.DEFENSES else g["modes"]
        for a in modes:
            lst = users.setdefault(a["res"], [])
            txt = f"{g['codename']} ({_per_txt(g, a['shots_per_unit'] / a['units_per_shot'], a['res'])})"
            if txt not in lst:
                lst.append(txt)
    out = ["## Munições", "",
           "> Pilha = quanto um tripulante leva por viagem (e cabe num quadro de depósito).", "",
           "| Recurso | Pilha | Fábrica | Receita por unidade | Quem usa (por unidade) |", "|---|---|---|---|---|"]
    out.append(f"| **Munição** (jogo base) | {BULLET_STACK} | {FAC_PT} (jogo base) | - | "
               f"{', '.join(users.get('bullet', []))}; também é a matéria-prima da Prensa de Carregadores |")
    for r in D.RESOURCES:
        f, _rate = PROD[r["id"]]
        oq = f["output"][1]
        rec = " + ".join(_res_q(x, q / oq) for x, q in f["inputs"])
        if f.get("power"):
            rec += f" + {fmt_t(f['power'] / 1000 / oq)} de energia"
        use = ", ".join(users.get(r["id"], []))
        made_of = [g["name_pt"] for g in D.FACTORIES if any(x == r["id"] for x, _q in g["inputs"])]
        if made_of:
            use += ("; " if use else "") + "matéria-prima de: " + ", ".join(made_of)
        out.append(f"| **{r['name_pt']}** | {r['max_stack']} | {f['name_pt']} | {rec} | {use} |")
    return out + [""]


def _factories_section():
    from bs_strings import VANILLA_AMMO_PER_S
    out = ["## Fábricas", "",
           "> Produção sem bônus. Como no jogo base: +25% de velocidade para cada fábrica vizinha e overclock "
           "(liberado por tech na Carreira) que multiplica a velocidade em troca de calor.", "",
           "| Fábrica | Tamanho | Entrada | Saída | Tempo | Produção | Energia | Overclock |",
           "|---|---|---|---|---|---|---|---|"]
    for f in D.FACTORIES:
        ins = " + ".join(_res_q(r, q) for r, q in f["inputs"])
        out_r, out_q = f["output"]
        outs = _res_q(out_r, out_q)
        pw = f"{fmt_t(f['power'] / 1000)} por ciclo" if f.get("power") else "não usa"
        oc = f.get("oc")
        if oc:
            # calor/s em overclock = calor por ciclo x fator de velocidade / intervalo (factory_he.rules SecondaryToolTip)
            hs = oc["heat_per_conversion"] * oc["speed_factor"] / f["interval"]
            ocs = f"{fmt2(oc['speed_factor'])}x mais rápida, {fmt(round(hs))} MJ/s de calor"
            if f.get("power"):
                ocs += f", {fmt2(oc['power_use_factor'])}x energia por ciclo"
        else:
            ocs = "-"
        size = f"{f['size'][0]}x{f['size'][1]}" if f.get("size") else "-"
        out.append(f"| **{f['name_pt']}** | {size} | {ins} | {outs} | {fmt_t(f['interval'])} s | "
                   f"{fmt_t(out_q / f['interval'])}/s | {pw} | {ocs} |")
    out += ["", "**Proporções** (valem com os mesmos bônus dos dois lados: vizinhança e overclock):", ""]
    for f in D.FACTORIES:
        for r, q in f["inputs"]:
            need = q / f["interval"]
            if r == "bullet":
                n = need / VANILLA_AMMO_PER_S
                out.append(f"- {fmt2(n)} {FAC_PT if n == 1 else 'Fábricas de munição para canhão'} "
                           f"alimenta{'' if n == 1 else 'm'} 1 {f['name_pt']} ({fmt2(need)} munições/s).")
            elif r in PROD:
                src, rate = PROD[r]
                out.append(f"- {f['name_pt']}: consome {fmt2(need)} {RES_NAME[r]}/s, ou seja, cada {src['name_pt']} "
                           f"({fmt2(rate)}/s) abastece {fmt2(rate / need)} dessas fábricas.")
    return out + [""]


CAT_PT = {"missile": "mísseis", "mine": "minas", "bullet": "projéteis", "laser": "lasers", "ion_shot": "tiros iônicos"}


def _defense_section():
    """Defesas: as duas cargas da rajada (projeteis / lasers e ions do SW:ACD), giro e angulo de disparo da torre.
    Numeros do spec (anti_projectile, rotate_speed_deg_s, fire_threshold_deg, random_offset_radius_m)."""
    from bsgen import common as C
    def _e(lst):
        names = [CAT_PT[c] for c in lst]
        return ", ".join(names[:-1]) + " e " + names[-1] if len(names) > 1 else names[0]
    prio = _e(C.PD_PRIORITY_TARGETS)
    sec = _e(C.PD_SECONDARY_TARGETS)
    out = ["## Defesas (Tatu, Tamanduá e Pororoca)", "",
           "> Cada rajada leva **duas cargas separadas**: uma contra mísseis, minas e projéteis, e outra, mais forte e "
           "maior, "
           "só contra os disparos laser e os tiros iônicos (os turbolasers e canhões iônicos do SW:ACD têm muita "
           "vida). A torre procura primeiro " + prio + "; " + sec + " ficam numa segunda lista de alvos. A torre "
           "não volta ao centro entre um alvo e outro. Feixes contínuos (o prisma iônico do jogo, os feixes do SW:ACD) "
           "não são projéteis e não podem ser abatidos.", "",
           "| Defesa | Codinome | Contra mísseis, minas e projéteis | Contra lasers e tiros iônicos | Por segundo "
           "(projéteis / lasers) | Giro da torre | Atira a menos de | Espalhamento da rajada |",
           "|---|---|---|---|---|---|---|---|"]
    for g in D.DEFENSES:
        w = g["spec"]
        ap = w["anti_projectile"]
        c = w["computed"]
        ro = w["random_offset_radius_m"]
        out.append(f"| **{g['name_pt']}** | {g['codename']} | {fmt(ap['damage_vs_shots'])} em {fmt2(ap['blast_radius_m'])} m | "
                   f"{fmt(ap['damage_vs_lasers'])} em {fmt2(ap['blast_radius_vs_lasers_m'])} m | "
                   f"{fmt(round(c['anti_shot_pool_per_s']))} / {fmt(round(c['anti_laser_pool_per_s']))} | "
                   f"{w['rotate_speed_deg_s']}°/s | {fmt2(w['fire_threshold_deg'])}° do alvo | "
                   f"{fmt2(ro[0])} a {fmt2(ro[1])} m |")
    return out + [""]


# ----------------------------------------------------------------------------- efeitos visuais
LOOK_PT = {"tracer": "traçante", "shell": "granada 3D", "nuke_shell": "granada nuclear 3D"}
MSL_COLOR_PT = {"he": "âmbar", "napalm": "laranja", "cluster": "amarelo", "limpet": "vermelho", "emp": "azul",
                "torpedo": "branco-azulado", "nuclear": "verde"}
MSL_TYPE_PT = {"he": "Jararaca / Muriçoca (A.E.)", "napalm": "Taturana / Taturana-mirim (napalm)",
               "cluster": "Piranha (submunições)", "limpet": "Carrapato (grudento)", "emp": "Poraquê (P.E.M.)",
               "torpedo": "Boto (torpedo com iscas)", "nuclear": "Iara (torpedo nuclear)"}
SMOKE_PT = {"grey": "cinza", "wake": "esteira branca", "faint": "fraca", "oily": "oleosa", "nuke": "nuclear"}
MSL_EXTRA_PT = {"he": "-",
                "napalm": "fogo no escapamento; gotas de napalm e estilhaços térmicos no impacto",
                "cluster": "clarão amarelo e estilhaços quando abre; filhotes só com um feixe curto, sem fumaça",
                "limpet": "clarão vermelho ao grudar; a carga mostra uma contagem regressiva de 2,5 s (10 quadros) "
                          "e explode com outro clarão vermelho",
                "emp": "faíscas elétricas no escapamento",
                "torpedo": "anel e clarão brancos no impacto; baforada e destroços na separação da ogiva; sopro x1,4 "
                           "no lançamento",
                "nuclear": "fogo verde, trevo de radiação girando; no impacto, anel verde, brilho residual e o tremor "
                           "da Boiúna (0,5 por 1,5 s); abatido, "
                           "vaza verde com um anel pequeno; baforada e destroços na separação da ogiva; sopro x1,4 e "
                           "tremor no lançamento"}


def _visual_section():
    """Efeitos visuais por calibre (tools/spec/bullet_strike_vfx.json, bsgen/caliber_fx.py) e dos misseis
    (tools/spec/bullet_strike_missile_fx.json, bsgen/missile_fx.py). Le as tabelas que o gerador usa."""
    import json
    spec_dir = os.path.join(HERE, "spec")
    vfx_p = os.path.join(spec_dir, "bullet_strike_vfx.json")
    mfx_p = os.path.join(spec_dir, "bullet_strike_missile_fx.json")
    if not (os.path.exists(vfx_p) and os.path.exists(mfx_p)):
        return []
    vfx = json.load(open(vfx_p, encoding="utf-8"))
    mfx = json.load(open(mfx_p, encoding="utf-8"))
    out = ["## Efeitos visuais", "",
           "> Só visual: nenhum número de dano, alcance ou cadência muda. O tamanho de tudo segue o calibre: "
           "7,62 < 12,7 < 20 < 30 < 76 < 155 < 406 < nuclear. Escalas em relação ao efeito do jogo base que cada "
           "arma usa (1 = tamanho do jogo). Gerado de `tools/spec/bullet_strike_vfx.json` (`tools/bsgen/caliber_fx.py`) "
           "e `tools/spec/bullet_strike_missile_fx.json` (`tools/bsgen/missile_fx.py`). Um build com `BS_FX_EXT=0` "
           "volta ao visual antigo (as mudanças das defesas continuam).", "",
           "### Por calibre", "",
           "| Arma | Codinome | Calibre | Em voo (tiles) | Clarão de boca (OC) | Fumaça na culatra | Impacto no casco | "
           "Tremor (disparo / impacto) |",
           "|---|---|---|---|---|---|---|---|"]
    names = {g["short"]: g for g in D.GUNS + D.DEFENSES}
    for short in vfx["order"]:
        w = vfx["weapons"][short]
        g = names.get(short)
        pr, mz, im = w["projectile"], w["muzzle"], w["impact"]
        mm = w["mm"]
        cal = (fmt2(mm) + " mm") if short != "bs_nuke_howitzer" else f"{fmt2(mm)} mm (visual)"
        if pr is None:
            fly = "- (explode no ar)"
        elif pr["look"] == "tracer":
            fly = f"traçante {fmt2(pr['streak'][0])} x {fmt2(pr['streak'][1])}"
        else:
            fly = (f"{LOOK_PT[pr['look']]} {fmt2(pr['body'][0])} x {fmt2(pr['body'][1])} + traçante "
                   f"{fmt2(pr['tracer'][0])}")
            if pr.get("smoke_trail"):
                fly += " + esteira de fumaça"
        n_sc = mz["N"][0][1]
        mzt = f"x{fmt2(n_sc)}" + (f" ({'x' + fmt2(mz['OC'][0][1])})" if mz.get("OC") else "")
        breech = "sim" if any(len(e) > 2 and e[2].get("at") == "breech" for e in mz["N"]) else "-"
        if im.get("burst"):
            n0, n1 = im["shrapnel_n"]
            hit = f"rajada x{fmt2(im['burst'][1])}, {n0} a {n1} estilhaços"
        else:
            first = next(iter(im["hull"].values()))
            hit = f"x{fmt2(first[1])}"
        # tremor com todas as casas (0,015 do Furacao; fmt2 arredondava para 0,01)
        shk = lambda s: f"{s[0]:g}".replace(".", ",") if s and s[0] else "-"  # noqa: E731
        out.append(f"| {g['name_pt'] if g else short} | **{w['codename']}** | {cal} | {fly} | {mzt} | {breech} | {hit} | "
                   f"{shk(mz.get('shake'))} / {shk(im.get('shake'))} |")
    out += ["", "Boitatá e Curupira têm efeitos próprios de plasma (`tools/bsgen/plasma_fx.py`); sobre casco branco o "
            "raio aparece como uma lança com contorno escuro, sem névoa clara.", "",
            "### Mísseis", "",
            "> Cada tipo tem arte 3D própria (`art3d/bs_missiles`, 22 desenhos: 3 tamanhos por fase, ogivas, iscas, "
            "filhotes e a carga do Carrapato), luzes piscando e um feixe de escapamento na cor do tipo. Fases: "
            "s = Tocandira, m = Caipora, l = Mula-sem-Cabeça. Fumaça em partículas por segundo; impacto = escala da "
            "explosão do jogo base.", "",
            "| Míssil | Escapamento | Fumaça (s / m / l) | Impacto (s / m / l) | Extras |", "|---|---|---|---|---|"]
    hms = mfx["hit_media_scale"]
    hkey = mfx["hit_scale_key"]["main"]
    for typ in ("he", "napalm", "cluster", "limpet", "emp", "torpedo", "nuclear"):
        smk, imp = [], []
        for t in ("s", "m", "l"):
            it = mfx["items"].get(f"{typ}_{t}")
            if it is None:
                smk.append("-")
                imp.append("-")
                continue
            sm = it["exhaust"].get("smoke")
            smk.append(f"{SMOKE_PT[sm[0]]} {sm[1]}" if sm else "sem fumaça")
            sc = hms.get(hkey[typ], {}).get(t)
            imp.append(f"x{fmt2(sc)}" if sc is not None else "-")
        out.append(f"| {MSL_TYPE_PT[typ]} | feixe {MSL_COLOR_PT[typ]} | {' / '.join(smk)} | {' / '.join(imp)} | "
                   f"{MSL_EXTRA_PT[typ]} |")
    return out + [""]


def main():
    lines = ["# Bullet Strike: armas, munições e fábricas", "",
             "> Gerado automaticamente por `tools/make_docs.py` a partir de `tools/spec/bullet_strike_spec.json` e "
             "`tools/spec/bullet_strike_missiles.json`. Não edite à mão.",
             "> DPS = dano por segundo com munição padrão, sem overclock: dano direto + metade das explosões "
             "(convenção do spec). As defesas (Tatu, Tamanduá e Pororoca) só defendem: não causam dano em naves; "
             "a coluna mostra o dano por segundo contra projéteis.", ""]
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
                # so defesa: nenhum dano em nave, so a explosao contra projeteis; a carga separada contra os lasers
                # e tiros ionicos do SW:ACD (defense_design C8) vem de damage_vs_lasers
                dps = (f"só defesa: {fmt(round(ap['damage_vs_shots'] * w['fire_rate_shots_per_s']))}/s contra projéteis"
                       f" e {fmt(round(ap['damage_vs_lasers'] * w['fire_rate_shots_per_s']))}/s contra laser")
                ammo = "Carregador Padrão" if g["ammo"]["res"] != "bullet" else AMMO["bullet"]
            else:
                dps = fmt(round(w["computed"].get("dps_hull_std", 0)))
                a = g["modes"][0]["ammo"]
                ammo = AMMO["std"] if len(g["modes"]) > 1 else AMMO_ONE.get(a) or AMMO.get(a, a)
            oc = w["overclock"]["name_ptbr"] if g.get("oc") else "-"
            lines.append(f"| **{g['name_pt']}** | {g.get('codename', '')} | {w['size'][0]}x{w['size'][1]} | {w['crew']} | "
                         f"{w['range_m']} m | {dps} | {ammo} | {oc} |")
        lines.append("")
    lines += _defense_section()
    if D.LAUNCHERS:
        lines += _missile_section()
    lines += _resources_section()
    lines += _factories_section()
    lines += _logistics_section()
    lines += ["## Tipos de munição (seletor das armas de meio/fim de jogo)", "",
              "Armas com seletor: " + ", ".join(f"{g['codename']}" for g in D.GUNS if g["selector"]) +
              ". Perfurante e Perfurante-Explosiva usam o mesmo Carregador Perfurante.", "",
              "Ao trocar de munição, cada modo continua com o próprio depósito na arma (Perfurante e "
              "Perfurante-Explosiva usam o mesmo Carregador Perfurante, mas cada um guarda o seu); a tripulação só "
              "reabastece o modo escolhido e nenhum carregador sai como outro tipo. Para testar, monte a nave sem \"Reabastecer todos os recursos\" e sem recursos cheios, "
              "porque os dois enchem os depósitos de **todos** os tipos na arma. Se o depósito P.E.M. já estiver cheio, o certo é "
              "a arma atirar P.E.M. desse depósito e os Carregadores Padrão continuarem no depósito deles.", "",
              "| Tipo | Carregador | Para que serve |", "|---|---|---|"]
    from bs_strings import AMMO_DESC, AMMO_NAMES
    sel = next(g for g in D.GUNS if g["selector"])
    res_of = {m["ammo"]: m["res"] for m in sel["modes"]}
    for a in ("std", "ap", "aphe", "emp"):
        lines.append(f"| **{AMMO_NAMES[a][1]}** | {RES_NAME[res_of[a]]} | {AMMO_DESC[a][1]} |")
    lines.append("")
    lines += _visual_section()
    path =os.path.join(HERE, "..", "docs", "ARMAS.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("docs/ARMAS.md gerado")


if __name__ == "__main__":
    main()
