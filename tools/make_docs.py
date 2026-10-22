#!/usr/bin/env python3
"""Documentacao pt-BR do Bullet Strike 2.0 (dono: WP14b). Todo numero sai do spec (tools/spec/) e da camada de dados
(tools/bs_data.py, com os switches do build); nada de numero digitado a mao.

Gera:
    README.md                      novidades da 2.0, aviso de ruptura, qual pasta instalar, armas, build
    docs/ARMAS.md                  canhoes, defesas, PEM, Tupa, lancadores, fabricas, paiois, Fita, techs, balanco
    docs/MISSEIS_PROJETO.md        lancadores e misseis 2.0
    docs/COMO_TESTAR.md            aponta para o checklist; valores 'safe' em uso; testes x itens
    docs/CHECKLIST_2_0.md          o que o usuario testa no jogo (tools/spec/checklist_2_0.json)
    docs/preview/2.0/LEIA.md       aponta para docs/preview/3d/v2/
    CHECKLIST_2_0_CURTO.txt        so com --curto CAMINHO (raiz dos 2 zips do pacote final)

Uso:
    python3 tools/make_docs.py [--curto CAMINHO] [--check] [--estrito]
      --check    nao grava; sai 1 se algum arquivo gerado mudaria (validacao 'docs sem diff')
      --estrito  sai 1 se sobrar algum 'a confirmar' (modulo PEM/Tupa ausente, switches.json ausente...);
                 o pacote final (WP14b) roda sempre com --estrito
Sempre: a varredura de nomes removidos (SPEC.conventions.removed_names_scan) e do nome antigo da PEM pesada roda
em todo texto gerado; achou -> sai 1 sem gravar nada.

Os docs descrevem o build oficial (variante 'fita' + tools/spec/bullet_strike_switches.json): variaveis BS_* do
ambiente sao ignoradas. Sem o switches.json (WP14a ainda nao gravou) usa SPEC.build_2_0.switch_values_fita e marca
'a confirmar'.
"""

import argparse
import json
import math
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
SPEC_DIR = os.path.join(HERE, "spec")
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

AVISOS = []      # avisos do gerador (stderr)
PENDENTES = []   # 'a confirmar': com --estrito a lista tem que ficar vazia


def aviso(msg):
    if msg not in AVISOS:
        AVISOS.append(msg)
        print(f"(aviso) {msg}", file=sys.stderr)


def pendente(o_que):
    """Registra uma pendencia e devolve a marca que vai no texto."""
    if o_que not in PENDENTES:
        PENDENTES.append(o_que)
    return f"_(a confirmar: {o_que})_"


def _json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _preparar_ambiente():
    """Docs = build oficial: variante fita, switches do arquivo; overrides BS_* do ambiente nao valem aqui."""
    ignorar = sorted(k for k in os.environ if k.startswith("BS_") and k != "BS_ARTE_PROCEDURAL")
    for k in ignorar:
        del os.environ[k]
    if ignorar:
        aviso(f"variaveis ignoradas (os docs descrevem o build oficial): {', '.join(ignorar)}")
    os.environ["BS__VARIANTE"] = "fita"
    sw_file = os.path.join(SPEC_DIR, "bullet_strike_switches.json")
    if not os.path.isfile(sw_file):
        spec = _json(os.path.join(SPEC_DIR, "bullet_strike_spec.json"))
        defs = {f"{g}.{n}" for g, d in spec["switches"].items() if isinstance(d, dict)
                for n, e in d.items() if isinstance(e, dict) and "default" in e}
        vals = {k: v for k, v in spec["build_2_0"]["switch_values_fita"].items() if k in defs}
        os.environ["BS__CLI_SWITCHES"] = json.dumps(vals)
        pendente("tools/spec/bullet_strike_switches.json ainda nao gravado (WP14a): valores de "
                 "SPEC.build_2_0.switch_values_fita")


_preparar_ambiente()
import bs_data as D  # noqa: E402
from bsgen import common as C  # noqa: E402

FULL = _json(os.path.join(SPEC_DIR, "SPEC_2.0.json"))
ADD = _json(os.path.join(SPEC_DIR, "ADDENDUM_2_0.json"))
_CHK_PATH = os.path.join(SPEC_DIR, "checklist_2_0.json")
CHK = _json(_CHK_PATH) if os.path.isfile(_CHK_PATH) else dict(ADD["checklist"], _meta={})
if not os.path.isfile(_CHK_PATH):
    aviso("tools/spec/checklist_2_0.json ausente: usando ADDENDUM_2_0.json 'checklist' sem as correcoes")
MSPEC = D.MSPEC["missiles"]
RAIL = D.RAIL
BAL = FULL["balance"]

GERADO = ("> Gerado por `tools/make_docs.py` a partir de `tools/spec/` (spec 2.0) e da camada de dados "
          "`tools/bs_data.py`, com os switches do build. Não edite à mão.")

# ============================================================================= formato pt-BR
TIER = {"early": "Início de jogo", "mid": "Meio de jogo", "late": "Fim de jogo"}
TIER_CURTO = {"early": "início", "mid": "meio", "late": "fim"}
# nomes dos recursos do jogo base em pt-BR (strings/pt-br.rules do jogo: Sulfur, Tristeel, Coil2...)
VANILLA_PT = {"sulfur": "Enxofre", "tristeel": "Triaço", "coil": "Bobina", "coil2": "Hiperbobina", "copper": "Cobre",
              "iron": "Ferro", "uranium": "Urânio", "steel": "Aço", "processor": "Processador",
              "diamond": "Diamante", "battery": "bateria"}


def num(x, casas=0):
    """72490 -> '72.490'; 1.875 com 1 casa -> '1,9'; zeros a direita somem (2.0 -> '2')."""
    if x is None:
        return "-"
    v = round(float(x), casas)
    if casas == 0 or v == int(v):
        return f"{int(round(v)):,}".replace(",", ".")
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",")


def razao(x):
    """Razao com 2 casas fixas: 0.8 -> '0,80'."""
    return f"{float(x):.2f}".replace(".", ",")


def lista(itens, conj="e"):
    itens = [str(i) for i in itens if i not in (None, "")]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + f" {conj} " + itens[-1]


def tam(s):
    return f"{s[0]}x{s[1]}"


def cel(v):
    return str(v).replace("|", "/")


def tabela(cab, linhas):
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for ln in linhas:
        out.append("| " + " | ".join(cel(c) for c in ln) + " |")
    return out


def plural(nome):
    """Plural da primeira palavra ('Prensa HE' -> 'Prensas HE', 'Tambor' -> 'Tambores')."""
    head, sep, rest = nome.partition(" ")
    if head.endswith("ão"):
        head = head[:-2] + "ões"
    elif head.endswith(("r", "z", "s")):
        head = head + "es"
    elif head.endswith("l"):
        head = head[:-1] + "is"
    else:
        head = head + "s"
    return head + sep + rest


def numeros_pt(texto):
    """'m(N) = 1 + 0.25 x N^0.85' -> '... 0,25 ... 0,85' (so numeros com ponto decimal)."""
    return re.sub(r"(\d)\.(\d)", r"\1,\2", texto)


def custo_pt(bc):
    return " + ".join(f"{q} {VANILLA_PT.get(r, r).lower()}" for r, q in bc)


def _fold(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def _parse(pat, texto, onde):
    m = re.search(pat, str(texto or ""))
    if not m:
        raise SystemExit(f"make_docs: nao achei {pat!r} em {onde} (o spec mudou?)")
    return m.group(1)


def _f(s):
    """'1,5' / '1.5' -> 1.5"""
    return float(str(s).replace(",", "."))


# ============================================================================= dados
def _short(pid):
    return pid.split(".", 1)[1]


GUN = {g["short"]: g for g in D.GUNS}
DEF = {g["short"]: g for g in D.DEFENSES}
PEM = {p["short"]: p for p in D.PEM}
FAC = {f["code"]: f for f in D.FACTORIES}
RES = {r["spec_key"]: r for r in D.RESOURCES}
RES_ID = {r["id"]: r for r in D.RESOURCES}
PAIOL = {p["short"]: p for p in D.PAIOL_PARTS}
LCH = {L["short"]: L for L in D.LAUNCHERS}
MSL = {m["file"]: m for m in D.MISSILES}
LIM = {L["category"]: L for L in D.LIMIT_DEFS}
NAME_BY_ID = {}
for _g in D.GUNS + D.DEFENSES + D.LAUNCHERS:
    NAME_BY_ID[_g["id"]] = _g["codename"] or _g["name_pt"]
for _p in D.PEM:
    NAME_BY_ID[_p["id"]] = _p["codename"]
for _f_ in D.FACTORIES:
    NAME_BY_ID[_f_["id"]] = _f_["name_pt"]
for _p in D.PAIOL_PARTS:
    NAME_BY_ID[_p["id"]] = _p["name_ptbr"]
for _k, _p in RAIL["parts"].items():
    NAME_BY_ID[_p["id"]] = _p["name_ptbr"]
NAME_BY_ID[D.FITA_PART["id"]] = D.FITA_PART["name_ptbr"]

MOD_PEM = C.content_module("bsgen.pem") is not None
MOD_RAIL = C.content_module("bsgen.railgun") is not None
TELEPORTE = D.transport() == "teleporte"
ADJ_ON = D.switch("econ.factory_adjacency") == "vanilla"
SCALING = RAIL["scaling_table"]
NROW = {r["canos"]: r for r in SCALING}
MAX_CANOS = max(NROW)
# banda do alvo do balanco ('band 1.10-1.25' em conventions.balance_target)
BANDA = tuple(float(x) for x in _parse(r"band ([\d.]+-[\d.]+)", D.SPEC["conventions"]["balance_target"],
                                       "conventions.balance_target").split("-"))
# nomes de pecas do SW:ACD como o jogo mostra (o spec usa nomes internos): SW strings/pt-br.rules
# SiegeTurbolaser12x12 (o 'Siege Turbolaser 12x12 [WarRoom]' do spec) e Imperialturbolaserswitchable
SW_NOMES = {"siege": "Dual 70TT Superheavy Turbolaser", "imperial": "Imperial Heavy Turbolaser"}


def nota_pem():
    if MOD_PEM:
        return []
    return [pendente("a linha PEM (bsgen.pem, WP08) ainda não está no gerador; números do spec 2.0"), ""]


def nota_rail():
    if not RAIL["enabled"]:
        return [pendente("rail.enabled = false neste build: o Tupã fica fora"), ""]
    if MOD_RAIL:
        return []
    return [pendente("o Tupã (bsgen.railgun, WP09) ainda não está no gerador; números do spec 2.0"), ""]


def gun_modes(g):
    return [m["key"] for m in g["modes"]]


def mode_label(k):
    return {"plasma": "Plasma"}.get(k, k.upper())


def units_per_s(g):
    return float(g["spec"]["internal_stock"]["units_per_s"])


def cal_mm(cal):
    m = re.match(r"\s*([\d,]+)\s*mm", str(cal or ""))
    return _f(m.group(1)) if m else None


def adj_factor():
    """Intervalo com vizinhanca ligada / intervalo do projeto (x1,5) e o bonus por vizinha (+25 %)."""
    r = FAC["F1"]["recipes"][0]
    base = r["interval_s_base"] / r["interval_s_spec"]
    fin = D.SPEC["switches"]["econ"]["factory_adjacency"]["final_intervals_s"]
    row = next(v for k, v in fin.items() if k.startswith("F1"))
    bonus = row[0] / row[1] - 1
    return base, bonus


def intervalo(r, vizinhas):
    """Segundos por ciclo com n vizinhas (vizinhanca ligada) ou o do projeto (desligada)."""
    if not ADJ_ON:
        return r["interval_s_base"]
    _b, bonus = adj_factor()
    return r["interval_s_base"] / (1 + bonus * vizinhas)


def oc_fab():
    oc = FAC["F1"]["oc"] or {}
    return float(str(oc.get("SPEED_FACTOR", "300%")).rstrip("%")) / 100


def res_pt(k):
    """Nome pt-BR de um insumo/recurso (do jogo base ou do Bullet Strike)."""
    if k in VANILLA_PT:
        return VANILLA_PT[k]
    r = RES.get(k) or RES_ID.get(k)
    return r["name_pt"] if r else k


def insumos(f, recipe=None):
    ks = []
    for r in f["recipes"]:
        if recipe and r["recipe"] != recipe:
            continue
        for k in r["inputs_per_cycle"]:
            if k not in ks:
                ks.append(k)
    return ks


def item_plural(nome):
    """'Célula de Plasma' -> 'Células de Plasma' (bs_strings.plural_pt)."""
    from bs_strings import plural_pt
    return plural_pt(nome)


def agrupa_itens(nomes):
    """['Carregador HE', 'Carregador AP', 'Célula de Plasma', 'Célula PEM'] ->
    'Carregadores HE e AP, Células de Plasma e PEM' (mesma primeira palavra = um grupo)."""
    grupos = []
    for nome in nomes:
        base = re.sub(r"\s*\([^)]*\)", "", nome).strip()
        head = base.split(" ")[0]
        g = next((x for x in grupos if x[0] == head), None)
        if g is None:
            grupos.append((head, [base]))
        else:
            g[1].append(base)
    out = []
    for head, nomes_g in grupos:
        if len(nomes_g) == 1:
            out.append(nomes_g[0])
            continue
        partes = [n.split(" ") for n in nomes_g]
        k = 0
        while all(len(p) > k + 1 for p in partes) and len({p[k] for p in partes}) == 1:
            k += 1
        prefixo = " ".join(partes[0][:k])
        restos = [" ".join(p[k:]) for p in partes]
        out.append(item_plural(prefixo) + " " + lista(restos))
    return lista(out)


# ============================================================================= fatos (numeros do checklist)
def fatos():
    F = {}
    v_fita, v_sem = D.VARIANTS["fita"], D.VARIANTS["semfita"]
    F["pasta_mod"] = v_fita["out"].strip("/").split("/")[-1]
    F["pasta_reserva"] = v_sem["out"].strip("/").split("/")[-1]
    F["nome_mod"], F["nome_reserva"] = v_fita["name"], v_sem["name"]
    F["versao"] = D.VERSION
    F["versao_jogo"] = _parse(r"(\d+\.\d+\.\d+\w*)", D.SPEC["game"], "SPEC.game")
    F["desc_prefixo"] = _parse(r"^(\[[^\]]+\])", v_fita["description_first_line_ptbr"], "build_2_0 descricao")
    # pecas
    n_rail = len(D.RAIL_PARTS) if RAIL["enabled"] else 0
    n_fita = 1 if TELEPORTE else 0
    pem_nomes = [PEM[s]["codename"] for s in ("bs_pem_light", "bs_pem_medium", "bs_pem_heavy")]
    F["n_pecas"] = num(len(D.GUNS) + len(D.DEFENSES) + len(D.PEM) + len(D.LAUNCHERS) + n_rail + len(D.FACTORIES)
                       + len(D.PAIOL_PARTS) + n_fita)
    partes = [f"{len(D.GUNS)} canhões", f"{len(D.DEFENSES)} defesas", f"{len(D.PEM)} PEM ({lista(pem_nomes)})",
              f"{len(D.LAUNCHERS)} lança-mísseis"]
    if n_rail:
        partes.append(f"{n_rail} peças do Tupã")
    partes += [f"{len(D.FACTORIES)} fábricas", f"{len(D.PAIOL_PARTS)} paióis"]
    if n_fita:
        partes.append("a Fita")
    F["lista_pecas"] = lista(partes)
    F["n_itens"] = num(len(D.RESOURCES))
    F["lista_itens"] = agrupa_itens([r["name_pt"] for r in D.RESOURCES])
    # fabricas e paiois
    F["paiol_cart_1x1"] = PAIOL["bs_paiol_cartuchos_1x1"]["name_ptbr"]
    f1, f2 = FAC["F1"], FAC["F2"]
    F["f1_nome"], F["f2_nome"] = f1["name_pt"], f2["name_pt"]
    F["f1_nome_plural"] = plural(f1["name_pt"])
    r1 = f1["recipes"][0]
    F["f1_sozinha_s"] = num(intervalo(r1, 0), 1)
    F["f1_2viz_s"] = num(intervalo(r1, 2), 2)
    F["f1_sozinha_min"] = num(60 * r1.get("units_per_cycle", 1) / intervalo(r1, 0))
    _b, bonus = adj_factor()
    F["viz_pct"] = num(bonus * 100)
    F["fab_oc_x"] = num(oc_fab(), 1)
    sec2 = []
    for code in ("F1", "F2", "F6"):
        if code in FAC:
            for k in insumos(FAC[code]):
                if k not in sec2:
                    sec2.append(k)
    F["insumos_secao2"] = lista(res_pt(k) for k in sec2)
    F["n_fabricas"] = num(len(D.FACTORIES))
    F["fabricas_lista"] = lista(f"{f['code']} {f['name_pt']} {tam(f['size'])}" for f in D.FACTORIES)
    ent = []
    for f in D.FACTORIES:
        por_receita = {r["recipe"]: insumos(f, r["recipe"]) for r in f["recipes"]}
        conjuntos = {tuple(v) for v in por_receita.values()}
        if len(conjuntos) == 1:
            ent.append(f"{f['code']} " + " + ".join(res_pt(k).lower() for k in insumos(f)))
        else:
            ps = [" + ".join(res_pt(k).lower() for k in v) + f" ({mode_label(rk) if rk != 'pem' else 'PEM'})"
                  for rk, v in por_receita.items()]
            ent.append(f"{f['code']} " + " e ".join(ps))
    F["fabricas_entradas"] = "; ".join(ent)
    modos = []
    for f in D.FACTORIES:
        sel = f.get("selector")
        if not sel:
            continue
        labels = [_recipe_label(r["recipe"]) for r in f["recipes"]]
        txt = f"{f['code']} ({'/'.join(labels)}"
        dflt = sel.get("Default")
        first = next((r for r in f["recipes"] if r.get("selector_mode") == dflt), None)
        if first is not None and dflt not in (0, None):
            txt += f", começa em {_recipe_label(first['recipe'])}"
        modos.append(txt + ")")
    F["fabricas_modos"] = lista(modos)
    F["n_paiois"] = num(len(D.PAIOL_PARTS))
    fams = []
    for p in D.PAIOL_PARTS:
        if p["family"] not in fams:
            fams.append(p["family"])
    F["paiol_familias"] = lista({"celulas": "células", "misseis": "mísseis", "projeteis": "projéteis"}.get(x, x)
                                for x in fams)
    niveis = []
    for p in D.PAIOL_PARTS:
        lv = p.get("roof_gauge_levels")
        if lv not in niveis:
            niveis.append(lv)
    F["paiol_niveis"] = " / ".join(num(x) for x in niveis)

    def cap(short, key):
        return next(k["MaxResources"] for k in PAIOL[short]["kinds"] if k["key"] == key)
    F["cap_he"] = lista(f"{num(cap(f'bs_paiol_cartuchos_{n}', 'he'))} no {n}" for n in ("1x1", "2x2", "3x3"))
    proj = [n for n in ("1x1", "2x2", "3x3") if f"bs_paiol_projeteis_{n}" in PAIOL]
    F["cap_proj"] = " / ".join(num(cap(f"bs_paiol_projeteis_{n}", "slug")) for n in proj) or "-"
    F["cap_proj_1x1"] = num(cap("bs_paiol_projeteis_1x1", "slug")) if proj else "-"
    F["paiol_proj_1x1"] = PAIOL["bs_paiol_projeteis_1x1"]["name_ptbr"] if proj else "-"
    # Tambor e companhia
    tb = GUN["bs_naval_76"]
    F["tambor"], F["tambor_nome"], F["tambor_plural"] = tb["codename"], tb["name_pt"], plural(tb["codename"])
    ups = units_per_s(tb)
    m0 = tb["modes"][0]
    F["tambor_he_min"] = num(ups * 60)
    F["tambor_meia_s"] = num((m0["storage"] - m0["resupply_threshold"]) / ups)
    F["tambor_vazio_s"] = num(m0["storage"] / ups)
    F["he_item"] = RES["he"]["name_pt"]
    F["he_itens"] = item_plural(RES["he"]["name_pt"])
    F["trovao"], F["mapinguari"] = GUN["bs_naval_155"]["codename"], GUN["bs_naval_406"]["codename"]
    F["furacao"], F["marimbondo"] = GUN["bs_rotary_30"]["codename"], GUN["bs_lmg"]["codename"]
    leves = [g for g in D.GUNS if "he" in gun_modes(g) and "ac" not in gun_modes(g)]
    F["leves_nomes"] = lista(g["codename"] for g in leves)
    grupos = {}
    for g in leves:
        grupos.setdefault("/".join(mode_label(k) for k in gun_modes(g)), []).append(g["codename"])
    F["leves_tipos"] = "; ".join(f"{lista(v)}: {k}" for k, v in grupos.items())
    navais = [g for g in D.GUNS if gun_modes(g) == ["he", "ap", "sap", "ac"]]
    F["navais"] = lista(f"{g['codename']} {g['spec']['caliber']}" for g in navais)
    bo = GUN["bs_nuke_howitzer"]
    F["boiuna"], F["boiuna_tam"], F["boiuna_alcance"] = bo["codename"], tam(bo["size"]), num(bo["spec"]["range_m"])
    m_bo = bo["modes"][0]
    F["boiuna_carreg_tiro"] = num(m_bo["units_per_shot"] / m_bo["shots_per_unit"], 2)
    fl = LIM["bs_limit_flagship"]
    F["flagship_nomes"] = lista(NAME_BY_ID[p] for p in fl["parts"])
    F["flagship_max"] = num(fl["max"])
    plasma = [g for g in D.GUNS if gun_modes(g) == ["plasma"]]
    F["plasma_nomes"] = lista(g["codename"] for g in plasma)
    F["plasma_item"] = item_plural(RES["plasma"]["name_pt"])
    F["pem_item"] = item_plural(RES["pem"]["name_pt"])
    # misseis
    F["lancadores_nomes"] = lista(L["codename"] for L in D.LAUNCHERS)
    lab = {c["index"]: c.get("label_ptbr") or c["name_ptbr"] for c in D.SPEC["toggles"]["bs_missile_type"]["choices"]}
    tl = []
    for L in D.LAUNCHERS:
        ls = [lab[m["index"]] for m in L["modes"]]
        tl.append(f"{L['codename']} só {ls[0]}" if len(ls) == 1 else f"{L['codename']} {' / '.join(ls)}")
    F["lancadores_tipos"] = "; ".join(tl)
    car_c, car_m = MSL["bs_msl_twin_cluster"], MSL["bs_msl_quad_cluster"]
    F["piranha_abre_caipora"] = num(car_c["carrier"]["proximity_range"])
    F["piranha_abre_mula"] = num(car_m["carrier"]["proximity_range"])
    F["piranha_minis_caipora"] = num(car_c["children"][0]["count"])
    F["piranha_minis_mula"] = num(car_m["children"][0]["count"])
    F["poraque_caipora"] = num(MSL["bs_msl_twin_emp"]["damage"]["shield_hp_per_missile"])
    F["poraque_mula"] = num(MSL["bs_msl_quad_emp"]["damage"]["shield_hp_per_missile"])
    F["iara_estagio_s"] = num(MSL["bs_msl_quad_nuclear"]["deploy_lifetime"], 1)
    F["mula_limite_mais_1"] = num(LIM["bs_limit_nuke"]["max"] + 1)
    # PEM
    tv, tt, co = PEM["bs_pem_light"], PEM["bs_pem_medium"], PEM["bs_pem_heavy"]
    F["tuvira"], F["treme"], F["pem_pesada"] = tv["codename"], tt["codename"], co["codename"]
    F["pem_pesada_oc"] = (co.get("overclock") or {}).get("name_ptbr") or "-"
    F["tuvira_tam"], F["tuvira_arco"] = tam(tv["size"]), num(tv["firing_arc_deg"])
    F["tuvira_canos"], F["tuvira_tiros_s"] = num(tv["barrels"]), num(tv["fire_rate_shots_per_s"], 1)
    ttb = D.SPEC["pem_weapons"]["time_to_break_s_no_refill"]
    chave_media = next(k for k in ttb[tv["codename"]] if k.startswith("SW medium"))
    F["bolha_media"] = num(int(_parse(r"(\d+)", chave_media, "time_to_break_s_no_refill")))
    F["ttb_tuvira"] = num(ttb[tv["codename"]][chave_media], 1)
    F["ttb_treme"] = num(ttb[tt["codename"]][chave_media], 1)
    F["ttb_pesada"] = num(ttb[co["codename"]][chave_media], 1)
    hs = D.SPEC["pem_weapons"]["heavy_overclock_shot"]["Hit"]["HitShield"]
    F["relampago_s"] = num(next(e["StatusDuration"] for e in hs if e.get("Type") == "StatusApplication"))
    # Tupa
    car = RAIL["parts"]["carregador"]
    F["rail_carregador"], F["rail_carregador_tam"] = car["name_ptbr"], tam(car["size"])
    F["rail_capsulas"] = num(car["storages"]["SlugMagazine"]["MaxResources"])
    F["rail_canos_demais"] = num(MAX_CANOS + 1)
    F["rail_max_canos"] = num(MAX_CANOS)
    for n in (1, 4, 6):
        r = NROW[n]
        F[f"rail_bonus_{n}"] = num(r["bonus_pct"])
        F[f"rail_cp_{n}"] = num(r["cp"])
        F[f"rail_energia_{n}"] = num(r["power_per_shot"])
        F[f"rail_alcance_{n}"] = num(r["range_m"])
    bat = car["storages"]["LoaderBattery"]["MaxResources"]
    F["rail_bateria"] = num(bat)
    F["rail_tiros_bateria_6"] = num(math.floor(bat / NROW[6]["power_per_shot"]))
    F["rail_tiros_bolha_grande_4"] = num(NROW[4]["sw_large_bubble_shots_no_refill"])
    F["rail_r2_min"] = num(int(_parse(r">=\s*(\d+)", RAIL["r2_fallback"]["acceptance"], "railgun.r2_fallback")))
    pen_op = RAIL["shot"]["Hit"]["PenetratingOperational"]["HitEffects"]
    F["rail_chiado_s"] = num(next(e["StatusDuration"] for e in pen_op if isinstance(e, dict)
                                  and e.get("StatusType") == "cosmoteer.disruptor_drain"))
    rl = LIM.get("bs_limit_railgun") or {"max": 0}
    F["rail_limite"], F["rail_limite_mais_1"] = num(rl["max"]), num(rl["max"] + 1)
    F["rail_vs_siege_4"] = num(NROW[4]["vs_sw_siege_per_shot"], 1)
    fire = RAIL["parts"]["ponta"]["weapon"]["FireInterval"]
    F["rail_intervalo"] = num(fire, 1)
    rec_b = RAIL.get("balance_recommendation_r2", {}).get("recommendation", {}).get("B", "")
    F["rail_intervalo_alt"] = num(_f(_parse(r"FireInterval\s*[\d.]+\s*->\s*([\d.]+)", rec_b,
                                           "railgun.balance_recommendation_r2.B")), 1)
    F["f6_nome"] = FAC["F6"]["name_pt"] if "F6" in FAC else "-"
    F["insumos_f6"] = lista(res_pt(k) for k in insumos(FAC["F6"])) if "F6" in FAC else "-"
    F["f6_sozinha_s"] = num(intervalo(FAC["F6"]["recipes"][0], 0), 1) if "F6" in FAC else "-"
    # defesas
    F["defesas_nomes"] = lista(g["codename"] for g in D.DEFENSES)
    F["tamandua"] = DEF["bs_ciws"]["codename"]
    lr = [g["spec"]["sw_anchor"]["vs_lasers"]["ratio"] for g in D.DEFENSES]
    F["antilaser_faixa"] = f"{razao(min(lr))}-{razao(max(lr))}"
    banda_txt = D.SPEC["switches"]["guns"]["defesa_antilaser"]["values"]["banda"]
    F["antilaser_banda"] = razao(_f(_parse(r"\(([\d,]+)\s*/", banda_txt, "guns.defesa_antilaser.banda")))
    pequenas = [cal_mm(g["spec"]["caliber"]) for g in D.GUNS if g["spec"]["shot"].get("targetable") is False]
    F["bala_pequena_mm"] = num(max(x for x in pequenas if x))
    # T3 e balanco
    F["t3_he_lim"] = num(_f(_parse(r"X <= ([\d,]+)", D.SPEC["switches"]["guns"]["he_further_factor"]["decided_by"],
                                   "guns.he_further_factor.decided_by")), 1)
    pred = BAL["ap_path_model"]["r4"]["t3_prediction"]
    F["t3_ap_lim"] = razao(next(p["limit"] for p in pred if p["class"] != "sap"))
    F["t3_sap_lim"] = razao(next(p["limit"] for p in pred if p["class"] == "sap"))
    F["alvo_pct"] = _parse(r"\+(\d+)%", D.SPEC["conventions"]["balance_target"], "conventions.balance_target")
    F["banda_min"], F["banda_max"] = razao(BANDA[0]), razao(BANDA[1])
    conv = D.SPEC["conventions"]
    F["dreno_k"] = numeros_pt(_parse(r"\+ ?([\d.]+) x ResourceDrain", conv["newweapons"]["shp"],
                                     "conventions.newweapons.shp"))
    F["dreno_bat"] = numeros_pt(_parse(r"\(([\d.]+) battery per shield HP", conv["missiles"]["shield_hp"],
                                       "conventions.missiles.shield_hp"))
    F["banda_alvo"] = f"{F['banda_min']}-{F['banda_max']}"
    # AP das metralhadoras (pen <= 8) no casco do SW: a AP para na durasteel (r4.t3_prediction, classe pen_le_8)
    F["ap_pen8_no_alvo"] = razao(max(p["after_max"] for p in pred if p["class"] == "pen_le_8"))
    # estoque interno das armas por nivel (mediana de spec.internal_stock.internal_storage_seconds)
    seg = {}
    for g in D.GUNS:
        seg.setdefault(g["spec"]["tier"], []).append(g["spec"]["internal_stock"]["internal_storage_seconds"])
    med = {t: num(sorted(v)[len(v) // 2]) for t, v in seg.items()}
    if med.get("early") == med.get("mid"):
        F["estoque_armas"] = f"~{med['early']} s de tiro (~{med['late']} s no fim de jogo)"
    else:
        F["estoque_armas"] = (f"~{med['early']} s de tiro no início de jogo, ~{med['mid']} s no meio e "
                              f"~{med['late']} s no fim")
    # nomes do SW como aparecem no jogo (SW strings/pt-br.rules: SiegeTurbolaser12x12, Imperialturbolaserswitchable)
    F["sw_siege"], F["sw_imperial"] = SW_NOMES["siege"], SW_NOMES["imperial"]
    sg = [r["sw_anchor"] for r in BAL["vs_sw_table"] if r["group"] == "railgun"]
    F["sw_siege_tiro"] = num(int(_parse(r"(\d+) por tiro", sg[0] if sg else "", "balance.vs_sw_table railgun")))
    # ions do SW: so drenam bateria; entre as armas do Bullet Strike so o carregador do Tupa tem bateria
    F["tupa"] = RAIL["name"].split(" (")[0].strip()
    F["ions_excecao"] = (f" (menos o {F['tupa']}, que gasta a bateria do carregador)" if RAIL["enabled"] else "")
    alc = D.SPEC["switches"]["logistics"]["fita_alcance"]
    F["fita_alcance_alt"] = num(min(int(k) for k in alc["values"]))
    # secoes com itens (com SW)
    F["secoes_com_sw"] = lista(str(s["n"]) for s in CHK["sections"]
                               if any(i.get("com_sw") for i in s["itens"]))
    return F


def _recipe_label(k):
    lab = {"ap": "AP", "sap": "SAP", "ac": "AC", "frag": "FRAG", "he": "HE", "plasma": "Plasma", "pem": "PEM",
           "msl_he": "HE", "msl_cluster": "Submunição", "msl_emp": "PEM", "msl_nuke": "Ogiva", "slug": "Projétil"}
    return lab.get(k, k)


FATOS = fatos()


def preenche(texto, onde):
    def sub(m):
        k = m.group(1)
        if k not in FATOS:
            raise SystemExit(f"make_docs: chave {{{k}}} desconhecida em {onde}")
        return str(FATOS[k])
    return re.sub(r"\{([a-z0-9_]+)\}", sub, texto)


# ============================================================================= textos comuns
def aviso_sw():
    return D.SPEC["vanilla_profile"]["sw_only_warning_ptbr"]


def aviso_ruptura():
    return D.SPEC["removed_ids"]["clean_break_texts"]["readme_and_mod_description_ptbr"]


def descr_teste():
    return D.VARIANTS["fita"]["description_first_line_ptbr"]


# ============================================================================= ARMAS.md
def armas_md():
    L = ["# Bullet Strike 2.0: armas, munições, fábricas e logística", "", GERADO, "",
         f"> **{FATOS['desc_prefixo']}** Números do build de teste (versão {D.VERSION}). A versão final só sai "
         "depois do [checklist](CHECKLIST_2_0.md).", ">",
         f"> **Balanço:** {aviso_sw()}", ""]
    if PENDENTES:
        L += [f"> {p}" for p in [pendente(x) for x in list(PENDENTES)]] + [""]
    he_f = D.switch("guns.he_further_factor")
    L += ["**Convenções.** DPS no casco = tiros por segundo x (dano direto + metade da explosão). Escudo por segundo = "
          f"dano no escudo + {FATOS['dreno_k']} x o dreno de bateria (o escudo do SW gasta {FATOS['dreno_bat']} de "
          "bateria por ponto). Sem overclock, "
          "salvo quando dito. \"Por tile\" = dividido pelos quadrados da peça. Custos em créditos.", "",
          "## Índice", "",
          "- [Canhões](#canhões)", "- [Munições](#munições)", "- [Defesas](#defesas)", "- [Linha PEM](#linha-pem)",
          "- [Railgun Tupã](#railgun-tupã)", "- [Lança-mísseis](#lança-mísseis)", "- [Fábricas](#fábricas)",
          "- [Paióis](#paióis)", "- [Fita de Alimentação](#fita-de-alimentação)",
          "- [Limites por nave](#limites-por-nave)",
          "- [Techs da Carreira](#techs-da-carreira)", "- [Balanço contra o SW:ACD](#balanço-contra-o-swacd)",
          "- [Logística por tipo de munição](#logística-por-tipo-de-munição)",
          "- [Efeitos visuais](#efeitos-visuais)", ""]
    # ------------------------------------------------------------------ canhoes
    L += ["## Canhões", "",
          "Só precisam de tripulação e munição: nenhum usa energia. Cada tipo de munição tem o seu estoque dentro da "
          "arma; trocar o tipo nunca joga fora o que já está lá. A tripulação reabastece a arma quando ela cai abaixo "
          "da metade (com a Fita, os paióis abastecem antes).", ""]
    cab = ["Codinome", "Arma", "Calibre", "Tamanho", "Tripulação", "Comando", "Vida", "Custo", "Alcance",
           "DPS HE (casco)", "Munições", "Overclock"]
    for tier in ("early", "mid", "late"):
        rows = []
        for g in D.GUNS:
            if g["tier"] != tier:
                continue
            w = g["spec"]
            dps = w["dps"].get("hull_he") or w["ammo_modes"][0]["hull_dps"]
            rows.append([f"**{g['codename']}**", g["name_pt"], w["caliber"], tam(g["size"]), g["crew"], g["cp"],
                         num(g["hp"]), num(w["build_cost_credits"]), f"{num(w['range_m'])} m", num(dps),
                         "/".join(mode_label(k) for k in gun_modes(g)), (g.get("oc") or {}).get("name_pt") or "-"])
        if rows:
            L += [f"### {TIER[tier]}", ""] + tabela(cab, rows) + [""]
    stun = [g["codename"] for g in D.GUNS if g["spec"].get("crew_stun")]
    spin = [g["codename"] for g in D.GUNS if g["spec"].get("spinup")]
    hyb = [g["codename"] for g in D.GUNS if g.get("hybrid")]
    L += [f"- **Aceleram enquanto atiram:** {lista(spin)} (começam devagar e chegam à cadência máxima em alguns "
          "segundos).",
          f"- **Atordoam a tripulação perto da torre ao disparar:** {lista(stun)} (mais forte com overclock).",
          f"- **Híbrida:** {lista(hyb)} também derruba mísseis, minas e projéteis no modo Defender.",
          f"- **{GUN['bs_nuke_howitzer']['codename']}:** obuseiro pesado; a AC dele é guiada "
          f"({'ligada' if D.switch('boiuna.ac_guided') else 'desligada'} neste build) e cada disparo gasta "
          f"{FATOS['boiuna_carreg_tiro']} carregador.",
          f"- **{LIM['bs_limit_flagship']['nouns_ptbr'][1]}:** {FATOS['flagship_nomes']} somados, no máximo "
          f"{FATOS['flagship_max']} por nave.", ""]
    # ------------------------------------------------------------------ municoes
    L += ["## Munições", ""]
    for a in D.SPEC["ammo_types"]:
        L.append(f"- **{a['label']} ({a['name_ptbr']})** - {a['resource_name_ptbr']}: {a['desc_ptbr']}")
    L += ["", f"\"Peça seguinte\" = dano em cada peça que a granada atravessa depois da primeira. HE e AC: "
          f"{num(float(he_f) * 100) if not isinstance(he_f, str) else he_f} % do dano direto (como os turbolasers do "
          f"SW). AP e SAP: fator do switch `guns.ap_further_factor` = {D.switch('guns.ap_further_factor')}.", ""]
    rows = []
    for g in D.GUNS:
        for m in g["modes"]:
            s2 = m["spec2"]
            per = m["shots_per_unit"] / m["units_per_shot"]
            disp = (f"{num(per, 2)} disparo{'s' if per != 1 else ''}" if per >= 1 else
                    f"{num(1 / per, 2)} carregador por disparo")
            exp = (f"{num(s2.get('explosive'))} ({num(s2.get('explosive_radius_m'), 2)} m)"
                   if s2.get("explosive") else "-")
            rows.append([g["codename"], mode_label(m["key"]), num(s2.get("direct")), exp, num(s2.get("penetration"), 1),
                         num(s2.get("pen_damage_per_further_part")) if s2.get("pen_damage_per_further_part") else "-",
                         num(s2.get("hull_dps")), num(s2.get("shield_dps")), disp,
                         f"{num(m['storage'])} ({num(g['spec']['internal_stock']['internal_storage_seconds'])} s)"])
    L += tabela(["Arma", "Tipo", "Dano direto", "Explosão (raio)", "Penetração", "Peça seguinte", "Casco/s",
                 "Escudo/s", "Por unidade", "Estoque (tempo de tiro)"], rows) + [""]
    # ------------------------------------------------------------------ defesas
    L += ["## Defesas", "",
          f"{lista(g['codename'] for g in D.DEFENSES)} só defendem: não atacam naves. Cada rajada leva duas cargas "
          "separadas: uma contra mísseis, minas e projéteis e outra, só contra os disparos laser e os tiros iônicos "
          "(os turbolasers e íons do SW:ACD). A munição FRAG (Nuvem de Fragmentos) estoura uma carga menor e solta "
          "fragmentos que varrem o caminho dos mísseis; contra lasers ela vale o mesmo que a HE.", ""]
    rows = []
    for g in D.DEFENSES:
        w = g["spec"]
        he = next(m for m in w["ammo_modes"] if m["key"] == "he")
        fr = next((m for m in w["ammo_modes"] if m["key"] == "frag"), None)
        bs, bl = he["blast_vs_shots"], he["blast_vs_lasers"]
        frag_txt = "-"
        if fr:
            fb, ff = fr["blast_vs_shots"], fr["fragments"]
            frag_txt = (f"{num(fb['total_damage'])} ({num(fb['radius_m'], 1)} m) + {ff['count']} x "
                        f"{num(ff['damage_each_vs_bullets'])}")
        rate = w.get("fire_rate_airbursts_per_s")
        rows.append([f"**{g['codename']}**", g["name_pt"], tam(g["size"]), g["crew"], f"{num(w['range_m'])} m",
                     num(rate, 2), f"{num(bs['total_damage'])} ({num(bs['radius_m'], 1)} m)", frag_txt,
                     f"{num(bl['total_damage'])} ({num(bl['radius_m'], 1)} m)",
                     f"{num(he['anti_shot_pool_per_s'])} / {num(he['anti_laser_pool_per_s'])}",
                     (g.get("oc") or {}).get("name_pt") or "-"])
    L += tabela(["Codinome", "Defesa", "Tamanho", "Tripulação", "Alcance", "Rajadas/s", "HE: contra mísseis e "
                 "projéteis", "FRAG: central + fragmentos", "Contra lasers e íons", "Por segundo (anti-tiro / "
                 "anti-laser)", "Overclock"], rows) + [""]
    shots = [f"{g['codename']} {razao(g['spec']['sw_anchor']['ratio'])}x" for g in D.DEFENSES]
    lasers = [f"{g['codename']} {razao(g['spec']['sw_anchor']['vs_lasers']['ratio'])}x" for g in D.DEFENSES]
    L += [f"**Contra o SW:ACD.** Contra mísseis, minas e balas: {lista(shots)} a defesa equivalente do SW. Contra os "
          f"lasers e íons do SW: {lista(lasers)} (decisão da Fase B; `guns.defesa_antilaser` = "
          f"{D.switch('guns.defesa_antilaser')}; a opção `banda` leva a {FATOS['antilaser_banda']}x). As balas de até "
          f"{FATOS['bala_pequena_mm']} mm não podem ser derrubadas por defesas (como o canhão de repetição do jogo "
          "base).", ""]
    # ------------------------------------------------------------------ PEM
    tv, tt, co = PEM["bs_pem_light"], PEM["bs_pem_medium"], PEM["bs_pem_heavy"]
    L += ["## Linha PEM", ""] + nota_pem()
    rr = [p["computed"]["vs_sw"]["shp_per_s"] for p in (tt, co)]
    L += ["Canhões que disparam granadas PEM e drenam a bateria do escudo atingido, com pouco dano no casco. São o "
          f"par dos canhões de íons do SW:ACD ({tt['codename']} e {co['codename']}: "
          f"{razao(min(rr))}-{razao(max(rr))}x os íons do SW). O overclock do escudo não corta esse dreno pela "
          f"metade. Usam uma munição só, a {RES['pem']['name_pt']}, feita na F3 só com cobre.", ""]
    rows = []
    for p in (tv, tt, co):
        c = p["computed"]
        mont = f"torre {num(p['firing_arc_deg'])}°"
        if p.get("rotate_speed_deg_s"):
            mont += f" ({num(p['rotate_speed_deg_s'])}°/s)"
        if (p.get("barrels") or 1) > 1:
            mont += f", {p['barrels']} canos"
        st = p["internal_storage"]
        rows.append([f"**{p['codename']}**", p["name_pt"], tam(p["size"]), mont, p["crew"], p["command_points"],
                     f"{num(p['range_m'])} m", num(c["shots_per_s"], 2), num(c["shp_per_hit"]), num(c["shp_per_s"]),
                     num(c["shp_per_s_per_cp"]), num(c["hull_dps"]), num(c["cells_per_s"], 2),
                     f"{num(st['MaxResources'])} células ({num(c['internal_stock_s'])} s)",
                     (p.get("overclock") or {}).get("name_ptbr") or "-"])
    L += tabela(["Codinome", "Arma", "Tamanho", "Montagem", "Tripulação", "Comando", "Alcance", "Tiros/s",
                 "Escudo por acerto", "Escudo/s", "Escudo/s por comando", "Casco/s", "Células/s", "Estoque",
                 "Overclock"], rows) + [""]
    L += [f"**Escada.** Por arma: {tv['codename']} {num(tv['computed']['shp_per_s'])} < {tt['codename']} "
          f"{num(tt['computed']['shp_per_s'])} < {co['codename']} {num(co['computed']['shp_per_s'])} de escudo por "
          f"segundo. Por ponto de comando: {tv['codename']} {num(tv['computed']['shp_per_s_per_cp'])}, "
          f"{tt['codename']} {num(tt['computed']['shp_per_s_per_cp'])}, {co['codename']} "
          f"{num(co['computed']['shp_per_s_per_cp'])} (`pem.tuvira_cp` = {D.switch('pem.tuvira_cp')}).", ""]
    oc = D.SPEC["pem_weapons"]["heavy_overclock_shot"]
    ph = oc["per_hit_shield_hp"]
    L += [f"**{co['codename']} com overclock ({(co.get('overclock') or {}).get('name_ptbr')}).** O tiro atravessa "
          f"peças com energia e drena por {FATOS['relampago_s']} s: {num(ph['instant'])} de escudo na hora + "
          f"{num(ph['lingering_over_10s'])} ao longo do tempo ({num(ph['total'])} por acerto), alcance "
          f"{num(oc['Range'])} m.", ""]
    ttb = D.SPEC["pem_weapons"]["time_to_break_s_no_refill"]
    keys = list(ttb[tv["codename"]].keys())
    rows = [[p["codename"]] + [num(ttb[p["codename"]][k], 1) + " s" for k in keys] for p in (tv, tt, co)]
    L += ["Tempo para derrubar uma bolha de escudo cheia, sem recarga:", ""]
    L += tabela(["Arma"] + [k.replace("small", "pequena").replace("medium", "média").replace("large", "grande")
                            .replace("vanilla", "jogo base") for k in keys], rows) + [""]
    L += ["Contra os íons do SW:", ""]
    rows = []
    for p in (tv, tt, co):
        vs = p["computed"].get("vs_sw") or p.get("vs_sw") or {}
        rows.append([p["codename"], ancora(vs.get("anchor")), f"{razao(vs.get('shp_per_s', 0))}x",
                     f"{razao(vs.get('per_cp', 0))}x", "sim" if vs.get("in_band_1_10_1_25") else "não (escolha)"])
    L += tabela(["Arma", "Âncora do SW", "Escudo/s", "Por comando", f"Na banda {FATOS['banda_alvo']}"], rows)
    L += ["", f"A {tv['codename']} virou torre de {num(tv['firing_arc_deg'])}° a pedido: o arco paga a cadência, e "
          "ela fica abaixo da âncora fixa do SW por arma.", ""]
    # ------------------------------------------------------------------ Tupa
    L += rail_section()
    # ------------------------------------------------------------------ lancadores
    L += ["## Lança-mísseis", "", "Projeto completo em [MISSEIS_PROJETO.md](MISSEIS_PROJETO.md).", ""]
    rows = []
    lab = {c["index"]: c.get("label_ptbr") for c in D.SPEC["toggles"]["bs_missile_type"]["choices"]}
    for Lc in D.LAUNCHERS:
        lim = next((f"{x['max']} por nave" for x in D.LIMIT_DEFS if Lc["id"] in x["parts"]), "-")
        rng = max(m["range"] for m in D.MISSILES if m["launcher"] == Lc["id"])
        rows.append([f"**{Lc['codename']}**", Lc["name_pt"], TIER_CURTO[Lc["tier"]], tam(Lc["size"]), Lc["crew"],
                     Lc["cp"], num(Lc["hp"]), num(Lc["cost"] if isinstance(Lc["cost"], (int, float)) else
                                                 D.MSPEC["launchers"][D.LAUNCHERS.index(Lc)]["build_cost_credits"]),
                     " / ".join(lab[m["index"]] for m in Lc["modes"]), f"{num(rng)} m",
                     (Lc.get("oc") or {}).get("name_pt") or "-", lim])
    L += tabela(["Codinome", "Lançador", "Fase", "Tamanho", "Tripulação", "Comando", "Vida", "Custo", "Tipos",
                 "Alcance", "Overclock", "Limite"], rows) + [""]
    dens = [r for r in BAL["vs_sw_table"] if r["group"] == "missil" and r.get("metric")]
    trip = _parse(r"([\d,]+-[\d,]+x)", dens[0].get("note_tripulacao", ""), "vs_sw_table missil note_tripulacao")
    rr = [r["ratio_hull"] for r in dens]
    L += [f"**Contra o SW.** Os lançadores do SW pagam em peças de míssil e tripulação carregando, então a conta é a "
          f"densidade do sistema (lançador + fábrica + tripulação, por tile): {razao(min(rr))}-{razao(max(rr))}x o "
          f"lançador do SW com a Fita ou o paiol acoplado; só com a tripulação, sem acoplamento: {trip}.", ""]
    # ------------------------------------------------------------------ fabricas
    L += fabricas_section()
    L += paiol_section()
    L += fita_section()
    L += limites_section()
    L += techs_section()
    L += balanco_section()
    L += logistica_section()
    L += visual_section()
    return "\n".join(L)


def rail_section():
    car, cano, ponta = RAIL["parts"]["carregador"], RAIL["parts"]["cano"], RAIL["parts"]["ponta"]
    L = ["## Railgun Tupã", ""] + nota_rail()
    cp_fixo = car["command_points"] + ponta["command_points"]
    st = car["storages"]
    imp = RAIL["tranco"]["impulse"]["by_N"]
    shake = RAIL["tranco"]["shake"]["rules"]
    sk_a = _parse(r"ShakeAmount\s*=\s*([\d.]+)", shake, "railgun.tranco.shake")
    sk_d = _parse(r"Duration\s*=\s*([\d.]+)", shake, "railgun.tranco.shake")
    L += ["Fixa e modular, como o canhão eletromagnético (railgun) do jogo base: "
          f"**{car['name_ptbr']}** {tam(car['size'])} + 1 a {MAX_CANOS} **{plural(cano['name_ptbr'])}** "
          f"{tam(cano['size'])} + **{ponta['name_ptbr']}** {tam(ponta['size'])}. Os canos "
          f"encaixam no meio da borda de cima do carregador e a Ponta no último cano; com 0 ou mais de {MAX_CANOS} "
          "canos a Ponta não atira.", "",
          f"- **Mais canos = mais dano, alcance, penetração, velocidade e energia por tiro:** "
          f"{numeros_pt(RAIL['scaling_formula'])}.",
          f"- **Comando:** {cp_fixo} + {cano['command_points']} por cano. Tripulação: {car['crew']} no carregador.",
          f"- **Energia:** sai da bateria do carregador ({num(st['LoaderBattery']['MaxResources'])}): "
          f"{num(NROW[1]['power_per_shot'])} por tiro com 1 cano até {num(NROW[MAX_CANOS]['power_per_shot'])} com "
          f"{MAX_CANOS}. A tripulação leva bateria ao carregador.",
          f"- **Ritmo:** 1 tiro a cada {num(ponta['weapon']['FireInterval'], 1)} s. Estoque: "
          f"{num(st['SlugMagazine']['MaxResources'])} projéteis no carregador + 1 na câmara = "
          f"{num(RAIL['internal_stock']['slugs'])} tiros ({num(RAIL['internal_stock']['seconds'])} s).",
          f"- **Tranco:** um impulso por tiro na ponta ({num(imp[str(1)])} com 1 cano até "
          f"{num(imp[str(MAX_CANOS)])} com {MAX_CANOS}), tremor de tela {numeros_pt(sk_a)} por {numeros_pt(sk_d)} s, "
          "anel de choque azul e recuo animado da ponta, dos canos e da culatra. Fora do centro da nave ela gira um "
          "pouco, como o canhão eletromagnético do jogo base.",
          "- **Passa por cima da própria nave:** o dardo não acerta peças nossas.",
          f"- **Limite:** {num((LIM.get('bs_limit_railgun') or {}).get('max', 0))} por nave (a Ponta conta), à parte "
          "do limite do Mapinguari e da Boiúna.",
          "- **Visual:** tudo azul elétrico (carregador, canos, dardo, rastro, impacto); só as brasas que ficam "
          "queimando no alvo são laranja.", ""]
    rows = []
    bat = st["LoaderBattery"]["MaxResources"]
    for n in sorted(NROW):
        r = NROW[n]
        rows.append([n, r["tiles"], r["cp"], num(r["build_cost_credits"]), num(r["pool_per_shot"]), num(r["dps"]),
                     num(r["dps_per_tile"]), num(r["penetration"], 1), f"{num(r['range_m'])} m",
                     f"{num(r['speed_mps'])} m/s", num(r["power_per_shot"]), num(math.floor(bat / r["power_per_shot"])),
                     num(r["impulse_per_shot"]), razao(r["f6_tiles_per_1000_dps_at_3_0s"])])
    L += tabela(["Canos", "Tiles", "Comando", "Custo", "Dano por tiro", "DPS", "DPS por tile", "Penetração", "Alcance",
                 "Velocidade", "Energia por tiro", "Tiros com a bateria cheia", "Impulso do tranco",
                 "F6 por 1000 DPS"], rows) + [""]
    band = next(r["band"] for r in D.SPEC["logistics_table"] if r["tier"] == "late")
    bmax = _f(band.split("-")[1])
    acima = [n for n in sorted(NROW) if NROW[n]["f6_tiles_per_1000_dps_at_3_0s"] > bmax]
    if acima:
        L += [f"Com {lista([str(n) for n in acima], 'ou')} cano{'s' if len(acima) > 1 or acima[0] > 1 else ''} "
              "a logística "
              f"({' / '.join(razao(NROW[n]['f6_tiles_per_1000_dps_at_3_0s']) for n in acima)} tile de F6 por 1000 "
              f"DPS) fica acima da banda do fim ({numeros_pt(band.replace('-', ' a '))}); de {max(acima) + 1} canos em "
              "diante fica dentro.", ""]
    L += [f"**Contra o SW.** Por tiro: {razao(NROW[1]['vs_sw_siege_per_shot'])}x (1 cano) a "
          f"{razao(NROW[MAX_CANOS]['vs_sw_siege_per_shot'])}x ({MAX_CANOS}) o {FATOS['sw_siege']} do SW. Por tile: "
          f"{razao(NROW[1]['vs_sw_late_line_353_per_tile'])} a "
          f"{razao(NROW[MAX_CANOS]['vs_sw_late_line_353_per_tile'])}x"
          f" a linha tardia do SW: o carregador {tam(car['size'])} é o preço. Se ficar fraco, dá para atirar a cada "
          f"{FATOS['rail_intervalo_alt']} s em vez de {FATOS['rail_intervalo']} s (checklist 10.4).", ""]
    return L


def fabricas_section():
    base, bonus = adj_factor()
    L = ["## Fábricas", "",
         f"Etapa única, sem tripulante (a tripulação só leva a matéria-prima e a energia), com overclock "
         f"({num(oc_fab(), 1)}x mais rápido, esquentando)."]
    if ADJ_ON:
        L += ["", f"**Vizinhança ligada, como no jogo base:** +{num(bonus * 100)} % por fábrica vizinha (do Bullet "
              f"Strike ou do jogo base). Os intervalos do Bullet Strike foram multiplicados por {num(base, 2)}: "
              "sozinha a fábrica é mais lenta, e com 2 vizinhas ela volta ao ritmo do projeto."]
    L += [""]
    rows = []
    for f in D.FACTORIES:
        for r in f["recipes"]:
            ins = " + ".join(f"{num(v['raw_units'], 3)} {res_pt(k).lower()}" for k, v in r["inputs_per_cycle"].items())
            upc = r.get("units_per_cycle", 1)
            out = res_pt(r["output_resource"])
            ritmo = " / ".join(f"{num(intervalo(r, n), 2)} s" for n in ((0, 1, 2) if ADJ_ON else (0,)))
            rows.append([f["code"], f["name_pt"], tam(f["size"]), ins,
                         (f"{upc} x " if upc > 1 else "") + out, ritmo,
                         f"{num(intervalo(r, 0) / oc_fab(), 2)} s", num(r.get("battery_mb_per_cycle"))])
    cab_r = "Ritmo: sozinha / 1 vizinha / 2 vizinhas" if ADJ_ON else "Ritmo"
    L += tabela(["Código", "Fábrica", "Tamanho", "Entra por ciclo", "Sai por ciclo", cab_r, "Com overclock (sozinha)",
                 "Bateria por ciclo"], rows) + [""]
    sel = [f for f in D.FACTORIES if f.get("selector")]
    L += [f"Modos (botão da fábrica): {FATOS['fabricas_modos']}. A placa do teto mostra o modo; a F3 em PEM acende o "
          f"banco PEM só produzindo. Entradas: {FATOS['fabricas_entradas']}.", ""]
    if not sel:
        aviso("nenhuma fabrica com seletor")
    return L


def paiol_section():
    L = ["## Paióis", "",
         "Quatro famílias, de 1x1 a 3x3. O tipo é escolhido no botão do paiol; cada tipo tem o seu estoque (trocar o "
         "tipo não apaga nada, e o paiol continua empurrando o que já tinha para as armas daquele tipo). Barra sob a "
         f"vida + medidor no teto ({FATOS['paiol_niveis']} níveis) + placa do tipo; "
         + ("com contador de números." if D.switch("logistics.paiol_contador") else "sem contador de números nesta "
            "versão.")
         + " Cheio, explode; vazio, quase não.", ""]
    if TELEPORTE:
        L += ["No build com a Fita os paióis são selados (sem porta): só a Fita põe e tira munição. Na reserva sem "
              "Fita eles têm portas, a tripulação entra e um paiol encostado atrás da arma (ou embaixo da saída da "
              "fábrica) passa a munição sozinho.", ""]
    rows = []
    for p in D.PAIOL_PARTS:
        caps = ", ".join(f"{_kind_label(k['key'])} {num(k['MaxResources'])}" for k in p["kinds"])
        push = (p.get("teleporte") or {}).get("push_units_per_s_per_kind")
        rows.append([p["name_ptbr"], tam(p["size"]), num(p["max_health"]), caps,
                     f"{num(push)}/s" if push else "-", custo_pt(p["build_cost"])])
    L += tabela(["Paiol", "Tamanho", "Vida", "Capacidade por tipo", "Empurra por tipo", "Custo"], rows) + [""]
    return L


def _kind_label(k):
    return {"he": "HE", "ap": "AP", "sap": "SAP", "ac": "AC", "frag": "FRAG", "plasma": "Plasma", "pem": "PEM",
            "msl_he": "HE", "msl_cluster": "Submunição", "msl_emp": "PEM", "msl_nuke": "Ogiva", "slug": "Projétil"}[k]


def fita_section():
    fp = D.FITA_PART
    alc = int(D.switch("logistics.fita_alcance"))
    L = ["## Fita de Alimentação", ""]
    if not TELEPORTE:
        return L + ["Não existe neste build (transporte pela tripulação).", ""]
    jeito = D.switch("logistics.fita_fabrica")
    L += [fp["description_ptbr"], "",
          f"- **Peça:** {tam(fp['size'])}, vida {num(fp['max_health'])}, custo {custo_pt(fp['build_cost'])}. "
          "Grude de lado "
          "(não na quina) na máquina; uma Fita encostada em duas máquinas liga as duas.",
          f"- **Fábrica → paiol (jeito {jeito}):** a fábrica com Fita manda cada unidade pronta para os paióis com "
          "Fita "
          "que aceitam aquele tipo, em qualquer lugar da nave. Sem paiol com Fita ela não manda nada e a grade de "
          "saída fica para a tripulação, como no jogo base.",
          f"- **Paiol → arma ({D.switch('logistics.fita_arma')}):** o paiol com Fita empurra cada tipo que guarda para "
          "as armas com Fita naquele tipo (a vazão por tipo está na coluna \"Empurra por tipo\" dos paióis).",
          "- **Um tipo nunca vira outro:** o paiol de HE só recebe HE e a arma só recebe o tipo escolhido no botão.",
          f"- **Reserva da tripulação ({D.switch('logistics.reserva_tripulacao')}):** a tripulação continua levando "
          "munição para a arma que cair abaixo da metade (de uma Baia ou de munição comprada).",
          f"- **Alcance:** {'a nave inteira' if alc >= 1000 else f'{alc} quadrados'} (`logistics.fita_alcance` = "
          f"{alc}); se o jogo ficar lento, dá para trocar para ~{FATOS['fita_alcance_alt']} quadrados.",
          "- **O que se vê:** a luz verde da Fita grudada, o ícone da Fita na máquina ligada, a barra do paiol e "
          "cartuchos saindo de uma peça e entrando na outra.",
          "- **Não atravessa para outra nave:** se a nave se partir, cada pedaço fica com os seus paióis.", ""]
    return L


def limites_section():
    L = ["## Limites por nave", ""]
    for x in D.LIMIT_DEFS:
        nomes = lista(NAME_BY_ID.get(p, p) for p in x["parts"])
        extra = " somados" if len(x["parts"]) > 1 else ""
        L.append(f"- **{x['nouns_ptbr'][1]}** ({nomes}{extra}): no máximo {x['max']} por nave.")
    return L + [""]


def _unlock_pt(u):
    if u.startswith("ammo:"):
        return f"munição {u.split(':', 1)[1].upper()}"
    if u.startswith("cell:"):
        return f"célula {u.split(':', 1)[1].upper()}"
    if u.startswith("missile:"):
        k = u.split(":", 1)[1]
        c = next(c for c in D.SPEC["toggles"]["bs_missile_type"]["choices"] if c["choice_id"].endswith(k))
        return f"míssil {c['codename']}"
    if u.startswith("overclock:"):
        return f"overclock: {NAME_BY_ID.get(u.split(':', 1)[1], u)}"
    return NAME_BY_ID.get(u, u)


def techs_section():
    L = ["## Techs da Carreira", "",
         "Pré-requisitos do jogo base aparecem pelo ID (`cosmoteer.*`). No modo Construir e Batalhar as peças vêm "
         "liberadas pela lista branca do mod.", ""]
    written = set(NAME_BY_ID)
    rows = []
    for t in D.SPEC["career_techs"]:
        if t.get("enabled") is False:
            continue
        unl = [u for u in t["unlocks"] if not u.startswith("rafaeltessaro.") or u in written]
        if not unl:
            continue
        pre = [_tech_nome(p) if p.startswith("rafaeltessaro.") else f"`{p}`" for p in t["prerequisites"]]
        rows.append([_tech_nome(t["id"]), t.get("tier", "-"), num(t["cost_credits"]), lista(pre) or "-",
                     lista(_unlock_pt(u) for u in unl)])
    L += tabela(["Tech", "Nível", "Custo", "Pré-requisitos", "Libera"], rows) + [""]
    return L


_TECH_NOMES = {}


def _tech_nome(tid):
    """Nome da tech como o jogo mostra (D.career_techs: NameKey da peca ou chave BSTechs), com codinome nas armas."""
    if not _TECH_NOMES:
        from bs_strings import tech_strings
        pt = tech_strings(D)[1]
        for t in D.career_techs(None):
            nk = t["NameKey"]
            m = re.match(r"&<\.\./parts/([^/]+)/", nk)
            if t["ID"].endswith("-overclock"):
                base = t["ID"][:-len("-overclock")]
                if base not in NAME_BY_ID:
                    base = next((u.split(":", 1)[1] for x in D.SPEC["career_techs"] if x["id"] == t["ID"]
                                 for u in x["unlocks"] if u.startswith("overclock:")), base)
                _TECH_NOMES[t["ID"]] = f"Overclock: {NAME_BY_ID.get(base, base)}"
            elif m:
                _TECH_NOMES[t["ID"]] = NAME_BY_ID.get(f"{D.AUTHOR}.{m.group(1)}", m.group(1))
            else:
                _TECH_NOMES[t["ID"]] = pt.get(nk.split("/", 1)[-1], nk)
    return _TECH_NOMES.get(tid, f"`{tid}`")


def balanco_section():
    L = ["## Balanço contra o SW:ACD", "",
         f"Alvo: cada arma do Bullet Strike bate ~{FATOS['alvo_pct']} % mais que a equivalente do SW no mesmo nível "
         f"(banda {FATOS['banda_alvo']}x), no casco e no escudo. Em troca, a arma custa logística: fábricas, paióis e "
         "estoque.", ""]
    rows = []
    for r in BAL["vs_sw_table"]:
        g = r["group"]
        if g in ("PEM", "railgun", "missil"):
            continue
        if g == "defesa":
            ours = f"{num(r['ours_antishot'])} anti-tiro/s"
            rat = f"{razao(r['ratio_hull'])}x (lasers {razao(r['ratio_antilaser'])}x)"
        elif g == "plasma":
            ours = f"{num(r['ours_hull_dps'])} casco / {num(r['ours_shield_dps'])} escudo"
            rat = (f"{razao(r['ratio_hull'])}x / {razao(r['ratio_shield'])}x; por tile "
                   f"{razao(r['ratio_shield_per_tile'])}x")
        else:
            ours = f"{num(r['ours_hull_dps'])} casco/s"
            rat = f"{razao(r['ratio_hull'])}x" + (f"; por tile {razao(r['ratio_per_tile_vs_late_line'])}x"
                                                    if r.get("ratio_per_tile_vs_late_line") else "")
        rows.append([{"canhao": "canhão", "defesa": "defesa", "plasma": "plasma"}[g], r["ours"], ours,
                     ancora(r["sw_anchor"]), rat])
    for p in (PEM["bs_pem_light"], PEM["bs_pem_medium"], PEM["bs_pem_heavy"]):
        vs = p["computed"].get("vs_sw") or {}
        rows.append(["PEM", p["codename"], f"{num(p['computed']['shp_per_s'])} escudo/s", ancora(vs.get("anchor")),
                     f"{razao(vs.get('shp_per_s', 0))}x"])
    for r in BAL["vs_sw_table"]:
        if r["group"] == "missil" and r.get("ratio_shield") and not r.get("metric"):
            rows.append(["míssil", r["ours"], f"{num(r['ours_shield_dps'])} escudo/s", "íons do SW por tile",
                         f"{razao(r['ratio_shield'])}x"])
    if RAIL["enabled"]:
        for n in (1, 4, MAX_CANOS):
            r = NROW[n]
            rows.append(["railgun", f"Tupã, {n} cano{'s' if n > 1 else ''}", f"{num(r['pool_per_shot'])} por tiro",
                         f"{FATOS['sw_siege']} ({FATOS['sw_siege_tiro']} por tiro)",
                         f"{razao(r['vs_sw_siege_per_shot'])}x por tiro; {razao(r['vs_sw_late_line_353_per_tile'])}x "
                         "por tile"])
    L += tabela(["Grupo", "Arma", "Bullet Strike", "Âncora do SW", "Razão"], rows) + [""]
    plasma = [r for r in BAL["vs_sw_table"] if r["group"] == "plasma" and r.get("below_band_by_rule")]
    out = [r for r in BAL["vs_sw_table"] if r["group"] == "canhao" and r["ratio_hull"] > BANDA[1]]
    L += [f"- **Fora da banda de propósito:** {lista(r['ours'] for r in out)} (sem par do SW desse tamanho; "
          f"{FATOS['flagship_max']} somados por nave).",
          f"- **Plasma abaixo da banda por regra:** por tile, "
          f"{lista(r['ours'] + ' ' + razao(r['ratio_shield_per_tile']) + 'x' for r in plasma)} os íons do SW; e o "
          "overclock de escudo corta o plasma pela metade. O anti-escudo do Bullet Strike é a linha PEM.", ""]
    # residuo fora do alvo (R4)
    wr = BAL["ap_path_model"]["worst_r4"]
    he_x = _he_x_mapinguari()
    L += ["### Fora do alvo do balanço", "",
          "O alvo do balanço é o casco do SW (1 durasteel + interior), que o teste T3 mede. Fora dele ainda sobra:",
          "",
          f"- **AP das metralhadoras:** até {razao(wr['ap_fora_do_alvo_pen_le_8']['valor'])}x o HE "
          f"({wr['ap_fora_do_alvo_pen_le_8']['arma']}) em blindagem do jogo base ou casco sem blindagem; não é "
          f"medido (no casco do SW elas param na durasteel e ficam em {FATOS['ap_pen8_no_alvo']}x).",
          f"- **AP e SAP dos canhões grandes fora do casco do SW:** em blindagem do jogo base o HE perde a explosão ao "
          f"atravessar, e o AP chega a {razao(wr['ap_fora_do_alvo']['valor'])}x o HE ({wr['ap_fora_do_alvo']['arma']});"
          f" o SAP, a {razao(wr['sap_fora_do_alvo']['valor'])}x."]
    L.append(f"- **HE do {FATOS['mapinguari']}:** {he_x}. Vale até o teste T3 responder (checklist 10.1).")
    L.append("")
    return L


def _he_x_mapinguari():
    """Frase do HE do Mapinguari no interior do jogo base (switches.guns.he_further_factor.residual_r4)."""
    res = D.SPEC["switches"]["guns"]["he_further_factor"].get("residual_r4") or ""
    m = re.search(r"interior R1 linear ([\d,]+) / ([\d,]+)", res)
    if m:
        return (f"no modelo, com o interior do jogo base, o que entra depois da primeira peça fica {m.group(2)}x o do "
                f"turbolaser do SW (o {FATOS['trovao']}, {m.group(1)}x; o limite é {FATOS['t3_he_lim']}x)")
    raise SystemExit("make_docs: switches.guns.he_further_factor.residual_r4 sem 'interior R1 linear X / Y' "
                     "(o spec mudou?)")


def logistica_section():
    late_band = next(r["band"] for r in D.SPEC["logistics_table"] if r["tier"] == "late")
    early_band = next(r["band"] for r in D.SPEC["logistics_table"] if r["tier"] == "early")
    L = ["## Logística por tipo de munição", "",
         "Tiles de fábrica do Bullet Strike para sustentar 1000 de dano (ou escudo) por segundo em fogo contínuo. "
         f"Banda: {numeros_pt(early_band.replace('-', ' a '))} no início e no meio, "
         f"{numeros_pt(late_band.replace('-', ' a '))} no fim. A banda conta só as fábricas do Bullet Strike no ritmo "
         "do projeto"
         + (", que é o de uma fábrica com 2 vizinhas (a vizinhança está ligada e os intervalos foram multiplicados por "
            f"{num(adj_factor()[0], 2)}; sozinha, multiplique por {num(adj_factor()[0], 2)})" if ADJ_ON else
            " (sem o bônus de vizinhança)")
         + "; refinados (triaço, bobina, hiperbobina) comprados ou feitos fora. A coluna \"com refino\" soma o refino "
         "do jogo base. Overclock: um terço.", ""]
    rows = []
    for r in D.SPEC["logistics_table"]:
        pid = r["id"]
        dps, mt = r["dps"], r["metric"]
        if _short(pid) in PEM:
            # a linha do spec traz o numero da Tuvira fixa; o da torre esta no computed (ADDENDUM)
            dps = PEM[_short(pid)]["computed"]["shp_per_s"]
        if pid == RAIL["parts"]["carregador"]["id"] and not RAIL["enabled"]:
            continue
        metric = {"hull": "casco", "shield": "escudo", "antishot": "anti-tiro"}.get(mt, mt)
        st = {"in_band": "na banda", "premium": "acima (munição cara)", "n/a": "-"}.get(r["status"], None)
        if st is None:
            st = "acima de propósito (canos curtos)" if "acima" in r["status"] else r["status"]
        rows.append([r["weapon"], _kind_label(r["mode"]) if r["mode"] in ("he", "ap", "sap", "ac", "frag", "plasma",
                                                                         "pem") else
                     {"cluster": "Submunição", "emp": "PEM", "nuclear": "Nuclear"}.get(r["mode"], None)
                     or _tupa_tipo(r["mode"]),
                     f"{num(dps)} {metric}", r["factory"], razao(r["tiles_per_1000_base"]),
                     razao(r["tiles_per_1000_with_refining"]), numeros_pt(r["band"]), st])
    L += tabela(["Arma", "Tipo", "Por segundo", "Fábrica", "Tiles por 1000", "Com refino", "Banda", "Situação"],
                rows) + [""]
    notas = [t for t in BAL.get("notes", []) if t.startswith("Logistica por tipo")]
    if notas:
        m = re.search(r"AP pede ~([\d,]+)x.*?SAP ~([\d,]+)x.*?AC ~([\d,]+)x", notas[0])
        if m:
            L += [f"AP pede ~{m.group(1)}x mais fábrica por dano que o HE, SAP ~{m.group(2)}x e AC ~{m.group(3)}x: é o "
                  "preço de trocar dano por penetração (AP e SAP) ou por alfa (AC).", ""]
    return L


def _tupa_tipo(mode):
    m = re.match(r"slug_N(\d+)", mode)
    return f"Projétil, {m.group(1)} cano{'s' if m.group(1) != '1' else ''}" if m else mode


def ancora(txt):
    """Ancora do SW sem os detalhes internos entre parenteses/colchetes."""
    t = re.sub(r"\s*\([^)]*\)", "", str(txt or "-"))
    t = re.sub(r"\s*\[[^\]]*\]", "", t)
    return t.strip() or "-"


def visual_section():
    vfx = _json(os.path.join(SPEC_DIR, "bullet_strike_vfx.json"))
    mfx = _json(os.path.join(SPEC_DIR, "bullet_strike_missile_fx.json"))
    L = ["## Efeitos visuais", "",
         "Só visual: nada de dano, alcance ou cadência muda. O tamanho segue o calibre. As balas pequenas são "
         "traçantes na cor da munição; do 76 mm para cima são granadas 3D futuristas. O brilho grande dos projéteis "
         "aparece só no espaço (o casco branco não fica lavado). Escalas em relação ao efeito do jogo base "
         "(1 = tamanho do jogo).", ""]
    cores = {"he": "âmbar", "ap": "branco-azulado", "sap": "laranja", "ac": "carmim com faixa dourada",
             "frag": "verde-água"}
    L += ["Cores: " + "; ".join(f"{k.upper()} {v}" for k, v in cores.items()) + ".", ""]
    rows = []
    names = {g["short"]: g for g in D.GUNS + D.DEFENSES}
    for short in vfx["order"]:
        w = vfx["weapons"][short]
        g = names.get(short)
        pr, mz, im = w.get("projectile"), w["muzzle"], w["impact"]
        if pr is None:
            fly = "explode no ar"
        elif pr.get("look") == "tracer":
            fly = "traçante"
        else:
            fly = "granada 3D" + (" + fumaça" if pr.get("smoke_trail") else "")
        n0 = mz["N"][0][1] if mz.get("N") else None
        oc = mz["OC"][0][1] if mz.get("OC") else None
        sh = mz.get("shake") or [0]
        ish = im.get("shake") or [0]
        cal = g["spec"].get("caliber") if g and g in D.GUNS else None
        rows.append([g["codename"] if g else short, cal or f"{num(w['mm'], 2)} mm", fly,
                     (f"x{num(n0, 2)}" if n0 else "-") + (f" (OC x{num(oc, 2)})" if oc else ""),
                     f"{num(sh[0], 3)} / {num(ish[0], 3)}"])
    L += tabela(["Arma", "Calibre", "Em voo", "Clarão de boca", "Tremor (disparo / impacto)"], rows) + [""]
    L += ["Mísseis: cada tipo tem arte 3D própria, luzes e escapamento na cor do tipo: "
          + lista(f"{_tipo_missil(k)} {_cor(v.get('halo'))}" for k, v in mfx["types"].items())
          + ". A Piranha solta as pétalas do nariz ao abrir; a Iara tem o trevo de radiação e a explosão nuclear "
          "verde.", ""]
    return L


def _tipo_missil(k):
    c = next((c for c in D.SPEC["toggles"]["bs_missile_type"]["choices"]
              if c["choice_id"].endswith("_" + k)), None)
    return c["codename"] if c else k


def _cor(rgb):
    """Nome da cor do escapamento pelo canal dominante (halo do bullet_strike_missile_fx.json)."""
    if not rgb:
        return ""
    r, g, b = rgb[:3]
    if g >= r and g >= b and b < 160:
        return "(verde)"
    if b >= r and b >= g:
        return "(azul)"
    if r >= 200 and g >= 200:
        return "(amarelo)"
    if r >= 200:
        return "(âmbar)"
    return ""


# ============================================================================= MISSEIS_PROJETO.md
def misseis_md():
    M = MSPEC
    L = ["# Lança-mísseis de convés do Bullet Strike 2.0", "", GERADO, "",
         f"> **{FATOS['desc_prefixo']}** Números do build de teste. O que testar está nas seções 6 e 11 do "
         "[checklist](CHECKLIST_2_0.md).", ""]
    L += ["## 1. Em um parágrafo", "",
          f"Três lançadores de convés, um por fase: **{lista(Lc['codename'] for Lc in D.LAUNCHERS)}**. Cada um carrega "
          "cargas de míssil feitas na Fábrica de Mísseis (e ogivas nucleares na Fábrica de Ogivas), guardadas num "
          "depósito por tipo dentro do lançador. Um autocarregador passa as cargas para as células visíveis, só com "
          "tripulação no posto; com todas as células cheias sai a salva em sequência e a recarga recomeça. O tipo é "
          "escolhido no botão do lançador. Sem energia: o custo é a logística (fábrica, paiol e Fita).", ""]
    # lancadores
    L += ["## 2. Os lançadores", ""]
    rows = []
    for Lc in D.LAUNCHERS:
        spec = next(x for x in D.MSPEC["launchers"] if x["id"] == Lc["id"])
        lim = next((f"{x['max']} por nave" for x in D.LIMIT_DEFS if Lc["id"] in x["parts"]), "-")
        rows.append([f"**{Lc['codename']}**", Lc["name_pt"], TIER_CURTO[Lc["tier"]], tam(Lc["size"]), Lc["crew"],
                     Lc["cp"], num(Lc["hp"]), num(spec["build_cost_credits"]),
                     (Lc.get("oc") or {}).get("name_pt") or "sem overclock", lim])
    L += tabela(["Codinome", "Lançador", "Fase", "Tamanho", "Tripulação", "Comando", "Vida", "Custo", "Overclock",
                 "Limite"], rows) + [""]
    L += ["### Modos", "",
          "Estoque = 1 salva nas células + 4 salvas no depósito. Ciclo = recarga de todas as células + salva.", ""]
    rows = []
    lab = {c["index"]: c.get("label_ptbr") for c in D.SPEC["toggles"]["bs_missile_type"]["choices"]}
    for Lc in D.LAUNCHERS:
        ocx = (Lc.get("oc") or {}).get("per_mode") or {}
        for m in Lc["modes"]:
            c = m["computed"]
            sh = next(s for s in D.MISSILES if s["file"] == m["shot"])
            per_unit = m["parts"] / m["mpu"]
            carga = (f"{num(per_unit, 2)} carga{'s' if per_unit > 1 else ''} por míssil" if per_unit >= 1 else
                     f"1 carga = {num(m['mpu'])} mísseis")
            a_, _, b_ = str(m["ripple"]).partition("/")
            rip = f"{num(int(a_) / int(b_), 2)} s" if b_ else str(m["ripple"])
            dmg = (f"{num(c['shield_eff_dps'])} escudo/s" if c.get("damage_per_charge_metric") == "shield_hp"
                   else f"{num(c['hull_eff_dps'])} casco/s")
            o = ocx.get(m["type"])
            rows.append([Lc["codename"], f"{m['codename']} ({lab[m['index']]})", f"{sh['per_salvo']}",
                         carga, f"{num(m['reload'], 2)} s", rip, dmg, f"{num(sh['range'])} m",
                         f"{num(m['storage'])}", f"÷{num(o, 2)}" if o else "-"])
    L += tabela(["Lançador", "Míssil", "Por salva", "Cargas", "Recarga por célula", "Entre um míssil e outro", "Dano",
                 "Alcance", "Depósito (cargas)", "Overclock na recarga"], rows) + [""]
    L += ["## 3. Os mísseis", ""]
    L += _missil_he() + _missil_piranha() + _missil_poraque() + _missil_iara()
    # fabricas e recursos
    L += ["## 4. Cargas e fábricas", ""]
    rows = []
    for a in M["ammo_per_type"]:
        r = RES_ID[a["resource"]]
        f = next(f for f in D.FACTORIES if any(x["output_resource"] == a["resource"] for x in f["recipes"]))
        rc = next(x for x in f["recipes"] if x["output_resource"] == a["resource"])
        upc = rc.get("units_per_cycle", 1)
        rows.append([r["name_pt"], num(r["max_stack"]), f"{f['code']} {f['name_pt']}",
                     (f"{upc} a cada " if upc > 1 else "1 a cada ") + f"{num(intervalo(rc, 0), 2)} s sozinha, "
                     f"{num(intervalo(rc, 2), 2)} s com 2 vizinhas",
                     ", ".join(f"{k} {v}" for k, v in a["per_missile"].items() if isinstance(v, (int, float)))
                     or "-"])
    L += tabela(["Carga", "Pilha", "Fábrica", "Ritmo", "Cargas por míssil"], rows) + [""]
    L += ["Com a Fita, a Fábrica de Mísseis manda as cargas para os paióis de mísseis e os paióis empurram para os "
          "lançadores no tipo escolhido. Sem a Fita, a tripulação abastece abaixo da metade; na reserva sem Fita um "
          "paiol encostado no lançador também alimenta.", ""]
    # balanco
    L += ["## 5. Balanço", ""]
    rows = []
    rot = {"he": "HE", "cluster": "Submunição"}
    for r in BAL["vs_sw_table"]:
        if r["group"] != "missil":
            continue
        nome, _, modo = r["ours"].rpartition(" ")
        if r.get("metric"):
            rows.append([f"{nome} ({rot.get(modo, modo)})", f"{num(r['ours_hull_dps'])} casco/s",
                         "lançador do SW (densidade do sistema)", f"{razao(r['ratio_hull'])}x"])
        else:
            rows.append([f"{nome} ({modo})", f"{num(r['ours_shield_dps'])} escudo/s", "íons do SW (por tile)",
                         f"{razao(r['ratio_shield'])}x"])
    L += tabela(["Lançador e modo", "Dano", "Comparado com", "Razão"], rows) + [""]
    dens = [r for r in BAL["vs_sw_table"] if r["group"] == "missil" and r.get("metric")]
    L += [f"A conta dos lançadores é a densidade do sistema (lançador + fábrica + tripulação, por tile), porque os "
          f"lançadores do SW pagam em peças de míssil e tripulação. Só com a tripulação, sem a Fita e sem acoplamento: "
          f"{_parse(r'([0-9,]+-[0-9,]+x)', dens[0].get('note_tripulacao', ''), 'note_tripulacao')}.", ""]
    rows = []
    for t in M["internal_stock_and_cookoff"]["table"]:
        rows.append([t["launcher"], {"he": "HE", "cluster": "Submunição", "emp": "PEM", "nuclear": "Nuclear"}
                     .get(t["mode"], t["mode"]), num(t["total_charges"]), f"{num(t['seconds_of_fire'], 1)} s"])
    L += ["### Estoque interno", ""] + tabela(["Lançador", "Modo", "Cargas (células + depósito)", "Tempo de tiro"],
                                              rows) + [""]
    L += ["O lançador carregado explode junto com o estoque quando é destruído (uma explosão por depósito, com o "
          "teto da 1.x).", ""]
    # techs
    L += ["## 6. Techs", ""]
    rows = []
    for t in D.SPEC["career_techs"]:
        if any(u.startswith("missile:") or u in LCH_IDS for u in t["unlocks"]) or "bs_msl_" in t["id"]:
            pre = [_tech_nome(p) if p.startswith("rafaeltessaro.") else f"`{p}`" for p in t["prerequisites"]]
            rows.append([_tech_nome(t["id"]), num(t["cost_credits"]), lista(pre) or "-",
                         lista(_unlock_pt(u) for u in t["unlocks"])])
    L += tabela(["Tech", "Custo", "Pré-requisitos", "Libera"], rows) + [""]
    # variantes
    L += ["## 7. Variantes (o que muda se um teste falhar)", ""]
    rows = []
    for key in sorted(k for k in D.SWITCH_DEFS if k.startswith("missiles.")):
        e = D.SWITCH_DEFS[key]
        vals = e.get("values")
        alt = ", ".join(str(v) for v in (vals.keys() if isinstance(vals, dict) else vals or []))
        if not alt and isinstance(e.get("default"), bool):
            alt = "true, false"
        rows.append([f"`{key}`", f"`{D._canon(D.switch(key))}`", alt or "-", _decidido(e)])
    L += tabela(["Switch", "Neste build", "Valores", "Decidido por"], rows) + [""]
    return "\n".join(L)


LCH_IDS = {L["id"] for L in D.LAUNCHERS}


def _decidido(e):
    d = e.get("decided_by")
    if not d:
        return "-"
    if isinstance(d, dict):
        return "kit TesteFita"
    m = re.search(r"(T-[A-Z0-9-]+|T\d+|B-\d|R-\d|T-ART-\d+|C\d|A\d+b?)", str(d))
    if str(d).startswith("usuario"):
        return "você (outras escolhas)"
    if m:
        return f"teste {m.group(1)}"
    return "teste do build"


def _missil_he():
    out = ["### HE: Jararaca (e Muriçoca na Tocandira)", ""]
    rows = []
    for s in D.MISSILES:
        if s["payload"] != "he":
            continue
        dm = s["damage"]
        rows.append([s["launcher_codename"], s["codename"], num(dm["ExplosiveDamage"]), f"{num(dm['Radius'], 2)} m",
                     num(s["hp"]), f"{num(s['range'])} m", s["per_salvo"]])
    out += tabela(["Lançador", "Míssil", "Explosão", "Raio", "Vida do míssil", "Alcance", "Por salva"], rows)
    return out + ["", "Míssil padrão: barato e bom para saturar a defesa de ponto. Não acende fogo.", ""]


def _missil_piranha():
    out = ["### Submunição: Piranha", ""]
    rows = []
    for s in D.MISSILES:
        if s["payload"] != "cluster":
            continue
        ch, ca = s["children"][0], s["carrier"]
        rows.append([s["launcher_codename"], f"{num(ca['proximity_range'])} m",
                     f"{num(ca['proximity_start_delay'], 1)} s",
                     f"{num(ca['timed_fuse'], 1)} s", ch["count"], num(ch["hp"]), num(ch["damage"]),
                     f"{num(ch['radius'], 1)} m", num(s["hp"])])
    out += tabela(["Lançador", "Abre a", "Nunca antes de", "Abre sozinha em", "Minimísseis", "Vida de cada",
                   "Explosão de cada", "Raio", "Vida do portador"], rows)
    out += ["", "O portador abre antes do alvo e solta um cardume de minimísseis que se espalham pelas peças "
            "inimigas (cada um procura uma peça diferente); as pétalas do nariz caem e somem. Fora de alcance ele abre "
            "sozinho; um impacto antes da hora também solta o cardume. Nunca abre sobre o próprio convés. "
            f"Neste build: alvo aleatório `{D.switch('missiles.cluster_randomize_target')}`, pétalas "
            f"`{D.switch('missiles.cluster_petals')}`, versão leve "
            f"`{D._canon(D.switch('missiles.cluster_lite'))}`.", ""]
    return out


def _missil_poraque():
    out = ["### PEM: Poraquê", ""]
    rows = []
    for s in D.MISSILES:
        if s["payload"] != "emp":
            continue
        p, dm = s["poraque"], s["damage"]
        rows.append([s["launcher_codename"], num(p["drain"]), num(p["Damage"]), num(dm["shield_hp_per_missile"]),
                     num(dm["shield_hp_per_salvo"]), f"{num(dm['HitOperational']['ExplosiveResourceDrain_battery'])} "
                     f"({num(dm['HitOperational']['Radius'], 1)} m)"])
    out += tabela(["Lançador", "Dreno no escudo", "Dano no escudo", "Escudo por acerto", "Escudo por salva",
                   "Pulso no casco (raio)"], rows)
    ov = D.switch("missiles.poraque_overload")
    out += ["", "Drena a bateria do escudo atingido (como os íons do SW): o overclock do escudo não corta esse dreno. "
            "No casco, um pulso de área apaga peças com energia. Nenhuma salva derruba sozinha uma bolha gigante do "
            "SW. "
            f"Sobrecarga extra no escudo: {'ligada' if ov else 'desligada'} neste build "
            "(`missiles.poraque_overload`).", ""]
    return out


def _missil_iara():
    s = MSL["bs_msl_quad_nuclear"]
    wh = s["children"][0]
    nn = MSPEC["iara"]["numbers"]
    out = ["### Nuclear: Iara", "",
           f"Só na {s['launcher_codename']}, {s['per_salvo']} por salva, 1 Ogiva Nuclear por míssil. Dois estágios: o "
           f"corpo voa {num(s['deploy_lifetime'], 1)} s e solta a ogiva, que segue o alvo. Uma ogiva só. "
           f"Explosão: {num(wh['damage']['op'])} ({num(wh['damage']['op_radius'])} m) nas peças + "
           f"{num(wh['damage']['struct'])} ({num(wh['damage']['struct_radius'])} m) na estrutura. Vida "
           f"{num(s['hp'])}, alcance {num(s['range'])} m, recarga {num(nn['reload_s_per_missile'], 2)} s por míssil "
           f"(o overclock não acelera a nuclear). No máximo {LIM['bs_limit_nuke']['max']} "
           f"{LIM['bs_limit_nuke']['nouns_ptbr'][1].lower()} por nave.", ""]
    return out


# ============================================================================= CHECKLIST
def _itens(sec):
    return sec.get("itens") or []


def com_sw_ids():
    return [i["id"] for s in CHK["sections"] for i in _itens(s) if i.get("com_sw")]


def portao():
    return set(CHK.get("portao") or [])


def _check_com_sw(i):
    if i.get("com_sw") and not i["faca"].startswith("(com SW)"):
        raise SystemExit(f"checklist {i['id']}: item com com_sw tem que comecar por '(com SW)'")
    if not i.get("com_sw") and i["faca"].startswith("(com SW)"):
        raise SystemExit(f"checklist {i['id']}: '(com SW)' sem com_sw")


def abertura():
    sw = com_sw_ids()
    return [f"Este é o build de **teste** da 2.0 com a Fita de Alimentação (pasta `{FATOS['pasta_mod']}`, versão "
            f"{FATOS['versao']}, descrição começando com \"{FATOS['desc_prefixo']}\"). Se ele não carregar, use a "
            f"reserva \"{FATOS['nome_reserva']}\" (seção 12). Os itens marcados **(com SW)** são feitos com o Star "
            "Wars: A Cosmos Divided ativo junto; **todos os outros, só com o Bullet Strike**. Sugestão: faça primeiro "
            "todos os itens sem a marca e depois, com o SW ativo, todos os (com SW) de uma vez: "
            f"{lista(sw)}.",
            "",
            "Os itens com ★ liberam a versão final 2.0.0; se tiver pouco tempo, faça pelo menos esses. Em cada item: "
            "faça o que está em \"O que fazer\", confira \"O que olhar\" e marque sim ou não. Se for não, siga o "
            "\"Se não\". No fim (seção 13) está como me mandar as respostas."]


def _confere_ordem():
    """As 14 secoes na ordem do ADDENDUM (checklist.required_order: 0 instalacao ... 13 como mandar)."""
    ns = [s["n"] for s in CHK["sections"]]
    ordem = CHK.get("required_order") or ADD["checklist"]["required_order"]
    if ns != list(range(len(ordem))):
        raise SystemExit(f"checklist: secoes {ns} fora da ordem do ADDENDUM ({len(ordem)} secoes)")
    ids = [i["id"] for s in CHK["sections"] for i in _itens(s)]
    if len(ids) != len(set(ids)):
        raise SystemExit("checklist: id de item repetido")
    falta = portao() - set(ids)
    if falta:
        raise SystemExit(f"checklist: itens do portao inexistentes: {sorted(falta)}")


def checklist_md():
    _confere_ordem()
    L = [f"# {CHK.get('titulo') or 'Bullet Strike 2.0 - o que testar'}", "",
         GERADO.replace("Não edite à mão.", "Não edite à mão: o texto fica em `tools/spec/checklist_2_0.json`."), ""]
    L += [preenche(x, "abertura") for x in abertura()] + [""]
    if PENDENTES:
        L += [f"> {pendente(x)}" for x in list(PENDENTES)] + [""]
    gate = portao()
    for s in CHK["sections"]:
        L += [f"## {s['n']}. {s['titulo']}", ""]
        if s["n"] == 7 and not MOD_PEM:
            L += nota_pem()
        if s["n"] == 8:
            L += nota_rail()
        prep = s.get("preparo")
        if prep:
            L += ["**Preparo:**", ""]
            L += [f"- {preenche(p, f'preparo {s[chr(110)]}')}" for p in (prep if isinstance(prep, list) else [prep])]
            L += [""]
        if s.get("instrucoes"):
            for k, i in enumerate(_itens(s), 1):
                txt = preenche(i["faca"], i["id"])
                if i.get("olhe"):
                    txt += " " + preenche(i["olhe"], i["id"])
                L.append(f"{k}. {txt}")
            L.append("")
            continue
        for i in _itens(s):
            _check_com_sw(i)
            star = " ★" if i["id"] in gate else ""
            L += [f"**{i['id']}**{star}", "",
                  f"- **O que fazer:** {preenche(i['faca'], i['id'])}",
                  f"- **O que olhar:** {preenche(i['olhe'], i['id'])}",
                  "- **Deu certo?** [ ] sim  [ ] não",
                  f"- **Se não:** {preenche(i.get('se_nao') or 'Anote o que viu.', i['id'])}"]
            if i.get("decide"):
                L.append(f"- _(decide: {i['decide']})_")
            L.append("")
    return "\n".join(L)


def checklist_curto(md_rel="docs/CHECKLIST_2_0.md"):
    gate = portao()
    L = ["BULLET STRIKE 2.0 - CHECKLIST CURTO",
         f"(o completo, com o preparo de cada seção, está em {md_rel} no repositório)", "",
         f"Build de teste com a Fita (pasta {FATOS['pasta_mod']}, versão {FATOS['versao']}, descrição começando com "
         f"\"{FATOS['desc_prefixo']}\").",
         f"Se não carregar, use a reserva \"{FATOS['nome_reserva']}\" (nunca as duas juntas).",
         "Itens \"(com SW)\": com o Star Wars: A Cosmos Divided ativo junto. Todos os outros: só o Bullet Strike.",
         "Faça primeiro os itens sem a marca e depois os \"(com SW)\" de uma vez.",
         "★ = libera a versão final 2.0.0.", ""]
    for s in CHK["sections"]:
        itens = [i for i in _itens(s) if i.get("curto") or i["id"] in gate]
        if not itens:
            continue
        L += [f"== {s['n']}. {s['titulo']} ==", ""]
        if s.get("instrucoes"):
            for i in itens:
                txt = preenche(i["faca"], i["id"])
                if i.get("olhe"):
                    txt += " " + preenche(i["olhe"], i["id"])
                L.append(f"- {txt}")
            L.append("")
            continue
        prep = s.get("preparo")
        if prep:
            L.append("Preparo:")
            L += [f"  - {preenche(p, 'preparo')}" for p in (prep if isinstance(prep, list) else [prep])]
            L.append("")
        for i in itens:
            star = " ★" if i["id"] in gate else ""
            L += [f"{i['id']}{star}   [ ] sim  [ ] não",
                  f"  Faça: {preenche(i['faca'], i['id'])}",
                  f"  Olhe: {preenche(i['olhe'], i['id'])}",
                  f"  Se não: {preenche(i.get('se_nao') or 'Anote o que viu.', i['id'])}", ""]
    return "\n".join(L)


# ============================================================================= COMO_TESTAR.md
def como_testar_md():
    zips = ADD["deliverable"]["zips"]
    L = ["# Bullet Strike 2.0: como testar", "", GERADO, "",
         "O roteiro de testes da 2.0 é o **[CHECKLIST_2_0.md](CHECKLIST_2_0.md)**. Ele começa pela instalação, pelo "
         "carregamento e pela Fita de Alimentação, e segue família por família. Este arquivo só junta as dicas e o que "
         "está valendo enquanto os testes não voltam.", ""]
    L += ["## 1. O que instalar", ""]
    rows = []
    for v, z in (("fita", "testes/BulletStrike_2_0.zip"), ("semfita", "testes/BulletStrike_SemFita.zip")):
        var = D.VARIANTS[v]
        rows.append([f"`{var['out'].rstrip('/')}`", var["name"], f"`{z}`" if z in zips else "-",
                     var["description_first_line_ptbr"]])
    L += tabela(["Pasta no repositório", "Nome na lista de mods", "Zip", "Descrição"], rows) + [""]
    L += ["Nunca ative as duas juntas: as peças têm os mesmos IDs. Cada zip traz também o `CHECKLIST_2_0_CURTO.txt` "
          "(os itens essenciais).", ""]
    L += ["## 2. Como seguir o checklist", "",
          "- Faça as seções na ordem. A seção 2 (Fita) vem antes das armas porque decide o transporte da munição.",
          f"- Os itens com ★ liberam a versão final 2.0.0: {lista(sorted(portao(), key=_ordem))}.",
          f"- Os itens **(com SW)** são com o Star Wars: A Cosmos Divided ativo junto: {lista(com_sw_ids())}. Todos "
          "os outros: só o Bullet Strike.",
          "- Abra o jogo com o modo desenvolvedor (na Steam: botão direito no Cosmoteer > Propriedades > Opções de "
          "inicialização > `--devmode`): os erros de carregamento aparecem com detalhes.",
          "- Se travar, o motivo fica nas primeiras linhas do log mais recente da pasta Logs, acima de "
          "`--- End of inner exception stack trace ---`.", ""]
    sec13 = next((s for s in CHK["sections"] if s.get("instrucoes")), None)
    if sec13:
        L += ["## 3. Como me mandar o resultado", ""]
        for k, i in enumerate(_itens(sec13), 1):
            txt = preenche(i["faca"], i["id"]) + (" " + preenche(i["olhe"], i["id"]) if i.get("olhe") else "")
            L.append(f"{k}. {txt}")
        L.append("")
    L += ["## 4. O que está valendo enquanto os testes não voltam", "",
          "Cada escolha que depende de um teste usa o valor seguro (\"safe\") até a resposta, a não ser que você já "
          "tenha respondido ou que o build precise de outro valor. Quando você mandar as respostas, eu troco o que "
          "falhou.", ""]
    rows = []
    item_by_switch = _itens_por_switch()
    g9 = _g9_decididas()
    for key in sorted(D.SWITCH_DEFS):
        e = D.SWITCH_DEFS[key]
        if "decided_by" not in e or e.get("decided_by") is None:
            continue
        if key in D.SPEC["build_2_0"].get("not_applicable", []):
            continue
        v = D.switch(key)
        rows.append([f"`{key}`", f"`{D._canon(v)}`", _por_que(key, e, v, g9), item_by_switch.get(key, "-")])
    L += tabela(["Escolha", "Valor neste build", "Por quê", "Item do checklist"], rows) + [""]
    L += ["## 5. Testes do projeto x itens do checklist", ""]
    mp = CHK.get("maps_tests") or {}
    for k, v in mp.items():
        L.append(f"- **{ {'TesteFita': 'Kit TesteFita', 'build': 'Testes do 1º build 2.0'}.get(k, k)}:** {v}")
    L += ["", "Se você ainda tiver respostas do kit TesteFita, elas valem no lugar dos itens correspondentes.", ""]
    return "\n".join(L)


def _g9_decididas():
    """{nome: (valor, nota)} das excecoes decididas do ADDENDUM G9 ('transport teleporte (build), fita_fabrica B, ...').

    O nome pode vir curto (fita_fabrica, paiol_contador): casa pelo sufixo da chave do switch."""
    txt = ADD["global_decisions"]["G9_switches_sem_resposta"]
    m = re.search(r"excecoes decididas:\s*(.+?)\.?\s*$", txt)
    if not m:
        raise SystemExit("make_docs: ADDENDUM global_decisions.G9_switches_sem_resposta sem 'excecoes decididas:' "
                         "(o addendum mudou?)")
    out = {}
    for tok in m.group(1).split(","):
        t = re.match(r"\s*([\w.]+)\s+(\S+)\s*(?:\(([^)]*)\))?\s*$", tok)
        if not t:
            raise SystemExit(f"make_docs: G9 com excecao ilegivel: {tok.strip()!r}")
        out[t.group(1)] = (t.group(2), (t.group(3) or "").strip())
    return out


def _por_que(key, e, v, g9):
    """Coluna 'Por que' da secao 4 do COMO_TESTAR: de quem e o valor deste build."""
    cv = D._canon(v)
    ans = e.get("answered_addendum")
    if ans and D._canon(ans.get("value")) == cv:
        # so e 'sua resposta' quando o registro e do usuario; regra do build (ex.: rail.loader_intake) nao e
        by = _fold(str(ans.get("by") or "")).strip()
        return "sua resposta / pedido" if by.startswith("usuario") else "decisão do build de teste"
    for nome, (val, nota) in g9.items():
        if (key == nome or key.endswith("." + nome)) and D._canon(val) == cv:
            return "decisão do build de teste" if nota == "build" else "decisão (sua resposta / do build)"
    if e.get("safe") is not None and D._canon(e["safe"]) == cv:
        return "safe (sem resposta)"
    fita_vals = D.SPEC["build_2_0"]["switch_values_fita"]
    if key in fita_vals and D._canon(fita_vals[key]) == cv:
        return "decisão do build de teste"
    return D.switch_source(key)


def _ordem(i):
    a, _, b = i.partition(".")
    return (int(a), int(b or 0))


def _mapa_testes():
    """{teste: itens} de checklist.maps_tests ('T-ART-5' -> '3.2'; chaves com '*' ou '..' casam por faixa)."""
    out = {}
    for txt in (CHK.get("maps_tests") or {}).values():
        for parte in txt.split(", "):
            k, sep, v = parte.partition("->")
            if sep:
                for kk in k.split("/"):
                    out[kk.strip()] = v.strip()
    return out


def _casa_teste(tok, chave):
    if chave == tok:
        return True
    if chave.endswith("*"):
        return tok.startswith(chave[:-1])
    m = re.match(r"^(.*?)(\d+)\.\.(?:\1)?(\d+)$", chave)
    if m:
        m2 = re.match(r"^(.*?)(\d+)$", tok)
        return bool(m2) and m2.group(1) == m.group(1) and int(m.group(2)) <= int(m2.group(2)) <= int(m.group(3))
    return False


def _itens_por_switch():
    out = {}
    mapa = _mapa_testes()
    for key, e in D.SWITCH_DEFS.items():
        d = e.get("decided_by")
        if not isinstance(d, str):
            continue
        # so testes com nome inequivoco (T-ART-5, T-MSL-PERF, R-1, B-1, C2...); 'T3' sozinho tem dois sentidos
        for tok in re.findall(r"\b(T-[A-Z]+(?:-[A-Z0-9]+)?|[RB]-\d|[ABC]\d+b?)\b", d):
            hit = next((v for k, v in mapa.items() if _casa_teste(tok, k)), None)
            if hit:
                out[key] = hit
                break
    for s in CHK["sections"]:
        for i in _itens(s):
            d = i.get("decide") or ""
            for key in re.findall(r"([a-z]+\.[a-z_0-9]+)", d):
                if key in D.SWITCH_DEFS:
                    out[key] = i["id"]
            for frag in re.findall(r"/\s*([a-z_0-9]+)", d):
                for key in D.SWITCH_DEFS:
                    if key.endswith("." + frag):
                        out[key] = i["id"]
    return out


# ============================================================================= README.md
GALERIA = [
    ("armas_galeria_2_0.png", "Armas e defesas da 2.0 por fase"),
    ("fabricas_2_0.png", "As 6 fábricas (F1 a F6)"),
    ("logistica_fita.gif", "A Fita de Alimentação: cartuchos saindo da fábrica e entrando no paiol e na arma"),
    ("logistica_paiois.png", "Os paióis (cartuchos, células, mísseis e projéteis)"),
    ("railgun_tranco.gif", "Railgun Tupã: o tranco no disparo"),
    ("railgun_montado.png", "Railgun Tupã montada (carregador, canos e ponta)"),
    ("armas_pem.png", "Linha PEM"),
    ("misseis_lancadores_2_0.png", "Lança-mísseis e mísseis"),
    ("municoes_itens.png", "Os itens de munição"),
    ("projeteis_futuristas.png", "Projéteis futuristas por calibre"),
    ("icones_2_0.png", "Ícones dos botões"),
]


def readme_md():
    v_fita, v_sem = D.VARIANTS["fita"], D.VARIANTS["semfita"]
    prev = os.path.join(REPO, "docs", "preview", "3d", "v2")
    L = ["# Bullet Strike: armas de convés movidas a munição (mod para Cosmoteer)", ""]
    if os.path.isfile(os.path.join(REPO, "docs", "preview", "3d", "logo.png")):
        L += ['<p align="center"><img src="docs/preview/3d/logo.png" width="320" alt="Bullet Strike"></p>', ""]
    L += [f"> **{FATOS['desc_prefixo']}** Esta é a versão 2.0 em teste (versão {D.VERSION}). Ela ainda precisa ser "
          "testada no jogo: siga o **[checklist](docs/CHECKLIST_2_0.md)** e me mande as respostas. A versão final "
          "2.0.0 só sai depois disso.", ">",
          f"> ⚠️ **Saves da 1.x:** {aviso_ruptura()}", ">",
          f"> **Balanço:** {aviso_sw()}", ""]
    n_armas = len(D.GUNS) + len(D.PEM) + (1 if RAIL["enabled"] else 0)
    L += ["**Bullet Strike** é um mod para **Cosmoteer: Starship Architect & Commander** com armas de convés que "
          "gastam **munição** em vez de energia. Na 2.0 a munição tem uma cadeia de verdade: **fábricas** fazem "
          "carregadores, células e cargas de míssil, os **paióis** guardam e a **Fita de Alimentação** leva tudo até "
          "as armas, de um canto ao outro da nave.", "",
          f"- **{n_armas} armas**, **{len(D.DEFENSES)} defesas** e **{len(D.LAUNCHERS)} lança-mísseis**, divididos em "
          "início, meio e fim de jogo.",
          f"- **{len(D.FACTORIES)} fábricas**, **{len(D.PAIOL_PARTS)} paióis** e a **Fita de Alimentação**.",
          f"- **{len(D.RESOURCES)} itens de munição** com visual futurista.",
          f"- Jogo: **{FATOS['versao_jogo']}**. Feito para jogar junto com o **Star Wars: A Cosmos Divided** (SW:ACD).",
          "- Textos em **português (pt-BR)** e **inglês**.", "",
          "## Índice", "",
          "- [Novidades da 2.0](#novidades-da-20)", "- [Qual pasta instalar](#qual-pasta-instalar)",
          "- [Como instalar](#como-instalar)", "- [Como testar](#como-testar)", "- [Galeria](#galeria)",
          "- [Armas por fase](#armas-por-fase)", "- [Logística em um minuto](#logística-em-um-minuto)",
          "- [Limites por nave](#limites-por-nave)",
          "- [Compatibilidade com Star Wars: A Cosmos Divided](#compatibilidade-com-star-wars-a-cosmos-divided)",
          "- [Para quem quer mexer no mod](#para-quem-quer-mexer-no-mod)", "- [Créditos](#créditos)", ""]
    # novidades
    tv, tt, co = PEM["bs_pem_light"], PEM["bs_pem_medium"], PEM["bs_pem_heavy"]
    car = RAIL["parts"]["carregador"]
    _b, bonus = adj_factor()
    amm = {a["key"]: a for a in D.SPEC["ammo_types"]}
    L += ["## Novidades da 2.0", ""]
    if TELEPORTE:
        L += [f"- **Fita de Alimentação (teletransporte):** {D.FITA_PART['description_ptbr']} A fábrica com Fita manda "
              "para os paióis com Fita; o paiol com Fita empurra para as armas com Fita no tipo escolhido. A "
              "tripulação continua de reserva: abastece a arma que cair abaixo da metade."]
    L += [f"- **Paióis:** {FATOS['paiol_familias']}, de 1x1 a 3x3. O tipo é escolhido no botão do paiol; barra e "
          f"medidor no teto ({FATOS['paiol_niveis']} níveis). Na nave com a Fita eles são selados.",
          f"- **Fábricas F1 a F{len(D.FACTORIES)}:** etapa única, sem tripulante, com overclock "
          f"({num(oc_fab(), 1)}x)."
          + (f" Vizinhança ligada como no jogo base (+{num(bonus * 100)} % por fábrica vizinha)." if ADJ_ON else ""),
          "- **Munições:** " + "; ".join(f"**{a['label']}** ({a['name_ptbr']})" for a in amm.values())
          + ". Cada tipo tem o seu estoque na arma, e um tipo nunca vira outro.",
          f"- **Linha PEM:** {tv['codename']} (torre de {num(tv['firing_arc_deg'])}°), {tt['codename']} e "
          f"{co['codename']} (overclock {(co.get('overclock') or {}).get('name_ptbr')}): drenam o escudo, como os íons "
          "do SW."]
    if RAIL["enabled"]:
        L.append(f"- **Railgun Tupã:** fixa e modular: Carregador {tam(car['size'])} + 1 a {MAX_CANOS} canos + Ponta. "
                 "Mais canos = mais dano, alcance, penetração e energia por tiro. Dá um **tranco** a cada disparo e o "
                 "dardo passa por cima da própria nave.")
    L += [f"- **Mísseis:** {lista(_tipo_missil(k) for k in ('he', 'cluster', 'emp', 'nuclear'))} "
          "(HE, submunição, PEM e nuclear).",
          "- **Visual futurista:** itens, granadas, mísseis e ícones novos; brilho dos projéteis só no espaço "
          "(o casco branco não fica lavado).",
          "- **Ruptura limpa com a 1.x:** veja o aviso no topo (saves e naves da 1.x não passam para a 2.0).", ""]
    # pastas
    L += ["## Qual pasta instalar", ""]
    rows = [[f"`{v_fita['out'].rstrip('/')}/`", v_fita["name"], "Principal, com a Fita de Alimentação."],
            [f"`{v_sem['out'].rstrip('/')}/`", v_sem["name"],
             "Reserva: as mesmas armas, paióis e fábricas, sem a Fita (a tripulação leva a munição; paiol encostado "
             "na arma ou na fábrica passa a munição sozinho). Use se a principal não carregar."]]
    L += tabela(["Pasta", "Nome na lista de mods", "Quando usar"], rows) + [""]
    L += ["**Nunca ative as duas juntas:** as peças têm os mesmos IDs. As naves passam de uma para a outra (na reserva "
          "as Fitas somem). Os zips de teste ficam em `testes/` e trazem o `CHECKLIST_2_0_CURTO.txt`.", ""]
    L += ["## Como instalar", "",
          "1. Guarde uma cópia da pasta da 1.x e da sua carreira.",
          f"2. Copie a pasta `{FATOS['pasta_mod']}` para a pasta de mods do Cosmoteer (Windows: "
          "`C:\\Users\\<seu usuário>\\Saved Games\\Cosmoteer\\<seu SteamID>\\Mods\\`). O resultado deve ficar "
          f"`...\\Mods\\{FATOS['pasta_mod']}\\mod.rules`. Apague a pasta antiga antes (arquivos que mudaram de nome "
          "ficariam sobrando).",
          f"3. Se quiser a reserva, copie também `{FATOS['pasta_reserva']}`, mas deixe desativada.",
          f"4. Abra o Cosmoteer, vá em **Mods**, ative o **{v_fita['name']}** e reinicie. Para jogar com o SW:ACD, "
          "ative os dois (a ordem não importa).", ""]
    L += ["## Como testar", "",
          "O roteiro é o **[docs/CHECKLIST_2_0.md](docs/CHECKLIST_2_0.md)**: começa pelo carregamento e pela Fita e "
          "segue família por família. A versão curta (`CHECKLIST_2_0_CURTO.txt`) vai dentro dos zips. Dicas e o que "
          "está valendo enquanto os testes não voltam: [docs/COMO_TESTAR.md](docs/COMO_TESTAR.md).", ""]
    # galeria
    imgs = [(f, t) for f, t in GALERIA if os.path.isfile(os.path.join(prev, f))]
    L += ["## Galeria", ""]
    if imgs:
        for f, t in imgs:
            L += [f"![{t}](docs/preview/3d/v2/{f})", "", f"<p align=\"center\"><i>{t}</i></p>", ""]
    L += ["Todas as prévias da 2.0: [docs/preview/3d/v2/](docs/preview/3d/v2/) (veja também "
          "[docs/preview/2.0/LEIA.md](docs/preview/2.0/LEIA.md)).", ""]
    # armas por fase
    L += ["## Armas por fase", "",
          "Os números completos (dano, vida, custo, consumo, logística) ficam em **[docs/ARMAS.md](docs/ARMAS.md)**; "
          "os lança-mísseis, em **[docs/MISSEIS_PROJETO.md](docs/MISSEIS_PROJETO.md)**.", ""]
    for tier in ("early", "mid", "late"):
        rows = []
        for g in D.GUNS:
            if g["tier"] == tier:
                rows.append([f"**{g['codename']}**", g["name_pt"], tam(g["size"]), g["crew"],
                             f"{num(g['spec']['range_m'])} m", "/".join(mode_label(k) for k in gun_modes(g))])
        for g in D.DEFENSES:
            if g["tier"] == tier:
                rows.append([f"**{g['codename']}**", g["name_pt"] + " (defesa)", tam(g["size"]), g["crew"],
                             f"{num(g['spec']['range_m'])} m", "/".join(mode_label(k) for k in gun_modes(g))])
        for p in D.PEM:
            if p["tier"] == tier:
                rows.append([f"**{p['codename']}**", p["name_pt"], tam(p["size"]), p["crew"], f"{num(p['range_m'])} m",
                             "PEM"])
        for Lc in D.LAUNCHERS:
            if Lc["tier"] == tier:
                rng = max(m["range"] for m in D.MISSILES if m["launcher"] == Lc["id"])
                lab = {c["index"]: c.get("label_ptbr") for c in D.SPEC["toggles"]["bs_missile_type"]["choices"]}
                rows.append([f"**{Lc['codename']}**", Lc["name_pt"], tam(Lc["size"]), Lc["crew"], f"{num(rng)} m",
                             "/".join(lab[m["index"]] for m in Lc["modes"])])
        if tier == "late" and RAIL["enabled"]:
            rows.append(["**Tupã**", f"Railgun (Carregador + 1 a {MAX_CANOS} Canos + Ponta)",
                         f"{num(NROW[1]['tiles'])} a {num(NROW[MAX_CANOS]['tiles'])} tiles", car["crew"],
                         f"{num(NROW[1]['range_m'])} a {num(NROW[MAX_CANOS]['range_m'])} m", "Projétil"])
        L += [f"### {TIER[tier]}", ""] + tabela(["Codinome", "Arma", "Tamanho", "Tripulação", "Alcance", "Munições"],
                                                 rows) + [""]
    L += ["## Logística em um minuto", "",
          "1. **Fábrica:** faz a munição (carregador, célula, carga de míssil, ogiva ou projétil) com matéria-prima do "
          "jogo base e energia.",
          "2. **Paiol:** guarda a munição; você escolhe o tipo no botão dele.",
          f"3. **Arma:** guarda um estoque de {FATOS['estoque_armas']} e gasta enquanto atira.",
          "4. **Fita:** grudada na fábrica, no paiol e na arma, leva a munição de uma para a outra sem caminho e sem "
          "tripulação. Sem a Fita, a tripulação leva, como no jogo base, quando a arma cai abaixo da metade.", ""]
    L += limites_section()
    L += ["## Compatibilidade com Star Wars: A Cosmos Divided", "",
          "- O Bullet Strike **não substitui nenhum arquivo** do jogo nem do SW:ACD: só **adiciona** peças, recursos, "
          "techs e textos, com prefixo próprio (`rafaeltessaro.bs_*`, `BS*`).",
          f"- **Balanceado para jogar com o SW:** cada arma bate ~{FATOS['alvo_pct']} % mais que a equivalente do SW "
          "no mesmo nível, e paga em logística (fábricas, paióis e estoque).",
          "- As defesas derrubam mísseis, minas e balas "
          f"({lista(razao(g['spec']['sw_anchor']['ratio']) + 'x' for g in D.DEFENSES)} "
          f"a defesa do SW) e também parte dos lasers e íons do SW ({FATOS['antilaser_faixa']}x). Os feixes contínuos "
          "do SW não são projéteis e não podem ser abatidos.",
          "- A linha PEM e o míssil Poraquê drenam o escudo como os íons do SW. As armas do Bullet Strike não usam "
          f"bateria{FATOS['ions_excecao']}, então os íons do SW quase não as afetam. As fábricas usam bateria e "
          "sentem os íons.",
          "- Os limites por nave usam o mesmo método do SW:ACD, então os dois mods convivem.", ""]
    L += ["## Para quem quer mexer no mod", "",
          f"Os arquivos de `{FATOS['pasta_mod']}/` e de `{v_sem['out'].rstrip('/')}/` são **gerados**: não edite à "
          "mão. Os números ficam em `tools/spec/SPEC_2.0.json` (dividido em `tools/spec/bullet_strike_*.json` por "
          "`tools/spec2_split.py`); as escolhas de build ficam em `tools/spec/bullet_strike_switches.json`.", "",
          "```bash",
          f"{v_fita['cli']}",
          f"{v_sem['cli']}",
          "python3 tools/make_docs.py --estrito          # README, docs/ e checklist (--curto CAMINHO: o curto)",
          "python3 tools/spec2_check.py --mod BulletStrike --vanilla \"$COSMOTEER_DATA\" --docs",
          "python3 tools/rules_lint.py --mod BulletStrike --vanilla \"$COSMOTEER_DATA\"",
          "```", "",
          "- `$COSMOTEER_DATA` = a pasta `Data` do jogo (`steamapps\\common\\Cosmoteer\\Data`).",
          "- Precisa de Python 3 com **Pillow** e **numpy** (`pip install pillow numpy`).",
          "- Um switch pode ser trocado só num build: `--switch grupo.nome=valor` (ex.: "
          "`--switch logistics.fita_alcance=12`).",
          "- A arte 3D fica em `art3d/` (renders prontos) e os modelos em `tools/blender/`; o build só copia os "
          "renders. `python3 tools/check_art3d.py todos --estrito` confere tudo.", ""]
    rows = [["`BulletStrike/`", "O mod pronto, com a Fita"],
            [f"`{v_sem['out'].rstrip('/')}/`", "A reserva sem a Fita"],
            ["`tools/spec/`", "Spec 2.0, switches, addendum e o texto do checklist (`checklist_2_0.json`)"],
            ["`tools/build_mod.py`", "Gera o mod (`--variante fita` ou `semfita`)"],
            ["`tools/bs_data.py`", "Camada de dados: lê o spec e os switches"],
            ["`tools/bsgen/`", "Geradores das peças, tiros, fábricas, paióis, Fita e efeitos"],
            ["`tools/make_docs.py`", "Gera este README e os docs"],
            ["`tools/spec2_check.py` / `tools/rules_lint.py`", "Conferências do mod gerado"],
            ["`art3d/`", "Renders 3D das peças e munições"],
            ["`docs/`", "ARMAS, MISSEIS_PROJETO, COMO_TESTAR, CHECKLIST_2_0 e as prévias"]]
    L += tabela(["Caminho", "O que é"], rows) + [""]
    L += ["## Créditos", "",
          "- Ideia e direção: **Rafael Tessaro**.",
          "- Arte 3D, regras e ferramentas feitas com ajuda do Claude (Anthropic).",
          "- Sons, imagens de partículas e a maior parte dos efeitos reaproveitam os do Cosmoteer por referência. "
          "Alguns arquivos de partículas do jogo são copiados como texto (`tools/vanilla_fx/`), só com tamanho, "
          "quantidade e posição ajustados; nenhuma imagem nem som do jogo é copiado para o mod.", ""]
    return "\n".join(L)


# ============================================================================= docs/preview/2.0/LEIA.md
V2_DESC = {
    "armas_boiuna_ac.png": "Boiúna (obuseiro âmbar) e a granada AC",
    "armas_casco_branco.png": "Armas novas sobre casco branco",
    "armas_pem_disparo.gif": "Linha PEM atirando",
    "fabricas_2_0.gif": "Fábricas trabalhando",
    "logistica_fita.png": "A Fita grudada nas máquinas (quadros)",
    "misseis_antes_depois.png": "Mísseis: antes e depois",
    "misseis_casco_branco.png": "Mísseis sobre casco branco",
    "misseis_cluster_abrindo.gif": "Piranha abrindo e soltando os minimísseis",
    "misseis_futuristas.png": "Os mísseis em voo",
    "misseis_luzes.gif": "Luzes e escapamento dos mísseis",
    "projeteis_antes_depois.png": "Projéteis: antes e depois",
    "projeteis_casco_branco.png": "Projéteis sobre casco branco",
    "projeteis_luzes.gif": "Luzes dos projéteis em voo",
    "railgun_casco_branco.png": "Tupã sobre casco branco",
    "railgun_disparo.gif": "Tupã disparando (carga azul e dardo)",
    "railgun_disparo.mp4": "Tupã disparando (vídeo)",
    "railgun_pecas.png": "As peças do Tupã",
    "railgun_referencia.png": "Tupã ao lado da referência que você mandou",
    "railgun_tranco.mp4": "O tranco (vídeo)",
    "railgun_tranco_curto.gif": "O tranco, versão curta",
    "railgun_tranco_curto.mp4": "O tranco, versão curta (vídeo)",
    "railgun_tranco_quadros.png": "Quadros do tranco: repouso x recuo",
}

LEIA_DESC = {
    "ac_2_0.gif": "Explosão da munição AC: anel de pressão e brasas douradas.",
    "casco_branco_2_0.png": "Luz dos projéteis sobre casco branco: o brilho grande fica só no espaço.",
    "frag_2_0.gif": "Rajada FRAG das defesas: carga central e fragmentos.",
    "penetracao_2_0.png": "AP atravessando peças: só faísca em cada peça, explosão cheia onde a granada para.",
}


def leia_md():
    pasta = os.path.join(REPO, "docs", "preview", "2.0")
    L = ["# Prévias da 2.0", "", GERADO, "",
         "As prévias da arte 2.0 (armas, munições, fábricas, paióis, Fita, Tupã, linha PEM, mísseis e ícones) ficam em "
         "**[docs/preview/3d/v2/](../3d/v2/)**.", "",
         "Nesta pasta ficam só as prévias dos efeitos das munições:", ""]
    rows = []
    for f in sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []:
        if f.lower().endswith((".png", ".gif", ".mp4")):
            if f not in LEIA_DESC:
                aviso(f"docs/preview/2.0/{f} sem descricao no LEIA_DESC do make_docs.py")
            rows.append([f"[`{f}`]({f})", LEIA_DESC.get(f, "-")])
    L += tabela(["Arquivo", "O que mostra"], rows) + [""]
    v2 = os.path.join(REPO, "docs", "preview", "3d", "v2")
    if os.path.isdir(v2):
        desc = dict(GALERIA)
        desc.update(V2_DESC)
        rows = []
        for f in sorted(os.listdir(v2)):
            if f.lower().endswith((".png", ".gif", ".mp4")):
                if f not in desc:
                    aviso(f"docs/preview/3d/v2/{f} sem descricao no make_docs.py (V2_DESC)")
                rows.append([f"[`{f}`](../3d/v2/{f})", desc.get(f, "-")])
        L += ["Em `docs/preview/3d/v2/`:", ""] + tabela(["Arquivo", "Destaque"], rows) + [""]
    return "\n".join(L)


# ============================================================================= varredura e gravacao
def varredura(nome, texto):
    rs = D.SPEC["conventions"]["removed_names_scan"]
    pat = re.compile(rs["pattern"])
    allow = [a.split(" ")[0] for a in rs.get("allow", [])]
    probs = []
    for n, ln in enumerate(texto.split("\n"), 1):
        for m in pat.finditer(ln):
            h = m.group(0)
            if not any(a in ln and h in a for a in allow):
                probs.append(f"{nome}:{n}: nome removido '{h}'")
        if re.search(r"mae[- ]do[- ]ouro", _fold(ln)):
            probs.append(f"{nome}:{n}: nome antigo da PEM pesada")
    return probs


def gerar(curto=None):
    docs = {
        "README.md": readme_md(),
        "docs/ARMAS.md": armas_md(),
        "docs/MISSEIS_PROJETO.md": misseis_md(),
        "docs/COMO_TESTAR.md": como_testar_md(),
        "docs/CHECKLIST_2_0.md": checklist_md(),
        "docs/preview/2.0/LEIA.md": leia_md(),
    }
    out = {os.path.join(REPO, k): v.rstrip("\n") + "\n" for k, v in docs.items()}
    if curto:
        out[os.path.abspath(curto)] = checklist_curto().rstrip("\n") + "\n"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gera a documentacao pt-BR do Bullet Strike 2.0.")
    ap.add_argument("--curto", metavar="CAMINHO", help="grava tambem o CHECKLIST_2_0_CURTO.txt neste caminho")
    ap.add_argument("--check", action="store_true", help="nao grava; sai 1 se algum arquivo mudaria")
    ap.add_argument("--estrito", action="store_true", help="sai 1 se sobrar 'a confirmar' (pacote final)")
    a = ap.parse_args(argv)
    out = gerar(a.curto)
    probs = []
    for p, txt in out.items():
        probs += varredura(os.path.relpath(p, REPO), txt)
    if probs:
        for p in probs:
            print(f"ERRO: {p}", file=sys.stderr)
        return 1
    mudou = []
    for p, txt in out.items():
        old = None
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                old = fh.read()
        if old != txt:
            mudou.append(p)
            if not a.check:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(txt)
    for p in out:
        rel = os.path.relpath(p, REPO)
        if rel.startswith(".."):
            rel = p
        st = ("mudaria" if a.check else "gravado") if p in mudou else "sem mudança"
        print(f"{rel}: {st}")
    for x in PENDENTES:
        print(f"a confirmar: {x}", file=sys.stderr)
    if a.estrito and PENDENTES:
        print(f"make_docs --estrito: {len(PENDENTES)} pendencia(s) 'a confirmar'", file=sys.stderr)
        return 1
    if a.check and mudou:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
