"""mod.rules, strings, seletor de municao, aba do editor, stats e techs do Bullet Strike."""

from rules_dsl import Q, Inh, render
from bsgen import common as C

COMPAT = ["0.30.4", "0.30.4a", "0.30.4b", "0.30.4c", "0.30.5"]


def mod_rules(data, part_paths, resource_paths, version, limits=(), status_paths=()):
    desc_lines = data["description"]
    top = {
        "ID": C.MOD_ID,
        "Name": Q("Bullet Strike"),
        "Version": version,
        "CompatibleGameVersions": [Q(v) for v in COMPAT],
        "UseThisFileIfNoVersionMatch": True,
        "ModifiesGameplay": True,
        "Author": Q("Rafael Tessaro"),
        "Logo": Q("logo.png"),
        "Description": Q(desc_lines),
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
    actions.append({"Action": "AddMany", "AddTo": Q("<resources/resources.rules>/Resources"),
                    "ManyToAdd": [f"&<{p}>" for p in resource_paths]})
    # 3) pecas
    actions.append({"Action": "AddMany", "AddTo": Q("<ships/terran/terran.rules>/Terran/Parts"),
                    "ManyToAdd": [f"&<{p}>/Part" for p in part_paths]})
    # 4) linhas de estatistica (nunca Replace: o pre-requisito do SW:ACD substitui a lista inteira antes)
    actions.append({"Action": "AddMany", "AddTo": Q("<gui/game/parts/part_stats.rules>/PartStats"),
                    "ManyToAdd": "&<gui/bs_part_stats.rules>/PartStats"})
    # 5) seletor de municao
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
        # status proprios (Carrapato F2): o sistema de status e moddavel desde a 0.30.0; lista vanilla em
        # statuses/statuses.rules l.5-13. So entra com limpet_anchor=F2 (teste T14b antes).
        actions.append({"Action": "AddMany", "AddTo": Q("<statuses/statuses.rules>/Statuses"),
                        "ManyToAdd": [f"&<{p}>" for p in status_paths]})
    if limits:
        # limite por nave (ex.: obuseiros nucleares). Mesmo padrao em 2 passos do SW:ACD (mod.rules l.263-356),
        # para os dois mods poderem criar a lista sem conflito.
        actions.append({"Action": "Add", "AddTo": Q("<ships/terran/terran.rules>/Terran"), "Name": "CategoryLimits",
                        "OnlyIfNotExisting": True, "ToAdd": []})
        actions.append({"Action": "AddMany", "AddTo": Q("<ships/terran/terran.rules>/Terran/CategoryLimits"),
                        "ManyToAdd": [{"Category": Q(cat), "Max": mx} for cat, mx, _s, _p in limits]})
        actions.append({"Action": "AddMany", "AddTo": Q("<ships/terran/terran.rules>/Terran/CategoryNouns"),
                        "ManyToAdd": [{"Category": cat, "SingularKey": Q(sk), "PluralKey": Q(pk)}
                                      for cat, _m, sk, pk in limits]})
    top["Actions"] = actions
    header = ("Bullet Strike - armas de convés movidas a munição para Cosmoteer\n"
              "Gerado por tools/build_mod.py - edite os dados em tools/bs_data.py e rode o gerador de novo.\n"
              "Alvo: Cosmoteer 0.30.4 (estavel) e 0.30.5 (RC). Compativel com Star Wars: A Cosmos Divided.\n"
              "ATENCAO: este deve ser o UNICO arquivo chamado mod.rules / mod_*.rules no mod.")
    return render(top, header)


def part_stats(extra_ids=()):
    """extra_ids: linhas proprias a mais (ex.: 'uso de <insumo>' das fabricas, factory.input_stat_ids)."""
    stats = [
        {"ID": "BSShotsPerMag", "FormatKey": Q("Stats/BSShotsPerMagFmt")},
        {"ID": "BSFactoryOutput", "FormatKey": Q("Stats/BSFactoryOutputFmt")},
    ]
    stats += [{"ID": sid, "FormatKey": Q(f"Stats/{sid}Fmt")} for sid in extra_ids]
    return render({"PartStats": stats}, "Linhas de estatistica do Bullet Strike (adicionadas com AddMany).")


def part_toggles(ammo_choices, extra_toggles=()):
    """ammo_choices: lista de (mode, choice_id, tooltip_key, icon_file).

    extra_toggles: outros seletores [(toggle_id, choices)] com o mesmo formato (ex.: bs_missile_type dos
    lancadores de misseis); cada um vira mais uma entrada de PartToggles."""
    def entry(tid, chs):
        choices = []
        for mode, cid, tip, icon in chs:
            choices.append({"ChoiceID": Q(cid), "Mode": mode, "ButtonToolTipKey": Q(tip),
                            "ButtonSprite": {"Texture": {"File": Q(icon), "MipLevels": 2, "SampleMode": "Linear"}}})
        return {"ToggleID": Q(tid), "Style": "Popout", "ShowInEditor": True, "Choices": choices}
    toggles = [entry("bs_ammo_type", ammo_choices)]
    for tid, chs in extra_toggles:
        toggles.append(entry(tid, chs))
    head = "Seletor de municao do Bullet Strike (mesmo formato do missile_type vanilla)."
    if extra_toggles:
        head = "Seletores do Bullet Strike: municao das armas e tipo de missil dos lancadores (formato do missile_type vanilla)."
    return render({"PartToggles": toggles}, head)


def techs(career, buildbattle, whitelist):
    car = render({"Techs": career, "OverclockIcon": "&<./Data/modes/career/techs.rules>/OverclockIcon"},
                 "Techs do modo Carreira do Bullet Strike.\n"
                 "&~/OverclockIcon aponta para ESTE arquivo, por isso o OverclockIcon local no fim.")
    bb = render({"Techs": buildbattle, "PartsWhitelist": whitelist,
                 "OverclockIcon": "&<./Data/modes/career/techs.rules>/OverclockIcon"},
                "Techs e pecas sempre liberadas no Build & Battle.")
    return car, bb


def strings_file(groups, tag):
    """groups: dict grupo -> dict chave -> texto (ou '&Outro' para referencia)."""
    top = {"BSModTag": Q(tag)}
    for gname, entries in groups.items():
        d = {}
        for k, v in entries.items():
            d[k] = v if (isinstance(v, str) and v.startswith("&") and not isinstance(v, Q)) else Q(v)
        top[gname] = d
    return render(top, "Textos do Bullet Strike. Nao coloque __Name / __DebugOnly em arquivos de mod.")
