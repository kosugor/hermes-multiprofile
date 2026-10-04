---
name: diagnose-and-fix
description: Reproduce a software defect, identify its cause and test a focused
  fix.
---

# diagnose-and-fix

## Language

Write internal English in ASD-STE100 style. Use short sentences, direct verbs,
and one term for one meaning in reports and Kanban messages. Use the operator's
language for user-facing replies.

Record the expected behavior, the observed behavior, and the smallest failing
input. Inspect logs and related code. Do not print credentials. Reproduce the
problem in the authorized offline workspace. If you cannot reproduce it, state
why. Mark the diagnosis as provisional.

State a cause that you can test. Separate the cause from related symptoms.
Trace data and control flow to the failure. Change only the behavior that
causes the failure. Add a regression test when it can catch the defect. Do not
add a test for implementation wording alone.

Run the reproducer before and after the fix when practical. Run the nearest
related tests. Separate environment failures from failed assertions. State
when the fix changes assumptions or data formats.

Use `implement-project-change` to inspect the final diff and hand off the work
for review. Report the cause, the fix, reproduction evidence, and unresolved
questions. Do not add unrelated changes to a bug fix.
