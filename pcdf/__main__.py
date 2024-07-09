import logging
from dataclasses import dataclass

from pcdf.core import AbstractResourceProvider, AbstractResourceMutator
from pcdf.core.config import ResourceCfg, check_protocols
from pcdf.lib.deployment import DeploymentProvider, DeploymentEnvMutator
from pcdf.lib.datamodel import (
    BaseDatamodel,
    ImageConfigModel,
    NetworkingConfigModel,
    EnvVarModel,
    PortModel,
)


class Datamodel(BaseDatamodel):
    #image: ImageConfigModel
    #network: NetworkingConfigModel
    envs: list[EnvVarModel] = []


cfg = [ResourceCfg(provider=DeploymentProvider, mutators=[DeploymentEnvMutator])]



def main():
    log = logging.getLogger()

    dm = Datamodel(
        name="test-app",
        namespace="test",
        image=ImageConfigModel(repository="nginx", tag="latest"),
        network=NetworkingConfigModel(ports=[PortModel(name="http", number=8888)]),
        envs=[EnvVarModel(name="DEBUG", value="True")],
    )

    check_protocols(cfg, dm)

    

    # r = DeploymentProvider().with_mutators(DeploymentEnvMutator()).execute(log, dm)
    # for res in r:
    #     print(res.model)


main()
