"""Plain dataclasses mirroring the BCN bcn-norms ontology (SPARQL query results)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Norm:
    uri: str
    norm_type: str
    number: str | None
    title: str | None
    organism: str | None
    promulgation_date: str | None
    publish_date: str | None
    leychile_code: str | None


@dataclass(frozen=True)
class Citation:
    lex_uri: str
    human_readable_citation: str
    source_url: str
