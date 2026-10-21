"""Sprites 3D (renderizados no Blender) do Bullet Strike: leitura do meta.json e copia para o mod.

Cada peca com arte 3D tem uma pasta art3d/<pasta>/ com os PNGs no formato do jogo e um meta.json
gerado por tools/blender/render_part.py (torre, fabrica, recurso, lancador, projeteis) ou por
tools/blender/render_layered.py (kind "layered": carregador/cano/ponta do Tupa, paiois, Fita, placas).
Quando a pasta existe, o gerador do mod usa a geometria do meta (pivo, tamanho da torre, canos, quadros de
animacao, retangulos das camadas) e copia os PNGs em vez de desenhar a arte procedural antiga.

Tipos de pasta (2.0):
  * meta.json "normal" (gun, factory, resource, launcher, missiles, shells, layered);
  * meta.json "shared" (layered com varias pecas numa pasta so: {shared: true, id, parts: {sub: meta}, files});
    a pasta da arte (art3d/bs_paiol) pode ser publicada com outro nome no mod (parts/bs_paiol_comum: o id do meta);
  * icons.json (sem meta.json): icones de interface 96x96 (art3d/bs_ui_icons2), mapa 'files' gui/<x>.png -> <x>.png;
    load_meta devolve um meta {kind: "ui_icons", publish: {gui/...: arquivo}, files: [...]}.
"""

import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART3D = os.path.join(ROOT, "art3d")


def _icons_meta(short, p):
    """icons.json (art3d/bs_ui_icons2) no formato de um meta: kind ui_icons, publish = {gui/<x>.png: <x>.png}."""
    with open(p, encoding="utf-8") as f:
        ic = json.load(f)
    pub = dict(ic.get("files") or {})
    return {"version": ic.get("version", 1), "kind": "ui_icons", "id": f"rafaeltessaro.{short}",
            "size": list(ic.get("size") or [96, 96]), "publish": pub, "files": sorted(set(pub.values())),
            "accents": ic.get("accents") or {}, "drop_1x": ic.get("drop_1x") or [], "source": "icons.json"}


def meta_path(short):
    """Caminho do meta da pasta (meta.json; ou icons.json nas pastas de icones de interface). None sem nenhum."""
    for n in ("meta.json", "icons.json"):
        p = os.path.join(ART3D, short, n)
        if os.path.exists(p):
            return p
    return None


def load_meta(short):
    p = meta_path(short)
    if p is None:
        return None
    if p.endswith("icons.json"):
        meta = _icons_meta(short, p)
    else:
        with open(p, encoding="utf-8") as f:
            meta = json.load(f)
    missing = [n for n in meta.get("files", []) if not os.path.exists(os.path.join(ART3D, short, n))]
    if missing:
        raise FileNotFoundError(f"art3d/{short}: meta.json cita arquivos que nao existem: {missing[:5]}")
    return meta


# ============================================================================ kind "layered" (e pastas shared)
def sub_meta(meta, sub=None):
    """Meta de UMA peca: o proprio meta, ou meta['parts'][sub] numa pasta compartilhada (shared)."""
    if not meta.get("shared"):
        if sub not in (None, meta.get("sub")):
            raise KeyError(f"{meta.get('id')}: meta nao e compartilhado (sub {sub!r})")
        return meta
    parts = meta.get("parts") or {}
    if sub is None:
        if len(parts) == 1:
            return next(iter(parts.values()))
        raise KeyError(f"{meta.get('id')}: pasta compartilhada, escolha sub entre {sorted(parts)}")
    if sub not in parts:
        raise KeyError(f"{meta.get('id')}: sub {sub!r} nao existe (ha {sorted(parts)})")
    return parts[sub]


def sub_metas(meta):
    """[(sub, meta da peca)] de uma pasta layered (shared ou nao)."""
    if meta.get("shared"):
        return sorted((meta.get("parts") or {}).items())
    return [(meta.get("sub"), meta)]


def published_dir(short, meta=None):
    """Pasta do mod onde a arte de art3d/<short> e publicada (parts/<isto>/): o id curto do meta nas pastas
    compartilhadas (art3d/bs_paiol -> bs_paiol_comum), meta['publish_dir'] se existir, senao o proprio nome."""
    meta = meta if meta is not None else load_meta(short)
    if meta and meta.get("publish_dir"):
        return meta["publish_dir"]
    if meta and meta.get("shared") and "." in (meta.get("id") or ""):
        return meta["id"].split(".", 1)[1]
    return short


def layer_files(meta, sub=None, layers=None, normals=True, extras=True):
    """Arquivos de uma peca layered: das camadas pedidas (todas por padrao), com as normais e (extras) walls,
    icone(s) e blueprints."""
    m = sub_meta(meta, sub)
    out = []
    for name, ent in (m.get("layers") or {}).items():
        if layers is not None and name not in layers:
            continue
        out += list(ent.get("files") or [])
        if normals:
            out += list(ent.get("normals") or [])
    if extras:
        for k in ("walls", "icon", "blueprints"):
            v = m.get(k)
            out += list(v) if isinstance(v, list) else ([v] if v else [])
    return out


# Arte procedural antiga (desenhada em Python) so com BS_ARTE_PROCEDURAL=1; sem isso, falta de art3d/<id> ou do
# logo 3D para o build (uma regressao nao passa despercebida).
ALLOW_PROCEDURAL = os.environ.get("BS_ARTE_PROCEDURAL") == "1"


def require(short, meta):
    """Devolve o meta; sem ele (art3d/<id>/meta.json ausente) aborta, a menos que BS_ARTE_PROCEDURAL=1."""
    if meta is None and not ALLOW_PROCEDURAL:
        raise FileNotFoundError(f"art3d/{short}/meta.json nao existe: renderize a peca (tools/blender/render_part.py) "
                                f"ou use BS_ARTE_PROCEDURAL=1 para a arte procedural antiga")
    return meta


def part_scales(short):
    """(unit_scale, icon_scale) do modelo tools/blender/parts/<id>.py, lidos do dicionario PART com ast (sem
    importar o Blender). None quando o modelo nao existe ou nao define as escalas."""
    import ast
    p = os.path.join(ROOT, "tools", "blender", "parts", f"{short}.py")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PART" for t in node.targets) \
                and isinstance(node.value, ast.Dict):
            vals = {}
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and k.value in ("unit_scale", "icon_scale"):
                    vals[k.value] = ast.literal_eval(v)
            if "unit_scale" in vals and "icon_scale" in vals:
                return vals["unit_scale"], vals["icon_scale"]
    return None


def nugget_factor(short, meta):
    """Reducao da unidade solta (nugget) de renders antigos, feitos com icon_scale: o tripulante carregava um
    carregador do tamanho do icone, o dobro da unidade da pilha. render_part.py agora renderiza o nugget com
    unit_scale e grava meta["nugget_scale"]; ate re-renderizar, o build reduz a imagem (fator < 1) no centro."""
    if meta.get("kind") != "resource" or meta.get("nugget_scale"):
        return None
    sc = part_scales(short)
    if not sc:
        return None
    f = sc[0] / sc[1]
    return f if f < 0.95 else None


def scaled_center(img, f):
    """Imagem do mesmo tamanho com o conteudo reduzido pelo fator f em volta do centro (alfa pre-multiplicado,
    sem franja nas bordas transparentes)."""
    from PIL import Image
    im = img.convert("RGBA")
    w, h = im.size
    sw, sh = max(1, round(w * f)), max(1, round(h * f))
    small = im.convert("RGBa").resize((sw, sh), Image.LANCZOS).convert("RGBA")
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(small, ((w - sw) // 2, (h - sh) // 2))
    return out


def overlay_glow(alpha, radius=5.0, strength=0.7):
    """Silhueta branca com halo suave (como os overlay.png vanilla, ex. resources/bullet/overlay.png): o alfa
    borrado (radius px) a strength fica por baixo da silhueta solida."""
    from PIL import Image, ImageChops, ImageFilter
    a = alpha.convert("L")
    halo = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(v * strength))
    out = Image.new("RGBA", a.size, (255, 255, 255, 0))
    out.putalpha(ImageChops.lighter(a, halo))
    return out


_COPIED = set()


def copy_files(out_root, pdir, short, meta, only=None, exclude=None, once=False):
    """Copia os PNGs listados no meta para <mod>/<pdir>/. Renders de recurso antigos (sem nugget_scale /
    overlay_glow no meta) saem ja no formato atual: nugget do tamanho de uma unidade da pilha e overlay com halo.

    only / exclude: conjuntos de nomes (ex.: digitos do paiol so com paiol_counter); once=True copia a mesma pasta
    para o mesmo destino uma vez so por build (pastas compartilhadas: 12 paiois, placas de modo). Icones de
    interface (kind ui_icons): use copy_ui_icons. Devolve os nomes copiados."""
    from PIL import Image
    if meta.get("kind") == "ui_icons":
        raise ValueError(f"art3d/{short}: icones de interface vao para gui/ (use art3d.copy_ui_icons)")
    key = (os.path.abspath(out_root), pdir, short, tuple(sorted(only or ())), tuple(sorted(exclude or ())))
    if once and key in _COPIED:
        return []
    dst = os.path.join(out_root, pdir)
    os.makedirs(dst, exist_ok=True)
    nf = nugget_factor(short, meta)
    names = [n for n in meta["files"] if (only is None or n in only) and not (exclude and n in exclude)]
    if only is not None:
        miss = sorted(set(only) - set(meta["files"]))
        if miss:
            raise FileNotFoundError(f"art3d/{short}: o meta nao lista {miss[:5]}")
    for name in names:
        src = os.path.join(ART3D, short, name)
        if nf and name in ("nugget.png", "nugget_normals.png"):
            scaled_center(Image.open(src), nf).save(os.path.join(dst, name), optimize=True)
        elif meta.get("kind") == "resource" and name == "overlay.png" and not meta.get("overlay_glow"):
            overlay_glow(Image.open(src).convert("RGBA").getchannel("A")).save(os.path.join(dst, name), optimize=True)
        else:
            shutil.copyfile(src, os.path.join(dst, name))
    if once:
        _COPIED.add(key)
    return names


def copy_ui_icons(out_root, short="bs_ui_icons2", only=None):
    """Copia os icones de interface de art3d/<short>/ para os caminhos do mapa icons.json 'files' (gui/<x>.png).
    only: caminhos publicados a copiar (padrao: todos). Devolve [caminhos publicados]."""
    meta = load_meta(short)
    if meta is None:
        return []
    if meta.get("kind") != "ui_icons":
        raise ValueError(f"art3d/{short}: kind {meta.get('kind')} (esperado ui_icons)")
    done = []
    for rel, name in sorted(meta["publish"].items()):
        if only is not None and rel not in only:
            continue
        p = os.path.join(out_root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        shutil.copyfile(os.path.join(ART3D, short, name), p)
        done.append(rel)
    return done


def path(short, name):
    return os.path.join(ART3D, short, name)
