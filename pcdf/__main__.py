from pcdf.core import Config
from pcdf.cmd.render import render
from pcdf.lib.deployment import (
    DeploymentProvider,
    DeploymentEnvMutator,
    DeploymentRuntimeMutator,
    DeploymentDefaultContainerAnnotationMutator,
)
from pcdf.lib.datamodel import (
    BaseDatamodel,
    NetworkingModel,
    EnvVarModel,
    MetadataModel,
    RuntimeModel,
    PortModel,
)


class Datamodel(BaseDatamodel):
    runtime: RuntimeModel
    network: NetworkingModel
    envs: list[EnvVarModel] = []


cfg = Config(
    debug=False,
    resources=[
        Config.Resource(
            provider=DeploymentProvider,
            mutators=[
                DeploymentEnvMutator,
                DeploymentRuntimeMutator,
                DeploymentDefaultContainerAnnotationMutator,
            ],
        )
    ],
)

dm = Datamodel(
    metadata=MetadataModel(name="test-app", namespace="test"),
    runtime=RuntimeModel(
        image="nginx",
        tag="alpine",
        entrypoint=["/bin/bash"],
        command=["tail -f /dev/null"],
    ),
    network=NetworkingModel(ports=[PortModel(name="http", number=8888)]),
    envs=[EnvVarModel(name="DEBUG", value="True")],
)


def main():
    render(dm, cfg)


main()
