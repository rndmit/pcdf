import logging
import sys

import typer
from pydantic import Field

from pcdf import Settings
from pcdf.cmd import CommandContext
from pcdf.cli.typer import datamodel_cli, render_cli
from pcdf.lib import configmap, datamodel, deployment, ingress, service

from .ext import secret

TOOL_VERSION = "0.0.0"


def default_resources_factory() -> datamodel.Resources:
    return datamodel.Resources(
        limits=datamodel.ResourceReqPair(cpu="20m", memory="20Mi"),
        requests=datamodel.ResourceReqPair(cpu="20m", memory="20Mi")
    )


class Datamodel(datamodel.Base):
    runtime: datamodel.Runtime
    resources: datamodel.Resources = Field(default_factory=default_resources_factory)
    network: datamodel.Networking
    certmanager: datamodel.CertManager = Field(default_factory=datamodel.CertManager)
    envs: list[datamodel.EnvVar] = []
    files: list[datamodel.Document] = []
    filesMountPath: str = "/opt/app"


settings = Settings(
    version=TOOL_VERSION,
    resources=[
        deployment.DEFAULT_CONFIG.with_mutators(deployment.ResourcesMutator),
        service.DEFAULT_CONFIG,
        ingress.DEFAULT_CONFIG.with_mutators(ingress.CertManagerMutator),
        configmap.DEFAULT_CONFIG,
        Settings.Resource(provider=secret.Provider, mutators=[]),
    ],
)

cli = typer.Typer(
    no_args_is_help=True,
    context_settings={},
    pretty_exceptions_enable=True,
    rich_markup_mode="markdown",
)


@cli.callback()
def setup(ctx: typer.Context, debug: bool = False, interactive: bool = True):
    log = logging.getLogger()
    log.setLevel(logging.DEBUG) if debug else log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler(sys.stderr))

    ctx.obj = CommandContext(
        logger=log, settings=settings, datamodel=Datamodel, interactive=interactive
    )


cli.add_typer(render_cli, invoke_without_command=True)
cli.add_typer(datamodel_cli)
cli()
