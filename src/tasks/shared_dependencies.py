from typing import *
from dataclasses import dataclass

import logging

from src.modules import Module

@dataclass
class SharedDependencies:
    # Logging
    log_level: int
    agent_logger: logging.Logger

    # Public functions
    parse_rest_payload: Callable[..., Awaitable[dict[str, Any]]]
    sanitize_extra_kwargs: Callable[..., tuple[dict[str, Any], list[str]]]
    send_error: Callable[..., dict[str, Any]]
    random_uuid4: Callable[..., str]

    # Permission scopes
    _permission: list[str]
    
    # Database
    
    # Modules
    module_a: Module
