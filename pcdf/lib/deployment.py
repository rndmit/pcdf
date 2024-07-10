from collections.abc import Sequence
from logging import Logger
from typing import Any, Protocol, runtime_checkable

from pcdf.core import (
    AbstractResourceProvider,
    AbstractResourceMutator,
    Resource,
)
from pcdf.lib.datamodel import (
    RuntimeModel,
    NetworkingModel,
    EnvVarModel,
    MetadataModel,
)

from kubemodels.io.k8s.api.apps.v1 import Deployment, DeploymentSpec
from kubemodels.io.k8s.api.core.v1 import PodTemplateSpec, PodSpec, Container, EnvVar
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta, LabelSelector


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


class DeploymentRuntimeMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        runtime: RuntimeModel

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (spec := resource.model.spec) is None or spec.template.spec is None:
            log.debug(
                f"{self.__qualname__} exited because given Deployment manifest is not correct"
            )
            return

        ct = [c for c in spec.template.spec.containers if c.name == "app"]
        if len(ct) != 1:
            raise Exception(
                "deployment has more (or less) than 1 container named 'app'"
            )
        ct = ct[0]

        ct.image = f"{data.runtime.image}:{data.runtime.tag}"
        ct.command = data.runtime.entrypoint
        ct.args = data.runtime.command

        spec.replicas = data.runtime.replicas


class DeploymentDefaultContainerAnnotationMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        runtime: RuntimeModel

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (meta := resource.model.metadata) is None or meta.annotations is None:
            log.debug(
                f"{self.__qualname__} exited because given Deployment manifest is not correct"
            )
            return
        
        meta.annotations["kubectl.kubernetes.io/default-container"] = data.runtime.container_name


class DeploymentProvider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: MetadataModel
        runtime: RuntimeModel
        network: NetworkingModel

    def execute(self, log: Logger, data: Datamodel) -> Sequence[Resource]:
        res = Resource(
            Deployment(
                apiVersion="apps/v1",
                kind="Deployment",
                metadata=ObjectMeta(
                    name=data.metadata.name,
                    namespace=data.metadata.namespace,
                    annotations={},
                ),
                spec=DeploymentSpec(
                    selector=LabelSelector(),
                    template=PodTemplateSpec(
                        spec=PodSpec(
                            containers=[
                                Container(
                                    name=data.runtime.container_name,
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
