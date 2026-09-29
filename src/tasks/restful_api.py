from __future__ import annotations

from typing import *

import logging
from starlette.responses import Response, JSONResponse
from starlette.requests import Request

logger = logging.getLogger(__name__)

class RestfulAPI:
    def __init__(
        self,
        parse_rest_payload: Callable[..., Awaitable[dict[str, Any]]]
    ):
        self.parse_rest_payload = parse_rest_payload

    @staticmethod
    def callback(
        content: Any,
        status_code: int = 200,
        headers: Optional[dict[str, Any]] = None,
        media_type: Optional[str] = "application/json",
        background: Optional[Any] = None,
    ) -> JSONResponse:
        return JSONResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    async def do_something_independently(
        self,
        request: Request,
    ) -> Response:
        payload = await self.parse_rest_payload(request)
        return self.callback(content="Do something independently")

    async def do_something_with_any(
        self,
        request: Request,
        any_function: Callable[..., Awaitable[Any]],
    ) -> Response:
        data = await self.parse_rest_payload(request) 
        result = await any_function(**data)
        return self.callback(content=result)