import os
from typing import Annotated

import httpx
from pydantic import Field
from mcp.server.mcpserver import MCPServer

API_URL = os.environ.get("TICKETS_API_URL", "https://tickets.corp.example/api")
TOKEN = os.environ["TICKETS_API_TOKEN"]

# httpx picks up HTTPS_PROXY and SSL_CERT_FILE from the environment (trust_env=True),
# which is how it reaches the API through the corporate proxy.
client = httpx.Client(base_url=API_URL, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)

mcp = MCPServer("tickets", version="1.2.0")


@mcp.tool()
def search_tickets(query: Annotated[str, Field(description="Free text, e.g. 'login timeout'")]) -> str:
    """Search open tickets by text. Returns at most 20 tickets as JSON lines."""
    rows = client.get("/tickets", params={"q": query, "limit": 20}).json()
    return "\n".join(f'{r["id"]}\t{r["title"]}' for r in rows)


if __name__ == "__main__":
    mcp.run()
