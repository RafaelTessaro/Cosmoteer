#!/usr/bin/env python3
"""Checagem de "esquema" por corpus: compara campos e valores-enum usados pelo mod com os usados
pelos arquivos do jogo base (e opcionalmente por outro mod grande, ex. SW:ACD, como prova do 0.30.4).

Para cada grupo com `Type = X`, junta os nomes de campos que o jogo usa com esse Type. Um campo do mod
que nunca aparece com aquele Type no corpus e reportado (provavel erro de digitacao ou campo inexistente,
que o jogo ignoraria em silencio). Tambem confere valores de campos com vocabulario pequeno
(Mode, ModificationMode, TargetType, Direction, Layer...).

Uso:
    python3 tools/schema_check.py --mod BulletStrike --vanilla <Data do jogo> [--extra <outro mod>]
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules_lint as RL  # noqa: E402

ENUM_FIELDS = {"mode", "modificationmode", "targettype", "direction", "layer", "addmode", "removemode",
               "valuetype", "statusvaluetype", "operation", "nonoperationalbehaviour", "style", "samplemode",
               "animationstarttime", "renderbucket", "buffmode", "type", "rarity", "healthtype"}
ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Grupos de acerto que o JOGO mostra serem do mesmo tipo (Cosmoteer.Bullets.Hits.HitRules): o proprio jogo atribui
# um ao outro por referencia, entao um campo provado num deles vale nos outros. Sem isto o corpus acusa, por exemplo,
# MediaEffectsScale no HitShield de um SimpleHit so porque o jogo nunca escreveu o HitShield por extenso.
# Contexto do mod -> contextos do corpus cujos campos tambem valem (precedente vanilla 0.30.x em cada linha).
SAME_TYPE = {
    # missile_he.rules l.125: "HitShield = &HitOperational" (SimpleHit)
    "N:SimpleHit/hitshield": ("N:SimpleHit/hitoperational",),
    # missile_he.rules l.117 "OnDeath = &../Hit/HitFriendly" e mine.rules l.78 "OnDeath = &~/Components/Hit/HitOperational":
    # HitFriendly e HitOperational cabem no mesmo campo OnDeath
    "N:SimpleHit/hitfriendly": ("N:SimpleHit/hitoperational",),
    # bullet_railgun.rules l.61: "HitCrew = &HitOperational"
    "N:PenetratingHit/hitcrew": ("N:PenetratingHit/hitoperational",),
    # disruptor_bolt_overclock.rules l.46: "PenetratingOperational : ^/0/HitOperational"
    "N:PenetratingHit/penetratingoperational": ("N:PenetratingHit/hitoperational",),
    # bullet_deck.rules l.147: "PenetratingStructural : &HitStructural"
    "N:PenetratingHit/penetratingstructural": ("N:PenetratingHit/hitstructural",),
    # bullet_deck.rules l.152: "FinishedPenetratingOperational = &PenetratingOperational" (+ a linha acima)
    "N:PenetratingHit/finishedpenetratingoperational": ("N:PenetratingHit/penetratingoperational",
                                                        "N:PenetratingHit/hitoperational"),
    # bullet_deck.rules l.153: "FinishedPenetratingStructural = &PenetratingStructural"
    "N:PenetratingHit/finishedpenetratingstructural": ("N:PenetratingHit/penetratingstructural",
                                                       "N:PenetratingHit/hitstructural"),
    # raiz de arquivo de feixe (Beam): ion_beam.rules l.161 "HitShield = &HitOperational";
    # ion_beam_overclock.rules l.62-64 "HitShield/HitCrew/HitNothing = &HitOperational"
    "R:hitshield": ("R:hitoperational",),
    "R:hitcrew": ("R:hitoperational",),
    "R:hitnothing": ("R:hitoperational",),
}


def known_fields(corpus, sig):
    """Campos que o corpus aceita no contexto sig: os dele mais os dos contextos do mesmo tipo (SAME_TYPE).
    None quando nem o contexto nem os equivalentes aparecem no corpus."""
    sets = [corpus[s] for s in (sig,) + SAME_TYPE.get(sig, ()) if s in corpus]
    if not sets:
        return None
    return set().union(*sets)


def iter_nodes(node):
    yield node
    for c in node.children:
        yield from iter_nodes(c)


def child_value(node, name):
    for c in node.children:
        if c.name and c.name.lower() == name and c.kind == "value":
            return (c.value or "").strip().strip('"')
    return None


def signature(n):
    """Chave de contexto de um grupo: seu Type, ou (Type do ancestral mais proximo, nome)."""
    t = child_value(n, "type")
    if t:
        return "T:" + t
    names = []
    a = n
    while a is not None and a.parent is not None:
        names.append((a.name or "[]").lower())
        at = child_value(a.parent, "type") if a.parent.kind in ("group", "inherit") else None
        if at:
            return f"N:{at}/" + "/".join(reversed(names))
        a = a.parent
        if len(names) > 3:
            break
    return "R:" + "/".join(reversed(names))


def collect(files, corpus, enums, types):
    for path in files:
        try:
            text = open(path, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        rf = RL.RFile("fs", path, path)
        root, errs, _w = RL.parse_text(text, rf)
        if root is None:
            continue
        for n in iter_nodes(root):
            if n.kind not in ("group", "inherit") or n.parent is None:
                continue
            sig = signature(n)
            if sig.startswith("T:"):
                types.add(sig[2:])
            fields = corpus.setdefault(sig, set())
            for c in n.children:
                if not c.name:
                    continue
                fields.add(c.name.lower())
                if c.kind == "value" and c.name.lower() in ENUM_FIELDS and sig != "T:ModeToggle":
                    v = (c.value or "").strip().strip('"')
                    if ID_RE.match(v):
                        enums.setdefault((sig, c.name.lower()), set()).add(v.lower())


def rules_files(d):
    out = []
    for dp, dn, fn in os.walk(d):
        if ".git" in dp:
            continue
        for f in fn:
            if f.endswith(".rules"):
                out.append(os.path.join(dp, f))
    return out


def vanilla_full(vanilla, cache):
    """Inclui arquivos do historico git que nao estao no checkout (le com git show)."""
    files = rules_files(vanilla)
    try:
        lst = subprocess.run(["git", "-C", vanilla, "-c", "gc.auto=0", "ls-tree", "-r", "--name-only",
                              "origin/main-unstable"], capture_output=True, text=True, check=True).stdout.split("\n")
    except Exception:
        return files
    have = {os.path.relpath(f, vanilla).replace(os.sep, "/") for f in files}
    os.makedirs(cache, exist_ok=True)
    for rel in lst:
        if rel.endswith(".rules") and rel not in have:
            dst = os.path.join(cache, rel)
            if not os.path.exists(dst):
                try:
                    txt = subprocess.run(["git", "-C", vanilla, "-c", "gc.auto=0", "show", f"origin/main-unstable:{rel}"],
                                         capture_output=True, check=True).stdout
                except Exception:
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, "wb").write(txt)
            files.append(dst)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", required=True)
    ap.add_argument("--vanilla", required=True)
    ap.add_argument("--extra", action="append", default=[])
    ap.add_argument("--cache", default=os.path.join(HERE, ".vanilla_cache"))
    a = ap.parse_args()
    corpus, enums, types = {}, {}, set()
    collect(vanilla_full(a.vanilla, a.cache), corpus, enums, types)
    for e in a.extra:
        collect(rules_files(e), corpus, enums, types)
    problems = 0
    for path in rules_files(a.mod):
        text = open(path, encoding="utf-8").read()
        rf = RL.RFile("fs", path, path)
        root, errs, _w = RL.parse_text(text, rf)
        for n in iter_nodes(root):
            if n.kind not in ("group", "inherit") or n.parent is None:
                continue
            sig = signature(n)
            rel = os.path.relpath(path, a.mod)
            # nomes livres: componentes, constantes de stats e arquivos de textos
            if rel.startswith("strings") or sig.endswith("components") or sig.endswith("/stats") \
                    or sig.endswith("[]") or sig.split("/")[-1].startswith("emitter"):
                continue
            if sig.startswith("T:") and sig[2:] not in types:
                print(f"{rel}:{n.line}: Type '{sig[2:]}' nunca usado pelo jogo")
                problems += 1
                continue
            known = known_fields(corpus, sig)
            if known is None:
                if sig.startswith("N:"):
                    print(f"{rel}:{n.line}: grupo '{n.name}' ({sig}) nunca aparece nesse contexto no jogo")
                    problems += 1
                continue
            for c in n.children:
                if not c.name:
                    continue
                nm = c.name.lower()
                if c.name.isupper() or c.name.startswith("_") or c.name.startswith("STAT_"):
                    continue  # constantes auxiliares (o jogo ignora) / parametros de shader
                if nm not in known:
                    print(f"{rel}:{c.line}: campo '{c.name}' nunca aparece em {sig} no jogo")
                    problems += 1
                elif c.kind == "value" and nm in ENUM_FIELDS and sig != "T:ModeToggle":
                    v = (c.value or "").strip().strip('"')
                    seen = enums.get((sig, nm))
                    if seen and ID_RE.match(v) and v.lower() not in seen:
                        print(f"{rel}:{c.line}: valor '{v}' em {c.name} ({sig}) nunca usado pelo jogo "
                              f"(o jogo usa: {', '.join(sorted(seen)[:8])})")
                        problems += 1
    print(f"schema_check: {problems} ocorrencia(s) suspeita(s); corpus com {len(types)} Types")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
