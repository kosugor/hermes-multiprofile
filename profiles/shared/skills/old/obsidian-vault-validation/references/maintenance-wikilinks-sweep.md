# Maintenance wikilink sweep notes

Session-derived workflow for cleaning an Obsidian wiki vault without overcorrecting legitimate references.

## Observed useful pattern

1. Run a vault-wide markdown scan.
2. Heuristically validate `[[wikilink]]` targets against:
   - relative vault paths
   - file stems
   - `title:` frontmatter values
3. Separate true content targets from expected noise:
   - Reddit/user handles
   - `deleted` placeholders
   - helper/glossary notes that intentionally explain link syntax
4. Prefer small compatibility redirects for legacy paths instead of mass-renaming existing content.

## Redirect/stub note pattern

When old links point to a historical path, create a tiny compatibility note at that path:

```md
---
title: "Legacy Title"
aliases:
  - "raw/old/path"
tags:
  - alias
  - redirect
---

# Alias / redirect

Ova kompatibilna stranica vodi na stvarnu belešku:

- [[Actual Note Name]]
```

This preserved existing links while keeping the note graph navigable.

## When to stop

If the remaining broken targets are mostly handles, deleted authors, or intentional external references, record that the residue is expected noise rather than forcing exhaustive cleanup.

## Examples from this session

Resolved legacy path aliases for:
- `raw/articles/licnefinansije-kako-poslati-novac-na-interactive-brokers-iz-srbije-2026-uputstvo`
- `raw/articles/licnefinansije-recenzija-brokera-interactive-brokers-2023`
- `raw/articles/licnefinansije-obveznice-su-kljuc-za-razumevanje-novca-2026`
- `raw/articles/local-html-investopedia-compound-interest`
- `raw/articles/local-html-investengine-s-p500-vs-all-world-etfs`
- `raw/articles/local-html-investopedia-etfs`
