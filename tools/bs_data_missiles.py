"""Dados dos lancadores de misseis 2.0 do Bullet Strike (Tocandira / Caipora / Mula-sem-Cabeca; dono: WP06).

Fonte: tools/spec/bullet_strike_missiles.json (dividido de SPEC_2.0.json): launchers[] (pecas, modos, estoque,
cook-off, overclock por modo, logistica, arte) e missiles (seletor, tipos, Piranha estilo Sunflower, Poraque 2.0,
Iara sem segundo estagio de distracao). Os numeros chegam prontos; este modulo so os organiza e confere.

Modulo de conteudo (API = 2, registro do tools/build_mod.py). O bs_data so copia LAUNCHERS / MISSILES /
MISSILE_CHOICES / MISSILE_STATUSES / MISSILE_TYPES / MISSILE_VARIANTS para DATA quando bs_data_missiles,
bsgen.launchers E bsgen.missile_shots tem API >= 2 (bs_data.load_launchers); sem o WP07 os lancadores ficam fora.

Exporta:
  LAUNCHERS        uma entrada por lancador (formato lido por bsgen/launchers.py, make_art.launcher_art,
                   check_art3d e pelo seam de logistica bsgen.intake: id/short/key/size/modes[index, key, res,
                   storage, names...]/logistica/belt/fita_fx_location/extra_categories)
  MISSILES         uma entrada por (lancador, modo): o tiro que o lancador dispara (kind 'missile', owner
                   'bsgen.missile_shots', file/dir/id) com voo, HP, dano e filhos (portador da Piranha -> _child;
                   Iara -> _warhead). O WP07 constroi os arquivos (shots(DATA) acrescenta a DATA.SHOTS).
  MISSILE_CHOICES  [(indice, choice_id, chave do tooltip, icone sem 'gui/', tipo)] de SPEC.toggles.bs_missile_type
  MISSILE_TYPES    {tipo: missiles.missile_types[]}
  MISSILE_VARIANTS variantes de mecanica (mechanic_variants_2_0 + switches missiles.*; BS_MSL_VARIANTS='k=v,...'
                   para as variantes de lancador)
  MISSILE_STATUSES [] (a 2.0 nao tem status proprio de missil)

Conferencias (selfcheck_data, tambem chamada pelo selfcheck do bsgen.launchers): filhos por portador <= 20,
portadores por salva <= 8, minimisseis por salva <= 160, HP dos filhos >= HP do portador, dreno por carga <= 3000,
escudo por salva < 320000, nuclear so com limite por nave, ciclos/salvas/alfa/estoque/cook-off contra o spec.
`python3 -c 'import sys; sys.path.insert(0, "tools"); import bs_data_missiles as M; M.selfcheck_data()'` levanta
ValueError com a lista se algo divergir.
"""

API = 2

import copy  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

import bs_data as D  # noqa: E402
from bsgen import common as C  # noqa: E402
from launcher_layout import cell_layout  # noqa: E402

MSPEC = D.MSPEC
MS = MSPEC["missiles"]
AUTHOR = D.AUTHOR

ERRORS = []                 # problemas encontrados na carga (selfcheck_data devolve/levanta)
LAUNCHERS = []
MISSILES = []
MISSILE_STATUSES = []
MISSILE_TYPES = {m["id"]: m for m in MS["missile_types"]}
TYPE_BY_INDEX = {v: k for k, v in D.MISSILE_INDEX.items()}

# limites duros (SPEC.missiles.cluster_sunflower.performance_budget.hard_checks, poraque_2.caps, iara)
MAX_CHILDREN = 20
MAX_CARRIERS_PER_SALVO = 8
MAX_MINIS_PER_SALVO = 160
MAX_DRAIN_PER_CHARGE = 3000
SW_GIGA_BUBBLE = 320000
TIER_LETTER = {"early": "s", "mid": "m", "late": "l"}
# arte de voo (art3d/bs_missiles2): item por tipo e porte do lancador (bs_missiles2.py; Tocandira = he_s)
ART_KEY = {("he", "early"): "he_s", ("he", "mid"): "he_m", ("he", "late"): "he_l",
           ("cluster", "mid"): "cluster_m", ("cluster", "late"): "cluster_l",
           ("emp", "mid"): "emp_m", ("emp", "late"): "emp_l", ("nuclear", "late"): "nuclear_l"}


def _err(msg):
    if msg not in ERRORS:
        ERRORS.append(msg)


# ============================================================================= variantes de mecanica
# variantes do LANCADOR que o bsgen/launchers.py implementa (o resto do mechanic_variants_2_0 passa adiante:
# tiros = WP07, nuvem da Pororoca = WP02). BS_MSL_VARIANTS so aceita estas chaves (os switches missiles.* vao por
# --switch / BS_SWITCHES).
LAUNCHER_VARIANTS = {
    "rack_gate": ("latch", "salvo_timer"),
    "loader_crew_gate": ("is_operational", "explicit_partcrew"),
    "mode_switch_delay": ("per_mode", "single_longest"),
    "prefilled_switch": ("full_delay", "oc_delay"),
    "dry_flush": ("debounced", "instant", "off"),
    "cassette": ("burst", "twin_emitter"),
    "cell_sync": ("reset_each_reload", "free_cycle"),
    "overlays": ("per_pod",),
    "ai_firepower": ("full", "x0_8"),
    "early_overclock": ("disabled",),
    "selector_ids": ("shared",),
}
PASS_VARIANTS = {
    "source_part_collision_delay": ("ticks_1_5", "s_0_3"),
    "homing_avoidance": ("omit", "raycast_250", "no_avoid_friendlies"),
    "cluster_hp_inherit": ("all_paths", "fuses_only"),
    "emp_rider": ("on", "off"),
    "emp_shield_drain": ("single_part", "area"),
    "ciws_vs_own_missiles": ("as_is", "enemies_only"),
}
# switches missiles.* (SPEC.switches.missiles) espelhados em MISSILE_VARIANTS com o valor efetivo
SWITCH_KEYS = ("cluster_randomize_target", "cluster_open", "cluster_petals", "cluster_lite", "poraque_pulses",
               "category_limits", "iara_hp", "poraque_overload")


def _first_word(v):
    return str(v).split()[0].strip() if v is not None else v


def _variants():
    mv = MS.get("mechanic_variants_2_0") or {}
    v = {}
    for grp in ("keep_defaults", "changed_defaults", "new"):
        for k, val in (mv.get(grp) or {}).items():
            v[k] = _first_word(val)
    for k in SWITCH_KEYS:
        v[k] = D.switch(f"missiles.{k}")
    for item in filter(None, (x.strip() for x in os.environ.get("BS_MSL_VARIANTS", "").split(","))):
        k, sep, val = item.partition("=")
        k, val = k.strip(), val.strip()
        if k in SWITCH_KEYS:
            raise SystemExit(f"BS_MSL_VARIANTS: {k} e switch: use --switch missiles.{k}={val} (ou BS_SWITCHES)")
        opts = LAUNCHER_VARIANTS.get(k) or PASS_VARIANTS.get(k)
        if not sep or not opts:
            raise SystemExit(f"BS_MSL_VARIANTS: variante desconhecida {item!r} (chaves: "
                             f"{', '.join(sorted(LAUNCHER_VARIANTS) + sorted(PASS_VARIANTS))})")
        if val not in opts:
            raise SystemExit(f"BS_MSL_VARIANTS: {k}={val} nao implementada nesta versao (valores: {', '.join(opts)})")
        v[k] = val
    for k, opts in list(LAUNCHER_VARIANTS.items()) + list(PASS_VARIANTS.items()):
        v.setdefault(k, opts[0])
        if v[k] not in opts:
            _err(f"variante {k}={v[k]} do spec sem implementacao (valores: {', '.join(opts)})")
    return v


MISSILE_VARIANTS = _variants()

# ============================================================================= seletor
MISSILE_CHOICES = []
for _c in D.TOGGLES["bs_missile_type"]["choices"]:
    _icon = _c["icon"][4:] if _c["icon"].startswith("gui/") else _c["icon"]
    MISSILE_CHOICES.append((_c["index"], _c["choice_id"], _c["string_key"], _icon, TYPE_BY_INDEX[_c["index"]]))
CHOICE_BY_TYPE = {TYPE_BY_INDEX[c["index"]]: c for c in D.TOGGLES["bs_missile_type"]["choices"]}


# ============================================================================= utilidades
def _short(pid):
    return pid.split(".", 1)[1]


def _key(short):
    return "BS" + "".join(p.capitalize() for p in short.split("_")[1:])


def _res_key(res):
    """rafaeltessaro.bs_msl_he -> msl_he (chave do paiol / FitaEntra_<chave> / Estoque_<chave>)."""
    s = _short(res)
    return s[3:] if s.startswith("bs_") else s


def _boxes(physics):
    """'BoxPhysics Size [2.0, 0.65] (stage), [1.6, 0.6] (warhead)' -> [[2.0, 0.65], [1.6, 0.6]]."""
    return [[float(a), float(b)] for a, b in re.findall(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", physics or "")]


def _ticks(txt):
    return int(txt) / 30


def _ripples(L, modes):
    """Intervalo entre unidades da salva por modo (n/30 s, tick) e o BurstDelay do cassete, lidos de
    launchers[].ripple_s ('4/30 ... for every mode' ou 'HE fine48 2/30; cluster heavy8 4/30; ...')."""
    txt = str(L.get("ripple_s") or "")
    bm = re.search(r"BurstDelay\s+(\d+)/30", txt)
    burst = int(bm.group(1)) if bm else 2
    clean = re.sub(r"BurstDelay\s+\d+/30", "", txt)
    first = re.search(r"(\d+)/30", clean)
    if not first:
        _err(f"{L['codename']}: ripple_s sem n/30 ({txt!r})")
        return {m["missile_type"]: 4 for m in modes}, burst
    segs = [s for s in clean.split(";") if re.search(r"\d+/30", s)]
    per = {}
    for m in modes:
        words = {m["layout"], m["missile_type"], {"he": "HE", "emp": "EMP"}.get(m["missile_type"], m["missile_type"])}
        for s in segs:
            if any(re.search(r"(?<![\w])" + re.escape(w) + r"s?(?![\w])", s, re.I) for w in words):
                per[m["missile_type"]] = int(re.search(r"(\d+)/30", s).group(1))
                break
        per.setdefault(m["missile_type"], int(first.group(1)))
    return per, burst


def _num(x):
    return int(round(x)) if abs(x - round(x)) < 1e-9 else x


# ============================================================================= misseis (tiros)
def _stat_damage(t, d):
    """Dano por missil mostrado no tooltip (STAT_DAMAGE do tiro) e raio (STAT_RADIUS)."""
    if t == "he":
        return d["ExplosiveDamage"], d["Radius"]
    if t == "cluster":
        return d["explosive_per_carrier"], d["child_Radius"]
    if t == "emp":
        op = d["HitOperational"]
        return op["Damage"] + op["structural_ExplosiveDamage"], op["structural_Radius"]
    return d["warhead_operational"] + d["warhead_structural"], d["op_radius"]


def _missile(L, m):
    """Entrada de MISSILES de um modo: o arquivo que o lancador dispara (e os filhos na mesma pasta)."""
    t = m["missile_type"]
    sid = m["shot_ids"][0]
    short = _short(sid)
    fl = m["flight"]
    boxes = _boxes(fl.get("physics"))
    ch = CHOICE_BY_TYPE[t]
    d = copy.deepcopy(m["damage"])
    sdmg, srad = _stat_damage(t, d)
    s = {"kind": "missile", "owner": "bsgen.missile_shots", "file": short, "dir": short, "id": sid,
         "title": f"{ch['name_en']} ({m['variant_codename']}) - {L['codename']}",
         "payload": t, "missile_index": m["toggle_index"], "resource": m["resource"],
         "launcher": L["id"], "launcher_short": _short(L["id"]), "launcher_codename": L["codename"],
         "tier": L["tier"], "codename": m["variant_codename"], "name_en": ch["name_en"], "name_pt": ch["name_ptbr"],
         "range": fl["range_m"], "ideal_range": list(fl.get("ideal_range_m") or [fl["range_m"], fl["range_m"]]),
         "speed": fl["speed"], "accel": fl["accel"], "turn": fl["turn_deg_s"], "homing_delay": fl["homing_delay_s"],
         "lifetime": fl["lifetime_s"], "box": boxes[0] if boxes else None, "hp": m["missile_hp"],
         "damage": d, "stat_damage": sdmg, "stat_radius": srad,
         "per_salvo": m["missiles_per_salvo"], "rack_units": m["rack_units"],
         "art_key": ART_KEY.get((t, L["tier"])), "variants": MISSILE_VARIANTS, "children": [], "spec_mode": m}
    cc = L["codename"]
    if t == "cluster":
        cs = MS["cluster_sunflower"]
        car, kid = cs["carrier"], cs["children"]
        trig = car["open_triggers"]
        s["carrier"] = {"proximity_range": trig["ProximityFuse"]["Range"][cc],
                        "proximity_start_delay": trig["ProximityFuse"]["StartDelay"][cc],
                        "proximity_interval": trig["ProximityFuse"]["Interval"],
                        "timed_fuse": trig["TimedFuse"]["Lifetime"][cc], "hp": car["hp"][cc]}
        kf = kid["flight"]
        kb = _boxes(kf["physics"][cc])
        s["children"].append({
            "role": "child", "file": f"{short}_child", "id": f"{sid}_child", "count": kid["Count"][cc],
            "hp": kid["hp"][cc], "damage": kid["damage"][cc]["ExplosiveDamage"],
            "radius": kid["damage"][cc]["Radius"], "impulse": kid["damage"][cc]["Impulse"],
            "speed": kf["Speed"], "accel": kf["Acceleration"][cc], "turn": kf["TargetHoming"]["TurnVelocity"][cc],
            "homing_delay": kf["TargetHoming"]["Delay"], "velocity_compensation": kf["TargetHoming"]["VelocityCompensation"],
            "lifetime": kf["DeathByLifetime"][cc], "range": kf["Range"][cc], "box": kb[0] if kb else None,
            "art_key": "cluster_mini", "art_scale": 1.2 if L["tier"] == "late" else 1.0,
            "title": f"{ch['name_en']} mini-missile ({m['variant_codename']}) - {cc}"})
    elif t == "nuclear":
        ia = MS["iara"]
        hp = int(D.switch("missiles.iara_hp"))
        s["hp"] = hp
        s["deploy_lifetime"] = 1.5
        s["children"].append({
            "role": "warhead", "file": f"{short}_warhead", "id": f"{sid}_warhead", "hp": hp,
            "speed": 0, "accel": fl["accel"], "turn": fl["turn_deg_s"], "lifetime": 9.5,
            "box": boxes[1] if len(boxes) > 1 else None, "range": fl["range_m"],
            "damage": {"op": ia["numbers"]["op"], "op_radius": ia["numbers"]["op_radius"],
                       "struct": ia["numbers"]["struct"], "struct_radius": ia["numbers"]["struct_radius"]},
            "art_key": "nuclear_wh_l", "title": f"{ch['name_en']} warhead ({m['variant_codename']}) - {cc}"})
    elif t == "emp":
        s["poraque"] = dict(MS["poraque_2"]["per_missile"][cc])
    return s


def _check_missile(s, L, m, lch_extra):
    """Limites duros do spec para o tiro de um modo (e a coerencia com os numeros do modo)."""
    who = f"{L['codename']}/{s['payload']}"
    d = s["damage"]
    n = m["missiles_per_salvo"]
    t = s["payload"]
    if s["box"] is None:
        _err(f"{who}: BoxPhysics sem tamanho ({m['flight'].get('physics')!r})")
    if t == "he":
        if d["ExplosiveDamage"] * n != d["alpha_explosive_per_salvo"]:
            _err(f"{who}: alfa {d['ExplosiveDamage']} x {n} != {d['alpha_explosive_per_salvo']}")
    elif t == "cluster":
        kid = s["children"][0]
        lite = bool(MISSILE_VARIANTS.get("cluster_lite"))
        for tag, cnt, hp, dmg in (("", kid["count"], kid["hp"], kid["damage"]),
                                  (" (cluster_lite)", {20: 10, 12: 6}.get(kid["count"], kid["count"] // 2),
                                   kid["hp"] * 2, kid["damage"] * 2)):
            if cnt > MAX_CHILDREN:
                _err(f"{who}{tag}: {cnt} filhos por portador (> {MAX_CHILDREN})")
            if cnt * hp < s["carrier"]["hp"]:
                _err(f"{who}{tag}: HP dos filhos {cnt} x {hp} < HP do portador {s['carrier']['hp']}")
            if cnt * n > MAX_MINIS_PER_SALVO:
                _err(f"{who}{tag}: {cnt * n} minimisseis por salva (> {MAX_MINIS_PER_SALVO})")
            if abs(cnt * dmg - kid["count"] * kid["damage"]) > 1e-6 * max(1, kid["count"] * kid["damage"]) and tag:
                _err(f"{who}{tag}: dano total do portador muda com cluster_lite")
        if lite and kid["count"] not in (12, 20):
            _err(f"{who}: cluster_lite sem tabela para {kid['count']} filhos")
        if n > MAX_CARRIERS_PER_SALVO:
            _err(f"{who}: {n} portadores por salva (> {MAX_CARRIERS_PER_SALVO})")
        if kid["count"] != d["children_per_carrier"] or kid["hp"] != d["child_hp"] \
                or kid["damage"] != d["child_ExplosiveDamage"]:
            _err(f"{who}: cluster_sunflower difere de modes[].damage (filhos/HP/dano)")
        if kid["count"] * kid["hp"] != d["children_hp_pool"]:
            _err(f"{who}: children_hp_pool {d['children_hp_pool']} != {kid['count']} x {kid['hp']}")
        if kid["count"] * kid["damage"] != d["explosive_per_carrier"]:
            _err(f"{who}: explosive_per_carrier {d['explosive_per_carrier']} != {kid['count']} x {kid['damage']}")
        if d["explosive_per_carrier"] * n != d["alpha_explosive_per_salvo"]:
            _err(f"{who}: alfa {d['explosive_per_carrier']} x {n} != {d['alpha_explosive_per_salvo']}")
        if kid["count"] * n != d["minis_per_salvo"]:
            _err(f"{who}: minis_per_salvo {d['minis_per_salvo']} != {kid['count']} x {n}")
        if s["carrier"]["hp"] != m["missile_hp"]:
            _err(f"{who}: HP do portador {s['carrier']['hp']} != missile_hp {m['missile_hp']}")
    elif t == "emp":
        hs, op = d["HitShield"], d["HitOperational"]
        drain = hs["ResourceDrain_battery_TreatShieldAsPart"]
        if drain / m["charges_per_rack_unit"] > MAX_DRAIN_PER_CHARGE:
            _err(f"{who}: dreno por carga {drain / m['charges_per_rack_unit']:.0f} (> {MAX_DRAIN_PER_CHARGE})")
        per = hs["shield_hp_removed_sw"] + hs["Damage"]
        if per != d["shield_hp_per_missile"] or per * n != d["shield_hp_per_salvo"]:
            _err(f"{who}: escudo por missil/salva {per}/{per * n} difere do spec "
                 f"{d['shield_hp_per_missile']}/{d['shield_hp_per_salvo']}")
        if per * n >= SW_GIGA_BUBBLE:
            _err(f"{who}: uma salva tira {per * n} de escudo (>= {SW_GIGA_BUBBLE}, a bolha giga do SW)")
        if op["ExplosiveResourceDrain_battery"] != drain:
            _err(f"{who}: dreno do casco {op['ExplosiveResourceDrain_battery']} != dreno do escudo {drain}")
        pq = s.get("poraque") or {}
        if pq.get("drain") != drain or pq.get("Damage") != hs["Damage"]:
            _err(f"{who}: poraque_2.per_missile difere de modes[].damage")
    elif t == "nuclear":
        wh = s["children"][0]
        tot = wh["damage"]["op"] + wh["damage"]["struct"]
        if tot * n != d["alpha_explosive_per_salvo"] or wh["damage"]["op"] != d["warhead_operational"] \
                or wh["damage"]["struct"] != d["warhead_structural"]:
            _err(f"{who}: ogiva {wh['damage']} difere de modes[].damage")
        if d.get("decoys"):
            _err(f"{who}: a Iara 2.0 nao solta nada alem da ogiva (decoys = {d['decoys']})")
        if wh["box"] is None:
            _err(f"{who}: BoxPhysics da ogiva ausente ({m['flight'].get('physics')!r})")
        hp_ok = [int(k) for k in (D.SWITCH_DEFS["missiles.iara_hp"].get("values") or {})]
        if s["hp"] not in hp_ok or wh["hp"] != s["hp"]:
            _err(f"{who}: HP {s['hp']} fora de missiles.iara_hp {hp_ok}")
        lim = MISSILE_VARIANTS.get("category_limits") == "on"
        if lim and "bs_limit_nuke" not in lch_extra:
            _err(f"{who}: lancador nuclear sem o limite por nave bs_limit_nuke (missiles.category_limits = on)")
        if m.get("overclock_affects") or m.get("overclock"):
            _err(f"{who}: o overclock nunca pode acelerar a recarga nuclear")


# ============================================================================= lancadores
def _base_part(L):
    """launchers[].base_part sem o sufixo _overclock (o gerador poe o sufixo quando o overclock esta ligado)."""
    base = str(L["base_part"]).split()[0]
    return base[:-len("_overclock")] if base.endswith("_overclock") else base


def _glow(t):
    pal = D.PAL
    src = {"he": ("msl_he", "hull"), "cluster": ("cluster", "band"), "emp": ("msl_emp", "hull"),
           "nuclear": ("nuclear", "hull")}[t]
    return list((pal.get(src[0]) or {}).get(src[1]) or [255, 200, 120])


def _art3d(L):
    """meta.json de art3d/<pasta do lancador> (kind 'launcher'), com a lista de arquivos e os modos SO dos tipos
    2.0 do lancador (as sobreposicoes de tipos que sairam nao vao para o mod). None = arte procedural
    (BS_ARTE_PROCEDURAL=1)."""
    import art3d as A3
    d = L.get("art3d_dir") or _short(L["id"])
    meta = A3.load_meta(d)
    if meta is None:
        A3.require(d, None)
        return None, d
    if meta.get("kind") != "launcher":
        _err(f"art3d/{d}: meta.json nao e de lancador (kind {meta.get('kind')})")
        return None, d
    if meta.get("id") and meta["id"] != L["id"]:
        _err(f"art3d/{d}: meta.id {meta['id']} nao e {L['id']}")
    if list(meta.get("size") or []) != list(L["size"]):
        _err(f"art3d/{d}: tamanho {meta.get('size')} difere do spec {L['size']}")
    types = {m["missile_type"] for m in L["modes"]}
    meta = copy.deepcopy(meta)
    meta["modes"] = {k: v for k, v in (meta.get("modes") or {}).items() if k in types}
    drop = re.compile(r"^(cells|shutters)_([a-z]+)_")
    meta["files"] = [f for f in meta.get("files", []) if not (drop.match(f) and drop.match(f).group(2) not in types)]
    return meta, d


def _launcher(L):
    short = _short(L["id"])
    w, h = L["size"]
    pm = L["art"]["part_meta"]
    tier = L["tier"]
    per_launcher = MS["toggle"]["per_launcher"].get(L["codename"])
    if per_launcher is not None and list(per_launcher) != list(L["available_choices"]):
        _err(f"{L['codename']}: available_choices {L['available_choices']} != toggle.per_launcher {per_launcher}")
    ripple_n, burst_n = _ripples(L, L["modes"])
    oc_info = D.launcher_overclock(L)
    if oc_info and MISSILE_VARIANTS.get("early_overclock") == "disabled" and tier == "early":
        oc_info = None
    extra = list(D.EXTRA_CATEGORIES.get(L["id"], []))
    ck_by = {c["mode_index"]: c for c in L.get("cookoff_at_full_stock") or []}
    heat_const = sorted({(m.get("overclock") or {}).get("heat_per_s_constant") for m in L["modes"]
                         if m.get("overclock")} - {None})
    modes = []
    for m in L["modes"]:
        t = m["missile_type"]
        i = m["toggle_index"]
        who = f"{L['codename']}/{t}"
        if D.MISSILE_INDEX.get(t) != i:
            _err(f"{who}: toggle_index {i} difere da tabela fixa MISSILE_INDEX {D.MISSILE_INDEX.get(t)}")
        if i not in L["available_choices"]:
            _err(f"{who}: indice {i} fora de available_choices {L['available_choices']}")
        cells, parts = int(m["rack_units"]), m["charges_per_rack_unit"]
        if m["missiles_per_salvo"] % cells:
            _err(f"{who}: {m['missiles_per_salvo']} misseis por salva nao divide em {cells} unidades")
        mpu = m["missiles_per_salvo"] // cells
        st = m["stock"]
        storage = st["MagStorage_MaxResources"]
        oc = m.get("overclock") if (oc_info and m.get("overclock_affects")) else None
        key = _res_key(m["resource"])
        try:
            geo = cell_layout(pm["cells"], m["layout"], cells, who)
        except (ValueError, NotImplementedError) as e:
            _err(str(e))
            geo = {"units": [], "pods": [], "shutters": [], "tube_r": pm["cells"].get("tube_r", 0.09), "form": "tube",
                   "tubes_per_unit": 1}
        mode = {
            "index": i, "mode": i, "key": key, "type": t, "codename": m["variant_codename"],
            "name_en": CHOICE_BY_TYPE[t]["name_en"], "name_pt": CHOICE_BY_TYPE[t]["name_ptbr"],
            "res": m["resource"], "storage": storage, "internal_storage_units": storage,
            "resupply_threshold": C.half(storage), "cells": cells, "parts": parts, "mpu": mpu,
            "reload": m["reload_s_per_unit"], "ripple_ticks": ripple_n[t], "ripple": f"{ripple_n[t]}/30",
            "layout": m["layout"], "vent": int(oc["vent_charges_per_salvo"]) if oc else 0,
            "oc_factor": oc["reload_divide"] if oc else None,
            "heat_per_charge": oc["heat_per_charge_loaded"] if oc else None,
            "shot": _short(m["shot_ids"][0]), "shot_ids": list(m["shot_ids"]), "computed": m["computed"],
            "glow": _glow(t), "geo": geo, "names": C.index_names(i, key),
            "feed_q": int((m.get("feeder") or {}).get("FromQuantity", 1)), "cookoff": ck_by.get(i), "spec2": m,
        }
        modes.append(mode)
    modes.sort(key=lambda x: x["index"])
    meta, art_dir = _art3d(L)
    crew_pos = None
    if meta and meta.get("crew_pos"):
        crew_pos = [tuple(c) for c in meta["crew_pos"]][:L["crew"]]
        if len(crew_pos) < L["crew"]:
            _err(f"{L['codename']}: art3d/{art_dir} tem {len(meta['crew_pos'])} postos de tripulacao, crew {L['crew']}")
    base_ticks = min(x["ripple_ticks"] for x in modes)
    lch = {
        "id": L["id"], "short": short, "key": _key(short), "kind": "launcher",
        "name_en": L["name_en"], "name_pt": L["name_ptbr"], "codename": L["codename"], "tier": tier,
        "size": list(L["size"]), "base_part": _base_part(L), "crew": L["crew"], "cp": L["command_points"],
        "hp": L["max_health"], "cost": [list(c) for c in L["build_cost"]], "ring": L.get("prohibit_ring_tiles", 1),
        "arc": L["arc_deg"], "rotate": L["rotate_speed_deg_s"], "threshold": L["fire_threshold_deg"],
        "categories": list(L["type_categories"]), "extra_categories": extra,
        "ripple_ticks": base_ticks, "ripple": f"{base_ticks}/30", "ripple_s": base_ticks / 30,
        "burst_delay": f"{burst_n}/30", "burst_ticks": burst_n,
        "toggle_id": MS["toggle"]["toggle_id"], "available": list(L["available_choices"]),
        "available_choices": list(L["available_choices"]), "selector": True,
        "default_mode": modes[0]["index"], "modes": modes,
        "oc": None, "oc_glow": bool(oc_info),
        "geo": {"pivot": list(pm["pivot"]), "turret_size": pm["turret_box"], "collider": pm["collider"],
                "ring_r": pm["ring_r"], "backblast": [[b[1], b[0]] for b in pm.get("backblast", [])],
                "accent": pm.get("accent", "amber"), "pitch_deg": pm.get("pitch_deg", 35)},
        "fx": copy.deepcopy(D.FX[f"launch_{TIER_LETTER[tier]}"]),
        "art": {"style": f"launcher_{short.rsplit('_', 1)[-1]}", "accent": "ammo"},
        "art3d_dir": art_dir, "art3d": meta, "crew_pos": crew_pos,
        "logistica": L.get("logistica"), "belt": L.get("belt"), "fita_fx_location": [w / 2, h - 0.5],
        "per_ship_limit": L.get("per_ship_limit"), "range": L["range_m"], "spec": L, "variants": MISSILE_VARIANTS,
    }
    if oc_info:
        lch["oc"] = {"reload_factor": oc_info["reload_factor"], "per_mode": dict(oc_info["per_mode"]),
                     "excluded": list(oc_info["excluded"]), "name_en": oc_info["name_en"],
                     "name_pt": oc_info["name_ptbr"], "tech": oc_info.get("tech"),
                     "heat_per_second": heat_const[0] if heat_const else 0}
        if len(heat_const) > 1:
            _err(f"{L['codename']}: calor constante do overclock difere entre modos {heat_const}")
    return lch


def _check_launcher(lch, L):
    """As regras geradas tem que reproduzir os numeros do spec (salva, ciclo, estoque, cook-off, logistica)."""
    who = L["codename"]
    burst = lch["burst_ticks"] / 30
    if [m["index"] for m in lch["modes"]] != list(L["available_choices"]):
        _err(f"{who}: modos {[m['index'] for m in lch['modes']]} != available_choices {L['available_choices']}")
    if lch["oc"] is None and any(m.get("overclock_affects") for m in L["modes"]) and lch["tier"] != "early":
        _err(f"{who}: modos com overclock_affects sem overclock na peca (base_part {L['base_part']})")
    if lch["tier"] == "early" and lch["oc"]:
        _err(f"{who}: lancador de inicio de jogo com overclock")
    if not lch["crew_pos"] and lch["art3d"]:
        _err(f"{who}: art3d sem crew_pos")
    for m in lch["modes"]:
        s2 = m["spec2"]
        mw = f"{who}/{m['type']}"
        rip = m["ripple_ticks"] / 30
        if m["ripple_ticks"] % lch["ripple_ticks"]:
            _err(f"{mw}: ripple {m['ripple']} nao e multiplo do intervalo da torre {lch['ripple']}")
        salvo = (m["cells"] - 1) * rip + (m["mpu"] - 1) * burst
        cycle = m["cells"] * m["reload"] + salvo
        if abs(salvo - s2["salvo_duration_s"]) > 0.002:
            _err(f"{mw}: salva {salvo:.4f} s, spec {s2['salvo_duration_s']}")
        if abs(cycle - s2["cycle_s"]) > 0.01:
            _err(f"{mw}: ciclo {cycle:.4f} s, spec {s2['cycle_s']}")
        if m["cells"] * m["parts"] != s2["charges_per_salvo"]:
            _err(f"{mw}: {m['cells']} x {m['parts']} cargas por salva, spec {s2['charges_per_salvo']}")
        st = s2["stock"]
        if st["ReadyRack_units"] != m["cells"]:
            _err(f"{mw}: ReadyRack {m['cells']}, spec stock {st['ReadyRack_units']}")
        if m["storage"] != 4 * m["cells"] * m["parts"] or st["total_charges"] != m["storage"] + m["cells"] * m["parts"]:
            _err(f"{mw}: estoque {m['storage']} + rack {m['cells'] * m['parts']} nao sao 4 + 1 salvas "
                 f"(spec {st['total_charges']})")
        for v in (m["storage"], m["cells"], m["parts"], m["mpu"]):
            if not isinstance(v, int) or v <= 0 or v > 2 ** 31 - 1:
                _err(f"{mw}: valor Int32 invalido {v!r}")
        cc = s2.get("crew_consumer") or {}
        if cc.get("ResupplyThreshold") is not None and cc["ResupplyThreshold"] != m["resupply_threshold"]:
            _err(f"{mw}: ResupplyThreshold {m['resupply_threshold']}, spec {cc['ResupplyThreshold']}")
        fd = s2.get("feeder") or {}
        if fd and (fd.get("FromQuantity") != fd.get("ToQuantity") or fd.get("Interval") != 0.1):
            _err(f"{mw}: alimentador do spec fora do padrao q por 0,1 s ({fd})")
        if lch["oc"] and m["oc_factor"]:
            oc = s2["overclock"]
            ocyc = m["cells"] * m["reload"] / m["oc_factor"] + salvo
            if abs(ocyc - oc["cycle_s"]) > 0.01:
                _err(f"{mw}: ciclo em overclock {ocyc:.4f} s, spec {oc['cycle_s']}")
            if abs(m["vent"] - round(m["cells"] * m["parts"] / 16)) > 1e-9:
                _err(f"{mw}: respiro {m['vent']} cargas, regra 6,25 % da salva da "
                     f"{round(m['cells'] * m['parts'] / 16)}")
            per = (lch["oc"].get("per_mode") or {}).get(m["type"])
            if per is not None and abs(per - m["oc_factor"]) > 1e-9:
                _err(f"{mw}: divisor do overclock {m['oc_factor']} difere de launcher_overclock {per}")
        ck = m["cookoff"]
        if not ck:
            _err(f"{mw}: modo sem cook-off no spec (cookoff_at_full_stock)")
            continue
        full = m["storage"] + m["cells"] * m["parts"]
        if ck["charges_full"] != full:
            _err(f"{mw}: cook-off charges_full {ck['charges_full']} != estoque cheio {full}")
        if ck["family"] != m["res"]:
            _err(f"{mw}: cook-off da familia {ck['family']} != {m['res']}")
        ps = ck.get("per_storage") or {}
        share = {f"MagStorage_{m['index']}": m["storage"] / full, f"ReadyRack_{m['index']}": m["cells"] * m["parts"] / full}
        for comp_id, f in share.items():
            got = ps.get(comp_id)
            if got is None:
                _err(f"{mw}: cook-off sem per_storage.{comp_id}")
                continue
            if ck["kind"] == "blast":
                for k_tot, k_bv in (("op_total_full", "op_BaseValue"), ("struct_total_full", "struct_BaseValue")):
                    want = ck[k_tot] * f
                    if abs(got[k_bv] - want) > 0.5 or not isinstance(got[k_bv], int):
                        _err(f"{mw}: cook-off {comp_id}.{k_bv} {got[k_bv]} != {k_tot} x {f:.4f} = {want:.1f}")
            elif str(ck["kind"]).startswith("ExplosiveResourceDrain"):
                want = ck["drain_total_full"] * f
                if abs(got - want) > 0.5:
                    _err(f"{mw}: dreno do cook-off {comp_id} {got} != {want:.1f}")
            else:
                _err(f"{mw}: cook-off de tipo desconhecido {ck['kind']}")
    # HE + submunicao dividem o teto 1.x 50/50 (as duas familias valem o mesmo cheias)
    he = next((m["cookoff"] for m in lch["modes"] if m["type"] == "he"), None)
    cl = next((m["cookoff"] for m in lch["modes"] if m["type"] == "cluster"), None)
    if he and cl and (he["op_total_full"], he["struct_total_full"]) != (cl["op_total_full"], cl["struct_total_full"]):
        _err(f"{who}: HE e submunicao com tetos de cook-off diferentes (regra 50/50)")
    # logistica do spec (o seam do WP05 gera a partir dela): empurra/puxa/acoplamento por modo
    lg = (lch.get("logistica") or {}).get("teleporte") or {}
    push = next((v for k, v in lg.items() if k.startswith("empurra")), None) or []
    pull = (next((v for k, v in lg.items() if k.startswith("puxa")), None) or {}).get("per_mode") or []
    acop = next((v for k, v in (lch.get("logistica") or {}).items() if k.startswith("acoplamento")), None) or {}
    for m in lch["modes"]:
        mw = f"{who}/{m['type']}"
        e = next((x for x in push if x.get("index") == m["index"]), None)
        if not e or e.get("key") != m["key"] or not e.get(f"FitaEntra_{m['key']}"):
            _err(f"{mw}: logistica.teleporte sem FitaEntra_{m['key']} para o modo {m['index']}")
        elif e[f"FitaEntra_{m['key']}"].get("ComponentID") != f"MagStorage_{m['index']}":
            _err(f"{mw}: FitaEntra_{m['key']} nao aponta para MagStorage_{m['index']}")
        p = next((x for x in pull if x.get("index") == m["index"]), None)
        al = (p or {}).get(f"Alimentador_{m['index']}") or {}
        if not p or al.get("FromQuantity") != m["feed_q"]:
            _err(f"{mw}: puxa: Alimentador_{m['index']} q {al.get('FromQuantity')} != feeder {m['feed_q']}")
        a = next((x for x in (acop.get("per_mode") or []) if x.get("index") == m["index"]), None)
        aa = (a or {}).get(f"AlimentadorAcoplado_{m['index']}") or {}
        if not a or aa.get("FromQuantity") != m["feed_q"]:
            _err(f"{mw}: acoplamento: AlimentadorAcoplado_{m['index']} q {aa.get('FromQuantity')} != {m['feed_q']}")
    # Mula: HE e submunicao com q = 2 no 'puxa' (fora do build)
    if lch["short"] == "bs_msl_quad":
        q2 = sorted(m["type"] for m in lch["modes"] if m["feed_q"] == 2)
        if q2 != ["cluster", "he"]:
            _err(f"{who}: alimentador q = 2 em {q2}, o spec pede HE e submunicao")
    # limite por nave: so a Mula (Iara)
    lim_on = MISSILE_VARIANTS.get("category_limits") == "on"
    has_lim = "bs_limit_nuke" in lch["extra_categories"]
    nuke = any(m["type"] == "nuclear" for m in lch["modes"])
    if nuke and lim_on and not has_lim:
        _err(f"{who}: modo nuclear sem bs_limit_nuke")
    if has_lim and not nuke:
        _err(f"{who}: bs_limit_nuke sem modo nuclear")


def _convert():
    for L in MSPEC["launchers"]:
        lch = _launcher(L)
        for ms in sorted(L["modes"], key=lambda x: x["toggle_index"]):
            s = _missile(L, ms)
            _check_missile(s, L, ms, lch["extra_categories"])
            MISSILES.append(s)
            # numeros do tiro que o tooltip do lancador mostra (sem referencia cruzada ao arquivo do tiro)
            mode = next(x for x in lch["modes"] if x["index"] == ms["toggle_index"])
            mode["missile"] = {k: s[k] for k in ("file", "id", "stat_damage", "stat_radius", "range", "speed",
                                                 "accel", "turn", "hp")}
        _check_launcher(lch, L)
        LAUNCHERS.append(lch)
    ids = [s["id"] for s in MISSILES] + [c["id"] for s in MISSILES for c in s["children"]]
    if len(ids) != len(set(ids)):
        _err("tiros de missil com ID repetido")
    gone = set(D.SPEC["removed_ids"].get("missile_shots") or [])
    for i in ids:
        if i in gone:
            _err(f"tiro removido na 2.0 voltou: {i}")
    if sorted(c[0] for c in MISSILE_CHOICES) != sorted(D.MISSILE_INDEX.values()):
        _err(f"seletor bs_missile_type com escolhas {[c[0] for c in MISSILE_CHOICES]}")
    lab = next((c for c in D.TOGGLES["bs_missile_type"]["choices"] if c["index"] == 1), {})
    if lab.get("label_ptbr") != "Submunição":
        _err(f"bs_missile_type indice 1 com rotulo {lab.get('label_ptbr')!r} (esperado 'Submunição')")


_convert()
MISSILE_BY_FILE = {s["file"]: s for s in MISSILES}
LAUNCHER_BY_ID = {lch["id"]: lch for lch in LAUNCHERS}


def selfcheck_data(strict=True):
    """Problemas dos dados (lista vazia = OK). strict: levanta ValueError com a lista (uso em linha de comando)."""
    errs = list(ERRORS)
    if strict and errs:
        raise ValueError("bs_data_missiles: " + "; ".join(errs))
    return errs


# ============================================================================= textos (gancho strings)
FLAVOR = {
    "bs_msl_box": ("A RAM-style micro-missile box: the gunner cranks it around and twelve micro-missiles hiss out, "
                   "pair by pair.",
                   "Uma caixa de micromísseis estilo RAM: o atirador gira a caixa e doze micromísseis saem chiando, "
                   "de dois em dois."),
    "bs_msl_twin": ("Two octagonal pods flank an armored sensor dome; a full rack is a two-second drum-roll of "
                    "sixteen missiles, right pod first.",
                    "Dois casulos octogonais ladeiam uma cúpula blindada com olho sensor; com as células cheias, vem "
                    "um rufar de dezesseis mísseis em dois segundos, o casulo direito primeiro."),
    "bs_msl_quad": ("A headless armored body carries four long pods on hydraulic arms: a stampede of 48 heavy "
                    "missiles in three seconds. Loaded, it is the most dangerous part of your ship.",
                    "Um corpo blindado sem cabeça carrega quatro casulos longos em braços hidráulicos: um estouro de "
                    "48 mísseis pesados em três segundos. Carregada, é a peça mais perigosa da sua nave."),
}
TYPE_WORD = {"he": ("HE", "HE"), "cluster": ("cluster", "submunição"), "emp": ("EMP", "PEM"),
             "nuclear": ("nuclear", "nuclear")}


def _n_en(x, nd=2):
    return f"{x:.{nd}f}".rstrip("0").rstrip(".")


def _n_pt(x, nd=2):
    return _n_en(x, nd).replace(".", ",")


def _launcher_texts(lch):
    """(en, pt) de Parts/<key>Desc."""
    import bs_strings as S
    m0 = lch["modes"][0]
    n = m0["cells"] * m0["mpu"]
    salvo = (m0["cells"] - 1) * m0["ripple_ticks"] / 30 + (m0["mpu"] - 1) * lch["burst_ticks"] / 30
    cycle = m0["cells"] * m0["reload"] + salvo
    unit_en, unit_pt = ("cassette", "um cassete") if m0["mpu"] > 1 else ("cell", "uma célula")
    fl_en, fl_pt = FLAVOR.get(lch["short"], ("Deck missile launcher.", "Lança-mísseis de convés."))
    mis_en = ", ".join(f"{m['codename']} ({TYPE_WORD[m['type']][0]})" for m in lch["modes"])
    mis_pt = ", ".join(f"{m['codename']} ({TYPE_WORD[m['type']][1]})" for m in lch["modes"])
    sizes = {}
    for m in lch["modes"]:
        sizes.setdefault(m["cells"] * m["mpu"], []).append(m["codename"])
    var_en = var_pt = ""
    if len(sizes) > 1:
        var_en = " Missiles per salvo: " + "; ".join(f"{', '.join(v)} {k}" for k, v in sizes.items()) + "."
        var_pt = " Mísseis por salva: " + "; ".join(f"{', '.join(v)} {k}" for k, v in sizes.items()) + "."
    stock_en = ", ".join(f"{m['codename']} {m['storage']}" for m in lch["modes"])
    crew_en = f"{lch['crew']} crew"
    crew_pt = f"{lch['crew']} tripulante" + ("s" if lch["crew"] > 1 else "")
    dry = MISSILE_VARIANTS.get("dry_flush", "debounced")
    dry_en, dry_pt = {
        "debounced": ("; if no charge arrives for a whole reload, the loaded cells fire anyway",
                      "; se nenhuma carga chegar por uma recarga inteira, as células já carregadas disparam mesmo "
                      "assim"),
        "instant": ("; with the magazine dry, the loaded cells fire anyway",
                    "; com o carregador vazio, as células já carregadas disparam mesmo assim")}.get(dry, ("", ""))
    oc_en = " Can be overclocked." if lch.get("oc") else ""
    oc_pt = " Aceita overclock." if lch.get("oc") else ""
    lim_en = lim_pt = ""
    if "bs_limit_nuke" in lch["extra_categories"]:
        mx = next((lim[1] for lim in D.LIMITS if lim[0] == "bs_limit_nuke"), 2)
        lim_en = f"\n\nLimit: {mx} per ship (it is the only launcher of the nuclear missile)."
        lim_pt = f"\n\nLimite: {mx} por nave (é o único lançador do míssil nuclear)."
    en = (f"{fl_en} \"{lch['codename']}\"\n\n{S.TIER_EN[lch['tier']]} deck missile launcher. A full rack ripples "
          f"{n} missiles in {_n_en(salvo)} s, then a crewed autoloader refills it one {unit_en} at a time "
          f"({_n_en(m0['reload'])} s each; reloading stops while nobody mans it): one salvo every {_n_en(cycle, 1)} s. "
          f"Range {lch['range']} m. Missiles: {mis_en}.{var_en}\n\nNeeds no power: {crew_en} and missile charges "
          f"in one internal magazine per missile type (4 salvos each: {stock_en}). Switching the missile type costs "
          f"one full reload{dry_en}. The missiles fly over your own deck and can be shot down by point defense. A "
          f"loaded launcher cooks off when it burns or is destroyed.{oc_en}{lim_en}<string id='BSModTag'/>")
    pt = (f"{fl_pt} \"{lch['codename']}\"\n\n{S.TIER_PT[lch['tier']]} - lança-mísseis de convés. Com todas as "
          f"células carregadas, dispara {n} mísseis em sequência em {_n_pt(salvo)} s; depois um autocarregador "
          f"tripulado recarrega {unit_pt} por vez ({_n_pt(m0['reload'])} s cada; sem tripulação no posto a recarga "
          f"para): uma salva a cada {_n_pt(cycle, 1)} s. Alcance {lch['range']} m. Mísseis: {mis_pt}.{var_pt}\n\n"
          f"Não usa energia: {crew_pt} e cargas de míssil num carregador interno por tipo de míssil (4 salvas cada: "
          f"{stock_en}). Trocar o tipo de míssil custa uma recarga completa{dry_pt}. Os mísseis passam por cima do "
          f"próprio convés e podem ser abatidos pelos pontos de defesa. Carregado, o lançador explode quando pega "
          f"fogo ou é destruído.{oc_pt}{lim_pt}<string id='BSModTag'/>")
    return en, pt


def strings(DATA=None):
    """(en, pt) dos lancadores (so os de DATA.LAUNCHERS, ou seja, escritos neste build): Parts/<key>, Icon, Desc,
    Overclock, OverclockDesc e StatCategories/<key>_<tipo>. Seletor, techs (_BBOC, _BBAmmo) e recursos sao do
    nucleo (bs_strings, WP01)."""
    import bs_strings as S
    Dm = DATA if DATA is not None else D
    en = {"Parts": {}, "StatCategories": {}}
    pt = {"Parts": {}, "StatCategories": {}}
    for lch in Dm.LAUNCHERS:
        k = lch["key"]
        en["Parts"][k] = lch["name_en"]
        pt["Parts"][k] = lch["name_pt"]
        en["Parts"][k + "Icon"] = lch["codename"][:18]
        pt["Parts"][k + "Icon"] = lch["codename"][:18]
        en["Parts"][k + "Desc"], pt["Parts"][k + "Desc"] = _launcher_texts(lch)
        if lch.get("oc"):
            oc = D.launcher_overclock(lch["spec"]) or {}
            en["Parts"][k + "Overclock"] = f"Overclocked {lch['name_en']}"
            pt["Parts"][k + "Overclock"] = f"{lch['name_pt']} (Overclocking)"
            en["Parts"][k + "OverclockDesc"] = S.launcher_oc_text(D, oc, "en")
            pt["Parts"][k + "OverclockDesc"] = S.launcher_oc_text(D, oc, "pt")
        for m in lch["modes"]:
            for grp, name in ((en, m["name_en"]), (pt, m["name_pt"])):
                # o nome do seletor ja pode trazer o codinome (Submunicao: '... (Piranha)')
                grp["StatCategories"][f"{k}_{m['type']}"] = (name if m["codename"] in name
                                                            else f"{name} ({m['codename']})")
    return en, pt


# ----------------------------------------------------------------------------- carga isolada / placeholders
def _art_placeholders():
    """Com os lancadores no build (os tres modulos de missil com API 2): celulas cuja arte ainda e de outro layout
    (cluster8 / heavy8 antes do re-render do WP13) ou sem art3d entram em D.PLACEHOLDERS ja na carga, para o
    spec2_check (processo separado, sem o gancho parts) tambem listar; o WP14b exige a lista vazia."""
    from bsgen import launchers as BL
    for lch in LAUNCHERS:
        notes = list(BL.launcher_geometry(lch)["art_notes"])
        if not lch.get("art3d"):
            notes.append(f"{lch['short']}: art3d/{lch['art3d_dir']} ausente (arte procedural)")
        for note in notes:
            if note not in D.PLACEHOLDERS:
                D.PLACEHOLDERS.append(note)


if D.launchers_ready():
    # importado antes do bs_data (python3 -c 'import bs_data_missiles'): o load_launchers do bs_data rodou com
    # este modulo pela metade; liga de novo agora que as listas existem (idempotente)
    if not D.LAUNCHERS:
        D.load_launchers()
    _art_placeholders()
