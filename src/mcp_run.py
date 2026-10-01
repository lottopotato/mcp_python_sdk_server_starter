from .mcp import SERVER

import argparse

# Run the server for debug
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the mcp server")

    args = parser.parse_args()
    SERVER.preprocess_before_run(
        preprocessing=[]
    )
    SERVER.run()

# python -m src.mcp_run