"""Dados do Bullet Strike.

Os NUMEROS de balanceamento ficam em tools/spec/bullet_strike_spec.json (gerado pelo painel de design
e editavel a mao). Este arquivo converte o spec para o formato que o gerador usa e acrescenta as
dicas de implementacao (estilo de arte, tipo de cano, efeitos) que nao sao balanceamento.
"""

import json
import os

from rules_dsl import Q

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "spec", "bullet_strike_spec.json")
with open(SPEC_PATH, encoding="utf-8") as fh:
    SPEC = json.load(fh)

VERSION = SPEC.get("version", "1.0.0")
AUTHOR = "rafaeltessaro"

MOD_TAG_EN = "\n<s16><gray>Mod: Bullet Strike</gray></s16>"
MOD_TAG_PT = "\n<s16><gray>Mod: Bullet Strike</gray></s16>"

MOD = {
    "description_en": (
        "Deck-mounted, crew-operated weapons that run on AMMUNITION instead of power.\n\n"
        "- Early game: light machine guns and autocannons (1-2 tiles).\n"
        "- Mid game: minigun, naval automatic cannon, plasma gatling, CIWS (with overclock).\n"
        "- Late game: heavy naval guns, heavy rotary cannon, heavy plasma, nuclear howitzer (with overclock).\n"
        "- Flak/CIWS that shreds many missiles, mines, shells and laser bolts at once - but eats ammo.\n"
        "- Magazine logistics: factories pack ammo into magazines that crew carry to the guns.\n"
        "- Ammo selector: Standard, Armor-Piercing, AP-Explosive and EMP. Plus plasma cells and nuclear shells.\n\n"
        "Compatible with Star Wars: A Cosmos Divided.\n\n"
        "Armas de convés operadas por tripulação que usam MUNIÇÃO em vez de energia. Compatível com SW:ACD."
    ),
}


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


def _shot_spec(w, ammo, t, oc=None):
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
    if oc:
        dmg = round(dmg * oc.get("damage_factor", 1))
        exp_d = round(exp_d * oc.get("damage_factor", 1))
        if shield is not None:
            shield = round(shield * oc.get("damage_factor", 1))
        rf = oc.get("range_factor", 1)
        rng = min(600, round(rng * rf))
        speed = round(speed * (1 + (rf - 1) * 1.5))
    cal = _caliber(dmg + exp_d)
    look = "med" if cal in ("mg", "med") else "large"
    size = {"mg": 0.18, "med": 0.32, "large": 0.7, "deck": 1.05}[cal]
    color = GLOW.get(ammo, GLOW["std"])
    s = {
        "file": name, "id": f"{AUTHOR}.{name}", "title": f"{w['name_en']} - {ammo}{' (overclock)' if oc else ''}",
        "range": rng, "speed": max(60, speed), "health": w.get("shot_hp") or max(60, round((dmg + exp_d) * 0.35)),
        "look": look, "sprite_size": size, "glow_color": color,
        "glow_size": {"mg": [3, 1.5], "med": [5, 2.5], "large": [10, 5], "deck": [16, 8]}[cal],
        "fx": {"mg": "mg", "med": "med", "large": "large", "deck": "deck"}[cal],
        "volume": {"mg": 0.5, "med": 0.6, "large": 0.8, "deck": 1.0}[cal],
        "max_conc": {"mg": 30, "med": 20, "large": 12, "deck": 8}[cal],
        "shake": {"mg": 0, "med": 0, "large": 0.04, "deck": 0.08}[cal],
        "radius": {"mg": 0.1, "med": 0.15, "large": 0.3, "deck": 0.45}[cal],
        "fire": fire,
    }
    if cal in ("large", "deck") and not w.get("spinup"):
        s["trail"] = "large" if cal == "large" else "deck"
    if ammo == "plasma":
        s["look"] = "energy"
        s["fx"] = "plasma"
        s["sprite_wh"] = [size * 4, size * 1.6]
        s.pop("trail", None)
        if cal in ("large", "deck"):
            s["trail"] = "plasma"
    if ammo == "emp":
        s["fx"] = "emp"
    if ammo == "nuclear" or (exp_d and pen <= 1 and ammo in ("std", "bullet", "nuclear", "plasma") and exp_d >= dmg * 0.25):
        # granada que explode no impacto
        s.update({"kind": "explosive", "damage": dmg, "explosion": [max(1.0, exp_r), exp_d],
                  "explosion_fire": 50 if ammo != "plasma" else None,
                  "shield_factor": (shield / max(1, dmg + exp_d)) if shield else 1})
        if ammo == "nuclear":
            s.update({"fx": "nuke", "friendly_fire": True, "shake": 0.35, "volume": 1.0, "max_conc": 4,
                      "struct_explosion": [max(2, exp_r * 0.8), round(exp_d * 0.3)], "category": "missile"})
            s["extra_particles"] = None
        return s
    s.update({"kind": "kinetic", "damage": dmg, "penetration": pen,
              "struct_damage": max(1, round(dmg / 4))})
    if shield is not None and abs(shield - dmg) > 1:
        s["shield_damage"] = shield
    if ammo == "ap":
        s["armor_factor"] = 0.5
    if ammo == "aphe":
        s["armor_factor"] = 0.75
        if exp_d:
            s["finish_explosion"] = [max(1.0, exp_r), exp_d]
            s["explosion_fire"] = 40
    if ammo == "std" and exp_d and pen > 1:
        s["finish_explosion"] = [max(1.0, exp_r), exp_d]
    if ammo == "emp":
        drain = t.get("emp_drain", 0) or 0
        if drain:
            s["emp_shield_drain"] = drain
            s["emp_drain"] = round(drain * 0.6)
    if ammo == "plasma":
        s["heat"] = round(min(400, dmg * 0.08))
    if (w.get("anti_projectile") or {}).get("blast_radius_m") == 0:
        s["anti_projectile"] = (w["anti_projectile"] or {}).get("damage_vs_shots", 100)
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
                res = RES_BY_AMMO.get(a, w["ammo_resource"])
                modes.append((i, a, res, t))
        else:
            res = w["ammo_resource"]
            a = "bullet" if res == "bullet" else ("plasma" if "plasma" in res else
                                                  "nuclear" if "nuke" in res else "std")
            modes.append((0, a, res, _ammo_table(w, a)))
        gmodes = []
        for k, a, res, t in modes:
            s = _shot_spec(w, a, t)
            SHOTS.append(s)
            m = {"mode": k, "ammo": a, "res": res, "shots_per_unit": int(w.get("shots_per_resource_unit") or 1),
                 "units_per_shot": int(w.get("resource_units_per_shot") or 1),
                 "storage": int(w.get("internal_storage_units") or 4), "shot": s["file"],
                 "show_pen": s["kind"] == "kinetic"}
            if oc:
                so = _shot_spec(w, a, t, oc)
                SHOTS.append(so)
                m["shot_oc"] = so["file"]
            gmodes.append(m)
        nb = int(w.get("barrels") or 1)
        burst = int(w.get("burst") or 1)
        visual_barrels = 1 if spin else nb
        pattern = "alternate"
        if burst > 1 and burst == nb:
            pattern = "volley"
        shots_per_trigger = (visual_barrels if pattern == "volley" else 1)
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
        if nb > 1 and not spin:
            g["barrels"]["count"] = min(nb, 4)
            if nb > 4:
                g["barrels"]["count"] = 3
        if spin:
            g["spin"] = {"max": round(spin["max_rate"] / spin["min_rate"], 3), "up": spin["seconds_to_max"],
                         "down": round(spin["seconds_to_max"] / 2, 2)}
        if w.get("crew_stun"):
            st = w["crew_stun"]
            g["stun"] = {"radius": st["radius_m"], "duration": st["seconds"],
                         "oc_radius": st["radius_m"] * 1.3, "oc_duration": st["seconds"] * 1.5}
        if oc:
            fr = oc.get("fire_rate_factor", 1) or 1
            g["oc"] = {"fire_interval_factor": round(1 / fr, 4), "half_spread": round(g["spread"] * 1.25, 3),
                       "recoil_factor": 1.6, "heat_per_shot": oc["heat_per_shot"],
                       "heat_per_second": oc.get("heat_per_second", 0)}
            if spin:
                g["oc"]["max_spin"] = g["spin"]["max"]
        GUNS.append(g)


def _defense(w, hint, short, oc, ap):
    rng = w["range_m"]
    beam = {"kind": "flak", "file": f"bs_flak_{short.replace('bs_', '')}", "dir": short,
            "range": rng, "vs_shots": ap["damage_vs_shots"], "vs_ships": w["damage_per_hit_std"],
            "radius": ap["blast_radius_m"], "ship_radius": max(1.5, ap["blast_radius_m"] * 0.6),
            "categories": ["missile", "mine", "bullet", "laser", "ion_shot"],
            "offset": [0.5, max(2.0, rng / 60)], "volume": 0.3, "max_conc": 12, "particles": 2}
    SHOTS.append(beam)
    nb = int(w.get("barrels") or 1)
    res = w["ammo_resource"]
    d = {
        "short": short, "key": "BS" + "".join(p.capitalize() for p in short.split("_")[1:]),
        "name_en": w["name_en"], "name_pt": w["name_ptbr"], "codename": w.get("codename", ""), "tier": w["tier"],
        "size": w["size"], "crew": w["crew"], "cp": w["command_points"], "hp": w["max_health"], "cost": w["build_cost"],
        "ring": w.get("prohibit_ring_tiles", 1), "arc": w["firing_arc_deg"], "rotate": w["rotate_speed_deg_s"],
        "fire_interval": round(1.0 / w["fire_rate_shots_per_s"], 4), "beam": beam["file"],
        "ammo": {"res": res, "shots_per_unit": int(w.get("shots_per_resource_unit") or 1),
                 "units_per_shot": int(w.get("resource_units_per_shot") or 1),
                 "storage": int(w.get("internal_storage_units") or 4)},
        "barrels": {"count": 1 if hint["barrel"] == "gatling" else min(nb, 4), "spacing": 0.3 if w["size"][0] <= 3 else 0.5,
                    "length": {"early": 0.9, "mid": 1.4, "late": 1.9}[w["tier"]],
                    "width": 0.14 if hint["barrel"] != "gatling" else 0.3},
        "fx": dict(FX["flak"]), "fire_pref_default": 1,
        "art": {"style": hint["style"], "barrel": hint["barrel"], "accent": hint["accent"]},
        "desc": w.get("visual_concept", ""), "spec": w,
    }
    if oc:
        cloud = {"kind": "cloud", "file": f"bs_cloud_{short.replace('bs_', '')}", "dir": short,
                 "id": f"{AUTHOR}.bs_cloud_{short.replace('bs_', '')}",
                 "radius": max(2.0, ap["blast_radius_m"] * 0.75), "lifetime": 3.0,
                 "pool": round(ap["damage_vs_shots"] * 0.5)}
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
        "art": {"kind": kind, "accent": acc}, "spec": f,
    })

AMMO_CHOICES = [
    (0, "bs_ammo_std", "PartToggles/BSAmmo_Std", "ammo_std.png"),
    (1, "bs_ammo_ap", "PartToggles/BSAmmo_AP", "ammo_ap.png"),
    (2, "bs_ammo_aphe", "PartToggles/BSAmmo_APHE", "ammo_aphe.png"),
    (3, "bs_ammo_emp", "PartToggles/BSAmmo_EMP", "ammo_emp.png"),
]

ALL_PARTS = {g["short"]: g for g in GUNS + DEFENSES}
ALL_PARTS.update({f["short"]: f for f in FACTORIES})


def _part_ref(short, field):
    return f"&<../parts/{short}/{short}.rules>/Part/{field}"


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
            idx = {"std": 0, "ap": 1, "aphe": 2, "emp": 3}.get(a)
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
    return out


BB_WHITELIST = [f"{AUTHOR}.{g['short']}" for g in GUNS + DEFENSES if g["tier"] == "early"] + \
               [f"{AUTHOR}.{f['short']}" for f in FACTORIES]


from bs_strings import strings  # noqa: E402,F401
