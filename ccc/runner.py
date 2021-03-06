import os
import uuid

import subprocess

from loguru import logger as log


def run(code: str):

    filename = f"program_{uuid.uuid4()}.py"

    # store code to temporary file
    os.makedirs("tmp", exist_ok=True)
    with open(f"tmp/{filename}", "w+", encoding="utf8") as f:
        f.write(code)

    # run code
    proc = subprocess.Popen(["python", f"tmp/{filename}"], stdout=subprocess.PIPE)

    # read output
    stdout = proc.communicate()[0].decode().replace("\r\n", "\n")
    code = proc.returncode

    log.debug(f"run tmp/{filename} (code: {code})")
    # log.debug(f"=> {stdout}")

    if code != 0:
        log.error("program exited with non-zero exit code")

    return stdout
