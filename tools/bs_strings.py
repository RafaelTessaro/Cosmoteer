"""Textos (en / pt-br) do Bullet Strike 2.0 que o WP01 escreve: grupo do editor, recursos, seletores (bs_ammo_type,
bs_cell_type, bs_missile_type), estatisticas, limites por nave, techs e os textos das pecas de canhao/defesa.

Os modulos de conteudo acrescentam os seus pelo gancho strings(DATA) -> (en, pt) (mesmo formato: dict grupo -> dict
chave -> texto); o build_mod junta tudo e o texto do modulo vence o daqui na mesma chave.
Nunca citar nomes removidos (SPEC.conventions.removed_names_scan), nem para dizer que sairam.
"""

TIER_EN = {"early": "Early-game", "mid": "Mid-game", "late": "Late-game"}
TIER_PT = {"early": "Início de jogo", "mid": "Meio de jogo", "late": "Fim de jogo"}

# descricoes em ingles dos 12 recursos (o pt-BR vem de SPEC.resources[].description_ptbr), por resources[].key
RES_DESC_EN = {
    "he": "Standard High-Explosive ammunition. Made at the HE Press from sulfur only.",
    "ap": "Armor-Piercing: less damage, tunnels through armor and SW small/medium shields.",
    "sap": "Semi-Armor-Piercing: the middle ground between HE and AP.",
    "ac": "High-Capacity: a huge bursting charge, nothing nuclear. Expensive, but the most destructive.",
    "frag": "Programmable Fragment Cloud (defenses only): bursts ahead of missiles and shots.",
    "plasma": "Plasma Cell for Boitatá and Curupira (shield specialist).",
    "pem": "Charged EMP Cell for the EMP cannon line (drains shields). Made at the Cell Factory from copper only.",
    "msl_he": "High-Explosive missile charge (Jararaca).",
    "msl_cluster": "Cluster missile charge: the carrier opens and releases several mini-missiles (Piranha). Not the "
                   "defenses' FRAG.",
    "msl_emp": "EMP missile charge: a flux-compression generator that drains shields (Poraquê).",
    "msl_nuke": "Nuclear warhead: 1 warhead = 1 Iara missile (Mula-sem-Cabeça only).",
    "slug": "Solid slug for the Tupã railgun. Inert (it barely explodes).",
}
PLURAL_PT_HEAD = {"Carregador": "Carregadores", "Célula": "Células", "Carga": "Cargas", "Ogiva": "Ogivas",
                  "Projétil": "Projéteis"}
PLURAL_PT_FULL = {"Ogiva Nuclear": "Ogivas Nucleares"}

# nomes das celulas (SPEC.toggles.bs_cell_type so tem name_ptbr)
CELL_TXT = {"plasma": ("Plasma", "Plasma", "Plasma Cells for Boitatá and Curupira (shield specialists).",
                       "Células de Plasma para Boitatá e Curupira (especialistas contra escudos)."),
            "pem": ("EMP", "PEM", "EMP Cells for the EMP cannon line (Tuvira, Treme-Treme and the heavy one).",
                    "Células PEM para a linha de canhões PEM (Tuvira, Treme-Treme e a pesada).")}

# techs com nome proprio (bs_data.NAMED_TECHS): (en, pt, desc en, desc pt)
TECH_NAMES = {
    "rafaeltessaro.bs_logistica": (
        "Ammo Logistics", "Logística de Munição",
        "Shell magazines (1x1 and 2x2) and the ammo logistics of Bullet Strike: factories fill the magazines and the "
        "magazines feed the guns.",
        "Paióis de cartuchos (1x1 e 2x2) e a logística de munição do Bullet Strike: as fábricas enchem os paióis e os "
        "paióis abastecem as armas."),
    "rafaeltessaro.bs_paiol_pesado": (
        "Heavy Magazines", "Paiol Pesado",
        "3x3 magazines for shells, cells and missiles: more stock per tile.",
        "Paióis 3x3 de cartuchos, células e mísseis: mais estoque por quadro."),
    "rafaeltessaro.bs_rail": (
        "Tupã Railgun", "Railgun Tupã",
        "Modular fixed railgun: Loader + 1 to 6 Barrels + Muzzle. More barrels = more damage, range, penetration and "
        "power per shot. Plus the Slug Factory.",
        "Railgun fixa e modular: Carregador + 1 a 6 Canos + Ponta. Mais canos = mais dano, alcance, penetração e "
        "energia por tiro. Mais a Fábrica de Projéteis."),
}

# frases de efeito por arma (pedaco do ID curto; a primeira que bater: "quad" antes de "hmg"). en, pt
FLAVOR = [
    ("lmg", ("A cheap pintle-mounted machine gun. Small enough to fit anywhere on deck.",
             "Metralhadora barata em reparo de pino. Pequena o bastante para caber em qualquer canto do convés.")),
    ("quad", ("Four heavy machine guns on one mount. Can also swat down incoming missiles and mines.",
              "Quatro metralhadoras pesadas num só reparo. Também derruba mísseis e minas que se aproximam.")),
    ("hmg", ("Heavy machine gun that keeps a steady stream of tracers on target.",
             "Metralhadora pesada que mantém um fluxo constante de traçantes no alvo.")),
    ("autocannon", ("Twin 20 mm autocannon: the first real teeth of a gunboat.",
                    "Autocanhão duplo de 20 mm: os primeiros dentes de verdade de uma canhoneira.")),
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
    ("flak_heavy", ("Twin heavy flak battery: a wall of fire against missiles, shells and bolts.",
                    "Bateria dupla de flak pesada: uma muralha de fogo contra mísseis, granadas e disparos.")),
    ("nuke", ("Heavy deck howitzer with the biggest conventional shells of the mod: HE and a guided High-Capacity "
              "shell. Strong against crew and dense interiors, weak against armor; its slow shells can be shot down.",
              "Obuseiro pesado de convés com as maiores granadas convencionais do mod: HE e a granada de Alta "
              "Capacidade guiada. Forte contra tripulação e interiores densos, fraco contra blindagem; as granadas "
              "lentas podem ser abatidas.")),
]

AMMO_SHORT = {"he": "HE", "ap": "AP", "sap": "SAP", "ac": "AC", "frag": "FRAG"}


def _flavor(short):
    for key, txt in FLAVOR:
        if key in short:
            return txt
    return ("Deck-mounted ammunition weapon.", "Arma de convés movida a munição.")


def plural_en(name):
    head, sep, tail = name.partition(" (")
    head = head if head.endswith("s") else head + "s"
    return head + (sep + tail if sep else "")


def plural_pt(name):
    if name in PLURAL_PT_FULL:
        return PLURAL_PT_FULL[name]
    first, _, rest = name.partition(" ")
    if first in PLURAL_PT_HEAD:
        return PLURAL_PT_HEAD[first] + (" " + rest if rest else "")
    return name + "s"


def _pct(x):
    return f"{int(round((x - 1) * 100)):+d}%"


def _ammo_words(g, D):
    keys = [m["key"] for m in g["modes"]]
    if keys == ["plasma"]:
        return ("Plasma Cells", "células de plasma")
    names = " / ".join(AMMO_SHORT.get(k, k.upper()) for k in keys)
    if len(keys) > 1:
        return (f"magazines (selectable: {names})", f"carregadores (selecionáveis: {names})")
    return (f"{names} magazines", f"carregadores {names}")


def oc_text(oc, lang):
    """Descricao do overclock montada dos numeros do spec (fator de cadencia, alcance, dano)."""
    name = oc.get("name_en" if lang == "en" else "name_ptbr") or ""
    bits = []
    fr = oc.get("fire_rate_factor")
    if fr and abs(fr - 1) > 1e-3:
        bits.append(f"{_pct(fr)} {'fire rate' if lang == 'en' else 'cadência'}")
    rf = oc.get("range_factor")
    if rf and abs(rf - 1) > 1e-3:
        bits.append(f"{_pct(rf)} {'range' if lang == 'en' else 'alcance'}")
    df = oc.get("damage_factor")
    if df and abs(df - 1) > 1e-3:
        bits.append(f"{_pct(df)} {'damage' if lang == 'en' else 'dano'}")
    if oc.get("explosive_damage"):
        bits.append("explosion on impact" if lang == "en" else "explosão no impacto")
    if oc.get("cloud"):
        bits.append("leaves a flak cloud" if lang == "en" else "deixa uma nuvem de flak")
    body = ", ".join(bits) if bits else ("faster operation" if lang == "en" else "opera mais rápido")
    tail = " Produces waste heat when firing." if lang == "en" else " Produz calor ao disparar."
    return f"\"{name}\": {body}.{tail}" if name else f"{body[0].upper()}{body[1:]}.{tail}"


def _part_strings(D, en, pt):
    """Textos das pecas de canhao e de defesa (Parts/<key>, Desc, Icon, Overclock, OverclockDesc); o WP02 pode
    trocar pelo gancho strings(DATA)."""
    for g in D.GUNS + D.DEFENSES:
        k = g["key"]
        w = g["spec"]
        fen, fpt = _flavor(g["short"])
        code = f" \"{g['codename']}\"" if g.get("codename") else ""
        en["Parts"][k] = g["name_en"]
        pt["Parts"][k] = g["name_pt"]
        en["Parts"][k + "Icon"] = (g.get("codename") or g["name_en"])[:18]
        pt["Parts"][k + "Icon"] = (g.get("codename") or g["name_pt"])[:18]
        crew_en = f"{g['crew']} crew"
        crew_pt = f"{g['crew']} tripulante" + ("s" if g["crew"] > 1 else "")
        a_en, a_pt = _ammo_words(g, D)
        role_en = role_pt = ""
        if g in D.DEFENSES:
            role_en = ("DEFENSE. Airburst flak that damages EVERY missile, mine, shell, laser bolt and ion shot inside "
                       "its blast. Defense only: it never fires at ships. HE = proximity-fused airburst; FRAG = smaller "
                       "burst plus a cone of fragments, best against swarms and salvos.")
            role_pt = ("DEFESA. Flak de explosão aérea que danifica TODOS os mísseis, minas, granadas, disparos laser "
                       "e iônicos dentro da explosão. Só defende: nunca atira em naves. HE = espoleta de proximidade; "
                       "FRAG = explosão menor e um cone de fragmentos, melhor contra enxames e salvas.")
        oc_en = " Can be overclocked." if g.get("oc") else ""
        oc_pt = " Aceita overclock." if g.get("oc") else ""
        en["Parts"][k + "Desc"] = (f"{fen}{code}\n\n{TIER_EN[g['tier']]} deck weapon. Range {w['range_m']} m. "
                                   f"Needs no power: {crew_en} and {a_en}.{oc_en}"
                                   + (f"\n\n{role_en}" if role_en else "") + "<string id='BSModTag'/>")
        pt["Parts"][k + "Desc"] = (f"{fpt}{code}\n\n{TIER_PT[g['tier']]} - arma de convés. Alcance {w['range_m']} m. "
                                   f"Não usa energia: {crew_pt} e {a_pt}.{oc_pt}"
                                   + (f"\n\n{role_pt}" if role_pt else "") + "<string id='BSModTag'/>")
        if g.get("oc"):
            ocs = w.get("overclock") or {}
            en["Parts"][k + "Overclock"] = f"Overclocked {g['name_en']}"
            pt["Parts"][k + "Overclock"] = f"{g['name_pt']} (Overclocking)"
            en["Parts"][k + "OverclockDesc"] = oc_text(ocs, "en")
            pt["Parts"][k + "OverclockDesc"] = oc_text(ocs, "pt")


def _oc_spec(D, pid):
    for g in D.GUNS + D.DEFENSES:
        if g["id"] == pid:
            return g["spec"].get("overclock")
    for p in D.PEM:
        if p["id"] == pid:
            return p.get("overclock")
    for L in D.MSPEC.get("launchers", []):
        if L["id"] == pid:
            return D.launcher_overclock(L)
    return None


def _missile_name(D, key, lang):
    ch = next((c for c in D.TOGGLES["bs_missile_type"]["choices"] if c["index"] == D.MISSILE_INDEX.get(key)), None)
    if ch is None:
        return str(key).upper()
    return ch["name_en"] if lang == "en" else ch["name_ptbr"]


def launcher_oc_text(D, oc, lang):
    """Descricao do overclock de um lancador (MSPEC: divisor de recarga por modo; dano e alcance nao mudam)."""
    name = oc.get("name_en" if lang == "en" else "name_ptbr") or ""
    per = oc.get("per_mode") or {}
    top = oc.get("reload_factor")
    if top:
        body = f"{_pct(top)} {'reload speed' if lang == 'en' else 'velocidade de recarga'}"
        notes = [f"{_missile_name(D, k, lang)} {_pct(f)}" for k, f in per.items() if f and abs(f - top) > 1e-3]
        notes += [f"{_missile_name(D, k, lang)} {'unchanged' if lang == 'en' else 'sem mudança'}"
                  for k in oc.get("excluded") or []]
        if notes:
            body += f" ({', '.join(notes)})"
        body += "; damage and range unchanged" if lang == "en" else "; dano e alcance iguais"
    else:
        body = "faster reload" if lang == "en" else "recarga mais rápida"
    tail = " Produces waste heat while loading." if lang == "en" else " Produz calor ao carregar."
    return f"\"{name}\": {body}.{tail}" if name else f"{body[0].upper()}{body[1:]}.{tail}"


def _oc_strings(D, pid):
    info = D.PART_INFO.get(pid) or {}
    n_en, n_pt = info.get("name_en", pid), info.get("name_pt", pid)
    oc = _oc_spec(D, pid)
    if oc and info.get("kind") == "launcher":
        d_en, d_pt = launcher_oc_text(D, oc, "en"), launcher_oc_text(D, oc, "pt")
    elif oc and (oc.get("name_en") or oc.get("name_ptbr")):
        d_en, d_pt = oc_text(oc, "en"), oc_text(oc, "pt")
    elif info.get("kind") == "factory":
        d_en = "Overclock: the factory works 3x faster and uses 1.5x the power. Produces waste heat."
        d_pt = "Overclock: a fábrica trabalha 3x mais rápido e usa 1,5x a energia. Produz calor."
    else:
        d_en = "Unlocks the overclock of this part. Produces waste heat."
        d_pt = "Libera o overclock desta peça. Produz calor."
    return (f"Overclocked {n_en}", f"{n_pt} (Overclocking)", d_en, d_pt)


def _choice_strings(D, tok):
    kind, key = tok.split(":", 1)
    if kind == "ammo":
        a = next(x for x in D.SPEC["ammo_types"] if x["key"] == key)
        return (f"{a['name_en']} Ammo ({a['label']})", f"Munição {a['name_ptbr']} ({a['label']})", a["desc_en"],
                a["desc_ptbr"])
    if kind == "cell":
        c = CELL_TXT[key]
        return (f"{c[0]} Cells", f"Células {c[1]}", c[2], c[3])
    ch = next(c for c in D.TOGGLES["bs_missile_type"]["choices"] if c["index"] == D.MISSILE_INDEX[key])
    return (ch["name_en"], ch["name_ptbr"], ch["desc_en"], ch["desc_ptbr"])


def tech_strings(D):
    """Textos de todas as techs que usam chave propria (grupo BSTechs): nomeadas, so de overclock, so de escolha, e as
    do Build & Battle (overclock e municao da Tocandira)."""
    en, pt = {}, {}

    def put(key, t):
        en[key], pt[key], en[key + "Desc"], pt[key + "Desc"] = t[0], t[1], t[2], t[3]
    for t in D.SPEC["career_techs"]:
        tid = t["id"]
        key = D.tech_string_key(tid)
        toks = t["unlocks"]
        if tid in TECH_NAMES:
            put(key, TECH_NAMES[tid])
            continue
        ocs = [u.split(":", 1)[1] for u in toks if u.startswith("overclock:")]
        choices = [u for u in toks if u.startswith(("ammo:", "cell:", "missile:"))]
        if ocs:
            put(key, _oc_strings(D, ocs[0]))
        elif choices:
            put(key, _choice_strings(D, choices[0]))
        # tech so de pecas: o nome vem da propria peca (&<...>/Part/NameKey); sem chave propria
    for pid, info in D.PART_INFO.items():
        if info.get("oc"):
            put(D.tech_string_key(pid) + "_BBOC", _oc_strings(D, pid))
    for L in D.MSPEC.get("launchers", []):
        info = D.PART_INFO.get(L["id"]) or {}
        put(D.tech_string_key(L["id"]) + "_BBAmmo",
            (f"{info.get('name_en', L['id'])} Missiles", f"Mísseis do {info.get('name_pt', L['id'])}",
             "Unlocks the missile charges of this launcher.", "Libera as cargas de míssil deste lançador."))
    rk = D.tech_string_key(f"{D.AUTHOR}.bs_rail")
    if rk not in en:
        put(rk, TECH_NAMES[f"{D.AUTHOR}.bs_rail"])
    return en, pt


def _toggle_strings(D, en, pt):
    for a in D.SPEC["ammo_types"]:
        ch = next(c for c in D.TOGGLES["bs_ammo_type"]["choices"] if c["index"] == a["index"])
        key = ch["string_key"].split("/", 1)[1]
        r = D.RES_BY_ID.get(a["resource"])
        mag = f" Uses <string id='Resource/{r['key']}Plural'/>." if r else ""
        mag_pt = f" Usa <string id='Resource/{r['key']}Plural'/>." if r else ""
        en["PartToggles"][key] = f"<b>Ammo: {a['name_en']} ({a['label']})</b>\n\n{a['desc_en']}{mag}"
        pt["PartToggles"][key] = f"<b>Munição: {a['name_ptbr']} ({a['label']})</b>\n\n{a['desc_ptbr']}{mag_pt}"
    for ch in D.TOGGLES["bs_cell_type"]["choices"]:
        c = CELL_TXT[ch["key"]]
        key = cell_tip_key(ch["key"]).split("/", 1)[1]
        en["PartToggles"][key] = f"<b>Cell: {c[0]}</b>\n\n{c[2]}"
        pt["PartToggles"][key] = f"<b>Célula: {c[1]}</b>\n\n{c[3]}"
    for ch in D.TOGGLES["bs_missile_type"]["choices"]:
        key = ch["string_key"].split("/", 1)[1]
        en["PartToggles"][key] = f"<b>Missile: {ch['name_en']}</b>\n\n{ch['desc_en']}"
        pt["PartToggles"][key] = f"<b>Míssil: {ch['name_ptbr']}</b>\n\n{ch['desc_ptbr']}"


def cell_tip_key(key):
    return {"plasma": "PartToggles/BSCell_Plasma", "pem": "PartToggles/BSCell_PEM"}[key]


# recursos do jogo citados nas linhas 'uso de <insumo>' das fabricas (en, pt)
VANILLA_RES = {
    "sulfur": ("Sulfur Use", "Uso de enxofre"),
    "coil": ("Coil Use", "Uso de bobina"),
    "coil2": ("Superconductor Use", "Uso de supercondutor"),
    "copper": ("Copper Use", "Uso de cobre"),
    "tristeel": ("Tri-Steel Use", "Uso de triaço"),
    "iron": ("Iron Use", "Uso de ferro"),
    "uranium": ("Uranium Use", "Uso de urânio"),
}


def use_stat(res):
    """ID da linha 'uso de <insumo>' ([por item, por segundo]) - mesmo formato do factory.use_stat 1.x."""
    short = res.split(".")[-1]
    if short.startswith("bs_"):
        short = short[3:]
    return "BSAmmo" + "".join(p.capitalize() for p in short.split("_")) + "Usage"


def input_stat_ids(D):
    """Linhas 'uso de <insumo>' de todas as entradas das fabricas do spec (ordem de aparecimento)."""
    out = []
    for f in D.SPEC["factories"]:
        for r in f["recipes"]:
            for res in (r.get("inputs_per_cycle") or {}):
                sid = use_stat(res)
                if sid not in out:
                    out.append(sid)
    return out


def strings(written=None):
    """(en, pt) do nucleo; o build_mod junta os strings(DATA) dos modulos por cima."""
    import bs_data as D
    groups = ("EditorGroups", "Parts", "PartToggles", "Stats", "StatCategories", "Resource", "CategoryNouns", "BSTechs")
    en = {g: {} for g in groups}
    pt = {g: {} for g in groups}
    en["EditorGroups"]["BulletStrike"] = "Bullet Strike"
    pt["EditorGroups"]["BulletStrike"] = "Bullet Strike"

    for r in D.RESOURCES:
        k = r["key"]
        en["Resource"][k] = r["name_en"]
        pt["Resource"][k] = r["name_pt"]
        en["Resource"][k + "Plural"] = plural_en(r["name_en"])
        pt["Resource"][k + "Plural"] = plural_pt(r["name_pt"])
        en["Resource"][k + "Desc"] = RES_DESC_EN.get(r["spec_key"], "") + " Bullet Strike ammunition."
        pt["Resource"][k + "Desc"] = (r.get("desc_pt") or "") + " Munição do Bullet Strike."

    _toggle_strings(D, en, pt)
    _part_strings(D, en, pt)

    for a in D.SPEC["ammo_types"]:
        en["StatCategories"][f"BSAmmo_{a['key']}"] = f"{a['name_en']} ({a['label']})"
        pt["StatCategories"][f"BSAmmo_{a['key']}"] = f"{a['name_ptbr']} ({a['label']})"
    en["StatCategories"]["BSAmmo_plasma"], pt["StatCategories"]["BSAmmo_plasma"] = "Plasma Bolt", "Disparo de plasma"
    en["StatCategories"]["BSAmmo_pem"], pt["StatCategories"]["BSAmmo_pem"] = "EMP Shell", "Granada PEM"
    en["StatCategories"]["BSFlak"], pt["StatCategories"]["BSFlak"] = "Airburst Flak", "Flak de explosão aérea"

    for l in D.LIMIT_DEFS:
        sk, pk = l["string_keys"]
        en["CategoryNouns"][sk.split("/", 1)[1]], en["CategoryNouns"][pk.split("/", 1)[1]] = l["nouns_en"]
        pt["CategoryNouns"][sk.split("/", 1)[1]], pt["CategoryNouns"][pk.split("/", 1)[1]] = l["nouns_ptbr"]

    en["Stats"]["BSShotsPerMagFmt"] = "<white>Shots per Load:</white> <good>{0:0}</good>"
    pt["Stats"]["BSShotsPerMagFmt"] = "<white>Disparos por carga:</white> <good>{0:0}</good>"
    en["Stats"]["BSFactoryOutputFmt"] = "<white>Production:</white> <good>{0:0.##}</good><gray>/sec</gray>"
    pt["Stats"]["BSFactoryOutputFmt"] = "<white>Produção:</white> <good>{0:0.##}</good><gray>/s</gray>"
    en["Stats"]["BSShotDamageVsLasersFmt"] = ("<white>Dmg vs Lasers:</white> <good>{0:n0}</good><gray>/shot (</gray>"
                                              "<good>{1:n0}</good><gray>/sec)</gray>")
    pt["Stats"]["BSShotDamageVsLasersFmt"] = ("<white>Dano x lasers:</white> <good>{0:n0}</good><gray>/disparo (</gray>"
                                              "<good>{1:n0}</good><gray>/s)</gray>")
    for res in [r for f in D.SPEC["factories"] for rc in f["recipes"] for r in (rc.get("inputs_per_cycle") or {})]:
        sid = use_stat(res)
        own = D.RES_BY_ID.get(res)
        l_en, l_pt = ((f"{own['name_en']} Use", f"Uso de {own['name_pt'].lower()}") if own
                      else VANILLA_RES.get(res, (f"{res} Use", f"Uso de {res}")))
        en["Stats"][sid + "Fmt"] = (f"<white>{l_en}:</white> <good>{{0:0.###}}</good><gray>/ammo (</gray>"
                                    f"<good>{{1:0.###}}</good><gray>/sec)</gray>")
        pt["Stats"][sid + "Fmt"] = (f"<white>{l_pt}:</white> <good>{{0:0.###}}</good><gray>/munição (</gray>"
                                    f"<good>{{1:0.###}}</good><gray>/s)</gray>")

    ten, tpt = tech_strings(D)
    en["BSTechs"].update(ten)
    pt["BSTechs"].update(tpt)
    return en, pt
