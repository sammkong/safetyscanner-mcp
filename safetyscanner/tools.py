"""MCP tool definitions for SafetyScanner."""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from safetyscanner.scorer import score_text


mcp = FastMCP(
    name="SafetyScanner",
    host="0.0.0.0",
    port=8000,
    streamable_http_path="/mcp",
    stateless_http=True,
)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Score Listing Risk",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=True,
    )
)
def score_listing_risk(text: str) -> str:
    """Score a listing text for fraud risk."""
    return score_text(text)
