"""mod.rules, strings, seletores (PartToggles), aba do editor, stats e techs do Bullet Strike 2.0 (dono: WP01)."""

from rules_dsl import Q, render
from bsgen import common as C

COMPAT = ["0.30.4", "0.30.4a", "0.30.4b", "0.30.4c", "0.30.5"]


def mod_description(spec, profile, body_pt, body_en):
    """Description bilingue do menu Mods: a 1a linha de CADA metade vem de SPEC.build_2_0.variants (nunca inventada
    aqui), depois o corpo, o aviso de ruptura limpa (SPEC.removed_ids.clean_break_texts) e SEMPRE a linha
    SPEC.vanilla_profile.sw_only_warning_ptbr/_en (J1R3-5)."""
    cb = spec["removed_ids"]["clean_break_texts"]
    vp = spec["vanilla_profile"]
    pt = "\n\n".join(x for x in (profile["description_first_line_ptbr"], body_pt,
                                 cb["readme_and_mod_description_ptbr"], vp["sw_only_warning_ptbr"]) if x)
    en = "\n\n".join(x for x in (profile["description_first_line_en"], body_en, cb["en"], vp["sw_only_warning_en"]) if x)
    return f"{pt}\n\n---\n\n{en}"


def mod_rules(data, part_paths, resource_paths, version, limits=(), status_paths=(), actions_extra=()):
    """data = {'description': texto}; limits = [(categoria, max, chave singular, chave plural)] de
    SPEC.category_limits; actions_extra = Actions dos modulos (gancho mod_actions(): o WP05 manda o Overrides dos
    buffs da fita, o WP09 o do railgun), inseridas depois das acoes do nucleo."""
    top = {
        "ID": C.MOD_ID,
        "Name": Q(C.MOD_NAME),
        "Version": version,
        "CompatibleGameVersions": [Q(v) for v in COMPAT],
        "UseThisFileIfNoVersionMatch": True,
        "ModifiesGameplay": True,
        "Author": Q("Rafael Tessaro"),
        "Logo": Q("logo.png"),
        "Description": Q(data["description"]),
        "StringsFolder": Q("strings"),
    }
    actions = []
    # 1) aba "Bullet Strike" no menu de construcao (padrao do Jani's Shipyard: Overrides inline)
    actions.append({
        "Action": "Overrides",
        "OverrideIn": Q("<gui/game/designer/editor_groups.rules>"),
        "Overrides": {
            C.EDITOR_GROUP: {
                "NameKey": Q(f"EditorGroups/{C.EDITOR_GROUP}"),
                "Icon": {"Texture": {"File": Q("gui/group_bullet_strike.png"), "MipLevels": 2, "SampleMode": "Linear"}},
                "SortOrder": 250,
            }
        },
    })
    # 2) recursos novos
    if resource_paths:
        actions.append({"Action": "AddMany", "AddTo": Q("<resources/resources.rules>/Resources"),
                        "ManyToAdd": [f"&<{p}>" for p in resource_paths]})
    # 3) pecas (so as escritas pelos modulos com API >= 2)
    if part_paths:
        actions.append({"Action": "AddMany", "AddTo": Q("<ships/terran/terran.rules>/Terran/Parts"),
                        "ManyToAdd": [f"&<{p}>/Part" for p in part_paths]})
    # 4) linhas de estatistica (nunca Replace: o pre-requisito do SW:ACD substitui a lista inteira antes)
    actions.append({"Action": "AddMany", "AddTo": Q("<gui/game/parts/part_stats.rules>/PartStats"),
                    "ManyToAdd": "&<gui/bs_part_stats.rules>/PartStats"})
    # 5) seletores (municao, celula, missil + os dos modulos)
    actions.append({"Action": "AddMany", "AddTo": Q("<gui/game/parts/part_toggles.rules>/PartToggles"),
                    "ManyToAdd": "&<gui/bs_part_toggles.rules>/PartToggles"})
    # 6) techs do modo Carreira
    actions.append({"Action": "AddMany", "AddTo": Q("<modes/career/techs.rules>/Techs"),
                    "ManyToAdd": "&<techs/bs_techs_career.rules>/Techs"})
    # 7) Build & Battle
    actions.append({"Action": "AddMany", "AddTo": Q("<modes/pvp/pvp_buildbattle/techs_buildbattle.rules>/Techs"),
                    "ManyToAdd": "&<techs/bs_techs_buildbattle.rules>/Techs"})
    actions.append({"Action": "AddMany",
                    "AddTo": Q("<modes/pvp/pvp_buildbattle/techs_buildbattle.rules>/PartsWhitelist"),
                    "ManyToAdd": "&<techs/bs_techs_buildbattle.rules>/PartsWhitelist"})
    if status_paths:
        # status proprios (o sistema de status e moddavel desde a 0.30.0; lista vanilla em statuses/statuses.rules)
        actions.append({"Action": "AddMany", "AddTo": Q("<statuses/statuses.rules>/Statuses"),
                        "ManyToAdd": [f"&<{p}>" for p in status_paths]})
    if limits:
        # limite por nave (SPEC.category_limits). Mesmo padrao em 2 passos do SW:ACD (mod.rules l.263-356), para os
        # dois mods poderem criar a lista sem conflito.
        actions.append({"Action": "Add", "AddTo": Q("<ships/terran/terran.rules>/Terran"), "Name": "CategoryLimits",
                        "OnlyIfNotExisting": True, "ToAdd": []})
        actions.append({"Action": "AddMany", "AddTo": Q("<ships/terran/terran.rules>/Terran/CategoryLimits"),
                        "ManyToAdd": [{"Category": Q(cat), "Max": mx} for cat, mx, _s, _p in limits]})
        actions.append({"Action": "AddMany", "AddTo": Q("<ships/terran/terran.rules>/Terran/CategoryNouns"),
                        "ManyToAdd": [{"Category": cat, "SingularKey": Q(sk), "PluralKey": Q(pk)}
                                      for cat, _m, sk, pk in limits]})
    actions.extend(actions_extra or ())
    top["Actions"] = actions
    header = ("Bullet Strike - armas de convés movidas a munição para Cosmoteer\n"
              "Gerado por tools/build_mod.py - edite os dados em tools/spec/SPEC_2.0.json e rode o gerador de novo.\n"
              "Alvo: Cosmoteer 0.30.4c (estavel). Compativel com Star Wars: A Cosmos Divided.\n"
              "ATENCAO: este deve ser o UNICO arquivo chamado mod.rules / mod_*.rules no mod.")
    return render(top, header)


def part_stats(extra_ids=()):
    """Linhas de estatistica proprias: BSShotsPerMag, BSFactoryOutput, as 'uso de <insumo>' das fabricas
    (bs_strings.input_stat_ids: BSAmmo<Insumo>Usage) e a BSShotDamageVsLasers das defesas (no fim)."""
    stats = [
        {"ID": "BSShotsPerMag", "FormatKey": Q("Stats/BSShotsPerMagFmt")},
        {"ID": "BSFactoryOutput", "FormatKey": Q("Stats/BSFactoryOutputFmt")},
    ]
    stats += [{"ID": sid, "FormatKey": Q(f"Stats/{sid}Fmt")} for sid in extra_ids]
    stats.append({"ID": "BSShotDamageVsLasers", "FormatKey": Q("Stats/BSShotDamageVsLasersFmt")})
    return render({"PartStats": stats}, "Linhas de estatistica do Bullet Strike (adicionadas com AddMany).")


def core_toggles(D):
    """As 3 PartToggles do nucleo (SPEC.toggles; dono WP01 - R4): bs_ammo_type 0-4, bs_cell_type 0-1,
    bs_missile_type 0-3 (rotulo 1 'Submunicao'). [(toggle_id, [(modo, choice_id, chave do tooltip, icone)])]."""
    from bs_strings import cell_tip_key
    tg = D.TOGGLES

    def ic(icon):
        # o arquivo das PartToggles fica em gui/: o icone 'gui/x.png' do spec vira 'x.png'
        return icon[4:] if icon.startswith("gui/") else icon
    ammo = [(c["index"], c["choice_id"], c["string_key"], ic(c["icon"])) for c in tg["bs_ammo_type"]["choices"]]
    cell = [(c["index"], c["choice_id"], cell_tip_key(c["key"]), ic(c["icon"])) for c in tg["bs_cell_type"]["choices"]]
    msl = [(c["index"], c["choice_id"], c["string_key"], ic(c["icon"])) for c in tg["bs_missile_type"]["choices"]]
    return [("bs_ammo_type", ammo), ("bs_cell_type", cell), ("bs_missile_type", msl)]


def part_toggles(toggles):
    """toggles: [(toggle_id, [(modo, choice_id, chave do tooltip, icone 'gui/x.png')])] (nucleo + gancho toggles()
    dos modulos, que pode devolver o mesmo formato ou dicts PartToggle prontos)."""
    def entry(tid, chs):
        if isinstance(chs, dict):
            return chs
        choices = []
        for mode, cid, tip, icon in chs:
            choices.append({"ChoiceID": Q(cid), "Mode": mode, "ButtonToolTipKey": Q(tip),
                            "ButtonSprite": {"Texture": {"File": Q(icon), "MipLevels": 2, "SampleMode": "Linear"}}})
        return {"ToggleID": Q(tid), "Style": "Popout", "ShowInEditor": True, "Choices": choices}
    out = [entry(tid, chs) for tid, chs in toggles]
    return render({"PartToggles": out},
                  "Seletores do Bullet Strike: municao (bs_ammo_type), celula (bs_cell_type), missil (bs_missile_type) "
                  "e os dos modulos (formato do missile_type vanilla).")


def techs(career, buildbattle, whitelist):
    car = render({"Techs": career, "OverclockIcon": "&<./Data/modes/career/techs.rules>/OverclockIcon"},
                 "Techs do modo Carreira do Bullet Strike (so pecas escritas neste build).\n"
                 "&~/OverclockIcon aponta para ESTE arquivo, por isso o OverclockIcon local no fim.")
    bb = render({"Techs": buildbattle, "PartsWhitelist": whitelist,
                 "OverclockIcon": "&<./Data/modes/career/techs.rules>/OverclockIcon"},
                "Techs e pecas sempre liberadas no Build & Battle (so pecas escritas neste build).")
    return car, bb


def strings_file(groups, tag):
    """groups: dict grupo -> dict chave -> texto (ou '&Outro' para referencia)."""
    top = {"BSModTag": Q(tag)}
    for gname, entries in groups.items():
        if not entries:
            continue
        d = {}
        for k, v in entries.items():
            d[k] = v if (isinstance(v, str) and v.startswith("&") and not isinstance(v, Q)) else Q(v)
        top[gname] = d
    return render(top, "Textos do Bullet Strike. Nao coloque __Name / __DebugOnly em arquivos de mod.")
