from typing import Protocol
from dataclasses import dataclass
from pydantic import BaseModel
from pcdf.core.resource import AbstractResourceProvider, AbstractResourceMutator


@dataclass
class ResourceCfg:
    provider: type[AbstractResourceProvider]
    mutators: list[type[AbstractResourceMutator]]


@dataclass
class UndefinedDatamodelError(Exception):
    entity: str

    def __str__(self) -> str:
        return f"{self.entity} has no Datamodel defined"


@dataclass
class ProtocolConformanceError(Exception):
    protocol: str
    unconformed: list[str]

    def __str__(self) -> str:
        return f"input does not conform {self.protocol}. Missing fields: \n\t{"\n\t".join(self.unconformed)}"


def check_protocols(cfg: list[ResourceCfg], input: BaseModel):
    """Checks if input datamodel conforms to"""
    for res in cfg:
        check_datamodel_conformance(res.provider, input)

        for mut in res.mutators:
            check_datamodel_conformance(mut, input)


class FqNamedEntity(Protocol):
    @classmethod
    def fqname(cls) -> str: ...


def check_datamodel_conformance(cls: FqNamedEntity, input: BaseModel):
    try:
        datamodel = getattr(cls, "Datamodel")
    except AttributeError:
        raise UndefinedDatamodelError(cls.fqname())

    if not isinstance(input, datamodel):
        dmvars = vars(datamodel)
        raise ProtocolConformanceError(
            cls.fqname(),
            [
                f"{field}: {dmvars["__annotations__"][field]}"
                for field in set(dmvars["__protocol_attrs__"])
                - set(input.model_dump().keys())
            ],
        )
