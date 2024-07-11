from collections.abc import Sequence
from dataclasses import dataclass
from logging import Logger
from typing import Protocol, runtime_checkable

from kubemodels.io.k8s.api.apps.v1 import Deployment, DeploymentSpec
from kubemodels.io.k8s.api.core.v1 import (
    ConfigMapVolumeSource,
    ResourceRequirements,
    Container,
    ContainerPort,
    EnvVar,
    KeyToPath,
    PodSpec,
    PodTemplateSpec,
    Volume,
    VolumeMount,
)
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import LabelSelector, ObjectMeta
from kubemodels.io.k8s.apimachinery.pkg.api.resource import Quantity

from pcdf import Settings
from pcdf.core import (
    AbstractResourceMutator,
    AbstractResourceProvider,
    Resource,
    RunContext,
)
from pcdf.lib import datamodel, utils
from pcdf.lib.exceptions import IncorrectManifestError


@dataclass
class MainContainersMiscountError(Exception):
    mc_name: str
    count: int

    def __str__(self) -> str:
        return f" has {self.count} container named '{self.mc_name}'. Expected only 1"


def app_container(containers: list[Container], runtime_cfg: datamodel.Runtime):
    ct = [c for c in containers if c.name == runtime_cfg.containerName]
    if (ctlen := len(ct)) != 1:
        raise MainContainersMiscountError(runtime_cfg.containerName, ctlen)
    return ct[0]


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

        ct = app_container(spec.template.spec.containers, data.runtime)
        ct.image = f"{data.runtime.image}:{data.runtime.tag}"
        ct.command = data.runtime.entrypoint
        ct.args = data.runtime.command

        spec.replicas = data.runtime.replicas


class ResourcesMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        runtime: datamodel.Runtime
        resources: datamodel.Resources

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (spec := resource.model.spec) is None or spec.template.spec is None:
            raise IncorrectManifestError(self.__qualname__)

        ct = app_container(spec.template.spec.containers, data.runtime)
        ct.resources = ResourceRequirements(
            limits={
                "cpu": Quantity(data.resources.limits.cpu),
                "memory": Quantity(data.resources.limits.memory),
            },
            requests={
                "cpu": Quantity(data.resources.requests.cpu),
                "memory": Quantity(data.resources.requests.memory),
            },
        )


class ContainerPortMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        network: datamodel.Networking
        runtime: datamodel.Runtime

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (spec := resource.model.spec) is None or spec.template.spec is None:
            raise IncorrectManifestError(self.__qualname__)

        ct = app_container(spec.template.spec.containers, data.runtime)
        ct.ports = [
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
            data.runtime.containerName
        )


class ConfigmapMountMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        files: list[datamodel.Document]
        runtime: datamodel.Runtime
        filesMountPath: str

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Deployment]):
        if (spec := resource.model.spec) is None or spec.template.spec is None:
            raise IncorrectManifestError(self.__qualname__)

        if len(data.files) < 1:
            return

        tplspec = spec.template.spec
        if tplspec.volumes is None:
            tplspec.volumes = []
        tplspec.volumes.append(
            Volume(
                name="mounted-config",
                configMap=ConfigMapVolumeSource(
                    name=data.metadata.name,
                    items=[KeyToPath(key=f.name, path=f.name) for f in data.files],
                ),
            )
        )

        ct = app_container(spec.template.spec.containers, data.runtime)
        ct.volumeMounts = [
            VolumeMount(mountPath=data.filesMountPath, name="mounted-config")
        ]


class Provider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        runtime: datamodel.Runtime

    def execute(
        self, log: Logger, ctx: RunContext, data: Datamodel
    ) -> Sequence[Resource]:
        default_labels = utils.default_labels(data.metadata)
        res = Resource(
            Deployment(
                apiVersion="apps/v1",
                kind="Deployment",
                metadata=ObjectMeta(
                    name=data.metadata.name,
                    namespace=data.metadata.namespace,
                    labels=default_labels
                    | {"app.kubernetes.io/version": data.runtime.tag}
                    | ctx.system.labels()
                    | ctx.run.labels(),
                    annotations={},
                ),
                spec=DeploymentSpec(
                    selector=LabelSelector(matchLabels=default_labels),
                    template=PodTemplateSpec(
                        metadata=ObjectMeta(labels=default_labels),
                        spec=PodSpec(
                            containers=[
                                Container(
                                    name=data.runtime.containerName,
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
        ConfigmapMountMutator,
        DefaultContainerAnnotationMutator,
    ],
)
