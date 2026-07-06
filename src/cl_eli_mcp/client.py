"""Async httpx client for the BCN Linked Open Data SPARQL endpoint (datos.bcn.cl/sparql).

Keyless, live Virtuoso SPARQL endpoint over Chilean legislation (748,783+ norm
instances per a 2026-07-06 live count). Full-text search uses Virtuoso's
``bif:contains`` extension over titles.
"""

from __future__ import annotations

import anyio
import httpx

from .cache import HttpCache

DEFAULT_BASE_URL = "https://datos.bcn.cl/sparql"
DEFAULT_TIMEOUT = httpx.Timeout(40.0, connect=10.0)
USER_AGENT = "cl-eli-mcp/0.1.0 (+https://github.com/matematicsolutions/cl-eli-mcp)"

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3

_PREFIXES = """\
PREFIX bcnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
"""

_SEARCH_QUERY = _PREFIXES + """\
SELECT ?s ?title ?number ?pdate WHERE {
  ?s a bcnorms:RootNorm ; dc:title ?title .
  ?title bif:contains "%s" .
  OPTIONAL { ?s bcnorms:hasNumber ?number }
  OPTIONAL { ?s bcnorms:promulgationDate ?pdate }
} LIMIT %d
"""

_DESCRIBE_QUERY = _PREFIXES + """\
SELECT ?p ?o WHERE { <%s> ?p ?o }
"""


class BcnSparqlClient:
    """Async client. Use as ``async with BcnSparqlClient() as c: ...``."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: HttpCache | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url
        self._cache = cache or HttpCache()
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
        )

    async def __aenter__(self) -> BcnSparqlClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    async def _query(self, sparql: str, *, category: str) -> list[dict]:
        cache_key = self.base_url + "?q=" + sparql
        cached = self._cache.get(cache_key)
        if cached is not None and isinstance(cached, list):
            return cached
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                params = {"query": sparql, "format": "json"}
                resp = await self._http.get(self.base_url, params=params)
                resp.raise_for_status()
                bindings = resp.json()["results"]["bindings"]
                self._cache.set(cache_key, bindings, ttl=HttpCache.ttl_for(category))
                return bindings
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
            await anyio.sleep(0.5 * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        # Virtuoso's bif:contains needs an explicit boolean expression for
        # multi-word phrases - a bare "word1 word2" string is a syntax error.
        words = [w.replace("'", "").replace('"', "") for w in query.split() if w]
        contains_expr = " AND ".join(f"'{w}'" for w in words) or f"'{query}'"
        sparql = _SEARCH_QUERY % (contains_expr, limit)
        return await self._query(sparql, category="search")

    async def describe(self, uri: str) -> list[dict]:
        sparql = _DESCRIBE_QUERY % uri
        return await self._query(sparql, category="act")
