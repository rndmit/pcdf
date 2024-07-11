from collections.abc import Sequence
from logging import Logger
from typing import Protocol, cast, runtime_checkable

from kubemodels.io.k8s.api.networking.v1 import (
    HTTPIngressPath,
    HTTPIngressRuleValue,
    Ingress,
    IngressBackend,
    IngressRule,
    IngressServiceBackend,
    IngressSpec,
    IngressTLS,
    ServiceBackendPort,
)
from kubemodels.io.k8s.apimachinery.pkg.apis.meta.v1 import ObjectMeta

from pcdf import Settings
from pcdf.core import (
    AbstractResourceMutator,
    AbstractResourceProvider,
    Resource,
    RunContext,
)
from pcdf.lib import datamodel, utils
from pcdf.lib.exceptions import IncorrectManifestError


class RulesMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        network: datamodel.Networking

    def __publication_port(self, data: datamodel.Publication) -> ServiceBackendPort:
        match p := data.destPort:
            case str():
                return ServiceBackendPort(name=cast("str", p))
            case int():
                return ServiceBackendPort(number=cast("int", p))
            case _:
                raise Exception("Unable to determine port type")

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Ingress]):
        if (spec := resource.model.spec) is None or spec.rules is None:
            raise IncorrectManifestError(self.__qualname__)

        for r in data.network.publicate:
            spec.rules.append(
                IngressRule(
                    host=r.host,
                    http=HTTPIngressRuleValue(
                        paths=[
                            HTTPIngressPath(
                                backend=IngressBackend(
                                    service=IngressServiceBackend(
                                        name=data.metadata.name
                                        if (rdo := r.destOverride) is None
                                        else rdo,
                                        port=self.__publication_port(r),
                                    )
                                ),
                                path=r.path,
                                pathType=r.pathType,
                            )
                        ]
                    ),
                )
            )


class TlsMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        network: datamodel.Networking

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Ingress]):
        if not data.network.tls:
            return

        if (spec := resource.model.spec) is None or spec.rules is None:
            raise IncorrectManifestError(self.__qualname__)

        spec.tls = [
            IngressTLS(
                hosts=[pub.host for pub in data.network.publicate],
                secretName=f"{data.metadata.name}{data.network.tlsSecretSuffix}",
            )
        ]


class CertManagerMutator(AbstractResourceMutator):
    @runtime_checkable
    class Datamodel(Protocol):
        network: datamodel.Networking
        certmanager: datamodel.CertManager

    def execute(self, log: Logger, data: Datamodel, resource: Resource[Ingress]):
        if not data.network.tls:
            return

        if (meta := resource.model.metadata) is None:
            raise IncorrectManifestError(self.__qualname__)

        if meta.annotations is None:
            meta.annotations = {}
        meta.annotations.update(
            {
                f"cert-manager.io/{data.certmanager.issuerType}": data.certmanager.issuer,
            }
            | data.certmanager.annotations
        )


class Provider(AbstractResourceProvider):
    @runtime_checkable
    class Datamodel(Protocol):
        metadata: datamodel.Metadata
        network: datamodel.Networking

    def execute(
        self, log: Logger, ctx: RunContext, data: Datamodel
    ) -> Sequence[Resource]:
        default_labels = utils.default_labels(data.metadata)
        res = Resource(
            Ingress(
                apiVersion="networking.k8s.io/v1",
                kind="Ingress",
                metadata=ObjectMeta(
                    labels=default_labels | ctx.system.labels() | ctx.run.labels(),
                    annotations={},
                ),
                spec=IngressSpec(ingressClassName=data.network.ingressClass, rules=[]),
            )
        )

        for mut in self.mutators:
            mut.execute(log, data, res)

        return [res]


DEFAULT_CONFIG = Settings.Resource(
    provider=Provider, mutators=[RulesMutator, TlsMutator]
)
