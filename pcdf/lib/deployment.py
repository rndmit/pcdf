from collections.abc import Sequence
from dataclasses import dataclass
from logging import Logger
from typing import Protocol, runtime_checkable

from pcdf.core import (
    AbstractResourceProvider,
    AbstractResourceMutator,
    Resource,
    Context,
)

from pcdf import Settings
from pcdf.lib.exceptions import IncorrectManifestError, IncorrectRunContextErrorMsg
from pcdf.lib import datamodel, utils

from kubemodels.io.k8s.api.apps.v1 import Deployment, DeploymentSpec
from kubemodels.io.k8s.api.core.v1 import (
    PodTemplateSpec,
    PodSpec,
    Container,
    EnvVar,
    ContainerPort,
)
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta, LabelSelector


@dataclass
class MainContainersMiscountError(Exception):
    mc_name: str
    count: int

    def __str__(self) -> str:
        return f" has {self.count} container named '{self.mc_name}'. Expected only 1"


class EnvMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        envs: list[datamodel.EnvVar]

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if resource.model.spec is None or resource.model.spec.template.spec is None:
            raise IncorrectManifestError(self.__qualname__)

        containers = resource.model.spec.template.spec.containers
        if len(containers) < 1:
            return

        for container in containers:
            if container.env is None:
                container.env = []
            container.env += [EnvVar(name=v.name, value=v.value) for v in data.envs]


class RuntimeMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        runtime: datamodel.Runtime

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (spec := resource.model.spec) is None or spec.template.spec is None:
            raise IncorrectManifestError(self.__qualname__)

        ct = [
            c
            for c in spec.template.spec.containers
            if c.name == data.runtime.container_name
        ]
        if (ctlen := len(ct)) != 1:
            raise MainContainersMiscountError(data.runtime.container_name, ctlen)

        ct[0].image = f"{data.runtime.image}:{data.runtime.tag}"
        ct[0].command = data.runtime.entrypoint
        ct[0].args = data.runtime.command

        spec.replicas = data.runtime.replicas


class ContainerPortMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        network: datamodel.Networking
        runtime: datamodel.Runtime

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (spec := resource.model.spec) is None or spec.template.spec is None:
            raise IncorrectManifestError(self.__qualname__)

        ct = [
            c
            for c in spec.template.spec.containers
            if c.name == data.runtime.container_name
        ]
        if (ctlen := len(ct)) != 1:
            raise MainContainersMiscountError(data.runtime.container_name, ctlen)

        ct[0].ports = [
            ContainerPort(name=p.name, containerPort=p.number)
            for p in data.network.ports
        ]


class DefaultContainerAnnotationMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        runtime: datamodel.Runtime

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (meta := resource.model.metadata) is None or meta.annotations is None:
            raise IncorrectManifestError(self.__qualname__)

        meta.annotations["kubectl.kubernetes.io/default-container"] = (
            data.runtime.container_name
        )


class Provider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        runtime: datamodel.Runtime

    def execute(self, log: Logger, ctx: Context, data: Datamodel) -> Sequence[Resource]:
        assert ctx.run is not None, IncorrectRunContextErrorMsg
        
        default_labels = utils.default_labels(data.metadata)
        res = Resource(
            Deployment(
                apiVersion="apps/v1",
                kind="Deployment",
                metadata=ObjectMeta(
                    name=data.metadata.name,
                    namespace=data.metadata.namespace,
                    labels=default_labels | ctx.system.labels() | ctx.run.labels()
                    if ctx.run is not None
                    else {},
                    annotations={},
                ),
                spec=DeploymentSpec(
                    selector=LabelSelector(matchLabels=default_labels),
                    template=PodTemplateSpec(
                        metadata=ObjectMeta(labels=default_labels),
                        spec=PodSpec(
                            containers=[
                                Container(
                                    name=data.runtime.container_name,
                                )
                            ]
                        ),
                    ),
                ),
            )
        )

        for mut in self.mutators:
            mut.execute(log, data, res)

        return [res]


DEFAULT_CONFIG = Settings.Resource(
    provider=Provider,
    mutators=[
        EnvMutator,
        ContainerPortMutator,
        RuntimeMutator,
        DefaultContainerAnnotationMutator,
    ],
)
