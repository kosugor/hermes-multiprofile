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

## Language

Write internal English in ASD-STE100 style. Use this style for memory, comments,
reports, and Kanban messages. Use the operator's language for user-facing
replies.

## Procedure

1. Read project context from `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and related
   docs.
2. Inspect affected code and tests before you propose a change.
3. Define the smallest change that meets the requirement.
4. For a behavior change, add or update focused tests when practical.
5. Implement incrementally.
6. Run the smallest relevant tests first. Run wider checks when needed.
7. Diagnose failures from local evidence. Ask Researcher to answer external
   dependency or API questions. This profile has no web access.
8. Before you report completion:
   - inspect `git diff`;
   - confirm that no unrelated files changed;
   - run relevant format, lint, and type checks;
   - run tests;
   - report commands and results.
9. Hand off the diff and verification evidence for independent review.

## Git Rules

- Never force-push unless the task requires it.
- Never rewrite unrelated history.
- Do not commit secrets or local credential files.
- Do not remove user changes just to make the diff clean.
- Preserve unexpected workspace changes. Work around them. Do not reset the
  workspace without a clear reason.

## Verification

For artifact and capture checks, verify the parsed frontmatter. Recompute the
hash from the saved body bytes. Check the assigned workspace root. Separate
corruption from valid deferred, no-change, or blocked-source results. When you
change this contract, check invalid YAML, a stale body hash, a valid display
alias, a wrong root, and a valid deferred input.

A handoff must state:
- files changed;
- behavior change;
- tests/checks executed;
- failures or skipped checks;
- remaining risks or next steps.
