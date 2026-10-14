# Regulated / financial research notes

Use this pattern when turning public financial-fund research into an Obsidian note.

## Reliable source hierarchy
- Prefer regulator publications, fund prospectuses, and official fund-manager pages.
- Use aggregators or media pages only to cross-check or fill gaps.
- When the source is a snapshot in time, state the snapshot date in the note title or subtitle.

## Table design
- Split complex fund research into multiple tables when needed:
  - **main facts table**: founding date / license date, currency, UCITS, open/closed, type, objective, policy
  - **fees table**: entry fee, exit fee, management fee, depositary fee
  - **ranking table**: assets / NAV snapshot and rank date
- Prefer `n/a` over guessing missing fields.
- Keep notes compact and directly comparable across funds.

## Extraction quirks encountered
- Official fund pages often expose the useful text in visible HTML rather than a clean API.
- WordPress-backed fund sites may expose useful metadata through `/wp-json/wp/v2/pages?slug=...` even when the visible page is hard to parse.
- The page body may contain the legal / prospectus text in a single long stream, so extracting by section label is often easier than relying on tables.
- Public pages can show date-of-page or date-of-post metadata that is not the same as the legal license date; do not silently substitute one for the other.

## Reporting discipline
- If a field is only partially verified, say so in the note rather than smoothing it over.
- For company pages, capture the exact fee wording in the fees table where possible.
- For regulator-based rankings, keep the ranking date and currency basis visible so later comparisons are reproducible.
