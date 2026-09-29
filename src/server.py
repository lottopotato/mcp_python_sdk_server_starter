from __future__ import annotations

from typing import *
# from pydantic import AnyHttpUrl, BaseModel

from src.modules.logging_module import LoggingModule, LoggingModuleConfig
from mcp_types import Tool as MCPTool

from starlette.applications import Starlette
from starlette.middleware import Middleware
from mcp.server import MCPServer
from mcp.server.transport_security import DEFAULT_MAX_REQUEST_BODY_SIZE, TransportSecuritySettings
import logging
import uvicorn
import anyio


class StreamableServer(MCPServer):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        streamable_http_path: str = "/mcp",
        stateless_http: bool = False,
        transport_security: Optional[TransportSecuritySettings] = None,
        max_request_body_size: int = DEFAULT_MAX_REQUEST_BODY_SIZE,
        *args,
        **kwargs
    ):
        super().__init__(
            name=name,
            *args,
            **kwargs
        )
        self.host = host
        self.port = port
        self.stateless_http = stateless_http
        self.max_request_body_size = max_request_body_size
        self.transport_security = transport_security

        logging_module = LoggingModule(
            LoggingModuleConfig(log_level=logging.INFO)
        )
        self.app: Starlette = self.streamable_http_app(
            streamable_http_path=streamable_http_path,
            stateless_http=self.stateless_http,
            max_request_body_size=self.max_request_body_size,
            transport_security=self.transport_security,
            host=self.host,
        )
        self.logger = logging_module.create_rich_logger(
            name=name,
            log_file_name=f"logs/{name}.log",
            level=logging.INFO
        )

    def add_middleware(self, middleware: Middleware, **options) -> None:
        self.app.add_middleware(middleware, **options)

    def preprocess_before_run(
        self,
        preprocessing: Optional[list[Callable]] = None,
    ) -> None:
        if preprocessing is not None:
            for function in preprocessing:
                if isinstance(function, Callable):
                    function()

        custom_routes_rows = []
        for route in self._custom_starlette_routes:
            self.app.add_route(
                path=route.path,
                route=route,
                methods=route.methods,
                name=route.name,
                include_in_schema=route.include_in_schema,
            )
            custom_routes_rows.append([str(route.name), str(route.path), str(route.methods)])

        list_tools: list[MCPTool] = self._tool_manager.list_tools()
        list_tools = sorted(list_tools, key=lambda tool: tool.name)
        self.logger.info("Registered Tools:")
        table = LoggingModule.create_rich_table(
            title="Registered Tools",
            columns=["No", "Name"],
            rows=[[str(index + 1), str(tool.name)] for index, tool in enumerate(list_tools)],
            table_config={
                "body": {"style": "dim"},
                "columns": {
                    0: {"style": "dim", "width": 5},
                    1: {"style": "bold cyan", "width": 40},
                }
            }
        )
        self.logger.info(table)

        if len(custom_routes_rows) > 0:
            table = LoggingModule.create_rich_table(
                title="Custom Routes Added",
                columns=["Name", "Path", "Methods"],
                rows=custom_routes_rows,
                table_config={
                    "body": {"style": "dim"},
                    "columns": {
                        0: {"style": "dim", "width": 20},
                        1: {"style": "bold cyan", "width": 40},
                        2: {"style": "bold magenta"}
                    },
                }
            )
            self.logger.info(table)

    def show_info(self) -> None:
        table = LoggingModule.create_rich_table(
            title="Server Configuration",
            columns=["Name", "Value"],
            rows=[[str(key), str(value)] for key, value in self.settings.__dict__.items()],
            table_config={
                "body": {"style": "dim"},
                "columns": {
                    0: {"style": "dim", "width": 40},
                    1: {"style": "bold cyan"}
                }
             }
        )
        self.logger.info(table)
    
    async def run_async(self) -> None:
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run(self, show_info: bool = True) -> None:
        if show_info:
            self.show_info()
        anyio.run(self.run_async)

        
        