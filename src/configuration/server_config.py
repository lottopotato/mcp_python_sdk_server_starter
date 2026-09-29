
import os
from dotenv import load_dotenv

load_dotenv()

class ServerConfig:
    name: str = 'MCP Streamable http Server'
    
    stateless_http: bool = os.getenv('server_stateless_http', 'false').lower() == 'true'
    
    # development mode
    port: int = int(os.getenv('server_port', '8096'))
    host: str = os.getenv('server_host', '127.0.0.1')

    # production mode
    # port: int = 80
    # host: str = ''
