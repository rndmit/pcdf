from importlib.metadata import version as pkg_version
from typing import Self

from pydantic import BaseModel

from pcdf.core.context import SystemInfo
from pcdf.core.resource import (
    AbstractResourceMutator,
    AbstractResourceProvider,
    check_datamodel_conformance,
)


class Settings(BaseModel):
    class Resource(BaseModel):
        provider: type[AbstractResourceProvider]
        mutators: list[type[AbstractResourceMutator]]

        def with_mutators(self, *mutators: type[AbstractResourceMutator]) -> Self:
            self.mutators += list(mutators)
            return self

    resources: list[Resource]
    version: str
    framework_version: str = pkg_version("pcdf")

    def get_system_info(self) -> SystemInfo:
        return SystemInfo(
            version=self.version, framework_version=self.framework_version
        )


def validate_config(cfg: list[Settings.Resource], input: BaseModel):
    """Checks if input datamodel conforms to"""
    for res in cfg:
        check_datamodel_conformance(res.provider, input)
        for mut in res.mutators:
            check_datamodel_conformance(mut, input)
