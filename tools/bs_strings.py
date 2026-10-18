"""Textos (en / pt-br) do Bullet Strike, montados a partir dos dados."""

TIER_EN = {"early": "Early-game", "mid": "Mid-game", "late": "Late-game"}
TIER_PT = {"early": "Início de jogo", "mid": "Meio de jogo", "late": "Fim de jogo"}

AMMO_EN = {
    "bullet": "loose Ammo (the vanilla Cannon Ammo)",
    "std": "Magazines",
    "plasma": "Plasma Cells",
    "nuclear": "Nuclear Shells",
}
AMMO_PT = {
    "bullet": "munição avulsa (a munição de canhão do jogo)",
    "std": "carregadores",
    "plasma": "células de plasma",
    "nuclear": "projéteis nucleares",
}

AMMO_NAMES = {  # (en, pt)
    "bullet": ("Ball Round", "Munição comum"),
    "std": ("Standard", "Padrão"),
    "ap": ("Armor-Piercing", "Perfurante"),
    "aphe": ("AP-Explosive", "Perfurante-Explosiva"),
    "emp": ("EMP", "EMP"),
    "plasma": ("Plasma Bolt", "Disparo de plasma"),
    "nuclear": ("Nuclear Shell", "Projétil nuclear"),
}

AMMO_DESC = {
    "std": ("All-round ammunition. Shell guns fire high-explosive rounds that burst on impact.",
            "Munição versátil. Os canhões disparam granadas explosivas que estouram no impacto."),
    "ap": ("Hardened penetrators that punch through armor (armor counts as half) to wreck the parts behind it. Weak against shields.",
           "Penetradores endurecidos que atravessam blindagem (a blindagem conta pela metade) e destroem o que está atrás. Fracos contra escudos."),
    "aphe": ("Penetrates one or two armor plates and then detonates INSIDE the enemy hull.",
             "Atravessa uma ou duas placas de blindagem e então detona DENTRO do casco inimigo."),
    "emp": ("Each hit drains battery from shields and powered parts. Lower hull damage, but great against energy-hungry ships and shields.",
            "Cada acerto drena bateria de escudos e partes energizadas. Menos dano ao casco, mas ótima contra naves que dependem de energia e escudos."),
}

# Frases de efeito por arma (casam por pedaco do ID). en, pt
FLAVOR = [
    ("lmg", ("A cheap pintle-mounted machine gun. Small enough to fit anywhere on deck.",
             "Metralhadora barata em reparo de pino. Pequena o bastante para caber em qualquer canto do convés.")),
    ("hmg", ("Heavy machine gun that keeps a steady stream of tracers on target.",
             "Metralhadora pesada que mantém um fluxo constante de traçantes no alvo.")),
    ("autocannon", ("Twin 20 mm autocannon: the first real teeth of a gunboat.",
                    "Autocanhão duplo de 20 mm: os primeiros dentes de verdade de uma canhoneira.")),
    ("quad", ("Four heavy machine guns on one mount. Can also swat down incoming missiles and mines.",
              "Quatro metralhadoras pesadas num só reparo. Também derruba mísseis e minas que se aproximam.")),
    ("minigun", ("Six spinning barrels. Takes a few seconds to spin up, then turns targets into scrap.",
                 "Seis canos girando. Leva alguns segundos para acelerar e depois transforma o alvo em sucata.")),
    ("naval_76", ("A naval automatic cannon: not the fastest gun around, but every 'thump' lands a heavy shell.",
                  "Um canhão naval automático: não é o mais rápido, mas cada 'tum' entrega uma granada pesada.")),
    ("naval_155", ("Twin 155 mm naval turret. Long-range artillery for capital ships.",
                   "Torre naval dupla de 155 mm. Artilharia de longo alcance para naves capitais.")),
    ("naval_406", ("The flagship's crown: a triple 406 mm battleship turret that fires full broadsides.",
                   "A coroa da nave capitânia: uma torre tripla de 406 mm de encouraçado que dispara salvas completas.")),
    ("rotary", ("A 30 mm rotary cannon. Slow to spin up, devastating once it does.",
                "Canhão rotativo de 30 mm. Demora para acelerar, devastador quando acelera.")),
    ("plasma_gatling", ("Fires superheated plasma bolts that tear through shields.",
                        "Dispara rajadas de plasma superaquecido que rasgam escudos.")),
    ("plasma_heavy", ("A heavy plasma cannon that hurls blinding bolts at extreme range. A shield breaker.",
                      "Um canhão de plasma pesado que lança disparos ofuscantes a distâncias extremas. Quebra escudos.")),
    ("ciws", ("Close-in weapon system: a radar-guided rotary gun that fills the sky with airburst flak.",
              "Sistema de defesa de curto alcance: um canhão rotativo guiado por radar que enche o céu de flak.")),
    ("flak_light", ("Light flak mount that bursts near incoming projectiles, destroying several at once.",
                    "Flak leve que explode perto dos projéteis que chegam, destruindo vários de uma vez.")),
    ("flak_heavy", ("Quad heavy flak battery: a wall of fire against missiles, torpedoes, shells and bolts.",
                    "Bateria quádrupla de flak pesada: uma muralha de fogo contra mísseis, torpedos, granadas e disparos.")),
    ("nuke", ("Nuclear howitzer. Very slow, very loud, and nothing survives the blast radius. Shells can be shot down.",
              "Obuseiro nuclear. Muito lento, muito barulhento, e nada sobrevive à explosão. Os projéteis podem ser abatidos.")),
]


def _flavor(short):
    for key, txt in FLAVOR:
        if key in short:
            return txt
    return ("Deck-mounted ammunition weapon.", "Arma de convés movida a munição.")


def _ammo_word(g, lang):
    if "modes" not in g:  # defesas
        res = g["ammo"]["res"]
        a = "bullet" if res == "bullet" else "std"
        table = AMMO_EN if lang == "en" else AMMO_PT
        return table[a] if a == "bullet" else (("Standard Magazines" if lang == "en" else "carregadores padrão"))
    a = g["modes"][0]["ammo"]
    if len(g["modes"]) > 1:
        return ("Magazines (selectable: Standard / AP / AP-Explosive / EMP)" if lang == "en"
                else "carregadores (selecionáveis: Padrão / Perfurante / Perfurante-Explosiva / EMP)")
    table = AMMO_EN if lang == "en" else AMMO_PT
    return table.get(a, table["std"])


def strings():
    import bs_data as D
    en = {"EditorGroups": {"BulletStrike": "Bullet Strike"}, "Parts": {}, "PartToggles": {}, "Stats": {},
          "StatCategories": {}, "Resource": {}}
    pt = {"EditorGroups": {"BulletStrike": "Bullet Strike"}, "Parts": {}, "PartToggles": {}, "Stats": {},
          "StatCategories": {}, "Resource": {}}

    for g in D.GUNS + D.DEFENSES:
        k = g["key"]
        w = g["spec"]
        fen, fpt = _flavor(g["short"])
        code = f" \"{g['codename']}\"" if g.get("codename") else ""
        en["Parts"][k] = f"{g['name_en']}"
        pt["Parts"][k] = f"{g['name_pt']}"
        en["Parts"][k + "Icon"] = (g.get("codename") or g["name_en"])[:18]
        pt["Parts"][k + "Icon"] = (g.get("codename") or g["name_pt"])[:18]
        crew_en = f"{g['crew']} crew"
        crew_pt = f"{g['crew']} tripulante" + ("s" if g["crew"] > 1 else "")
        if g in D.DEFENSES:
            role_en = ("DEFENSE. Airburst flak that damages EVERY missile, mine, shell, laser bolt and ion shot inside its blast. "
                       "Set it to Defend, Attack or Both.")
            role_pt = ("DEFESA. Flak de explosão aérea que danifica TODOS os mísseis, minas, granadas, disparos laser e iônicos "
                       "dentro da explosão. Pode ser ajustada para Defender, Atacar ou Ambos.")
        else:
            role_en, role_pt = "", ""
        oc_en = " Can be overclocked." if g.get("oc") else ""
        oc_pt = " Aceita overclock." if g.get("oc") else ""
        en["Parts"][k + "Desc"] = (f"{fen}{code}\n\n{TIER_EN[g['tier']]} deck weapon. Range {w['range_m']} m. "
                                   f"Needs no power: {crew_en} and {_ammo_word(g, 'en')}.{oc_en}"
                                   + (f"\n\n{role_en}" if role_en else "") + "<string id='BSModTag'/>")
        pt["Parts"][k + "Desc"] = (f"{fpt}{code}\n\n{TIER_PT[g['tier']]} - arma de convés. Alcance {w['range_m']} m. "
                                   f"Não usa energia: {crew_pt} e {_ammo_word(g, 'pt')}.{oc_pt}"
                                   + (f"\n\n{role_pt}" if role_pt else "") + "<string id='BSModTag'/>")
        if g.get("oc"):
            ocd = (w.get("overclock") or {}).get("description", "")
            en["Parts"][k + "Overclock"] = f"Overclocked {g['name_en']}"
            pt["Parts"][k + "Overclock"] = f"{g['name_pt']} (Overclocking)"
            en["Parts"][k + "OverclockDesc"] = (ocd or "Fires faster and harder, but produces a lot of waste heat.") + \
                " Produces waste heat while firing."
            pt["Parts"][k + "OverclockDesc"] = OC_PT.get(g["short"], "Atira mais rápido e mais forte, mas gera muito calor.") + \
                " Gera calor residual ao disparar."

    _factory_strings(D, en, pt)

    for r in D.RESOURCES:
        k = r["key"]
        en["Resource"][k] = r["name_en"]
        pt["Resource"][k] = r["name_pt"]
        en["Resource"][k + "Plural"] = r["name_en"] + ("s" if not r["name_en"].endswith("s") else "")
        pt["Resource"][k + "Plural"] = PLURAL_PT.get(r["name_pt"], r["name_pt"] + "s")
        en["Resource"][k + "Desc"] = RES_DESC_EN.get(r["art"]["kind"], "") + " Bullet Strike ammunition."
        pt["Resource"][k + "Desc"] = RES_DESC_PT.get(r["art"]["kind"], "") + " Munição do Bullet Strike."

    for idx, a in enumerate(("std", "ap", "aphe", "emp")):
        key = {0: "Std", 1: "AP", 2: "APHE", 3: "EMP"}[idx]
        n_en, n_pt = AMMO_NAMES[a]
        d_en, d_pt = AMMO_DESC[a]
        en["PartToggles"][f"BSAmmo_{key}"] = f"<b>Ammo: {n_en}</b>\n\n{d_en}"
        pt["PartToggles"][f"BSAmmo_{key}"] = f"<b>Munição: {n_pt}</b>\n\n{d_pt}"
        en["PartToggles"][f"BSAmmo_{key}Name"] = f"{n_en} Magazines"
        pt["PartToggles"][f"BSAmmo_{key}Name"] = f"Carregadores: {n_pt}"
        en["PartToggles"][f"BSAmmo_{key}Desc"] = d_en
        pt["PartToggles"][f"BSAmmo_{key}Desc"] = d_pt

    for a, (n_en, n_pt) in AMMO_NAMES.items():
        en["StatCategories"][f"BSAmmo_{a}"] = n_en
        pt["StatCategories"][f"BSAmmo_{a}"] = n_pt
    en["CategoryNouns"], pt["CategoryNouns"] = {}, {}
    for l in D.LIMIT_DEFS:
        key = "BS" + "".join(p.capitalize() for p in l["category"].split("_")[1:])
        en["CategoryNouns"][key + "Singular"], en["CategoryNouns"][key + "Plural"] = l["en"]
        pt["CategoryNouns"][key + "Singular"], pt["CategoryNouns"][key + "Plural"] = l["pt"]
    en["StatCategories"]["BSFlak"] = "Airburst Flak"
    pt["StatCategories"]["BSFlak"] = "Flak de explosão aérea"
    en["Stats"]["BSShotsPerMagFmt"] = "<white>Shots per Load:</white> <good>{0:0}</good>"
    pt["Stats"]["BSShotsPerMagFmt"] = "<white>Disparos por carga:</white> <good>{0:0}</good>"
    en["Stats"]["BSFactoryOutputFmt"] = "<white>Production:</white> <good>{0:0.##}</good><gray>/sec</gray>"
    pt["Stats"]["BSFactoryOutputFmt"] = "<white>Produção:</white> <good>{0:0.##}</good><gray>/s</gray>"
    _factory_stat_strings(D, en, pt)
    _launcher_strings(D, en, pt)
    return en, pt


# ============================================================================= fabricas
# Recursos vanilla citados nas descricoes: chave em strings/<lingua>.rules Resource/<chave> (nome traduzido pelo
# proprio jogo) e rotulo da linha "uso de <insumo>" das fabricas (en, pt).
VANILLA_RES = {
    "bullet": ("Bullet", "Cannon Ammo Use", "Uso de munição de canhão"),
    "sulfur": ("Sulfur", "Sulfur Use", "Uso de enxofre"),
    "coil": ("Coil", "Coil Use", "Uso de bobina"),
    "copper": ("Copper", "Copper Use", "Uso de cobre"),
    "tristeel": ("Tristeel", "Tri-Steel Use", "Uso de triaço"),
    "enriched_uranium": ("EnrichedUranium", "Enriched Uranium Use", "Uso de urânio enriquecido"),
}
# Taxa da Fabrica de Municao para Canhao vanilla (factory_ammo.rules: ToQuantity 1 / Interval 0.5 s)
VANILLA_AMMO_PER_S = 2.0


def _res_ref(D, res, qty):
    """<string id='Resource/X'/> (ou XPlural) do recurso: o jogo mostra o nome traduzido."""
    own = next((r for r in D.RESOURCES if r["id"] == res), None)
    key = own["key"] if own else VANILLA_RES[res][0]
    return f"<string id='Resource/{key}{'Plural' if qty > 1 else ''}'/>"


def _factory_strings(D, en, pt):
    seen = {"en": {}, "pt": {}}
    for f in D.FACTORIES:
        k = f["key"]
        out_r, out_q = f["output"]
        ins_en = " + ".join(f"{_num_en(q, 3)} {_res_ref(D, r, q)}" for r, q in f["inputs"])
        ins_pt = " + ".join(f"{_num_pt(q, 3)} {_res_ref(D, r, q)}" for r, q in f["inputs"])
        out_ref = _res_ref(D, out_r, out_q)
        pw_en = f" and {_num_en(f['power'] / 1000, 3)} power" if f.get("power") else " (no power needed)"
        pw_pt = f" e {_num_pt(f['power'] / 1000, 3)} de energia" if f.get("power") else " (não usa energia)"
        oc = f.get("oc")
        oc_en = " Can be overclocked." if oc else ""
        oc_pt = " Aceita overclock." if oc else ""
        tip_en = tip_pt = ""
        bullets = sum(q for r, q in f["inputs"] if r == "bullet")
        if bullets:
            # dica do spec: quantas Fabricas de Municao vanilla alimentam esta fabrica (mesmos bonus dos dois lados)
            need = bullets / f["interval"] / VANILLA_AMMO_PER_S
            if abs(need - round(need)) > 1e-6:
                raise ValueError(f"{f['short']}: {need:.3f} Fabricas de Municao por prensa nao e um numero inteiro")
            need = int(round(need))
            fac_en = "Cannon Ammo Factory" if need == 1 else "Cannon Ammo Factories"
            fac_pt = "Fábrica de munição para canhão" if need == 1 else "Fábricas de munição para canhão"
            tip_en = f"\n\nTip: {need} {fac_en} feed{'s' if need == 1 else ''} 1 {f['name_en']}."
            tip_pt = f"\n\nDica: {need} {fac_pt} alimenta{'m' if need > 1 else ''} 1 {f['name_pt']}."
        en["Parts"][k] = f["name_en"]
        pt["Parts"][k] = f["name_pt"]
        # rotulo do menu de construcao = o produto, como no vanilla (FactoryAmmoIcon = "Ammo")
        icon_en = f.get("icon_en") or f["name_en"]
        icon_pt = f.get("icon_pt") or f["name_pt"]
        for lang, lab in (("en", icon_en), ("pt", icon_pt)):
            if len(lab) > 24:
                raise ValueError(f"{f['short']}: rotulo do icone '{lab}' ({lang}) passa de 24 caracteres")
            if lab in seen[lang]:
                raise ValueError(f"{f['short']}: rotulo do icone '{lab}' ({lang}) repete o de {seen[lang][lab]}")
            seen[lang][lab] = f["short"]
        en["Parts"][k + "Icon"] = icon_en
        pt["Parts"][k + "Icon"] = icon_pt
        en["Parts"][k + "Desc"] = (f"Turns {ins_en}{pw_en} into {_num_en(out_q, 3)} {out_ref} every "
                                   f"{_num_en(f['interval'], 3)} s. +25% speed for each adjacent factory.{oc_en}"
                                   f"{tip_en}<string id='BSModTag'/>")
        pt["Parts"][k + "Desc"] = (f"Transforma {ins_pt}{pw_pt} em {_num_pt(out_q, 3)} {out_ref} a cada "
                                   f"{_num_pt(f['interval'], 3)} s. +25% de velocidade para cada fábrica vizinha."
                                   f"{oc_pt}{tip_pt}<string id='BSModTag'/>")
        if oc:
            sf = oc["speed_factor"]
            out_pl = _res_ref(D, out_r, 2)
            pwx_en = (f", using {_num_en(oc['power_use_factor'])}x the power per item" if f.get("power") else "")
            pwx_pt = (f", com {_num_pt(oc['power_use_factor'])} vez a energia por item" if f.get("power") else "")
            en["Parts"][k + "Overclock"] = f"Overclocked {f['name_en']}"
            pt["Parts"][k + "Overclock"] = f"{f['name_pt']} (Overclocking)"
            en["Parts"][k + "OverclockDesc"] = (f"Produces {_num_en(sf)}x faster{pwx_en}. Produces waste heat while "
                                                f"producing {out_pl}.")
            pt["Parts"][k + "OverclockDesc"] = (f"Produz {_num_pt(sf)} vezes mais rápido{pwx_pt}. Produz calor "
                                                f"enquanto fabrica {out_pl}.")


def _factory_stat_strings(D, en, pt):
    """Linhas 'uso de <insumo>' das fabricas ([por item, por segundo]); mesmo formato de AmmoSulfurUsageFmt."""
    from bsgen.factory import input_stat_ids, use_stat
    labels = {}
    for f in D.FACTORIES:
        for r, _q in f["inputs"]:
            own = next((x for x in D.RESOURCES if x["id"] == r), None)
            if own:
                labels[use_stat(r)] = (f"{own['name_en']} Use", f"Uso de {own['name_pt'].lower()}")
            else:
                labels[use_stat(r)] = VANILLA_RES[r][1:]
    for sid in input_stat_ids(D.FACTORIES):
        l_en, l_pt = labels[sid]
        en["Stats"][sid + "Fmt"] = (f"<white>{l_en}:</white> <good>{{0:0.###}}</good><gray>/ammo (</gray>"
                                    f"<good>{{1:0.###}}</good><gray>/sec)</gray>")
        pt["Stats"][sid + "Fmt"] = (f"<white>{l_pt}:</white> <good>{{0:0.###}}</good><gray>/munição (</gray>"
                                    f"<good>{{1:0.###}}</good><gray>/s)</gray>")


# ============================================================================= lancadores de misseis
# Nomes e codinomes vem do spec (tools/spec/bullet_strike_missiles.json); aqui so as frases.
MISSILE_TXT = {  # tipo: (nome curto en, nome curto pt, descricao en, descricao pt)
    "he": ("High-Explosive", "Alto-Explosivo",
           "A fast, direct high-explosive warhead: the reference missile. Big salvos saturate point defense.",
           "Ogiva alto-explosiva rápida e direta: o míssil de referência. Salvas grandes saturam a defesa de ponto."),
    "cluster": ("Cluster", "Submunições",
                "Opens 25 m from the enemy hull (or on impact, or at the end of its flight) and releases a school of "
                "mini-missiles that spread over several parts. Shot down before it opens, it releases nothing.",
                "Abre a 25 m do casco inimigo (ou no impacto, ou no fim do voo) e solta um cardume de minimísseis que "
                "se espalham por várias peças. Abatido antes de abrir, não solta nada."),
    "limpet": ("Limpet", "Grudento",
               "Sticks to the hull and explodes 2.5 s later, with a high chance to kill crew rushing in to repair. "
               "Shot down in flight it is lost; on a shield it only pops.",
               "Gruda no casco e explode 2,5 s depois, com alta chance de matar a tripulação que vier consertar. "
               "Abatido no voo, se perde; num escudo só estoura."),
    "napalm": ("Napalm", "Napalm",
               "Small blast, guaranteed fire on the part it hits and a heat pool that keeps lighting new fires. "
               "Useless against armor; extinguishers and foam are the counter.",
               "Explosão pequena, fogo garantido na peça atingida e calor em volta que continua acendendo incêndios. "
               "Inútil contra blindagem; extintor e espuma são o contra."),
    "emp": ("EMP", "PEM",
            "Drains batteries and shields in an area and keeps draining powered parts for a few seconds. "
            "Bullet Strike weapons have no battery and are immune.",
            "Drena baterias e escudos em área e continua drenando as peças com energia por alguns segundos. "
            "As armas do Bullet Strike não usam bateria e são imunes."),
    "torpedo": ("Decoy Torpedo", "Torpedo com Iscas",
                "A slow, tough torpedo: 1.5 s after launch the warhead separates among decoys that soak up point "
                "defense and flak.",
                "Torpedo lento e resistente: 1,5 s depois do lançamento a ogiva se separa no meio de iscas que gastam "
                "a defesa de ponto e a flak."),
    "nuclear": ("Nuclear Torpedo", "Torpedo Nuclear",
                "Heavy battery only. Counts toward the nuclear limit (2 per ship, shared with the Boiúna) and overclock "
                "never speeds up its reload. Dies to area flak on its own: mask it with a heavy salvo fired right after it.",
                "Só na bateria pesada. Conta no limite nuclear (2 por nave, junto com a Boiúna) e o overclock nunca "
                "acelera a recarga. Sozinho morre para flak de área: esconda-o com uma salva pesada logo depois."),
}
RES_WORD = {"missile_part_he": ("H.E. Missile Parts", "peças de míssil A.E."),
            "missile_part_thermal": ("T.C. Missile Parts", "peças de míssil T.C."),
            "missile_part_emp": ("E.M.P. Missile Parts", "peças de míssil PEM"),
            "missile_part_nuke": ("Nuclear Missile Parts", "peças de míssil nuclear")}
LAUNCHER_FLAVOR = {
    "bs_msl_box": ("A RAM-style micro-missile box: the gunner cranks it around and twelve micro-missiles hiss out, "
                   "pair by pair.",
                   "Uma caixa de micromísseis estilo RAM: o atirador gira a caixa e doze micromísseis saem chiando, "
                   "de dois em dois."),
    "bs_msl_twin": ("Two octagonal pods flank an armored sensor dome; a full rack is a two-second drum-roll of sixteen "
                    "missiles, right pod first.",
                    "Dois casulos octogonais ladeiam uma cúpula blindada com olho sensor; o rack cheio vira um rufar de "
                    "dezesseis mísseis em dois segundos, o casulo direito primeiro."),
    "bs_msl_quad": ("A headless armored body carries four long pods on hydraulic arms: a stampede of 48 heavy missiles "
                    "in three seconds. Loaded, it is the most dangerous part of your ship.",
                    "Um corpo blindado sem cabeça carrega quatro casulos longos em braços hidráulicos: um estouro de 48 "
                    "mísseis pesados em três segundos. Carregada, é a peça mais perigosa da sua nave."),
}
FAMILY_WORD = {"missile_part_he": ("H.E.", "A.E."), "missile_part_thermal": ("thermal", "térmica"),
               "missile_part_emp": ("EMP", "PEM"), "missile_part_nuke": ("nuclear", "nuclear")}


def _low(s):
    """Minuscula para uso no meio da frase, sem estragar siglas (PEM)."""
    return " ".join(w if w.isupper() else w.lower() for w in s.split(" "))


def _num_pt(x, nd=2):
    return f"{x:.{nd}f}".rstrip("0").rstrip(".").replace(".", ",")


def _num_en(x, nd=2):
    return f"{x:.{nd}f}".rstrip("0").rstrip(".")


def _launcher_strings(D, en, pt):
    for c_idx, cid, key, _icon, mt in D.MISSILE_CHOICES:
        t = D.MISSILE_TYPES[mt]
        s_en, s_pt, d_en, d_pt = MISSILE_TXT[mt]
        k = key.split("/", 1)[1]
        en["PartToggles"][k] = f"<b>Missile: {t['codename']} ({s_en})</b>\n\n{d_en}"
        pt["PartToggles"][k] = f"<b>Míssil: {t['codename']} ({s_pt})</b>\n\n{d_pt}"
        en["PartToggles"][k + "Name"] = f"{t['codename']} Missiles ({s_en})"
        pt["PartToggles"][k + "Name"] = f"Mísseis {t['codename']} ({_low(s_pt)})"
        en["PartToggles"][k + "Desc"] = d_en
        pt["PartToggles"][k + "Desc"] = d_pt
    for lch in D.LAUNCHERS:
        k = lch["key"]
        m0 = lch["modes"][0]
        n = m0["cells"] * m0["mpu"]
        salvo_t = (m0["cells"] - 1) * lch["ripple_s"] + (m0["mpu"] - 1) * (2 / 30)
        cycle = m0["cells"] * m0["reload"] + salvo_t
        unit_en = "cassette" if m0["mpu"] > 1 else "cell"
        unit_pt = "um cassete" if m0["mpu"] > 1 else "uma célula"
        rng = lch["spec"]["range_m"][m0["type"]]
        mis_en = ", ".join(f"{m['codename']} ({MISSILE_TXT[m['type']][0]})" for m in lch["modes"])
        mis_pt = ", ".join(f"{m['codename']} ({_low(MISSILE_TXT[m['type']][1])})" for m in lch["modes"])
        res_en = " / ".join(RES_WORD[f["res"]][0] for f in lch["families"])
        res_pt = " / ".join(RES_WORD[f["res"]][1] for f in lch["families"])
        mags = [f["mag"] for f in lch["families"]]
        if len(set(mags)) == 1:
            mag_en, mag_pt = f"{mags[0]} parts each", f"{mags[0]} peças cada"
        else:
            mag_en = ", ".join(f"{FAMILY_WORD[f['res']][0]} {f['mag']}" for f in lch["families"]) + " parts"
            mag_pt = ", ".join(f"{FAMILY_WORD[f['res']][1]} {f['mag']}" for f in lch["families"]) + " peças"
        crew_en = f"{lch['crew']} crew"
        crew_pt = f"{lch['crew']} tripulante" + ("s" if lch["crew"] > 1 else "")
        fl_en, fl_pt = LAUNCHER_FLAVOR.get(lch["short"], ("Deck missile launcher.", "Lança-mísseis de convés."))
        # salva parcial (variante dry_flush do spec): o texto segue o mecanismo gerado
        dry_en, dry_pt = {
            "debounced": ("; when the magazine stays dry for a whole reload, the partial rack still fires",
                          "; se o paiol fica vazio por uma recarga inteira, o rack parcial dispara mesmo assim"),
            "instant": ("; a dry magazine still fires the partial rack",
                        "; com o paiol vazio, o rack parcial dispara mesmo assim"),
        }.get(D.MISSILE_VARIANTS.get("dry_flush", "debounced"), ("", ""))
        oc_en = " Can be overclocked." if lch.get("oc") else ""
        oc_pt = " Aceita overclock." if lch.get("oc") else ""
        # salvas de tamanhos diferentes por modo (Mula: 48 finos, 16 pesados, 4 torpedos, 2 Iara)
        sizes = {}
        for m in lch["modes"]:
            sizes.setdefault(m["cells"] * m["mpu"], []).append(m["codename"])
        var_en = var_pt = ""
        if len(sizes) > 1:
            var_en = " Missiles per salvo: " + "; ".join(f"{', '.join(v)} {n}" for n, v in sizes.items()) + "."
            var_pt = " Mísseis por salva: " + "; ".join(f"{', '.join(v)} {n}" for n, v in sizes.items()) + "."
        lim_en = lim_pt = ""
        lims = [c for c in lch["categories"] if c.startswith("bs_limit_")]
        if "bs_limit_nuke" in lims:
            mx = next(l_[1] for l_ in D.LIMITS if l_[0] == "bs_limit_nuke")
            lim_en = (f"\n\nLimit: {mx} per ship, shared with the Boiúna nuclear howitzer (nuclear weapons, any mix).")
            lim_pt = (f"\n\nLimite: {mx} por nave, junto com o obuseiro nuclear Boiúna (armas nucleares, em qualquer "
                      f"combinação).")
        en["Parts"][k] = lch["name_en"]
        pt["Parts"][k] = lch["name_pt"]
        en["Parts"][k + "Icon"] = lch["codename"][:18]
        pt["Parts"][k + "Icon"] = lch["codename"][:18]
        en["Parts"][k + "Desc"] = (
            f"{fl_en} \"{lch['codename']}\"\n\n{TIER_EN[lch['tier']]} deck missile launcher. A full rack ripples "
            f"{n} missiles in {_num_en(salvo_t)} s, then a crewed autoloader refills it one {unit_en} at a time "
            f"({_num_en(m0['reload'])} s each; reloading stops while nobody mans it): one salvo every "
            f"{_num_en(cycle, 1)} s. Range {rng} m. Missiles: {mis_en}.{var_en}\n\nNeeds no power: {crew_en} and vanilla "
            f"{res_en} carried into its internal magazines ({mag_en}). Switching the missile type costs one "
            f"full reload{dry_en}. The missiles "
            f"fly over your own deck and can be shot down by point defense. A loaded launcher cooks off when it burns or is destroyed.{oc_en}{lim_en}"
            "<string id='BSModTag'/>")
        pt["Parts"][k + "Desc"] = (
            f"{fl_pt} \"{lch['codename']}\"\n\n{TIER_PT[lch['tier']]} - lança-mísseis de convés. Com o rack cheio, "
            f"dispara {n} mísseis em sequência em {_num_pt(salvo_t)} s; depois um autocarregador tripulado recarrega "
            f"{unit_pt} por vez ({_num_pt(m0['reload'])} s cada; sem tripulação no posto a recarga para): uma "
            f"salva a cada {_num_pt(cycle, 1)} s. Alcance {rng} m. Mísseis: {mis_pt}.{var_pt}\n\nNão usa energia: "
            f"{crew_pt} e {res_pt} do jogo base levadas até os paióis internos ({mag_pt}). Trocar o tipo de "
            f"míssil custa uma recarga completa{dry_pt}. Os mísseis passam por cima do próprio convés e podem ser abatidos pela defesa de "
            f"ponto. Carregado, o lançador explode quando pega fogo ou é destruído.{oc_pt}{lim_pt}<string id='BSModTag'/>")
        if lch["tier"] == "early":
            # tech do Build & Battle que libera as pecas de missil vanilla do lancador de inicio (bs_data.buildbattle_techs)
            res_and_en = " and ".join(RES_WORD[f["res"]][0] for f in lch["families"])
            res_and_pt = " e as ".join(RES_WORD[f["res"]][1] for f in lch["families"])
            en["Parts"][k + "Ammo"] = f"{lch['codename']} Missile Parts"
            pt["Parts"][k + "Ammo"] = f"Peças de Míssil da {lch['codename']}"
            en["Parts"][k + "AmmoDesc"] = (
                f"Unlocks the vanilla {res_and_en} that the {lch['name_en']} \"{lch['codename']}\" fires. In Build & "
                f"Battle the launcher itself is always available, but its missile parts are not.")
            pt["Parts"][k + "AmmoDesc"] = (
                f"Libera as {res_and_pt} do jogo base que a {lch['name_pt']} \"{lch['codename']}\" dispara. No Build "
                f"& Battle o lançador já vem liberado, mas as peças de míssil não.")
        if lch.get("oc"):
            o = lch["spec"]["overclock"]
            en["Parts"][k + "Overclock"] = f"Overclocked {lch['name_en']}"
            pt["Parts"][k + "Overclock"] = f"{lch['name_pt']} (Overclocking)"
            oc = lch["oc"]
            fac = sorted({m["oc_factor"] for m in lch["modes"] if m["oc_factor"]}, reverse=True)
            emp = [m for m in lch["modes"] if m["oc_factor"] and m["oc_factor"] != fac[0]]
            no_oc = [m for m in lch["modes"] if not m["oc_factor"]]
            vent = any(m["vent"] for m in lch["modes"])
            ex_en = "".join(f" ({m['codename']}: {_num_en(m['oc_factor'])}x)" for m in emp)
            ex_pt = "".join(f" ({m['codename']}: {_num_pt(m['oc_factor'])} vez)" for m in emp)
            nn_en = "".join(f" It never speeds up the reload of the {m['codename']} {m['name_en'].lower()}." for m in no_oc)
            nn_pt = "".join(f" Nunca acelera a recarga do {m['name_pt'].lower()} {m['codename']}." for m in no_oc)
            pre = D.MISSILE_VARIANTS.get("prefilled_switch", "full_delay") == "full_delay"
            pre_en = (" A rack that is already full when you switch to its missile type waits a normal (not overclocked) "
                      "reload." if pre else "")
            pre_pt = (" Um rack que já estava cheio na troca de míssil espera a recarga normal (sem overclock)."
                      if pre else "")
            vent_en = " About 1 in 16 missiles is vented from the magazine every salvo (torpedoes exempt)." if vent else ""
            vent_pt = (" Cerca de 1 em cada 16 mísseis é descartado do paiol a cada salva (torpedos isentos)."
                       if vent else "")
            en["Parts"][k + "OverclockDesc"] = (
                f"\"{o.get('name_en', '')}\": the autoloader works {_num_en(fac[0])}x faster{ex_en}; ripple, damage and "
                f"range stay the same.{nn_en} Costs {oc['heat_per_part']} heat per missile part loaded plus "
                f"{oc['heat_per_second']} heat/s (needs radiators).{vent_en}{pre_en} Switching it off pauses the launcher for 3 s, "
                f"and the magazine empties faster. Without enough cooling it overheats, catches fire and cooks off with "
                f"its stock.")
            pt["Parts"][k + "OverclockDesc"] = (
                f"\"{o.get('name_ptbr', '')}\": o autocarregador trabalha {_num_pt(fac[0])} vez mais rápido{ex_pt}; "
                f"ripple, dano e alcance não mudam.{nn_pt} Custa {oc['heat_per_part']} de calor por peça de míssil "
                f"carregada mais {oc['heat_per_second']} de calor/s (precisa de radiador).{vent_pt}{pre_pt} Desligar dá uma "
                f"pausa de 3 s e o paiol esvazia mais rápido. Sem refrigeração suficiente, esquenta, pega fogo e explode "
                f"junto com o estoque.")
        for m in lch["modes"]:
            en["StatCategories"][f"{k}_{m['type']}"] = f"{m['name_en']} \"{m['codename']}\""
            pt["StatCategories"][f"{k}_{m['type']}"] = f"{m['name_pt']} \"{m['codename']}\""


RES_DESC_EN = {"mag": "A sealed magazine that crew carry to Bullet Strike guns. Each gun opens it into a number of shots.",
               "cell": "A magnetically sealed cell of plasma for plasma weapons.",
               "shell": "A nuclear artillery shell. Handle with care: it cooks off violently if its storage is destroyed."}
RES_DESC_PT = {"mag": "Um carregador lacrado que a tripulação leva até as armas do Bullet Strike. Cada arma o abre em vários disparos.",
               "cell": "Uma célula de plasma selada magneticamente para armas de plasma.",
               "shell": "Um projétil de artilharia nuclear. Cuidado: explode violentamente se o depósito for destruído."}
# plural em pt-br: o nucleo do nome vai para o plural ("Carregador Padrao" + "s" daria "Carregador Padraos")
PLURAL_PT = {
    "Carregador Padrão": "Carregadores Padrão",
    "Carregador Perfurante": "Carregadores Perfurantes",
    "Carregador EMP": "Carregadores EMP",
    "Célula de Plasma": "Células de Plasma",
    "Projétil Nuclear": "Projéteis Nucleares",
}
OC_PT = {}
