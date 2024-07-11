import sys
from typing import Annotated, cast

import typer
import yaml

from pcdf.cmd.context import CommandContext
from pcdf.cmd.datamodel import validate
from pcdf.core import (
    ResourceFactory,
)


def render(
    ctx: CommandContext,
    values: str,
    output: str = "",
):
    log = ctx["logger"]
    settings = ctx["settings"]
    with open(values, "r") as file:
        vals = ctx["datamodel"](**yaml.safe_load(file))

    validate(ctx, values, show_success_msg=False)

    log.debug("launching resource factory")
    try:
        result = ResourceFactory.from_config(log, settings).run(vals)
    except Exception as err:
        log.error(err)
        return

    dumped = [res.dump() for res in result]
    if output == "":
        yaml.dump_all(dumped, sys.stdout)
    else:
        with open(output, "w") as file:
            yaml.dump_all(dumped, file)
