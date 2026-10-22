"""Linha PEM do Bullet Strike 2.0 (dono: WP08; modulo de CONTEUDO, API 2): Tuvira, Treme-Treme e a pesada (Corisco).

Fonte: SPEC.pem_weapons (tools/spec/bullet_strike_spec.json) com as transformacoes do bs_data (d) pem.tuvira_cp,
(d2) pem.tuvira_mount e pem.heavy_name ja aplicadas em DATA.PEM; os NOMES vem do spec (name_ptbr/name_en/codename e
overclock.name_*), nunca fixos aqui. Tres canhoes cineticos que disparam granadas PEM (Celula PEM da F3, modo PEM;
nao existe mais municao PEM para os canhoes comuns) e drenam a BATERIA do escudo atingido (ResourceDrain com
TreatShieldAsPart, o par dos ions do SW:ACD), com pouco dano no casco:
  * Tuvira (bs_pem_light, 1x2): pem.tuvira_mount = torre -> TurretWeapon 270 graus a 180 graus/s, 2 canos juntos a
    cada 1,3889 s, MagStorage_0 22 / limiar 11; fixa -> 30 graus, 0,8333 s, 36 / 18 (nome historico do spec);
    1 celula = 4 granadas (Splitter_0 1 -> 4); CommandPoints = pem.tuvira_cp;
  * Treme-Treme (bs_pem_medium, 2x2): torre 300 graus, 1 cano a cada 1,92 s, 1 celula por granada, overclock so de
    cadencia (x1,5);
  * pesada (bs_pem_heavy, 4x4, codinome do spec: Corisco com pem.heavy_name = Corisco): torre dupla 270 graus, canos
    alternados (1,03 s), 1 celula por granada; overclock = troca de projetil para bs_shot_pem_heavy_oc (alcance 650,
    velocidade 300, PenetratesOperational, blindagem 60 %, dreno 3400 na hora + cosmoteer.disruptor_drain 10 s x
    1,36 no escudo e em toda peca com energia atravessada); arcos de carga entre os canos e o brilho charge_glow1..4
    (art3d/bs_pem_heavy, pem.charge_glow) nos 0,5 s antes de cada disparo.

Ganchos (tools/build_mod.py):
  shots(DATA)                  poe em DATA.SHOTS os 3 tiros + o do overclock da pesada (kind 'pem', owner bsgen.pem,
                               art_key pem_s / pem_m / pem_l, art_tier 'pem'; a arte de voo vem do caliber_fx);
  build_shot(out, s, header)   escreve shots/<id>/<id>.rules (SHOT_KINDS = ('pem',): o build_mod nao conhece o kind);
  parts(out, DATA, ctx)        escreve parts/<id>/<id>.rules pelo guns.build_gun (dicts no formato dele, sem seletor)
                               + estatisticas do disruptor vanilla (ShieldDamage, PowerDrain, ...) + carga da pesada;
  strings(DATA)                textos en / pt-br das 3 pecas, do overclock e do seletor de celula;
  selfcheck(mod_dir, SPEC)     drenos, danos, penetracao, estoques, IDs, nomes e CP contra o spec.
Tambem: build_pem(p, shot_paths, ctx=None) (check_art3d chama com o meta da arte).

Tiros (SPEC.pem_weapons.weapons[].shot): PenetratingHit 3 / 8 / 30, PenetratesOperational false, Targetable
1300 / 2600 / 5000 (bullet); HitShield = ResourceDrain {battery; 1100 / 4400 / 6800; TreatShieldAsPart} + Damage
250 / 1000 / 1000 (+ AreaShieldStatusApplication cosmoteer.shield_overload SO com pem.overload_rider = true; safe =
false); HitOperational = ResourceDrain 750 / 3000 / 6300 + Damage 150 / 250 / 400 (+ disruptor_drain no Treme-Treme e
na pesada) + Impulse; HitStructural 100 / 150 / 250; Penetrating*/Finished* vazios. Sem campos so do 0.30.5
(StructuralDamageRetentionPerHit / MinStructuralDamageScale / CommandRoomDrainOverTime) e sem &/SW_*.
Logistica pelo seam do WP05 (bsgen.intake: Fita, acoplamento [0,2] / [0,2] / [1,4]) e cook-off por enchimento do
MagStorage_0: ExplosiveResourceDrain 30000 r6 / 60000 r8 / 120000 r10 (8 fatias) + ExplosiveDamage 1500 / 3000 / 6000.
Efeitos: bsgen.pem_fx (FX, BS_FX_EXT=0 desliga: entao so os efeitos vanilla do disruptor) e a arte de voo do
bsgen.caliber_fx (sem ele: brilho procedural).
"""

import os
import re

from rules_dsl import Q, Inh, comment, render
from bsgen import common as C
from bsgen import fxkit as FXK
from bsgen import guns as G

API = 2
SHOT_KINDS = ("pem",)

TIER = {"bs_pem_light": "s", "bs_pem_medium": "m", "bs_pem_heavy": "l"}
ART_KEY = {"s": "pem_s", "m": "pem_m", "l": "pem_l"}
SHIELD_PER_BATTERY = 0.4    # literal do spec (tooltip_stats: ShieldTuner do SW / ResourceDrainPerDamage vanilla)
SPREAD = {"s": 1.5, "m": 1.0, "l": 0.75}         # meio-angulo (graus; escolha WP08, o spec nao fixa)
RECOIL = {"s": 4, "m": 6, "l": 10}               # BulletEmitter.Recoil (regra do guns: dano / 40)
HALO = {"s": [2.5, 1.25], "m": [3.2, 1.6], "l": [4.0, 2.0]}     # halo de espaco (spec: <= 4 x 2 tiles)
CORE = {"s": [0.5, 0.25], "m": [0.7, 0.32], "l": [0.9, 0.38]}  # nucleo aditivo (spec: pem_s [0,5; 0,25])
SHEATH = [1.6, 0.7]          # bainha da pem_l (bs_pem_sheath.png, 12 qps)
TAIL = [4.0, 0.6]            # cauda da pem_l (bs_pem_trail.png, 30 qps, StartTime 0,02)
HULL_MES = {"s": 0.8, "m": 1.2, "l": 1.8}        # hull_hit escalado (spec)
SHIELD_MES = {"s": 0.2, "m": 0.3, "l": 0.45}     # shield_hit (o choque do missil PEM vanilla tem ~26 tiles)
CHARGE_S = 0.5               # carga da pesada antes de cada disparo (spec)
WHITE_HOT = [255, 250, 235]

DS = "./Data/shots"
SND_IMPACT = [f"{DS}/disruptor_bolt/sounds/disruptor_impact_0{i}.wav" for i in (1, 2, 3, 4)]
SND_DRAIN = [f"{DS}/disruptor_bolt/sounds/disruptor_discharge_0{i}.wav" for i in (1, 2, 3, 4)]
DT = "./Data/ships/terran/disruptor"
SND_SHOT = [f"{DT}/sounds/disruptor_shot_0{i}.wav" for i in (1, 2, 3, 4)]
SND_SHOT_OC = [f"{DT}/sounds/disruptor_overclocked_shot_0{i}.wav" for i in (1, 2, 3, 4)]
SND_CHARGE = [f"{DT}/sounds/disruptor_reload_0{i}.wav" for i in (1, 2, 3)]
P_HULL = [f"{DS}/disruptor_bolt/particles/disruptor_bolt_hit_orb.rules",
          f"{DS}/disruptor_bolt/particles/disruptor_bolt_hit_bolts.rules",
          f"{DS}/disruptor_bolt/particles/disruptor_bolt_flash.rules"]
P_HULL_FAST = [P_HULL[0], P_HULL[2]]             # Tuvira: sem os 30-40 raios do hit_bolts (spec EMP_FAST)
P_SHIELD = [f"{DS}/missile_emp/particles/missile_emp_hit_orb.rules",
            f"{DS}/missile_emp/particles/missile_emp_hit_shockwave.rules"]
P_SHIELD_HEAVY = [f"{DS}/missile_emp/particles/missile_emp_lightning.rules"]
P_STRUCT = [f"{DS}/disruptor_bolt/particles/disruptor_bolt_hit_struct_lightning.rules"]
P_DRAIN = [f"{DS}/disruptor_bolt/particles/ship_drain.rules"]
P_SIZZLE_VANILLA = f"{DS}/disruptor_bolt/particles/disruptor_bolt_hit_sizzle.rules"
P_MUZZLE_VANILLA = [f"{DT}/particles/disruptor_shoot_flash.rules", f"{DT}/particles/disruptor_shoot_lightning.rules"]


# ============================================================================= modulos opcionais
def _fx_on():
    return os.environ.get("BS_FX_EXT", "1") != "0"


def _pfx():
    """bsgen.pem_fx (efeitos proprios, FX) ou None (BS_FX_EXT=0 / ausente: so os efeitos vanilla do disruptor)."""
    return C.content_module("bsgen.pem_fx") if _fx_on() else None


def _cfx():
    """bsgen.caliber_fx (arte de voo de art3d/bs_shells2, copiada por ele) ou None (brilho procedural)."""
    return C.content_module("bsgen.caliber_fx") if _fx_on() else None


def _D():
    import bs_data as D
    return D


def _short(pid):
    return pid.split(".", 1)[1]


def _val(v):
    return {"BaseValue": v, "EffectScaleExponent": 1}


def _int(v, what):
    """Campo Int32 do jogo (ResourceDrain.Amount, Penetration, Health, ...): numero inteiro ou o build para."""
    f = float(v)
    if abs(f - round(f)) > 1e-9:
        raise ValueError(f"bsgen.pem: {what} = {v} nao e inteiro (campo Int32 derruba o carregamento)")
    return int(round(f))


def _effects(lst, typ):
    return [e for e in (lst or []) if isinstance(e, dict) and e.get("Type") == typ]


def _base(e, key):
    v = e.get(key)
    return v.get("BaseValue") if isinstance(v, dict) else v


# ============================================================================= tiros (dados)
def _tier(p):
    return TIER[p["short"] if "short" in p else _short(p["id"])]


def _shot_dict(D, p):
    """Tiro normal da arma p (D.PEM) a partir de SPEC.pem_weapons.weapons[].shot (+ o bloco 'pem' para conferir)."""
    t = _tier(p)
    sh = p["shot"]
    hit = sh["Hit"]
    hs = hit["HitShield"]["HitEffects"]
    ho = hit["HitOperational"]["HitEffects"]
    hst = hit["HitStructural"]["HitEffects"]
    sid = _short(sh["id"])
    drain_s = _effects(hs, "ResourceDrain")[0]
    dmg_s = _effects(hs, "Damage")[0]
    drain_o = _effects(ho, "ResourceDrain")[0]
    dmg_o = _effects(ho, "Damage")[0]
    imp = _effects(ho, "Impulse")
    st = _effects(ho, "StatusApplication")
    ov = _effects(hs, "AreaShieldStatusApplication")
    s = {"kind": "pem", "file": sid, "dir": sid, "id": sh["id"], "owner": "bsgen.pem",
         "title": f"{p['name_en']} - EMP", "gun": p["short"], "index": 0, "key": "pem", "ammo": "pem",
         "tier": t, "art_key": ART_KEY[t], "art_tier": "pem", "oc": False, "res": p["ammo_resource"],
         "range": sh["Range"], "ideal": list(sh.get("IdealRange") or [round(0.3 * sh["Range"]), sh["Range"]]),
         "speed": sh["Speed"], "radius": sh["Physics"]["Radius"], "targetable": True,
         "health": _int(sh["Targetable"]["Health"], f"{sid} Targetable.Health"),
         "target_category": sh["Targetable"].get("TargetCategory") or "bullet",
         "penetration": _int(hit["Penetration"], f"{sid} Penetration"), "pen_speed": hit.get("PenetrationSpeed", 25),
         "penetrates_operational": bool(hit.get("PenetratesOperational", False)),
         "shield_drain": _int(_base(drain_s, "Amount"), f"{sid} HitShield ResourceDrain"),
         "shield_damage": _int(_base(dmg_s, "Damage"), f"{sid} HitShield Damage"),
         "part_drain": _int(_base(drain_o, "Amount"), f"{sid} HitOperational ResourceDrain"),
         "damage": _int(_base(dmg_o, "Damage"), f"{sid} HitOperational Damage"),
         "impulse": _base(imp[0], "Impulse") if imp else 5,
         "struct_damage": _int(_base(_effects(hst, "Damage")[0], "Damage"), f"{sid} HitStructural Damage"),
         "drain_status": ({"duration": st[0]["StatusDuration"], "value": _base(st[0], "StatusValue")} if st else None),
         "overload": None, "spec2": p}
    if ov and D.switch("pem.overload_rider"):
        o = ov[0]
        s["overload"] = {k: o[k] for k in ("Radius", "StatusDuration", "StatusValue", "MaxStatusValue",
                                           "UseMaxValuesForHitShield") if k in o}
    s["shield_hp"] = round(s["shield_drain"] / SHIELD_PER_BATTERY + s["shield_damage"])
    return s


def _oc_shot_dict(D, p, base):
    """Tiro do overclock da pesada (SPEC.pem_weapons.heavy_overclock_shot): troca de emissor."""
    oc = D.SPEC["pem_weapons"]["heavy_overclock_shot"]
    hit = oc["Hit"]
    hs = hit["HitShield"]
    st = _effects(hs, "StatusApplication")[0]
    pen = hit["PenetratingOperational"]
    m = re.search(r"ResourceDrain\s+(\d+)", str(hit.get("HitOperational") or ""))
    if not m:
        raise ValueError("bsgen.pem: SPEC.pem_weapons.heavy_overclock_shot.Hit.HitOperational sem 'ResourceDrain <n>'")
    af = str((hit.get("PartCategoryPenetrationFactors") or {}).get("armor") or "100%").rstrip("%")
    sid = _short(oc["id"])
    s = dict(base)
    s.update({"file": sid, "dir": sid, "id": oc["id"], "oc": True, "title": f"{p['name_en']} - EMP (overclock)",
              "range": oc["Range"], "ideal": [round(0.3 * oc["Range"]), oc["Range"]], "speed": oc["Speed"],
              "health": _int(oc["Targetable.Health"], f"{sid} Targetable.Health"),
              "penetration": _int(hit["Penetration"], f"{sid} Penetration"),
              "penetrates_operational": bool(hit["PenetratesOperational"]), "armor_factor": float(af) / 100,
              "shield_drain": _int(_base(_effects(hs, "ResourceDrain")[0], "Amount"), f"{sid} HitShield ResourceDrain"),
              "shield_damage": _int(_base(_effects(hs, "Damage")[0], "Damage"), f"{sid} HitShield Damage"),
              "part_drain": _int(m.group(1), f"{sid} HitOperational ResourceDrain"),
              "damage": _int(_base(_effects(pen, "Damage")[0], "Damage"), f"{sid} Damage"),
              "lingering": {"duration": st["StatusDuration"], "value": _base(st, "StatusValue")},
              "drain_status": None, "overload": None, "spec2": oc})
    s["shield_hp"] = round(s["shield_drain"] / SHIELD_PER_BATTERY + s["shield_damage"])
    return s


def shot_dicts(D, p):
    """[tiro normal (+ overclock da pesada)] da arma p."""
    base = _shot_dict(D, p)
    out = [base]
    if _tier(p) == "l" and p.get("overclock"):
        out.append(_oc_shot_dict(D, p, base))
    return out


def shots(DATA):
    """Gancho: os tiros PEM entram em DATA.SHOTS (idempotente)."""
    have = {s["file"] for s in DATA.SHOTS}
    for p in DATA.PEM:
        for s in shot_dicts(DATA, p):
            if s["file"] not in have:
                DATA.SHOTS.append(s)
                have.add(s["file"])


# ============================================================================= tiros (regras)
def _sound(lst, volume, max_conc, speed_var=0.15):
    return Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(x) for x in lst], "Volume": volume,
                                               "SpeedVariation": speed_var, "MaxConcurrent": max_conc})


def _refs(paths):
    return [f"&<{x}>" for x in paths]


def _drain_media(t):
    """MediaEffectsOnDrain (sem MediaEffectsOnDrainFactor: so existe no ExplosiveResourceDrain): ship_drain vanilla +
    chiado ciano proprio + descarga."""
    pfx = _pfx()
    sz = pfx.sizzle_ref("shot") if pfx else P_SIZZLE_VANILLA
    return _refs(P_DRAIN + [sz]) + [_sound(SND_DRAIN, {"s": 0.5, "m": 0.7, "l": 0.9}[t], 8)]


def _hull_media(t):
    lst = P_HULL_FAST if t == "s" else P_HULL
    media = _refs(lst) + [_sound(SND_IMPACT, {"s": 0.6, "m": 0.8, "l": 1.0}[t], {"s": 16, "m": 12, "l": 8}[t])]
    if t == "l":
        media.append(Inh("/BASE_SHAKE", {"ShakeAmount": 0.05, "Duration": 0.3}))
    return media


def _shield_media(t):
    pfx = _pfx()
    lst = list(P_SHIELD) + (P_SHIELD_HEAVY if t == "l" else [])
    media = _refs(lst)
    if pfx:
        media += _refs([pfx.ring_ref(t, "shot")])
    return media + [_sound(SND_IMPACT, {"s": 0.5, "m": 0.7, "l": 0.9}[t], {"s": 16, "m": 12, "l": 8}[t])]


def _struct_media(t):
    return _refs(P_STRUCT) + [_sound(SND_IMPACT, 0.4, 8)]


def _pop_media(s):
    """Abatida no ar: SO o estouro ciano pequeno (pem_fizzle), nunca o preset do acerto."""
    pfx = _pfx()
    if pfx:
        return _refs([pfx.fizzle_ref("shot")])
    cfx = _cfx()
    r = C.call(cfx, "pop_effect", "pem") if cfx else None
    return list(r) if r else _refs([P_HULL[2]])


def _drain(amount, shield, t):
    e = {"Type": "ResourceDrain", "ResourceType": "battery", "Amount": _val(_int(amount, "ResourceDrain.Amount"))}
    if shield:
        e["TreatShieldAsPart"] = True
    e["MediaEffectsOnDrain"] = _drain_media(t)
    return e


def _status(duration, value):
    return {"Type": "StatusApplication", "StatusType": "cosmoteer.disruptor_drain", "StatusDuration": duration,
            "StatusValue": _val(value)}


def _overload(o):
    e = {"Type": "AreaShieldStatusApplication", "StatusType": "cosmoteer.shield_overload"}
    e.update(o)
    return e


def _visual(s):
    """Visual em voo: corpo da arte (art3d/bs_shells2 pem_s/m/l, pelo caliber_fx) por baixo das camadas aditivas
    (nucleo ciano; na pem_l nucleo branco-quente + bainha bs_pem_sheath + cauda bs_pem_trail), halo de espaco +
    luz de casco (fxkit.light_pair: palette.pem.hull, refl 6) e o crepitar ciano (pem_fx)."""
    t = s["tier"]
    key = s["art_key"]
    pal = FXK.pal("pem")
    cfx = _cfx()
    comps = {}
    body = s.get("art_body")
    if cfx:
        body = cfx.art_body(key)
        comps.update(cfx.art_components(key, bucket_body="BulletUpper2", bucket_lights="BulletUpper4"))
    if not body:
        import json
        with open(FXK.ART2_PATH, encoding="utf-8") as fh:
            body = json.load(fh)["art_assets"]["shell_ladder"]["items"][key]["in_game_body"]
    L, W = float(body[0]), float(body[1])
    if "Sprite" not in comps:
        # sem a arte de voo (BS_FX_EXT=0): capsula aditiva procedural
        comps["Sprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper2", "Offset": [0, 0],
                           "Sprite": {"Texture": {"File": Q(FXK.BLOB), "MipLevels": "max", "SampleMode": "Linear"},
                                      "Size": [round(L * 1.3, 3), round(W * 1.6, 3)], "VertexColor": list(pal["glow"]),
                                      "TargetBlendMode": "Add"}}
    cl, cw = CORE[t]
    core_col = WHITE_HOT if t == "l" else [int(round(v * 0.6)) for v in pal["band"]]
    comps["CoreSprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper3", "Offset": [0, 0],
                           "Sprite": {"Texture": {"File": Q(FXK.BLOB), "MipLevels": "max", "SampleMode": "Linear"},
                                      "Size": [cl, cw], "VertexColor": core_col, "TargetBlendMode": "Add"}}
    if t == "l":
        tex = "../bs_fx_tex/"    # fx_tex.ref(nome, 'shot') (fx_tex e de CONTEUDO: existe tambem com BS_FX_EXT=0)
        comps["SheathSprite"] = {
            "Type": "AnimatedSprite", "RenderBucket": "BulletUpper3", "Offset": [0, 0],
            "Animation": {"AtlasSprite": {"Texture": {"File": Q(tex + "bs_pem_sheath.png"), "MipLevels": "max",
                                                      "SampleMode": "Linear"},
                                          "Size": list(SHEATH), "TargetBlendMode": "Add"},
                          "FrameCount": 4, "FrameSize": [256, 96], "FramesPerRow": 2, "FramesPerSecond": 12}}
        # cauda: a borda direita (cabeca do raio) fica logo atras da base da granada; StartTime: nao aparece por
        # cima da propria torre no quadro do disparo (receita da cauda do plasma_fx)
        comps["TailSprite"] = {
            "Type": "AnimatedSprite", "RenderBucket": "BulletUpper2", "StartTime": 0.02,
            "Offset": [round(-0.5 * L + 0.1 - TAIL[0] / 2, 3), 0],
            "Animation": {"AtlasSprite": {"Texture": {"File": Q(tex + "bs_pem_trail.png"), "MipLevels": "max",
                                                      "SampleMode": "Linear"},
                                          "Size": list(TAIL), "TargetBlendMode": "Add"},
                          "FrameCount": 8, "FrameSize": [512, 64], "FramesPerRow": 2, "FramesPerSecond": 30}}
    comps.update(FXK.light_pair(HALO[t], pal["glow"], [round(1.2 * L, 3), 0.6], None, s.get("start"),
                                FXK.UNLIT_SHELL, key="pem", legacy_unlit=0.125))
    pfx = _pfx()
    if pfx:
        comps["Crackle"] = {"Type": "MediaEffects", "MediaEffects": _refs([pfx.crackle_ref(t, "shot")])}
    return comps


def build_pem_shot(s):
    """Arquivo do tiro PEM (dict para o rules_dsl.render)."""
    t = s["tier"]
    oc = bool(s.get("oc"))
    top = {
        "STAT_DAMAGE": s["damage"],
        "STAT_PENETRATION": s["penetration"],
        "STAT_SHIELD_DRAIN": s["shield_drain"],
        "STAT_SHIELD_DAMAGE": s["shield_damage"],
        "STAT_SHIELD_HP": s["shield_hp"],
        "STAT_PART_DRAIN": s["part_drain"],
    }
    if oc:
        ln = s["lingering"]
        top["DRAIN_DURATION"] = ln["duration"]
        top["DRAIN_PER_SECOND"] = round(ln["value"] * 1000, 3)
        top["TOTAL_DRAIN"] = round(ln["value"] * 1000 * ln["duration"], 3)
        top["SHIELD_DRAIN_PER_SECOND"] = round(ln["value"] * 1000 / SHIELD_PER_BATTERY, 3)
        top["TOTAL_SHIELD_DAMAGE"] = round(ln["value"] * 1000 * ln["duration"] / SHIELD_PER_BATTERY, 3)
        top["ARMOR_PENETRATION_FACTOR"] = s["armor_factor"]
    top.update({"ID": Q(s["id"]), "Range": s["range"], "IdealRange": list(s["ideal"]), "IdealRadius": [5, 50],
                "Speed": s["speed"]})
    shield_fx = [_drain(s["shield_drain"], True, t), {"Type": "Damage", "Damage": _val(s["shield_damage"])}]
    if oc:
        ln = s["lingering"]
        shield_fx.append(_status(ln["duration"], ln["value"]))
    if s.get("overload"):
        shield_fx.append(_overload(s["overload"]))
    hit_shield = {"ReduceEffectsByPenetration": True, "Offset": [-0.15, 0], "HitEffects": shield_fx,
                  "MediaEffects": _shield_media(t), "MediaEffectsScale": SHIELD_MES[t]}
    op_fx = [_drain(s["part_drain"], False, t)]
    if oc:
        ln = s["lingering"]
        op_fx.append(_status(ln["duration"], ln["value"]))
    op_fx.append({"Type": "Damage", "Damage": _val(s["damage"])})
    if s.get("drain_status"):
        op_fx.append(_status(s["drain_status"]["duration"], s["drain_status"]["value"]))
    op_fx.append({"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))})
    hit_op = {"ReduceEffectsByPenetration": True, "Offset": [-0.15, 0], "HitEffects": op_fx,
              "MediaEffects": _hull_media(t), "MediaEffectsScale": HULL_MES[t]}
    hit_struct = {"ReduceEffectsByPenetration": True, "Offset": [0.15, 0],
                  "HitEffects": [{"Type": "Damage", "Damage": _val(s["struct_damage"])}],
                  "MediaEffects": _struct_media(t)}
    hit = {"Type": "PenetratingHit", "Penetration": s["penetration"], "PenetrationSpeed": s.get("pen_speed", 25),
           "PenetratesOperational": bool(s["penetrates_operational"])}
    if oc and s.get("armor_factor") is not None and abs(s["armor_factor"] - 1) > 1e-9:
        hit["PartCategoryPenetrationFactors"] = {"armor": f"{int(round(s['armor_factor'] * 100))}%"}
    from bsgen import shots as SH    # import tardio (shots importa os modulos FX)
    hit.update(SH.OWN_SHIP_PASS)
    hit.update({"CrewCollisions": "{Enemies=true; Junk=true}", "PenetratesCrew": True, "HitCrew": "&HitOperational"})
    hit["HitShield"] = hit_shield
    hit["HitOperational"] = hit_op
    hit["HitStructural"] = hit_struct
    if oc:
        # cada peca com energia atravessada: dreno que fica (disruptor_drain) + dano; midia leve (so o chiado)
        ln = s["lingering"]
        pfx = _pfx()
        pen_media = _refs([pfx.sizzle_ref("shot") if pfx else P_SIZZLE_VANILLA])
        hit["PenetratingOperational"] = {"ReduceEffectsByPenetration": True,
                                         "HitEffects": [_status(ln["duration"], ln["value"]),
                                                        {"Type": "Damage", "Damage": _val(s["damage"])}],
                                         "MediaEffects": pen_media}
        hit["PenetratingStructural"] = {}
        hit["FinishedPenetratingOperational"] = "&PenetratingOperational"
        hit["FinishedPenetratingStructural"] = {}
    else:
        hit["PenetratingOperational"] = {}
        hit["PenetratingStructural"] = {}
        hit["FinishedPenetratingOperational"] = {}
        hit["FinishedPenetratingStructural"] = {}
    comps = {"Physics": {"Type": "CirclePhysics", "Radius": s["radius"], "Density": 0.0001},
             "Death": {"Type": "DeathByLifetime"},
             "Targetable": {"Type": "Targetable", "Health": s["health"], "TargetCategory": Q(s["target_category"]),
                            "OnDeath": {"MediaEffects": _pop_media(s)}},
             "Hit": hit}
    comps.update(_visual(s))
    top["Components"] = comps
    return top


def build_shot(out, s, header):
    """SHOT_KINDS 'pem': escreve shots/<dir>/<file>.rules e devolve o caminho (None = nao e meu)."""
    if s.get("kind") != "pem":
        return None
    rel = f"shots/{s['dir']}/{s['file']}.rules"
    if s.get("start") is None:
        s["start"] = _start(s)
    out.text(rel, render(build_pem_shot(s), header + f"\nProjetil PEM: {s['title']}"))
    return rel


def _start(s):
    """StartTime das luzes (fxkit.start_time pelo raio da torre do meta da arma)."""
    D = _D()
    p = next((x for x in D.PEM if x["short"] == s.get("gun")), None)
    meta = (p or {}).get("art3d") or {}
    r = (meta.get("turret_size") or max((p or {}).get("size") or [1, 1])) / 2
    return FXK.start_time(r, s.get("speed") or 0)


# ============================================================================= pecas
def _fire_fx(t, oc):
    """Boca da arma (g['fx'] do guns.build_gun): clarao cobre + arcos ciano + luz (pem_fx) e o tiro do disruptor."""
    pfx = _pfx()
    parts = pfx.muzzle_refs(t, "part") if pfx else list(P_MUZZLE_VANILLA)
    fx = {"particles": parts, "sound": list(SND_SHOT), "volume": {"s": 0.55, "m": 0.75, "l": 0.95}[t],
          "max_concurrent": {"s": 20, "m": 12, "l": 8}[t], "shake": {"s": 0, "m": 0.02, "l": 0.06}[t],
          "shake_time": 0.4, "offset": 0}
    if oc:
        fx["sound_oc"] = list(SND_SHOT_OC)
        fx["particles_oc"] = list(parts)
    return fx


def cookoff_hits(p):
    """Cook-off de UM MagStorage_0 cheio (guns.cookoff_effects escala pelo enchimento): a celula PEM descarrega
    (ExplosiveResourceDrain do spec) e quase nao explode (ExplosiveDamage pequeno)."""
    ck = p.get("cookoff_cap") or {}
    dr = ck.get("ExplosiveResourceDrain") or {}
    ex = ck.get("ExplosiveDamage") or {}
    hits = []
    if dr:
        hits.append({"Type": "ExplosiveResourceDrain", "ResourceType": dr.get("ResourceType", "battery"),
                     "TotalDrain": _val(_int(dr["TotalDrain"], "cook-off TotalDrain")), "Radius": dr["Radius"],
                     "Slices": _int(dr.get("Slices", 8), "cook-off Slices"), "Delay": 0.05,
                     "Filter": {"Ships": True, "Shields": True, "Friendlies": True},
                     "MediaEffectsOnDrainFactor": 0.00025,
                     "MediaEffectsOnDrain": [
                         f"&<{DS}/missile_emp/particles/missile_emp_hit_sizzle.rules>",
                         f"&<{DS}/missile_emp/particles/missile_emp_lightning.rules>",
                         f"&<{DS}/missile_emp/particles/missile_emp_drain.rules>",
                         _sound(SND_DRAIN, 1, 4, 0.2)]})
    if ex:
        hits.append({"Type": "ExplosiveDamage", "TotalDamage": _val(_int(ex["TotalDamage"], "cook-off TotalDamage")),
                     "Radius": ex["Radius"], "Delay": 0.05, "Filter": {"Friendlies": True}})
    return hits


def gun_dict(p):
    """Dict no formato do guns.build_gun (sem seletor) para a arma PEM p (entrada de D.PEM, ja transformada)."""
    D = _D()
    s = p["short"] if "short" in p else _short(p["id"])
    t = TIER[s]
    shots_ = shot_dicts(D, p)
    base = shots_[0]
    oc = p.get("overclock")
    isto = p["internal_storage"]
    split = 4 if (p.get("ammo_accounting") or {}).get("splitter") else 1
    m = re.search(r"ToQuantity\s+(\d+)", str((p.get("ammo_accounting") or {}).get("splitter") or ""))
    if m:
        split = int(m.group(1))
    storage = _int(isto["MaxResources"], f"{s} MagStorage_0")
    mode = {"index": 0, "mode": 0, "key": "pem", "ammo": "pem", "res": p["ammo_resource"],
            "internal_storage_units": storage, "storage": storage, "resupply_threshold": C.half(storage),
            "splitter_to_quantity": split, "shots_per_unit": split, "resources_used_per_shot": 1,
            "units_per_shot": 1, "shot": base["file"], "shot_oc": shots_[-1]["file"] if oc else base["file"],
            "show_pen": True, "oc_range": False, "shot_targetable": True, "names": C.index_names(0, "pem"),
            "spec2": isto}
    nb = int(p.get("barrels") or 1)
    pattern = {"synchronized_2": "volley", "alternate_2": "alternate"}.get(p.get("fire_pattern"), "single")
    spt = int(p.get("shots_per_trigger") or (nb if pattern == "volley" else 1))
    meta = p.get("art3d")
    g = {
        "id": p["id"], "short": s, "key": p["key"], "kind": "pem", "name_en": p["name_en"],
        "name_pt": p.get("name_pt") or p["name_ptbr"], "codename": p.get("codename", ""), "tier": p["tier"],
        "size": list(p["size"]), "crew": int(p["crew"]), "cp": _int(p["command_points"], f"{s} CommandPoints"),
        "hp": _int(p["max_health"], f"{s} MaxHealth"), "cost": p["build_cost"], "ring": 1,
        "arc": int(round(float(p["firing_arc_deg"]))), "rotate": int(round(float(p.get("rotate_speed_deg_s") or 180))),
        "threshold": 4 if p["tier"] == "early" else 2, "fire_interval": round(float(p["trigger_interval_s"]), 4),
        "spread": SPREAD[t], "recoil": RECOIL[t], "modes": [mode], "selector": False, "available_choices": [],
        "barrels": {"count": nb, "spacing": {"s": 0.3, "m": 0.3, "l": 1.0}[t], "pattern": pattern,
                    "width": {"s": 0.12, "m": 0.2, "l": 0.34}[t], "len_factor": {"s": 0.75, "m": 0.85, "l": 1.0}[t]},
        "burst": None, "shots_per_trigger": spt, "fx": _fire_fx(t, bool(oc)),
        "art": dict(p.get("art") or {"style": "plasma", "barrel": "fins", "accent": "emp"}), "art_tier": "pem",
        "art3d_dir": p.get("art3d_dir") or s, "art3d": meta, "hybrid": False, "desc": "",
        "cookoff_hits": cookoff_hits(p), "cookoff_cap": None, "belt": p.get("belt"), "logistica": p.get("logistica"),
        "extra_categories": list(p.get("extra_categories") or []), "spec": p, "spec2": p,
        "pem_tier": t, "pem_shots": shots_,
    }
    if meta and meta.get("crew_pos"):
        g["crew_pos"] = [tuple(c) for c in meta["crew_pos"]]
    if oc:
        fr = float(oc.get("fire_rate_factor") or 1)
        g["oc"] = {"fire_interval_factor": round(1 / fr, 4), "half_spread": round(SPREAD[t] * 1.25, 3),
                   "recoil_factor": 1.6, "heat_per_shot": oc["heat_per_shot"],
                   "heat_per_second": oc.get("heat_per_second", 0), "name_en": oc.get("name_en", ""),
                   "name_pt": oc.get("name_ptbr", ""), "spec2": oc}
    return g


def _em(g, oc_state):
    if g.get("oc"):
        return f"&~/Part/Components/Fire_0_{'OC' if oc_state else 'N'}/Components/TargetEmitter"
    return "&~/Part/Components/TargetEmitter"


def _fi_path(g):
    base = "&~/Part/Components/Turret/FireInterval"
    return f"{base}/BaseValue" if g.get("oc") else base


def _spt(g):
    return g["barrels"]["count"] if g["barrels"]["pattern"] == "volley" else 1


def _stats(g, oc_state):
    """Linhas do disruptor vanilla (disruptor.rules 0.30.2 l.796-822, sem CommandRoomDrainOverTime): ShieldDamage =
    dreno do escudo / 0,4 + dano no escudo, PowerDrain, Damage, ShieldPenetration, ... + consumo de celulas."""
    em = _em(g, oc_state)
    fi = _fi_path(g)
    if oc_state:
        fi = f"({fi}) * (&~/OVERCLOCK/FIRE_INTERVAL_FACTOR)"
    hs = f"{em}/Bullet/Components/Hit/HitShield/HitEffects"
    ho = f"{em}/Bullet/Components/Hit/HitOperational/HitEffects"
    st = {
        "ShotsPerSecond": f"{_spt(g)} / ({fi})",
        "ROF": "&ShotsPerSecond",
        "ShieldDamagePerShot": f"({hs}/0/Amount/BaseValue) / {SHIELD_PER_BATTERY} + ({hs}/1/Damage/BaseValue)",
        "ShieldDamagePerSecond": "(&ShieldDamagePerShot) * (&ShotsPerSecond)",
        "ShieldDamage": ["&../ShieldDamagePerShot", "&../ShieldDamagePerSecond"],
        "PowerDrainPerShot": f"({ho}/0/Amount/BaseValue) / 1000",
        "PowerDrainPerSecond": "(&PowerDrainPerShot) * (&ShotsPerSecond)",
        "PowerDrain": ["&../PowerDrainPerShot", "&../PowerDrainPerSecond"],
        "DamagePerShot": f"{em}/Bullet/STAT_DAMAGE",
        "DamagePerSecond": "(&DamagePerShot) * (&ShotsPerSecond)",
        "Damage": ["&../DamagePerShot", "&../DamagePerSecond"],
        "ShieldPenetration": f"{em}/Bullet/Components/Hit/Penetration",
        "Range": f"{em}/Bullet/Range",
        "ShotSpeed": f"{em}/Bullet/Speed",
    }
    if not oc_state:
        st.update({
            "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
            "Spread": f"deg({em}/Spread/1)",
            "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
            "ShotHP": f"{em}/Bullet/Components/Targetable/Health",
            "AmmoPerShot": f"({em}/ResourcesUsed) / (&~/Part/Components/Splitter_0/ToQuantity)",
            "AmmoPerSecond": "(&AmmoPerShot) * (&ShotsPerSecond)",
            "ShotAmmoUsage": ["&../AmmoPerShot", "&../AmmoPerSecond"],
        })
    else:
        st.update({"Spread": "deg(&~/OVERCLOCK/HALF_SPREAD)", "HeatPerShot": "(&~/OVERCLOCK/HEAT_PER_SHOT)",
                   "HeatGeneration": "(&~/OVERCLOCK/HEAT_PER_SECOND)"})
    return st


def _tooltips(g, part):
    """StatsByCategory (granada PEM) e, com overclock, a SecondaryToolTip (Treme-Treme: so cadencia; pesada: o tiro
    do overclock + 'Disrupcao do overclock' do disruptor vanilla com PowerDrainOverTime / ShieldDamageOverTime /
    EffectDuration e Features [PenetratesOperational])."""
    part["StatsByCategory"] = [{"NameKey": Q("StatCategories/BSAmmo_pem"), "Stats": _stats(g, False)}]
    if not g.get("oc"):
        part.pop("SecondaryToolTip", None)
        return
    oc_st = _stats(g, True)
    cats = [{"NameKey": Q("StatCategories/BSAmmo_pem"), "Stats": oc_st}]
    if g["pem_tier"] == "l":
        em = _em(g, True)
        oc_st["Penetration"] = f"{em}/Bullet/Components/Hit/Penetration"
        oc_st["ArmorPenetrationResistance"] = f"({em}/Bullet/ARMOR_PENETRATION_FACTOR) * 100"
        cats[0]["Features"] = ["PenetratesOperational"]
        b = f"{em}/Bullet"
        cats.append({"NameKey": Q("StatCategories/OverclockedDisruption"), "Stats": {
            "PowerDrainOverTime": [f"({b}/TOTAL_DRAIN) / 1000", f"({b}/DRAIN_PER_SECOND) / 1000"],
            "ShieldDamageOverTime": [f"{b}/TOTAL_SHIELD_DAMAGE", f"{b}/SHIELD_DRAIN_PER_SECOND"],
            "EffectDuration": f"{b}/DRAIN_DURATION"}})
    part["SecondaryToolTip"] = {"TitleKey": Q("StatCategories/Overclocked"),
                                "DescriptionKey": Q(f"Parts/{g['key']}OverclockDesc"), "StatsByCategory": cats}


def _charge(comp, g, geo):
    """Pesada: carga de 0,5 s antes de cada disparo (CHARGE_S) - arcos entre os canos (pem_fx) e o brilho
    charge_glow1..4 do meta (pem.charge_glow), som de carga do disruptor. Timers do jogo base (padrao do
    IsFiringTimer do chaingun): EsperaCarga (expira CHARGE_S antes do proximo disparo) e DisparandoRecente (o canhao
    esta atirando); Carregando = os dois + IsOperational + AmmoPrereq."""
    D = _D()
    fi = float(g["fire_interval"]) * float((g.get("oc") or {}).get("fire_interval_factor") or 1)
    wait = round(max(0.05, min(float(g["fire_interval"]), fi) - CHARGE_S), 4)
    pfx = _pfx()
    meta = g.get("art3d") or {}
    cg = (meta.get("turret") or {}).get("charge_glow") if meta else None
    glow = bool(cg) and bool(D.switch("pem.charge_glow"))
    if not pfx and not glow:
        return
    comp[comment("---- carga da pesada: 0,5 s antes de cada disparo (arcos entre os canos + charge_glow) ----")] = None
    comp["EsperaCarga"] = {"Type": "Timer", "Duration": wait, "StartTrigger": "Turret", "ResetTrigger": "Turret",
                           "StartExpired": True}
    comp["DisparandoRecente"] = {"Type": "Timer", "Duration": round(max(fi, float(g["fire_interval"])) * 1.25, 4),
                                 "StartTrigger": "Turret", "ResetTrigger": "Turret", "StartExpired": True,
                                 "InvertToggle": True}
    comp["Carregando"] = {"Type": "MultiToggle", "Mode": "All",
                          "Toggles": ["IsOperational", "AmmoPrereq", "DisparandoRecente", "EsperaCarga"]}
    comp["ComecaCarga"] = {"Type": "ToggleTrigger", "Toggle": "Carregando", "TriggerWhenOn": True,
                           "TriggerWhenOff": False}
    comp["SomCarga"] = {"Type": "TriggeredEffects", "ChainedTo": "Turret", "Trigger": "ComecaCarga",
                        "Location": [round(geo["front"], 3), 0],
                        "MediaEffects": [_sound(SND_CHARGE, 0.6, 4)]}
    if pfx:
        x = round((geo["front"] + geo["muzzle"]) / 2, 3)
        for i, r in enumerate(pfx.charge_refs("part")):
            comp[f"ChargeArcs{i + 1}"] = {"Type": "ContinuousEffects", "ChainedTo": "Turret", "Location": [x, 0],
                                          "OperationalToggle": "Carregando", "MediaEffects": [f"&<{r}>"]}
    if glow:
        ts = geo["turret_size"]
        comp["ChargeGlowGraphics"] = {
            "Type": "Graphics", "ChainedTo": "Turret", "Location": [0, 0], "Rotation": "90d",
            "OperationalToggle": "Carregando", "ResetAnimationTrigger": "ComecaCarga",
            "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [{
                "AnimationFiles": [Q(f) for f in cg["frames"]], "Size": [ts, ts],
                "AnimationInterval": float(cg.get("interval") or 0.125), "AnimationStartTime": "MinValue",
                "ClampAnimation": True}]}}


def _ai_rating(g):
    """AIFirepowerRating como o disruptor vanilla (600 para 4500 escudo/s): escudo/s da granada / 7,5."""
    s0 = g["pem_shots"][0]
    sps = _spt(g) / float(g["fire_interval"])
    return int(round(s0["shield_hp"] * sps / 7.5))


def build_pem(p, shot_paths, ctx=None):
    """(top, info) da arma PEM p (entrada de D.PEM; check_art3d passa dict(pem, art3d=meta) e shot_paths de mentira):
    guns.build_gun com os dicts PEM + estatisticas do disruptor + carga da pesada. info['g'] = o dict usado."""
    g = gun_dict(p)
    top, info = G.build_gun(g, shot_paths, ctx)
    key = next(k for k in top if k.startswith("Part : "))
    part = top[key]
    comp = part["Components : ^/0/Components"]
    comp["Turret"]["AIFirepowerRating"] = _ai_rating(g)
    _tooltips(g, part)
    if g["pem_tier"] == "l":
        _charge(comp, g, info["geo"])
        # os componentes de grafico da carga ficam por ultimo (por cima dos canos, meta layer 'above_barrels'): o
        # IndicatorSprites e a planta continuam no fim
        for k in ("Indicators", "Blueprints"):
            if k in comp:
                comp[k] = comp.pop(k)
    info["g"] = g
    return top, info


def parts(out, D, ctx):
    """Gancho: escreve as 3 pecas PEM (parts/<curto>/<curto>.rules) com os tiros ja escritos (ctx['shot_rel'])."""
    for p in D.PEM:
        s = p["short"]
        pdir = f"parts/{s}"
        files = [x["file"] for x in shot_dicts(D, p)]
        missing = [f for f in files if f not in ctx["shot_rel"]]
        if missing:
            ctx["warn"](f"peca {p['id']} pulada: tiros nao escritos {missing}")
            continue
        sp = {(0, False): ctx["relpath"](pdir, ctx["shot_rel"][files[0]]),
              (0, True): ctx["relpath"](pdir, ctx["shot_rel"][files[-1]])}
        top, info = build_pem(p, sp, ctx)
        g = info["g"]
        code = f" \"{g['codename']}\"" if g.get("codename") else ""
        out.text(f"{pdir}/{s}.rules", render(top, ctx["header"] + f"\nArma PEM: {g['name_en']} / {g['name_pt']}{code}"))
        G.write_art(out, pdir, g, info, ctx)
        ctx["add_part"](p["id"])


# ============================================================================= textos
def _fmt(n, lang):
    s = f"{int(round(n)):,}"
    return s.replace(",", ".") if lang == "pt" else s


def _num(x, lang):
    """Numero curto para texto (10 -> '10', 2.5 -> '2,5' em pt)."""
    s = f"{float(x):g}"
    return s.replace(".", ",") if lang == "pt" else s


def _oc_linger(D, p):
    """(base, oc, bateria total, escudo total) do dreno que fica do tiro do overclock da pesada - a mesma conta do
    TOTAL_DRAIN / TOTAL_SHIELD_DAMAGE do tiro (StatusValue*1000*StatusDuration; escudo = bateria / 0.4)."""
    base = _shot_dict(D, p)
    ocs = _oc_shot_dict(D, p, base)
    ln = ocs["lingering"]
    bat = float(ln["value"]) * 1000 * float(ln["duration"])
    return base, ocs, bat, bat / SHIELD_PER_BATTERY


def _oc_desc(p, lang):
    oc = p.get("overclock") or {}
    name = oc.get("name_en" if lang == "en" else "name_ptbr") or ""
    if _tier(p) != "l":
        from bs_strings import oc_text
        return oc_text(oc, lang)
    D = _D()
    base, ocs, bat, shp = _oc_linger(D, p)
    rf = int(round(((oc.get("range_factor") or 1) - 1) * 100))
    vf = int(round(((oc.get("speed_factor") or 1) - 1) * 100))
    arm = int(round(float(ocs.get("armor_factor") or 1) * 100))
    dur = _num(ocs["lingering"]["duration"], lang)
    rng = ocs["range"]
    frac = float(ocs["shield_drain"]) / float(base["shield_drain"]) if base["shield_drain"] else 1.0
    pct = int(round(frac * 100))
    if lang == "en":
        inst = ("only half the usual amount" if abs(frac - 0.5) < 0.005 else
                f"{'only ' if frac < 1 else ''}{pct}% of the usual amount")
        return (f"\"{name}\": +{rf}% range ({rng} m) and +{vf}% shell speed. The shell punches through parts "
                f"(armor counts {arm}%), drains {inst} on impact, then another {_fmt(bat, 'en')} battery "
                f"({_fmt(shp, 'en')} shield HP) over {dur} s from the shield and from every powered part it crosses. "
                f"Produces waste heat when firing.")
    inst = ("só metade do normal" if abs(frac - 0.5) < 0.005 else
            f"{'só ' if frac < 1 else ''}{pct}% do normal")
    return (f"\"{name}\": +{rf}% de alcance ({rng} m) e +{vf}% de velocidade da granada. A granada atravessa as peças "
            f"(a blindagem conta {arm}%), drena na hora {inst} e deixa um dreno de mais {_fmt(bat, 'pt')} de bateria "
            f"({_fmt(shp, 'pt')} de escudo) por {dur} s no escudo e em toda peça com energia que cruzar. Produz calor "
            f"ao disparar.")


def _desc(p, lang):
    t = _tier(p)
    D = _D()
    s0 = _shot_dict(D, p)
    cells = int((p.get("internal_storage") or {}).get("MaxResources") or 0)
    per_cell = 4 if t == "s" else 1
    crew = int(p["crew"])
    code = p.get("codename") or ""
    tier_en = {"early": "Early-game", "mid": "Mid-game", "late": "Late-game"}[p["tier"]]
    tier_pt = {"early": "Início de jogo", "mid": "Meio de jogo", "late": "Fim de jogo"}[p["tier"]]
    arc = int(round(float(p["firing_arc_deg"])))
    if lang == "en":
        mount = {"s": (f"Light {arc}° turret with two short copper-coiled barrels firing together." if arc > 30 else
                       "Low bow mount with two short copper-coiled barrels firing together."),
                 "m": "Squat turret with one thick barrel ringed by three copper coils.",
                 "l": "Big armored twin turret: two long barrels in glowing coil stacks; arcs jump between them "
                      "just before each shot."}[t]
        body = (f"{mount} Fires EMP shells that drain the BATTERY of the shield they hit (about "
                f"{_fmt(s0['shield_hp'], 'en')} shield HP per shell) and barely scratch the hull: a shield breaker.")
        if s0.get("drain_status"):
            body += " On a part, it also keeps draining powered systems for a few seconds."
        extra = (f"\n\n{tier_en} EMP deck weapon. Range {s0['range']} m. Needs no power: {crew} crew and EMP Cells "
                 f"(1 cell = {per_cell} shell{'s' if per_cell > 1 else ''}; holds {cells}). Bullet Strike guns run on "
                 f"ammo, so EMP does not silence them; it hits shields, reactors and power-fed weapons.")
        if p.get("overclock"):
            extra += " Can be overclocked."
        return f"{body} \"{code}\"{extra}<string id='BSModTag'/>"
    mount = {"s": (f"Torre leve de {arc}° com dois canos curtos envoltos em bobinas de cobre, disparando juntos."
                   if arc > 30 else
                   "Reparo baixo de proa com dois canos curtos envoltos em bobinas de cobre, disparando juntos."),
             "m": "Torre atarracada de um cano grosso cercado por três bobinas de cobre.",
             "l": "Grande torre dupla blindada: dois canos longos em pilhas de bobinas acesas; raios saltam entre eles "
                  "logo antes de cada disparo."}[t]
    body = (f"{mount} Dispara granadas PEM que drenam a BATERIA do escudo atingido (cerca de "
            f"{_fmt(s0['shield_hp'], 'pt')} de escudo por granada) e mal arranham o casco: um quebra-escudos.")
    if s0.get("drain_status"):
        body += " Numa peça, ainda continua drenando os sistemas com energia por alguns segundos."
    extra = (f"\n\n{tier_pt} - arma de convés PEM. Alcance {s0['range']} m. Não usa energia: {crew} "
             f"tripulante{'s' if crew > 1 else ''} e Células PEM (1 célula = {per_cell} granada"
             f"{'s' if per_cell > 1 else ''}; guarda {cells}). As armas do Bullet Strike usam munição, então o PEM não "
             f"as desliga; ele derruba escudos, reatores e armas de energia.")
    if p.get("overclock"):
        extra += " Aceita overclock."
    return f"{body} \"{code}\"{extra}<string id='BSModTag'/>"


def strings(DATA):
    """(en, pt): Parts/<chave>(Icon|Desc|Overclock|OverclockDesc) das 3 armas, o texto da tech do overclock da
    pesada (descricao completa do dreno) e o seletor de celula / recurso com os codinomes do spec."""
    en = {"Parts": {}, "BSTechs": {}, "PartToggles": {}}
    pt = {"Parts": {}, "BSTechs": {}, "PartToggles": {}}
    for p in DATA.PEM:
        k = p["key"]
        code = p.get("codename") or ""
        en["Parts"][k] = p["name_en"]
        pt["Parts"][k] = p.get("name_pt") or p["name_ptbr"]
        en["Parts"][k + "Icon"] = (code or p["name_en"])[:18]
        pt["Parts"][k + "Icon"] = (code or p["name_ptbr"])[:18]
        en["Parts"][k + "Desc"] = _desc(p, "en")
        pt["Parts"][k + "Desc"] = _desc(p, "pt")
        if p.get("overclock"):
            en["Parts"][k + "Overclock"] = f"Overclocked {p['name_en']}"
            pt["Parts"][k + "Overclock"] = f"{p.get('name_pt') or p['name_ptbr']} (Overclocking)"
            en["Parts"][k + "OverclockDesc"] = _oc_desc(p, "en")
            pt["Parts"][k + "OverclockDesc"] = _oc_desc(p, "pt")
            if _tier(p) == "l":
                tk = DATA.tech_string_key(p["id"] + "-overclock")
                bk = DATA.tech_string_key(p["id"]) + "_BBOC"
                for kk in (tk, bk):
                    en["BSTechs"][kk + "Desc"] = _oc_desc(p, "en")
                    pt["BSTechs"][kk + "Desc"] = _oc_desc(p, "pt")
    codes = [p.get("codename") for p in DATA.PEM if p.get("codename")]
    if codes:
        names = ", ".join(codes[:-1]) + (" e " if len(codes) > 1 else "") + codes[-1]
        names_en = ", ".join(codes[:-1]) + (" and " if len(codes) > 1 else "") + codes[-1]
        d_en = f"EMP Cells for the EMP cannon line ({names_en}): shield breakers."
        d_pt = f"Células PEM para a linha de canhões PEM ({names}): quebra-escudos."
        en["PartToggles"]["BSCell_PEM"] = f"<b>Cell: EMP</b>\n\n{d_en}"
        pt["PartToggles"]["BSCell_PEM"] = f"<b>Célula: PEM</b>\n\n{d_pt}"
        # texto da escolha 'cell:pem' nas techs (bs_strings.tech_strings) com os codinomes do spec
        for t in DATA.SPEC.get("career_techs") or []:
            if "cell:pem" in (t.get("unlocks") or []):
                tk = DATA.tech_string_key(t["id"])
                en["BSTechs"][tk + "Desc"] = d_en
                pt["BSTechs"][tk + "Desc"] = d_pt
    return en, pt


# ============================================================================= conferencia
def _strings_text(mod_dir, lang):
    p = os.path.join(mod_dir, "strings", f"{lang}.rules")
    if not os.path.isfile(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def _check_shot(mod_dir, s, D):
    errs = []
    sid = s["file"]
    path = os.path.join(mod_dir, "shots", s["dir"], f"{sid}.rules")
    root = G.rules_root(path)
    if root is None:
        return [f"{sid}: arquivo do tiro ausente ou ilegivel"]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for f in D.SPEC["conventions"]["forbidden_fields_0305"]:
        if re.search(rf"^\s*{re.escape(f)}\b", text, re.M):
            errs.append(f"{sid}: campo 0.30.5 proibido {f}")
    if "&/SW_" in text:
        errs.append(f"{sid}: cita global do SW (&/SW_*)")
    if (G.node_at(root, "ID").value or "").strip('"') != s["id"]:
        errs.append(f"{sid}: ID {G.node_at(root, 'ID').value} != {s['id']}")
    for fld, want in (("Range", s["range"]), ("Speed", s["speed"])):
        if not G._eq(G.num_at(root, fld), want):
            errs.append(f"{sid}: {fld} {G.num_at(root, fld)} != {want}")
    hit = G.node_at(root, "Components/Hit")
    if (G.node_at(hit, "Type").value or "") != "PenetratingHit":
        errs.append(f"{sid}: Hit nao e PenetratingHit")
    if not G._eq(G.num_at(hit, "Penetration"), s["penetration"]):
        errs.append(f"{sid}: Penetration {G.num_at(hit, 'Penetration')} != {s['penetration']}")
    po = (G.node_at(hit, "PenetratesOperational").value or "").strip().lower()
    if po != ("true" if s["penetrates_operational"] else "false"):
        errs.append(f"{sid}: PenetratesOperational {po}")
    if not G._eq(G.num_at(root, "Components/Targetable/Health"), s["health"]):
        errs.append(f"{sid}: Targetable {G.num_at(root, 'Components/Targetable/Health')} != {s['health']}")
    hs = G.node_at(hit, "HitShield/HitEffects")
    items = hs.children if hs is not None else []
    types = [(G.node_at(c, "Type").value if G.node_at(c, "Type") else None) for c in items]
    if types[:2] != ["ResourceDrain", "Damage"]:
        errs.append(f"{sid}: HitShield {types} (esperado ResourceDrain, Damage, ...)")
    else:
        dr = G.num_at(items[0], "Amount")
        dm = G.num_at(items[1], "Damage")
        if not G._eq(dr, s["shield_drain"]) or not G._eq(dm, s["shield_damage"]):
            errs.append(f"{sid}: HitShield dreno {dr} / dano {dm} != {s['shield_drain']} / {s['shield_damage']}")
        if (G.node_at(items[0], "TreatShieldAsPart").value or "").lower() != "true":
            errs.append(f"{sid}: ResourceDrain do escudo sem TreatShieldAsPart = true")
        if dr is not None and abs(dr - round(dr)) > 1e-9:
            errs.append(f"{sid}: ResourceDrain.Amount {dr} nao e inteiro (Int32)")
        if dr is not None and dm is not None and not G._eq(dr / SHIELD_PER_BATTERY + dm, s["shield_hp"]):
            errs.append(f"{sid}: ShieldDamage por tiro {dr / SHIELD_PER_BATTERY + dm} != {s['shield_hp']}")
    has_ov = "AreaShieldStatusApplication" in types
    want_ov = bool(s.get("overload"))
    if has_ov != want_ov:
        errs.append(f"{sid}: AreaShieldStatusApplication {'presente' if has_ov else 'ausente'} com "
                    f"pem.overload_rider = {D.switch('pem.overload_rider')}")
    if s.get("oc"):
        ln = s["lingering"]
        sa = [c for c, ty in zip(items, types) if ty == "StatusApplication"]
        if not sa or not G._eq(G.num_at(sa[0], "StatusDuration"), ln["duration"]) or \
                not G._eq(G.num_at(sa[0], "StatusValue"), ln["value"]):
            errs.append(f"{sid}: HitShield sem disruptor_drain {ln['duration']} s x {ln['value']}")
        af = G.num_at(hit, "PartCategoryPenetrationFactors/armor")
        if not G._eq(af, s["armor_factor"] * 100):
            errs.append(f"{sid}: armor {af} != {s['armor_factor'] * 100}%")
        pen = G.node_at(hit, "PenetratingOperational/HitEffects")
        pt_ = [(G.node_at(c, "Type").value, c) for c in (pen.children if pen is not None else [])]
        if [x for x, _c in pt_] != ["StatusApplication", "Damage"] or not G._eq(G.num_at(pt_[1][1], "Damage"),
                                                                                s["damage"]):
            errs.append(f"{sid}: PenetratingOperational {[x for x, _c in pt_]} (esperado disruptor_drain + Damage "
                        f"{s['damage']})")
    ho = G.node_at(hit, "HitOperational/HitEffects")
    oi = ho.children if ho is not None else []
    ot = [(G.node_at(c, "Type").value if G.node_at(c, "Type") else None) for c in oi]
    if not ot or ot[0] != "ResourceDrain" or not G._eq(G.num_at(oi[0], "Amount"), s["part_drain"]):
        errs.append(f"{sid}: HitOperational sem ResourceDrain {s['part_drain']}")
    dmg = [c for c, ty in zip(oi, ot) if ty == "Damage"]
    if not dmg or not G._eq(G.num_at(dmg[0], "Damage"), s["damage"]):
        errs.append(f"{sid}: HitOperational Damage != {s['damage']}")
    sa = [c for c, ty in zip(oi, ot) if ty == "StatusApplication"]
    want = s.get("drain_status") or s.get("lingering")
    if bool(sa) != bool(want):
        errs.append(f"{sid}: disruptor_drain no HitOperational {'presente' if sa else 'ausente'}")
    elif want and (not G._eq(G.num_at(sa[0], "StatusDuration"), want["duration"]) or
                   not G._eq(G.num_at(sa[0], "StatusValue"), want["value"])):
        errs.append(f"{sid}: disruptor_drain {G.num_at(sa[0], 'StatusDuration')} s x {G.num_at(sa[0], 'StatusValue')} "
                    f"!= {want['duration']} x {want['value']}")
    if not G._eq(G.num_at(hit, "HitStructural/HitEffects/0/Damage"), s["struct_damage"]):
        errs.append(f"{sid}: HitStructural != {s['struct_damage']}")
    return errs


def selfcheck(mod_dir, SPEC):
    """Pecas e tiros PEM escritos contra o spec (numeros brutos) e o DATA (transformados pelos switches): estoque,
    divisor, ResourcesUsed, Crew/CP (pem.tuvira_cp), FiringArc/RotateSpeed/FIRE_INTERVAL (pem.tuvira_mount),
    CoverageSectorArc, cook-off (dreno + explosao), overclock, ShieldDamage por tiro (3000 / 12000 / 18000),
    drenos/danos/penetracao/HP do tiro, o rider de sobrecarga so com pem.overload_rider, IDs e nomes (strings sem
    nome historico com os switches da 2.0)."""
    D = _D()
    errs = []
    spec_w = {w["id"]: w for w in SPEC["pem_weapons"]["weapons"]}
    for p in D.PEM:
        s = p["short"]
        w = spec_w.get(p["id"])
        if w is None:
            errs.append(f"{p['id']} fora de SPEC.pem_weapons")
            continue
        root = G.rules_root(os.path.join(mod_dir, "parts", s, f"{s}.rules"))
        if root is None:
            errs.append(f"{s}: parts/{s}/{s}.rules ausente ou ilegivel")
            continue
        part = G.node_at(root, "Part")
        comp = G.node_at(part, "Components")
        if (G.node_at(part, "ID").value or "").strip('"') != p["id"]:
            errs.append(f"{s}: ID {G.node_at(part, 'ID').value} != {p['id']}")
        checks = [("PartCrew/Crew", w["crew"]), ("CommandConsumer/CommandPoints", p["command_points"]),
                  ("MagStorage_0/MaxResources", p["internal_storage"]["MaxResources"]),
                  ("Splitter_0/ToQuantity", 4 if _tier(p) == "s" else 1),
                  ("Turret/FiringArc", p["firing_arc_deg"]),
                  ("Turret/RotateSpeed", p.get("rotate_speed_deg_s") or 180)]
        for path, want in checks:
            if not G._eq(G.num_at(comp, path), want):
                errs.append(f"{s}: {path} {G.num_at(comp, path)} != {want}")
        if s == "bs_pem_light" and not G._eq(G.num_at(comp, "CommandConsumer/CommandPoints"),
                                             D.switch("pem.tuvira_cp")):
            errs.append(f"{s}: CommandPoints != pem.tuvira_cp {D.switch('pem.tuvira_cp')}")
        if not G._eq(G.num_at(root, "FIRE_INTERVAL"), p["trigger_interval_s"], 1e-3):
            errs.append(f"{s}: FIRE_INTERVAL {G.num_at(root, 'FIRE_INTERVAL')} != {p['trigger_interval_s']}")
        mc = G.node_at(comp, "MagConsumer_0")
        if mc is None or not G._eq(G.num_at(mc, "ResupplyThreshold"), p["internal_storage"]["ResupplyThreshold"]):
            errs.append(f"{s}: MagConsumer_0 ResupplyThreshold != {p['internal_storage']['ResupplyThreshold']}")
        if G.node_at(comp, "Turret/CoverageSectorArc") is None:
            errs.append(f"{s}: TurretWeapon sem CoverageSectorArc")
        oc = bool(p.get("overclock"))
        cand = ["Fire_0_N/Components/TargetEmitter"] if oc else ["TargetEmitter"]
        em = next((G.node_at(comp, c) for c in cand if G.node_at(comp, c) is not None), None)
        if em is None or not G._eq(G.num_at(em, "ResourcesUsed"), 1) or \
                (G.node_at(em, "ResourceStorage").value or "") != "Splitter_0":
            errs.append(f"{s}: emissor sem ResourcesUsed 1 do Splitter_0")
        if oc and G.node_at(comp, "Fire_0_OC/Components/TargetEmitter") is None:
            errs.append(f"{s}: sem o bloco de overclock Fire_0_OC")
        # cook-off: dreno + explosao pequena, escalados pelo MagStorage_0
        ck = w["cookoff_cap"]
        de = G.node_at(comp, "DestroyedEffects_0")
        if de is None or (G.node_at(de, "FactorHitEffectsWith").value or "") != "MagStorage_0":
            errs.append(f"{s}: sem DestroyedEffects_0 escalado pelo MagStorage_0")
        else:
            hx = G.node_at(de, "HitEffects")
            its = {(G.node_at(c, "Type").value): c for c in (hx.children if hx is not None else [])}
            dr = its.get("ExplosiveResourceDrain")
            ex = its.get("ExplosiveDamage")
            if dr is None or not G._eq(G.num_at(dr, "TotalDrain"), ck["ExplosiveResourceDrain"]["TotalDrain"]) or \
                    not G._eq(G.num_at(dr, "Radius"), ck["ExplosiveResourceDrain"]["Radius"]):
                errs.append(f"{s}: cook-off sem ExplosiveResourceDrain {ck['ExplosiveResourceDrain']['TotalDrain']}")
            if ex is None or not G._eq(G.num_at(ex, "TotalDamage"), ck["ExplosiveDamage"]["TotalDamage"]):
                errs.append(f"{s}: cook-off sem ExplosiveDamage {ck['ExplosiveDamage']['TotalDamage']}")
        # tiros
        sds = shot_dicts(D, p)
        if not G._eq(sds[0]["shield_hp"], w["computed"]["shp_per_hit"]):
            errs.append(f"{s}: ShieldDamage por tiro {sds[0]['shield_hp']} != spec {w['computed']['shp_per_hit']}")
        for sd in sds:
            errs += _check_shot(mod_dir, sd, D)
        # carga da pesada
        if _tier(p) == "l":
            glow = bool(((p.get("art3d") or {}).get("turret") or {}).get("charge_glow")) and D.switch("pem.charge_glow")
            if glow and G.node_at(comp, "ChargeGlowGraphics") is None:
                errs.append(f"{s}: pem.charge_glow ligado e sem ChargeGlowGraphics")
            if not D.switch("pem.charge_glow") and G.node_at(comp, "ChargeGlowGraphics") is not None:
                errs.append(f"{s}: ChargeGlowGraphics com pem.charge_glow desligado")
    # nomes nos textos (en e pt-br): os do spec, nada historico com os switches da 2.0
    for lang in ("en", "pt-br"):
        text = _strings_text(mod_dir, lang)
        if not text:
            errs.append(f"strings/{lang}.rules ausente")
            continue
        for p in D.PEM:
            name = p["name_en"] if lang == "en" else (p.get("name_pt") or p["name_ptbr"])
            if f"{p['key']} = \"{name}\"" not in text and f'{p["key"]} = {name}' not in text:
                errs.append(f"strings/{lang}: Parts/{p['key']} sem o nome do spec {name!r}")
            if p.get("codename") and p["codename"] not in text:
                errs.append(f"strings/{lang}: codinome {p['codename']!r} ausente")
            oc = p.get("overclock") or {}
            ocn = oc.get("name_en" if lang == "en" else "name_ptbr")
            if ocn and ocn not in text:
                errs.append(f"strings/{lang}: overclock {ocn!r} ausente")
            if _tier(p) == "l" and oc:
                # o texto do overclock da os numeros reais do dreno que fica (os mesmos do tooltip)
                lg = "en" if lang == "en" else "pt"
                _b, _o, bat, shp = _oc_linger(D, p)
                for v in (_fmt(bat, lg), _fmt(shp, lg)):
                    if v not in text:
                        errs.append(f"strings/{lang}: texto do overclock {ocn!r} sem o dreno que fica ({v})")
                if re.search(r"o resto aos poucos|the rest over", text):
                    errs.append(f"strings/{lang}: texto antigo do overclock ('o resto' / 'the rest')")
        heavy = SPEC["switches"]["pem"]["heavy_name"]
        if D.switch("pem.heavy_name") == "Corisco":
            old = [v for v in heavy.get("values", {}) if v != "Corisco"]
            for o in old:
                for v in {o, D._fold(o)}:
                    if re.search(re.escape(v), text, re.I):
                        errs.append(f"strings/{lang}: nome historico da pesada {o!r} com pem.heavy_name = Corisco")
        if D.switch("pem.tuvira_mount") == "torre":
            light = next(x for x in SPEC["pem_weapons"]["weapons"] if x["id"].endswith("bs_pem_light"))
            fx = light["mount_fixa_historico"]
            for v in (fx["name_ptbr"], fx["name_en"]):
                if v in text:
                    errs.append(f"strings/{lang}: nome da Tuvira fixa {v!r} com pem.tuvira_mount = torre")
    return errs
