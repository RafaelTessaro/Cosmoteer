# Bullet Strike deck missile launchers: final design

- **Machine-readable version:** `MISSILE_SPEC.json` (same folder).
- **Generator:** `final/model.py` + `final/gen_missile_spec.py` in this folder (run `python3 -I final/gen_missile_spec.py`). Every number below comes from the model; the script asserts every hard limit from the three verdicts and aborts if one fails.
- **Hard limits:** 95 checks, 95 pass, 0 fail (the generator aborts on any failure).

## 1. Design in one paragraph

Tiro, porrada e bomba, with A's engine and A's numbers. Three crewed, power-free deck launchers - RAM micro-missile box (early), twin octagonal pods with a sensor dome (mid), headless quad battery with 48 tips (late) - run one loop: crew fill an internal magazine per resource family, a crewed autoloader fills the visible cells, a full rack ripples one dramatic salvo, then the launcher reloads. Sustained DPS sits exactly on the mod's tier bands; the drama is in the alpha and in the missiles: the Piranha school, the Carrapato countdown, napalm that keeps burning, EMP, the Boto decoy torpedo and the Iara nuke that must be masked. Overclock buys reload speed with heat, vented missiles and cook-off risk; the endgame battery is very powerful and very costly (5x6, 8 crew, 18 CP, 77000 cr, 2 per ship in the nuclear pool). Only vanilla component types and vanilla missile parts on the default path; every risky mechanic has a fallback that changes no number.

**Base and grafts.** BASE = Design A's launcher core (Model B latch, crewed autoloader, ModeSwitchDelay, DryFlush, safe napalm, untargetable limpet, heat per part loaded) and A's numeric spine (bands, OC <= 550, 300/400/600 m, 1500 drain per EMP part) - the two judges that weigh engine risk and balance both picked it (8.5 / 8.0). GRAFTED from B (fidelity 8.5): the stage-to-reference roster (RAM box -> twin octagonal pods + dome -> quad 3x4 battery), the Mula-sem-Cabeça endgame, the Piranha parameters (25 m, InheritVelocity false, weak late homing), the Iara in bs_limit_nuke with no OC, one magazine per resource family, per-family cook-off, the complete turret sketch and CrewKillChance on the limpet. GRAFTED from C: the micro-missile cassette (as Burst 2), the Boto decoy torpedo, the OC vent cost (scaled per cell), magnet + spacing children, the buzz-droid limpet charge, threshold MultiResourceStorage toggles, the isolated Repeating variant pattern and the counter matrix. NEW here: per-mode ModeSwitchDelay, tick-aligned ripples, heavy 16-unit layout on the Mula, children HP pool >= carrier HP, Iara masking timing.

## 2. Constraints honoured

- Cosmoteer 0.30.4 + 0.30.5 RC4: vanilla component types present in 0.30.3 and RC4 only; literals everywhere; no DefaultWeaponCoverage / MatchWeaponCoverage / CoverageSectorArc / UseContiguity / AllowVertexContiguity / structural-retention globals / APPLIED_HEAT_PER_MISSILE; HealthFactor, never ScaleHealth.
- Deck turrets only: ProhibitedBy [tall] + tall ring, no ProhibitAbove, TurretCollider { IsHigh = true; ChainedTo = Turret }, pod on roof_doodads, cell overlays on roof_turrets; every missile/child/decoy/charge Hit has FriendlyShipLowCollisions = false, FriendlyShipHighCollisions = false and SourcePartCollisionDelay.
- Crew only, no power: no battery storage, TypeCategories without uses_power; IsOperational = [PowerToggle (on/off), PartCrew, ScorchedToggle (+ OC reset)].
- Internal stock refilled by crew: one magazine per resource family + ResourceConsumer (Weapon_Supply), outside the toggled blocks.
- Crewed-only automatic reload: Autoloader OperationalToggle contains IsOperational (PartCrew).
- Overclock shortens reload with real costs: Interval / 1.5; heat per part loaded + constant heat; vent; OC reset; faster magazine drain; cook-off chain; never on the nuclear reload; early OC designed but disabled (mod rule).
- SW:ACD compatible: TargetCategory 'missile' everywhere, own toggle bs_missile_type, vanilla parts shared with SW, no SW types/fields/references except one isolated build-flag variant file.

## 3. The three launchers

|  | Tocandira (early) | Caipora (mid) | Mula-sem-Cabeça (late) |
|---|---|---|---|
| ID | `rafaeltessaro.bs_msl_box` | `rafaeltessaro.bs_msl_twin` | `rafaeltessaro.bs_msl_quad` |
| Name (en / pt-BR) | Deck Micro-Missile Box / Caixa de Micromísseis de Convés | Twin-Pod Deck Missile Launcher / Lançador de Mísseis de Convés de Casulo Duplo | Quad-Pod Heavy Missile Battery / Bateria Pesada de Mísseis Quádrupla |
| Size / crew / CP / HP | 2x2 / 1 / 2 / 8000 | 3x3 / 2 / 5 / 12000 | 5x6 / 8 / 18 / 42000 |
| Build cost | steel 60, coil 16 (3100 cr) | steel 100, coil2 20, tristeel 8, processor 1 (12600 cr) | steel 400, coil2 110, tristeel 100, processor 4, enriched_uranium 2 (77000 cr) |
| Visible cells | 12 tubes (6 twin-tube cassettes) | 16 (2 pods x 8, 3-2-3) | 48 (4 pods x 3x4) |
| HE salvo / ripple | 12 in 0.733 s / Turret FireInterval = 4/30 (tick-aligned like point_defense 2/30); cassette tube B fires BurstDelay = 2/30 after tube A | 16 in 2.0 s / Turret FireInterval = 4/30 (tick-aligned like point_defense 2/30) | 48 in 3.133 s / Turret FireInterval = 2/30 (tick-aligned like point_defense 2/30) |
| HE reload / cycle | 1.39 s per cassette / 9.073 s | 1.06 s per missile / 18.96 s | 0.264 s per missile / 15.805 s |
| Magazines (parts) | he 12, thermal 12 | he 64, thermal 64, emp 64 | he 192, thermal 192, emp 96, nuke 32 |
| Selector (bs_missile_type) | 0 Muriçoca, 3 Taturana-mirim | 0 Jararaca, 1 Piranha, 2 Carrapato, 3 Taturana, 4 Poraquê, 5 Boto | 0 Jararaca, 1 Piranha, 2 Carrapato, 3 Taturana, 4 Poraquê, 5 Boto, 6 Iara |
| Range | 300 m | 400 m (torpedo 400) | 600 m |
| Arc / traverse / threshold | 360 / 120 deg/s / 30 deg | 360 / 75 deg/s / 25 deg | 360 / 40 deg/s / 20 deg |
| Ring / collider | 1 / 0.85 | 1 / 1.25 | 2 / 2.1 |
| HE eff. DPS per tile (OC) | 264.5 (381.4, disabled) | 328.2 (467.6) | 379.6 (518.1) |
| Overclock | Furious Swarm / Enxame Furioso (disabled) | Caipora's Fury / Fúria da Caipora | Stampede / Estouro da Boiada |
| Per-ship limit | none | none | 2 (bs_limit_nuke, shared with Boiúna) |
| Cook-off (HE family, full) | 11500 + 3800 structural | 61200 + 20400 structural | 183600 + 61200 structural |

### 3.1 Tocandira (early): Deck Micro-Missile Box / Caixa de Micromísseis de Convés

- **Concept.** Early RAM-style micro-missile box: the gunner cranks a 2x2 deck box around, and 12 micro-missiles hiss out in 0.73 s as six twin-tube cassettes fire pair by pair ('tsk-tsk ... tsk-tsk'), each cassette spitting a small flash forward and a puff of backblast over the deck.
- **Base part / categories.** base_med_part_terran (no overclock; OC wiring kept in data, disabled); TypeCategories [weapon, is_crewed, uses_missiles, uses_launcher_parts].
- **Credits per effective DPS:** 2.93. **Emitter components:** 12.

| Mode | Codename | Layout | Missiles/salvo | Ammo per missile | Reload s/unit | Salvo s | Cycle s | Eff/tile | x HE | Stock (missiles / s of fire) | OC eff/tile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| he | Muriçoca | cassette | 12 | 1 missile_part_he per cassette = 2 micro-missiles (0.5 part each) | 1.39 | 0.733 | 9.073 | 264.5 | 1.0 | 36.0 / 27.2 | 381.4 |
| napalm | Taturana-mirim | cassette | 12 | 1 missile_part_thermal per cassette = 2 micro-missiles (0.5 part each) | 1.39 | 0.733 | 9.073 | 99.2 | 0.375 | 36.0 / 27.2 | 143.0 |

**Overclock - Furious Swarm / Enxame Furioso (designed, DISABLED by default).** Designed but DISABLED (mod rule: overclock only on mid/late weapons). Enabling = switch the base part to base_med_part_terran_overclock and register tech rafaeltessaro.bs_msl_box-overclock; every number below is already in the data.

- Effect: Autoloader_k Interval / 1.5 (EMP / 1.2 so its OC shield rate stays <= 880); ModeSwitchDelay_k Duration / same factor; ripple, damage, range and missile unchanged.
- Heat: 200 per part loaded + 30/s -> HE 220.7 avg / 245.8 peak heat/s (0.2 / 0.22 radiators).
- Vent per salvo (parts): he 0, napalm 0.
- heat is produced when the AUTOLOADER moves a missile into the rack (factory_he Overclock_ConversionHeatProducer pattern with Trigger = Autoloader_k): heavy munitions pay for their weight, heat follows the extra loading work
- VENT: every time a rack latches full while overclocked, CELLS/16 missiles' parts are vented from the family magazine (ResourceChange, negative Amount, Trigger = RackFullTrigger_k; thruster_boost precedent); torpedo and nuclear modes exempt; salvos under 16 missiles (Tocandira) vent nothing
- OverclockReset 3 s downtime when OC is switched off (base_part_overclock, inherited)
- magazine empties faster: HE crew trips 3.97 -> 5.72/min, HE factories 0.2 -> 0.29
- cook-off chain: heat the network cannot take overflows onto the launcher's own tiles (OverheatEffects) -> >= 350 heat rolls fire -> scorched -> the stock-scaled family cook-off fires
- thermal ports must stay reachable (same port geometry as our 3x3 CIWS / 5x6 Boiúna)
- Visual signature: spine slit flickers orange, 2 steam puffs per load.

**Cook-off at full stock:** missile_part_he: DeathEffects FactorHitEffectsWith = Stock_HE: ExplosiveDamage 11500 r3.5 (fire 50 %/1000, CrewKillChance 30 %) + 3800 structural; 18 parts at full = 850.0 per part; missile_part_thermal: GridStatusApplication cosmoteer.heat pool 4500 on own tiles (Filter { Self = true }, vanilla thermal-launcher dump).

**Art.** Compact RAM-style box (ref 1) on a short armored yoke: one chamfered box pod pitched 35 deg, dark recessed 4x3 tube grid read as 6 twin-tube cassettes; forward claws hug the box sides; raised spine with an amber IR-seeker slit; open-backed tubes with louvers (backblast); rear vent bay with 3 amber pips. Reads at 64 px as a 'box of holes'.

- Pods: 1 box pod (6 cassettes x 2 tubes). Cell grid: 4 cols x 3 rows = 12 tubes, pitch 0.26 x 0.22 tile (foreshortened), tube radius 0.09, face 1.1 x 0.7 tile; cassettes = horizontal pairs.
- Layouts: `cassette` = 6 twin-tube cassettes (12 visible tubes); rack counts cassettes; overlay levels 0..6 (pairs).
- Animations: turret traverse 120 deg/s (engine); overlay pairs empty LIFO per launch (ResourceSprites on ReadyRack_k, layer roof_turrets over the pod on roof_doodads); per-tube launch flash (missile_launcher_shoot_flash, Upper1, 60 %) + backblast puff (chaingun_shoot_smoke, Upper) at the box rear; reload: cassette pairs refill one by one (launcher_reload_0x.wav via TriggeredEffects { Trigger = Autoloader_k }); rack full: launcher_ready sound + the 3 vent pips light (ToggleEffects on the latch); spine slit pulse loop 8 frames x 0.12 s; no pod recoil (keeps overlays aligned).
- PART meta (`tools/blender/parts/bs_msl_box.py`, new `kind: "launcher"`): `{"kind": "launcher", "size": [2, 2], "pivot": [1.0, 0.95], "turret_box": 1.9, "ring_r": 0.8, "collider": 0.85, "cell_style": "pitched", "pitch_deg": 35, "accent": "amber", "cells": {"pods": [{"center": [0.0, 0.32], "cols": 4, "rows": 3, "pitch": [0.26, 0.22]}], "tube_r": 0.09, "units": "pairs", "fill_order": "row_major_bottom_up"}, "looks": ["he", "napalm"], "backblast": [[0.0, -0.55]], "preview_pattern": "ripple"}`

### 3.2 Caipora (mid): Twin-Pod Deck Missile Launcher / Lançador de Mísseis de Convés de Casulo Duplo

- **Concept.** Mid twin-pod launcher: two octagonal pods with visible warheads flank an armored sensor dome; a salvo is a 2 s drum-roll of 16 missiles, right pod then left, nose bands showing the selected warhead; in Boto mode each pod face carries one fat capped torpedo.
- **Base part / categories.** base_med_part_terran_overclock; TypeCategories [weapon, is_crewed, uses_missiles, uses_launcher_parts, uses_emps].
- **Credits per effective DPS:** 4.27. **Emitter components:** 82.

| Mode | Codename | Layout | Missiles/salvo | Ammo per missile | Reload s/unit | Salvo s | Cycle s | Eff/tile | x HE | Stock (missiles / s of fire) | OC eff/tile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| he | Jararaca | fine16 | 16 | 2 missile_part_he | 1.06 | 2.0 | 18.96 | 328.2 | 1.0 | 48.0 / 56.9 | 467.6 |
| cluster | Piranha | fine16 | 16 | 2 missile_part_he | 1.06 | 2.0 | 18.96 | 295.4 | 0.9 | 48.0 / 56.9 | 420.8 |
| limpet | Carrapato | fine16 | 16 | 2 missile_part_he | 1.06 | 2.0 | 18.96 | 328.2 | 1.0 | 48.0 / 56.9 | 467.6 |
| napalm | Taturana | fine16 | 16 | 2 missile_part_thermal | 1.06 | 2.0 | 18.96 | 140.6 | 0.429 | 48.0 / 56.9 | 200.4 |
| emp | Poraquê | fine16 | 16 | 2 missile_part_emp | 1.06 | 2.0 | 18.96 | 121.9 | 0.371 | 48.0 / 56.9 | 143.3 |
| torpedo | Boto | torpedo2 | 2 | 6 missile_part_he | 4.65 | 0.133 | 9.433 | 282.7 | 0.861 | 12.7 / 59.7 | 421.1 |

**Overclock - Caipora's Fury / Fúria da Caipora.** The loader governors are wired open - pods reload in 2/3 of the time while the dome eye burns orange.

- Effect: Autoloader_k Interval / 1.5 (EMP / 1.2 so its OC shield rate stays <= 880); ModeSwitchDelay_k Duration / same factor; ripple, damage, range and missile unchanged.
- Heat: 425 per part loaded + 100/s -> HE 1122.0 avg / 1302.8 peak heat/s (1.02 / 1.18 radiators).
- Vent per salvo (parts): he 2, cluster 2, limpet 2, napalm 2, emp 2, torpedo 0.
- heat is produced when the AUTOLOADER moves a missile into the rack (factory_he Overclock_ConversionHeatProducer pattern with Trigger = Autoloader_k): heavy munitions pay for their weight, heat follows the extra loading work
- VENT: every time a rack latches full while overclocked, CELLS/16 missiles' parts are vented from the family magazine (ResourceChange, negative Amount, Trigger = RackFullTrigger_k; thruster_boost precedent); torpedo and nuclear modes exempt; salvos under 16 missiles (Tocandira) vent nothing
- OverclockReset 3 s downtime when OC is switched off (base_part_overclock, inherited)
- magazine empties faster: HE crew trips 10.13 -> 15.33/min, HE factories 0.51 -> 0.77
- cook-off chain: heat the network cannot take overflows onto the launcher's own tiles (OverheatEffects) -> >= 350 heat rolls fire -> scorched -> the stock-scaled family cook-off fires
- thermal ports must stay reachable (same port geometry as our 3x3 CIWS / 5x6 Boiúna)
- Visual signature: dome eye turns orange, vent ember sprite, launch flash 120 %.

**Cook-off at full stock:** missile_part_he: DeathEffects FactorHitEffectsWith = Stock_HE: ExplosiveDamage 61200 r5 (fire 50 %/1000, CrewKillChance 30 %) + 20400 structural; 96 parts at full = 850.0 per part; missile_part_thermal: GridStatusApplication cosmoteer.heat pool 24000 on own tiles (Filter { Self = true }, vanilla thermal-launcher dump); missile_part_emp: ExplosiveResourceDrain battery 57600 r12 (vanilla EMP launcher death pattern).

**Art.** Wide 'two fists' head (refs 3 + 2): twin chamfered OCTAGONAL pods flanking a central armored dome with one amber sensor-eye slit (ref 2's eye, recoloured to the family accent), forward claw blades gripping the pods, four splayed feet drawn on the turret ring (ref 3's four-leg base), rear magazine hatch and vent bay with 5 amber pips.

- Pods: 2 octagonal pods, mirror-symmetric. Cell grid: 8 cells per pod in a 3-2-3 pattern, pitch 0.24 tile, tube radius 0.085, pods pitched 35 deg; torpedo look = one capped torpedo nose per pod face.
- Layouts: `fine16` = 16 cells: 2 octagonal pods x 8 (3-2-3); per-pod ResourceSprites RangeLow/RangeHigh 0-8 / 8-16, 9 levels each; `torpedo2` = 2 torpedo cassettes, one capped torpedo nose covering each pod face; per-pod 2 levels (0/1).
- Animations: turret traverse 75 deg/s; per-pod overlays (2 x ResourceSprites on one rack, RangeLow/RangeHigh), LIFO, right pod empties first; per-cell launch flash + backblast (Upper buckets), screen shake 0.01 per launch; nose bands per look: HE amber, Piranha yellow petal cap, Carrapato red clamp ring, Taturana orange cap, Poraquê blue coil band, Boto white cap; dome eye blink loop (turret_anim 8 frames x 0.12 s); eye turns orange and vent embers glow under overclock (sprite toggled by IsOverclocked); no pod recoil.
- PART meta (`tools/blender/parts/bs_msl_twin.py`, new `kind: "launcher"`): `{"kind": "launcher", "size": [3, 3], "pivot": [1.5, 1.4], "turret_box": 2.8, "ring_r": 1.15, "collider": 1.25, "cell_style": "pitched", "pitch_deg": 35, "accent": "amber", "cells": {"pods": [{"center": [-0.85, 0.35], "pattern": "3-2-3", "pitch": [0.24, 0.24]}, {"center": [0.85, 0.35], "pattern": "3-2-3", "pitch": [0.24, 0.24]}], "tube_r": 0.085, "fill_order": "pod_sequential (L then R)"}, "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo"], "backblast": [[-0.85, -0.6], [0.85, -0.6]], "preview_pattern": "ripple"}`

### 3.3 Mula-sem-Cabeça (late): Quad-Pod Heavy Missile Battery / Bateria Pesada de Mísseis Quádrupla

- **Concept.** Late flagship-class battery (Mula-sem-Cabeça): a headless armored body with four long pods on hydraulic arms; a salvo is a four-beat stampede of 48 heavy missiles in 3.1 s that buries the deck in backblast smoke. It is the ship's most dangerous part when loaded.
- **Base part / categories.** base_large_part_terran_overclock; TypeCategories [weapon, is_crewed, uses_missiles, uses_launcher_parts, uses_emps, uses_nukes, bs_limit_nuke].
- **Credits per effective DPS:** 6.76. **Emitter components:** 118.

| Mode | Codename | Layout | Missiles/salvo | Ammo per missile | Reload s/unit | Salvo s | Cycle s | Eff/tile | x HE | Stock (missiles / s of fire) | OC eff/tile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| he | Jararaca | fine48 | 48 | 2 missile_part_he | 0.264 | 3.133 | 15.805 | 379.6 | 1.0 | 144.0 / 47.4 | 518.1 |
| cluster | Piranha | heavy16 | 16 | 4 missile_part_he | 0.6 | 1.0 | 10.6 | 339.6 | 0.895 | 64.0 / 42.4 | 486.5 |
| limpet | Carrapato | heavy16 | 16 | 4 missile_part_he | 0.6 | 1.0 | 10.6 | 377.4 | 0.994 | 64.0 / 42.4 | 540.5 |
| napalm | Taturana | heavy16 | 16 | 4 missile_part_thermal | 0.6 | 1.0 | 10.6 | 150.9 | 0.398 | 64.0 / 42.4 | 216.2 |
| emp | Poraquê | heavy16 | 16 | 3 missile_part_emp | 0.6 | 1.0 | 10.6 | 95.6 | 0.252 | 48.0 / 31.8 | 112.6 |
| torpedo | Boto | torpedo4 | 4 | 12 missile_part_he | 2.37 | 0.2 | 9.68 | 330.6 | 0.871 | 20.0 / 48.4 | 490.8 |
| nuclear | Iara | torpedo2_inner | 2 | 8 missile_part_nuke | 9.97 | 0.067 | 20.007 | 266.6 | 0.702 | 6.0 / 60.0 | no OC |

**Overclock - Stampede / Estouro da Boiada.** Four pod loaders on emergency cycle - the headless mule's collar glows and the stampede comes every ~11.6 s.

- Effect: Autoloader_k Interval / 1.5 (EMP / 1.2 so its OC shield rate stays <= 880; nuclear excluded); ModeSwitchDelay_k Duration / same factor; ripple, damage, range and missile unchanged.
- Heat: 400 per part loaded + 150/s -> HE 3465.7 avg / 4695.5 peak heat/s (3.15 / 4.27 radiators).
- Vent per salvo (parts): he 6, cluster 4, limpet 4, napalm 4, emp 3, torpedo 0.
- heat is produced when the AUTOLOADER moves a missile into the rack (factory_he Overclock_ConversionHeatProducer pattern with Trigger = Autoloader_k): heavy munitions pay for their weight, heat follows the extra loading work
- VENT: every time a rack latches full while overclocked, CELLS/16 missiles' parts are vented from the family magazine (ResourceChange, negative Amount, Trigger = RackFullTrigger_k; thruster_boost precedent); torpedo and nuclear modes exempt; salvos under 16 missiles (Tocandira) vent nothing
- OverclockReset 3 s downtime when OC is switched off (base_part_overclock, inherited)
- magazine empties faster: HE crew trips 36.44 -> 52.84/min, HE factories 1.82 -> 2.64
- cook-off chain: heat the network cannot take overflows onto the launcher's own tiles (OverheatEffects) -> >= 350 heat rolls fire -> scorched -> the stock-scaled family cook-off fires
- thermal ports must stay reachable (same port geometry as our 3x3 CIWS / 5x6 Boiúna)
- Visual signature: collar recess brightens (ember frames), pod vents glow, ripple sound pitch +15 %.

**Cook-off at full stock:** missile_part_he: DeathEffects FactorHitEffectsWith = Stock_HE: ExplosiveDamage 183600 r7 (fire 50 %/1000, CrewKillChance 30 %) + 61200 structural; 288 parts at full = 850.0 per part; missile_part_thermal: GridStatusApplication cosmoteer.heat pool 64000 on own tiles (Filter { Self = true }, vanilla thermal-launcher dump); missile_part_emp: ExplosiveResourceDrain battery 86400 r12 (vanilla EMP launcher death pattern); missile_part_nuke: DeathEffects FactorHitEffectsWith = Stock_NUKE: ExplosiveDamage 72000 r8 (fire 50 %/1000, CrewKillChance 30 %) + 24000 structural; 48 parts at full = 2000 per part.

**Art.** Cyberpunk quad battery (ref 4) in the family style: a flat wide headless body 4.8 tiles across - an open armored collar ('neck') with a very dim ember recess where a head should be - carrying two pairs of long rectangular pods on visible hydraulic piston arms, each pod face a 3x4 cell grid (48 tips); claw blades at the pod roots, armored skirt over the ring, rear vent bay with 6 amber pips. Reads at 64 px as 'four ammo boxes around a dark collar'. ALT HEAD (user's choice): Gorjala's 'one-eyed giant' - an armored brow with ONE sensor eye in a dark recess between the pod pairs (ref 2).

- Pods: 4 rectangular pods (2 per side) on piston arms, outer pods splayed 6 deg. Cell grid: per pod 3 cols x 4 rows = 12, pitch 0.26 x 0.22 tile, tube radius 0.09, pitched 40 deg; heavy look = one long nose per 3-cell row; torpedo look = one large capped nose per pod face; nuclear look = inner pods capped (green band), outer pods shuttered.
- Layouts: `fine48` = 48 cells: 4 pods x (3 cols x 4 rows); per-pod ResourceSprites RangeLow/RangeHigh 0-12/12-24/24-36/36-48, 13 levels each; `heavy16` = 16 heavy units: each unit = one 3-cell row of a pod (4 per pod) shown as one long double-calibre nose; per-pod 5 levels; `torpedo2_inner` = 2 nuclear cassettes on the inner pods; outer pods show closed shutters (static sprite toggled by ModeToggle_nuclear); `torpedo4` = 4 torpedo cassettes, one per pod face; per-pod 2 levels.
- Animations: slow traverse 40 deg/s; 4 ResourceSprites per mode on one rack (RangeLow/RangeHigh per pod; one image set reused by the 4 pods); four-beat ripple drum across the pods, per-launch flash + backblast fan (cannon_smoke_deck, RoofCannonSmoke bucket), screen shake 0.02, 0.15 thump on the last missile (TriggeredEffects on the latch turning off); piston arms loop (turret_anim 8 frames, subtle); collar ember recess uses M['ember'] (very dim) and brightens only under overclock - total emissive area stays under the 1-2 % budget (STYLE.md §1.6); NO flame particle by default; nuclear mode: outer-pod shutters close (static sprite toggled by ModeToggle_nuclear); impact reuses the Boiúna mushroom (already budgeted); no pod recoil.
- PART meta (`tools/blender/parts/bs_msl_quad.py`, new `kind: "launcher"`): `{"kind": "launcher", "size": [5, 6], "pivot": [2.5, 2.6], "turret_box": 4.8, "ring_r": 2.0, "collider": 2.1, "cell_style": "pitched", "pitch_deg": 40, "accent": "amber", "cells": {"pods": [{"center": [-1.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}, {"center": [-0.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}, {"center": [0.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}, {"center": [1.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}], "tube_r": 0.09, "fill_order": "pod_sequential (outer-L, inner-L, inner-R, outer-R)", "heavy_unit": "one 3-cell row"}, "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo", "nuclear"], "backblast": [[-1.75, -1.3], [-0.75, -1.3], [0.75, -1.3], [1.75, -1.3]], "preview_pattern": "ripple", "alt_head": "one_eyed_giant"}`

## 4. How a launcher works

1. Crew carry vanilla missile parts into ONE magazine per resource family (HE / thermal / EMP / nuke) - the user's 'internal storage space for missiles'. Consumers request only the family the selected mode uses.
2. While (and only while) the launcher is crewed, the selected mode's AUTOLOADER moves one missile (PARTS parts -> 1 rack unit) every RELOAD seconds into the READY RACK. Vanilla reload timers keep counting unmanned; ours stop (gaps §4.4 #2).
3. The rack is a LATCH (thruster_boost battery pattern): it opens only when every cell is loaded and stays open until the last cell fired, so a salvo always completes and an overclocked loader can never turn it into endless fire.
4. The turret fires one cell every RIPPLE through a per-mode ModeCycle in LIFO order, so the ResourceSprites overlays always match the real rack.
5. Switching INTO a mode starts that mode's ModeSwitchDelay (= one full reload of that mode, OC-divided): a pre-filled second rack can never give two salvos back to back, also when the switch happens mid-salvo.
6. When the family magazine cannot load one more missile of the mode, the partial rack still fires (DryFlush) - nothing is ever stranded.
7. Interrupted salvo: the latch stays on and the remaining cells go to the next target, then the launcher reloads.
8. Cook-off: one stock-scaled DeathEffects per resource family, outside the toggled blocks; a scorched or destroyed loaded launcher explodes.

Cut from v1: C's Stream toggle (bs_salvo_mode): DPS-neutral, contradicts the user's 'reload between salvos' rhythm, adds a second loader per mode (D-C4); C's Unloader_k unload-on-switch: leaks when the magazine is full (D-C3); replaced by ModeSwitchDelay_k; B's part-level ShootCycle and single SalvoCooldown (D-B2, D-B5).

Component sketch (vanilla types only; Caipora shown):

```
// ---- part root (Caipora shown; generated per launcher) ----
RIPPLE = 4/30                                   // tick-aligned (point_defense FireInterval 2/30 precedent)
OVERCLOCK { RELOAD_FACTOR = 1.5; HEAT_PER_PART = 425; HEAT_PER_SECOND = 100 }
HEAT_TO_RESOURCE = &<./Data/statuses/heat/heat.rules>/STATUS_TO_RESOURCE_RATIO
MODE_he      { CELLS = 16; PARTS = 2; RELOAD = 1.06; VENT = 2 }     // ... one block per mode (values in launchers[].modes)
MODE_torpedo { CELLS = 2;  PARTS = 6; RELOAD = 4.65; VENT = 0 }

MissileTypeToggle { Type = UIToggle; ToggleID = "bs_missile_type"; Default = 0; AvailableChoices = [0, 1, 2, 3, 4, 5]; AlwaysAllowInBuildMode = true }
ModeToggle_he { Type = ModeToggle; Mode = MissileTypeToggle; OnMode = 0 }          // ... _cluster 1, _limpet 2, _napalm 3, _emp 4, _torpedo 5

// (1) ONE MAGAZINE PER RESOURCE FAMILY (HE / cluster / limpet / torpedo share MagStorage_HE), outside every ToggledComponents
UsesHE     { Type = MultiToggle; Toggles = [ModeToggle_he, ModeToggle_cluster, ModeToggle_limpet, ModeToggle_torpedo]; Mode = Any }
ConsumeHE  { Type = MultiToggle; Toggles = [CommandConsumptionToggle, UsesHE]; Mode = All }
MagStorage_HE  { Type = ResourceStorage; ResourceType = missile_part_he; MaxResources = 64; DelayBeforeReadyToUse = .5
                 DropResourcesWhenDestroyed = true; DropResourcesWhenRemoved = true; ReceiveResourceMediaEffects = &/COMMON_EFFECTS/AmmoDeliver; UITileRect = [...] }
MagConsumer_HE { Type = ResourceConsumer; ResourceType = missile_part_he; Storage = MagStorage_HE; DefaultPriority = &/PRIORITIES/Weapon_Supply
                 OperationalToggle = ConsumeHE; ConsumptionToggleButtonOffset = [0, -.4] }
// ... MagStorage_Thermal (napalm), MagStorage_EMP (emp), MagStorage_Nuke (nuclear, Mula only)

// (2) PER MODE: rack latch, crewed autoloader, threshold toggles (thruster_boost.rules:176-199 patterns)
ReadyRack_he   { Type = ResourceStorage; ResourceType = missile_part_he; MaxResources = &~/MODE_he/CELLS
                 ToggleOnResources = &~/MODE_he/CELLS; ToggleOffResources = 0; AnticipateMoreResourcesFrom = [MagStorage_HE]; DropResourcesWhenDestroyed = false }
RackAny_he     { Type = MultiResourceStorage; ResourceType = missile_part_he; ResourceStorages = [ReadyRack_he]; ToggleOnResources = 1; ToggleOffResources = 0 }
MagCanLoad_he  { Type = MultiResourceStorage; ResourceType = missile_part_he; ResourceStorages = [MagStorage_HE]
                 ToggleOnResources = &~/MODE_he/PARTS; ToggleOffResources = (&ToggleOnResources) - 1 }       // family holds >= 1 missile of THIS mode
LoaderOn_he    { Type = MultiToggle; Toggles = [IsOperational, ModeToggle_he, { Toggle = ReadyRack_he; Invert = true }]; Mode = All }   // crewed only
Autoloader_he  { Type = ResourceConverter; OperationalToggle = LoaderOn_he; CheckResourceLimits = true
                 FromStorage = MagStorage_HE; FromQuantity = &~/MODE_he/PARTS; ToStorage = ReadyRack_he; ToQuantity = 1
                 Interval { BaseValue = &~/MODE_he/RELOAD
                            Modifiers [ { Type = BuffRemap; BuffType = Overclock; RemapFrom = [0, 1]; RemapTo = [1, &~/OVERCLOCK/RELOAD_FACTOR]; ModificationMode = Divide } ] } }
                 // EMP modes: RemapTo = [1, 1.2]; nuclear mode: same block WITHOUT the Modifiers list

// (3) CROSS-MODE EXPLOIT: per-mode switch delay = one full reload of the mode you switch INTO (holds mid-salvo too)
ModeOn_he         { Type = ToggleTrigger; Toggle = ModeToggle_he; TriggerWhenOn = true; TriggerWhenOff = false }
ModeSwitchDelay_he { Type = Timer; StartTrigger = ModeOn_he; StartExpired = true
                     Duration { BaseValue = (&~/MODE_he/CELLS) * (&~/MODE_he/RELOAD); Modifiers [ same BuffRemap Divide (none for nuclear) ] } }

// (4) PARTIAL SALVO when the family magazine runs dry (DryFlush)
DryFlush_he  { Type = MultiToggle; Toggles = [RackAny_he, { Toggle = MagCanLoad_he; Invert = true }]; Mode = All }
CanFire_he   { Type = MultiToggle; Toggles = [ReadyRack_he, DryFlush_he]; Mode = Any }
RackReady_he { Type = MultiToggle; Toggles = [ModeToggle_he, ModeSwitchDelay_he, CanFire_he]; Mode = All }
HasMissiles_he { Type = MultiToggle; Toggles = [ModeToggle_he, { Type = MultiToggle; Toggles = [MagCanLoad_he, RackAny_he]; Mode = Any }]; Mode = All }
// ... repeat (2)-(4) per mode
RackReady      { Type = MultiToggle; Toggles = [RackReady_he, RackReady_cluster, ...]; Mode = Any }
HasMissiles    { Type = MultiToggle; Toggles = [HasMissiles_he, ...]; Mode = Any }          // PartCrew HighPriorityPrerequisites + NoMissiles indicator
FirePermission { Type = MultiToggle; Toggles = [RackReady, FireModeToggle]; Mode = All }

// (5) TURRET (complete: emitter proxy for targeting, IsHigh collider chained to the turret)
Turret { Type = TurretWeapon; Location = [pivot]; OperationalToggle = IsOperational; AutoFireToggle = AutoFireToggle
         FireInterval = &~/RIPPLE; FirePermissionToggle = FirePermission
         FiringArc = 360d; RotateSpeed = 75d; FireThresholdAngle = 25d
         AllowFireWithBlockedLOS = true; IgnoreFriendlyShipLowLOSChecks = true
         Emitter = TargetEmitterProxy                           // cannon_deck.rules:617 "only used for targeting"
         AIFirepowerRating = &~/Part/StatsByCategory/0/Stats/DamagePerSecond
         AutoTargets [ { TargetType = ShipParts; Toggle = AutoTargetToggle; EnableInDirectControlMode = true } ] }
TurretCollider { Type = CircleCollider; ChainedTo = Turret; Radius = 1.25; IsHigh = true }
TargetEmitterProxy { Type = EmitterProxy; ComponentID = Emitter_0; ChainedTo = Turret }   // Emitter_0 of the ACTIVE Fire_k (cannon_deck.rules:895, T/bsgen/guns.py:438)

// (6) PER MODE FIRE BLOCK (only one active): ShootCycle INSIDE the block, per-mode ModeRange (fixes Iara/torpedo ripple, D-B2)
Fire_he { Type = ToggledComponents; Toggle = ModeToggle_he; IncludeInBlueprints = true
  Components {
    ShootCycle     { Type = ModeCycle; ModeRange = [0, 15]; IncrementTrigger = Turret; StartingMode = 15 }
    ShootTrigger_0 { Type = ModeTrigger; Mode = ShootCycle; TriggerInModes = [0] }           // ... _15
    Emitter_0 { Type = BulletEmitter; ChainedTo = Turret; GetTargetFrom = Turret; FireTrigger = ShootTrigger_0; OperationalToggle = IsOperational
                Location = [cell 15 in fill order]                                          // LIFO: last cell filled fires first
                Bullet = &<../../shots/bs_msl_twin_he/bs_msl_twin_he.rules>; ResourceStorage = ReadyRack_he; ResourcesUsed = 1
                TargetLeadPrediction = false; Spread = [-4d, 4d]; Recoil = 0 }
    // Emitter_1..15 : Emitter_0 { Location = ...; FireTrigger = ShootTrigger_i }
    // Tocandira cassette emitters add: Burst = 2; BurstDelay = 2/30 (UseResourcePerShotInBurst default false -> 1 rack unit per pair)
    EmitterAny     { Type = MultiTrigger; Triggers = [Emitter_0, ..., Emitter_15] }
    CellsPodL      { Type = ResourceSprites; ChainedTo = Turret; Rotation = 90d; Location = [...]; Layer = "roof_turrets"
                     ResourceStorage = ReadyRack_he; RangeLow = 0; RangeHigh = 8; HasZeroResourceSprite = true; ResourceLevels [ 9 entries ] }
    CellsPodR : CellsPodL { Location = [...]; RangeLow = 8; RangeHigh = 16 }
    ReloadProgressBar { Type = ProgressBar; OperationalToggle = IsOperational; ShowProgressFor = ReadyRack_he; ValueRange = [0, &~/MODE_he/CELLS] }
    LaunchEffect_i { Type = TriggeredEffects; ChainedTo = Emitter_i; Trigger = Emitter_i; MediaEffects [ flash (Upper1), backblast (Upper), launch sound ] }
  } }

// (7) OVERCLOCK COSTS (base_*_overclock gives IsOverclocked / HEAT_TARGET_STORAGE / OverclockReset)
Overclock_LoadHeat_he { Type = ResourceChange; OperationalToggle = IsOverclocked; Trigger = Autoloader_he
                        ResourceStorage = &~/Part/^/0/HEAT_TARGET_STORAGE; Amount = (&~/OVERCLOCK/HEAT_PER_PART) * (&~/MODE_he/PARTS) * (&~/HEAT_TO_RESOURCE) }
RackFullTrigger_he    { Type = ToggleTrigger; Toggle = ReadyRack_he; TriggerWhenOn = true; TriggerWhenOff = false }
Overclock_Vent_he     { Type = ResourceChange; OperationalToggle = IsOverclocked; Trigger = RackFullTrigger_he
                        ResourceStorage = MagStorage_HE; Amount = -(&~/MODE_he/VENT) }      // thruster_boost.rules:224 negative ResourceChange
// constant heat: Overclock_ConstantHeatProducer (T/bsgen/common.py:133); nuclear mode has no LoadHeat and no Vent

// (8) COOK-OFF PER FAMILY, outside the toggled blocks, ScorchedTrigger copied VERBATIM (fixes D-C1)
Stock_HE         { Type = MultiResourceStorage; ResourceType = missile_part_he; ResourceStorages = [MagStorage_HE, ReadyRack_he, ReadyRack_cluster, ReadyRack_limpet, ReadyRack_torpedo] }
ScorchedTrigger  { Type = ToggleTrigger; Toggle = ScorchedToggle; TriggerWhenOn = false; TriggerWhenOff = true }   // missile_launcher_he.rules:271-276
ScorchedEffects_HE  { Type = TriggeredEffects; Trigger = ScorchedTrigger; FactorHitEffectsWith = Stock_HE; HitEffects = &../DestroyedEffects_HE/HitEffects }
DestroyedEffects_HE { Type = DeathEffects; OperationalToggle = ScorchedToggle; FactorHitEffectsWith = Stock_HE
                      HitEffects [ { Type = ExplosiveDamage; TotalDamage = { BaseValue = 61200; EffectScaleExponent = 1 }; Radius = 5; StatusType = cosmoteer.fire
                                     StatusChancePerNDamage = 50%; StatusValue = 1; StatusValueType = Interpolated; NDamage = 1000; CrewKillChance = 30% }
                                   { Type = ExplosiveDamage; TotalDamage = { BaseValue = 20400; EffectScaleExponent = 1 }; Radius = 4; Filter { OperationalHealth = false; StructuralHealth = true } } ] }
// thermal family: GridStatusApplication cosmoteer.heat dump (Filter { Self = true }); EMP family: ExplosiveResourceDrain battery; nuke family: big blast

// FALLBACK if the latch behaves as a pure threshold (test T02), all timings unchanged (NGEN §14.1):
// IsSalvoActive { Type = Timer; StartTrigger = Turret; ResetTrigger = Turret; Duration = RIPPLE x 1.5; StartExpired = true }
// RackFull_k { Type = MultiResourceStorage; ResourceStorages = [ReadyRack_k]; ToggleOnResources = CELLS; ToggleOffResources = CELLS - 1 }
// CanFire_k = Any[RackFull_k, All[IsSalvoActive, RackAny_k], DryFlush_k]
```

## 5. Missile types

**Shared core.** Deck-safe missile core (every missile, child, decoy and charge): Hit { Type = SimpleHit (charge: PenetratingHit); FriendlyShipLowCollisions = false; FriendlyShipHighCollisions = false; SourcePartCollisionDelay = 1.5 / (&/Simulation/PhysicsUpdatesPerSecond) }; TargetHoming { TurnVelocity; Delay; VelocityCompensation = 60% } with NO AvoidanceRaycastDistance (AvoidsFriendlies default, test T07); SameShipRetarget; Acceleration + NegativeAcceleration [-90, 0] over [0, .75] Direction = FrameOfReferenceVelocity; DeathByLifetime; Targetable { TargetCategory = "missile"; OnDeath = &../Hit/HitFriendly } (shot down = fizzle, no AOE); explosions WITHOUT Friendlies = true; every scalable number written { BaseValue = X; EffectScaleExponent = 1 }; sprite vanilla missile_he.png scaled (RenderBucket BulletUpper3) + type-coloured glow (BulletUpper4) + missile_he_thruster_plume_light (Upper4); never the Lower-bucket thruster particles (hidden under our roof).

| # | Codename | Missile (en / pt-BR) | Ammo | Launchers | Glow |
|---|---|---|---|---|---|
| 0 | Jararaca | High-Explosive Missile / Míssil Alto-Explosivo | missile_part_he | Tocandira, Caipora, Mula-sem-Cabeça | #FFB000 amber |
| 1 | Piranha | Cluster Missile (Transformer) / Míssil de Submunições (Transformer) | missile_part_he | Caipora, Mula-sem-Cabeça | #FFE45C yellow, petal-segmented nose |
| 2 | Carrapato | Limpet Missile / Míssil Grudento | missile_part_he | Caipora, Mula-sem-Cabeça | #FF3B30 red, blinking charge |
| 3 | Taturana | Napalm Missile / Míssil de Napalm | missile_part_thermal | Tocandira, Caipora, Mula-sem-Cabeça | #FF6A1A orange |
| 4 | Poraquê | EMP Missile / Míssil PEM | missile_part_emp | Caipora, Mula-sem-Cabeça | #4FC3FF blue, coil ring |
| 5 | Boto | Decoy Torpedo / Torpedo com Iscas | missile_part_he | Caipora, Mula-sem-Cabeça | #F4F7FF white nose |
| 6 | Iara | Nuclear Torpedo / Torpedo Nuclear | missile_part_nuke | Mula-sem-Cabeça | #7CFF6B thin green band |

### 0. Jararaca: High-Explosive Missile / Míssil Alto-Explosivo

*Why the name:* the pit viper: fast, direct, lethal bite.

- **Mechanic.** SimpleHit; HitOperational = [ ExplosiveDamage { TotalDamage = { BaseValue = X; EffectScaleExponent = 1 }; Radius = r } (no fire rider, no Friendlies), Impulse ]; HitStructural = &HitOperational; HitShield = &HitOperational (vanilla missile_he shape).
- **Special.** The reference missile and the SW 'normal missile'. A stream of single-target heads; the heavy 48-missile Mula salvo is the best PD-saturation tool in the reference model.
- **Counterplay.** Point defense and CIWS (single-target triage), shields absorb the blast at the bubble edge, armor soaks explosions.
- **Fallback (no number changes).** None needed beyond the shared deck-flight tests (T06/T07).
- **Risk.** LOW

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira (Muriçoca) | `rafaeltessaro.bs_msl_box_he` | 0.5 he | 55 / 85 / 300 | 300 | 0.15 | 380 | 2.09 s | ExplosiveDamage 1600; Radius 1.5; Impulse 15 | 800.0 | 264.5 | 800.0 |
| Caipora | `rafaeltessaro.bs_msl_twin_he` | 2.0 he | 45 / 65 / 230 | 400 | 0.15 | 1050 | 2.88 s | ExplosiveDamage 7000; Radius 3.0; Impulse 60 | 3500.0 | 328.2 | 875.0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_he` | 2.0 he | 45 / 60 / 200 | 600 | 0.15 | 2200 | 3.78 s | ExplosiveDamage 7500; Radius 3.5; Impulse 80 | 3750.0 | 379.6 | 937.5 |

### 1. Piranha: Cluster Missile (Transformer) / Míssil de Submunições (Transformer)

*Why the name:* one shape in the water, then a school that strips the target from every side.

- **Mechanic.** Carrier = SW Discord MIRV shape on vanilla types (SW missile_discord.rules:48-96, 170-172): root group BURST { HitEffects [ { Type = SpawnBullets; Bullet = &~/CHILD; Count = K; Distance = [0, .8]; Arc = [-25d, 50d]; Spread = [-5d, 5d]; InheritVelocity = false; HealthFactor = { BaseValue = 1; EffectScaleExponent = 1 } } ] MediaEffects [petal flash] }. Three triggers, never a dud: ProximityFuse { Type = DeathByEnemyProximity; Interval = .05; Range = 25; StartDelay = .4; DetectsShips = true; DetectsBullets = false; FactorEffectsWith = Targetable; OnDeath = &~/BURST }; TimedFuse { Type = DeathByLifetime; Lifetime = class lifetime; OnDeath = &~/BURST }; Hit { HitShield / HitOperational / HitStructural = &~/BURST }. The carrier has NO warhead. CHILD (same folder, relative ref like our flak_oc): Speed 40; Acceleration 100; TargetHoming { TurnVelocity = 120d/110d; Delay = .25 } (late, weak homing -> children fan over several parts); SameShipRetarget; Magnet = ProximityAcceleration { Range = 30; Acceleration = 25; AccelerateTowardsShips = true; AccelerateTowardsEnemies = true; AccelerateTowardsFriendlies = false; AccelerateTowardsBullets = false } (buzz-droid magnet, works even without target inheritance); Spacing = ProximityAcceleration { Range = 3; Acceleration = -10; AccelerateTowardsShips = false; AccelerateTowardsBullets = true; AccelerateTowardsBulletCategories = [missile]; AccelerateTowardsFriendlies = true; AccelerateTowardsEnemies = false } (vanilla mine repulsion); DeathByLifetime 2.5; Targetable { Health; "missile"; fizzle }; SimpleHit WITH every deck flag; HitOperational = ExplosiveDamage small radius + Impulse 10; one cheap glow sprite (performance).
- **Special.** The user's 'Transformers 3' missile. Opens only 25 m from the hull (Discord value) so it never 'transforms' over our own deck; children leave at 40 m/s in a +-25 deg cone with late, weak homing + magnet + spacing, so they land on several parts. Children's HP pool >= carrier HP, so splitting never makes interception easier. Trades 10 % sustained damage for multi-part spread and for taxing the defender's ammo; in the reference LOCK model it leaks about as well as HE against one PD/CIWS (see balance_checks.interception).
- **Counterplay.** Kill carriers before 25 m; big-radius area flak eats the child clumps (Pororoca r7, vanilla flak); shields catch the whole brood at the bubble; armor stops the small blasts.
- **Fallback (no number changes).** Q1 target inheritance [INFERRED strong]: children keep the magnet, so they still reach the nearest enemy hull - same Count/damage/HP. Q2 children's source ship unknown: deck flags on children anyway; if a carrier opens over our hull, ProximityFuse StartDelay .4 -> 1.0 (not a balance number). Performance: strip the child glow and delete the Spacing component (visual/spread only, Count stays). RandomizeTarget = true stays an experiment file (never shipped anywhere).
- **Risk.** MEDIUM (target inheritance, children source ship, performance)

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_cluster` | 2.0 he | 45 / 65 / 230 | 400 | 0.15 | 1050 | 2.88 s | carrier_warhead 0; children 4; child_ExplosiveDamage 1575; child_radius 1.75; child_hp 300; child_total 6300; children_hp_pool 1200; proximity_range 25; child_turn_deg_s 120; child_speed 40; child_accel 100; child_homing_delay_s 0.25; child_lifetime_s 2.5 | 3150.0 | 295.4 | 787.5 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_cluster` | 4.0 he | 45 / 60 / 200 | 600 | 0.15 | 2200 | 3.78 s | carrier_warhead 0; children 6; child_ExplosiveDamage 2250; child_radius 2.0; child_hp 400; child_total 13500; children_hp_pool 2400; proximity_range 25; child_turn_deg_s 110; child_speed 40; child_accel 100; child_homing_delay_s 0.25; child_lifetime_s 2.5 | 6750.0 | 339.6 | 843.8 |

### 2. Carrapato: Limpet Missile / Míssil Grudento

*Why the name:* the tick: it bites, holds on, and you notice too late.

- **Mechanic.** Missile SimpleHit: HitOperational / HitStructural = { Offset = [-0.4, 0]; HitEffects [ Damage d; SpawnBullets { Bullet = &~/CHARGE; Count = 1; Distance = 0; Spread = [0d, 0d]; InheritVelocity = false }; Impulse 20 ]; MediaEffects [clank + red flash] }; HitShield = small ExplosiveDamage only (cannot stick to a bubble). CHARGE = SW buzz-droid recipe on vanilla types (SW buzzdroid.rules:37-44 magnet + :78-81 crawl): CirclePhysics .25 Density 1; Speed 12; Magnet ProximityAcceleration { Range = 8; Acceleration = 30; ships, enemies }; Hit { Type = PenetratingHit; Penetration = 1000; PenetrationSpeed = 0.05; ShieldCollisions = { Shields = false; }; deck flags; empty Penetrating*/FinishedPenetrating* groups }; Fuse = DeathByLifetime { Lifetime = 2.5; OnDeath = BLAST { ExplosiveDamage X r; CrewKillChance = 50% } }; NO Targetable (user's literal rule: shot down in flight = lost, stuck = it WILL explode; also avoids the victim's PD firing into its own hull, D-B4); blinking red AnimatedSprite (BulletUpper3) + light; chained red beacons on a salvo.
- **Special.** Shot down in flight = lost; hits the hull = sticks and explodes 2.5 s later (CrewKillChance 50 % punishes repair crews that rush in). Same sustained DPS as HE, different feel: a countdown of red beacons.
- **Counterplay.** Shoot it down in flight (same HP as HE); shields (no stick, only a 43 % pop); sacrificial armor eats the charge; spread crews away from the beacon.
- **Fallback (no number changes).** Same fuse, blast and radius in every step: F1 drop the magnet (pure drill); F2 custom Part status rafaeltessaro.bs_limpet (disruptor_drain template: Layer = Part; ApplyNewInstance; TickInterval = 2.5; TickingEffects Damage; ParentMediaEffectsToShip) applied by StatusApplication { StatusDuration = 2.6 } - only if T14b proves mod status registration + first tick at TickInterval on both versions; F3 Speed-0 charge with Hit FrameOfReference = HitObject; F4 last resort: same blast at impact. Isolated SW-only variant bs_msl_<l>_limpet_rep.rules with Repeating { Count 1; InitialDelay 2.5; RequireHitPart true } behind a build flag, checked with schema_check --extra SW (never on the default path). Optional 'defusable' variant: Targetable 500/600 'missile' (off: own-hull PD lock).
- **Risk.** MEDIUM-HIGH behaviour (anchoring), LOW load

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_limpet` | 2.0 he | 45 / 65 / 230 | 400 | 0.15 | 1050 | 2.88 s | impact_Damage 250; charge_ExplosiveDamage 6500; charge_radius 2.5; charge_CrewKillChance 50%; fuse_s 2.5; charge_targetable no (default); shield_pop_ExplosiveDamage 3000; shield_pop_radius 2.0 | 3500.0 | 328.2 | 875.0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_limpet` | 4.0 he | 45 / 60 / 200 | 600 | 0.15 | 2200 | 3.78 s | impact_Damage 500; charge_ExplosiveDamage 14000; charge_radius 3.5; charge_CrewKillChance 50%; fuse_s 2.5; charge_targetable no (default); shield_pop_ExplosiveDamage 6500; shield_pop_radius 3.0 | 7500.0 | 377.4 | 937.5 |

### 3. Taturana: Napalm Missile / Míssil de Napalm

*Why the name:* the fire caterpillar: touch it and it burns for a long time.

- **Mechanic.** HitOperational = [ ExplosiveDamage (blast, NO fire rider: interpolated ExplosiveDamage chances differ 0.30.4/0.30.5, PN:19); { Type = StatusApplication; StatusType = cosmoteer.fire; StatusChance = { BaseValue = c; EffectScaleExponent = 1 }; StatusValue = v%; ValueType = Interpolated } (bullet_med.rules:129-132 + bullet_large_overclock_shrapnel.rules:113-114 pattern); { Type = GridStatusApplication; StatusType = cosmoteer.heat; StatusValue = 0; StatusValuePool = H (literal, never APPLIED_HEAT_PER_MISSILE); ValueFalloff = 1; MaxCost = k; FalloffPadding = .5; EmptyTileCost = 1000; AllowDiagonals = true; Filter { Friendlies = false; TargetedFriendlies = true } } (missile_thermal.rules:128-139 shape) ]; HitStructural = &HitOperational; HitShield = [ the blast; StatusApplication cosmoteer.heat (raw value, ApplyToAllHitPartTiles = true; DivideValueByPartArea = true) ]. Optional 'gel splash' GridStatusApplication cosmoteer.fire is OFF until test T15 (raw vs interpolated value in a bullet is unproven). Never UseContiguity / AllowVertexContiguity.
- **Special.** Interior arsonist: guaranteed fire on the hit part + a heat pool that keeps rolling new fires (5-50 % per 0.25 s above 350 heat). Weak direct damage; useless on armor and structure (non_flammable).
- **Counterplay.** Fire extinguishers (-1 fire per unit + fire_foam 100 % fire resistance for 3-15 s), crew soft-repair cools heat, armor belts, shields (only generator heat).
- **Fallback (no number changes).** If StatusApplication fire misbehaves: ApplyToAllHitPartTiles = true on the same entry. Gel GridStatusApplication fire only after T15. Heat pool alone still re-ignites (same numbers).
- **Risk.** LOW

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira (Taturana-mirim) | `rafaeltessaro.bs_msl_box_napalm` | 0.5 thermal | 55 / 85 / 300 | 300 | 0.15 | 380 | 2.09 s | blast_ExplosiveDamage 600; blast_radius 1.5; fire_StatusChance 0.6; fire_StatusValue_interpolated 40%; heat_StatusValuePool 500; heat_MaxCost 1; shield_heat 50; shield_blast 600 | 300.0 | 99.2 | 200.0 |
| Caipora | `rafaeltessaro.bs_msl_twin_napalm` | 2.0 thermal | 45 / 65 / 230 | 400 | 0.15 | 1050 | 2.88 s | blast_ExplosiveDamage 3000; blast_radius 2.5; fire_StatusChance 1.0; fire_StatusValue_interpolated 60%; heat_StatusValuePool 1600; heat_MaxCost 3; shield_heat 160; shield_blast 3000 | 1500.0 | 140.6 | 250.0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_napalm` | 4.0 thermal | 45 / 60 / 200 | 600 | 0.15 | 2200 | 3.78 s | blast_ExplosiveDamage 6000; blast_radius 3.5; fire_StatusChance 1.0; fire_StatusValue_interpolated 70%; heat_StatusValuePool 4800; heat_MaxCost 4; shield_heat 480; shield_blast 6000 | 3000.0 | 150.9 | 250.0 |

### 4. Poraquê: EMP Missile / Míssil PEM

*Why the name:* the Amazon electric eel: one shock and everything goes dark.

- **Mechanic.** HitOperational = [ { Type = ExplosiveResourceDrain; ResourceType = battery; TotalDrain = { BaseValue = D; EffectScaleExponent = 1 }; Radius = R; Slices = 1; Filter { Ships = true; Shields = true } (NO Friendlies); MediaEffectsOnDrainFactor = .0005; MediaEffectsOnDrain [vanilla missile_emp sizzle/drain] }; { Type = Damage; Damage = d }; { Type = ExplosiveDamage; TotalDamage = s; Radius = rs; Filter { OperationalHealth = false; StructuralHealth = true } }; optional rider StatusApplication cosmoteer.disruptor_drain (StatusDuration 3, StatusValue .1, not counted) ]; HitShield = HitStructural = &HitOperational (missile_emp.rules:151-196 shape, scaled to 1500 drain per EMP part).
- **Special.** Support / shield breaker against battery ships (vanilla, SW:ACD). Bullet Strike weapons have no battery and are immune by design.
- **Counterplay.** Armor soaks area drain (ExplosiveResourceDrainSink 2000/tile), battery-free ships shrug it off, shoot it down like any missile.
- **Fallback (no number changes).** Drop the disruptor_drain rider if it misbehaves (never counted). If drain at a bubble edge does not reach the generator: add a single-part ResourceDrain { TreatShieldAsPart = true } with the same total.
- **Risk.** LOW

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_emp` | 2.0 emp | 45 / 65 / 230 | 400 | 0.15 | 1500 | 2.88 s | battery_TotalDrain 3000; drain_radius 8; direct_Damage 300; structural_ExplosiveDamage 2000; structural_radius 2.0; sw_shield_hp_per_missile 7500.0 | 1300.0 | 121.9 | 130.0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_emp` | 3.0 emp | 45 / 60 / 200 | 600 | 0.15 | 2800 | 3.78 s | battery_TotalDrain 4500; drain_radius 10; direct_Damage 400; structural_ExplosiveDamage 3000; structural_radius 2.5; sw_shield_hp_per_missile 11250.0 | 1900.0 | 95.6 | 126.7 |

### 5. Boto: Decoy Torpedo / Torpedo com Iscas

*Why the name:* the river dolphin that takes other shapes to deceive: one warhead hides among decoys.

- **Mechanic.** Two-stage chain on the vanilla nuke pattern: LAUNCH STAGE (1.5 s; BoxPhysics [2.0, .65]; TargetHoming 90d Delay .3; Acceleration 12, no LinearDamping; Targetable HP "missile" fizzle; Hit = &<warhead file>/Components/Hit so an early impact still detonates) whose Deploy = DeathByLifetime { Lifetime = 1.5; FactorEffectsWith = Targetable; OnDeath { HitEffects [ SpawnBullets { Bullet = &~/WARHEAD; Count = 1; InheritVelocity = true; HealthFactor {...} }; SpawnBullets { Bullet = &~/DECOY; Count = N; Distance = [0.5, 1.5]; Arc = [-60d, 120d]; Spread = [-10d, 10d]; InheritVelocity = true } ] } }. WARHEAD: Speed 0 (inherits), homing 90d, Acceleration 12, SimpleHit; HitOperational = [ ExplosiveDamage op (ExpandDuration .5; ExpandStartRadius 1.5; ExpandLoss 100%; Filter op only), ExplosiveDamage structural-only ] (missile_nuke_stage1.rules:141-160 shape, literals, no Friendlies); HitShield = operational block only. DECOY: Speed 0, Box [1.2, .4], homing 70d Delay .4, Acceleration 12, Spacing ProximityAcceleration (Range 3.5, -6, [missile], friendlies), Lifetime 9, Targetable HP "missile", SimpleHit with deck flags and NO HitEffects (small pop media).
- **Special.** SW 'torpedo (bigger, single)': slow, tough (one Tamanduá trigger of 3 x 2000 does not kill a 6500-HP late warhead), and hides among decoys that spend single-target PD shots and flak pools.
- **Counterplay.** Area flak (decoys do not fool a big blast), a Tamanduá needs two triggers per late warhead, fast ships out-turn it (90 deg/s); shields take the operational blast.
- **Fallback (no number changes).** If two SpawnBullets in one OnDeath list misbehave (T17): single-stage torpedo + decoys fired by a second BulletEmitter per torpedo cell (Burst N, BurstDelay 0.1, no ResourceStorage) - same counts and HP.
- **Risk.** LOW-MEDIUM (two SpawnBullets in one OnDeath)

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_torpedo` | 6.0 he | 30 / 12 / 90 | 400 | 0.3 | 4500 | 6.04 s | warhead_operational 18000; op_radius 4.0; warhead_structural 6000; struct_radius 5.0; launch_stage_s 1.5; decoys 4; decoy_hp 600; decoy_damage 0 | 12000.0 | 282.7 | 1000.0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_torpedo` | 12.0 he | 30 / 12 / 90 | 600 | 0.3 | 6500 | 7.81 s | warhead_operational 36000; op_radius 5.0; warhead_structural 12000; struct_radius 6.0; launch_stage_s 1.5; decoys 6; decoy_hp 700; decoy_damage 0 | 24000.0 | 330.6 | 1000.0 |

### 6. Iara: Nuclear Torpedo / Torpedo Nuclear

*Why the name:* the river siren: beautiful, slow, and nobody who meets her comes back.

- **Mechanic.** Same chain and shared DECOY file as the late Boto; WARHEAD HitOperational = [ ExplosiveDamage 120000 r9 (ExpandDuration .8; ExpandStartRadius 2; ExpandLoss 100%; ImpulsePerNDamage 10; NDamage 1000; Filter op only); ExplosiveDamage 40000 r7 structural-only ] (literals, NO Friendlies); MediaEffects = the Boiúna mushroom (BS/shots/bs_shot_nuke_howitzer_nuclear particles). Launcher side: Autoloader_nuclear has NO overclock BuffRemap, no OC heat and no vent (overclock never shortens a nuclear reload - Boiúna rule).
- **Special.** SW 'nuclear one': Mula only, in bs_limit_nuke with Boiúna, never accelerated by overclock. Dies to area flak alone, so it must be MASKED: launch the Iara pair first and fire a heavy HE salvo 1-3 s later so both arrive together.
- **Counterplay.** Any area flak alone (Tamanduá, Pororoca, vanilla flak), two vanilla PDs; shields eat the whole yield on the bubble; it is slow (7.8 s to 600 m) and visible.
- **Fallback (no number changes).** Same decoy fallback as Boto. If CategoryLimits fail on 0.30.5 RC: ship without limits like Boiúna/Mapinguari (cost, 8 nuke parts and the 20 s reload still gate it).
- **Risk.** LOW (plus limit pool test)

| Launcher | Shot ID | Ammo/missile | Speed / accel / turn | Range | Homing delay | HP | Flight to max range | Damage | Eff/missile | Eff/tile | Per bullet-eq |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_nuclear` | 8.0 nuke | 30 / 12 / 90 | 600 | 0.3 | 6500 | 7.81 s | warhead_operational 120000; op_radius 9.0; warhead_structural 40000; struct_radius 7.0; launch_stage_s 1.5; decoys 6; decoy_hp 700; decoy_damage 0 | 80000.0 | 266.6 | 1111.1 |

## 6. Resources and factories

NO new resource and NO new factory in v1. Every missile uses a vanilla missile part, as the user asked ('pega o padrão que já tem no jogo'). The vanilla factories feed the launchers; parts can be bought or salvaged; SW:ACD launchers use the same IDs (missile_part_he/emp/nuke), so a combined game shares factories and nothing collides. Napalm runs on missile_part_thermal (vanilla since 0.30.0, never used by SW) and gets its own copper + sulfur chain. The Iara uses missile_part_nuke, never the Boiúna's Nuclear Shell chain.

| Part | Buy | Stack | Cooks off | Used by | Factory |
|---|---|---|---|---|---|
| missile_part_he | 8 | 10 | yes | he, cluster, limpet, torpedo | cosmoteer.factory_he (3x3, iron + sulfur + 125 battery/part; 200 parts/min) |
| missile_part_thermal | 12 | 10 | yes | napalm | cosmoteer.factory_thermal (3x3, copper + sulfur; 200 parts/min) |
| missile_part_emp | 20 | 10 | no | emp | cosmoteer.factory_emp (3x4, iron + copper; 120 parts/min) |
| missile_part_nuke | 36 | 10 | yes | nuclear | cosmoteer.factory_nuke (4x4, iron + uranium; 120 parts/min) |

- In-game tip: 1 HE Factory feeds 2 Caiporas or 5 Tocandiras; a Mula needs 1.8 HE Factories (2.6 with Stampede); a Mula on Poraquê needs 2.3 EMP Factories.
- The launchers use no power (mod rule for weapons); the vanilla factories do - that is the vanilla missile economy.
- **Factory efficiency.** DECIDED: accept the vanilla missile economy. A vanilla HE factory feeds ~5300-6300 effective DPS of our HE missiles against ~1270 per factory in our guns' magazine chain (4-5x). Per ammo credit and per crew trip the missiles are in line or hungrier, and they pay with interception, crew, cook-off risk and long crewed reloads. SW:ACD and vanilla use the same parts at the same efficiency, so a factory-hungrier Bullet Strike missile would look weak next to them. Damage is NOT the lever. Lever kept for later (v2): a rafaeltessaro.bs_msl_canister resource (vanilla parts + 1 Standard Magazine, power-free press) would raise factory load without touching any damage number.
- v2 option: rafaeltessaro.bs_msl_canister (stack 4, packed from 4 missile_part_he + 1 rafaeltessaro.bs_mag_std by a Magazine-Press-style part) - only parts_per_missile and the resource ID would change.

## 7. Career techs

| Tech ID | Tier | Cost | Prerequisites | Unlocks |
|---|---|---|---|---|
| `rafaeltessaro.bs_msl_box` | 1 | 3500 | rafaeltessaro.bs_autocannon_20 | rafaeltessaro.bs_msl_box, missile:he |
| `rafaeltessaro.bs_msl_napalm` | 2 | 9000 | rafaeltessaro.bs_msl_box, cosmoteer.factory_thermal | missile:napalm |
| `rafaeltessaro.bs_msl_twin` | 2 | 14000 | rafaeltessaro.bs_msl_box, cosmoteer.factory_he | rafaeltessaro.bs_msl_twin |
| `rafaeltessaro.bs_msl_cluster` | 2 | 16000 | rafaeltessaro.bs_msl_twin | missile:cluster |
| `rafaeltessaro.bs_msl_emp` | 2 | 12000 | rafaeltessaro.bs_msl_twin, cosmoteer.factory_emp | missile:emp |
| `rafaeltessaro.bs_msl_limpet` | 3 | 22000 | rafaeltessaro.bs_msl_cluster, rafaeltessaro.bs_ammo_aphe | missile:limpet |
| `rafaeltessaro.bs_msl_torpedo` | 3 | 25000 | rafaeltessaro.bs_msl_cluster | missile:torpedo |
| `rafaeltessaro.bs_msl_twin-overclock` | 3 | 40000 | rafaeltessaro.bs_msl_twin, cosmoteer.heat_management | overclock:rafaeltessaro.bs_msl_twin |
| `rafaeltessaro.bs_msl_quad` | 4 | 150000 | rafaeltessaro.bs_msl_torpedo, cosmoteer.control_room_large | rafaeltessaro.bs_msl_quad |
| `rafaeltessaro.bs_msl_nuclear` | 4 | 110000 | rafaeltessaro.bs_msl_quad, rafaeltessaro.bs_nuclear, cosmoteer.factory_nuke | missile:nuclear |
| `rafaeltessaro.bs_msl_quad-overclock` | 4 | 160000 | rafaeltessaro.bs_msl_quad, cosmoteer.heat_management | overclock:rafaeltessaro.bs_msl_quad |
| `rafaeltessaro.bs_msl_box-overclock` (disabled) | 3 | 30000 | rafaeltessaro.bs_msl_box, cosmoteer.heat_management | overclock:rafaeltessaro.bs_msl_box |

- 'missile:<type>' is a new prefix in bs_data.career_techs -> ToggleChoicesUnlocked = [[bs_missile_type, N]] (vanilla techs.rules:118 shape; mirrors 'ammo:' at T/bs_data.py:467-473). One unlock covers every launcher that lists the choice.
- Costs sit on the mod ladder: tier 1 1000-3500, tier 2 4000-16000, tier 3 20000-50000, tier 4 60000-170000 (Mapinguari 150000, its OC 160000).
- Vanilla anchors (RJ/modes/career/techs.rules): factory_he 7500 requires missile_launcher_he (5000, :112-119, :382-389); factory_thermal 9000 requires missile_launcher_thermal (+ heat_management); factory_emp 10000 requires missile_launcher_emp; factory_nuke 15000 requires missile_launcher_nuke + factory_uranium; control_room_large 10000; heat_management 5000.
- HE parts can be bought at stations before factory_he is researched, so the Tocandira is usable from tier 1.
- Limpet requires our APHE ammo tech (delayed-fuse shells) - thematic link; the nuclear torpedo requires our bs_nuclear (Boiúna) tech and the vanilla nuke factory.
- Build & Battle: add the three launchers to BB_WHITELIST and buildbattle_techs (iterate GUNS + DEFENSES + LAUNCHERS).

## 8. Balance checks

Conventions: effective DPS = direct + 50 % of explosive, per Size cell; bullet-eq = credits / 4; crew trips = parts/min / 10; factories unbuffed (HE/thermal 200, EMP/nuke 120 parts/min); SW bubble 1 drain = 2.5 shield HP; cycle = units x reload + salvo duration.

### 8.1 DPS per tile against our deck guns and the vanilla launcher

Gun bands: early Marimbondo 260 / Mangangá 270 / Carcará 250 per tile @220-250 m; mid Saci 332.5 / Cigarra 340 / Tambor 312.5 / Boitatá 266.7 @300-340 m; late Furacão 375 / Trovão 380 / Curupira 270 / Boiúna 266.7 / Mapinguari 381 @500-600 m. Vanilla HE launcher: 938 explosive DPS/tile (469 effective), 2 crew, hull edge only.

| Launcher | Mode | Cycle s | Alpha (expl.) | Eff DPS | Eff/tile | Expl/tile | x vanilla 938 | Eff/crew | Per bullet-eq | x HE | OC eff/tile |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | 9.073 | 19200 | 1058.0 | 264.5 | 529.0 | 0.56 | 1058.0 | 800.0 | 1.0 | 381.4 |
| Tocandira | napalm | 9.073 | 7200 | 396.8 | 99.2 | 198.4 | 0.21 | 396.8 | 200.0 | 0.375 | 143.0 |
| Caipora | he | 18.96 | 112000 | 2953.6 | 328.2 | 656.4 | 0.7 | 1476.8 | 875.0 | 1.0 | 467.6 |
| Caipora | cluster | 18.96 | 100800 | 2658.2 | 295.4 | 590.7 | 0.63 | 1329.1 | 787.5 | 0.9 | 420.8 |
| Caipora | limpet | 18.96 | 104000 | 2953.6 | 328.2 | 609.5 | 0.65 | 1476.8 | 875.0 | 1.0 | 467.6 |
| Caipora | napalm | 18.96 | 48000 | 1265.8 | 140.6 | 281.3 | 0.3 | 632.9 | 250.0 | 0.429 | 200.4 |
| Caipora | emp | 18.96 | 32000 | 1097.0 | 121.9 | 187.5 | 0.2 | 548.5 | 130.0 | 0.371 | 143.3 |
| Caipora | torpedo | 9.433 | 48000 | 2544.2 | 282.7 | 565.4 | 0.6 | 1272.1 | 1000.0 | 0.861 | 421.1 |
| Mula-sem-Cabeça | he | 15.805 | 360000 | 11388.6 | 379.6 | 759.2 | 0.81 | 1423.6 | 937.5 | 1.0 | 518.1 |
| Mula-sem-Cabeça | cluster | 10.6 | 216000 | 10188.7 | 339.6 | 679.2 | 0.72 | 1273.6 | 843.8 | 0.895 | 486.5 |
| Mula-sem-Cabeça | limpet | 10.6 | 224000 | 11320.8 | 377.4 | 704.4 | 0.75 | 1415.1 | 937.5 | 0.994 | 540.5 |
| Mula-sem-Cabeça | napalm | 10.6 | 96000 | 4528.3 | 150.9 | 301.9 | 0.32 | 566.0 | 250.0 | 0.398 | 216.2 |
| Mula-sem-Cabeça | emp | 10.6 | 48000 | 2867.9 | 95.6 | 150.9 | 0.16 | 358.5 | 126.7 | 0.252 | 112.6 |
| Mula-sem-Cabeça | torpedo | 9.68 | 192000 | 9917.4 | 330.6 | 661.2 | 0.7 | 1239.7 | 1000.0 | 0.871 | 490.8 |
| Mula-sem-Cabeça | nuclear | 20.007 | 320000 | 7997.3 | 266.6 | 533.2 | 0.57 | 999.7 | 1111.1 | 0.702 | - |

- HE per tile: Tocandira 264.5 (early band 250-280), Caipora 328.2 (mid 312.5-340), Mula 379.6 (late 375-381, = Mapinguari 381). Progression: every mid mode <= 328.2 < late HE 379.6.
- Specials as fractions of HE: Piranha 0.90 (mid) / 0.895 (late); Carrapato 1.00 / 0.99; Boto 0.86 / 0.87; Taturana and Poraquê are support (direct only, DoT/drain not counted); Iara 266.6/tile = Boiúna 266.7.
- Against the vanilla launcher (938 explosive DPS/tile): ours are 529.0 / 656.4 / 759.2 explosive/tile (0.56 / 0.70 / 0.81 x). Why lower although deck-mounted: we fire over our own hull from anywhere, need no hull edge and ripple big salvos (alpha) that saturate PD; vanilla's per-tile number buys none of that.
- DPS per crew: 1058.0 / 1476.8 / 1423.6 (cap 1600; vanilla 670-1500).
- Credits per effective DPS: Tocandira 2.93, Caipora 4.27, Mula 6.76 (early guns 2.6-3.1, mid 3.1-4.0, Mapinguari 6.38, Boiúna 6.44).
- Alpha (spectacle, not sustained): Tocandira 19200 in 0.73 s, Caipora 112000 in 2.0 s (pops a SW large bubble), Mula 360000 in 3.1 s every 15.8 s - the same damage a Mapinguari deals in ~16 s, front-loaded, interceptable, limited to 2 per ship.

### 8.2 Overclock value against cost

| Launcher | Mode | Enabled | DPS x | OC eff/tile | Heat/missile | Heat/s avg (peak) | Radiators | Heat per +1 DPS | Vent parts (share) | OC trips/min |
|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | no | 1.442 | 381.4 | 100.0 | 220.7 (245.8) | 0.2 | 0.472 | 0 (0 %) | 5.72 |
| Tocandira | napalm | no | 1.442 | 143.0 | 100.0 | 220.7 (245.8) | 0.2 | 1.259 | 0 (0 %) | 5.72 |
| Caipora | he | yes | 1.425 | 467.6 | 850.0 | 1122.0 (1302.8) | 1.02 | 0.894 | 2 (6 %) | 15.33 |
| Caipora | cluster | yes | 1.425 | 420.8 | 850.0 | 1122.0 (1302.8) | 1.02 | 0.994 | 2 (6 %) | 15.33 |
| Caipora | limpet | yes | 1.425 | 467.6 | 850.0 | 1122.0 (1302.8) | 1.02 | 0.894 | 2 (6 %) | 15.33 |
| Caipora | napalm | yes | 1.425 | 200.4 | 850.0 | 1122.0 (1302.8) | 1.02 | 2.086 | 2 (6 %) | 15.33 |
| Caipora | emp | yes | 1.175 | 143.3 | 850.0 | 943.0 (1062.3) | 0.86 | 4.906 | 2 (6 %) | 12.64 |
| Caipora | torpedo | yes | 1.489 | 421.1 | 2550.0 | 905.3 (922.6) | 0.82 | 0.727 | 0 (0 %) | 11.37 |
| Mula-sem-Cabeça | he | yes | 1.365 | 518.1 | 800.0 | 3465.7 (4695.5) | 3.15 | 0.834 | 6 (6 %) | 52.84 |
| Mula-sem-Cabeça | cluster | yes | 1.432 | 486.5 | 1600.0 | 3609.5 (4150.0) | 3.28 | 0.819 | 4 (6 %) | 55.14 |
| Mula-sem-Cabeça | limpet | yes | 1.432 | 540.5 | 1600.0 | 3609.5 (4150.0) | 3.28 | 0.737 | 4 (6 %) | 55.14 |
| Mula-sem-Cabeça | napalm | yes | 1.432 | 216.2 | 1600.0 | 3609.5 (4150.0) | 3.28 | 1.843 | 4 (6 %) | 55.14 |
| Mula-sem-Cabeça | emp | yes | 1.178 | 112.6 | 1200.0 | 2283.3 (2550.0) | 2.08 | 4.478 | 3 (6 %) | 34.0 |
| Mula-sem-Cabeça | torpedo | yes | 1.485 | 490.8 | 4800.0 | 3094.8 (3188.0) | 2.81 | 0.644 | 0 (0 %) | 44.17 |

- Reload / 1.5 on every mode except EMP (/ 1.2) and nuclear (none) -> x1.43 (Caipora) / x1.37 (Mula HE) sustained DPS; ripple, damage and range unchanged, so the interception math is unchanged.
- Caipora OC 467.6/tile, Mula OC 518.1/tile (max 540.5, cap 550). Early OC is designed (would be 381.4/tile) but disabled.
- Heat per +1 effective DPS 0.83-0.89 on HE (Tambor 0.71, Furacão 0.88) charged per part loaded, plus the vent (6.25 % of the salvo's parts) - two real costs besides OC reset and the cook-off chain.
- Torpedo modes pay heat per part loaded (Boto 12 parts = 4800 heat per torpedo on the Mula) but no vent; the Iara pays nothing because overclock does nothing to it.

### 8.3 Point-defense saturation (one salvo; share of warheads reaching the hull)

Judge model (VERDICT_balance §2.6), extended: launch at max range, constant acceleration; PD shot latency 0.3 s, PD keeps its target (earliest impact) until it dies or impacts; airburst defenders at real trigger rates; LOCK = all airbursts of a trigger land on one target and catch up to lock_catch members of its clump (children / decoys); RETARGET = every airburst picks a fresh target (pessimistic bound for missiles); children spawn at 25 m with HealthFactor; torpedo decoys spawn at 1.5 s, half fly just ahead of the warhead. Multi-defender scenarios run every mount in parallel on the same salvo. Ideal aim, no overkill waste -> real swarms leak more.

Defenders: vanilla PD 180/shot 15/s 200 m; Saci 95/shot 14/s 300 m; SW PD4 1250/shot 6.67/s 250 m; Tatu 1000 pool 3/s 180 m; vanilla flak 3000 pool 4/s 150 m; Tamanduá 3 x 2000 per trigger 1.67/s 250 m; Pororoca 2 x 4000 per trigger 1.5/s 320 m.

| Launcher | Mode | Warheads | 1 vPD | 2 vPD | Saci | SW PD4 | Tatu | vFlak | Taman. LOCK | Taman. RETGT | Poro. LOCK | Poro. RETGT | Taman.+vPD | Layered late |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | 12 | 58 % | 0 % | 33 % | 0 % | 50 % | 50 % | 67 % | 17 % | 58 % | 25 % | 42 % | 0 % |
| Caipora | he | 16 | 88 % | 44 % | 94 % | 0 % | 88 % | 31 % | 62 % | 0 % | 62 % | 31 % | 56 % | 0 % |
| Caipora | cluster | 64 | 88 % | 31 % | 94 % | 0 % | 92 % | 28 % | 56 % | 3 % | 56 % | 27 % | 56 % | 0 % |
| Caipora | emp | 16 | 94 % | 81 % | 94 % | 56 % | 88 % | 31 % | 62 % | 0 % | 62 % | 31 % | 62 % | 0 % |
| Caipora | torpedo | 2 | 100 % | 50 % | 100 % | 0 % | 100 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |
| Mula-sem-Cabeça | he | 48 | 100 % | 98 % | 100 % | 92 % | 98 % | 69 % | 85 % | 85 % | 85 % | 73 % | 85 % | 56 % |
| Mula-sem-Cabeça | cluster | 96 | 100 % | 88 % | 100 % | 77 % | 98 % | 58 % | 75 % | 73 % | 71 % | 53 % | 75 % | 23 % |
| Mula-sem-Cabeça | emp | 16 | 100 % | 94 % | 100 % | 88 % | 94 % | 56 % | 75 % | 75 % | 75 % | 56 % | 75 % | 38 % |
| Mula-sem-Cabeça | torpedo | 4 | 100 % | 100 % | 100 % | 75 % | 100 % | 75 % | 50 % | 50 % | 50 % | 50 % | 50 % | 0 % |
| Mula-sem-Cabeça | nuclear | 2 | 100 % | 100 % | 100 % | 50 % | 100 % | 50 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % |

- EARLY: one Tocandira salvo leaks 58 % past ONE vanilla PD (target 40-60 %), 0 % past two; 380 HP = 3 vanilla PD shots; 12 micro-missiles 1/15 s apart.
- MID HE vs one Tamanduá: 62 % under LOCK, 0 % under RETARGET - the CIWS model decides almost everything (test T10).
- PIRANHA (mid): 88 % vs one vanilla PD, 92 % vs Tatu, 56 % vs Tamanduá LOCK: about HE's share (within ~6 points) at 90 % of HE's damage, spread over many parts; big-radius flak is its counter.
- MULA HE: 56 % of 48 heads through the layered late defense (Pororoca + 2 Tamanduá + 2 vanilla PD) - the 48-missile stampede is the strongest saturation tool in the roster.
- TORPEDOES: the late Boto leaks 50 % past one Tamanduá (6500 HP needs two triggers, decoys spend triggers) and 0 % past the layered defense; Iara 0 % alone against any CIWS/heavy flak - by design.
- SW PD4 (1250 per shot) erases mid salvos; only the Mula saturates it. Intended: SW missiles (7000-9800 HP) stay the strongest missiles in SW; ours stay at vanilla scale.

Combined arms (layered late defense; the Iara pair launches at t = 0, the masking salvo at +delay):

| Mask | Mask delay s | Iara landed (of 2) | Mask warheads landed |
|---|---|---|---|
| he | 0 | 0 | 27 / 48 |
| he | 1 | 2 | 28 / 48 |
| he | 2 | 2 | 29 / 48 |
| he | 3 | 1 | 28 / 48 |
| he | 4 | 0 | 27 / 48 |
| cluster | 0 | 0 | 22 / 96 |
| cluster | 1 | 0 | 22 / 96 |
| cluster | 2 | 1 | 22 / 96 |
| cluster | 3 | 1 | 33 / 96 |
| cluster | 4 | 0 | 30 / 96 |
| 2 Caipora HE | 1 | 0 | 13 / 32 |
| 2 Caipora HE | 2 | 1 | 13 / 32 |
| 2 Caipora HE | 3 | 2 | 14 / 32 |

Iara pair launched first, masking salvo launched 1-3 s later (heavy missiles fly ~3.8 s to 600 m, torpedoes ~7.8 s): both warheads land through the layered late defense with a Mula HE mask at +1 s / +2 s. Same time or later = both die. Timing is the skill (B's 'tiro, porrada e bomba' hook, with the timing corrected).

### 8.4 Ammo logistics

| Launcher | Mode | Part | Parts/min | Trips/min | Factories | cr/s | RecCrew | Stock (missiles) | Stock (s) | Trips per 1000 eff DPS | Eff DPS per factory | OC trips/min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | he | 39.7 | 3.97 | 0.2 | 5.29 | 3.6 | 36.0 | 27.2 | 3.75 | 5333.0 | 5.72 |
| Tocandira | napalm | thermal | 39.7 | 3.97 | 0.2 | 7.94 | 3.6 | 36.0 | 27.2 | 10.0 | 2000.0 | 5.72 |
| Caipora | he | he | 101.3 | 10.13 | 0.51 | 13.5 | 8.8 | 48.0 | 56.9 | 3.43 | 5833.0 | 15.33 |
| Caipora | cluster | he | 101.3 | 10.13 | 0.51 | 13.5 | 8.8 | 48.0 | 56.9 | 3.81 | 5250.0 | 15.33 |
| Caipora | limpet | he | 101.3 | 10.13 | 0.51 | 13.5 | 8.8 | 48.0 | 56.9 | 3.43 | 5833.0 | 15.33 |
| Caipora | napalm | thermal | 101.3 | 10.13 | 0.51 | 20.25 | 8.8 | 48.0 | 56.9 | 8.0 | 2500.0 | 15.33 |
| Caipora | emp | emp | 101.3 | 10.13 | 0.84 | 33.76 | 8.8 | 48.0 | 56.9 | 9.23 | 1300.0 | 12.64 |
| Caipora | torpedo | he | 76.3 | 7.63 | 0.38 | 10.18 | 7.1 | 12.7 | 59.7 | 3.0 | 6667.0 | 11.37 |
| Mula-sem-Cabeça | he | he | 364.4 | 36.44 | 1.82 | 48.59 | 32.3 | 144.0 | 47.4 | 3.2 | 6250.0 | 52.84 |
| Mula-sem-Cabeça | cluster | he | 362.3 | 36.23 | 1.81 | 48.3 | 32.2 | 64.0 | 42.4 | 3.56 | 5625.0 | 55.14 |
| Mula-sem-Cabeça | limpet | he | 362.3 | 36.23 | 1.81 | 48.3 | 32.2 | 64.0 | 42.4 | 3.2 | 6250.0 | 55.14 |
| Mula-sem-Cabeça | napalm | thermal | 362.3 | 36.23 | 1.81 | 72.45 | 32.2 | 64.0 | 42.4 | 8.0 | 2500.0 | 55.14 |
| Mula-sem-Cabeça | emp | emp | 271.7 | 27.17 | 2.26 | 90.57 | 26.1 | 48.0 | 31.8 | 9.47 | 1267.0 | 34.0 |
| Mula-sem-Cabeça | torpedo | he | 297.5 | 29.75 | 1.49 | 39.67 | 27.8 | 20.0 | 48.4 | 3.0 | 6667.0 | 44.17 |
| Mula-sem-Cabeça | nuclear | nuke | 48.0 | 4.8 | 0.4 | 28.79 | 11.2 | 6.0 | 60.0 | 0.6 | 20000.0 | - |

- HE crew trips/min: Tocandira 3.97, Caipora 10.13, Mula 36.44 (our guns: Carcará 3.75, Tambor 8.33, Trovão 16, Mapinguari 30); vanilla HE launcher 12 trips/min for 3750 effective DPS = 3.2 trips per 1000 effective DPS; ours 3.2-3.75.
- HE factories: 0.2 / 0.51 / 1.82; RecCrew (vanilla formula) 3.6 / 8.8 / 32.3 - the Mula needs a real logistics deck.
- Internal stock = rack + 2 salvos of parts per family = 3 salvos: 27 s (Tocandira), 57 s (Caipora), 47 s (Mula HE) of fire; our guns hold 12-32 s - missiles carry more because the crewed reload is the real limiter and a full stock is a cook-off liability.

### 8.5 EMP and shields

| Launcher | Drain/missile | Drain per EMP part | SW shield HP per salvo | per tile per s | OC per tile per s | Cap |
|---|---|---|---|---|---|---|
| Caipora | 3000 | 1500.0 | 120000.0 | 703.2 | 826.4 | 750 |
| Mula-sem-Cabeça | 4500 | 1500.0 | 180000.0 | 566.0 | 666.7 | 750 |

1500 drain per EMP part (vanilla 2000), <= 750 SW shield HP per tile per second, and no salvo erases a SW giga bubble (320000): Caipora salvo 120000 (pops SW large 80000 - noted alpha), Mula salvo 180000. The EMP autoloader overclocks only / 1.2, so the overclocked rate stays under the mod's plasma OC cap of 880.

- Every missile is SimpleHit (penetration 0): it pops on the bubble edge, so against SW bubbles HE salvos are shield-breakers first (Caipora 112000, Mula 360000, Boto 4 x 36000 operational).
- Piranha: the carrier opens on the bubble and children spend themselves on it (no bypass). Carrapato: no stick on shields, only the pop (43 % of HE). Taturana: generator heat + blast.

### 8.6 Cook-off, napalm bound, limpet, nuclear rule

| Launcher | HE parts at full | HE blast (op + struct) | per HE part | Thermal heat dump | EMP drain | Nuke blast |
|---|---|---|---|---|---|---|
| Tocandira | 18 | 11500 + 3800 | 850.0 | 4500 | - | - |
| Caipora | 96 | 61200 + 20400 | 850.0 | 24000 | 57600 | - |
| Mula-sem-Cabeça | 288 | 183600 + 61200 | 850.0 | 64000 | 86400 | 72000 + 24000 |

~850 explosive per stored HE part (band 600-1000; vanilla 3333 over 12 parts): Tocandira 15300 at 18 parts, Caipora 81600 at 96, Mula 240000 at 288 + 96000 more with nuclear parts aboard. A loaded Mula is the ship's most dangerous part. Racks are counted in missile units inside Stock_<family> (a rack missile weighs as 1 part, S2) - this under-states rack weight slightly and never duplicates parts.

| Launcher | Napalm direct eff/tile | Max burning tiles per salvo | DoT bound DPS | DoT bound per tile | Total bound per tile | HE eff/tile |
|---|---|---|---|---|---|---|
| Tocandira | 99.2 | 12 | 336 | 84.0 | 183.2 | 264.5 |
| Caipora | 140.6 | 32 | 896 | 99.6 | 240.2 | 328.2 |
| Mula-sem-Cabeça | 150.9 | 64 | 1792 | 59.7 | 210.6 | 379.6 |

Fire does at most 28 damage/s per burning tile (DAMAGE_PER_TICK 7 every 0.25 s at full value) until the part scorches; even if a whole salvo's tiles burn unattended, napalm stays below HE per tile -> it is not a hidden DPS mode. Zero on armor/structure.

- **Limpet.** The limpet's charge is centred inside the first part hit (a surface blast wastes up to half its circle on space), so 1.0x HE sustained already favours it slightly; the 2.5 s fuse, shield weakness (43 % pop) and the first-part-only rule pay for it. CrewKillChance is a bonus not counted in DPS.
- **Nuclear rule.** Two Mula (bs_limit_nuke max, shared with Boiúna) on Iara = 4 torpedoes per 20.007 s = 1 per 5.0 s = two Boiúna (1 per 10 s each). 120000 r9 + 40000 r7 per torpedo (Boiúna 150000 r8 + 40000 r6); 8 nuke parts (288 cr) per torpedo; HP 6500 (Boiúna 7500); overclock never shortens it.

### 8.7 SW:ACD sanity

- Category 'missile' on every missile, child, decoy (vanilla PD/flak, SW PD4, SW blaster PD, SW flak all engage them); the limpet charge is untargetable on purpose.
- No SW type or field on the default path (no Repeating, SourceShip*, TargetHomingComponent, &/SW_*, SW layers/categories/toggles); the only SW-only type sits in one isolated build-flag variant file.
- Vanilla missile parts shared with SW launchers; EMP below vanilla per part; HP <= 2800 except torpedoes (SW 7000-9800); range <= 600 (SW 1250).
- Our launchers store no battery and are not uses_power: SW ion/disruptor (and our own EMP) do nothing to them.

### 8.8 Hard limits (asserted by the generator)

| Check | Value | Limit | OK |
|---|---|---|---|
| Tocandira he: HE eff/tile in tier band | 264.5 | 250.0-280.0 | yes |
| Tocandira he: OC eff/tile <= 550 | 381.4 | <= 550 | yes |
| Tocandira he: eff DPS/crew <= 1600 | 1058.0 | <= 1600 | yes |
| Tocandira he: eff per bullet-eq 700-1050 | 800.0 | 700-1050 | yes |
| Tocandira he: range <= tier cap | 300 | <= 300 | yes |
| Tocandira napalm: eff/tile <= tier cap | 99.2 | <= 280.0 | yes |
| Tocandira napalm: OC eff/tile <= 550 | 143.0 | <= 550 | yes |
| Tocandira napalm: eff DPS/crew <= 1600 | 396.8 | <= 1600 | yes |
| Tocandira napalm: range <= tier cap | 300 | <= 300 | yes |
| Caipora he: HE eff/tile in tier band | 328.2 | 312.5-340.0 | yes |
| Caipora he: OC eff/tile <= 550 | 467.6 | <= 550 | yes |
| Caipora he: eff DPS/crew <= 1600 | 1476.8 | <= 1600 | yes |
| Caipora he: eff per bullet-eq 700-1050 | 875.0 | 700-1050 | yes |
| Caipora he: range <= tier cap | 400 | <= 450 | yes |
| Caipora cluster: eff/tile <= tier cap | 295.4 | <= 340.0 | yes |
| Caipora cluster: OC eff/tile <= 550 | 420.8 | <= 550 | yes |
| Caipora cluster: eff DPS/crew <= 1600 | 1329.1 | <= 1600 | yes |
| Caipora cluster: eff per bullet-eq 700-1050 | 787.5 | 700-1050 | yes |
| Caipora cluster: range <= tier cap | 400 | <= 450 | yes |
| Caipora cluster: carrier HP <= HE HP | 1050 | <= 1050 | yes |
| Caipora cluster: children total <= 90 % of HE per part | 0.9 | <= 0.9 | yes |
| Caipora cluster: children per carrier <= 6 | 4 | <= 6 | yes |
| Caipora cluster: carriers per salvo <= 16 | 16 | <= 16 | yes |
| Caipora cluster: children per salvo <= 96 | 64 | <= 96 | yes |
| Caipora limpet: eff/tile <= tier cap | 328.2 | <= 340.0 | yes |
| Caipora limpet: OC eff/tile <= 550 | 467.6 | <= 550 | yes |
| Caipora limpet: eff DPS/crew <= 1600 | 1476.8 | <= 1600 | yes |
| Caipora limpet: eff per bullet-eq 700-1050 | 875.0 | 700-1050 | yes |
| Caipora limpet: range <= tier cap | 400 | <= 450 | yes |
| Caipora napalm: eff/tile <= tier cap | 140.6 | <= 340.0 | yes |
| Caipora napalm: OC eff/tile <= 550 | 200.4 | <= 550 | yes |
| Caipora napalm: eff DPS/crew <= 1600 | 632.9 | <= 1600 | yes |
| Caipora napalm: range <= tier cap | 400 | <= 450 | yes |
| Caipora emp: eff/tile <= tier cap | 121.9 | <= 340.0 | yes |
| Caipora emp: OC eff/tile <= 550 | 143.3 | <= 550 | yes |
| Caipora emp: eff DPS/crew <= 1600 | 548.5 | <= 1600 | yes |
| Caipora emp: range <= tier cap | 400 | <= 450 | yes |
| Caipora emp: drain per EMP part <= 1500 | 1500.0 | <= 1500 | yes |
| Caipora emp: SW shield HP/tile/s <= 750 | 703.2 | <= 750 | yes |
| Caipora emp: EMP salvo < SW giga bubble 320000 | 120000.0 | < 320000 | yes |
| Caipora emp: OC SW shield HP/tile/s <= 880 (plasma OC cap) | 826.4 | <= 880 | yes |
| Caipora torpedo: eff/tile <= tier cap | 282.7 | <= 340.0 | yes |
| Caipora torpedo: OC eff/tile <= 550 | 421.1 | <= 550 | yes |
| Caipora torpedo: eff DPS/crew <= 1600 | 1272.1 | <= 1600 | yes |
| Caipora torpedo: eff per bullet-eq 700-1050 | 1000.0 | 700-1050 | yes |
| Caipora torpedo: range <= tier cap | 400 | <= 450 | yes |
| Caipora torpedo: torpedo >= 80000/shot needs a per-ship limit | 24000 | >= 80000 -> limited | yes |
| Mula-sem-Cabeça he: HE eff/tile in tier band | 379.6 | 375.0-381.0 | yes |
| Mula-sem-Cabeça he: OC eff/tile <= 550 | 518.1 | <= 550 | yes |
| Mula-sem-Cabeça he: eff DPS/crew <= 1600 | 1423.6 | <= 1600 | yes |
| Mula-sem-Cabeça he: eff per bullet-eq 700-1050 | 937.5 | 700-1050 | yes |
| Mula-sem-Cabeça he: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça cluster: eff/tile <= tier cap | 339.6 | <= 381.0 | yes |
| Mula-sem-Cabeça cluster: OC eff/tile <= 550 | 486.5 | <= 550 | yes |
| Mula-sem-Cabeça cluster: eff DPS/crew <= 1600 | 1273.6 | <= 1600 | yes |
| Mula-sem-Cabeça cluster: eff per bullet-eq 700-1050 | 843.8 | 700-1050 | yes |
| Mula-sem-Cabeça cluster: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça cluster: carrier HP <= HE HP | 2200 | <= 2200 | yes |
| Mula-sem-Cabeça cluster: children total <= 90 % of HE per part | 0.9 | <= 0.9 | yes |
| Mula-sem-Cabeça cluster: children per carrier <= 6 | 6 | <= 6 | yes |
| Mula-sem-Cabeça cluster: carriers per salvo <= 16 | 16 | <= 16 | yes |
| Mula-sem-Cabeça cluster: children per salvo <= 96 | 96 | <= 96 | yes |
| Mula-sem-Cabeça limpet: eff/tile <= tier cap | 377.4 | <= 381.0 | yes |
| Mula-sem-Cabeça limpet: OC eff/tile <= 550 | 540.5 | <= 550 | yes |
| Mula-sem-Cabeça limpet: eff DPS/crew <= 1600 | 1415.1 | <= 1600 | yes |
| Mula-sem-Cabeça limpet: eff per bullet-eq 700-1050 | 937.5 | 700-1050 | yes |
| Mula-sem-Cabeça limpet: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça napalm: eff/tile <= tier cap | 150.9 | <= 381.0 | yes |
| Mula-sem-Cabeça napalm: OC eff/tile <= 550 | 216.2 | <= 550 | yes |
| Mula-sem-Cabeça napalm: eff DPS/crew <= 1600 | 566.0 | <= 1600 | yes |
| Mula-sem-Cabeça napalm: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça emp: eff/tile <= tier cap | 95.6 | <= 381.0 | yes |
| Mula-sem-Cabeça emp: OC eff/tile <= 550 | 112.6 | <= 550 | yes |
| Mula-sem-Cabeça emp: eff DPS/crew <= 1600 | 358.5 | <= 1600 | yes |
| Mula-sem-Cabeça emp: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça emp: drain per EMP part <= 1500 | 1500.0 | <= 1500 | yes |
| Mula-sem-Cabeça emp: SW shield HP/tile/s <= 750 | 566.0 | <= 750 | yes |
| Mula-sem-Cabeça emp: EMP salvo < SW giga bubble 320000 | 180000.0 | < 320000 | yes |
| Mula-sem-Cabeça emp: OC SW shield HP/tile/s <= 880 (plasma OC cap) | 666.7 | <= 880 | yes |
| Mula-sem-Cabeça torpedo: eff/tile <= tier cap | 330.6 | <= 381.0 | yes |
| Mula-sem-Cabeça torpedo: OC eff/tile <= 550 | 490.8 | <= 550 | yes |
| Mula-sem-Cabeça torpedo: eff DPS/crew <= 1600 | 1239.7 | <= 1600 | yes |
| Mula-sem-Cabeça torpedo: eff per bullet-eq 700-1050 | 1000.0 | 700-1050 | yes |
| Mula-sem-Cabeça torpedo: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça torpedo: torpedo >= 80000/shot needs a per-ship limit | 48000 | >= 80000 -> limited | yes |
| Mula-sem-Cabeça nuclear: eff DPS/crew <= 1600 | 999.7 | <= 1600 | yes |
| Mula-sem-Cabeça nuclear: range <= tier cap | 600 | <= 600 | yes |
| Mula-sem-Cabeça nuclear: torpedo >= 80000/shot needs a per-ship limit | 160000 | >= 80000 -> limited | yes |
| Progression: every mid mode < late HE | 328.2 | < 379.6 | yes |
| Nuclear parity: 2 Mula (pool max) -> >= 5 s per nuclear torpedo | 5.002 | >= 5.0 | yes |
| Nuclear torpedo: no OC on reload | no_oc | True | yes |
| Early salvo leak vs ONE vanilla PD in 40-60 % | 0.583 | 0.40-0.60 | yes |
| Tocandira: cook-off per stored HE part 600-1000 | 850.0 | 600-1000 | yes |
| Caipora: cook-off per stored HE part 600-1000 | 850.0 | 600-1000 | yes |
| Mula-sem-Cabeça: cook-off per stored HE part 600-1000 | 850.0 | 600-1000 | yes |

## 9. Test plan (dev mode, 0.30.4 and 0.30.5 RC4, with and without SW:ACD)

| # | Question | How | Pass | Fallback (no number changes) |
|---|---|---|---|---|
| T01 | Load and lint | build_mod.py --no-art, rules_lint.py, schema_check.py --extra SW on 0.30.4 and 0.30.5 RC4, with and without SW:ACD. | 0 errors; no 0.30.5-only global referenced | - |
| T02 | Rack latch hysteresis (gap Q7) | Caipora HE vs dummy: watch overlays + ProgressBar; kill the target mid-salvo. | rack fills 0->16, fires 16 in a row, loader idle while latched; rest of an interrupted salvo goes to the next target | IsSalvoActive Timer + RackFull_k gate (sketch footer); same timings |
| T03 | Crewed-only reload | Unassign the crew with a half rack; reassign. | rack frozen, magazine still accepts deliveries, resumes when crewed | add PartCrew explicitly to LoaderOn_k |
| T04 | Cross-mode exploit | Fill HE rack, switch to Piranha, fire, switch back at once; also switch mid-salvo; OC on/off. | the HE rack waits ModeSwitchDelay_he (one HE reload, /1.5 under OC); never two salvos back to back | single part-level ModeSwitchDelay with the longest duration (A's version) |
| T05 | DryFlush partial salvo | Give the HE family 5 parts and an empty rack. | loads 2 missiles, fires the 2, no lock-up; slow resupply fires in trickles (accepted behaviour) | drop DryFlush (stranded missiles wait for resupply) |
| T06 | Deck launch over own hull (gap Q4) | Launchers boxed in by armor and deck turrets; slowest missile (torpedo) from an off-centre cell; targets behind the ship. | no HitFriendly fizzles on our parts, pod or neighbouring turrets | SourcePartCollisionDelay 0.05 -> 0.3 s on that shot |
| T07 | Homing avoidance over own hull (gap Q5) | 3 variants: AvoidanceRaycastDistance omitted (default) / 250 / AvoidsFriendlies = false. | no braking or swerving right after launch | use the best variant (no balance number) |
| T08 | Allied hulls (gap Q6) | Two allied ships in line of fire. | documented (deck shells behave the same) | tooltip line only |
| T09 | Our CIWS/flak vs our own missiles (gap Q9) | Fire Piranha and HE salvos through our own Tamanduá airbursts and Pororoca Flak Wall field. | no own losses | explicit enemies-only filter on bs_cloud_ciws VolumeHit (defense file, no missile number) |
| T10 | CIWS LOCK vs RETARGET (balance §1) | Fire 16 missiles at 4/30 s ripple through ONE Tamanduá; count kills per trigger; repeat with Pororoca. | measure which model holds; re-run model.py with it | balance knob only: missile HP / ripple, never a mechanic change |
| T11 | Piranha: inheritance, magnet, spread (gap Q1/Q2) | 1 carrier at an off-axis target; log distinct parts hit; variant RandomizeTarget = true; burst one with an enemy 20 m from our big hull. | children home after .25 s and hit >= 3 parts; no friendly fizzles | magnet-only children; StartDelay 1.0; RandomizeTarget stays off |
| T12 | Piranha vs shields | SW and vanilla bubbles. | carrier opens on the bubble; children spend themselves on it | - |
| T13 | Performance | 2 Mula Piranha (192 children) + 4 Caipora Piranha (256) + enemy flak + our CIWS, 0.30.4 and 0.30.5. | >= 30 fps on the dev machine | strip child glow, delete the child Spacing component (Count unchanged) |
| T14 | Carrapato anchoring (gap Q10) + no PD lock | Target at full thrust and rotating; 16 limpets; enemy PD present. | charges ride the hull 2.5 s and blow on it; enemy PD does not fire at its own hull | F1 no magnet -> F2 status (T14b) -> F3 HitObject Speed-0 -> F4 impact blast; same numbers |
| T14b | Mod status registration (gap Q3) | AddMany a test Part status into <statuses/statuses.rules>/Statuses; apply StatusDuration 3, TickInterval 2.5; log tick timing; ExplosiveDamage vs Damage in TickingEffects. | loads on both versions; first tick at TickInterval | do not use F2 |
| T15 | Taturana napalm | Interior hit on an unarmored test ship, with and without extinguishers; 0.30.4 vs 0.30.5; gel-splash variant file. | fire on the hit part, heat >= 350 on 2-4 tiles, re-ignition 6-10 s; foam stops it; armor never burns | ApplyToAllHitPartTiles = true; gel stays off |
| T16 | Poraquê EMP | Vanilla shield + reactor ship; SW medium/large bubble; Bullet Strike gun ship. | drain on shields/batteries at the computed rate; nothing on BS guns; no friendly drain | drop the disruptor_drain rider; add ResourceDrain TreatShieldAsPart on HitShield |
| T17 | Torpedo stage + decoys | Watch the 1.5 s stage: warhead + N decoys from two SpawnBullets in one OnDeath; damage the stage first (HealthFactor). | 1 warhead + N decoys; decoys draw PD shots and flak pools; a damaged stage gives a damaged warhead | decoys from a second emitter (Burst N, BurstDelay 0.1, no ResourceStorage) |
| T18 | Nuclear rules | Build 2 Mula + try a Boiúna; 1 Mula + 1 Boiúna; Iara impact next to an ally; OC on in Iara mode. | 3rd platform refused; mix allowed; no ally damage; reload stays 9.97 s, no OC heat | ship without limits if CategoryLimits fail on 0.30.5 (as Boiúna) |
| T19 | Overclock costs + cook-off chain (gap Q12) | Caipora OC with radiators, then unpiped, rack full, continuous fire; then repair the scorch. | heat reaches the network; vent removes 2 parts per salvo; unpiped -> own-tile heat -> fire -> scorched -> family cook-off; NO cook-off on repair | if the vent misbehaves, delete it (heat costs remain) |
| T20 | Family cook-off | Destroy full launchers (HE, then thermal, EMP, nuke aboard). | blast scaled by each family's fill; a scorched launcher explodes once | - |
| T21 | Overlays | Pod rotates; overlays on roof_turrets over the pod on roof_doodads; per-pod RangeLow/RangeHigh; heavy/torpedo looks; interior view. | LIFO matches the count in every layout | one combined pod sprite per level |
| T22 | Cassette burst + tick ripple | Count Tocandira missiles and parts per salvo; measure real ripple on all three (4/30, 2/30). | 12 missiles per 6 parts; tube B 2/30 s after tube A; ripples as specified | C's twin-tube emitter (FireDelay 2/30, no ResourceStorage) + HoldTargetAfterCancel |
| T23 | AI behaviour | AI ships with each launcher vs PD-heavy targets. | fires full salvos, uses AIFirepowerRating | AIFirepowerRating x0.8 |
| T24 | Selector and unlocks | Career: each tech unlocks only its choice; AvailableChoices per launcher. | Tocandira 2 choices, Caipora 6, Mula 7 | separate ToggleIDs per launcher (bs_missile_type_s/_m/_l) |

## 10. Implementation notes (vanilla patterns to copy)

Path aliases: `R/` = /tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/research/vanilla_rules_0.30.5/ (vanilla 0.30.5 RC4); `RJ/` = /home/user/rojamahorse/cosmoteerupdates/ (vanilla RC4 on disk; commit ae16922 = 0.30.3, the 0.30.4 proxy); `SW/` = /tmp/claude-0/-home-user/f8886d0a-a310-5d28-bdb1-569b20620ed3/scratchpad/repos/main/ (SW:ACD, targets 0.30.4); `BS/` = /home/user/Cosmoteer/BulletStrike/ (our generated mod); `T/` = /home/user/Cosmoteer/tools/ (our generator); `NVL/NSM/NSW/NGEN/GAPS` = scratchpad/notes/missiles_vanilla_launcher.md / _special_mechanics.md / _swacd.md / _our_generator.md / _gaps.md.

| Topic | Copy from (file:line) | Note |
|---|---|---|
| Deck part shell | R/ships/terran/cannon_deck/cannon_deck.rules:35-36 (ProhibitedBy [tall] + ProhibitRects ring), :611 (FireInterval = 0 // separate fire timer), :617 (Emitter = BaseEmitterProxy 'only used for targeting'), :618 (IgnoreFriendlyShipLowLOSChecks), :817 (IsHigh collider), :895 (Type = EmitterProxy); T/bsgen/guns.py:347-348 (Emitter = TargetEmitterProxy, LOS flag), :367 (TurretCollider), :374/:382 (ShootCycle), :438 (EmitterProxy ChainedTo = Turret) | no ProhibitAbove; ring 1/1/2 tiles; TypeCategories without uses_power; base_med_part_terran(_overclock) / base_large_part_terran_overclock |
| Selector | R/ships/terran/missile_launcher/missile_launcher.rules:126-202 (UIToggle + ModeToggle + ToggledComponents, same names per block), :281-291 (TriggerProxy/ToggleProxy to the active block); RJ/ships/terran/point_defense/point_defense.rules:102 (AvailableChoices, also in 0.30.3); RJ/modes/career/techs.rules:112-119 (ToggleChoicesUnlocked = [[missile_type, 0]]); T/bsgen/guns.py:263/:268 (AmmoTypeToggle, ModeToggle_k); T/bsgen/infra.py:83 (part_toggles -> generalise to a list) | new ToggleID bs_missile_type, choices bs_missile_<type>, never vanilla missile_type or SW.missile_type |
| Family magazine + consumer | T/bsgen/guns.py:273-287 (MagStorage_k / MagConsumer_k); R/ships/terran/missile_launcher/he/missile_launcher_he.rules:13-46 storage fields, :89-98 consumer (NVL §3) | new magazine_block variant: one storage per resource family, consumer toggle All[CommandConsumptionToggle, Any[ModeToggle_k of the family]] (D-B7) |
| Crewed autoloader + OC divide | SW/ships/terran/weapons/small/discordmissile/dm_launcher.rules:109-176 (stock + timed storage->storage loader, shipped on 0.30.4); RJ/ships/terran/factory_he/factory_he.rules:212-227 (Interval { BaseValue; Modifiers [ Buff Factory Divide, BuffRemap Overclock Divide ] }, CheckResourceLimits) | OperationalToggle = LoaderOn_k (IsOperational contains PartCrew); nuclear loader has no Modifiers |
| Rack latch, progress, thresholds, triggers, negative change | RJ/ships/terran/thruster_boost/thruster_boost.rules:176-177 (ToggleOnResources = (&MaxResources) - 999 / ToggleOffResources = 0), :186 (ShowProgressFor = storage), :198-199 (threshold MultiResourceStorage FullAmmoToggle), :213-214 and :237-238 (ToggleTrigger TriggerWhenOn = false / TriggerWhenOff = true), :224 (ResourceChange Amount = -999999 on a storage) | latch, RackAny_k / MagCanLoad_k, ModeOn_k, vent |
| Timer with OC-modified Duration, StartExpired | railgun Overclock_ChargeTimer Duration { BaseValue; Modifiers } (NVL §10; RJ railgun_launcher.rules:413-436); chaingun Timer StartExpired (0.30.3 chaingun.rules:200-207, verified by the feasibility judge) | ModeSwitchDelay_k |
| Tick-aligned ripple | RJ/ships/terran/point_defense/point_defense.rules:365-367 (FireInterval BaseValue = 2/30); R/cosmoteer.rules:76 (PhysicsUpdatesPerSecond = 30) | RIPPLE = 4/30 (Tocandira cassette, Caipora) and 2/30 (Mula); cassette BurstDelay 2/30 |
| Cassette burst | BS/parts/bs_ciws/bs_ciws.rules:261-263 (Burst = 3; BurstDelay = 0.03; UseResourcePerShotInBurst = true -> the default false consumes one unit per burst); RJ/ships/terran/cannon_med/cannon_med.rules:512-526 (Burst / BurstDelay); RJ/ships/terran/chaingun/chaingun.rules:939 | Tocandira emitters: Burst = 2; BurstDelay = 2/30; ResourcesUsed = 1 |
| Cell overlays | RJ/ships/terran/cannon_med/cannon_med.rules:858-915 (ResourceSprites ChainedTo = Turret, RangeLow/RangeHigh 0-5 / 5-15); missile_launcher_he.rules:220-269 (HasZeroResourceSprite, one level per count, NVL §4) | pod on roof_doodads (1100), overlays on roof_turrets (1200); per-pod RangeLow/RangeHigh; LIFO fire order = reverse fill order |
| Cook-off | RJ/ships/terran/missile_launcher/he/missile_launcher_he.rules:271-276 (ScorchedTrigger TriggerWhenOn = false; TriggerWhenOff = true), :278-283 (ScorchedEffects FactorHitEffectsWith), :288-330 (DeathEffects 30000 r5 + CrewKillChance 50 % at :308 + 10000 r4); thermal heat dump: missile_launcher_thermal.rules:536-619 (NVL §9) | one DeathEffects per family OUTSIDE the toggled blocks; copy ScorchedTrigger verbatim (D-C1) |
| Missile core (deck-safe) | R/shots/missile_he/missile_he.rules:16-48 (TargetHoming / SameShipRetarget / Acceleration / NegativeAcceleration / DeathByLifetime), :110-123 (Targetable fizzle + SourcePartCollisionDelay) (NVL §7); R/shots/bullet_deck/bullet_deck.rules:40-41 (FriendlyShipLowCollisions = false), :159/:188 (BulletUpper3/4); T/bsgen/shots.py:94-122 (Upper sprites), :187/:273/:312 (deck flag), :294 (TargetHoming) | no AvoidanceRaycastDistance; no Friendlies = true; literals only |
| Piranha | SW/shots/missiles/discord/missile/missile_discord.rules:48-72 (DeathByEnemyProximity -> SpawnBullets), :75-96 (lifetime fallback), :170-172 (Hit groups = OnDeath); RJ/shots/bullet_large/overclock/bullet_large_overclock.rules:13-18 (Arc cone, InheritVelocity commented out = off); RJ/shots/mine/mine.rules:20-27 (repulsion); SW/shots/missiles/discord/buzz-droids/buzzdroid.rules:37-44 (magnet); RJ/shots/missile_nuke/missile_nuke_stage1.rules:46 (HealthFactor) | carrier + child in one folder; build_mod.shot_file kind 'missile' writes children first (flak_oc pattern T/build_mod.py:56-77) |
| Carrapato | SW/shots/missiles/discord/buzz-droids/buzzdroid.rules:37-44 (magnet) + :78-81 (PenetratingHit, PenetrationSpeed = 0.05); F2 status: RJ/statuses/disruptor_drain/disruptor_drain.rules:2-4, :25 (Layer = Part; ApplyNewInstance; TickInterval; ParentMediaEffectsToShip) + RJ/statuses/statuses.rules:5-12 (registry list); isolated variant: SW/shots/missiles/intruder/missile_intruder.rules:130-134 (Repeating, InitialDelay, RequireHitPart) | charge has NO Targetable; CrewKillChance in the BLAST (vanilla field, missile_launcher_he.rules:308) |
| Taturana | RJ/shots/bullet_med/bullet_med.rules:129-132 (StatusApplication cosmoteer.fire, StatusChance, ValueType = Interpolated); RJ/shots/bullet_large/overclock/bullet_large_overclock_shrapnel.rules:14, :113-114 (StatusValue = 30 %, Interpolated); RJ/shots/missile_thermal/missile_thermal.rules:128-139 (GridStatusApplication heat pool - write a literal pool instead of the RC-only APPLIED_HEAT_PER_MISSILE at :131), :173-174 (shield heat ApplyToAllHitPartTiles) | no ExplosiveDamage fire rider; no UseContiguity/AllowVertexContiguity |
| Poraquê | RJ/shots/missile_emp/missile_emp.rules:151-155 (ExplosiveResourceDrain TotalDrain / Radius / Slices), :182 (Damage), :192-196 (structural-only ExplosiveDamage); RJ/statuses/disruptor_drain (rider) | Filter without Friendlies |
| Boto / Iara | RJ/shots/missile_nuke/missile_nuke_stage1.rules:46 (HealthFactor), :141-160 (ExpandDuration / ExpandStartRadius op + structural blasts); BS/shots/bs_shot_nuke_howitzer_nuclear (mushroom media) | literals; no LinearDamping (constant accel 12 - nothing to fall back from, D-A4) |
| Overclock machinery | T/bsgen/common.py:83-88 (standard_toggles + OVERCLOCK_OPERATIONAL), :111-140 (overclock_machinery; Overclock_ShotHeatProducer :126, Overclock_ConstantHeatProducer :133); RJ/ships/base_part_overclock.rules:122-125 (OverclockReset Duration 3), :172-189 (OverflowHeatStorage, OverheatEffects); RJ/ships/terran/radiator/radiator.rules:191 (1100 heat/s); RJ/statuses/heat/heat.rules:12 (STATUS_TO_RESOURCE_RATIO = 1000); RJ/ships/terran/factory_he/factory_he.rules:272 (Overclock_ConversionHeatProducer) | per-mode Overclock_LoadHeat_k with Trigger = Autoloader_k instead of the emitter-proxy shot heat |
| Per-ship limit | BS/mod.rules:106-136 (CategoryLimits AddTo terran.rules; bs_limit_nuke Max = 2 at :116-117; CategoryNouns) | Mula TypeCategories += [uses_nukes, bs_limit_nuke]; no new category |
| Launch FX buckets | ships/terran/missile_launcher/particles/missile_launcher_shoot_flash.rules (Upper1, NGEN §2); avoid missile_launcher_shoot.rules (Middle3, under our roof); backblast cannon_smoke_deck / chaingun_shoot_smoke (Upper) | check_vanilla_paths verifies every path on --vanilla builds |
| Generator files | NGEN §12 checklist: T/bsgen/launchers.py (new), shots.py build_missile / build_missile_child / build_limpet_charge / build_torpedo, build_mod.py shot_file multi-file kinds, bs_data.py LAUNCHERS / MISSILE_CHOICES / 'missile:' techs / LIMITS, bs_strings.py, render_part.py kind 'launcher' + STYLE.md §8 | spec keys launchers / missile_types (+ missile_type_tables) as new top-level keys - never inside weapons[] (bs_data._convert assumes gun fields) |

- **Generator volume.** 212 BulletEmitter components in total (Tocandira 12, Caipora 82, Mula 118), generated by one loop; only one Fire_k block (<= 48 emitters) is active at a time. Mula heavy modes use 16 units (one 3-cell row each) to keep the emitter count, the charge bullets and the art matrix down. Shot files: HE x3, Piranha x2 (+2 child), Carrapato x2 (+2 charge, +2 isolated rep variants), Taturana x3, Poraquê x2, Boto x2 (+2 warhead, +2 decoy), Iara x1 (+warhead, +decoy) = 28 default files.
- **ID map.** early: rafaeltessaro.bs_msl_box (Tocandira); mid: rafaeltessaro.bs_msl_twin (Caipora); late: rafaeltessaro.bs_msl_quad (Mula-sem-Cabeça); shots: rafaeltessaro.bs_msl_<box|twin|quad>_<he|cluster|limpet|napalm|emp|torpedo|nuclear>[_child|_charge|_warhead|_decoy|_rep]; note: fixes the A/B ID collision (S3): box = early RAM box, twin = mid twin pods, quad = late quad battery.

## 11. Risks and fallbacks

| Risk | Level | Fallback |
|---|---|---|
| Limpet anchoring on a moving, rotating ship | MEDIUM-HIGH behaviour | F1-F4 chain, same fuse/blast (T14) |
| Cluster target inheritance + children's source ship | MEDIUM [INFERRED strong] | magnet children; StartDelay 1.0 (T11) |
| Rack latch hysteresis | LOW-MEDIUM [INFERRED strong] | IsSalvoActive + RackFull gate, same timings (T02) |
| CIWS LOCK vs RETARGET | balance only | re-run model.py; tune HP/ripple (T10) |
| Homing avoidance over own hull | MEDIUM | AvoidsFriendlies = false (T07) |
| Own IsHigh collider after 0.05 s | MEDIUM | FriendlyShipHighCollisions = false already; SourcePartCollisionDelay 0.3 s (T06) |
| Two SpawnBullets in one OnDeath (decoys) | LOW-MEDIUM | emitter decoys, same counts (T17) |
| Mod status registration (only for limpet F2) | MEDIUM | skip F2 (T14b) |
| Performance (<= 96 children per launcher salvo) | MEDIUM | visual strip + delete Spacing (T13) |
| Our CIWS cloud vs our missiles | LOW [INFERRED enemies-only] | enemies-only filter on the cloud (T09) |
| Tick alignment of FireInterval / BurstDelay | LOW | ripples are tick multiples; measure (T22) |
| CategoryLimits on 0.30.5 RC | LOW | ship without limits (as Boiúna/Mapinguari) |

## 12. Every judge defect and how it was resolved

| Judge | Design | Defect | Resolution |
|---|---|---|---|
| balance | A | Cook-off undersized (444/361 per HE part) | ~850 per stored HE part for every launcher (15300 / 81600 / 240000 at full). |
| balance | A | Hidden stock: per-mode magazines, cook-off inside Fire_k | One magazine per resource family + one cook-off per family OUTSIDE the toggled blocks (Stock_<family> counts magazine + all racks). |
| balance | A | Gorjala torpedo 100000/shot with no limit | Conventional torpedoes stay < 80000 (Boto 24000 / 48000 explosive); the only >= 80000 torpedo (Iara) rides the Mula, limited by bs_limit_nuke. |
| balance | A | Cluster spread claim contradicts 180 deg/s homing after 0.15 s | InheritVelocity = false, homing 110-120 deg/s after 0.25 s, magnet + spacing; part spread is a test item (T11). |
| balance | A/B/C | CIWS LOCK vs RETARGET untested | LOCK is the primary model, RETARGET the pessimistic bound in every table; test T10 calibrates it. |
| balance | A | EMP alpha note | Caipora EMP salvo 120000 SW shield HP (pops SW large) documented; no salvo reaches a giga bubble. |
| balance | B | EMP over cap (874/1015, 3500-4000 per part) | 1500 per EMP part; 703 / 566 SW shield HP per tile per s; Mula salvo 180000 (< 320000). |
| balance | B | Tocandira dead on arrival vs one vanilla PD | Micro-missile cassettes (12 in 0.73 s), 380 HP = 3 PD shots: 58 % leak vs one vanilla PD. |
| balance | B | Mula Piranha buses 4200 HP beat flak | Carrier HP = HE HP (2200). |
| balance | B | 240-480 children per volley | Mula Piranha = 16 buses x 6 = 96 children per salvo (192 for 2 Mula); Caipora 16 x 4 = 64. |
| balance | B | CIWS conclusions built on RETARGET | All interception tables recomputed with the judge's model, LOCK primary. |
| balance | B | Cook-off 271-306 per part | ~850 per part. |
| balance | B | SalvoCooldown holes (interrupted salvo, global duration) | Per-mode ModeSwitchDelay_k started on ANY switch into the mode, duration = that mode's full reload. |
| balance | B | Alpha concentration 360000 in 3.8 s | Kept as the endgame spectacle but bounded: 48 cells only on HE, 2 per ship (nuke pool), equal to ~16 s of Mapinguari damage front-loaded and fully interceptable; heavy modes use 16 units. |
| balance | C | Band violations (early 314, mid 418-447, OC 616-670, crew 1879-2011) | Early 264.5, mid 328.2, late 379.6; OC max 540.5; crew max 1556. |
| balance | C | Ranges 400 / 520 / 720 | 300 / 400 / 600 m (torpedo 400 on mid). |
| balance | C | Damage per bullet-eq Boto 1719, Sanguessuga 1188 | Boto 1000; limpet 875 / 937.5; nuclear 1111 (nuke excepted, Boiúna 1103). |
| balance | C | HP breakpoints moot under LOCK | HP now targets single-target PD breakpoints (micro 380 = 3 PD shots) and the LOCK trigger (late torpedo 6500 > 3 x 2000). |
| balance | C | Unload-on-switch fails when the magazine is full | Not used; ModeSwitchDelay_k is the primary fix. |
| balance | C | Vespeiro proximity 280 m | 25 m (Discord), StartDelay 0.4. |
| balance | C | OC vent taxes 2-cell Boto 50 % | Vent = CELLS/16 missiles (6.25 % of a salvo); torpedo and nuclear exempt. |
| balance | C | Limpet charge category 'mine' | No Targetable by default; optional defusable variant uses 'missile'. |
| balance | all | Factory efficiency not decided | Decided: accept the vanilla missile economy; v2 canister lever documented (resources_factories.factory_efficiency_decision). |
| balance | all | No napalm/limpet DoT bound | napalm_dot_upper_bound table: napalm <= HE per tile even if every burning tile is ignored; limpet 1.0x HE. |
| fidelity | A | No quad-pod launcher | Mula-sem-Cabeça: 4 pods x 3x4 = 48 cells (ref 4). |
| fidelity | A | Endgame under-delivered | Mula: 5x6, 8 crew, 18 CP, 77000 cr + 2 enriched uranium, nuke pool, 360000 alpha. |
| fidelity | A | No nuclear missile | Iara nuclear torpedo (Mula, bs_limit_nuke). |
| fidelity | A | Cluster's main job weak | Piranha with 25 m opening, cone, weak late homing, magnet + spacing; honest numbers in balance_checks (parity with HE vs PD at 90 % damage, multi-part spread). |
| fidelity | A | Modest micro salvo | 12 micro-missiles in 0.73 s from 6 twin-tube cassettes. |
| fidelity | A | Low excitement | B's skeleton (RAM box -> twin octagonal pods -> quad battery), Piranha, Boto decoys, Iara masking. |
| fidelity | B | No conventional torpedo | Boto decoy torpedo on the Caipora (2 per salvo) and the Mula (4 per salvo). |
| fidelity | B | Early launcher hard-countered | Cassette swarm, 380 HP, ~58 % leak vs one vanilla PD. |
| fidelity | B | Performance vs spectacle | <= 96 children per launcher salvo; perf fallback strips visuals/spacing only. |
| fidelity | B | Partial salvo postponed | DryFlush in v1. |
| fidelity | B | Limpet defusal beyond the user's rule | Default = user's literal rule (untargetable charge); defusable is an optional variant. |
| fidelity | B | Dual-pool limit unproven, crowds out Mapinguari | Single proven pool bs_limit_nuke; flagship pool untouched; dual pool only as an optional variant after T18. |
| fidelity | B | Emissive 'burning neck' | Collar recess uses M['ember'] (very dim), brighter only under OC; no flame particle by default; within the 1-2 % budget. |
| fidelity | C | 720 m range / DPS above bands / OC cap 688 / 280 m split / nuke outside limit / Stream toggle | All rejected: 600 m cap, bands, 550 OC cap, 25 m split, Iara in bs_limit_nuke, no Stream toggle. |
| fidelity | C | Thin selectors at both ends | Early 2 types (micro HE, micro napalm), mid 6, late 7. |
| fidelity | C | Less salvo spectacle | 12 / 16 / 48 visible tips. |
| fidelity | C | Endgame cost moderate | Mula 77000 cr, 18 CP, 8 crew, nuke pool. |
| fidelity | C | Arapuá tube without storage | Burst = 2 on one emitter per cassette (primary); C's twin-tube emitter is the fallback. |
| feasibility | A | D-A1 turret without Emitter | Turret Emitter = TargetEmitterProxy -> Emitter_0 of the active Fire_k; collider ChainedTo = Turret; Location given. |
| feasibility | A | D-A2 80-90 m fuse over own hull | 25 m, StartDelay 0.4 (fallback 1.0). |
| feasibility | A | D-A3 cook-off only for the selected mode | Per-family cook-off counting all stocks. |
| feasibility | A | D-A4 torpedo fallback changes a number | No LinearDamping at all: constant acceleration 12, nothing to fall back from. |
| feasibility | A | D-A5 limpet without magnet | Buzz-droid magnet + crawl (shipped SW combination). |
| feasibility | B | D-B1 Mula scale (242 emitters, 240 children) | 118 emitters (48 HE + 4 x 16 heavy + 4 + 2), 96 children per salvo. |
| feasibility | B | D-B2 Iara ripple without mechanism | Per-mode ShootCycle inside Fire_k; torpedoes use the launcher ripple. |
| feasibility | B | D-B3 napalm primary on raw gel value | StatusApplication fire (Interpolated) + heat pool primary; gel off until T15. |
| feasibility | B | D-B4 limpet charge Targetable 'missile' (own-hull PD lock) | No Targetable. |
| feasibility | B | D-B5 SalvoCooldown misses mid-salvo switch | ModeSwitchDelay_k on any switch. |
| feasibility | B | D-B6 two CategoryLimits pools | One pool (bs_limit_nuke). |
| feasibility | B | D-B7 family magazines = new code | Budgeted: new magazine_block variant (implementation_notes). |
| feasibility | C | D-C1 ScorchedTrigger fires on repair | Copied verbatim from vanilla (TriggerWhenOn = false; TriggerWhenOff = true), test T19. |
| feasibility | C | D-C2 280 m split over our deck | 25 m. |
| feasibility | C | D-C3 unload leak | Not used. |
| feasibility | C | D-C4 Stream toggle | Cut. |
| feasibility | C | D-C5 'mine' charge | No Targetable. |
| feasibility | C | D-C6 nuke outside bs_limit_nuke / 720 m | Inside; 600 m. |
| feasibility | C | D-C7 turret without Emitter | Fixed (see D-A1). |
| feasibility | C | D-C8 perf fallback changes Count/damage | Perf fallback strips visuals and the Spacing component only. |
| feasibility | C | D-C9 per-mode cell layouts | Three layout families only (fine / heavy-row / torpedo cassette), all via per-pod RangeLow/RangeHigh. |
| feasibility | C | D-C10 cassette tube B without storage | Burst 2 primary. |
| feasibility | shared | S1 open gap tests | All in test_plan (T06-T11, T14, T14b). |
| feasibility | shared | S2 rack weighting in cook-off | Documented approximation (rack missile = 1 unit); never duplicates parts. |
| feasibility | shared | S3 ID collision A/B | One ID map: box = early, twin = mid, quad = late. |

## 13. Apresentação para o usuário (pt-BR)

Três lançadores, um para cada fase. Todos são torres de convés (em cima do casco), operados só pela tripulação e **sem energia**.

### Como funciona (igual nos três)
- **Estoque interno:** cada lançador tem um paiol por tipo de peça (HE, térmica, PEM, nuclear). A tripulação carrega as peças de míssil do jogo base até ele. O estoque cheio dá 3 salvas.
- **Recarga automática:** um autocarregador passa um míssil por vez do paiol para as células visíveis. **Só funciona com tripulação no posto.** Com todas as células cheias, sai a salva em sequência e a recarga recomeça. Se o paiol acabar, a salva parcial sai mesmo assim.
- **Trocar de míssil não dá salva grátis:** ao trocar o tipo, o lançador espera um ciclo completo de recarga do tipo novo.
- **Overclock (só meio e fim):** a recarga fica 1,5 vez mais rápida (PEM: 1,2 vez). Custos: calor por peça carregada (precisa de radiador), cerca de 1 em cada 16 mísseis é descartado a cada salva, pausa de 3 s ao desligar, o paiol esvazia mais rápido e, sem radiador, o lançador esquenta, pega fogo e explode junto com o estoque. Nunca acelera o torpedo nuclear.
- **Lançador cheio é uma bomba:** destruído ou queimado, explode proporcional ao estoque (cerca de 850 de dano por peça HE guardada).

### Os lançadores
- **Início - Tocandira (Caixa de Micromísseis de Convés), 2x2, 1 tripulante.** Caixa estilo RAM com 6 cassetes de tubo duplo: 12 micromísseis em 0,73 s a cada 9,1 s, alcance 300 m. Mísseis: Muriçoca (alto-explosivo) e Taturana-mirim (incendiário). Contra um PD vanilla, cerca de 58 % da salva passa.
- **Meio - Caipora (Lançador de Mísseis de Convés de Casulo Duplo), 3x3, 2 tripulantes.** Dois casulos octogonais e uma cúpula com olho sensor: 16 mísseis em 2 s a cada 19,0 s, alcance 400 m. Mísseis: Jararaca, Piranha, Carrapato, Taturana, Poraquê e o torpedo Boto (2 por salva). Overclock: Fúria da Caipora.
- **Fim - Mula-sem-Cabeça (Bateria Pesada de Mísseis Quádrupla), 5x6, 8 tripulantes, 18 CP, 77000 créditos.** Corpo sem cabeça com quatro casulos de 3x4 em braços hidráulicos: 48 mísseis pesados em 3,1 s a cada 15,8 s, alcance 600 m. Tem todos os mísseis, inclusive o nuclear Iara. Divide a vaga nuclear com a Boiúna (no máximo 2 por nave, em qualquer combinação). Overclock: Estouro da Boiada.

### Os mísseis
- **Jararaca (Alto-Explosivo):** explosão padrão; é o míssil "normal" do SW. Em salva grande, satura a defesa de ponto.
- **Piranha (Submunições, o "Transformers 3"):** abre a 25 m do casco e solta 4 (meio) ou 6 (fim) minimísseis que se espalham e acertam várias peças. Faz 90 % do dano do HE. O contra é flak de área de raio grande.
- **Carrapato (Grudento):** se for abatido no voo, perde-se; se acertar o casco, gruda, pisca e explode 2,5 s depois, com 50 % de chance de matar a tripulação que vier consertar. Não gruda em escudo.
- **Taturana (Napalm):** explosão pequena, fogo garantido na peça atingida e calor em volta que continua acendendo incêndios. Extintor, espuma e blindagem são o contra.
- **Poraquê (PEM):** drena bateria e escudos em área (1500 por peça PEM, abaixo do PEM vanilla). Não afeta as armas do Bullet Strike.
- **Boto (Torpedo com Iscas):** torpedo lento e resistente que solta 4 a 6 iscas para enganar a defesa de ponto. Faz 24000 (meio) ou 48000 (fim) de dano explosivo.
- **Iara (Torpedo Nuclear, só na Mula):** 120000 + 40000, 2 por salva a cada 20 s. Sozinho morre para qualquer flak; dispare o Iara primeiro e uma salva HE 1 a 3 s depois para os dois chegarem juntos.

### O que é arriscado e precisa de teste no jogo
1. **Carrapato:** a carga grudar num navio que gira e acelera. Há 4 planos B com os mesmos números.
2. **Piranha:** os filhotes herdarem o alvo e não estourarem sobre o nosso casco. Plano B: ímã para o casco inimigo e atraso maior.
3. **Trava das células** (salva completa antes de recarregar). Plano B com temporizador.
4. **Mísseis sobre o próprio convés:** não podem bater na nossa torre nem desviar do nosso casco.
5. **Nosso CIWS contra os nossos mísseis**, e o modelo do CIWS (cada disparo mata 1 míssil ou vários). Isso muda os números de interceptação.
6. **Desempenho** com muitas submunições; **torpedo com iscas** (dois disparos no mesmo evento); **vaga nuclear** dividida com a Boiúna.

Todas as mecânicas usam componentes do jogo base, a categoria 'missile' (compatível com o SW:ACD) e funcionam no 0.30.4 e no 0.30.5. Cada risco tem um plano B que não muda nenhum número.

## Resumo (pt-BR)

| Codinome | Lançador | Fase | Tamanho | Trip. | Salva HE | Ciclo | Alcance | Mísseis | DPS efetivo/tile (OC) | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | Caixa de Micromísseis de Convés | início | 2x2 | 1 | 12 em 0,73 s | 9,1 s | 300 m | Muriçoca, Taturana-mirim | 264,5 (381,4, desligado) | Enxame Furioso (desligado) | sem |
| Caipora | Lançador de Mísseis de Convés de Casulo Duplo | meio | 3x3 | 2 | 16 em 2,00 s | 19,0 s | 400 m | Jararaca, Piranha, Carrapato, Taturana, Poraquê, Boto | 328,2 (467,6) | Fúria da Caipora | sem |
| Mula-sem-Cabeça | Bateria Pesada de Mísseis Quádrupla | fim | 5x6 | 8 | 48 em 3,13 s | 15,8 s | 600 m | Jararaca, Piranha, Carrapato, Taturana, Poraquê, Boto, Iara | 379,6 (518,1) | Estouro da Boiada | 2 por nave (vaga nuclear) |

## 14. Generator: mechanic variants and stages

Every risky mechanic is a **selectable variant** in the spec (`mechanic_variants`). The default is the primary design; each other option is the fallback named in the test plan. Switching a variant changes the generated mechanism only - no balance number (damage, HP, reload, ripple, cells, parts, range, cost). To build a fallback for a test: `BS_MSL_VARIANTS="rack_gate=salvo_timer,cassette=twin_emitter" python3 tools/build_mod.py ...`.

| variant | test | default | fallback option(s) | stage |
|---|---|---|---|---|
| `rack_gate` | T02 | `latch` | salvo_timer | 1 |
| `loader_crew_gate` | T03 | `is_operational` | explicit_partcrew | 1 |
| `mode_switch_delay` | T04 | `per_mode` | single_longest | 1 |
| `dry_flush` | T05 | `on` | off | 1 |
| `source_part_collision_delay` | T06 | `ticks_1_5` | s_0_3 | 1 |
| `homing_avoidance` | T07 | `omit` | raycast_250, no_avoid_friendlies | 1 |
| `cassette` | T22 | `burst` | twin_emitter | 1 |
| `cell_sync` | T21 | `reset_each_reload` | free_cycle | 1 |
| `overlays` | T21 | `per_pod` | combined | 1 |
| `napalm_fire` | T15 | `status_application` | all_hit_part_tiles | 1 |
| `napalm_gel` | T15 | `off` | on | 2 |
| `ai_firepower` | T23 | `full` | x0_8 | 1 |
| `selector_ids` | T24 | `shared` | per_launcher | 1 |
| `early_overclock` | - | `disabled` | enabled | 1 |
| `cluster_children` | T11 | `inherit_target_and_magnet` | magnet_only | 2 |
| `cluster_randomize_target` | T11 | `off` | on (experiment build only) | 2 |
| `limpet_anchor` | T14 / T14b | `F1` | F1_drill, F2, F3, F4 | 2 |
| `limpet_repeating` | T14 / Q11 | `off` | isolated_file (SW-only `_rep.rules`, no launcher fires it) | 2 |
| `limpet_defusable` | T14 | `off` | on (charge Targetable 500 / 600 'missile') | 2 |
| `emp_rider` | T16 | `on` | off | 2 |
| `emp_shield_drain` | T16 | `area` | single_part | 2 |
| `torpedo_decoys` | T17 | `spawn_on_stage` | emitter | 2 |
| `category_limits` | T18 | `on` | off | 2 |
| `ciws_vs_own_missiles` | T09 | `as_is` | enemies_only | 2 |
| `performance_strip` | T13 | `off` | on | 2 |

Generator stages (`tools/bs_data.py` `BUILD_LAUNCHERS` / `BUILD_PAYLOADS`):
- **Stage 1 (built):** Tocandira (`rafaeltessaro.bs_msl_box`) with Muriçoca (micro HE) and Taturana-mirim (micro incendiary); the whole launch logic (family magazines, crewed autoloader, rack latch, ripple salvo with LIFO cells, per-mode switch delay, DryFlush, per-family cook-off), the `bs_missile_type` selector with all 7 choices, techs `bs_msl_box` and `bs_msl_napalm`, placeholder art and the 3D art contract (`tools/blender/STYLE.md` section 8, `render_part.py` kind `launcher`). The OC wiring is generated and tested behind `early_overclock=enabled` but stays off (mod rule).
- **Stage 2 (built): payloads.** Every missile file of `missile_types[].variants[].files`, for every launcher tier, is generated (`tools/bsgen/shots.py`): Jararaca and Taturana on Caipora/Mula, Piranha (carrier with proximity / timed / impact BURST + child with late homing, hull magnet and missile spacing), Carrapato (missile + slow PenetratingHit charge with magnet and blinking beacon; fallbacks F1_drill, F2 Part status `rafaeltessaro.bs_limpet_<twin|quad>` registered in `statuses.rules`, F3 HitObject Speed-0 charge, F4 impact blast; isolated SW-only Repeating file behind `limpet_repeating`), Poraquê (area battery drain + direct hit + structural blast + disruptor_drain rider), Boto and Iara (1.5 s launch stage -> warhead + decoys from two SpawnBullets; Iara with the Boiúna mushroom). The numbers each payload needs beyond the variant tables are in `missile_types[].payload_params` (a structured copy of `payload_mechanic`, no new balance number). `tools/bs_data.py` aborts if a file list, the effective damage, the salvo alpha or a payload hard limit (children per carrier, children HP pool, carrier HP, drain per EMP part, torpedo >= 80000 needs a per-ship limit) differs from the spec. Files of launchers that are not built yet exist but no part fires them. The Mula's `bs_limit_nuke` category comes from the spec (`category_limits=off` strips it).
- **Stage 3 (built): Caipora and Mula-sem-Cabeça.** `BUILD_LAUNCHERS` holds all three launchers and every missile mode of the spec (`GENERATOR_STAGE = 3`).
  - Layouts (`tools/launcher_layout.py`): `fine16` with `pattern: "3-2-3"` pods and `torpedo2` (Caipora); `fine48`, `heavy16` (one 3-tube row = one heavy unit), `torpedo4` and `torpedo2_inner` (Mula; the outer pods show closed shutters, a `Graphics` inside `Fire_nuclear`). Each unit carries a `form` (`tube` / `heavy` / `torpedo`) and a nose `box` for the art.
  - Overclock on Caipora and Mula (spec `overclock.enabled`): Autoloader_k Interval and ModeSwitchDelay_k Duration divided by the per-mode factor (1.5, EMP 1.2, nuclear none), heat per part loaded (425 / 400) + constant heat (100 / 150 heat/s), vent of CELLS/16 missiles' parts per full rack (torpedo, nuclear and sub-16 salvos exempt), OC reset inherited, thermal ports, OC tooltip with the HE OC cycle, and an `OverclockGlowGraphics` (`turret_oc.png`, `IsOverclocked`) for the dome eye / collar ember.
  - Mula in `bs_limit_nuke` (Max 2, shared with the Boiúna; the limit noun becomes "Nuclear Weapon(s)" / "Arma(s) Nuclear(es)"); `category_limits=off` strips it.
  - FX presets per tier: Caipora shake 0.01 per launch, torpedoes with the vanilla nuke launch sound; Mula `cannon_smoke_deck` backblast, shake 0.02 and a 0.15 thump when the rack empties. With more than one pod the backblast puffs behind the pod that fired (`PodFired_<pod>` MultiTrigger inside each `Fire_k`).
  - `torpedo_decoys=emitter` (T17 fallback): a `DecoyEmitter_i` per torpedo cell (Burst = decoys, BurstDelay 0.1, no ResourceStorage) next to the single-stage torpedo.
  - Career techs (twin, cluster, emp, limpet, torpedo, twin-overclock, quad, nuclear, quad-overclock) and Build & Battle techs for Caipora and Mula (+ their overclocks; they also unlock the missile parts of their families, `ResourcesUnlocked`); the Tocandira stays on the B&B whitelist.
  - `tools/bs_data.py` also aborts if the overclocked cycle, the vent rule, the emitter count (`emitter_components`) or the cook-off stock (magazine + largest rack of the family, in parts = `cookoff[].parts_full`) differ from the spec, or if the overclock could touch the nuclear reload.
  - Art: procedural placeholders for both pods (`tools/bsgen/sprites.py`), the art contract in `tools/blender/STYLE.md` section 8 (forms, shutters, `turret_oc.png`) and `render_part.py` kind `launcher` with `cell(..., form, box)`, `shutter()` and `oc_glow()`.
- `tools/bs_data.py` aborts the build if the generated salvo size, salvo duration, cycle, alpha or cook-off stock differ from the `computed` numbers in this spec.
