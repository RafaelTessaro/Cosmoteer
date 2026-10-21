"""Gerador dos projeteis (shots) de canhoes e defesas do Bullet Strike 2.0 (dono: WP02).

Estrutura copiada de shots/bullet_med, bullet_deck, pd_shot, disruptor_bolt e flak_large (0.30.x). Cada arquivo define
constantes STAT_* na raiz: o jogo ignora campos desconhecidos e as estatisticas das pecas leem esses valores.

Kinds nativos (build_mod.native_shot): kinetic (build_kinetic), explosive (build_explosive, Boiuna), flak
(build_flak_beam), flak_oc (montado no build_mod a partir do feixe base) e cloud (build_flak_cloud). O fragmento da
Nuvem de Fragmentos (kind frag_fragment) e do bsgen.ciws (SHOT_KINDS), que chama build_frag_fragment daqui.

2.0 (plano WP02 + ADDENDUM):
  * HE/AC: PenetratingOperational com o dano por peca seguinte do spec (pen_damage = guns.he_further_factor x direto,
    ja aplicado pelo bs_data); AP: PartCategoryPenetrationFactors {armor = 60%} e pen_damage do guns.ap_further_factor;
    SAP: armor 80 % e meia carga com raio 0,75x no FinishedPenetratingOperational; AC: carga 2x com raio 1,5x (numeros
    do spec). Nunca s['damage'] nas pecas seguintes.
  * Sem StructuralDamageRetentionPerHit / MinStructuralDamageScale (campos so do 0.30.5).
  * HitShield proprio so quando shield_damage != direto; tiro <= 30 mm sem Targetable (guns.small_rounds_targetable
    devolve).
  * Sobras da Fase B pelos seams do WP03 (bsgen.caliber_fx / bsgen.fxkit com API >= 2): pen_effect(art_tier),
    pop_effect(art_tier), light_pair(...); seam ausente ou None -> PARTICLES['pen'] / o OnDeath antigo / a luz antiga.
    Plasma (Boitata e Curupira) NAO chama esses seams: segue com bsgen/plasma_fx.py.
  * Os construtores de missil sairam deste arquivo (bsgen/missile_shots.py, WP07).
Contrato mantido para WP07/WP08/WP09 (mesmas assinaturas): D, SOUNDS, PARTICLES, GLOW, OWN_SHIP_PASS, _sound, _media,
_val, _blob_sprite, _drain_effect, _explosion.
"""

import inspect
import os

from rules_dsl import Q, Inh
from bsgen import common as C
from bsgen import trails as TR
from bsgen import plasma_fx as PFX


# modulos de efeitos (registro FX do build_mod): so com API >= 2; BS_FX_EXT=0 desliga todos. Um modulo 1.x (sem API)
# fica de fora, como no registro. Os modulos de efeitos NAO importam este arquivo no nivel do modulo (ciclo de import).
def _opt(name):
    if os.environ.get("BS_FX_EXT", "1") == "0":
        return None
    return C.content_module(name, min_api=2)


def _call(mod, fn, *a, **k):
    f = getattr(mod, fn, None) if mod is not None else None
    return f(*a, **k) if f is not None else None


FXK = _opt("bsgen.fxkit")
CFX = _opt("bsgen.caliber_fx")

D = "./Data/shots"

SOUNDS = {
    "mg": [f"{D}/chaingun_shot/sounds/chain_gun_impact_0{i}.wav" for i in range(1, 6)],
    "med": [f"{D}/bullet_med/sounds/cannon_impact_0{i}.wav" for i in range(1, 5)],
    "large": [f"{D}/bullet_large/sounds/large_cannon_impact_0{i}.wav" for i in range(1, 4)],
    "deck": [f"{D}/bullet_deck/sounds/deck_cannon_impact_0{i}.wav" for i in range(1, 4)],
    "he": [f"{D}/missile_he/sounds/launcher_rocket_impact_0{i}.wav" for i in range(1, 4)],
    "he_fast": [f"{D}/missile_he/sounds/launcher_rocket_impact_0{i}.wav" for i in range(1, 4)],
    "nuke": [f"{D}/missile_nuke/missile_nuke_hit.wav"],
    "emp": [f"{D}/disruptor_bolt/sounds/disruptor_impact_0{i}.wav" for i in range(1, 5)],
    "plasma": [f"{D}/bullet_railgun/sounds/railgun_impact_0{i}.wav" for i in range(1, 4)],
    "emp_fast": [f"{D}/disruptor_bolt/sounds/disruptor_impact_0{i}.wav" for i in range(1, 5)],
    "plasma_fast": [f"{D}/bullet_railgun/sounds/railgun_impact_0{i}.wav" for i in range(1, 4)],
    "flak": [f"{D}/flak_large/sounds/flak_cannon_impact_0{i}.wav" for i in range(1, 5)],
}

PARTICLES = {
    "mg": [f"{D}/chaingun_shot/particles/chaingun_sparks.rules", f"{D}/bullet_med/particles/bullet_flash_med.rules"],
    "mg_struct": [f"{D}/chaingun_shot/particles/chaingun_sparks.rules"],
    "med": [f"{D}/bullet_med/particles/bullet_hit_med.rules", f"{D}/bullet_med/particles/bullet_hit_med_sparks.rules",
            f"{D}/bullet_med/particles/bullet_smoke_med.rules", f"{D}/bullet_med/particles/bullet_flash_med.rules"],
    "med_struct": [f"{D}/bullet_med/particles/bullet_hit_med_struct.rules",
                   f"{D}/bullet_med/particles/bullet_flash_med_struct.rules"],
    "large": [f"{D}/bullet_large/particles/bullet_hit_large.rules", f"{D}/bullet_large/particles/bullet_hit_large_sparks.rules",
              f"{D}/bullet_large/particles/bullet_smoke_large.rules", f"{D}/bullet_large/particles/bullet_flash_large.rules"],
    "large_struct": [f"{D}/bullet_large/particles/bullet_hit_large_sparks.rules",
                     f"{D}/bullet_large/particles/bullet_flash_large_struct.rules"],
    "deck": [f"{D}/bullet_deck/particles/bullet_hit_deck.rules", f"{D}/bullet_deck/particles/bullet_hit_deck_sparks.rules",
             f"{D}/bullet_deck/particles/bullet_smoke_deck.rules", f"{D}/bullet_deck/particles/bullet_flash_deck.rules"],
    "deck_struct": [f"{D}/bullet_deck/particles/bullet_hit_deck_sparks.rules",
                    f"{D}/bullet_deck/particles/bullet_flash_deck_struct.rules"],
    "he": [f"{D}/missile_he/particles/missile_he_hit.rules", f"{D}/missile_he/particles/missile_he_flash.rules",
           f"{D}/missile_he/particles/missile_he_smoke.rules"],
    "nuke": [f"{D}/missile_nuke/particles/missile_nuke_flash_light.rules", f"{D}/missile_nuke/particles/missile_nuke_flash.rules",
             f"{D}/missile_nuke/particles/missile_nuke_shockwave.rules", f"{D}/missile_nuke/particles/missile_nuke_hit.rules"],
    "emp": [f"{D}/disruptor_bolt/particles/disruptor_bolt_hit_orb.rules", f"{D}/disruptor_bolt/particles/disruptor_bolt_hit_bolts.rules",
            f"{D}/disruptor_bolt/particles/disruptor_bolt_flash.rules"],
    # canhoes rapidos (bs_data.FAST_RATE): sem os 30-40 raios do disruptor_bolt_hit_bolts por acerto
    "emp_fast": [f"{D}/disruptor_bolt/particles/disruptor_bolt_hit_orb.rules",
                 f"{D}/disruptor_bolt/particles/disruptor_bolt_flash.rules"],
    "emp_drain": [f"{D}/disruptor_bolt/particles/ship_drain.rules", f"{D}/disruptor_bolt/particles/disruptor_bolt_hit_sizzle.rules"],
    "plasma": [f"{D}/bullet_railgun/particles/bullet_hit_railgun.rules", f"{D}/bullet_railgun/particles/bullet_railgun_sparks.rules",
               f"{D}/bullet_railgun/particles/bullet_flash_railgun.rules"],
    "plasma_struct": [f"{D}/bullet_railgun/particles/bullet_hit_struct_railgun.rules",
                      f"{D}/bullet_railgun/particles/bullet_hit_struct_railgun_sparks.rules"],
    # Boitata (10 tiros/s): sem as 80-100 faiscas do bullet_railgun_sparks por acerto
    "plasma_fast": [f"{D}/bullet_railgun/particles/bullet_hit_railgun.rules",
                    f"{D}/bullet_railgun/particles/bullet_flash_railgun.rules"],
    # carga explosiva das balas rapidas: impacto leve do chaingun em overclock (2-3 particulas de 0,3 s) + clarao, no
    # lugar da explosao inteira do missil HE a 17-36 tiros/s
    "he_fast": [f"{D}/chaingun_shot/overclock/particles/chaingun_shot_overclock_hit.rules",
                f"{D}/bullet_med/particles/bullet_flash_med.rules"],
    "flak": [f"{D}/flak_large/particles/flak_large_shrapnel.rules", f"{D}/flak_large/particles/flak_large_flash.rules",
             f"{D}/flak_large/particles/flak_large_smoke.rules"],
    # cada peca atravessada depois da primeira (sobra da Fase B, SPEC.art_assets.phase_b_leftovers fallback): so o
    # impacto leve do chaingun em overclock (2-3 particulas), nunca o preset cheio do primeiro acerto de novo; sem som,
    # como o PenetratingOperational do bullet_deck.rules vanilla
    "pen": [f"{D}/chaingun_shot/overclock/particles/chaingun_shot_overclock_hit.rules"],
}


def _trail_ref(s):
    """Rastro de particulas do projetil (bsgen/trails.py): copia propria no bucket de cima, na cor da municao;
    deck ambar usa o bullet_trail_deck.rules vanilla (ja e BulletTrailUpper)."""
    try:
        name = TR.trail_name(s["trail"], s.get("trail_color"))
    except ValueError:
        # trails.py sem a cor 2.0 desta municao (WP03 ausente): o rastro ambar da mesma forma, ou o deck vanilla
        try:
            name = TR.trail_name(s["trail"], None)
        except ValueError:
            name = None
    if name is None:
        return f"&<{TR.VANILLA_DECK}>"
    # pasta do projetil: BulletStrike/shots/<id>/ -> ../bs_trails/
    return f"&<../{TR.DIR.split('/', 1)[1]}/{name}.rules>"


GLOW = {
    "Texture": {"File": Q("./Data/common_effects/particles/blob.png"), "MipLevels": "max", "SampleMode": "Linear"},
}

# nossos projeteis e rajadas passam por cima do proprio casco (Low) e das nossas torres de conves e sensores
# (High, todos os TurretCollider sao IsHigh): bullet_deck.rules l.41, manipulator_beam.rules l.5-6
OWN_SHIP_PASS = {"FriendlyShipLowCollisions": False, "FriendlyShipHighCollisions": False}


def _sound(preset, volume, max_conc, speed_var=0.2):
    return Inh("/BASE_SOUNDS/AudioExterior", {
        "RandomSounds": [Q(s) for s in SOUNDS[preset]],
        "Volume": volume, "SpeedVariation": speed_var, "MaxConcurrent": max_conc})


def _media(preset, volume=0.6, max_conc=30, shake=0.0, struct=False, extra=None):
    key = preset + ("_struct" if struct and (preset + "_struct") in PARTICLES else "")
    media = [f"&<{p}>" for p in PARTICLES[key]]
    if extra:
        media += [f"&<{p}>" for p in extra]
    if not struct:
        media.append(_sound(preset, volume, max_conc))
        if shake:
            media.append(Inh("/BASE_SHAKE", {"ShakeAmount": shake, "Duration": 0.5}))
    return media


def _val(v):
    return {"BaseValue": v, "EffectScaleExponent": 1}


def _blob_sprite(bucket, wh, color, offset):
    """Sprite aditivo de blob.png (emissivo: aparece sobre o espaco e sobre cascos)."""
    return {"Type": "Sprite", "RenderBucket": bucket, "Offset": [round(offset, 3), 0],
            "Sprite": {**GLOW, "Size": list(wh), "VertexColor": list(color), "TargetBlendMode": "Add"}}


# ----------------------------------------------------------------------------- seams do WP03 (efeitos por calibre)
def _as_media(r):
    """Resultado de um seam de midia (lista de referencias, uma referencia ou {'MediaEffects': ...}) -> lista."""
    if isinstance(r, dict) and "MediaEffects" in r:
        r = r["MediaEffects"]
    if isinstance(r, (list, tuple)):
        return list(r)
    return [r]


def _pen_media(s):
    """MediaEffects de cada peca atravessada depois da primeira: caliber_fx.pen_effect(art_tier) (tabela
    SPEC.art_assets.seam_tier_map: tracer PEN_S, s/m PEN_M, l/h PEN_L); None (tier sem mapa ou WP03 ausente) ->
    PARTICLES['pen']; com art.pen_media = full (teste A/B da Fase B) a referencia antiga ao HitOperational."""
    r = _call(CFX, "pen_effect", s.get("art_tier"))
    if r is not None:
        return _as_media(r)
    if _switch("art.pen_media", "light") == "full":
        return "&../HitOperational/MediaEffects"
    return [f"&<{p}>" for p in PARTICLES["pen"]]


def _pop_media(s, old):
    """MediaEffects do projetil abatido no ar: caliber_fx.pop_effect(art_tier) (POP_S ate 76 mm, POP_L do 155 para
    cima); None -> o efeito antigo (old)."""
    r = _call(CFX, "pop_effect", s.get("art_tier"))
    return old if r is None else _as_media(r)


def _switch(key, default=None):
    try:
        import bs_data as DATA   # import tardio: bs_data nao importa este arquivo
        return DATA.switch(key)
    except Exception:   # noqa: BLE001 (sem o spec carregado, ex. testes isolados)
        return default


def _hull_color(ammo):
    try:
        import bs_data as DATA
        p = (DATA.PAL.get(ammo) or {}).get("hull")
        return list(p) if p else None
    except Exception:   # noqa: BLE001
        return None


def _light_pair(s, size, color, offset, z, unlit):
    """Luz do projetil pela fxkit.light_pair (WP03: halo so no espaco + luz de casco que nunca lava o branco).
    Assinatura do spec (SPEC.art_assets.phase_b_leftovers.islight_white_hull.where): light_pair(halo_size,
    halo_color, hull_size, hull_color, x_halo, x_hull, start, unlit); so os parametros que a funcao aceita sao
    passados. Tracante (<= 30 mm) sem luz de casco (hull_size None). Devolve componentes ou None (luz antiga)."""
    lp = getattr(FXK, "light_pair", None) if FXK is not None else None
    if lp is None:
        return None
    tracer = s.get("look", "tracer") == "tracer"
    if tracer:
        hull_size = None
    elif s.get("sprite_size"):
        hull_size = [round(1.2 * s["sprite_size"], 3), round(max(1.2 * s["sprite_size"] * 0.4, 0.5), 3)]
    else:
        L, W = s.get("sprite_wh") or (1.0, 0.3)
        hull_size = [round(1.2 * L, 3), round(max(1.2 * W, 0.5), 3)]
    speed = max(1.0, float(s.get("speed") or 100))
    args = {"halo_size": list(size), "halo_color": list(color), "hull_size": hull_size,
            "hull_color": _hull_color(s.get("ammo") or s.get("key")), "x_halo": round(offset, 3), "x_hull": 0,
            # halo com a cor glow/4: _unlitAdditiveStrength x4 para o mesmo brilho no espaco da Fase B (0,2 -> 0,8
            # tracantes; 0,125 -> 0,5 granadas)
            "start": round(min(0.05, max(0.01, 2.0 / speed)), 3), "unlit": round(unlit * 4, 3), "z": z,
            "ammo": s.get("ammo") or s.get("key")}
    try:
        sig = inspect.signature(lp)
    except (TypeError, ValueError):
        return None
    kw, missing = {}, False
    for name, p in sig.parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if name in args:
            kw[name] = args[name]
        elif p.default is p.empty:
            missing = True
    if missing:
        return None
    r = lp(**kw)
    if r is None:
        return None
    if isinstance(r, (list, tuple)):
        return {name: c for name, c in zip(("GlowSprite", "GlowSprite2"), r) if c}
    if isinstance(r, dict) and r.get("Type"):
        return {"GlowSprite": r}
    return dict(r) if isinstance(r, dict) else None


def _sprite_components(s):
    """Visual em voo (R1): visual por arma em bs_data.VIS, so a cor segue a municao.

    tracer (metralhadoras, 20/30 mm): risco aditivo alongado com a cabeca no projetil (pd_shot.rules: Size [8, .25],
        Offset [-3.5, 0] = -0.4375 L, LerpScaleFrom [.25, 1], LerpTime .05) + nucleo branco-quente (Upper4);
    energy (plasma): raio aditivo + nucleo; large (granadas): AnimatedSprite do bullet_large / bullet_deck.
    Mais a luz (fxkit.light_pair do WP03 ou o brilho IsLight da Fase B) e o rastro so nas armas lentas.
    Plasma (s["plasma_fx"] = gatling/heavy): visual proprio de bsgen/plasma_fx.py."""
    if s.get("plasma_fx"):
        return PFX.bolt_components(s["plasma_fx"], s.get("plasma_oc"))
    # seam S1: visual em voo por calibre (bsgen/caliber_fx.py); None = caminho antigo abaixo
    r = _call(CFX, "projectile_components", s, _trail_ref(s) if s.get("trail") else None)
    if r is not None:
        return r
    comps = {}
    look = s.get("look", "tracer")
    if look in ("tracer", "energy"):
        L, W = s["sprite_wh"]
        cl, cw = s["core_wh"]
        if look == "tracer":
            spr = _blob_sprite("BulletUpper3", [L, W], s["tracer_color"], -0.4375 * L)
            spr["LerpScaleFrom"] = [0.25, 1]
            spr["LerpTime"] = 0.05
        else:
            spr = _blob_sprite("BulletUpper3", [L, W], s["tracer_color"], -0.2 * L)
        comps["Sprite"] = spr
        comps["CoreSprite"] = _blob_sprite("BulletUpper4", [cl, cw], s["core_color"], -0.35 * cl)
        glow_off = s.get("glow_offset", -0.4 * L if look == "tracer" else -0.25 * L)
        unlit = 0.2  # pd_shot.rules: risco rapido brilha um pouco mais sobre o espaco
    else:
        size = s["sprite_size"]
        comps["Sprite"] = {"Type": "AnimatedSprite", "RenderBucket": "BulletUpper3", "ReduceScaleWith": "Hit",
                           "ReduceScaleExponent": 0.5,
                           "Animation": {"AtlasSprite": {"Texture": {"File": Q("./Data/shots/bullet_large/bullet_large.png"),
                                                                     "SampleMode": "Linear", "MipLevels": "max"},
                                                         "Size": [size, size]},
                                         "FrameCount": 16, "FrameSize": [256, 256], "FramesPerRow": 4,
                                         "FramesPerSecond": 120},
                           "NormalsTexture": "&Animation/AtlasSprite/Texture",
                           "DiffuseShader": Q("./Data/default.shader"),
                           "NormalsShader": Q("./Data/no_normals.shader")}
        glow_off = s.get("glow_offset", -1)
        unlit = 0.125
    gl = s["glow_size"]
    light = _light_pair(s, gl, s["glow_color"], glow_off, s.get("glow_z", 0), unlit)
    if light:
        comps.update(light)
    else:
        comps["GlowSprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": s.get("glow_z", 0),
                               "IsLight": True, "Offset": [round(glow_off, 3), 0],
                               "Sprite": {**GLOW, "Size": gl, "VertexColor": s["glow_color"], "TargetBlendMode": "Add",
                                          "Shader": Q("./Data/common_effects/fancy_light.shader"),
                                          "_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 24,
                                          "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": unlit}}
    if s.get("trail"):
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [_trail_ref(s)]}
    return comps


def _drain_effect(amount, shield=False):
    e = {"Type": "ResourceDrain", "ResourceType": "battery", "Amount": _val(amount)}
    if shield:
        e["TreatShieldAsPart"] = True
    e["MediaEffectsOnDrain"] = [f"&<{p}>" for p in PARTICLES["emp_drain"]]
    return e


def _explosion(radius, total, fire_per_n=None, friendly=False, structural=None):
    e = {"Type": "ExplosiveDamage", "TotalDamage": _val(total), "Radius": radius}
    if fire_per_n:
        e.update({"StatusType": "cosmoteer.fire", "StatusChancePerNDamage": f"{fire_per_n}%", "StatusValue": 1,
                  "StatusValueType": "Interpolated", "NDamage": 1000})
    if friendly:
        e["Filter"] = {"Friendlies": True}
    return e


def _pen_damage(s):
    """Dano em cada peca atravessada depois da primeira: pen_damage do spec (bs_data: HE/AC = guns.he_further_factor
    x direto; AP/SAP = guns.ap_further_factor x direto). Tiro sem o numero (modulo de fora) cai na convencao SW
    DAMAGE/2, nunca no dano cheio."""
    pd = s.get("pen_damage")
    if pd is None:
        return max(1, int(round(0.5 * s["damage"])))
    return pd


def _targetable(s, old_pop):
    """Targetable do projetil ou None (tiro <= 30 mm sem Targetable: precedente vanilla chaingun/pd_shot; o
    guns.small_rounds_targetable do bs_data devolve com o HP de reserva)."""
    if not s.get("targetable", True):
        return None
    if s.get("health") is None:
        raise ValueError(f"tiro {s.get('file')}: alvejavel sem Health")
    t = {"Type": "Targetable", "Health": int(s["health"]),
         "TargetCategory": Q(s.get("category") or s.get("target_category") or "bullet")}
    if s.get("plasma_fx"):
        # plasma: abatido no ar = so o estouro (respingo + clarao) e um chiado baixo (bsgen/plasma_fx.py), sem o seam
        t["OnDeath"] = {"MediaEffects": PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "pop", s.get("volume", 0.6))}
    else:
        t["OnDeath"] = {"MediaEffects": _pop_media(s, old_pop)}
    return t


# ----------------------------------------------------------------------------- canhoes
def build_kinetic(s):
    """Projetil penetrante (HE, AP, SAP, AC, plasma)."""
    top = {}
    if s.get("oc_range"):
        # alcance maior em overclock sem trocar o projetil (pd_shot.rules: OVERCLOCK/RANGE + Range BuffRemap)
        top["OVERCLOCK"] = {"RANGE": s["oc_range"]}
    top.update({
        "STAT_DAMAGE": s["damage"],
        "STAT_PENETRATION": s["penetration"],
        "STAT_PEN_DAMAGE": _pen_damage(s),
        "ID": Q(s["id"]),
        "Range": s["range"],
        "IdealRange": [round(s["range"] * 0.3), "&~/Range"],
        "IdealRadius": [5, 50],
        "Speed": s["speed"],
    })
    if s.get("oc_range"):
        top["Range"] = {"BaseValue": s["range"], "Modifiers": [
            {"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Replace", "RemapFrom": [0, 1],
             "RemapTo": ["&../../../BaseValue", "&~/OVERCLOCK/RANGE"]}]}
        top["IdealRange"] = [round(s["range"] * 0.3), s["range"]]
        top["ReceivableBuffs"] = ["Overclock"]
    # nos tiros de plasma (s["plasma_fx"]) o preset s["fx"] so alimenta stats/docs: o visual e os efeitos de impacto vem
    # de bsgen/plasma_fx.py (bolt_components / hit_media)
    preset = s.get("fx", "med")
    hit_op = {"ReduceEffectsByPenetration": True, "Offset": [-0.15, 0],
              "HitEffects": [{"Type": "Damage", "Damage": _val(s["damage"])},
                             {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
              "MediaEffects": _media(preset, s.get("volume", 0.6), s.get("max_conc", 30), s.get("shake", 0),
                                     extra=s.get("extra_particles"))}
    if s.get("plasma_fx"):
        hit_op["MediaEffects"] = PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "hull", s.get("volume", 0.6),
                                               s.get("max_conc", 30), s.get("shake", 0))
    if s.get("impact_explosion"):
        # explosao no impacto (overclock "Erupcao Solar" do Curupira)
        r, total = s["impact_explosion"]
        hit_op["HitEffects"].insert(1, _explosion(r, total))
    if s.get("emp_drain"):
        hit_op["HitEffects"].append(_drain_effect(s["emp_drain"]))
    if s.get("heat"):
        hit_op["HitEffects"].append({"Type": "StatusApplication", "StatusType": "cosmoteer.heat",
                                     "StatusValue": s["heat"], "ApplyToAllHitPartTiles": True,
                                     "DivideValueByPartArea": True})
    hit_struct = {"ReduceEffectsByPenetration": True, "Offset": [0.15, 0],
                  "HitEffects": [{"Type": "Damage", "Damage": _val(s.get("struct_damage", max(1, round(s["damage"] / 4))))},
                                 {"Type": "Impulse", "Impulse": _val(max(1, s.get("impulse", 5) / 2))}],
                  "MediaEffects": _media(preset, struct=True)}
    if s.get("plasma_fx"):
        hit_struct["MediaEffects"] = PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "struct", s.get("volume", 0.6),
                                                   s.get("max_conc", 30))
    if s.get("bolt"):
        top = _bolt_kinetic(s, top, hit_op, hit_struct)
        # seam S3 (o modulo de calibre ignora os de plasma)
        _call(CFX, "decorate", s, top)
        return top
    # pecas atravessadas depois da primeira: dano proprio do spec (J1R3-0), fogo e impulso; midia leve (Fase B)
    pen_op = {"ReduceEffectsByPenetration": True,
              "HitEffects": [{"Type": "Damage", "Damage": _val(_pen_damage(s))},
                             {"Type": "StatusApplication", "StatusType": "cosmoteer.fire",
                              "StatusChance": _val(s.get("fire", 0.04)), "ValueType": "Interpolated"},
                             {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
              "MediaEffects": _pen_media(s)}
    hit = {
        "Type": "PenetratingHit",
        "Penetration": s["penetration"],
        "PenetrationSpeed": s.get("pen_speed", 25),
        **OWN_SHIP_PASS,
        "CrewCollisions": "{Enemies=true; Junk=true}",
        "PenetratesCrew": True,
        "HitCrew": "&HitOperational",
    }
    af = s.get("armor_factor")
    if af is not None and abs(float(af) - 1.0) > 1e-9:
        # AP 60 %, SAP 80 % (SPEC.penetration_rules.armor_factor); HE/AC 100 % = sem o campo
        hit["PartCategoryPenetrationFactors"] = {"armor": f"{int(round(float(af) * 100))}%"}
    if s.get("emp_shield_drain") or (s.get("shield_damage") is not None and s["shield_damage"] != s["damage"]):
        shield_fx = [{"Type": "Damage", "Damage": _val(s["shield_damage"] if s.get("shield_damage") is not None
                                                       else s["damage"])},
                     {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}]
        if s.get("emp_shield_drain"):
            shield_fx.append(_drain_effect(s["emp_shield_drain"], shield=True))
        hit["HitShield"] = {"ReduceEffectsByPenetration": True, "Offset": [-0.15, 0], "HitEffects": shield_fx,
                            "MediaEffects": "&../HitOperational/MediaEffects"}
    else:
        hit["HitShield"] = "&HitOperational"
    hit["HitOperational"] = hit_op
    hit["HitStructural"] = hit_struct
    hit["PenetratingOperational"] = pen_op
    # sem StructuralDamageRetentionPerHit / MinStructuralDamageScale (so 0.30.5: SPEC.conventions.forbidden_fields_0305)
    hit["PenetratingStructural"] = "&HitStructural"
    if s.get("finish_explosion"):
        # carga onde o projetil para: HE/AC cheia, SAP com meia carga e raio 0,75x (numeros do spec)
        r, total = s["finish_explosion"]
        hit["FinishedPenetratingOperational"] = {
            "HitEffects": [_explosion(r, total, fire_per_n=s.get("explosion_fire"))],
            "MediaEffects": _media("he_fast", 0.4, 20) if s.get("fast") else _media("he", 0.5, 20, s.get("shake", 0.03))}
    else:
        hit["FinishedPenetratingOperational"] = "&PenetratingOperational"
    hit["FinishedPenetratingStructural"] = "&PenetratingStructural"
    if s.get("anti_projectile"):
        # tambem acerta misseis/minas/projeteis (padrao de shots/mine/mine_shrapnel.rules e pd_shot.rules)
        hit["BulletCollisions"] = {"Enemies": True, "Junk": True, "Neutrals": True,
                                   "OnlyBulletCategories": s.get("anti_categories",
                                                                 ["missile", "mine", "bullet", "laser", "ion_shot"])}
        hit["HitBullet"] = {"Offset": [-0.15, 0],
                            "HitEffects": [{"Type": "Damage", "Damage": _val(s["anti_projectile"])}],
                            "MediaEffects": [f"&<{D}/pd_shot/particles/pd_shot_sparks.rules>"]}

    top["Components"] = _kinetic_components(s, hit)
    # seam S3: midia de impacto por calibre (bsgen/caliber_fx.py), so visual, altera top no lugar
    _call(CFX, "decorate", s, top)
    return top


def _kinetic_components(s, hit):
    comps = {
        "Physics": {"Type": "CirclePhysics", "Radius": s.get("radius", 0.12), "Density": 0.0001},
        "Death": {"Type": "DeathByLifetime"},
    }
    t = _targetable(s, "&~/Components/Hit/HitOperational/MediaEffects")
    if t is not None:
        comps["Targetable"] = t
    comps["Hit"] = hit
    comps.update(_sprite_components(s))
    return comps


def _bolt_kinetic(s, top, hit_op, hit_struct):
    """Disparo que se gasta no primeiro escudo/peca (plasma; spec ammo_types[plasma]: penetracao 0). Segue o raio
    laser do jogo base (laser_bolt_small.rules: PenetratingHit sem Penetration e SEM ReduceEffectsByPenetration,
    Penetrating/FinishedPenetratingOperational sem efeito): com penetracao 0 o ReduceEffectsByPenetration poderia
    cortar o dano do acerto e a explosao do overclock do Curupira. Nao vira SimpleHit porque o SimpleHit do jogo
    nunca tem HitStructural proprio (so &HitOperational), e o plasma mantem 1/4 do dano na estrutura, como o
    raio laser (500/125). HitShield proprio (padrao do railgun); a chance de fogo vai no HitOperational."""
    hit_op = dict(hit_op)
    hit_op.pop("ReduceEffectsByPenetration", None)
    hit_op["HitEffects"] = hit_op["HitEffects"] + [{"Type": "StatusApplication", "StatusType": "cosmoteer.fire",
                                                    "StatusChance": _val(s.get("fire", 0.04)),
                                                    "ValueType": "Interpolated"}]
    hit_struct = dict(hit_struct)
    hit_struct.pop("ReduceEffectsByPenetration", None)
    hit = {"Type": "PenetratingHit", **OWN_SHIP_PASS,
           "CrewCollisions": "{Enemies=true; Junk=true}", "HitCrew": "&HitOperational"}
    if s.get("shield_damage") is not None and s["shield_damage"] != s["damage"]:
        hit["HitShield"] = {"Offset": [-0.15, 0],
                            "HitEffects": [{"Type": "Damage", "Damage": _val(s["shield_damage"])},
                                           {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
                            "MediaEffects": "&../HitOperational/MediaEffects"}
        if s.get("plasma_fx"):
            # escudo: respingo achatado na face do escudo + clarao (o escudo ja desenha a propria ondulacao)
            hit["HitShield"]["MediaEffects"] = PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "shield",
                                                             s.get("volume", 0.6), s.get("max_conc", 30))
    else:
        hit["HitShield"] = "&HitOperational"
    hit["HitOperational"] = hit_op
    hit["HitStructural"] = hit_struct
    hit["PenetratingOperational"] = {}
    hit["PenetratingStructural"] = "&HitStructural"
    hit["FinishedPenetratingOperational"] = {}
    hit["FinishedPenetratingStructural"] = {}
    top["STAT_PENETRATION"] = 0
    top.pop("STAT_PEN_DAMAGE", None)
    top["Components"] = _kinetic_components(s, hit)
    return top


def build_explosive(s):
    """Granada de contato da Boiuna (HE e AC; plano WP02): detona no primeiro escudo ou peca (SimpleHit). HitShield =
    o dano contra escudo do spec; na peca: dano direto + explosao (com fogo, bonus fora do balanco) + explosao so
    estrutural; no fim do alcance detona (OnDeath da vida util, padrao mine_deployed); abatida no ar = so o estouro.
    AC guiada (boiuna.ac_guided): TargetHoming do bullet_railgun.rules vanilla (s['guided'])."""
    direct = s.get("damage", 0)
    exp_r, exp_total = s["explosion"]
    top = {
        "STAT_DAMAGE": direct + exp_total,
        "STAT_PENETRATION": 0,
        "STAT_EXPLOSIVE": exp_total,
        "STAT_RADIUS": exp_r,
        "ID": Q(s["id"]),
        "Range": s["range"],
        "IdealRange": [round(s["range"] * 0.3), "&~/Range"],
        "IdealRadius": [5, 50],
        "Speed": s["speed"],
    }
    # midia de impacto da granada: explosao do missil HE (o preset de calibre 'deck' do bs_data e de bala); o WP03
    # troca pelo HE_BIG / AC_BLAST_L no decorate
    preset = s.get("explosive_fx") or "he"
    fx_list = []
    if direct:
        fx_list.append({"Type": "Damage", "Damage": _val(direct)})
    fx_list.append(_explosion(exp_r, exp_total, fire_per_n=s.get("explosion_fire"), friendly=s.get("friendly_fire", False)))
    if s.get("struct_explosion"):
        sr, st = s["struct_explosion"]
        fx_list.append({"Type": "ExplosiveDamage", "TotalDamage": _val(st), "Radius": sr,
                        "Filter": {"OperationalHealth": False, "StructuralHealth": True,
                                   "Friendlies": bool(s.get("friendly_fire", False))}})
    if s.get("emp_area"):
        er, ed = s["emp_area"]
        fx_list.append({"Type": "ExplosiveResourceDrain", "ResourceType": "battery", "TotalDrain": _val(ed),
                        "Radius": er, "Slices": 1, "Filter": {"Ships": True, "Shields": True},
                        "MediaEffectsOnDrainFactor": 0.002,
                        "MediaEffectsOnDrain": [f"&<{p}>" for p in PARTICLES["emp_drain"]]})
    if s.get("heat"):
        fx_list.append({"Type": "StatusApplication", "StatusType": "cosmoteer.heat", "StatusValue": s["heat"],
                        "ApplyToAllHitPartTiles": True, "DivideValueByPartArea": True})
    fx_list.append({"Type": "Impulse", "Impulse": _val(s.get("impulse", 30))})
    hit_op = {"HitEffects": fx_list,
              "MediaEffects": _media(preset, s.get("volume", 0.8), s.get("max_conc", 12), s.get("shake", 0.08),
                                     extra=s.get("extra_particles"))}
    hit = {"Type": "SimpleHit", **OWN_SHIP_PASS, "HitOperational": hit_op,
           "HitStructural": "&HitOperational", "HitCrew": "&HitOperational",
           "CrewCollisions": "{Enemies=true; Junk=true}"}
    shield = s.get("shield_damage")
    if shield is not None and shield != direct + exp_total:
        # contato no escudo: o dano contra escudo do spec num golpe so (nunca passa o escudo)
        hit["HitShield"] = {"HitEffects": [{"Type": "Damage", "Damage": _val(shield)},
                                           {"Type": "Impulse", "Impulse": _val(s.get("impulse", 30))}],
                            "MediaEffects": "&../HitOperational/MediaEffects"}
    else:
        hit["HitShield"] = "&HitOperational"
    death = {"Type": "DeathByLifetime"}
    if s.get("death_blast"):
        # no fim do alcance o projetil detona (mine_deployed.rules: DeathByLifetime -> OnDeath); so as explosoes,
        # sem o dano direto nem o impulso, que precisam de uma peca atingida
        death["OnDeath"] = {"HitEffects": [e for e in fx_list if e["Type"] in ("ExplosiveDamage", "ExplosiveResourceDrain")],
                            "MediaEffects": "&../../Hit/HitOperational/MediaEffects"}
    comps = {
        "Physics": {"Type": "CirclePhysics", "Radius": s.get("radius", 0.25), "Density": 0.0001},
        "Death": death,
    }
    # abatida no ar: sem dano em area (como os misseis vanilla), so o estouro
    t = _targetable(s, [f"&<{PARTICLES['flak'][1]}>"])
    if t is not None:
        comps["Targetable"] = t
    comps["Hit"] = hit
    guided = s.get("guided")
    if isinstance(guided, dict):
        comps["Homing"] = {"Type": guided.get("Type", "TargetHoming"), "TurnVelocity": guided["TurnVelocity"]}
        for k in ("Delay", "ModifiesLinearVelocity", "VelocityCompensation"):
            if k in guided:
                comps["Homing"][k] = guided[k]
    elif s.get("homing"):
        comps["Homing"] = {"Type": "TargetHoming", "TurnVelocity": f"{s['homing']}d",
                           "ModifiesLinearVelocity": True, "VelocityCompensation": "100%"}
    comps.update(_sprite_components(s))
    top["Components"] = comps
    # seam S3: midia de impacto por calibre (bsgen/caliber_fx.py), so visual, altera top no lugar
    _call(CFX, "decorate", s, top)
    return top


# ----------------------------------------------------------------------------- defesas
def _deg(v):
    v = float(v)
    return f"{int(v) if v == int(v) else f'{v:g}'}d"


def build_flak_beam(s):
    """Rajada antiprojetil de UM modo (HE ou FRAG): feixe instantaneo ate o ponto mirado + explosao em area
    (flak_large.rules).

    Duas cargas no mesmo HitNothing (o flak_large vanilla tambem tem 2 ExplosiveDamage): a de sempre contra
    misseis/minas/projeteis (s["categories"]) e a da Fase B so contra laser/ion_shot (s["laser_categories"], raios do
    SW:ACD; guns.defesa_antilaser), sem tripulacao. O filtro padrao e Enemy: nosso plasma (categoria laser) e nossos
    misseis nunca sao atingidos. FRAG (s["fragment"]): explosao central menor + SpawnBullets do cone de fragmentos
    (Arc [inicio, abertura], Spread faixa simetrica, InheritVelocity false), como o FLAK_FIELD do
    flak_large_overclock.rules (constante na raiz + &~/). O overclock da Pororoca (flak_oc) herda tudo."""
    cats = s["categories"]
    top = {
        "STAT_DAMAGE": s["vs_shots"],
        "STAT_RADIUS": s["radius"],
        "STAT_LASER_DAMAGE": s["vs_lasers"],
        "STAT_LASER_RADIUS": s["laser_radius"],
    }
    sp = s.get("frag_spawn")
    if s.get("fragment"):
        top["STAT_FRAGMENTS"] = sp["count"]
        top["FRAGMENT"] = f"&<{s['fragment']}.rules>"
    top.update({
        "Range": s["range"],
        "IdealRange": round(s["range"] * 0.9),
        "ClipRangeToTarget": True,
        "RandomOffsetRadius": s.get("offset", [0.5, 3]),
        # passa por cima do casco (Low) e das nossas torres (High): manipulator_beam.rules l.5-6
        **OWN_SHIP_PASS,
    })
    fx = [
        {"Type": "ExplosiveDamage", "TotalDamage": _val(s["vs_shots"]), "Radius": s["radius"], "Slices": 1,
         "Filter": {"Ships": False, "Shields": False, "Bullets": True, "OnlyBulletCategories": cats,
                    "Crew": bool(s.get("crew", True))}},
        # carga extra so contra raios laser/ion (SW:ACD: 250-20000 de vida), sem tripulacao
        {"Type": "ExplosiveDamage", "TotalDamage": _val(s["vs_lasers"]), "Radius": s["laser_radius"], "Slices": 1,
         "Filter": {"Ships": False, "Shields": False, "Bullets": True, "OnlyBulletCategories": s["laser_categories"],
                    "Crew": False}},
    ]  # so defesa: sem a explosao contra naves e escudos da flak vanilla
    if s.get("fragment"):
        a0, a1 = sp["arc"]
        s0, s1 = sp["spread"]
        fx.append({"Type": "SpawnBullets", "Bullet": "&~/FRAGMENT", "Count": int(sp["count"]),
                   "Arc": [_deg(a0), _deg(a1)], "Spread": [_deg(s0), _deg(s1)], "InheritVelocity": False})
    if s.get("spawn_cloud"):
        fx.append({"Type": "SpawnBullets", "Bullet": f"&<{s['spawn_cloud']}>", "Count": 1})
    media = [f"&<{p}>" for p in PARTICLES["flak"][: s.get("particles", 2)]]
    media.append(_sound("flak", s.get("volume", 0.3), s.get("max_conc", 10), 0.25))
    top["HitNothing"] = {"HitEffects": fx, "MediaEffects": media}
    top["HitShield"] = "&HitNothing"
    top["HitOperational"] = "&HitNothing"
    top["HitStructural"] = "&HitNothing"
    # seam S3: rajada por defesa (bsgen/caliber_fx.py), so visual, altera top no lugar (depois do HitNothing)
    _call(CFX, "decorate", s, top)
    return top


def _cloud_filter(s):
    """Filtro so de inimigos (formato do BulletCollisions do pd_shot.rules l.92-99, com Friendlies = false). Na
    nuvem do overclock da Pororoca so com s['enemies_only'] (variante ciws_vs_own_missiles; padrao as_is = nuvem como
    a vanilla, sem o grupo); no fragmento VolumeHit da Nuvem de Fragmentos sempre (guns.frag_fragment = volumehit).
    O jogo base so usa esse grupo em SimpleHit/PenetratingHit: num VolumeHit pode nao ter efeito (o campo e ignorado
    sem erro)."""
    if not s.get("enemies_only"):
        return {}
    bc = {"Enemies": True, "Junk": True, "Neutrals": True, "Friendlies": False}
    if s.get("only_categories"):
        bc["OnlyBulletCategories"] = list(s["only_categories"])
    return {"BulletCollisions": bc}


def build_flak_cloud(s):
    """Nuvem de estilhacos que fica parada e consome projeteis (flak_large_overclock_field.rules)."""
    top = {
        "ID": Q(s["id"]),
        "Range": 0,
        "Speed": 0,
        "RADIUS": s["radius"],
        "REPULSE_RANGE": s["radius"] * 2,
        "LIFETIME": s["lifetime"],
        "DAMAGE_POOL": s["pool"],
        "MAX_BULLET_DAMAGE": "ceil((&DAMAGE_POOL) / ((&RADIUS) * 2))",
        "Components": {
            "Physics": {"Type": "CirclePhysics", "Radius": "&~/RADIUS", "Density": 1, "LinearDamping": "25%"},
            "FieldRepulsion": {"Type": "ProximityAcceleration", "Range": "&~/REPULSE_RANGE", "Acceleration": -7,
                               "AccelerateTowardsShips": False, "AccelerateTowardsBullets": True,
                               "AccelerateTowardsBulletCategories": ["bs_flak_cloud"],
                               "AccelerateTowardsFriendlies": True, "AccelerateTowardsEnemies": False},
            "Targetable": {"Type": "Targetable", "Health": 1, "TargetCategory": Q("bs_flak_cloud")},
            "LifetimeDeath": {"Type": "DeathByLifetime", "Lifetime": "&~/LIFETIME"},
            "DamagePoolDeath": {"Type": "DeathByDamagePool", "DamagePool": "DamagePool"},
            "DamagePool": {"Type": "DamagePool", "Damage": {"BaseValue": "(&~/DAMAGE_POOL)", "EffectScaleExponent": 1}},
            "VolHit": {"Type": "VolumeHit", "BeamAttenuationDamagePool": "DamagePool", **_cloud_filter(s),
                       "HitBullet": {"HitEffects": [{"Type": "Damage", "Damage": 0, "DamagePool": "DamagePool",
                                                     "MaxDamageFromPool": {"BaseValue": "(&~/MAX_BULLET_DAMAGE)",
                                                                           "EffectScaleExponent": 1}}],
                                     "MediaEffects": ["&<./Data/shots/flak_large/overclock/particles/sparks_field.rules>"]}},
            "MediaEffects": {"Type": "MediaEffects", "FactorEffectsWith": "DamagePool",
                             "MediaEffects": ["&<./Data/shots/flak_large/overclock/particles/flak_large_overclock_field_shrapnel.rules>"]},
        },
    }
    # seam S3: nuvem de estilhacos (bsgen/caliber_fx.py), so visual, altera top no lugar
    _call(CFX, "decorate", s, top)
    return top


FRAG_VARIANTS = ("simplehit", "volumehit")


def build_frag_fragment(s):
    """Fragmento da Nuvem de Fragmentos (municao FRAG, indice 4) - um por defesa, disparado pelo SpawnBullets do feixe
    FRAG. Sem Targetable (nunca e alvo de PD), passa por cima do proprio casco (OWN_SHIP_PASS), so acerta
    misseis/minas/projeteis inimigos e no casco so faisca (chaingun_sparks, 2-4 particulas; nunca o pd_shot_sparks).
    Visual (SPEC.art_assets.effects.frag.fragments): um Sprite aditivo blob.png [0.35, 0.06] na cor palette.frag.tracer,
    BulletUpper3, LerpScaleFrom [0.3, 1], LerpTime 0.03; sem IsLight.
    guns.frag_fragment (s['variant']):
      simplehit: SimpleHit com BulletCollisions {Enemies, Junk, Neutrals; OnlyBulletCategories} (pd_shot.rules l.92-99)
                 e HitBullet com o dano do spec; HitOperational/HitShield/HitStructural sem HitEffects;
      volumehit (safe): fragmento VolumeHit movel no molde da nuvem da Pororoca (flak_large_overclock_field.rules:
                 DamagePool = o dano do fragmento, DeathByDamagePool) com o filtro so de inimigos (_cloud_filter)."""
    variant = s.get("variant") or "volumehit"
    if variant not in FRAG_VARIANTS:
        raise ValueError(f"fragmento {s.get('file')}: variante {variant!r} (use {', '.join(FRAG_VARIANTS)})")
    dmg = int(s["damage"])
    speed = s["speed"]
    life = float(s["lifetime"])
    reach = s.get("reach") or round(speed * life, 2)
    cats = list(s.get("categories") or ["missile", "mine", "bullet"])
    sparks = [f"&<{p}>" for p in PARTICLES["mg_struct"]]
    color = s.get("tracer_color") or [150, 230, 215]
    top = {"STAT_DAMAGE": dmg, "STAT_VARIANT": Q(variant), "ID": Q(s["id"]), "Range": reach, "Speed": speed}
    spr = _blob_sprite("BulletUpper3", [0.35, 0.06], color, -0.15)
    spr["LerpScaleFrom"] = [0.3, 1]
    spr["LerpTime"] = 0.03
    comps = {
        "Physics": {"Type": "CirclePhysics", "Radius": s.get("radius", 0.3), "Density": 0.0001},
        "Death": {"Type": "DeathByLifetime", "Lifetime": life},
        "Sprite": spr,
    }
    if variant == "simplehit":
        comps["Hit"] = {"Type": "SimpleHit", **OWN_SHIP_PASS,
                        "BulletCollisions": {"Enemies": True, "Junk": True, "Neutrals": True,
                                             "OnlyBulletCategories": cats},
                        "HitBullet": {"HitEffects": [{"Type": "Damage", "Damage": _val(dmg)}], "MediaEffects": sparks},
                        "HitShield": "&HitOperational",
                        "HitOperational": {"MediaEffects": sparks},
                        "HitStructural": "&HitOperational"}
    else:
        comps["DamagePoolDeath"] = {"Type": "DeathByDamagePool", "DamagePool": "DamagePool"}
        comps["DamagePool"] = {"Type": "DamagePool", "Damage": _val(dmg)}
        comps["VolHit"] = {"Type": "VolumeHit", "BeamAttenuationDamagePool": "DamagePool",
                           **_cloud_filter({"enemies_only": True, "only_categories": cats}),
                           "HitBullet": {"HitEffects": [{"Type": "Damage", "Damage": 0, "DamagePool": "DamagePool",
                                                         "MaxDamageFromPool": _val(dmg)}],
                                         "MediaEffects": sparks}}
    top["Components"] = comps
    # seam S3: o modulo de calibre pode trocar o visual do fragmento (s['kind'] = frag_fragment)
    _call(CFX, "decorate", s, top)
    return top
