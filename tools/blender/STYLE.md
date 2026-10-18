# Bullet Strike: 3D art style and model contract

This guide applies to every 3D sprite in the mod. The reference model is the **76 mm Naval Automatic
Cannon** (`tools/blender/parts/bs_naval_76.py`), which the user approved with the words "exactly the style I want
for the mod's weapons". Every new weapon must look like it belongs to the same family.

Rendered references (open them before you start):
- `docs/preview/3d/naval76_ampliado.png` (top view, 4x)
- `docs/preview/3d/naval76_no_jogo.png` (in-game scale 1x and 3x)
- `docs/preview/3d/naval76_disparo.gif` (firing animation)
- `docs/preview/3d/naval76_perspectiva.png` (3/4 view of the model)

Background reading: the style study of the "Redline Orbital Heavy Industries" mod that the user asked us to match is
`/tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/redline/STYLE_NOTES.md`.
Game graphics conventions are in
`/tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/notes/08_graphics_conventions.md`.

---

## 1. Visual language (mandatory)

1. **Dark core plus light armor.** Each turret head is a near-black mechanical core (`M["core"]`,
   `M["core_mid"]`) wrapped in separate light-grey armor shards (`M["armor"]`). Dark gaps of 0.05–0.15 tile run
   between the shards. The head should read as an exoskeleton, not a box.
2. **Angular, faceted, aggressive.** Silhouettes are chamfered octagons and wedges that point forward, with
   stepped notches. Avoid perfect circles on the roof layer; the turret ring is the only exception. Use
   `B.shard()` (chamfered plate plus a raised inner panel, the double bevel) for every armor piece.
3. **Mirror symmetry** along the barrel axis. Asymmetry may come only from small details (for example an ammo box on
   one side, if the art direction asks for it).
4. **Recurring elements** that give the family its identity. Adapt them to each weapon's size:
   - forward-sweeping "claws" or "blades" that grip the barrel roots;
   - a raised central spine with a sensor window (dark recess with a small glowing slit);
   - a rear vent bay (dark recess, louvers, a row of 3–6 amber pips);
   - mechanical greebles **only in the dark core gaps**: magazine drums with lit counters, feed chutes, pistons,
     cables and modules;
   - panel lines cut into the armor (`B.cut` with thin boxes), LED slots cut into armor (`Mo.slot_with_pips`).
5. **Barrels** are long faceted sleeves (8-sided cylinders, flat shading) with a dark channel cut along the top,
   2–3 collars and a muzzle brake or flash hider. The root sits in a dark cradle or mantlet. A rotary weapon has a
   cluster of barrels plus a front clamp ring.
6. **Small, scarce emissives.** Glowing area should be under 1–2 % of the sprite. LEDs sit in **dark recesses**,
   never directly on white armor. Use `M["glow"]` (strong), `M["glow_dim"]` (soft) and `M["ember"]` (heat, very
   dim). No logos, no large text and no hazard stripes on the turret.
7. **Factory-clean finish.** No rust and no visible dirt. Wear and grime come only from the materials in
   `Mo.mats()`.
8. **Detail density.** At 64 px/tile there should be a structural break (gap, step, groove or slot) every
   0.3–0.5 tile. No flat area larger than about 1x1 tile without a groove or inset.
9. **Scale with size.** Small weapons (1x1, 1x2, 2x2) are compact, with 1–2 tiers of shards and big readable
   shapes, because detail disappears at 64 px. Large weapons (4x5 and up) add tiers of shards, more core modules
   and more LEDs, but keep the same kinds of shapes.

### Colors and accents
- Use **only** the palette in `Mo.mats(accent)`: light naval-grey armor, dark core, steel. Ignore the colors
  listed in the spec's `art_direction` (olive, rust-red, sand and so on). The user approved a single family
  look. Take only the **silhouette, barrel count/style and animations** from `art_direction`.
- Accent (light color) per weapon: `"amber"` by default; `"cyan"` for plasma weapons (Boitatá, Curupira);
  `"green"` for the nuclear howitzer (Boiúna). A small red radar light (`M["red"]`) is allowed on the CIWS.
- The hull roof is **pure green** (`B.mat_roof_green()`); the game replaces green with the ship's paint. Anything
  that should not be painted (vents, hatches, metal) uses non-green materials.

## 2. Coordinates and conventions

- 1 Blender unit = 1 tile = 64 px. The camera looks straight down.
- **Head and barrel:** origin at the turret pivot, **+X = right, +Y = forward (barrel direction), +Z = up**.
  The barrel is modeled with its **root at y = 0** and its muzzle at y = L, centered at x = 0 (height z ≈ 0.4–0.6).
- **Roof and floor:** coordinates centered on the part (x in [-w/2, w/2], y in [-h/2, h/2], +Y = front of the
  part). Pivot in part coordinates (x right, y **down**) converts as `px = pivot[0] - w/2`, `py = h/2 - pivot[1]`.
- The turret sprite is a square of side `turret_box` centered on the pivot. **The whole head must fit inside
  that square** (keep a margin of about 0.03).
- The barrel sprite covers from `-pad` to `L` (pad = recoil space) and is `width` wide. The whole barrel,
  including the muzzle brake, must fit inside that width.
- **Turret/barrel overlap:** within the same layer the game does not guarantee draw order. Where the barrel root
  overlaps the head (the cradle/mantlet), make it look right **both with the barrel over the head and under it**.
  Make that region dark (core_mid/core), and do not let the barrel cover white armor.

## 3. Model contract (`tools/blender/parts/<short_id>.py`)

```python
import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_xxx",
    "kind": "gun",                     # deck turrets (weapons and defenses)
    "size": [w, h],                    # MUST match the spec (tools/spec/bullet_strike_spec.json)
    "pivot": [x, y],                   # part coordinates (x right, y down), in tiles
    "turret_box": 2.9,                 # side of the turret sprite
    "ring_r": 1.3,                     # turret ring radius drawn on the roof/floor
    "accent": "amber",
    "collider": 1.3,                   # optional: turret collision radius (default 0.45 * box)
    "barrels": {
        "ys": [0.0],                   # lateral offset of each VISIBLE barrel (+ = right). The COUNT is fixed per weapon (table below)
        "root": 0.88,                  # pivot -> barrel root distance
        "length": 2.6,                 # root -> muzzle
        "width": 0.46,                 # barrel sprite width (tiles)
        "pad": 0.30,                   # recoil space behind the root
        "anim": "recoil",              # "recoil" | "spin" | "static"
        "recoil": [0.26, 0.18, 0.10, 0.04],   # recoil per frame (tiles), first = shot
        "heat": [1.0, 0.9, 0.78, 0.64, 0.5, 0.36, 0.22, 0.1],  # heat glow per frame (cools down afterwards)
        "interval": 0.06,              # seconds per frame
        # for anim == "spin": "spin_frames": 3 (barrel(M, L, T, phase) with phase in [0,1) = fraction of the
        # angle between two barrels; the renderer asks for phases 1/4, 2/4, 3/4 and 0 for rest)
    },
    "turret_anim": {"frames": 8, "interval": 0.1},   # optional: looping animation of the head (radar, lights)
    "lights": [{"at": [x, y], "size": 1.4, "color": [255, 120, 30], "z": 0.8}],  # dynamic lights (head coordinates)
    "preview_pattern": "single",       # GIF preview: single | alternate | pairs | volley | rotary
}

def head(M, T="head", phase=0.0): ...        # turret head; phase in [0,1) when turret_anim exists
def barrel(M, L, T="barrel", phase=0.0): ... # ONE barrel (or the rotary cluster); root at y=0
def roof(M, T="roof"): ...                   # optional (default: Mo.hull_roof)
def floor(M, T="floor"): ...                 # optional (default: Mo.hull_floor, with crew seats)
```

Rules:
- Every rendered object receives the tag passed in `T` (`tags=(T,)`). Barrel parts that should glow when hot (sleeve, brake,
  collars) receive `tags=(T, "hot")`.
- **Never** give tags to boolean cutters (`B.cut` handles them).
- The number of barrels in `ys` must equal the table (the build fails otherwise):

| weapon | size | crew | visible barrels (`ys`) | anim | pattern | accent |
|---|---|---|---|---|---|---|
| bs_lmg (Marimbondo) | 1x1 | 1 | 1 | recoil | single | amber |
| bs_hmg (Mangangá) | 1x2 | 1 | 2 | recoil | alternate | amber |
| bs_autocannon_20 (Carcará) | 2x2 | 1 | 2 | recoil | alternate | amber |
| bs_flak_light (Tatu) | 2x2 | 1 | 2 | recoil | alternate | amber |
| bs_quad_hmg (Saci) | 2x2 | 2 | 4 | recoil | pairs (1+3 / 2+4) | amber |
| bs_minigun (Cigarra) | 2x3 | 2 | 1 (6-barrel cluster) | spin | rotary | amber |
| bs_naval_76 (Tambor) | 3x4 | 3 | 1 | recoil | single | amber |
| bs_plasma_gatling (Boitatá) | 2x3 | 2 | 1 (4-barrel cluster) | spin | rotary | cyan |
| bs_ciws (Tamanduá) | 3x3 | 2 | 1 (4-barrel cluster) | spin | rotary | amber (+red radar) |
| bs_rotary_30 (Furacão) | 4x4 | 4 | 1 (7-barrel cluster) | spin | rotary | amber |
| bs_naval_155 (Trovão) | 4x5 | 5 | 2 | recoil | alternate | amber |
| bs_plasma_heavy (Curupira) | 4x5 | 4 | 2 | recoil | alternate | cyan |
| bs_flak_heavy (Pororoca) | 4x4 | 4 | 2 | recoil | alternate | amber |
| bs_nuke_howitzer (Boiúna) | 5x6 | 6 | 1 | recoil | single | green |
| bs_naval_406 (Mapinguari) | 6x7 | 10 | 3 | recoil | volley | amber |

- Placement: the head usually covers the front rows; the **back row** of the part (where the crew sits) usually
  stays visible on the roof (hatch, vents). The crew is placed automatically in the back row; do not set `crew_pos`.
- Recoil should be proportional to the caliber: small MG 0.04–0.08 tile, autocannon 0.1–0.15, 76 mm 0.26,
  155 mm 0.4, 406 mm 0.6, howitzer 0.7. Heat glow suits cannons (76 mm and up) and plasma (cyan glow via the
  `ember`/`glow_dim` materials). Light MGs should use little or no heat.

## 4. Commands

```bash
PY=/tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/blendenv/bin/python
cd /home/user/Cosmoteer
# quick iteration (low quality), output to a draft folder:
$PY tools/blender/render_part.py bs_xxx --quick --preview --out /tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/art3d/draft_bs_xxx
#   (--only turret | barrel | hull renders just one piece)
# final (goes to art3d/bs_xxx/, which the mod uses):
$PY tools/blender/render_part.py bs_xxx --preview
# check that the mod builds and validates:
python3 tools/build_mod.py --no-art && python3 tools/rules_lint.py --mod BulletStrike --vanilla /tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/repos/vanilla
```

The `--preview` flag writes `preview_ingame.png` (1x and 3x) and `preview_fire.gif` to the output folder. **Look at the
images** (Read tool) on every iteration. The machine has only 4 CPUs, so render the final version once.

## 5. Quality checklist (critique yourself before finishing)

- [ ] At 1x (64 px/tile) the silhouette reads well and differs from the other weapons (see `art_direction`).
- [ ] It looks like the 76 mm family: dark core plus light shards with gaps, claws, spine, vent bay, LEDs in recesses.
- [ ] It looks aggressive: forward-pointing shapes and chamfers. Nothing looks "boxy" or "toy-like".
- [ ] Every armor piece has a double bevel; there are panel lines; no big flat empty areas.
- [ ] Emissives are small; heat is orange (not white); plasma is cyan; nuclear is green.
- [ ] The head fits in the `turret_box`; the barrel fits in `width`; nothing is clipped at the sprite edges.
- [ ] The barrel root/cradle looks right with either draw order.
- [ ] The roof is green with non-green details; the floor has seats/consoles at the crew positions and visible
      magazine racks.
- [ ] `python3 tools/build_mod.py --no-art` plus `rules_lint` give 0 errors.

## 6. Factories (`kind: "factory"`)

Reference (simple first version): `tools/blender/parts/bs_factory_mag_std.py`.

```python
PART = {"id": "rafaeltessaro.bs_factory_xxx", "kind": "factory", "size": [w, h], "accent": "amber",
        "machine_frames": 4, "machine_interval": 0.12}
def floor(M, T="floor"): ...                  # opaque interior floor (whole part)
def machine(M, T="machine", phase=0.0): ...   # machinery (animated frame; phase in [0,1)); transparent where empty
def roof(M, T="roof"): ...                    # green roof + unpainted details
```
- Coordinates centered on the part, +Y = front of the part (image top), 1 unit = 1 tile.
- **Grid layout (fixed by the rules, tools/bsgen/factory.py):**
  - 2x2 (Magazine Press): top row = machinery (blocked to crew). Bottom row: INPUT at the left tile, OUTPUT at the
    right tile.
  - 3x3 (other factories, vanilla `factory_he` layout): top row + center tile (1,1) = machinery. Tiles (0,1)
    left and (2,1) right = INPUTS (the 2nd input on the right). The whole bottom row (y = 2) = OUTPUT.
  - The game draws the resource stacks on top of the input/output tiles (`doodads_low` layer). The floor
    should show marked "pads" there. Keep those tiles free of machinery.
- The machinery must look like the same family: light chamfered shells with a double bevel, dark core, LEDs in
  recesses, panel lines. The animation must show work (press ram, conveyor, spinning rotor, pulsing light...).
  Theme per factory: Magazine Press (packs bullets), AP Magazine Press (tristeel tips), EMP Magazine Charger (copper coils and
  electric glow), Plasma Cell Factory (cyan, cell tanks), Nuclear Shell Foundry (green, radiation-shielded hot cell).
- Accent: amber (standard/AP press), blue (EMP), cyan (plasma), green (nuclear).

## 7. Ammunition (`kind: "resource"`)

Reference: `tools/blender/parts/bs_mag_std.py`.

```python
PART = {"id": "rafaeltessaro.bs_xxx", "kind": "resource", "accent": "amber", "unit_scale": 0.44,
        # optional: "stack_layout": {k: [(x, y, z), ...]}, "stack_rot": [...], "icon_scale": 0.8}
def item(M, T="item"): ...   # ONE unit centered on the origin, fitting in ~1x1 (z up to ~0.5)
```
- The renderer produces `stack_1..N` (N = `max_stack_size` from the spec) at 64x64, the `nugget` (loose item,
  with normals), `icon.png` 64x64 and `overlay.png` (white silhouette 128x128).
- The item must be recognizable at 64 px and 1/2 tile: a clear silhouette, a light shell + dark core, and a
  distinctive detail per type: Standard (amber LEDs, visible brass), AP/APHE (tristeel tips, blue-white band),
  EMP (blue coils/glow), plasma cell (glowing cyan cylinder), nuclear shell (large shell, green band, radiation
  symbol made of 3 wedges).
- Stacks of 5-6 must not look like a jumble: use an organized 2-layer arrangement (`stack_layout`).
