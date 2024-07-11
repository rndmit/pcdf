import json

import yaml
from rich import print

from pcdf.cmd.context import CommandContext
from pcdf.core import ProtocolConformanceError, validate_config


def schema(
    ctx: CommandContext,
    output: str,
):
    with open(output, "w") as file:
        json.dump(ctx["datamodel"].model_json_schema(), file)

    if ctx["interactive"]:
        print(f"[green]schema writen to {output}[/green]")


def validate(
    ctx: CommandContext,
    values: str,
    show_success_msg: bool = True,
):
    log = ctx["logger"]
    settings = ctx["settings"]
    with open(values, "r") as file:
        datamodel = ctx["datamodel"](**yaml.safe_load(file))

    log.debug("validating datamodel")
    try:
        validate_config(settings.resources, datamodel)
    except ProtocolConformanceError as err:
        if ctx["interactive"]:
            print(
                f"[red]Error[/red]: given datamodel does not conform [yellow]{err.protocol}[/yellow] protocol"
                f"\nMissing fields: {"\n - " + "\n - ".join(err.unconformed)}",
            )
        else:
            log.fatal(err)
        exit(51)
    if show_success_msg:
        log.info("datamodel correct")
