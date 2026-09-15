---
name: manage-web-watchlist
description: Maintain a file-based source list and discover selectable documentation page trees.
---

# manage-web-watchlist

Use `/monitor/watchlist.json` as the only watch registry. If it is absent, copy the supplied `watchlist.example.json` from this profile pack only when the user asks to initialize monitoring. Never replace a populated watchlist with the example.

Before editing, parse the JSON and validate `version`, unique source IDs, supported source types, absolute HTTP(S) URLs, and unique page URLs within each site. Preserve unknown fields. Read the file again immediately before replacement; if it changed, stop and report a conflict. Write through a temporary file followed by an atomic rename, and retain `/monitor/backups/watchlist-<UTC timestamp>.json` before a material edit.

For a site tree:

1. Start with declared sitemap URLs, then same-origin sitemap links and explicitly requested entry pages.
2. Discover only canonical same-origin HTTP(S) pages. Remove fragments; normally discard tracking query parameters and non-HTML assets. Obey the configured `max_pages` and report truncation.
3. Build `pages` as nested nodes with `title`, `url`, `watch`, and optional `children`. Group by URL path segments so the JSON renders as a readable tree.
4. Preserve the existing `watch` value for known canonical URLs. Set every newly discovered page to `false`; discovery is not authorization to monitor it.
5. Show a compact proposed tree/diff. Apply selections the user explicitly gives by URL or unambiguous tree path. Never guess between duplicate titles.

For blogs, feeds, Reddit and X, store only public source definitions and filters. Do not store credentials, cookies or access tokens in the watchlist. Prefer a canonical RSS/Atom feed for a blog. Reddit entries may specify subreddits, public feed URLs and search terms. X entries may specify public accounts, queries, optional public feed bridges, and a `coverage_note`; explain that search/browser-only coverage can be incomplete.

After editing, parse the new file again and report the exact source/page selections changed. Do not run a full monitor tick unless requested.
