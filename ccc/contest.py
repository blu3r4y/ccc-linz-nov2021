from lark import Lark, Transformer
from loguru import logger as log

from .runner import run

GRAMMAR = r"""
    ?start: program

    program: "start" statement+ "end"
    statement: print
    print: "print" (BOOLEAN | INT | NAME)

    BOOLEAN: "true" | "false"

    %import common.CNAME -> NAME
    %import common.INT
    %import common.WS_INLINE
    %ignore WS_INLINE
"""


class PythonTransformer(Transformer):

    BOOLEAN = bool
    INT = int
    NAME = str

    def program(self, args):
        return "\n".join(args)

    def statement(self, args):
        return args[0]

    def print(self, args):
        return f"print('{args[0]}', end='')"


def solve(data):
    tokens = " ".join(data["tokens"])

    parser = Lark(GRAMMAR, parser="lalr")
    ast = parser.parse(tokens)
    code = PythonTransformer().transform(ast)

    result = run(code)
    return result
