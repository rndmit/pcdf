from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from logging import Logger
from typing import Any, Self, Protocol

from pydantic import BaseModel, Field


class ExecutionStage(Enum):
    PRE_HOOK = "pre_hook"
    MAIN = "main"
    POST_HOOK = "post_hook"


class Resource[V: BaseModel]:
    model: V
    tags: dict[str, str]

    def __init__(self, model: V) -> None:
        self.model = model


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

    mutators: list[AbstractResourceMutator] = []

    @classmethod
    def fqname(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"

    def with_mutators(self, *mutators: AbstractResourceMutator) -> Self:
        for m in mutators:
            self.mutators.append(m)
        return self

    @abstractmethod
    def execute(self, log: Logger, data: Any) -> Sequence[Resource]:  # pragma: no cover
        """main stage of Provider execution"""
        ...

    def pre_hook(self, log: Logger):  # pragma: no cover
        """pre_hook executed before main stage"""
        return

    def post_hook(self, log: Logger):  # pragma: no cover
        """post_hook executed after main stage"""
        return


class ResourceFactoryConfig(BaseModel):
    debug: bool = Field(default=False, description="Turns debug mode on/off")


class ResourceFactory[T]:
    providers: dict[str, AbstractResourceProvider]
    resources: list[Resource]

    def __init__(self, logger: Logger, cfg: ResourceFactoryConfig):
        self.logger = logger
        self.cfg = cfg
        self.providers = {}
        self.resources = []

    def with_providers(self, *providers: AbstractResourceProvider) -> Self:
        for p in providers:
            self.providers[p.fqname()] = p
        return self

    def run(self, data: T) -> Sequence[Resource]:
        for pname in self.providers.keys():
            self.logger.debug(f"executing {pname}")
            self._execute_provider(pname, data)
        return self.resources

    def _execute_provider(self, pname: str, data: T):
        provider = self.providers[pname]
        plog = self.logger.getChild(pname)

        if type(provider).pre_hook != AbstractResourceProvider.pre_hook:
            stlog = plog.getChild(ExecutionStage.PRE_HOOK.value)
            try:
                provider.pre_hook(stlog)
            except Exception as err:
                raise ProviderExecutionError(ExecutionStage.PRE_HOOK, pname, err)

        try:
            self.resources += provider.execute(plog, data)
        except Exception as err:
            raise ProviderExecutionError(ExecutionStage.MAIN, pname, err)

        if type(provider).post_hook != AbstractResourceProvider.post_hook:
            stlog = plog.getChild(ExecutionStage.POST_HOOK.value)
            try:
                provider.post_hook(stlog)
            except Exception as err:
                raise ProviderExecutionError(ExecutionStage.POST_HOOK, pname, err)
