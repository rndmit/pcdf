import yaml

from pcdf import Settings
from pcdf.cmd import render
from pcdf.lib import deployment, service

from pcd.datamodel import Datamodel

TOOL_VERSION = "0.0.0"

settings = Settings(
    debug=False,
    version=TOOL_VERSION,
    resources=[deployment.DEFAULT_CONFIG, service.DEFAULT_CONFIG],
)


def main():
    with open("values.yaml", "r") as input:
        dm = Datamodel(**yaml.safe_load(input))
    render(dm, settings)


main()
