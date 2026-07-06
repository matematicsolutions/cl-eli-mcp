# Sources

## BCN Linked Open Data (`datos.bcn.cl`)

- **Origin**: Biblioteca del Congreso Nacional de Chile.
- **License**: public government open data.
- **Access**: keyless SPARQL 1.1 (Virtuoso), JSON results, `bif:contains` full-text extension.
- **Ontology**: `http://datos.bcn.cl/ontologies/bcn-norms#` (Norm / RootNorm /
  NormInstance, FRBR Work/Expression/Manifestation model). Confirmed live
  2026-07-06: 748,783 `Norm` instances, 359,720 `RootNorm` (top-level laws/
  decrees/resolutions).
- **Identifier**: the resource URI itself, e.g.
  `http://datos.bcn.cl/recurso/cl/ley/ministerio-de-justicia/1984-02-07/18290`
  - jurisdiction/type/issuing-body/date/number, dereferenceable (redirects to
    a human-readable page). Not formally ELI, but the same idea.
- **Coverage**: this connector only queries `RootNorm` title/number/
  promulgationDate via SPARQL. It does not cover `NormInstance` (versioned
  text), `VotoProyectoDeLey` (bill votes), `EjecucionPresupuesto` (budget
  execution), or any of the other classes in this same triple store.

## Not covered (out of scope for this connector)

- **Legacy `legislacion_abierta_web_service`** (leychile.cl/bcn.cl) - the
  older REST-style web service returned HTTP 401 on every probe from this
  network on 2026-07-06 (possibly geo/IP-restricted or deprecated in favor
  of the SPARQL endpoint). Not used here.
- **Full operative text of a law** - the SPARQL endpoint exposes metadata,
  not article-level text. `leychileCode` (present on some norms) is the
  numeric ID used by the legacy web viewer, kept here for reference only -
  not resolved into a URL, since the legacy domain was unreachable during
  discovery.
