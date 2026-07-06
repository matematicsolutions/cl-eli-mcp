"""Citation contract for cl-eli-mcp.

BCN's Linked Open Data resource URIs (e.g.
``http://datos.bcn.cl/recurso/cl/ley/ministerio-de-justicia/1984-02-07/18290``)
are already a native, dereferenceable persistent identifier - not called ELI,
but structurally the same idea (jurisdiction/type/issuing-body/date/number).
We use it directly rather than inventing anything.
"""

from __future__ import annotations

from typing import Any

from .models import Citation, Norm

_TYPE_LABELS = {
    "ley": "Ley",
    "dto": "Decreto",
    "dfl": "Decreto con Fuerza de Ley",
    "dl": "Decreto Ley",
    "res": "Resolucion",
    "auto": "Auto Acordado",
    "cir": "Circular",
}


def _extract_type(uri: str) -> str:
    parts = uri.split("/recurso/cl/", 1)
    if len(parts) != 2:
        return "norma"
    return parts[1].split("/", 1)[0]


def group_describe(bindings: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Group SPARQL DESCRIBE-style (?p ?o) bindings by predicate local name."""
    grouped: dict[str, list[str]] = {}
    for row in bindings:
        pred = row["p"]["value"]
        local = pred.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        grouped.setdefault(local, []).append(row["o"]["value"])
    return grouped


def norm_from_search_row(row: dict[str, Any]) -> Norm:
    uri = row["s"]["value"]
    return Norm(
        uri=uri,
        norm_type=_extract_type(uri),
        number=row.get("number", {}).get("value"),
        title=row.get("title", {}).get("value"),
        organism=None,
        promulgation_date=row.get("pdate", {}).get("value"),
        publish_date=None,
        leychile_code=None,
    )


def norm_from_bindings(uri: str, props: dict[str, list[str]]) -> Norm:
    return Norm(
        uri=uri,
        norm_type=_extract_type(uri),
        number=(props.get("hasNumber") or [None])[0],
        title=(props.get("title") or props.get("label") or [None])[0],
        organism=(props.get("createdBy") or [None])[0],
        promulgation_date=(props.get("promulgationDate") or [None])[0],
        publish_date=(props.get("publishDate") or [None])[0],
        leychile_code=(props.get("leychileCode") or [None])[0],
    )


def build_citation(n: Any) -> Citation:
    label = _TYPE_LABELS.get(n.norm_type, n.norm_type.capitalize())
    number = n.number or "?"
    date = n.promulgation_date or n.publish_date or ""
    human = f"{label} {number}" + (f", de {date}" if date else "")
    return Citation(lex_uri=n.uri, human_readable_citation=human, source_url=n.uri)
