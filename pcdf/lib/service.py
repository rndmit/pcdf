from collections.abc import Sequence
from dataclasses import dataclass
from logging import Logger
from typing import Any, Protocol, runtime_checkable

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
    Service,
    ServiceSpec,
    PodTemplateSpec,
    PodSpec,
    Container,
    EnvVar,
    ContainerPort,
)
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta, LabelSelector


class Provider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        network: datamodel.Networking

    def execute(self, log: Logger, ctx: Context, data: Datamodel) -> Sequence[Resource]:
        assert ctx.run is not None, IncorrectRunContextErrorMsg

        default_labels = utils.default_labels(data.metadata)
        res = Resource(
            Service(
                apiVersion="core/v1",
                kind="Service",
                metadata=ObjectMeta(
                    labels=default_labels | ctx.system.labels() | ctx.run.labels()
                ),
                spec=ServiceSpec(selector=default_labels),
            )
        )

        for mut in self.mutators:
            mut.execute(log, data, res)

        return [res]


DEFAULT_CONFIG = Settings.Resource(provider=Provider, mutators=[])
