#!/usr/bin/env python3
"""Gera o mod Bullet Strike 2.0 (rules + sprites + textos) a partir de tools/spec/SPEC_2.0.json (via tools/bs_data.py).

Uso (na raiz do repositorio):
    python3 tools/build_mod.py                         # variante fita em BulletStrike/
    python3 tools/build_mod.py --variante semfita      # reserva sem a Fita em testes/BulletStrike_SemFita/
    python3 tools/build_mod.py --no-art                # so os .rules e textos (mais rapido)
    python3 tools/build_mod.py --vanilla <Data do jogo ou clone>   # confere caminhos ./Data/...
    python3 tools/build_mod.py --out <pasta>           # build privado (tambem env BS_OUT)
    python3 tools/build_mod.py --switch logistics.transport=tripulacao --switch guns.ac_cost=3x
    python3 tools/build_mod.py --logistica teleporte|rede|gemea|tripulacao --acoplamento auto|on|off
                               --paiol-seletor botao|nenhum --contador --perfil sw

Switches (SPEC.switches): CLI > env (BS_SWITCHES='a.b=v,c.d=w', BS_LOGISTICA, BS_RAIL, ...) >
tools/spec/bullet_strike_switches.json > padrao do spec (ver tools/bs_data.py switch()).

REGISTRO DE MODULOS (WP01): cada subsistema 2.0 e um modulo que so participa com API >= 2 (atributo API no topo):
  CONTENT = bsgen.guns, bsgen.ciws, bsgen.factory, bsgen.logistics, bsgen.intake, bsgen.belt_net (reserva, WP15),
            bsgen.pem, bsgen.railgun, bs_data_missiles, bsgen.launchers, bsgen.missile_shots, bsgen.fx_tex
            (import por common.content_module: nunca desligado pelo BS_FX_EXT)
  FX      = bsgen.fxkit, bsgen.caliber_fx, bsgen.missile_fx, bsgen.pem_fx, bsgen.rail_fx (BS_FX_EXT=0 desliga)
Lancadores so entram quando bs_data_missiles, bsgen.launchers E bsgen.missile_shots tem API >= 2.
Ganchos (todos opcionais), NESTA ORDEM:
  resources(DATA) -> shots(DATA) -> annotate(DATA) (so FX) -> write(out, header) -> build_shot (um por tiro de
  DATA.SHOTS, despachado por kind/owner: SPEC.generator_mapping.shot_dispatch) -> parts(out, DATA, ctx) ->
  copy_art(out) (so FX) -> toggles() / strings(DATA) / part_stats() -> techs (nucleo) -> mod_actions() ->
  selfcheck(mod_dir, SPEC)
Declaracoes no topo do modulo: API = 2; SHOT_KINDS = ('<kind>', ...) + build_shot(out, s, header);
VARIANTS = {'chave.switch': (valores implementados, ...)} (tira da lista de variantes adiadas do bs_data).

O resultado e o mod pronto: copie a pasta para %USERPROFILE%\\Saved Games\\Cosmoteer\\<SteamID>\\Mods\\
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.normpath(os.path.join(HERE, ".."))

from rules_dsl import render  # noqa: E402

HEADER = "Bullet Strike - arquivo gerado por tools/build_mod.py (nao edite a mao; edite tools/spec/SPEC_2.0.json)."

CONTENT = ["bsgen.guns", "bsgen.ciws", "bsgen.factory", "bsgen.logistics", "bsgen.intake", "bsgen.belt_net",
           "bsgen.pem", "bsgen.railgun", "bs_data_missiles", "bsgen.launchers", "bsgen.missile_shots", "bsgen.fx_tex"]
FX = ["bsgen.fxkit", "bsgen.caliber_fx", "bsgen.missile_fx", "bsgen.pem_fx", "bsgen.rail_fx"]
LAUNCHER_SET = ("bs_data_missiles", "bsgen.launchers", "bsgen.missile_shots")
# kinds construidos pelas funcoes de bsgen/shots.py (WP02); os outros vem do SHOT_KINDS dos modulos
NATIVE_KINDS = ("kinetic", "explosive", "flak", "flak_oc", "cloud")


class Out:
    def __init__(self, root):
        self.root = root
        self.files = {}

    def text(self, rel, content):
        self.files[rel] = content
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)

    def image(self, rel, img):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path, optimize=True)

    def exists(self, rel):
        return rel in self.files or os.path.exists(os.path.join(self.root, rel))


def relpath(from_dir, to_file):
    return os.path.relpath(to_file, from_dir).replace(os.sep, "/")


# ----------------------------------------------------------------------------- registro dos modulos
class Registry:
    """Modulos de conteudo e de efeitos ativos (API >= 2), na ordem de CONTENT e depois FX."""

    def __init__(self, D, C):
        self.D = D
        self.active = []        # [(nome, modulo, 'content'|'fx')]
        self.skipped = []       # [(nome, motivo)]
        apis = {}
        for name in CONTENT:
            mod = C.content_module(name, min_api=0)
            if mod is None:
                self.skipped.append((name, "ausente"))
                continue
            api = int(getattr(mod, "API", 0) or 0)
            if api < 2:
                self.skipped.append((name, f"API {api} < 2 (ainda 1.x)"))
                continue
            apis[name] = mod
        missing = [n for n in LAUNCHER_SET if n not in apis]
        if missing and any(n in apis for n in LAUNCHER_SET):
            for n in LAUNCHER_SET:
                if n in apis:
                    del apis[n]
                    self.skipped.append((n, f"lancadores precisam de {', '.join(LAUNCHER_SET)} (falta {missing})"))
        for name in CONTENT:
            if name in apis:
                self.active.append((name, apis[name], "content"))
        if os.environ.get("BS_FX_EXT", "1") == "0":
            self.skipped += [(n, "BS_FX_EXT=0") for n in FX]
        else:
            for name in FX:
                mod = C.content_module(name, min_api=0)
                if mod is None:
                    self.skipped.append((name, "ausente"))
                    continue
                api = int(getattr(mod, "API", 0) or 0)
                if api < 2:
                    self.skipped.append((name, f"API {api} < 2 (ainda 1.x)"))
                    continue
                self.active.append((name, mod, "fx"))
        self.names = {n for n, _m, _k in self.active}
        # tiros: um modulo por kind (dois -> erro antes de escrever qualquer arquivo)
        self.shot_kinds = {}
        for name, mod, _k in self.active:
            for kind in getattr(mod, "SHOT_KINDS", ()) or ():
                if kind in NATIVE_KINDS:
                    raise SystemExit(f"ERRO: {name} declara o kind nativo '{kind}' em SHOT_KINDS")
                if kind in self.shot_kinds:
                    raise SystemExit(f"ERRO: kind de tiro '{kind}' declarado por {self.shot_kinds[kind][0]} e {name}")
                if not callable(getattr(mod, "build_shot", None)):
                    raise SystemExit(f"ERRO: {name} declara SHOT_KINDS sem build_shot(out, s, header)")
                self.shot_kinds[kind] = (name, mod)
            if getattr(mod, "VARIANTS", None):
                D.implement_variants(mod.VARIANTS, name)

    def mods(self, which=("content", "fx")):
        return [(n, m) for n, m, k in self.active if k in which]

    def call(self, hook, *a, which=("content", "fx")):
        """[(nome, resultado)] de mod.hook(*a) nos modulos ativos que tem o gancho."""
        res = []
        for name, mod in self.mods(which):
            f = getattr(mod, hook, None)
            if callable(f):
                res.append((name, f(*a)))
        return res


# ----------------------------------------------------------------------------- tiros
def native_shot(out, s):
    """kinds nativos (bsgen/shots.py, WP02), como o build_mod 1.x; o ramo 'missile' saiu (bsgen.missile_shots)."""
    from bsgen import shots
    sid = s["file"]
    rel = f"shots/{s.get('dir') or sid}/{sid}.rules"
    kind = s["kind"]
    if kind == "kinetic":
        top = shots.build_kinetic(s)
    elif kind == "explosive":
        top = shots.build_explosive(s)
    elif kind == "flak":
        top = shots.build_flak_beam(s)
    elif kind == "flak_oc":
        top = {"BASE": f"&<{s['base']}.rules>", "CLOUD": f"&<{s['cloud']}.rules>",
               "Beam : BASE": {"STAT_CLOUD_RADIUS": s["cloud_radius"], "STAT_CLOUD_POOL": s["cloud_pool"],
                               "STAT_CLOUD_LIFETIME": s["cloud_lifetime"],
                               "HitNothing : ^/0/HitNothing": {
                                   "HitEffects : ^/0/HitEffects": [{"Type": "SpawnBullets", "Bullet": "&~/CLOUD",
                                                                    "Count": 1}]},
                               "HitShield": "&HitNothing", "HitOperational": "&HitNothing",
                               "HitStructural": "&HitNothing"}}
    elif kind == "cloud":
        top = shots.build_flak_cloud(s)
    else:
        raise ValueError(kind)
    out.text(rel, render(top, HEADER + f"\nProjetil: {s.get('title', sid)}"))
    return rel


def shot_file(out, s, reg, D):
    """Contrato SPEC.generator_mapping.shot_dispatch: owner sem API 2 -> pulado com aviso (nunca ValueError);
    kind nativo -> bsgen/shots.py; outro kind -> build_shot do modulo que o declarou em SHOT_KINDS."""
    owner = s.get("owner")
    if owner not in reg.names:
        D.warn(f"tiro {s['file']} pulado: {owner} ausente")
        return None
    kind = s["kind"]
    if kind in NATIVE_KINDS:
        return native_shot(out, s)
    hit = reg.shot_kinds.get(kind)
    if hit is None:
        raise ValueError(f"tiro {s['file']}: kind '{kind}' sem modulo (SHOT_KINDS declarados: "
                         f"{sorted(reg.shot_kinds) or 'nenhum'})")
    rel = hit[1].build_shot(out, s, HEADER)
    if rel is None:
        raise ValueError(f"tiro {s['file']}: kind '{kind}' recusado por {hit[0]} (declarantes: {hit[0]})")
    return rel


# ----------------------------------------------------------------------------- descricao do menu Mods
def _join(items, lang):
    """'a, b e c' / 'a, b and c'."""
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + (" e " if lang == "pt" else " and ") + items[-1]


# tipos de peca (PART_INFO kind) na ordem da descricao: (kind, pt, en)
_DESC_KINDS = (("gun", "canhões", "cannons"), ("defense", "defesas", "defenses"), ("pem", "linha PEM", "EMP line"),
               ("rail", "railgun Tupã", "Tupã railgun"), ("launcher", "lança-mísseis", "missile launchers"),
               ("factory", "fábricas", "factories"), ("paiol", "paióis", "magazines"),
               ("fita", "Fita de Alimentação", "Ammo Feed Link"))


def _description_bodies(D, ctx):
    """Corpo da Description (pt, en) tirado do PROPRIO build: pecas registradas (por tipo), recursos escritos,
    transporte e switches (econ.factory_adjacency, logistics.reserva_tripulacao, logistics.acoplamento, rail.enabled).
    Nada que o build nao tenha entra no texto."""
    from bsgen import common as C
    w = ctx["written_parts"]
    n = len(w)
    kinds = {(D.PART_INFO.get(p) or {}).get("kind") for p in w}
    if not D.RAIL_ENABLED:
        kinds.discard("rail")
    cats = [(pt, en) for k, pt, en in _DESC_KINDS if k in kinds]
    if cats:
        parts_pt = (f"{n} {'peça' if n == 1 else 'peças'} neste build: "
                    f"{_join([c[0] for c in cats], 'pt')}.")
        parts_en = f"{n} {'part' if n == 1 else 'parts'} in this build: {_join([c[1] for c in cats], 'en')}."
    else:
        parts_pt, parts_en = "Nenhuma peça neste build.", "No parts in this build."
    # municoes: so os recursos que este build escreve
    rids = {r["id"] for r in D.RESOURCES}
    fams = {r["family"] for r in D.RESOURCES}
    labels = [a["label"] for a in D.SPEC["ammo_types"] if a.get("resource") in rids]
    am_pt, am_en = [], []
    if labels:
        am_pt.append(_join(labels, "pt"))
        am_en.append(_join(labels, "en"))
    cells = [(pt, en) for rid, pt, en in ((f"{D.AUTHOR}.bs_plasma_cell", "plasma", "plasma"),
                                          (f"{D.AUTHOR}.bs_cell_emp", "PEM", "EMP")) if rid in rids]
    if cells:
        am_pt.append(f"{'células' if len(cells) > 1 else 'célula'} de {_join([c[0] for c in cells], 'pt')}")
        am_en.append(f"{_join([c[1] for c in cells], 'en')} {'cells' if len(cells) > 1 else 'cell'}")
    if "misseis" in fams:
        am_pt.append("cargas de míssil")
        am_en.append("missile charges")
    if "projeteis" in fams and D.RAIL_ENABLED:
        am_pt.append("projétil do railgun")
        am_en.append("railgun slug")
    ammo_pt = f"Munições: {'; '.join(am_pt)}." if am_pt else ""
    ammo_en = f"Ammo: {'; '.join(am_en)}." if am_en else ""
    # logistica: transporte e switches
    adj_on = D.switch("econ.factory_adjacency") != "off"
    t = D.transport()
    fac_pt = ("fábricas (vizinhança do jogo base ligada)" if adj_on else "fábricas (sem o bônus de vizinhança do jogo base)")
    fac_en = "factories (base-game adjacency bonus on)" if adj_on else "factories (no base-game adjacency bonus)"
    lg_pt, lg_en = [], []
    if "factory" in kinds:
        lg_pt.append(fac_pt)
        lg_en.append(fac_en)
    if "paiol" in kinds:
        lg_pt.append("paióis")
        lg_en.append("magazines")
    aco = D.switch("logistics.acoplamento")
    acoplado = "paiol" in kinds and (aco == "on" or (aco == "auto" and t == "tripulacao"))
    if t == "teleporte":
        if "fita" in kinds:
            lg_pt.append("a Fita de Alimentação")
            lg_en.append("the Ammo Feed Link")
            how_pt = ("grude a Fita do lado de uma fábrica, paiol ou arma e a munição passa sozinha entre elas "
                      "(teletransporte)")
            how_en = "stick it next to a factory, magazine or gun and ammo moves between them by itself (teleport)"
            if C.reserva_sem_fita():
                how_pt += "; a tripulação só abastece arma sem Fita"
                how_en += "; the crew only resupply guns without a Link"
            else:
                how_pt += "; abaixo da metade a tripulação também abastece"
                how_en += "; below half the crew also resupplies"
        else:
            how_pt, how_en = "a tripulação leva a munição até as armas", "the crew carry ammo to the guns"
    else:
        how_pt, how_en = "a tripulação leva a munição até as armas", "the crew carry ammo to the guns"
    if acoplado:
        how_pt += " (paióis acoplados alimentam a arma vizinha)"
        how_en += " (docked magazines feed the adjacent gun)"
    if lg_pt:
        logi_pt = f"Logística: {_join(lg_pt, 'pt')}; {how_pt}."
        logi_en = f"Logistics: {_join(lg_en, 'en')}; {how_en}."
    else:
        logi_pt = f"Logística: {how_pt}."
        logi_en = f"Logistics: {how_en}."
    pt_lines = [parts_pt, ammo_pt, logi_pt, "Compatível com Star Wars: A Cosmos Divided."]
    en_lines = [parts_en, ammo_en, logi_en, "Compatible with Star Wars: A Cosmos Divided."]
    pt = ("Armas de convés operadas pela tripulação que usam MUNIÇÃO em vez de energia.\n\n"
          + "\n".join(f"- {x}" for x in pt_lines if x))
    en = ("Deck-mounted, crew-operated weapons that run on AMMUNITION instead of power.\n\n"
          + "\n".join(f"- {x}" for x in en_lines if x))
    return pt, en


# ----------------------------------------------------------------------------- build
def _is_mod_dir(root):
    """Pasta que o gerador pode limpar: so a que tem mod.rules no primeiro nivel (CONTRATOS B1)."""
    return os.path.isfile(os.path.join(root, "mod.rules"))


def _merge(base, extra):
    for g, entries in (extra or {}).items():
        base.setdefault(g, {}).update(entries or {})


def build(args, D):
    from bsgen import common as C
    from bsgen import resources, infra, trails, plasma_fx, placeholder_icons
    import art3d as A3
    import bs_strings

    root = os.path.abspath(args.out)
    if os.path.isdir(root) and not args.keep and os.listdir(root) and not _is_mod_dir(root):
        sys.exit(f"ERRO: {root} nao esta vazia e nao tem mod.rules; nao apago uma pasta que nao e do mod "
                 "(use uma pasta vazia ou nova em --out / BS_OUT)")
    if os.path.isdir(root) and not args.keep:
        if args.no_art:
            for dp, _dn, fn in os.walk(root):
                for f in fn:
                    if f.endswith(".rules"):
                        os.remove(os.path.join(dp, f))
        else:
            for name in os.listdir(root):
                p = os.path.join(root, name)
                if name in (".workshop",):
                    continue
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    out = Out(root)
    art = None
    if not args.no_art:
        import make_art as art  # noqa: E402

    reg = Registry(D, C)
    print(f"variante {D.VARIANT} ({D.MOD_ID}); logistics.transport = {D.transport()}")
    for name, _m, kind in reg.active:
        print(f"  modulo ativo ({kind}): {name}")
    for name, why in reg.skipped:
        print(f"  modulo pulado: {name} ({why})")
    for t in D.TRANSFORMS:
        print(f"  transformacao {t}")

    ctx = {"D": D, "out": out, "art": art, "header": HEADER, "registry": reg, "relpath": relpath,
           "written_parts": set(), "part_files": {}, "part_order": [], "shot_rel": {}, "status_paths": [],
           "stat_ids": [], "transport": D.transport(), "warn": D.warn, "placeholders": D.PLACEHOLDERS}

    def add_part(pid, rel=None):
        """Registra uma peca escrita (ID e, se fora do padrao parts/<id>/<id>.rules, o arquivo)."""
        ctx["written_parts"].add(pid)
        if rel:
            ctx["part_files"][pid] = rel
        if pid not in ctx["part_order"]:
            ctx["part_order"].append(pid)
    ctx["add_part"] = add_part

    # 1) recursos (os modulos podem mexer em DATA.RESOURCES antes)
    reg.call("resources", D)
    res_paths = []
    for r in D.RESOURCES:
        rel = f"resources/{r['dir']}/{r['dir']}.rules"
        out.text(rel, render(resources.build_resource(r), HEADER + f"\nRecurso: {r['name_en']}"))
        res_paths.append(rel)
        if art:
            art.resource_art(out, r)
        elif r.get("art3d"):
            A3.copy_files(out.root, f"resources/{r['dir']}", r["art3d_dir"], r["art3d"])

    # 2) tiros dos modulos e anotacao visual (FX)
    reg.call("shots", D)
    reg.call("annotate", D, which=("fx",))

    # 3) arquivos proprios: rastros e plasma (sempre: Boitata/Curupira dependem) + gancho write
    for rel, text in trails.all_trails():
        out.text(rel, "\n".join(f"// {ln}" for ln in (HEADER + "\nRastro de particulas (copia vanilla, ver bsgen/trails.py)").split("\n"))
                 + "\n\n" + text)
    plasma_fx.write(out, HEADER + "\nEfeito de plasma (ver bsgen/plasma_fx.py e bsgen/plasma_tex.py)")
    reg.call("write", out, HEADER)

    # 4) tiros
    for s in D.SHOTS:
        rel = shot_file(out, s, reg, D)
        if rel:
            ctx["shot_rel"][s["file"]] = rel

    # 5) pecas
    reg.call("parts", out, D, ctx, which=("content",))
    reg.call("copy_art", out, which=("fx",))
    part_paths = []
    for pid in ctx["part_order"] + sorted(ctx["written_parts"] - set(ctx["part_order"])):
        short = pid.split(".", 1)[1]
        rel = ctx["part_files"].get(pid) or f"parts/{short}/{short}.rules"
        if rel not in out.files:
            sys.exit(f"ERRO: peca {pid} registrada em ctx['written_parts'] sem o arquivo {rel}")
        part_paths.append(rel)

    # 6) seletores, textos e estatisticas
    toggles = infra.core_toggles(D)
    for name, t in reg.call("toggles", which=("content",)):
        for item in (t or []):
            if isinstance(item, dict):
                toggles.append((item.get("ToggleID"), item))
            else:
                toggles.append(item)
    ids = [t[0] for t in toggles]
    if len(ids) != len(set(ids)):
        sys.exit(f"ERRO: PartToggle duplicada: {ids}")
    out.text("gui/bs_part_toggles.rules", infra.part_toggles(toggles))
    stat_ids = bs_strings.input_stat_ids(D)
    for _n, ids2 in reg.call("part_stats", which=("content",)):
        stat_ids += [i for i in (ids2 or []) if i not in stat_ids]
    out.text("gui/bs_part_stats.rules", infra.part_stats(stat_ids))
    en, pt = bs_strings.strings(ctx["written_parts"])
    for name, res in reg.call("strings", D):
        if res:
            _merge(en, res[0])
            _merge(pt, res[1])

    # 7) techs (depois das pecas: so o que foi escrito)
    reserve = D.transport() in ("rede", "gemea")
    car = D.career_techs(ctx["written_parts"], reserve=reserve)
    bb = D.buildbattle_techs(ctx["written_parts"])
    wl = D.bb_whitelist(ctx["written_parts"], reserve=reserve)
    car_txt, bb_txt = infra.techs(car, bb, wl)
    out.text("techs/bs_techs_career.rules", car_txt)
    out.text("techs/bs_techs_buildbattle.rules", bb_txt)
    out.text("strings/en.rules", infra.strings_file(en, "\n<s16><gray>Mod: Bullet Strike</gray></s16>"))
    out.text("strings/pt-br.rules", infra.strings_file(pt, "\n<s16><gray>Mod: Bullet Strike</gray></s16>"))

    # 8) mod.rules (acoes dos modulos: Overrides de buffs da fita, do railgun, ...)
    actions = []
    for _n, acts in reg.call("mod_actions", which=("content", "fx")):
        actions += list(acts or [])
    body_pt, body_en = _description_bodies(D, ctx)
    D.MOD["description"] = infra.mod_description(D.SPEC, D.PROFILE, body_pt, body_en)
    out.text("mod.rules", infra.mod_rules(D.MOD, part_paths, res_paths, D.VERSION, D.LIMITS, ctx["status_paths"],
                                          actions_extra=actions))
    if art:
        art.misc_art(out)
    made = placeholder_icons.ensure(out, D.SPEC, D.ART2)
    for rel in made:
        D.PLACEHOLDERS.append(f"icone provisorio {rel}")

    check_vanilla_paths(out, args.vanilla)

    # 9) conferencias dos modulos
    bad = 0
    for name, res in reg.call("selfcheck", root, D.SPEC):
        probs = [p for p in (res or []) if p]
        if probs:
            bad += len(probs)
            for p in probs:
                print(f"ERRO selfcheck {name}: {p}")
        else:
            print(f"selfcheck {name}: OK")
    for p in D.selfcheck_data():
        bad += 1
        print(f"ERRO selfcheck bs_data: {p}")
    if bad:
        sys.exit(1)
    print(f"pecas escritas: {len(part_paths)}; techs: {len(car)} carreira, {len(bb)} build battle, "
          f"{len(wl)} na lista branca")
    if D.PLACEHOLDERS:
        print(f"placeholders ({len(D.PLACEHOLDERS)}): " + "; ".join(D.PLACEHOLDERS))
    if D.WARNINGS:
        print(f"avisos: {len(D.WARNINGS)} (impressos acima com '(aviso)')")
    print(f"OK: {len(out.files)} arquivos .rules em {root}")


def vanilla_listing(vanilla):
    if not vanilla:
        return None
    if os.path.isdir(os.path.join(vanilla, ".git")):
        try:
            res = subprocess.run(["git", "-C", vanilla, "-c", "gc.auto=0", "ls-tree", "-r", "--name-only",
                                  "origin/main-unstable"], capture_output=True, text=True, check=True, timeout=120)
            return set(res.stdout.split("\n"))
        except Exception:  # noqa: BLE001
            pass
    files = set()
    for dp, _dn, fn in os.walk(vanilla):
        for f in fn:
            files.add(os.path.relpath(os.path.join(dp, f), vanilla).replace(os.sep, "/"))
    return files


def check_vanilla_paths(out, vanilla):
    listing = vanilla_listing(vanilla)
    if listing is None:
        print("(aviso) sem --vanilla: caminhos ./Data/... nao foram conferidos")
        return
    bad = []
    pat = re.compile(r"\./Data/([^\">\s]+)")
    for rel, text in out.files.items():
        for m in pat.finditer(text):
            p = m.group(1)
            if p not in listing:
                bad.append((rel, p))
    if bad:
        for rel, p in bad:
            print(f"ERRO: {rel}: ./Data/{p} nao existe no jogo")
        sys.exit(1)
    print("Caminhos ./Data/... conferidos: todos existem.")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Gera o mod Bullet Strike 2.0.")
    ap.add_argument("--no-art", action="store_true")
    ap.add_argument("--keep", action="store_true", help="nao apaga a pasta de saida antes")
    ap.add_argument("--vanilla", default=os.environ.get("COSMOTEER_DATA"))
    ap.add_argument("--out", default=os.environ.get("BS_OUT"),
                    help="pasta de saida (padrao: a da variante em SPEC.build_2_0.variants; env BS_OUT)")
    ap.add_argument("--variante", default=os.environ.get("BS_VARIANTE") or "fita",
                    help="fita (BulletStrike/) | semfita (testes/BulletStrike_SemFita/, forca transport tripulacao)")
    ap.add_argument("--switch", action="append", default=[], metavar="CHAVE=VALOR",
                    help="qualquer switch de SPEC.switches (repetivel)")
    ap.add_argument("--logistica", help="teleporte | rede | gemea | tripulacao (logistics.transport)")
    ap.add_argument("--logistics", help=argparse.SUPPRESS)   # apelido obsoleto
    ap.add_argument("--acoplamento", help="auto | on | off (logistics.acoplamento)")
    ap.add_argument("--paiol-seletor", dest="paiol_seletor", help="botao | nenhum (logistics.paiol_seletor)")
    ap.add_argument("--contador", action="store_true", help="logistics.paiol_contador = true")
    ap.add_argument("--perfil", help="sw | vanilla (balance.perfil; vanilla nao existe na 2.0)")
    return ap.parse_args(argv)


def cli_switches(args):
    sw = {}
    if args.logistics and not args.logistica:
        print("(aviso) --logistics e obsoleto: use --logistica", file=sys.stderr)
        sw["logistics.transport"] = args.logistics
    if args.logistica:
        sw["logistics.transport"] = args.logistica
    if args.acoplamento:
        sw["logistics.acoplamento"] = args.acoplamento
    if args.paiol_seletor:
        sw["logistics.paiol_seletor"] = args.paiol_seletor
    if args.contador:
        sw["logistics.paiol_contador"] = "true"
    if args.perfil:
        sw["balance.perfil"] = args.perfil
    for item in args.switch:
        k, sep, v = item.partition("=")
        if not sep:
            sys.exit(f"ERRO: --switch {item!r}: use chave=valor")
        sw[k.strip()] = v.strip()
    return sw


def main(argv=None):
    args = parse_args(argv)
    # a CLI e a variante chegam ao bs_data antes do import (ele monta os dados na carga)
    os.environ["BS__CLI_SWITCHES"] = json.dumps(cli_switches(args))
    os.environ["BS__VARIANTE"] = args.variante
    import bs_data as D
    if not args.out:
        args.out = os.path.join(REPO, D.PROFILE["out"].rstrip("/"))
    build(args, D)


if __name__ == "__main__":
    main()
