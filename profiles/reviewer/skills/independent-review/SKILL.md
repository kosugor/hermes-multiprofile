---
name: independent-review
description: Independent read-mostly review workflow for code and technical deliverables, with severity-ranked findings and test evidence.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [review, code-review, verification, quality]
    category: software-development
    requires_toolsets: [file]
---

# Independent Review

## Language

Write internal English in ASD-STE100 style. Use this style for findings and
Kanban messages. Keep source quotations in their original language. Use the
operator's language for user-facing replies.

## Procedure

1. Read the task requirement and acceptance criteria.
2. Read the exact submitted artifact from this review worker's own accessible
   workspace or durable attachment. Record its path and revision/hash before
   proceeding. If it cannot be opened/read or does not match the handoff, stop
   with `review-access-blocked`; attachment support described in product docs
   does not establish attachment delivery/access in this run.
3. Confirm this is the original implementation card, identify the named
   implementer, and inspect that revision's diff or changed files.
4. Inspect surrounding code only as needed to understand behavior.
5. Check:
   - correctness and edge cases;
   - error handling and failure modes;
   - security boundaries and secret handling;
   - concurrency/state issues;
   - backward compatibility;
   - API/schema compatibility;
   - tests and negative cases;
   - performance only where material.
6. Run relevant tests/checks without changing source files.
7. Compare claimed verification with what was actually executed.
8. Report findings by severity:
   - BLOCKER: unsafe or fundamentally incorrect;
   - HIGH: likely user-visible failure, data loss, security, major regression;
   - MEDIUM: meaningful defect or maintainability risk;
   - LOW: limited impact.
9. If no material defect is found, state what was checked and what remains
   unverified.

## Independence Rules

- Do not patch the code.
- Do not turn review into refactoring.
- Do not waive a finding because the implementation is otherwise good.
- Do not require stylistic changes that are unsupported by repo conventions.
- When external documentation is required to decide a finding, flag the exact
  research question for the researcher profile.

## Output

Return:
- verdict: approve / approve-with-notes / changes-required;
- findings with severity and evidence;
- tests/checks run and outcomes;
- unverified areas;
- concise recommended next action.
