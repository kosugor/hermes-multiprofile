---
name: diagnose-and-fix
description: Reproduce a software defect, identify its cause and verify a focused
  fix.
---

# diagnose-and-fix

Capture expected versus observed behavior and the minimal failing input. Inspect logs and relevant code without printing credentials. Reproduce in the authorized offline workspace; if impossible, record exactly why and keep the diagnosis provisional.

Form a testable cause and distinguish it from correlated symptoms. Follow data/control flow to the failure. Change the smallest responsible behavior. Add a regression test when it would catch the real defect; avoid tests that merely assert the implementation's wording.

Run the reproducer before and after when feasible, plus the nearest affected checks. Separate environment failures from failed assertions. If the fix changes assumptions or data formats, make that explicit.

Use implement-project-change for final diff inspection and review handoff. Report cause, fix, reproduction evidence and remaining uncertainty. Do not expand a bug fix into an unrelated refactor.
