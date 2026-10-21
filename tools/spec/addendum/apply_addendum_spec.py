#!/usr/bin/env python3
"""Aplica as decisoes posteriores ao plano (ADDENDUM 2.0) no SPEC_2.0.json.

Sempre parte do backup SPEC_2.0.before.json (idempotente) e grava SPEC_2.0.json no mesmo formato (json indent=1,
ensure_ascii=False, '\n' no fim). Roda em dois lugares (mesmo codigo):
  scratchpad  design/final/addendum/ -> grava design/final/SPEC_2.0.json
  repo        tools/spec/addendum/   -> grava tools/spec/SPEC_2.0.json (copia feita pelo WP01, ADDENDUM G13)
Caminhos por variavel de ambiente (opcional): BS_ADDENDUM_BASE (o SPEC_2.0.before.json), BS_TRANCO_PATCH (o
spec_patch do tranco), BS_SPEC_OUT (o SPEC gerado), BS_REPO (o clone do mod; so leitura).

Fontes: design/USER_NOTES.txt (inteiro), railart/tranco/tranco_research.json + o spec_patch.json MAIS NOVO do job do
tranco (a rodada sai do meta.round do arquivo; os metas de art3d/bs_rail_* VENCEM), art3d/*/meta.json do repo (lidos
aqui, so leitura), shellart/make_sheets.py (BOIUNA_THIN, clarao da base) e as decisoes de implementacao do
orquestrador para o build pedido pelo usuario ("monte o MoD"). O estado do repo (HEAD, commit da arte do Tupa,
git status) e lido na hora (git so leitura) e gravado em SPEC.status_addendum: o portao do WP01 so fica SATISFEITO
com o spec_patch da rodada r2 (ou mais nova), um commit de arte do Tupa depois de 9fba772 e o status limpo.
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)
IN_REPO = os.path.basename(FINAL) == "spec" and os.path.basename(os.path.dirname(FINAL)) == "tools"
SRC = os.environ.get("BS_ADDENDUM_BASE") or os.path.join(HERE, "SPEC_2.0.before.json")
DST = os.environ.get("BS_SPEC_OUT") or os.path.join(FINAL, "SPEC_2.0.json")
REPO = os.environ.get("BS_REPO") or (os.path.dirname(os.path.dirname(FINAL)) if IN_REPO else "/home/user/Cosmoteer")
ART = os.path.join(REPO, "art3d")
TRANCO = os.path.normpath(os.path.join(FINAL, "..", "..", "railart", "tranco"))
DATE = "2026-10-21"
TAG = "ADDENDUM 2.0 (" + DATE + ")"
R1_COMMIT = "9fba772"          # commit da arte do refino r1 do tranco (base antiga, NAO serve mais de BASE)
GATE_ROUND = 2                 # o portao pede o spec_patch do refino r2 do tranco (ou mais novo)
ART_GATE_PATHS = ["art3d", "tools/blender", "tools/check_art3d.py", "docs/preview/3d/v2"]
RAIL_ART_PATHS = ["art3d/bs_rail_loader", "art3d/bs_rail_barrel", "art3d/bs_rail_muzzle", "tools/blender/parts/bs_rail.py"]


def _patch_path():
    """spec_patch do tranco: BS_TRANCO_PATCH > copia no repo (tools/spec/addendum/spec_patch_tranco.json) >
    railart/tranco/spec_patch.json (scratchpad)."""
    for p in (os.environ.get("BS_TRANCO_PATCH"), os.path.join(HERE, "spec_patch_tranco.json"),
              os.path.join(TRANCO, "spec_patch.json")):
        if p and os.path.isfile(p):
            return os.path.abspath(p)
    raise SystemExit("spec_patch do tranco nao encontrado (BS_TRANCO_PATCH, spec_patch_tranco.json ou railart/tranco)")


with open(SRC, encoding="utf-8") as fh:
    S = json.load(fh)
# historico 3x4 da Tupa ANTES do spec_patch (o ops_balance_derived sobrescreve 'tiles')
TILES_3X4 = {r["canos"]: r["tiles"] for r in S["railgun"]["scaling_table"]}
PATCH_PATH = _patch_path()
with open(PATCH_PATH, encoding="utf-8") as fh:
    _raw = fh.read()
PATCH = json.loads(_raw)
_m = re.search(r"tranco-r(\d+)", PATCH.get("meta", {}).get("round", ""))
PATCH_ROUND_N = int(_m.group(1)) if _m else 0
PATCH_INFO = {"path": PATCH_PATH, "round": PATCH.get("meta", {}).get("round", "?"), "round_n": PATCH_ROUND_N,
              "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(PATCH_PATH))),
              "sha256_12": hashlib.sha256(_raw.encode("utf-8")).hexdigest()[:12],
              "rascunho": "spec_patch_try" in os.path.basename(PATCH_PATH)}
PATCH_LABEL = "spec_patch %s (%s%s)" % (PATCH_INFO["round"].split(" ")[0], PATCH_INFO["mtime"],
                                         ", RASCUNHO" if PATCH_INFO["rascunho"] else "")


def _git(*args, raw=False):
    try:
        r = subprocess.run(["git", "-C", REPO, "-c", "gc.auto=0"] + list(args), capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        return r.stdout if raw else r.stdout.strip()
    except Exception:  # noqa: BLE001 (git ausente: o portao fica 'desconhecido')
        return None


def repo_state():
    head = _git("log", "-1", "--format=%h %ad %s", "--date=format:%Y-%m-%d %H:%M")
    rail = _git("log", "-1", "--format=%h %ad %s", "--date=format:%Y-%m-%d %H:%M", "--", *RAIL_ART_PATHS)
    dirty = _git("status", "--porcelain", "--", *ART_GATE_PATHS, raw=True)
    dirty_list = [ln[3:] for ln in (dirty or "").splitlines() if ln.strip()]
    rail_hash = rail.split(" ")[0] if rail else None
    after_r1 = None
    if rail_hash:
        after_r1 = rail_hash != R1_COMMIT and _git("merge-base", "--is-ancestor", R1_COMMIT, rail_hash) is not None
    st = {"seen_at": time.strftime("%Y-%m-%d %H:%M"), "head": head, "ultimo_commit_arte_tupa": rail,
          "arte_tupa_depois_de_r1": bool(after_r1), "git_status_arte": dirty_list[:12],
          "git_status_arte_n": len(dirty_list), "spec_patch": PATCH_INFO}
    ok = (head is not None and PATCH_ROUND_N >= GATE_ROUND and not PATCH_INFO["rascunho"] and bool(after_r1)
          and not dirty_list)
    # criticas do job do tranco (so no scratchpad): crit_rN_* de uma rodada >= a do spec_patch = revisao ainda aberta
    crits = []
    if os.path.isdir(TRANCO):
        for dn in sorted(os.listdir(TRANCO)):
            mm = re.match(r"crit_r(\d+)_\d+$", dn)
            if mm and os.path.isdir(os.path.join(TRANCO, dn)):
                _mt = os.path.getmtime(os.path.join(TRANCO, dn))
                crits.append((int(mm.group(1)), dn, time.strftime("%H:%M", time.localtime(_mt)), _mt))
    st["criticas_tranco"] = ["%s (%s)" % (dn, t) for _, dn, t, _ in crits]
    # revisao aberta = criticas de rodada maior que a do spec_patch E nenhum commit da arte do Tupa depois delas (se a
    # revisao aprovar sem rodada nova, o commit de entrega fecha o portao normalmente)
    rail_ct = _git("log", "-1", "--format=%ct", "--", *RAIL_ART_PATHS)
    last_crit = max((c[3] for c in crits), default=0)
    crit_open = (bool(crits) and max(c[0] for c in crits) > PATCH_ROUND_N
                 and not (after_r1 and rail_ct and float(rail_ct) >= last_crit))
    ok = ok and not crit_open
    st["portao_tranco_r2"] = "SATISFEITO" if ok else "NAO SATISFEITO"
    falta = []
    if crit_open:
        falta.append("o job do tranco abriu outra revisao depois do spec_patch lido (%s): esperar o fim (pode vir um spec_patch "
                     "e uma arte de rodada nova; o portao aceita a rodada mais nova)" % ", ".join(st["criticas_tranco"][-2:]))
    if PATCH_ROUND_N < GATE_ROUND or PATCH_INFO["rascunho"]:
        falta.append("spec_patch.json FINAL da rodada tranco-r2 (o lido e %s)" % PATCH_LABEL)
    if not after_r1:
        falta.append("commit da arte r2 do Tupa depois de %s (ultimo commit que toca art3d/bs_rail_* ou bs_rail.py: %s)"
                     % (R1_COMMIT, rail))
    if dirty_list:
        falta.append("git status das pastas de arte limpo (%d caminhos sujos, ex.: %s)" % (len(dirty_list), ", ".join(dirty_list[:3])))
    st["falta"] = falta
    st["base"] = (rail_hash if ok else None)
    return st


REPO_STATE = repo_state()


def _jp_apply(doc, op):
    parts = [x.replace("~1", "/").replace("~0", "~") for x in op["path"].lstrip("/").split("/")]
    cur = doc
    for k in parts[:-1]:
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    last = parts[-1]
    if isinstance(cur, list):
        if last == "-":
            cur.append(copy.deepcopy(op["value"]))
        elif op["op"] == "add":
            cur.insert(int(last), copy.deepcopy(op["value"]))
        else:
            cur[int(last)] = copy.deepcopy(op["value"])
    else:
        if op["op"] == "replace" and last not in cur:
            raise KeyError(op["path"])
        cur[last] = copy.deepcopy(op["value"])


# spec_patch do tranco (rodada lida de meta.round): ops RFC 6902 sobre o SPEC sem addendum + ops_balance_derived
# (opcao A_keep). NAO aplica ops_on_current_spec (sao para quem NAO roda este script: as mesmas mudancas ja estao em
# 'ops' a partir do r2) nem ops_balance_option_B/_C (recomendacao r2 do job de arte; decisao do dono do balanco:
# registrada em railgun.balance_recommendation_r2 e nos riscos do addendum, nao adotada neste build).
for _op in PATCH["ops"] + PATCH["ops_balance_derived"]:
    _jp_apply(S, _op)


def meta(d):
    p = os.path.join(ART, d, "meta.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def nfiles(d):
    p = os.path.join(ART, d)
    return len([f for f in os.listdir(p) if f != "meta.json"]) if os.path.isdir(p) else 0


# ---------------------------------------------------------------------------------------------
# 1) Nomes: PEM pesada = Corisco (overclock Relampago). Renomeia o resto do spec (menos o historico).
# ---------------------------------------------------------------------------------------------
SKIP_TOP = {"reconciliation", "revision_r1", "revision_r2", "revision_r3", "revision_r4", "status_r3", "status_r4"}
SKIP_PATHS = {("switches", "pem", "heavy_name"), ("pem_weapons", "weapons", 2, "name_reason")}


def rename(o, path=()):
    if path[:1] and path[0] in SKIP_TOP:
        return o
    for sp in SKIP_PATHS:
        if path[:len(sp)] == sp:
            return o
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            nk = k.replace("Mãe-do-Ouro", "Corisco").replace("Mae-do-Ouro", "Corisco") if isinstance(k, str) else k
            out[nk] = rename(v, path + (k,))
        return out
    if isinstance(o, list):
        return [rename(v, path + (i,)) for i, v in enumerate(o)]
    if isinstance(o, str):
        # o overclock da pesada era 'Corisco': passa a 'Relampago' ANTES de renomear a arma
        o = o.replace("overclock 'Corisco'", "overclock 'Relâmpago'")
        return o.replace("Mãe-do-Ouro", "Corisco").replace("Mae-do-Ouro", "Corisco")
    return o


for k in list(S.keys()):
    S[k] = rename(S[k], (k,))

pw = S["pem_weapons"]
heavy = pw["weapons"][2]
assert heavy["id"] == "rafaeltessaro.bs_pem_heavy"
heavy["codename"] = "Corisco"
heavy["name_reason"] = ("Corisco (raio): resposta 1 do usuario em " + DATE + " ('PEM pesada = Corisco, overclock "
                        "Relampago'). Historico: o projeto propunha 'Mãe-do-Ouro' com overclock 'Corisco'.")
heavy["overclock"]["name_ptbr"] = "Relâmpago"
heavy["overclock"]["name_en"] = "Lightning"
pw["family_names"]["heavy"] = "Corisco (resposta 1 do usuario, " + DATE + "; overclock 'Relâmpago')"
pw["family_names"]["heavy_alternative"] = "descartado: 'Mãe-do-Ouro' (nome antigo do projeto)"
for t in S["career_techs"]:
    if t.get("id") == "rafaeltessaro.bs_pem_heavy-overclock":
        t["note"] = "'Relâmpago' (overclock do Corisco)"

# ---------------------------------------------------------------------------------------------
# 2) Tuvira vira TORRE (270 graus, cadencia x0,6 = 4320 escudo/s), CP 2 (sem resposta -> safe)
# ---------------------------------------------------------------------------------------------
tuv = pw["weapons"][0]
assert tuv["id"] == "rafaeltessaro.bs_pem_light"
tuv["mount"] = ("TORRE 270 graus (pem.tuvira_mount = torre, resposta 1 do usuario em " + DATE + "): TurretWeapon "
                "FiringArc 270d, RotateSpeed 180d, cadencia x0,6; arte art3d/bs_pem_light ja e torre (pivo [0.5, 0.5], "
                "2 canos sincronizados). Historico: 'fixed bow gimbal 30d'.")
tuv["firing_arc_deg"] = 270
# nomes de canhao FIXO de proa -> nomes de torre (vao para strings/tooltips; mesmo padrao do Treme-Treme/Corisco)
tuv["name_historico_fixa"] = {"name_ptbr": tuv["name_ptbr"], "name_en": tuv["name_en"]}
tuv["name_ptbr"] = "Canhão PEM Leve"
tuv["name_en"] = "Light EMP Cannon"
tuv["name_addendum"] = ("ADDENDUM: era 'Canhão PEM Leve de Proa' / 'Light EMP Bow Gun' (canhao fixo de proa); com a "
                        "torre de 270 graus (resposta 1) o nome segue o do Treme-Treme ('Canhão PEM Médio' / 'EMP Cannon') e "
                        "do Corisco ('Canhão PEM Pesado' / 'Heavy EMP Cannon'). Nenhum 'Proa'/'Bow' em strings/tooltips.")
tuv["mount_fixa_historico"] = {"firing_arc_deg": 30, "trigger_interval_s": 0.8333, "fire_rate_shots_per_s": 2.4,
                               "shp_per_s": 7200, "MaxResources": 36, "ResupplyThreshold": 18,
                               "name_ptbr": "Canhão PEM Leve de Proa", "name_en": "Light EMP Bow Gun",
                               "vs_sw": copy.deepcopy(tuv.get("vs_sw")), "ladder_note": tuv.get("ladder_note")}
# 2 tiros por gatilho a 1,44 tiro/s = 0,72 gatilho/s -> 1/0,72 = 25/18 = 1,38889 s (o mesmo de torre_numbers e do WP08)
tuv["trigger_interval_s"] = round(25 / 18, 4)
assert tuv["trigger_interval_s"] == 1.3889
tuv["fire_rate_shots_per_s"] = 1.44
tuv["internal_storage"]["MaxResources"] = 22
tuv["internal_storage"]["ResupplyThreshold"] = 11
tuv["internal_storage"]["seconds"] = 61.1
tuv["internal_storage"]["rule"] = "60 s de tiro continuo (binding): 0,36 celula/s x 61,1 s = 22 celulas (torre)"
c = tuv["computed"]
c.update({"shots_per_s": 1.44, "shp_per_s": 4320, "shp_per_s_per_tile": 2160, "shp_per_s_per_cp": 2160,
          "hull_dps": 216, "part_drain_per_s": 1080, "cells_per_s": 0.36, "internal_stock_cells": 22,
          "internal_stock_s": 61.1, "resupply_threshold_cells": 11, "f3_parts_sustained": 0.324,
          "f3_tiles_sustained": 2.92, "factory_battery_per_s": 180})
c["vs_sw"] = {"anchor": "SW Dual Mounted Ion Cannon CE (SW.DualFighterGun, FIXA 15 graus)", "shp_per_s": 0.672,
              "alpha": 1.333, "range": 1.086, "hull": 0.302, "per_cp": 0.672, "in_band_1_10_1_25": False,
              "why_ok": "escolha do usuario: torre 270 graus contra uma ancora fixa de 15 graus; o arco paga a cadencia "
                        "(spec: 'abaixo do Treme-Treme' por arma: 4320 x 6250 escudo/s)"}
tuv["torre_numbers_" + DATE] = {"FiringArc": "270d", "RotateSpeed": "180d", "trigger_interval_s": 1.3889,
                                "shots_per_trigger": 2, "fire_rate_shots_per_s": 1.44, "shp_per_s": 4320,
                                "MagStorage_0": 22, "ResupplyThreshold": 11, "CommandPoints": 2,
                                "applied_by": "WP01 bs_data transformacao (d2) com pem.tuvira_mount = torre; o WP08 recebe pronto"}
pw["ladder_note"] = ("ADDENDUM: Tuvira TORRE (resposta 1): 4320 escudo/s (2 CP = 2160 por CP), Treme-Treme 6250 (5 CP = 1250), "
                     "Corisco 17476 (10 CP = 1748). A Tuvira ficou abaixo do Treme-Treme por arma e acima por CP/tile "
                     "(peca de 2 tiles e 2 CP); pem.tuvira_cp sem resposta -> 2 (safe). Historico J1R2-LOW: escada "
                     "invertida por CP com a Tuvira fixa (3600/CP).")
# o vs_sw e o ladder_note DA PROPRIA Tuvira ainda eram os da peca fixa (1,12x na banda; 3600 por CP)
tuv["vs_sw"] = copy.deepcopy(c["vs_sw"])
tuv["vs_sw"]["note"] = ("ADDENDUM: = computed.vs_sw (torre). Historico fixa (mount_fixa_historico.vs_sw): shp 1,12x, hull "
                        "0,504, por CP 1,12x, dentro da banda 1,10-1,25.")
tuv["ladder_note"] = ("ADDENDUM (torre): 4320 escudo/s = 2160 por CP (2 CP) e por tile; Treme-Treme 1250/CP (5 CP), Corisco "
                      "1748/CP (10 CP): 3 Tuviras (6 CP, 12960/s) ainda drenam mais por CP que 1 Corisco (17476/s, 10 CP), "
                      "mas a escada por ARMA fica Tuvira < Treme-Treme < Corisco. pem.tuvira_cp = 4 levaria a 1080/CP. "
                      "Historico J1R2-LOW (fixa): 3600 por CP (mount_fixa_historico.ladder_note).")
tcp = S["switches"]["pem"]["tuvira_cp"]
tcp["values_historico_fixa"] = copy.deepcopy(tcp["values"])
tcp["values"]["2"] = ("ancora SW (DualFighterGun 1x1, 2 CP); com a TORRE (pem.tuvira_mount = torre): 4320 escudo/s = 2160 por "
                      "ponto de comando (fixa: 3600)")
tcp["values"]["4"] = "1080 por CP com a torre (fixa: 1800), abaixo do Corisco (1748): a escada PEM fica Tuvira <= Corisco por CP"
pv_parts = pw["visuals"]["parts"]
pv_parts["light_historico_fixa"] = pv_parts["light"]
pv_parts["light"] = ("Tuvira: TORRE 1x2 de 270 graus (anel giratorio no tile da frente, batentes a +-135 graus), dois canos "
                     "curtos sincronizados com bobinas de cobre, brilho azul dos capacitores na culatra, tremonha de celulas "
                     "atras (art3d/bs_pem_light: pivo [0.5, 0.5], turret_size 1.0)")
ttb = pw["time_to_break_s_no_refill"]["Tuvira"]
pw["time_to_break_s_no_refill"]["Tuvira_historico_fixa"] = copy.deepcopy(ttb)
for _k, _hp in (("SW small 5000", 5000), ("SW medium 20000", 20000), ("SW large 80000", 80000),
                ("SW giga 320000", 320000), ("vanilla small 15000", 15000), ("vanilla large 45000", 45000)):
    ttb[_k] = round(_hp / 4320, 1)
pw["time_to_break_s_no_refill"]["note_addendum"] = "Tuvira = torre (4320 escudo/s); historico da fixa (7200/s) em Tuvira_historico_fixa"
for _b in S["balance_checks"]:
    if _b.get("id") == "STOCK-Tuvira":
        _b["text_historico_fixa"] = _b["text"]
        _b["text"] = "Tuvira (torre): 22 celulas = 61.1 s (alvo 60 s; 0,36 celula/s)"
    elif _b.get("id") == "BAND-Tuvira":
        _b["text_historico_fixa"] = _b["text"]
        _b["status"] = "ACEITO (escolha do usuario)"
        _b["text"] = ("Tuvira (torre 270 graus): escudo x0.672 vs ion SW fixo de 15 graus (fora da banda 1,10-1,25 por "
                      "escolha do usuario: o arco paga a cadencia)")
_bn = S["balance"].get("notes", [])
for _i, _n in enumerate(_bn):
    if isinstance(_n, str) and _n.startswith("Escada PEM por CP invertida (Tuvira 3600"):
        _bn[_i] = ("Escada PEM por CP (ADDENDUM, Tuvira torre): Tuvira 2160, Treme-Treme 1250, Corisco 1748 escudo/s por CP "
                   "(fixa: 3600); pem.tuvira_cp = 2 (sem pedido do usuario). Historico: '" + _n + "'")
S["balance"].setdefault("notes", []).append(
    "ADDENDUM " + DATE + ": Tuvira torre 270 graus (4320 escudo/s, 0,67x a ancora SW fixa de 15 graus, escolha do usuario); "
    "PEM pesada = Corisco (overclock Relampago); vizinhanca das fabricas LIGADA (intervalos x1,5: com 2 vizinhas o custo "
    "volta ao da tabela); Tupa com carregador 5x5 (+13 tiles: DPS por tile 181..157, o tamanho e a energia balanceiam).")

# ---------------------------------------------------------------------------------------------
# 3) Switches: respostas do usuario, valores do build de teste, switches novos do tranco
# ---------------------------------------------------------------------------------------------
SW = S["switches"]
lg, rl, pm, ec, ar, bl = SW["logistics"], SW["rail"], SW["pem"], SW["econ"], SW["art"], SW["balance"]


def answered(sw, value, by):
    sw["answered_addendum"] = {"value": value, "by": by, "date": DATE}


lg["transport"]["build_2_0_teste"] = {
    "fita": "teleporte", "semfita": "tripulacao",
    "why": ("Pedido do usuario 'quando terminar tudo monte o MoD e me forneca um checklist' ANTES das respostas do "
            "TesteFita: o build principal (BulletStrike/) usa o teletransporte com a reserva de tripulacao e as pernas "
            "PUSH com precedente vivo no SW:ACD (fita_fabrica B + fita_arma empurra); o build reserva "
            "testes/BulletStrike_SemFita usa o safe 'tripulacao'. A 2.0.0 continua presa no portao (tests.release_gate): "
            "este e um build de TESTE com Version 2.0.0; as respostas do CHECKLIST_2_0 secao 2 substituem o TesteFita.")}
answered(lg["transport"], "teleporte", "orquestrador, a pedido do usuario ('monte o MoD'); safe 'tripulacao' = build SemFita")

lg["fita_fabrica"]["default"] = "B"
lg["fita_fabrica"]["safe"] = "B"
lg["fita_fabrica"]["addendum"] = ("default/safe A -> B: o empurrao da fabrica pelo proprio GridBuffProvider "
                                  "BulletStrike_FitaFab + OutgoingBuffProviders tem precedente VIVO no SW:ACD 0.30.4 "
                                  "(hypermatter_reactor_2x2.rules:256-292); o jeito A (IncomingBuffTypes) so tem o "
                                  "vanilla thruster_small. A continua implementado (A3 do TesteFita/checklist 2.x).")
lg["fita_arma"]["build_2_0_teste"] = "empurra (OutgoingBuffProviders do paiol, precedente vanilla engine_room + SW)"
lg["reserva_tripulacao"]["build_2_0_teste"] = "metade (a tripulacao continua levando municao abaixo da metade)"
lg["devolucao_arma"]["build_2_0_teste"] = "off (safe; T-DEVOL fica para o build seguinte: o modo nao escolhido guarda a sobra)"
lg["paiol_contador"]["build_2_0_teste"] = False
lg["paiol_contador"]["addendum"] = ("DESLIGADO por decisao (orquestrador): so barra (ProgressBar) + medidor do teto. O WP05 NAO "
                                    "precisa implementar Contador_<k> nesta versao; os digitos (art3d/bs_paiol digito0..9) nao "
                                    "sao publicados; a janela de digitos pintada no teto 2x2/3x3 fica escura (decorativa).")
lg["fita_embutida"]["build_2_0_teste"] = "off (implementacao do botao pode ficar para depois)"
lg["fita_alcance"]["build_2_0_teste"] = 1000
lg["acoplamento"]["build_2_0_teste"] = "auto (build fita: sem acoplamento; build SemFita: ligado)"

ar["fita_luz"]["safe"] = "ack"
ar["fita_luz"]["addendum"] = ("safe 'sempre' -> 'ack': o aviso de volta e o MESMO mecanismo do elo (AreaBuffProvider + "
                              "BuffToggle, cadeia vanilla do railgun); se falhar e benigno (so a luz nao acende) e com "
                              "'sempre' a luz mentiria, e ela e o primeiro diagnostico do checklist (secao 2).")

rl["enabled"]["build_2_0_teste"] = True
answered(rl["enabled"], True, "usuario: DECISAO FINAL da Tupa ('deixa ela FIXA mesmo, so coloque o efeito de TRANCO') + 'monte o MoD'")
rl["power_mode"]["safe"] = "B"
rl["power_mode"]["build_2_0_teste"] = "B"
rl["power_mode"]["addendum"] = ("safe fixo -> B ('Cano B'): o carregador drena N x 500 da PROPRIA bateria pelo buff de "
                                "contagem (100 % padroes vanilla + 1 buff proprio); mais canos = mais energia por tiro "
                                "(pedido do usuario). 'fixo' continua como emergencia; 'A' (ResourceChange num proxy, nao "
                                "verificado) NAO precisa ser implementado.")
rl["charge_wave"]["build_2_0_teste"] = "atraso"
rl["loader_intake"]["build_2_0_teste"] = "auto (fita: FitaEntra_slug -> SlugMagazine; SemFita: acoplamento [0,5] + tripulacao)"
answered(rl["loader_intake"], "auto", "segue o transporte decidido para o build (teleporte -> fita; SemFita -> acoplamento + tripulacao)")
rl["tranco_impulso"] = {
    "default": "impulso", "safe": "impulso", "values": {
        "impulso": "TriggeredEffects TrancoImpulso na Ponta: UM Impulse por tiro, {BaseValue 2400; BuffType BulletStrike_RailShot; BuffMode Multiply} = 3000 (N=1) .. 5152 (N=6) (vanilla railgun_launcher.rules:540-552 usa Impulse buffavel; verificado 0.30.3/0.30.5)",
        "recoil": "Recoil = 4000 fixo no BulletEmitter (EmitterRules.Recoil, numero; as armas BS ja usam 0..400)",
        "off": "sem empurrao fisico (so quadros + tremor + anel)"},
    "decided_by": "T-TR-1 (checklist 8): a nave anda para TRAS a cada tiro; para a frente -> Rotation -90d; nada -> recoil",
    "never": "NUNCA o timer vanilla de 1/30 s (RecoilProjectile + Timer: 8-24 empurroes = 24000-72000 por tiro com o dardo lento) e nunca ChainedTo o Projectile (Interpolate = true: desync)",
    "env": "BS_SWITCHES='rail.tranco_impulso=recoil'"}
rl["tranco_gatilho"] = {
    "default": "relay", "safe": "relay", "values": {
        "relay": "cada peca reinicia a animacao do tranco por um Timer local TrancoRelay {StartTrigger = <TriggerProxy do tiro>; Duration 0.5; TriggerWhenStarted true} (Timer como gatilho: vanilla factory_diamond.rules:272; TriggerWhenStarted: railgun_launcher.rules:522-530) - tudo verificado",
        "proxy": "ResetAnimationTrigger = o TriggerProxy de outra peca direto (inferido, sem exemplo vanilla)"},
    "decided_by": "T-TR-3 (checklist 8)", "env": "BS_SWITCHES='rail.tranco_gatilho=proxy'"}
rl["recoil_com"] = {
    "default": False, "safe": False,
    "values": {"false": "como o vanilla: Tupa fora do centro gira a nave um pouco", "true": "ApplyToCenterOfMass = true: so empurra"},
    "decided_by": "T-TR-2 (checklist 8)", "env": "BS_SWITCHES='rail.recoil_com=true'"}

pm["heavy_name"]["default"] = "Corisco"
answered(pm["heavy_name"], "Corisco", "usuario, resposta 1 (overclock 'Relâmpago')")
pm["tuvira_mount"]["default"] = "torre"
answered(pm["tuvira_mount"], "torre", "usuario, resposta 1 (270 graus, 4320 escudo/s)")
pm["tuvira_cp"]["addendum"] = "sem pedido do usuario -> 2 (safe); com torre: 2160 escudo/s por CP"
ec["factory_adjacency"]["default"] = "vanilla"
answered(ec["factory_adjacency"], "vanilla", "usuario, resposta 2 (+25 % como no jogo base; intervalos x1,5)")
ec["factory_adjacency"]["final_intervals_s"] = {
    "rule": "intervalo = interval_s_base x 1,5 / (1 + 0,25 x vizinhas) (Factory: BaseValue 100 %, CombineMode Add, Divide; vanilla buffs.rules:31 + factory_ammo.rules:175-180); overclock x3 por cima",
    "F1 he": [1.875, 1.5, 1.25], "F2 ap": [0.9375, 0.75, 0.625], "F2 sap": [0.78, 0.624, 0.52], "F2 ac (4x)": [2.5, 2.0, 1.6667],
    "F2 frag": [0.78, 0.624, 0.52], "F3 plasma": [3.0, 2.4, 2.0], "F3 pem": [1.35, 1.08, 0.9],
    "F4 msl_he (x2)": [0.45, 0.36, 0.3], "F4 msl_cluster (x2)": [0.54, 0.432, 0.36], "F4 msl_emp": [0.54, 0.432, 0.36],
    "F5 msl_nuke": [4.5, 3.6, 3.0], "F6 slug": [4.5, 3.6, 3.0],
    "columns": "[sozinha, 1 vizinha, 2 vizinhas]"}
answered(bl["perfil_extra"], False, "usuario, resposta 3 (perfil jogo base separado: NAO)")
for k in ("small_rounds_targetable", "defesa_antilaser", "ac_cost"):
    SW["guns"][k]["addendum"] = "usuario: 'outras escolhas sem pedido de mudanca' -> safe"
SW["missiles"]["iara_hp"]["addendum"] = "usuario: 'Iara 12.000 HP' -> safe 12000"
SW["safe_rule_addendum"] = ("ADDENDUM: valor gravado em bullet_strike_switches.json valido = 'safe' do switch OU "
                            "switches.*.answered_addendum.value OU o valor de SPEC.build_2_0.switch_values_fita "
                            "(decisao de build). O spec2_check (WP01) aceita os tres.")

# ---------------------------------------------------------------------------------------------
# 4) Railgun Tupa: carregador 5x5, encadeamento, tranco, Cano B, paleta azul, passa sobre a propria nave
# ---------------------------------------------------------------------------------------------
R = S["railgun"]
car, cano, ponta = R["parts"]["carregador"], R["parts"]["cano"], R["parts"]["ponta"]
ops = {o["path"]: o for o in PATCH["ops"]}


def pv(path):
    return copy.deepcopy(ops[path]["value"])


car["size_historico"] = [3, 4]
car["size"] = [5, 5]
car["tiles"] = 25
car["max_health"] = 33000
car["max_health_note"] = ("ADDENDUM: 20000 (12 tiles) -> 33000 (25 tiles, 1320 por tile; spec_patch.balance.loader_health): o "
                          "miolo continua denso; cano/ponta 2000 por tile. Custo (24000 cr) mantido: 'o tamanho e a energia balanceiam'.")
car["layout_unrotated"] = pv("/railgun/parts/carregador/layout_unrotated")
car["doors"] = pv("/railgun/parts/carregador/doors")
car["chains_start"] = pv("/railgun/parts/carregador/chains_start")
car["geometry_5x5"] = pv("/railgun/parts/carregador/geometry_5x5")
car["storages"]["LoaderBattery"]["MaxResources"] = 15000
car["storages"]["BatteryConsumer"]["ResupplyThreshold"] = 7500
car["storages"]["capacitores_addendum"] = ("'mais estoque/capacitores' (USER_NOTES): bateria 10000 -> 15000 (3 tiros com 6 canos, "
                                           "6 com 1); SlugMagazine 12 (12 capsulas da arte = 6 niveis x 2) + 1 na camara = 13 tiros = 78 s")
car["belt_intake"]["ports"] = pv("/railgun/parts/carregador/belt_intake/ports")
car["belt_intake"]["fallback_adjacency_historico"] = car["belt_intake"]["fallback_adjacency"]
# texto inteiro para o 5x5 (o .replace antigo deixava 'the rear-middle door [1,4] stays free', frase do 3x4)
car["belt_intake"]["fallback_adjacency"] = (
    "switch logistics.acoplamento no Carregador 5x5: PaiolAcoplado_0 = ResourceStorageProxy ResourceType "
    "rafaeltessaro.bs_slug_rail, PartLocation [0,5] (a celula logo ATRAS do canto de tras-esquerdo), PartCriteria "
    "{ Category = bs_paiol_slug } (R2: categoria do tipo), ComponentID = Estoque_slug (o estoque do paiol) + "
    "AlimentadorAcoplado_0 ResourceConverter -> SlugMagazine 1 por 0,1 s: um paiol de projeteis encostado atras do "
    "carregador o alimenta sem tripulacao (padrao AmmoProxy vanilla RAIL303/railgun_launcher.rules:220-235). PORTAS do "
    "5x5 = AllowedDoorLocations [[-1,1],[5,1],[1,5],[3,5]] (o meio de tras [2,5] e a coluna do paiol interno, nao porta). "
    "Paiol 1x1 em [0,5]: as duas portas de tras [1,5] e [3,5] ficam livres. Paiol 2x2/3x3: a celula [0,5] tem de ser a "
    "coluna da DIREITA dele (crescendo para a esquerda, x <= 0): assim [1,5] fica livre; se ele crescer para a direita "
    "(cobrindo x = 1) a porta [1,5] fica tampada e a tripulacao entra por [3,5] ou pelos lados [-1,1]/[5,1] (funciona, "
    "so nao tampar [3,5] tambem). Sem acoplamento (build com fita): nada em [0,5] e preciso.")
S["switches"]["rail"]["loader_intake"]["values"]["acoplamento"] = (
    "paiol de projeteis encostado atras do canto de tras-esquerdo do Carregador 5x5 (ResourceStorageProxy PartLocation "
    "[0,5]; era [0,4] no 3x4); portas de tras [1,5]/[3,5] livres com paiol 1x1 (2x2/3x3: crescer para a esquerda)")
car["crew_pos"] = [[1.5, 2.0], [3.5, 2.0]]
car["drain_b"] = ("DrenoB {Type = ResourceChange; Trigger = EmitTrigger; ResourceStorage = LoaderBattery; Amount {BaseValue = 0; "
                  "Modifiers [{Type = ScaledBuff; BuffType = BulletStrike_RailCount; Scale = -500; ModificationMode = Add}]}} "
                  "(rail.power_mode = B; kit bs2t_rail_carregador.rules:349-368)")
car["fita_fx_location"] = [1.0, 3.5]
car["fita_fx_note"] = "coluna da esquerda (capacitores), fora da janela do paiol (x 2-3, y 2.7-4.78) e da culatra; ajuste fino na previa"
R["belt"]["ports"] = pv("/railgun/belt/ports")
R["logistica"]["teleporte"]["host"]["AvisaFitaHorizontal"]["BuffArea"] = [-1, 0, 7, 5]
R["logistica"]["teleporte"]["host"]["AvisaFitaVertical"]["BuffArea"] = [0, -1, 5, 7]
R["logistica"]["teleporte"]["anim"]["AnimEntrando"] = R["logistica"]["teleporte"]["anim"]["AnimEntrando"].replace(
    "Location [1.5, 2]", "Location [1.0, 3.5]")
for k in list(R["logistica"].keys()):
    if k.startswith("acoplamento"):
        R["logistica"][k]["cell"] = [0, 5]
        for pm_ in R["logistica"][k]["per_mode"]:
            pm_["PaiolAcoplado_0"]["PartLocation"] = [0, 5]
cano["proxies"] = pv("/railgun/parts/cano/proxies")
cano["loader_5x5_links"] = pv("/railgun/parts/cano/loader_5x5_links")
ponta["weapon"]["IgnoreSourceShipLOSChecks"] = True
ponta["weapon"]["IgnoreSourceShipLowLOSChecks"] = True
ponta["weapon"]["own_ship_note"] = ("o dardo passa POR CIMA da propria nave sem dano (pedido do usuario, como o SH-TT do SW): "
                                   "IgnoreSourceShipLOSChecks/IgnoreSourceShipLowLOSChecks = true na arma (SW turbolaser_huge01.rules:73 "
                                   "e Fixed_Light_Laser_Cannon/fixedlaser.rules:671-672, vivos no 0.30.4; em FixedWeapon: inferido, "
                                   "WeaponRules) + shots.OWN_SHIP_PASS no Hit do tiro (FriendlyShipLow/HighCollisions false)")
R["shot"]["own_ship_pass"] = "shots.OWN_SHIP_PASS (FriendlyShipLowCollisions = false; FriendlyShipHighCollisions = false) no PenetratingHit"
R["shot"]["Targetable"]["OnDeath"] = "rail_intercepted (pequeno estouro AZUL), nao o impacto cheio"
pen_op = R["shot"]["Hit"]["PenetratingOperational"]["HitEffects"][1]
pen_op["MediaEffectsOnDrain"] = "um chiado azul (rail palette)"
R["shot"]["IMPACT"]["EmpBurst"]["MediaEffectsOnDrain"] = "missile_emp_hit_sizzle + missile_emp_lightning (copias AZUIS)"
R["firing_timeline"]["sequence"][4] = pv("/railgun/firing_timeline/sequence/4")
R["power"]["decision_addendum"] = ("rail.power_mode = B ('Cano B'): energia por tiro = POWER_BASE 2000 (BatteryProxy da Ponta) + "
                                   "500 x N (DrenoB do carregador) = 2500 / 3000 / 3500 / 4000 / 4500 / 5000 para N = 1..6; tudo "
                                   "da LoaderBattery (15000). A variante A nao e implementada; 'fixo' fica como emergencia.")
R["power"]["battery"] = "LoaderBattery MaxResources 15000 (3 tiros com 6 canos), ResupplyThreshold 7500; a tripulacao so leva bateria ao carregador"
# variante B com o carregador 5x5: o ContagemProvider do cano precisa das DUAS entradas de Criteria (como os proxies e o
# ReverseBuffOperationProvider, railgun.parts.cano.loader_5x5_links); com so {bs_rail_municao; Top 3} o 1o cano nunca
# reconhece o carregador centrado -> sem contagem e sem RailReverseOperation (carregador desligado para sempre)
vb = R["power"]["variants"]["B"]
vb["component_historico_3x4"] = vb["component"]
vb["component"] = (
    "Cano: ContagemProvider AreaBuffProvider BulletStrike_RailCount BuffAmount {1 + recebido} BuffArea [0,3,3,1] "
    "ChainsFromBuffType BulletStrike_RailCount Criterias [ {Category bs_rail_municao; Rot 0; Left 0; Right 3; Top 3} "
    "{IDs [rafaeltessaro.bs_rail_loader]; Rot 0; Left -1; Right 4; Top 3} ] (a 2a entrada = o carregador 5x5 centrado; "
    "IGUAL a railgun.parts.cano.loader_5x5_links e aos proxies do cano; forma de lista viva no SW chaingun_magazine.rules); "
    "Ponta: ContagemInicio BuffAmount 0 para [0,4] (so encaixa num cano: sem mudanca); Carregador: DrenoB { Type = "
    "ResourceChange; Trigger = EmitTrigger; ResourceStorage = LoaderBattery; Amount { BaseValue = 0; Modifiers [ { Type = "
    "ScaledBuff; BuffType = BulletStrike_RailCount; Scale = -500; ModificationMode = Add } ] } }")
vb["critico_5x5"] = ("sem a entrada {IDs [rafaeltessaro.bs_rail_loader]; Left -1; Right 4; Top 3} o carregador 5x5 nao recebe "
                     "RailCount (DrenoB = 0: tiro de graca) nem RailReverseOperation (fica desligado): spec2_check exige 2 "
                     "entradas em TODO Criterias/ProxyableComponents do cano")
R["internal_stock"]["battery_shots_buffered"] = "N=6: 3 tiros; N=4: 3,75; N=1: 6 (bateria 15000)"
tab = {t["canos"]: t for t in PATCH["balance"]["table"]}
for row in R["scaling_table"]:
    n = row["canos"]
    t = tab[n]
    # historico = o valor do SPEC ANTES do spec_patch (3x4: 33/42/51/60/69/78), nao o 'tiles' ja sobrescrito
    row["tiles_historico_3x4"] = TILES_3X4[n]
    assert row["tiles_historico_3x4"] == t.get("tiles_was", TILES_3X4[n]) == 24 + 9 * n, (n, TILES_3X4[n])
    row["tiles"] = t["tiles"]
    row["dps_per_tile"] = t["dps_per_tile"]
    row["vs_mapinguari_dps_per_tile"] = t["vs_mapinguari_dps_per_tile"]
    row["vs_sw_late_line_353_per_tile"] = t["vs_sw_late_line_353_per_tile"]
    row["impulse_per_shot"] = t["impulse_per_shot"]
    row["shake"] = "BASE_SHAKE 0.2 / 0.7 s (fixo)"
R["scaling_note_addendum"] = ("ADDENDUM: carregador 5x5 (+13 tiles: 25 + 9N + 12). DPS, dano por tiro, penetracao, alcance, "
                              "velocidade e energia por tiro NAO mudaram (opcao A_keep do spec_patch: 'o tamanho e a energia "
                              "balanceiam'); o DPS por tile cai para 181..157 (0,63-0,55x o Mapinguari; 0,51-0,45x a linha "
                              "tardia do SW). Mais canos = mais dano, alcance, penetracao, velocidade e energia (m(N) = 1 + 0,25 N^0,85).")
vis = R["visuals"]
vis["palette"] = ("AZUL ELETRICO (referencia do usuario, " + DATE + "): grafite + placas brancas grossas + canal azul "
                  "[45,115,255] / azul claro [100,175,255] / nucleo branco-azulado [205,228,255] + laranja-OURO [215,145,40] so "
                  "em detalhes pintados, molas [235,185,50]; NUNCA violeta, NUNCA cobre (cobre = familia PEM)")
vis["muzzle"] = pv("/railgun/visuals/muzzle")
vis["in_flight"] = ("arte art3d/bs_shells2 'slug' (dardo APFSDS 3,0 x 0,8 com colares EM azuis, ancora 'tip' [1.45, 0]; "
                    "luzes 4 quadros 12 fps) ALFA sobre casco branco + rastro AZUL (bs_rail_streak recolorido) + aneis EM azuis + "
                    "bullet_trail_railgun_ring_distortion vanilla; luzes = fxkit.light_pair: halo SO NO ESPACO (refl 0) cor glow/4 + "
                    "luz de casco [3.6, 1.2] VertexColor palette.rail.hull [20,82,255] refl 4; light_blob da Ponta {0.10, 0.32, 1.0}")
vis["end_of_path"] = vis["end_of_path"].replace("gold-white flash, violet lightning", "white-blue flash, BLUE lightning")
vis["shield_hit"] = "own rail_shield_hit: flash branco-azulado + chiado de sobrecarga (AZUL)"
vis["parts"] = {
    "carregador": "art3d/bs_rail_loader (5x5, layered; %d arquivos + meta no momento desta geracao): ver "
                  "art_assets.assets.railgun.carregador e railgun.tranco" % nfiles("bs_rail_loader"),
    "cano": "art3d/bs_rail_barrel (3x3; %d arquivos + meta nesta geracao)" % nfiles("bs_rail_barrel"),
    "ponta": "art3d/bs_rail_muzzle (3x4; %d arquivos + meta nesta geracao)" % nfiles("bs_rail_muzzle"),
    "contagem": "as contagens sao do disco na hora em que este script rodou (" + REPO_STATE["seen_at"] + "); a lista "
                "valida e a 'files' do meta.json de cada pasta NO BASE",
    "render": "tools/blender/parts/bs_rail.py + tools/blender/render_layered.py (ADOTADO)"}
tr = copy.deepcopy(PATCH["tranco"])
tr["status"] = ("APROVADO pelo usuario ('so coloque o efeito de TRANCO'; depois 'pra mim esta parado' -> refinos r1/r2: curso "
                "13 px = 0,203 tile em tudo, segurado 2 quadros, culatra 1 quadro depois da boca). Este bloco vem do "
                + PATCH_LABEL + " (" + PATCH_INFO["path"] + "). A arte valida e a do BASE (commit da arte r2 do Tupa: "
                "SPEC.status_addendum.portao_tranco_r2). Os VALORES DE ARTE (rects, cursos, quadros, nomes, contagens) vem "
                "SEMPRE de art3d/bs_rail_*/meta.json do BASE.")
tr["spec_patch"] = copy.deepcopy(PATCH_INFO)
tr["meta_wins"] = True
tr["switches"] = {"impulso": "rail.tranco_impulso", "gatilho": "rail.tranco_gatilho (padrao relay)", "centro_de_massa": "rail.recoil_com"}
tr["triggers_build"] = ("rail.tranco_gatilho = relay: TrancoRelay {Type = Timer; StartTrigger = EmitTrigger (carregador) / "
                        "EmissionTriggered (cano) / BulletEmitter (ponta: direto); Duration = 0.5; TriggerWhenStarted = true} e "
                        "ResetAnimationTrigger = TrancoRelay")
tr["shock_ring"]["color"] = "borda azul clara [100,175,255] -> nucleo branco-azulado [205,228,255], sem cobre"
tr["checklist"] = "CHECKLIST_2_0 secao 8 (T-TR-1..6, T-TR-A1/A2)"
R["tranco"] = tr
R["chain_offsets_5x5"] = copy.deepcopy(PATCH["chain_offsets_5x5"])
R["source_section_addendum"] = ("tranco_research.json (q1-q4) + " + PATCH_LABEL + " + USER_NOTES (carregador 5x5, "
                                "tranco, FIXA, passa sobre a propria nave, azul)")
_rec = (PATCH.get("balance") or {}).get("recommendation_r2")
if _rec:
    R["balance_recommendation_r2"] = {
        "from": PATCH_LABEL, "recommendation": copy.deepcopy(_rec),
        "status": ("NAO ADOTADA neste build: continua a opcao A_keep (FireInterval 6,0 s, custo 24000 cr; DPS por tile "
                   "181..157). As ops_balance_option_B/_C do spec_patch NAO sao aplicadas por este script; adotar B (+11 % "
                   "de DPS) e/ou C (30000 cr) e decisao do usuario/orquestrador (aparece nos riscos do addendum e no "
                   "CHECKLIST 10.4)")}
R["slug_and_logistics"]["paiol_projeteis"]["cookoff"] = R["slug_and_logistics"]["paiol_projeteis"]["cookoff"].replace(
    "violet-gold slug icon", "slug azul + ponta laranja (placa_slug.png)")

# ---------------------------------------------------------------------------------------------
# 5) Fabricas: vizinhanca LIGADA, pastas de arte, ritmo
# ---------------------------------------------------------------------------------------------
FDIR = {"F1": "bs_factory_mag_std", "F2": "bs_factory_special", "F3": "bs_factory_plasma", "F4": "bs_factory_missile",
        "F5": "bs_factory_warhead", "F6": "bs_factory_slug"}
RHY = {"F1": "HE 1,875 s sozinha · 1,5 s com 1 vizinha · 1,25 s com 2",
       "F2": "sozinha AP 0,94 · SAP 0,78 · AC 2,5 · FRAG 0,78 s (com 2 vizinhas 0,625 / 0,52 / 1,67 / 0,52 s)",
       "F3": "sozinha plasma 3,0 · PEM 1,35 s (com 2 vizinhas 2,0 / 0,9 s)",
       "F4": "sozinha HE 0,45 s x2 · submunição 0,54 s x2 · PEM 0,54 s (com 2 vizinhas 0,3 / 0,36 / 0,36 s)",
       "F5": "ogiva 4,5 s sozinha (3,0 s com 2 vizinhas)", "F6": "projétil 4,5 s sozinha (3,0 s com 2 vizinhas)"}
for f in S["factories"]:
    code = f["code"]
    m = meta(FDIR[code])
    f["art3d_dir"] = FDIR[code]
    f["art3d_status"] = ("PRONTO (adotado): art3d/%s, kind %s, size %s, %d quadros x %s s, meta id %s"
                         % (FDIR[code], m["kind"], m["size"], len(m["machine"]["frames"]), m["machine"]["interval"], m["id"]))
    if m.get("mode_plate"):
        f["mode_plate_art"] = m["mode_plate"]
    if m.get("overlays"):
        f["overlays_art"] = m["overlays"]
    ab = f["adjacency_buff"]
    # a chave antiga 'off (padrao e safe)' dizia que o padrao era off: o padrao agora e 'vanilla' (resposta 2)
    _new_ab = {}
    for _k, _v in ab.items():
        if _k == "off (padrao e safe)":
            _new_ab["padrao"] = "vanilla (resposta 2 do usuario, " + DATE + "; switches.econ.factory_adjacency.default)"
            _new_ab["off (safe; NAO e mais o padrao)"] = _v
        elif _k == "vanilla":
            _new_ab["vanilla (PADRAO desde o addendum)"] = _v
        else:
            _new_ab[_k] = _v
    _new_ab["chave_antiga"] = "'off (padrao e safe)' (antes da resposta 2: o padrao era off)"
    _new_ab["addendum"] = ("LIGADA (resposta 2 do usuario): o factory.py emite os 4 itens do jogo base "
                           "(ReceivableBuffs [Factory], modificadores BuffType Factory Divide nos intervalos, "
                           "GridBuffProvider Factory 25 % GridDistance 1, estatistica FactoryBuff); intervalos "
                           "base x1,5 (feito pelo WP01, transformacao c). 'off' continua implementado (safe do switch)")
    f["adjacency_buff"] = _new_ab
    f["rhythm_ptbr_addendum"] = RHY[code]
F2 = [f for f in S["factories"] if f["code"] == "F2"][0]
F2["art3d_note"] = ("arte 2.0 em art3d/bs_factory_special (meta id rafaeltessaro.bs_factory_mag_ap, 4x3): o bs_data le "
                    "factories[].art3d_dir; a pasta 1.x art3d/bs_factory_mag_ap (3x3) e tools/blender/parts/bs_factory_mag_ap.py "
                    "SAEM no WP12 (duas pastas nao podem reivindicar o mesmo id)")
F4 = [f for f in S["factories"] if f["code"] == "F4"][0]
F4["art3d_note"] = ("cor das saidas: o job 'Fabricas r2' alinha LEDs/pastilhas com as placas (bs_placas); se ainda divergir, "
                    "a PLACA manda (placa_msl_cluster laranja = palette.cluster.chip)")

# ---------------------------------------------------------------------------------------------
# 6) Paiol / Fita
# ---------------------------------------------------------------------------------------------
P = S["paiol"]
pm_meta = meta("bs_paiol")
P["art3d_dir"] = "bs_paiol"
P["published_dir"] = "bs_paiol_comum"
P["art3d_note"] = ("art3d/bs_paiol (meta shared: true, id rafaeltessaro.bs_paiol_comum, parts 1x1/2x2/3x3 com ids reais por "
                   "familia em parts.<n>.ids) -> publicado em parts/bs_paiol_comum/ (regras '../bs_paiol_comum/<arquivo>')")
P["fita_fx_location"] = {n: pm_meta["parts"][n]["fita_fx"] for n in ("1x1", "2x2", "3x3")}
P["plate_rect"] = {n: pm_meta["parts"][n]["plate"]["rect"] for n in ("1x1", "2x2", "3x3")}
P["gauge_rect"] = {n: pm_meta["parts"][n]["layers"]["gauge"]["rect"] for n in ("1x1", "2x2", "3x3")}
P["display"] = ("ADDENDUM: ProgressBar sob a barra de vida + medidor do teto (5/8/10 niveis) + placa do tipo. Contador de 4 "
                "digitos DESLIGADO (logistics.paiol_contador = false): nada de Contador_<k>/digitos nesta versao.")
FT = S["fita_teleporte"]
FT["build_2_0_teste"] = {"fita_fabrica": "B (GridBuffProvider BulletStrike_FitaFab + OutgoingBuffProviders; kit bs2f_fab_bala_b.rules)",
                         "fita_arma": "empurra (paiol Empurra_<k> -> ParaArmas_<k> OutgoingBuffProviders [Rede] -> FitaEntra_<k>)",
                         "reserva_tripulacao": "metade", "fita_luz": "ack", "fita_alcance": 1000, "devolucao_arma": "off",
                         "fita_embutida": "off"}
FT["buffs"]["BulletStrike_FitaFab"] = ("fita_fabrica = B (PADRAO desde o addendum): fabrica com fita -> navio (CombineMode Max; "
                                       "Rect [0,0,0,0]); o paiol tem ReceivableBuffs [FitaLink, FitaFab]")
FT["art"] = {
    "bs_fita": "art3d/bs_fita (1x1 layered): floor.png, roof.png + roof_normals.png, luz_grudada.png (lights_add, piso) + "
               "luz_grudada_teto.png (roof_doodads, alfa: as 4 lentes acesas por cima do teto) - as DUAS no OperationalToggle "
               "Grudada; icon.png 32x32 (EditorIcon [32,32]); blueprints.png 64x64; SEM walls (como heat_pipe_adaptive)",
    "bs_fita_fx": "art3d/bs_fita_fx: cartucho_sai/entra1..8 (roof_doodads) + brilho_sai/entra1..8 (lights_add), 8 x 0,075 s",
    "fx_location": {"fabricas": "centro da peca", "paiois": "SPEC.paiol.fita_fx_location (meta)",
                    "armas_e_lancadores_com_torre": "centro da fileira de TRAS [w/2, h - 0.5] (roof_doodads fica sob roof_turrets)",
                    "carregador_tupa": "[1.0, 3.5]", "size": "[1, 1] (paiol: o Size do meta)"}}

# ---------------------------------------------------------------------------------------------
# 7) Recursos, armas, defesas, lancadores: mapa de pastas de arte
# ---------------------------------------------------------------------------------------------
for r in S["resources"]:
    short = r["id"].split(".", 1)[1]
    m = meta(short)
    r["art"]["art3d_dir"] = short
    r["art"]["art3d"] = ("PRONTO (adotado): art3d/%s, stack %s, %d arquivos (stack_1..N, icon, overlay, nugget + normals)"
                         % (short, m["stack"], len(m["files"])))
    assert m["stack"] == r["max_stack_size"], (short, m["stack"], r["max_stack_size"])
for w in S["weapons"]:
    w.setdefault("art3d_dir", w["id"].split(".", 1)[1])
    if not w.get("art3d_dir"):
        w["art3d_dir"] = w["id"].split(".", 1)[1]
for d in S["defenses"]:
    d.setdefault("art3d_dir", d["id"].split(".", 1)[1])
for L in S["launchers"]:
    L.setdefault("art3d_dir", L["id"].split(".", 1)[1])
    L["art3d_note"] = ("arte 1.x mantida (turret); WP13: re-render --only cells com cluster8 (Caipora) / heavy8 (Mula) e "
                       "apagar cells_napalm/limpet/torpedo")
for w, d in zip(pw["weapons"], ("bs_pem_light", "bs_pem_medium", "bs_pem_heavy")):
    w["art3d_dir"] = d
    m = meta(d)
    w["art3d_status"] = "PRONTO (adotado): art3d/%s kind %s size %s pivot %s" % (d, m["kind"], m["size"], m["pivot"])

# ---------------------------------------------------------------------------------------------
# 8) art_assets: paleta, luzes, canvases, dono das pastas, base, previas
# ---------------------------------------------------------------------------------------------
A = S["art_assets"]
pal = A["palette"]
pal["rail"] = {"blue": [45, 115, 255], "glow": [100, 175, 255], "core": [205, 228, 255], "hull": [20, 82, 255],
               "hull_refl": 4, "light_blob_vertexcolor_float": [0.10, 0.32, 1.0], "chip": [64, 128, 255],
               "chip_tip": [255, 140, 40], "accent_orange_gold": [215, 145, 40], "springs": [235, 185, 50],
               "note": ("ADDENDUM: AZUL ELETRICO (referencia do usuario); violeta/ouro REMOVIDOS. Luz de casco: canal mais fraco "
                        "20 <= 37 (limite a refl 4) e refl 4 (a refl 6 o slug saturava o casco branco, shellart nota c). "
                        "NUNCA cobre. Cor de cada efeito da Tupa: art_assets.effects.railgun.palette_map_addendum.")}
pal["ac"]["tracer"] = [220, 30, 60]
pal["ac"]["glow"] = [220, 30, 60]
pal["ac"]["hull"] = [200, 10, 40]
pal["ac"]["hull_refl"] = 4
pal["ac"]["note"] = "ADDENDUM: tracante/luz da AC em CARMIM profundo (~220,30,60), nao rosa; luz de casco refl 4 (shellart nota b/c)"
pal["family_chip"]["projeteis"] = [64, 128, 255]
pal["family_chip"]["projeteis_tip"] = [255, 140, 40]
pal["family_chip"]["note"] = "ADDENDUM: projeteis AZUL com pontas laranja (meta art3d/bs_paiol family_chip; troque o spec, nao a arte)"
lw = A["phase_b_leftovers"]["islight_white_hull"]["values"]
lw["GlowSprite (halo)"]["_litReflectiveStrength"] = 0
lw["GlowSprite (halo)"]["addendum"] = ("HALO SO NO ESPACO: _litReflectiveStrength 0 e _litAdditiveStrength 0 (antes refl 3: o AP "
                                       "estourava 95 % do casco branco - shellart nota a); o brilho no espaco fica pelo "
                                       "_unlitAdditiveStrength (0,8 tracantes / 0,5 granadas e misseis)")
lw["GlowSprite2 (hull)"]["refl_por_municao"] = {"default": 6, "ac": 4, "slug": 4,
                                                "why": "shellart nota c: rail.hull e ac.hull a refl 6 saturavam o casco branco"}
A["guns_visuals"]["light_fixes_addendum"] = {
    "a_halo": "halo grande so no espaco (light_pair: halo refl 0)",
    "b_ac": "AC carmim profundo: palette.ac.tracer/glow [220,30,60], hull [200,10,40] refl 4",
    "c_refl": "luz de casco refl 4 para ac e slug (resto 6)",
    "d_boiuna_tracante_fino": {"what": "Boiuna (tier h, he_h/ac_h): tracante fino de granada, nao 'chama de foguete'",
                               "values": {"tw": 0.45, "tl": 6.5, "kw": 0.5, "kl": 1.6, "kback": 0.35, "puff": 0.5, "gain": 0.75},
                               "meaning": "tracante 6,5 quadros com 45 % da largura atual; nucleo curto 1,6 quadro com metade da largura comecando 0,35 quadro atras da base; rastro com metade da largura; tracante, nucleo e rastro a 75 % da intensidade",
                               "source": "scratchpad/v2/shellart/make_sheets.py BOIUNA_THIN"},
    "e_canvases": "tamanho do sprite = meta.items.<chave>.size de art3d/bs_shells2 (telas de 2,0 de comprimento; ac_h [2.0,0.89], pem_s [2.0,0.80], pem_m [2.0,0.75], slug [3.0,0.8]); slug sem trilhos (colares EM); check_art3d aceita a ancora 'tip'",
    "f_clarao_base": {"what": "Tambor (he_s/ap_s/sap_s/ac_s) e Trovao (_m): clarao branco da base com METADE do diametro e RECUADO para tras da base",
                      "values": {"head_k": 0.5, "head_dx": 0.15}, "source": "shellart make_sheets.py (folha projeteis_antes_depois.png)"}}
shell_meta = meta("bs_shells2")
for k, it in A["shell_ladder"]["items"].items():
    mi = shell_meta["items"][k]
    it["canvas"] = mi["size"]
    it["canvas_px"] = mi["px"]
    it["lights_frames"] = (mi.get("lights") or {}).get("frames")
    it["anchors_meta"] = mi.get("anchors", {})
    if k in ("ac_s", "ac_m", "ac_l"):
        it["status_addendum"] = ("ARTE AINDA GUIADA no meta (ancora seeker + luzes 2/4 quadros): o WP11 re-renderiza "
                                 "sem canards/sensor (1 quadro de luz, sem 'seeker'); so a ac_h da Boiuna e guiada")
A["shell_ladder"]["pem"] = {"pem_s": "Tuvira (torre) tela 2,0 x 0,80", "pem_m": "Treme-Treme tela 2,0 x 0,75", "pem_l": "Corisco tela 2,0 x 0,70"}
A["shell_ladder"]["rail"] = {"slug": "Tupa tela 3,0 x 0,8 (dardo APFSDS azul, colares EM, ancora 'tip'); o dardo no cano (slug.png) e o mesmo objeto"}
# historico do que o addendum recolore fica FORA do bullet_strike_art2.json (o arquivo que o gerador le): chave docs-only
HIST = S.setdefault("historico_addendum", {})
HIST["_nota"] = ("valores ANTIGOS (violeta/ouro, Tupa 3x4) trocados pelo addendum " + DATE + ", guardados so para consulta; "
                 "docs only (nao lido pelo gerador)")
_slug = A["shell_ladder"]["items"]["slug"]
HIST["art_assets.shell_ladder.items.slug.shape"] = _slug["shape"]
_slug["shape"] = ("dardo APFSDS longo e FINO de tungstenio CLARO (haste ~0,19 quadro), penetrador conico com a ponta quente "
                  "BRANCO-AZULADA (palette.rail.core [205,228,255] sobre azul claro [100,175,255]) e o colar LARANJA-OURO "
                  "(palette.rail.accent_orange_gold [215,145,40]) atras dela, 4 colares EM AZUIS (palette.rail.blue/glow; 3 "
                  "acesos por quadro, a onda corre da cauda para a ponta) e um feixe compacto de 6 aletas curtas na cauda; "
                  "sem trilhos, sem sela de armadura, NUNCA cobre, NUNCA violeta, NUNCA chama de foguete (bs_shells2.py "
                  "docstring, referencia do usuario). Os colares EM fazem o papel das sapatas de trilho (critica r1).")

# ---------------------------------------------------------------------------------------------
# 8b) Tupa: TODO o rail_fx AZUL, elemento por elemento (o split tools/spec/bullet_strike_art2.json e o que o gerador le)
# ---------------------------------------------------------------------------------------------
RC = pal["rail"]
CORE, GLOW, BLUE, HULLC, OG = RC["core"], RC["glow"], RC["blue"], RC["hull"], RC["accent_orange_gold"]
EMBER_END = [120, 45, 10]
HALO = [round(c / 4) for c in GLOW]
E = A["effects"]["railgun"]
HIST["art_assets.effects.railgun"] = copy.deepcopy(E)
HIST["art_assets.assets.fx_textures.files (ring/streak)"] = {k: A["assets"]["fx_textures"]["files"][k]
                                                             for k in ("bs_ring_thin.png", "bs_rail_streak.png")}
HIST["art_assets.assets.railgun.cano.files (trilhos/carga)"] = {k: A["assets"]["railgun"]["cano"]["files"][k]
                                                                 for k in ("trilhos1..9.png", "carga1..8.png")}
HIST["art_assets.assets.railgun.ponta.files.slug_glow.png"] = A["assets"]["railgun"]["ponta"]["files"]["slug_glow.png"]
HIST["art_assets.resolved_dependencies.slug_light"] = A["resolved_dependencies"]["slug_light"]
E["palette_map_addendum"] = {
    "rule": ("rail_fx AZUL (USER_NOTES: 'Efeitos da Tupa (rail_fx) em azul'; referencia do usuario): TODO efeito de ENERGIA "
             "da Tupa (claroes, aneis, arcos, raios, chiados, rastro, halo, escudo, interceptado, carga dos canos) usa "
             "palette.rail; o UNICO elemento quente e a brasa do ALVO queimando (rail_embers). Nada violeta, nada "
             "ouro-branco [255,225,150], nada cobre."),
    "map": {
        "gold-white (claroes, ponta quente, nucleo do rastro)": "core %s no centro -> glow %s na borda" % (CORE, GLOW),
        "violet (aneis EM, aneis do rastro, chiado, raios, arcos de carga, halo, escudo, interceptado)":
            "glow %s; franja/borda externa blue %s" % (GLOW, BLUE),
        "gold (particulas do rastro, faiscas da perfuracao e do impacto)": "core %s ao nascer -> glow %s ao morrer (faiscas branco-azuladas)" % (CORE, GLOW),
        "gold-orange (rail_embers)": ("FICA QUENTE: accent_orange_gold %s -> %s ao apagar (o alvo queimando; ponte para o "
                                      "fogo do jogo base; o laranja-ouro e a cor de detalhe da propria Tupa)" % (OG, EMBER_END)),
        "luzes": "fxkit.blob light=True e luz de casco: palette.rail.hull %s (refl 4); halo do light_pair = glow/4 %s, so no espaco" % (HULLC, HALO)},
    "fica": {"ouro/laranja que CONTINUA": "so rail_embers e as molas/detalhes pintados da ARTE (molas [235,185,50], laranja-ouro [215,145,40])",
             "ouro que SAI": "trail_core, faiscas, claroes, nucleo do bs_rail_streak, ponta do slug_glow, carga 7..8 dos canos"},
    "by": "addendum " + DATE + " (decisao do orquestrador: a frase do usuario manda o rail_fx em azul; as brasas sao o alvo, nao a Tupa)"}
E["charge_wave"]["rail_charge_arcs"] = (
    "vendored copy of ./Data/ships/terran/disruptor/particles/disruptor_shoot_lightning.rules recoloured BLUE (arco glow "
    "%s com nucleo core %s; plasma_fx 'arcs' builder), 1-2 arcs per 0.16 s, <= 4 live" % (GLOW, CORE))
E["muzzle"] = {
    "file": "bs_rail_fx/rail_muzzle_flash",
    "parts": ["blue-white flash: fxkit.blob additive 6 tiles 0.12 s, core %s -> glow %s (era gold-white)" % (CORE, GLOW),
              "blue EM ring: fxkit.blob tex bs_ring_thin.png 8 tiles, scale 0.2->1, 0.35 s, colour glow %s (era violet)" % GLOW,
              "TRANCO shock ring (railgun.tranco.shock_ring): TriggeredEffects proprio na boca (Location [1.5, 0]), "
              "AnchorMediaEffects = false (fica no espaco enquanto a nave recua), vanilla shockwave.png pelo fxkit ring, "
              "1.0 -> 6.5 tiles em 0.32 s (ease-out), borda glow %s -> nucleo core %s, alfa 1 -> 0, bucket Upper2" % (GLOW, CORE),
              "vanilla railgun_shoot_distortion (colourless)",
              "light: fxkit.blob light=True 10 tiles 0.2 s colour palette.rail.hull %s" % HULLC],
    "shake": "BASE_SHAKE 0.2 / 0.7 s (railgun.tranco.shake; MediaEffects do FireEffect da ponta)",
    "scale": "MediaEffectsScale BulletStrike_RailShot", "budget_particles": 5,
    "palette": "resolvido pelo addendum (palette_map_addendum): o 'palette_debt' do spec_patch r2 nao existe mais"}
inf = E["in_flight"]
inf["streak"] = ("AnimatedSprite bs_rail_streak.png (AZUL: core %s + franja blue %s + aneis glow %s, ver "
                 "assets.fx_textures), Size [4.2, 1.6], Offset [-0.6, 0], BulletUpper3, Add" % (CORE, BLUE, GLOW))
inf["trail_core"] = ("rail_trail_core: particulas BRANCO-AZULADAS core %s ao nascer -> glow %s ao morrer, no mundo (receita do "
                     "rastro ionico do Curupira no plasma_fx: FpsCompensator sem InheritVelocity), 40/s x 0.3 s = ~12 vivas "
                     "(era gold)" % (CORE, GLOW))
inf["trail_rings"] = ("rail_trail_rings: bs_ring_thin tingido glow %s (franja blue %s), 10/s, scale 0.4->1.6, scale2 [0.35, 1] "
                      "(achatado perpendicular ao voo), vida 0.35 s = ~4 vivos (era violet)" % (GLOW, BLUE))
inf["lights"] = ("fxkit.light_pair: halo [6, 3] cor glow/4 %s SO NO ESPACO (refl 0) + luz de casco [3.6, 1.2] palette.rail.hull "
                 "%s refl 4, StartTime por regra" % (HALO, HULLC))
ppp = E["per_penetrated_part"]["media"]
ppp[1] = ("rail_puncture: 1 flash blob core %s 1.4 tiles 0.08 s + fxkit.streaks n (3,3) core -> glow %s + 1 chiado (sizzle) "
          "blob glow %s 1.0 tile 0.25 s (era gold + violet)" % (CORE, GLOW, GLOW))
eop = E["end_of_path_impact"]["parts"]
eop[0] = "flash light: fxkit.blob light=True 9 tiles 0.25 s colour palette.rail.hull %s" % HULLC
eop[1] = "flash additive 6 tiles 0.15 s core %s -> glow %s" % (CORE, GLOW)
eop[2] = ("BLUE lightning: vendored missile_emp_lightning copy recoloured glow %s com nucleo core %s, 4-6 arcs (era violet)"
          % (GLOW, CORE))
eop[3] = "sparks: fxkit.streaks n (10, 14) core %s -> glow %s (faiscas branco-azuladas; era gold)" % (CORE, GLOW)
eop[5] = ("rail_embers: 8-12 brasas accent_orange_gold %s -> %s que desaceleram e brilham 1.2-2.0 s (codigo droplets_text do "
          "napalm em missile_fx.py:607-640, recolorido, reaproveitado antes de o napalm sair) = 'a area continua queimando' ate "
          "o visual do status de fogo assumir. UNICA cor quente do rail_fx (o alvo queimando)" % (OG, EMBER_END))
sh = E["shield_hit"]["parts"]
sh[0] = "flash branco-azulado blob core %s -> glow %s 5 tiles 0.18 s (era violet-white)" % (CORE, GLOW)
sh[1] = "bs_ring_thin tingido glow %s 6 tiles 0.4 s (era violet)" % GLOW
ic = E["intercepted"]["parts"]
ic[0] = "blob azul glow %s 3 tiles 0.2 s (era violet)" % GLOW
ic[1] = "fxkit.streaks n (4, 4) core %s -> glow %s" % (CORE, GLOW)
fxf = A["assets"]["fx_textures"]["files"]
fxf["bs_ring_thin.png"] = ("256x256 single frame, WHITE thin ring (alpha ring 6 px, soft 3 px) - tingido por uso: rail glow %s "
                           "(palette.rail.glow), PEM cyan, AC gold (o railgun_shoot.png vanilla e ciano e nao recolore por "
                           "multiplicacao)" % GLOW)
fxf["bs_rail_streak.png"] = ("512x384 atlas, 8 frames of 256x96 (2 per row): risco com nucleo branco-azulado core %s, franja "
                             "azul blue %s e 2 bojos de anel glow %s andando para tras; AnimatedSprite 30 fps. Cores ASSADAS "
                             "pelo fx_tex.py a partir de palette.rail (nada de ouro/violeta)" % (CORE, BLUE, GLOW))
_rcano = A["assets"]["railgun"]["cano"]["files"]
_rcano["trilhos1..9.png"] = ("doodads_low ValueSprites 3x3 (TK bs2t_rail_cano.rules:248-262): trilhos + 3 aneis de bobina AZUIS "
                             "por cano (palette.rail blue/glow); o nivel k acende os aneis da culatra (baixo) para a boca (cima); "
                             "nivel 1 = frio. A arte (art3d/bs_rail_barrel) manda")
_rcano["carga1..8.png"] = ("lights_add ValueSprites 3x3 (TK :268-284): planos aditivos de LARGURA INTEIRA sobre o canal (licao 2 do "
                           "prototipo), o nivel k cobre os k/8 de baixo do cano; AZUL blue %s -> glow %s, puxando para o nucleo "
                           "branco-azulado core %s nos niveis 7..8 (era violet [150,105,255] + gold-white [255,225,150]); "
                           "largura igual em todos os canos para as emendas casarem. A arte (art3d/bs_rail_barrel) manda"
                           % (BLUE, GLOW, CORE))
A["assets"]["railgun"]["ponta"]["files"]["slug_glow.png"] = (
    "lights_add, Size [1.2, 3.4], ChainedTo Projectile (TK :448-454); halo AZUL (blue %s -> glow %s), OCO no meio para o dardo "
    "claro continuar legivel; sem ponta dourada (era violet halo + gold tip)" % (BLUE, GLOW))
rd = A["resolved_dependencies"]
rd["slug_light"] = ("ADDENDUM (paleta azul): luz de casco palette.rail.hull %s refl 4 + light_blob da Ponta {0.10, 0.32, 1.0} "
                    "(historico R11 violeta: [96,0,255] refl 6 + light_blob {0.38, 0, 1.0})" % HULLC)
iwh = A["phase_b_leftovers"]["islight_white_hull"]


def _lit(vc, refl, add, D=0.85):
    return [round((refl * D + add) * c / 255, 2) for c in vc]


for row in iwh["check_table"]:
    lt = row.get("light", "")
    if lt == "2.0 hull light rail (refl 6)":
        row["historico"] = {k: row[k] for k in ("light", "vertex_color", "refl", "lit_white_hull", "c_min", "c_min_limit")}
        row.update({"light": "2.0 hull light rail (refl 4) ADDENDUM azul", "vertex_color": HULLC, "refl": 4, "add": 0.05,
                    "lit_white_hull": _lit(HULLC, 4, 0.05), "washes_white": False, "c_min": min(HULLC),
                    "c_min_limit": int(0.5 * 255 / (0.85 * 4))})
    elif lt == "2.0 hull light ac (refl 6)":
        acv = pal["ac"]["hull"]
        row["historico"] = {k: row[k] for k in ("light", "vertex_color", "refl", "lit_white_hull", "c_min", "c_min_limit")}
        row.update({"light": "2.0 hull light ac (refl 4) ADDENDUM carmim", "vertex_color": acv, "refl": 4, "add": 0.05,
                    "lit_white_hull": _lit(acv, 4, 0.05), "washes_white": False, "c_min": min(acv),
                    "c_min_limit": int(0.5 * 255 / (0.85 * 4))})
    elif lt.startswith("2.0 halo (GlowSprite)"):
        row["addendum"] = "SUBSTITUIDO: halo refl 0 / add 0 (so no espaco; guns_visuals.light_fixes_addendum.a_halo)"
    if row.get("c_min") is not None and row.get("c_min_limit") is not None and row["light"].endswith("ADDENDUM azul"):
        assert row["c_min"] <= row["c_min_limit"], row
iwh["corrections_to_siblings"]["newweapons_addendum"] = (
    "SUBSTITUI a linha 'newweapons': a luz da Tupa agora e AZUL: GlowSprite2 palette.rail.hull %s refl 4 e light_blob "
    "{0.10, 0.32, 1.0}; [96,0,255] / {0.38, 0, 1.0} sao historico (violeta)" % HULLC)
for _b in S["balance_checks"]:
    if _b.get("id") == "LIGHT-rail":
        _b["text_historico"] = _b["text"]
        _b["text"] = "luz de casco rail %s: canal mais fraco %d <= 37 (refl 4) (ADDENDUM azul; era [96, 0, 255] refl 6)" % (HULLC, min(HULLC))
    elif _b.get("id") == "LIGHT-ac":
        _b["text_historico"] = _b["text"]
        _b["text"] = "luz de casco ac %s: canal mais fraco %d <= 37 (refl 4) (ADDENDUM carmim)" % (pal["ac"]["hull"], min(pal["ac"]["hull"]))
_ui = A["assets"]["ui_icons"]["icons"]
if "gui/slug_rail.png" in _ui:
    _ui["gui/slug_rail.png"] = ("ADOTADO (art3d/bs_ui_icons2/slug_rail.png): dardo com aneis de armadura, acento 'rail' "
                                "[185,225,255] azul claro (icons.json accents.rail; era 'accent violet')")
R["visuals"]["rail_fx"] = "cores por elemento em art_assets.effects.railgun (palette_map_addendum): energia azul, so as brasas do alvo quentes"


def _no_violet_left():
    bad = []
    pat = re.compile(r"violet|violeta|\[96, ?0, ?255\]|150, ?105, ?255|0\.38, ?0", re.I)

    def walk(o, p):
        if isinstance(o, dict):
            for k, v in o.items():
                if "historico" in str(k):
                    continue
                walk(v, p + "/" + str(k))
        elif isinstance(o, list):
            if o and all(isinstance(x, (int, float)) for x in o):
                if pat.search(json.dumps(o)):
                    bad.append(p)
                return
            for i, v in enumerate(o):
                walk(v, p + "/" + str(i))
        elif isinstance(o, str) and pat.search(o) and "era " not in o and "historico" not in o.lower() \
                and "NUNCA violeta" not in o and "nada violeta" not in o.lower() and "removidos" not in o.lower() \
                and "ouro/violeta" not in o and not p.endswith("/ui_icons/renderer"):
            bad.append(p)
    for k in ("effects", "assets", "resolved_dependencies", "shell_ladder", "palette"):
        walk(A[k], "/art_assets/" + k)
    walk(A["phase_b_leftovers"]["islight_white_hull"]["check_table"], "/art_assets/phase_b_leftovers/islight_white_hull/check_table")
    walk(S["railgun"], "/railgun")
    return bad


rail_assets = A["assets"]["railgun"]
for part, d in (("carregador", "bs_rail_loader"), ("cano", "bs_rail_barrel"), ("ponta", "bs_rail_muzzle")):
    rail_assets[part]["count_now"] = nfiles(d)
    rail_assets[part]["count_now_seen_at"] = REPO_STATE["seen_at"] + " (disco; a lista valida e a 'files' do meta.json no BASE)"
    rail_assets[part]["meta_wins"] = ("valores de art3d/%s/meta.json do BASE vencem (BASE = commit da arte r2 do Tupa: "
                                      "SPEC.status_addendum.portao_tranco_r2)" % d)
    rail_assets[part].pop("art_contract_tranco_r1", None)
    rail_assets[part]["art_contract_tranco"] = copy.deepcopy(PATCH["art_contract"][part])
    rail_assets[part]["art_contract_tranco"]["from"] = PATCH_LABEL
rail_assets["source_addendum"] = ("ADOTADA (bs_rail.py + render_layered.py): carregador 5x5 e camadas do tranco (" + PATCH_LABEL +
                                  "); a arte valida e a do commit r2 (portao do WP01)")
pg = A["assets"]["pem_guns"]
pg["Tuvira"]["look"] = "TORRE 270 graus 1x2 com 2 canos curtos sincronizados (arte refeita: pivo [0.5,0.5], turret_size 1.0)"
pg["Tuvira"]["art3d"] = "art3d/bs_pem_light (kind gun; 17 arquivos + meta)"
pg["Corisco"]["art3d"] = "art3d/bs_pem_heavy (charge_glow1..4)"
pg["Treme-Treme"]["art3d"] = "art3d/bs_pem_medium"
fa = A["assets"]["factories"]
fa["F2"]["model"] = "bs_factory_special.py"
fa["F2"]["art3d_dir"] = "bs_factory_special"
fa["F6"]["accent"] = "blue (paleta da Tupa nova; laranja-ouro so nos detalhes)"
fa["DROP"] = fa["DROP"] + ["art3d/bs_factory_mag_ap (1.x 3x3; a F2 2.0 esta em art3d/bs_factory_special)",
                           "tools/blender/parts/bs_factory_mag_ap.py (1.x)"]
for r in A["assets"]["resources"]:
    r["art3d_dir"] = r["id"].split(".", 1)[1]
    r["status"] = "PRONTO (adotado, itens 2.0)"
    if r["id"] == "rafaeltessaro.bs_slug_rail":
        r["look"] = "dardo de tungstenio com colares EM AZUIS e colar laranja-ouro (paleta da Tupa nova)"
        r["accent"] = "blue"
A["assets"]["paiol"]["art_dir"] = "art3d/bs_paiol (meta shared) -> parts/bs_paiol_comum/"
A["assets"]["paiol"]["digits"] = "DESLIGADO nesta versao (logistics.paiol_contador = false): digitos nao publicados"
ui = A["assets"]["ui_icons"]
ui["art3d"] = ("art3d/bs_ui_icons2 (ADOTADO; icons.json 'files' = mapa gui/<x>.png -> <x>.png, 96x96): ammo_he/ap/sap/ac/frag, "
               "cell_plasma/pem, missile_he/cluster/emp/nuclear, slug_rail, group_bullet_strike")
ui["gap_addendum"] = "FALTA gui/buff_fita.png (icone do buff da Fita): WP11 acrescenta icon_buff_fita() ao ui_icons.py e grava em art3d/bs_ui_icons2"
own = A["art3d_owner_map"]["entries"]
for e in own:
    if e.get("tipo") == "factory":
        e["dirs"] = [FDIR[c] for c in ("F1", "F2", "F3", "F4", "F5", "F6")]
        e["nota"] = "F2 = art3d/bs_factory_special (meta id rafaeltessaro.bs_factory_mag_ap, 4x3, art3d_dir no meta)"
    if e.get("dados", "").startswith("WP05"):
        e["dirs"] = ["bs_paiol", "bs_fita", "bs_fita_fx", "bs_placas"]
        e["nota"] = "bs_paiol = pasta compartilhada (meta shared) publicada como parts/bs_paiol_comum"
own.append({"dirs": ["bs_ui_icons2"], "dono": "WP11", "tipo": "ui_icons", "dados": "WP10 make_art.misc_art (icons.json -> gui/)"})
own.append({"dirs": ["bs_factory_mag_ap"], "dono": "WP12", "legado": True, "sai_em": "WP12 (1.x 3x3; F2 2.0 = bs_factory_special)"})
bro = A["base_required_outputs"]
extra = ["art3d/bs_fita/meta.json", "art3d/bs_fita_fx/meta.json", "art3d/bs_placas/meta.json", "art3d/bs_paiol/meta.json",
         "art3d/bs_ui_icons2/icons.json"] + ["art3d/%s/meta.json" % d for d in FDIR.values()] + \
        ["art3d/%s/meta.json" % r["id"].split(".", 1)[1] for r in S["resources"]] + \
        ["tools/blender/parts/%s.py" % n for n in ("bs_fita", "bs_fita_fx", "bs_placas", "bs_paiol", "bs_factory_special",
                                                    "bs_factory_mag_std", "bs_factory_plasma", "bs_factory_missile",
                                                    "bs_factory_warhead", "bs_factory_slug")]
bro["paths"] = bro["paths"] + [p for p in extra if p not in bro["paths"]]
bro["content_checks_addendum"] = [
    "art3d/bs_rail_loader/meta.json tem size [5,5] e as camadas culatra_tranco; bs_rail_barrel tambores_tranco; bs_rail_muzzle weapon_tranco + tambor_tranco",
    "PORTAO TRANCO r2: railart/tranco/spec_patch.json (ou tools/spec/addendum/spec_patch_tranco.json) com meta.round "
    "'tranco-r2' ou mais novo (nao o rascunho v/spec_patch_try.json); o ultimo commit que toca art3d/bs_rail_* ou "
    "tools/blender/parts/bs_rail.py e POSTERIOR a 9fba772 (o commit do r1); as tarefas do job do tranco r2 (#114-116 da "
    "sessao) concluidas; depois disso apply_addendum_spec.py + make_addendum.py rodados de novo com esse spec_patch",
    "nenhum job de arte rodando e `git status --porcelain -- art3d tools/blender tools/check_art3d.py docs/preview/3d/v2` vazio",
    "estado lido por esta geracao (" + REPO_STATE["seen_at"] + "): portao " + REPO_STATE["portao_tranco_r2"] + "; HEAD " +
    str(REPO_STATE["head"]) + "; ultimo commit da arte do Tupa " + str(REPO_STATE["ultimo_commit_arte_tupa"]) + "; " +
    str(REPO_STATE["git_status_arte_n"]) + " caminhos sujos nas pastas de arte; " + PATCH_LABEL +
    ("" if not REPO_STATE["falta"] else "; FALTA: " + " | ".join(REPO_STATE["falta"]))]
A["adopted_addendum"] = {
    "rule": "TODA a arte abaixo esta pronta no repo e e ADOTADA: os WP10-WP13 so ligam (wire) e completam lacunas; nunca refazem",
    "folders": {d: {"files": nfiles(d), "kind": (meta(d) or {}).get("kind")} for d in
                ["bs_shells2", "bs_missiles2", "bs_rail_loader", "bs_rail_barrel", "bs_rail_muzzle", "bs_pem_light",
                 "bs_pem_medium", "bs_pem_heavy", "bs_boiuna_ac", "bs_fita", "bs_fita_fx", "bs_placas", "bs_paiol"] +
                list(FDIR.values()) + [r["id"].split(".", 1)[1] for r in S["resources"]]},
    "ui_icons": "art3d/bs_ui_icons2 (13 icones; falta buff_fita)",
    "gaps": ["ac_s/ac_m/ac_l ainda guiadas (WP11)", "gui/buff_fita.png (WP11)",
             "celulas cluster8/heavy8 dos lancadores + apagar napalm/limpet/torpedo (WP13)",
             "previas WP03 (casco_branco/penetracao/ac/frag 2.0) opcionais nesta build",
             "arte r2 do Tupa (refino 2 do tranco) ainda nao commitada: portao do WP01/WP13 (status_addendum.portao_tranco_r2)",
             "previas a REGERAR: projeteis_* (WP11), fabricas_2_0.png com 2 defeitos + logistica_fita.png/.gif depois da F1 final "
             "(WP12), armas_galeria_2_0.png + armas_casco_branco.png com a Tuvira antiga e 'PEM pesada' (WP13)"],
    "previews_adopted": "docs/preview/3d/v2/: municoes_itens.png, icones_2_0.png, logistica_paiois.png, fabricas_2_0.gif, "
                        "railgun_* (montado, disparo, tranco, tranco_curto, tranco_quadros, pecas, casco, referencia: os do "
                        "commit r2 do tranco), armas_pem.png, armas_pem_disparo.gif, armas_boiuna_ac.png, misseis_* "
                        "(cluster abrindo, futuristas, luzes)",
    "previews_regerar": {
        "projeteis_futuristas/antes_depois/casco_branco.png + projeteis_luzes.gif": "WP11 (slug azul e AC s/m/l sem guiagem; af0b0ed 11:43 e anterior ao slug azul)",
        "fabricas_2_0.png": "WP12 (USER_NOTES: 2 defeitos so na folha: a F3 do topo mostra o banco PEM com a placa de plasma; a legenda da F1 sai cortada)",
        "logistica_fita.png/.gif": "WP12 (be40fcd 20:01, anteriores a F1 final das fabricas r2 em 50c6804 20:37)",
        "armas_galeria_2_0.png + armas_casco_branco.png": "WP13 (6cc61aa 16:03: Tuvira fixa antiga e rotulo 'PEM pesada · 2.0' em vez de Corisco)"}}

# ---------------------------------------------------------------------------------------------
# 9) Testes do tranco, build 2.0, addendum (docs) e mapeamento do split
# ---------------------------------------------------------------------------------------------
for t in PATCH["tests"]:
    S["tests"]["newweapons"].append({"id": t["id"], "what": t["what"], "source": "spec_patch tranco " + DATE})
S["tests"]["checklist_2_0"] = ("ADDENDUM: os testes do 1o build 2.0 (T-FITA-1, T-F2-SPLIT, T-FRAG, T3, R-1..R-4, T-MSL-*, "
                               "T11, T-ART-*, T-TR-*) e o equivalente do TesteFita com as pecas reais estao no "
                               "docs/CHECKLIST_2_0.md (ADDENDUM_2_0.json.checklist); o usuario responde sim/nao por item.")
# o texto R4 do portao dizia 'sem o TesteFita so saem builds de teste (modo tripulacao)' e 'sem 36-46 o Tupa fica fora':
# as duas frases contradizem o build_2_0 (teleporte + rail.enabled = true por decisao do usuario). Emenda no proprio texto.
_rg = S["tests"]["release_gate"]
S["tests"]["release_gate_historico_r4"] = _rg
_rg2 = _rg.replace(
    "Sem o TesteFita so saem builds de teste (modo tripulacao).",
    "[ADDENDUM " + DATE + ": sem o TesteFita saem DOIS builds de TESTE: BulletStrike/ em teleporte (fita B + empurra + reserva "
    "da tripulacao abaixo da metade) e testes/BulletStrike_SemFita/ em tripulacao; o CHECKLIST_2_0 secao 2 refaz o TesteFita "
    "com as pecas reais.]")
_rg2 = _rg2.replace(
    "(sem 36-46 o Tupã fica fora)",
    "([ADDENDUM: o Tupa ENTRA nos dois builds: rail.enabled = true por decisao do usuario ('deixa ela FIXA mesmo, so coloque "
    "o efeito de TRANCO'); os itens 36-46 do Teste2 sao substituidos pelo CHECKLIST_2_0 secao 8 (R-1..R-4, T-TR-*) e "
    "decidem so as variantes do Tupa, nao a presenca dele])")
assert _rg2 != _rg and "Sem o TesteFita so saem builds de teste (modo tripulacao)." not in _rg2 and "(sem 36-46 o Tupã fica fora)" not in _rg2
S["tests"]["release_gate"] = _rg2
S["tests"]["release_gate_addendum"] = {
    "estado": "pendente: so builds de TESTE (Version 2.0.0, descricao '[2.0 de TESTE]'); SEM tag/publicacao da 2.0.0",
    "portao_2_0_0": ("respostas do CHECKLIST_2_0 nos itens do portao = respostas_2_0.json portao.falta: 1.1-1.3 e 2.1-2.10 "
                     "(A1-A7/A3b), 2.11-2.13 (B1-B3), 2.14 (C1), 11.1 (C2) e, COM SW, 1.7 e 2.15 (C3; C3 = nao trava ate "
                     "corrigir). Os demais itens decidem switches (sem resposta -> safe) e nao travam a 2.0.0"),
    "testefita": "o kit testes/BulletStrike_TesteFita continua valido; respostas dele (A1-A7, A3b, B1-B3, C1-C3) entram no lugar dos itens mapeados (checklist.maps_tests)"}

S["build_2_0"] = {
    "status": "BUILD DE TESTE (portao da 2.0.0 pendente: TesteFita/checklist sem resposta). Version = 2.0.0 nos dois builds (so numeros: o parser de Version do mod.rules pode nao aceitar sufixo).",
    "variants": {
        "fita": {"out": "BulletStrike/", "mod_id": "rafaeltessaro.bullet_strike", "name": "Bullet Strike",
                 "description_first_line_ptbr": "[2.0 de TESTE] Versão com a Fita de Alimentação (teletransporte). Se não carregar, use a reserva 'Bullet Strike (reserva sem Fita)'. Nunca ative as duas juntas.",
                 "description_first_line_en": "[2.0 TEST BUILD] Version with the Ammo Feed Link (teleport logistics). If it does not load, use the backup 'Bullet Strike (reserva sem Fita)'. Never enable both at once.",
                 "cli": "python3 tools/build_mod.py --variante fita --vanilla \"$COSMOTEER_DATA\" --out BulletStrike"},
        "semfita": {"out": "testes/BulletStrike_SemFita/", "mod_id": "rafaeltessaro.bullet_strike_semfita",
                    "name": "Bullet Strike (reserva sem Fita)",
                    "description_first_line_ptbr": "[2.0 de TESTE - RESERVA SEM FITA] Mesmas armas, paióis e fábricas; sem a peça Fita (tripulação + paiol acoplado). Nunca ative junto com o 'Bullet Strike'.",
                    "description_first_line_en": "[2.0 TEST BUILD - BACKUP WITHOUT THE FEED LINK] Same weapons, magazines and factories; no Ammo Feed Link part (crew + docked magazines). Never enable it together with 'Bullet Strike'.",
                    "cli": "python3 tools/build_mod.py --variante semfita --vanilla \"$COSMOTEER_DATA\" --out testes/BulletStrike_SemFita",
                    "forces": {"logistics.transport": "tripulacao"}}},
    "switch_values_fita": {
        "logistics.transport": "teleporte", "logistics.fita_fabrica": "B", "logistics.fita_arma": "empurra",
        "logistics.reserva_tripulacao": "metade", "logistics.fita_alcance": 1000, "logistics.fita_embutida": "off",
        "logistics.devolucao_arma": "off", "logistics.acoplamento": "auto", "logistics.paiol_seletor": "botao",
        "logistics.paiol_contador": False, "logistics.recurso_cookoff": "off", "logistics.projeteis_3x3": True,
        "art.fita_luz": "ack", "rail.enabled": True, "rail.power_mode": "B", "rail.charge_wave": "atraso",
        "rail.buffed_riders": False, "rail.overload_rider": False, "rail.per_ship_limit": 2, "rail.loader_intake": "auto",
        "rail.r2_fallback": True, "rail.codex": False, "rail.tranco_impulso": "impulso", "rail.tranco_gatilho": "relay",
        "rail.recoil_com": False, "pem.heavy_name": "Corisco", "pem.tuvira_mount": "torre", "pem.tuvira_cp": 2,
        "pem.overload_rider": False, "pem.charge_glow": True, "boiuna.ac_guided": True,
        "missiles.cluster_randomize_target": "on", "missiles.cluster_open": "proximity", "missiles.cluster_petals": "bullets",
        "missiles.cluster_lite": False, "missiles.poraque_pulses": "off", "missiles.category_limits": "on",
        "missiles.iara_hp": 12000, "missiles.poraque_overload": False, "guns.small_rounds_targetable": False,
        "guns.frag_fragment": "volumehit", "guns.ap_further_factor": "sem_reducao", "guns.ac_cost": "4x",
        "guns.defesa_antilaser": "fase_b", "guns.he_further_factor": 0.5, "art.light_split": "split",
        "art.pen_media": "light", "art.frag_cone": "radial", "balance.perfil": "sw", "balance.perfil_extra": False,
        "econ.factory_adjacency": "vanilla"},
    "switch_values_semfita_overrides": {"logistics.transport": "tripulacao"},
    "not_applicable": ["logistics.paiol_expulsao", "logistics.tremonha", "logistics.entrada_alternada",
                       "logistics.paiol_seletor_rede", "logistics.esteira_corredor", "logistics.esteira_overlay",
                       "art.corredor_carts", "art.esteira_shapes"],
    "wp15": "pular",
    "deliverables": ["BulletStrike/ (fita)", "testes/BulletStrike_SemFita/ (reserva)", "docs/CHECKLIST_2_0.md",
                     "testes/BulletStrike_2_0.zip (BulletStrike/ + CHECKLIST_2_0_CURTO.txt)",
                     "testes/BulletStrike_SemFita.zip (BulletStrike_SemFita/ + CHECKLIST_2_0_CURTO.txt)"]}

S["addendum_2_0"] = {
    "date": DATE, "file": "design/final/addendum/ADDENDUM_2_0.json (copiado para tools/spec/ADDENDUM_2_0.json pelo WP01)",
    "user_answers": {"pergunta_1": "PEM pesada = Corisco (overclock Relâmpago); Tuvira vira TORRE (270 graus, 4320 escudo/s)",
                     "pergunta_2": "vizinhanca das fabricas LIGADA (+25 %, intervalos x1,5)", "pergunta_3": "perfil jogo base separado: NAO",
                     "outras_escolhas": "sem mudanca -> safe (balas <= 30 mm nao derrubaveis, so a peca Fita, defesas anti-laser da Fase B, Iara 12000, AC 4x)",
                     "tupa": "fixa + tranco + carregador 5x5 + azul + passa sobre a propria nave; mais canos = mais dano/alcance/penetracao/velocidade/energia",
                     "visual": "toda municao futurista (itens, projeteis, icones)", "esteira": "NAO quer esteira fisica (WP15 pulado)",
                     "pedido_atual": "quando terminar tudo monte o MoD e me forneca um checklist do que eu devo testar",
                     "testefita": "SEM resposta"},
    "applied_by": ("design/final/addendum/apply_addendum_spec.py (parte de addendum/SPEC_2.0.before.json); no repo: "
                   "tools/spec/addendum/apply_addendum_spec.py (copia do WP01, G13)"),
    "spec_patch": copy.deepcopy(PATCH_INFO)}
S["revision_addendum"] = [
    {"id": "ADD-1", "finding": "plano R4 esperava o TesteFita para escolher o transporte e so montava builds em tripulacao", "resolution": "build principal em teleporte (B + empurra + reserva metade) + build reserva SemFita (tripulacao); checklist substitui o kit"},
    {"id": "ADD-2", "finding": "Tupa 3x4, violeta/ouro, recuo 1/30 s (8-24 empurroes)", "resolution": "carregador 5x5 com encadeamento exato, azul, UM impulso 2400 x m(N), tremor, anel, quadros do tranco (relay)"},
    {"id": "ADD-3", "finding": "nomes Mãe-do-Ouro/Corisco e Tuvira fixa", "resolution": "Corisco (Relâmpago) e Tuvira torre 270 graus 4320/s (22 celulas)"},
    {"id": "ADD-4", "finding": "vizinhanca off", "resolution": "vanilla (+25 %, x1,5) como padrao"},
    {"id": "ADD-5", "finding": "arte: pastas e nomes do plano diferem do que foi feito (bs_paiol, bs_factory_special, bs_ui_icons2)", "resolution": "mapa de pastas e dono atualizados; F2 1.x apagada no WP12"},
    {"id": "ADD-6", "finding": "luzes: halo lavava o casco branco; AC rosa; Boiuna 'foguete'; clarao da base grande", "resolution": "halo refl 0, AC carmim refl 4, slug refl 4, Boiuna tracante fino, clarao metade e recuado"},
    {"id": "ADD-7", "finding": "contador de 4 digitos", "resolution": "desligado (barra + medidor)"}]
S["status_addendum"] = {
    "seen_at": REPO_STATE["seen_at"], "head": REPO_STATE["head"],
    "ultimo_commit_arte_tupa": REPO_STATE["ultimo_commit_arte_tupa"],
    "git_status_arte_n": REPO_STATE["git_status_arte_n"], "git_status_arte_amostra": REPO_STATE["git_status_arte"],
    "spec_patch": PATCH_INFO,
    "portao_tranco_r2": REPO_STATE["portao_tranco_r2"],
    "falta": REPO_STATE["falta"],
    "base": REPO_STATE["base"],
    "art_jobs": ("logistica/fabricas r2/itens/icones COMMITADOS em 50c6804; Tupa tranco r1 em 9fba772 MAS o job do tranco "
                 "entrou no refino r2 (backup_tranco_r1 20:52, criticas crit_r2_1/crit_r2_2 20:42-20:49, tarefas #114-116 da "
                 "sessao: must_fix do spec_patch, re-render da arte, previas novas): 9fba772 NAO e mais o BASE"),
    "rule": ("WP01 (e o WP13) so comecam com portao_tranco_r2 = SATISFEITO: spec_patch FINAL da rodada r2 (ou mais nova), "
             "commit da arte r2 do Tupa depois de 9fba772, git status das pastas de arte limpo e nenhum job de arte rodando. "
             "Entao: re-rodar apply_addendum_spec.py e make_addendum.py com esse spec_patch (o status sai SATISFEITO com o "
             "hash do commit em 'base'), conferir HEAD e git status de novo e so depois copiar SPEC/ADDENDUM para tools/spec "
             "(G13). Este SPEC foi gerado com " + PATCH_LABEL + ".")}
gm = S["generator_mapping"]["split_files"]
if "build_2_0" not in gm["tools/spec/bullet_strike_spec.json"]:
    gm["tools/spec/bullet_strike_spec.json"].append("build_2_0")
for k in ("addendum_2_0", "revision_addendum", "status_addendum", "historico_addendum"):
    if k not in gm["docs only (nao lido pelo gerador)"]:
        gm["docs only (nao lido pelo gerador)"].append(k)
S["binding_inputs"]["user_answers_" + DATE] = S["addendum_2_0"]["user_answers"]
S["binding_inputs"]["logistics_weight_addendum"] = ("a banda de logistica foi medida com a vizinhanca off; com a vizinhanca "
                                                    "LIGADA e intervalos x1,5 o custo e o mesmo com 2 fabricas vizinhas, 1,5x "
                                                    "com a fabrica sozinha e menor com 3-4 vizinhas")
S["vanilla_profile"]["addendum"] = "NAO montado: pergunta 3 = NAO (balance.perfil_extra = false); o WP01 nao precisa implementar --perfil vanilla"

# ---------------------------------------------------------------------------------------------
# grava + confere
# ---------------------------------------------------------------------------------------------
txt = json.dumps(S, ensure_ascii=False, indent=1)
json.loads(txt)
with open(DST, "w", encoding="utf-8") as fh:
    fh.write(txt + "\n")
left = []


def scan(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            scan(v, path + "/" + str(k))
            if isinstance(k, str) and ("Mãe-do-Ouro" in k or "Mae-do-Ouro" in k):
                left.append(path + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            scan(v, path + "/" + str(i))
    elif isinstance(o, str) and ("Mãe-do-Ouro" in o or "Mae-do-Ouro" in o):
        left.append(path)


scan({k: v for k, v in S.items() if k not in SKIP_TOP})
print("escrito", DST, len(txt) + 1, "bytes")
print("Mae-do-Ouro restante (permitido: switch heavy_name, name_reason, family_names.heavy_alternative):", left)
_viol = _no_violet_left()
print("violeta restante no rail (fora de historico):", _viol)
print("spec_patch:", PATCH_LABEL, PATCH_INFO["path"])
print("portao tranco r2:", REPO_STATE["portao_tranco_r2"], "| HEAD", REPO_STATE["head"], "| arte Tupa",
      REPO_STATE["ultimo_commit_arte_tupa"], "| sujos", REPO_STATE["git_status_arte_n"])
for _f in REPO_STATE["falta"]:
    print("  falta:", _f)
