from pprint import pprint
from pathlib import Path

from loguru import logger as log

from .contest import solve


def load(data):
    return {"data": data}


if __name__ == "__main__":
    level, quests = 0, 5
    for quest in range(quests + 1):
        base_path = Path("data")
        input_file = base_path / f"level{level}" / f"level{level}_{quest}.in"
        output_file = input_file.with_suffix(".out")

        if not input_file.exists():
            log.warning(f"file not found, skip: {input_file}")
            continue

        with open(input_file, "r") as fi:
            data = load(fi.read().splitlines())
            pprint(data)

            print("=== Input {}".format(quest))
            print("======================")

            result = solve(data)
            pprint(result)

            with open(output_file, "w+") as fo:
                fo.write(result)
