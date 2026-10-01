# gunicorn.conf.py
import os
from dotenv import load_dotenv

load_dotenv()

# The address and port to bind to
# bind = "0.0.0.0:8096"
bind = os.getenv("gunicorn_bind", "127.0.0.1:8000")

# The number of worker processes
# Rule of thumb: (2 * CPU cores) + 1
# cpu_cores = 8  # Adjust this based on your server's CPU cores
# workers ~= cpu_cores * 2 + 1  # Assuming an 8-core machine
workers = int(os.getenv("gunicorn_workers", "1"))

# The type of worker to use
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
# Use '-' to log to stdout
accesslog = "-"
errorlog = "-"

wsgi_app = 'src.mcp:app'

# The user and group to run as (security best practice)
# user = "your_user"
# group = "your_group"

# Other settings
timeout = int(os.getenv("gunicorn_timeout", "600"))  # Increase timeout for long-running requests
# keepalive = 2

# To run the server, use the following command in your terminal:
# gunicorn -c gunicorn.conf.py