---
name: deep-web-research
description: Default evidence-first workflow for deep web research using SearXNG search, Firecrawl extraction, and the built-in browser only as a fallback.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [research, web, searxng, firecrawl, camofox, citations]
    category: research
    requires_toolsets: [web]
---

# Deep Web Research

## When to Use

Use this as the default workflow for open-ended web research, current technical
questions, product/project comparisons, documentation investigation, or any task
where multiple sources should be reconciled.

## Procedure

1. Restate the research question internally as concrete subquestions.
2. Search with SearXNG using several targeted queries rather than one giant query.
3. Prefer primary sources:
   - official documentation and repositories;
   - standards bodies and specifications;
   - vendor release notes;
   - original research papers;
   - authoritative public records.
4. Use `web_extract` through Firecrawl on promising URLs.
5. Only use the built-in browser when extraction fails or the page requires
   JavaScript, interaction, authentication, or anti-bot handling.
6. Cross-check material claims with a second independent source when practical.
7. Track freshness. For changing software, prices, policies, model names, or
   service limits, favor sources with explicit current dates.
8. Separate:
   - confirmed fact;
   - inference;
   - recommendation;
   - uncertainty/conflict.
9. Return a concise synthesis plus the source URLs that support each important
   conclusion.

## Source Quality Rules

- Documentation beats blogs for product behavior.
- Source repositories/release notes beat secondary summaries for software.
- A search-result snippet is discovery evidence, not final evidence.
- Do not cite a page you did not actually inspect when its contents matter.
- Do not over-weight SEO pages, scraped copies, or AI-generated summaries.

## Browser Escalation

Firecrawl first. Built-in browser second.

Escalate to the built-in browser only when one of these is true:
- extracted content is incomplete or empty;
- navigation is required to reach the content;
- JavaScript renders the material;
- a cookie/login session is explicitly required;
- anti-bot behavior blocks normal extraction.

## Handoff

Return:
- direct answer;
- key findings;
- important caveats/conflicts;
- source URL per significant claim;
- date/version context where relevant;
- any question that could not be resolved.
