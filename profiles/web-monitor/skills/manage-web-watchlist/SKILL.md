---
name: manage-web-watchlist
description: Maintain a source list and find documentation pages for review.
---

# manage-web-watchlist

## Language

Write internal English in ASD-STE100 style for monitoring records, reports, and
profile-to-profile messages. Use the operator's language for user-facing
replies.

Use `/workspace/monitoring/watchlist.json` as the only watchlist. If it does not
exist, copy `watchlist.example.json` from this profile pack only when the user
asks to start monitoring. Never replace a populated watchlist with the sample.

Before you edit, parse the JSON. Check `version`, unique source IDs, source
types, absolute HTTP(S) URLs, and unique page URLs within each site. Preserve
unknown fields. Read the file again before replacement. If it changed, stop
and report a conflict. Write to a temporary file. Replace the old file with an
atomic rename. Before a material edit, save a copy to
`/workspace/monitoring/backups/watchlist-<UTC timestamp>.json`.

For a site tree:

1. Start with the listed sitemap URLs, same-origin sitemap links, and requested
   entry pages.
2. Find canonical same-origin HTTP(S) pages only. Remove URL fragments.
   Normally remove tracking query parameters and non-HTML files. Obey
   `max_pages`. Report when the limit cuts off results.
3. Build `pages` as nested nodes. Use `title`, `url`, `watch`, and optional
   `children` fields. Group nodes by URL path so JSON shows a clear tree.
4. Keep the current `watch` value for known canonical URLs. Set `watch` to
   `false` for each new page. Discovery does not authorize monitoring.
5. Show a short proposed tree or diff. Apply only URL or tree-path selections
   that the user gives. Do not guess when titles are the same.

For blogs, feeds, Reddit, and X, store public source details and filters only.
Do not store credentials, cookies, or access tokens. Prefer a canonical RSS or
Atom feed for a blog. A Reddit entry can list subreddits, public feed URLs, and
search terms. An X entry can list public accounts, queries, public feed
bridges, and a `coverage_note`. Explain that search and browser results can be
incomplete.

After you edit, parse the new file. Report each changed source or page
selection. Do not run a full monitor check unless the user asks.
