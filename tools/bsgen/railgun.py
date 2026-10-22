"""Railgun Tupa 2.0 (dono: WP09): FIXA e modular como a railgun vanilla - Carregador 5x5 + 1..6 Canos 3x3 + Ponta 3x4.

Modulo de CONTEUDO do registro do tools/build_mod.py (API = 2; nunca desligado pelo BS_FX_EXT). Ganchos: shots(DATA)
(o tiro rafaeltessaro.bs_slug_rail_shot, kind 'slug_rail'), build_shot(out, s, header), write(out, header) (buffs
proprios em buffs/bs_rail_buffs.rules), parts(out, DATA, ctx), strings(DATA), mod_actions() (Overrides dos buffs) e
selfcheck(mod_dir, SPEC). Nada e escrito com rail.enabled = false (o bs_data ja tira recurso, F6, paiois de
projeteis, limite e techs).

Fontes (ordem de leitura do ADDENDUM G0): USER_NOTES (Tupa FIXA, tranco, carregador 5x5, azul, passa sobre a propria
nave), ADDENDUM_2_0 work_packages.WP09 (o que mudou no plano), plan_final WP09, SPEC.railgun (tools/spec/SPEC_2.0.json)
e os metas art3d/bs_rail_*/meta.json (VENCEM numeros de arte do spec). Molde testado: kit testes/BulletStrike_Teste2
(TK parts/bs2t_rail_*, shots/bs2t_slug, buffs/bs2t_buffs.rules); vanilla 0.30.3 railgun_loader / accelerator /
launcher (V303) e shots/bullet_railgun.

Corrente (como a vanilla, com buffs/categorias/portas PROPRIOS: nenhuma peca vanilla ou do SW conversa com a Tupa):
  * BulletStrike_Rail: contador (carregador da 0, cada cano 1 + o que recebeu; a ponta recebe N);
  * BulletStrike_RailShot: m(N) = 1 + 25 % x N^0,85 (SelfBuffProvider da ponta; o tiro herda); MaxValue 2,1466;
  * BulletStrike_RailOperation (para a frente) e BulletStrike_RailReverseOperation (para tras): uma peca quebrada
    para a arma inteira;
  * BulletStrike_RailCount (so rail.power_mode = B): contagem de tras para frente, o carregador recebe N e cobra
    500 x N da propria bateria (DrenoB, ScaledBuff como o Overclock_ShotHeatProducer vanilla).
  O cano olha para TRAS com DUAS entradas (o cano de tras {Category bs_rail_municao; Left 0; Right 3; Top 3} OU o
  carregador 5x5 centrado {IDs [bs_rail_loader]; Left -1; Right 4; Top 3}; formas de lista do SW chaingun_magazine):
  sem a 2a o carregador nunca recebe RailReverseOperation (fica desligado) nem RailCount (tiro de graca).

Disparo (linha do tempo do spec): gatilho -> carga 1,0 s + 0,25 s por cano (onda de brilho, rail.charge_wave) ->
o dardo corre pelo cano (RailgunProjectile, so grafico, Interpolate = true) -> BulletEmitter no fim da corrida ->
TRANCO: UM Impulse por tiro na ponta (TriggeredEffects TrancoImpulso, Trigger = BulletEmitter, nunca ChainedTo o
Projectile), tremor BASE_SHAKE 0,2 / 0,7 s, anel de choque azul que fica no espaco e os quadros de recuo da coroa,
dos tambores (ponta e cada cano) e da culatra (Graphics com ResetAnimationTrigger + ClampAnimation +
AnimationStartTime MinValue, ultimo quadro = repouso).

Gatilho do recuo nas pecas de tras (rail.tranco_gatilho):
  relay (padrao): TrancoRelay = MultiTrigger { Triggers = [<TriggerProxy do EmissionTriggered da ponta>] } - um
         repetidor LOCAL de PULSO UNICO (o MultiTrigger dispara uma vez a cada disparo da sua entrada; vanilla
         ProjectileStartTrigger / EmissionTriggered / ReiniciaCarga sao MultiTrigger sobre TriggerProxy). O Timer
         {Duration 0,5; TriggerWhenStarted true} do spec_patch disparava DUAS vezes (inicio e expiracao = segundo
         coice 0,5 s depois do tiro) e NAO e usado; o selfcheck prova pelo arquivo gerado que nenhum Timer chega
         num ResetAnimationTrigger e que o TrancoRelay tem uma entrada so;
  proxy: ResetAnimationTrigger = o TriggerProxy direto (EmitTrigger / EmissionTriggered), sem repetidor.
  Na ponta o gatilho e sempre o BulletEmitter (dela mesma).

Switches (SPEC.switches.rail; os valores adiados pelo bs_data caem no 'safe' com aviso):
  enabled, power_mode B | fixo (A adiado -> B), charge_wave atraso | off (rede adiado -> atraso), buffed_riders,
  overload_rider, r2_fallback, loader_intake auto | acoplamento | tripulacao, tranco_impulso impulso | recoil | off,
  tranco_gatilho relay | proxy, recoil_com, per_ship_limit (no bs_data: LIMIT_DEFS), codex (nao implementado: aviso).
"""

import math
import os
import re

from rules_dsl import Q, Inh, comment, render
from bsgen import common as C
from bsgen import layered as L
from bsgen import fxkit as FXK
import art3d as A3

API = 2
SHOT_KINDS = ("slug_rail",)

AUTHOR = C.AUTHOR
LOADER = f"{AUTHOR}.bs_rail_loader"
BARREL = f"{AUTHOR}.bs_rail_barrel"
MUZZLE = f"{AUTHOR}.bs_rail_muzzle"
SHORT = {LOADER: "bs_rail_loader", BARREL: "bs_rail_barrel", MUZZLE: "bs_rail_muzzle"}
KEY = {LOADER: "BSRailLoader", BARREL: "BSRailBarrel", MUZZLE: "BSRailMuzzle"}
RES_SLUG = f"{AUTHOR}.bs_slug_rail"
SHOT_FILE = "bs_slug_rail_shot"
SHOT_ID = f"{AUTHOR}.bs_slug_rail_shot"
BUFFS_FILE = "buffs/bs_rail_buffs.rules"

B_RAIL = "BulletStrike_Rail"
B_SHOT = "BulletStrike_RailShot"
B_OP = "BulletStrike_RailOperation"
B_REV = "BulletStrike_RailReverseOperation"
B_COUNT = "BulletStrike_RailCount"
CAT_RAIL = "bs_rail"
CAT_MUN = "bs_rail_municao"
CAT_ENE = "bs_rail_energia"

MAX_CANOS = 6
SHOT_EXPONENT = 0.85          # BulletStrike_RailShot (SPEC.railgun.buffs): m(N) = 1 + 25 % x N^0,85
SHOT_MULT = 0.25
SHOT_MAX = 2.1466             # trava em 6 canos (a ponta tambem recusa mais de 6)
FIRE_INTERVAL = 6.0           # s (SPEC.railgun.parts.ponta.weapon.FireInterval; balanco A_keep)
CARGA_BASE = 1.0              # s (vanilla overclock 0,5)
CARGA_POR_CANO = 0.25         # s (vanilla overclock 0,125)
POWER_BASE = 2000             # energia da ponta por tiro (BatteryProxy) - Int
POWER_PER_CANO = 500          # variante B: o carregador cobra 500 x N (DrenoB) - Int
POWER_FIXO = 4000             # variante 'fixo': custo de N=4 para todo N - Int
SLUG_PER_SHOT = 1             # Int
COMPRIMENTO_CANO = 3          # passo do YStartOffset (quadros por cano)
VEL_INICIO_ANIM = 6           # quadros/s do dardo DENTRO do cano (so grafico)
VEL_FIM_ANIM = 50
TRANCO_IMPULSE = 2400         # x m(N) = 3000..5152 (SPEC.railgun.tranco.impulse)
TRANCO_RECOIL = 4000          # rail.tranco_impulso = recoil (numero fixo do BulletEmitter)
SHAKE = (0.2, 0.7)            # BASE_SHAKE do disparo (fixo: buff em media de peca nao verificado)
IMPACT_SHAKE = (0.15, 0.9)    # BASE_SHAKE do fim do caminho x RailShot (no tiro: buff provado no vanilla)
WAVE_STEP = 0.3               # charge_wave atraso: o cano de indice i acende 0,3 s x i depois do gatilho
WAVE_FRAME = 0.03             # s por quadro da subida da carga (trilhos / carga)
R2_PER_PART = 6700            # rail.r2_fallback: dano por peca = pool / 6 (x m(N))
LIGHT_BLOB = (0.10, 0.32, 1.0)   # VertexColor do light_blob do dardo no cano (x 12 como o vanilla; nao lava o casco)

# arestas exatas (SPEC.railgun.chain_offsets_5x5): o cano encaixa nos quadros x 1..3 da borda de cima do carregador
CRIT_FRENTE = {"Category": CAT_ENE, "Rot": 0, "Left": 0, "Right": 3, "Bottom": 0}         # cano/ponta na frente
CRIT_CANO_TRAS = {"Category": CAT_MUN, "Rot": 0, "Left": 0, "Right": 3, "Top": 3}         # cano atras (do cano)
CRIT_CARREGADOR_TRAS = {"IDs": [LOADER], "Rot": 0, "Left": -1, "Right": 4, "Top": 3}       # carregador 5x5 atras
CRIT_CARREGADOR_FRENTE = {"Category": CAT_ENE, "Rot": 0, "Left": 1, "Right": 4, "Bottom": 0}   # do carregador
CRIT_PONTA_TRAS = {"Category": CAT_MUN, "Rot": 0, "Left": 0, "Right": 3, "Top": 4}        # da ponta (so num cano)

# carregador 5x5 (ADDENDUM WP09 'fazer'; SPEC.railgun.parts.carregador.doors)
LOADER_DOORS = [[-1, 1], [5, 1], [1, 5], [3, 5]]
LOADER_BLOCKED = [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [2, 1], [2, 2], [2, 3], [2, 4], [0, 2], [0, 3], [0, 4],
                  [4, 2], [4, 3], [4, 4]]
ACOPLA_CELL = [0, 5]          # paiol de projeteis encostado atras do canto de tras-esquerdo (logistics.celula_acoplada)

_WARNED = set()


# ============================================================================= dados e switches
def _D():
    import bs_data as D
    return D


def _warn(msg):
    if msg not in _WARNED:
        _WARNED.add(msg)
        _D().warn(msg)


def sw(name):
    """Valor efetivo de rail.<name> (bs_data.switch: CLI > env > bullet_strike_switches.json > padrao; variante
    adiada -> safe com aviso)."""
    return _D().switch(f"rail.{name}")


def power_mode():
    v = sw("power_mode")
    return "B" if v == "A" else v      # 'A' nunca chega aqui (adiado no bs_data); por garantia, B


def charge_wave():
    v = sw("charge_wave")
    return "atraso" if v == "rede" else v


def tranco_gatilho():
    return sw("tranco_gatilho")


def tranco_impulso():
    return sw("tranco_impulso")


def loader_intake():
    return sw("loader_intake")


def spec():
    return _D().RAIL


def m_of(n):
    """m(N) = 1 + 0,25 N^0,85 (preso em SHOT_MAX), o mesmo do BulletStrike_RailShot."""
    return min(SHOT_MAX, 1 + SHOT_MULT * float(n) ** SHOT_EXPONENT) if n > 0 else 1.0


def charge_s(n):
    return CARGA_BASE + CARGA_POR_CANO * n


def power_per_shot(n):
    return POWER_FIXO if power_mode() == "fixo" else POWER_BASE + POWER_PER_CANO * n


def impulse_per_shot(n):
    t = tranco_impulso()
    if t == "impulso":
        return int(round(TRANCO_IMPULSE * m_of(n)))
    if t == "recoil":
        return TRANCO_RECOIL
    return 0


def _he(effects, typ, nth=0):
    """n-esimo efeito de tipo typ numa lista HitEffects do spec."""
    hits = [e for e in effects or [] if isinstance(e, dict) and e.get("Type") == typ]
    return hits[nth] if len(hits) > nth else {}


def _bv(x, default):
    if isinstance(x, dict):
        return x.get("BaseValue", default)
    return default if x is None else x


def shot_numbers():
    """Numeros do tiro (SPEC.railgun.shot; o que o spec escreve em texto fica nas constantes deste modulo)."""
    s = spec()["shot"]
    h = s["Hit"]
    hs = h["HitShield"]["HitEffects"]
    po = h["PenetratingOperational"]["HitEffects"]
    hst = h["HitStructural"]["HitEffects"]
    imp = s["IMPACT"]
    ov = _he(hs, "AreaShieldStatusApplication")
    return {
        "range": _bv(s["Range"], 400), "range_max": s["Range"].get("MaxValue", 700),
        "ideal": [(_bv(x, 0), x.get("MaxValue")) for x in s["IdealRange"]],
        "speed": _bv(s["Speed"], 440), "speed_max": s["Speed"].get("MaxValue", 1200),
        "hp": int(s["Targetable"]["Health"]), "pool": int(_bv(s["DamagePool"], 40000)),
        "pen": _bv(h["Penetration"], 26),
        "shield_dmg": _bv(_he(hs, "Damage").get("Damage"), 16500),
        "shield_drain": _bv(_he(hs, "ResourceDrain").get("Amount"), 2400),
        "overload": {"Radius": ov.get("Radius", 6), "StatusDuration": ov.get("StatusDuration", 3),
                     "StatusValue": ov.get("StatusValue", 0.25), "MaxStatusValue": ov.get("MaxStatusValue", 0.5)},
        "impulse": _bv(_he(hs, "Impulse").get("Impulse"), 140),
        "struct_dmg": _bv(_he(hst, "Damage").get("Damage"), 2400),
        "struct_imp": _bv(_he(hst, "Impulse").get("Impulse"), 34),
        "part_dmg": _bv(_he(po, "Damage").get("Damage"), 2000),
        "part_drain": _bv(_he(po, "ExplosiveResourceDrain").get("TotalDrain"), 3000),
        "part_drain_r": _he(po, "ExplosiveResourceDrain").get("Radius", 3),
        "disruptor_s": _he(po, "StatusApplication", 0).get("StatusDuration", 4),
        "disruptor_v": _bv(_he(po, "StatusApplication", 0).get("StatusValue"), 0.5),
        "fire_chance": _bv(_he(po, "StatusApplication", 1).get("StatusChance"), 0.35),
        "emp_end": _bv(imp["EmpBurst"]["TotalDrain"], 8000), "emp_end_r": imp["EmpBurst"].get("Radius", 5),
        "emp_end_slices": imp["EmpBurst"].get("Slices", 8),
        "heat_pool": _bv(imp["HeatPool"]["StatusValuePool"], 4000),
        "fire_splash": imp["FireSplash"],
        "radius": 0.35, "turn": "3d",
    }


# ============================================================================= modulos opcionais
def _opt(name):
    """Modulo de efeitos (FX) so com API >= 2 e BS_FX_EXT != 0 (registro do build_mod)."""
    if os.environ.get("BS_FX_EXT", "1") == "0":
        return None
    return C.content_module(name, min_api=2)


def _rfx():
    return _opt("bsgen.rail_fx")


def _cfx():
    return _opt("bsgen.caliber_fx")


def _intake():
    return C.content_module("bsgen.intake")


def _tex():
    return C.content_module("bsgen.fx_tex")


def _rmedia(group, frm, fallback):
    """MediaEffects do rail_fx (azul) ou, sem ele (BS_FX_EXT=0), os efeitos vanilla do railgun (ciano)."""
    R = _rfx()
    if R is not None:
        return list(R.media(group, frm))
    return [f"&<{p}>" for p in fallback]


V = "./Data"
VAN_RAIL_SHOOT = f"{V}/ships/terran/railgun_launcher/particles/railgun_shoot.rules"
VAN_RAIL_DIST = f"{V}/ships/terran/railgun_launcher/particles/railgun_shoot_distortion.rules"
VAN_TRAIL = f"{V}/shots/bullet_railgun/particles/bullet_trail_railgun.rules"
VAN_TRAIL_RING = f"{V}/shots/bullet_railgun/particles/bullet_trail_railgun_ring.rules"
VAN_TRAIL_DIST = f"{V}/shots/bullet_railgun/particles/bullet_trail_railgun_ring_distortion.rules"
VAN_PEN = f"{V}/shots/bullet_railgun/particles/bullet_penetrate_railgun.rules"
VAN_HIT = [f"{V}/shots/bullet_railgun/particles/bullet_hit_railgun.rules",
           f"{V}/shots/bullet_railgun/particles/bullet_railgun_sparks.rules",
           f"{V}/shots/bullet_railgun/particles/bullet_flash_railgun.rules"]
VAN_SMOKE = f"{V}/shots/bullet_deck/particles/bullet_smoke_deck.rules"
VAN_STRUCT = [f"{V}/shots/bullet_railgun/particles/bullet_hit_struct_railgun.rules",
              f"{V}/shots/bullet_railgun/particles/bullet_hit_struct_railgun_sparks.rules"]
VAN_EMP_SHOCK = f"{V}/shots/missile_emp/particles/missile_emp_hit_shockwave.rules"
VAN_IMPACT_SOUNDS = [f"{V}/shots/bullet_railgun/sounds/railgun_impact_0{i}.wav" for i in (1, 2, 3)]
VAN_SHOT_SOUNDS = [f"{V}/ships/terran/railgun_loader/sounds/railgun_shot_0{i}.wav" for i in (1, 2, 3)]
VAN_CHARGE_LOOP = f"{V}/ships/terran/railgun_launcher/sounds/railgun_charge_up_loop.wav"
VAN_CHARGE_START = f"{V}/ships/terran/railgun_launcher/sounds/railgun_charge_up_start.wav"
VAN_RAIL_WAV = f"{V}/ships/terran/railgun_launcher/sounds/rail.wav"
VAN_SLUG_SPRITE = f"{V}/shots/bullet_railgun/bullet_railgun.png"


# ============================================================================= tiro (kind slug_rail)
def _shot(v, mx=None, ese=True):
    """{ BaseValue = v; BuffType = BulletStrike_RailShot; BuffMode = Multiply [; MaxValue] [; EffectScaleExponent] }"""
    d = {"BaseValue": v, "BuffType": B_SHOT, "BuffMode": "Multiply"}
    if mx is not None:
        d["MaxValue"] = mx
    if ese:
        d["EffectScaleExponent"] = 1
    return d


def _rider(v):
    """Drenos e poca de calor (rail.buffed_riders): com buff (precedente GA TotalDrain x RailgunShot) ou o valor de N=4
    fixo (inteiro)."""
    if sw("buffed_riders"):
        return _shot(v)
    return {"BaseValue": int(round(v * m_of(4))), "EffectScaleExponent": 1}


def _sound(files, volume, shot_buff=False):
    vol = {"BaseValue": volume, "BuffType": B_SHOT, "BuffMode": "Multiply"} if shot_buff else volume
    return Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(f) for f in files], "Volume": vol,
                                               "SpeedVariation": 0.15})


def build_slug(s=None):
    """Arquivo do tiro rafaeltessaro.bs_slug_rail_shot (SPEC.railgun.shot; estrutura do bullet_railgun 0.30.3, sem
    campos do 0.30.5; tudo x BulletStrike_RailShot)."""
    from bsgen.shots import OWN_SHIP_PASS
    n = shot_numbers()
    cfx = _cfx()
    rfx = _rfx()
    top = {}
    top["ID"] = Q(SHOT_ID)
    top["Range"] = _shot(n["range"], n["range_max"], ese=False)
    top["IdealRange"] = [_shot(v, mx, ese=False) for v, mx in n["ideal"]]
    top["IdealRadius"] = [5, 50]
    top["Speed"] = _shot(n["speed"], n["speed_max"], ese=False)
    top["ReceivableBuffs"] = [B_SHOT]
    # fim do caminho (HitOperational e, sem r2_fallback, FinishedPenetratingOperational): PEM + calor + fogo
    fs = n["fire_splash"]
    top["IMPACT"] = {
        "EmpBurst": {"Type": "ExplosiveResourceDrain", "ResourceType": "battery", "TotalDrain": _rider(n["emp_end"]),
                     "Radius": n["emp_end_r"], "Slices": int(n["emp_end_slices"]),
                     "Filter": {"Ships": True, "Shields": True}, "MediaEffectsOnDrainFactor": 0.0005,
                     "MediaEffectsOnDrain": _rmedia("emp_burst", "shot", [])},
        "HeatPool": {"Type": "GridStatusApplication", "StatusType": "cosmoteer.heat", "StatusValue": 0,
                     "StatusValuePool": _rider(n["heat_pool"]), "ValueFalloff": 1, "MaxCost": 2,
                     "FalloffPadding": 0.5, "EmptyTileCost": 1000, "AllowDiagonals": True,
                     "Filter": {"Friendlies": False, "TargetedFriendlies": True}},
        "FireSplash": {"Type": "GridStatusApplication", "StatusType": "cosmoteer.fire",
                       "StatusChance": fs.get("StatusChance", "60%"), "StatusValue": fs.get("StatusValue", 30),
                       "MaxCost": fs.get("MaxCost", 1), "MinDistance": fs.get("MinDistance", 0),
                       "MaxDistance": fs.get("MaxDistance", 1), "BlockedByWalls": bool(fs.get("BlockedByWalls", False)),
                       "Filter": {"Friendlies": False}},
    }
    if not top["IMPACT"]["EmpBurst"]["MediaEffectsOnDrain"]:
        top["IMPACT"]["EmpBurst"]["MediaEffectsOnDrain"] = [
            f"&<{V}/shots/missile_emp/particles/missile_emp_hit_sizzle.rules>",
            f"&<{V}/shots/missile_emp/particles/missile_emp_lightning.rules>"]
    comp = {}
    comp["Physics"] = {"Type": "CirclePhysics", "Radius": n["radius"], "Density": 0.0001}
    comp["Homing"] = {"Type": "TargetHoming", "TurnVelocity": n["turn"], "ModifiesLinearVelocity": True,
                      "VelocityCompensation": "100%"}
    comp["Death"] = {"Type": "DeathByLifetime"}
    # abatido no ar: um estouro azul pequeno, nunca o impacto cheio
    if rfx is not None:
        pop = list(rfx.media("intercepted", "shot"))
    else:
        pop = list(C.call(cfx, "pop_effect", "slug") or []) or [f"&<{VAN_HIT[2]}>"]
    comp["Targetable"] = {"Type": "Targetable", "Health": n["hp"], "TargetCategory": Q("bullet"),
                          "OnDeath": {"MediaEffects": pop}}
    comp["DamagePool"] = {"Type": "DamagePool", "Damage": _shot(n["pool"], ese=False)}
    # ---- acertos
    impact_media = _rmedia("impact", "shot", VAN_HIT) + [f"&<{VAN_SMOKE}>"] + [
        _sound(VAN_IMPACT_SOUNDS, 0.75, shot_buff=True),
        Inh("/BASE_SHAKE", {"ShakeAmount": {"BaseValue": IMPACT_SHAKE[0], "BuffType": B_SHOT, "BuffMode": "Multiply"},
                            "Duration": IMPACT_SHAKE[1]})]
    shield_eff = [{"Type": "Damage", "Damage": _shot(n["shield_dmg"])},
                  {"Type": "ResourceDrain", "ResourceType": "battery", "Amount": _rider(n["shield_drain"]),
                   "TreatShieldAsPart": True}]
    if sw("overload_rider"):
        o = n["overload"]
        shield_eff.append({"Type": "AreaShieldStatusApplication", "StatusType": "cosmoteer.shield_overload",
                           "Radius": o["Radius"], "StatusDuration": o["StatusDuration"],
                           "StatusValue": o["StatusValue"], "MaxStatusValue": o["MaxStatusValue"]})
    shield_eff.append({"Type": "Impulse", "Impulse": _shot(n["impulse"])})
    # HitShield sem MediaEffectsScale e com volume fixo (o bullet_railgun 0.30.3 nao escala a midia do escudo)
    shield_media = _rmedia("shield_hit", "shot", VAN_HIT[:1]) + [f"&<{VAN_EMP_SHOCK}>",
                                                                   _sound(VAN_IMPACT_SOUNDS, 0.6)]
    hit_op = {"ReduceEffectsByPenetration": True,
              "HitEffects": [{"Type": "Damage", "Damage": 0, "DamagePool": "DamagePool",
                              "DamagePoolFactor": {"BaseValue": 1, "EffectScaleExponent": 1}},
                             {"Type": "Impulse", "Impulse": _shot(n["impulse"])},
                             "&~/IMPACT/EmpBurst", "&~/IMPACT/HeatPool", "&~/IMPACT/FireSplash"],
              "MediaEffectsScale": {"BaseValue": 1, "BuffType": B_SHOT, "BuffMode": "Multiply"},
              "MediaEffects": impact_media}
    r2 = bool(sw("r2_fallback"))
    per_part = R2_PER_PART if r2 else n["part_dmg"]
    pen_media = [f"&<{VAN_PEN}>"]
    if rfx is not None:
        pen_media += list(rfx.media("puncture", "shot"))
    else:
        pen_media += [x for x in (C.call(cfx, "pen_effect", "slug") or []) if x not in pen_media]
    drain_media = _rmedia("drain_part", "shot", [])
    part_drain = {"Type": "ExplosiveResourceDrain", "ResourceType": "battery", "TotalDrain": _rider(n["part_drain"]),
                  "Radius": n["part_drain_r"], "Slices": 1, "Filter": {"Ships": True, "Shields": True}}
    if drain_media:
        part_drain["MediaEffectsOnDrainFactor"] = 0.0003
        part_drain["MediaEffectsOnDrain"] = drain_media
    pen_eff = [{"Type": "Damage", "Damage": _shot(per_part), "DamagePool": "DamagePool", "DoPooledDamageFirst": True},
               part_drain,
               {"Type": "StatusApplication", "StatusType": "cosmoteer.disruptor_drain",
                "StatusDuration": n["disruptor_s"], "StatusValue": {"BaseValue": n["disruptor_v"],
                                                                    "EffectScaleExponent": 1}},
               {"Type": "StatusApplication", "StatusType": "cosmoteer.fire",
                "StatusChance": {"BaseValue": n["fire_chance"], "EffectScaleExponent": 1}, "ValueType": "Interpolated"},
               {"Type": "Impulse", "Impulse": _shot(n["impulse"])}]
    pen_op = {"ReduceEffectsByPenetration": True, "HitEffects": pen_eff,
              "MediaEffectsScale": {"BaseValue": 1, "BuffType": B_SHOT, "BuffMode": "Multiply"},
              "MediaEffects": pen_media}
    hit = {"Type": "PenetratingHit", **OWN_SHIP_PASS,
           "Penetration": _shot(n["pen"], ese=False), "PenetrationSpeed": "&~/Speed",
           "CrewCollisions": {"Enemies": True, "Junk": True}, "PenetratesCrew": True,
           "HitCrew": "&HitOperational",
           "HitShield": {"ReduceEffectsByPenetration": True, "HitEffects": shield_eff, "MediaEffects": shield_media},
           "HitOperational": hit_op,
           "HitStructural": {"ReduceEffectsByPenetration": True,
                             "HitEffects": [{"Type": "Damage", "Damage": _shot(n["struct_dmg"])},
                                            {"Type": "Impulse", "Impulse": _shot(n["struct_imp"])}],
                             "MediaEffectsScale": {"BaseValue": 1, "BuffType": B_SHOT, "BuffMode": "Multiply"},
                             "MediaEffects": [f"&<{p}>" for p in VAN_STRUCT] + [_sound(VAN_IMPACT_SOUNDS, 0.5,
                                                                                     shot_buff=True)]},
           "PenetratingOperational": pen_op,
           "PenetratingStructural": {}}
    if r2:
        # semantica vanilla (bullet_railgun 0.30.3): o resto do pool se perde onde o dardo para
        hit["FinishedPenetratingOperational"] = "&PenetratingOperational"
    else:
        # despejo do pool + pacote do fim do caminho onde a penetracao acaba (desvio do vanilla: SPEC.shot)
        fin = dict(pen_op)
        fin["HitEffects"] = list(pen_eff) + [{"Type": "Damage", "Damage": 0, "DamagePool": "DamagePool",
                                              "DamagePoolFactor": {"BaseValue": 1, "EffectScaleExponent": 1}},
                                             "&~/IMPACT/EmpBurst", "&~/IMPACT/HeatPool", "&~/IMPACT/FireSplash"]
        fin["MediaEffects"] = list(impact_media)
        hit["FinishedPenetratingOperational"] = fin
    hit["FinishedPenetratingStructural"] = "&PenetratingStructural"
    comp["Hit"] = hit
    # ---- visual em voo: dardo da arte (art3d/bs_shells2 'slug') + risco azul + luzes (fxkit.light_pair)
    art = C.call(cfx, "art_components", "slug") or {}
    if art:
        comp.update(art)
    else:
        comp["Sprite"] = {"Type": "AnimatedSprite", "ReduceScaleWith": "Hit", "ReduceScaleExponent": 0.5,
                          "Animation": {"AtlasSprite": {"Texture": {"File": Q(VAN_SLUG_SPRITE), "SampleMode": "Linear",
                                                                    "MipLevels": "max"},
                                                        "Size": [2.8125, 1.875], "TargetBlendMode": dict(FXK.ADD_SPARK)},
                                        "FrameCount": 16, "FrameSize": [128, 128], "FramesPerRow": 4,
                                        "FramesPerSecond": 60}}
    tex = _tex()
    if tex is not None:
        comp["Streak"] = {"Type": "AnimatedSprite", "RenderBucket": "BulletUpper3", "Offset": [-0.6, 0],
                          "Animation": {"AtlasSprite": {"Texture": {"File": Q(tex.ref("bs_rail_streak.png")),
                                                                    "SampleMode": "Linear", "MipLevels": "max"},
                                                        "Size": [4.2, 1.6], "TargetBlendMode": "Add"},
                                        "FrameCount": 8, "FrameSize": [256, 96], "FramesPerRow": 2,
                                        "FramesPerSecond": 30}}
    start = FXK.start_time(1.5, n["speed"] * m_of(1))
    comp.update(FXK.light_pair([6, 3], FXK.pal("rail")["glow"], [3.6, 1.2], None, start, FXK.UNLIT_SHELL, key="slug"))
    trail = _rmedia("trail", "shot", [VAN_TRAIL, VAN_TRAIL_RING]) + [f"&<{VAN_TRAIL_DIST}>"]
    comp["MediaEffects"] = {"Type": "MediaEffects",
                            "MediaEffectsScale": {"BaseValue": 1, "BuffType": B_SHOT, "BuffMode": "Multiply"},
                            "MediaEffects": trail}
    top["Components"] = comp
    return top


# ============================================================================= arte (metas layered)
# camadas dos metas aprovados (art3d/bs_rail_*/meta.json no BASE), so para a arte PROVISORIA quando a pasta faltar
# (BS_ARTE_PROCEDURAL=1): mesmos nomes, camadas do jogo e retangulos, entao as regras saem iguais
STAND_IN = {
    "bs_rail_loader": ([5, 5], [
        {"name": "floor", "game_layer": "floors"},
        {"name": "projeteis", "game_layer": "doodads_low", "rect": [1.75, 2.625, 1.5, 2.25], "levels": 6},
        {"name": "culatra_projetil", "game_layer": "doodads_low", "rect": [2.0, 0.0, 1.0, 2.0]},
        {"name": "consola", "game_layer": "walls", "rect": [1.0, 1.5, 1.0, 1.0], "frames": 4, "interval": 0.1,
         "rects": [[1.0, 1.5, 1.0, 1.0], [3.0, 1.5, 1.0, 1.0]]},
        {"name": "culatra_abre", "game_layer": "walls", "rect": [2.0, 0.0, 1.0, 1.0], "frames": 3, "interval": 0.0666},
        {"name": "culatra_carrega", "game_layer": "walls", "rect": [2.0, 0.0, 1.0, 2.0], "frames": 6, "interval": 0.2},
        {"name": "weapon", "game_layer": "weapons", "rect": [1.0, 0.0, 3.0, 1.0], "normals": True},
        {"name": "capacitores", "game_layer": "doodads_high", "rect": [0.0, 2.625, 5.0, 2.0], "levels": 3},
        {"name": "luz_culatra", "game_layer": "lights_add", "rect": [1.0, 0.0, 3.0, 1.0], "levels": 2},
        {"name": "roof", "game_layer": "roofs", "normals": True},
        {"name": "culatra_tranco", "game_layer": "roof_turrets", "rect": [0.375, 0.0, 4.25, 4.75], "frames": 8,
         "interval": 0.05, "normals": True}]),
    "bs_rail_barrel": ([3, 3], [
        {"name": "floor", "game_layer": "floors"},
        {"name": "trilhos", "game_layer": "doodads_low", "levels": 9},
        {"name": "carga", "game_layer": "lights_add", "levels": 8},
        {"name": "roof", "game_layer": "roofs", "normals": True},
        {"name": "tambores_tranco", "game_layer": "roof_turrets", "frames": 8, "interval": 0.05, "normals": True}]),
    "bs_rail_muzzle": ([3, 4], [
        {"name": "floor", "game_layer": "floors"},
        {"name": "trilhos", "game_layer": "doodads_low"},
        {"name": "weapon_tranco", "game_layer": "weapons", "rect": [0.0, 0.0, 3.0, 3.5625], "frames": 8,
         "interval": 0.05, "normals": True},
        {"name": "carga", "game_layer": "lights_add", "levels": 6},
        {"name": "roof", "game_layer": "roofs", "normals": True},
        {"name": "slug", "game_layer": "walls", "rect": [1.1, 0.5, 0.8, 3.0]},
        {"name": "slug_glow", "game_layer": "lights_add", "rect": [0.9, 0.3, 1.2, 3.4]},
        {"name": "tambor_tranco", "game_layer": "roof_turrets", "rect": [0.875, 3.0, 1.25, 1.0], "frames": 8,
         "interval": 0.05, "normals": True}]),
}
TRANCO_LAYERS = {"bs_rail_loader": ["culatra_tranco"], "bs_rail_barrel": ["tambores_tranco"],
                 "bs_rail_muzzle": ["weapon_tranco", "tambor_tranco"]}
_METAS = {}


def meta_of(short):
    """meta.json de art3d/<short> (ADOTADO) ou, sem ele e com BS_ARTE_PROCEDURAL=1, um meta provisorio com as mesmas
    camadas (bsgen.layered.stand_in; os quadros do tranco recebem a mesma ordem X2..X8, X1)."""
    if short in _METAS:
        return _METAS[short]
    meta = A3.load_meta(short)
    if meta is None:
        A3.require(short, None)       # sem BS_ARTE_PROCEDURAL=1: para o build (regressao de arte)
        size, layers = STAND_IN[short]
        meta = L.stand_in(f"{AUTHOR}.{short}", size, layers)
        meta["tranco"] = {}
        for nm in TRANCO_LAYERS[short]:
            files = meta["layers"][nm]["files"]
            meta["tranco"][nm] = {"AnimationFiles_order": files[1:] + files[:1]}
        _D().PLACEHOLDERS.append(f"{AUTHOR}.{short}: art3d/{short} ausente (arte provisoria layered)")
    elif meta.get("kind") != "layered" or list(meta.get("size") or []) != list(STAND_IN[short][0]):
        raise ValueError(f"art3d/{short}: meta {meta.get('kind')} {meta.get('size')} (esperado layered "
                         f"{STAND_IN[short][0]})")
    _METAS[short] = meta
    return meta


def publish_art(out, short, meta, ctx):
    """Arte da peca em parts/<short>/ (make_art.layered_art: copia + paredes danificadas; --no-art: so a copia) ->
    nomes das paredes por nivel de dano (ou None = so walls.png)."""
    art = ctx.get("art")
    pdir = f"parts/{short}"
    if art is not None:
        res = art.layered_art(out, pdir, short, meta, what=f"{AUTHOR}.{short}")
        return (res.get("walls_damage") or {}).get(meta.get("sub"))
    if not meta.get("stand_in"):
        A3.copy_files(out.root, pdir, short, meta)
    return None


def _anim_files(meta, name):
    return [f for f, _n in L.sprites(meta, name, order="files")]


def _rect(meta, name, i=0):
    return L.rects(L.layer(meta, name))[i]


def toggled_anim(meta, name, toggle, interval=WAVE_FRAME, off_static=False, location=None):
    """Graphics que acende quando `toggle` liga: ToggleOnDoodad = os niveis da camada como animacao (subida, presa no
    ultimo: ClampAnimation); off_static = ToggleOffDoodad com o 1o nivel parado (trilhos apagados). Layer e
    retangulo do meta."""
    ent = L.layer(meta, name)
    r = _rect(meta, name)
    gl = ent["game_layer"]
    files = _anim_files(meta, name)
    comp = {"Type": "Graphics", "Location": location or L.location(r), "DoodadToggle": toggle,
            "ToggleOnDoodad": {"Layer": Q(gl), "DamageLevels": [
                {"AnimationFiles": [Q(f) for f in files], "Size": L.size(r), "AnimationInterval": interval,
                 "ClampAnimation": True}]}}
    if off_static:
        comp["ToggleOffDoodad"] = {"Layer": Q(gl), "DamageLevels": [{"File": Q(files[0]), "Size": L.size(r)}]}
    return comp


def tranco_graphics(meta, name, trigger):
    """Graphics do TRANCO (quadros do meta, ordem [X2..X8, X1], ultimo = repouso; AnimationStartTime MinValue +
    ClampAnimation: em repouso desde o carregamento, so o gatilho toca; NonOperationalDoodad = X1)."""
    if not L.has_tranco(meta, name):
        raise ValueError(f"{meta.get('id')}: camada {name} sem a tabela 'tranco' do meta (ordem dos quadros)")
    g = L.graphics(meta, name, OperationalToggle="IsOperational", ResetAnimationTrigger=trigger,
                   off_slot="NonOperationalDoodad")
    if isinstance(g, list):
        raise ValueError(f"{meta.get('id')}: camada de tranco {name} com varias copias")
    return g


def editor_icon(meta, size):
    return {"Texture": {"File": Q(L.editor_icon(meta) or "icon.png"), "SampleMode": "Linear"}, "Size": list(size)}


def blueprints(meta, w, h):
    return {"Type": "BlueprintSprite", "File": Q(L.blueprints(meta) or "blueprints.png"), "Size": [w, h]}


def base_graphics(meta, walls):
    """Piso, moldura (niveis de dano quando o make_art gravou) e teto + normais."""
    return L.base_graphics(meta, walls_damage=walls)


# ============================================================================= pedacos comuns das pecas
def _sealed(part):
    """Peca fechada e blindada (vanilla thermal_battery.rules:23-25)."""
    part["AllowedDoorLocations"] = []
    part["GeneratorRequiresDoor"] = False
    part["CrewSpeedFactor"] = 0


def _armor(part, sp):
    ar = sp.get("armor") or {}
    if ar:
        part["InitialPenetrationResistance"] = ar.get("InitialPenetrationResistance", 5)
        part["ContinuingPenetrationResistance"] = ar.get("ContinuingPenetrationResistance", 3)


def _scorched(comp):
    comp["ScorchedToggle"] = {"Type": "StatusToggle", "StatusType": "cosmoteer.scorched", "MinStatusValue": 1,
                              "Invert": True}


def _perdeu(comp):
    """Gatilho 'perdeu a operacao' (apaga carga/luz que ficariam acesas sem tiro)."""
    comp["PerdeuOperacao"] = {"Type": "ToggleTrigger", "Toggle": "IsOperational", "TriggerWhenOn": False,
                              "TriggerWhenOff": True}


def _relay(comp, proxy):
    """rail.tranco_gatilho: 'relay' = MultiTrigger local de pulso unico sobre o TriggerProxy (nunca Timer); 'proxy' =
    o TriggerProxy direto. Devolve o nome do gatilho do ResetAnimationTrigger."""
    if tranco_gatilho() == "proxy":
        return proxy
    comp["TrancoRelay"] = {"Type": "MultiTrigger", "Triggers": [proxy]}
    return "TrancoRelay"


def _wave_delays():
    """Atraso da DESCIDA da carga por indice de cano (1 = junto do carregador): o dardo entra no cano i em
    t(3i - 4) s depois do ProjectileStartTrigger (cinematica do RailgunProjectile 6 -> 50 quadros/s em 3N + 4 quadros,
    tabela do meta art3d/bs_rail_barrel); a media sobre os N possiveis (N >= i) erra <= 0,03 s (1 quadro)."""
    out = {}
    for i in range(1, MAX_CANOS + 1):
        d = 3 * i - 4
        vals = []
        for N in range(i, MAX_CANOS + 1):
            T = (3 * N + 4) / 28.0
            vals.append(0.0 if d <= 0 else (-6 + math.sqrt(36 + 88 * d / T)) / (44 / T))
        out[i] = round(sum(vals) / len(vals), 2)
    return out


def _indicators(center, items):
    return {"Type": "IndicatorSprites", "Location": center, "Indicators": items}


def _ind(toggle, sprite, hides=None, delay=None, build=False):
    it = {"Toggle": toggle}
    if build:
        it["ShowInBuildMode"] = True
    if delay is not None:
        it["Delay"] = delay
    it["AtlasSprite"] = sprite if sprite.startswith("&") and sprite.endswith("Scorched") else \
        {"File": sprite, "Size": [1, 1]}
    if hides:
        it["HidesIndicators"] = hides
    return it


# ============================================================================= Carregador 5x5
def build_loader(meta, ctx, walls):
    D = _D()
    sp = spec()["parts"]["carregador"]
    st = sp["storages"]
    w, h = sp["size"]
    center = [w / 2, h / 2]
    li = loader_intake()
    tele = D.transport() == "teleporte"
    g = {"id": LOADER, "short": SHORT[LOADER], "size": [w, h], "kind": "arma",
         "fita_fx_location": sp.get("fita_fx_location")}
    add_cats, add_buffs = [], []
    if li == "auto":
        res = C.call(_intake(), "part_fields", g, ctx) or {}
        add_cats = list(res.get("TypeCategories_add") or [])
        add_buffs = list(res.get("ReceivableBuffs_add") or [])
    cats = list(sp["type_categories"])
    for c in add_cats:
        if c not in cats:
            cats.append(c)
    buffs = [B_REV] + ([B_COUNT] if power_mode() == "B" else []) + [b for b in add_buffs]

    part = {
        "NameKey": Q(f"Parts/{KEY[LOADER]}"), "IconNameKey": Q(f"Parts/{KEY[LOADER]}Icon"),
        "DescriptionKey": Q(f"Parts/{KEY[LOADER]}Desc"), "ID": LOADER,
        "EditorParentParts": [Q(MUZZLE)],
        "Resources": [[r, q] for r, q in sp["build_cost"]],
        "Size": [w, h], "Density": 4, "SelectionTypeID": Q("bs_rail"), "SelectionPriority": 1,
        "SelectionTypeByRotation": True, "MaxHealth": int(sp["max_health"]), "TypeCategories": cats,
        "ReceivableBuffs : ^/0/ReceivableBuffs": buffs,
        "AllowedDoorLocations": LOADER_DOORS, "ForceManhattanPathInPart": True, "BlockedTravelCells": LOADER_BLOCKED,
        "EditorIcon": editor_icon(meta, (sp.get("geometry_5x5") or {}).get("EditorIcon_Size") or [115, 115]),
    }
    comp = {}
    comp[comment("---- liga/desliga (V303 railgun_loader.rules:57-104) ----")] = None
    comp["BuffOperational"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "PartCrew", "ScorchedToggle"],
                               "Mode": "All"}
    comp["IsOperational"] = {"Type": "MultiToggle", "Toggles": ["BuffOperational", "RailReverseOperationBuffToggle"],
                             "Mode": "All"}
    comp["CommandConsumptionToggle"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "ScorchedToggle"],
                                        "Mode": "All"}
    comp["RailReverseOperationBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_REV}
    comp["PowerToggle"] = {"Type": "UIToggle", "ToggleID": Q("on_off"), "Default": 1, "RequiresCommand": False}
    _scorched(comp)
    comp["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "CommandConsumptionToggle",
                               "CommandPoints": int(sp["command_points"])}

    comp[comment("---- energia da arma inteira (a ponta e os canos usam por proxy) ----")] = None
    comp["LoaderBattery"] = {"Type": "ResourceStorage", "ResourceType": "battery",
                             "MaxResources": int(st["LoaderBattery"]["MaxResources"]),
                             "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/PowerDeliver"}
    comp["BatteryConsumer"] = {"Type": "ResourceConsumer", "ResourceType": "battery", "Storage": "LoaderBattery",
                               "DefaultPriority": "&/PRIORITIES/Weapon_Supply",
                               "ResupplyThreshold": int(st["BatteryConsumer"]["ResupplyThreshold"]),
                               "OperationalToggle": "PowerToggle"}

    comp[comment("---- projeteis: paiol interno (12) -> camara (1) ----")] = None
    mag = int(st["SlugMagazine"]["MaxResources"])
    comp["SlugMagazine"] = {"Type": "ResourceStorage", "ResourceType": RES_SLUG, "MaxResources": mag,
                            "UITileRect": ["2 + 7/64", "3 + 7/64", "1 - 14/64", "1 - 14/64"],
                            "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
                            "DropResourcesWhenDestroyed": True}
    fita = li == "auto" and tele
    comp["SlugConsumer"] = C.mag_consumer(RES_SLUG, "SlugMagazine", "CommandConsumptionToggle",
                                          threshold=int(st["SlugConsumer"]["ResupplyThreshold"]), comp=comp,
                                          toggle_name="Reserva_SlugConsumer", fita_gate=fita)
    comp["LoadedSlug"] = {"Type": "ResourceStorage", "ResourceType": RES_SLUG,
                          "MaxResources": int(st["LoadedSlug"]["MaxResources"]),
                          "DelayBeforeReadyToUse": st["LoadedSlug"].get("DelayBeforeReadyToUse", 0.25),
                          "AnticipateMoreResourcesFrom": ["SlugMagazine"], "ToggleOnResources": 1,
                          "ToggleOffResources": 0,
                          "UITileRect": ["2 + 7/64", "7/64", "1 - 14/64", "1 - 14/64"],
                          "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
                          "DropResourcesWhenDestroyed": True}
    comp["AmmoPrereq"] = {"Type": "MultiResourceStorage", "ResourceType": RES_SLUG,
                          "ResourceStorages": ["LoadedSlug", "SlugMagazine"], "ToggleOnResources": 1,
                          "ToggleOffResources": 0}
    comp["AmmoLoader"] = {"Type": "ResourceConverter", "FromStorage": "SlugMagazine", "ToStorage": "LoadedSlug",
                          "FromQuantity": 1, "ToQuantity": 1, "Interval": st["AmmoLoader"]["Interval"]}
    comp["LoadEffects"] = {"Type": "TriggeredEffects", "Trigger": "AmmoLoader",
                           "MediaEffects": "&/COMMON_EFFECTS/AmmoLoadWithIntensity", "FactorMediaEffectsWith": "LoadedSlug"}

    # ---- logistica (rail.loader_intake)
    if li == "auto":
        comp[comment("---- entrada pela logistica (seam do bsgen.intake: Fita / acoplamento) ----")] = None
        C.call(_intake(), "weapon_intake", comp, g, ctx)
        C.call(_intake(), "weapon_return", comp, g, ctx)
    elif li == "acoplamento":
        comp[comment(f"---- rail.loader_intake = acoplamento: paiol de projeteis encostado em {ACOPLA_CELL} ----")] = None
        I = _intake()
        prox = C.call(I, "acoplado_proxy", RES_SLUG, "slug", ACOPLA_CELL) or {
            "Type": "ResourceStorageProxy", "ResourceType": RES_SLUG, "PartLocation": list(ACOPLA_CELL),
            "ProxyableComponents": [{"PartCriteria": {"Category": "bs_paiol_slug"}, "ComponentID": "Estoque_slug"}]}
        comp["PaiolAcoplado_0"] = prox
        comp["AlimentadorAcoplado_0"] = {"Type": "ResourceConverter", "OperationalToggle": "CommandConsumptionToggle",
                                         "FromStorage": "PaiolAcoplado_0", "FromQuantity": 1,
                                         "MinFromQuantityForConversion": 1, "ToStorage": "SlugMagazine",
                                         "ToQuantity": 1, "Interval": 0.1}

    comp[comment("---- corrente para a frente (SPEC.railgun.chain_offsets_5x5) ----")] = None
    comp["RailBuffProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_RAIL, "BuffAmount": 0,
                                "BuffArea": [1, -1, 3, 1], "Criteria": dict(CRIT_CARREGADOR_FRENTE)}
    comp["OperationBuffProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_OP, "BuffArea": [1, -1, 3, 1],
                                     "OperationalToggle": "BuffOperational", "Criteria": dict(CRIT_CARREGADOR_FRENTE)}
    comp["WeaponTrigger"] = {"Type": "TriggerProxy", "PartLocation": [1, -1],
                             "PartCriteria": dict(CRIT_CARREGADOR_FRENTE), "ComponentID": "Weapon"}
    comp["ProjectileStartTrigger"] = {"Type": "TriggerProxy", "PartLocation": [1, -1],
                                      "PartCriteria": dict(CRIT_CARREGADOR_FRENTE),
                                      "ComponentID": "ProjectileStartTrigger"}
    comp["EmitTrigger"] = {"Type": "TriggerProxy", "PartLocation": [1, -1], "PartCriteria": dict(CRIT_CARREGADOR_FRENTE),
                           "ComponentID": "EmissionTriggered"}
    if power_mode() == "B":
        comp[comment("---- energia 'Cano B': 500 por cano, tirados da PROPRIA bateria (ScaledBuff vanilla) ----")] = None
        comp["DrenoB"] = {"Type": "ResourceChange", "Trigger": "EmitTrigger", "ResourceStorage": "LoaderBattery",
                          "Amount": {"BaseValue": 0, "Modifiers": [{"Type": "ScaledBuff", "BuffType": B_COUNT,
                                                                    "Scale": -POWER_PER_CANO,
                                                                    "ModificationMode": "Add"}]}}
    _perdeu(comp)

    comp[comment("---- tripulacao (2 postos: meta crew_pos) ----")] = None
    names = []
    for i, (x, y) in enumerate(sp.get("crew_pos") or meta.get("crew_pos") or [[1.5, 2.0], [3.5, 2.0]], start=1):
        nm = f"CrewLocation{i}"
        comp[nm] = {"Type": "CrewLocation", "Location": [x, y], "Rotation": "0d"}
        names.append(nm)
    comp["PartCrew"] = {"Type": "PartCrew", "Crew": int(sp["crew"]), "DefaultPriority": "&/PRIORITIES/Weapon_Crew",
                        "PrerequisitesBeforeCrewing": ["CommandConsumptionToggle"],
                        "HighPriorityPrerequisites": ["AmmoPrereq"],
                        "CrewDestinations": [f"&../../{n}/Location" for n in names], "CrewLocations": names}

    comp[comment("---- arte (art3d/bs_rail_loader, layered) ----")] = None
    comp["Graficos"] = base_graphics(meta, walls)
    comp["Culatra"] = L.graphics(meta, "weapon", OperationalToggle="IsOperational", off_slot="NonOperationalDoodad")
    comp.update(L.components(meta, "consola", "Consola", OperationalToggle="IsOperational",
                             off_slot="NonOperationalDoodad"))
    comp["Capacitores"] = L.graphics(meta, "capacitores", ResourceStorage="LoaderBattery")
    comp["Projeteis"] = L.graphics(meta, "projeteis", ResourceStorage="SlugMagazine")
    # folhas da culatra (walls): culatra_abre fecha sobre o dardo quando ele chega; culatra_carrega (folhas abertas
    # + o dardo subindo) so enquanto recarrega - nunca as duas juntas (meta notes): a de abrir some (OperationalToggle,
    # toggled doodads escondem fora de operacao) enquanto a de carregar aparece
    comp["Recarregando"] = {"Type": "MultiToggle", "Mode": "All",
                            "Toggles": ["{ Toggle=LoadedSlug; Invert=true; }", "AmmoPrereq"]}
    comp["NaoRecarregando"] = {"Type": "MultiToggle", "Mode": "All", "Toggles": ["{ Toggle=Recarregando; Invert=true; }"]}
    ra, rc = _rect(meta, "culatra_abre"), _rect(meta, "culatra_carrega")
    abre = _anim_files(meta, "culatra_abre")
    iv_a = L.layer(meta, "culatra_abre").get("interval", 0.0666)
    comp["CulatraFolhas"] = {
        "Type": "Graphics", "Location": L.location(ra), "OperationalToggle": "NaoRecarregando",
        "DoodadToggle": "LoadedSlug",
        "ToggleOnDoodad": {"Layer": Q("walls"), "DamageLevels": [
            {"AnimationFiles": [Q(f) for f in reversed(abre)], "Size": L.size(ra), "AnimationInterval": iv_a,
             "ClampAnimation": True}]},
        "ToggleOffDoodad": {"Layer": Q("walls"), "DamageLevels": [
            {"AnimationFiles": [Q(f) for f in abre], "Size": L.size(ra), "AnimationInterval": iv_a,
             "ClampAnimation": True}]}}
    # carga do dardo: doodad LIGADO pelo Recarregando (a animacao recomeca quando o toggle vira, como as portas
    # bullet_door do railgun_loader vanilla 0.30.3:566-660), presa no ultimo quadro (dardo em cima, folhas abertas)
    comp["CulatraCarregando"] = {
        "Type": "Graphics", "Location": L.location(rc), "DoodadToggle": "Recarregando",
        "ToggleOnDoodad": {"Layer": Q("walls"), "DamageLevels": [
            {"AnimationFiles": [Q(f) for f in _anim_files(meta, "culatra_carrega")], "Size": L.size(rc),
             "AnimationInterval": L.layer(meta, "culatra_carrega").get("interval", 0.2), "ClampAnimation": True}]}}
    # o dardo na camara: some quando a corrida pelo cano comeca (o RailgunProjectile da ponta mostra o mesmo dardo)
    comp["AmmoHideToggle"] = {"Type": "TriggeredToggle", "OnTrigger": "ProjectileStartTrigger", "OffTrigger": "EmitTrigger",
                              "OperationalToggle": "IsOperational"}
    comp["DardoNaCamara"] = {"Type": "ToggledComponents", "Toggle": "AmmoHideToggle", "Invert": True,
                             "Components": {"DardoNaCamaraSprite": L.graphics(meta, "culatra_projetil", kind="resource",
                                                                              ResourceStorage="LoadedSlug")}}
    if charge_wave() == "atraso":
        comp[comment("---- carga (rail.charge_wave = atraso): a culatra acende no gatilho e apaga na corrida ----")] = None
        comp["LuzCulatraApaga"] = {"Type": "MultiTrigger",
                                   "Triggers": ["ProjectileStartTrigger", "EmitTrigger", "PerdeuOperacao"]}
        comp["LuzCulatraAcesa"] = {"Type": "TriggeredToggle", "OnTrigger": "WeaponTrigger",
                                   "OffTrigger": "LuzCulatraApaga", "OperationalToggle": "IsOperational"}
        comp["LuzCulatra"] = toggled_anim(meta, "luz_culatra", "LuzCulatraAcesa", interval=0.1)
    comp[comment("---- TRANCO: a culatra bate para tras 1 quadro depois da boca (um coice por tiro) ----")] = None
    trig = _relay(comp, "EmitTrigger")
    comp["TrancoCulatra"] = tranco_graphics(meta, "culatra_tranco", trig)

    comp[comment("---- efeitos ----")] = None
    comp["FireEffect"] = {"Type": "TriggeredEffects", "Trigger": "ProjectileStartTrigger", "Location": [2.5, 0.5],
                          "MediaEffects": [_sound(VAN_SHOT_SOUNDS, 1)]}
    comp.update(C.destroyed_effects(center, w, h))
    # descarga dos capacitores (SPEC cookoff: 6000 em raio 2 x carga da bateria). ExplosiveDamage com TotalDamage
    # { EffectScaleExponent 1 } e a forma que o vanilla escala por FactorHitEffectsWith (factory_he); o AreaDamage
    # nunca aparece com EffectScaleExponent no jogo (sem ele a descarga nao acompanharia a bateria)
    comp["CapacitorDischarge"] = {"Type": "DeathEffects", "Location": center, "FactorHitEffectsWith": "LoaderBattery",
                                  "IncludeWhenUnderConstruction": False,
                                  "HitEffects": [{"Type": "ExplosiveDamage",
                                                  "TotalDamage": {"BaseValue": 6000, "EffectScaleExponent": 1},
                                                  "Radius": 2,
                                                  "Filter": {"OperationalHealth": True, "StructuralHealth": False,
                                                             "Friendlies": True}}]}
    comp["Indicators"] = _indicators(center, [
        _ind("ScorchedToggle", "&/INDICATORS/Scorched", hides=[1, 2, 3, 4]),
        _ind("PowerToggle", "&/INDICATORS/PowerOff", hides=[2, 3, 4]),
        _ind("AmmoPrereq", "&/INDICATORS/NoAmmo", delay=FIRE_INTERVAL),
        _ind("LoaderBattery", "&/INDICATORS/NoPower", delay=FIRE_INTERVAL),
        _ind("PartCrew", "&/INDICATORS/NoCrew")])
    comp["Blueprints"] = blueprints(meta, w, h)
    part["Components : ^/0/Components"] = comp
    part["Stats"] = {
        "CrewRequired": "&~/Part/Components/PartCrew/Crew",
        "AmmoCapacity": "(&~/Part/Components/SlugMagazine/MaxResources) + (&~/Part/Components/LoadedSlug/MaxResources)",
        "PowerCapacity": "(&~/Part/Components/LoaderBattery/MaxResources) / 1000",
    }
    part["StatsByCategory"] = f"&<../{SHORT[MUZZLE]}/{SHORT[MUZZLE]}.rules>/Part/StatsByCategory"
    return {"Part : <./Data/ships/terran/base_large_part_terran.rules>/Part": part}


# ============================================================================= Cano 3x3
def build_barrel(meta, ctx, walls):
    sp = spec()["parts"]["cano"]
    w, h = sp["size"]
    center = [w / 2, h / 2]
    two = [dict(CRIT_CANO_TRAS), dict(CRIT_CARREGADOR_TRAS)]
    part = {
        "NameKey": Q(f"Parts/{KEY[BARREL]}"), "IconNameKey": Q(f"Parts/{KEY[BARREL]}Icon"),
        "DescriptionKey": Q(f"Parts/{KEY[BARREL]}Desc"), "ID": BARREL,
        "EditorParentParts": [Q(MUZZLE)],
        "Resources": [[r, q] for r, q in sp["build_cost"]],
        "Size": [w, h], "Density": 6, "SelectionTypeID": Q("bs_rail"), "SelectionPriority": 1,
        "SelectionTypeByRotation": True, "MaxHealth": int(sp["max_health"]),
        "TypeCategories": list(sp["type_categories"]),
        "ReceivableBuffs : ^/0/ReceivableBuffs": [B_RAIL, B_OP, B_REV] + ([B_COUNT] if power_mode() == "B" else []),
    }
    _sealed(part)
    _armor(part, sp)
    part["EditorIcon"] = editor_icon(meta, [69, 69])
    comp = {}
    _scorched(comp)
    comp["RailBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_RAIL}
    comp["RailOperationBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_OP}
    comp["RailReverseOperationBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_REV}
    comp["BuffOperational"] = {"Type": "MultiToggle", "Toggles": ["RailOperationBuffToggle", "ScorchedToggle"],
                               "Mode": "All"}
    comp["IsOperational"] = {"Type": "MultiToggle", "Toggles": ["BuffOperational", "RailReverseOperationBuffToggle"],
                             "Mode": "All"}
    comp["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "ScorchedToggle",
                               "CommandPoints": int(sp["command_points"])}

    comp[comment("---- cadeias para a frente (V303 railgun_accelerator.rules:142-195) ----")] = None
    comp["RailBuffProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_RAIL,
                                "BuffAmount": {"BaseValue": 1, "BuffType": B_RAIL, "BuffMode": "Add"},
                                "BuffArea": [0, -1, 3, 1], "OperationalToggle": "RailBuffToggle",
                                "ChainsFromBuffType": B_RAIL, "Criteria": dict(CRIT_FRENTE)}
    comp["RailOperationBuffProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_OP, "BuffArea": [0, -1, 3, 1],
                                         "OperationalToggle": "BuffOperational", "ChainsFromBuffType": B_OP,
                                         "Criteria": dict(CRIT_FRENTE)}
    comp[comment("---- para TRAS: o cano de tras OU o carregador 5x5 centrado (2 entradas, SW chaingun_magazine) ----")] = None
    comp["ReverseBuffOperationProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_REV, "BuffArea": [0, 3, 3, 1],
                                            "OperationalToggle": "RailReverseOperationBuffToggle",
                                            "ChainsFromBuffType": B_REV, "Criterias": [dict(c) for c in two]}
    if power_mode() == "B":
        comp["ContagemBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_COUNT}
        comp["ContagemProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_COUNT,
                                    "BuffAmount": {"BaseValue": 1, "BuffType": B_COUNT, "BuffMode": "Add"},
                                    "BuffArea": [0, 3, 3, 1], "OperationalToggle": "ContagemBuffToggle",
                                    "ChainsFromBuffType": B_COUNT, "Criterias": [dict(c) for c in two]}
    comp["LoadedSlug"] = {"Type": "ResourceStorageProxy", "ResourceType": RES_SLUG, "PartLocation": [0, 3],
                          "ProxyableComponents": [{"PartCriteria": dict(c), "ComponentID": "LoadedSlug"} for c in two]}
    comp["LoaderBattery"] = {"Type": "ResourceStorageProxy", "ResourceType": "battery", "PartLocation": [0, 3],
                             "ProxyableComponents": [{"PartCriteria": dict(c), "ComponentID": "LoaderBattery"}
                                                     for c in two]}
    comp[comment("---- gatilhos passam para tras com os mesmos nomes (V303 railgun_accelerator.rules:212-256) ----")] = None
    for nm in ("Weapon", "ProjectileStartTrigger", "EmissionTriggered"):
        comp[nm] = {"Type": "TriggerProxy", "PartLocation": [0, -1], "PartCriteria": dict(CRIT_FRENTE),
                    "ComponentID": nm}
    _perdeu(comp)

    comp[comment("---- arte (art3d/bs_rail_barrel, layered) ----")] = None
    comp["Graficos"] = base_graphics(meta, walls)
    cw = charge_wave()
    if cw == "atraso":
        comp[comment("---- carga (rail.charge_wave = atraso): o cano de indice i acende 0,3 s x i depois do gatilho "
                     "e descarrega quando o dardo entra nele ----")] = None
        delays = _wave_delays()
        up, down = [], []
        for k in range(1, MAX_CANOS + 1):
            tog = f"EhCano_{k}"
            comp[tog] = {"Type": "BuffToggle", "BuffType": B_RAIL, "MinBuffValue": k - 1, "MaxBuffValue": k - 1}
            comp[f"CanoSobe_{k}"] = {"Type": "DelayTrigger", "OperationalToggle": tog, "Trigger": "Weapon",
                                     "Delay": round(WAVE_STEP * k, 3)}
            up.append(f"CanoSobe_{k}")
            if delays[k] <= 0:
                comp[f"CanoDesce_{k}"] = {"Type": "MultiTrigger", "OperationalToggle": tog,
                                          "Triggers": ["ProjectileStartTrigger"]}
            else:
                comp[f"CanoDesce_{k}"] = {"Type": "DelayTrigger", "OperationalToggle": tog,
                                          "Trigger": "ProjectileStartTrigger", "Delay": delays[k]}
            down.append(f"CanoDesce_{k}")
        comp["CargaSubiu"] = {"Type": "MultiTrigger", "Triggers": up}
        comp["CargaDesceu"] = {"Type": "MultiTrigger", "Triggers": down + ["EmissionTriggered", "PerdeuOperacao"]}
        comp["CargaAcesa"] = {"Type": "TriggeredToggle", "OnTrigger": "CargaSubiu", "OffTrigger": "CargaDesceu",
                              "OperationalToggle": "IsOperational"}
        comp["TrilhosCarga"] = toggled_anim(meta, "trilhos", "CargaAcesa", off_static=True)
        comp["BrilhoCarga"] = toggled_anim(meta, "carga", "CargaAcesa")
    else:
        comp["Trilhos"] = L.graphics(meta, "trilhos", kind="graphics", variant=1)
    comp[comment("---- TRANCO: os 3 tambores recuam (um coice por tiro) ----")] = None
    trig = _relay(comp, "EmissionTriggered")
    comp["TrancoTambores"] = tranco_graphics(meta, "tambores_tranco", trig)
    comp["ScorchedTrigger"] = {"Type": "ToggleTrigger", "Toggle": "ScorchedToggle", "TriggerWhenOn": False}
    comp["ScorchedEffects"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger", "Location": center,
                               "MediaEffects": "&/COMMON_EFFECTS/BigPartScorched"}
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "MediaEffects": "&/COMMON_EFFECTS/BigPartDestroyed",
                                "Location": center}
    comp["Indicators"] = _indicators(center, [
        _ind("ScorchedToggle", "&/INDICATORS/Scorched", hides=[1]),
        _ind("RailBuffToggle", "&/INDICATORS/MissingComponent", build=True)])
    comp["Blueprints"] = blueprints(meta, w, h)
    part["Components : ^/0/Components"] = comp
    stats = {}
    if power_mode() == "B":
        stats["PowerPerShot"] = POWER_PER_CANO / 1000
        stats["PowerPerSecond"] = f"(&PowerPerShot) / {FIRE_INTERVAL:g}"
        stats["ShotPowerUsage"] = ["&../PowerPerShot", "&../PowerPerSecond"]
    if stats:
        part["Stats"] = stats
    # SEM StatsByCategory RailgunBuff: o Stats/RailgunBuffFmt vanilla formata {0}..{29} (30 valores; com menos o
    # String.Format estoura no tooltip) e de 7 a 30 canos a Ponta fica desligada (CanosOk 1..6), entao uma tabela
    # de 30 linhas mentiria. O bonus por N vai no texto do Cano (strings) e a tabela completa no tooltip da Ponta.
    return {"Part : <./Data/ships/terran/base_large_part_terran.rules>/Part": part}


# ============================================================================= Ponta 3x4
def build_muzzle(meta, ctx, walls, shot_path):
    D = _D()
    sp = spec()["parts"]["ponta"]
    w, h = sp["size"]
    center = [w / 2, h / 2]
    cats = list(sp["type_categories"])
    for c in D.EXTRA_CATEGORIES.get(MUZZLE, []):
        if c not in cats:
            cats.append(c)
    part = {
        "NameKey": Q(f"Parts/{KEY[MUZZLE]}"), "IconNameKey": Q(f"Parts/{KEY[MUZZLE]}Icon"),
        "DescriptionKey": Q(f"Parts/{KEY[MUZZLE]}Desc"), "ID": MUZZLE,
        "EditorGroups": [Q(C.EDITOR_GROUP), Q("WeaponsProjectile")],
        "Resources": [[r, q] for r, q in sp["build_cost"]],
        "Size": [w, h], "Density": 6, "SelectionTypeID": Q("bs_rail"), "SelectionPriority": 1,
        "SelectionTypeByRotation": True, "MaxHealth": int(sp["max_health"]), "TypeCategories": cats,
        "SignificanceToggle": "ScorchedToggle", "ProhibitAbove": 3,
        "ReceivableBuffs : ^/0/ReceivableBuffs": [B_RAIL, B_SHOT, B_OP],
    }
    _sealed(part)
    _armor(part, sp)
    part["EditorIcon"] = editor_icon(meta, [69, 92])
    pw = power_mode()
    comp = {}
    comp[comment("---- liga/desliga (V303 railgun_launcher.rules:103-158) ----")] = None
    comp["IsOperational"] = {"Type": "MultiToggle", "Mode": "All",
                             "Toggles": ["PowerToggle", "RailOperationBuffToggle", "CanosOk", "ScorchedToggle"]}
    comp["CommandConsumptionToggle"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "ScorchedToggle"],
                                        "Mode": "All"}
    comp["PowerToggle"] = {"Type": "UIToggle", "ToggleID": Q("on_off"), "Default": 1, "RequiresCommand": False}
    _scorched(comp)
    comp["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "CommandConsumptionToggle",
                               "CommandPoints": int(sp["command_points"])}
    comp["FireModeToggle"] = {"Type": "UIToggle", "ToggleID": Q("fire_mode"), "Default": 1,
                              "ToggledOnChoices": [0, 1, 2]}
    comp["AutoTargetToggle"] = {"Type": "ModeToggle", "Mode": "FireModeToggle", "OnModes": [1, 2]}
    comp["AutoFireToggle"] = {"Type": "ModeToggle", "Mode": "FireModeToggle", "OnMode": 2}

    comp[comment("---- cadeia: N canos, multiplicador do tiro, operacao para tras ----")] = None
    comp["RailBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_RAIL}
    comp["RailOperationBuffToggle"] = {"Type": "BuffToggle", "BuffType": B_OP}
    comp["CanosOk"] = {"Type": "BuffToggle", "BuffType": B_RAIL, "MinBuffValue": 1, "MaxBuffValue": MAX_CANOS}
    comp["ShotBuffProvider"] = {"Type": "SelfBuffProvider", "BuffType": B_SHOT, "ChainsFromBuffType": B_RAIL,
                                "BuffAmount": {"BaseValue": 0, "BuffType": B_RAIL, "BuffMode": "Add"}}
    comp["ReverseOperationBuffProvider"] = {"Type": "AreaBuffProvider", "BuffType": B_REV, "BuffArea": [0, 4, 3, 1],
                                            "OperationalToggle": "IsOperational", "Criteria": dict(CRIT_PONTA_TRAS)}
    if pw == "B":
        comp["ContagemInicio"] = {"Type": "AreaBuffProvider", "BuffType": B_COUNT, "BuffAmount": 0,
                                  "BuffArea": [0, 4, 3, 1], "Criteria": dict(CRIT_PONTA_TRAS)}
    comp["SlugProxy"] = {"Type": "ResourceStorageProxy", "ResourceType": RES_SLUG, "PartLocation": [0, 4],
                         "PartCriteria": dict(CRIT_PONTA_TRAS), "ComponentID": "LoadedSlug"}
    comp["BatteryProxy"] = {"Type": "ResourceStorageProxy", "ResourceType": "battery", "PartLocation": [0, 4],
                            "PartCriteria": dict(CRIT_PONTA_TRAS), "ComponentID": "LoaderBattery"}

    comp[comment("---- arma fixa: passa por cima da propria nave (IgnoreFriendlyShip*LOSChecks) ----")] = None
    wsp = sp["weapon"]
    comp["Weapon"] = {
        "Type": "FixedWeapon", "Location": list(wsp["Location"]), "Rotation": wsp["Rotation"],
        "OperationalToggle": "IsOperational", "AutoFireToggle": "AutoFireToggle", "FireInterval": FIRE_INTERVAL,
        "TargetingArc": "90d",
        "AIFirepowerRating": {"BaseValue": 8000, "BuffType": B_SHOT, "BuffMode": "Multiply"},
        "Emitter": "BulletEmitter", "FirePermissionToggle": "FirePermission",
        # nomes do WeaponRules do 0.30.4c (vanilla cannon_deck.rules:618 e manipulator_beam_emitter.rules:447-448;
        # o IgnoreSourceShip* do SW nao existe no jogo e seria ignorado)
        "IgnoreFriendlyShipLowLOSChecks": True, "IgnoreFriendlyShipHighLOSChecks": True,
        "AutoTarget": {"TargetType": "ShipParts", "Toggle": "AutoTargetToggle"},
        # linha de cobertura da arma fixa (vanilla 0.30.3 railgun_launcher.rules:255-276 e SW 0.30.4 spinal
        # turbolasers; o 0.30.5 tirou o campo e ignora o que sobrar)
        "CoverageLine": {"LineSprite": {"Texture": "&/INDICATORS/RadialGradient", "VertexColor": [255, 255, 255, 191],
                                        "UVRect": [0.5, 0, 0, 1]},
                         "LineThickness": 2,
                         "BeginCapSprite : LineSprite": {"UVRect": [0, 0, 0.5, 1]}, "BeginCapSize": [1, 2],
                         "EndCapSprite : LineSprite": {"UVRect": [0.5, 0, 0.5, 1]}, "EndCapSize": [1, 2]},
    }
    comp["FirePermission"] = {"Type": "MultiToggle", "Mode": "All",
                              "Toggles": ["FireModeToggle", "{ Toggle=Carregando; Invert=true; }",
                                          "{ Toggle=ProjectileToggle; Invert=true; }"]}
    comp["Carregando"] = {"Type": "MultiToggle", "Mode": "All",
                          "Toggles": ['{ Toggle = { ID=TimerCarga; ToggleID="IsRunning"; } }']}
    comp["ReloadProgressBar"] = {"Type": "ProgressBar", "OperationalToggle": "IsOperational", "ShowProgressFor": "Weapon"}

    comp[comment("---- 1) carga: 1,0 s + 0,25 s por cano (cadeia de overclock vanilla como sequencia normal) ----")] = None
    comp["GatilhoArma"] = {"Type": "TriggerProxy", "ComponentID": "Weapon", "ProxyToggle": "IsOperational"}
    _perdeu(comp)
    comp["ReiniciaCarga"] = {"Type": "MultiTrigger", "Triggers": ["GatilhoArma", "PerdeuOperacao"]}
    comp["TimerCarga"] = {"Type": "Timer", "OperationalToggle": "IsOperational",
                          "Duration": {"BaseValue": CARGA_BASE, "MaxValue": FIRE_INTERVAL - 1.5,
                                       "Modifiers": [{"Type": "ScaledBuff", "BuffType": B_RAIL, "Scale": CARGA_POR_CANO,
                                                      "ModificationMode": "Add"}]},
                          "StartTrigger": "GatilhoArma", "ResetTrigger": "ReiniciaCarga",
                          "StopTrigger": "PerdeuOperacao"}
    comp["SomCarga"] = {"Type": "ContinuousEffects", "OperationalToggle": "Carregando",
                        "MediaEffectsRequireShipInView": False, "ParentToShip": True,
                        "MediaEffects": [Inh("/BASE_SOUNDS/AudioExteriorLongRange", {
                            "Sound": Q(VAN_CHARGE_LOOP), "OnlyWhenInSight": False, "Volume": 1.5, "RampUpTime": 0.5,
                            "RampDownTime": 0.1})],
                        "StartMediaEffects": [Inh("/BASE_SOUNDS/AudioExteriorLongRange", {
                            "Sound": Q(VAN_CHARGE_START), "OnlyWhenInSight": False, "Volume": 1.5,
                            "VolumeOverIntensity": 1})]}

    comp[comment("---- 2) o dardo corre pelo cano (RailgunProjectile: so grafico) ----")] = None
    comp["ProjectileStartTrigger"] = {"Type": "MultiTrigger", "Triggers": ["TimerCarga"]}
    comp["ProjectileToggle"] = {"Type": "TriggeredToggle", "OnTrigger": "ProjectileStartTrigger",
                                "OffTrigger": "Projectile", "OperationalToggle": "IsOperational"}
    comp["Projectile"] = {"Type": "RailgunProjectile", "Location": [1.5, 4.5], "OperationalToggle": "ProjectileToggle",
                          "YStartOffset": {"BaseValue": COMPRIMENTO_CANO, "BuffType": B_RAIL, "BuffMode": "Multiply"},
                          "YEndOffset": -4, "SpeedStart": VEL_INICIO_ANIM, "SpeedEnd": VEL_FIM_ANIM,
                          # AVISO vanilla: so para graficos (logica presa nele dessincroniza o multijogador)
                          "Interpolate": True}
    comp["ProjetilTerminou"] = {"Type": "TriggerProxy", "ComponentID": "Projectile"}

    comp[comment("---- 3) tiro: 1 dardo + energia do carregador pelos proxies ----")] = None
    emitter = {"Type": "BulletEmitter", "ChainedTo": "Weapon", "FireTrigger": "ProjetilTerminou",
               "GetTargetFrom": "Weapon", "OperationalToggle": "IsOperational", "DynamicDelayPredictor": "Projectile",
               "Bullet": f"&<{shot_path}>",
               "ResourceUsage": [{"ResourceStorage": "SlugProxy", "ResourcesUsed": SLUG_PER_SHOT},
                                 {"ResourceStorage": "BatteryProxy",
                                  "ResourcesUsed": POWER_FIXO if pw == "fixo" else POWER_BASE}]}
    if tranco_impulso() == "recoil":
        emitter["Recoil"] = TRANCO_RECOIL
    comp["BulletEmitter"] = emitter
    comp["EmissionTriggered"] = {"Type": "MultiTrigger", "Triggers": ["BulletEmitter"]}
    rfx = _rfx()
    muzzle = _rmedia("muzzle", "part", []) or [f"&<{VAN_RAIL_SHOOT}>"]
    muzzle.append(Inh("/BASE_SHAKE", {"ShakeAmount": SHAKE[0], "Duration": SHAKE[1]}))
    comp["FireEffect"] = {"Type": "TriggeredEffects", "ChainedTo": "Weapon", "Trigger": "BulletEmitter",
                          "Location": [0.6, 0], "AnchorMediaEffects": True, "MediaEffects": muzzle}
    comp[comment("---- TRANCO: anel de choque que fica no espaco + empurrao fisico (UM por tiro) ----")] = None
    ring = (list(rfx.media("shock", "part")) if rfx is not None else []) + \
        [f"&<{VAN_RAIL_SHOOT}>", f"&<{VAN_RAIL_DIST}>"]
    # tamanho FIXO em todo N (desvio do ADDENDUM 'x MediaEffectsScale RailShot'): nenhum componente de peca vanilla
    # ou SW usa MediaEffectsScale; o tremor da boca (BASE_SHAKE acima) tambem e fixo
    comp["TrancoAnel"] = {"Type": "TriggeredEffects", "Trigger": "BulletEmitter", "Location": [1.5, 0],
                          "Rotation": "-90d", "AnchorMediaEffects": False, "MediaEffects": ring}
    if tranco_impulso() == "impulso":
        imp = {"Type": "Impulse", "Impulse": {"BaseValue": TRANCO_IMPULSE, "BuffType": B_SHOT, "BuffMode": "Multiply"}}
        if sw("recoil_com"):
            imp["ApplyToCenterOfMass"] = True
        # sem ChainedTo (o Projectile e Interpolate = true): 90d = para tras de uma arma que atira para -y
        comp["TrancoImpulso"] = {"Type": "TriggeredEffects", "Trigger": "BulletEmitter", "Location": [1.5, 2],
                                 "Rotation": "90d", "HitEffects": [imp]}

    comp[comment("---- o dardo visivel dentro do canal (arte da ponta, presa ao Projectile) ----")] = None
    sl, sg = _rect(meta, "slug"), _rect(meta, "slug_glow")
    lb = LIGHT_BLOB
    comp["ProjetilVisivel"] = {"Type": "ToggledComponents", "Toggle": "ProjectileToggle", "Components": {
        "ProjetilBrilho": {"Type": "Sprite", "ChainedTo": "Projectile", "Layer": Q("lights_add"),
                           "AtlasSprite": {"File": Q(L.layer(meta, "slug_glow")["files"][0]), "Size": L.size(sg)}},
        "ProjetilLuz": {"Type": "Sprite", "ChainedTo": "Projectile", "Layer": Q("roof_lights_fancy"),
                        "AtlasSprite": {"File": Q(f"{V}/ships/common/light_blob.png"), "Size": [9, 9], "Z": 0.25,
                                        "VertexColor": {"Rf": round(lb[0] * 12, 3), "Gf": round(lb[1] * 12, 3),
                                                        "Bf": round(lb[2] * 12, 3), "Af": 1}}},
        "ProjetilSprite": {"Type": "Sprite", "ChainedTo": "Projectile", "Layer": Q("walls"),
                           "AtlasSprite": {"File": Q(L.layer(meta, "slug")["files"][0]), "Size": L.size(sl)}}}}
    comp["SomProjetil"] = {"Type": "ContinuousEffects", "ChainedTo": "Projectile", "OperationalToggle": "ProjectileToggle",
                           "FactorMediaEffectsIntensityWith": "Projectile",
                           "MediaEffects": [Inh("/BASE_SOUNDS/AudioExterior", {
                               "Sound": Q(VAN_RAIL_WAV), "Volume": 2, "Speed": 0.8, "RampUpTime": 0.05,
                               "RampDownTime": 0.25, "AllowStacking": False, "VolumeOverIntensity": 1,
                               "SpeedOverIntensity": [0.5, 1]})]}

    comp[comment("---- arte (art3d/bs_rail_muzzle, layered) ----")] = None
    comp["Graficos"] = base_graphics(meta, walls)
    comp["Trilhos"] = L.graphics(meta, "trilhos")
    if charge_wave() == "atraso":
        comp[comment("---- carga (atraso): a ponta acende depois do ultimo cano e apaga com o clarao; arcos azuis "
                     "nos ultimos 0,5 s ----")] = None
        up, arcs = [], []
        for k in range(1, MAX_CANOS + 1):
            tog = f"EhN_{k}"
            comp[tog] = {"Type": "BuffToggle", "BuffType": B_RAIL, "MinBuffValue": k, "MaxBuffValue": k}
            comp[f"PontaSobe_{k}"] = {"Type": "DelayTrigger", "OperationalToggle": tog, "Trigger": "GatilhoArma",
                                      "Delay": round(WAVE_STEP * (k + 1), 3)}
            up.append(f"PontaSobe_{k}")
            if rfx is not None:
                comp[f"ArcosInicio_{k}"] = {"Type": "DelayTrigger", "OperationalToggle": tog, "Trigger": "GatilhoArma",
                                            "Delay": round(max(0.05, charge_s(k) - 0.5), 3)}
                arcs.append(f"ArcosInicio_{k}")
        comp["PontaCargaSobe"] = {"Type": "MultiTrigger", "Triggers": up}
        comp["PontaCargaApaga"] = {"Type": "MultiTrigger", "Triggers": ["BulletEmitter", "PerdeuOperacao"]}
        comp["PontaCargaAcesa"] = {"Type": "TriggeredToggle", "OnTrigger": "PontaCargaSobe",
                                   "OffTrigger": "PontaCargaApaga", "OperationalToggle": "IsOperational"}
        comp["BrilhoCarga"] = toggled_anim(meta, "carga", "PontaCargaAcesa")
        if arcs:
            comp["ArcosLiga"] = {"Type": "MultiTrigger", "Triggers": arcs}
            comp["ArcosDesliga"] = {"Type": "MultiTrigger", "Triggers": ["ProjectileStartTrigger", "PerdeuOperacao"]}
            comp["ArcosLigados"] = {"Type": "TriggeredToggle", "OnTrigger": "ArcosLiga", "OffTrigger": "ArcosDesliga",
                                    "OperationalToggle": "IsOperational"}
            comp["ArcosCarga"] = {"Type": "ContinuousEffects", "OperationalToggle": "ArcosLigados",
                                  "Location": [1.5, 0.75], "MediaEffects": list(rfx.media("charge_arcs", "part"))}
    comp[comment("---- TRANCO: coroa + bochechas (substitui a weapon.png parada; nunca as duas) e o tambor ----")] = None
    comp["TrancoCoroa"] = tranco_graphics(meta, "weapon_tranco", "BulletEmitter")
    comp["TrancoTambor"] = tranco_graphics(meta, "tambor_tranco", "BulletEmitter")

    comp["OperationEffects"] = {"Type": "ToggleEffects", "Location": center, "Toggle": "IsOperational",
                                "ToggledOnMediaEffects": "&/COMMON_EFFECTS/PowerOn",
                                "ToggledOffMediaEffects": "&/COMMON_EFFECTS/PowerOff"}
    comp["ScorchedTrigger"] = {"Type": "ToggleTrigger", "Toggle": "ScorchedToggle", "TriggerWhenOn": False}
    comp["ScorchedEffects"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger", "Location": center,
                               "MediaEffects": "&/COMMON_EFFECTS/BigPartScorched"}
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "MediaEffects": "&/COMMON_EFFECTS/BigPartDestroyed",
                                "Location": center}
    comp["Indicators"] = _indicators(center, [
        _ind("ScorchedToggle", "&/INDICATORS/Scorched", hides=[1, 2]),
        _ind("CanosOk", "&/INDICATORS/MissingComponent", build=True),
        _ind("PowerToggle", "&/INDICATORS/PowerOff")])
    comp["Blueprints"] = blueprints(meta, w, h)
    part["Components : ^/0/Components"] = comp
    part["Stats"] = {"RecPower": "&../StatsByCategory/0/Stats/PowerPerSecond"}
    bp = "&~/Part/Components/BulletEmitter/Bullet"
    part["StatsByCategory"] = [{"NameKey": Q("StatCategories/BulletRailgun"), "Stats": {
        "DamagePerShot": f"{bp}/Components/DamagePool/Damage/BaseValue",
        "DamagePerSecond": "(&DamagePerShot) * (&ROF)",
        "Damage": ["&../DamagePerShot", "&../DamagePerSecond"],
        "Penetration": f"{bp}/Components/Hit/Penetration/BaseValue",
        "ROF": "1 / (&~/Part/Components/Weapon/FireInterval)",
        "RangeLimited": [f"{bp}/Range/BaseValue", f"{bp}/Range/MaxValue"],
        "Arc": 0,
        "ShotSpeed": f"{bp}/Speed/BaseValue",
        "ShotHP": f"{bp}/Components/Targetable/Health",
        "AmmoPerShot": "&~/Part/Components/BulletEmitter/ResourceUsage/0/ResourcesUsed",
        "AmmoPerSecond": "(&AmmoPerShot) * (&ROF)",
        "ShotAmmoUsage": ["&../AmmoPerShot", "&../AmmoPerSecond"],
        "PowerPerShot": "(&~/Part/Components/BulletEmitter/ResourceUsage/1/ResourcesUsed) / 1000",
        "PowerPerSecond": "(&PowerPerShot) * (&ROF)",
        "ShotPowerUsage": ["&../PowerPerShot", "&../PowerPerSecond"]}}]
    return {"Part : <./Data/ships/terran/base_large_part_terran.rules>/Part": part}


# ============================================================================= buffs
def buffs_top():
    """Tipos de buff proprios (padrao SW mod.rules:39-43; TK buffs/bs2t_buffs.rules). RailCount so na variante B."""
    rect = {"RectBorderColor": [255, 170, 60, 160], "RectFillColor": [255, 170, 60, 64]}
    top = {
        B_RAIL: {"CombineMode": "Add"},
        B_SHOT: {"CombineMode": "Add", "Exponent": SHOT_EXPONENT, "Multiplier": f"{int(round(SHOT_MULT * 100))}%",
                 "BaseValue": "100%", "MaxValue": SHOT_MAX, "IconTextFormatKey": Q("BuildBox/BuffPercentageFmt"),
                 "IconTextMultiply": 100, "IconTextAdd": -100, "ShowIconTextForZeroValue": False},
        B_OP: dict({"CombineMode": "Add"}, **rect),
        B_REV: dict({"CombineMode": "Add"}, **rect),
    }
    if power_mode() == "B":
        top[B_COUNT] = {"CombineMode": "Add"}
    return top


# ============================================================================= ganchos do build_mod
def shots(DATA):
    """O tiro da Tupa em DATA.SHOTS (kind 'slug_rail', dono bsgen.railgun; art_key/art_tier 'slug' para o
    caliber_fx.annotate resolver a arte de voo)."""
    if not DATA.RAIL_ENABLED:
        return
    if any(x.get("file") == SHOT_FILE for x in DATA.SHOTS):
        return
    DATA.SHOTS.append({"file": SHOT_FILE, "dir": SHOT_FILE, "id": SHOT_ID, "kind": "slug_rail",
                       "owner": "bsgen.railgun", "art_key": "slug", "art_tier": "slug", "ammo": "slug",
                       "title": "Dardo da railgun Tupã / Tupã railgun slug"})


def build_shot(out, s, header):
    if s.get("kind") != "slug_rail":
        return None
    rel = f"shots/{s.get('dir') or SHOT_FILE}/{s['file']}.rules"
    out.text(rel, render(build_slug(s), header + "\nProjetil: dardo da railgun Tupa (SPEC.railgun.shot)"))
    return rel


def write(out, header):
    if not _D().RAIL_ENABLED:
        return
    if sw("codex"):
        _warn("rail.codex = true: a pagina do codex da Tupa nao foi implementada nesta versao (nao testada em mod "
              "nenhum); nada escrito")
    out.text(BUFFS_FILE, render(buffs_top(), header + "\nBuffs proprios da railgun Tupa (SPEC.railgun.buffs). "
                                                      "Registrados por Overrides em <./Data/buffs/buffs.rules>."))


def mod_actions():
    if not _D().RAIL_ENABLED:
        return []
    return [{"Action": "Overrides", "OverrideIn": Q("<./Data/buffs/buffs.rules>"), "Overrides": f"&<{BUFFS_FILE}>"}]


def parts(out, D, ctx):
    D = _D()
    if not D.RAIL_ENABLED:
        return
    shot_rel = ctx["shot_rel"].get(SHOT_FILE)
    if shot_rel is None:
        ctx["warn"](f"Tupa pulada: tiro {SHOT_FILE} nao escrito")
        return
    for pid in (LOADER, BARREL, MUZZLE):
        short = SHORT[pid]
        meta = meta_of(short)
        walls = publish_art(out, short, meta, ctx)
        pdir = f"parts/{short}"
        if pid == LOADER:
            top = build_loader(meta, ctx, walls)
        elif pid == BARREL:
            top = build_barrel(meta, ctx, walls)
        else:
            top = build_muzzle(meta, ctx, walls, ctx["relpath"](pdir, shot_rel))
        info = D.PART_INFO.get(pid) or {}
        out.text(f"{pdir}/{short}.rules", render(top, ctx["header"] + f"\nPeca: {info.get('name_en', pid)} / "
                                                                      f"{info.get('name_pt', pid)}"))
        ctx["add_part"](pid)


# ============================================================================= textos
def _fmt(v, lang, dec=0):
    s = f"{v:,.{dec}f}"
    if lang == "pt":
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _pw(v, lang):
    """Energia na unidade da interface do jogo (interna / 1000: 500 -> 0,5; 15000 -> 15), como os Stats."""
    t = f"{v / 1000:g}"
    return t.replace(".", ",") if lang == "pt" else t


def _bonus_list(lang):
    """'1: +25 %, 2: +45 %, ...' (bonus m(N) - 1 por numero de canos, o que o acelerador vanilla mostra)."""
    pct = " %" if lang == "pt" else "%"
    return ", ".join(f"{k}: +{int(round(100 * (m_of(k) - 1)))}{pct}" for k in range(1, MAX_CANOS + 1))


def _table(lang):
    """Linhas por N da tabela do spec (dano por tiro, alcance, penetracao, velocidade, energia, impulso)."""
    rows = []
    for r in spec()["scaling_table"]:
        n = int(r["canos"])
        e = power_per_shot(n) / 1000
        imp = impulse_per_shot(n)
        if lang == "pt":
            ln = (f"{n} {'cano' if n == 1 else 'canos'}: {_fmt(r['pool_per_shot'], 'pt')} de dano, "
                  f"{_fmt(r['range_m'], 'pt')} m, pen. {_fmt(r['penetration'], 'pt', 1)}, "
                  f"{_fmt(r['speed_mps'], 'pt')} m/s, energia {_fmt(e, 'pt', 1)}")
            if imp:
                ln += f", tranco {_fmt(imp, 'pt')}"
        else:
            ln = (f"{n} {'barrel' if n == 1 else 'barrels'}: {_fmt(r['pool_per_shot'], 'en')} damage, "
                  f"{_fmt(r['range_m'], 'en')} m, pen. {_fmt(r['penetration'], 'en', 1)}, "
                  f"{_fmt(r['speed_mps'], 'en')} m/s, power {_fmt(e, 'en', 1)}")
            if imp:
                ln += f", kick {_fmt(imp, 'en')}"
        rows.append(ln)
    return rows


def _intake_text(lang):
    li = loader_intake()
    t = _D().transport()
    if li == "tripulacao":
        return ("A tripulação traz os projéteis e as baterias." if lang == "pt"
                else "The crew carry slugs and batteries to it.")
    if li == "acoplamento" or (li == "auto" and t == "tripulacao" and C.call(_intake(), "acoplamento_on")):
        return ("Um paiol de projéteis encostado logo atrás do canto traseiro esquerdo alimenta o carregador sozinho; "
                "a tripulação traz o resto e as baterias." if lang == "pt" else
                "A slug magazine docked right behind the rear-left corner feeds the loader by itself; the crew carry "
                "the rest and the batteries.")
    if li == "auto" and t == "teleporte":
        return ("Recebe projéteis pela Fita de Alimentação; a tripulação traz as baterias (e os projéteis abaixo da "
                "metade)." if lang == "pt" else
                "Gets slugs through the Ammo Feed Link; the crew carry the batteries (and slugs below half).")
    return ("A tripulação traz os projéteis e as baterias." if lang == "pt"
            else "The crew carry slugs and batteries to it.")


def strings(DATA=None):
    """Parts/BSRailLoader|Barrel|Muzzle (+Icon, Desc) em pt-BR e en (tooltip do ADDENDUM: canos, bonus, CP)."""
    D = _D()
    if not D.RAIL_ENABLED:
        return None
    rs = spec()["parts"]
    en = {"Parts": {}}
    pt = {"Parts": {}}
    pw = power_mode()
    bonus_lo, bonus_hi = int(round(100 * (m_of(1) - 1))), int(round(100 * (m_of(MAX_CANOS) - 1)))
    tag = "<string id='BSModTag'/>"
    # Carregador
    car = rs["carregador"]
    st = car["storages"]
    bat_pt, bat_en = _pw(st["LoaderBattery"]["MaxResources"], "pt"), _pw(st["LoaderBattery"]["MaxResources"], "en")
    en["Parts"][KEY[LOADER]] = car["name_en"]
    pt["Parts"][KEY[LOADER]] = car["name_ptbr"]
    en["Parts"][KEY[LOADER] + "Icon"] = "Tupã Loader"
    pt["Parts"][KEY[LOADER] + "Icon"] = "Carregador Tupã"
    pw_pt = (f"Cobra {_pw(POWER_PER_CANO, 'pt')} de energia por cano a cada tiro (mais {_pw(POWER_BASE, 'pt')} da "
             f"Ponta)." if pw == "B" else f"Cada tiro gasta {_pw(POWER_FIXO, 'pt')} de energia.")
    pw_en = (f"Charges {_pw(POWER_PER_CANO, 'en')} power per barrel each shot (plus {_pw(POWER_BASE, 'en')} from the "
             f"Muzzle)." if pw == "B" else f"Each shot uses {_pw(POWER_FIXO, 'en')} power.")
    pt["Parts"][KEY[LOADER] + "Desc"] = (
        f"Carregador 5x5 da railgun Tupã: 2 tripulantes, bateria de {bat_pt} e paiol interno de "
        f"{st['SlugMagazine']['MaxResources']} projéteis (+1 na câmara). Toda a energia e todos os projéteis da arma "
        f"entram por aqui. {pw_pt} {_intake_text('pt')}\n\nMonte: Carregador atrás, de 1 a 6 Canos no meio e a "
        f"Ponta na frente, alinhados pelo centro." + tag)
    en["Parts"][KEY[LOADER] + "Desc"] = (
        f"5x5 loader of the Tupã railgun: 2 crew, a battery of {bat_en} and an "
        f"internal magazine of {st['SlugMagazine']['MaxResources']} slugs (+1 in the chamber). All power and slugs "
        f"of the gun enter here. {pw_en} {_intake_text('en')}\n\nBuild: Loader at the back, 1 to 6 Barrels in the "
        f"middle and the Muzzle at the front, centered." + tag)
    # Cano
    cano = rs["cano"]
    en["Parts"][KEY[BARREL]] = cano["name_en"]
    pt["Parts"][KEY[BARREL]] = cano["name_ptbr"]
    en["Parts"][KEY[BARREL] + "Icon"] = "Tupã Barrel"
    pt["Parts"][KEY[BARREL] + "Icon"] = "Cano Tupã"
    extra_pt = f" e +{_pw(POWER_PER_CANO, 'pt')} de energia por tiro" if pw == "B" else ""
    extra_en = f" and +{_pw(POWER_PER_CANO, 'en')} power per shot" if pw == "B" else ""
    pt["Parts"][KEY[BARREL] + "Desc"] = (
        f"Cano blindado e selado da railgun Tupã (sem porta). Encadeie de 1 a 6 entre o Carregador e a Ponta. Cada "
        f"cano aumenta o dano, o alcance, a penetração e a velocidade do tiro (bônus +{bonus_lo} a +{bonus_hi} %)"
        f"{extra_pt}. Pontos de comando: {cano['command_points']}.\n\nBônus por número de canos: {_bonus_list('pt')}. "
        f"Com mais de {MAX_CANOS} canos a Ponta não dispara." + tag)
    en["Parts"][KEY[BARREL] + "Desc"] = (
        f"Armored, sealed barrel of the Tupã railgun (no doors). Chain 1 to 6 between the Loader and the Muzzle. Each "
        f"barrel raises shot damage, range, penetration and speed (bonus +{bonus_lo} to +{bonus_hi}%){extra_en}. "
        f"Command points: {cano['command_points']}.\n\nBonus by number of barrels: {_bonus_list('en')}. "
        f"With more than {MAX_CANOS} barrels the Muzzle does not fire." + tag)
    # Ponta
    pon = rs["ponta"]
    en["Parts"][KEY[MUZZLE]] = pon["name_en"]
    pt["Parts"][KEY[MUZZLE]] = pon["name_ptbr"]
    en["Parts"][KEY[MUZZLE] + "Icon"] = "Tupã Railgun"
    pt["Parts"][KEY[MUZZLE] + "Icon"] = "Railgun Tupã"
    lim = int(D.switch("rail.per_ship_limit"))
    tr = tranco_impulso()
    kick_pt = "" if tr == "off" else "; o disparo empurra a nave para trás (tranco)"
    kick_en = "" if tr == "off" else "; the shot kicks the ship backwards"
    pt["Parts"][KEY[MUZZLE] + "Desc"] = (
        "\"Tupã\" - railgun fixa e modular de fim de jogo: Carregador 5x5 + 1 a 6 Canos + Ponta. Carrega 1,0 s + "
        "0,25 s por cano antes de disparar; o dardo atravessa várias peças, drena a energia de cada peça perfurada, "
        f"pode incendiá-las e passa por cima da própria nave sem dano. Tremor na tela a cada tiro{kick_pt}.\n\n"
        f"Canos: N (1-6) | Bônus +{bonus_lo}..+{bonus_hi} % | Pontos de comando no total: 6 + 2N. Mais canos = mais "
        f"dano, alcance, penetração, velocidade e energia por tiro. Máximo {lim} por nave.\n\n"
        + "\n".join(_table("pt")) + tag)
    en["Parts"][KEY[MUZZLE] + "Desc"] = (
        "\"Tupã\" - fixed modular late-game railgun: 5x5 Loader + 1 to 6 Barrels + Muzzle. Charges 1.0 s + 0.25 s per "
        "barrel before firing; the slug pierces several parts, drains the power of every part it pierces, can set "
        f"them on fire and passes over its own ship harmlessly. Screen shake on every shot{kick_en}.\n\n"
        f"Barrels: N (1-6) | Bonus +{bonus_lo}..+{bonus_hi}% | Total command points: 6 + 2N. More barrels = more "
        f"damage, range, penetration, speed and power per shot. Max {lim} per ship.\n\n"
        + "\n".join(_table("en")) + tag)
    return en, pt


# ============================================================================= conferencia (selfcheck)
def _parse(path):
    import rules_lint as RL
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    root, errs, _w = RL.parse_text(text, RL.RFile("fs", path, path))
    return (root if not errs else None), text


def _ch(node, name):
    if node is None:
        return None
    return next((c for c in node.children if c.name == name), None)


def _val(node, name):
    c = _ch(node, name)
    return (c.value or "").strip().strip('"') if c is not None and c.kind == "value" else None


def _num(node, name):
    v = _val(node, name)
    try:
        return float(v.rstrip("d%")) if v is not None else None
    except ValueError:
        return None


def _items(node, name):
    c = _ch(node, name)
    return list(c.children) if c is not None and c.kind == "list" else []


def _comps(root):
    """{nome: no} dos componentes da Part (inclusive dentro de ToggledComponents)."""
    part = _ch(root, "Part")
    out = {}

    def walk(cn):
        for c in (cn.children if cn is not None else []):
            if not c.name or c.kind not in ("group", "inherit"):
                continue
            out[c.name] = c
            sub = _ch(c, "Components")
            if sub is not None and _val(c, "Type") == "ToggledComponents":
                walk(sub)
    walk(_ch(part, "Components"))
    return part, out


def _crit_entries(node):
    """Lista de PartCriteria/Criteria de um componente (forma simples ou lista)."""
    if _ch(node, "Criterias") is not None:
        return _items(node, "Criterias")
    if _ch(node, "ProxyableComponents") is not None:
        return [_ch(x, "PartCriteria") for x in _items(node, "ProxyableComponents")]
    for nm in ("Criteria", "PartCriteria"):
        if _ch(node, nm) is not None:
            return [_ch(node, nm)]
    return []


def _edges(crit):
    return {k: _num(crit, k) for k in ("Left", "Right", "Top", "Bottom") if _num(crit, k) is not None}


def _check_tranco(who, comps, names, want_trig, probs):
    for nm in names:
        g = comps.get(nm)
        if g is None:
            probs.append(f"{who}: sem a Graphics de tranco {nm}")
            continue
        if _val(g, "ResetAnimationTrigger") != want_trig:
            probs.append(f"{who}: {nm} ResetAnimationTrigger {_val(g, 'ResetAnimationTrigger')} (esperado {want_trig})")
        od = _ch(g, "OperationalDoodad")
        item = _items(od, "DamageLevels")[0] if _items(od, "DamageLevels") else None
        if item is None or _val(item, "AnimationStartTime") != "MinValue" or _val(item, "ClampAnimation") != "true":
            probs.append(f"{who}: {nm} sem AnimationStartTime MinValue + ClampAnimation true")
            continue
        files = [(x.value or "").strip().strip('"') for x in _items(item, "AnimationFiles")]
        if not files or not re.search(r"tranco1\.png$", files[-1]) or len(files) != 8:
            probs.append(f"{who}: {nm} quadros {files[:2]}..{files[-1:]} (8 quadros, o ultimo = repouso X1)")
        nod = _ch(g, "NonOperationalDoodad")
        rest = _items(nod, "DamageLevels")
        if not rest or not (_val(rest[0], "File") or "").endswith("tranco1.png"):
            probs.append(f"{who}: {nm} NonOperationalDoodad diferente do repouso X1")


def _check_single_pulse(who, comps, proxy, probs):
    """PROVA do pulso unico pelo arquivo gerado: o gatilho do ResetAnimationTrigger e o TriggerProxy do
    EmissionTriggered (proxy) ou um MultiTrigger com UMA entrada que e esse TriggerProxy (relay); nenhum Timer chega
    num ResetAnimationTrigger (o Timer com TriggerWhenStarted dispara no inicio E na expiracao = 2 coices)."""
    p = comps.get(proxy)
    if p is None or _val(p, "Type") != "TriggerProxy" or _val(p, "ComponentID") != "EmissionTriggered":
        probs.append(f"{who}: {proxy} nao e o TriggerProxy do EmissionTriggered da ponta")
    for nm, c in comps.items():
        if _val(c, "Type") == "Timer" and (nm == "TrancoRelay" or _val(c, "TriggerWhenStarted") == "true"):
            probs.append(f"{who}: Timer {nm} (TriggerWhenStarted/TrancoRelay) - pulso duplo proibido")
    for nm, c in comps.items():
        trig = _val(c, "ResetAnimationTrigger")
        if not trig:
            continue
        t = comps.get(trig)
        if t is None:
            probs.append(f"{who}: {nm} ResetAnimationTrigger {trig} nao existe")
            continue
        ty = _val(t, "Type")
        if ty == "Timer":
            probs.append(f"{who}: {nm} reiniciado por Timer {trig} (pulso duplo)")
        if nm.startswith("Tranco"):
            if tranco_gatilho() == "relay":
                entries = [(x.value or "").strip() for x in _items(t, "Triggers")]
                if ty != "MultiTrigger" or entries != [proxy]:
                    probs.append(f"{who}: {nm} relay {trig} = {ty} {entries} (esperado MultiTrigger [{proxy}])")
            elif trig != proxy:
                probs.append(f"{who}: {nm} (tranco_gatilho = proxy) usa {trig}, esperado {proxy}")


def selfcheck(mod_dir, SPEC=None):
    D = _D()
    probs = []
    pdir = os.path.join(mod_dir, "parts")
    files = {pid: os.path.join(pdir, SHORT[pid], f"{SHORT[pid]}.rules") for pid in SHORT}
    shot_p = os.path.join(mod_dir, "shots", SHOT_FILE, f"{SHOT_FILE}.rules")
    buffs_p = os.path.join(mod_dir, BUFFS_FILE)
    if not D.RAIL_ENABLED:
        for p in list(files.values()) + [shot_p, buffs_p]:
            if os.path.exists(p):
                probs.append(f"rail.enabled = false e {os.path.relpath(p, mod_dir)} foi escrito")
        if os.path.isdir(pdir) and any(d.startswith("bs_rail_") for d in os.listdir(pdir)):
            probs.append("rail.enabled = false com pasta parts/bs_rail_*")
        mr = os.path.join(mod_dir, "mod.rules")
        if os.path.isfile(mr):
            with open(mr, encoding="utf-8") as fh:
                t = fh.read()
            for bad in ("bs_rail_", "bs_slug_rail", "bs_factory_slug", BUFFS_FILE):
                if bad in t:
                    probs.append(f"rail.enabled = false e mod.rules cita {bad}")
        return probs
    pw = power_mode()
    # ---- tabela m(N) / numeros por N contra SPEC.railgun.scaling_table
    n = shot_numbers()
    for r in spec()["scaling_table"]:
        N = int(r["canos"])
        m = m_of(N)
        chk = [("mult", m, 0.0006), ("pool_per_shot", n["pool"] * m, 1.01), ("penetration", n["pen"] * m, 0.06),
               ("range_m", min(n["range"] * m, n["range_max"]), 1.01), ("speed_mps", n["speed"] * m, 1.01),
               ("cp", 6 + 2 * N, 0.01), ("impulse_per_shot", TRANCO_IMPULSE * m, 1.01),
               ("per_part_damage_fallback_r2", R2_PER_PART * m, 1.01)]
        if pw == "B":
            chk.append(("power_per_shot", POWER_BASE + POWER_PER_CANO * N, 0.01))
        for key, got, tol in chk:
            if key in r and abs(float(r[key]) - got) > tol:
                probs.append(f"tabela N={N}: {key} spec {r[key]} x calculado {got:.4f}")
    cps = {LOADER: spec()["parts"]["carregador"]["command_points"], BARREL: spec()["parts"]["cano"]["command_points"],
           MUZZLE: spec()["parts"]["ponta"]["command_points"]}
    if cps[LOADER] + cps[MUZZLE] != 6 or cps[BARREL] != 2:
        probs.append(f"CP {cps} nao dao 6 + 2N")
    # ---- buffs
    broot, btext = _parse(buffs_p)
    if broot is None:
        probs.append(f"{BUFFS_FILE} ausente ou ilegivel")
    else:
        want = [B_RAIL, B_SHOT, B_OP, B_REV] + ([B_COUNT] if pw == "B" else [])
        have = [c.name for c in broot.children if c.name]
        if sorted(have) != sorted(want):
            probs.append(f"{BUFFS_FILE}: buffs {have}, esperado {want}")
        sh = _ch(broot, B_SHOT)
        if _num(sh, "Exponent") != SHOT_EXPONENT or _val(sh, "Multiplier") != "25%" or _num(sh, "MaxValue") != SHOT_MAX:
            probs.append(f"{B_SHOT}: Exponent/Multiplier/MaxValue fora do spec")
    # ---- pecas
    roots = {}
    for pid, p in files.items():
        root, text = _parse(p)
        if root is None:
            probs.append(f"{os.path.relpath(p, mod_dir)} ausente ou ilegivel")
            continue
        roots[pid] = (root, text) + _comps(root)
    if len(roots) != 3:
        return probs
    rl, tl, partl, cl = roots[LOADER]
    rb, tb, partb, cb = roots[BARREL]
    rm, tm, partm, cm = roots[MUZZLE]
    # carregador 5x5
    size = [int(float((x.value or "0"))) for x in _items(partl, "Size")]
    if size != [5, 5] or _num(partl, "MaxHealth") != 33000:
        probs.append(f"carregador Size {size} MaxHealth {_num(partl, 'MaxHealth')} (esperado [5,5] / 33000)")
    for pid, (root, text, part, comps) in roots.items():
        cc = comps.get("CommandConsumer")
        if _num(cc, "CommandPoints") != cps[pid]:
            probs.append(f"{SHORT[pid]}: CommandPoints {_num(cc, 'CommandPoints')} (spec {cps[pid]})")
        # Stats/RailgunBuffFmt vanilla formata {0}..{29}: com outro numero de valores o tooltip estoura
        for m in re.finditer(r"\bRailgunBuff\s*=\s*\[([^\]]*)\]", text):
            nv = len([x for x in m.group(1).split(",") if x.strip()])
            if nv != 30:
                probs.append(f"{SHORT[pid]}: stat RailgunBuff com {nv} valores (o formato vanilla pede 30)")
    # cano: criterio para tras com as 2 entradas (cano de tras OU carregador 5x5)
    back = ["LoadedSlug", "LoaderBattery", "ReverseBuffOperationProvider"] + (["ContagemProvider"] if pw == "B" else [])
    for nm in back:
        c = cb.get(nm)
        ents = _crit_entries(c) if c is not None else []
        eds = [(_val(e, "Category"), _edges(e), bool(_ch(e, "IDs"))) for e in ents]
        ok = len(ents) == 2 and eds[0][1] == {"Left": 0, "Right": 3, "Top": 3} and eds[0][0] == CAT_MUN and \
            eds[1][1] == {"Left": -1, "Right": 4, "Top": 3} and eds[1][2]
        if not ok:
            probs.append(f"cano {nm}: entradas para tras {eds} (esperado o cano de tras E o carregador 5x5)")
    if pw != "B" and any(B_COUNT in t for t in (tl, tb, tm)):
        probs.append(f"power_mode {pw} com {B_COUNT} nas pecas")
    # carregador: corrente para a frente nas arestas do 5x5
    for nm in ("RailBuffProvider", "OperationBuffProvider", "WeaponTrigger", "ProjectileStartTrigger", "EmitTrigger"):
        c = cl.get(nm)
        ents = _crit_entries(c) if c is not None else []
        if len(ents) != 1 or _edges(ents[0]) != {"Left": 1, "Right": 4, "Bottom": 0}:
            probs.append(f"carregador {nm}: criterio para a frente fora de {{Left 1; Right 4; Bottom 0}}")
    # energia
    pe = _ch(cm.get("BulletEmitter"), "ResourceUsage")
    used = [_num(x, "ResourcesUsed") for x in (pe.children if pe is not None else [])]
    want_pw = POWER_FIXO if pw == "fixo" else POWER_BASE
    if used != [SLUG_PER_SHOT, want_pw]:
        probs.append(f"ponta ResourceUsage {used} (esperado [{SLUG_PER_SHOT}, {want_pw}])")
    if (pw == "B") != ("DrenoB" in cl) or (pw == "B") != ("ContagemInicio" in cm):
        probs.append(f"power_mode {pw}: DrenoB/ContagemInicio fora da variante")
    if pw == "B" and f"Scale = -{POWER_PER_CANO}" not in tl:
        probs.append("DrenoB sem Scale -500")
    # ponta: arma, tranco fisico e passagem sobre a propria nave
    wpn = cm.get("Weapon")
    if _val(wpn, "IgnoreFriendlyShipLowLOSChecks") != "true" or _val(wpn, "IgnoreFriendlyShipHighLOSChecks") != "true":
        probs.append("ponta: Weapon sem IgnoreFriendlyShipLowLOSChecks/IgnoreFriendlyShipHighLOSChecks = true")
    if _val(wpn, "IgnoreSourceShipLOSChecks") is not None or _val(wpn, "IgnoreSourceShipLowLOSChecks") is not None:
        probs.append("ponta: Weapon com IgnoreSourceShip*LOSChecks (nome do SW, nao existe no 0.30.4c)")
    if _num(wpn, "FireInterval") != FIRE_INTERVAL:
        probs.append(f"ponta: FireInterval {_num(wpn, 'FireInterval')}")
    ok_ = cm.get("CanosOk")
    if _num(ok_, "MinBuffValue") != 1 or _num(ok_, "MaxBuffValue") != MAX_CANOS:
        probs.append("ponta: CanosOk fora de 1..6")
    if "bs_limit_railgun" not in [(x.value or "").strip() for x in _items(partm, "TypeCategories")]:
        probs.append("ponta sem a categoria bs_limit_railgun")
    # todo TriggeredEffects da ponta com um Impulse nos HitEffects (o tranco tem de ser UM so)
    imps = [nm for nm, c in cm.items() if _val(c, "Type") == "TriggeredEffects" and
            any(_val(x, "Type") == "Impulse" for x in _items(c, "HitEffects"))]
    tr = tranco_impulso()
    if tr == "impulso":
        if imps != ["TrancoImpulso"]:
            probs.append(f"ponta: {imps} (esperado exatamente 1 TrancoImpulso)")
        ti = cm.get("TrancoImpulso")
        if ti is not None and (_val(ti, "ChainedTo") or _val(ti, "Trigger") != "BulletEmitter"):
            probs.append("TrancoImpulso tem de ser Trigger = BulletEmitter, sem ChainedTo")
    elif imps:
        probs.append(f"tranco_impulso {tr} com TrancoImpulso")
    if (tr == "recoil") != (_ch(cm.get("BulletEmitter"), "Recoil") is not None):
        probs.append(f"tranco_impulso {tr}: Recoil do BulletEmitter fora da variante")
    for pid, (root, text, part, comps) in roots.items():
        if "RecoilProjectile" in comps or "RecoilTimer" in comps:
            probs.append(f"{SHORT[pid]}: RecoilProjectile/RecoilTimer (empurrao de 1/30 s) proibido")
        for nm, c in comps.items():
            if _val(c, "Type") == "Timer":
                dur = _ch(c, "Duration")
                if dur is not None and dur.kind == "value" and (dur.value or "").replace(" ", "") in ("1/30", "0.0333"):
                    probs.append(f"{SHORT[pid]}: Timer {nm} de 1/30 s")
            if _val(c, "ChainedTo") == "Projectile" and _ch(c, "HitEffects") is not None:
                probs.append(f"{SHORT[pid]}: {nm} com HitEffects preso ao Projectile (Interpolate: desync)")
    if "/BASE_SHAKE" not in (tm or "") or f"ShakeAmount = {SHAKE[0]:g}" not in tm:
        probs.append("ponta: FireEffect sem BASE_SHAKE 0.2 / 0.7")
    # quadros do tranco e pulso unico
    _check_tranco("carregador", cl, ["TrancoCulatra"], "TrancoRelay" if tranco_gatilho() == "relay" else "EmitTrigger",
                  probs)
    _check_tranco("cano", cb, ["TrancoTambores"],
                  "TrancoRelay" if tranco_gatilho() == "relay" else "EmissionTriggered", probs)
    _check_tranco("ponta", cm, ["TrancoCoroa", "TrancoTambor"], "BulletEmitter", probs)
    _check_single_pulse("carregador", cl, "EmitTrigger", probs)
    _check_single_pulse("cano", cb, "EmissionTriggered", probs)
    if '"weapon.png"' in (tm or ""):
        probs.append("ponta: weapon.png desenhada junto com weapon_tranco (coroa dobrada)")
    # carga
    cw = charge_wave()
    has_wave = any(nm.startswith("CanoSobe_") for nm in cb)
    if (cw == "atraso") != has_wave:
        probs.append(f"charge_wave {cw}: onda de carga {'ausente' if not has_wave else 'presente'} no cano")
    # logistica do carregador (rail.loader_intake)
    li = loader_intake()
    fe = "FitaEntra_slug" in cl
    pa = cl.get("PaiolAcoplado_0")
    if li == "tripulacao" and (fe or pa is not None):
        probs.append("loader_intake tripulacao com Fita/acoplamento no carregador")
    if li == "acoplamento":
        if pa is None or [float(x.value) for x in _items(pa, "PartLocation")] != [float(v) for v in ACOPLA_CELL] or fe:
            probs.append(f"loader_intake acoplamento: PaiolAcoplado_0 em {ACOPLA_CELL} e sem Fita")
    if li == "auto" and D.transport() == "teleporte" and not fe:
        probs.append("loader_intake auto + teleporte sem FitaEntra_slug -> SlugMagazine")
    # tiro
    sroot, stext = _parse(shot_p)
    if sroot is None:
        probs.append(f"shots/{SHOT_FILE} ausente ou ilegivel")
    else:
        hit = _ch(_ch(sroot, "Components"), "Hit")
        if _val(hit, "FriendlyShipLowCollisions") != "false" or _val(hit, "FriendlyShipHighCollisions") != "false":
            probs.append("tiro sem OWN_SHIP_PASS (FriendlyShipLow/HighCollisions false) no PenetratingHit")
        fin = _ch(hit, "FinishedPenetratingOperational")
        r2 = bool(sw("r2_fallback"))
        if r2 != (fin is not None and fin.kind == "value"):
            probs.append(f"r2_fallback {r2}: FinishedPenetratingOperational fora da variante")
        for bad in ("StructuralDamageRetentionPerHit", "MinStructuralDamageScale", "STRUCTURAL_DAMAGE_RETENTION"):
            if bad in stext:
                probs.append(f"tiro com campo 0.30.5 {bad}")
        if sw("overload_rider") != ("AreaShieldStatusApplication" in stext):
            probs.append("overload_rider fora da variante")
    # cores: nada violeta / ouro-branco nos arquivos do rail (o rail_fx confere os dele)
    R = C.content_module("bsgen.rail_fx")
    if R is not None:
        for pid, (root, text, part, comps) in roots.items():
            probs += R.color_problems(f"parts/{SHORT[pid]}", text)
        if stext:
            probs += R.color_problems(f"shots/{SHOT_FILE}", stext)
    return probs
