"""Tiros de missil 2.0 do Bullet Strike (dono: WP07): Jararaca/Muricoca (HE), Piranha (submunicao estilo Sunflower),
Poraque 2.0 (PEM que drena o escudo) e Iara (nuclear de 2 estagios, so a ogiva).

Modulo de conteudo do registro do tools/build_mod.py (API = 2):
  SHOT_KINDS = ('missile',) + build_shot(out, s, header): escreve shots/<dir>/<file>.rules e, na MESMA pasta, os
    filhos (portador da Piranha -> <file>_child; Iara -> <file>_warhead) e as petalas da Piranha com
    missiles.cluster_petals = bullets (<file>_petal_a / _petal_b); devolve o rel do arquivo principal (o lancador le
    ctx['shot_rel'][<file>]).
  shots(DATA): acrescenta cada DATA.MISSILES (bs_data_missiles, WP06; kind 'missile', owner 'bsgen.missile_shots') a
    DATA.SHOTS e completa os dados visuais (corpo/brilho/escapamento de reserva, som, petalas, filhos com o tipo e a
    fase do pai) antes do annotate do bsgen.missile_fx.
  selfcheck(mod_dir, spec): confere os arquivos gerados (ver selfcheck()).

Fontes: tools/spec/bullet_strike_missiles.json (missiles.missile_types, cluster_sunflower, poraque_2, iara,
launchers[].modes[].damage/flight, ja organizados em DATA.MISSILES pelo bs_data_missiles) e os switches missiles.*
(valores efetivos em s['variants'] = bs_data_missiles.MISSILE_VARIANTS):
  cluster_randomize_target  on (RandomizeTarget no SpawnBullets) | off_fan (sem RandomizeTarget, homing com Delay
                            0,35 e o ima 1.x ProximityAcceleration Range 30 / Acceleration 25)
  cluster_open              proximity (DeathByEnemyProximity 300/400 m + espoleta de tempo) | timer (so a espoleta, no
                            tempo de voo ate R - 300/400 m)
  cluster_lite              false | true (BS_CLUSTER_LITE=1: 6/10 filhos com dano x2 e HP x2, mesmos totais)
  cluster_petals            particles (petalas = particulas do bsgen.missile_fx no BURST) | bullets (4 tiros-petala)
  poraque_overload          true = AreaShieldStatusApplication cosmoteer.shield_overload no HitShield | false (safe)
  poraque_pulses            off | repeating (o pulso do casco vira Type = Repeating, 3 x 1/3 do dreno)
  iara_hp                   HP do estagio e da ogiva (ja aplicado pelo bs_data_missiles)
  e as variantes de passagem source_part_collision_delay, homing_avoidance, cluster_hp_inherit, emp_rider,
  emp_shield_drain.

Nucleo seguro para o conves (copiado do 1.x, shots/missile_he/missile_he.rules l.9-48, 110-123): SimpleHit com
FriendlyShipLowCollisions = false + FriendlyShipHighCollisions = false e SourcePartCollisionDelay; Targetable
categoria "missile" (abatido = so o efeito do HitFriendly); explosoes SEM Friendlies; numeros escalaveis
{ BaseValue; EffectScaleExponent = 1 }; o mesmo nucleo em todo filho (submunicao e ogiva).

Visual: seams do bsgen.missile_fx (FX, API 2): visual_components (corpo de bs_missiles2, luz em duas sprites do
fxkit.light_pair, escapamento), petal_sprite (petala recortada do atlas), decorate (escala da fase e extras de
impacto/abertura/separacao). Sem o modulo (BS_FX_EXT=0): corpo vanilla missile_he.png, halo so no espaco
(_litReflectiveStrength 0) e a midia vanilla de impacto; petalas com o debris.png vanilla.

Importa de bsgen/shots.py (WP02) so D, OWN_SHIP_PASS e _val. Nunca importa bs_data no nivel do modulo (o bs_data
importa este modulo pelo load_launchers).
"""

import json
import os
import re

from rules_dsl import Q, Inh, render
from bsgen import common as C
from bsgen.shots import D as SD, OWN_SHIP_PASS, _val

API = 2
SHOT_KINDS = ("missile",)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FX_SPEC_PATH = os.path.join(ROOT, "tools", "spec", "bullet_strike_missile_fx.json")
with open(FX_SPEC_PATH, encoding="utf-8") as _fh:
    FX_SPEC = json.load(_fh)
SOUNDS = FX_SPEC["SOUNDS"]          # slots de som por tipo: launch, impact, deploy, open (Piranha), drain (Poraque)
TYPES = FX_SPEC["types"]

MSL_D = f"{SD}/missile_he"
MSL_E = f"{SD}/missile_emp"
MSL_N = f"{SD}/missile_nuke"
VANILLA_BODY = MSL_D                 # corpo de reserva (missile_he.png + normais)
DEBRIS = "./Data/common_effects/particles/debris.png"   # petala de reserva (atlas vanilla 4 x 4 de 64 px)

# midia base de impacto (sem o bsgen.missile_fx); o missile_fx so poe escala e extras por cima (decorate)
MISSILE_MEDIA = {
    "he": {"particles": [f"{MSL_D}/particles/missile_he_hit.rules", f"{MSL_D}/particles/missile_he_flash.rules",
                         f"{MSL_D}/particles/missile_he_smoke.rules"], "sound": ("he", "impact")},
    # missile_emp.rules l.198-213 (orbe/raios/onda de choque)
    "emp": {"particles": [f"{MSL_E}/particles/missile_emp_hit_orb.rules", f"{MSL_E}/particles/missile_emp_hit_bolts.rules",
                          f"{MSL_E}/particles/missile_emp_hit_shockwave.rules"], "sound": ("emp", "impact")},
    # cogumelo vanilla (missile_nuke_stage1.rules l.163-169): so a Iara (a Boiuna 2.0 nao e nuclear)
    "nuclear": {"particles": [f"{MSL_N}/particles/missile_nuke_flash_light.rules",
                              f"{MSL_N}/particles/missile_nuke_flash.rules",
                              f"{MSL_N}/particles/missile_nuke_shockwave.rules",
                              f"{MSL_N}/particles/missile_nuke_hit.rules"], "sound": ("nuclear", "impact")},
    # Iara abatida: so o clarao (HitFriendly do missile_nuke_stage1.rules l.190-200)
    "nuclear_fizzle": {"particles": [f"{MSL_N}/particles/missile_nuke_flash.rules"], "sound": ("nuclear", "impact")},
    # abertura da Piranha (BURST v2, <= 40 particulas com os extras do missile_fx): clarao (1) + baforada (10)
    "burst": {"particles": [f"{MSL_D}/particles/missile_he_flash.rules", f"{SD}/bullet_med/particles/bullet_smoke_med.rules"],
              "sound": ("cluster", "open")},
    # portador da Piranha abatido antes de abrir: clarao + baforada
    "burst_pop": {"particles": [f"{MSL_D}/particles/missile_he_flash.rules",
                                f"{SD}/bullet_med/particles/bullet_smoke_med.rules"], "sound": ("cluster", "impact")},
    # minimissil: <= 8 particulas, sem fumaca (cluster_sunflower.performance_budget: preset 'cluster_child')
    "child": {"particles": [f"{MSL_D}/particles/missile_he_hit.rules", f"{MSL_D}/particles/missile_he_flash.rules",
                            f"{SD}/chaingun_shot/overclock/particles/chaingun_shot_overclock_hit.rules"],
              "sound": ("cluster", "impact")},
    "child_pop": {"particles": [f"{MSL_D}/particles/missile_he_flash.rules"], "sound": ("cluster", "impact")},
}
PLUME_LIGHT = {"he": f"{MSL_D}/particles/missile_he_thruster_plume_light.rules",
               "cluster": f"{MSL_D}/particles/missile_he_thruster_plume_light.rules",
               "emp": f"{MSL_E}/particles/missile_emp_thruster_plume_light.rules",
               "nuclear": f"{MSL_N}/particles/missile_nuke_thruster_plume_light.rules"}
# descarga do PEM (missile_emp.rules l.165-178): sizzle + raios + dreno
EMP_DRAIN_MEDIA = [f"{MSL_E}/particles/missile_emp_hit_sizzle.rules", f"{MSL_E}/particles/missile_emp_lightning.rules",
                   f"{MSL_E}/particles/missile_emp_drain.rules"]
# particulas por disparo (EmitPerOneShot Max) dos arquivos vanilla da conta da salva (texto 0.30.2 = 0.30.5)
VANILLA_PARTICLES = {
    f"{MSL_D}/particles/missile_he_hit.rules": 3,
    f"{MSL_D}/particles/missile_he_flash.rules": 1,
    f"{MSL_D}/particles/missile_he_smoke.rules": 20,
    f"{SD}/bullet_med/particles/bullet_smoke_med.rules": 10,
    f"{SD}/chaingun_shot/overclock/particles/chaingun_shot_overclock_hit.rules": 3,
}
SALVO_PARTICLE_CAP = 960        # orcamento da salva da Mula (missiles.cluster_sunflower.performance_budget.estimate)
BURST_PARTICLE_CAP = 40         # BURST do portador (1 clarao, 4 petalas, <= 12 baforada, <= 20 faiscas)
CHILD_PARTICLE_CAP = 8          # impacto do minimissil
CHILD_MAX_CONC = 6              # som do impacto dos minimisseis (MaxConcurrent)
OVERLAP = 0.5                   # minimisseis que explodem ao mesmo tempo na conta da salva

# petalas tiro (missiles.cluster_petals = bullets): 2 + 2 por portador, cada par com um giro
PETALS = (("a", 2, "-135d", "270d", "540d"), ("b", 2, "-45d", "90d", "-420d"))
PETAL_SPEED = 32                # + RandomExtraSpeed [-7, 8] = 25-40 m/s (cluster_sunflower.petals)
PETAL_LIFE = [0.5, 0.8]

_RIDER_RE = re.compile(r"StatusApplication\s+(\S+)\s+StatusDuration\s+([\d.]+),\s*StatusValue\s+([\d.]+)")


def _opt(name):
    """Modulo de efeitos (FX) com API >= 2, ou None (ausente / 1.x / BS_FX_EXT=0)."""
    if os.environ.get("BS_FX_EXT", "1") == "0":
        return None
    return C.content_module(name, min_api=2)


def _mfx():
    return _opt("bsgen.missile_fx")


def _num(v):
    """int quando inteiro (campos Int32 do jogo nao aceitam 7666.667)."""
    f = float(v)
    return int(round(f)) if abs(f - round(f)) < 1e-9 else f


def _deg(v):
    """300 -> '300d'; '300d' fica."""
    s = str(v).strip()
    return s if s.endswith("d") else f"{_num(s)}d"


# ============================================================================= nucleo de conves
def _sounds(typ, slot):
    lst = (SOUNDS.get(typ) or {}).get(slot) or []
    if not lst:
        raise KeyError(f"missile_shots: slot de som {typ}.{slot} vazio em {os.path.basename(FX_SPEC_PATH)}")
    return lst


def _audio(typ, slot, volume, max_conc, speed_var=0.15):
    return Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(x) for x in _sounds(typ, slot)],
                                              "Volume": volume, "SpeedVariation": speed_var,
                                              "MaxConcurrent": max_conc})


def _missile_media(s, key, shake=True):
    mm = MISSILE_MEDIA[key]
    media = [f"&<{p}>" for p in mm["particles"]]
    media.append(_audio(*mm["sound"], s.get("volume", 0.7), s.get("max_conc", 16)))
    if shake and s.get("shake"):
        media.append(Inh("/BASE_SHAKE", {"ShakeAmount": s["shake"], "Duration": 0.5}))
    return media


def _deck_flags(s, hit_type="SimpleHit"):
    v = s.get("variants", {})
    delay = "0.3" if v.get("source_part_collision_delay") == "s_0_3" else "1.5 / (&/Simulation/PhysicsUpdatesPerSecond)"
    return {"Type": hit_type, "SourcePartCollisionDelay": delay, **OWN_SHIP_PASS}


def _missile_hit(s, hit_op, hit_shield, friendly_key):
    hit = _deck_flags(s)
    hit["HitShield"] = hit_shield if hit_shield is not None else "&HitOperational"
    hit["HitOperational"] = hit_op
    hit["HitStructural"] = "&HitOperational"
    hit["HitFriendly"] = {"MediaEffects": _missile_media(s, friendly_key, shake=False)}
    return hit


def _homing(s, turn, delay):
    v = s.get("variants", {})
    homing = {"Type": "TargetHoming", "TurnVelocity": _deg(turn)}
    if delay is not None:
        homing["Delay"] = delay
    if v.get("homing_avoidance") == "raycast_250":
        homing["AvoidanceRaycastDistance"] = 250
    elif v.get("homing_avoidance") == "no_avoid_friendlies":
        homing["AvoidsFriendlies"] = False
    homing["VelocityCompensation"] = s.get("velocity_compensation") or "60%"
    return homing


def _halo(L, color, size, x):
    """Brilho de reserva (sem o fxkit): so o HALO no espaco (_litReflectiveStrength 0, cor/4, unlit 0,5: a mesma
    regra do fxkit.light_pair, ADDENDUM G7a), nunca a luz de casco que lavaria o casco branco."""
    vc = [int(round(float(c) / 4)) for c in list(color)[:3]]
    return {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": 0, "IsLight": True, "Offset": [round(x, 3), 0],
            "Sprite": {"Texture": {"File": Q("./Data/common_effects/particles/blob.png"), "MipLevels": "max",
                                   "SampleMode": "Linear"},
                       "Size": list(size), "VertexColor": vc, "TargetBlendMode": "Add",
                       "Shader": Q("./Data/common_effects/fancy_light.shader"), "_z": 1, "_nrmlStrengthLimit": 1,
                       "_litReflectiveStrength": 0, "_litAdditiveStrength": 0, "_unlitAdditiveStrength": 0.5}}


def _missile_visuals(s, glow=True, plume=True):
    """Corpo + luz + escapamento. Seam do bsgen.missile_fx (visual_components); sem ele, o corpo vanilla
    (missile_he.png no tamanho da caixa), o halo so no espaco e a luz vanilla do propulsor."""
    mfx = _mfx()
    r = C.call(mfx, "visual_components", s, glow, plume)
    if r is not None:
        return r
    w, h = s["sprite_wh"]
    body = {"Type": "Sprite", "RenderBucket": "BulletUpper3",
            "Sprite": {"Texture": {"File": Q(f"{VANILLA_BODY}/missile_he.png"), "MipLevels": "max"}, "Size": [w, h]}}
    if s.get("role", "main") != "child":
        # minimissil sem normais (orcamento da salva: performance_budget.per_mini_components)
        body = {"Type": "Sprite", "RenderBucket": "BulletUpper3", "IsLit": True, "Sprite": body["Sprite"],
                "NormalsTexture": {"File": Q(f"{VANILLA_BODY}/missile_he_normals.png"), "MipLevels": "max"}}
    comps = {"Sprite": body}
    if glow:
        comps["GlowSprite"] = _halo(w, s["glow_color"], s["glow_size"], -0.45 * w)
    if plume:
        comps["MediaEffects"] = {"Type": "MediaEffects", "Offset": [s["plume_offset"], 0], "Rotation": "180d",
                                 "MediaEffects": [f"&<{PLUME_LIGHT[s['payload']]}>"]}
    return comps


def _targetable(hp):
    # abatido no ar: so o efeito, sem dano em area ("No AOE damage when shot down", missile_he.rules l.116)
    return {"Type": "Targetable", "Health": int(hp), "TargetCategory": Q("missile"), "OnDeath": "&../Hit/HitFriendly"}


def _arc(pair):
    return [_deg(a) for a in pair]


def _proximity_accel(rng, accel, ships, bullets, friendlies, enemies):
    """ProximityAcceleration: o ima 1.x (buzzdroid.rules l.37-44) da variante off_fan."""
    return {"Type": "ProximityAcceleration", "Range": rng, "Acceleration": accel, "AccelerateTowardsShips": ships,
            "AccelerateTowardsBullets": bullets, "AccelerateTowardsFriendlies": friendlies,
            "AccelerateTowardsEnemies": enemies}


# ============================================================================= dados (gancho shots)
def _spec():
    import bs_data as D        # import tardio (ver docstring)
    return D.MSPEC["missiles"]


def _body(box):
    """Escala do corpo de reserva pela caixa de fisica (missil vanilla: BoxPhysics [1.5, .5], sprite [2, 1])."""
    k = box[0] / 1.5
    return {"sprite_wh": [round(2 * k, 3), round(1 * k, 3)], "glow_size": [round(4.5 * k, 2), round(2.2 * k, 2)],
            "plume_offset": round(-0.6 * box[0], 3)}, k


def _burst_params():
    """Distance / Arc / Spread do SpawnBullets do portador, lidos do texto de cluster_sunflower.carrier.BURST."""
    txt = _spec()["cluster_sunflower"]["carrier"]["BURST"]

    def pair(name, unit=""):
        m = re.search(name + r"\s*=\s*\[\s*(-?[\d.]+)" + unit + r"\s*,\s*(-?[\d.]+)" + unit + r"\s*\]", txt)
        if not m:
            raise ValueError(f"missile_shots: cluster_sunflower.carrier.BURST sem {name} ({txt!r})")
        return [_num(m.group(1)), _num(m.group(2))]
    return {"Distance": pair("Distance"), "Arc": pair("Arc", "d"), "Spread": pair("Spread", "d")}


def _lite_count(n):
    return {12: 6, 20: 10}.get(n, n // 2)


def _flight_time(v0, a, dist):
    """Tempo de voo ate dist com velocidade inicial v0 e aceleracao a (a mesma conta do flight_time_max_range_s)."""
    if a <= 0:
        return dist / v0
    return (-v0 + (v0 * v0 + 2 * a * dist) ** 0.5) / a


def _prepare(s):
    """Completa um tiro de DATA.MISSILES (idempotente): corpo/brilho de reserva, som, filhos com tipo/fase/variantes
    do pai, valores efetivos dos switches da Piranha e as petalas tiro."""
    if s.get("_ms_ready"):
        return s
    v = s.get("variants") or {}
    t = s["payload"]
    vis, k = _body(s["box"])
    s.update(vis)
    s["glow_color"] = list(TYPES[t]["halo"])
    s["volume"] = round(min(1.0, 0.45 + 0.4 * k), 2)
    s["max_conc"] = 16
    s["shake"] = round(min(0.15, 0.04 + 0.1 * k), 3)
    if t == "nuclear":
        s.update({"volume": 1.0, "max_conc": 4, "shake": 0.35})
    for c in s.get("children", []):
        c.setdefault("payload", t)
        c.setdefault("tier", s["tier"])
        c.setdefault("variants", v)
        cvis, ck = _body(c["box"])
        c.update(cvis)
        c["glow_color"] = list(TYPES[t]["halo"])
        if c["role"] == "child":
            lite = bool(v.get("cluster_lite"))
            c["n"] = _lite_count(c["count"]) if lite else c["count"]
            c["hp_eff"] = c["hp"] * 2 if lite else c["hp"]
            c["damage_eff"] = c["damage"] * 2 if lite else c["damage"]
            c.update({"volume": 0.5, "max_conc": CHILD_MAX_CONC, "shake": 0.03})
        else:
            c.update({"volume": s["volume"], "max_conc": s["max_conc"], "shake": s["shake"]})
    s["petal_shots"] = []
    if t == "cluster" and v.get("cluster_petals") == "bullets":
        for tag, n, a0, a1, spin in PETALS:
            s["petal_shots"].append({
                "role": "petal", "petal": tag, "count": n, "arc": [a0, a1], "spin": spin, "payload": t,
                "tier": s["tier"], "variants": v, "file": f"{s['file']}_petal_{tag}", "id": f"{s['id']}_petal_{tag}",
                "title": f"Cluster nose petal {tag.upper()} ({s['codename']}) - {s['launcher_codename']}"})
    s["_ms_ready"] = True
    return s


def shots(DATA):
    """Gancho do registro: os tiros de missil (um por lancador e modo) entram em DATA.SHOTS."""
    have = {x.get("file") for x in DATA.SHOTS}
    for s in getattr(DATA, "MISSILES", None) or []:
        _prepare(s)
        if s["file"] not in have:
            DATA.SHOTS.append(s)
            have.add(s["file"])


# ============================================================================= cargas
def _payload_he(s):
    d = s["damage"]
    fx = [{"Type": "ExplosiveDamage", "TotalDamage": _val(_num(d["ExplosiveDamage"])), "Radius": d["Radius"]},
          {"Type": "Impulse", "Impulse": _val(_num(d.get("Impulse", 0)))}]
    hit = _missile_hit(s, {"HitEffects": fx, "MediaEffects": _missile_media(s, "he")}, None, "he")
    return {"stats": {"STAT_DAMAGE": s["stat_damage"], "STAT_RADIUS": s["stat_radius"]}, "hit": hit}


def _child_of(s, role):
    return next(c for c in s.get("children", []) if c["role"] == role)


def _payload_cluster(s):
    """Piranha estilo Sunflower: o portador nao tem ogiva; proximidade (300/400 m), tempo ou impacto abrem o cardume
    (BURST na raiz: SpawnBullets de 12/20 minimisseis em leque de 120 graus para a frente, RandomizeTarget)."""
    v = s.get("variants", {})
    car = s["carrier"]
    child = _child_of(s, "child")
    bp = _burst_params()
    spawn = {"Type": "SpawnBullets", "Bullet": "&~/CHILD", "Count": int(child["n"]), "Distance": bp["Distance"],
             "Arc": _arc(bp["Arc"]), "Spread": _arc(bp["Spread"]), "InheritVelocity": True,
             "HealthFactor": _val(1)}
    if v.get("cluster_randomize_target", "on") == "on":
        # campo bool do SpawnBulletsEffectRules (0.30.4c): cada filhote mira uma peca ao acaso (T-MSL-CLUSTER)
        spawn["RandomizeTarget"] = True
    effects = [spawn]
    root = {"CHILD": f"&<{child['file']}.rules>"}
    for p in s.get("petal_shots", []):
        key = f"PETAL_{p['petal'].upper()}"
        root[key] = f"&<{p['file']}.rules>"
        effects.append({"Type": "SpawnBullets", "Bullet": f"&~/{key}", "Count": int(p["count"]),
                        "Distance": [0.1, 0.3], "Arc": list(p["arc"]), "Spread": ["-20d", "20d"],
                        "InheritVelocity": True})
    root["BURST"] = {"HitEffects": effects, "MediaEffects": _missile_media(s, "burst", shake=False)}
    pf = _spec()["cluster_sunflower"]["carrier"]["open_triggers"]["ProximityFuse"]
    timed = car["timed_fuse"]
    death = {}
    if v.get("cluster_open", "proximity") == "timer":
        # sem proximidade: abre no tempo de voo ate R - 300/400 m (contra alvo mais perto o impacto abre)
        timed = round(min(timed, _flight_time(s["speed"], s["accel"], s["range"] - car["proximity_range"])), 2)
    else:
        death["ProximityFuse"] = {"Type": "DeathByEnemyProximity", "Interval": car["proximity_interval"],
                                  "Range": car["proximity_range"], "StartDelay": car["proximity_start_delay"],
                                  "DetectsShips": bool(pf.get("DetectsShips", True)),
                                  "DetectsBullets": bool(pf.get("DetectsBullets", False)),
                                  "FactorEffectsWith": "Targetable", "OnDeath": "&~/BURST"}
    # os caminhos do BURST passam o HP que restou ao portador para os filhotes (HealthFactor com FactorEffectsWith =
    # Targetable: missile_nuke_stage1.rules DeployDeath)
    death["TimedFuse"] = {"Type": "DeathByLifetime", "Lifetime": timed, "FactorEffectsWith": "Targetable",
                          "OnDeath": "&~/BURST"}
    hit = _deck_flags(s)
    if v.get("cluster_hp_inherit", "all_paths") == "all_paths":
        hit["FactorEffectsWith"] = "Targetable"
    hit.update({"HitShield": "&~/BURST", "HitOperational": "&~/BURST", "HitStructural": "&~/BURST",
                "HitFriendly": {"MediaEffects": _missile_media(s, "burst_pop", shake=False)}})
    stats = {"STAT_DAMAGE": s["stat_damage"], "STAT_RADIUS": s["stat_radius"], "STAT_CHILDREN": int(child["n"]),
             "STAT_CHILD_DAMAGE": _num(child["damage_eff"]), "STAT_CHILD_HP": int(child["hp_eff"]),
             "STAT_BURST_RANGE": car["proximity_range"]}
    return {"stats": stats, "root": root, "death": death, "hit": hit}


def _poraque_numbers(s):
    """Numeros do Poraque 2.0 (launchers[].modes[emp].damage + poraque_2): dreno, Damage, raio, fatias, estrutural,
    impulso, montaria (disruptor_drain) e a sobrecarga do escudo."""
    d = s["damage"]
    hs, op = d["HitShield"], d["HitOperational"]
    rm = _RIDER_RE.search(str(op.get("rider") or ""))
    if not rm:
        raise ValueError(f"missile_shots: {s['file']}: montaria do Poraque ilegivel ({op.get('rider')!r})")
    ov = {}
    for k, val in re.findall(r"(Radius|StatusDuration|StatusValue|MaxStatusValue|UseMaxValuesForHitShield)\s+"
                             r"(true|false|[\d.]+)", str(hs.get("shield_overload") or "")):
        ov[k] = (val == "true") if val in ("true", "false") else _num(val)
    if len(ov) != 5:
        raise ValueError(f"missile_shots: {s['file']}: shield_overload ilegivel ({hs.get('shield_overload')!r})")
    return {"drain": int(hs["ResourceDrain_battery_TreatShieldAsPart"]), "shield_damage": int(hs["Damage"]),
            "hull_drain": int(op["ExplosiveResourceDrain_battery"]), "radius": op["Radius"], "slices": int(op["Slices"]),
            "damage": int(op["Damage"]), "struct": int(op["structural_ExplosiveDamage"]),
            "struct_radius": op["structural_Radius"], "impulse": _num(op["Impulse"]),
            "rider": (rm.group(1), _num(rm.group(2)), _num(rm.group(3))), "overload": ov}


def _drain_media(s):
    return [f"&<{p}>" for p in EMP_DRAIN_MEDIA] + [_audio("emp", "drain", 1, s.get("max_conc", 16), 0.2)]


def _payload_emp(s):
    """Poraque 2.0: HitShield = dreno de UMA peca (ResourceDrain TreatShieldAsPart: o overclock do escudo nao corta)
    + Damage (+ shield_overload so com missiles.poraque_overload); casco = pulso em area ExplosiveResourceDrain
    (Slices 16, sem Friendlies; missile_emp.rules l.145-199) + Damage + estrutural + disruptor_drain + Impulse."""
    v = s.get("variants", {})
    n = _poraque_numbers(s)
    pulse = {"Type": "ExplosiveResourceDrain", "ResourceType": "battery", "TotalDrain": _val(n["hull_drain"]),
             "Radius": n["radius"], "Slices": n["slices"], "Filter": {"Ships": True, "Shields": True},
             # MediaEffectsOnDrainFactor so existe no ExplosiveResourceDrain (missile_emp.rules l.163)
             "MediaEffectsOnDrainFactor": 0.0005, "MediaEffectsOnDrain": _drain_media(s)}
    if v.get("poraque_pulses") == "repeating":
        # tres choques da enguia (Type = Repeating do SW, missile_intruder.rules l.129-178): 3 x 1/3 do dreno
        part = dict(pulse, TotalDrain=_val(int(round(n["hull_drain"] / 3))))
        pulse = {"Type": "Repeating", "Count": 3, "Interval": 0.8, "InitialDelay": 0.1, "RequireHitPart": True,
                 "HitEffects": [part]}
    tail = [{"Type": "Damage", "Damage": _val(n["damage"])},
            {"Type": "ExplosiveDamage", "TotalDamage": _val(n["struct"]), "Radius": n["struct_radius"],
             "Filter": {"OperationalHealth": False, "StructuralHealth": True}}]
    if v.get("emp_rider", "on") == "on":
        st, dur, val = n["rider"]
        tail.append({"Type": "StatusApplication", "StatusType": st, "StatusDuration": dur, "StatusValue": _val(val)})
    tail.append({"Type": "Impulse", "Impulse": _val(n["impulse"])})
    hit_op = {"HitEffects": [pulse] + tail, "MediaEffects": _missile_media(s, "emp")}
    hit_shield = None
    if v.get("emp_shield_drain", "single_part") == "single_part":
        fx = [{"Type": "ResourceDrain", "ResourceType": "battery", "Amount": _val(n["drain"]), "TreatShieldAsPart": True,
               "MediaEffectsOnDrain": _drain_media(s)},
              {"Type": "Damage", "Damage": _val(n["shield_damage"])}]
        if bool(v.get("poraque_overload")):
            ov = n["overload"]
            fx.append({"Type": "AreaShieldStatusApplication", "StatusType": "cosmoteer.shield_overload",
                       "Radius": ov["Radius"], "StatusDuration": ov["StatusDuration"], "StatusValue": ov["StatusValue"],
                       "MaxStatusValue": ov["MaxStatusValue"],
                       "UseMaxValuesForHitShield": ov["UseMaxValuesForHitShield"]})
        hit_shield = {"HitEffects": fx, "MediaEffects": "&../HitOperational/MediaEffects"}
    stats = {"STAT_DAMAGE": s["stat_damage"], "STAT_RADIUS": s["stat_radius"], "STAT_DRAIN": n["drain"],
             "STAT_DRAIN_RADIUS": n["radius"]}
    return {"stats": stats, "hit": _missile_hit(s, hit_op, hit_shield, "emp")}


def _iara_expand():
    """ExpandDuration / ExpandStartRadius / ExpandLoss / ImpulsePerNDamage / NDamage da ogiva (texto do spec)."""
    txt = _spec()["iara"]["warhead_hit"]
    out = {}
    for k in ("ExpandDuration", "ExpandStartRadius", "ExpandLoss", "ImpulsePerNDamage", "NDamage"):
        m = re.search(r"\b" + k + r"\s*=\s*([\d.]+%?)", txt)     # \b: NDamage nao casa dentro de ImpulsePerNDamage
        if not m:
            raise ValueError(f"missile_shots: iara.warhead_hit sem {k}")
        val = m.group(1)
        out[k] = val if val.endswith("%") else _num(val)
    return out


def _warhead_hit(w):
    """Ogiva da Iara (missile_nuke_stage1.rules l.141-176 em literais, SEM Friendlies): explosao em expansao
    operacional + explosao so estrutural; no escudo so o bloco operacional."""
    d = w["damage"]
    ex = _iara_expand()
    exp = {k: ex[k] for k in ("ExpandDuration", "ExpandStartRadius", "ExpandLoss")}
    op = {"Type": "ExplosiveDamage", "TotalDamage": _val(int(d["op"])), "Radius": d["op_radius"], **exp,
          "ImpulsePerNDamage": ex["ImpulsePerNDamage"], "NDamage": ex["NDamage"],
          "Filter": {"OperationalHealth": True, "StructuralHealth": False}}
    st = {"Type": "ExplosiveDamage", "TotalDamage": _val(int(d["struct"])), "Radius": d["struct_radius"], **exp,
          "Filter": {"OperationalHealth": False, "StructuralHealth": True}}
    hit_op = {"HitEffects": [op, st], "MediaEffects": _missile_media(w, "nuclear")}
    hit_shield = {"HitEffects": [dict(op)], "MediaEffects": "&../HitOperational/MediaEffects"}
    return _missile_hit(w, hit_op, hit_shield, "nuclear_fizzle")


def _payload_nuclear(s):
    """Iara: estagio de lancamento (1,5 s) -> UMA ogiva por SpawnBullets (missile_nuke_stage1.rules l.31-50; nada
    alem da ogiva). Impacto antes da separacao ja detona (Hit = o da ogiva)."""
    wh = _child_of(s, "warhead")
    deploy = {"Type": "DeathByLifetime", "Lifetime": s["deploy_lifetime"], "FactorEffectsWith": "Targetable",
              "OnDeath": {"HitEffects": [{"Type": "SpawnBullets", "Bullet": "&~/WARHEAD", "Count": 1,
                                          "InheritVelocity": True, "HealthFactor": _val(1)}]}}
    d = wh["damage"]
    stats = {"STAT_DAMAGE": int(d["op"] + d["struct"]), "STAT_RADIUS": d["op_radius"],
             "STAT_STRUCT_RADIUS": d["struct_radius"]}
    return {"stats": stats, "root": {"WARHEAD": f"&<{wh['file']}.rules>"}, "death": {"Deploy": deploy},
            "hit": f"&<{wh['file']}.rules>/Components/Hit"}


PAYLOADS = {"he": _payload_he, "cluster": _payload_cluster, "emp": _payload_emp, "nuclear": _payload_nuclear}


# ============================================================================= arquivos
def build_missile(s):
    """Missil que o lancador dispara: nucleo de conves + carga (s['payload'])."""
    pl = PAYLOADS[s["payload"]](s)
    top = dict(pl["stats"])
    top.update({"ID": Q(s["id"]), "Range": s["range"], "IdealRange": s["range"], "Speed": s["speed"]})
    top.update(pl.get("root", {}))
    comps = {
        "Physics": {"Type": "BoxPhysics", "Size": list(s["box"]), "Density": 0.1},
        "Homing": _homing(s, s["turn"], s["homing_delay"]),
        "Retarget": {"Type": "SameShipRetarget"},
        "Acceleration": {"Type": "Acceleration", "Acceleration": s["accel"]},
        "NegativeAcceleration": {"Type": "Acceleration", "Acceleration": [-90, 0], "AccelerationOverTime": [0, 0.75],
                                 "Direction": "FrameOfReferenceVelocity"},
    }
    comps.update(pl.get("death") or {"DeathByLifetime": {"Type": "DeathByLifetime", "Lifetime": s["lifetime"]}})
    comps.update(_missile_visuals(s))
    comps["Targetable"] = _targetable(s["hp"])
    comps["Hit"] = pl["hit"]
    top["Components"] = comps
    C.call(_mfx(), "decorate", s, top)
    return top


def build_cluster_child(c):
    """Minimissil da Piranha: homing depois de 0,12 s (o RandomizeTarget do portador espalha os alvos), sem luz
    IsLight, sem particulas em voo (so o feixe do propulsor do missile_fx). off_fan: Delay 0,35 + ima 1.x."""
    v = c.get("variants", {})
    off = v.get("cluster_randomize_target", "on") == "off_fan"
    top = {"STAT_DAMAGE": _num(c["damage_eff"]), "STAT_RADIUS": c["radius"], "ID": Q(c["id"]), "Range": c["range"],
           "IdealRange": c["range"], "Speed": c["speed"]}
    comps = {"Physics": {"Type": "BoxPhysics", "Size": list(c["box"]), "Density": 0.1},
             "Homing": _homing(c, c["turn"], 0.35 if off else c["homing_delay"]),
             "Retarget": {"Type": "SameShipRetarget"},
             "Acceleration": {"Type": "Acceleration", "Acceleration": c["accel"]}}
    if off:
        comps["Magnet"] = _proximity_accel(30, 25, True, False, False, True)
    comps["DeathByLifetime"] = {"Type": "DeathByLifetime", "Lifetime": c["lifetime"]}
    comps.update(_missile_visuals(c, glow=False, plume=False))
    comps["Targetable"] = _targetable(c["hp_eff"])
    fx = [{"Type": "ExplosiveDamage", "TotalDamage": _val(_num(c["damage_eff"])), "Radius": c["radius"]},
          {"Type": "Impulse", "Impulse": _val(_num(c["impulse"]))}]
    comps["Hit"] = _missile_hit(c, {"HitEffects": fx, "MediaEffects": _missile_media(c, "child")}, None, "child_pop")
    top["Components"] = comps
    return top


def build_warhead(w):
    """Ogiva da Iara (2o estagio): Speed 0 + InheritVelocity (herda o estagio), homing 90 graus/s."""
    d = w["damage"]
    top = {"STAT_DAMAGE": int(d["op"] + d["struct"]), "STAT_RADIUS": d["op_radius"], "ID": Q(w["id"]),
           "Range": w["range"], "IdealRange": w["range"], "Speed": 0}
    comps = {
        "Physics": {"Type": "BoxPhysics", "Size": list(w["box"]), "Density": 0.1},
        "Homing": _homing(w, w["turn"], None),
        "Retarget": {"Type": "SameShipRetarget"},
        "Acceleration": {"Type": "Acceleration", "Acceleration": w["accel"]},
        "DeathByLifetime": {"Type": "DeathByLifetime", "Lifetime": w["lifetime"]},
    }
    comps.update(_missile_visuals(w))
    comps["Targetable"] = _targetable(w["hp"])
    comps["Hit"] = _warhead_hit(w)
    top["Components"] = comps
    return top


def build_petal(p):
    """Tiro-petala (missiles.cluster_petals = bullets): so visual. Sprite recortado do atlas bs_petals_<m|l> com Spin
    (missile_fx.petal_sprite); sem a arte, o atlas vanilla debris.png (1a fileira, 8 quadros/s). CirclePhysics com
    RandomExtraSpeed e vida [min, max] como o mine_shrapnel.rules vanilla; sem Targetable; SimpleHit sem efeitos."""
    top = {"ID": Q(p["id"]), "Range": 30, "IdealRange": 30, "Speed": PETAL_SPEED}
    comps = {"Physics": {"Type": "CirclePhysics", "Radius": 0.1, "Density": 0.1, "RandomExtraSpeed": [-7, 8]},
             "DeathByLifetime": {"Type": "DeathByLifetime", "Lifetime": list(PETAL_LIFE)}}
    spr = C.call(_mfx(), "petal_sprite", p)
    if spr is None:
        # reserva sem a arte das petalas: debris.png vanilla (AnimatedSprite + AtlasSprite como o bullet_large.rules)
        size = 0.6 if p["tier"] == "late" else 0.5
        spr = {"Sprite": {"Type": "AnimatedSprite", "RenderBucket": "BulletUpper3",
                          "Animation": {"AtlasSprite": {"Texture": {"File": Q(DEBRIS), "MipLevels": "max",
                                                                    "SampleMode": "Linear"},
                                                        "Size": [size, size]},
                                        "FrameCount": 4, "FrameSize": [64, 64], "FramesPerRow": 4,
                                        "FramesPerSecond": 8}}}
    comps.update(spr)
    hit = _deck_flags(p)
    hit.update({"HitShield": "&HitOperational", "HitOperational": {}, "HitStructural": "&HitOperational"})
    comps["Hit"] = hit
    top["Components"] = comps
    return top


CHILD_BUILDERS = {"child": build_cluster_child, "warhead": build_warhead}


def build_shot(out, s, header):
    """Gancho do registro (kind 'missile'): arquivo principal + filhos + petalas na pasta do tiro."""
    if s.get("kind") != "missile":
        return None
    _prepare(s)
    mfx = _mfx()
    d = f"shots/{s['dir']}"
    rel = f"{d}/{s['file']}.rules"
    out.text(rel, render(build_missile(s), header + f"\nProjetil: {s['title']}"))
    for c in s.get("children", []):
        top = CHILD_BUILDERS[c["role"]](c)
        C.call(mfx, "decorate", c, top)
        out.text(f"{d}/{c['file']}.rules", render(top, header + f"\nProjetil filho: {c['title']}"))
    for p in s.get("petal_shots", []):
        out.text(f"{d}/{p['file']}.rules", render(build_petal(p), header + f"\nPetala (so visual): {p['title']}"))
    return rel


# ============================================================================= conferencia do mod gerado
def _read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def _block(text, name):
    """Texto do primeiro grupo 'name { ... }' (com chaves balanceadas) ou None."""
    m = re.search(r"(?m)^\s*" + re.escape(name) + r"\s*(?::[^\n{]*)?\n\s*\{", text)
    if not m:
        return None
    i = text.index("{", m.start())
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def _field(block, name):
    m = re.search(r"(?m)^\s*" + re.escape(name) + r"\s*=\s*(.+?)\s*$", block or "")
    return m.group(1) if m else None


def _base_value(block, name):
    """Valor de 'name = N' ou de 'name { BaseValue = N ... }'."""
    v = _field(block, name)
    if v is not None:
        return v
    b = _block(block or "", name)
    return _field(b, "BaseValue") if b else None


def _effects(block, kind):
    """Blocos { Type = kind ... } dentro de block (qualquer profundidade)."""
    res = []
    for m in re.finditer(r"(?m)^(\t*)Type = " + re.escape(kind) + r"\s*$", block or ""):
        # sobe ate o '{' que abre este elemento
        i = block.rfind("{", 0, m.start())
        depth = 0
        for j in range(i, len(block)):
            if block[j] == "{":
                depth += 1
            elif block[j] == "}":
                depth -= 1
                if depth == 0:
                    res.append(block[i:j + 1])
                    break
    return res


def _media_refs(block):
    lst = re.search(r"MediaEffects\s*\n\s*\[(.*?)\n\t*\]", block or "", re.S)
    return re.findall(r"&<([^>]+)>", lst.group(1)) if lst else []


def particles_of(ref, file_dir):
    """Particulas por disparo de uma referencia de midia: vanilla pela tabela VANILLA_PARTICLES; arquivo do mod pelo
    EmitPerOneShot (Max) do EmitterDef; Beam = 0. None = desconhecida."""
    if ref.startswith("./Data/"):
        return VANILLA_PARTICLES.get(ref)
    p = os.path.normpath(os.path.join(file_dir, ref))
    if not os.path.isfile(p):
        return None
    t = _read(p)
    if re.search(r"(?m)^Type = Beam\s*$", t):
        return 0
    em = t.find("EmitterDef")
    if em < 0:
        return None
    seg = t[em:]
    m = re.search(r"EmitPerOneShot\s*=\s*(\d+)", seg)
    if m:
        return int(m.group(1))
    b = _block(seg, "EmitPerOneShot")
    mx = _field(b, "Max") if b else None
    return int(float(mx)) if mx is not None else None


def _count_media(block, file_dir, probs, who):
    n = 0
    for ref in _media_refs(block):
        k = particles_of(ref, file_dir)
        if k is None:
            probs.append(f"{who}: contagem de particulas desconhecida para {ref}")
            continue
        n += k
    return n


def selfcheck(mod_dir, spec):
    """Conferencias dos tiros de missil gerados (lista vazia = OK): filhos 12/20 (6/10 lite) com o HP do spec,
    RandomizeTarget so com o switch, proximidade 300/400 m, drenos do Poraque (ResourceDrain sem
    MediaEffectsOnDrainFactor; AreaShieldStatusApplication so com missiles.poraque_overload), Iara com UM SpawnBullets
    e o HP do switch, nucleo de conves em todo Hit, nenhum arquivo dos tipos que sairam, orcamento de particulas
    (BURST <= 40, impacto do minimissil <= 8, salva da Mula <= 960)."""
    import bs_data as D
    probs = []
    shots_dir = os.path.join(mod_dir, "shots")
    gone = set(D.SPEC["removed_ids"].get("missile_shots") or [])
    bad_name = re.compile(r"napalm|limpet|torpedo|decoy")
    if os.path.isdir(shots_dir):
        for dp, dn, fn in os.walk(shots_dir):
            for f in fn + dn:
                if bad_name.search(f):
                    probs.append(f"arquivo de tipo que saiu na 2.0: {os.path.relpath(os.path.join(dp, f), mod_dir)}")
    v = (D.MISSILES[0]["variants"] if D.MISSILES else {}) or {}
    iara_hp = int(D.switch("missiles.iara_hp"))
    for s in D.MISSILES:
        d = os.path.join(shots_dir, s["dir"])
        p = os.path.join(d, f"{s['file']}.rules")
        who = s["file"]
        if not os.path.isfile(p):
            probs.append(f"{who}: arquivo nao escrito")
            continue
        text = _read(p)
        if s["id"] in gone:
            probs.append(f"{who}: ID removido na 2.0")
        files = [(s, text)]
        for c in s.get("children", []):
            cp = os.path.join(d, f"{c['file']}.rules")
            if not os.path.isfile(cp):
                probs.append(f"{who}: filho {c['file']} nao escrito")
                continue
            files.append((c, _read(cp)))
        for u, t in files:
            hit = _block(t, "Hit")
            if isinstance(hit, str) and ("FriendlyShipLowCollisions = false" not in hit
                                         or "FriendlyShipHighCollisions = false" not in hit):
                probs.append(f"{u['file']}: Hit sem o nucleo de conves (FriendlyShipLow/HighCollisions = false)")
            if "Friendlies = true" in t:
                probs.append(f"{u['file']}: efeito com Friendlies = true (missil do mod nunca fere a propria nave)")
            for rd in _effects(t, "ResourceDrain"):
                if "MediaEffectsOnDrainFactor" in rd:
                    probs.append(f"{u['file']}: MediaEffectsOnDrainFactor num ResourceDrain (so existe no "
                                 f"ExplosiveResourceDrain)")
        t = s["payload"]
        if t == "cluster":
            probs += _check_cluster(s, text, files, d, v)
        elif t == "emp":
            probs += _check_emp(s, text, v)
        elif t == "nuclear":
            n_spawn = len(_effects(text, "SpawnBullets"))
            if n_spawn != 1:
                probs.append(f"{who}: {n_spawn} SpawnBullets no estagio da Iara (so a ogiva)")
            hp = _field(_block(text, "Targetable"), "Health")
            if hp is None or int(float(hp)) != iara_hp:
                probs.append(f"{who}: HP do estagio {hp} != missiles.iara_hp {iara_hp}")
            for c, ct in files[1:]:
                if c["role"] == "warhead":
                    whp = _field(_block(ct, "Targetable"), "Health")
                    if whp is None or int(float(whp)) != iara_hp:
                        probs.append(f"{c['file']}: HP da ogiva {whp} != missiles.iara_hp {iara_hp}")
        if "AreaShieldStatusApplication" in text and t != "emp":
            probs.append(f"{who}: AreaShieldStatusApplication fora do Poraque")
    return probs


def _check_cluster(s, text, files, d, v):
    probs = []
    who = s["file"]
    child = _child_of(s, "child")
    lite = bool(v.get("cluster_lite"))
    want_n = _lite_count(child["count"]) if lite else child["count"]
    want_hp = child["hp"] * 2 if lite else child["hp"]
    burst = _block(text, "BURST")
    spawns = _effects(burst, "SpawnBullets")
    kid = [b for b in spawns if "&~/CHILD" in b]
    if len(kid) != 1:
        probs.append(f"{who}: {len(kid)} SpawnBullets de filhotes no BURST")
        return probs
    cnt = _field(kid[0], "Count")
    if cnt is None or int(cnt) != want_n or want_n not in ((6, 10) if lite else (12, 20)):
        probs.append(f"{who}: Count {cnt} (esperado {want_n}{' com cluster_lite' if lite else ''})")
    rt = "RandomizeTarget = true" in kid[0]
    if rt != (v.get("cluster_randomize_target", "on") == "on"):
        probs.append(f"{who}: RandomizeTarget {'presente' if rt else 'ausente'} com cluster_randomize_target="
                     f"{v.get('cluster_randomize_target')}")
    prox = _effects(_block(text, "Components"), "DeathByEnemyProximity")
    if v.get("cluster_open", "proximity") == "proximity":
        rng = _field(prox[0], "Range") if prox else None
        if rng is None or float(rng) != float(s["carrier"]["proximity_range"]):
            probs.append(f"{who}: espoleta de proximidade {rng} != {s['carrier']['proximity_range']} m")
    elif prox:
        probs.append(f"{who}: cluster_open=timer com DeathByEnemyProximity")
    petals = [b for b in spawns if "&~/PETAL_" in b]
    if (v.get("cluster_petals") == "bullets") != bool(petals):
        probs.append(f"{who}: tiros-petala {'presentes' if petals else 'ausentes'} com cluster_petals="
                     f"{v.get('cluster_petals')}")
    for c, ct in files[1:]:
        if c["role"] != "child":
            continue
        hp = _field(_block(ct, "Targetable"), "Health")
        if hp is None or int(float(hp)) != want_hp:
            probs.append(f"{c['file']}: HP do filhote {hp} != {want_hp}")
        if "IsLight = true" in ct:
            probs.append(f"{c['file']}: minimissil com luz IsLight (160 luzes lavam o casco branco)")
        n_child = _count_media(_block(ct, "HitOperational"), d, probs, c["file"])
        if n_child > CHILD_PARTICLE_CAP:
            probs.append(f"{c['file']}: impacto com {n_child} particulas (> {CHILD_PARTICLE_CAP})")
        n_burst = _count_media(burst, d, probs, f"{who}/BURST")
        if n_burst > BURST_PARTICLE_CAP:
            probs.append(f"{who}: BURST com {n_burst} particulas (> {BURST_PARTICLE_CAP})")
        total = s["per_salvo"] * (want_n * n_child * OVERLAP + n_burst)
        s["_salvo_particles"] = total
        if total > SALVO_PARTICLE_CAP:
            probs.append(f"{who}: salva de {s['per_salvo']} portadores ~{total:.0f} particulas (> {SALVO_PARTICLE_CAP})")
    for p in s.get("petal_shots", []):
        if not os.path.isfile(os.path.join(d, f"{p['file']}.rules")):
            probs.append(f"{who}: petala {p['file']} nao escrita")
    return probs


def _check_emp(s, text, v):
    probs = []
    who = s["file"]
    n = _poraque_numbers(s)
    hit = _block(text, "Hit")
    op = _block(hit, "HitOperational")
    ed = _effects(op, "ExplosiveResourceDrain")
    want_tot = n["hull_drain"] if v.get("poraque_pulses") != "repeating" else int(round(n["hull_drain"] / 3))
    if not ed or int(float(_base_value(ed[0], "TotalDrain") or 0)) != want_tot:
        probs.append(f"{who}: pulso do casco {ed and _base_value(ed[0], 'TotalDrain')} != {want_tot}")
    elif _field(ed[0], "Slices") != str(n["slices"]):
        probs.append(f"{who}: Slices {_field(ed[0], 'Slices')} != {n['slices']}")
    sh = _block(hit, "HitShield")
    single = v.get("emp_shield_drain", "single_part") == "single_part"
    if single:
        rd = _effects(sh, "ResourceDrain")
        if not rd or int(float(_base_value(rd[0], "Amount") or 0)) != n["drain"] or "TreatShieldAsPart = true" not in rd[0]:
            probs.append(f"{who}: HitShield sem ResourceDrain {n['drain']} TreatShieldAsPart")
        asa = "AreaShieldStatusApplication" in (sh or "")
        if asa != bool(v.get("poraque_overload")):
            probs.append(f"{who}: AreaShieldStatusApplication {'presente' if asa else 'ausente'} com "
                         f"missiles.poraque_overload={v.get('poraque_overload')}")
    elif sh is not None:
        probs.append(f"{who}: emp_shield_drain=area com HitShield proprio")
    return probs
