# Python MCP Server Starter

A Python starter pack that you can clone and customize for projects that need an MCP server. It provides a Streamable HTTP server setup, example tools and resources, and a REST API route.

## Features

- MCP Streamable HTTP endpoint (`/mcp`)
- Example MCP tool: `Do_something`
- MCP resource that returns the project README: `file://README.md`
- REST API endpoint: `POST /api/v1/do_something`
- Server configuration through environment variables and a `.env` file

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)

## Installation

Install the project dependencies from the repository root:

```bash
uv sync
```

## Running the Server

The `python-mcp-server` command does not currently start the server. The server application is configured in `src/main.py`, but it is not connected to the package CLI entry point. Connect an appropriate entry point before deciding how to launch the server.

## Configuration

Copy `.env_example` to `.env` in the repository root, then update the values as needed. `.env` is excluded from Git because it may contain sensitive information, while `.env_example` is committed as a shareable configuration template. If a setting is omitted, its default value from the table below is used.

```bash
cp .env_example .env
```

| Environment variable | Default | Description |
|---|---|---|
| `server_host` | `127.0.0.1` | Address the server binds to |
| `server_port` | `8096` | Server port |
| `server_stateless_http` | `false` | Whether to use stateless mode for HTTP transport |
| `log_level` | `INFO` | Logging level |
| `enable_dns_rebinding_protection` | `false` | Enable DNS rebinding protection |
| `allowed_hosts` | `127.0.0.1:*,localhost:*,[::1]:*` | Comma-separated list of allowed hosts for DNS rebinding protection |
| `allowed_origins` | `http://127.0.0.1:*,http://localhost:*,http://[::1]:*` | Comma-separated list of allowed origins for DNS rebinding protection |
| `allow_test_kwargs` | `false` | Allow test-only retrieval arguments |

`allowed_hosts` and `allowed_origins` are passed to the DNS rebinding protection settings. The current CORS middleware allows all origins, methods, and headers for development convenience. Restrict these settings before deploying to production.

## Available Interfaces

### MCP Tool

| Name | Description | Return value |
|---|---|---|
| `Do_something` | Performs an example action | `something` |

### MCP Resource

| URI | Description |
|---|---|
| `file://README.md` | Reads and returns `README.md` from the current working directory at runtime |

### REST API

`POST /api/v1/do_something` parses a JSON or form request body. The current example implementation returns the JSON string `"Do something independently"`.

```bash
curl -X POST http://127.0.0.1:8096/api/v1/do_something \
  -H 'Content-Type: application/json' \
  -d '{}'
```

## Project Structure

```text
src/
├── configuration/  # Server configuration
├── modules/        # Shared modules and logging
├── tasks/          # MCP tools and resources, and REST API
├── utils/          # Utilities
├── main.py         # Server and interface configuration
└── server.py       # Streamable HTTP server wrapper
```

## Development Notes

- Project metadata and dependencies are managed in `pyproject.toml`.
- The `.env` file is loaded automatically.
- The default server address and port are intended for development. Review the bind address, allowed hosts, and CORS policy before exposing the server externally.
