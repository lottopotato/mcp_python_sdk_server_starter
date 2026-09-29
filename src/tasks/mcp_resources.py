from __future__ import annotations

from typing import *

import os
import logging

from tasks.shared_dependencies import SharedDependencies

logger = logging.getLogger(__name__)

class Resources:
    def __init__(self, dependencies: SharedDependencies):
        self.dependencies = dependencies

    async def readme_resource(self) -> str:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        return content

    