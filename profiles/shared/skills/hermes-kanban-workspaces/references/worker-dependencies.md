# Worker dependency verification

Use this recipe when a subprocess fails on a Python import before claiming its job.

1. Retrieve the full redacted traceback with the owning profile's `hermes --profile <name> cron runs <job-id> --limit 5`. Distinguish failure during package import from failure after job execution; do not infer later writes from an earlier successful run's checkpoint.
2. Read the installed launcher, subprocess argv construction, and bootstrap/import ordering. Compare the interpreter and activated dependency paths, not only the interpreter filename. Managed Hermes installations can use a store Python whose default site-packages do not contain the generation's dependencies.
3. Check the declaration of the dependency and its import after the supported Hermes bootstrap. If bare Python fails but the bootstrapped process succeeds, classify this as dependency activation/path visibility rather than an absent installation. Do not prescribe a global pip install from a bare interpreter failure.
4. Build a safe red/green probe in fresh subprocesses: use the same interpreter; remove inherited PYTHONPATH, PYTHONHOME, and worker markers; first expose only the checkout and attempt the import, then use the current worker environment builder and bootstrap marker and repeat it. Inspect installed helper names before invoking them. In the inspected implementation these seams are `cron.scheduler_worker_env.pin_hermes_tree_on_pythonpath` and `cron.worker_bootstrap.WORKER_MARKER`.
5. Have the child import `cron.scheduler` and the dependency and print its version, resolved module path, and exit status. Do not invoke the scheduler module's main entry for an import-only check: `python -m cron.scheduler` without worker arguments can execute a real scheduler tick.
6. Report the proof boundary accurately: a successful fresh worker-style import verifies dependency initialization, not provider authentication, vault access, ownership acknowledgement, or end-to-end triage. Read actual execution history before claiming the production job recovered.
7. Transfer the traceback and probe output into worker-readable task context before requeueing. Keep host diagnostics outside the narrow repository mount instead of exposing the entire Hermes home to the worker.

Preserve valid generation activation and leases; inherited site-packages alone need not provide the same lifetime guarantees as the supported bootstrap. Treat exact paths, helper names, and installed versions as discovered state, not permanent assumptions.
