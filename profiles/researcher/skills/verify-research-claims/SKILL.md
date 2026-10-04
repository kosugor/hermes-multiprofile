---
name: verify-research-claims
description: Assess factual claims, version compatibility, and citations before a research
  handoff.
---

# verify-research-claims

## Language

Write internal English in ASD-STE100 style. Use this style for claim ledgers,
reports, and Kanban messages. Keep source quotations in their original language.
Use the operator's language for user-facing replies.

List claims that affect the recommendation. Inspect numbers, prices, dates,
configuration keys, and compatibility first. Name a source that you read for
each claim. Give its supporting passage or code location. Remove unsupported
precision.

Inspect each URL. Ensure that it opens the cited document. Ensure that the cited
version applies. Ensure that the source states the attributed claim. A search
result or another AI answer is not proof. Trace secondary reports to original
sources when practical.

Ensure that code snippets have valid structure and required setup or
authentication.
State if you ran, inspected, or only proposed each snippet. A valid config file
does not prove that the application supports it.

Return a claim ledger with these columns: claim, source and passage,
publication or update date, retrieval date, conditions and version, evidence
status, and affected canonical page. Use `verified`, `author-claim`,
`inference`, `unverified`, or `conflict`. State what changed, where it applies,
and how sources differ. Keep useful negative results. Do not treat an
inaccessible page as proof. If available evidence does not resolve a key claim,
qualify the result and name the next step.

For important claims about models, prices, hardware, or security, use primary
documents, original papers, advisories, or executed tests. Attribute blog
reports to their authors. List prerequisites. State if you tested, inspected,
or did not inspect each procedure.
