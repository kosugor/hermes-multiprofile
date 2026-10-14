# Legacy alias / redirect notes

Use this pattern when a vault contains many backlinks to a deprecated internal path.

## When to use
- A large cluster of broken links points to the same old path.
- The old path is a stable legacy identifier rather than a one-off typo.
- You want to preserve existing backlinks and avoid mass rewrites.

## Recommended alias note shape

```md
---
title: "Canonical note title"
aliases:
  - "raw/articles/old-legacy-path"
tags:
  - alias
  - redirect
---

# Alias / redirect

Ova kompatibilna stranica vodi na stvarnu belešku:

- [[Canonical note title]]
```

## Audit checklist
1. Count broken links before the change.
2. Create one alias note per legacy path.
3. Read back the alias note to ensure the wikilink targets the canonical title exactly.
4. Re-scan links and compare before/after counts.
5. Leave usernames, handles, and external references alone unless there is a real note target to map them to.

## Notes
- Keep the alias page minimal.
- Use the same language as the surrounding vault content.
- Prefer one redirect note per legacy path when the path is used widely across the wiki.
