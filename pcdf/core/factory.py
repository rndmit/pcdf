from collections.abc import Sequence
from logging import Logger
from typing import Self

from pydantic import BaseModel, Field

from pcdf.core.config import Config
from pcdf.core.resource import (
    AbstractResourceProvider,
    Resource,
    ExecutionStage,
    ProviderExecutionError,
)


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

    @classmethod
    def from_config(cls, logger: Logger, cfg: Config) -> Self:
        return cls(logger, ResourceFactoryConfig(debug=cfg.debug)).with_providers(
            *[
                res.provider().with_mutators(*[mut() for mut in res.mutators])
                for res in cfg.resources
            ]
        )

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
