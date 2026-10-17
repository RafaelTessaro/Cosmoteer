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

    for f in D.FACTORIES:
        k = f["key"]
        ins_en = " + ".join(f"{q} {r.split('.')[-1]}" for r, q in f["inputs"])
        out_r, out_q = f["output"]
        out_name_en = next((r["name_en"] for r in D.RESOURCES if r["id"] == out_r), out_r)
        out_name_pt = next((r["name_pt"] for r in D.RESOURCES if r["id"] == out_r), out_r)
        pw_en = f" and {f['power'] / 1000:g} power" if f.get("power") else " (no power needed)"
        pw_pt = f" e {f['power'] / 1000:g} de energia" if f.get("power") else " (não usa energia)"
        en["Parts"][k] = f["name_en"]
        pt["Parts"][k] = f["name_pt"]
        en["Parts"][k + "Icon"] = f["name_en"][:18]
        pt["Parts"][k + "Icon"] = f["name_pt"][:18]
        en["Parts"][k + "Desc"] = (f"Turns {ins_en}{pw_en} into {out_q} {out_name_en} every {f['interval']:g} s. "
                                   f"+25% speed for each adjacent factory.<string id='BSModTag'/>")
        pt["Parts"][k + "Desc"] = (f"Transforma {ins_en}{pw_pt} em {out_q} {out_name_pt} a cada {f['interval']:g} s. "
                                   f"+25% de velocidade para cada fábrica vizinha.<string id='BSModTag'/>")

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
    return en, pt


RES_DESC_EN = {"mag": "A sealed magazine that crew carry to Bullet Strike guns. Each gun opens it into a number of shots.",
               "cell": "A magnetically sealed cell of plasma for plasma weapons.",
               "shell": "A nuclear artillery shell. Handle with care: it cooks off violently if its storage is destroyed."}
RES_DESC_PT = {"mag": "Um carregador lacrado que a tripulação leva até as armas do Bullet Strike. Cada arma o abre em vários disparos.",
               "cell": "Uma célula de plasma selada magneticamente para armas de plasma.",
               "shell": "Um projétil de artilharia nuclear. Cuidado: explode violentamente se o depósito for destruído."}
PLURAL_PT = {}
OC_PT = {}
