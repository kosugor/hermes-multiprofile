---
name: run-web-monitor
description: Check sources by schedule or request. Report only new or material changes.
---

# run-web-monitor

## Language

Write internal English in ASD-STE100 style for reports and profile-to-profile
messages. Keep source quotations in their original language. Use the operator's
language for user-facing replies.

Read `/workspace/monitoring/watchlist.json` and the source records under
`/workspace/monitoring/state/`. Check enabled sources only. For site pages,
check pages marked `watch: true`. Record the UTC start time and the current
watchlist fingerprint. If a prior run is active, skip this run.

Choose the most reliable retrieval path:

- `feed` or `blog`: Use the canonical RSS or Atom feed when available.
  Otherwise, extract the listed page. Identify entries by GUID or canonical URL.
  Use publication time as a second key.
- `reddit`: Prefer configured public RSS endpoints. If none exist, use SearXNG
  and extract only the public threads needed for the report. Do not vote,
  comment, or log in.
- `x`: Use the configured public feed bridge first. Otherwise, use SearXNG and
  the enabled browser for public accounts or queries. Without an official API,
  coverage can be incomplete. Record login walls, rate limits, and index delay.
- `page` or watched `site` page: Extract page content. Remove navigation,
  footers, cookie text, generated times, and extra spaces before comparison.
  Use the browser only when the rendered page lacks important content.

For each result, record the source ID, canonical URL, title, release or advisory
ID, publication time, discovery time, fingerprint, and evidence summary. Use
`unknown` when a date is not available. Classify each run as `baseline`,
`no-change`, `material-change`, or `fetch-failed`.

On the first successful check, create a baseline. Do not report old content as
new unless the prompt asks for catch-up. On later checks, remove duplicates by
ID and canonical URL. Treat a hash change as a candidate only. Report a change
when meaning, instructions, version, API behavior, availability, or configured
materiality changes. On fetch or parse failure, keep the last good snapshot
and cursor. Record the failure separately.

Write a Markdown report to
`/workspace/monitoring/reports/YYYY-MM-DDTHHMMSSZ.md`. Include the interval,
highlights, new posts or articles, document changes with before and after
evidence, source coverage, failures, and links. Keep an empty successful report
short. Do not claim full X or Reddit coverage when access was partial.

Update state only for sources that passed their checks. Keep the old cursor and
fingerprint for failed or unclear checks. This lets the next run retry them.
Write state to a temporary file. Then replace the old file with an atomic
rename. Before you commit, read the watchlist fingerprint again. If it changed,
keep the evidence in the report. Do not update affected state until the next
run.

Return the digest and report path. Send material evidence to Researcher or
Reviewer for triage. Do not edit the wiki. Keep a paused monitor paused after
each run. For a scheduled run, use the job's delivery target. Do not send a
second message or change cron jobs.
