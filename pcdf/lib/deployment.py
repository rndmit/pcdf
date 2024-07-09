from collections.abc import Sequence
from logging import Logger
from typing import Any, Protocol, runtime_checkable

from pcdf.core.resource import (
    AbstractResourceProvider,
    AbstractResourceMutator,
    Resource,
)
from pcdf.lib.datamodel import ImageConfigModel, NetworkingConfigModel, EnvVarModel

from kubemodels.io.k8s.api.apps.v1 import Deployment, DeploymentSpec
from kubemodels.io.k8s.api.core.v1 import PodTemplateSpec, PodSpec, Container, EnvVar
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta, LabelSelector


class DeploymentDatamodel(Protocol):
    name: str
    namespace: str
    image: ImageConfigModel
    network: NetworkingConfigModel


class DeploymentEnvMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        envs: list[EnvVarModel]

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if resource.model.spec is None or resource.model.spec.template.spec is None:
            log.debug(
                f"{self.__qualname__} exited because given Deployment manifest is not correct"
            )
            return

        containers = resource.model.spec.template.spec.containers
        if len(containers) < 1:
            return

        for container in containers:
            if container.env is None:
                container.env = []
            container.env += [EnvVar(name=v.name, value=v.value) for v in data.envs]

        return


class DeploymentProvider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        name: str
        namespace: str
        image: ImageConfigModel
        network: NetworkingConfigModel

    def execute(self, log: Logger, data: Datamodel) -> Sequence[Resource]:
        res = Resource(
            Deployment(
                metadata=ObjectMeta(
                    name=data.name,
                    namespace=data.namespace,
                ),
                spec=DeploymentSpec(
                    selector=LabelSelector(),
                    template=PodTemplateSpec(
                        spec=PodSpec(
                            containers=[
                                Container(
                                    name="app",
                                    image=f"{data.image.repository}:{data.image.tag}",
                                )
                            ]
                        )
                    ),
                ),
            )
        )

        for mut in self.mutators:
            mut.execute(log, data, res)

        return [res]
