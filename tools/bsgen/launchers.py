"""Gerador dos lancadores de misseis de convés do Bullet Strike (Tocandira / Caipora / Mula-sem-Cabeca).

Projeto: tools/spec/bullet_strike_missiles.json (launch_logic, launchers, mechanic_variants) e
docs/MISSEIS_PROJETO.md. So tipos de componente vanilla:

  (1) CARREGADOR POR FAMILIA de recurso (HE / termico / EMP / nuclear): ResourceStorage + ResourceConsumer
      (Weapon_Supply), fora dos blocos alternados; a tripulacao so entrega a familia do modo escolhido.
  (2) AUTOLOADER TRIPULADO por modo: ResourceConverter carregador -> rack (PARTS pecas -> 1 unidade) a cada
      RELOAD s, ligado so com IsOperational (contem PartCrew) e enquanto o rack nao esta travado.
      Overclock divide o Interval (factory_he.rules l.212-226).
  (3) RACK COM TRAVA: ResourceStorage ToggleOnResources = CELLS / ToggleOffResources = 0
      (thruster_boost.rules l.170-178): abre cheio e so fecha vazio, a salva sempre termina.
  (4) SALVA EM RIPPLE: torre com FireInterval = RIPPLE (multiplo do tick, point_defense 2/30); um ModeCycle
      por modo escolhe o emissor da celula em ordem LIFO (a ultima carregada sai primeiro), entao as
      sobreposicoes ResourceSprites batem com o rack em toda salva cheia (limite cosmetico conhecido, teste T21:
      salva parcial e resto de salva interrompida depois de voltar ao modo comecam pela ultima celula).
  (5) TROCA DE MODO: ModeSwitchDelay_k = uma recarga inteira do modo de destino (racks pre-carregados nunca
      dao duas salvas seguidas); rack JA CHEIO na troca espera a recarga sem a divisao do overclock
      (PrefilledDelay_k, variante prefilled_switch).
  (6) SALVA PARCIAL (DryFlush) so depois de DRY_DELAY = uma recarga inteira sem a familia carregar nenhum missil
      (rampa ValueTween + limiar 100 %, padrao do chaingun): entrega atrasada nao vira salva picada.
  (7) COOK-OFF por storage (carregador e cada rack, fora dos blocos alternados), linear nas pecas guardadas.

Variantes de mecanica (spec mechanic_variants, sem mudar numeros): rack_gate, loader_crew_gate,
mode_switch_delay, prefilled_switch, dry_flush, cassette, cell_sync, overlays, ai_firepower, torpedo_decoys
(emissor de iscas).

Layouts das celulas (tools/launcher_layout.py): cassette (Tocandira), fine16 3-2-3 / torpedo2 (Caipora),
fine48 / heavy16 / torpedo4 / torpedo2_inner com persianas nos casulos externos (Mula-sem-Cabeca).
"""

import posixpath

from rules_dsl import Q, VOID, Inh, comment
from bsgen import common as C
from launcher_layout import PX, overlay_rect, rect_placement
from bsgen.guns import deck_hull_graphics, deck_turret_graphics, deck_light_graphics


def _inv(name):
    return "{ Toggle=%s; Invert=true }" % name


# ----------------------------------------------------------------------------- geometria
def overlay_files(lch, mtype, pod, levels):
    """Nomes das imagens das sobreposicoes (contrato da arte, STYLE.md secao 8)."""
    tag = "all" if pod is None else f"p{pod}"
    return ([f"cells_{mtype}_{tag}_{j}.png" for j in range(levels + 1)],
            [f"cells_{mtype}_{tag}_{j}_normals.png" for j in range(levels + 1)])


def launcher_geometry(lch):
    """Pivo, torre, colisor e, por modo, as unidades do rack em ORDEM DE ENCHIMENTO (coordenadas da torre:
    x = frente, y = direita) + as sobreposicoes (arquivos por casulo ou combinadas)."""
    g = dict(lch["geo"])
    a3 = lch.get("art3d")
    if a3:
        g.update({"pivot": list(a3["pivot"]), "turret_size": a3["turret_size"], "collider": a3["collider"],
                  "backblast": [list(b) for b in a3.get("backblast", g["backblast"])]})
    combined = lch.get("variants", {}).get("overlays") == "combined"
    T = int(round(g["turret_size"] * PX))
    modes = {}
    for m in lch["modes"]:
        if a3:
            mm = a3["modes"][m["type"]]
            units = [{"pos": list(u), "pod": p} for u, p in zip(mm["units"], mm.get("unit_pods", [0] * len(mm["units"])))]
            tubes = mm.get("tubes")
            for i, u in enumerate(units):
                u["tubes"] = [list(t) for t in tubes[i]] if tubes else [u["pos"]]
            # "rect": recorte do casulo gravado pelo render_part (STYLE.md 8.1); sem ele, o quadro inteiro da torre
            overlays = [{"range": list(o["range"]), "files": list(o["files"]), "normals": list(o["normals"]),
                         "rect": list(o.get("rect") or [0, 0, T, T])} for o in mm["overlays"]]
            shutters = dict(mm["shutters"]) if mm.get("shutters") else None
        else:
            units = m["geo"]["units"]
            tr = m["geo"]["tube_r"]
            if combined:
                f, n = overlay_files(lch, m["type"], None, len(units))
                overlays = [{"range": [0, len(units)], "files": f, "normals": n,
                             "rect": overlay_rect(units, tr, g["turret_size"])}]
            else:
                overlays = []
                for pod in m["geo"]["pods"]:
                    a, b = pod["range"]
                    f, n = overlay_files(lch, m["type"], pod["index"], b - a)
                    overlays.append({"range": [a, b], "files": f, "normals": n, "pod": pod["index"],
                                     "rect": overlay_rect(units[a:b], tr, g["turret_size"])})
            shutters = None
            if m["geo"].get("shutters"):
                # casulos sem celula neste modo (Iara: casulos externos) mostram a persiana fechada
                shutters = {"file": f"shutters_{m['type']}.png", "normals": f"shutters_{m['type']}_normals.png",
                            "pods": [sh["pod"] for sh in m["geo"]["shutters"]]}
        modes[m["type"]] = {"units": units, "overlays": overlays, "shutters": shutters}
    g["modes"] = modes
    if a3:
        g["oc_glow"] = a3["turret"].get("oc_glow") if lch.get("oc_glow") else None
    else:
        g["oc_glow"] = "turret_oc.png" if lch.get("oc_glow") else None
    return g


# ----------------------------------------------------------------------------- blocos
def _interval(lch, m, base):
    """Valor com o modificador de overclock (BuffRemap Overclock Divide, factory_he.rules l.212-226)."""
    if not lch.get("oc") or not m.get("oc_factor"):
        return base
    return {"BaseValue": base, "Modifiers": [
        {"Type": "BuffRemap", "BuffType": "Overclock", "RemapFrom": [0, 1],
         "RemapTo": [1, f"&~/MODE_{m['type']}/OC_FACTOR"], "ModificationMode": "Divide"}]}


def _mode_constants(lch, m, has_burst):
    k = m["type"]
    d = {"CELLS": m["cells"], "PARTS": m["parts"], "MISSILES_PER_UNIT": m["mpu"], "RELOAD": m["reload"],
         "VENT": m["vent"]}
    if lch.get("variants", {}).get("dry_flush", "debounced") == "debounced":
        # salva parcial so depois de uma recarga inteira (sem overclock) sem nenhuma entrega da tripulacao
        d["DRY_DELAY"] = "(&CELLS) * (&RELOAD)"
    if lch.get("oc") and m.get("oc_factor"):
        d["OC_FACTOR"] = m["oc_factor"]
    salvo = "((&CELLS) - 1) * (&~/RIPPLE)"
    if has_burst:
        salvo += " + ((&MISSILES_PER_UNIT) - 1) * (&~/BURST_DELAY)"
    d["SALVO_TIME"] = salvo
    d["CYCLE"] = "(&CELLS) * (&RELOAD) + (&SALVO_TIME)"
    if lch.get("oc"):
        d["OC_CYCLE"] = ("(&CELLS) * (&RELOAD) / (&OC_FACTOR) + (&SALVO_TIME)" if m.get("oc_factor")
                         else "&CYCLE")
    return {f"MODE_{k}": d}


def _family_blocks(lch, comp):
    """(1) um carregador por familia de recurso, consumidor so com um modo da familia selecionado."""
    w, h = lch["size"]
    n_fam = len(lch["families"])
    for i, f in enumerate(lch["families"]):
        F = f["key"]
        comp[f"Uses{F}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}" for k in f["modes"]], "Mode": "Any"}
        comp[f"Consume{F}"] = {"Type": "MultiToggle", "Toggles": ["CommandConsumptionToggle", f"Uses{F}"], "Mode": "All"}
        comp[f"MagStorage_{F}"] = {
            "Type": "ResourceStorage", "ResourceType": f["res"], "MaxResources": f["mag"],
            "DelayBeforeReadyToUse": 0.5,
            "UITileRect": [f"{i % w} + 7/64", f"{max(0, h - 1 - i // w)} + 7/64", "1 - 14/64", "1 - 14/64"],
            "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
            "DropResourcesWhenDestroyed": True, "DropResourcesWhenRemoved": True,
        }
        comp[f"MagConsumer_{F}"] = {
            "Type": "ResourceConsumer", "ResourceType": f["res"], "Storage": f"MagStorage_{F}",
            "DefaultPriority": "&/PRIORITIES/Weapon_Supply", "OperationalToggle": f"Consume{F}",
            "ConsumptionToggleButtonOffset": [0, -0.4 + (0.25 * i if n_fam > 1 else 0)],
        }


def _media_sounds(files, volume=None, interior=True, max_conc=None):
    snd = {"RandomSounds": [Q(s) for s in files], "SpeedVariation": 0.1}
    if volume is not None:
        snd["Volume"] = volume
    if max_conc:
        snd["MaxConcurrent"] = max_conc
    return Inh("/BASE_SOUNDS/AudioInterior" if interior else "/BASE_SOUNDS/AudioExterior", snd)


def _mode_logic(lch, m, comp, v, all_modes):
    """(2)-(6) por modo: rack com trava, autoloader tripulado, atraso de troca, salva parcial."""
    k = m["type"]
    F = m["family"]
    M = f"&~/MODE_{k}"
    fx = lch["fx"]
    gate = v.get("rack_gate", "latch")
    comp[comment(f"---- modo {k} ({m['codename']}): rack, autoloader, troca de modo, salva parcial ----")] = None
    rack = {"Type": "ResourceStorage", "ResourceType": m["res"], "MaxResources": f"{M}/CELLS"}
    if gate == "latch":
        # trava (thruster_boost.rules l.176-177): liga cheio, so desliga vazio
        rack.update({"ToggleOnResources": f"{M}/CELLS", "ToggleOffResources": 0})
    rack.update({"AnticipateMoreResourcesFrom": [f"MagStorage_{F}"], "DropResourcesWhenDestroyed": False})
    comp[f"ReadyRack_{k}"] = rack
    full = f"ReadyRack_{k}"
    if gate == "salvo_timer":
        comp[f"RackFull_{k}"] = {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                                 "ResourceStorages": [f"ReadyRack_{k}"], "ToggleOnResources": f"{M}/CELLS",
                                 "ToggleOffResources": "(&ToggleOnResources) - 1"}
        full = f"RackFull_{k}"
    comp[f"RackAny_{k}"] = {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                            "ResourceStorages": [f"ReadyRack_{k}"], "ToggleOnResources": 1, "ToggleOffResources": 0}
    # a familia ainda tem pecas para pelo menos 1 missil DESTE modo (threshold, thruster_boost.rules l.193-199)
    comp[f"MagCanLoad_{k}"] = {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                               "ResourceStorages": [f"MagStorage_{F}"], "ToggleOnResources": f"{M}/PARTS",
                               "ToggleOffResources": "(&ToggleOnResources) - 1"}
    loader = ["IsOperational"]
    if v.get("loader_crew_gate") == "explicit_partcrew":
        loader.append("PartCrew")
    loader += [f"ModeToggle_{k}", _inv(full)]
    if gate == "salvo_timer":
        loader.append(_inv("IsSalvoActive"))
    comp[f"LoaderOn_{k}"] = {"Type": "MultiToggle", "Toggles": loader, "Mode": "All"}
    comp[f"Autoloader_{k}"] = {
        "Type": "ResourceConverter", "OperationalToggle": f"LoaderOn_{k}", "CheckResourceLimits": True,
        "FromStorage": f"MagStorage_{F}", "FromQuantity": f"{M}/PARTS",
        "ToStorage": f"ReadyRack_{k}", "ToQuantity": 1,
        "Interval": _interval(lch, m, f"{M}/RELOAD"),
    }
    comp[f"ReloadEffect_{k}"] = {"Type": "TriggeredEffects", "Trigger": f"Autoloader_{k}",
                                 "Location": "&../DestroyedEffects/Location",
                                 "MediaEffects": [_media_sounds(fx["reload"], 0.6)]}
    comp[f"RackFullEffect_{k}"] = {"Type": "ToggleEffects", "Toggle": full,
                                   "ToggledOnMediaEffects": [_media_sounds(fx["ready"], 0.7)]}
    if fx.get("thump"):
        # pancada no ultimo missil da salva: o rack acabou de esvaziar (RackAny desliga)
        comp[f"RackEmptied_{k}"] = {"Type": "ToggleTrigger", "Toggle": f"RackAny_{k}", "TriggerWhenOn": False,
                                    "TriggerWhenOff": True}
        comp[f"SalvoEndEffect_{k}"] = {"Type": "TriggeredEffects", "Trigger": f"RackEmptied_{k}",
                                       "Location": "&../DestroyedEffects/Location",
                                       "MediaEffects": [Inh("/BASE_SHAKE", {"ShakeAmount": fx["thump"], "Duration": 0.6})]}
    # (5) troca de modo: atraso = uma recarga inteira do modo de DESTINO
    comp[f"ModeOn_{k}"] = {"Type": "ToggleTrigger", "Toggle": f"ModeToggle_{k}", "TriggerWhenOn": True,
                           "TriggerWhenOff": False}
    if v.get("mode_switch_delay", "per_mode") == "per_mode":
        comp[f"ModeSwitchDelay_{k}"] = {"Type": "Timer", "StartTrigger": f"ModeOn_{k}", "StartExpired": True,
                                        "Duration": _interval(lch, m, f"({M}/CELLS) * ({M}/RELOAD)")}
        delays = [f"ModeSwitchDelay_{k}"]
    else:
        delays = ["ModeSwitchDelay"]
    if _prefilled_gate(lch, m, v):
        # rack JA CHEIO na troca (carregado antes, sem pagar o calor do overclock): espera a recarga inteira SEM a
        # divisao do overclock, entao ligar o overclock nao adianta a salva de um rack pre-carregado.
        # TriggerProxy com ProxyToggle (base_part_overclock.rules WasOperationalOverclockDisabled)
        comp[f"PrefilledSwitch_{k}"] = {"Type": "TriggerProxy", "ComponentID": f"ModeOn_{k}", "ProxyToggle": full}
        if v.get("mode_switch_delay", "per_mode") == "per_mode":
            comp[f"PrefilledDelay_{k}"] = {"Type": "Timer", "StartTrigger": f"PrefilledSwitch_{k}", "StartExpired": True,
                                           "Duration": f"({M}/CELLS) * ({M}/RELOAD)"}
            delays.append(f"PrefilledDelay_{k}")
        else:
            delays.append("PrefilledDelay")
    # (6) salva parcial quando a familia nao carrega mais nenhum missil deste modo
    can = [full]
    if gate == "salvo_timer":
        comp[f"SalvoContinue_{k}"] = {"Type": "MultiToggle", "Toggles": ["IsSalvoActive", f"RackAny_{k}"], "Mode": "All"}
        can.append(f"SalvoContinue_{k}")
    dry = v.get("dry_flush", "debounced")
    if dry == "debounced":
        # so dispara o rack parcial quando o paiol fica SEM carregar nada por DRY_DELAY seguidos: uma entrega
        # atrasada da tripulacao nao vira uma salva picada (a trava espera o rack cheio). Rampa + limiar 100 %
        # (chaingun.rules ShellChangingValueTween / IsShellFullyOpen); qualquer entrega derruba a rampa.
        comp[f"DryPending_{k}"] = {"Type": "MultiToggle", "Toggles": [f"RackAny_{k}", _inv(f"MagCanLoad_{k}")],
                                   "Mode": "All"}
        comp[f"DryWait_{k}"] = {"Type": "ValueTween", "IsOnToggle": f"DryPending_{k}",
                                "OnTweenDuration": f"{M}/DRY_DELAY", "OffTweenDuration": 0.1}
        comp[f"DryFlush_{k}"] = {"Type": "ThresholdToggle", "ValueFrom": f"DryWait_{k}", "MinAmount": "100%"}
        can.append(f"DryFlush_{k}")
    elif dry == "instant":
        comp[f"DryFlush_{k}"] = {"Type": "MultiToggle", "Toggles": [f"RackAny_{k}", _inv(f"MagCanLoad_{k}")],
                                 "Mode": "All"}
        can.append(f"DryFlush_{k}")
    comp[f"CanFire_{k}"] = {"Type": "MultiToggle", "Toggles": can, "Mode": "Any"}
    comp[f"RackReady_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}"] + delays + [f"CanFire_{k}"],
                              "Mode": "All"}
    comp[f"MagOrRack_{k}"] = {"Type": "MultiToggle", "Toggles": [f"MagCanLoad_{k}", f"RackAny_{k}"], "Mode": "Any"}
    comp[f"HasMissiles_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", f"MagOrRack_{k}"], "Mode": "All"}
    if lch.get("oc"):
        if m.get("oc_factor"):
            # calor por missil carregado (factory_he.rules l.272-285 Overclock_ConversionHeatProducer)
            comp[f"Overclock_LoadHeat_{k}"] = {
                "Type": "ResourceChange", "OperationalToggle": "IsOverclocked", "Trigger": f"Autoloader_{k}",
                "ResourceStorage": "&~/Part/^/0/HEAT_TARGET_STORAGE",
                "Amount": f"(&~/OVERCLOCK/HEAT_PER_PART) * ({M}/PARTS) * (&~/HEAT_TO_RESOURCE)"}
        if m["vent"] > 0:
            # respiro: a cada rack cheio em overclock perde VENT pecas (thruster_boost.rules l.219-225)
            comp[f"RackFullTrigger_{k}"] = {"Type": "ToggleTrigger", "Toggle": full, "TriggerWhenOn": True,
                                            "TriggerWhenOff": False}
            comp[f"Overclock_Vent_{k}"] = {"Type": "ResourceChange", "OperationalToggle": "IsOverclocked",
                                           "Trigger": f"RackFullTrigger_{k}", "ResourceStorage": f"MagStorage_{F}",
                                           "Amount": f"-({M}/VENT)"}
    if v.get("cell_sync", "reset_each_reload") == "reset_each_reload":
        # o ModeCycle fica num bloco reconstruido durante a recarga de um rack nao vazio: toda salva cheia
        # comeca alinhada (LIFO), mesmo depois de uma salva parcial ou de troca de modo no meio da salva.
        comp[f"MidReload_{k}"] = {"Type": "MultiToggle", "Toggles": [f"LoaderOn_{k}", f"MagCanLoad_{k}", f"RackAny_{k}"],
                                  "Mode": "All"}
        comp[f"SalvoOn_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", _inv(f"MidReload_{k}")],
                                "Mode": "All"}
        comp[f"ReloadOn_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", f"MidReload_{k}"], "Mode": "All"}
        n_max = max(x["cells"] for x in all_modes)
        for blk, tog, live in ((f"Salvo_{k}", f"SalvoOn_{k}", True), (f"Reload_{k}", f"ReloadOn_{k}", False)):
            inner = {"ShootCycle": _cycle(m["cells"], live)}
            for i in range(n_max):
                inner[f"ShootTrigger_{i}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [i]}
            comp[blk] = {"Type": "ToggledComponents", "Toggle": tog, "Components": inner}


def _prefilled_gate(lch, m, v):
    """Variante prefilled_switch: atraso extra (sem overclock) ao entrar num rack ja cheio; so faz sentido em
    modos cuja recarga o overclock acelera."""
    return bool(lch.get("oc") and m.get("oc_factor") and v.get("prefilled_switch", "full_delay") == "full_delay")


def _cycle(cells, live=True):
    c = {"Type": "ModeCycle", "ModeRange": [0, max(1, cells) - 1]}
    if live:
        c["IncrementTrigger"] = "Turret"
    c["StartingMode"] = max(1, cells) - 1          # o 1o disparo vai para o modo 0 (cannon_deck.rules l.721)
    return c


def _fire_block(lch, m, geo, shot_path, v):
    """Bloco do modo: emissores (um por unidade do rack, LIFO), efeitos, sobreposicoes, barra de recarga."""
    k = m["type"]
    gm = geo["modes"][k]
    units = gm["units"]
    n = len(units)
    fx = lch["fx"]
    twin = m["mpu"] > 1 and v.get("cassette", "burst") == "twin_emitter"
    sync = v.get("cell_sync", "reset_each_reload")
    inner = {}
    base = {
        "Type": "BulletEmitter", "ChainedTo": "Turret", "FireTrigger": VOID, "GetTargetFrom": "Turret",
        "OperationalToggle": "IsOperational", "Location": list(units[-1]["pos"]),
        "Bullet": f"&<{shot_path}>", "ResourceStorage": f"ReadyRack_{k}", "ResourcesUsed": 1,
        "TargetLeadPrediction": False, "Spread": ["-4d", "4d"], "Recoil": 0,
    }
    if m["mpu"] > 1 and not twin:
        # cassete: 2 micromisseis por unidade do rack (UseResourcePerShotInBurst padrao false -> 1 unidade por par)
        base.update({"Burst": m["mpu"], "BurstDelay": "&~/BURST_DELAY"})
    if sync == "free_cycle":
        inner["ShootCycle"] = _cycle(m["cells"])
    inner["TargetEmitter"] = base
    flash = [f"&<{p}>" for p in fx["flash"]]
    heavy = m["geo"].get("form") == "torpedo" and fx.get("sound_heavy")
    snd = _media_sounds(fx["sound_heavy"] if heavy else fx["sound"], fx.get("volume", 0.6), interior=False,
                        max_conc=fx.get("max_concurrent", 12))
    if fx.get("shake"):
        snd = [snd, Inh("/BASE_SHAKE", {"ShakeAmount": fx["shake"] * (3 if heavy else 1), "Duration": 0.4})]
    else:
        snd = [snd]
    dec = m.get("decoy")
    if dec:
        # fallback T17 (torpedo_decoys=emitter): torpedo de estagio unico + iscas de um 2o emissor por celula,
        # disparado junto (Burst = iscas, BurstDelay 0.1, sem ResourceStorage: nao gasta o rack)
        dec_path = posixpath.join(posixpath.dirname(shot_path), f"{dec['file']}.rules")
    for i in range(n):
        u = units[n - 1 - i]                         # LIFO: o 1o disparo da salva sai da ultima unidade carregada
        if sync == "free_cycle":
            inner[f"ShootTrigger_{i}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [i]}
            trig = f"ShootTrigger_{i}"
        else:
            trig = f"ShootTriggerProxy_{i}"
        loc = list(u["tubes"][0]) if twin else list(u["pos"])
        inner[f"Emitter_{i} : TargetEmitter"] = {"Location": loc, "FireTrigger": trig}
        inner[f"LaunchEffect_{i}"] = {"Type": "TriggeredEffects", "ChainedTo": f"Emitter_{i}", "Trigger": f"Emitter_{i}",
                                      "MediaEffects": flash + snd}
        if dec:
            de = {k2: v2 for k2, v2 in base.items() if k2 not in ("ResourceStorage", "ResourcesUsed")}
            de.update({"Location": loc, "FireTrigger": trig, "Bullet": f"&<{dec_path}>", "Burst": dec["burst"],
                       "BurstDelay": dec["burst_delay"], "Spread": ["-12d", "12d"]})
            inner[f"DecoyEmitter_{i}"] = de
        if twin:
            eb = {k2: v2 for k2, v2 in base.items() if k2 not in ("ResourceStorage", "ResourcesUsed")}
            eb.update({"Location": list(u["tubes"][-1]), "FireTrigger": trig, "FireDelay": "&~/BURST_DELAY"})
            inner[f"EmitterB_{i}"] = eb
            inner[f"LaunchEffectB_{i}"] = {"Type": "TriggeredEffects", "ChainedTo": f"EmitterB_{i}",
                                           "Trigger": f"EmitterB_{i}", "MediaEffects": flash + snd}
    ts = geo["turret_size"]
    for j, ov in enumerate(gm["overlays"]):
        a, b = ov["range"]
        # imagens recortadas no retangulo do casulo (STYLE.md 8.1): Location = centro dele no quadro da torre
        loc, size = rect_placement(ov["rect"], ts)
        levels = [{"File": Q(f), "NormalsFile": Q(nf), "Size": size} for f, nf in zip(ov["files"], ov["normals"])]
        inner[f"Cells_{j}"] = {
            "Type": "ResourceSprites", "ChainedTo": "Turret", "Location": loc, "Rotation": "90d",
            "Layer": Q("roof_turrets"), "ResourceStorage": f"ReadyRack_{k}", "RangeLow": a, "RangeHigh": b,
            "HasZeroResourceSprite": True, "ResourceLevels": levels}
    bbs = geo.get("backblast") or []
    if len(bbs) > 1:
        # varios casulos: o sopro sai atras do casulo que disparou (um ponto por casulo, o mais proximo na lateral)
        by_pod = {}
        for i in range(n):
            by_pod.setdefault(units[n - 1 - i]["pod"], []).append(i)
        for p_i, idxs in sorted(by_pod.items()):
            lat = sum(units[n - 1 - i]["pos"][1] for i in idxs) / len(idxs)
            bb = min(bbs, key=lambda b: abs(b[1] - lat))
            trig = [f"Emitter_{i}" for i in idxs] + ([f"EmitterB_{i}" for i in idxs] if twin else [])
            inner[f"PodFired_{p_i}"] = {"Type": "MultiTrigger", "Triggers": trig}
            inner[f"Backblast_{p_i}"] = {"Type": "TriggeredEffects", "ChainedTo": "Turret", "Trigger": f"PodFired_{p_i}",
                                         "Location": list(bb), "Rotation": "180d",
                                         "MediaEffects": [f"&<{q}>" for q in fx["backblast"]]}
    sh = gm.get("shutters")
    if sh:
        # persianas fechadas nos casulos sem celula neste modo (Iara: casulos externos), spec layout_note
        img = {"File": Q(sh["file"]), "NormalsFile": Q(sh["normals"]), "Size": [ts, ts]}
        inner["Shutters"] = {"Type": "Graphics", "ChainedTo": "Turret", "Location": [0, 0], "Rotation": "90d",
                             "OperationalToggle": "IsOperational",
                             "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [img]},
                             "NonOperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [dict(img)]}}
    # sem ValueRange: o rack fornece a fracao de enchimento 0..1 (ProvidedValueRange padrao), como as barras
    # vanilla sobre um storage simples (shield_gen_small.rules: ShowProgressFor = BatteryStorage)
    inner["ReloadProgressBar"] = {"Type": "ProgressBar", "OperationalToggle": "IsOperational",
                                  "ShowProgressFor": f"ReadyRack_{k}"}
    return {"Type": "ToggledComponents", "Toggle": f"ModeToggle_{k}", "IncludeInBlueprints": True,
            "Components": inner}


def _num(x):
    """Numero do cook-off: inteiro quando exato, senao 3 casas."""
    return int(round(x)) if abs(x - round(x)) < 1e-6 else round(x, 3)


def cookoff_storages(lch, fam):
    """Storages de uma familia que guardam pecas, com a capacidade em PECAS: o carregador (1 peca por recurso) e o
    rack de cada modo da familia (CELLS unidades x PARTS pecas). [(componente, capacidade em recursos, pecas por
    recurso, modo ou None)]."""
    out = [(f"MagStorage_{fam['key']}", fam["mag"], 1, None)]
    for m in lch["modes"]:
        if m["family"] == fam["key"]:
            out.append((f"ReadyRack_{m['type']}", m["cells"], m["parts"], m["type"]))
    return out


def _cookoff_hits(ck, f):
    """HitEffects do cook-off de UM storage; f = fracao do valor 'estoque cheio' do spec que ele carrega cheio.
    TotalDamage e inteiro no jogo (ModifiableInt): um valor fracionario derruba o carregamento do mod."""
    if ck["kind"] == "blast":
        return [
            {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": int(round(ck["op_damage"] * f)), "EffectScaleExponent": 1},
             "Radius": ck["op_radius"], "Delay": 0.05, "StatusType": "cosmoteer.fire",
             "StatusChancePerNDamage": f"{int(round(ck['fire_chance_per_1000'] * 100))}%", "StatusValue": 1,
             "StatusValueType": "Interpolated", "NDamage": 1000,
             "CrewKillChance": f"{int(round(ck['crew_kill_chance'] * 100))}%",
             "Filter": {"OperationalHealth": True, "StructuralHealth": False, "Friendlies": True}},
            {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": int(round(ck["st_damage"] * f)), "EffectScaleExponent": 1},
             "Radius": ck["st_radius"], "Delay": 0.05,
             "Filter": {"OperationalHealth": False, "StructuralHealth": True, "Friendlies": True, "Crew": False}},
        ]
    if ck["kind"] == "heat_dump":
        return [{"Type": "GridStatusApplication", "StatusType": "cosmoteer.heat", "HitPartSourceRectType": "Normal",
                 "StatusValue": 0, "StatusValuePool": {"BaseValue": _num(ck["heat_pool"] * f), "EffectScaleExponent": 1},
                 "MaxCost": 3, "EmptyTileCost": "Infinity", "ValueFalloff": 1, "FalloffPadding": 1,
                 "Filter": {"Self": True}}]
    if ck["kind"] == "drain":
        return [{"Type": "ExplosiveResourceDrain", "ResourceType": "battery",
                 "TotalDrain": {"BaseValue": _num(ck["drain"] * f), "EffectScaleExponent": 1},
                 "Radius": {"BaseValue": ck["radius"], "EffectScaleExponent": 0.5}, "Slices": 1,
                 "Filter": {"Ships": True, "Shields": True, "Friendlies": True}}]
    return None


_COOKOFF_KEYS = {"blast": ("op_damage", "st_damage"), "heat_dump": ("heat_pool",), "drain": ("drain",)}
_COOKOFF_PATHS = {"op_damage": (0, "TotalDamage"), "st_damage": (1, "TotalDamage"), "heat_pool": (0, "StatusValuePool"),
                  "drain": (0, "TotalDrain")}


def _cookoff(lch, comp, center):
    """(7) cook-off linear nas pecas guardadas, fora dos blocos (missile_launcher_he.rules l.271-330; termico:
    missile_launcher_thermal.rules l.590-618). Um par ScorchedEffects/DeathEffects POR STORAGE (carregador e cada
    rack), escalado pela fracao de enchimento dele (FactorHitEffectsWith num storage simples, como
    missile_launcher_nuke.rules MissileStorage) e com BaseValue = valor cheio do spec x pecas do storage /
    cookoff.parts_full: cada peca guardada vale valor/parts_full, esteja no carregador ou num rack."""
    sz, on, off = C.effect_size(*lch["size"])
    comp[comment("---- cook-off: um par por storage (carregador + racks), linear nas pecas guardadas ----")] = None
    comp["OperationEffects"] = {"Type": "ToggleEffects", "Location": center, "Toggle": "IsOperational",
                                "ToggledOnMediaEffects": f"&/COMMON_EFFECTS/{on}",
                                "ToggledOffMediaEffects": f"&/COMMON_EFFECTS/{off}"}
    comp["ScorchedTrigger"] = {"Type": "ToggleTrigger", "Toggle": "ScorchedToggle", "TriggerWhenOn": False,
                               "TriggerWhenOff": True}
    comp["ScorchedEffects"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                               "Location": "&../DestroyedEffects/Location",
                               "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartScorched"}
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed",
                                "Location": center}
    for fam in lch["families"]:
        ck = lch["cookoff"].get(fam["res"])
        if not ck or ck["kind"] not in _COOKOFF_KEYS:
            continue
        pf = ck["parts_full"]
        for name, cap, ppr, mode in cookoff_storages(lch, fam):
            tag = f"Mag_{fam['key']}" if mode is None else f"Rack_{mode}"
            hits = _cookoff_hits(ck, cap * ppr / pf)
            comp[f"ScorchedEffects_{tag}"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger", "Location": center,
                                              "FactorHitEffectsWith": name,
                                              "HitEffects": f"&../DestroyedEffects_{tag}/HitEffects"}
            dest = {"Type": "DeathEffects", "OperationalToggle": "ScorchedToggle", "Location": center,
                    "FactorHitEffectsWith": name}
            if ck["kind"] == "heat_dump":
                dest["IncludeWhenUnderConstruction"] = False
            dest["HitEffects"] = hits
            comp[f"DestroyedEffects_{tag}"] = dest
    _check_cookoff(lch, comp)


def _check_cookoff(lch, comp):
    """Confere o que o MOTOR calcula com os componentes gerados (nao a aritmetica do spec): cada DeathEffects vale
    BaseValue x (recursos guardados / MaxResources do storage em FactorHitEffectsWith). Com o carregador cheio e o
    maior rack da familia cheio (o 'estoque cheio' do spec) a soma tem que dar o valor do spec, e cada peca guardada
    tem que valer valor/parts_full em qualquer storage. Aborta o build se divergir."""
    errs = []
    for fam in lch["families"]:
        ck = lch["cookoff"].get(fam["res"])
        if not ck or ck["kind"] not in _COOKOFF_KEYS:
            continue
        sto = {name: (cap, ppr, mode) for name, cap, ppr, mode in cookoff_storages(lch, fam)}
        # capacidade de verdade dos storages gerados (MaxResources do carregador / CELLS do modo para o rack)
        for name, (cap, ppr, mode) in sto.items():
            real = comp[name]["MaxResources"]
            if mode:
                if real != f"&~/MODE_{mode}/CELLS":
                    errs.append(f"{name}: MaxResources {real} nao e &~/MODE_{mode}/CELLS")
                real = lch_mode(lch, mode)["cells"]
            if real != cap:
                errs.append(f"{name}: capacidade {real} != {cap}")
        racks = [(n, c * p) for n, (c, p, mo) in sto.items() if mo]
        big = max(racks, key=lambda x: x[1])[0]
        full_state = {n: 1.0 if (mo is None or n == big) else 0.0 for n, (c, p, mo) in sto.items()}
        for key in _COOKOFF_KEYS[ck["kind"]]:
            idx, field = _COOKOFF_PATHS[key]
            total = 0.0
            for tag_comp, d in comp.items():
                if not (isinstance(d, dict) and d.get("Type") == "DeathEffects" and d.get("FactorHitEffectsWith") in sto):
                    continue
                name = d["FactorHitEffectsWith"]
                base = d["HitEffects"][idx][field]["BaseValue"]
                cap, ppr, _mo = sto[name]
                per_part = base / (cap * ppr)
                if abs(per_part - ck[key] / ck["parts_full"]) > 1e-3 * max(1.0, abs(per_part)):
                    errs.append(f"{tag_comp}: {key} {per_part:.3f} por peca, spec {ck[key] / ck['parts_full']:.3f}")
                total += base * full_state[name]
            if abs(total - ck[key]) > 1e-3 * ck[key]:
                errs.append(f"familia {fam['key']}: {key} com estoque cheio {total:.1f}, spec {ck[key]}")
    if errs:
        raise ValueError(f"{lch['codename']}: cook-off gerado diverge do spec: " + "; ".join(errs))


def lch_mode(lch, k):
    return next(m for m in lch["modes"] if m["type"] == k)


# ----------------------------------------------------------------------------- peca
def build_launcher(lch, shot_paths):
    """Retorna (top, info) de um lancador. shot_paths: tipo de missil -> caminho relativo do .rules do missil."""
    w, h = lch["size"]
    v = lch.get("variants", {})
    oc = lch.get("oc")
    modes = lch["modes"]
    geo = launcher_geometry(lch)
    center = [w / 2, h / 2]
    has_burst = any(m["mpu"] > 1 for m in modes)

    top = {}
    if oc:
        top["OVERCLOCK"] = {"RELOAD_FACTOR": oc["reload_factor"], "HEAT_PER_PART": oc["heat_per_part"],
                            "HEAT_PER_SECOND": oc["heat_per_second"]}
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    top["RIPPLE"] = lch["ripple"]                       # alinhado ao tick (point_defense.rules: 2/30)
    if has_burst:
        top["BURST_DELAY"] = lch["burst_delay"]
    for m in modes:
        top.update(_mode_constants(lch, m, has_burst))

    part = {
        "NameKey": Q(f"Parts/{lch['key']}"), "IconNameKey": Q(f"Parts/{lch['key']}Icon"),
        "DescriptionKey": Q(f"Parts/{lch['key']}Desc"), "ID": C.pid(lch["short"]),
        "EditorGroups": [Q(C.EDITOR_GROUP), Q("WeaponsProjectile")],
        "Resources": [[r, q] for r, q in lch["cost"]], "Size": [w, h], "SelectionPriority": 1,
        "MaxHealth": lch["hp"], "TypeCategories": list(lch["categories"]) + list(lch.get("extra_categories", [])),
        "SignificanceToggle": "ScorchedToggle",
        "ReceivableBuffs : ^/0/ReceivableBuffs": [],
        "ProhibitedBy : ^/0/ProhibitedBy": ["tall"],
    }
    ring = C.tall_ring(w, h, lch.get("ring", 1))
    if ring:
        part["ProhibitRects"] = ring
    part["AllowedDoorLocations"] = C.door_locations(w, h)
    part["EditorIcon"] = C.editor_icon(w, h, 0)

    comp = {}
    comp.update(C.standard_toggles(bool(oc), lch["cp"]))
    comp[comment("---- seletor de missil (missile_launcher.rules l.126-202; AvailableChoices: point_defense.rules l.102) ----")] = None
    comp["MissileTypeToggle"] = {"Type": "UIToggle", "ToggleID": Q(lch["toggle_id"]), "Default": lch["default_mode"],
                                 "AvailableChoices": list(lch["available"]), "AlwaysAllowInBuildMode": True}
    for m in modes:
        comp[f"ModeToggle_{m['type']}"] = {"Type": "ModeToggle", "Mode": "MissileTypeToggle", "OnMode": m["index"]}
    comp[comment("---- (1) carregador interno por familia de recurso (a tripulacao enche) ----")] = None
    _family_blocks(lch, comp)
    if v.get("mode_switch_delay", "per_mode") == "single_longest":
        longest = max(modes, key=lambda x: x["cells"] * x["reload"])
        comp["ModeChanged"] = {"Type": "MultiTrigger", "Triggers": [f"ModeOn_{m['type']}" for m in modes]}
        comp["ModeSwitchDelay"] = {"Type": "Timer", "StartTrigger": "ModeChanged", "StartExpired": True,
                                   "Duration": _interval(lch, longest, f"(&~/MODE_{longest['type']}/CELLS) * "
                                                                       f"(&~/MODE_{longest['type']}/RELOAD)")}
        pre = [m for m in modes if _prefilled_gate(lch, m, v)]
        if pre:
            # rack ja cheio na troca: o atraso unico sem a divisao do overclock (variante prefilled_switch)
            comp["PrefilledChanged"] = {"Type": "MultiTrigger", "Triggers": [f"PrefilledSwitch_{m['type']}" for m in pre]}
            comp["PrefilledDelay"] = {"Type": "Timer", "StartTrigger": "PrefilledChanged", "StartExpired": True,
                                      "Duration": f"(&~/MODE_{longest['type']}/CELLS) * (&~/MODE_{longest['type']}/RELOAD)"}
    for m in modes:
        _mode_logic(lch, m, comp, v, modes)

    comp[comment("---- permissao de tiro ----")] = None
    comp["RackReady"] = {"Type": "MultiToggle", "Toggles": [f"RackReady_{m['type']}" for m in modes], "Mode": "Any"}
    comp["HasMissiles"] = {"Type": "MultiToggle", "Toggles": [f"HasMissiles_{m['type']}" for m in modes], "Mode": "Any"}
    comp["FirePermission"] = {"Type": "MultiToggle", "Toggles": ["RackReady", "FireModeToggle"], "Mode": "All"}
    if v.get("rack_gate") == "salvo_timer":
        comp["IsSalvoActive"] = {"Type": "Timer", "Duration": "(&~/RIPPLE) * 1.5", "StartTrigger": "Turret",
                                 "ResetTrigger": "Turret", "StartExpired": True, "InvertToggle": True}

    comp[comment("---- (4) torre: dispara uma unidade do rack a cada RIPPLE ----")] = None
    ai = "&~/Part/StatsByCategory/0/Stats/DamagePerSecond"
    if v.get("ai_firepower") == "x0_8":
        ai = "(&~/Part/StatsByCategory/0/Stats/DamagePerSecond) * 0.8"
    turret = {
        "Type": "TurretWeapon", "Location": geo["pivot"], "Rotation": "-90d", "OperationalToggle": "IsOperational",
        "AutoFireToggle": "AutoFireToggle", "FirePermissionToggle": "FirePermission", "FireInterval": "&~/RIPPLE",
        "FiringArc": f"{lch['arc']}d", "RotateSpeed": f"{lch['rotate']}d", "FireThresholdAngle": f"{lch['threshold']}d",
        "AllowFireWithBlockedLOS": True, "IgnoreFriendlyShipLowLOSChecks": True,
        "AIFirepowerRating": ai,
        "Emitter": "TargetEmitterProxy",          # so para mirar (cannon_deck.rules l.617)
        "AutoTargets": [{"TargetType": "ShipParts", "Toggle": "AutoTargetToggle", "EnableInDirectControlMode": True}],
        "BlueprintArcSprite": {"Texture": "&/INDICATORS/WeaponArc", "Size": [0, 1.5], "Color": [255, 0, 0, 63]},
        "BlueprintArcRadius": 10, "BlueprintArcSpriteSegments": 64,
    }
    if any(m["mpu"] > 1 for m in modes) and v.get("cassette") == "twin_emitter":
        turret["HoldTargetAfterCancel"] = "&~/BURST_DELAY"
    comp["Turret"] = turret
    comp["TurretCollider"] = {"Type": "CircleCollider", "Location": "&../Turret/Location",
                              "Radius": geo["collider"], "IsHigh": True}
    if v.get("cell_sync", "reset_each_reload") == "reset_each_reload":
        # os ModeTriggers vivem nos blocos Salvo_k/Reload_k; os emissores falam com eles por proxy
        # (cannon_deck.rules l.636-656: ShootTrigger2 = TriggerProxy para ShootRightTrigger)
        for i in range(max(m["cells"] for m in modes)):
            comp[f"ShootTriggerProxy_{i}"] = {"Type": "TriggerProxy", "ComponentID": f"ShootTrigger_{i}"}

    comp[comment("---- emissores, efeitos e sobreposicoes das celulas: um bloco por modo ----")] = None
    for m in modes:
        comp[f"Fire_{m['type']}"] = _fire_block(lch, m, geo, shot_paths[m["type"]], v)
    comp["TargetEmitterProxy"] = {"Type": "EmitterProxy", "ComponentID": "TargetEmitter", "ChainedTo": "Turret"}
    bbs = geo.get("backblast") or []
    if len(bbs) == 1:
        # um casulo so: o sopro sai a cada disparo da torre
        comp["Backblast_0"] = {"Type": "TriggeredEffects", "ChainedTo": "Turret", "Trigger": "Turret",
                               "Location": list(bbs[0]), "Rotation": "180d",
                               "MediaEffects": [f"&<{p}>" for p in lch["fx"]["backblast"]]}

    _cookoff(lch, comp, center)

    comp[comment("---- tripulacao ----")] = None
    comp.update(C.crew_block(lch.get("crew_pos") or C.crew_positions(w, h, lch["crew"], geo["pivot"]), "HasMissiles"))

    if oc:
        comp[comment("---- overclock: recarga / OC_FACTOR, calor por missil carregado + calor constante ----")] = None
        comp.update(C.overclock_machinery(center, w, h, [], has_constant_heat=oc["heat_per_second"] > 0, shot_heat=False))
        m0 = next((m for m in modes if m.get("oc_factor")), modes[0])
        comp["PeakHeatGenerationValue"] = {
            "Type": "StaticValue",
            "LOAD_HEAT_PER_SECOND": f"(&~/OVERCLOCK/HEAT_PER_PART) * (&~/MODE_{m0['type']}/PARTS) * "
                                    f"(&~/MODE_{m0['type']}/OC_FACTOR) / (&~/MODE_{m0['type']}/RELOAD)",
            "Value": "(&~/OVERCLOCK/HEAT_PER_SECOND) + (&LOAD_HEAT_PER_SECOND)",
        }
        comp["HeatGenerationStatProvider"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                              "OperationalToggle": "OverclockModeToggle",
                                              "ValueFrom": "PeakHeatGenerationValue"}

    comp[comment("---- graficos: casulo em roof_doodads, celulas (ResourceSprites) por cima em roof_turrets ----")] = None
    deck_hull_graphics(comp, lch)
    deck_turret_graphics(comp, lch, geo, layer="roof_doodads")
    deck_light_graphics(comp, lch)
    if oc and geo.get("oc_glow"):
        # assinatura visual do overclock (olho da cupula / colar em brasa): so com IsOverclocked
        ts = geo["turret_size"]
        comp["OverclockGlowGraphics"] = {
            "Type": "Graphics", "ChainedTo": "Turret", "Location": [0, 0], "Rotation": "90d",
            "OperationalToggle": "IsOverclocked",
            "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [{"File": Q(geo["oc_glow"]),
                                                                                 "Size": [ts, ts]}]}}
    comp["Indicators"] = C.weapon_indicators(center, "HasMissiles", bool(oc), f"&~/MODE_{modes[0]['type']}/RELOAD",
                                             no_ammo_sprite="&/INDICATORS/NoMissiles")
    comp["Blueprints"] = C.blueprint(w, h)
    part["Components : ^/0/Components"] = comp

    # ------------------------------------------------------------------ stats (IDs vanilla, tambem no SW:ACD)
    part["Stats"] = {"CrewRequired": "&~/Part/Components/PartCrew/Crew"}
    cats = []
    for m in modes:
        cats.append({"NameKey": Q(f"StatCategories/{lch['key']}_{m['type']}"), "Stats": _mode_stats(m, False)})
    part["StatsByCategory"] = cats
    if oc:
        m0 = next((m for m in modes if m.get("oc_factor")), modes[0])
        st = _mode_stats(m0, True)
        st["HeatGeneration"] = "&~/Part/Components/PeakHeatGenerationValue/Value"
        part["SecondaryToolTip"] = {"TitleKey": Q("StatCategories/Overclocked"),
                                    "DescriptionKey": Q(f"Parts/{lch['key']}OverclockDesc"),
                                    "StatsByCategory": [{"NameKey": Q(f"StatCategories/{lch['key']}_{m0['type']}"),
                                                         "Stats": st}]}
    # arquivo base do spec (launchers[].base_part; Caipora 3x3 = base_med como factory_he/reactor_med vanilla)
    top["Part : " + C.base_part_path(w, h, bool(oc), base=lch.get("base_part"))] = part
    return top, {"geo": geo, "center": center}


def _mode_stats(m, oc):
    k = m["type"]
    em = f"&~/Part/Components/Fire_{k}/Components/TargetEmitter"
    M = f"&~/MODE_{k}"
    fam = m["family"]
    st = {
        "DamagePerShot": f"{em}/Bullet/STAT_DAMAGE",
        "MissilesPerSalvo": f"({M}/CELLS) * ({M}/MISSILES_PER_UNIT)",
        "SalvoCycle": f"{M}/OC_CYCLE" if oc else f"{M}/CYCLE",
        "ROF": "(&MissilesPerSalvo) / (&SalvoCycle)",
        "DamagePerSecond": "(&DamagePerShot) * (&ROF)",
        "MaxDamage": ["&../DamagePerShot", "&../DamagePerSecond"],
        "DamageArea": f"{em}/Bullet/STAT_RADIUS",
        "Salvo": ["&../MissilesPerSalvo", "&../SalvoCycle"],
        "Range": f"{em}/Bullet/Range",
    }
    if not oc:
        st.update({
            "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
            "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
            "ShotLaunchSpeed": f"{em}/Bullet/Speed",
            "Acceleration": f"{em}/Bullet/Components/Acceleration/Acceleration",
            "ShotGuidance": f"deg({em}/Bullet/Components/Homing/TurnVelocity)",
            "ShotHP": f"{em}/Bullet/Components/Targetable/Health",
            "MissileParts": f"({M}/PARTS) / ({M}/MISSILES_PER_UNIT)",
            "MissilePartCapacity": [f"&~/Part/Components/MagStorage_{fam}/MaxResources",
                                    f"(&~/Part/Components/MagStorage_{fam}/MaxResources) * ({M}/MISSILES_PER_UNIT) / ({M}/PARTS)"],
        })
    return st
