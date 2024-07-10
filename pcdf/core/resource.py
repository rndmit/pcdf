from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from logging import Logger
from typing import Any, Self, Protocol

from pydantic import BaseModel

from pcdf.core.context import Context

class ExecutionStage(Enum):
    PRE_HOOK = "pre_hook"
    MAIN = "main"
    POST_HOOK = "post_hook"


class Resource[V: BaseModel]:
    model: V
    tags: dict[str, str]

    def __init__(self, model: V) -> None:
        self.model = model

    def dump(self) -> dict[str, Any]:
        return self.model.model_dump(exclude_none=True)


class AbstractResourceMutator(ABC):
    @classmethod
    def fqname(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"

    @abstractmethod
    def execute(self, log: Logger, data: Any, resource: Resource):
        pass


@dataclass
class ProviderExecutionError(Exception):
    stage: ExecutionStage
    provider_name: str
    wrapped_err: Exception

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.provider_name} execution failed on {self.stage.value} stage: {self.wrapped_err}"  # noqa: E501


class AbstractResourceProvider(ABC):
    """Base class for ResourceProviders"""

    mutators: list[AbstractResourceMutator]

    @classmethod
    def fqname(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"

    def with_mutators(self, *mutators: AbstractResourceMutator) -> Self:
        self.mutators = []
        for m in mutators:
            self.mutators.append(m)
        return self

    @abstractmethod
    def execute(self, log: Logger, ctx: Context, data: Any) -> Sequence[Resource]:  # pragma: no cover
        """main stage of Provider execution"""
        ...

    def pre_hook(self, log: Logger, ctx: Context):  # pragma: no cover
        """pre_hook executed before main stage"""
        return

    def post_hook(self, log: Logger, ctx: Context):  # pragma: no cover
        """post_hook executed after main stage"""
        return


class FqNamedEntity(Protocol):
    @classmethod
    def fqname(cls) -> str: ...


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
        return f"input does not conform {self.protocol}. Missing fields: {self.unconformed}"


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
