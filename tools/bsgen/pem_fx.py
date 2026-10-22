"""Efeitos da linha PEM do Bullet Strike 2.0 (dono: WP08; modulo FX do registro do build_mod, API 2; BS_FX_EXT=0
desliga). Fonte: SPEC.art_assets.effects.pem (tools/spec/bullet_strike_art2.json) e SPEC.pem_weapons.visuals.

Gancho write(out, header): grava shots/bs_pem_fx/*.rules (DIR), todos em CIANO / azul eletrico (palette.pem), nunca
vermelho; o cobre so no clarao da boca (assinatura da familia):
  pem_muzzle_flash_<t>   clarao cobre-ambar (1, 0.62, 0.3) de 1 particula, 1,2 / 1,8 / 2,6 tiles (t = s, m, l:
                         Tuvira, Treme-Treme, pesada);
  pem_muzzle_arcs_<t>    arcos ciano na boca: copia RECOLORIDA de disruptor_shoot_lightning (vanilla, guardada em
                         tools/vanilla_fx/pem/), 1-2 / 2-3 / 3-4 arcos;
  pem_muzzle_light_<t>   luz de casco ciano-azul (particle_light, palette.pem.hull com alfa 0,25: canal mais fraco no
                         casco branco <= 0,5, fxkit.particle_light_white);
  pem_crackle_<t>        crepitar em voo: copia recolorida de disruptor_bolt_lightning (a do raio vanilla, feita para
                         projetil: InheritVelocity + Barrier), 2 / 4 / 6 por segundo;
  pem_ring_<t>           anel ciano no escudo (bs_ring_thin do fx_tex), 3 / 4,5 / 6 tiles DEPOIS do MediaEffectsScale
                         do bloco HitShield (SHIELD_MES; o tamanho no arquivo ja e dividido por ele);
  pem_sizzle             chiado ciano do dreno (MediaEffectsOnDrain) e da peca atravessada pelo overclock da pesada;
  pem_fizzle             estouro ciano pequeno quando a granada e abatida no ar (Targetable.OnDeath);
  pem_charge_arcs_a/_b   arcos entre os dois canos da pesada durante a carga de 0,5 s antes de cada disparo (copia de
                         disruptor_shoot_lightning com o angulo travado para o lado: um arquivo para cada cano).
Orcamento da boca (particulas por disparo, SPEC.art_assets.effects.pem.muzzle.budget_particles): 4 / 6 / 8.

Quem usa (bsgen/pem.py): muzzle_refs(t, frm), crackle_ref(t), ring_ref(t), sizzle_ref(), fizzle_ref(),
charge_refs(frm); refs no formato do fxkit.ref (caminho sem &<>, frm 'shot' ou 'part').
Copias vanilla: so trocam cores do material (_centerColor/_outerColor/_bloomColor), caminhos relativos -> ./Data, a
quantidade (EmitPerOneShot / EmitPerSecond), o tamanho (SetRandom da escala) e o angulo; cada troca confere quantas
vezes achou o texto (texto vanilla diferente = build para). Nenhum &/SW_* e nenhum campo so do 0.30.5.
"""

import os
import re

from bsgen import fxkit as FXK

API = 2

DIR = "shots/bs_pem_fx"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # tools/
VENDOR_DIR = os.path.join(HERE, "vanilla_fx", "pem")
D = "./Data"
TIERS = ("s", "m", "l")
TEX_RING = "../bs_fx_tex/bs_ring_thin.png"      # fx_tex.ref('bs_ring_thin.png', 'shot') (fx_tex e de CONTEUDO)

# fontes vanilla guardadas: nome -> (caminho no Data, pasta do arquivo no Data para resolver caminhos relativos)
VENDORED = {
    "shoot_lightning": ("ships/terran/disruptor/particles/disruptor_shoot_lightning.rules",
                        "ships/terran/disruptor/particles"),
    "bolt_lightning": ("shots/disruptor_bolt/particles/disruptor_bolt_lightning.rules",
                       "shots/disruptor_bolt/particles"),
}

# numeros (SPEC.art_assets.effects.pem; o que o spec nao fixa esta marcado "escolha WP08")
FLASH = {"s": 1.2, "m": 1.8, "l": 2.6}                   # clarao cobre-ambar (spec)
FLASH_COLOR = (1, 0.62, 0.3, 1)                          # spec
ARCS = {"s": (1, 2), "m": (2, 3), "l": (3, 4)}           # arcos da boca (spec)
ARC_SCALE = {"s": 0.6, "m": 0.85, "l": 1.2}              # escala dos arcos x vanilla (escolha WP08: peca 1 / 2 / 4)
LIGHT = {"s": 2.0, "m": 3.0, "l": 4.5}                   # luz de casco da boca (tiles; escolha WP08)
CRACKLE = {"s": 2, "m": 4, "l": 6}                       # crepitar por segundo (spec: 2/s na pem_s; m/l escolha WP08)
CRACKLE_SCALE = {"s": 0.5, "m": 0.7, "l": 1.0}           # x vanilla (o raio vanilla e de 1 a 1,8 tiles)
RING = {"s": 3.0, "m": 4.5, "l": 6.0}                    # anel no escudo (spec), tiles finais
SHIELD_MES = {"s": 0.2, "m": 0.3, "l": 0.45}             # MediaEffectsScale do HitShield (pem.py usa o mesmo)
HULL_MES = {"s": 0.8, "m": 1.2, "l": 1.8}                # MediaEffectsScale do HitOperational (spec: 0,8/1,2/1,8)
BUDGET = {"s": 4, "m": 6, "l": 8}                        # particulas por disparo na boca (spec)
CHARGE_PER_S = 4                                         # por arquivo (2 arquivos = 8/s, spec)
CHARGE_LIFE = (0.12, 0.2)                                # vida (spec: 0,16 s em media)

HOT = [(1.6, 1.6, 1.6, 1), (1.15, 1.15, 1.15, 0.75), (1, 1, 1, 0.25), (1, 1, 1, 0)]
RING_RAMP = [(1.4, 1.4, 1.4, 1), (1.1, 1.1, 1.1, 0.95), (1, 1, 1, 0.7), (1, 1, 1, 0)]
LIGHT_RAMP = [(1, 1, 1, 1), (1, 1, 1, 0.5), (1, 1, 1, 0)]


def _c255(rgb, a=1.0):
    return tuple(round(float(v) / 255.0, 4) for v in list(rgb)[:3]) + (a,)


def colors():
    """Cores (float) da familia PEM a partir de palette.pem: centro/franja/bloom dos raios, ciano e a luz de casco."""
    p = FXK.pal("pem")
    return {"center": _c255(p["core"]), "outer": _c255(p["band"]), "bloom": _c255(p["glow"]),
            "cyan": _c255(p["band"]), "hull": _c255(p["hull"], 0.25)}


# ============================================================================= copias vanilla recoloridas
_VENDOR_CACHE = {}


def vendor_text(name):
    """Texto vanilla guardado (sem as linhas // do cabecalho do vendor)."""
    if name not in _VENDOR_CACHE:
        path = os.path.join(VENDOR_DIR, os.path.basename(VENDORED[name][0]))
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        i = 0
        while i < len(lines) and lines[i].startswith("//"):
            i += 1
        _VENDOR_CACHE[name] = "\n".join(lines[i:])
    return _VENDOR_CACHE[name]


def _sub(text, pat, repl, count, what, flags=re.M):
    """re.subn conferido: o padrao tem de casar exatamente count vezes (texto vanilla diferente = erro no build)."""
    new, n = re.subn(pat, repl, text, flags=flags)
    if n != count:
        raise ValueError(f"pem_fx: troca '{what}' achou {n} vez(es), esperado {count} (texto vanilla mudou?)")
    return new


def _num(v):
    s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _color_block(name, c):
    return (f"\t\t{name}\n\t\t{{\n\t\t\tRf = {_num(c[0])}\n\t\t\tGf = {_num(c[1])}\n\t\t\tBf = {_num(c[2])}\n"
            f"\t\t\tAf = 1\n\t\t}}")


def _recolor(text):
    """Troca as tres cores do material do particle_lightning.shader (o amarelo-verde do disruptor) pelo ciano PEM.
    A rampa de cor da particula NAO e cor (o shader le os canais como parametros) e fica como esta."""
    col = colors()
    for field, key in (("_centerColor", "center"), ("_outerColor", "outer"), ("_bloomColor", "bloom")):
        text = _sub(text, rf"^\t\t{field}\n\t\t\{{\n(?:\t\t\t[RGBA]f = [-0-9.E]+\n){{4}}\t\t\}}",
                    _color_block(field, col[key]), 1, field)
    return text


def _abs_paths(text, base):
    """File = <relativo> -> File = "./Data/<pasta resolvida>" (a copia mora em shots/bs_pem_fx/)."""
    def repl(m):
        rel = m.group(2).strip().strip('"')
        p = os.path.normpath(os.path.join(base, rel)).replace(os.sep, "/")
        if p.startswith(".."):
            raise ValueError(f"pem_fx: caminho {rel!r} sai do Data")
        return f'{m.group(1)}File = "{D}/{p}"'
    return _sub(text, r"^(\t+)File = (.+)$", repl, 2, "File (shader + textura)")


def _note(text, what):
    return "\n".join(f"// {ln}" for ln in what.split("\n")) + "\n" + text


def muzzle_arcs_text(t):
    """Arcos ciano da boca (disruptor_shoot_lightning recolorido): ARCS[t] arcos, escala ARC_SCALE[t], quantidade
    fixa (ScaleEmissionWithIntensity false: o orcamento da boca nao cresce com a intensidade)."""
    src, base = VENDORED["shoot_lightning"]
    txt = _abs_paths(_recolor(vendor_text("shoot_lightning")), base)
    lo, hi = ARCS[t]
    txt = _sub(txt, r"^\t\tMin = 10\n\t\tMax = 12$", f"\t\tMin = {lo}\n\t\tMax = {hi}", 1, "EmitPerOneShot")
    k = ARC_SCALE[t]
    txt = _sub(txt, r"^(\t+)FromValue = 0\.4\n(\t+)ToValue = 0\.6$",
               lambda m: f"{m.group(1)}FromValue = {_num(0.4 * k)}\n{m.group(2)}ToValue = {_num(0.6 * k)}", 1,
               "SetRandom scale")
    txt = _sub(txt, r"^ScaleEmissionWithIntensity = true$", "ScaleEmissionWithIntensity = false", 1,
               "ScaleEmissionWithIntensity")
    return _note(txt, f"Bullet Strike 2.0 (pem_muzzle_arcs_{t}): arcos ciano da boca da linha PEM. Copia de "
                      f"./Data/{src} "
                      f"(tools/vanilla_fx/pem/) com as cores do material trocadas pelo ciano PEM, {lo}-{hi} arcos e "
                      f"escala x{_num(k)}.")


def charge_arcs_text(side):
    """Arcos da carga da pesada (0,5 s antes do disparo): disruptor_shoot_lightning recolorido com o angulo travado
    para um dos canos (side 'a' = -20..20 graus, 'b' = 160..200 graus: o arco do quadro corre no eixo Y, o lateral da
    torre), CHARGE_PER_S por segundo."""
    src, base = VENDORED["shoot_lightning"]
    txt = _abs_paths(_recolor(vendor_text("shoot_lightning")), base)
    txt = _sub(txt, r"^\tEmitPerSecond = 0\n\tEmitPerOneShot\n\t\{\n\t\tMin = 10\n\t\tMax = 12\n\t\}",
               f"\tEmitPerSecond = {CHARGE_PER_S}\n\tEmitPerOneShot\n\t{{\n\t\tMin = 0\n\t\tMax = 0\n\t}}", 1,
               "EmitPerSecond/EmitPerOneShot")
    # o arco do disruptor_bolt_discharge.png corre no eixo Y do quadro (Offset Y 0,4 poe uma ponta no emissor): com o
    # angulo perto de 0 / 180 graus ele cruza de lado (eixo Y da torre = o vao entre os canos), nunca ao longo deles
    a = -20 if side == "a" else 160
    txt = _sub(txt, r"^(\t+)FromValue = 0d\n(\t+)ToValue = 360d$",
               lambda m: f"{m.group(1)}FromValue = {a}d\n{m.group(2)}ToValue = {a + 40}d", 1, "SetRandom rot")
    txt = _sub(txt, r"^(\t+)FromValue = 0\.3\n(\t+)ToValue = 0\.4$",
               lambda m: (f"{m.group(1)}FromValue = {_num(CHARGE_LIFE[0])}\n"
                          f"{m.group(2)}ToValue = {_num(CHARGE_LIFE[1])}"),
               1, "SetRandom lifetime")
    txt = _sub(txt, r"^ScaleEmissionWithIntensity = true$", "ScaleEmissionWithIntensity = false", 1,
               "ScaleEmissionWithIntensity")
    return _note(txt, f"Bullet Strike 2.0 (pem_charge_arcs_{side}): arcos ciano entre os canos da PEM pesada durante a "
                      f"carga de 0,5 s antes de cada disparo. Copia de ./Data/{src} (tools/vanilla_fx/pem/), cor PEM, "
                      f"{CHARGE_PER_S}/s, angulo de {a} a {a + 40} graus.")


def crackle_text(t):
    """Crepitar em voo (disruptor_bolt_lightning recolorido): CRACKLE[t] por segundo, escala CRACKLE_SCALE[t]."""
    src, base = VENDORED["bolt_lightning"]
    txt = _abs_paths(_recolor(vendor_text("bolt_lightning")), base)
    txt = _sub(txt, r"^\tEmitPerSecond = 60$", f"\tEmitPerSecond = {CRACKLE[t]}", 1, "EmitPerSecond")
    k = CRACKLE_SCALE[t]
    txt = _sub(txt, r"^(\t+)FromValue = 0\.4\n(\t+)ToValue = 0\.6$",
               lambda m: f"{m.group(1)}FromValue = {_num(0.4 * k)}\n{m.group(2)}ToValue = {_num(0.6 * k)}", 1,
               "SetRandom baseScale")
    return _note(txt, f"Bullet Strike 2.0 (pem_crackle_{t}): crepitar ciano da granada PEM em voo. Copia de "
                      f"./Data/{src} "
                      f"(tools/vanilla_fx/pem/), cor PEM, {CRACKLE[t]}/s, escala x{_num(k)}.")


# ============================================================================= efeitos proprios (tijolos do fxkit)
def flash_text(t):
    return FXK.blob(f"Bullet Strike 2.0 (pem_muzzle_flash_{t}): clarao cobre-ambar da boca da linha PEM (cobre = "
                    f"assinatura da familia), {_num(FLASH[t])} tiles.", FLASH[t], 0.08, 0, FLASH_COLOR, HOT,
                    scale=(0.6, 1.2), bucket="Upper2")


def light_text(t):
    return FXK.blob(f"Bullet Strike 2.0 (pem_muzzle_light_{t}): luz ciano-azul da boca no casco (palette.pem.hull, "
                    f"alfa 0,25: o casco branco nao vira mancha branca).", LIGHT[t], 0.15, 0, colors()["hull"],
                    LIGHT_RAMP, scale=(0.8, 1.15), light=True, bucket="Upper5")


def ring_text(t):
    size = RING[t] / SHIELD_MES[t]
    return FXK.textured_blob(f"Bullet Strike 2.0 (pem_ring_{t}): anel ciano no escudo atingido pela granada PEM, "
                             f"{_num(RING[t])} tiles = {_num(size)} x MediaEffectsScale {_num(SHIELD_MES[t])} do "
                             f"HitShield.", TEX_RING, size, 0.3, colors()["cyan"], RING_RAMP, scale=(0.3, 1),
                             bucket="Upper2")


def sizzle_text():
    return FXK.blob("Bullet Strike 2.0 (pem_sizzle): chiado ciano do dreno de bateria da granada PEM.", 1.0, 0.2, 0,
                    colors()["cyan"], HOT, scale=(0.7, 1.1), bucket="Upper2")


def fizzle_text():
    return FXK.blob("Bullet Strike 2.0 (pem_fizzle): estouro ciano pequeno da granada PEM abatida no ar.", 1.2, 0.15,
                    0, colors()["cyan"], HOT, scale=(0.6, 1.2), bucket="Upper2")


def all_files():
    """{nome: texto} de todos os arquivos de shots/bs_pem_fx/."""
    out = {}
    for t in TIERS:
        out[f"pem_muzzle_flash_{t}"] = flash_text(t)
        out[f"pem_muzzle_arcs_{t}"] = muzzle_arcs_text(t)
        out[f"pem_muzzle_light_{t}"] = light_text(t)
        out[f"pem_crackle_{t}"] = crackle_text(t)
        out[f"pem_ring_{t}"] = ring_text(t)
    out["pem_sizzle"] = sizzle_text()
    out["pem_fizzle"] = fizzle_text()
    out["pem_charge_arcs_a"] = charge_arcs_text("a")
    out["pem_charge_arcs_b"] = charge_arcs_text("b")
    return out


def write(out, header):
    """Gancho do build_mod (FX): grava shots/bs_pem_fx/*.rules (tambem com --no-art: so texto)."""
    head = "\n".join(f"// {ln}" for ln in header.split("\n"))
    for name, text in sorted(all_files().items()):
        out.text(f"{DIR}/{name}.rules", head + "\n" + text)


# ============================================================================= referencias (para o bsgen.pem)
def ref(name, frm="shot"):
    return FXK.ref(DIR, name, frm)


def muzzle_refs(t, frm="part"):
    """Boca da arma do tier t: clarao cobre, arcos ciano e luz de casco (caminhos sem &<>; guns.fire_media poe)."""
    return [ref(f"pem_muzzle_flash_{t}", frm), ref(f"pem_muzzle_arcs_{t}", frm), ref(f"pem_muzzle_light_{t}", frm)]


def crackle_ref(t, frm="shot"):
    return ref(f"pem_crackle_{t}", frm)


def ring_ref(t, frm="shot"):
    return ref(f"pem_ring_{t}", frm)


def sizzle_ref(frm="shot"):
    return ref("pem_sizzle", frm)


def fizzle_ref(frm="shot"):
    return ref("pem_fizzle", frm)


def charge_refs(frm="part"):
    return [ref("pem_charge_arcs_a", frm), ref("pem_charge_arcs_b", frm)]


def shield_mes(t):
    return SHIELD_MES[t]


def hull_mes(t):
    return HULL_MES[t]


# ============================================================================= conferencia
def selfcheck(mod_dir, spec):
    """Arquivos de shots/bs_pem_fx escritos; orcamento da boca (<= 4 / 6 / 8 particulas); luzes no casco branco
    (particle_light_white <= 0,5); nenhuma cor vermelha nos raios; copias sem caminho relativo e sem &/SW_*; as pecas
    PEM escritas tocam a boca da familia; a pesada (com a carga) referencia os arcos de carga."""
    probs = []
    files = all_files()
    for name in files:
        p = os.path.join(mod_dir, DIR, f"{name}.rules")
        if not os.path.isfile(p):
            probs.append(f"{DIR}/{name}.rules nao foi escrito")
            continue
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        if "&/SW_" in text:
            probs.append(f"{DIR}/{name}.rules cita global do SW (&/SW_*)")
        for m in re.finditer(r"^\t+File = (.+)$", text, re.M):
            v = m.group(1).strip().strip('"')
            if not (v.startswith("./Data/") or v.startswith("../bs_fx_tex/")):
                probs.append(f"{DIR}/{name}.rules: caminho relativo ao vanilla {v!r}")
    for t in TIERS:
        lo, hi = ARCS[t]
        n = 1 + hi + 1
        if n > BUDGET[t]:
            probs.append(f"boca pem {t}: {n} particulas > {BUDGET[t]}")
    w = FXK.particle_light_white(colors()["hull"], LIGHT_RAMP)
    if w > 0.5 + 1e-9:
        probs.append(f"pem_muzzle_light: canal mais fraco no casco branco {w:.2f} > 0,5")
    col = colors()
    for k in ("center", "outer", "bloom", "cyan"):
        r, g, b = col[k][:3]
        if r > g or r > b:
            probs.append(f"cor {k} da familia PEM puxa para o vermelho: {col[k]}")
    # pecas PEM escritas: boca da familia e carga da pesada
    parts = os.path.join(mod_dir, "parts")
    for short, t in (("bs_pem_light", "s"), ("bs_pem_medium", "m"), ("bs_pem_heavy", "l")):
        p = os.path.join(parts, short, f"{short}.rules")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        for r in muzzle_refs(t, "part"):
            if r not in text:
                probs.append(f"{short}: sem a boca da familia {r}")
        if t == "l" and "ChargeArcs" in text:
            for r in charge_refs("part"):
                if r not in text:
                    probs.append(f"{short}: carga sem {r}")
    return probs
