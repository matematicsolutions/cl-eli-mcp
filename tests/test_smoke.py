"""Live smoke test against the real BCN SPARQL endpoint. Network required."""

from __future__ import annotations

import pytest

from cl_eli_mcp.citations import build_citation, group_describe, norm_from_bindings, norm_from_search_row
from cl_eli_mcp.client import BcnSparqlClient


@pytest.mark.asyncio
async def test_search_and_describe_norm() -> None:
    async with BcnSparqlClient() as client:
        rows = await client.search("ley de transito", limit=2)
        assert len(rows) == 2

        norm = norm_from_search_row(rows[0])
        citation = build_citation(norm)
        assert citation.lex_uri.startswith("http://datos.bcn.cl/recurso/cl/")
        assert citation.human_readable_citation.startswith("Ley ")

        bindings = await client.describe(norm.uri)
        assert bindings
        props = group_describe(bindings)
        detail = norm_from_bindings(norm.uri, props)
        assert detail.title is not None
        assert detail.organism is not None
