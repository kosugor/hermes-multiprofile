---
name: verify-research-claims
description: Check factual claims, version compatibility and citations before a research
  handoff.
---

# verify-research-claims

List claims that determine the recommendation, especially numbers, prices, dates, configuration keys and compatibility. For each, identify an actually read source and the relevant supporting passage or code location. Remove unsupported precision.

Check that URLs resolve to the claimed document, the cited version applies, and a source explicitly states what you attribute to it. A search result or another AI answer is not sufficient verification. Trace secondary reports to originals where practical.

Inspect code snippets for valid structure and for installation/authentication prerequisites. Say whether they were executed, statically inspected or simply proposed. A parsable config does not prove the installed application supports it.

Return a claim ledger with columns for claim, source/passage, publication or
update date, retrieval date, applicable conditions/version, evidence status,
and affected canonical page. Use `verified`, `author-claim`, `inference`,
`unverified`, or `conflict`. Then synthesize what changed, where it applies,
and how sources differ. Preserve useful negative results without treating
inaccessible pages as proof of absence. When a decisive claim remains
unresolved, qualify the conclusion and specify the narrow follow-up needed.

For material model, pricing, hardware, and security claims, trace to primary
documentation, original papers/advisories, or executed tests. Keep blog
experience attributed. State prerequisites and whether any proposed procedure
was tested, statically inspected, or not checked.
