"""Gerador das fabricas F1-F6 do Bullet Strike 2.0 (dono: WP04; modulo de CONTEUDO, API 2).

Gancho parts(out, DATA, ctx) do build_mod: as fabricas de DATA.FACTORIES (SPEC.factories, receitas ja transformadas
pelo bs_data: guns.ac_cost e econ.factory_adjacency = vanilla x1,5 - nunca aplicar de novo aqui).

Fabricas de ETAPA UNICA: materia-prima (enxofre, ferro, cobre, uranio bruto; triaco, bobina, hiperbobina refinados)
vira municao direto, sem fabrica vanilla no meio.
  F1 Prensa HE 2x2 (factory_ammo)          F2 Municao Especial 4x3 (factory_mine; ID 1.x bs_factory_mag_ap mantido)
  F3 Celulas 3x3 (factory_he + cobre [1,2]) F4 Misseis 3x3 (factory_he)
  F5 Ogivas Nucleares 4x4 (factory_nuke)    F6 Forja de Projeteis 3x4 (factory_emp; so com rail.enabled)

Arquitetura (SPEC.multi_recipe_implementation; so padroes do jogo base 0.30.x e do SW:ACD 0.30.4):
  * Entradas: uma TypedResourceGrid Entrada_<insumo> por insumo (a tripulacao entrega, prioridade Factory_Supply) e
    um divisor compartilhado Divisor_<insumo> (InlineResourceConverter FromQuantity 1 / ToQuantity N, factory_he
    l.150-165); cada receita saca draw_Quantity inteiro do divisor (SW factory_durasteel.rules:231-237 saca 2 de 1:3).
    Reserva do teste T-F2-SPLIT: DIVISOR_POR_RECEITA (env BS_FABRICA_DIVISOR=por_receita ou a chave extra
    'econ.factory_splitter' = 'por_receita' do bullet_strike_switches.json) -> um divisor por receita
    (Divisor_<insumo>_<receita>), todos lendo a mesma grade.
  * Por receita k: grade de saida fixa Saida_<k> (SuppliesResources true: sem Fita a tripulacao recolhe dali como
    numa fabrica vanilla - REQ3) e conversor Conversor_<k> sempre presente com OperationalToggle Ready_<k> =
    MultiToggle All [IsOperational, ModeToggle_<sel>, divisores da receita]. Nada de ToggledComponents em volta de
    estoque: trocar de receita nunca derruba o que ja foi produzido.
  * Seletor (F2 bs_ammo_type [1,2,3,4] Default 1; F3 bs_cell_type [0,1]; F4 bs_missile_type [0,1,2]): UIToggle com
    AvailableChoices + ModeToggle_<sel> (missile_launcher.rules l.125-146). As PartToggles sao do WP01 (infra): este
    modulo so referencia (sem gancho toggles()).
  * Intervalo: BaseValue = interval_s_base (ja x1,5 com a vizinhanca) com BuffRemap Overclock (300 % / 150 % da
    bateria por ciclo) e, com econ.factory_adjacency = vanilla, o modificador Factory Divide (factory_ammo l.175-180).
  * VIZINHANCA (econ.factory_adjacency): 'vanilla' (padrao do addendum) emite os 4 itens do jogo base -
    ReceivableBuffs [Factory], os modificadores BuffType Factory (intervalos e BeltSpeedFactor), o GridBuffProvider
    Factory 25 % GridDistance 1 e a estatistica FactoryBuff; 'off' nao emite NENHUM deles (a base
    base_part_*_overclock so acrescenta [Overclock], nada herdado para sobrescrever).
  * Calor de overclock: um ResourceChange por conversor (HEAT_<RECEITA> por ciclo) e um StatProvider HeatGeneration
    por receita, ligado so no modo escolhido.
  * Cook-off por saida: DeathEffects Explosao_<k> escalado por FactorHitEffectsWith Saida_<k> (factory_he l.1207-1256);
    total do molde vanilla / numero de saidas (J1R3-2); PEM = ExplosiveResourceDrain (factory_emp l.1008-1050).
  * LOGISTICA SO PELO SEAM (WP05, J2R2-MED): INTAKE = common.content_module('bsgen.intake');
    C.call(INTAKE, 'part_fields', f, ctx) -> {TypeCategories_add, ReceivableBuffs_add} e, por receita,
    C.call(INTAKE, 'factory_output', comp, f, rc, ctx) (teleporte jeito B: RedeFab/AncoraSaida_<k>/ParaPaiois_<k>/
    Envio_<k>; tripulacao: acoplamento EntregaAcoplada_<k>). Este modulo NUNCA escreve PartCriteria,
    NetworkResource* nem buffs da Fita.
  * Arte: f['art3d'] (art3d/<f['art3d_dir']>, a F2 le art3d/bs_factory_special) via make_art.factory_art; placa de
    modo '../bs_placas/placa_<modo>.png' (art3d/bs_placas publicada em parts/bs_placas) num ToggledComponents por
    modo; F3: banco PEM (overlay do meta) no modo PEM e as luzes do banco so produzindo PEM (roof_lights_fancy).
"""

import os
import re

from rules_dsl import Q, Inh, comment, render
from bsgen import common as C

API = 2

RES_STACK = {  # MaxStackSize dos recursos vanilla (resources/*.rules)
    "bullet": 20, "sulfur": 5, "steel": 40, "coil": 40, "coil2": 40, "tristeel": 40, "diamond": 5,
    "uranium": 5, "carbon": 5, "copper": 5, "gold": 5, "iron": 5, "tritanium": 5,
    "hyperium": 20, "processor": 5,
}

# Categoria vanilla de cada insumo (factory_mine uses_iron/uses_ammo, factory_ammo uses_sulfur, factory_processor
# uses_coils, factory_emp uses_copper, factory_nuke uses_uranium). Triaco e hiperbobina nao tem categoria no jogo
# base (nenhuma fabrica vanilla consome): ficam sem categoria.
RES_CATEGORY = {"bullet": "uses_ammo", "sulfur": "uses_sulfur", "coil": "uses_coils", "copper": "uses_copper",
                "iron": "uses_iron", "uranium": "uses_uranium"}

# nome dos insumos nos textos: (en, pt, refinado?) - nomes do jogo (strings Resource/<X> do en.rules / pt-br.rules)
# (en, pt, refinado?, qualificador pt: bruto / refinado / refinada)
INPUT_NAMES = {
    "sulfur": ("Sulfur", "enxofre", False, "bruto"), "iron": ("Iron", "ferro", False, "bruto"),
    "copper": ("Copper", "cobre", False, "bruto"), "uranium": ("Uranium", "urânio", False, "bruto"),
    "tristeel": ("Tri-Steel", "triaço", True, "refinado"), "coil": ("Coil", "bobina", True, "refinada"),
    "coil2": ("Hyper-Coil", "hiperbobina", True, "refinada"),
}

# rotulo curto de cada receita (en, pt): botao do seletor / linhas de estatistica
RECIPE_LABEL = {
    "he": ("HE", "HE"), "ap": ("AP", "AP"), "sap": ("SAP", "SAP"), "ac": ("AC", "AC"), "frag": ("FRAG", "FRAG"),
    "plasma": ("Plasma", "Plasma"), "pem": ("EMP", "PEM"), "msl_he": ("HE", "HE"),
    "msl_cluster": ("Cluster", "Submunição"), "msl_emp": ("EMP", "PEM"), "msl_nuke": ("Warhead", "Ogiva"),
    "slug": ("Slug", "Projétil"),
}

# unidade de cada familia de recurso nas linhas por receita (en, pt)
UNIT_NAMES = {"cartuchos": ("magazine", "carregador"), "celulas": ("cell", "célula"), "misseis": ("charge", "carga"),
              "projeteis": ("slug", "projétil")}

# nome do UIToggle do seletor na peca (mesmo nome usado nas armas: guns.ammo_selector)
SELECTOR_COMPONENT = {"bs_ammo_type": "AmmoTypeToggle", "bs_cell_type": "CellTypeToggle",
                      "bs_missile_type": "MissileTypeToggle"}

# sons de cada fabrica: (pasta vanilla, som do maquinario ligado, sons de cada item pronto)
SOUNDS = {
    "ammo": ("factory_ammo", "cannon_ammo_factory_idle.wav",
             [f"cannon_ammo_factory_putdown_0{i}.wav" for i in range(1, 8)]),
    "mine": ("factory_mine", "mine_factory_idle.wav", [f"mine_factory_putdown_0{i}.wav" for i in range(1, 6)]),
    "he": ("factory_he", "he_missile_factory_idle.wav", [f"missile_factory_putdown_0{i}.wav" for i in range(1, 6)]),
    "emp": ("factory_emp", "emp_missile_factory_idle.wav",
            [f"emp_missile_factory_putdown_0{i}.wav" for i in range(1, 6)]),
    "nuke": ("factory_nuke", "nuclear_missiles_factory_idle.wav",
             [f"nuclear_missiles_factory_putdown_0{i}.wav" for i in range(1, 6)]),
}
FACTORY_SOUND = {"F1": "ammo", "F2": "ammo", "F3": "emp", "F4": "he", "F5": "nuke", "F6": "mine"}

# molde vanilla do cook-off (soma das saidas cheias <= isto; J1R3-2): (operacional, estrutural, dreno de bateria)
#   F1 factory_ammo l.780-829; F2 factory_mine l.823-851; F3/F4 factory_he l.1207-1256 (+ dreno: F3 250000 =
#   factory_emp / 2 pela regra do spec, F4 = factory_emp l.1016-1018 inteiro); F5 factory_nuke l.896-935;
#   F6 sem molde vanilla (projeteis inertes; o proprio spec e o teto)
COOKOFF_MOLD = {"F1": (40000, 11250, 0), "F2": (64500, 20000, 0), "F3": (64500, 20000, 250000),
                "F4": (64500, 20000, 500000), "F5": (200000, 60000, 0), "F6": (20000, 10000, 0)}

WALL_DAMAGE = ["walls.png", "walls_33.png", "walls_66.png"]  # niveis de dano das paredes (make_art.factory_art)
PLATES_DIR = "bs_placas"        # art3d/bs_placas publicada em parts/bs_placas (placas de modo e dos paiois)
INSET_LEFT = ["17/64", "9/64", "5/64", "5/64"]      # factory_he IronStorage
INSET_RIGHT = ["5/64", "9/64", "17/64", "5/64"]     # factory_he SulfurStorage
INSET_BOTTOM = ["9/64", "6/64", "9/64", "16/64"]    # factory_he MissileStorage
INSET_MID = ["8/64", "6/64", "8/64", "9/64"]
INSET_2X2 = {0: ["12/64", "4/64", "6/64", "11/64"], 1: ["6/64", "4/64", "12/64", "11/64"]}  # factory_ammo


def _intake():
    """bsgen.intake (WP05) com API >= 2, ou None (fabrica so com a tripulacao). Import tardio (evita ciclo)."""
    return C.content_module("bsgen.intake")


def pct(x):
    return f"{int(round(x * 100))}%"


def _pctnum(v, default):
    """'300%' / 3.0 / None -> fator (3.0)."""
    if v is None:
        return default
    s = str(v).strip()
    if s.endswith("%"):
        return float(s[:-1]) / 100
    return float(s)


def adjacency_on():
    """econ.factory_adjacency = vanilla (+25 % por fabrica vizinha, intervalos x1,5 feitos pelo bs_data)."""
    import bs_data as D
    return D.switch("econ.factory_adjacency") == "vanilla"


def splitter_mode():
    """'compartilhado' (padrao: um divisor por insumo) ou 'por_receita' (reserva do teste T-F2-SPLIT)."""
    env = (os.environ.get("BS_FABRICA_DIVISOR") or "").strip().lower()
    if env:
        v = env
    else:
        import bs_data as D
        v = str(D.switch_extra("econ.factory_splitter", "compartilhado") or "compartilhado").strip().lower()
    if v not in ("compartilhado", "por_receita"):
        raise SystemExit(f"BS_FABRICA_DIVISOR / econ.factory_splitter = {v!r}: use compartilhado ou por_receita")
    return v


def use_stat(res):
    """ID da linha 'uso de <insumo>' ([por item, por segundo]); o mesmo do bs_strings.use_stat (registrado pelo
    nucleo em bs_strings.input_stat_ids)."""
    import bs_strings
    return bs_strings.use_stat(res)


def recipe_stat(k, oc=False):
    """ID da linha de estatistica de uma receita das fabricas com seletor (BSRecipe<Chave>[OC])."""
    return "BSRecipe" + "".join(p.capitalize() for p in k.split("_")) + ("OC" if oc else "")


def _rkey(r):
    return r["recipe"]


def _base_name(base):
    """'base_med_part_terran_overclock' do spec -> 'base_med_part_terran' (common.base_part_path poe o sufixo)."""
    return base[:-len("_overclock")] if base and base.endswith("_overclock") else base


# ----------------------------------------------------------------------------- geometria
def grid_cells(rect):
    x, y, w, h = [int(v) for v in rect]
    return [[x + i, y + j] for j in range(h) for i in range(w)]


def layout(f):
    """Grades de entrada/saida do spec, celulas bloqueadas (tudo que nao e grade = maquinario), portas (fora da peca,
    vizinhas de uma celula livre, nunca do lado do maquinario) e fileiras com porta termica."""
    w, h = f["size"]
    grids = {}
    for res, rect in (f.get("input_grids") or {}).items():
        grids[("in", res)] = list(rect)
    for r in f["recipes"]:
        grids[("out", _rkey(r))] = list(r["output_grid_rect"])
    free = set()
    for rect in grids.values():
        for c in grid_cells(rect):
            free.add(tuple(c))
    blocked = [[x, y] for y in range(h) for x in range(w) if (x, y) not in free]
    doors = []
    for (x, y) in sorted(free, key=lambda c: (c[1], c[0])):
        for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                continue
            if [nx, ny] not in doors:
                doors.append([nx, ny])
    doors.sort(key=lambda c: (c[0] >= w, c[1] >= h, c[0] < 0, c[0], c[1]))
    top = min(y for (_x, y) in free)
    return {"w": w, "h": h, "grids": grids, "blocked": blocked, "doors": doors, "port_rows": range(top, h)}


def sprite_inset(f, rect):
    w, h = f["size"]
    x, y = int(rect[0]), int(rect[1])
    if [w, h] == [2, 2]:
        return INSET_2X2.get(x, INSET_MID)
    if rect[2] > 1:
        return INSET_BOTTOM
    if y == h - 1:
        return INSET_BOTTOM
    if x == 0:
        return INSET_LEFT
    if x == w - 1:
        return INSET_RIGHT
    return INSET_MID


def reachable(f, lay=None):
    """Celulas livres que a tripulacao alcanca de alguma porta andando so por celulas livres (ForceManhattanPathInPart)."""
    lay = lay or layout(f)
    w, h = lay["w"], lay["h"]
    free = {(x, y) for y in range(h) for x in range(w)} - {tuple(c) for c in lay["blocked"]}
    seen = set()
    todo = []
    for dx, dy in lay["doors"]:
        for ax, ay in ((dx + 1, dy), (dx - 1, dy), (dx, dy + 1), (dx, dy - 1)):
            if (ax, ay) in free and (ax, ay) not in seen:
                seen.add((ax, ay))
                todo.append((ax, ay))
    while todo:
        x, y = todo.pop()
        for ax, ay in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (ax, ay) in free and (ax, ay) not in seen:
                seen.add((ax, ay))
                todo.append((ax, ay))
    return seen


# ----------------------------------------------------------------------------- cook-off
def parse_cookoff(text):
    """Texto SPEC.factories[].recipes[].cookoff -> {op: (dano, raio), st: (dano, raio), drain: (dreno, raio),
    expand: bool, rese: expoente do raio}."""
    s = text or ""
    out = {}
    m = re.search(r"\bop (\d+) r(\d+(?:\.\d+)?)", s)
    if m:
        out["op"] = (int(m.group(1)), float(m.group(2)))
    m = re.search(r"\bstruct (\d+) r(\d+(?:\.\d+)?)", s)
    if m:
        out["st"] = (int(m.group(1)), float(m.group(2)))
    m = re.search(r"\bTotalDrain (\d+) r(\d+(?:\.\d+)?)", s)
    if m:
        out["drain"] = (int(m.group(1)), float(m.group(2)))
    out["expand"] = "ExpandStartRadius" in s
    m = re.search(r"RadiusEffectScaleExponent ([\d.]+)", s)
    out["rese"] = float(m.group(1)) if m else None
    return out


def _num(v):
    return int(v) if float(v) == int(v) else float(v)


def cookoff_hits(ck):
    """HitEffects de UMA saida cheia (escalados pelo FactorHitEffectsWith da grade)."""
    hits = []
    if "op" in ck:
        dmg, rad = ck["op"]
        e = {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": dmg, "EffectScaleExponent": 1},
             "Radius": _num(rad)}
        if ck.get("expand"):
            # factory_nuke.rules l.906-922
            e.update({"ExpandDuration": 0.8, "ExpandStartRadius": 1, "RadiusEffectScaleExponent": ck.get("rese") or 0.5,
                      "ImpulsePerNDamage": 10, "NDamage": 1000})
        else:
            # factory_he.rules l.1216-1233
            e.update({"Delay": 0.05, "StatusType": "cosmoteer.fire", "StatusChancePerNDamage": "100%", "StatusValue": 1,
                      "StatusValueType": "Interpolated", "NDamage": 1000, "CrewKillChance": "50%"})
        e["Filter"] = {"OperationalHealth": True, "StructuralHealth": False, "Friendlies": True}
        hits.append(e)
    if "st" in ck:
        dmg, rad = ck["st"]
        e = {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": dmg, "EffectScaleExponent": 1},
             "Radius": _num(rad)}
        if ck.get("expand"):
            e.update({"ExpandDuration": 0.8, "ExpandStartRadius": 1, "RadiusEffectScaleExponent": ck.get("rese") or 0.5,
                      "ImpulsePerNDamage": 5, "NDamage": 1000})
            e["Filter"] = {"OperationalHealth": False, "StructuralHealth": True, "Friendlies": True}
        else:
            e["Delay"] = 0.05
            e["Filter"] = {"OperationalHealth": False, "StructuralHealth": True, "Friendlies": True, "Crew": False}
        hits.append(e)
    if "drain" in ck:
        drain, rad = ck["drain"]
        # factory_emp.rules l.1015-1048: descarga da bateria em area (a celula/carga PEM nao explode)
        hits.append({
            "Type": "ExplosiveResourceDrain", "ResourceType": "battery",
            "TotalDrain": {"BaseValue": drain, "EffectScaleExponent": 1}, "Radius": _num(rad), "Slices": 1,
            "Delay": 0.05, "RadiusEffectScaleExponent": ck.get("rese") or 0.5,
            "Filter": {"Ships": True, "Shields": True, "Friendlies": True},
            "MediaEffectsOnDrainFactor": 0.00025,
            "MediaEffectsOnDrain": [
                "&<./Data/shots/missile_emp/particles/missile_emp_hit_sizzle.rules>",
                "&<./Data/shots/missile_emp/particles/missile_emp_lightning.rules>",
                "&<./Data/shots/missile_emp/particles/missile_emp_drain.rules>",
                Inh("/BASE_SOUNDS/AudioExterior", {
                    "RandomSounds": [Q(f"./Data/shots/disruptor_bolt/sounds/disruptor_discharge_0{i}.wav")
                                     for i in range(1, 5)],
                    "Volume": 1, "SpeedVariation": 0.2}),
            ]})
    return hits


def cookoff_media(ck):
    """MediaEffects escalados da explosao (so a ogiva e o dreno PEM, como factory_nuke / factory_emp)."""
    if ck.get("expand"):
        return ["&<./Data/shots/missile_nuke/particles/missile_nuke_flash.rules>",
                "&<./Data/shots/missile_nuke/particles/missile_nuke_shockwave.rules>",
                Inh("/BASE_SOUNDS/AudioExterior", {"Sound": Q("./Data/shots/missile_nuke/missile_nuke_hit.wav"),
                                                   "Volume": 1}),
                Inh("/BASE_SHAKE", {"ShakeAmount": 0.15, "Duration": 0.75})]
    if "drain" in ck:
        return ["&<./Data/shots/missile_emp/particles/missile_emp_hit_orb.rules>",
                "&<./Data/shots/missile_emp/particles/missile_emp_hit_bolts.rules>",
                "&<./Data/shots/missile_emp/particles/missile_emp_hit_shockwave.rules>"]
    return None


# ----------------------------------------------------------------------------- receitas
def recipe_inputs(r):
    """[(insumo, divisor ToQuantity, saque por ciclo)] da receita, na ordem do spec."""
    out = []
    for res, d in (r.get("inputs_per_cycle") or {}).items():
        to_q = int(d["splitter_ToQuantity"])
        draw = int(d["draw_Quantity"])
        if to_q < 1 or draw < 1 or draw > to_q * 2:
            raise ValueError(f"receita {r['recipe']}: {res} divisor 1:{to_q} saque {draw} invalido")
        out.append((res, to_q, draw))
    return out


def splitter_name(res, k, mode):
    return f"Divisor_{res}" if mode == "compartilhado" else f"Divisor_{res}_{k}"


def _mode_toggle(f, r):
    sel = f.get("selector")
    if not sel or r.get("selector_mode") is None:
        return None
    return f"ModeToggle_{int(r['selector_mode'])}"


def _default_recipe(f):
    sel = f.get("selector")
    if sel:
        for r in f["recipes"]:
            if r.get("selector_mode") == sel.get("Default"):
                return r
    return f["recipes"][0]


# ----------------------------------------------------------------------------- peca
def build_factory(f, ctx=None):
    """(top, info) do arquivo parts/<curto>/<curto>.rules de uma fabrica de DATA.FACTORIES."""
    import bs_data as D
    ctx = ctx or {"D": D, "transport": D.transport(), "warn": D.warn, "header": ""}
    lay = layout(f)
    w, h = lay["w"], lay["h"]
    center = [w / 2, h / 2]
    recipes = f["recipes"]
    multi = len(recipes) > 1
    sel = f.get("selector")
    adj = adjacency_on()
    smode = splitter_mode()
    oc = f.get("oc") or {}
    speed = _pctnum(oc.get("SPEED_FACTOR"), 3.0)
    power_f = _pctnum(oc.get("POWER_USE_FACTOR"), 1.5)
    snd_dir, snd_idle, snd_put = SOUNDS[FACTORY_SOUND.get(f["code"], "ammo")]
    snd_base = f"./Data/ships/terran/{snd_dir}/sounds"
    own_stack = {r["id"]: r["max_stack"] for r in D.RESOURCES}
    intake = _intake()

    # ------------------------------------------------------------------ campos da peca
    cats = list(f.get("type_categories") or ["provides_ammo", "uses_power"])
    for res in (f.get("input_grids") or {}):
        c = RES_CATEGORY.get(res)
        if c and c not in cats:
            cats.append(c)
    if "uses_power" not in cats:
        cats.append("uses_power")
    cats += [c for c in f.get("extra_categories") or [] if c not in cats]
    fields = C.call(intake, "part_fields", f, ctx) or {}
    cats += [c for c in (fields.get("TypeCategories_add") or fields.get("TypeCategories") or []) if c not in cats]
    rbuffs = (["Factory"] if adj else [])
    rbuffs += [b for b in (fields.get("ReceivableBuffs_add") or fields.get("ReceivableBuffs") or []) if b not in rbuffs]

    part = {
        "NameKey": Q(f"Parts/{f['key']}"),
        "IconNameKey": Q(f"Parts/{f['key']}Icon"),
        "DescriptionKey": Q(f"Parts/{f['key']}Desc"),
        "ID": f["id"],
        "EditorGroups": [Q(C.EDITOR_GROUP), Q("Production")],
        "Resources": [[r, int(q)] for r, q in f["cost"]],
        "Size": [w, h],
        "IsFlippable": True,
        "SelectionPriority": 1,
        "MaxHealth": int(f["hp"]),
        "TypeCategories": cats,
    }
    if rbuffs:
        # vizinhanca do jogo base (factory_ammo.rules l.30) + o que o transporte pedir (Fita); a base
        # base_part_overclock so tem [Overclock]
        part["ReceivableBuffs : ^/0/ReceivableBuffs"] = rbuffs
    part["BlockedTravelCells"] = lay["blocked"]
    part["ForceManhattanPathInPart"] = True
    part["AllowedDoorLocations"] = lay["doors"]
    part["EditorIcon"] = {"Texture": {"File": Q("icon.png"), "SampleMode": "Linear"},
                          "Size": [64, round(64 * h / w, 2)] if w >= h else [round(64 * w / h, 2), 64]}

    comp = {}
    # ------------------------------------------------------------------ estado (factory_he l.69-110)
    comp["IsOperational"] = {"Type": "MultiToggle", "Mode": "All",
                             "Toggles": ["PowerToggle", "NonJunkToggle", "ScorchedToggle", "BatteryStorage",
                                         "&~/Part/^/0/OVERCLOCK_OPERATIONAL"]}
    comp["NonJunkToggle"] = {"Type": "JunkToggle", "OnWhenJunk": False}
    comp["CommandConsumptionToggle"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "ScorchedToggle"],
                                        "Mode": "All"}
    comp["PowerToggle"] = {"Type": "UIToggle", "ToggleID": Q("on_off"), "Default": 1, "RequiresCommand": False}
    comp["ScorchedToggle"] = {"Type": "StatusToggle", "StatusType": "cosmoteer.scorched", "MinStatusValue": 1,
                              "Invert": True, "IncludeWhenUnderConstruction": True}
    comp["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "CommandConsumptionToggle",
                               "CommandPoints": int(f.get("cp") or 1)}

    # ------------------------------------------------------------------ seletor de receita
    if sel:
        tcomp = SELECTOR_COMPONENT.get(sel["toggle"], "RecipeToggle")
        comp[comment(f"---- seletor de receita {sel['toggle']} (missile_launcher.rules l.125-146; PartToggle do WP01) "
                     "----")] = None
        comp[tcomp] = {"Type": "UIToggle", "ToggleID": Q(sel["toggle"]), "Default": int(sel["Default"]),
                       "AvailableChoices": [int(x) for x in sel["available"]], "AlwaysAllowInBuildMode": True}
        for r in recipes:
            comp[_mode_toggle(f, r)] = {"Type": "ModeToggle", "Mode": tcomp, "OnMode": int(r["selector_mode"])}

    # ------------------------------------------------------------------ entradas (uma grade por insumo)
    comp[comment("---- entradas: grade da tripulacao + divisor (factory_he l.112-165) ----")] = None
    users = {}          # insumo -> [receitas que usam]
    for r in recipes:
        for res, _to_q, _draw in recipe_inputs(r):
            users.setdefault(res, []).append(r)
    in_toggle = {}      # insumo -> toggle do indicador 'sem insumo'
    for res, rect in (f.get("input_grids") or {}).items():
        if res not in users:
            raise ValueError(f"{f['id']}: grade de {res} sem receita que use")
        grid = {"Type": "TypedResourceGrid", "ResourceType": res, "GridRect": list(rect),
                "Layer": Q("doodads_low"), "SpriteInset": sprite_inset(f, rect),
                "AllowExternalPickupAndDelivery": True}
        comp[f"Entrada_{res}"] = grid
        all_use = len(users[res]) == len(recipes)
        if all_use or not sel:
            cons_tog = "CommandConsumptionToggle"
        else:
            # so pede o insumo quando o modo escolhido usa (a F3 nao pede cobre fazendo plasma)
            mts = [_mode_toggle(f, r) for r in users[res]]
            comp[f"Usa_{res}"] = {"Type": "MultiToggle", "Mode": "Any", "Toggles": mts}
            comp[f"Pede_{res}"] = {"Type": "MultiToggle", "Mode": "All",
                                   "Toggles": ["CommandConsumptionToggle", f"Usa_{res}"]}
            cons_tog = f"Pede_{res}"
        comp[f"Consumo_{res}"] = {"Type": "TypedResourceGridConsumer", "ResourceType": res,
                                  "Storage": f"Entrada_{res}", "DefaultPriority": "&/PRIORITIES/Factory_Supply",
                                  "OperationalToggle": cons_tog, "ConsumptionToggleButtonOffset": [0, -0.4]}
        tos = {to_q for r in users[res] for rr, to_q, _d in recipe_inputs(r) if rr == res}
        if smode == "compartilhado":
            if len(tos) != 1:
                raise ValueError(f"{f['id']}: {res} com divisores diferentes por receita {sorted(tos)} (use por_receita)")
            comp[f"Divisor_{res}"] = {"Type": "InlineResourceConverter", "ResourceType": res,
                                      "FromStorage": f"Entrada_{res}", "FromQuantity": 1, "ToQuantity": tos.pop()}
            spl = [f"Divisor_{res}"]
        else:
            spl = []
            for r in users[res]:
                to_q = next(t for rr, t, _d in recipe_inputs(r) if rr == res)
                nm = splitter_name(res, _rkey(r), smode)
                comp[nm] = {"Type": "InlineResourceConverter", "ResourceType": res, "FromStorage": f"Entrada_{res}",
                            "FromQuantity": 1, "ToQuantity": to_q}
                spl.append(nm)
        if all_use or not sel:
            in_toggle[res] = spl[0] if len(spl) == 1 else None
            if in_toggle[res] is None:
                comp[f"TemInsumo_{res}"] = {"Type": "MultiToggle", "Mode": "Any", "Toggles": spl}
                in_toggle[res] = f"TemInsumo_{res}"
        else:
            # indicador 'sem insumo' so quando o modo escolhido usa este insumo
            comp[f"TemInsumo_{res}"] = {"Type": "MultiToggle", "Mode": "Any",
                                        "Toggles": spl + [f"{{ Toggle=Usa_{res}; Invert=true }}"]}
            in_toggle[res] = f"TemInsumo_{res}"

    # ------------------------------------------------------------------ bateria (factory_he l.166-185)
    bmax = int(f.get("battery_max") or (4000 if w * h > 4 else 2000))
    comp["BatteryStorage"] = {"Type": "ResourceStorage", "ResourceType": "battery", "MaxResources": bmax,
                              "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/PowerDeliver"}
    comp["BatteryConsumer"] = {"Type": "ResourceConsumer", "ResourceType": "battery", "Storage": "BatteryStorage",
                               "DefaultPriority": "&/PRIORITIES/Factory_Supply",
                               "ResupplyThreshold": int(f.get("battery_threshold") or 500),
                               "OperationalToggle": "CommandConsumptionToggle"}

    # ------------------------------------------------------------------ receitas: saida + conversor
    conv_names = []
    rinfo = []
    for i, r in enumerate(recipes):
        k = _rkey(r)
        comp[comment(f"---- receita {k}: {r['output_resource']} ----")] = None
        rect = list(r["output_grid_rect"])
        comp[f"Saida_{k}"] = {"Type": "TypedResourceGrid", "ResourceType": r["output_resource"], "GridRect": rect,
                              "Layer": Q("doodads_low"), "SpriteInset": sprite_inset(f, rect),
                              "SuppliesResources": True, "SupplyToggleButtonOffset": [0, -0.4],
                              "InitToMaxResources": 0, "AllowExternalPickupAndDelivery": True}
        ins = recipe_inputs(r)
        rt = ["IsOperational"]
        mt = _mode_toggle(f, r)
        if mt:
            rt.append(mt)
        frm = []
        for res, _to_q, draw in ins:
            spl = splitter_name(res, k, smode)
            if spl not in rt:
                rt.append(spl)
            frm.append({"Storage": spl, "Quantity": int(draw)})
        mb = int(r["battery_mb_per_cycle"])
        # em overclock cada ciclo gasta POWER_USE_FACTOR x a bateria (factory_he.rules l.193-208)
        frm.append({"Storage": "BatteryStorage", "Quantity": {"BaseValue": mb, "Modifiers": [
            Inh("~/MODIFIERS/OVERCLOCK_LERP", {"MinValue": "&../../BaseValue",
                                               "MaxValue": "(&MinValue) * (&~/OVERCLOCK/POWER_USE_FACTOR)"})]},
                    "MinQuantityForConversion": 1})
        comp[f"Ready_{k}"] = {"Type": "MultiToggle", "Mode": "All", "Toggles": rt}
        mods = []
        if adj:
            mods.append({"Type": "Buff", "BuffType": "Factory", "ModificationMode": "Divide"})
        mods.append({"Type": "BuffRemap", "BuffType": "Overclock", "RemapFrom": [0, 1],
                     "RemapTo": [1, "&~/OVERCLOCK/SPEED_FACTOR"], "ModificationMode": "Divide"})
        comp[f"Conversor_{k}"] = {"Type": "ResourceConverter", "OperationalToggle": f"Ready_{k}", "From": frm,
                                  "ToStorage": f"Saida_{k}", "ToQuantity": int(r.get("units_per_cycle") or 1),
                                  "Interval": {"BaseValue": r["interval_s_base"], "Modifiers": mods},
                                  "CheckResourceLimits": True}
        conv_names.append(f"Conversor_{k}")
        cx = rect[0] + rect[2] / 2
        cy = rect[1] + rect[3] / 2
        rc = dict(r, key=k, index=i, first=(i == 0), last=(i == len(recipes) - 1), saida=f"Saida_{k}",
                  conversor=f"Conversor_{k}", ready=f"Ready_{k}", mode_toggle=mt, location=[cx, cy],
                  center=list(center))
        rinfo.append(rc)
        # logistica (WP05): teleporte jeito B / acoplamento / reserva - so pelo seam
        C.call(intake, "factory_output", comp, f, rc, ctx)

    comp["Pronta"] = ({"Type": "MultiToggle", "Mode": "Any", "Toggles": [f"Ready_{_rkey(r)}" for r in recipes]}
                      if multi else {"Type": "MultiToggle", "Mode": "All", "Toggles": [f"Ready_{_rkey(recipes[0])}"]})
    anim = conv_names[0]
    if multi:
        comp["Produzindo"] = {"Type": "MultiToggle", "Mode": "Any", "Toggles": conv_names}
        anim = "Produzindo"

    # ------------------------------------------------------------------ efeitos de producao
    comp["ConvertEffects"] = {
        "Type": "TriggeredEffects", "Trigger": conv_names[0] if not multi else "ConvertTrigger", "Location": center,
        "MediaEffects": [Inh("/BASE_SOUNDS/AudioInteriorDetail", {
            "RandomSounds": [Q(f"{snd_base}/{s}") for s in snd_put],
            "Volume": 1, "Db": -2, "Speed": 1, "SpeedVariation": 0.05})],
    }
    if multi:
        comp["ConvertTrigger"] = {"Type": "MultiTrigger", "Triggers": conv_names}
    if adj:
        # bonus para as vizinhas (factory_ammo l.217-224: ligado pela bateria)
        comp["BuffProvider"] = {"Type": "GridBuffProvider", "BuffType": "Factory", "BuffAmount": "25%",
                                "GridDistance": 1, "OperationalToggle": "BatteryStorage"}

    # ------------------------------------------------------------------ overclock (factory_he l.261-318, 1332-1354)
    comp[comment("---- overclock (factory_he.rules l.261-318 e l.1332-1354) ----")] = None
    comp.update(C.overclock_machinery(center, w, h, [], has_constant_heat=False, shot_heat=False,
                                      port_rows=lay["port_rows"], skip_down=D.belt_skip_down(f)))
    for r in recipes:
        k = _rkey(r)
        hk = f"HEAT_{k.upper()}"
        comp[f"Overclock_ConversionHeatProducer_{k}"] = {
            "Type": "ResourceChange", "OperationalToggle": "IsOverclocked",
            "ResourceStorage": "&~/Part/^/0/HEAT_TARGET_STORAGE", "Trigger": f"Overclock_ConverterProxy_{k}",
            "Amount": f"(&~/OVERCLOCK/{hk}) * (&~/HEAT_TO_RESOURCE)"}
        comp[f"Overclock_ConverterProxy_{k}"] = {"Type": "TriggerProxy", "ProxyToggle": "IsOverclocked",
                                                 "ComponentID": f"Conversor_{k}"}
        # calor/s no painel termico do editor (stat HeatGeneration): so o modo escolhido
        comp[f"Overclock_HeatProductionInterval_{k}"] = {"Type": "BuffableValue",
                                                         "Value": f"&~/Part/Components/Conversor_{k}/Interval",
                                                         "IncludeInBlueprints": True}
        comp[f"Overclock_HeatPerConversion_{k}"] = {"Type": "StaticValue", "Value": f"&~/OVERCLOCK/{hk}"}
        comp[f"HeatGenerationValue_{k}"] = {"Type": "ValueOperation", "Operator": "Divide",
                                            "ValueOne": f"Overclock_HeatPerConversion_{k}",
                                            "ValueTwo": f"Overclock_HeatProductionInterval_{k}",
                                            "NaNFallbackValue": 0, "IncludeInBlueprints": "Normal"}
        mt = _mode_toggle(f, r)
        if mt:
            comp[f"HeatStatToggle_{k}"] = {"Type": "MultiToggle", "Mode": "All", "Toggles": ["OverclockModeToggle", mt]}
        comp[f"HeatGenerationStatProvider_{k}"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                                   "OperationalToggle": f"HeatStatToggle_{k}" if mt else
                                                   "OverclockModeToggle",
                                                   "ValueFrom": f"HeatGenerationValue_{k}"}

    # ------------------------------------------------------------------ graficos (factory_he l.849-959)
    comp[comment("---- graficos (factory_he.rules l.849-959) ----")] = None
    a3 = f.get("art3d")
    if a3:
        mm = a3["machine"]
        frames, off_png, msize, moff, mint = mm["frames"], mm["off"], mm["size"], mm.get("offset", [0, 0]), mm["interval"]
        lights = (a3.get("hull") or {}).get("lights")
    else:
        # arte procedural (make_art.factory_art / sprites.render_factory): faixa de maquinario na fileira de cima
        frames = [f"machine_on{i}.png" for i in range(1, 5)]
        off_png, msize, moff, mint, lights = "machine_off.png", [w, 1], [0, 0.5 - h / 2], 0.12, None
    belt = []
    if adj:
        belt.append({"Type": "Buff", "BuffType": "Factory", "ModificationMode": "Multiply"})
    belt.append({"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Multiply",
                 "RemapFrom": [0, 1], "RemapTo": [1, "&~/OVERCLOCK/SPEED_FACTOR"]})
    comp["BeltSpeedFactor"] = {"Type": "BuffableValue", "Value": {"BaseValue": 1, "Modifiers": belt}}
    comp["Graphics"] = {
        "Type": "Graphics", "Location": center, "OperationalToggle": "Pronta",
        # a animacao so corre enquanto um conversor trabalha (para com a saida cheia ou sem insumo)
        "AnimationToggle": anim, "AnimationSpeedFactor": "BeltSpeedFactor",
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": [w, h]}]},
        "OperationalDoodad": {"Layer": Q("doodads_low"), "Offset": moff, "DamageLevels": [{
            "AnimationFiles": [Q(x) for x in frames], "Size": msize, "AnimationInterval": mint,
            "AnimationStartTime": "WhenSpawned"}]},
        "NonOperationalDoodad": {"Layer": Q("doodads_low"), "Offset": moff,
                                 "DamageLevels": [{"File": Q(off_png), "Size": msize}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q(x), "Size": [w, h]} for x in WALL_DAMAGE]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"), "NormalsFile": Q("roof_normals.png"),
                                                          "Size": [w, h]}]},
    }
    if lights:
        comp["Graphics"]["OperationalLighting"] = {"Layer": Q("lights_add"), "DamageLevels": [
            {"File": Q(lights), "Size": [w, h]}]}
    # brilho vermelho no teto com iluminacao sofisticada (factory_he l.946-959 / factory_ammo l.529-542)
    comp["Graphics"]["OperationalRoofLighting"] = {
        "Layer": Q("roof_lights_fancy"), "Offset": [0, "-29/64" if h >= 3 else "-17/64"],
        "DamageLevels": [{"File": Q("./Data/ships/common/light_blob.png"), "Size": [4, 4] if h >= 3 else [3, 3],
                          "Z": 0.5, "VertexColor": ["255*1.5", 0, 0]}]}
    comp.update(mode_graphics(f, ctx))
    comp["Blueprints"] = C.blueprint(w, h)

    # ------------------------------------------------------------------ indicadores (factory_he l.1265-1313)
    inds = [{"Toggle": "ScorchedToggle", "AtlasSprite": "&/INDICATORS/Scorched", "HidesIndicators": None},
            {"Toggle": "PowerToggle", "AtlasSprite": {"File": "&/INDICATORS/PowerOff", "Size": [1, 1]},
             "HidesIndicators": None}]
    for res in (f.get("input_grids") or {}):
        inds.append({"Toggle": in_toggle[res], "AtlasSprite": {"File": "&/INDICATORS/NoResource", "Size": [1, 1]}})
    inds.append({"Toggle": "BatteryStorage", "AtlasSprite": {"File": "&/INDICATORS/NoPower", "Size": [1, 1]}})
    inds.append({"Toggle": "&~/Part/^/0/OVERCLOCK_OPERATIONAL",
                 "AtlasSprite : /INDICATORS/OverclockReset": {"Size": [1, 1]}})
    inds[0]["HidesIndicators"] = list(range(1, len(inds)))
    inds[1]["HidesIndicators"] = list(range(2, len(inds)))
    comp["Indicators"] = {"Type": "IndicatorSprites", "Location": center, "Indicators": inds}

    # ------------------------------------------------------------------ efeitos, sons e cook-off por saida
    sz, on, off = C.effect_size(w, h)
    comp["OperationEffects"] = {"Type": "ToggleEffects", "Location": center, "Toggle": "Pronta",
                                "ToggledOnMediaEffects": f"&/COMMON_EFFECTS/{on}",
                                "ToggledOffMediaEffects": f"&/COMMON_EFFECTS/{off}"}
    comp["OperationSoundLoop"] = {
        "Type": "ContinuousEffects", "Location": center, "OperationalToggle": "Pronta",
        "MaxMediaEffectsZoom": 4,
        "MediaEffects": [Inh("/BASE_SOUNDS/AudioInterior", {
            "Sound": Q(f"{snd_base}/{snd_idle}"), "Volume": 1, "MaxConcurrentVolume": 1, "Speed": 1,
            "MaxConcurrent": 1})]}
    comp["ScorchedTrigger"] = {"Type": "ToggleTrigger", "Toggle": "ScorchedToggle", "TriggerWhenOn": False,
                               "TriggerWhenOff": True}
    comp["ScorchedEffects"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                               "Location": "&~/Part/Components/DestroyedEffects/Location",
                               "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartScorched"}
    # sem escala pelo estoque: evita o crash durante a construcao (comentario do factory_he l.1250)
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "Location": center,
                                "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed"}
    for r in recipes:
        k = _rkey(r)
        ck = parse_cookoff(r.get("cookoff"))
        hits = cookoff_hits(ck)
        if not hits:
            raise ValueError(f"{f['id']}/{k}: cook-off do spec ilegivel: {r.get('cookoff')!r}")
        # explosao da saida cheia, escalada pelo enchimento da grade (factory_he l.1207-1256); a das pilhas
        # guardadas (DeathHitEffects do recurso) vem por cima, como no vanilla
        de = {"Type": "DeathEffects", "OperationalToggle": "ScorchedToggle", "FactorHitEffectsWith": f"Saida_{k}",
              "Location": rinfo[recipes.index(r)]["location"], "IncludeWhenUnderConstruction": False,
              "HitEffects": hits}
        media = cookoff_media(ck)
        if media:
            de["FactorMediaEffectsWith"] = "&FactorHitEffectsWith"
            de["MediaEffects"] = media
        comp[f"Explosao_{k}"] = de
        # queimada (scorched) tambem explode o estoque da saida (factory_he l.1197-1205; FactorHitEffectsWith no
        # TriggeredEffects como o SW chaingun_magazine.rules l.694)
        comp[f"ExplosaoQueimada_{k}"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                                         "Location": f"&~/Part/Components/Explosao_{k}/Location",
                                         "HitEffects": f"&~/Part/Components/Explosao_{k}/HitEffects",
                                         "FactorHitEffectsWith": f"Saida_{k}", "IncludeWhenUnderConstruction": False}
    part["Components : ^/0/Components"] = comp

    # ------------------------------------------------------------------ estatisticas
    part["Stats"], sec = factory_stats(f, recipes, own_stack, adj)
    part["SecondaryToolTip"] = {"TitleKey": Q("StatCategories/Overclocked"),
                                "DescriptionKey": Q(f"Parts/{f['key']}OverclockDesc"), "Stats": sec}

    top = {}
    dr = _default_recipe(f)
    o = {"HEAT_PER_CONVERSION": int(dr["HEAT_PER_CONVERSION"]), "SPEED_FACTOR": pct(speed),
         "POWER_USE_FACTOR": pct(power_f)}
    for r in recipes:
        o[f"HEAT_{_rkey(r).upper()}"] = int(r["HEAT_PER_CONVERSION"])
    top["OVERCLOCK"] = o
    top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    base = _base_name(f.get("base_part")) or C.size_class(w, h)
    top["Part : " + C.base_part_path(w, h, True, base=base)] = part
    top["MODIFIERS"] = {"OVERCLOCK_LERP": {"Type": "Buff", "BuffType": "Overclock", "ModificationMode": "Lerp"}}
    return top, {"size": [w, h], "layout": lay, "recipes": rinfo}


def factory_stats(f, recipes, own_stack, adj):
    """(Stats, Stats do SecondaryToolTip de overclock). Uma receita: as linhas do factory_ammo (producao, uso de cada
    insumo, energia, capacidade); com seletor: uma linha por receita (BSRecipe<Chave>: itens/s, insumos por item,
    energia/s) e, no overclock, BSRecipe<Chave>OC (com o calor/s)."""
    pc = "&~/Part/Components"
    stats, sec = {}, {}
    multi = len(recipes) > 1
    smode = splitter_mode()
    rec_power = {}
    for r in recipes:
        k = _rkey(r)
        cv = f"{pc}/Conversor_{k}"
        ins = recipe_inputs(r)
        n = len(ins)
        rate = f"({cv}/ToQuantity) / ({cv}/Interval/BaseValue)"
        per_item = [f"({cv}/From/{j}/Quantity) / ({pc}/{splitter_name(res, k, smode)}/ToQuantity) / ({cv}/ToQuantity)"
                    for j, (res, _t, _d) in enumerate(ins)]
        pw_sec = f"({cv}/From/{n}/Quantity/BaseValue) / ({cv}/Interval/BaseValue) / 1000"
        pw_item = f"({cv}/From/{n}/Quantity/BaseValue) / ({cv}/ToQuantity) / 1000"
        rec_power[k] = pw_sec
        if multi:
            stats[recipe_stat(k)] = [rate] + per_item + [pw_sec]
            heat_sec = f"(&~/OVERCLOCK/HEAT_{k.upper()}) / ({cv}/Interval/BaseValue) * (&~/OVERCLOCK/SPEED_FACTOR)"
            sec[recipe_stat(k, True)] = ([f"({rate}) * (&~/OVERCLOCK/SPEED_FACTOR)"] + per_item +
                                         [f"({pw_sec}) * (&~/OVERCLOCK/POWER_USE_FACTOR) * (&~/OVERCLOCK/SPEED_FACTOR)",
                                          heat_sec])
            continue
        # uma receita so (F1, F5, F6): linhas do factory_ammo.rules l.919-935
        stats["BSFactoryOutput"] = rate
        use_ids = []
        for j, (res, _t, _d) in enumerate(ins):
            sp = splitter_name(res, k, smode)
            stats[f"Input{j}PerAmmo"] = per_item[j]
            stats[f"Input{j}PerSecond"] = (f"({cv}/From/{j}/Quantity) / ({pc}/{sp}/ToQuantity) / "
                                           f"({cv}/Interval/BaseValue)")
            sid = use_stat(res)
            stats[sid] = [f"&../Input{j}PerAmmo", f"&../Input{j}PerSecond"]
            use_ids.append(sid)
        stats["PowerPerAmmo"] = pw_item
        stats["PowerPerSecond"] = pw_sec
        stats["AmmoPowerUsage"] = ["&../PowerPerAmmo", "&../PowerPerSecond"]
        out_res = r["output_resource"]
        rdir = out_res.split(".")[-1]
        stack_ref = (f"&<../../resources/{rdir}/{rdir}.rules>/MaxStackSize" if out_res in own_stack
                     else f"&<./Data/resources/{rdir}/{rdir}.rules>/MaxStackSize")
        stats["AmmoCapacity"] = (f"({pc}/Saida_{k}/GridRect/2) * ({pc}/Saida_{k}/GridRect/3) * ({stack_ref})")
        # tooltip "Overclocked" (factory_ammo.rules l.937-953)
        sec["BSFactoryOutput"] = "(&~/Part/Stats/BSFactoryOutput) * (&~/OVERCLOCK/SPEED_FACTOR)"
        for sid in use_ids:
            sec[sid] = [f"(&~/Part/Stats/{sid}/0)", f"(&~/Part/Stats/{sid}/1) * (&~/OVERCLOCK/SPEED_FACTOR)"]
        sec["POWER_PER_AMMO"] = "(&~/Part/Stats/AmmoPowerUsage/0) * (&~/OVERCLOCK/POWER_USE_FACTOR)"
        sec["POWER_PER_SECOND"] = ("(&~/Part/Stats/AmmoPowerUsage/1) * (&~/OVERCLOCK/POWER_USE_FACTOR) * "
                                   "(&~/OVERCLOCK/SPEED_FACTOR)")
        sec["AmmoPowerUsage"] = ["&../POWER_PER_AMMO", "&../POWER_PER_SECOND"]
        sec["AMMO_PER_CONVERSION"] = f"({cv}/ToQuantity)"
        sec["HEAT_PER_AMMO"] = f"(&~/OVERCLOCK/HEAT_{k.upper()}) / (&AMMO_PER_CONVERSION)"
        sec["HEAT_PER_SECOND"] = (f"(&~/OVERCLOCK/HEAT_{k.upper()}) / ({cv}/Interval/BaseValue) * "
                                  f"(&~/OVERCLOCK/SPEED_FACTOR)")
        sec["AmmoHeatGeneration"] = ["&../HEAT_PER_AMMO", "&../HEAT_PER_SECOND"]
    stats["PowerCapacity"] = f"({pc}/BatteryStorage/MaxResources) / 1000"
    if adj:
        stats["FactoryBuff"] = f"({pc}/BuffProvider/BuffAmount) * 100"
    # barras de energia/tripulacao recomendadas do editor (stat_widgets.rules l.16, l.44): a receita que mais gasta
    # bateria por segundo (escolhida aqui, sem funcao max nas expressoes)
    if multi:
        top = max(recipes, key=lambda r: float(r["battery_mb_per_cycle"]) / float(r["interval_s_base"]))
        stats["RecPower"] = rec_power[_rkey(top)]
    else:
        stats["RecPower"] = "&PowerPerSecond"
    stats["RecCrew"] = "(&RecPower) * 4"
    return stats, sec


def mode_graphics(f, ctx=None):
    """Placa de modo no teto (um ToggledComponents por modo; art3d/bs_placas) e, na F3, o banco PEM (overlay do meta:
    teto no modo PEM; luzes so produzindo PEM, em roof_lights_fancy - nota do meta: lights_add some sob o teto)."""
    import bs_data as D
    comp = {}
    sel = f.get("selector")
    a3 = f.get("art3d") or {}
    mp = a3.get("mode_plate") or (f.get("spec") or {}).get("mode_plate_art")
    plates = D.FITA_ART.get(PLATES_DIR) if hasattr(D, "FITA_ART") else None
    if sel and mp and plates:
        files = set(plates.get("files") or [])
        loc = list(mp.get("rect_centre") or [f["size"][0] / 2, 0.5])
        size = float(mp.get("size") or 0.8)
        comp[comment("---- placa de modo no teto (art3d/bs_placas; ToggledComponents pelo seletor) ----")] = None
        for r in f["recipes"]:
            k = _rkey(r)
            png = f"placa_{k}.png"
            if png not in files:
                D.warn(f"{f['id']}: placa {png} ausente em art3d/{PLATES_DIR}")
                continue
            comp[f"PlacaModo_{k}"] = {"Type": "ToggledComponents", "Toggle": _mode_toggle(f, r), "Components": {
                f"Placa_{k}": {"Type": "Graphics", "Location": loc, "OperationalRoofDoodad": {
                    "Layer": Q("roof_doodads"),
                    "DamageLevels": [{"File": Q(f"../{PLATES_DIR}/{png}"), "Size": [size, size]}]}}}}
    ov = a3.get("overlays") or {}
    bank, luz = ov.get("banco_pem"), ov.get("banco_pem_luz")
    pem = next((r for r in f["recipes"] if _rkey(r) == "pem"), None)
    if bank and pem is not None and _mode_toggle(f, pem):
        x, y, bw, bh = bank["rect"]
        loc = [round(x + bw / 2, 4), round(y + bh / 2, 4)]
        lvl = {"File": Q(bank["files"][0]), "Size": [bw, bh]}
        if bank.get("normals"):
            lvl["NormalsFile"] = Q(bank["normals"][0])
        comp[comment("---- banco PEM da F3 (overlay do meta: so no modo PEM) ----")] = None
        g = {"Type": "Graphics", "Location": loc,
             "OperationalRoofDoodad": {"Layer": Q("roof_doodads"), "DamageLevels": [lvl]}}
        if luz:
            lx, ly, lw, lh = luz["rect"]
            # luzes do banco: PEM escolhido E produzindo (AnimationToggle = Conversor_pem)
            g2 = {"Type": "Graphics", "Location": [round(lx + lw / 2, 4), round(ly + lh / 2, 4)],
                  "OperationalToggle": "Conversor_pem",
                  "OperationalRoofLighting": {"Layer": Q("roof_lights_fancy"), "DamageLevels": [{
                      "AnimationFiles": [Q(x) for x in luz["files"]], "Size": [lw, lh],
                      "AnimationInterval": luz.get("interval") or 0.1}]}}
        comp["BancoPEM"] = {"Type": "ToggledComponents", "Toggle": _mode_toggle(f, pem),
                            "Components": dict({"BancoPEM_Teto": g}, **({"BancoPEM_Luz": g2} if luz else {}))}
    return comp


# ----------------------------------------------------------------------------- textos
def _fmt(v, lang):
    """1.875 -> '1,875' (pt) / '1.875' (en); 0.9375 -> '0,94'; 2.5 -> '2,5'."""
    v3 = round(v, 3)
    s = f"{v3:.3f}" if abs(v - v3) < 1e-9 else f"{round(v, 2):.2f}"
    s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",") if lang == "pt" else s


def _inputs_txt(ins, lang, raw=False):
    names = []
    for res, _t, _d in ins:
        en, pt, refined, qual = INPUT_NAMES.get(res, (res, res, False, "bruto"))
        nm = en if lang == "en" else pt
        if raw:
            nm += (" (refined)" if refined else " (raw)") if lang == "en" else f" ({qual})"
        names.append(nm)
    return " + ".join(names)


def _rhythm(iv, adj, lang):
    if not adj:
        return f"{_fmt(iv, lang)} s"
    if lang == "pt":
        return (f"{_fmt(iv, lang)} s sozinha · {_fmt(iv / 1.25, lang)} s com 1 vizinha · "
                f"{_fmt(iv / 1.5, lang)} s com 2")
    return f"{_fmt(iv, lang)} s alone · {_fmt(iv / 1.25, lang)} s with 1 neighbour · {_fmt(iv / 1.5, lang)} s with 2"


def factory_texts(f):
    """{Parts/<key>, Icon, Desc, OverclockDesc} en e pt de uma fabrica (numeros do proprio DATA: mudam com os
    switches)."""
    import bs_data as D
    import bs_strings as S
    adj = adjacency_on()
    k = f["key"]
    recipes = f["recipes"]
    multi = len(recipes) > 1
    all_ins = []
    for r in recipes:
        for t in recipe_inputs(r):
            if t[0] not in [x[0] for x in all_ins]:
                all_ins.append(t)
    en, pt = {}, {}
    en[k], pt[k] = f["name_en"], f["name_pt"]
    icons = {"F1": ("HE Press", "Prensa HE"), "F2": ("Special Ammo", "Munição Especial"), "F3": ("Cells", "Células"),
             "F4": ("Missiles", "Mísseis"), "F5": ("Warheads", "Ogivas"), "F6": ("Slug Forge", "Forja")}
    ic = icons.get(f["code"], (f["name_en"], f["name_pt"]))
    en[k + "Icon"], pt[k + "Icon"] = ic[0][:18], ic[1][:18]
    lines_en, lines_pt = [], []
    for r in recipes:
        res = D.RES_BY_ID.get(r["output_resource"]) or {}
        n = int(r.get("units_per_cycle") or 1)
        nm_en = res.get("name_en", r["output_resource"])
        nm_pt = res.get("name_pt", r["output_resource"])
        if n > 1:
            nm_en, nm_pt = S.plural_en(nm_en), S.plural_pt(nm_pt)
        iv = float(r["interval_s_base"])
        ins = recipe_inputs(r)
        lab = RECIPE_LABEL.get(_rkey(r), (_rkey(r), _rkey(r)))
        if multi:
            lines_en.append(f"- {lab[0]} ({_inputs_txt(ins, 'en')}): {n} {nm_en} every {_rhythm(iv, adj, 'en')}")
            lines_pt.append(f"- {lab[1]} ({_inputs_txt(ins, 'pt')}): {n} {nm_pt} a cada {_rhythm(iv, adj, 'pt')}")
        else:
            lines_en.append(f"Output: {n} {nm_en} every {_rhythm(iv, adj, 'en')}.")
            lines_pt.append(f"Saída: {n} {nm_pt} a cada {_rhythm(iv, adj, 'pt')}.")
    head_en = f"Single-step factory: turns raw materials straight into ammunition.\n\nInputs: {_inputs_txt(all_ins, 'en', True)}."
    head_pt = (f"Fábrica de etapa única: transforma matéria-prima direto em munição.\n\n"
               f"Entradas: {_inputs_txt(all_ins, 'pt', True)}.")
    if multi:
        head_en += "\nModes (part button; every mode has its own output grid and switching never loses stock):"
        head_pt += "\nModos (botão da peça; cada modo tem a sua grade de saída e trocar de modo não perde estoque):"
    tail_en, tail_pt = [], []
    if adj:
        tail_en.append("Gains +25% production speed for each adjacent factory of any type, as in the base game.")
        tail_pt.append("Ganha +25% de velocidade para cada fábrica vizinha de qualquer tipo, como no jogo base.")
    tail_en.append("The crew bring the inputs and collect the output grid, as in a base-game factory.")
    tail_pt.append("A tripulação traz os insumos e recolhe a grade de saída, como numa fábrica do jogo base.")
    if D.transport() == "teleporte" and _intake() is not None:
        tail_en.append("With an Ammo Feed Link stuck to it, production goes straight to the magazines of the same type.")
        tail_pt.append("Com a Fita de Alimentação grudada, a produção vai sozinha para os paióis do mesmo tipo.")
    oc_en = " Can be overclocked." if f.get("oc") else ""
    oc_pt = " Aceita overclock." if f.get("oc") else ""
    en[k + "Desc"] = (head_en + "\n" + "\n".join(lines_en) + "\n\n" + " ".join(tail_en) + oc_en +
                      "<string id='BSModTag'/>")
    pt[k + "Desc"] = (head_pt + "\n" + "\n".join(lines_pt) + "\n\n" + " ".join(tail_pt) + oc_pt +
                      "<string id='BSModTag'/>")
    oc = f.get("oc") or {}
    sp = _pctnum(oc.get("SPEED_FACTOR"), 3.0)
    pw = _pctnum(oc.get("POWER_USE_FACTOR"), 1.5)
    en[k + "OverclockDesc"] = (f"Works {_fmt(sp, 'en')}x faster and uses {_fmt(pw, 'en')}x the power per cycle "
                               f"({_fmt(sp * pw, 'en')}x per second). Produces waste heat while producing.")
    pt[k + "OverclockDesc"] = (f"Trabalha {_fmt(sp, 'pt')}x mais rápido e gasta {_fmt(pw, 'pt')}x a energia por "
                               f"ciclo ({_fmt(sp * pw, 'pt')}x por segundo). Produz calor enquanto fabrica.")
    return en, pt


def recipe_stat_texts(f):
    """Formatos das linhas BSRecipe<Chave>[OC] (en, pt) de uma fabrica com seletor."""
    import bs_data as D
    en, pt = {}, {}
    for r in f["recipes"]:
        k = _rkey(r)
        ins = recipe_inputs(r)
        lab = RECIPE_LABEL.get(k, (k, k))
        res = D.RES_BY_ID.get(r["output_resource"]) or {}
        unit_en, unit_pt = UNIT_NAMES.get(res.get("family"), ("item", "item"))
        parts_en = [f"<good>{{{j + 1}:0.###}}</good> <gray>{INPUT_NAMES.get(x[0], (x[0], x[0], False, ""))[0]}</gray>"
                    for j, x in enumerate(ins)]
        parts_pt = [f"<good>{{{j + 1}:0.###}}</good> <gray>{INPUT_NAMES.get(x[0], (x[0], x[0], False, ""))[1]}</gray>"
                    for j, x in enumerate(ins)]
        n = len(ins)
        base_en = (f"<white>{lab[0]}:</white> <good>{{0:0.##}}</good><gray>/sec · per {unit_en}:</gray> "
                   + " <gray>+</gray> ".join(parts_en) +
                   f" <gray>· power</gray> <good>{{{n + 1}:0.##}}</good><gray>/sec</gray>")
        base_pt = (f"<white>{lab[1]}:</white> <good>{{0:0.##}}</good><gray>/s · por {unit_pt}:</gray> "
                   + " <gray>+</gray> ".join(parts_pt) +
                   f" <gray>· energia</gray> <good>{{{n + 1}:0.##}}</good><gray>/s</gray>")
        en[recipe_stat(k) + "Fmt"] = base_en
        pt[recipe_stat(k) + "Fmt"] = base_pt
        en[recipe_stat(k, True) + "Fmt"] = base_en + f" <gray>· heat</gray> <good>{{{n + 2}:0.#}}</good><gray>/sec</gray>"
        pt[recipe_stat(k, True) + "Fmt"] = base_pt + f" <gray>· calor</gray> <good>{{{n + 2}:0.#}}</good><gray>/s</gray>"
    return en, pt


# ----------------------------------------------------------------------------- arte
def write_art(out, pdir, f, info, ctx):
    """Arte da fabrica (make_art.factory_art: art3d/<art3d_dir> ou procedural) e as placas de modo publicadas em
    parts/bs_placas (uma vez por build). Com --no-art so copia os PNGs do art3d."""
    import art3d as A3
    import bs_data as D
    art = ctx.get("art")
    if art:
        # make_art do WP10 le f['art3d_dir'] (art_dir); o make_art 1.x le f['short'] (shim para a F2)
        art_f = f if hasattr(art, "art_dir") or not f.get("art3d") else dict(f, short=f["art3d_dir"])
        art.factory_art(out, pdir, art_f, info)
    elif f.get("art3d"):
        A3.copy_files(out.root, pdir, f.get("art3d_dir") or f["short"], f["art3d"])
    plates = D.FITA_ART.get(PLATES_DIR) if hasattr(D, "FITA_ART") else None
    if f.get("selector") and plates and not os.path.isfile(os.path.join(out.root, "parts", PLATES_DIR,
                                                                        plates["files"][0])):
        A3.copy_files(out.root, f"parts/{PLATES_DIR}", PLATES_DIR, plates)


# ----------------------------------------------------------------------------- ganchos do build_mod
def parts(out, D, ctx):
    """Escreve as fabricas de DATA.FACTORIES (parts/<curto>/<curto>.rules) e registra cada uma."""
    for f in D.FACTORIES:
        pdir = f"parts/{f['short']}"
        top, info = build_factory(f, ctx)
        rel = f"{pdir}/{f['short']}.rules"
        out.text(rel, render(top, ctx["header"] + f"\nFabrica {f['code']}: {f['name_en']} / {f['name_pt']}"))
        write_art(out, pdir, f, info, ctx)
        ctx["add_part"](f["id"])


def part_stats():
    """Linhas de estatistica proprias das fabricas com seletor (BSRecipe<Chave> e BSRecipe<Chave>OC)."""
    import bs_data as D
    ids = []
    for f in D.FACTORIES:
        if len(f["recipes"]) > 1:
            for r in f["recipes"]:
                ids += [recipe_stat(_rkey(r)), recipe_stat(_rkey(r), True)]
    return ids


def strings(D):
    """(en, pt): nome/icone/descricao/overclock das fabricas escritas e os formatos das linhas por receita. Tambem
    corrige o nome da hiperbobina (coil2) na linha 'uso de' do nucleo (o jogo chama de Hyper-Coil / Hiperbobina)."""
    en = {"Parts": {}, "Stats": {}}
    pt = {"Parts": {}, "Stats": {}}
    for f in D.FACTORIES:
        e, p = factory_texts(f)
        en["Parts"].update(e)
        pt["Parts"].update(p)
        if len(f["recipes"]) > 1:
            e, p = recipe_stat_texts(f)
            en["Stats"].update(e)
            pt["Stats"].update(p)
    sid = use_stat("coil2")
    en["Stats"][sid + "Fmt"] = ("<white>Hyper-Coil Use:</white> <good>{0:0.###}</good><gray>/ammo (</gray>"
                                "<good>{1:0.###}</good><gray>/sec)</gray>")
    pt["Stats"][sid + "Fmt"] = ("<white>Uso de hiperbobina:</white> <good>{0:0.###}</good><gray>/munição (</gray>"
                                "<good>{1:0.###}</good><gray>/s)</gray>")
    return en, pt


# ----------------------------------------------------------------------------- conferencia (selfcheck)
def _rules_root(path):
    import rules_lint as RL
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    root, errs, _w = RL.parse_text(text, RL.RFile("fs", path, path))
    return root if not errs else None


def _node(node, path):
    for seg in [x for x in path.split("/") if x]:
        if node is None:
            return None
        if seg.isdigit() and node.kind == "list":
            i = int(seg)
            node = node.children[i] if i < len(node.children) else None
            continue
        node = next((c for c in node.children if c.name == seg), None)
    return node


def _val(node, path=""):
    n = _node(node, path) if path else node
    if n is None or n.kind != "value" or n.value is None:
        return None
    return n.value.strip().strip('"')


def _numv(node, path=""):
    n = _node(node, path) if path else node
    if n is None:
        return None
    if n.kind == "group":
        return _numv(n, "BaseValue")
    v = _val(n)
    if v is None:
        return None
    v = v.rstrip("d%")
    try:
        return float(v)
    except ValueError:
        return None


def _list(node, path):
    n = _node(node, path)
    if n is None or n.kind != "list":
        return None
    out = []
    for c in n.children:
        if c.kind == "list":
            out.append([(x.value or "").strip() for x in c.children])
        else:
            out.append((c.value or "").strip())
    return out


def _cells(lst):
    return [[int(float(a)) for a in c] for c in (lst or [])]


def _eq(a, b, tol=1e-4):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))


def expected_interval(spec_f, spec_r):
    """Intervalo esperado calculado de novo do spec cru (nao do bs_data): guns.ac_cost = 3x (F2 AC 1,25) e depois
    econ.factory_adjacency = vanilla (x1,5) - J2R3-25."""
    import bs_data as D
    iv = float(spec_r["interval_s_base"])
    if D.switch("guns.ac_cost") == "3x" and spec_f["code"] == "F2" and spec_r["recipe"] == "ac":
        iv = 1.25
    if D.switch("econ.factory_adjacency") == "vanilla":
        iv = round(iv * 1.5, 4)
    return iv


def selfcheck(mod_dir, SPEC):
    """Confere as fabricas escritas contra o spec cru e os switches: ID/tamanho (F2 = bs_factory_mag_ap 4x3), grades
    (cobre da F3 em [1,2] fora de BlockedTravelCells; toda grade alcancavel por uma porta; meta.grid = spec),
    intervalos (com e sem os switches), saques e divisores, AvailableChoices/Default, cook-off por saida (soma <=
    molde vanilla), vizinhanca (off: nenhum item Factory; vanilla: os 4), nenhum enriched_uranium, nenhum PartCriteria
    escrito por este modulo, F6 so com rail.enabled."""
    import bs_data as D
    errs = []
    spec_by_id = {f["id"]: f for f in SPEC["factories"]}
    adj = D.switch("econ.factory_adjacency") == "vanilla"
    smode = splitter_mode()
    written = [f["id"] for f in D.FACTORIES]
    if D.RAIL_ENABLED != (f"{D.AUTHOR}.bs_factory_slug" in written):
        errs.append(f"F6 (bs_factory_slug) {'ausente' if D.RAIL_ENABLED else 'presente'} com rail.enabled = "
                    f"{D.RAIL_ENABLED}")
    for rid in SPEC.get("factories_removed") or []:
        if os.path.isdir(os.path.join(mod_dir, "parts", rid.split(".", 1)[1])):
            errs.append(f"peca removida {rid} escrita")
    for f in D.FACTORIES:
        sf = spec_by_id.get(f["id"])
        short = f["short"]
        if sf is None:
            errs.append(f"{f['id']} fora do spec")
            continue
        path = os.path.join(mod_dir, "parts", short, f"{short}.rules")
        root = _rules_root(path)
        if root is None:
            errs.append(f"{short}: parts/{short}/{short}.rules ausente ou ilegivel")
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        body = "\n".join(ln.split("//", 1)[0] for ln in text.split("\n"))
        part = next((c for c in root.children if (c.name or "").startswith("Part")), None)
        comp = _node(part, "Components") if part is not None else None
        if part is None or comp is None:
            errs.append(f"{short}: sem Part/Components")
            continue
        # ID e tamanho
        if _val(part, "ID") != sf["id"]:
            errs.append(f"{short}: ID {_val(part, 'ID')} != {sf['id']}")
        size = [int(float(x)) for x in (_list(part, "Size") or [])]
        if size != list(sf["size"]):
            errs.append(f"{short}: Size {size} != {sf['size']}")
        if sf["code"] == "F2" and (sf["id"] != f"{D.AUTHOR}.bs_factory_mag_ap" or list(sf["size"]) != [4, 3]):
            errs.append("F2 tem que ser rafaeltessaro.bs_factory_mag_ap 4x3 (ID 1.x mantido)")
        # grades da tripulacao
        blocked = _cells(_list(part, "BlockedTravelCells"))
        doors = _cells(_list(part, "AllowedDoorLocations"))
        lay = {"w": size[0] if size else sf["size"][0], "h": size[1] if size else sf["size"][1],
               "blocked": blocked, "doors": doors}
        reach = reachable(sf, lay)
        for res, rect in (sf.get("input_grids") or {}).items():
            got = [int(float(x)) for x in (_list(comp, f"Entrada_{res}/GridRect") or [])]
            if got != list(rect):
                errs.append(f"{short}: Entrada_{res} GridRect {got} != {rect}")
            for c in grid_cells(rect):
                if c in blocked:
                    errs.append(f"{short}: grade de {res} {c} em BlockedTravelCells")
                if tuple(c) not in reach:
                    errs.append(f"{short}: grade de {res} {c} fora do alcance da tripulacao")
        if sf["code"] == "F3":
            cu = [int(float(x)) for x in (_list(comp, "Entrada_copper/GridRect") or [])]
            if cu[:2] != [1, 2] or [1, 2] in blocked:
                errs.append(f"{short}: grade de cobre da F3 tem que ficar em [1,2] fora de BlockedTravelCells ({cu})")
        # seletor
        sel = sf.get("selector")
        if sel:
            tcomp = SELECTOR_COMPONENT.get(sel["toggle"], "RecipeToggle")
            if _val(comp, f"{tcomp}/ToggleID") != sel["toggle"]:
                errs.append(f"{short}: seletor {_val(comp, f'{tcomp}/ToggleID')} != {sel['toggle']}")
            ac = [int(float(x)) for x in (_list(comp, f"{tcomp}/AvailableChoices") or [])]
            if ac != [int(x) for x in sel["available"]]:
                errs.append(f"{short}: AvailableChoices {ac} != {sel['available']}")
            if not _eq(_numv(comp, f"{tcomp}/Default"), sel["Default"]):
                errs.append(f"{short}: Default {_numv(comp, f'{tcomp}/Default')} != {sel['Default']}")
        # receitas
        tot = [0, 0, 0]
        for sr in sf["recipes"]:
            k = sr["recipe"]
            cv = _node(comp, f"Conversor_{k}")
            if cv is None:
                errs.append(f"{short}: sem Conversor_{k}")
                continue
            exp = expected_interval(sf, sr)
            got = _numv(cv, "Interval")
            if not _eq(got, exp):
                errs.append(f"{short}/{k}: Interval {got} != {exp}")
            mods = _node(cv, "Interval/Modifiers")
            has_fac = mods is not None and any(_val(m, "BuffType") == "Factory" for m in mods.children)
            if has_fac != adj:
                errs.append(f"{short}/{k}: modificador Factory no intervalo = {has_fac} com adjacency "
                            f"{'vanilla' if adj else 'off'}")
            if not _eq(_numv(cv, "ToQuantity"), sr.get("units_per_cycle") or 1):
                errs.append(f"{short}/{k}: ToQuantity {_numv(cv, 'ToQuantity')} != {sr.get('units_per_cycle')}")
            if _val(cv, "ToStorage") != f"Saida_{k}":
                errs.append(f"{short}/{k}: ToStorage {_val(cv, 'ToStorage')}")
            if _val(cv, "OperationalToggle") != f"Ready_{k}":
                errs.append(f"{short}/{k}: OperationalToggle {_val(cv, 'OperationalToggle')} != Ready_{k}")
            ready = _list(comp, f"Ready_{k}/Toggles") or []
            if sel and f"ModeToggle_{sr['selector_mode']}" not in ready:
                errs.append(f"{short}/{k}: Ready_{k} sem ModeToggle_{sr['selector_mode']}")
            if sel and not _eq(_numv(comp, f"ModeToggle_{sr['selector_mode']}/OnMode"), sr["selector_mode"]):
                errs.append(f"{short}/{k}: ModeToggle_{sr['selector_mode']} OnMode errado")
            frm = _node(cv, "From")
            for j, (res, d) in enumerate((sr.get("inputs_per_cycle") or {}).items()):
                spl = splitter_name(res, k, smode)
                e = frm.children[j] if frm is not None and j < len(frm.children) else None
                if e is None or _val(e, "Storage") != spl or not _eq(_numv(e, "Quantity"), d["draw_Quantity"]):
                    errs.append(f"{short}/{k}: From {j} != {spl} x {d['draw_Quantity']}")
                to_q = _numv(comp, f"{spl}/ToQuantity")
                if not _eq(to_q, d["splitter_ToQuantity"]) or _val(comp, f"{spl}/FromStorage") != f"Entrada_{res}":
                    errs.append(f"{short}/{k}: {spl} 1:{to_q} != 1:{d['splitter_ToQuantity']} (Entrada_{res})")
                elif not _eq(d["draw_Quantity"] / to_q, d["raw_units"], 1e-3):
                    errs.append(f"{short}/{k}: {res} {d['draw_Quantity']}/{to_q} != raw_units {d['raw_units']}")
            nin = len(sr.get("inputs_per_cycle") or {})
            be = frm.children[nin] if frm is not None and nin < len(frm.children) else None
            if be is None or _val(be, "Storage") != "BatteryStorage" or \
                    not _eq(_numv(be, "Quantity"), sr["battery_mb_per_cycle"]):
                errs.append(f"{short}/{k}: bateria por ciclo != {sr['battery_mb_per_cycle']}")
            if not _eq(_numv(root, f"OVERCLOCK/HEAT_{k.upper()}"), sr["HEAT_PER_CONVERSION"]):
                errs.append(f"{short}/{k}: HEAT_{k.upper()} != {sr['HEAT_PER_CONVERSION']}")
            # saida
            sa = _node(comp, f"Saida_{k}")
            got = [int(float(x)) for x in (_list(comp, f"Saida_{k}/GridRect") or [])]
            if sa is None or got != list(sr["output_grid_rect"]) or _val(sa, "ResourceType") != sr["output_resource"] \
                    or _val(sa, "SuppliesResources") != "true":
                errs.append(f"{short}/{k}: Saida_{k} {got} {_val(sa, 'ResourceType') if sa else None} != "
                            f"{sr['output_grid_rect']} {sr['output_resource']} (SuppliesResources true)")
            for c in grid_cells(sr["output_grid_rect"]):
                if c in blocked or tuple(c) not in reach:
                    errs.append(f"{short}/{k}: saida {c} bloqueada ou fora do alcance da tripulacao")
            # cook-off por saida
            ck = parse_cookoff(sr.get("cookoff"))
            ex = _node(comp, f"Explosao_{k}")
            if ex is None or _val(ex, "FactorHitEffectsWith") != f"Saida_{k}":
                errs.append(f"{short}/{k}: sem Explosao_{k} escalada por Saida_{k}")
            else:
                hits = _node(ex, "HitEffects")
                vals = {"op": None, "st": None, "drain": None}
                for hn in (hits.children if hits is not None else []):
                    t = _val(hn, "Type")
                    if t == "ExplosiveResourceDrain":
                        vals["drain"] = (_numv(hn, "TotalDrain"), _numv(hn, "Radius"))
                    elif t == "ExplosiveDamage":
                        key = "op" if _val(hn, "Filter/OperationalHealth") == "true" else "st"
                        vals[key] = (_numv(hn, "TotalDamage"), _numv(hn, "Radius"))
                for key in ("op", "st", "drain"):
                    want = ck.get(key)
                    if (want is None) != (vals[key] is None) or (want and (not _eq(vals[key][0], want[0]) or
                                                                           not _eq(vals[key][1], want[1]))):
                        errs.append(f"{short}/{k}: cook-off {key} {vals[key]} != spec {want}")
            for i, key in enumerate(("op", "st", "drain")):
                if ck.get(key):
                    tot[i] += ck[key][0]
        mold = COOKOFF_MOLD.get(sf["code"])
        if mold:
            for i, nm in enumerate(("operacional", "estrutural", "dreno")):
                if tot[i] > mold[i] + 1:
                    errs.append(f"{short}: cook-off {nm} somado {tot[i]} > molde vanilla {mold[i]} (J1R3-2)")
        # vizinhanca
        rb = _node(part, "ReceivableBuffs")
        rbl = [(c.value or "").strip() for c in rb.children] if rb is not None and rb.kind in ("list", "inherit") else []
        fac_items = len(re.findall(r"BuffType\s*=\s*Factory\b", body))
        if adj:
            bp = _node(comp, "BuffProvider")
            if "Factory" not in rbl:
                errs.append(f"{short}: adjacency vanilla sem Factory em ReceivableBuffs")
            if bp is None or _val(bp, "Type") != "GridBuffProvider" or _val(bp, "BuffType") != "Factory" or \
                    _val(bp, "BuffAmount") != "25%" or not _eq(_numv(bp, "GridDistance"), 1):
                errs.append(f"{short}: adjacency vanilla sem GridBuffProvider Factory 25% GridDistance 1")
            if _node(part, "Stats/FactoryBuff") is None:
                errs.append(f"{short}: adjacency vanilla sem a estatistica FactoryBuff")
        else:
            if "Factory" in rbl or fac_items or _node(part, "Stats/FactoryBuff") is not None or \
                    re.search(r"\bFactoryBuff\b", body):
                errs.append(f"{short}: adjacency off com item Factory (ReceivableBuffs {rbl}, BuffType Factory "
                            f"{fac_items}x)")
        # textos proibidos e logistica so pelo seam
        if "enriched_uranium" in body:
            errs.append(f"{short}: enriched_uranium")
        if re.search(r"\bNetworkResource\w*", body):
            errs.append(f"{short}: NetworkResource* numa fabrica")
        if re.search(r"\bPartCriteria\b", body) and (_intake() is None or D.transport() == "teleporte"):
            errs.append(f"{short}: PartCriteria numa fabrica ({D.transport()})")
        # arte: meta.grid = spec e a placa de modo
        a3 = f.get("art3d") or {}
        g = a3.get("grid")
        if g:
            if {k2: list(v) for k2, v in (g.get("inputs") or {}).items()} != \
                    {k2: list(v) for k2, v in (sf.get("input_grids") or {}).items()}:
                errs.append(f"{short}: meta.grid.inputs {g.get('inputs')} != spec {sf.get('input_grids')}")
            if {k2: list(v) for k2, v in (g.get("outputs") or {}).items()} != \
                    {r["recipe"]: list(r["output_grid_rect"]) for r in sf["recipes"]}:
                errs.append(f"{short}: meta.grid.outputs != spec")
            if sorted(map(tuple, g.get("blocked") or [])) != sorted(map(tuple, blocked)):
                errs.append(f"{short}: meta.grid.blocked {g.get('blocked')} != BlockedTravelCells {blocked}")
        for m in re.finditer(r'File = "\.\./bs_placas/([^"]+)"', text):
            if not os.path.isfile(os.path.join(mod_dir, "parts", "bs_placas", m.group(1))):
                errs.append(f"{short}: placa ../bs_placas/{m.group(1)} nao publicada")
        if sf["code"] == "F2" and a3 and a3.get("art3d_dir", f.get("art3d_dir")) != "bs_factory_special" and \
                f.get("art3d_dir") != "bs_factory_special":
            errs.append("F2 tem que usar art3d/bs_factory_special")
    if f"{D.AUTHOR}.bs_factory_mag_ap" in written and not next(
            (f for f in D.FACTORIES if f["code"] == "F2"), {}).get("art3d"):
        errs.append("F2 sem art3d (bs_factory_special de outro tamanho ou ausente: arte procedural)")
    return errs
