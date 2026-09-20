---
name: coding-workflow
description: Conservative implementation workflow for the coder profile: inspect, plan, edit minimally, test, and hand off evidence for independent review.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [coding, implementation, testing, git]
    category: software-development
    requires_toolsets: [file, terminal]
---

# Coding Workflow

## Procedure

1. Read project context (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, relevant docs).
2. Inspect the affected code and tests before proposing a change.
3. Define the smallest change that satisfies the requirement.
4. For behavioral changes, write or update focused tests when practical.
5. Implement incrementally.
6. Run the narrowest relevant tests first, then broader checks when warranted.
7. Diagnose failures from local evidence; route unresolved external dependency
   or API questions to Researcher because this profile has no web access.
9. Before declaring completion:
   - inspect `git diff`;
   - confirm no unrelated files changed;
   - run formatting/lint/type checks relevant to the repo;
   - run tests;
   - report commands and results.
10. Hand off the diff and verification evidence for independent review.

## Git Rules

- Never force-push unless the task explicitly requires it.
- Never rewrite unrelated history.
- Do not commit secrets or local credential files.
- Do not remove user changes just to make the diff clean.
- If the workspace contains unexpected changes, preserve them and work around
  them rather than resetting blindly.

## Verification

A completion handoff must state:
- files changed;
- behavior changed;
- tests/checks executed;
- failures or skipped checks;
- remaining risks or follow-ups.
