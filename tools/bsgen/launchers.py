"""Gerador dos lancadores de misseis de conves 2.0 do Bullet Strike (Tocandira / Caipora / Mula-sem-Cabeca).

Modulo de conteudo (API = 2, registro do tools/build_mod.py; dono: WP06). Dados: tools/bs_data_missiles.py
(DATA.LAUNCHERS, que o bs_data so preenche com bs_data_missiles + bsgen.launchers + bsgen.missile_shots em API 2).
Projeto: SPEC.launchers e SPEC.missiles.launch_logic. So tipos de componente vanilla:

  (1) CARREGADOR POR MODO (indice i do seletor bs_missile_type: 0 HE, 1 Submunicao, 2 PEM, 3 Nuclear):
      MagStorage_i (ResourceType = a carga bs_msl_* do modo, 4 salvas) + MagConsumer_i (Weapon_Supply, reserva da
      tripulacao floor(Max/2)) em dois ToggledComponents ligados pelo ModeToggle_i (common.toggled_consumers,
      chaingun.rules l.383-437). A entrada pela Fita (FitaEntra_<chave> por modo, Alimenta_i, host da fita) vem do
      seam do WP05: bsgen.intake part_fields / weapon_intake / weapon_return com g = o lancador.
  (2) AUTOLOADER TRIPULADO por modo: Autoloader_i = ResourceConverter MagStorage_i -> ReadyRack_i (PARTS cargas
      -> 1 unidade) a cada RELOAD s, ligado so com IsOperational (contem PartCrew) e o rack nao travado.
      Overclock divide o Interval (factory_he.rules l.212-226); o modo nuclear nunca tem o divisor.
  (3) RACK COM TRAVA (ReadyRack_i = 1 salva): ToggleOnResources = CELLS / ToggleOffResources = 0
      (thruster_boost.rules l.170-178): abre cheio e so fecha vazio, a salva sempre termina.
  (4) SALVA EM SEQUENCIA: torre com FireInterval = RIPPLE (o menor intervalo dos modos, multiplo do tick); um
      ModeCycle por modo escolhe o emissor da celula em ordem LIFO; modo com intervalo maior (Mula, Submunicao
      4/30) pula disparos da torre (RIPPLE_STEP).
  (5) TROCA DE MODO: ModeSwitchDelay_i = uma recarga inteira do modo de destino; rack JA CHEIO na troca espera a
      recarga sem a divisao do overclock (PrefilledDelay_i).
  (6) SALVA PARCIAL (DryWait_i / DryFlush_i) so depois de uma recarga inteira sem nenhuma carga entrar.
  (7) COOK-OFF por storage (MagStorage_i e ReadyRack_i), com os valores por storage do spec
      (launchers[].cookoff_at_full_stock: teto 1.x; HE e Submunicao dividem 50/50; PEM = ExplosiveResourceDrain).
  (8) OVERCLOCK por modo (Caipora /1,5 e PEM /1,2; Mula /1,3 e PEM /1,15; nuclear sem buff): calor por carga
      carregada (Overclock_LoadHeat_i), calor constante, respiro RackFullTrigger_i -> -VENT cargas.

Layouts das celulas: tools/launcher_layout.py (cassette, fine16, cluster8, fine48, heavy8, heavy16,
torpedo2_inner com persianas nos casulos externos). Arte: art3d/bs_msl_box|twin|quad (meta kind 'launcher');
modo cuja arte ainda e de outro layout (celulas 1.x) reaproveita os niveis por casulo e entra na lista de
placeholders ate o WP13 re-renderizar (render_part.py <peca> --only cells).
"""

API = 2

import re  # noqa: E402

from rules_dsl import Q, VOID, Inh, comment, render  # noqa: E402
from bsgen import common as C  # noqa: E402
from launcher_layout import PX, overlay_rect, rect_placement  # noqa: E402


def _inv(name):
    return "{ Toggle=%s; Invert=true }" % name


# ----------------------------------------------------------------------------- geometria
def overlay_files(lch, mtype, pod, levels):
    """Nomes das imagens das sobreposicoes (contrato da arte, STYLE.md secao 8)."""
    tag = "all" if pod is None else f"p{pod}"
    return ([f"cells_{mtype}_{tag}_{j}.png" for j in range(levels + 1)],
            [f"cells_{mtype}_{tag}_{j}_normals.png" for j in range(levels + 1)])


def _remap_levels(old, pods, who):
    """Niveis de uma arte de outro layout (ex.: celulas 1.x de 8 tubos por casulo com o cluster8 de 4 portadores):
    o nivel j do casulo novo usa a imagem round(j * antigos / novos) do mesmo casulo."""
    if len(old) != len(pods):
        raise ValueError(f"{who}: arte com {len(old)} sobreposicoes e layout com {len(pods)} casulos")
    out = []
    for ov, pod in zip(old, pods):
        a, b = pod["range"]
        k_new = b - a
        k_old = len(ov["files"]) - 1
        idx = [int(round(j * k_old / k_new)) for j in range(k_new + 1)]
        out.append({"range": [a, b], "files": [ov["files"][x] for x in idx],
                    "normals": [ov["normals"][x] for x in idx], "rect": list(ov["rect"]), "pod": pod["index"]})
    return out


def launcher_geometry(lch):
    """Pivo, torre, colisor e, por modo (chave = tipo), as unidades do rack em ORDEM DE ENCHIMENTO (coordenadas da
    torre: x = frente, y = direita; do launcher_layout) + as sobreposicoes (arquivos e recorte de cada casulo) +
    persianas/tampas. 'art_notes' = modos cuja arte ainda nao bate com o layout (placeholders)."""
    g = dict(lch["geo"])
    a3 = lch.get("art3d")
    notes = []
    if a3:
        g.update({"pivot": list(a3["pivot"]), "turret_size": a3["turret_size"], "collider": a3["collider"],
                  "backblast": [list(b) for b in a3.get("backblast", g["backblast"])]})
    T = int(round(g["turret_size"] * PX))
    modes = {}
    for m in lch["modes"]:
        k = m["type"]
        lay = m["geo"]
        units = lay["units"]
        who = f"{lch['codename']}/{k}"
        shutters = None
        if a3:
            mm = (a3.get("modes") or {}).get(k)
            if mm is None:
                raise ValueError(f"art3d/{lch['art3d_dir']}: meta sem o modo {k}")
            if len(mm["units"]) == len(units):
                for u, p in zip(units, mm["units"]):
                    if max(abs(a - b) for a, b in zip(u["pos"], p)) > 1e-3:
                        raise ValueError(f"{who}: unidade {p} do meta difere do layout {m['layout']} {u['pos']}")
                overlays = [{"range": list(o["range"]), "files": list(o["files"]), "normals": list(o["normals"]),
                             "rect": list(o.get("rect") or [0, 0, T, T])} for o in mm["overlays"]]
                if mm.get("shutters"):
                    shutters = dict(mm["shutters"])
                elif lay["shutters"]:
                    notes.append(f"celulas {lch['short']}/{k}: layout {m['layout']} pede shutters_{k}.png "
                                 f"(tampas/persianas) e a arte nao tem (WP13: render_part.py --only cells)")
            else:
                overlays = _remap_levels(mm["overlays"], lay["pods"], who)
                notes.append(f"celulas {lch['short']}/{k}: arte de {len(mm['units'])} unidades reaproveitada no "
                             f"layout {m['layout']} de {len(units)} (WP13: render_part.py {lch['short']} --only cells)")
        else:
            overlays = []
            for pod in lay["pods"]:
                a, b = pod["range"]
                f, n = overlay_files(lch, k, pod["index"], b - a)
                overlays.append({"range": [a, b], "files": f, "normals": n, "pod": pod["index"],
                                 "rect": overlay_rect(units[a:b], lay["tube_r"], g["turret_size"])})
            if lay["shutters"]:
                shutters = {"file": f"shutters_{k}.png", "normals": f"shutters_{k}_normals.png",
                            "pods": sorted({sh["pod"] for sh in lay["shutters"]})}
        modes[k] = {"units": units, "overlays": overlays, "shutters": shutters}
    g["modes"] = modes
    if a3:
        g["oc_glow"] = (a3.get("turret") or {}).get("oc_glow") if lch.get("oc") else None
    else:
        g["oc_glow"] = "turret_oc.png" if lch.get("oc") and lch.get("oc_glow") else None
    g["art_notes"] = notes
    return g


# ----------------------------------------------------------------------------- blocos
def _M(m):
    return f"&~/MODE_{m['index']}"


def _interval(lch, m, base):
    """Valor com o modificador de overclock (BuffRemap Overclock Divide, factory_he.rules l.212-226)."""
    if not lch.get("oc") or not m.get("oc_factor"):
        return base
    return {"BaseValue": base, "Modifiers": [
        {"Type": "BuffRemap", "BuffType": "Overclock", "RemapFrom": [0, 1],
         "RemapTo": [1, f"{_M(m)}/OC_FACTOR"], "ModificationMode": "Divide"}]}


def _step(lch, m):
    """Disparos da torre por missil do modo (o intervalo da torre e o menor dos modos)."""
    return m["ripple_ticks"] // lch["ripple_ticks"]


def _mode_constants(lch, m, has_burst):
    d = {"CELLS": m["cells"], "PARTS": m["parts"], "MISSILES_PER_UNIT": m["mpu"], "RELOAD": m["reload"],
         "RIPPLE": m["ripple"], "RIPPLE_STEP": _step(lch, m), "VENT": m["vent"]}
    if lch["variants"].get("dry_flush", "debounced") == "debounced":
        # salva parcial so depois de uma recarga inteira (sem overclock) sem nenhuma carga entrar
        d["DRY_DELAY"] = "(&CELLS) * (&RELOAD)"
    if lch.get("oc") and m.get("oc_factor"):
        d["OC_FACTOR"] = m["oc_factor"]
        d["HEAT_PER_CHARGE"] = m["heat_per_charge"]
    salvo = "((&CELLS) - 1) * (&RIPPLE)"
    if has_burst:
        salvo += " + ((&MISSILES_PER_UNIT) - 1) * (&~/BURST_DELAY)"
    d["SALVO_TIME"] = salvo
    d["CYCLE"] = "(&CELLS) * (&RELOAD) + (&SALVO_TIME)"
    if lch.get("oc"):
        d["OC_CYCLE"] = ("(&CELLS) * (&RELOAD) / (&OC_FACTOR) + (&SALVO_TIME)" if m.get("oc_factor") else "&CYCLE")
    return {f"MODE_{m['index']}": d}


def _magazines(lch, comp):
    """(1) um carregador por modo; a tripulacao so entrega a carga do modo escolhido (reserva: abaixo da metade)."""
    w, h = lch["size"]
    for n, m in enumerate(lch["modes"]):
        i = m["index"]
        comp[f"MagStorage_{i}"] = {
            "Type": "ResourceStorage", "ResourceType": m["res"], "MaxResources": m["storage"],
            "DelayBeforeReadyToUse": 0.5,
            "UITileRect": [f"{n % w} + 7/64", f"{max(0, h - 1 - n // w)} + 7/64", "1 - 14/64", "1 - 14/64"],
            "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
            "DropResourcesWhenDestroyed": True, "DropResourcesWhenRemoved": True,
        }
        # modo em uso: entrega normal (e a de prioridade minima com a peca desligada, como o
        # missile_launcher_he.rules); modo fora de uso: nenhuma entrega (chaingun.rules l.383-437)
        C.toggled_consumers(comp, f"MagConsumer_{i}", f"ModeToggle_{i}", m["res"], f"MagStorage_{i}",
                            f"AmmoConsumersOn_{i}", f"AmmoConsumersOff_{i}", threshold=m["resupply_threshold"])


def _media_sounds(files, volume=None, interior=True, max_conc=None):
    snd = {"RandomSounds": [Q(s) for s in files], "SpeedVariation": 0.1}
    if volume is not None:
        snd["Volume"] = volume
    if max_conc:
        snd["MaxConcurrent"] = max_conc
    return Inh("/BASE_SOUNDS/AudioInterior" if interior else "/BASE_SOUNDS/AudioExterior", snd)


def _prefilled_gate(lch, m):
    """Variante prefilled_switch: atraso extra (sem overclock) ao entrar num rack ja cheio; so nos modos cuja
    recarga o overclock acelera."""
    return bool(lch.get("oc") and m.get("oc_factor")
                and lch["variants"].get("prefilled_switch", "full_delay") == "full_delay")


def _cycle(cells, step, live=True):
    c = {"Type": "ModeCycle", "ModeRange": [0, max(1, cells) * step - 1]}
    if live:
        c["IncrementTrigger"] = "Turret"
    c["StartingMode"] = max(1, cells) * step - 1      # o 1o disparo vai para o modo 0 (cannon_deck.rules l.721)
    return c


def _mode_logic(lch, m, comp, all_modes):
    """(2)-(6) por modo: rack com trava, autoloader tripulado, atraso de troca, salva parcial."""
    i = m["index"]
    M = _M(m)
    v = lch["variants"]
    fx = lch["fx"]
    gate = v.get("rack_gate", "latch")
    comp[comment(f"---- modo {i} {m['type']} ({m['codename']}): rack, autoloader, troca de modo, salva parcial ----")] = None
    rack = {"Type": "ResourceStorage", "ResourceType": m["res"], "MaxResources": f"{M}/CELLS"}
    if gate == "latch":
        # trava (thruster_boost.rules l.176-177): liga cheio, so desliga vazio
        rack.update({"ToggleOnResources": f"{M}/CELLS", "ToggleOffResources": 0})
    rack.update({"AnticipateMoreResourcesFrom": [f"MagStorage_{i}"], "DropResourcesWhenDestroyed": False})
    comp[f"ReadyRack_{i}"] = rack
    full = f"ReadyRack_{i}"
    if gate == "salvo_timer":
        comp[f"RackFull_{i}"] = {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                                 "ResourceStorages": [f"ReadyRack_{i}"], "ToggleOnResources": f"{M}/CELLS",
                                 "ToggleOffResources": "(&ToggleOnResources) - 1"}
        full = f"RackFull_{i}"
    comp[f"RackAny_{i}"] = {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                            "ResourceStorages": [f"ReadyRack_{i}"], "ToggleOnResources": 1, "ToggleOffResources": 0}
    # o carregador ainda tem cargas para pelo menos 1 unidade do rack (threshold, thruster_boost.rules l.193-199)
    comp[f"MagCanLoad_{i}"] = {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                               "ResourceStorages": [f"MagStorage_{i}"], "ToggleOnResources": f"{M}/PARTS",
                               "ToggleOffResources": "(&ToggleOnResources) - 1"}
    loader = ["IsOperational"]
    if v.get("loader_crew_gate") == "explicit_partcrew":
        loader.append("PartCrew")
    loader += [f"ModeToggle_{i}", _inv(full)]
    if gate == "salvo_timer":
        loader.append(_inv("IsSalvoActive"))
    comp[f"LoaderOn_{i}"] = {"Type": "MultiToggle", "Toggles": loader, "Mode": "All"}
    comp[f"Autoloader_{i}"] = {
        "Type": "ResourceConverter", "OperationalToggle": f"LoaderOn_{i}", "CheckResourceLimits": True,
        "FromStorage": f"MagStorage_{i}", "FromQuantity": f"{M}/PARTS",
        "ToStorage": f"ReadyRack_{i}", "ToQuantity": 1,
        "Interval": _interval(lch, m, f"{M}/RELOAD"),
    }
    comp[f"ReloadEffect_{i}"] = {"Type": "TriggeredEffects", "Trigger": f"Autoloader_{i}",
                                 "Location": "&../DestroyedEffects/Location",
                                 "MediaEffects": [_media_sounds(fx["reload"], 0.6)]}
    comp[f"RackFullEffect_{i}"] = {"Type": "ToggleEffects", "Toggle": full,
                                   "ToggledOnMediaEffects": [_media_sounds(fx["ready"], 0.7)]}
    if fx.get("thump"):
        # pancada no ultimo missil da salva: o rack acabou de esvaziar (RackAny desliga)
        comp[f"RackEmptied_{i}"] = {"Type": "ToggleTrigger", "Toggle": f"RackAny_{i}", "TriggerWhenOn": False,
                                    "TriggerWhenOff": True}
        comp[f"SalvoEndEffect_{i}"] = {"Type": "TriggeredEffects", "Trigger": f"RackEmptied_{i}",
                                       "Location": "&../DestroyedEffects/Location",
                                       "MediaEffects": [Inh("/BASE_SHAKE", {"ShakeAmount": fx["thump"], "Duration": 0.6})]}
    # (5) troca de modo: atraso = uma recarga inteira do modo de DESTINO
    comp[f"ModeOn_{i}"] = {"Type": "ToggleTrigger", "Toggle": f"ModeToggle_{i}", "TriggerWhenOn": True,
                           "TriggerWhenOff": False}
    per_mode = v.get("mode_switch_delay", "per_mode") == "per_mode"
    if per_mode:
        comp[f"ModeSwitchDelay_{i}"] = {"Type": "Timer", "StartTrigger": f"ModeOn_{i}", "StartExpired": True,
                                        "Duration": _interval(lch, m, f"({M}/CELLS) * ({M}/RELOAD)")}
        delays = [f"ModeSwitchDelay_{i}"]
    else:
        delays = ["ModeSwitchDelay"]
    if _prefilled_gate(lch, m):
        # rack JA CHEIO na troca (carregado antes, sem pagar o calor do overclock): espera a recarga inteira SEM a
        # divisao do overclock. TriggerProxy com ProxyToggle (base_part_overclock.rules WasOperationalOverclockDisabled)
        comp[f"PrefilledSwitch_{i}"] = {"Type": "TriggerProxy", "ComponentID": f"ModeOn_{i}", "ProxyToggle": full}
        if per_mode:
            comp[f"PrefilledDelay_{i}"] = {"Type": "Timer", "StartTrigger": f"PrefilledSwitch_{i}", "StartExpired": True,
                                           "Duration": f"({M}/CELLS) * ({M}/RELOAD)"}
            delays.append(f"PrefilledDelay_{i}")
        else:
            delays.append("PrefilledDelay")
    # (6) salva parcial quando o carregador do modo nao carrega mais nenhuma unidade
    can = [full]
    if gate == "salvo_timer":
        comp[f"SalvoContinue_{i}"] = {"Type": "MultiToggle", "Toggles": ["IsSalvoActive", f"RackAny_{i}"], "Mode": "All"}
        can.append(f"SalvoContinue_{i}")
    dry = v.get("dry_flush", "debounced")
    if dry == "debounced":
        # so dispara o rack parcial quando o carregador fica SEM carregar nada por DRY_DELAY seguidos: uma entrega
        # atrasada nao vira uma salva picada (a trava espera o rack cheio). Rampa + limiar 100 %
        # (chaingun.rules ShellChangingValueTween / IsShellFullyOpen); qualquer entrega derruba a rampa.
        comp[f"DryPending_{i}"] = {"Type": "MultiToggle", "Toggles": [f"RackAny_{i}", _inv(f"MagCanLoad_{i}")],
                                   "Mode": "All"}
        comp[f"DryWait_{i}"] = {"Type": "ValueTween", "IsOnToggle": f"DryPending_{i}",
                                "OnTweenDuration": f"{M}/DRY_DELAY", "OffTweenDuration": 0.1}
        comp[f"DryFlush_{i}"] = {"Type": "ThresholdToggle", "ValueFrom": f"DryWait_{i}", "MinAmount": "100%"}
        can.append(f"DryFlush_{i}")
    elif dry == "instant":
        comp[f"DryFlush_{i}"] = {"Type": "MultiToggle", "Toggles": [f"RackAny_{i}", _inv(f"MagCanLoad_{i}")],
                                 "Mode": "All"}
        can.append(f"DryFlush_{i}")
    comp[f"CanFire_{i}"] = {"Type": "MultiToggle", "Toggles": can, "Mode": "Any"}
    comp[f"RackReady_{i}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{i}"] + delays + [f"CanFire_{i}"],
                              "Mode": "All"}
    comp[f"MagOrRack_{i}"] = {"Type": "MultiToggle", "Toggles": [f"MagCanLoad_{i}", f"RackAny_{i}"], "Mode": "Any"}
    comp[f"HasMissiles_{i}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{i}", f"MagOrRack_{i}"], "Mode": "All"}
    if lch.get("oc"):
        if m.get("oc_factor"):
            # calor por carga carregada (factory_he.rules l.272-285 Overclock_ConversionHeatProducer)
            comp[f"Overclock_LoadHeat_{i}"] = {
                "Type": "ResourceChange", "OperationalToggle": "IsOverclocked", "Trigger": f"Autoloader_{i}",
                "ResourceStorage": "&~/Part/^/0/HEAT_TARGET_STORAGE",
                "Amount": f"({M}/HEAT_PER_CHARGE) * ({M}/PARTS) * (&~/HEAT_TO_RESOURCE)"}
        if m["vent"] > 0:
            # respiro: a cada rack cheio em overclock perde VENT cargas (thruster_boost.rules l.219-225)
            comp[f"RackFullTrigger_{i}"] = {"Type": "ToggleTrigger", "Toggle": full, "TriggerWhenOn": True,
                                            "TriggerWhenOff": False}
            comp[f"Overclock_Vent_{i}"] = {"Type": "ResourceChange", "OperationalToggle": "IsOverclocked",
                                           "Trigger": f"RackFullTrigger_{i}", "ResourceStorage": f"MagStorage_{i}",
                                           "Amount": f"-({M}/VENT)"}
    if v.get("cell_sync", "reset_each_reload") == "reset_each_reload":
        # o ModeCycle fica num bloco reconstruido durante a recarga de um rack nao vazio: toda salva cheia
        # comeca alinhada (LIFO), mesmo depois de uma salva parcial ou de troca de modo no meio da salva.
        comp[f"MidReload_{i}"] = {"Type": "MultiToggle", "Toggles": [f"LoaderOn_{i}", f"MagCanLoad_{i}", f"RackAny_{i}"],
                                  "Mode": "All"}
        comp[f"SalvoOn_{i}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{i}", _inv(f"MidReload_{i}")],
                                "Mode": "All"}
        comp[f"ReloadOn_{i}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{i}", f"MidReload_{i}"], "Mode": "All"}
        n_max = max(x["cells"] for x in all_modes)
        step = _step(lch, m)
        for blk, tog, live in ((f"Salvo_{i}", f"SalvoOn_{i}", True), (f"Reload_{i}", f"ReloadOn_{i}", False)):
            inner = {"ShootCycle": _cycle(m["cells"], step, live)}
            for j in range(n_max):
                inner[f"ShootTrigger_{j}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [j * step]}
            comp[blk] = {"Type": "ToggledComponents", "Toggle": tog, "Components": inner}


def _fire_block(lch, m, geo, shot_path):
    """Bloco do modo: emissores (um por unidade do rack, LIFO), efeitos, sobreposicoes, barra de recarga."""
    i = m["index"]
    k = m["type"]
    v = lch["variants"]
    gm = geo["modes"][k]
    units = gm["units"]
    n = len(units)
    fx = lch["fx"]
    twin = m["mpu"] > 1 and v.get("cassette", "burst") == "twin_emitter"
    sync = v.get("cell_sync", "reset_each_reload")
    step = _step(lch, m)
    inner = {}
    base = {
        "Type": "BulletEmitter", "ChainedTo": "Turret", "FireTrigger": VOID, "GetTargetFrom": "Turret",
        "OperationalToggle": "IsOperational", "Location": list(units[-1]["pos"]),
        "Bullet": f"&<{shot_path}>", "ResourceStorage": f"ReadyRack_{i}", "ResourcesUsed": 1,
        "TargetLeadPrediction": False, "Spread": ["-4d", "4d"], "Recoil": 0,
    }
    if m["mpu"] > 1 and not twin:
        # cassete: 2 micromisseis por unidade do rack (UseResourcePerShotInBurst padrao false -> 1 unidade por par)
        base.update({"Burst": m["mpu"], "BurstDelay": "&~/BURST_DELAY"})
    if sync == "free_cycle":
        inner["ShootCycle"] = _cycle(m["cells"], step)
    inner["TargetEmitter"] = base
    # clarao / sopro / tremor por tipo de missil (gancho annotate do bsgen.missile_fx: flash_by_type,
    # backblast_by_type, shake_by_type com chave = tipo); sem essas chaves fica o efeito vanilla do porte
    flash = [f"&<{p}>" for p in fx.get("flash_by_type", {}).get(k, fx["flash"])]
    heavy = m["geo"].get("form") == "torpedo" and fx.get("sound_heavy")
    snd = _media_sounds(fx["sound_heavy"] if heavy else fx["sound"], fx.get("volume", 0.6), interior=False,
                        max_conc=fx.get("max_concurrent", 12))
    shake = fx.get("shake_by_type", {}).get(k)
    if shake is None and fx.get("shake"):
        shake = fx["shake"] * (3 if heavy else 1)
    snd = [snd, Inh("/BASE_SHAKE", {"ShakeAmount": shake, "Duration": 0.4})] if shake else [snd]
    for j in range(n):
        u = units[n - 1 - j]                         # LIFO: o 1o disparo da salva sai da ultima unidade carregada
        if sync == "free_cycle":
            inner[f"ShootTrigger_{j}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [j * step]}
            trig = f"ShootTrigger_{j}"
        else:
            trig = f"ShootTriggerProxy_{j}"
        loc = list(u["tubes"][0]) if twin else list(u["pos"])
        inner[f"Emitter_{j} : TargetEmitter"] = {"Location": loc, "FireTrigger": trig}
        inner[f"LaunchEffect_{j}"] = {"Type": "TriggeredEffects", "ChainedTo": f"Emitter_{j}", "Trigger": f"Emitter_{j}",
                                      "MediaEffects": flash + snd}
        if twin:
            eb = {k2: v2 for k2, v2 in base.items() if k2 not in ("ResourceStorage", "ResourcesUsed")}
            eb.update({"Location": list(u["tubes"][-1]), "FireTrigger": trig, "FireDelay": "&~/BURST_DELAY"})
            inner[f"EmitterB_{j}"] = eb
            inner[f"LaunchEffectB_{j}"] = {"Type": "TriggeredEffects", "ChainedTo": f"EmitterB_{j}",
                                           "Trigger": f"EmitterB_{j}", "MediaEffects": flash + snd}
    ts = geo["turret_size"]
    for o, ov in enumerate(gm["overlays"]):
        a, b = ov["range"]
        # imagens recortadas no retangulo do casulo (STYLE.md 8.1): Location = centro dele no quadro da torre
        loc, size = rect_placement(ov["rect"], ts)
        levels = [{"File": Q(f), "NormalsFile": Q(nf), "Size": size} for f, nf in zip(ov["files"], ov["normals"])]
        inner[f"Cells_{o}"] = {
            "Type": "ResourceSprites", "ChainedTo": "Turret", "Location": loc, "Rotation": "90d",
            "Layer": Q("roof_turrets"), "ResourceStorage": f"ReadyRack_{i}", "RangeLow": a, "RangeHigh": b,
            "HasZeroResourceSprite": True, "ResourceLevels": levels}
    bbs = geo.get("backblast") or []
    if bbs:
        # varios casulos: o sopro sai atras do casulo que disparou (um ponto por casulo, o mais proximo na lateral)
        by_pod = {}
        for j in range(n):
            by_pod.setdefault(units[n - 1 - j]["pod"], []).append(j)
        for p_i, idxs in sorted(by_pod.items()):
            lat = sum(units[n - 1 - j]["pos"][1] for j in idxs) / len(idxs)
            bb = min(bbs, key=lambda b_: abs(b_[1] - lat))
            trig = [f"Emitter_{j}" for j in idxs] + ([f"EmitterB_{j}" for j in idxs] if twin else [])
            inner[f"PodFired_{p_i}"] = {"Type": "MultiTrigger", "Triggers": trig}
            inner[f"Backblast_{p_i}"] = {"Type": "TriggeredEffects", "ChainedTo": "Turret", "Trigger": f"PodFired_{p_i}",
                                         "Location": list(bb), "Rotation": "180d",
                                         "MediaEffects": [f"&<{q}>" for q in
                                                          fx.get("backblast_by_type", {}).get(k, fx["backblast"])]}
    sh = gm.get("shutters")
    if sh:
        # tampas/persianas fixas do modo (Submunicao da Caipora: celulas do meio; Iara: casulos externos)
        img = {"File": Q(sh["file"]), "NormalsFile": Q(sh["normals"]), "Size": [ts, ts]}
        inner["Shutters"] = {"Type": "Graphics", "ChainedTo": "Turret", "Location": [0, 0], "Rotation": "90d",
                             "OperationalToggle": "IsOperational",
                             "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [img]},
                             "NonOperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [dict(img)]}}
    # sem ValueRange: o rack fornece a fracao de enchimento 0..1 (ProvidedValueRange padrao), como as barras
    # vanilla sobre um storage simples (shield_gen_small.rules: ShowProgressFor = BatteryStorage)
    inner["ReloadProgressBar"] = {"Type": "ProgressBar", "OperationalToggle": "IsOperational",
                                  "ShowProgressFor": f"ReadyRack_{i}"}
    return {"Type": "ToggledComponents", "Toggle": f"ModeToggle_{i}", "IncludeInBlueprints": True,
            "Components": inner}


def _cookoff_hits(m, comp_id):
    """HitEffects do cook-off de UM storage com o BaseValue do spec (launchers[].cookoff_at_full_stock
    .per_storage). TotalDamage e inteiro no jogo (ModifiableInt): um valor fracionario derruba o carregamento."""
    ck = m["cookoff"]
    ps = ck["per_storage"][comp_id]
    if ck["kind"] == "blast":
        return [
            {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": int(ps["op_BaseValue"]), "EffectScaleExponent": 1},
             "Radius": ck["op_radius"], "Delay": 0.05, "StatusType": "cosmoteer.fire",
             "StatusChancePerNDamage": "50%", "StatusValue": 1, "StatusValueType": "Interpolated", "NDamage": 1000,
             "CrewKillChance": "30%",
             "Filter": {"OperationalHealth": True, "StructuralHealth": False, "Friendlies": True}},
            {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": int(ps["struct_BaseValue"]), "EffectScaleExponent": 1},
             "Radius": ck["struct_radius"], "Delay": 0.05,
             "Filter": {"OperationalHealth": False, "StructuralHealth": True, "Friendlies": True, "Crew": False}},
        ]
    # PEM: dreno de bateria em area (missile_launcher_emp.rules l.287-299)
    tot = ps if not isinstance(ps, dict) else ps.get("drain_BaseValue")
    return [{"Type": "ExplosiveResourceDrain", "ResourceType": "battery",
             "TotalDrain": {"BaseValue": int(round(tot)) if abs(tot - round(tot)) < 1e-9 else tot,
                            "EffectScaleExponent": 1},
             "Radius": {"BaseValue": ck["radius"], "EffectScaleExponent": 0.5}, "Slices": 1, "Delay": 0.05,
             "Filter": {"Ships": True, "Shields": True, "Friendlies": True}}]


def _cookoff(lch, comp, center):
    """(7) cook-off linear nas cargas guardadas, fora dos blocos (missile_launcher_he.rules l.271-330). Um par
    ScorchedEffects/DeathEffects POR STORAGE (MagStorage_i e ReadyRack_i), escalado pela fracao de enchimento dele
    (FactorHitEffectsWith num storage simples, como missile_launcher_nuke.rules MissileStorage)."""
    sz, on, off = C.effect_size(*lch["size"])
    comp[comment("---- cook-off: um par por storage (carregador + rack de cada modo), teto do spec ----")] = None
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
    for m in lch["modes"]:
        if not m.get("cookoff"):
            raise ValueError(f"{lch['codename']}/{m['type']}: modo sem cook-off no spec")
        for comp_id in (f"MagStorage_{m['index']}", f"ReadyRack_{m['index']}"):
            comp[f"ScorchedEffects_{comp_id}"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                                                  "Location": center, "FactorHitEffectsWith": comp_id,
                                                  "HitEffects": f"&../DestroyedEffects_{comp_id}/HitEffects"}
            comp[f"DestroyedEffects_{comp_id}"] = {"Type": "DeathEffects", "OperationalToggle": "ScorchedToggle",
                                                   "Location": center, "FactorHitEffectsWith": comp_id,
                                                   "HitEffects": _cookoff_hits(m, comp_id)}
    _check_cookoff(lch, comp)


def _check_cookoff(lch, comp):
    """Confere o que o MOTOR calcula com os componentes gerados: cada DeathEffects vale BaseValue x (recursos
    guardados / MaxResources do storage); com o carregador e o rack do modo cheios a soma tem que dar o teto do
    spec, e cada carga guardada vale teto / charges_full em qualquer dos dois. Aborta o build se divergir."""
    errs = []
    for m in lch["modes"]:
        ck = m["cookoff"]
        full = m["storage"] + m["cells"] * m["parts"]
        tot_keys = (("op_total_full", 0), ("struct_total_full", 1)) if ck["kind"] == "blast" else (("drain_total_full", 0),)
        for key, idx in tot_keys:
            total = 0.0
            for comp_id, charges in ((f"MagStorage_{m['index']}", m["storage"]),
                                     (f"ReadyRack_{m['index']}", m["cells"] * m["parts"])):
                he = comp[f"DestroyedEffects_{comp_id}"]["HitEffects"][idx]
                bv = (he.get("TotalDamage") or he.get("TotalDrain"))["BaseValue"]
                if ck["kind"] == "blast" and not isinstance(bv, int):
                    errs.append(f"{comp_id}: TotalDamage {bv!r} nao e inteiro")
                per = bv / charges
                if abs(per - ck[key] / full) > 0.5 / charges + 1e-9:
                    errs.append(f"{comp_id}: {key} {per:.3f} por carga, spec {ck[key] / full:.3f}")
                total += bv
            if abs(total - ck[key]) > 1.0:
                errs.append(f"modo {m['index']}: {key} com estoque cheio {total:.1f}, spec {ck[key]}")
        if comp[f"MagStorage_{m['index']}"]["MaxResources"] != m["storage"]:
            errs.append(f"MagStorage_{m['index']}: MaxResources diferente do estoque do modo")
    if errs:
        raise ValueError(f"{lch['codename']}: cook-off gerado diverge do spec: " + "; ".join(errs))


def _fita_fx_location(comp, lch):
    """Animacao dos cartuchos entrando (art3d/bs_fita_fx, gerada pelo seam do WP05): nos lancadores fica no centro da
    fileira de TRAS [w/2, h - 0.5] (SPEC.fita_teleporte.art.fx_location.armas_e_lancadores_com_torre; ADDENDUM WP06:
    Tocandira [1, 1.5], Caipora [1.5, 2.5], Mula [2.5, 5.5]), fora da torre, que cobre o centro da peca."""
    loc = list(lch.get("fita_fx_location") or [lch["size"][0] / 2, lch["size"][1] - 0.5])
    for d in comp.values():
        if isinstance(d, dict) and d.get("Type") == "Graphics" and "ChainedTo" not in d and "bs_fita_fx/" in repr(d):
            d["Location"] = list(loc)


def lch_mode(lch, k):
    """Modo por tipo ('he') ou indice (0)."""
    return next(m for m in lch["modes"] if m["type"] == k or m["index"] == k)


# ----------------------------------------------------------------------------- peca
def build_launcher(lch, shot_paths, intake=None, ctx=None):
    """Retorna (top, info) de um lancador. shot_paths: tipo de missil -> caminho relativo (da pasta da peca) do
    .rules do missil. intake: modulo bsgen.intake (seam de logistica do WP05) ou None (so a tripulacao)."""
    from bsgen.guns import deck_hull_graphics, deck_turret_graphics, deck_light_graphics
    w, h = lch["size"]
    v = lch["variants"]
    oc = lch.get("oc")
    modes = lch["modes"]
    geo = launcher_geometry(lch)
    center = [w / 2, h / 2]
    has_burst = any(m["mpu"] > 1 for m in modes)

    top = {}
    if oc:
        top["OVERCLOCK"] = {"RELOAD_FACTOR": oc["reload_factor"], "HEAT_PER_SECOND": oc["heat_per_second"]}
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    top["RIPPLE"] = lch["ripple"]                       # alinhado ao tick (point_defense.rules: 2/30)
    if has_burst:
        top["BURST_DELAY"] = lch["burst_delay"]
    for m in modes:
        top.update(_mode_constants(lch, m, has_burst))

    pf = C.call(intake, "part_fields", lch, ctx) or {}
    cats = list(lch["categories"])
    for c in list(lch.get("extra_categories") or []) + list(pf.get("TypeCategories_add") or []):
        if c not in cats:
            cats.append(c)
    part = {
        "NameKey": Q(f"Parts/{lch['key']}"), "IconNameKey": Q(f"Parts/{lch['key']}Icon"),
        "DescriptionKey": Q(f"Parts/{lch['key']}Desc"), "ID": C.pid(lch["short"]),
        "EditorGroups": [Q(C.EDITOR_GROUP), Q("WeaponsProjectile")],
        "Resources": [[r, q] for r, q in lch["cost"]], "Size": [w, h], "SelectionPriority": 1,
        "MaxHealth": lch["hp"], "TypeCategories": cats,
        "SignificanceToggle": "ScorchedToggle",
        "ReceivableBuffs : ^/0/ReceivableBuffs": list(pf.get("ReceivableBuffs_add") or []),
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
        comp[f"ModeToggle_{m['index']}"] = {"Type": "ModeToggle", "Mode": "MissileTypeToggle", "OnMode": m["index"]}
    comp[comment("---- (1) carregador interno por modo (fita e/ou tripulacao enchem) ----")] = None
    _magazines(lch, comp)
    if intake is not None:
        comp[comment("---- entrada da municao (seam bsgen.intake, WP05) ----")] = None
        C.call(intake, "weapon_intake", comp, lch, ctx)
        C.call(intake, "weapon_return", comp, lch, ctx)
        _fita_fx_location(comp, lch)
    if v.get("mode_switch_delay", "per_mode") == "single_longest":
        longest = max(modes, key=lambda x: x["cells"] * x["reload"])
        L_ = _M(longest)
        comp["ModeChanged"] = {"Type": "MultiTrigger", "Triggers": [f"ModeOn_{m['index']}" for m in modes]}
        comp["ModeSwitchDelay"] = {"Type": "Timer", "StartTrigger": "ModeChanged", "StartExpired": True,
                                   "Duration": _interval(lch, longest, f"({L_}/CELLS) * ({L_}/RELOAD)")}
        pre = [m for m in modes if _prefilled_gate(lch, m)]
        if pre:
            # rack ja cheio na troca: o atraso unico sem a divisao do overclock (variante prefilled_switch)
            comp["PrefilledChanged"] = {"Type": "MultiTrigger", "Triggers": [f"PrefilledSwitch_{m['index']}" for m in pre]}
            comp["PrefilledDelay"] = {"Type": "Timer", "StartTrigger": "PrefilledChanged", "StartExpired": True,
                                      "Duration": f"({L_}/CELLS) * ({L_}/RELOAD)"}
    for m in modes:
        _mode_logic(lch, m, comp, modes)

    comp[comment("---- permissao de tiro ----")] = None
    comp["RackReady"] = {"Type": "MultiToggle", "Toggles": [f"RackReady_{m['index']}" for m in modes], "Mode": "Any"}
    comp["HasMissiles"] = {"Type": "MultiToggle", "Toggles": [f"HasMissiles_{m['index']}" for m in modes], "Mode": "Any"}
    comp["FirePermission"] = {"Type": "MultiToggle", "Toggles": ["RackReady", "FireModeToggle"], "Mode": "All"}
    if v.get("rack_gate") == "salvo_timer":
        smax = max(_step(lch, m) for m in modes)
        comp["IsSalvoActive"] = {"Type": "Timer", "Duration": f"(&~/RIPPLE) * {smax} * 1.5", "StartTrigger": "Turret",
                                 "ResetTrigger": "Turret", "StartExpired": True, "InvertToggle": True}

    comp[comment("---- (4) torre: dispara uma unidade do rack a cada RIPPLE x RIPPLE_STEP do modo ----")] = None
    ai = "&~/Part/StatsByCategory/0/Stats/DamagePerSecond"
    if v.get("ai_firepower") == "x0_8":
        ai = "(&~/Part/StatsByCategory/0/Stats/DamagePerSecond) * 0.8"
    turret = {
        "Type": "TurretWeapon", "Location": geo["pivot"], "Rotation": "-90d", "OperationalToggle": "IsOperational",
        "AutoFireToggle": "AutoFireToggle", "FirePermissionToggle": "FirePermission", "FireInterval": "&~/RIPPLE",
        "FiringArc": f"{lch['arc']}d", "RotateSpeed": f"{lch['rotate']}d", "FireThresholdAngle": f"{lch['threshold']}d",
        # por cima do casco e das nossas torres (manipulator_beam_emitter.rules l.447-448); os misseis ja passam
        "AllowFireWithBlockedLOS": True, "IgnoreFriendlyShipLowLOSChecks": True, "IgnoreFriendlyShipHighLOSChecks": True,
        "AIFirepowerRating": ai,
        "Emitter": "TargetEmitterProxy",          # so para mirar (cannon_deck.rules l.617)
        "AutoTargets": [{"TargetType": "ShipParts", "Toggle": "AutoTargetToggle", "EnableInDirectControlMode": True}],
        "BlueprintArcSprite": {"Texture": "&/INDICATORS/WeaponArc", "Size": [0, 1.5], "Color": [255, 0, 0, 63]},
        "BlueprintArcRadius": 10, "BlueprintArcSpriteSegments": 64,
        # setor de alcance ao selecionar / mandar atacar na 0.30.3 / 0.30.4 (missile_launcher_he.rules 0.30.3
        # l.135-140; bsgen/common.py COVERAGE_SECTOR_ARC); a 0.30.5 ignora
        "CoverageSectorArc": dict(C.COVERAGE_SECTOR_ARC),
    }
    if has_burst and v.get("cassette") == "twin_emitter":
        turret["HoldTargetAfterCancel"] = "&~/BURST_DELAY"
    comp["Turret"] = turret
    comp["TurretCollider"] = {"Type": "CircleCollider", "Location": "&../Turret/Location",
                              "Radius": geo["collider"], "IsHigh": True}
    if v.get("cell_sync", "reset_each_reload") == "reset_each_reload":
        # os ModeTriggers vivem nos blocos Salvo_i/Reload_i; os emissores falam com eles por proxy
        # (cannon_deck.rules l.636-656: ShootTrigger2 = TriggerProxy para ShootRightTrigger)
        for j in range(max(m["cells"] for m in modes)):
            comp[f"ShootTriggerProxy_{j}"] = {"Type": "TriggerProxy", "ComponentID": f"ShootTrigger_{j}"}

    comp[comment("---- emissores, efeitos e sobreposicoes das celulas: um bloco por modo ----")] = None
    for m in modes:
        comp[f"Fire_{m['index']}"] = _fire_block(lch, m, geo, shot_paths[m["type"]])
    comp["TargetEmitterProxy"] = {"Type": "EmitterProxy", "ComponentID": "TargetEmitter", "ChainedTo": "Turret"}

    _cookoff(lch, comp, center)

    comp[comment("---- tripulacao ----")] = None
    crew = list(lch.get("crew_pos") or C.crew_positions(w, h, lch["crew"], geo["pivot"]))[:lch["crew"]]
    if len(crew) < lch["crew"]:
        raise ValueError(f"{lch['codename']}: {len(crew)} postos de tripulacao para crew {lch['crew']}")
    comp.update(C.crew_block(crew, "HasMissiles"))

    if oc:
        comp[comment("---- overclock: recarga / OC_FACTOR, calor por carga carregada + calor constante ----")] = None
        import bs_data as D
        comp.update(C.overclock_machinery(center, w, h, [], has_constant_heat=oc["heat_per_second"] > 0,
                                          shot_heat=False, skip_down=D.belt_skip_down(lch)))
        m0 = next((m for m in modes if m.get("oc_factor")), modes[0])
        M0 = _M(m0)
        comp["PeakHeatGenerationValue"] = {
            "Type": "StaticValue",
            "LOAD_HEAT_PER_SECOND": f"({M0}/HEAT_PER_CHARGE) * ({M0}/PARTS) * ({M0}/OC_FACTOR) / ({M0}/RELOAD)",
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
    comp["Indicators"] = C.weapon_indicators(center, "HasMissiles", bool(oc), f"&~/MODE_{modes[0]['index']}/RELOAD",
                                             no_ammo_sprite="&/INDICATORS/NoMissiles")
    comp["Blueprints"] = C.blueprint(w, h)
    part["Components : ^/0/Components"] = comp

    # ------------------------------------------------------------------ stats (IDs vanilla, tambem no SW:ACD)
    part["Stats"] = {"CrewRequired": "&~/Part/Components/PartCrew/Crew"}
    part["StatsByCategory"] = [{"NameKey": Q(f"StatCategories/{lch['key']}_{m['type']}"), "Stats": _mode_stats(m, False)}
                               for m in modes]
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
    return top, {"geo": geo, "center": center, "art_notes": geo["art_notes"]}


def _mode_stats(m, oc):
    """Linhas do tooltip do modo. Os numeros do missil vem do DATA (mode['missile']: os mesmos que o WP07 grava no
    tiro), sem referencia cruzada aos componentes do arquivo do tiro."""
    i = m["index"]
    M = _M(m)
    ms = m["missile"]
    st = {
        "DamagePerShot": ms["stat_damage"],
        "MissilesPerSalvo": f"({M}/CELLS) * ({M}/MISSILES_PER_UNIT)",
        "SalvoCycle": f"{M}/OC_CYCLE" if oc else f"{M}/CYCLE",
        "ROF": "(&MissilesPerSalvo) / (&SalvoCycle)",
        "DamagePerSecond": "(&DamagePerShot) * (&ROF)",
        "MaxDamage": ["&../DamagePerShot", "&../DamagePerSecond"],
        "DamageArea": ms["stat_radius"],
        "Salvo": ["&../MissilesPerSalvo", "&../SalvoCycle"],
        "Range": ms["range"],
    }
    if not oc:
        st.update({
            "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
            "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
            "ShotLaunchSpeed": ms["speed"],
            "Acceleration": ms["accel"],
            "ShotGuidance": ms["turn"],
            "ShotHP": ms["hp"],
            "MissileParts": f"({M}/PARTS) / ({M}/MISSILES_PER_UNIT)",
            "MissilePartCapacity": [f"&~/Part/Components/MagStorage_{i}/MaxResources",
                                    f"(&~/Part/Components/MagStorage_{i}/MaxResources) * ({M}/MISSILES_PER_UNIT) / ({M}/PARTS)"],
        })
    return st


# ----------------------------------------------------------------------------- gancho do registro
def parts(out, DATA, ctx):
    """Escreve parts/<id>/<id>.rules dos 3 lancadores (so com DATA.LAUNCHERS: os tres modulos de missil com API 2),
    a arte (make_art.launcher_art ou a copia de art3d) e registra as pecas."""
    D = DATA
    if not D.LAUNCHERS:
        return
    import art3d as A3
    intake = C.content_module("bsgen.intake")
    for lch in D.LAUNCHERS:
        pdir = f"parts/{lch['short']}"
        sp = {}
        for m in lch["modes"]:
            rel = ctx["shot_rel"].get(m["shot"])
            if rel is None:
                raise SystemExit(f"ERRO: {lch['short']}: o tiro {m['shot']} nao foi escrito (bsgen.missile_shots: "
                                 f"shots(DATA) tem que acrescentar os DATA.MISSILES a DATA.SHOTS)")
            sp[m["type"]] = ctx["relpath"](pdir, rel)
        top, info = build_launcher(lch, sp, intake=intake, ctx=ctx)
        rel = f"{pdir}/{lch['short']}.rules"
        out.text(rel, render(top, ctx["header"] + f"\nLancador de misseis: {lch['name_en']} / {lch['name_pt']} "
                                                  f"(\"{lch['codename']}\")"))
        art = ctx.get("art")
        if art:
            art.launcher_art(out, pdir, lch, info)
        elif lch.get("art3d"):
            A3.copy_files(out.root, pdir, lch["art3d_dir"], lch["art3d"])
        else:
            ctx["warn"](f"{lch['short']}: sem art3d e com --no-art: a peca fica sem imagens")
        # arte de celulas de outro layout / sem art3d: o bs_data_missiles ja pos em D.PLACEHOLDERS na carga
        for note in info["art_notes"]:
            if note not in D.PLACEHOLDERS:
                D.PLACEHOLDERS.append(note)
        ctx["add_part"](lch["id"])


# ----------------------------------------------------------------------------- conferencia do mod gerado
def _block(text, name):
    """Corpo (texto) do bloco 'name' (ou 'name : base') do .rules gerado pelo rules_dsl (indentacao por tabs)."""
    m = re.search(r"^(\t*)" + re.escape(name) + r"(?: : [^\n]*)?\n\1\{\n(.*?)\n\1\}", text, re.M | re.S)
    return m.group(2) if m else None


def _field(body, key):
    if body is None:
        return None
    lv = min((len(x) - len(x.lstrip("\t")) for x in body.split("\n") if x.strip()), default=0)
    m = re.search(r"^" + "\t" * lv + re.escape(key) + r" = (.*)$", body, re.M)
    return m.group(1).strip() if m else None


def selfcheck(mod_dir, SPEC=None):
    """Confere os lancadores escritos contra o spec: MagStorage_i (estoque) e ReadyRack_i (rack) de cada modo,
    AvailableChoices, CoverageSectorArc, limite por nave (bs_limit_nuke so na Mula), cook-off inteiro, overclock
    sem divisor no nuclear, nada de familias/tipos 1.x; componentes de logistica SO com bsgen.intake carregado (o
    WP05 gera): teleporte + empurra -> FitaEntra_<chave> por modo; puxa -> DosPaiois_i + Alimentador_i com o q do
    spec (Mula HE/Submunicao 2). Sem os tres modulos de missil (lancadores fora do build) nao ha o que conferir."""
    import os
    import bs_data as D
    import bs_data_missiles as BM
    probs = [f"dados: {p}" for p in BM.selfcheck_data(strict=False)]
    if not D.LAUNCHERS:
        return probs
    intake = C.content_module("bsgen.intake")
    transport = D.transport()
    arma = D.switch("logistics.fita_arma") if transport == "teleporte" else None
    for lch in D.LAUNCHERS:
        p = os.path.join(mod_dir, "parts", lch["short"], f"{lch['short']}.rules")
        who = lch["codename"]
        if not os.path.isfile(p):
            probs.append(f"{who}: parts/{lch['short']}/{lch['short']}.rules nao foi escrito")
            continue
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        ac = re.search(r"MissileTypeToggle\n\t*\{.*?AvailableChoices = \[([^\]]*)\]", text, re.S)
        got = [int(x) for x in ac.group(1).split(",") if x.strip()] if ac else None
        want = list(lch["spec"]["available_choices"])
        if got != want:
            probs.append(f"{who}: AvailableChoices {got}, spec {want}")
        if "CoverageSectorArc" not in (_block(text, "Turret") or ""):
            probs.append(f"{who}: TurretWeapon sem CoverageSectorArc")
        tc = re.search(r"^\t*TypeCategories = \[([^\]]*)\]", text, re.M)
        cats = [x.strip() for x in tc.group(1).split(",")] if tc else []
        lim = D.switch("missiles.category_limits") == "on"
        is_mula = any(m["type"] == "nuclear" for m in lch["modes"])
        if ("bs_limit_nuke" in cats) != (is_mula and lim):
            probs.append(f"{who}: TypeCategories {cats}: bs_limit_nuke so na Mula com missiles.category_limits = on")
        for c in lch["spec"]["type_categories"]:
            if c not in cats:
                probs.append(f"{who}: TypeCategories sem {c}")
        for bad in (r"\bUses(HE|Thermal|EMP|Nuke)\b", r"MagStorage_(HE|Thermal|EMP|Nuke)\b", r"missile_part_",
                    r"(?i)\btorpedo\b(?!2_inner)", r"(?i)\blimpet\b", r"(?i)\bnapalm\b", r"(?i)\bdecoy\b"):
            if re.search(bad, text):
                probs.append(f"{who}: resto 1.x no .rules ({bad})")
        for sm in next(L for L in D.MSPEC["launchers"] if L["id"] == lch["id"])["modes"]:
            i = sm["toggle_index"]
            mag = _field(_block(text, f"MagStorage_{i}"), "MaxResources")
            if mag != str(sm["stock"]["MagStorage_MaxResources"]):
                probs.append(f"{who}: MagStorage_{i} MaxResources {mag}, spec {sm['stock']['MagStorage_MaxResources']}")
            rack = _field(_block(text, f"ReadyRack_{i}"), "MaxResources")
            cells = _field(_block(text, f"MODE_{i}"), "CELLS")
            if rack != f"&~/MODE_{i}/CELLS" or cells != str(sm["stock"]["ReadyRack_units"]):
                probs.append(f"{who}: ReadyRack_{i} {rack} / CELLS {cells}, spec {sm['stock']['ReadyRack_units']}")
            if _field(_block(text, f"ModeToggle_{i}"), "OnMode") != str(i):
                probs.append(f"{who}: ModeToggle_{i} sem OnMode {i}")
            al = _block(text, f"Autoloader_{i}") or ""
            if ("BuffRemap" in al) != bool(sm.get("overclock_affects") and lch.get("oc")):
                probs.append(f"{who}: Autoloader_{i}: divisor de overclock {'presente' if 'BuffRemap' in al else 'ausente'}"
                             f" (overclock_affects {sm.get('overclock_affects')})")
            for comp_id in (f"MagStorage_{i}", f"ReadyRack_{i}"):
                body = _block(text, f"DestroyedEffects_{comp_id}")
                if body is None:
                    probs.append(f"{who}: sem cook-off {comp_id}")
                    continue
                for bv in re.findall(r"TotalDamage\s*\n\t*\{\s*\n\t*BaseValue = ([^\n]+)", body):
                    if not re.fullmatch(r"-?\d+", bv.strip()):
                        probs.append(f"{who}: cook-off {comp_id} TotalDamage {bv} nao inteiro")
            key = BM._res_key(sm["resource"])
            if intake is not None and transport == "teleporte":
                if arma == "puxa":
                    q = (sm.get("feeder") or {}).get("FromQuantity", 1)
                    alim = _block(text, f"Alimentador_{i}")
                    if _block(text, f"DosPaiois_{i}") is None or alim is None:
                        probs.append(f"{who}: puxa sem DosPaiois_{i} / Alimentador_{i}")
                    elif _field(alim, "FromQuantity") != str(q):
                        probs.append(f"{who}: Alimentador_{i} FromQuantity {_field(alim, 'FromQuantity')}, spec {q}")
                elif _block(text, f"FitaEntra_{key}") is None:
                    probs.append(f"{who}: teleporte sem FitaEntra_{key} (modo {i})")
            if intake is None and re.search(r"\bFitaEntra_|\bAlimentador_\d|\bDosPaiois_", text):
                probs.append(f"{who}: componentes da fita sem o bsgen.intake")
        if re.search(r"NetworkResource", text):
            probs.append(f"{who}: NetworkResource* no lancador (esteira fisica nao existe na 2.0)")
        # animacao da fita (bs_fita_fx) no centro da fileira de tras
        want_loc = [lch["size"][0] / 2, lch["size"][1] - 0.5]
        for name, body in _components(text).items():
            if "bs_fita_fx/" in body and _field(body, "Type") == "Graphics" and _field(body, "ChainedTo") is None:
                loc = _field(body, "Location")
                try:
                    got = [float(x) for x in (loc or "").strip("[]").split(",")]
                except ValueError:
                    got = None
                if got != want_loc:
                    probs.append(f"{who}: {name} (animacao da fita) em {loc}, esperado {want_loc} (fileira de tras)")
    return probs


def _components(text):
    """{nome: corpo} dos componentes da peca (filhos de 'Components : ^/0/Components')."""
    m = re.search(r"^(\t*)Components : \^/0/Components\n\1\{\n(.*?)\n\1\}", text, re.M | re.S)
    if not m:
        return {}
    ind = m.group(1) + "\t"
    out = {}
    for c in re.finditer(r"^" + ind + r"([^\s{}\[\]=/][^\n=]*?)\n" + ind + r"\{\n(.*?)\n" + ind + r"\}", m.group(2),
                         re.M | re.S):
        out[c.group(1).split(" : ")[0].strip()] = c.group(2)
    return out
