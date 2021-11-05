from loguru import logger as log

from collections import namedtuple

Return = namedtuple("Return", "stdout retval")


def solve(data):
    tokens = data["tokens"]

    assert tokens[0] == "start"
    assert tokens[-1] == "end"

    inner_func = tokens[1:-1]
    func = interpret(inner_func)

    return func.stdout


def interpret(tokens):
    stdout = ""
    retval = None

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "start":
            log.error(f"token invalid here, fail: {tok}")
            return

        elif tok == "end":
            log.error(f"token invalid here, fail: {tok}")
            return

        elif tok == "return":
            i += 1
            retval = tokens[i]
            break

        elif tok == "if":
            # consume boolean value
            i += 1
            boolval = tokens[i]

            assert boolval == "true" or boolval == "false"

            # advance
            i += 1

            # scan inner block (if)
            inner_true = []
            while tokens[i] != "end":
                inner_true.append(tokens[i])
                i += 1

            # consume end
            i += 1

            assert tokens[i] == "else"
            i += 1

            # scan inner block (else)
            inner_false = []
            while tokens[i] != "end":
                inner_false.append(tokens[i])
                i += 1

            # execute correct block
            next_block = inner_true if boolval == "true" else inner_false

            inner_func = interpret(next_block)
            stdout += inner_func.stdout

            # check if no return occurred
            if inner_func.retval is not None:
                return Return(stdout, inner_func.retval)

        elif tok == "print":
            i += 1
            stdout += tokens[i]

        else:
            log.error(f"unknown token {tok}")

        i += 1

    log.debug(f"return value: {retval}")

    return Return(stdout, retval)
