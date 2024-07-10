import sys
from importlib.metadata import version as pkg_version
from pydantic import BaseModel, Field
from pcdf.core.resource import (
    AbstractResourceProvider,
    AbstractResourceMutator,
    check_datamodel_conformance,
)
from pcdf.core.context import SystemInfo


class Settings(BaseModel):
    class Resource(BaseModel):
        provider: type[AbstractResourceProvider]
        mutators: list[type[AbstractResourceMutator]]

    resources: list[Resource]
    debug: bool = Field(default=False, description="Turns debug mode on/off")
    version: str
    framework_version: str = pkg_version("pcdf")

    def get_system_info(self) -> SystemInfo:
        return SystemInfo(
            version=self.version,
            framework_version=self.framework_version
        )



def validate_config(cfg: list[Settings.Resource], input: BaseModel):
    """Checks if input datamodel conforms to"""
    for res in cfg:
        check_datamodel_conformance(res.provider, input)
        for mut in res.mutators:
            check_datamodel_conformance(mut, input)
