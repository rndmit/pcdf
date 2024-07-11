from collections.abc import Sequence
from logging import Logger
from typing import  Protocol, runtime_checkable

from kubemodels.io.k8s.api.core.v1 import (
    ConfigMap,
)
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta

from pcdf import Settings
from pcdf.core import (
    AbstractResourceProvider,
    Resource,
    RunContext,
)
from pcdf.lib import datamodel, utils


class Provider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        files: list[datamodel.Document]

    def execute(
        self, log: Logger, ctx: RunContext, data: Datamodel
    ) -> Sequence[Resource]:
        default_labels = utils.default_labels(data.metadata)
        res = Resource(
            ConfigMap(
                apiVersion="core/v1",
                kind="ConfigMap",
                metadata=ObjectMeta(
                    name=data.metadata.name,
                    namespace=data.metadata.namespace,
                    labels=default_labels | ctx.system.labels() | ctx.run.labels(),
                ),
                data={f.name: f.content for f in data.files},
            )
        )

        for mut in self.mutators:
            mut.execute(log, data, res)

        return [res]


DEFAULT_CONFIG = Settings.Resource(provider=Provider, mutators=[])
