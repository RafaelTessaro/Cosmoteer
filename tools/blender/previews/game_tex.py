"""Texturas do JOGO para os compositores de previa (ADDENDUM G13): procuradas pelo nome dentro da pasta Data do jogo.

Nunca commitar texturas do jogo: elas sao lidas de $COSMOTEER_DATA (ou de --vanilla / BS_VANILLA) na hora.
A pasta pode ser a Data instalada do jogo ou um clone git do Data (parcial ou nao): primeiro o disco, depois a
listagem do git (origin/main-unstable, senao HEAD), lida com `git show` para um cache temporario.

    import game_tex
    path = game_tex.find("blob.png")            # caminho local do arquivo
    path = game_tex.find("radiation.png", prefer="shots/missile_nuke")
"""
import os
import subprocess
import tempfile

_CACHE_DIR = os.path.join(tempfile.gettempdir(), "bs_game_tex")
_LISTING = {}
_FOUND = {}


def vanilla_dir():
    for k in ("BS_VANILLA", "COSMOTEER_DATA"):
        v = os.environ.get(k)
        if v and os.path.isdir(v):
            return v
    raise SystemExit("texturas do jogo: defina COSMOTEER_DATA (pasta Data do jogo ou clone git do Data); "
                     "as texturas do jogo nunca vao para o repositorio")


def _git_listing(vdir):
    if vdir in _LISTING:
        return _LISTING[vdir]
    out = (None, [])
    if os.path.isdir(os.path.join(vdir, ".git")):
        for ref in ("origin/main-unstable", "HEAD"):
            try:
                r = subprocess.run(["git", "-C", vdir, "-c", "gc.auto=0", "ls-tree", "-r", "--name-only", ref],
                                   capture_output=True, text=True, timeout=60)
            except Exception:  # noqa: BLE001 (git ausente)
                break
            if r.returncode == 0 and r.stdout.strip():
                out = (ref, r.stdout.split("\n"))
                break
    _LISTING[vdir] = out
    return out


def _pick(cands, prefer):
    if not cands:
        return None
    if prefer:
        pref = [c for c in cands if prefer.strip("/") in c.replace(os.sep, "/")]
        if pref:
            return sorted(pref, key=len)[0]
    return sorted(cands, key=len)[0]


def find(name, prefer=None, vdir=None):
    """Caminho local da textura do jogo 'name' (so o nome do arquivo). prefer = pedaco do caminho para desempatar."""
    vdir = vdir or vanilla_dir()
    key = (vdir, name, prefer)
    if key in _FOUND:
        return _FOUND[key]
    # 1) disco
    cands = []
    for dp, _dn, fn in os.walk(vdir):
        if ".git" in dp.split(os.sep):
            continue
        if name in fn:
            cands.append(os.path.join(dp, name))
    hit = _pick(cands, prefer)
    if hit is None:
        # 2) git (clone parcial: o arquivo pode estar so no historico)
        ref, files = _git_listing(vdir)
        rel = _pick([f for f in files if f.rsplit("/", 1)[-1] == name], prefer)
        if ref and rel:
            dst = os.path.join(_CACHE_DIR, ref.replace("/", "_"), rel)
            if not os.path.isfile(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                r = subprocess.run(["git", "-C", vdir, "-c", "gc.auto=0", "show", f"{ref}:{rel}"],
                                   capture_output=True, timeout=60)
                if r.returncode != 0:
                    raise FileNotFoundError(f"textura do jogo {name}: git show {ref}:{rel} falhou")
                with open(dst, "wb") as fh:
                    fh.write(r.stdout)
            hit = dst
    if hit is None:
        raise FileNotFoundError(f"textura do jogo {name} nao achada em {vdir}")
    _FOUND[key] = hit
    return hit
