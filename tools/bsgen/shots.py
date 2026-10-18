"""Gerador dos projeteis (shots) do Bullet Strike.

Estrutura copiada de shots/bullet_med, bullet_deck, missile_he, disruptor_bolt e flak_large (0.30.x).
Cada arquivo define constantes STAT_DAMAGE / STAT_PENETRATION na raiz: o jogo ignora campos
desconhecidos e as estatisticas das pecas leem esses valores (evita caminhos frageis).
"""

from rules_dsl import Q, Inh

D = "./Data/shots"

SOUNDS = {
    "mg": [f"{D}/chaingun_shot/sounds/chain_gun_impact_0{i}.wav" for i in range(1, 6)],
    "med": [f"{D}/bullet_med/sounds/cannon_impact_0{i}.wav" for i in range(1, 5)],
    "large": [f"{D}/bullet_large/sounds/large_cannon_impact_0{i}.wav" for i in range(1, 4)],
    "deck": [f"{D}/bullet_deck/sounds/deck_cannon_impact_0{i}.wav" for i in range(1, 4)],
    "he": [f"{D}/missile_he/sounds/launcher_rocket_impact_0{i}.wav" for i in range(1, 4)],
    "nuke": [f"{D}/missile_nuke/missile_nuke_hit.wav"],
    "emp": [f"{D}/disruptor_bolt/sounds/disruptor_impact_0{i}.wav" for i in range(1, 5)],
    "plasma": [f"{D}/bullet_railgun/sounds/railgun_impact_0{i}.wav" for i in range(1, 4)],
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
    "emp_drain": [f"{D}/disruptor_bolt/particles/ship_drain.rules", f"{D}/disruptor_bolt/particles/disruptor_bolt_hit_sizzle.rules"],
    "plasma": [f"{D}/bullet_railgun/particles/bullet_hit_railgun.rules", f"{D}/bullet_railgun/particles/bullet_railgun_sparks.rules",
               f"{D}/bullet_railgun/particles/bullet_flash_railgun.rules"],
    "plasma_struct": [f"{D}/bullet_railgun/particles/bullet_hit_struct_railgun.rules",
                      f"{D}/bullet_railgun/particles/bullet_hit_struct_railgun_sparks.rules"],
    "flak": [f"{D}/flak_large/particles/flak_large_shrapnel.rules", f"{D}/flak_large/particles/flak_large_flash.rules",
             f"{D}/flak_large/particles/flak_large_smoke.rules"],
}

TRAILS = {
    "med": f"{D}/bullet_med/particles/bullet_trail_med.rules",
    "large": f"{D}/bullet_large/particles/bullet_trail_large.rules",
    "deck": f"{D}/bullet_deck/particles/bullet_trail_deck.rules",
    "plasma": f"{D}/bullet_railgun/particles/bullet_trail_railgun.rules",
}

GLOW = {
    "Texture": {"File": Q("./Data/common_effects/particles/blob.png"), "MipLevels": "max", "SampleMode": "Linear"},
}


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


def _sprite_components(s):
    """Sprite principal + brilho aditivo (bullet_med.rules l.155-197, bullet_deck l.156-210)."""
    comps = {}
    look = s.get("look", "med")
    size = s.get("sprite_size", 0.3)
    if look == "med":
        comps["Sprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper3", "ReduceScaleWith": "Hit",
                           "ReduceScaleExponent": 0.5,
                           "Sprite": {"Texture": {"File": Q("./Data/shots/bullet_med/bullet_med.png"),
                                                  "SampleMode": "Linear", "MipLevels": "max"},
                                      "Size": [size, size]}}
    elif look == "large":
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
    elif look == "own":
        comps["Sprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper3", "ReduceScaleWith": "Hit",
                           "ReduceScaleExponent": 0.5,
                           "Sprite": {"Texture": {"File": Q(s["sprite_file"]), "SampleMode": "Linear", "MipLevels": "max"},
                                      "Size": s.get("sprite_wh", [size, size])}}
    elif look == "energy":
        col = s["glow_color"]
        comps["Sprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper3",
                           "Sprite": {**GLOW, "Size": s.get("sprite_wh", [size * 3, size]),
                                      "VertexColor": [min(255, c + 120) for c in col],
                                      "TargetBlendMode": "Add"}}
    gl = s.get("glow_size", [4, 2])
    comps["GlowSprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": 0, "IsLight": True,
                           "Offset": [-gl[0] / 8, 0],
                           "Sprite": {**GLOW, "Size": gl, "VertexColor": s["glow_color"], "TargetBlendMode": "Add",
                                      "Shader": Q("./Data/common_effects/fancy_light.shader"),
                                      "_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 24,
                                      "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": 0.125}}
    if s.get("trail"):
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [f"&<{TRAILS[s['trail']]}>"]}
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
    top = {
        "STAT_DAMAGE": s["damage"],
        "STAT_PENETRATION": s["penetration"],
        "ID": Q(s["id"]),
        "Range": s["range"],
        "IdealRange": [round(s["range"] * 0.3), "&~/Range"],
        "IdealRadius": [5, 50],
        "Speed": s["speed"],
    }
    preset = s.get("fx", "med")
    hit_op = {"ReduceEffectsByPenetration": True, "Offset": [-0.15, 0],
              "HitEffects": [{"Type": "Damage", "Damage": _val(s["damage"])},
                             {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
              "MediaEffects": _media(preset, s.get("volume", 0.6), s.get("max_conc", 30), s.get("shake", 0))}
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
    pen_op = {"ReduceEffectsByPenetration": True,
              "HitEffects": [{"Type": "Damage", "Damage": _val(s["damage"])},
                             {"Type": "StatusApplication", "StatusType": "cosmoteer.fire",
                              "StatusChance": _val(s.get("fire", 0.04)), "ValueType": "Interpolated"},
                             {"Type": "Impulse", "Impulse": _val(s.get("impulse", 5))}],
              "MediaEffects": "&../HitOperational/MediaEffects"}
    hit = {
        "Type": "PenetratingHit",
        "Penetration": s["penetration"],
        "PenetrationSpeed": s.get("pen_speed", 25),
        "FriendlyShipLowCollisions": False,
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
            "MediaEffects": _media("he", 0.5, 20, s.get("shake", 0.03))}
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

    comps = {
        "Physics": {"Type": "CirclePhysics", "Radius": s.get("radius", 0.12), "Density": 0.0001},
        "Death": {"Type": "DeathByLifetime"},
        "Targetable": {"Type": "Targetable", "Health": s["health"], "TargetCategory": Q("bullet"),
                       "OnDeath": {"MediaEffects": "&~/Components/Hit/HitOperational/MediaEffects"}},
        "Hit": hit,
    }
    comps.update(_sprite_components(s))
    top["Components"] = comps
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
    hit = {"Type": "SimpleHit", "FriendlyShipLowCollisions": False, "HitOperational": hit_op,
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
    comps = {
        "Physics": {"Type": "CirclePhysics", "Radius": s.get("radius", 0.25), "Density": 0.0001},
        "Death": {"Type": "DeathByLifetime"},
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


# ============================================================================= misseis de convés
# Nucleo comum (copiado de shots/missile_he/missile_he.rules l.9-48, 110-123, versao "de convés"):
#   - Hit com FriendlyShipLowCollisions = false + FriendlyShipHighCollisions = false (passa por cima do
#     proprio casco e das torres de convés vizinhas; bullet_deck.rules l.41) e SourcePartCollisionDelay;
#   - Targetable categoria "missile" (PD/flak vanilla e SW:ACD derrubam); abatido = so efeito (HitFriendly);
#   - explosoes SEM Friendlies = true; numeros escalaveis como { BaseValue; EffectScaleExponent = 1 };
#   - sprite e brilho em buckets Upper (os Lower das particulas de propulsor ficariam sob o nosso teto).
MSL_D = f"{D}/missile_he"
MSL_T = f"{D}/missile_thermal"
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
}


def _missile_media(s, shake=True):
    mm = MISSILE_MEDIA[s["payload"]]
    media = [f"&<{p}>" for p in mm["particles"]]
    media.append(Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(x) for x in mm["sounds"]],
                                                   "Volume": s.get("volume", 0.7), "SpeedVariation": 0.15,
                                                   "MaxConcurrent": s.get("max_conc", 16)}))
    if shake and s.get("shake"):
        media.append(Inh("/BASE_SHAKE", {"ShakeAmount": s["shake"], "Duration": 0.5}))
    return media


def _missile_hit(s, hit_op, hit_shield):
    v = s.get("variants", {})
    delay = "0.3" if v.get("source_part_collision_delay") == "s_0_3" else "1.5 / (&/Simulation/PhysicsUpdatesPerSecond)"
    hit = {"Type": "SimpleHit", "SourcePartCollisionDelay": delay,
           "FriendlyShipLowCollisions": False, "FriendlyShipHighCollisions": False}
    hit["HitShield"] = hit_shield if hit_shield is not None else "&HitOperational"
    hit["HitOperational"] = hit_op
    hit["HitStructural"] = "&HitOperational"
    hit["HitFriendly"] = {"MediaEffects": _missile_media(s, shake=False)}
    return hit


def _payload_he(s):
    d = s["damage"]
    fx = [{"Type": "ExplosiveDamage", "TotalDamage": _val(d["ExplosiveDamage"]), "Radius": d["Radius"]},
          {"Type": "Impulse", "Impulse": _val(d.get("Impulse", 0))}]
    stats = {"STAT_DAMAGE": d["ExplosiveDamage"], "STAT_RADIUS": d["Radius"]}
    return {"HitEffects": fx, "MediaEffects": _missile_media(s)}, None, stats


def _payload_napalm(s):
    """Taturana: explosao pequena sem fogo embutido (o fogo interpolado de ExplosiveDamage muda entre
    0.30.4 e 0.30.5) + fogo garantido na peca (bullet_med.rules l.129-132 / bullet_large_overclock_shrapnel
    l.113-114) + poca de calor que reacende (missile_thermal.rules l.128-139, com valor literal)."""
    d = s["damage"]
    fire = {"Type": "StatusApplication", "StatusType": "cosmoteer.fire", "StatusChance": _val(d["fire_StatusChance"]),
            "StatusValue": d["fire_StatusValue_interpolated"], "ValueType": "Interpolated"}
    if s.get("variants", {}).get("napalm_fire") == "all_hit_part_tiles":
        fire["ApplyToAllHitPartTiles"] = True
    heat_pool = {"Type": "GridStatusApplication", "StatusType": "cosmoteer.heat", "StatusValue": 0,
                 "StatusValuePool": d["heat_StatusValuePool"], "ValueFalloff": 1, "MaxCost": d["heat_MaxCost"],
                 "FalloffPadding": 0.5, "EmptyTileCost": 1000, "AllowDiagonals": True,
                 "Filter": {"Friendlies": False, "TargetedFriendlies": True}}
    blast = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["blast_ExplosiveDamage"]), "Radius": d["blast_radius"]}
    hit_op = {"HitEffects": [blast, fire, heat_pool], "MediaEffects": _missile_media(s)}
    shield_blast = {"Type": "ExplosiveDamage", "TotalDamage": _val(d["shield_blast"]), "Radius": d["blast_radius"]}
    hit_shield = {"HitEffects": [shield_blast,
                                 {"Type": "StatusApplication", "StatusType": "cosmoteer.heat", "StatusValue": d["shield_heat"],
                                  "ApplyToAllHitPartTiles": True, "DivideValueByPartArea": True}],
                  "MediaEffects": "&../HitOperational/MediaEffects"}
    stats = {"STAT_DAMAGE": d["blast_ExplosiveDamage"], "STAT_RADIUS": d["blast_radius"],
             "STAT_HEAT_POOL": d["heat_StatusValuePool"], "STAT_FIRE_CHANCE": d["fire_StatusChance"]}
    return hit_op, hit_shield, stats


MISSILE_PAYLOADS = {"he": _payload_he, "napalm": _payload_napalm}


def build_missile(s):
    """Missil de convés: nucleo comum + carga (s['payload'])."""
    hit_op, hit_shield, stats = MISSILE_PAYLOADS[s["payload"]](s)
    top = dict(stats)
    top.update({"ID": Q(s["id"]), "Range": s["range"], "IdealRange": s["range"], "Speed": s["speed"]})
    v = s.get("variants", {})
    homing = {"Type": "TargetHoming", "TurnVelocity": f"{s['turn']}d", "Delay": s["homing_delay"]}
    if v.get("homing_avoidance") == "raycast_250":
        homing["AvoidanceRaycastDistance"] = 250
    elif v.get("homing_avoidance") == "no_avoid_friendlies":
        homing["AvoidsFriendlies"] = False
    homing["VelocityCompensation"] = "60%"
    mm = MISSILE_MEDIA[s["payload"]]
    w, h = s["sprite_wh"]
    gl = s["glow_size"]
    comps = {
        "Physics": {"Type": "BoxPhysics", "Size": list(s["box"]), "Density": 0.1},
        "Homing": homing,
        "Retarget": {"Type": "SameShipRetarget"},
        "Acceleration": {"Type": "Acceleration", "Acceleration": s["accel"]},
        "NegativeAcceleration": {"Type": "Acceleration", "Acceleration": [-90, 0], "AccelerationOverTime": [0, 0.75],
                                 "Direction": "FrameOfReferenceVelocity"},
        "DeathByLifetime": {"Type": "DeathByLifetime", "Lifetime": s["lifetime"]},
        "Sprite": {"Type": "Sprite", "RenderBucket": "BulletUpper3", "IsLit": True,
                   "Sprite": {"Texture": {"File": Q(f"{MSL_D}/missile_he.png"), "MipLevels": "max"}, "Size": [w, h]},
                   "NormalsTexture": {"File": Q(f"{MSL_D}/missile_he_normals.png"), "MipLevels": "max"}},
        "GlowSprite": {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": 0, "IsLight": True,
                       "Offset": [round(-w * 0.45, 3), 0],
                       "Sprite": {**GLOW, "Size": gl, "VertexColor": s["glow_color"], "TargetBlendMode": "Add",
                                  "Shader": Q("./Data/common_effects/fancy_light.shader"),
                                  "_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 24,
                                  "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": 0.125}},
        "MediaEffects": {"Type": "MediaEffects", "Offset": [s["plume_offset"], 0], "Rotation": "180d",
                         "MediaEffects": [f"&<{mm['plume']}>"]},
        # abatido no ar: so o efeito, sem dano em area ("No AOE damage when shot down", missile_he.rules l.116)
        "Targetable": {"Type": "Targetable", "Health": s["hp"], "TargetCategory": Q("missile"),
                       "OnDeath": "&../Hit/HitFriendly"},
        "Hit": _missile_hit(s, hit_op, hit_shield),
    }
    top["Components"] = comps
    return top


def build_flak_beam(s):
    """Rajada antiprojetil: feixe instantaneo ate o ponto mirado + explosao em area (flak_large.rules)."""
    cats = s["categories"]
    top = {
        "STAT_DAMAGE": s["vs_shots"],
        "STAT_SHIP_DAMAGE": s["vs_ships"],
        "STAT_RADIUS": s["radius"],
        "Range": s["range"],
        "IdealRange": round(s["range"] * 0.9),
        "ClipRangeToTarget": True,
        "RandomOffsetRadius": s.get("offset", [0.5, 3]),
        "FriendlyShipLowCollisions": False,
    }
    fx = [
        {"Type": "ExplosiveDamage", "TotalDamage": _val(s["vs_shots"]), "Radius": s["radius"], "Slices": 1,
         "Filter": {"Ships": False, "Shields": False, "Bullets": True, "OnlyBulletCategories": cats, "Crew": True}},
        {"Type": "ExplosiveDamage", "TotalDamage": _val(s["vs_ships"]), "Radius": s.get("ship_radius", s["radius"]),
         "Filter": {"Ships": True, "Shields": True, "Bullets": False, "Crew": False}},
    ]
    if s.get("spawn_cloud"):
        fx.append({"Type": "SpawnBullets", "Bullet": f"&<{s['spawn_cloud']}>", "Count": 1})
    media = [f"&<{p}>" for p in PARTICLES["flak"][: s.get("particles", 2)]]
    media.append(_sound("flak", s.get("volume", 0.3), s.get("max_conc", 10), 0.25))
    top["HitNothing"] = {"HitEffects": fx, "MediaEffects": media}
    top["HitShield"] = "&HitNothing"
    top["HitOperational"] = "&HitNothing"
    top["HitStructural"] = "&HitNothing"
    return top


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
            "VolHit": {"Type": "VolumeHit", "BeamAttenuationDamagePool": "DamagePool",
                       "HitBullet": {"HitEffects": [{"Type": "Damage", "Damage": 0, "DamagePool": "DamagePool",
                                                     "MaxDamageFromPool": {"BaseValue": "(&~/MAX_BULLET_DAMAGE)",
                                                                           "EffectScaleExponent": 1}}],
                                     "MediaEffects": ["&<./Data/shots/flak_large/overclock/particles/sparks_field.rules>"]}},
            "MediaEffects": {"Type": "MediaEffects", "FactorEffectsWith": "DamagePool",
                             "MediaEffects": ["&<./Data/shots/flak_large/overclock/particles/flak_large_overclock_field_shrapnel.rules>"]},
        },
    }
    return top
