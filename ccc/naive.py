import sys

from typing import List, Dict, Any
from loguru import logger as log

from collections import namedtuple

Return = namedtuple("Return", "stdout retval error")


def solve(data):
    tokens = data["tokens"]

    assert tokens[0] == "start"
    assert tokens[-1] == "end"

    stdout = ""

    funcs = parse_functions(tokens)
    for func in funcs:
        log.debug("--- new function ---")
        result = interpret(func, {})

        stdout += result.stdout if not result.error else "ERROR"
        stdout += "\n"

    return stdout


def parse_functions(tokens):
    assert len(tokens) > 0
    assert tokens[0] == "start"
    assert tokens[-1] == "end"

    functions = []
    function = []

    # consume first start token
    i = 1

    while i < len(tokens):
        while i < len(tokens) and tokens[i] != "start":
            function.append(tokens[i])
            i += 1

        # pop last end
        assert function.pop() == "end"

        # append copy and re-use list
        functions.append(function[:])
        function.clear()
        i += 1

    return functions


def interpret(tokens: List[str], variables: Dict[str, Any]):
    log.debug("---")
    stdout = ""
    retval = None
    error = False

    def _get(name):
        if name not in variables:
            return name
        return variables[name]

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "start":
            log.error(f"token invalid here, fail-fast: {tok}")
            sys.exit(1)

        elif tok == "end":
            log.error(f"token invalid here, fail: {tok}")
            sys.exit(1)

        elif tok == "return":
            i += 1
            retval = _get(tokens[i])
            break

        elif tok == "var":
            i += 1
            varname = tokens[i]

            i += 1
            varval = _get(tokens[i])

            if varname in variables:
                log.warning(f"tried creating variable that exists: {varname}")
                error = True
                break

            variables[varname] = varval

        elif tok == "set":
            i += 1
            varname = tokens[i]

            i += 1
            varval = _get(tokens[i])

            if varname not in variables:
                log.warning(f"tried setting variable that does not exists: {varname}")
                error = True
                break

            variables[varname] = varval

        elif tok == "if":
            # consume boolean value
            i += 1
            boolval = _get(tokens[i])

            if boolval != "true" and boolval != "false":
                log.warning(f"invalid boolean value encountered: {boolval}")
                error = True
                break

            # advance
            i += 1

            # scan inner block (if) --- START
            inner_true = []

            # skip multiple ends
            parsed_ends, goal_ends = 0, 1
            is_end = False

            while not is_end:
                tok = tokens[i]

                # check end condition
                if tok == "end":
                    parsed_ends += 1
                is_end = parsed_ends == goal_ends

                if not is_end:
                    inner_true.append(tok)

                i += 1

                # detected an inner if, skip one end
                if tok == "if":
                    # we need to skip the next two end's now
                    goal_ends += 2

            # scan inner block (if) --- END

            # consume else
            assert tokens[i] == "else"
            i += 1

            # scan inner block (if) --- START
            inner_false = []

            # skip multiple ends
            parsed_ends, goal_ends = 0, 1
            is_end = False

            while not is_end:
                tok = tokens[i]

                # check end condition
                if tok == "end":
                    parsed_ends += 1
                is_end = parsed_ends == goal_ends

                if not is_end:
                    inner_false.append(tok)

                i += 1

                # detected an inner if, skip one end
                if tok == "if":
                    # we need to skip the next two end's now
                    goal_ends += 2

            # scan inner block (if) --- END

            # undo, we already advanced before
            i += -1

            # execute correct block
            next_block = inner_true if boolval == "true" else inner_false

            inner_func = interpret(next_block, variables)
            stdout += inner_func.stdout

            # check if no error occurred
            if inner_func.error:
                assert inner_func.retval is None
                return Return(stdout, None, True)

            # check if no return occurred
            if inner_func.retval is not None:
                return Return(stdout, inner_func.retval, inner_func.error)

        elif tok == "print":
            i += 1
            stdout += _get(tokens[i])

        else:
            log.error(f"unknown token, fail {tok}")
            sys.exit(1)

        i += 1

    # there can be no return if an error occurred before
    if error:
        assert retval is None

    log.debug(f"return value: {retval}")

    return Return(stdout, retval, error)
