#!/usr/bin/env python3
"""Conferencias da 2.0 (dono: WP01) sobre um build do mod e sobre o spec.

Uso:
    python3 tools/spec2_check.py --schema-diff BASE.txt NOVO.txt [--allow REGEX ...]
        assinaturas novas do schema_check (Type / grupo / campo / valor) que nao estavam na linha de base;
        sai 1 se alguma nao casar com --allow
    python3 tools/spec2_check.py --mod <pasta do mod> [--vanilla $COSMOTEER_DATA] [--docs] [--no-selfcheck]
        nucleo: recursos, seletores, techs e pre-requisitos, nenhum enriched_uranium, nenhum pre-requisito
        cosmoteer.factory_*, campos 0.30.5 proibidos (SPEC.conventions.forbidden_fields_0305), varredura de nomes
        removidos (SPEC.conventions.removed_names_scan, fronteira de palavra; --docs tambem nos docs gerados),
        toda referencia &<../parts/<id>/<id>.rules> existe, --data-paths (todo ./Data/<p> novo em relacao ao build
        do BASE existe nos dados 0.30.2 e 0.30.5), todo switch com decided_by tem safe, valores gravados em
        bullet_strike_switches.json validos (ADDENDUM G12), lista de placeholders; depois o selfcheck() de cada
        modulo presente (API >= 2)
    python3 tools/spec2_check.py --data-paths --mod <pasta>     # so os caminhos ./Data
    python3 tools/spec2_check.py --perfil vanilla               # nao existe na 2.0 (resposta 3 = nao)
"""

import argparse
import importlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

BASE_FILE = os.path.join(HERE, "spec", "BASE_2_0.txt")
COMMIT_0302 = "e07af76"


def _load_spec():
    with open(os.path.join(HERE, "spec", "bullet_strike_spec.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ----------------------------------------------------------------------------- schema diff
_SIG_RE = re.compile(r"^[^:]+:\d+: ")


def signatures(path):
    sigs = set()
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.rstrip("\n")
            if not _SIG_RE.match(ln):
                continue
            sig = _SIG_RE.sub("", ln)
            sig = re.sub(r" \(o jogo usa: [^)]*\)$", "", sig)
            sigs.add(sig)
    return sigs


def schema_diff(a, b, allow):
    old, new = signatures(a), signatures(b)
    extra = sorted(new - old)
    pats = [re.compile(x) for x in allow or []]
    bad = [s for s in extra if not any(p.search(s) for p in pats)]
    for s in extra:
        print(("NOVA (permitida): " if s not in bad else "NOVA: ") + s)
    gone = sorted(old - new)
    if gone:
        print(f"({len(gone)} assinatura(s) da base sumiram - ok)")
    print(f"schema-diff: {len(extra)} nova(s), {len(bad)} fora da allowlist")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- utilidades do mod
def rules_files(mod):
    for dp, dn, fn in os.walk(mod):
        dn[:] = sorted(d for d in dn if d != ".git")
        for f in sorted(fn):
            if f.endswith(".rules"):
                p = os.path.join(dp, f)
                yield os.path.relpath(p, mod).replace(os.sep, "/"), p


def read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in text.split("\n"))


def base_data_paths():
    if not os.path.isfile(BASE_FILE):
        return None
    out, on = set(), False
    for ln in read(BASE_FILE).split("\n"):
        if ln.strip() == "DATA_PATHS_BEGIN":
            on = True
            continue
        if ln.strip() == "DATA_PATHS_END":
            break
        if on and ln.strip():
            out.add(ln.strip())
    return out


def git_exists(vdir, objs):
    """{objeto: bool} via git cat-file --batch-check (objeto = '<ref>:<caminho>')."""
    if not objs:
        return {}
    r = subprocess.run(["git", "-C", vdir, "-c", "gc.auto=0", "cat-file", "--batch-check"],
                       input="\n".join(objs) + "\n", capture_output=True, text=True, timeout=300)
    res = {}
    for obj, ln in zip(objs, r.stdout.split("\n")):
        res[obj] = not ln.endswith("missing")
    return res


class Check:
    def __init__(self):
        self.errors = []
        self.notes = []

    def err(self, msg):
        self.errors.append(msg)
        print(f"ERRO: {msg}")

    def ok(self, msg):
        print(f"ok: {msg}")


# ----------------------------------------------------------------------------- checagens
def check_data_paths(c, mod, vdir):
    base = base_data_paths()
    if base is None:
        c.err(f"{BASE_FILE} sem a secao DATA_PATHS (linha de base do --data-paths)")
        return
    if not vdir or not os.path.isdir(os.path.join(vdir, ".git")):
        c.err("--data-paths precisa de --vanilla / COSMOTEER_DATA apontando para o clone git do Data")
        return
    used = {}
    pat = re.compile(r"\./Data/([^\">\s;,}\]]+)")
    for rel, p in rules_files(mod):
        for m in pat.finditer(read(p)):
            used.setdefault(m.group(1), rel)
    new = sorted(set(used) - base)
    objs = []
    for p in new:
        objs += [f"{COMMIT_0302}:Data/{p}", f"origin/main-unstable:{p}"]
    have = git_exists(vdir, objs)
    bad = 0
    for p in new:
        a, b = have.get(f"{COMMIT_0302}:Data/{p}"), have.get(f"origin/main-unstable:{p}")
        if not (a and b):
            bad += 1
            c.err(f"--data-paths: ./Data/{p} ({used[p]}) novo e ausente nos dados "
                  f"{'0.30.2 (' + COMMIT_0302 + ')' if not a else ''}{' e ' if not a and not b else ''}"
                  f"{'0.30.5 (origin/main-unstable)' if not b else ''}: vendorize em tools/vanilla_fx/")
    if not bad:
        c.ok(f"--data-paths: {len(used)} caminhos ./Data ({len(new)} novos em relacao ao BASE) nos dados 0.30.2 e 0.30.5")


def check_forbidden(c, mod, spec):
    fields = spec["conventions"]["forbidden_fields_0305"]
    pat = re.compile(r"^\s*(" + "|".join(map(re.escape, fields)) + r")\b", re.M)
    n = 0
    for rel, p in rules_files(mod):
        for m in pat.finditer(strip_comments(read(p))):
            n += 1
            c.err(f"campo 0.30.5 proibido {m.group(1)} em {rel}")
    if not n:
        c.ok(f"nenhum campo 0.30.5 proibido ({len(fields)} conferidos)")


def check_removed_names(c, mod, spec, docs=False):
    rs = spec["conventions"]["removed_names_scan"]
    pat = re.compile(rs["pattern"])
    boi = re.compile(rs.get("boiuna_only") or r"(?!x)x")
    allow = [a.split(" ")[0] for a in rs.get("allow", [])]
    targets = []
    for rel, p in rules_files(mod):
        if rel.startswith(("strings/", "parts/", "shots/")):
            targets.append((rel, p))
    if docs:
        for d in ("docs/ARMAS.md", "docs/MISSEIS_PROJETO.md", "README.md"):
            p = os.path.join(REPO, d)
            if os.path.isfile(p):
                targets.append((d, p))
    n = 0
    for rel, p in targets:
        text = read(p)
        for i, ln in enumerate(text.split("\n"), 1):
            hits = [m.group(0) for m in pat.finditer(ln)]
            if "howitzer" in rel or "boiuna" in rel.lower():
                hits += [m.group(0) for m in boi.finditer(ln)]
            hits = [h for h in hits if not any(a in ln and h in a for a in allow)]
            for h in hits:
                n += 1
                c.err(f"nome removido '{h}' em {rel}:{i}")
    if not n:
        c.ok(f"varredura de nomes removidos: {len(targets)} arquivo(s) limpos")


def check_part_refs(c, mod):
    pat = re.compile(r"&<\.\./parts/([^/>]+)/([^>]+\.rules)>")
    n = 0
    for rel, p in rules_files(mod):
        for m in pat.finditer(read(p)):
            tgt = os.path.normpath(os.path.join(os.path.dirname(p), "..", "parts", m.group(1), m.group(2)))
            if not os.path.isfile(tgt):
                n += 1
                c.err(f"{rel}: referencia &<../parts/{m.group(1)}/{m.group(2)}> para peca nao escrita")
    if not n:
        c.ok("toda referencia &<../parts/...> existe no mod")


def check_text_rules(c, mod):
    n = 0
    for rel, p in rules_files(mod):
        t = strip_comments(read(p))
        if "enriched_uranium" in t:
            n += 1
            c.err(f"enriched_uranium em {rel}")
        for m in re.finditer(r"cosmoteer\.factory_\w+", t):
            if "techs/" in rel:
                n += 1
                c.err(f"pre-requisito/peca vanilla de fabrica {m.group(0)} em {rel}")
    if not n:
        c.ok("nenhum enriched_uranium; nenhuma cosmoteer.factory_* nas techs")


def _vanilla_tech_ids(vdir):
    ids = set()
    for ref, path in (("origin/main-unstable", "modes/career/techs.rules"),
                      ("origin/main-unstable", "modes/pvp/pvp_buildbattle/techs_buildbattle.rules")):
        try:
            r = subprocess.run(["git", "-C", vdir, "-c", "gc.auto=0", "show", f"{ref}:{path}"],
                               capture_output=True, text=True, timeout=120)
            ids |= set(re.findall(r"^\s*ID\s*=\s*([\w.\-]+)", r.stdout, re.M))
        except Exception:  # noqa: BLE001
            pass
    return ids


def check_core(c, mod, D, vdir):
    # recursos
    for r in D.RESOURCES:
        p = os.path.join(mod, "resources", r["dir"], f"{r['dir']}.rules")
        if not os.path.isfile(p) or f"ID = {r['id']}" not in read(p):
            c.err(f"recurso {r['id']} ausente ou com outro ID")
    if any("bs_slug_rail" in r["id"] for r in D.RESOURCES) != D.RAIL_ENABLED:
        c.err("bs_slug_rail tem que existir so com rail.enabled")
    c.ok(f"{len(D.RESOURCES)} recursos")
    # seletores
    pt = read(os.path.join(mod, "gui", "bs_part_toggles.rules")) if os.path.isfile(os.path.join(mod, "gui", "bs_part_toggles.rules")) else ""
    for tid, n in (("bs_ammo_type", 5), ("bs_cell_type", 2), ("bs_missile_type", 4)):
        m = re.search(r'ToggleID = "' + tid + r'"(.*?)(?=ToggleID = |\Z)', pt, re.S)
        cnt = len(re.findall(r"ChoiceID", m.group(1))) if m else 0
        if cnt != n:
            c.err(f"PartToggle {tid}: {cnt} escolhas (esperado {n})")
    c.ok("seletores bs_ammo_type (5), bs_cell_type (2), bs_missile_type (4)")
    # techs e pre-requisitos
    car = read(os.path.join(mod, "techs", "bs_techs_career.rules"))
    ids = set(re.findall(r"^\s*ID = ([\w.\-]+)", car, re.M))
    van = _vanilla_tech_ids(vdir) if vdir else set()
    for blk in re.findall(r"Prerequisites = \[([^\]]*)\]", car):
        for pre in [x.strip() for x in blk.split(",") if x.strip()]:
            if pre.startswith("cosmoteer.factory_"):
                c.err(f"pre-requisito de fabrica vanilla {pre}")
            elif pre not in ids and (not van or pre not in van):
                c.err(f"pre-requisito {pre} nao e tech do mod nem do jogo")
    c.ok(f"techs da carreira: {len(ids)} (pre-requisitos conferidos)")


def check_switches(c, spec, D):
    n = 0
    for key, e in D.SWITCH_DEFS.items():
        if "decided_by" in e and "safe" not in e:
            n += 1
            c.err(f"switch {key} tem decided_by e nao tem safe")
    fita = (spec.get("build_2_0") or {}).get("switch_values_fita") or {}
    for key, v in D._FILE_SW.items():
        e = D.SWITCH_DEFS[key]
        ok = [e.get("safe"), (e.get("answered_addendum") or {}).get("value"), fita.get(key)]
        if "decided_by" in e and not any(x is not None and D._canon(x) == D._canon(v) for x in ok):
            n += 1
            c.err(f"bullet_strike_switches.json: {key} = {v} nao e safe, answered_addendum nem build_2_0 (G12)")
    if not n:
        c.ok(f"switches: todo decided_by tem safe; {len(D._FILE_SW)} valor(es) gravado(s) validos")


def check_placeholders(c, mod, spec, D):
    try:
        from PIL import Image, ImageChops
        from bsgen import placeholder_icons as P
    except Exception:  # noqa: BLE001
        return
    ph = []
    for rel, (label, rgb) in sorted(P.wanted(dict(spec, art_assets=D.ART2)).items()):
        p = os.path.join(mod, rel)
        if os.path.isfile(p):
            a = Image.open(p).convert("RGBA")
            b = P.draw(label, rgb)
            if a.size == b.size and ImageChops.difference(a, b).getbbox() is None:
                ph.append(f"icone provisorio {rel}")
    ph += [x for x in D.PLACEHOLDERS if not x.startswith("icone")]
    print(f"placeholders ({len(ph)}): " + ("; ".join(ph) if ph else "nenhum"))
    c.notes.append(("placeholders", ph))


def run_selfchecks(c, mod, spec):
    from bsgen import common as C
    names = ["bsgen.guns", "bsgen.ciws", "bsgen.factory", "bsgen.logistics", "bsgen.intake", "bsgen.belt_net",
             "bsgen.pem", "bsgen.railgun", "bs_data_missiles", "bsgen.launchers", "bsgen.missile_shots",
             "bsgen.fx_tex"]
    if os.environ.get("BS_FX_EXT", "1") != "0":
        names += ["bsgen.fxkit", "bsgen.caliber_fx", "bsgen.missile_fx", "bsgen.pem_fx", "bsgen.rail_fx"]
    ran = 0
    for name in names:
        mod_ = C.content_module(name)
        f = getattr(mod_, "selfcheck", None) if mod_ is not None else None
        if not callable(f):
            continue
        ran += 1
        probs = [p for p in (f(mod, spec) or []) if p]
        for p in probs:
            c.err(f"selfcheck {name}: {p}")
        if not probs:
            c.ok(f"selfcheck {name}")
    if not ran:
        print("selfcheck: nenhum modulo com API >= 2 presente")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Conferencias da 2.0 (WP01).")
    ap.add_argument("--schema-diff", nargs=2, metavar=("BASE", "NOVO"))
    ap.add_argument("--allow", action="append", default=[], help="regex de assinatura permitida (repetivel)")
    ap.add_argument("--mod")
    ap.add_argument("--vanilla", default=os.environ.get("COSMOTEER_DATA"))
    ap.add_argument("--data-paths", action="store_true", help="so a conferencia dos caminhos ./Data")
    ap.add_argument("--docs", action="store_true", help="varredura de nomes removidos tambem nos docs gerados")
    ap.add_argument("--no-selfcheck", action="store_true")
    ap.add_argument("--perfil")
    a = ap.parse_args(argv)
    if a.perfil:
        if a.perfil != "sw":
            print("perfil jogo base nao existe na 2.0 (resposta 3 = nao)")
            return 2
    if a.schema_diff:
        return schema_diff(a.schema_diff[0], a.schema_diff[1], a.allow)
    if not a.mod:
        ap.print_help()
        return 2
    mod = os.path.abspath(a.mod)
    spec = _load_spec()
    c = Check()
    if a.data_paths:
        check_data_paths(c, mod, a.vanilla)
        return 1 if c.errors else 0
    import bs_data as D
    check_switches(c, spec, D)
    check_core(c, mod, D, a.vanilla)
    check_text_rules(c, mod)
    check_forbidden(c, mod, spec)
    check_removed_names(c, mod, spec, a.docs)
    check_part_refs(c, mod)
    check_data_paths(c, mod, a.vanilla)
    check_placeholders(c, mod, spec, D)
    if not a.no_selfcheck:
        run_selfchecks(c, mod, spec)
    print(f"spec2_check: {'OK' if not c.errors else str(len(c.errors)) + ' erro(s)'}")
    return 1 if c.errors else 0


if __name__ == "__main__":
    sys.exit(main())
