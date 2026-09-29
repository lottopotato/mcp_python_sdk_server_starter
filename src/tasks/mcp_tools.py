from __future__ import annotations

from typing import *

import logging
from tasks.shared_dependencies import SharedDependencies

logger = logging.getLogger(__name__)

class Tools:
    def __init__(
        self,
        dependencies: SharedDependencies
    ):
        self.dependencies = dependencies

    async def do_something(self) -> str:
        """Perform some action and return a result."""
        return "something"
    