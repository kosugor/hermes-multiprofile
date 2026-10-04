# Canonical wiki page schema

This lightweight contract applies to decision and procedure pages. Keep the
vault's existing taxonomy and frontmatter; add these fields where missing
without dropping established metadata.

## Required content

For files under `entities/`, `concepts/`, `comparisons/`, and `queries/`, the
vault validator enforces the structured subset below. A navigational page under
`hubs/` is YAML-checked and link-checked, but does not need a claim ledger.

- **Freshness frontmatter:** `last_reviewed` is an ISO date. `review_after` is
  either an ISO date or a positive interval such as `90 days`.
- **Source provenance frontmatter:** `sources` is a non-empty YAML list. Each
  item has an absolute HTTP(S) `url`, `published_at` (an ISO date or
  `unknown`), and `retrieved_at` (an ISO date). Add `provider` and `model` on a
  source record when they are relevant to how the evidence was produced.
- **Evidence ledger:** include a `## Evidence ledger` Markdown table with these
  columns in order: `Claim`, `Source / inspected passage`, `Published / updated`,
  `Retrieved`, `Scope / version`, `Status`, and `Affected / updated page`.
  Every non-header row needs a source URL or vault wikilink, publication date or
  `unknown`, retrieval date, scope, one status from the list below, and an
  affected page (use `this page` when appropriate). The validator checks the
  table structure and values; it cannot establish that a claim is true or that
  a cited passage supports it.

Example structured fields and ledger row:

```yaml
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
| The setting defaults to off | https://example.com/documentation, “Configuration” | unknown | 2026-10-02 | version 3 | verified | this page |
```

- **Question and definition:** state the question this page answers and define
  the central concept in plain terms.
- **Evidence ledger:** for each material claim record a source link and
  inspected passage, publication/update date or `unknown`, retrieval date,
  applicable conditions/version, status (`verified`, `author-claim`,
  `inference`, `unverified`, or `conflict`), and affected/updated canonical
  page. Keep a citation close to its claim.
- **Decision or procedure:** give a usable decision guide or ordered steps.
  State prerequisites and mark each procedure `tested` or `untested`, including
  where and against which version it was tested.
- **Scope and limits:** explain where the advice applies, limitations, known
  conflicts, and open questions.
- **Provenance and freshness:** retain canonical source URLs, publication and
  retrieval dates, source/provider/model where relevant, `last_reviewed`, and a
  `review_after` date or freshness interval.
- **Concept links:** link to a small number of existing related concept pages
  and update the owning topic hub/index when pages or key relationships change.

## Disposition and search

Canonical pages belong in the topic's existing `entities`, `concepts`,
`comparisons`, `queries`, or `hubs` taxonomy. Hubs summarize the topic map and
link to canonical pages; they are navigation pages, not duplicate article
summaries. Each topic wiki has a `hubs/index.md` entry point. Reuse it if it
exists; create it when absent and maintain its links when canonical pages are
added, moved, or materially changed.

Keep permanent `shell`/`failed` captures under
`evidence-only/failed-sources/`, with original bytes, source URL, failure reason,
retrieval time, and the evidence that makes the failure terminal. Do not delete
them or send them through routine triage. `partial` captures remain deferred
until new evidence changes their disposition.

Normal QMD search uses canonical pages. Raw captures and evidence-only files
are in an opt-in `wiki-evidence` collection; query it only when the task asks
for source evidence or a citation needs rechecking.

## Pilot and golden queries

Before broad migration, review these pages against the schema:

- `local-llm-capacity-planning`
- `tailscale-remote-local-model-access`
- `model-api-pricing-and-capability-claims`

After the pilot, run and record a small golden-query set that tests decisions,
not article recall. Start with: (1) "How much RAM/VRAM do I need for this local
model?" (2) "How do I securely reach a local model over Tailscale?" and (3)
"Which model API fits this task and budget, and which pricing/capability claims
are verified?" Confirm default results point to canonical pages; repeat one
query with `wiki-evidence` explicitly selected and verify raw sources appear
only in that opt-in result set.
