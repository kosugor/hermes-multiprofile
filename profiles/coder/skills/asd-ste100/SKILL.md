---
name: asd-ste100
description: "Use when English text must be parsed without a human to resolve ambiguity — tool descriptions, error messages, inter-agent instructions, system prompts, status reports — and misreading has a real cost, or when text reads as dense, hedged, or easy to misparse. Triggers: disambiguate, STE100 rewrite, apply Simplified Technical English, plain-language rewrite, controlled-language rewrite, rewrite so an agent cannot misread this. Not for creative or marketing copy."
version: 0.5.0
---

# Simplified Technical English (ASD-STE100)

ASD-STE100 is a controlled-language standard built by the aerospace and defense industry (ASD, the AeroSpace and Defense Industries Association of Europe) to stop maintenance technicians from misreading English instructions. The standard removes the two biggest sources of misreading: words with more than one meaning, and sentences with more than one possible structure.

This skill borrows that same discipline for a different reader: an **AI agent or a downstream system** that has to parse an English string — an error message, a tool description, an inter-agent instruction, a status report — without a human in the loop to resolve ambiguity. If a maintenance technician can misread "close the valve" as an adjective ("the valve that is near") instead of a command, so can a language model.

## When to Use This Skill

- An agent's output (explanation, instruction, log message, tool description) reads as dense, jargon-heavy, or ambiguous.
- Text will be consumed by another agent, a translation pipeline, or a non-native English reader, and misparsing has a real cost.
- You are writing a prompt, system message, or tool description and want to remove ambiguity before a model ever sees it.
- You want a **before/after** comparison showing exactly which rule was violated and how the rewrite fixes it. Ask for it — the default output is the rewritten text alone (see Output Format).

This skill is not for creative or marketing copy — STE is deliberately flat and literal. Do not apply it to text where voice, nuance, or persuasion is the point.

## Two Modes

Pick a mode before rewriting. If the user does not say which, infer it from the text type. Keep the choice internal unless the user asks for the rule table (see Output Format).

**Strict** — procedures, error messages, tool and function descriptions, inter-agent instructions, and safety text. Apply every applicable Issue 9 rule. Flag dictionary and glossary checks that you cannot verify.

**STE-flavored** — READMEs, PR descriptions, changelogs, and explanatory prose. Apply the writing rules and treat dictionary-dependent checks as advisory. In practice, keep the sentence limits, use active voice, use permitted verb forms, avoid new phrasal verbs, omit semicolons, and prefer verbs over action nouns. Do not enforce one fixed term for every concept when the text needs more range.

The two modes and the structural/lexical split are the same distinction seen from two directions. The split says which rules this skill can verify without ASD's dictionary. The modes say which of them to enforce for a given kind of text.

## Source and Scope

This skill summarizes the **53 writing rules** in ASD-STE100 Issue 9 (Jan 2025), across all 9 sections, and the 8 general recommendations. See `references/writing-rules.md` for a paraphrased rule map.

It does **not** reproduce ASD's ~900-word approved dictionary verbatim. ASD-STE100 is free to obtain, but it is not free to redistribute. Issue 9 permits reproduction under written authority or for specified organizations and institutions. This project does not claim to qualify for those rights, so the dictionary stays out of this repo.

The dictionary is not stored in this repo. If you provide a local copy, the linter can check whether terms appear as uppercase approved entries or lowercase entries. It cannot verify meaning, part of speech, or form in context. Without a local copy, mark dictionary-dependent checks as unverified. Use the official dictionary as the source of truth. Request the standard from the [official downloads page](https://www.asd-ste100.org/STE_downloads.html).

## Core Rewrite Rules

The rules cover vocabulary, grammar, sentence structure, procedures, description, safety instructions, punctuation, word count, and writing practice. Some rules need the official dictionary or domain-approved terminology. Do not treat a plain-word preference as proof that a word is approved.

### Writing rules — apply these

| Rule | Do | Don't |
|---|---|---|
| Voice and procedure form (Rules 3.6, 5.3) | Use active voice. Write procedure instructions as commands. Use passive voice only in descriptive text when the actor is unknown. | Use passive procedure instructions or passive description when the actor is known. |
| One instruction per sentence (Rule 5.2) | Put separate actions in separate work steps. Keep actions together when they occur at the same time or when a result immediately follows an action. | Combine separate actions in one instruction. |
| Sentence length (Rules 5.1, 6.3) | ≤20 words per procedural sentence; ≤25 words per descriptive sentence. | Apply one cap to both types. |
| No semicolons (Rule 8.1) | Split into separate sentences | Any semicolon at all — STE bans the mark outright, not only as a clause join. (Rule 8.1 permits every other standard punctuation mark. The em dash is *not* banned by STE, though it often signals a sentence that should be split.) |
| Multi-word nouns (Rules 2.1–2.2) | Keep ordinary noun groups to three words or fewer. Write a technical noun longer than three words in full. | Shorten or split an approved technical noun and change its meaning. |
| Explicit wording (Rules 4.2, 4.5) | Keep required words. Use articles or demonstrative adjectives when applicable. | Omit words, articles, or demonstratives to shorten text. |
| Verb forms (Rules 3.2–3.5) | Use permitted simple forms. Use an -ing verb form only as a technical noun or as a modifier in a technical noun. | Use present perfect, other complex auxiliary constructions, or an -ing verb form outside a technical noun. |
| Conditions (Rule 5.4) | Put a condition the reader must know first before the command, then separate it with a comma. | Hide a required condition after the command. |
| Paragraphs (Rules 6.4–6.6) | Group related information. Keep one topic and no more than six sentences in each paragraph. | Mix topics or exceed six sentences in a paragraph. |
| Descriptive structure (Rules 6.1–6.2) | Give information in a useful order. Use key words and phrases to show the structure. | Present details before the reader has the information needed to understand them. |
| Vertical lists (Rule 4.3) | Use a vertical list for complex text. Make list items connect clearly to the lead-in. | Bury a complex sequence or enumeration in prose. |
| Connecting text (Rule 4.4) | Use approved connecting words or phrases to link related sentences. | Leave the relationship between related sentences unclear. |
| Safety instructions (Rules 7.1–7.3) | Identify the risk level, start with a clear command or condition, and explain the risk or result. | Invent a risk level or omit a stated risk explanation. |
| Punctuation and word counts (Rules 8.2–8.7) | Use hyphens for directly related words. Use parentheses for the listed functions. Count sentences and list items by the STE rules. | Assume whitespace token counts match STE word counts. |
| Style and sentence construction (Rules 9.1, 9.4) | Change sentence construction when word substitution is not enough. Use terminology and wording consistently. | Make word-for-word substitutions that preserve ambiguity or rotate terms for the same item. |
| Spelling (Rule 1.14) | Use American English unless an official directive says otherwise. | Change spelling required by an applicable directive. |

### Dictionary-dependent checks — verify externally

| Rule | Do | Don't | Why it is weaker here |
|---|---|---|---|
| Approved words, meanings, and parts of speech (Rules 1.1–1.4, 9.2) | Check each candidate against the official dictionary. | Infer approval from familiarity or simplicity. | This repo does not contain the dictionary. |
| Technical nouns and verbs (Rules 1.5–1.13) | Use an unapproved word only as a technical noun or part of one. Use technical terms approved for the company, industry, or subject field. Choose short, clear technical nouns. Keep terms consistent. Use technical verbs only in their approved roles. | Treat any jargon as approved or use a technical noun as a verb. | A domain glossary must come from the user or organization. |
| Action wording (Rule 3.7) | Describe an action with an approved verb. | Replace an action with a derived noun when the approved verb is available. | Exact approval requires the dictionary. |
| Regional, slang, and jargon terms (Rule 1.10) | Avoid these as technical nouns unless an approved terminology list permits them. | Treat an undefined term as standard STE vocabulary. | The skill cannot validate the dictionary entry. |
| Word combinations (Rule 9.3) | Use words with their approved meanings. Check the dictionary before using a verb and preposition together. | Create a phrasal verb whose meaning differs from its parts. | Only a small number of restricted phrasal verbs are approved. |

### Verb tense and meaning

STE permits the infinitive, imperative, simple present, simple past, simple future, and past participle as an adjective. It does not permit present perfect or other complex auxiliary constructions. This includes modal perfect forms such as "may have failed." Preserve the source meaning. If no permitted construction preserves it, do not silently change the claim: retain the meaning and flag that the text departs from the rule.

Use the past participle as an adjective only where the sentence structure supports that use. Do not use an -ing verb form except as a technical noun or as a modifier in a technical noun. Dictionary entries determine which forms are approved.

### Procedure and safety checks

For procedures, use the imperative. Put a required condition before the command. Use one instruction per sentence, except when actions occur at the same time or a result immediately follows an action. Use notes to give information, not to issue instructions.

For safety instructions, preserve the supplied risk level and label. A warning identifies risk of injury or death. A caution identifies risk of damage to objects. Start with a clear command or condition, then explain the risk or possible result. Do not infer a warning or caution from missing information. Flag the text for review when the risk level is not stated or is unclear.

### Word counts and punctuation

Count words with the Issue 9 rules, not whitespace tokens alone. A vertical-list colon ends the lead-in sentence for counting. Parenthetical text counts as one word in the surrounding sentence and also as a separate sentence when it is a sentence. Count numbers, numbers with units, abbreviations, alphanumeric identifiers, quoted text, titles, labels, and proper nouns as one word each. Hyphenated words count as one word. Rule 8.3 limits parentheses to specified uses, such as references, identifiers, procedure steps, abbreviations, explanations, and alternatives.

Use hyphens to connect directly related words. The semicolon is not permitted. STE does not define all punctuation use; use the applicable publication style guide for punctuation rules that the standard does not specify.

## Scan Checklist

These habits help identify common clarity problems. Some checks need context, dictionary review, or a judgment about meaning. Scan for all six before you rewrite anything.

1. **Synonym rotation** — the same thing gets several names in one document ("the user", "the customer", "the client"). The reader cannot tell whether they are one thing or three. Fix: pick one name, use it every time.
2. **Hedge stacking** — helper verbs and qualifiers pile up until the sentence asserts nothing ("it is important to note that this may potentially help to improve"). Fix: state the claim, or delete it.
3. **Nominalization** — an action frozen into a noun ("perform an analysis of", "provides assistance to"). Fix: use the verb ("analyze", "helps").
4. **Marketing adjectives** — words that claim quality instead of showing it: seamless, robust, powerful, cutting-edge, effortless, blazing-fast. Fix: delete, or replace with the measurement that earns the claim.
5. **Run-on sentences** — several ideas joined by semicolons or em dashes. Fix: one idea per sentence.
6. **Soft phrasal verbs** — spin up, reach out, dive into, kick off. Fix: use the single plain verb (start, contact, read, begin).

## Process

1. Pick the mode (Strict or STE-flavored). Say which only when the user asked for the rule table — see Output Format.
2. Read the input text once for meaning — do not start rewriting before you understand what it must still say afterward.
3. Walk the text sentence by sentence. Check all applicable items in the rule tables and the Scan Checklist. In STE-flavored mode, keep the sentence and document structure rules, but treat dictionary-dependent checks as advisory. The linter is a partial first pass. Use `--procedural` for its estimated 20-word limit; otherwise it uses an estimated 25-word descriptive limit. If the user has a local Issue 9 PDF, pass it with `--dictionary-pdf PATH`. The linter reads the PDF through `pdftotext` and keeps the extracted text in memory. Use `--technical-terms PATH` for a user-managed file with one approved domain term per line. The dictionary scan checks entry status only; review approved meaning, part of speech, and form in context. Review articles, list structure, safety labels, spelling, and word counts manually.
4. Rewrite each flagged sentence to fix the violation while preserving the original meaning exactly. If a rewrite would drop necessary precision (a safety condition, a scope qualifier, a number), keep the longer phrasing and flag it instead of silently simplifying.
   - **Check modality before you commit to a rewrite.** Hedges carry the author's confidence. Preserve that meaning, but do not claim full STE compliance if a required hedge needs a verb construction that STE prohibits. Flag the conflict.
   - Never add a fact the source did not state. A rewrite that reads better because it supplies a cause, a frequency, or a mechanism has stopped being a rewrite.
5. Output the rewritten text (see Output Format). Keep the mode choice and the rule analysis internal unless the user asked to see them. If a rule conflict or unavailable dictionary check prevents a compliance claim, include a short review note.
6. If the input already complies, say so — do not force changes onto compliant text.

## Output Format

**Default: the rewritten text, and nothing else.** Most callers want a result they can paste straight into a tool description, an error string, or a prompt. Print the simplified text on its own. Do not add a preamble about this skill, a mode announcement, a violation count, a summary of what changed, a rule table, or a closing offer to explain further.

Permitted review notes: use `Kept as-is:` when a longer phrase preserves needed precision. Use `STE review required:` when the source meaning conflicts with a rule, or when a dictionary or domain glossary check is unavailable. Omit both notes when there is nothing to report.

**On request: the rule table.** When the user asks to see the reasoning — "show the diff", "which rules did it break", "explain the changes", "before/after" — output this table instead:

```markdown
| Rule violated | Original | Simplified |
|---|---|---|
| Complex auxiliary construction (Rule 3.4) | "We have received your request." | "We received your request." |
| Multi-word noun (Rule 2.1) | "the high pressure fuel pump inlet valve" | Rewrite only if the phrase is not an approved technical noun. Keep longer technical nouns in full. |

Mode: Strict. 7 violations found.
```

Follow the table with a one-line note on anything you deliberately did **not** simplify, and why (usually: simplifying would lose required precision).

## Boundaries

**Will:**
- Rewrite ambiguous or dense English into short, single-meaning, active-voice sentences.
- Return the rewritten text alone by default, and name the rules it applied when the user asks.
- Preserve every fact, condition, and scope qualifier in the original.
- Preserve the meaning and strength of every hedge. Flag any conflict between that meaning and a required STE verb form.
- Suggest a one-line glossary entry for a domain term that must stay. Do not treat the suggestion as approved terminology.

**Will not:**
- Reproduce ASD's official ~900-word dictionary as if it were memorized verbatim — always treat the official download as the source of truth for exact approved wording.
- Simplify creative, marketing, or persuasive copy where voice and nuance are the point.
- Silently drop a safety condition, exception, or scope qualifier to shorten a sentence — it will flag the trade-off instead.
- Convert a hedge into a fact to force compliance. Preserve the claim and flag a non-compliant construction when no compliant rewrite preserves its meaning.
- Guarantee an aerospace/defense-grade STE-compliant document. This is a general-purpose clarity tool inspired by STE, not a certified STE authoring tool.
- Make weak content true or useful. STE fixes the *form* of a text, not its substance. A hollow paragraph rewritten under these rules becomes a clean, short, well-punctuated hollow paragraph. If the text has nothing to say, no rewrite fixes that — say so instead of polishing it.
- Shorten past the point of clarity. Cutting words is not the goal. Removing ambiguity is the goal. Past a certain point compression starts costing the reader time rather than saving it, so stop when the sentence is unambiguous, not when it is shortest.

## Additional Resources

- **`references/writing-rules.md`** — paraphrased map of all 9 rule sections and the general recommendations, with links to official ASD sources.
- **`examples/before-after.md`** — worked examples, including official STE examples and agent-output examples built for this skill.
- **`scripts/ste-lint.py`** — deterministic partial linter. It can check entry status against a user-supplied local PDF, but it cannot validate meaning in context or prove compliance. See its usage text and the README for setup and limits.
