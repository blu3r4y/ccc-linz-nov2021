from loguru import logger as log


def solve(data):
    tokens = data["tokens"]

    assert tokens[0] == "start"
    assert tokens[-1] == "end"

    stdout = ""

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "start":
            pass
        elif tok == "end":
            pass
        elif tok == "print":
            i += 1
            stdout += tokens[i]
        else:
            log.error(f"unknown token {tok}")
        i += 1

    return stdout
