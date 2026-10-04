# ASD-STE100 Skill — Simplified Technical English for Agent Output

A Claude Code skill that rewrites dense, ambiguous English using the rules in [ASD-STE100 Issue 9](https://www.asd-ste100.org/) (STE).

This skill repurposes that same discipline for a different reader: an **AI agent** parsing another agent's output, a tool description, an error message, or an inter-agent instruction, with no human in the loop to resolve ambiguity.

## Why STE, and Why for Agents

STE helps readers understand technical text. It combines writing rules with a controlled dictionary. Its rules cover word use, grammar, sentences, procedures, descriptions, safety instructions, punctuation, and word counts.

An LLM agent parsing another agent's output is in a strikingly similar position — no back-channel, no way to ask "did you mean X or Y?" The same rules that keep a mechanic from misreading a torque spec keep a downstream agent from misreading a tool description or an inter-agent message.

## Before / After

| Before | After |
|---|---|
| "This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review." | "The tool tries to synchronize state across the configured backends. If it finds a conflict, it reads the configured strategy. If the strategy allows automatic resolution, the tool may resolve the conflict without a user. If the tool does not resolve the conflict, it reports the conflict for manual review." |
| "An error may have occurred while processing your request due to a possible mismatch in the expected data format, which could be caused by an outdated client version." | "An error may have occurred when the system processed your request. A mismatch in the expected data format may be the cause. An outdated client version could cause this mismatch." |

More examples, including illustrations of the official STE rules themselves, in [`examples/before-after.md`](examples/before-after.md).

STE review required: the error-message example preserves a modal perfect construction from the source. Issue 9 does not permit that verb construction.

## What This Skill Does

1. Picks a mode. **Strict** applies the Issue 9 rules as far as the input and available terminology allow. **STE-flavored** uses the structural rules for explanatory prose and treats dictionary-dependent checks as advisory.
2. Reads the input English text for meaning.
3. Reviews each sentence and paragraph against the rule map in `references/writing-rules.md`, including procedure, safety, punctuation, and word-count requirements.
4. Rewrites flagged text while preserving its meaning. If a compliant rewrite is not possible, it preserves the source meaning and flags the conflict.
5. Outputs the rewritten text alone by default. It adds a short `Kept as-is:` or `STE review required:` note only when needed.

Ask for the reasoning ("show the diff", "which rules did it break") and it outputs a before/after table naming each rule instead.

The skill does not claim compliance when the required dictionary or domain glossary is unavailable. It identifies those checks as unverified.

The linter checks selected text patterns only. It does not compare an original text with a rewrite, verify meaning, or prove compliance. A zero-violation result means only that its configured checks found no findings.

The deterministic linter checks semicolons, selected phrasal verbs, nominalizations, marketing adjectives, possible passive voice, complex auxiliary forms, selected -ing verb forms, approximate sentence length, synonym rotation, and dangling conjunctions in supported list items. Use `--procedural` for the 20-word procedural cap. Sentence counts use whitespace tokens as an estimate; they do not apply every Issue 9 word-count exception. The linter does not check noun-cluster length, articles, risk classification, spelling, or all phrasal verbs. Manual review is required.

### Use a local dictionary PDF

The repo does not contain the official dictionary. Point the linter at your own local Issue 9 PDF:

```bash
python scripts/ste-lint.py --dictionary-pdf /path/to/ASD-STE100-ISSUE9.pdf input.md
```

The linter needs `pdftotext` on `PATH`. If it is not on `PATH`, pass its location with `--pdftotext /path/to/pdftotext`. On Windows, you can set `PDFTOTEXT_PATH` to the executable path. The linter reads extracted text in memory and does not save or add it to the repo.

You can set `ASD_STE100_DICTIONARY_PDF` to use the same local PDF on later runs. The script also accepts `--dictionary-pdf`, which overrides that setting.

The dictionary scan reports entries that appear lowercase or do not appear in the PDF. ASD marks uppercase entries as approved. The scan does not decide whether an approved word has the right meaning, part of speech, or form in context. Review those points manually. A word that is not listed can be a proper noun or an approved domain term.

To allow company or subject-field terms, pass a text file with one approved term per line:

```bash
python scripts/ste-lint.py --dictionary-pdf /path/to/ASD-STE100-ISSUE9.pdf --technical-terms glossary.txt input.md
```

Keep this glossary under your organization's control. Do not copy the official dictionary into it.

The rule map and examples quote patterns that the linter checks, so findings in those files can be examples rather than defects.

The dangling-conjunction rule checks list markers at the start of a line with zero to three leading spaces and ASCII spaces after the marker. It supports unordered markers `-`, `*`, and `+`, and ordered numeric markers that end in `.` or `)`, such as `1.` or `1)`. It checks indented continuation lines up to the final meaningful line. It does not parse list syntax inside blockquotes, lazy continuation, or full nested-list semantics. A standalone line with four or more leading spaces is not treated as a list marker. Within an active list item, indentation at the computed content column is treated as continuation text. Fence detection follows the linter's existing simple rule: a stripped line beginning with three backticks or three tildes toggles the fence state.

The intentionally invalid examples/linter-edge-cases.md file demonstrates incomplete Markdown list items. Run python scripts/ste-lint.py examples/linter-edge-cases.md to confirm that the linter reports the two expected findings. The file is a test fixture and should not be used as compliant STE prose.

It does **not** reproduce ASD's official approved dictionary. Use the official standard to verify approved words, meanings, parts of speech, and forms. This general-purpose skill does not certify technical documentation as STE-compliant.

Full rule summary and citations: [`references/writing-rules.md`](references/writing-rules.md).

## Installation

### Quick Install (npx skills)

The fastest way to install this skill is the [skills CLI](https://skills.sh/) — no clone, no path setup. Run it from your project root:

```bash
npx skills add danyuchn/asd-ste100-skill
```

This pulls the skill from the GitHub repo and installs it for the current project. The CLI sends anonymous install telemetry (skill name and timestamp, no personal or device information) to help rank skills on the skills.sh leaderboard. Set `DISABLE_TELEMETRY=1` to opt out.

Update later with `npx skills update`.

### Clone

```bash
git clone https://github.com/danyuchn/asd-ste100-skill ~/.claude/skills/asd-ste100
```

This clones the repo into `~/.claude/skills/`, making the skill available in every Claude Code project. Best for contributors and anyone who wants a live checkout that updates with `git pull`.

## Usage

Trigger with a request to simplify or clarify English text:

```
Disambiguate this tool description
Rewrite this error message so an agent can't misparse it
Apply ASD-STE100 to this instruction
```

Or paste text and ask Claude to "disambiguate this" / "apply STE100 to this" / "reduce ambiguity in this output."

You get the rewritten text back and nothing else. To see which rules were applied, add "show the diff" or "explain the changes" to the request.

## Scope

Built for: agent-to-agent messages, tool/function descriptions, error messages, system prompts, inter-agent instructions — any English text a machine or non-native reader has to parse without a human to ask.

Not built for: creative writing, marketing copy, or anything where voice and nuance are the point — STE is deliberately flat and literal by design.

One limit worth stating up front: this fixes the form of a text, not its substance. A paragraph with nothing to say comes out short, clean, and still empty.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/)
- [ASD-STE100 — About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe — Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English — Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe — ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)

## License

MIT — see [LICENSE](LICENSE).
