from .mcp import SERVER

# Run via gunicorn with the command: gunicorn -c gunicorn.conf.py
SERVER.preprocess_before_run(
    preprocessing=[]
)
SERVER.show_info()
app = SERVER.app
