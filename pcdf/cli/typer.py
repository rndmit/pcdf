from typing import Annotated

import typer

from pcdf.cmd import render, schema, validate

render_cli = typer.Typer(name="render", short_help="Render manifests")


@render_cli.callback(invoke_without_command=True)
def render_cmd(
    ctx: typer.Context,
    values: Annotated[str, typer.Option("--values", "-f")] = "values.yaml",
    output: Annotated[str, typer.Option("--output", "-o")] = "",
):
    """Render kubernetes manifests"""
    render(ctx.obj, values, output)


datamodel_cli = typer.Typer(
    name="datamodel",
    short_help="Datamodel tools",
    no_args_is_help=True,
)


@datamodel_cli.command("schema")
def schema_cmd(
    ctx: typer.Context,
    output: Annotated[str, typer.Option("--output", "-o")] = "values.datamodel.yaml",
):
    """Generate json-schema from configured datamodel

    Use `datamodel validate` first to ensure that you use correct schema
    """
    schema(ctx.obj, output)


@datamodel_cli.command("validate")
def validate_cmd(
    ctx: typer.Context,
    values: Annotated[str, typer.Option("--values", "-f")] = "values.yaml",
    show_success_msg: bool = True,
):
    """Check if datamodel is correct"""
    validate(ctx.obj, values, show_success_msg)
