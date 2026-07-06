# Discovery notes - Chile

Date: 2026-07-06.

## Why SPARQL instead of the documented REST web service

An earlier regional sweep flagged Chile's `legislacion_abierta_web_service`
as the most mature-looking source in the non-Brazil, non-US Latin America
set (a dedicated developer portal with RDF/OWL ontologies). Live probing on
2026-07-06 found the documented REST endpoint
(`leychile.cl/Consulta/legislacion_abierta_web_service`,
`bcn.cl/leychile/Consulta/legislacion_abierta_web_service`) returns HTTP 401
on every variant tried, from this network. Rather than guess at
undocumented auth, the developer portal itself (`datos.bcn.cl`) turned out
to expose a live, keyless SPARQL 1.1 endpoint over the same underlying data
(Virtuoso, `https://datos.bcn.cl/sparql`) - confirmed working and used here
instead.

## What's genuinely strong here

The `bcn-norms` ontology models norms as FRBR Work (`RootNorm`) /
Expression / Manifestation, and every root norm has a persistent,
dereferenceable resource URI encoding jurisdiction/type/issuing-body/date/
number - structurally the same idea as ELI, even though BCN does not use
that name. This is the strongest identifier scheme found in the Latin
America sweep outside Brazil's LexML URN Lex.

## Revisit later

- Confirm whether the legacy `legislacion_abierta_web_service` 401 is a
  genuine access restriction or geo/IP-based - if it turns out to be open
  from a different network, it may expose full operative text that the
  SPARQL endpoint does not.
- `NormInstance` (versioned/consolidated text) and cross-references
  (`modifiesTo`, `agreeWith`) exist in the ontology but are not exposed as
  tools yet - a natural v0.2.
