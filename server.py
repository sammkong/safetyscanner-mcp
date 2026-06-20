import os

from safetyscanner.tools import create_mcp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp = create_mcp(port=port)
    mcp.run(transport="streamable-http")
