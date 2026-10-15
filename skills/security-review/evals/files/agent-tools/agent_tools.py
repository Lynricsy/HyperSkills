"""Tools exposed to the hosted coding agent.

Each tenant gets a directory under WORKSPACES_ROOT named after its slug (for example
`acme`, `acme-labs`, `globex`). The model chooses every tool argument; tool calls are
executed by this worker process, which runs as one OS user for all tenants. The same
module ships in the Windows desktop edition, where WORKSPACES_ROOT is under %LOCALAPPDATA%.
"""

import os
import urllib.parse

import requests

WORKSPACES_ROOT = os.environ.get("WORKSPACES_ROOT", "/srv/agent/workspaces")
PARTNER_HOSTS = {"api.partner-docs.com", "status.partner-docs.com"}
PARTNER_API_KEY = os.environ["PARTNER_API_KEY"]  # paid API, billed per call
MAX_BYTES = 2_000_000


def _workspace(tenant_slug: str) -> str:
    return os.path.realpath(os.path.join(WORKSPACES_ROOT, tenant_slug))


def write_file(tenant_slug: str, rel_path: str, content: str) -> str:
    """Tool: create or overwrite a file inside the tenant's workspace."""
    root = _workspace(tenant_slug)
    target = os.path.realpath(os.path.join(root, rel_path))
    if not target.startswith(root):
        raise PermissionError(f"{rel_path} is outside the workspace")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(content)
    return target


def read_file(tenant_slug: str, rel_path: str) -> str:
    """Tool: read a file from the tenant's workspace."""
    root = _workspace(tenant_slug)
    target = os.path.realpath(os.path.join(root, rel_path))
    if not target.startswith(root):
        raise PermissionError(f"{rel_path} is outside the workspace")
    with open(target, encoding="utf-8") as fh:
        return fh.read(MAX_BYTES)


def fetch_docs(url: str) -> str:
    """Tool: fetch a page from the partner documentation API."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in PARTNER_HOSTS:
        raise PermissionError("only partner documentation hosts are allowed")
    resp = requests.get(
        url,
        headers={"X-Api-Key": PARTNER_API_KEY, "User-Agent": "agent-docs/1.4"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.text[:MAX_BYTES]
