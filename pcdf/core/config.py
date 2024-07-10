from pydantic import BaseModel, Field
from pcdf.core.resource import AbstractResourceProvider, AbstractResourceMutator, check_datamodel_conformance


class Config(BaseModel):
    class Resource(BaseModel):
        provider: type[AbstractResourceProvider]
        mutators: list[type[AbstractResourceMutator]]

    resources: list[Resource]
    debug: bool = Field(default=False, description="Turns debug mode on/off")


def validate_config(cfg: list[Config.Resource], input: BaseModel):
    """Checks if input datamodel conforms to"""
    for res in cfg:
        check_datamodel_conformance(res.provider, input)

        for mut in res.mutators:
            check_datamodel_conformance(mut, input)