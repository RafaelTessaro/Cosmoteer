"""Gerador dos projeteis (shots) do Bullet Strike.

Estrutura copiada de shots/bullet_med, bullet_deck, missile_he, disruptor_bolt e flak_large (0.30.x).
Cada arquivo define constantes STAT_DAMAGE / STAT_PENETRATION na raiz: o jogo ignora campos
desconhecidos e as estatisticas das pecas leem esses valores (evita caminhos frageis).
"""

from rules_dsl import Q, Inh
from bsgen import trails as TR
from bsgen import plasma_fx as PFX

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
    # carga explosiva das balas rapidas (Cigarra APHE, Furacao Padrao/APHE): impacto leve do chaingun em overclock
    # (2-3 particulas de 0,3 s) + clarao, no lugar da explosao inteira do missil HE a 17-36 tiros/s
    "he_fast": [f"{D}/chaingun_shot/overclock/particles/chaingun_shot_overclock_hit.rules",
                f"{D}/bullet_med/particles/bullet_flash_med.rules"],
    "flak": [f"{D}/flak_large/particles/flak_large_shrapnel.rules", f"{D}/flak_large/particles/flak_large_flash.rules",
             f"{D}/flak_large/particles/flak_large_smoke.rules"],
}


def _trail_ref(s):
    """Rastro de particulas do projetil (bsgen/trails.py): copia propria no bucket de cima, na cor da municao;
    Padrao/APHE dos canhoes de conves usam o bullet_trail_deck.rules vanilla (ja e BulletTrailUpper)."""
    name = TR.trail_name(s["trail"], s.get("trail_color"))
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


def _sprite_components(s):
    """Visual em voo (R1): visual por arma em bs_data.VIS, so a cor segue a municao.

    tracer (metralhadoras, 20/30 mm): risco aditivo alongado com a cabeca no projetil (pd_shot.rules: Size [8, .25],
        Offset [-3.5, 0] = -0.4375 L, LerpScaleFrom [.25, 1], LerpTime .05) + nucleo branco-quente (Upper4);
    energy (plasma): raio aditivo + nucleo; large (granadas): AnimatedSprite do bullet_large / bullet_deck.
    Mais o brilho IsLight (fancy_light) de sempre, maior, e o rastro so nas armas lentas.
    Plasma (s["plasma_fx"] = gatling/heavy): visual proprio de bsgen/plasma_fx.py (nucleo branco-quente, corona,
    cauda animada, crepitar; o rastro do Curupira tambem e de la, nao de bsgen/trails.py)."""
    if s.get("plasma_fx"):
        return PFX.bolt_components(s["plasma_fx"], s.get("plasma_oc"))
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
    comps["GlowSprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": s.get("glow_z", 0), "IsLight": True,
                           "Offset": [round(glow_off, 3), 0],
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


def build_kinetic(s):
    """Projetil penetrante (padrao, perfurante, perfurante-explosivo, plasma, EMP)."""
    top = {}
    if s.get("oc_range"):
        # alcance maior em overclock sem trocar o projetil (pd_shot.rules: OVERCLOCK/RANGE + Range BuffRemap)
        top["OVERCLOCK"] = {"RANGE": s["oc_range"]}
    top.update({
        "STAT_DAMAGE": s["damage"],
        "STAT_PENETRATION": s["penetration"],
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
    # nos tiros de plasma (s["plasma_fx"]) o preset s["fx"] e o VIS de bs_data so alimentam stats/docs: o visual e
    # os efeitos de impacto vem de bsgen/plasma_fx.py (bolt_components / hit_media) e sobrescrevem os de baixo
    preset = s.get("fx", "med")
    hit_op = {"ReduceEffectsByPenetration": True, "Offset": [-0.15, 0],
              "HitEffects": [{"Type": "Damage", "Damage": _val(s["damage"])},
                             {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
              "MediaEffects": _media(preset, s.get("volume", 0.6), s.get("max_conc", 30), s.get("shake", 0),
                                     extra=s.get("extra_particles"))}
    if s.get("plasma_fx"):
        # familia de efeitos de plasma (bsgen/plasma_fx.py): respingo, faiscas, clarao e brasa ciano; no overclock
        # do Curupira a onda de choque da "Erupcao Solar" entra no lugar da bola de fogo laranja do missil HE
        hit_op["MediaEffects"] = PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "hull", s.get("volume", 0.6),
                                               s.get("max_conc", 30), s.get("shake", 0))
    if s.get("impact_explosion"):
        # explosao no impacto (overclock "Erupcao Solar" da Curupira)
        r, total = s["impact_explosion"]
        hit_op["HitEffects"].insert(1, _explosion(r, total))
    if s.get("emp_drain"):
        hit_op["HitEffects"].append(_drain_effect(s["emp_drain"]))
    if s.get("heat"):
        hit_op["HitEffects"].append({"Type": "StatusApplication", "StatusType": "cosmoteer.heat",
                                     "StatusValue": s["heat"], "ApplyToAllHitPartTiles": True,
                                     "DivideValueByPartArea": True})
    hit_struct = {"ReduceEffectsByPenetration": True, "Offset": [0.15, 0],
                  "HitEffects": [{"Type": "Damage", "Damage": _val(s.get("struct_damage", round(s["damage"] / 4)))},
                                 {"Type": "Impulse", "Impulse": _val(max(1, s.get("impulse", 5) / 2))}],
                  "MediaEffects": _media(preset, struct=True)}
    if s.get("plasma_fx"):
        hit_struct["MediaEffects"] = PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "struct", s.get("volume", 0.6),
                                                   s.get("max_conc", 30))
    # pecas atravessadas depois da primeira: perfurante com dano proprio (50% do primeiro acerto), demais repetem
    pen_op = {"ReduceEffectsByPenetration": True,
              "HitEffects": [{"Type": "Damage", "Damage": _val(s.get("pen_damage", s["damage"]))},
                             {"Type": "StatusApplication", "StatusType": "cosmoteer.fire",
                              "StatusChance": _val(s.get("fire", 0.04)), "ValueType": "Interpolated"},
                             {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
              "MediaEffects": "&../HitOperational/MediaEffects"}
    if s.get("bolt"):
        return _bolt_kinetic(s, top, hit_op, hit_struct)
    hit = {
        "Type": "PenetratingHit",
        "Penetration": s["penetration"],
        "PenetrationSpeed": s.get("pen_speed", 25),
        **OWN_SHIP_PASS,
        "CrewCollisions": "{Enemies=true; Junk=true}",
        "PenetratesCrew": True,
        "HitCrew": "&HitOperational",
    }
    if s.get("armor_factor"):
        hit["PartCategoryPenetrationFactors"] = {"armor": f"{int(round(s['armor_factor'] * 100))}%"}
    if s.get("shield_damage") is not None or s.get("emp_shield_drain"):
        shield_fx = [{"Type": "Damage", "Damage": _val(s.get("shield_damage", s["damage"]))},
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
    hit["PenetratingStructural : &HitStructural"] = {
        "StructuralDamageRetentionPerHit": "50%", "MinStructuralDamageScale": "3%"}
    if s.get("finish_explosion"):
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
    return top


def _kinetic_components(s, hit):
    comps = {
        "Physics": {"Type": "CirclePhysics", "Radius": s.get("radius", 0.12), "Density": 0.0001},
        "Death": {"Type": "DeathByLifetime"},
        "Targetable": {"Type": "Targetable", "Health": s["health"], "TargetCategory": Q(s.get("category", "bullet")),
                       "OnDeath": {"MediaEffects": "&~/Components/Hit/HitOperational/MediaEffects"}},
        "Hit": hit,
    }
    if s.get("plasma_fx"):
        # abatido no ar: so o estouro (respingo + clarao) e um chiado baixo, sem brasa de casco nem faiscas
        comps["Targetable"]["OnDeath"]["MediaEffects"] = PFX.hit_media(s["plasma_fx"], s.get("plasma_oc"), "pop",
                                                                       s.get("volume", 0.6))
    comps.update(_sprite_components(s))
    return comps


def _bolt_kinetic(s, top, hit_op, hit_struct):
    """Disparo que se gasta no primeiro escudo/peca (plasma; spec ammo_types[plasma]: penetracao 0). Segue o raio
    laser do jogo base (laser_bolt_small.rules: PenetratingHit sem Penetration e SEM ReduceEffectsByPenetration,
    Penetrating/FinishedPenetratingOperational sem efeito): com penetracao 0 o ReduceEffectsByPenetration poderia
    cortar o dano do acerto e a explosao do overclock da Curupira. Nao vira SimpleHit porque o SimpleHit do jogo
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
    if s.get("shield_damage") is not None:
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
    hit["PenetratingStructural : &HitStructural"] = {
        "StructuralDamageRetentionPerHit": "50%", "MinStructuralDamageScale": "3%"}
    hit["FinishedPenetratingOperational"] = {}
    hit["FinishedPenetratingStructural"] = {}
    top["STAT_PENETRATION"] = 0
    top["Components"] = _kinetic_components(s, hit)
    return top


def build_explosive(s):
    """Granada que explode no impacto (naval HE, nuclear, bolha de plasma pesada)."""
    direct = s.get("damage", 0)
    exp_r, exp_total = s["explosion"]
    top = {
        "STAT_DAMAGE": direct + exp_total,
        "STAT_PENETRATION": 0,
        "ID": Q(s["id"]),
        "Range": s["range"],
        "IdealRange": [round(s["range"] * 0.3), "&~/Range"],
        "IdealRadius": [5, 50],
        "Speed": s["speed"],
    }
    preset = s.get("fx", "he")
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
    if s.get("shield_factor") is not None and s["shield_factor"] != 1:
        sh_list = []
        if direct:
            sh_list.append({"Type": "Damage", "Damage": _val(round(direct * s["shield_factor"]))})
        sh_list.append({"Type": "ExplosiveDamage", "TotalDamage": _val(round(exp_total * s["shield_factor"])),
                        "Radius": exp_r, "Filter": {"Ships": True, "Shields": True}})
        hit["HitShield"] = {"HitEffects": sh_list, "MediaEffects": "&../HitOperational/MediaEffects"}
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
        "Targetable": {"Type": "Targetable", "Health": s["health"], "TargetCategory": Q(s.get("category", "bullet")),
                       # abatido no ar: sem dano em area (como os misseis vanilla)
                       "OnDeath": {"MediaEffects": [f"&<{PARTICLES['flak'][1]}>"]}},
        "Hit": hit,
    }
    if s.get("homing"):
        comps["Homing"] = {"Type": "TargetHoming", "TurnVelocity": f"{s['homing']}d",
                           "ModifiesLinearVelocity": True, "VelocityCompensation": "100%"}
    comps.update(_sprite_components(s))
    top["Components"] = comps
    return top


# ============================================================================= misseis de conves
# Nucleo comum (copiado de shots/missile_he/missile_he.rules l.9-48, 110-123, versao "de conves"):
#   - Hit com FriendlyShipLowCollisions = false + FriendlyShipHighCollisions = false (passa por cima do
#     proprio casco e das torres de conves vizinhas; bullet_deck.rules l.41) e SourcePartCollisionDelay;
#   - Targetable categoria "missile" (PD/flak vanilla e SW:ACD derrubam); abatido = so efeito (HitFriendly);
#   - explosoes SEM Friendlies = true; numeros escalaveis como { BaseValue; EffectScaleExponent = 1 };
#   - sprite e brilho em buckets Upper (os Lower das particulas de propulsor ficariam sob o nosso teto).
# Os mesmos campos de conves vao em TODO projetil filho (submunicao, carga grudenta, ogiva, isca): nao se
# sabe se um filho de SpawnBullets herda a nave de origem (missiles_gaps §2.1/§6 Q2).
MSL_D = f"{D}/missile_he"
MSL_T = f"{D}/missile_thermal"
MSL_E = f"{D}/missile_emp"
MSL_N = f"{D}/missile_nuke"
MISSILE_MEDIA = {
    "he": {"particles": [f"{MSL_D}/particles/missile_he_hit.rules", f"{MSL_D}/particles/missile_he_flash.rules",
                         f"{MSL_D}/particles/missile_he_smoke.rules"],
           "sounds": [f"{MSL_D}/sounds/launcher_rocket_impact_0{i}.wav" for i in (1, 2, 3)],
           "plume": f"{MSL_D}/particles/missile_he_thruster_plume_light.rules"},
    "napalm": {"particles": [f"{MSL_T}/particles/missile_thermal_hit_cone.rules",
                             f"{MSL_T}/particles/missile_thermal_shockwave.rules",
                             f"{MSL_T}/particles/missile_thermal_flash.rules"],
               "sounds": [f"{MSL_T}/missile_thermal_hit.wav"],
               "plume": f"{MSL_T}/particles/missile_thermal_thruster_plume_light.rules"},
    # missile_emp.rules l.198-213 (orbe/raios/onda de choque; buckets Disruptor*/Upper4)
    "emp": {"particles": [f"{MSL_E}/particles/missile_emp_hit_orb.rules", f"{MSL_E}/particles/missile_emp_hit_bolts.rules",
                          f"{MSL_E}/particles/missile_emp_hit_shockwave.rules"],
            "sounds": [f"{MSL_E}/sounds/launcher_emp_impact_0{i}.wav" for i in (1, 2)],
            "plume": f"{MSL_E}/particles/missile_emp_thruster_plume_light.rules"},
    # cogumelo da Boiuna (bs_shot_nuke_howitzer_nuclear = missile_nuke_stage1.rules l.163-169)
    "nuclear": {"particles": [f"{MSL_N}/particles/missile_nuke_flash_light.rules", f"{MSL_N}/particles/missile_nuke_flash.rules",
                              f"{MSL_N}/particles/missile_nuke_shockwave.rules", f"{MSL_N}/particles/missile_nuke_hit.rules"],
                "sounds": [f"{MSL_N}/missile_nuke_hit.wav"],
                "plume": f"{MSL_N}/particles/missile_nuke_thruster_plume_light.rules"},
    # abatida / fiasco da Iara: so o clarao (HitFriendly do missile_nuke_stage1.rules l.190-200)
    "nuclear_fizzle": {"particles": [f"{MSL_N}/particles/missile_nuke_flash.rules"], "sounds": [f"{MSL_N}/missile_nuke_hit.wav"]},
    # abertura da Piranha (clarao em petalas): clarao + fumaca, sem a bola de fogo do impacto
    "burst": {"particles": [f"{MSL_D}/particles/missile_he_flash.rules", f"{MSL_D}/particles/missile_he_smoke.rules"],
              "sounds": [f"{MSL_D}/sounds/launcher_rocket_impact_0{i}.wav" for i in (1, 2, 3)]},
    # Carrapato gruda: "clank" metalico + clarao (sem explosao: a carga explode depois)
    "clank": {"particles": [f"{D}/bullet_med/particles/bullet_hit_med_sparks.rules",
                            f"{D}/bullet_med/particles/bullet_flash_med.rules", f"{MSL_D}/particles/missile_he_flash.rules"],
              "sounds": SOUNDS["med"]},
    # isca: estalo pequeno, sem dano
    "pop": {"particles": [f"{MSL_D}/particles/missile_he_flash.rules"],
            "sounds": [f"{MSL_D}/sounds/launcher_rocket_impact_0{i}.wav" for i in (1, 2, 3)]},
}
MEDIA_OF = {"cluster": "he", "limpet": "he", "torpedo": "he"}
# descarga do PEM (missile_emp.rules l.165-178)
EMP_DRAIN_MEDIA = [f"{MSL_E}/particles/missile_emp_hit_sizzle.rules", f"{MSL_E}/particles/missile_emp_lightning.rules",
                   f"{MSL_E}/particles/missile_emp_drain.rules"]
EMP_DRAIN_SOUNDS = [f"{D}/disruptor_bolt/sounds/disruptor_discharge_0{i}.wav" for i in (1, 2, 3, 4)]
# luzes vermelhas piscando da mina vanilla (mine_deployed.rules l.179-197): o "bip" do Carrapato
LIMPET_BLINK = f"{D}/mine/mine_small_lights.png"
LIMPET_STATUS_FX = "./Data/statuses/disruptor_drain/particles/electron_sizzle.rules"


def _missile_media(s, shake=True, key=None):
    mm = MISSILE_MEDIA[key or MEDIA_OF.get(s["payload"], s["payload"])]
    media = [f"&<{p}>" for p in mm["particles"]]
    media.append(Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(x) for x in mm["sounds"]],
                                                   "Volume": s.get("volume", 0.7), "SpeedVariation": 0.15,
                                                   "MaxConcurrent": s.get("max_conc", 16)}))
    if shake and s.get("shake"):
        media.append(Inh("/BASE_SHAKE", {"ShakeAmount": s["shake"], "Duration": 0.5}))
    return media


def _deck_flags(s, hit_type="SimpleHit"):
    v = s.get("variants", {})
    delay = "0.3" if v.get("source_part_collision_delay") == "s_0_3" else "1.5 / (&/Simulation/PhysicsUpdatesPerSecond)"
    return {"Type": hit_type, "SourcePartCollisionDelay": delay, **OWN_SHIP_PASS}


def _missile_hit(s, hit_op, hit_shield, friendly_key=None):
    hit = _deck_flags(s)
    hit["HitShield"] = hit_shield if hit_shield is not None else "&HitOperational"
    hit["HitOperational"] = hit_op
    hit["HitStructural"] = "&HitOperational"
    hit["HitFriendly"] = {"MediaEffects": _missile_media(s, shake=False, key=friendly_key)}
    return hit


def _homing(s, turn, delay):
    v = s.get("variants", {})
    homing = {"Type": "TargetHoming", "TurnVelocity": f"{turn}d"}
    if delay is not None:
        homing["Delay"] = delay
    if v.get("homing_avoidance") == "raycast_250":
        homing["AvoidanceRaycastDistance"] = 250
    elif v.get("homing_avoidance") == "no_avoid_friendlies":
        homing["AvoidsFriendlies"] = False
    homing["VelocityCompensation"] = "60%"
    return homing


def _glow_sprite(w, color, size):
    return {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": 0, "IsLight": True,
            "Offset": [round(-w * 0.45, 3), 0],
            "Sprite": {**GLOW, "Size": size, "VertexColor": color, "TargetBlendMode": "Add",
                       "Shader": Q("./Data/common_effects/fancy_light.shader"),
                       "_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 24,
                       "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": 0.125}}


def _missile_visuals(s, glow=True, plume=True):
    """Corpo (missile_he.png escalado, BulletUpper3) + brilho da cor do tipo (Upper4) + luz do propulsor (Upper4)."""
    w, h = s["sprite_wh"]
    comps = {"Sprite": {"Type": "Sprite", "RenderBucket": "BulletUpper3", "IsLit": True,
                        "Sprite": {"Texture": {"File": Q(f"{MSL_D}/missile_he.png"), "MipLevels": "max"}, "Size": [w, h]},
                        "NormalsTexture": {"File": Q(f"{MSL_D}/missile_he_normals.png"), "MipLevels": "max"}}}
    if glow:
        comps["GlowSprite"] = _glow_sprite(w, s["glow_color"], s["glow_size"])
    if plume:
        mm = MISSILE_MEDIA[s.get("plume_key") or MEDIA_OF.get(s["payload"], s["payload"])]
        comps["MediaEffects"] = {"Type": "MediaEffects", "Offset": [s["plume_offset"], 0], "Rotation": "180d",
                                 "MediaEffects": [f"&<{mm['plume']}>"]}
    return comps


def _targetable(hp):
    # abatido no ar: so o efeito, sem dano em area ("No AOE damage when shot down", missile_he.rules l.116)
    return {"Type": "Targetable", "Health": hp, "TargetCategory": Q("missile"), "OnDeath": "&../Hit/HitFriendly"}


def _arc(deg_pair):
    return [f"{a}d" for a in deg_pair]


def _proximity_accel(rng, accel, ships, bullets, friendlies, enemies, categories=None):
    """ProximityAcceleration: ima (buzzdroid.rules l.37-44) ou afastamento entre misseis (mine.rules l.20-30)."""
    e = {"Type": "ProximityAcceleration", "Range": rng, "Acceleration": accel, "AccelerateTowardsShips": ships,
         "AccelerateTowardsBullets": bullets}
    if categories:
        e["AccelerateTowardsBulletCategories"] = list(categories)
    e["AccelerateTowardsFriendlies"] = friendlies
    e["AccelerateTowardsEnemies"] = enemies
    return e


# ----------------------------------------------------------------------------- cargas (payloads)
def _payload_he(s):
    d = s["damage"]
    fx = [{"Type": "ExplosiveDamage", "TotalDamage": _val(d["ExplosiveDamage"]), "Radius": d["Radius"]},
          {"Type": "Impulse", "Impulse": _val(d.get("Impulse", 0))}]
    stats = {"STAT_DAMAGE": d["ExplosiveDamage"], "STAT_RADIUS": d["Radius"]}
    return {"stats": stats, "hit": _missile_hit(s, {"HitEffects": fx, "MediaEffects": _missile_media(s)}, None)}


def _payload_napalm(s):
    """Taturana: explosao pequena sem fogo embutido (o fogo interpolado de ExplosiveDamage muda entre
    0.30.4 e 0.30.5) + fogo garantido na peca (bullet_med.rules l.129-132 / bullet_large_overclock_shrapnel
    l.113-114) + poca de calor que reacende (missile_thermal.rules l.128-139, com valor literal)."""
    d = s["damage"]
    v = s.get("variants", {})
    fire = {"Type": "StatusApplication", "StatusType": "cosmoteer.fire", "StatusChance": _val(d["fire_StatusChance"]),
            "StatusValue": d["fire_StatusValue_interpolated"], "ValueType": "Interpolated"}
    if v.get("napalm_fire") == "all_hit_part_tiles":
        fire["ApplyToAllHitPartTiles"] = True
    heat_pool = {"Type": "GridStatusApplication", "StatusType": "cosmoteer.heat", "StatusValue": 0,
                 "StatusValuePool": d["heat_StatusValuePool"], "ValueFalloff": 1, "MaxCost": d["heat_MaxCost"],
                 "FalloffPadding": 0.5, "EmptyTileCost": 1000, "AllowDiagonals": True,
                 "Filter": {"Friendlies": False, "TargetedFriendlies": True}}
    blast = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["blast_ExplosiveDamage"]), "Radius": d["blast_radius"]}
    fx = [blast, fire]
    if v.get("napalm_gel") == "on":
        # SO no build de teste T15 (variante napalm_gel=on): "gel" GridStatusApplication de fogo (fire.rules
        # l.121-158), valores iniciais derivados dos numeros do spec (chance da peca, valor bruto = % x 75)
        pct = float(str(d["fire_StatusValue_interpolated"]).rstrip("%")) / 100
        fx.append({"Type": "GridStatusApplication", "StatusType": "cosmoteer.fire",
                   "StatusChance": _val(d["fire_StatusChance"]), "StatusValue": round(pct * 75, 2),
                   "MaxCost": d["heat_MaxCost"], "AllowDiagonals": True, "BlockedByWalls": True,
                   "Filter": {"Friendlies": False, "TargetedFriendlies": True}})
    fx.append(heat_pool)
    hit_op = {"HitEffects": fx, "MediaEffects": _missile_media(s)}
    shield_blast = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["shield_blast"]), "Radius": d["blast_radius"]}
    hit_shield = {"HitEffects": [shield_blast,
                                 {"Type": "StatusApplication", "StatusType": "cosmoteer.heat", "StatusValue": d["shield_heat"],
                                  "ApplyToAllHitPartTiles": True, "DivideValueByPartArea": True}],
                  "MediaEffects": "&../HitOperational/MediaEffects"}
    stats = {"STAT_DAMAGE": d["blast_ExplosiveDamage"], "STAT_RADIUS": d["blast_radius"],
             "STAT_HEAT_POOL": d["heat_StatusValuePool"], "STAT_FIRE_CHANCE": d["fire_StatusChance"]}
    return {"stats": stats, "hit": _missile_hit(s, hit_op, hit_shield)}


def _child(s, role):
    return next(c for c in s.get("children", []) if c["role"] == role)


def _payload_cluster(s):
    """Piranha (forma do MIRV Discord do SW, missile_discord.rules l.48-96/170-172, em tipos vanilla): o
    portador NAO tem ogiva; tres gatilhos abrem o cardume (proximidade 25 m, tempo de vida, impacto)."""
    d, p, v = s["damage"], s["params"], s.get("variants", {})
    child = _child(s, "child")
    b = p["burst"]
    spawn = {"Type": "SpawnBullets", "Bullet": "&~/CHILD", "Count": d["children"], "Distance": list(b["Distance"]),
             "Arc": _arc(b["Arc_deg"]), "Spread": _arc(b["Spread_deg"]), "InheritVelocity": b["InheritVelocity"],
             "HealthFactor": _val(b["HealthFactor"])}
    if v.get("cluster_randomize_target") == "on":
        spawn["RandomizeTarget"] = True          # experimento T11 (nunca no build padrao)
    root = {"CHILD": f"&<{child['file']}.rules>",
            "BURST": {"HitEffects": [spawn], "MediaEffects": _missile_media(s, shake=False, key="burst")}}
    pf = p["proximity_fuse"]
    start = pf["StartDelay_magnet_only"] if v.get("cluster_children") == "magnet_only" else pf["StartDelay"]
    death = {
        "ProximityFuse": {"Type": "DeathByEnemyProximity", "Interval": pf["Interval"], "Range": d["proximity_range"],
                          "StartDelay": start, "DetectsShips": pf["DetectsShips"], "DetectsBullets": pf["DetectsBullets"],
                          "FactorEffectsWith": pf["FactorEffectsWith"], "OnDeath": "&~/BURST"},
        # os tres caminhos do BURST passam o HP que restou ao portador para os filhotes (HealthFactor sempre com
        # FactorEffectsWith = Targetable: missile_nuke_stage1.rules DeployDeath, mine.rules DeployDeath)
        "TimedFuse": {"Type": "DeathByLifetime", "Lifetime": s["lifetime"], "FactorEffectsWith": pf["FactorEffectsWith"],
                      "OnDeath": "&~/BURST"},
    }
    hit = _deck_flags(s)
    if v.get("cluster_hp_inherit", "all_paths") == "all_paths":
        # impacto direto: o SimpleHit tambem escala os efeitos pelo Targetable (campo FactorEffectsWith do hit, como
        # o PenetratingHit de laser_bolt_large.rules); o BURST so tem o HealthFactor escalavel
        hit["FactorEffectsWith"] = pf["FactorEffectsWith"]
    hit.update({"HitShield": "&~/BURST", "HitOperational": "&~/BURST", "HitStructural": "&~/BURST",
                "HitFriendly": {"MediaEffects": _missile_media(s, shake=False, key="burst")}})
    stats = {"STAT_DAMAGE": d["child_total"], "STAT_RADIUS": d["child_radius"], "STAT_CHILDREN": d["children"],
             "STAT_CHILD_DAMAGE": d["child_ExplosiveDamage"], "STAT_CHILD_HP": d["child_hp"],
             "STAT_BURST_RANGE": d["proximity_range"]}
    return {"stats": stats, "root": root, "death": death, "hit": hit}


def _limpet_blast(s):
    d = s["damage"]
    pct = int(round(float(str(d["charge_CrewKillChance"]).rstrip("%"))))
    # CrewKillChance: campo vanilla de ExplosiveDamage (missile_launcher_he.rules l.308)
    return [{"Type": "ExplosiveDamage", "TotalDamage": _val(d["charge_ExplosiveDamage"]), "Radius": d["charge_radius"],
             "CrewKillChance": f"{pct}%"}]


def _payload_limpet(s):
    """Carrapato: gruda (carga filha) e explode 2,5 s depois; em escudo so estoura (nao gruda em bolha).
    limpet_anchor: F1 broca lenta + ima (padrao) | F1_drill sem ima | F2 status de peca | F3 carga
    parada no referencial do alvo | F4 explosao no impacto. Mesma espoleta, explosao e raio em todos."""
    d, p, v = s["damage"], s["params"], s.get("variants", {})
    anchor = v.get("limpet_anchor", "F1")
    impact = {"Type": "Damage", "Damage": _val(d["impact_Damage"])}
    impulse = {"Type": "Impulse", "Impulse": _val(p["impact"]["Impulse"])}
    root = {}
    hit_op = {"Offset": list(p["impact"]["Offset"])}
    media_key = "clank"
    if s.get("repeating"):
        # variante isolada so-SW (Type = Repeating: missile_intruder.rules l.130-134 do SW:ACD)
        r = p["repeating_isolated"]
        fx = [impact, {"Type": "Repeating", "Count": r["Count"], "Interval": r["Interval"],
                       "InitialDelay": r["InitialDelay"], "RequireHitPart": r["RequireHitPart"],
                       "HitEffects": _limpet_blast(s), "MediaEffects": _missile_media(s)}, impulse]
    elif anchor in ("F1", "F1_drill", "F3"):
        charge = _child(s, "charge")
        root["CHARGE"] = f"&<{charge['file']}.rules>"
        if anchor == "F3":
            hit_op["FrameOfReference"] = "HitObject"
        fx = [impact, {"Type": "SpawnBullets", "Bullet": "&~/CHARGE", "Count": 1, "Distance": 0, "Spread": ["0d", "0d"],
                       "InheritVelocity": anchor == "F3"}, impulse]
    elif anchor == "F2":
        st = s["status"]
        fx = [impact, {"Type": "StatusApplication", "StatusType": st["id"], "StatusDuration": st["duration"],
                       "StatusValue": st["value"]}, impulse]
    else:  # F4: ultimo recurso, a mesma explosao no impacto
        fx = [impact] + _limpet_blast(s) + [impulse]
        media_key = None
    hit_op["HitEffects"] = fx
    hit_op["MediaEffects"] = _missile_media(s, key=media_key)
    hit_shield = {"HitEffects": [{"Type": "ExplosiveDamage", "TotalDamage": _val(d["shield_pop_ExplosiveDamage"]),
                                  "Radius": d["shield_pop_radius"]}],
                  "MediaEffects": _missile_media(s)}
    stats = {"STAT_DAMAGE": d["impact_Damage"] + d["charge_ExplosiveDamage"], "STAT_RADIUS": d["charge_radius"],
             "STAT_CHARGE_DAMAGE": d["charge_ExplosiveDamage"], "STAT_FUSE": d["fuse_s"]}
    out = {"stats": stats, "hit": _missile_hit(s, hit_op, hit_shield)}
    if root:
        out["root"] = root
    return out


def _payload_emp(s):
    """Poraque (missile_emp.rules l.151-196, escalado para 1500 de dreno por peca PEM; filtros SEM Friendlies)."""
    d, p, v = s["damage"], s["params"], s.get("variants", {})
    dr = p["drain"]
    drain = {"Type": "ExplosiveResourceDrain", "ResourceType": dr["ResourceType"],
             "TotalDrain": _val(d["battery_TotalDrain"]), "Radius": d["drain_radius"], "Slices": dr["Slices"],
             "Filter": dict(dr["Filter"]), "MediaEffectsOnDrainFactor": dr["MediaEffectsOnDrainFactor"],
             "MediaEffectsOnDrain": [f"&<{x}>" for x in EMP_DRAIN_MEDIA] +
                                    [Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(x) for x in EMP_DRAIN_SOUNDS],
                                                                        "Volume": 1, "SpeedVariation": 0.2,
                                                                        "MaxConcurrent": s.get("max_conc", 16)})]}
    direct = {"Type": "Damage", "Damage": _val(d["direct_Damage"])}
    struct = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["structural_ExplosiveDamage"]), "Radius": d["structural_radius"],
              "Filter": {"OperationalHealth": False, "StructuralHealth": True}}
    tail = [direct, struct]
    if v.get("emp_rider", "on") == "on":
        r = p["rider"]
        tail.append({"Type": "StatusApplication", "StatusType": r["StatusType"], "StatusDuration": r["StatusDuration"],
                     "StatusValue": _val(r["StatusValue"])})
    hit_op = {"HitEffects": [drain] + tail, "MediaEffects": _missile_media(s)}
    hit_shield = None
    if v.get("emp_shield_drain") == "single_part":
        # fallback T16: o dreno em area pode nao alcancar o gerador pela borda da bolha
        hit_shield = {"HitEffects": [{"Type": "ResourceDrain", "ResourceType": dr["ResourceType"],
                                      "Amount": _val(d["battery_TotalDrain"]), "TreatShieldAsPart": True,
                                      "MediaEffectsOnDrain": drain["MediaEffectsOnDrain"]}] + tail,
                      "MediaEffects": "&../HitOperational/MediaEffects"}
    stats = {"STAT_DAMAGE": d["direct_Damage"] + d["structural_ExplosiveDamage"], "STAT_RADIUS": d["structural_radius"],
             "STAT_DRAIN": d["battery_TotalDrain"], "STAT_DRAIN_RADIUS": d["drain_radius"]}
    return {"stats": stats, "hit": _missile_hit(s, hit_op, hit_shield)}


def _torpedo_hit(s):
    """Ogiva do Boto/Iara (forma de missile_nuke_stage1.rules l.141-176, literais, SEM Friendlies):
    explosao em expansao operacional + explosao so estrutural; no escudo so o bloco operacional."""
    d, p = s["damage"], s["params"]
    ex = p["expand"]
    exp = {"ExpandDuration": ex["ExpandDuration"], "ExpandStartRadius": ex["ExpandStartRadius"], "ExpandLoss": ex["ExpandLoss"]}
    op = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["warhead_operational"]), "Radius": d["op_radius"], **exp}
    if p.get("impulse"):
        op.update({"ImpulsePerNDamage": p["impulse"]["ImpulsePerNDamage"], "NDamage": p["impulse"]["NDamage"]})
    op["Filter"] = {"OperationalHealth": True, "StructuralHealth": False}
    st = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["warhead_structural"]), "Radius": d["struct_radius"], **exp,
          "Filter": {"OperationalHealth": False, "StructuralHealth": True}}
    nuclear = s["payload"] == "nuclear"
    hit_op = {"HitEffects": [op, st], "MediaEffects": _missile_media(s)}
    hit_shield = {"HitEffects": [dict(op)], "MediaEffects": "&../HitOperational/MediaEffects"}
    return _missile_hit(s, hit_op, hit_shield, friendly_key="nuclear_fizzle" if nuclear else None)


def _torpedo_stats(s):
    d = s["damage"]
    return {"STAT_DAMAGE": d["warhead_operational"] + d["warhead_structural"], "STAT_RADIUS": d["op_radius"],
            "STAT_STRUCT_RADIUS": d["struct_radius"], "STAT_DECOYS": d["decoys"], "STAT_DECOY_HP": d["decoy_hp"]}


def _payload_torpedo(s):
    """Boto / Iara: estagio de lancamento (1,5 s) -> ogiva + N iscas por dois SpawnBullets no mesmo OnDeath
    (padrao do missile_nuke_stage1.rules l.31-50). Impacto antes do fim do estagio ja detona (Hit da ogiva).
    torpedo_decoys=emitter: torpedo de um estagio; as iscas saem de um segundo emissor do lancador."""
    v = s.get("variants", {})
    if v.get("torpedo_decoys") == "emitter":
        return {"stats": _torpedo_stats(s), "hit": _torpedo_hit(s)}
    p = s["params"]
    wh, dc = _child(s, "warhead"), _child(s, "decoy")
    sd = p["spawn_decoys"]
    ls = p["launch_stage"]
    root = {"WARHEAD": f"&<{wh['file']}.rules>", "DECOY": f"&<{dc['file']}.rules>"}
    deploy = {"Type": "DeathByLifetime", "Lifetime": ls["Lifetime"], "FactorEffectsWith": ls["FactorEffectsWith"],
              "OnDeath": {"HitEffects": [
                  {"Type": "SpawnBullets", "Bullet": "&~/WARHEAD", "Count": 1, "InheritVelocity": p["warhead"]["InheritVelocity"],
                   "HealthFactor": _val(p["warhead"]["HealthFactor"])},
                  {"Type": "SpawnBullets", "Bullet": "&~/DECOY", "Count": s["damage"]["decoys"], "Distance": list(sd["Distance"]),
                   "Arc": _arc(sd["Arc_deg"]), "Spread": _arc(sd["Spread_deg"]), "InheritVelocity": sd["InheritVelocity"]},
              ]}}
    return {"stats": _torpedo_stats(s), "root": root, "death": {"Deploy": deploy},
            "hit": f"&<{wh['file']}.rules>/Components/Hit"}


MISSILE_PAYLOADS = {"he": _payload_he, "napalm": _payload_napalm, "cluster": _payload_cluster,
                    "limpet": _payload_limpet, "emp": _payload_emp, "torpedo": _payload_torpedo,
                    "nuclear": _payload_torpedo}


def build_missile(s):
    """Missil de conves (arquivo que o lancador dispara): nucleo comum + carga (s['payload'])."""
    pl = MISSILE_PAYLOADS[s["payload"]](s)
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
    return top


# ----------------------------------------------------------------------------- projeteis filhos
def build_cluster_child(c):
    """Submunicao da Piranha: homing tardio e fraco + ima de casco (buzz droid) + afastamento (mina);
    um brilho barato (desempenho). cluster_children=magnet_only: sem TargetHoming, so o ima."""
    v = c.get("variants", {})
    p = c["params"]["child"]
    top = {"STAT_DAMAGE": c["damage"], "STAT_RADIUS": c["radius"], "ID": Q(c["id"]), "Range": c["range"],
           "IdealRange": c["range"], "Speed": c["speed"]}
    comps = {"Physics": {"Type": "BoxPhysics", "Size": list(c["box"]), "Density": 0.1}}
    if v.get("cluster_children") != "magnet_only":
        comps["Homing"] = _homing(c, c["turn"], c["homing_delay"])
        comps["Retarget"] = {"Type": "SameShipRetarget"}
    comps["Acceleration"] = {"Type": "Acceleration", "Acceleration": c["accel"]}
    m = p["magnet"]
    comps["Magnet"] = _proximity_accel(m["Range"], m["Acceleration"], True, False, False, True)
    strip = v.get("performance_strip") == "on"
    if not strip:
        sp = p["spacing"]
        comps["Spacing"] = _proximity_accel(sp["Range"], sp["Acceleration"], False, True, True, False, sp["BulletCategories"])
    comps["DeathByLifetime"] = {"Type": "DeathByLifetime", "Lifetime": c["lifetime"]}
    comps.update(_missile_visuals(c, glow=not strip, plume=False))
    comps["Targetable"] = _targetable(c["hp"])
    fx = [{"Type": "ExplosiveDamage", "TotalDamage": _val(c["damage"]), "Radius": c["radius"]},
          {"Type": "Impulse", "Impulse": _val(p["impulse"])}]
    comps["Hit"] = _missile_hit(c, {"HitEffects": fx, "MediaEffects": _missile_media(c)}, None)
    top["Components"] = comps
    return top


def build_limpet_charge(c):
    """Carga do Carrapato (receita do buzz droid do SW em tipos vanilla: ima buzzdroid.rules l.37-44 +
    PenetratingHit lento l.78-81): fica no casco e explode pela espoleta (DeathByLifetime -> BLAST).
    SEM Targetable no padrao (regra do usuario; e o PD da vitima nao atira no proprio casco)."""
    v = c.get("variants", {})
    p = c["params"]["charge"]
    top = {"STAT_DAMAGE": c["damage"]["charge_ExplosiveDamage"], "STAT_RADIUS": c["damage"]["charge_radius"],
           "STAT_FUSE": c["damage"]["fuse_s"], "ID": Q(c["id"]), "Range": 0, "IdealRange": 0, "Speed": c["speed"],
           "BLAST": {"HitEffects": _limpet_blast(c), "MediaEffects": _missile_media(c)}}
    comps = {"Physics": {"Type": "CirclePhysics", "Radius": p["radius"], "Density": p["density"]}}
    if v.get("limpet_anchor", "F1") == "F1":
        m = p["magnet"]
        comps["Magnet"] = _proximity_accel(m["Range"], m["Acceleration"], True, False, False, True)
    comps["Fuse"] = {"Type": "DeathByLifetime", "Lifetime": c["damage"]["fuse_s"], "OnDeath": "&~/BLAST"}
    bs = c["blink_size"]
    comps["Sprite"] = {"Type": "AnimatedSprite", "RenderBucket": "BulletUpper3",
                       "Animation": {"AtlasSprite": {"Texture": {"File": Q(LIMPET_BLINK), "MipLevels": "max"},
                                                     "Size": [bs, bs], "TargetBlendMode": "Add"},
                                     "FrameCount": 6, "FrameSize": [128, 128], "FramesPerRow": 6,
                                     "FramesPerSecond": 7}}
    comps["GlowSprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": 0, "IsLight": True,
                           "Sprite": {**GLOW, "Size": [bs, bs], "VertexColor": c["glow_color"], "TargetBlendMode": "Add",
                                      "Shader": Q("./Data/common_effects/fancy_light.shader"),
                                      "_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 24,
                                      "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": 0.125}}
    if v.get("limpet_defusable") == "on":
        comps["Targetable"] = {"Type": "Targetable", "Health": c["defusable_hp"], "TargetCategory": Q("missile"),
                               "OnDeath": {"MediaEffects": _missile_media(c, shake=False, key="pop")}}
    hit = _deck_flags(c, "PenetratingHit")
    hit.update({"Penetration": p["Penetration"], "PenetrationSpeed": p["PenetrationSpeed"],
                "ShieldCollisions": {"Shields": False},
                "HitOperational": {}, "HitStructural": "&HitOperational",
                "PenetratingOperational": {}, "PenetratingStructural": {},
                "FinishedPenetratingOperational": {}, "FinishedPenetratingStructural": {}})
    comps["Hit"] = hit
    top["Components"] = comps
    return top


def build_torpedo_warhead(w):
    """Ogiva (2o estagio do Boto/Iara): Speed 0 + InheritVelocity (herda o estagio), homing 90d."""
    top = {"STAT_DAMAGE": w["damage"]["warhead_operational"] + w["damage"]["warhead_structural"],
           "STAT_RADIUS": w["damage"]["op_radius"], "ID": Q(w["id"]), "Range": w["range"], "IdealRange": w["range"],
           "Speed": 0}
    comps = {
        "Physics": {"Type": "BoxPhysics", "Size": list(w["box"]), "Density": 0.1},
        "Homing": _homing(w, w["turn"], None),
        "Retarget": {"Type": "SameShipRetarget"},
        "Acceleration": {"Type": "Acceleration", "Acceleration": w["accel"]},
        "DeathByLifetime": {"Type": "DeathByLifetime", "Lifetime": w["lifetime"]},
    }
    comps.update(_missile_visuals(w))
    comps["Targetable"] = _targetable(w["hp"])
    comps["Hit"] = _torpedo_hit(w)
    top["Components"] = comps
    return top


def build_torpedo_decoy(c):
    """Isca do Boto/Iara: parece o torpedo, gasta tiros de PD e piscinas de flak; SimpleHit sem dano."""
    p = c["params"]["decoy"]
    top = {"STAT_DAMAGE": 0, "ID": Q(c["id"]), "Range": c["range"], "IdealRange": c["range"], "Speed": c["speed"]}
    sp = p["spacing"]
    comps = {
        "Physics": {"Type": "BoxPhysics", "Size": list(c["box"]), "Density": 0.1},
        "Homing": _homing(c, c["turn"], c["homing_delay"]),
        "Retarget": {"Type": "SameShipRetarget"},
        "Acceleration": {"Type": "Acceleration", "Acceleration": c["accel"]},
        "Spacing": _proximity_accel(sp["Range"], sp["Acceleration"], False, True, True, False, sp["BulletCategories"]),
        "DeathByLifetime": {"Type": "DeathByLifetime", "Lifetime": c["lifetime"]},
    }
    comps.update(_missile_visuals(c))
    comps["Targetable"] = _targetable(c["hp"])
    hit = _deck_flags(c)
    hit.update({"HitShield": "&HitOperational", "HitOperational": {"MediaEffects": _missile_media(c, shake=False, key="pop")},
                "HitStructural": "&HitOperational",
                "HitFriendly": {"MediaEffects": _missile_media(c, shake=False, key="pop")}})
    comps["Hit"] = hit
    top["Components"] = comps
    return top


MISSILE_CHILD_BUILDERS = {"child": build_cluster_child, "charge": build_limpet_charge,
                          "warhead": build_torpedo_warhead, "decoy": build_torpedo_decoy}


def build_missile_part(c):
    """Arquivo filho de um missil (mesma pasta; referenciado pelo nome relativo, como o flak_oc)."""
    return MISSILE_CHILD_BUILDERS[c["role"]](c)


def build_limpet_status(st):
    """F2 do Carrapato: status de PECA proprio (molde statuses/disruptor_drain: Layer = Part; ApplyNewInstance;
    TickInterval; ParentMediaEffectsToShip). Um tique em TickInterval = a mesma explosao da carga.
    So entra no build com limpet_anchor=F2 (depois do teste T14b); registrado por AddMany no statuses.rules."""
    return {
        "ID": st["id"],
        "Layer": "Part",
        "StatusCombineMode": "ApplyNewInstance",
        "TickInterval": st["tick"],
        "TickingEffects": [{"Type": "ExplosiveDamage", "TotalDamage": _val(st["damage"]), "Radius": st["radius"],
                            "CrewKillChance": st["crew_kill"],
                            # efeito de status: a fonte e a propria nave (disruptor_drain.rules l.17-22)
                            "Filter": {"Friendlies": True, "Neutrals": True, "Self": True}}],
        "ParentMediaEffectsToShip": True,
        "ContinuousMediaEffects": [f"&<{LIMPET_STATUS_FX}>"],
    }


def build_flak_beam(s):
    """Rajada antiprojetil: feixe instantaneo ate o ponto mirado + explosao em area (flak_large.rules)."""
    cats = s["categories"]
    top = {
        "STAT_DAMAGE": s["vs_shots"],
        "STAT_RADIUS": s["radius"],
        "Range": s["range"],
        "IdealRange": round(s["range"] * 0.9),
        "ClipRangeToTarget": True,
        "RandomOffsetRadius": s.get("offset", [0.5, 3]),
        # passa por cima do casco (Low) e das nossas torres (High): manipulator_beam.rules l.5-6. Sem isso a
        # rajada parava na primeira torre nossa no caminho e a explosao saia em cima dela (R5)
        **OWN_SHIP_PASS,
    }
    fx = [
        {"Type": "ExplosiveDamage", "TotalDamage": _val(s["vs_shots"]), "Radius": s["radius"], "Slices": 1,
         "Filter": {"Ships": False, "Shields": False, "Bullets": True, "OnlyBulletCategories": cats, "Crew": True}},
    ]  # so defesa: sem a 2a explosao contra naves e escudos da flak vanilla
    if s.get("spawn_cloud"):
        fx.append({"Type": "SpawnBullets", "Bullet": f"&<{s['spawn_cloud']}>", "Count": 1})
    media = [f"&<{p}>" for p in PARTICLES["flak"][: s.get("particles", 2)]]
    media.append(_sound("flak", s.get("volume", 0.3), s.get("max_conc", 10), 0.25))
    top["HitNothing"] = {"HitEffects": fx, "MediaEffects": media}
    top["HitShield"] = "&HitNothing"
    top["HitOperational"] = "&HitNothing"
    top["HitStructural"] = "&HitNothing"
    return top


def _cloud_filter(s):
    """Variante ciws_vs_own_missiles=enemies_only (fallback NAO comprovado do T09): filtro de projeteis so de
    inimigos na nuvem (formato do BulletCollisions do pd_shot.rules l.92-99, sem Friendlies). O jogo base so usa
    esse grupo em SimpleHit/PenetratingHit, nunca em VolumeHit, entao pode nao ter efeito. Padrao as_is: nuvem como
    a vanilla, sem o grupo."""
    if not s.get("enemies_only"):
        return {}
    return {"BulletCollisions": {"Enemies": True, "Junk": True, "Neutrals": True, "Friendlies": False}}


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
    return top
