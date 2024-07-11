import logging
from typing import TypedDict
from pcdf.core import Settings

from pydantic import BaseModel


class CommandContext(TypedDict):
    logger: logging.Logger
    settings: Settings
    datamodel: type[BaseModel]
    interactive: bool
