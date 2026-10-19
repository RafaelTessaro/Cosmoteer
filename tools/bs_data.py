"""Dados do Bullet Strike.

Os NUMEROS de balanceamento ficam em tools/spec/bullet_strike_spec.json (gerado pelo painel de design
e editavel a mao). Este arquivo converte o spec para o formato que o gerador usa e acrescenta as
dicas de implementacao (estilo de arte, tipo de cano, efeitos) que nao sao balanceamento.
"""

import json
import math
import os

from rules_dsl import Q
import art3d as A3
from launcher_layout import cell_layout

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "spec", "bullet_strike_spec.json")
with open(SPEC_PATH, encoding="utf-8") as fh:
    SPEC = json.load(fh)

VERSION = SPEC.get("version", "1.0.0")
AUTHOR = "rafaeltessaro"

MOD_TAG_EN = "\n<s16><gray>Mod: Bullet Strike</gray></s16>"
MOD_TAG_PT = "\n<s16><gray>Mod: Bullet Strike</gray></s16>"

# descricao do menu Mods (mod.rules tem um campo Description so, entao vai bilingue: pt-BR primeiro);
# montada no fim deste arquivo, depois das armas, lancadores, fabricas e limites (_mod_description)
MOD = {"description": ""}


def _short(pid):
    return pid.split(".", 1)[1]


# ----------------------------------------------------------------------------- dicas de implementacao
# estilo da torre, cano, acento de cor, efeitos e geometria. Chave = parte do ID (primeira que bater).
ART_HINTS = [
    ("nuke", {"style": "nuke", "barrel": "howitzer", "accent": "nuclear", "fx": "huge"}),
    ("naval_406", {"style": "heavy_naval", "barrel": "heavy", "accent": "aphe", "fx": "huge"}),
    ("naval_155", {"style": "heavy_naval", "barrel": "heavy", "accent": "aphe", "fx": "deck"}),
    ("naval", {"style": "naval", "barrel": "brake", "accent": "ammo", "fx": "large"}),
    ("plasma_heavy", {"style": "plasma", "barrel": "plasma", "accent": "plasma", "fx": "plasma_big"}),
    ("plasma", {"style": "plasma", "barrel": "plasma", "accent": "plasma", "fx": "plasma"}),
    ("ciws", {"style": "ciws", "barrel": "gatling", "accent": "defense", "fx": "flak"}),
    ("flak_heavy", {"style": "aa_heavy", "barrel": "plain", "accent": "flak", "fx": "flak"}),
    ("flak", {"style": "flak", "barrel": "plain", "accent": "flak", "fx": "flak"}),
    ("rotary", {"style": "minigun", "barrel": "gatling", "accent": "ammo", "fx": "mg_heavy"}),
    ("minigun", {"style": "minigun", "barrel": "gatling", "accent": "ammo", "fx": "mg"}),
    ("quad", {"style": "flak", "barrel": "fins", "accent": "ammo", "fx": "mg"}),
    ("autocannon", {"style": "autocannon", "barrel": "brake", "accent": "ammo", "fx": "med"}),
    ("hmg", {"style": "lmg", "barrel": "fins", "accent": "ammo", "fx": "mg"}),
    ("lmg", {"style": "lmg", "barrel": "fins", "accent": "ammo", "fx": "mg"}),
]


def art_hint(pid):
    for key, h in ART_HINTS:
        if key in pid:
            return dict(h)
    return {"style": "autocannon", "barrel": "brake", "accent": "ammo", "fx": "med"}


T = "./Data/ships/terran"
FX = {
    # particulas de boca (buckets "Upper" para nao ficarem sob o teto) + som de disparo
    "mg": {"particles": [f"{T}/chaingun/particles/chaingun_shoot.rules", f"{T}/chaingun/particles/chaingun_shoot_flash.rules"],
           "sound": [f"{T}/chaingun/sounds/chain_gun_shot_0{i}.wav" for i in (1, 2, 3, 4, 5)],
           "volume": 0.55, "max_concurrent": 40, "shake": 0, "offset": -0.3},
    "mg_heavy": {"particles": [f"{T}/chaingun/particles/chaingun_shoot.rules", f"{T}/chaingun/particles/chaingun_shoot_flash.rules",
                               f"{T}/chaingun/particles/chaingun_shoot_smoke.rules"],
                 "sound": [f"{T}/chaingun/sounds/chain_gun_shot_01.wav", f"{T}/chaingun/sounds/chain_gun_shot_02.wav"],
                 "volume": 0.8, "max_concurrent": 40, "shake": 0.02, "offset": -0.3},
    "med": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules", f"{T}/chaingun/particles/chaingun_shoot.rules"],
            "sound": f"{T}/cannon_med/sounds/cannon_med_shot.wav", "volume": 0.8, "max_concurrent": 20, "shake": 0.02,
            "offset": -0.2},
    "large": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules",
                            f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"],
              "sound": f"{T}/cannon_large/sounds/cannon_large_shot.wav",
              "sound_oc": [f"{T}/cannon_large/sounds/large_cannon_overclocked_shot_0{i}.wav" for i in (1, 2, 3)],
              "volume": 1.0, "shake": 0.06, "offset": -0.9},
    "deck": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules",
                           f"{T}/cannon_deck/particles/cannon_shoot_deck_flare.rules", f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"],
             "sound": f"{T}/cannon_deck/sounds/cannon_deck_shot.wav",
             "sound_oc": f"{T}/cannon_deck/sounds/deck_cannon_overclocked_shot.wav", "volume": 1.0, "shake": 0.1,
             "offset": -0.7},
    "huge": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules",
                           f"{T}/cannon_deck/particles/cannon_shoot_deck_flare.rules", f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"],
             "sound": f"{T}/cannon_deck/sounds/deck_cannon_overclocked_shot.wav", "volume": 1.0, "shake": 0.16,
             "shake_time": 0.9, "offset": -0.5},
    "plasma": {"particles": [f"{T}/chaingun/particles/chaingun_shoot_flash.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flare.rules"],
               "sound": [f"{T}/laser_blaster_small/sounds/laser_overclocked_shot_0{i}.wav" for i in (1, 2, 3)],
               "volume": 0.7, "max_concurrent": 30, "shake": 0.01, "offset": -0.2},
    "plasma_big": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flare.rules"],
                   "sound": f"{T}/cannon_deck/sounds/deck_cannon_overclocked_shot.wav", "volume": 0.9, "shake": 0.08,
                   "offset": -0.4},
    "flak": {"particles": [f"{T}/flak_cannon_large/particles/flak_cannon_shoot_flash_large.rules"],
             "sound": [f"{T}/flak_cannon_large/sounds/flak_cannon_shot_0{i}.wav" for i in (1, 2, 3, 4)],
             "volume": 0.35, "max_concurrent": 30, "shake": 0, "offset": 0},
}

GLOW = {"bullet": [255, 140, 40], "std": [255, 120, 30], "ap": [200, 225, 255], "aphe": [255, 80, 40],
        "emp": [80, 150, 255], "plasma": [0, 255, 220], "nuclear": [140, 255, 60]}
# cor do risco (tracer) e do nucleo branco-quente por municao (R1): ambar no Padrao, vermelho-alaranjado na
# Perfurante-Explosiva, branco-azulado na Perfurante, azul no P.E.M., ciano no plasma
TRACER = {"bullet": [255, 170, 60], "std": [255, 170, 60], "aphe": [255, 95, 45], "ap": [190, 215, 255],
          "emp": [100, 170, 255], "plasma": [120, 255, 255], "nuclear": [160, 255, 90]}
CORE = {"bullet": [255, 235, 190], "std": [255, 235, 190], "aphe": [255, 205, 170], "ap": [240, 248, 255],
        "emp": [200, 225, 255], "plasma": [225, 255, 255], "nuclear": [230, 255, 200]}

# Visual do projetil por ARMA (calibre), nao por municao: trocar a municao so troca a cor (R1). Antes o tamanho
# vinha do dano de cada municao, e as balas pequenas eram um "slug" de latao de 0,18 m sem brilho proprio nem
# rastro, invisivel a 250-320 m/s.
#   tracer: risco aditivo alongado (blob.png, molde do pd_shot.rules: Size [L, W], Offset -0.4375 L, LerpScaleFrom)
#           + nucleo branco-quente + brilho IsLight. Zero particulas.
#   energy: raio de plasma aditivo (blob) + nucleo + brilho (laser_bolt_small: brilho 6x6).
#   large:  granada AnimatedSprite bullet_large.png com brilho e Z do bullet_large/bullet_deck vanilla.
# Rastro de particulas so ate ~2,5 tiros/s; acima disso so sprites (sem spam de particulas: cada projetil com
# rastro mantem ~EmitPerSecond x 0,2 s particulas vivas; cannon_med vanilla ~63 por arma, cannon_deck ~91).
VIS = {
    "bs_lmg": {"look": "tracer", "wh": [3.0, 0.26], "core": [1.0, 0.12], "glow": [6, 2]},
    "bs_minigun": {"look": "tracer", "wh": [3.0, 0.26], "core": [1.0, 0.12], "glow": [6, 2]},
    "bs_hmg": {"look": "tracer", "wh": [3.5, 0.32], "core": [1.2, 0.15], "glow": [7, 2.5]},
    "bs_quad_hmg": {"look": "tracer", "wh": [3.5, 0.32], "core": [1.2, 0.15], "glow": [7, 2.5]},
    # 2,5 tiros/s: rastro med a 150/s (~30 vivas por projetil, ~75 por arma)
    "bs_autocannon_20": {"look": "tracer", "wh": [4.0, 0.40], "core": [1.4, 0.18], "glow": [8, 3], "trail": "med"},
    "bs_rotary_30": {"look": "tracer", "wh": [5.0, 0.48], "core": [1.8, 0.22], "glow": [9, 3.5]},
    "bs_plasma_gatling": {"look": "energy", "wh": [2.0, 0.5], "core": [0.9, 0.22], "glow": [6, 3]},
    # granadas no molde vanilla: bullet_large (0,7 / brilho 12x6 / -1) e bullet_deck (1,1 / 18x9 / -1,5 / Z 0,5)
    "bs_naval_76": {"look": "large", "size": 0.7, "glow": [12, 6], "glow_off": -1, "trail": "large"},
    "bs_naval_155": {"look": "large", "size": 1.1, "glow": [18, 9], "glow_off": -1.5, "z": 0.5, "trail": "deck"},
    "bs_naval_406": {"look": "large", "size": 1.35, "glow": [22, 11], "glow_off": -1.8, "z": 0.5, "trail": "deck"},
    "bs_nuke_howitzer": {"look": "large", "size": 1.35, "glow": [22, 11], "glow_off": -1.8, "z": 0.5, "trail": "deck"},
    # rastro deck ciano (300/s, ~250 por arma) no lugar das faiscas do railgun (2000/s, ~11.000 vivas por arma)
    "bs_plasma_heavy": {"look": "energy", "wh": [2.8, 1.12], "core": [1.4, 0.5], "glow": [12, 6], "glow_off": -1,
                        "trail": "deck"},
}
# a partir desta cadencia (tiros/s, ja com o overclock) o impacto usa efeitos leves (chaingun_shot_overclock_hit
# vanilla: 2-3 particulas de 0,3 s) no lugar da explosao de missil / faiscas de railgun / raios do disruptor
FAST_RATE = 5


def _caliber(dmg):
    if dmg < 450:
        return "mg"
    if dmg < 2500:
        return "med"
    if dmg < 6000:
        return "large"
    return "deck"


# ----------------------------------------------------------------------------- conversao
RES_BY_AMMO = {}
for _r in SPEC["resources"]:
    for _a in ("std", "ap", "aphe", "emp"):
        if _r["id"].endswith(f"_mag_{_a}"):
            RES_BY_AMMO[_a] = _r["id"]

SHOTS = []
GUNS = []
DEFENSES = []


def _ammo_table(w, ammo):
    t = SPEC.get("ammo_type_tables", {}).get(w["id"], {})
    if ammo in t:
        return t[ammo]
    # arma de tipo unico (bala avulsa / plasma / nuclear): usa os campos da propria arma
    if len(t) == 1:
        return list(t.values())[0]
    return {"damage": w["damage_per_hit_std"], "penetration": w["penetration_std"],
            "explosive_radius_m": w.get("explosive_radius_m", 0), "explosive_damage": w.get("explosive_damage", 0),
            "fire_chance": w.get("fire_chance", 0.05), "shield_damage": w["damage_per_hit_std"], "emp_drain": 0}


# Perfurante (spec ammo_types[ap].penetration_rule): blindagem custa 60% da penetracao normal e cada peca
# atravessada depois da primeira leva 50% do dano do primeiro acerto. Perfurante-explosiva: blindagem a 75%.
AP_ARMOR_FACTOR = 0.6
AP_PEN_DAMAGE_FACTOR = 0.5
APHE_ARMOR_FACTOR = 0.75
# categorias de projetil do modo defesa da metralhadora hibrida (spec: padrao pd_shot / point_defense)
PD_CATEGORIES = ["missile", "mine", "bullet"]


def _shot_spec(w, ammo, t, oc=None, oc_range=None):
    """Projetil de um modo de municao. oc = overclock do spec (arquivo _oc proprio); oc_range = alcance em
    overclock SEM troca de projetil (armas com seletor: Range com BuffRemap Overclock, padrao do pd_shot)."""
    short = _short(w["id"])
    name = f"bs_shot_{short.replace('bs_', '')}_{ammo}" + ("_oc" if oc else "")
    dmg = t["damage"]
    pen = t.get("penetration", 0)
    exp_r = t.get("explosive_radius_m", 0) or 0
    exp_d = t.get("explosive_damage", 0) or 0
    shield = t.get("shield_damage")
    fire = t.get("fire_chance", 0.05)
    rng = w["range_m"]
    speed = w["shot_speed_mps"]
    struct = None
    if t.get("structural_explosive_damage"):
        struct = [t["structural_explosive_radius_m"], t["structural_explosive_damage"]]
    impact = None
    if oc:
        df = oc.get("damage_factor", 1)
        dmg = round(dmg * df)
        exp_d = round(exp_d * df)
        if shield is not None:
            shield = round(shield * oc.get("shield_damage_factor", df))
        rf = oc.get("range_factor", 1)
        rng = min(600, round(rng * rf))
        # velocidade: fator explicito do spec (speed_factor); sem ele, a regra antiga derivada do alcance
        speed = round(speed * oc.get("speed_factor", 1 + (rf - 1) * 1.5))
        if oc.get("explosive_damage"):
            # explosao nova no impacto (Curupira "Erupcao Solar": 2000 r3)
            impact = [oc["explosive_radius_m"], oc["explosive_damage"]]
        elif oc.get("explosive_radius_m"):
            exp_r = oc["explosive_radius_m"]
        if oc.get("structural_explosive_damage"):
            struct = [oc["structural_explosive_radius_m"], oc["structural_explosive_damage"]]
    # calibre pelo dano: so efeitos de impacto, som, tremor e raio de fisica (o visual em voo vem de VIS)
    cal = _caliber(dmg + exp_d)
    color = GLOW.get(ammo, GLOW["std"])
    vis = VIS[short]
    oc_rate = max(1, ((w.get("overclock") or {}).get("fire_rate_factor") or 1))
    fast = w["fire_rate_shots_per_s"] * oc_rate >= FAST_RATE
    s = {
        "file": name, "id": f"{AUTHOR}.{name}", "title": f"{w['name_en']} - {ammo}{' (overclock)' if oc else ''}",
        "range": rng, "speed": max(60, speed), "health": w.get("shot_hp") or max(60, round((dmg + exp_d) * 0.35)),
        "look": vis["look"], "glow_color": color, "glow_size": list(vis["glow"]),
        "tracer_color": TRACER.get(ammo, TRACER["std"]), "core_color": CORE.get(ammo, CORE["std"]),
        "fx": {"mg": "mg", "med": "mg" if fast else "med", "large": "large", "deck": "deck"}[cal],
        "volume": {"mg": 0.5, "med": 0.6, "large": 0.8, "deck": 1.0}[cal],
        "max_conc": {"mg": 30, "med": 20, "large": 12, "deck": 8}[cal],
        "shake": {"mg": 0, "med": 0, "large": 0.04, "deck": 0.08}[cal],
        "radius": {"mg": 0.1, "med": 0.15, "large": 0.3, "deck": 0.45}[cal],
        "fire": fire,
    }
    if vis["look"] == "large":
        s["sprite_size"] = vis["size"]
    else:
        s["sprite_wh"] = list(vis["wh"])
        s["core_wh"] = list(vis["core"])
    if "glow_off" in vis:
        s["glow_offset"] = vis["glow_off"]
    if "z" in vis:
        s["glow_z"] = vis["z"]
    if vis.get("trail"):
        # forma do rastro + cor da municao (bsgen/trails.py escolhe o arquivo)
        s["trail"] = vis["trail"]
        s["trail_color"] = ammo
    if fast:
        s["fast"] = True
    if ammo == "plasma":
        s["fx"] = "plasma_fast" if fast else "plasma"
    if ammo == "emp":
        s["fx"] = "emp_fast" if fast else "emp"
    if ammo == "nuclear" or (exp_d and pen <= 1 and ammo in ("std", "bullet", "nuclear", "plasma") and exp_d >= dmg * 0.25):
        # granada que explode no impacto
        s.update({"kind": "explosive", "damage": dmg, "explosion": [max(1.0, exp_r), exp_d],
                  "explosion_fire": 50 if ammo != "plasma" else None,
                  "shield_factor": (shield / max(1, dmg + exp_d)) if shield else 1})
        if ammo == "nuclear":
            # spec ammo_types[nuclear]: Friendlies = false (nao destroi a propria nave), TargetCategory bullet,
            # explosao estrutural propria (40000 r6; Fat Boy 50000 r7) e detonacao no fim do alcance
            # (DeathByLifetime -> OnDeath, padrao mine.rules)
            s.update({"fx": "nuke", "friendly_fire": False, "shake": 0.35, "volume": 1.0, "max_conc": 4,
                      "struct_explosion": struct or [max(2, exp_r * 0.8), round(exp_d * 0.3)], "category": "bullet",
                      "death_blast": True})
            s["extra_particles"] = None
        return s
    s.update({"kind": "kinetic", "damage": dmg, "penetration": pen,
              "struct_damage": max(1, round(dmg / 4))})
    if shield is not None and abs(shield - dmg) > 1:
        s["shield_damage"] = shield
    if ammo == "ap":
        s["armor_factor"] = AP_ARMOR_FACTOR
        s["pen_damage"] = round(dmg * AP_PEN_DAMAGE_FACTOR)
    if ammo == "aphe":
        s["armor_factor"] = APHE_ARMOR_FACTOR
        if exp_d:
            s["finish_explosion"] = [max(1.0, exp_r), exp_d]
            s["explosion_fire"] = 40
    if ammo in ("std", "bullet") and exp_d and pen > 1:
        # carga explosiva onde o projetil para (Carcara 20 mm e granadas de 30 mm para cima)
        s["finish_explosion"] = [max(1.0, exp_r), exp_d]
    if ammo == "emp":
        drain = t.get("emp_drain", 0) or 0
        if drain:
            # dreno nas pecas e no escudo direto da tabela do spec (emp_drain / emp_drain_shield)
            s["emp_drain"] = drain
            s["emp_shield_drain"] = t.get("emp_drain_shield") or drain
    if ammo == "plasma":
        # spec ammo_types[plasma]: TargetCategory laser (o ponto de defesa vanilla nao intercepta; flak e CIWS sim)
        s["category"] = "laser"
        s["heat"] = t.get("heat_per_hit") or round(min(400, dmg * 0.08))
        # spec ammo_types[plasma].penetration_rule: penetracao 0, o disparo se gasta no primeiro escudo/peca;
        # efeitos sem ReduceEffectsByPenetration (padrao do laser_bolt_small, ver shots._bolt_kinetic)
        s["bolt"] = True
    if impact:
        s["impact_explosion"] = impact
        s["extra_particles"] = ["./Data/shots/missile_he/particles/missile_he_hit.rules"]
    if oc_range:
        s["oc_range"] = oc_range
    if (w.get("anti_projectile") or {}).get("blast_radius_m") == 0:
        s["anti_projectile"] = (w["anti_projectile"] or {}).get("damage_vs_shots", 100)
        s["anti_categories"] = PD_CATEGORIES
    return s


def _geom(w, hint, spin):
    """Proporcao dos canos: comprimento relativo ao tamanho da torre, grossura pelo calibre."""
    W, H = w["size"]
    tier = w["tier"]
    dmg = w["damage_per_hit_std"] + (w.get("explosive_damage") or 0) * 0.5
    lf = {"early": 0.75, "mid": 0.85, "late": 1.0}[tier]
    bw = 0.11 if dmg < 450 else 0.17 if dmg < 2000 else 0.26 if dmg < 5000 else 0.36
    if "406" in w["id"]:
        bw, lf = 0.46, 1.05
    if hint["barrel"] in ("gatling", "plasma"):
        bw = max(bw, 0.28 if W <= 3 else 0.4)
    if hint["barrel"] == "howitzer":
        bw, lf = 0.46, 0.95
    return {"len_factor": lf, "barrel_w": bw}


def _convert():
    for w in SPEC["weapons"]:
        hint = art_hint(w["id"])
        ap = w.get("anti_projectile") or {}
        short = _short(w["id"])
        oc = w.get("overclock")
        if ap.get("blast_radius_m", 0) > 0:
            DEFENSES.append(_defense(w, hint, short, oc, ap))
            continue
        spin = w.get("spinup")
        modes = []
        sel = [a for a in (w.get("ammo_selector") or [])]
        if sel:
            for i, a in enumerate(sel):
                t = _ammo_table(w, a)
                # a tabela de municao diz qual carregador alimenta cada modo (AP e APHE dividem o mesmo)
                res = t.get("resource") or RES_BY_AMMO.get(a, w["ammo_resource"])
                modes.append((i, a, res, t))
        else:
            res = w["ammo_resource"]
            a = "bullet" if res == "bullet" else ("plasma" if "plasma" in res else
                                                  "nuclear" if "nuke" in res else "std")
            modes.append((0, a, res, _ammo_table(w, a)))
        gmodes = []
        # alcance em overclock sem troca de projetil (Trovao "Supercarga": 520 -> 598 m, padrao pd_shot)
        oc_rf = (oc or {}).get("range_factor", 1) or 1
        oc_range = min(600, round(w["range_m"] * oc_rf)) if (oc and sel and oc_rf != 1) else None
        for k, a, res, t in modes:
            s = _shot_spec(w, a, t, oc_range=oc_range)
            SHOTS.append(s)
            # deposito interno: carregadores especiais (AP/APHE/EMP) tem o proprio tamanho no spec (12 padrao / 8)
            storage = int(w.get("internal_storage_units") or 4)
            if res != RES_BY_AMMO.get("std") and w.get("internal_storage_units_special") and sel:
                storage = int(w["internal_storage_units_special"])
            m = {"mode": k, "ammo": a, "res": res, "shots_per_unit": int(w.get("shots_per_resource_unit") or 1),
                 "units_per_shot": int(w.get("resource_units_per_shot") or 1),
                 "storage": storage, "shot": s["file"],
                 "show_pen": s["kind"] == "kinetic", "oc_range": bool(s.get("oc_range"))}
            if oc and (sel or (oc.get("damage_factor", 1) == 1 and oc_rf == 1)):
                # seletor (ou overclock so de cadencia, como o Saci): o projetil e o mesmo, sem arquivo _oc
                m["shot_oc"] = s["file"]
            elif oc:
                so = _shot_spec(w, a, t, oc)
                SHOTS.append(so)
                m["shot_oc"] = so["file"]
            gmodes.append(m)
        nb = int(w.get("barrels") or 1)
        burst = int(w.get("burst") or 1)
        visual_barrels = 1 if spin else nb
        fp = w.get("fire_pattern", "")
        pattern = "alternate"
        if fp.startswith("salvo") or (burst > 1 and burst == nb):
            pattern = "volley"
        elif fp == "alternate_pairs":
            pattern = "pairs"
        shots_per_trigger = int(w.get("shots_per_trigger") or (visual_barrels if pattern == "volley" else 1))
        if spin:
            fire_interval = 1.0 / spin["min_rate"]
        else:
            fire_interval = shots_per_trigger / w["fire_rate_shots_per_s"]
        g = {
            "short": short, "key": "BS" + "".join(p.capitalize() for p in short.split("_")[1:]),
            "name_en": w["name_en"], "name_pt": w["name_ptbr"], "codename": w.get("codename", ""),
            "tier": w["tier"], "size": w["size"], "crew": w["crew"], "cp": w["command_points"],
            "hp": w["max_health"], "cost": w["build_cost"], "ring": w.get("prohibit_ring_tiles", 1),
            "arc": w["firing_arc_deg"], "rotate": w["rotate_speed_deg_s"], "threshold": 2 if w["tier"] != "early" else 4,
            "fire_interval": round(fire_interval, 4), "spread": w.get("spread_deg_half", 1.5),
            "recoil": round(min(400, (w["damage_per_hit_std"] + (w.get('explosive_damage') or 0)) / 40)),
            "modes": gmodes, "selector": len(gmodes) > 1,
            "barrels": {"count": visual_barrels,
                        "spacing": round(max({"early": 0.22, "mid": 0.3, "late": 0.5}[w["tier"]],
                                             _geom(w, hint, spin)["barrel_w"] * 2.15), 3),
                        "pattern": pattern, "width": _geom(w, hint, spin)["barrel_w"],
                        "len_factor": _geom(w, hint, spin)["len_factor"]},
            "burst": None,
            "fx": dict(FX[hint["fx"]]),
            "art": {"style": hint["style"], "barrel": hint["barrel"], "accent": hint["accent"]},
            "hybrid": bool(ap and ap.get("blast_radius_m", 0) == 0),
            "desc": w.get("visual_concept", ""), "spec": w,
        }
        if g["hybrid"]:
            g["anti_categories"] = PD_CATEGORIES
            g["fire_pref_default"] = int(w.get("fire_pref_default") or 2)
        _attach_art3d(g)
        if nb > 1 and not spin:
            g["barrels"]["count"] = min(nb, 4)
            if nb > 4:
                g["barrels"]["count"] = 3
        if spin:
            g["spin"] = {"max": round(spin["max_rate"] / spin["min_rate"], 3), "up": spin["seconds_to_max"],
                         "down": round(spin["seconds_to_max"] / 2, 2)}
        if w.get("crew_stun"):
            st = w["crew_stun"]
            # atordoamento em overclock: numeros do spec (overclock.crew_stun); sem eles, +30% raio / +50% tempo
            ost = (oc or {}).get("crew_stun") or {}
            g["stun"] = {"radius": st["radius_m"], "duration": st["seconds"],
                         "oc_radius": ost.get("radius_m", round(st["radius_m"] * 1.3, 3)),
                         "oc_duration": ost.get("seconds", round(st["seconds"] * 1.5, 3))}
        if oc:
            fr = oc.get("fire_rate_factor", 1) or 1
            # dispersao e recuo em overclock: numeros do spec quando existem (formula antiga como reserva)
            g["oc"] = {"fire_interval_factor": round(1 / fr, 4),
                       "half_spread": oc.get("half_spread_deg", round(g["spread"] * 1.25, 3)),
                       "recoil_factor": oc.get("recoil_factor", 1.6), "heat_per_shot": oc["heat_per_shot"],
                       "heat_per_second": oc.get("heat_per_second", 0)}
            if spin:
                g["oc"]["max_spin"] = g["spin"]["max"]
                if oc.get("spin_up_s"):
                    g["oc"]["spin_up"] = oc["spin_up_s"]
        GUNS.append(g)


def _attach_art3d(g):
    """Se existir arte 3D (art3d/<id>/meta.json), a geometria e a tripulacao vem dela."""
    meta = A3.require(g["short"], A3.load_meta(g["short"]))
    g["art3d"] = meta
    if meta and len(meta["barrel"]["ys"]) != g["barrels"]["count"]:
        raise ValueError(f"art3d/{g['short']}: o render tem {len(meta['barrel']['ys'])} cano(s) visiveis, mas as "
                         f"regras esperam {g['barrels']['count']}. Ajuste PART['barrels']['ys'].")
    if meta and meta.get("crew_pos"):
        g["crew_pos"] = [tuple(c) for c in meta["crew_pos"]]


def _defense(w, hint, short, oc, ap):
    rng = w["range_m"]
    # so defesa: a explosao so danifica projeteis (sem a 2a explosao contra naves/escudos da flak vanilla);
    # damage_per_hit_std e 0 nas defesas (o feixe nao tem dano direto)
    beam = {"kind": "flak", "file": f"bs_flak_{short.replace('bs_', '')}", "dir": short,
            "range": rng, "vs_shots": ap["damage_vs_shots"],
            "radius": ap["blast_radius_m"],
            "categories": ["missile", "mine", "bullet", "laser", "ion_shot"],
            "offset": list(w.get("random_offset_radius_m") or [0.5, max(2.0, rng / 60)]),
            # explosao com estilhacos + clarao + fumaca (flak_large.rules l.40-59) e volume perto do vanilla (.5):
            # a rajada que acerta tem que ser vista e ouvida
            "volume": 0.4, "max_conc": 12, "particles": 3}
    SHOTS.append(beam)
    nb = int(w.get("barrels") or 1)
    res = w["ammo_resource"]
    d = {
        "short": short, "key": "BS" + "".join(p.capitalize() for p in short.split("_")[1:]),
        "name_en": w["name_en"], "name_pt": w["name_ptbr"], "codename": w.get("codename", ""), "tier": w["tier"],
        "size": w["size"], "crew": w["crew"], "cp": w["command_points"], "hp": w["max_health"], "cost": w["build_cost"],
        "ring": w.get("prohibit_ring_tiles", 1), "arc": w["firing_arc_deg"], "rotate": w["rotate_speed_deg_s"],
        # tolerancia de mira = angulo do raio da explosao no alcance maximo (point_defense.rules l.381 usa 1d):
        # com o cano assim alinhado, o erro de mira no alcance maximo fica no maximo igual ao raio e a rajada cai
        # perto do alvo. O feixe ainda soma a dispersao aleatoria (RandomOffsetRadius, que cresce com a distancia,
        # flak_large.rules l.4; ate 3 / 3,5 / 6 m no alcance maximo), entao uma rajada ainda pode errar. Nao
        # apertar mais: no Tatu a dispersao maxima ja e igual ao raio (raio - dispersao = 0)
        "threshold": round(math.degrees(math.atan(ap["blast_radius_m"] / rng)), 2),
        "fire_interval": round(int(w.get("shots_per_trigger") or 1) / w["fire_rate_shots_per_s"], 4),
        "burst": int(w.get("shots_per_trigger") or 1), "beam": beam["file"],
        "ammo": {"res": res, "shots_per_unit": int(w.get("shots_per_resource_unit") or 1),
                 "units_per_shot": int(w.get("resource_units_per_shot") or 1),
                 "storage": int(w.get("internal_storage_units") or 4)},
        "barrels": {"count": 1 if hint["barrel"] == "gatling" else min(nb, 4), "spacing": 0.3 if w["size"][0] <= 3 else 0.5,
                    "length": {"early": 0.9, "mid": 1.4, "late": 1.9}[w["tier"]],
                    "width": 0.14 if hint["barrel"] != "gatling" else 0.3},
        "fx": dict(FX["flak"]),
        "art": {"style": hint["style"], "barrel": hint["barrel"], "accent": hint["accent"]},
        "desc": w.get("visual_concept", ""), "spec": w,
    }
    if w.get("burst_delay_s"):
        d["burst_delay"] = w["burst_delay_s"]
    _attach_art3d(d)
    if oc:
        cl = oc.get("cloud")
        if cl:
            # nuvem de estilhacos so onde o spec pede (Pororoca "Muralha de Flak": LIFETIME 4, DAMAGE_POOL 500,
            # raio 5); a CIWS so muda a cadencia, com o mesmo feixe
            cloud = {"kind": "cloud", "file": f"bs_cloud_{short.replace('bs_', '')}", "dir": short,
                     "id": f"{AUTHOR}.bs_cloud_{short.replace('bs_', '')}",
                     "radius": cl["radius_m"], "lifetime": cl["lifetime_s"], "pool": cl["damage_pool"]}
            SHOTS.append(cloud)
            beam_oc = {"kind": "flak_oc", "file": f"{beam['file']}_oc", "dir": short, "base": beam["file"],
                       "cloud": cloud["file"], "cloud_radius": cloud["radius"], "cloud_pool": cloud["pool"],
                       "cloud_lifetime": cloud["lifetime"]}
            SHOTS.append(beam_oc)
            d["beam_oc"] = beam_oc["file"]
        fr = oc.get("fire_rate_factor", 1) or 1
        d["oc"] = {"fire_interval_factor": round(1 / fr, 4), "heat_per_shot": oc["heat_per_shot"],
                   "heat_per_second": oc.get("heat_per_second", 0)}
    return d


_convert()

# ----------------------------------------------------------------------------- limites por nave
# (categoria, maximo, chave singular, chave plural, pedaco do ID das armas que entram no limite)
LIMIT_DEFS = SPEC.get("category_limits") or [
    {"category": "bs_limit_nuke", "max": 2, "match": "nuke", "en": ["Nuclear Howitzer", "Nuclear Howitzers"],
     "pt": ["Obuseiro Nuclear", "Obuseiros Nucleares"]},
    {"category": "bs_limit_flagship", "max": 2, "match": "naval_406", "en": ["Battleship Turret", "Battleship Turrets"],
     "pt": ["Torre de Encouraçado", "Torres de Encouraçado"]},
]
# o limite de cada categoria vem do proprio spec (per_ship_limit), quando existir
for _l in LIMIT_DEFS:
    for _w in SPEC["weapons"]:
        if _l["match"] in _w["id"] and _w.get("per_ship_limit"):
            _l["max"] = int(_w["per_ship_limit"])
LIMITS = []
for _l in LIMIT_DEFS:
    key = "BS" + "".join(p.capitalize() for p in _l["category"].split("_")[1:])
    LIMITS.append((_l["category"], _l["max"], f"CategoryNouns/{key}Singular", f"CategoryNouns/{key}Plural"))
    for _g in GUNS + DEFENSES:
        if _l["match"] in _g["short"]:
            _g.setdefault("extra_categories", []).append(_l["category"])

# ----------------------------------------------------------------------------- recursos e fabricas
RESOURCES = []
for r in SPEC["resources"]:
    short = _short(r["id"])
    kind = "cell" if "plasma" in short else "shell" if "nuke" in short or "shell" in short else "mag"
    acc = "plasma" if kind == "cell" else "nuclear" if kind == "shell" else \
        {"std": "ammo", "ap": "ap", "aphe": "aphe", "emp": "emp"}.get(short.rsplit("_", 1)[-1], "ammo")
    cook = (2.5, 3000) if kind == "mag" else (3.0, 2500) if kind == "cell" else (6.0, 30000)
    RESOURCES.append({
        "id": r["id"], "dir": short, "key": "BS" + "".join(p.capitalize() for p in short.split("_")[1:]),
        "name_en": r["name_en"], "name_pt": r["name_ptbr"], "price": int(round(r["buy_price"] / 2) * 2),
        "max_stack": int(r["max_stack_size"]), "cookoff": cook,
        "death_fx": "BigPartDestroyed" if kind == "shell" else "MedPartDestroyed",
        "art": {"kind": kind, "accent": acc}, "note": r.get("shots_note", ""),
        "art3d": A3.require(short, A3.load_meta(short)),
    })

FACTORIES = []
for f in SPEC["factories"]:
    short = _short(f["id"])
    out_res = f["output"][0]
    kind = "cell" if "plasma" in out_res else "shell" if "nuke" in out_res else "mag"
    acc = "plasma" if kind == "cell" else "nuclear" if kind == "shell" else \
        {"std": "ammo", "ap": "ap", "aphe": "aphe", "emp": "emp"}.get(out_res.rsplit("_", 1)[-1], "ammo")
    FACTORIES.append({
        "short": short, "key": "BS" + "".join(p.capitalize() for p in short.split("_")[1:]),
        "name_en": f["name_en"], "name_pt": f["name_ptbr"], "cp": 1, "hp": f["max_health"], "cost": f["build_cost"],
        "inputs": [[r, q] for r, q in f["inputs"]], "output": f["output"], "interval": f["interval_s"],
        "power": f.get("power_per_cycle_battery") or None, "tier": f.get("tier", "mid"),
        "art": {"kind": kind, "accent": acc}, "spec": f, "size": f.get("size"),
        # overclock no padrao vanilla das fabricas (factory_ammo / factory_he): {speed_factor, power_use_factor,
        # heat_per_conversion}; None = sem overclock
        "oc": f.get("overclock"),
        "icon_en": f.get("icon_en"), "icon_pt": f.get("icon_ptbr"),
        "sounds": f.get("sounds", "ammo"), "cookoff": f.get("cookoff"), "base_part": f.get("base_part"),
        "art3d": A3.require(short, A3.load_meta(short)),
    })

AMMO_CHOICES = [
    (0, "bs_ammo_std", "PartToggles/BSAmmo_Std", "ammo_std.png"),
    (1, "bs_ammo_ap", "PartToggles/BSAmmo_AP", "ammo_ap.png"),
    (2, "bs_ammo_aphe", "PartToggles/BSAmmo_APHE", "ammo_aphe.png"),
    (3, "bs_ammo_emp", "PartToggles/BSAmmo_EMP", "ammo_emp.png"),
]

# ============================================================================= lancadores de misseis de conves
# O projeto dos lancadores fica num spec proprio (tools/spec/bullet_strike_missiles.json, legivel em
# docs/MISSEIS_PROJETO.md). Os lancadores NAO entram em GUNS: tem modelo de recarga proprio
# (carregador por familia -> autoloader tripulado -> rack com trava -> salva em ripple), ver bsgen/launchers.py.
MSPEC_PATH = os.path.join(HERE, "spec", "bullet_strike_missiles.json")
with open(MSPEC_PATH, encoding="utf-8") as fh:
    MSPEC = json.load(fh)

# Estagio do gerador: quais lancadores e quais cargas ja sao gerados. Os demais continuam so no spec.
# estagio 1: Tocandira (inicio de jogo); estagio 3: Caipora (meio) e Mula-sem-Cabeca (fim)
BUILD_LAUNCHERS = ["rafaeltessaro.bs_msl_box", "rafaeltessaro.bs_msl_twin", "rafaeltessaro.bs_msl_quad"]
# estagio 2: todas as cargas, em todos os niveis de lancador do spec
BUILD_PAYLOADS = {"he", "cluster", "limpet", "napalm", "emp", "torpedo", "nuclear"}
# estagio 4: correcoes da revisao (salva parcial com espera, rack pre-carregado sem overclock, cook-off por
# storage, sobreposicoes recortadas por casulo, arquivo base do spec, municao da Tocandira no Build & Battle)
GENERATOR_STAGE = 4


def _variants():
    """Variantes de mecanica (spec mechanic_variants). Default = projeto primario; para testar um fallback:
    BS_MSL_VARIANTS="rack_gate=salvo_timer,cell_sync=free_cycle" python3 tools/build_mod.py ..."""
    v = {k: e["default"] for k, e in MSPEC.get("mechanic_variants", {}).items() if isinstance(e, dict)}
    for item in filter(None, os.environ.get("BS_MSL_VARIANTS", "").split(",")):
        k, _, val = item.partition("=")
        k, val = k.strip(), val.strip()
        spec = MSPEC["mechanic_variants"].get(k)
        if not spec or val not in spec["options"]:
            raise ValueError(f"BS_MSL_VARIANTS: variante desconhecida {item!r}")
        if spec.get("stage", 1) > GENERATOR_STAGE and val != spec["default"]:
            raise NotImplementedError(f"BS_MSL_VARIANTS: {k} so existe a partir do estagio {spec['stage']}")
        v[k] = val
    return v


MISSILE_VARIANTS = _variants()
# ciws_vs_own_missiles (T09): padrao as_is = nuvem de estilhacos da Pororoca igual a vanilla (so campos vistos no
# VolumeHit vanilla). enemies_only e um fallback NAO comprovado: o jogo base so usa BulletCollisions em SimpleHit e
# PenetratingHit, entao o VolumeHit pode ignorar o filtro; so ligar se o T09 mostrar a nuvem pegando nossos misseis
for _s in SHOTS:
    if _s["kind"] == "cloud" and MISSILE_VARIANTS.get("ciws_vs_own_missiles") == "enemies_only":
        _s["enemies_only"] = True
MISSILE_TYPES = {m["id"]: m for m in MSPEC["missile_types"]}
FAMILY_OF = {"missile_part_he": "HE", "missile_part_thermal": "Thermal", "missile_part_emp": "EMP",
             "missile_part_nuke": "Nuke"}
_TIER_LETTER = {"early": "s", "mid": "m", "late": "l"}


def _hex_rgb(s):
    h = s.split()[0].lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _missile_toggle_id(tier):
    if MISSILE_VARIANTS.get("selector_ids") == "per_launcher":
        return f"bs_missile_type_{_TIER_LETTER[tier]}"
    return MSPEC["toggle"]["toggle_id"]


# (indice, choice_id, chave do texto, icone, tipo) - todas as 7 escolhas; cada lancador limita com AvailableChoices
MISSILE_CHOICES = [(c["index"], c["choice_id"], c["string_key"], c["icon"].split("/", 1)[-1],
                    next(m["id"] for m in MSPEC["missile_types"] if m["toggle_index"] == c["index"]))
                   for c in MSPEC["toggle"]["choices"]]

FX["launch_s"] = {
    # clarao Upper1 do lancador vanilla (missile_launcher_shoot.rules e Middle3: ficaria sob o teto) + som
    "flash": [f"{T}/missile_launcher/particles/missile_launcher_shoot_flash.rules"],
    "backblast": [f"{T}/chaingun/particles/chaingun_shoot_smoke.rules"],
    "sound": [f"{T}/missile_launcher/sounds/launcher_launch_0{i}.wav" for i in (1, 2, 3)],
    "volume": 0.5, "max_concurrent": 12, "shake": 0,
    "reload": [f"{T}/missile_launcher/sounds/launcher_reload_0{i}.wav" for i in (1, 2, 3)],
    "ready": [f"{T}/missile_launcher/sounds/launcher_ready_0{i}.wav" for i in (1, 2, 3)],
}
# meio (Caipora): clarao + fumaca de ripple por celula, tremor 0.01 por lancamento (spec launchers[].art.animations);
# torpedos com o som do lancador nuclear vanilla
FX["launch_m"] = dict(FX["launch_s"], volume=0.6, max_concurrent=16, shake=0.01,
                      sound_heavy=[f"{T}/missile_launcher/nuke/sounds/launcher_launch_nuke.wav"])
# fim (Mula): leque de fumaca do canhao de conves (RoofCannonSmoke), tremor 0.02 por lancamento e uma pancada
# de 0.15 quando o rack esvazia (ultimo missil da salva)
FX["launch_l"] = dict(FX["launch_m"], volume=0.7, shake=0.02, thump=0.15,
                      backblast=[f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"])

MISSILES = []          # especificacao de cada arquivo de missil (shots.build_missile), um por (tipo, lancador)
MISSILE_STATUSES = []  # status proprios (so com limpet_anchor=F2): registrados por AddMany no statuses.rules
LAUNCHERS = []
_LAUNCHER_SPEC = {L["id"]: L for L in MSPEC["launchers"]}


def _parse_box(physics):
    nums = [float(x) for x in physics.split("[", 1)[1].split("]", 1)[0].split(",")]
    return nums


def _body_visuals(box):
    """Escala do corpo a partir da caixa de fisica (missil vanilla: BoxPhysics [1.5, .5], sprite [2, 1])."""
    scale = box[0] / 1.5
    return {"sprite_wh": [round(2 * scale, 3), round(1 * scale, 3)],
            "glow_size": [round(4.5 * scale, 2), round(2.2 * scale, 2)], "plume_offset": round(-0.6 * box[0], 3)}, scale


def _missile_shot_spec(L, mtype, var):
    """Arquivo de projetil de uma variante (tipo de missil x lancador), com os arquivos filhos na mesma pasta."""
    short = _short(var["shot_id"])
    fl = var["flight"]
    box = _parse_box(fl["physics"])
    vis, scale = _body_visuals(box)
    glow = _hex_rgb(mtype["glow"])
    s = {"kind": "missile", "payload": mtype["id"], "file": short, "dir": short, "id": var["shot_id"],
         "title": f"{var['variant_name_en']} ({var['variant_codename']}) - {L['codename']}",
         "range": fl["range_m"], "speed": fl["speed"], "accel": fl["accel"], "turn": fl["turn_deg_s"],
         "homing_delay": fl["homing_delay_s"], "hp": fl["hp"], "lifetime": fl["lifetime_s"], "box": box,
         "sprite_wh": vis["sprite_wh"], "glow_color": glow,
         "glow_size": vis["glow_size"], "plume_offset": vis["plume_offset"],
         "damage": dict(var["damage"]), "shake": round(min(0.15, 0.04 + 0.1 * scale), 3),
         "volume": round(min(1.0, 0.45 + 0.4 * scale), 2), "max_conc": 16,
         "variants": MISSILE_VARIANTS, "codename": var["variant_codename"],
         "name_en": var["variant_name_en"], "name_pt": var["variant_name_ptbr"],
         "launcher": L["id"], "tier": L["tier"], "params": mtype.get("payload_params", {}),
         "spec_files": list(var["files"]), "children": [], "extras": []}
    if mtype["id"] == "nuclear":
        # cogumelo da Boiuna: mesmo tremor / volume do obuseiro nuclear
        s.update({"shake": 0.35, "volume": 1.0, "max_conc": 4})
    _PAYLOAD_SPECS.get(mtype["id"], lambda *_: None)(s, L, mtype, var)
    s["alpha"], s["eff"] = _missile_alpha_eff(s)
    return s


def _sub(s, role, suffix, title, **kw):
    """Projetil filho: mesma pasta, ID e arquivo com sufixo; herda variantes, cor e parametros do pai."""
    c = {"role": role, "payload": s["payload"], "file": f"{s['file']}_{suffix}", "id": f"{s['id']}_{suffix}",
         "title": f"{title} - {s['codename']} ({_LAUNCHER_SPEC[s['launcher']]['codename']})",
         "variants": s["variants"], "params": s["params"], "glow_color": s["glow_color"], "damage": s["damage"],
         "tier": s["tier"]}
    c.update(kw)
    return c


def _spec_cluster(s, L, mtype, var):
    d, cp = s["damage"], s["params"]["child"]
    box = list(cp["physics_box"])
    vis, _ = _body_visuals(box)
    lifetime = d["child_lifetime_s"]
    s["children"].append(_sub(
        s, "child", "child", "Cluster submunition", damage=d["child_ExplosiveDamage"], radius=d["child_radius"],
        speed=d["child_speed"], accel=d["child_accel"], turn=d["child_turn_deg_s"],
        homing_delay=d["child_homing_delay_s"], hp=d["child_hp"], lifetime=lifetime,
        range=round(d["child_speed"] * lifetime), box=box, volume=0.5, max_conc=10, shake=0.03, **vis))


def _spec_limpet(s, L, mtype, var):
    d, p = s["damage"], s["params"]
    anchor = MISSILE_VARIANTS.get("limpet_anchor", "F1")
    lshort = _short(L["id"]).rsplit("_", 1)[-1]
    if anchor in ("F1", "F1_drill", "F3"):
        cp = p["charge"]
        s["children"].append(_sub(
            s, "charge", "charge", "Limpet charge", speed=0 if anchor == "F3" else cp["speed"],
            blink_size=round(0.6 * d["charge_radius"], 2), defusable_hp=p["defusable_targetable_hp"][L["tier"]],
            volume=s["volume"], max_conc=s["max_conc"], shake=s["shake"]))
    elif anchor == "F2":
        sp = p["status_F2"]
        st = {"id": f"{sp['id_prefix']}_{lshort}", "dir": f"bs_limpet_{lshort}", "tick": sp["TickInterval"],
              "duration": sp["StatusDuration"], "value": sp["StatusValue"], "damage": d["charge_ExplosiveDamage"],
              "radius": d["charge_radius"], "crew_kill": d["charge_CrewKillChance"],
              "title": f"Limpet charge status - {L['codename']}"}
        if abs(sp["TickInterval"] - d["fuse_s"]) > 1e-9:
            raise ValueError("Carrapato F2: TickInterval do status difere da espoleta do spec")
        s["status"] = st
        MISSILE_STATUSES.append(st)
    if MISSILE_VARIANTS.get("limpet_repeating") == "isolated_file":
        rep = dict(s)
        rep.update({"file": f"{s['file']}_rep", "id": f"{s['id']}_rep", "repeating": True, "children": [],
                    "extras": [], "title": s["title"] + " - SW-only Repeating variant (isolated, no launcher uses it)"})
        s["extras"].append(rep)


def _spec_torpedo(s, L, mtype, var):
    d, p = s["damage"], s["params"]
    ls = p["launch_stage"]["Lifetime"]
    if abs(ls - d["launch_stage_s"]) > 1e-9:
        raise ValueError(f"{s['id']}: estagio de lancamento {ls} s difere do spec {d['launch_stage_s']} s")
    dp = p["decoy"]
    dbox = list(dp["physics_box"])
    dvis, _ = _body_visuals(dbox)
    emitter = MISSILE_VARIANTS.get("torpedo_decoys") == "emitter"
    if not emitter:
        s["children"].append(_sub(
            s, "warhead", "warhead", "Torpedo warhead", range=s["range"], box=s["box"], turn=s["turn"],
            accel=s["accel"], hp=s["hp"], lifetime=round(s["lifetime"] - ls, 3), sprite_wh=s["sprite_wh"],
            glow_size=s["glow_size"], plume_offset=s["plume_offset"], volume=s["volume"], max_conc=s["max_conc"],
            shake=s["shake"]))
    # isca: Speed 0 + InheritVelocity no padrao; disparada por emissor (fallback T17) sai na velocidade do torpedo
    s["children"].append(_sub(
        s, "decoy", "decoy", "Torpedo decoy", range=s["range"], box=dbox, speed=s["speed"] if emitter else 0,
        turn=dp["turn_deg_s"], homing_delay=dp["homing_delay_s"], accel=dp["accel"], hp=d["decoy_hp"],
        lifetime=dp["lifetime_s"], volume=0.4, max_conc=8, shake=0, **dvis))
    if emitter:
        # o lancador (estagio 3) poe um segundo emissor por celula de torpedo: Burst = iscas, sem ResourceStorage
        s["decoy_emitter"] = {"file": s["children"][-1]["file"], "burst": d["decoys"],
                              "burst_delay": p["emitter_fallback"]["BurstDelay"]}


_PAYLOAD_SPECS = {"cluster": _spec_cluster, "limpet": _spec_limpet, "torpedo": _spec_torpedo,
                  "nuclear": _spec_torpedo}


def _missile_alpha_eff(s):
    """(dano explosivo por missil, dano efetivo por missil) na convencao do spec: efetivo = direto + 50 %
    de todo ExplosiveDamage (balance_checks.conventions)."""
    d, p = s["damage"], s["payload"]
    if p == "he":
        alpha, direct = d["ExplosiveDamage"], 0
    elif p == "napalm":
        alpha, direct = d["blast_ExplosiveDamage"], 0
    elif p == "cluster":
        alpha, direct = d["children"] * d["child_ExplosiveDamage"], 0
    elif p == "limpet":
        alpha, direct = d["charge_ExplosiveDamage"], d["impact_Damage"]
    elif p == "emp":
        alpha, direct = d["structural_ExplosiveDamage"], d["direct_Damage"]
    else:  # torpedo / nuclear
        alpha, direct = d["warhead_operational"] + d["warhead_structural"], 0
    return alpha, direct + 0.5 * alpha


def _check_missile(s, var, L):
    """Os arquivos gerados tem que reproduzir os numeros do spec (variants[] e balance_checks.hard_limits)."""
    errs = []
    d, p = s["damage"], s["payload"]
    if abs(s["eff"] - var["eff_damage_per_missile"]) > 0.05:
        errs.append(f"dano efetivo {s['eff']}, spec {var['eff_damage_per_missile']}")
    if s["alpha"] * var["per_salvo"] != var["alpha_explosive_per_salvo"]:
        errs.append(f"alfa {s['alpha']} x {var['per_salvo']}, spec {var['alpha_explosive_per_salvo']}")
    files = [f"shots/{s['dir']}/{s['file']}.rules"] + [f"shots/{s['dir']}/{c['file']}.rules" for c in s["children"]]
    spec_files = [f.split(" ", 1)[0] for f in s["spec_files"] if "_rep.rules" not in f]
    if MISSILE_VARIANTS.get("torpedo_decoys") == "emitter":
        spec_files = [f for f in spec_files if not f.endswith("_warhead.rules")]
    if MISSILE_VARIANTS.get("limpet_anchor", "F1") in ("F2", "F4"):
        spec_files = [f for f in spec_files if not f.endswith("_charge.rules")]
    if sorted(files) != sorted(spec_files):
        errs.append(f"arquivos {files}, spec {spec_files}")
    if p == "cluster":
        he_hp = next(v["flight"]["hp"] for v in MISSILE_TYPES["he"]["variants"] if v["launcher"] == L["id"])
        if s["hp"] > he_hp:
            errs.append(f"portador HP {s['hp']} > HE {he_hp}")
        if d["children"] > 6:
            errs.append(f"{d['children']} filhos por portador (> 6)")
        if d["children"] * d["child_hp"] != d["children_hp_pool"] or d["children_hp_pool"] < s["hp"]:
            errs.append("HP dos filhos: soma diverge do spec ou menor que o do portador")
        if d["children"] * d["child_ExplosiveDamage"] != d["child_total"]:
            errs.append("child_total diverge de children x child_ExplosiveDamage")
        if d["children"] * var["per_salvo"] > 96:
            errs.append("mais de 96 filhos por salva")
    if p == "emp" and d["battery_TotalDrain"] / var["ammo"]["parts_per_missile"] > 1500:
        errs.append("dreno por peca PEM > 1500")
    if p in ("torpedo", "nuclear") and s["alpha"] >= 80000:
        if not L.get("per_ship_limit") and MISSILE_VARIANTS.get("category_limits") != "off":
            errs.append(f"torpedo de {s['alpha']} por tiro sem limite por nave")
    if p == "nuclear":
        # "same chain and shared DECOY as the late Boto": as iscas da Iara tem os numeros das do Boto da Mula
        boto = next(v["damage"] for v in MISSILE_TYPES["torpedo"]["variants"] if v["launcher"] == L["id"])
        if (d["decoys"], d["decoy_hp"]) != (boto["decoys"], boto["decoy_hp"]):
            errs.append("iscas da Iara diferem das do Boto do mesmo lancador")
    if errs:
        raise ValueError(f"{s['id']}: missil diverge do spec: " + "; ".join(errs))


def _convert_missiles():
    """Todos os arquivos de missil do spec (todas as variantes por lancador), mesmo os de lancadores que ainda
    nao sao gerados: o estagio 3 (Caipora, Mula) so liga os lancadores."""
    for mt in MSPEC["missile_types"]:
        if mt["id"] not in BUILD_PAYLOADS:
            continue
        for var in mt["variants"]:
            L = _LAUNCHER_SPEC[var["launcher"]]
            s = _missile_shot_spec(L, mt, var)
            _check_missile(s, var, L)
            MISSILES.append(s)


_convert_missiles()
MISSILE_BY_ID = {s["id"]: s for s in MISSILES}


def _cell_layout(L, mode):
    """Posicoes dos tubos e das unidades do rack (ordem de enchimento), em coordenadas da TORRE."""
    return cell_layout(L["art"]["part_meta"]["cells"], mode["layout"], mode["rack_units"],
                       f"{L['codename']}/{mode['missile_type']}")


def _attach_art3d_launcher(lch):
    """Arte 3D (art3d/<id>/meta.json, kind 'launcher'): geometria e camadas vem do render (STYLE.md secao 8)."""
    meta = A3.require(lch["short"], A3.load_meta(lch["short"]))
    lch["art3d"] = meta
    if not meta:
        return
    if meta.get("kind") != "launcher":
        raise ValueError(f"art3d/{lch['short']}: meta.json nao e de lancador (kind {meta.get('kind')})")
    for m in lch["modes"]:
        mm = meta["modes"].get(m["type"])
        if not mm or len(mm["units"]) != m["cells"]:
            raise ValueError(f"art3d/{lch['short']}: modo {m['type']} precisa de {m['cells']} unidades no meta")
        if m["geo"].get("shutters") and not mm.get("shutters"):
            raise ValueError(f"art3d/{lch['short']}: modo {m['type']} ({m['layout']}) precisa das persianas no meta")
    if meta.get("crew_pos"):
        lch["crew_pos"] = [tuple(c) for c in meta["crew_pos"]]


def _launcher_categories(L):
    """TypeCategories do lancador. A Mula entra no pool bs_limit_nuke (Max 2, com a Boiuna) pelo proprio spec;
    category_limits=off (fallback T18) tira os pools de limite, como o fallback da Boiuna/Mapinguari."""
    cats = list(L["type_categories"])
    if MISSILE_VARIANTS.get("category_limits") == "off":
        cats = [c for c in cats if not c.startswith("bs_limit_")]
    known = {lim["category"] for lim in LIMIT_DEFS}
    unknown = [c for c in cats if c.startswith("bs_limit_") and c not in known]
    if unknown:
        raise ValueError(f"{L['codename']}: pool de limite sem CategoryLimits: {unknown}")
    return cats


def _launcher_base(L):
    """Arquivo base vanilla do spec (launchers[].base_part, ex. "base_med_part_terran_overclock" ou
    "base_med_part_terran (no overclock; ...)"), sem o sufixo _overclock: o gerador poe o sufixo conforme o
    overclock estiver ligado (early_overclock=enabled liga o da Tocandira)."""
    base = L["base_part"].split()[0]
    return base[:-len("_overclock")] if base.endswith("_overclock") else base


def _convert_launchers():
    for L in MSPEC["launchers"]:
        if L["id"] not in BUILD_LAUNCHERS:
            continue
        short = _short(L["id"])
        oc_spec = L["overclock"]
        oc_on = oc_spec.get("enabled") or (L["tier"] == "early" and MISSILE_VARIANTS.get("early_overclock") == "enabled")
        tid = _missile_toggle_id(L["tier"])
        modes, fams = [], {}
        for m in L["modes"]:
            if m["missile_type"] not in BUILD_PAYLOADS:
                continue
            shot = MISSILE_BY_ID[m["shot_id"]]
            fam = FAMILY_OF[m["resource"]]
            oc_c = m["computed"].get("oc") or {}
            dec = shot.get("decoy_emitter")       # so com torpedo_decoys=emitter (fallback T17)
            mode = {"type": m["missile_type"], "index": m["toggle_index"], "codename": m["codename"],
                    "name_en": shot["name_en"], "name_pt": shot["name_pt"], "shot": shot["file"],
                    "res": m["resource"], "family": fam, "cells": int(m["rack_units"]),
                    "mpu": int(m["missiles_per_unit"]), "parts": m["parts_per_unit"],
                    "reload": m["reload_s_per_unit"], "layout": m["layout"],
                    "vent": int((oc_spec.get("costs", {}).get("vent_parts_per_salvo") or {}).get(m["missile_type"], 0)),
                    "oc_factor": (oc_c.get("reload_factor") if m.get("overclock_affects", True) else None),
                    "computed": m["computed"], "glow": shot["glow_color"]}
            if dec:
                mode["decoy"] = {"file": dec["file"], "burst": int(dec["burst"]), "burst_delay": dec["burst_delay"]}
            mode["geo"] = _cell_layout(L, m)
            modes.append(mode)
            fams.setdefault(fam, {"key": fam, "res": m["resource"], "modes": [],
                                  "mag": int(L["internal_stock"][m["resource"]]["magazine_parts"])})
            fams[fam]["modes"].append(mode["type"])
        pm = L["art"]["part_meta"]
        lch = {
            "id": L["id"], "short": short, "key": "BS" + "".join(p.capitalize() for p in short.split("_")[1:]),
            "name_en": L["name_en"], "name_pt": L["name_ptbr"], "codename": L["codename"], "tier": L["tier"],
            "size": L["size"], "base_part": _launcher_base(L),
            "crew": L["crew"], "cp": L["command_points"], "hp": L["max_health"],
            "cost": L["build_cost"], "ring": L.get("prohibit_ring_tiles", 1), "arc": L["firing_arc_deg"],
            "rotate": L["rotate_speed_deg_s"], "threshold": L["fire_threshold_deg"],
            "categories": _launcher_categories(L),
            "ripple": f"{round(L['ripple_delay_s'] * 30)}/30", "ripple_s": round(L["ripple_delay_s"] * 30) / 30,
            "burst_delay": "2/30",
            "toggle_id": tid, "available": [m["index"] for m in modes], "default_mode": modes[0]["index"],
            "modes": modes, "families": list(fams.values()),
            "oc": None, "cookoff": L["cookoff"],
            "geo": {"pivot": list(pm["pivot"]), "turret_size": pm["turret_box"], "collider": pm["collider"],
                    "ring_r": pm["ring_r"], "backblast": [[b[1], b[0]] for b in pm.get("backblast", [])],
                    "accent": pm.get("accent", "amber"), "pitch_deg": pm.get("pitch_deg", 35)},
            "fx": dict(FX[f"launch_{_TIER_LETTER[L['tier']]}"]),
            "art": {"style": f"launcher_{short.rsplit('_', 1)[-1]}", "accent": "ammo"},
            # brilho de overclock (olho da cupula / colar), so nos lancadores com overclock de projeto
            "oc_glow": bool(oc_spec.get("enabled")),
            "desc": L.get("visual_concept", ""), "spec": L, "variants": MISSILE_VARIANTS,
        }
        if oc_on:
            co = oc_spec["costs"]
            lch["oc"] = {"reload_factor": next((m["oc_factor"] for m in modes if m.get("oc_factor")), 1.5),
                         "heat_per_part": co["heat_per_part_loaded"],
                         "heat_per_second": co["heat_per_second"]}
        _attach_art3d_launcher(lch)
        _check_launcher(lch, L)
        LAUNCHERS.append(lch)


def _check_launcher(lch, L):
    """As regras geradas tem que reproduzir os numeros do spec (computed); aborta se divergirem."""
    errs = []
    burst = 2 / 30
    for m in lch["modes"]:
        c = m["computed"]
        n = m["cells"] * m["mpu"]
        salvo = (m["cells"] - 1) * lch["ripple_s"] + (m["mpu"] - 1) * burst
        cycle = m["cells"] * m["reload"] + salvo
        if n != c["missiles_per_salvo"]:
            errs.append(f"{m['type']}: {n} misseis por salva, spec {c['missiles_per_salvo']}")
        if abs(salvo - c["salvo_duration_s"]) > 0.002:
            errs.append(f"{m['type']}: salva {salvo:.4f} s, spec {c['salvo_duration_s']}")
        if abs(cycle - c["cycle_s"]) > 0.01:
            errs.append(f"{m['type']}: ciclo {cycle:.4f} s, spec {c['cycle_s']}")
        shot = next(s_ for s_ in MISSILES if s_["file"] == m["shot"])
        per = shot["alpha"]
        if per * n != c["alpha_explosive"]:
            errs.append(f"{m['type']}: alfa {per * n}, spec {c['alpha_explosive']}")
    if len(lch["modes"]) == len(L["modes"]):
        for f in lch["families"]:
            ck = lch["cookoff"].get(f["res"])
            # estoque cheio do spec = carregador + o maior rack da familia, em pecas (cookoff[].parts_full); o que o
            # MOTOR calcula com os storages gerados e conferido em bsgen/launchers.py _check_cookoff
            stock = f["mag"] + max(m["cells"] * m["parts"] for m in lch["modes"] if m["family"] == f["key"])
            if ck and ck.get("parts_full") != stock:
                errs.append(f"cook-off {f['key']}: estoque {stock}, spec parts_full {ck.get('parts_full')}")
            if not ck:
                errs.append(f"cook-off {f['key']}: familia sem cook-off no spec")
        # um emissor por unidade do rack em cada modo (spec emitter_components)
        n_em = sum(m["cells"] for m in lch["modes"])
        if n_em != L.get("emitter_components", n_em):
            errs.append(f"{n_em} emissores, spec emitter_components {L['emitter_components']}")
    if lch["oc"]:
        for m in lch["modes"]:
            oc = (m["computed"].get("oc") or {})
            if m["oc_factor"] and oc.get("cycle_s") is not None:
                salvo = (m["cells"] - 1) * lch["ripple_s"] + (m["mpu"] - 1) * burst
                cyc = m["cells"] * m["reload"] / m["oc_factor"] + salvo
                if abs(cyc - oc["cycle_s"]) > 0.01:
                    errs.append(f"{m['type']}: ciclo em overclock {cyc:.4f} s, spec {oc['cycle_s']}")
            if m["type"] == "nuclear" and m["oc_factor"]:
                errs.append("o overclock nunca pode acelerar a recarga nuclear")
            # respiro = pecas de CELLS/16 misseis por rack cheio; torpedo/nuclear e salvas < 16 isentos
            exempt = m["type"] in ("torpedo", "nuclear") or m["cells"] * m["mpu"] < 16
            vent = 0 if exempt else m["parts"] * m["cells"] / 16
            if abs(m["vent"] - vent) > 1e-9:
                errs.append(f"{m['type']}: respiro {m['vent']} pecas, regra CELLS/16 da {vent}")
    if errs:
        raise ValueError(f"{lch['codename']}: regras divergem do spec: " + "; ".join(errs))


_convert_launchers()
# com um lancador no pool nuclear, o substantivo do limite deixa de ser so "obuseiro nuclear"
_NUKE_POOL_NOUNS = {"en": ["Nuclear Weapon", "Nuclear Weapons"], "pt": ["Arma Nuclear", "Armas Nucleares"]}
for _l in LIMIT_DEFS:
    if any(_l["category"] in _lch["categories"] for _lch in LAUNCHERS) and _l["category"] == "bs_limit_nuke":
        _l.update(_NUKE_POOL_NOUNS)
for _lch in LAUNCHERS:
    for _l in LIMIT_DEFS:
        if _l["match"] in _lch["short"]:
            _lch.setdefault("extra_categories", []).append(_l["category"])

def missile_toggles():
    """Seletores de missil para gui/bs_part_toggles.rules: [(toggle_id, [(indice, choice_id, chave, icone)])]."""
    if not LAUNCHERS:
        return []
    if MISSILE_VARIANTS.get("selector_ids") == "per_launcher":
        out = []
        for lch in LAUNCHERS:
            out.append((lch["toggle_id"], [c[:4] for c in MISSILE_CHOICES if c[0] in lch["available"]]))
        return out
    return [(MSPEC["toggle"]["toggle_id"], [c[:4] for c in MISSILE_CHOICES])]


ALL_PARTS = {g["short"]: g for g in GUNS + DEFENSES}
ALL_PARTS.update({f["short"]: f for f in FACTORIES})
ALL_PARTS.update({lch["short"]: lch for lch in LAUNCHERS})


def _part_ref(short, field):
    return f"&<../parts/{short}/{short}.rules>/Part/{field}"


AMMO_INDEX = {"std": 0, "ap": 1, "aphe": 2, "emp": 3}


def _ammo_choice_unlocks(ammos):
    """'ammo:<tipo>' -> [bs_ammo_type, N]. O modo 0 (Padrao) e o padrao do seletor e fica sempre liberado;
    plasma e nuclear nao tem seletor. Sem isto, uma escolha que nenhuma tech lista ja nasce liberada."""
    return [f"[bs_ammo_type, {AMMO_INDEX[a]}]" for a in ammos if AMMO_INDEX.get(a)]


def career_techs():
    out = []
    for t in SPEC.get("career_techs", []):
        tid = t["id"]
        parts = [u for u in t["unlocks"] if not u.startswith(("overclock:", "ammo:"))]
        ocs = [u.split(":", 1)[1] for u in t["unlocks"] if u.startswith("overclock:")]
        ammos = [u.split(":", 1)[1] for u in t["unlocks"] if u.startswith("ammo:")]
        entry = {"ID": tid}
        if parts:
            p0 = _short(parts[0])
            if p0 not in ALL_PARTS:
                continue
            entry.update({"NameKey": _part_ref(p0, "NameKey"), "DescriptionKey": _part_ref(p0, "DescriptionKey"),
                          "Icon": _part_ref(p0, "EditorIcon"), "EditorGroup": Q("BulletStrike"),
                          "PartsUnlocked": [_part_ref(_short(p), "ID") for p in parts if _short(p) in ALL_PARTS]})
            # a tech da fabrica de um carregador especial tambem libera o modo do seletor (AP e P.E.M.)
            if _ammo_choice_unlocks(ammos):
                entry["ToggleChoicesUnlocked"] = _ammo_choice_unlocks(ammos)
        elif ocs:
            p0 = _short(ocs[0])
            if p0 not in ALL_PARTS:
                continue
            key = ALL_PARTS[p0]["key"]
            entry.update({"Categories": ["overclock"], "NameKey": Q(f"Parts/{key}Overclock"),
                          "DescriptionKey": Q(f"Parts/{key}OverclockDesc"), "Icon": _part_ref(p0, "EditorIcon"),
                          "SecondaryIcon": "&~/OverclockIcon", "EditorGroup": Q("BulletStrike"),
                          "ToggleChoicesUnlocked": [f"{{ PartID={AUTHOR}.{_short(o)}; ToggleID=thermal_overclock; Mode=1; }}"
                                                    for o in ocs if _short(o) in ALL_PARTS]})
        elif ammos:
            a = ammos[0]
            idx = AMMO_INDEX.get(a)
            if idx is None:
                continue
            key = {0: "Std", 1: "AP", 2: "APHE", 3: "EMP"}[idx]
            # icone: o da peca que mais usa a municao (primeira arma com seletor)
            first_sel = next(g for g in GUNS if g["selector"])
            entry.update({"NameKey": Q(f"PartToggles/BSAmmo_{key}Name"), "DescriptionKey": Q(f"PartToggles/BSAmmo_{key}Desc"),
                          "Icon": _part_ref(first_sel["short"], "EditorIcon"), "EditorGroup": Q("BulletStrike"),
                          "ToggleChoicesUnlocked": [f"[bs_ammo_type, {idx}]"]})
        else:
            continue
        entry["Cost"] = int(t["cost_credits"])
        pre = [p for p in t.get("prerequisites", []) if p]
        if pre:
            entry["Prerequisites"] = pre
        out.append(entry)
    out += _missile_career_techs()
    return out


def _missile_choice_unlocks(types):
    """'missile:<tipo>' -> ToggleChoicesUnlocked = [[bs_missile_type, N]] (techs.rules:118, como o 'ammo:')."""
    res = []
    for mt in types:
        idx = MISSILE_TYPES[mt]["toggle_index"]
        for lch in LAUNCHERS:
            entry = f"[{lch['toggle_id']}, {idx}]"
            if idx in lch["available"] and entry not in res:
                res.append(entry)
    return res


def _missile_career_techs():
    out = []
    built = {lch["id"]: lch for lch in LAUNCHERS}
    for t in MSPEC.get("career_techs", []):
        parts = [u for u in t["unlocks"] if ":" not in u and u in built]
        ocs = [u.split(":", 1)[1] for u in t["unlocks"] if u.startswith("overclock:")]
        ocs = [o for o in ocs if o in built and built[o].get("oc")]
        if t.get("enabled") is False and not ocs:
            continue
        missiles = _missile_choice_unlocks([u.split(":", 1)[1] for u in t["unlocks"] if u.startswith("missile:")])
        entry = {"ID": t["id"]}
        if parts:
            p0 = _short(parts[0])
            entry.update({"NameKey": _part_ref(p0, "NameKey"), "DescriptionKey": _part_ref(p0, "DescriptionKey"),
                          "Icon": _part_ref(p0, "EditorIcon"), "EditorGroup": Q("BulletStrike"),
                          "PartsUnlocked": [_part_ref(_short(p), "ID") for p in parts]})
            if missiles:
                entry["ToggleChoicesUnlocked"] = missiles
        elif ocs:
            p0 = _short(ocs[0])
            key = ALL_PARTS[p0]["key"]
            entry.update({"Categories": ["overclock"], "NameKey": Q(f"Parts/{key}Overclock"),
                          "DescriptionKey": Q(f"Parts/{key}OverclockDesc"), "Icon": _part_ref(p0, "EditorIcon"),
                          "SecondaryIcon": "&~/OverclockIcon", "EditorGroup": Q("BulletStrike"),
                          "ToggleChoicesUnlocked": [f"{{ PartID={o}; ToggleID=thermal_overclock; Mode=1; }}" for o in ocs]})
        elif missiles:
            mt = next(u.split(":", 1)[1] for u in t["unlocks"] if u.startswith("missile:"))
            key = MISSILE_TYPES[mt]["choice_id"].split("_", 2)[-1].capitalize()
            icon = next(lch for lch in LAUNCHERS if MISSILE_TYPES[mt]["toggle_index"] in lch["available"])
            entry.update({"NameKey": Q(f"PartToggles/BSMissile_{key}Name"),
                          "DescriptionKey": Q(f"PartToggles/BSMissile_{key}Desc"),
                          "Icon": _part_ref(icon["short"], "EditorIcon"), "EditorGroup": Q("BulletStrike"),
                          "ToggleChoicesUnlocked": missiles})
        else:
            continue
        entry["Cost"] = int(t["cost_credits"])
        pre = [p for p in t.get("prerequisites", []) if p]
        if pre:
            entry["Prerequisites"] = pre
        out.append(entry)
    return out


def buildbattle_techs():
    out = []
    for g in GUNS + DEFENSES:
        if g["tier"] == "early":
            continue
        cat = "defenses" if g in DEFENSES else "weapons"
        out.append({"ID": f"{AUTHOR}.bs_bb_{g['short']}", "NameKey": _part_ref(g["short"], "NameKey"),
                    "DescriptionKey": _part_ref(g["short"], "DescriptionKey"), "Icon": _part_ref(g["short"], "EditorIcon"),
                    "Category": [cat], "PartsUnlocked": [_part_ref(g["short"], "ID")], "Cost": 5000,
                    "FundsThresholdBeforeOffered": 0 if g["tier"] == "mid" else 200000})
        if g.get("oc"):
            out.append({"ID": f"{AUTHOR}.bs_bb_{g['short']}-overclock", "NameKey": Q(f"Parts/{g['key']}Overclock"),
                        "DescriptionKey": Q(f"Parts/{g['key']}OverclockDesc"), "Icon": _part_ref(g["short"], "EditorIcon"),
                        "SecondaryIcon": "&~/OverclockIcon", "Category": ["overclocks"],
                        "PartsUnlocked": "&<./Data/modes/pvp/pvp_buildbattle/techs_buildbattle.rules>/ThermalParts",
                        "ToggleChoicesUnlocked": [f"{{ PartID={AUTHOR}.{g['short']}; ToggleID=thermal_overclock; Mode=1; }}"],
                        "Cost": 5000, "FundsThresholdBeforeOffered": 0 if g["tier"] == "mid" else 200000,
                        "Prerequisites": [f"{AUTHOR}.bs_bb_{g['short']}"]})
    # lancadores de misseis (os de inicio de jogo entram na lista branca, como as armas)
    for lch in LAUNCHERS:
        if lch["tier"] == "early":
            # a peca vem liberada (lista branca), mas as pecas de missil vanilla so se liberam com as techs dos
            # lancadores vanilla (techs_buildbattle.rules: missile_launcher_he / _thermal ResourcesUnlocked); esta
            # tech sempre oferecida libera as familias do lancador de inicio. PartsUnlocked repete a peca da lista
            # branca, como a tech vanilla missile_launcher_he faz com a factory_he (tambem na PartsWhitelist)
            out.append({"ID": f"{AUTHOR}.bs_bb_{lch['short']}_ammo", "NameKey": Q(f"Parts/{lch['key']}Ammo"),
                        "DescriptionKey": Q(f"Parts/{lch['key']}AmmoDesc"),
                        "Icon": _part_ref(lch["short"], "EditorIcon"), "Category": ["weapons"],
                        "PartsUnlocked": [_part_ref(lch["short"], "ID")],
                        "ResourcesUnlocked": [f"&<./Data/resources/{f['res']}/{f['res']}.rules>/ID"
                                              for f in lch["families"]],
                        "Cost": 5000, "FundsThresholdBeforeOffered": 0})
            continue
        # as pecas de missil vanilla da familia vem junto (no B&B o lancador vanilla libera o recurso com a tech,
        # techs_buildbattle.rules: ResourcesUnlocked = [missile_part_*]); sem isso o lancador nao teria municao
        out.append({"ID": f"{AUTHOR}.bs_bb_{lch['short']}", "NameKey": _part_ref(lch["short"], "NameKey"),
                    "DescriptionKey": _part_ref(lch["short"], "DescriptionKey"),
                    "Icon": _part_ref(lch["short"], "EditorIcon"), "Category": ["weapons"],
                    "PartsUnlocked": [_part_ref(lch["short"], "ID")],
                    "ResourcesUnlocked": [f"&<./Data/resources/{f['res']}/{f['res']}.rules>/ID" for f in lch["families"]],
                    "Cost": 5000,
                    "FundsThresholdBeforeOffered": 0 if lch["tier"] == "mid" else 200000})
        if lch.get("oc"):
            out.append({"ID": f"{AUTHOR}.bs_bb_{lch['short']}-overclock", "NameKey": Q(f"Parts/{lch['key']}Overclock"),
                        "DescriptionKey": Q(f"Parts/{lch['key']}OverclockDesc"),
                        "Icon": _part_ref(lch["short"], "EditorIcon"), "SecondaryIcon": "&~/OverclockIcon",
                        "Category": ["overclocks"],
                        "PartsUnlocked": "&<./Data/modes/pvp/pvp_buildbattle/techs_buildbattle.rules>/ThermalParts",
                        "ToggleChoicesUnlocked": [f"{{ PartID={AUTHOR}.{lch['short']}; ToggleID=thermal_overclock; Mode=1; }}"],
                        "Cost": 5000, "FundsThresholdBeforeOffered": 0 if lch["tier"] == "mid" else 200000,
                        "Prerequisites": [f"{AUTHOR}.bs_bb_{lch['short']}"]})
    return out


BB_WHITELIST = [f"{AUTHOR}.{g['short']}" for g in GUNS + DEFENSES if g["tier"] == "early"] + \
               [f"{AUTHOR}.{f['short']}" for f in FACTORIES] + \
               [f"{AUTHOR}.{lch['short']}" for lch in LAUNCHERS if lch["tier"] == "early"]


def _mod_description():
    """Texto do menu Mods, com as contagens tiradas dos dados (armas, lancadores, misseis, fabricas, limites)."""
    n_w, n_l, n_m, n_f = len(GUNS) + len(DEFENSES), len(LAUNCHERS), len(MISSILE_TYPES), len(FACTORIES)
    lim = {lm["category"]: lm["max"] for lm in LIMIT_DEFS}
    nuke, flag = lim.get("bs_limit_nuke", 2), lim.get("bs_limit_flagship", 2)
    pt = (
        "Armas de convés operadas pela tripulação que usam MUNIÇÃO em vez de energia.\n\n"
        f"- {n_w} armas e {n_l} lança-mísseis de convés com {n_m} tipos de míssil, do início ao fim de jogo.\n"
        "- Início de jogo: metralhadoras, autocanhão de 20 mm, flak leve e a caixa de micromísseis Tocandira.\n"
        "- Meio de jogo: metralhadora quádrupla, minigun, canhão naval de 76 mm, gatling de plasma, CIWS e o "
        "lançador de mísseis Caipora, todos com overclock.\n"
        "- Fim de jogo: canhão rotativo de 30 mm, canhão naval duplo de 155 mm, plasma pesado, flak pesada, "
        "obuseiro nuclear, torre tripla de 406 mm e a bateria de mísseis Mula-sem-Cabeça, todos com overclock.\n"
        "- Flak e CIWS que só defendem: destroem vários mísseis, minas, granadas e disparos de uma vez, mas gastam muita munição.\n"
        f"- Logística de carregadores: {n_f} fábricas novas, todas com overclock; a tripulação leva os carregadores "
        "até as armas. Os lança-mísseis usam as peças de míssil do jogo base.\n"
        "- Seletor de munição: Padrão, Perfurante, Perfurante-Explosiva e P.E.M., além de células de plasma e "
        "projéteis nucleares.\n"
        f"- Limites por nave: {nuke} armas nucleares (Boiúna e Mula-sem-Cabeça) e {flag} torres de encouraçado.\n\n"
        "Compatível com Star Wars: A Cosmos Divided.")
    en = (
        "Deck-mounted, crew-operated weapons that run on AMMUNITION instead of power.\n\n"
        f"- {n_w} weapons and {n_l} deck missile launchers with {n_m} missile types, from early to late game.\n"
        "- Early game: machine guns, 20 mm autocannon, light flak and the Tocandira micro-missile box.\n"
        "- Mid game: quad machine gun, minigun, 76 mm naval cannon, plasma gatling, CIWS and the Caipora missile "
        "launcher, all with overclock.\n"
        "- Late game: 30 mm rotary cannon, twin 155 mm naval gun, heavy plasma, heavy flak, nuclear howitzer, "
        "triple 406 mm turret and the Mula-sem-Cabeça missile battery, all with overclock.\n"
        "- Defense-only flak and CIWS that shred many missiles, mines, shells and bolts at once, but eat ammo.\n"
        f"- Magazine logistics: {n_f} new factories, all with overclock; crew carry the magazines to the guns. The "
        "missile launchers use the vanilla missile parts.\n"
        "- Ammo selector: Standard, Armor-Piercing, AP-Explosive and EMP, plus plasma cells and nuclear shells.\n"
        f"- Per-ship limits: {nuke} nuclear weapons (Boiúna and Mula-sem-Cabeça) and {flag} battleship turrets.\n\n"
        "Compatible with Star Wars: A Cosmos Divided.")
    return f"{pt}\n\n---\n\n{en}"


MOD["description"] = _mod_description()


from bs_strings import strings  # noqa: E402,F401
