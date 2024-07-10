import logging
from pydantic import BaseModel

from pcdf.core import Config, validate_config, ProtocolConformanceError, ResourceFactory


def render(input: BaseModel, cfg: Config):
    log = logging.getLogger()

    try:
        validate_config(cfg.resources, input)
    except ProtocolConformanceError as err:
        sep = "\n - "
        log.fatal(
            f"input does not conform {err.protocol}. Missing fields: {sep + sep.join(err.unconformed)}"
        )
        exit(1)

    r = ResourceFactory[BaseModel].from_config(log, cfg).run(input)
    for res in r:
        print(res.dump())