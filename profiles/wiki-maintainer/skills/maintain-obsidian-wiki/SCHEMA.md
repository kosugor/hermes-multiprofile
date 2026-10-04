# Canonical wiki page schema

Write curated page prose in Serbian. This includes titles, headings, claims,
procedures, limits, and open questions. Keep quotations in their source
language. Keep frontmatter keys, field values required by validators, and the
required `Evidence ledger` heading and table columns unchanged.

Use this contract for decision and procedure pages. Keep the vault's taxonomy
and frontmatter. Add missing fields. Keep all current metadata.

## Required content

The vault validator checks files under `entities/`, `concepts/`,
`comparisons/`, and `queries/` against the schema below. It checks YAML and
links on pages under `hubs/`. Hubs do not need a claim ledger.

- **Freshness:** Set `last_reviewed` to an ISO date. Set `review_after` to an
  ISO date or positive interval, such as `90 days`.
- **Sources:** Set `sources` to a non-empty YAML list. Give each source an
  absolute HTTP(S) `url`, `published_at` date or `unknown`, and ISO
  `retrieved_at` date. Add `provider` and `model` when they explain how you got
  the evidence.
- **Evidence ledger:** Add a `## Evidence ledger` table. Use these columns in
  this order: `Claim`, `Source / inspected passage`, `Published / updated`,
  `Retrieved`, `Scope / version`, `Status`, and `Affected / updated page`.
  Give every data row a source URL or wiki link. Include its publication date
  or `unknown`, retrieval date, scope, status, and affected page. Use `this page`
  when needed.
  The validator checks the table structure and values. It cannot prove a claim
  or check that a source supports it.

Example structured fields and ledger row:

```yaml
title: "Naziv kanonske stranice"
last_reviewed: 2026-10-02
review_after: 90 days
sources:
  - url: https://example.com/documentation
    published_at: unknown
    retrieved_at: 2026-10-02
```

```markdown
## Evidence ledger

| Claim | Source / inspected passage | Published / updated | Retrieved | Scope / version | Status | Affected / updated page |
| --- | --- | --- | --- | --- | --- | --- |
| Podešavanje je podrazumevano isključeno | https://example.com/documentation, “Configuration” | unknown | 2026-10-02 | version 3 | verified | this page |
```

- **Question and definition:** State the page's question. Define the main
  concept in plain terms.
- **Evidence ledger:** Add a source and inspected passage for each material
  claim. Record publication or update date, retrieval date, conditions, version,
  status, and affected page. Use `verified`, `author-claim`, `inference`,
  `unverified`, or `conflict` as the status. Put each citation near its claim.
- **Decision or procedure:** Give a useful decision guide or ordered steps.
  List prerequisites. Mark each procedure `tested` or `untested`. If tested,
  state where and which version you tested.
- **Scope and limits:** State where the advice applies. List limits, known
  conflicts, and open questions.
- **Sources and freshness:** Keep canonical source URLs, publication and
  retrieval dates, and source, provider, or model details when relevant. Set
  `last_reviewed` and `review_after`.
- **Concept links:** Link to a few related concept pages. Update the topic hub
  when a page or key relationship changes.

## Disposition and search

Put canonical pages in the topic's `entities`, `concepts`, `comparisons`,
`queries`, or `hubs` folders. Hubs show the topic map and link to canonical
pages. Do not use them for article summaries. Each topic wiki has a
`hubs/index.md` entry point. Reuse it when it exists. If you add, move, or
change a canonical page, update the hub links.

Keep terminal `shell` and `failed` captures under
`evidence-only/failed-sources/`. Keep the original bytes, source URL, failure
reason, retrieval time, and evidence for the final disposition. Do not delete
these files or send them through routine triage. Defer `partial` captures until
new evidence changes their status.

Normal QMD search uses canonical pages. Raw captures and evidence-only files
are in the optional `wiki-evidence` collection. Search it only when a task asks
for source evidence or you must check a citation.

## Pilot and golden queries

Before a broad migration, check these pages against the schema:

- `local-llm-capacity-planning`
- `tailscale-remote-local-model-access`
- `model-api-pricing-and-capability-claims`

After the pilot, run and record queries that test decisions, not article recall.
Start with these questions:

1. How much RAM or VRAM does this local model need?
2. How can I reach a local model through Tailscale securely?
3. Which model API fits this task and budget? Which price and capability claims
   have evidence?

Check that default results point to canonical pages. Select `wiki-evidence`
for one query. Check that only this query returns raw sources.
