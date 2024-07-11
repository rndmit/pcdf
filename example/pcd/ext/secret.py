from collections.abc import Sequence
from logging import Logger
from typing import Protocol, runtime_checkable

from pcdf import Settings
from pcdf.core import (
    AbstractResourceProvider,
    Resource,
    RunContext,
)
from pcdf.lib import datamodel

from kubemodels.io.k8s.api.core.v1 import Secret
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta


class Provider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata

    def execute(
        self, log: Logger, ctx: RunContext, data: Datamodel
    ) -> Sequence[Resource]:
        return [
            Resource(
                Secret(
                    apiVersion="core/v1",
                    kind="Job",
                    metadata=ObjectMeta(
                        name=data.metadata.name, namespace=data.metadata.namespace
                    ),
                    stringData={"somesecretvariable": "oh it's very secret"},
                )
            )
        ]
