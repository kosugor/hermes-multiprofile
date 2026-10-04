---
name: independent-review
description: Review code and technical work. Rank findings by severity and cite test evidence.
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
2. Read the exact artifact from this worker's workspace or an accessible
   attachment. Record its path and revision or hash. If the artifact is missing
   or does not match the handoff, stop. Return `review-access-blocked`. Product
   docs do not prove that this run received the attachment.
3. Confirm this is the original implementation card, identify the named
   implementer, and inspect that revision's diff or changed files.
4. Read related code only when you need it to understand behavior.
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
7. Compare the reported checks with the checks that ran.
8. Report findings by severity:
   - BLOCKER: unsafe or fundamentally incorrect;
   - HIGH: likely visible failure, data loss, security risk, or major regression;
   - MEDIUM: meaningful defect or maintainability risk;
   - LOW: limited impact.
9. If you find no material defect, state what you checked and what you did not
   verify.

## Independence Rules

- Do not patch the code.
- Do not turn review into refactoring.
- Do not waive a finding because the implementation is otherwise good.
- Do not require stylistic changes that are unsupported by repo conventions.
- If you need external documentation, give Researcher the exact question.

## Output

Return these items:
- verdict: approve / approve-with-notes / changes-required;
- findings with severity and evidence;
- tests/checks run and outcomes;
- unverified areas;
- concise recommended next action.
