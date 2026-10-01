from __future__ import annotations

from typing import *
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.mcpserver import Context
from starlette.responses import Response, JSONResponse
from starlette.requests import Request

import logging

from .server import StreamableServer
# Modules
from .modules import Module
from .modules.logging_module import LoggerLevel, LoggingModule, LoggingModuleConfig
# Tasks
from .tasks.helpers import Helpers
from .tasks.shared_dependencies import SharedDependencies
# Configuration
from .configuration.server_config import ServerConfig
# Utilities
from .utils.various import random_uuid4
# Resources
from .tasks.mcp_resources import Resources
# Tools
from .tasks.mcp_tools import Tools
# Restful API
from .tasks.restful_api import RestfulAPI

load_dotenv() # .env

# ======== Configuration ========
LOG_LEVEL = LoggerLevel.to_int(Helpers.get_env('log_level', 'INFO'))

SSE_LOGGER= logging.getLogger("sse_starlette.sse") # starlette SSE logger
SSE_LOGGER.setLevel(logging.INFO)

ENABLE_DNS_REBINDING_PROTECTION = Helpers.get_env_bool("enable_dns_rebinding_protection", default=False)
# Note: In production, you should set ALLOWED_HOSTS and ALLOWED_ORIGINS to the specific hostnames or IP addresses of your gateway or frontend application to prevent DNS rebinding attacks. 
# ALLOWED_HOSTS = ["your-gateway-host:*"]
# ALLOWED_ORIGINS = ["http://your-gateway-host:*"]

## For development purposes, you can allow localhost.
ALLOWED_HOSTS = Helpers.get_env_list(
    "allowed_hosts",
    default=["127.0.0.1:*", "localhost:*", "[::1]:*"],
)
ALLOWED_ORIGINS = Helpers.get_env_list(
    "allowed_origins",
    default=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
)

# Guardrails for risky retrieval tuning via extraKwargs.
ALLOW_TEST_RETRIEVE_KWARGS = Helpers.get_env_bool("allow_test_kwargs", default=False)

# ======== Initialize Server ========
SERVER = StreamableServer(
    name=ServerConfig.name,
    host=ServerConfig.host,
    port=ServerConfig.port,
    stateless_http=ServerConfig.stateless_http,
    debug=(LOG_LEVEL <= logging.DEBUG),
    log_level=LoggerLevel.to_str(LOG_LEVEL), # need to string level name for StreamableServer
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=ENABLE_DNS_REBINDING_PROTECTION,
        allowed_hosts=ALLOWED_HOSTS,
        allowed_origins=ALLOWED_ORIGINS,
    )
)

# ======== Initialize modules ========
# 1. Agent Logger
log_module = LoggingModule(LoggingModuleConfig(log_level=LOG_LEVEL))
AGENT_LOGGER = log_module.create_rich_logger(
    name="Agent",
    log_file_name="logs/Agent.log",
    level=LOG_LEVEL
)

# 0. Module A
MODULE_A = Module()

# ======== Permission scopes ========
MASTER_PERMISSION = 'admin'
_API_PERMISSION = 'type:job'
_STREAMABLE_PERMISSION = 'type:streaming'
_PERMISSION = [_API_PERMISSION, _STREAMABLE_PERMISSION, MASTER_PERMISSION]

# ======== Custom middleware ========
# 1. CORS middleware (Deprecated recently mcp version. CORS is now handled by FastMCP's built-in CORS handling, which can be configured in the server settings.)
allow_origins = ["*"]  # Allow all origins for development; restrict in production
allow_methods = ["*"]  # Allow all HTTP methods
allow_headers = ["*"]  # Allow all headers
allow_credentials = True  # Allow cookies and authentication headers
expose_headers = [] if SERVER.stateless_http else ["mcp-session-id"] # Expose session ID header for stateful HTTP

SERVER.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
    allow_credentials=allow_credentials,
    expose_headers=expose_headers,
)

# ======== Public functions wrapping with static configuration ========
async def parse_rest_payload(
    request: Request,
    nested_keys: Optional[list[str]] = None
) -> dict[str, Any]:
    return await Helpers.parse_rest_payload(
        request=request,
        agent_logger=AGENT_LOGGER,
        nested_keys=nested_keys,
    )

def sanitize_extra_kwargs(extra_kwargs: Optional[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    return Helpers.sanitize_extra_kwargs(
        extra_kwargs=extra_kwargs,
        allow_test_kwargs=ALLOW_TEST_RETRIEVE_KWARGS
    )

# ======== MCP API endpoints with static configuration ========
shared_dependencies = SharedDependencies(
    log_level=LOG_LEVEL,
    agent_logger=AGENT_LOGGER,
    _permission=_PERMISSION,

    parse_rest_payload=parse_rest_payload,
    sanitize_extra_kwargs=sanitize_extra_kwargs,
    send_error=Helpers.send_error,
    random_uuid4=random_uuid4,

    module_a=MODULE_A,

)

resources = Resources(
    dependencies=shared_dependencies
)

tools = Tools(
    dependencies=shared_dependencies,
)

restful_api = RestfulAPI(
    parse_rest_payload=parse_rest_payload,
)

# ======== MCP Streamable-HTTP Endpoints ========
# ----- Resources -----
# 1. README.md resource

@SERVER.resource(
    uri='file://README.md',
    name='README.md',
    description='Resource of README file',
    mime_type='text/markdown',
)
async def readme_resource() -> str:
    return await resources.readme_resource()

# ----- Tools -----
# 1. Do_something; Dummy tool

@SERVER.tool(
    name="Do_something",
    description=tools.do_something.__doc__,
)
async def do_something(
) -> str:
    return await tools.do_something()

# ======== API endpoints (Restful) ========
# 1. /api/v1/do_something

@SERVER.custom_route(
    "/api/v1/do_something",
    methods=["POST"]
)
async def do_something_restful(request: Request) -> Response:
    return await restful_api.do_something_independently(request=request)

__all__ = ['SERVER']