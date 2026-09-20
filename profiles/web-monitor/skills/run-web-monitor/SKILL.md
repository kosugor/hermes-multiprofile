---
name: run-web-monitor
description: Run a stateful manual or scheduled check and summarize only new or material changes.
---

# run-web-monitor

Read `/workspace/monitoring/watchlist.json` and the per-source records under `/workspace/monitoring/state/`. Check only enabled sources and site pages marked `watch: true`. Record the UTC start time and the current watchlist content fingerprint. If a previous run is still active, skip rather than overlap it.

Choose the least brittle retrieval path:

- `feed` or `blog`: use the canonical RSS/Atom feed when configured; otherwise extract the declared page. Identify entries by stable GUID or canonical URL, then publication time.
- `reddit`: prefer configured public subreddit/search RSS endpoints; fall back to SearXNG discovery and extract only the public thread pages needed for the digest. Do not vote, comment or log in.
- `x`: use a configured public feed bridge first, then SearXNG and the enabled browser for public accounts/queries. Coverage is best-effort without an official API. Record login walls, rate limits and indexing lag.
- `page` or watched `site` page: extract substantive page content. Normalize navigation, footers, cookie text, generated timestamps and whitespace before comparison. Use the browser only for materially incomplete rendered pages.

For every observation retain source ID, canonical URL, title, published time if present, discovered time, normalized fingerprint, and a short evidence summary. On the first successful check, create a baseline and do not call existing content new unless the prompt explicitly requests catch-up. On later checks, deduplicate against stable IDs and canonical URLs. A hash change is a candidate: report a page change only when substantive meaning, instructions, version, API behavior, availability, or another configured materiality rule changed.

Write a Markdown report under `/workspace/monitoring/reports/YYYY-MM-DDTHHMMSSZ.md` containing: interval, concise highlights, new posts/articles, documentation changes with before/after evidence, per-source coverage, failures, and links. Keep empty successful runs short. Never fabricate a complete X/Reddit result when access was partial.

Update only state for sources checked successfully. Preserve the previous cursor/fingerprint for failed or ambiguous checks so content is retried later. Write new state through a temporary file and atomic rename. Re-read the watchlist fingerprint before committing; if the watchlist changed, keep fetched evidence in the report but do not advance affected state until the next run.

Return the digest plus the report path. For scheduled execution, rely on the job's configured delivery target; do not send separately and do not alter cron jobs.
