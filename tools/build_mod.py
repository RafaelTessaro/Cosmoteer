#!/usr/bin/env python3
"""Gera o mod Bullet Strike inteiro (rules + sprites + textos) a partir de tools/bs_data.py.

Uso (na raiz do repositorio):
    python3 tools/build_mod.py                # gera tudo em BulletStrike/
    python3 tools/build_mod.py --no-art       # so os .rules e textos (mais rapido)
    python3 tools/build_mod.py --vanilla <pasta Data do jogo ou clone>  # confere caminhos ./Data/...
    python3 tools/build_mod.py --out <pasta>  # gera em outra pasta (build privado; tambem env BS_OUT)

Modulos opcionais de efeitos (bsgen/fxkit.py, bsgen/caliber_fx.py, bsgen/missile_fx.py): entram pelos
"seams" de bs_data.py, bsgen/shots.py e deste arquivo; se o modulo nao existir, o build segue igual.
BS_FX_EXT=0 desliga todos (visual antigo).

O resultado (pasta BulletStrike/) e o mod pronto: copie para
    %USERPROFILE%\\Saved Games\\Cosmoteer\\<SteamID>\\Mods\\BulletStrike
"""

import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rules_dsl import render  # noqa: E402
from bsgen import common as C  # noqa: E402
from bsgen import guns, ciws, shots, factory, resources, infra, launchers, trails, plasma_fx  # noqa: E402
import bs_data as DATA  # noqa: E402
import art3d as A3  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "BulletStrike"))
HEADER = "Bullet Strike - arquivo gerado por tools/build_mod.py (nao edite a mao; edite tools/bs_data.py)."


# modulos opcionais de efeitos (CONTRATOS secao 1): ausente = silencioso; BS_FX_EXT=0 desliga todos.
# Um ModuleNotFoundError de OUTRO modulo (import quebrado dentro do modulo opcional) continua estourando.
def _opt(name):
    if os.environ.get("BS_FX_EXT", "1") == "0":
        return None
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name != name:
            raise
        return None


def _call(mod, fn, *a, **k):
    f = getattr(mod, fn, None) if mod is not None else None
    return f(*a, **k) if f is not None else None


FXK = _opt("bsgen.fxkit")
CFX = _opt("bsgen.caliber_fx")
MFX = _opt("bsgen.missile_fx")


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


def relpath(from_dir, to_file):
    return os.path.relpath(to_file, from_dir).replace(os.sep, "/")


# ----------------------------------------------------------------------------- shots
def shot_file(out, s):
    sid = s["file"]
    rel = f"shots/{sid}/{sid}.rules"
    kind = s["kind"]
    if kind == "kinetic":
        top = shots.build_kinetic(s)
    elif kind == "explosive":
        top = shots.build_explosive(s)
    elif kind == "flak":
        top = shots.build_flak_beam(s)
    elif kind == "flak_oc":
        base_rel = f"{s['base']}.rules"
        cloud_rel = f"{s['cloud']}.rules"
        top = {"BASE": f"&<{base_rel}>", "CLOUD": f"&<{cloud_rel}>",
               "Beam : BASE": {"STAT_CLOUD_RADIUS": s["cloud_radius"], "STAT_CLOUD_POOL": s["cloud_pool"],
                               "STAT_CLOUD_LIFETIME": s["cloud_lifetime"],
                               "HitNothing : ^/0/HitNothing": {
                                   "HitEffects : ^/0/HitEffects": [{"Type": "SpawnBullets", "Bullet": "&~/CLOUD",
                                                                    "Count": 1}]},
                               "HitShield": "&HitNothing", "HitOperational": "&HitNothing",
                               "HitStructural": "&HitNothing"}}
        rel = f"shots/{s['dir']}/{sid}.rules"
    elif kind == "cloud":
        top = shots.build_flak_cloud(s)
        rel = f"shots/{s['dir']}/{sid}.rules"
    elif kind == "missile":
        # missil de conves (bsgen/shots.py build_missile). Os filhos (submunicao, carga, ogiva, isca) vao na
        # mesma pasta e o pai os referencia pelo nome relativo (como o flak_oc); extras = variantes isoladas
        # que nenhum lancador dispara (ex.: Carrapato com Repeating, so-SW, limpet_repeating=isolated_file).
        for c in s.get("children", []):
            out.text(f"shots/{s['dir']}/{c['file']}.rules",
                     render(shots.build_missile_part(c), HEADER + f"\nProjetil: {c['title']}"))
        for x in s.get("extras", []):
            out.text(f"shots/{s['dir']}/{x['file']}.rules",
                     render(shots.build_missile(x), HEADER + f"\nProjetil: {x['title']}"))
        top = shots.build_missile(s)
        rel = f"shots/{s['dir']}/{sid}.rules"
    else:
        raise ValueError(kind)
    if kind in ("flak",):
        rel = f"shots/{s['dir']}/{sid}.rules"
    out.text(rel, render(top, HEADER + f"\nProjetil: {s.get('title', sid)}"))
    return rel


# ----------------------------------------------------------------------------- main
def _is_mod_dir(root):
    """Pasta que o gerador pode limpar: tem mod.rules, ou e um build nosso interrompido antes do mod.rules
    (algum .rules comeca com o cabecalho HEADER). Protege --out apontado para uma pasta qualquer."""
    if os.path.isfile(os.path.join(root, "mod.rules")):
        return True
    mark = f"// {HEADER}"
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if f.endswith(".rules"):
                try:
                    with open(os.path.join(dp, f), encoding="utf-8") as fh:
                        if fh.readline().rstrip("\n") == mark:
                            return True
                except (OSError, UnicodeDecodeError):
                    pass
    return False


def build(args):
    root = os.path.abspath(getattr(args, "out", None) or os.environ.get("BS_OUT") or ROOT)
    if os.path.isdir(root) and not args.keep and os.listdir(root) and not _is_mod_dir(root):
        sys.exit(f"ERRO: {root} nao esta vazia e nao tem mod.rules; nao apago uma pasta que nao e do mod "
                 "(use uma pasta vazia ou nova em --out / BS_OUT)")
    if os.path.isdir(root) and not args.keep:
        if args.no_art:
            # sem arte: apaga so os .rules (as imagens ja geradas continuam valendo)
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

    # recursos
    res_paths = []
    own_stack = {}
    for r in DATA.RESOURCES:
        rel = f"resources/{r['dir']}/{r['dir']}.rules"
        out.text(rel, render(resources.build_resource(r), HEADER + f"\nRecurso: {r['name_en']}"))
        res_paths.append(rel)
        own_stack[r["id"]] = r["max_stack"]
        if art:
            art.resource_art(out, r)
        elif r.get("art3d"):
            A3.copy_files(out.root, f"resources/{r['dir']}", r["dir"], r["art3d"])

    # rastros de particulas proprios (bucket de cima, cor por municao: bsgen/trails.py)
    for rel, text in trails.all_trails():
        out.text(rel, "\n".join(f"// {ln}" for ln in (HEADER + "\nRastro de particulas (copia vanilla, ver bsgen/trails.py)").split("\n"))
                 + "\n\n" + text)
    # efeitos de plasma da Boitata e do Curupira (texturas PIL + particulas; bsgen/plasma_fx.py)
    plasma_fx.write(out, HEADER + "\nEfeito de plasma (ver bsgen/plasma_fx.py e bsgen/plasma_tex.py)")
    # seam B2: arquivos dos modulos opcionais de efeitos (particulas/texturas proprias; ausente = nada)
    for m, note in ((FXK, "Efeito compartilhado (bsgen/fxkit.py)"), (CFX, "Efeito por calibre (bsgen/caliber_fx.py)"),
                    (MFX, "Efeito de missil (bsgen/missile_fx.py)")):
        _call(m, "write", out, HEADER + "\n" + note)
    # projeteis
    shot_rel = {}
    for s in DATA.SHOTS:
        shot_rel[s["file"]] = shot_file(out, s)
    for s in DATA.MISSILES:
        shot_rel[s["file"]] = shot_file(out, s)
    # status proprios dos misseis (so com limpet_anchor=F2, depois do teste T14b)
    status_paths = []
    for st in DATA.MISSILE_STATUSES:
        rel = f"statuses/{st['dir']}/{st['dir']}.rules"
        out.text(rel, render(shots.build_limpet_status(st), HEADER + f"\nStatus: {st['title']}"))
        status_paths.append(rel)

    part_paths = []
    # armas
    for g in DATA.GUNS:
        pdir = f"parts/{g['short']}"
        sp = {}
        for m in g["modes"]:
            sp[(m["mode"], False)] = relpath(pdir, os.path.join(shot_rel[m["shot"]]))
            if g.get("oc"):
                sp[(m["mode"], True)] = relpath(pdir, os.path.join(shot_rel[m["shot_oc"]]))
        top, info = guns.build_gun(g, sp)
        rel = f"{pdir}/{g['short']}.rules"
        out.text(rel, render(top, HEADER + f"\nArma: {g['name_en']} / {g['name_pt']}"))
        part_paths.append(rel)
        if art:
            art.gun_art(out, pdir, g, info)
        elif g.get("art3d"):
            A3.copy_files(out.root, pdir, g["short"], g["art3d"])
    # defesas
    for cdef in DATA.DEFENSES:
        pdir = f"parts/{cdef['short']}"
        beam = relpath(pdir, shot_rel[cdef["beam"]])
        beam_oc = relpath(pdir, shot_rel[cdef["beam_oc"]]) if cdef.get("beam_oc") else None
        top, info = ciws.build_ciws(cdef, beam, beam_oc)
        rel = f"{pdir}/{cdef['short']}.rules"
        out.text(rel, render(top, HEADER + f"\nDefesa: {cdef['name_en']} / {cdef['name_pt']}"))
        part_paths.append(rel)
        if art:
            art.gun_art(out, pdir, cdef, info)
        elif cdef.get("art3d"):
            A3.copy_files(out.root, pdir, cdef["short"], cdef["art3d"])
    # fabricas
    for f in DATA.FACTORIES:
        pdir = f"parts/{f['short']}"
        top, info = factory.build_factory(f, own_stack)
        rel = f"{pdir}/{f['short']}.rules"
        out.text(rel, render(top, HEADER + f"\nFabrica: {f['name_en']} / {f['name_pt']}"))
        part_paths.append(rel)
        if art:
            art.factory_art(out, pdir, f, info)
        elif f.get("art3d"):
            A3.copy_files(out.root, pdir, f["short"], f["art3d"])

    # lancadores de misseis de conves
    for lch in DATA.LAUNCHERS:
        pdir = f"parts/{lch['short']}"
        sp = {m["type"]: relpath(pdir, shot_rel[m["shot"]]) for m in lch["modes"]}
        top, info = launchers.build_launcher(lch, sp)
        rel = f"{pdir}/{lch['short']}.rules"
        out.text(rel, render(top, HEADER + f"\nLancador de misseis: {lch['name_en']} / {lch['name_pt']} "
                                           f"(\"{lch['codename']}\")"))
        part_paths.append(rel)
        if art:
            art.launcher_art(out, pdir, lch, info)
        elif lch.get("art3d"):
            A3.copy_files(out.root, pdir, lch["short"], lch["art3d"])
    # seam B3: arte dos projeteis (art3d/bs_missiles, art3d/bs_shells) copiada pelos modulos opcionais, com e
    # sem --no-art (como as copias de art3d acima)
    for m in (FXK, CFX, MFX):
        _call(m, "copy_art", out)
    # gui / techs / strings / mod.rules
    out.text("gui/bs_part_stats.rules", infra.part_stats(factory.input_stat_ids(DATA.FACTORIES)))
    out.text("gui/bs_part_toggles.rules", infra.part_toggles(DATA.AMMO_CHOICES, DATA.missile_toggles()))
    car, bb = infra.techs(DATA.career_techs(), DATA.buildbattle_techs(), DATA.BB_WHITELIST)
    out.text("techs/bs_techs_career.rules", car)
    out.text("techs/bs_techs_buildbattle.rules", bb)
    en, pt = DATA.strings()
    out.text("strings/en.rules", infra.strings_file(en, DATA.MOD_TAG_EN))
    out.text("strings/pt-br.rules", infra.strings_file(pt, DATA.MOD_TAG_PT))
    out.text("mod.rules", infra.mod_rules(DATA.MOD, part_paths, res_paths, DATA.VERSION, DATA.LIMITS, status_paths))
    if art:
        art.misc_art(out)

    check_vanilla_paths(out, args.vanilla)
    print(f"OK: {len(out.files)} arquivos .rules em {root}")


def vanilla_listing(vanilla):
    if not vanilla:
        return None
    if os.path.isdir(os.path.join(vanilla, ".git")):
        try:
            res = subprocess.run(["git", "-C", vanilla, "-c", "gc.auto=0", "ls-tree", "-r", "--name-only",
                                  "origin/main-unstable"], capture_output=True, text=True, check=True)
            return set(res.stdout.split("\n"))
        except Exception:
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-art", action="store_true")
    ap.add_argument("--keep", action="store_true", help="nao apaga a pasta de saida antes")
    ap.add_argument("--vanilla", default=os.environ.get("COSMOTEER_DATA"))
    ap.add_argument("--out", default=os.environ.get("BS_OUT") or ROOT,
                    help="pasta de saida (padrao: BulletStrike/ do repositorio; env BS_OUT)")
    build(ap.parse_args())
