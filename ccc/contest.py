from lark import Lark, Transformer
from loguru import logger as log

from .runner import run

from textwrap import indent

# one python indentation
PREFIX = "    "

GRAMMAR = r"""
    start: function+

    function: "start" block "end"
    statement: print_ | return_ | ifelse_ | var_ | set_ | postpone_
    block: statement*

    print_: "print" (BOOLEAN | INTEGER | STRING)
    return_: "return" (BOOLEAN | INTEGER | STRING)

    ifelse_: "if" STRING block "end" "else" block "end"

    var_: "var" STRING (BOOLEAN | INTEGER | STRING)
    set_: "set" STRING (BOOLEAN | INTEGER | STRING)

    postpone_: "postpone" block "end"

    BOOLEAN: "true" | "false"
    %import common.CNAME -> STRING
    %import common.INT -> INTEGER

    %import common.WS_INLINE
    %ignore WS_INLINE
"""


class PythonTransformer(Transformer):

    INTEGER = int
    STRING = str

    def __init__(self):
        super(PythonTransformer, self).__init__()
        self.prog_no = 0
        self.var_no = 0
        self.postpone_no = 0
        self.queue_no = 0

    def BOOLEAN(self, args):
        if args.value == "true":
            return "True"
        if args.value == "false":
            return "False"
        log.warning(f"invalid value {args.value}")
        return args.value

    def start(self, args):
        # concat individual function bodys
        functions = "\n".join(args)

        # concat function calls
        calls = ""
        for i in range(self.prog_no):
            calls += f"""
try:
    stdout, retval = program_{i + 1}(mem=dict(), queue=list())
    print(stdout)
except ProgramError as e:
    print("ERROR")
"""

        # main program body
        return f"""
import io


class ProgramError(Exception):
    pass


def __var(name, value, mem):
    if name in mem:
        raise ProgramError("variable %s already exists (tried setting it to %s)" % (name, value))
    mem[name] = value


def __set(name, value, mem):
    if name not in mem:
        raise ProgramError("variable %s does not exist (tried setting it to %s)" % (name, value))
    mem[name] = value


def __getval(name, mem):
    if name in mem:
        return mem[name]
    return name


def __exec_postponed_blocks(queue, mem):
    for block in queue:
        blockres = block(mem, queue)
        if blockres is not None:
            return blockres

{functions}

if __name__ == '__main__':
{indent(calls, prefix=PREFIX)}
"""

    def function(self, args):
        self.prog_no += 1
        self.queue_no += 1
        block = args[0]

        return f"""
def program_{self.prog_no}(mem, queue):
    stdout = io.StringIO()
    queue_{self.queue_no} = []
    queue = queue_{self.queue_no}

{block}

    retval_queues_{self.queue_no} = __exec_postponed_blocks(queue_{self.queue_no}, mem)
    return stdout.getvalue(), retval_queues_{self.queue_no}
"""

    def statement(self, args):
        return args[0]

    def block(self, args):
        if len(args) == 0:
            return indent("pass", prefix=PREFIX)
        return indent("\n".join(args), prefix=PREFIX)

    def print_(self, args):
        printval = args[0]
        return f"stdout.write(__getval('{printval}', mem))"

    def return_(self, args):
        retval = args[0]
        return f"return stdout.getvalue(), __getval('{retval}', mem)"

    def ifelse_(self, args):
        self.var_no += 1
        self.queue_no += 2  # one for the true, one for the false case

        cond, tcase, fcase = args[0], args[1], args[2]

        return f"""
tmp_{self.var_no} = __getval('{cond}', mem)
if tmp_{self.var_no} == 'true':
    queue_{self.queue_no - 1} = []
    pre_queue = queue
    queue = queue_{self.queue_no - 1}

{tcase}

    retval_queues_{self.queue_no - 1} = __exec_postponed_blocks(queue_{self.queue_no - 1}, mem)
    if retval_queues_{self.queue_no - 1} is not None:
        return stdout.getvalue(), retval_queues_{self.queue_no - 1}
    queue = pre_queue

elif tmp_{self.var_no} == 'false':
    queue_{self.queue_no} = []
    pre_queue = queue
    queue = queue_{self.queue_no}

{fcase}

    retval_queues_{self.queue_no} = __exec_postponed_blocks(queue_{self.queue_no}, mem)
    if retval_queues_{self.queue_no} is not None:
        return stdout.getvalue(), retval_queues_{self.queue_no}
    queue = pre_queue

else:
    raise ProgramError("invalid value %s for condition" % tmp_{self.var_no})
"""

    def var_(self, args):
        varname, varval = args[0], args[1]
        return f"__var('{varname}', __getval('{varval}', mem), mem)"

    def set_(self, args):
        varname, varval = args[0], args[1]
        return f"__set('{varname}', __getval('{varval}', mem), mem)"

    def postpone_(self, args):
        self.postpone_no += 1

        return f"""
def _postpone_block_{self.postpone_no}(mem, queue):
{args[0]}


queue.append(_postpone_block_{self.postpone_no})"""


def solve(data):
    tokens = " ".join(data["tokens"])

    parser = Lark(GRAMMAR, parser="lalr")
    ast = parser.parse(tokens)
    code = PythonTransformer().transform(ast)

    result = run(code)
    return result
