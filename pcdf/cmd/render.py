import logging

from pydantic import BaseModel

from pcdf.core import Settings, ProtocolConformanceError, ResourceFactory, validate_config


def render(input: BaseModel, cfg: Settings):
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    try:
        validate_config(cfg.resources, input)
    except ProtocolConformanceError as err:
        sep = "\n - "
        log.fatal(
            f"Given datamodel does not conform {err.protocol} protocol. Missing fields: {sep + sep.join(err.unconformed)}"
        )
        exit(1)

    r = ResourceFactory.from_config(log, cfg).run(input)
    for res in r:
        print(res.dump(),"\n---\n")
