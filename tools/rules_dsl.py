"""Mini-DSL para emitir arquivos .rules do Cosmoteer a partir de estruturas Python.

Convencoes:
  - dict  -> grupo  { ... }   (a ordem das chaves e preservada)
  - list  -> lista  [ ... ]
  - str   -> valor cru (identificador, referencia &..., expressao, numero com sufixo "d"/"%")
  - Q(s)  -> string entre aspas
  - int/float/bool -> numero / true / false
  - VOID  -> campo "vazio" (so o nome, sem valor) — ex.: FireTrigger nao usado
  - Inh(base, body) -> elemento de lista sem nome que herda: ": base { ... }"
  - chaves de dict podem conter heranca: "Emitter2 : Emitter1"
  - Comment(texto) como chave gera um comentario de linha (o valor e ignorado)
"""


class Q(str):
    """String que deve ser escrita entre aspas."""


class _Void:
    pass


VOID = _Void()


class Inh:
    """Elemento de lista sem nome com heranca (": base { ... }")."""

    def __init__(self, base, body):
        self.base = base
        self.body = body


class Comment(str):
    pass


_comment_counter = [0]


def comment(text):
    """Gera uma chave unica que vira comentario // text."""
    _comment_counter[0] += 1
    return Comment(f"{text}\u0000{_comment_counter[0]}")


def fmt_num(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return s
    raise TypeError(v)


def _escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _scalar(v):
    if isinstance(v, Q):
        return '"' + _escape(str(v)) + '"'
    if isinstance(v, (bool, int, float)):
        return fmt_num(v)
    if isinstance(v, str):
        return v
    raise TypeError(f"valor nao suportado: {v!r}")


def _inline_text(v):
    if isinstance(v, list):
        return "[" + ", ".join(_inline_text(x) for x in v) + "]"
    return _scalar(v)


def _is_inline_list(lst):
    def ok(x, depth):
        if isinstance(x, (dict, Inh)):
            return False
        if isinstance(x, list):
            return depth < 2 and all(ok(y, depth + 1) for y in x)
        return True
    return all(ok(x, 1) for x in lst) and len(lst) <= 8 and len(_inline_text(lst)) < 100


def _emit_value(name, v, ind, out):
    pad = "\t" * ind
    if v is VOID:
        out.append(f"{pad}{name}")
    elif isinstance(v, dict):
        out.append(f"{pad}{name}")
        out.append(f"{pad}{{")
        _emit_body(v, ind + 1, out)
        out.append(f"{pad}}}")
    elif isinstance(v, list):
        if _is_inline_list(v):
            sep = " " if " : " in name else " = "   # heranca: "X : base [..]" (sem "=")
            out.append(f"{pad}{name}{sep}{_inline_text(v)}")
        else:
            out.append(f"{pad}{name}")
            out.append(f"{pad}[")
            _emit_list_items(v, ind + 1, out)
            out.append(f"{pad}]")
    else:
        out.append(f"{pad}{name} = {_scalar(v)}")


def _emit_list_items(lst, ind, out):
    pad = "\t" * ind
    for item in lst:
        if isinstance(item, dict):
            out.append(f"{pad}{{")
            _emit_body(item, ind + 1, out)
            out.append(f"{pad}}}")
        elif isinstance(item, Inh):
            out.append(f"{pad}: {item.base}")
            out.append(f"{pad}{{")
            _emit_body(item.body, ind + 1, out)
            out.append(f"{pad}}}")
        elif isinstance(item, list):
            if _is_inline_list(item):
                out.append(f"{pad}{_inline_text(item)}")
            else:
                out.append(f"{pad}[")
                _emit_list_items(item, ind + 1, out)
                out.append(f"{pad}]")
        else:
            out.append(f"{pad}{_scalar(item)}")


def _emit_body(d, ind, out):
    pad = "\t" * ind
    for k, v in d.items():
        if isinstance(k, Comment):
            out.append(f"{pad}// {k.split(chr(0))[0]}")
            continue
        _emit_value(k, v, ind, out)


def render(top, header=None):
    """Renderiza um dict de nivel superior como conteudo de arquivo .rules."""
    out = []
    if header:
        for line in header.strip("\n").split("\n"):
            out.append(f"// {line}" if line else "//")
        out.append("")
    _emit_body(top, 0, out)
    return "\n".join(out) + "\n"
