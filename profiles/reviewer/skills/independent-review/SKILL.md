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

## Procedure

1. Read the task requirement and acceptance criteria.
2. Inspect the submitted diff or changed files.
3. Inspect surrounding code only as needed to understand behavior.
4. Check:
   - correctness and edge cases;
   - error handling and failure modes;
   - security boundaries and secret handling;
   - concurrency/state issues;
   - backward compatibility;
   - API/schema compatibility;
   - tests and negative cases;
   - performance only where material.
5. Run relevant tests/checks without changing source files.
6. Compare claimed verification with what was actually executed.
7. Report findings by severity:
   - BLOCKER: unsafe or fundamentally incorrect;
   - HIGH: likely user-visible failure, data loss, security, major regression;
   - MEDIUM: meaningful defect or maintainability risk;
   - LOW: limited impact.
8. If no material defect is found, state what was checked and what remains
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
