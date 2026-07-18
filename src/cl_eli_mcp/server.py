"""FastMCP entry point - Chilean legislation (BCN Linked Open Data) tools.

Run:

    python -m cl_eli_mcp.server

Configuration via env:

- ``CL_ELI_CACHE_DIR`` (default ``~/.matematic/cache/cl-eli``)
- ``CL_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``CL_ELI_BASE_URL`` (default ``https://datos.bcn.cl/sparql``)
"""

from __future__ import annotations

import dataclasses
import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import runtime
from .audit import AuditLogger, hash_input, timer
from .citations import build_citation, group_describe, norm_from_bindings, norm_from_search_row
from .client import DEFAULT_BASE_URL, BcnSparqlClient

INSTRUCTIONS = """\
This MCP server exposes the BCN (Biblioteca del Congreso Nacional de Chile) Linked Open Data SPARQL endpoint. It searches and fetches Chilean legislation (laws, decrees, resolutions) via a persistent resource URI - not called ELI, but structurally the same idea: jurisdiction/type/issuing-body/date/number.

## Call order

1. `cl_search_norms` - full-text search over norm titles (e.g. "ley de transito").
2. `cl_get_norm` - full detail for one norm by its `uri` (from the search results).

## Hard constraints

- **The resource URI IS the citation contract** - `lex_uri` and `source_url` are the same BCN URI; dereferencing it (a plain GET, following redirects) resolves to a human-readable page.
- **No full-text law content** - this connector returns metadata (title, number, dates, issuing body), not the operative articles of the law. For that, follow `source_url`.
- **Every response has `human_readable_citation`** - e.g. "Ley 18290, de 1984-01-23". Cite it plus `source_url`.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/cl-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing or malformed.
- `not_found` - no norm exists at that URI.
- `upstream_error` - a BCN SPARQL endpoint error (HTTP, timeout, malformed query). Retry once before surfacing.

## Response style

- Cite norms as `human_readable_citation`: "Ley 18290, de 1984-01-23".
- NEVER invent a URI, a number or a date - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for cl-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="cl-eli-mcp", instructions=INSTRUCTIONS)


def _base_url() -> str:
    return os.environ.get("CL_ELI_BASE_URL", runtime.base_url("eli", DEFAULT_BASE_URL))


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"BCN SPARQL endpoint error: {type(exc).__name__}: {exc}")
    return exc


def _to_dict(n) -> dict:
    citation = build_citation(n)
    return {**dataclasses.asdict(n), **dataclasses.asdict(citation)}


# ---------------------------------------------------------------------------
# cl_search_norms
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def cl_search_norms(query: str, limit: int = 20) -> dict:
    """Full-text search over Chilean legislation titles.

    Args:
        query: free text, e.g. ``"ley de transito"``.
        limit: max results (default 20).

    Returns:
        ``{"total": int, "items": [...]}`` - each item carries the citation contract.
    """
    audit = _audit()
    if not query or not query.strip():
        raise ToolError("invalid_arg", "query must be a non-empty string.")
    input_hash = hash_input({"query": query, "limit": limit})

    with timer() as t:
        try:
            async with BcnSparqlClient(base_url=_base_url()) as client:
                rows = await client.search(query, limit)
        except Exception as exc:
            audit.log(tool="cl_search_norms", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    items = [_to_dict(norm_from_search_row(r)) for r in rows]
    audit.log(tool="cl_search_norms", input_hash=input_hash, output_count_or_size=len(items),
              duration_ms=t.duration_ms, status="ok")
    return {"total": len(items), "items": items}


# ---------------------------------------------------------------------------
# cl_get_norm
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def cl_get_norm(uri: str) -> dict:
    """Fetch full detail for one Chilean norm by its BCN resource URI.

    Args:
        uri: e.g. ``"http://datos.bcn.cl/recurso/cl/ley/ministerio-de-justicia/1984-02-07/18290"``.

    Returns:
        A dict with ``norm_type``, ``number``, ``title``, ``organism``,
        ``promulgation_date``, ``publish_date``, ``leychile_code``,
        ``lex_uri``, ``human_readable_citation``, ``source_url``.
    """
    audit = _audit()
    if not uri or not uri.startswith("http://datos.bcn.cl/recurso/"):
        raise ToolError("invalid_arg", "uri must be a http://datos.bcn.cl/recurso/... BCN resource URI.")
    input_hash = hash_input({"uri": uri})

    with timer() as t:
        try:
            async with BcnSparqlClient(base_url=_base_url()) as client:
                bindings = await client.describe(uri)
        except Exception as exc:
            audit.log(tool="cl_get_norm", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    if not bindings:
        raise ToolError("not_found", f"No norm found at uri={uri!r}.")
    props = group_describe(bindings)
    result = _to_dict(norm_from_bindings(uri, props))
    audit.log(tool="cl_get_norm", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
