from collections.abc import Sequence
from logging import Logger
from typing import Self
from ksuid import Ksuid

from pcdf.core.settings import Settings
from pcdf.core.resource import (
    AbstractResourceProvider,
    Resource,
    ExecutionStage,
    ProviderExecutionError,
)
from pcdf.core.context import Context, SystemInfo, RunInfo


class ResourceFactory[T]:
    __slots__ = [
        "logger",
        "root_ctx",
        "providers",
        "resources",
    ]

    providers: dict[str, AbstractResourceProvider]
    resources: list[Resource]

    def __init__(self, logger: Logger, si: SystemInfo):
        self.logger = logger
        self.root_ctx = Context(si)
        self.providers = {}
        self.resources = []

    @classmethod
    def from_config(cls, logger: Logger, settings: Settings) -> Self:
        return cls(logger, settings.get_system_info()).with_providers(
            *[
                res.provider().with_mutators(*[mut() for mut in res.mutators])
                for res in settings.resources
            ]
        )

    def with_providers(self, *providers: AbstractResourceProvider) -> Self:
        for p in providers:
            self.providers[p.fqname()] = p
        return self

    def run(self, data: T) -> Sequence[Resource]:
        ctx = self.root_ctx.with_run_info(RunInfo(id=Ksuid().__str__()))
        for pname in self.providers.keys():
            self.logger.debug(f"executing {pname}")
            self._execute_provider(ctx, pname, data)
        return self.resources

    def _execute_provider(self, ctx: Context, pname: str, data: T):
        ctx = ctx.with_values({"pname": pname})
        provider = self.providers[pname]
        plog = self.logger.getChild(pname)

        if type(provider).pre_hook != AbstractResourceProvider.pre_hook:
            stlog = plog.getChild(ExecutionStage.PRE_HOOK.value)
            try:
                provider.pre_hook(stlog, ctx)
            except Exception as err:
                raise ProviderExecutionError(ExecutionStage.PRE_HOOK, pname, err)

        try:
            self.resources += provider.execute(plog, ctx, data)
        except Exception as err:
            raise ProviderExecutionError(ExecutionStage.MAIN, pname, err)

        if type(provider).post_hook != AbstractResourceProvider.post_hook:
            stlog = plog.getChild(ExecutionStage.POST_HOOK.value)
            try:
                provider.post_hook(stlog, ctx)
            except Exception as err:
                raise ProviderExecutionError(ExecutionStage.POST_HOOK, pname, err)
