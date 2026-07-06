# cl-eli-mcp

MCP server for Chilean legislation via the BCN (Biblioteca del Congreso
Nacional de Chile) Linked Open Data SPARQL endpoint. Searches and fetches
laws, decrees, and resolutions by their persistent resource URI.

## What this is not

BCN's resource URIs are not formally called ELI, but they carry the same
idea: jurisdiction, type, issuing body, date, number, all in one
dereferenceable URI. This connector returns metadata (title, number, dates,
issuing body) - not the operative text of the law. Following `source_url`
(the same URI, content-negotiated) takes you to the human-readable page.

## Tools

| Tool | Purpose |
|---|---|
| `cl_search_norms` | Full-text search over norm titles |
| `cl_get_norm` | Full detail for one norm by its BCN resource URI |

Every response carries `lex_uri` and `source_url` (both the BCN resource
URI) and `human_readable_citation` (e.g. `"Ley 18290, de 1984-01-23"`).

## Install

```bash
pip install cl-eli-mcp
```

## Configuration

| Env var | Default |
|---|---|
| `CL_ELI_CACHE_DIR` | `~/.matematic/cache/cl-eli` |
| `CL_ELI_AUDIT_DIR` | `~/.matematic/audit` |
| `CL_ELI_BASE_URL` | `https://datos.bcn.cl/sparql` |

## License

Apache-2.0 (code). BCN Linked Open Data is a public government dataset (see
[SOURCES.md](SOURCES.md)).
