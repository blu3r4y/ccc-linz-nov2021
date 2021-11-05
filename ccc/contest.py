import sys

from lark import Lark, Transformer
from loguru import logger as log

from .runner import run

from textwrap import indent

GRAMMAR = r"""
    ?start: program

    program: "start" block "end"
    statement: print_ | return_ | ifelse_
    block: statement*

    print_: "print" (BOOLEAN | INTEGER | STRING)
    return_: "return" (BOOLEAN | INTEGER | STRING)

    ifelse_: "if" BOOLEAN block "end" "else" block "end"

    BOOLEAN: "true" | "false"
    %import common.CNAME -> STRING
    %import common.INT -> INTEGER

    %import common.WS_INLINE
    %ignore WS_INLINE
"""


class PythonTransformer(Transformer):

    INTEGER = int
    STRING = str

    def BOOLEAN(self, args):
        if args.value == "true":
            return "True"
        if args.value == "false":
            return "False"
        log.warning(f"invalid value {args.value}")
        return args.value

    def program(self, args):
        out = ""
        out += "def program():\n"
        out += args[0]
        out += "\n\n"
        out += "if __name__ == '__main__':\n"
        out += "    program()\n"
        return out

    def statement(self, args):
        return args[0]

    def block(self, args):
        if len(args) == 0:
            return indent("pass", prefix="    ")
        return indent("\n".join(args), prefix="    ")

    def print_(self, args):
        return f"print('{args[0]}', end='')"

    def return_(self, args):
        return f"return '{args[0]}'"

    def ifelse_(self, args):
        out = ""
        out += f"if {args[0]}:\n"
        out += args[1] + "\n"
        out += "else:\n"
        out += args[2] + "\n"
        return out


def solve(data):
    tokens = " ".join(data["tokens"])

    parser = Lark(GRAMMAR, parser="lalr")
    ast = parser.parse(tokens)
    code = PythonTransformer().transform(ast)

    result = run(code)
    return result
