# ASD-STE100 Issue 9: Rule Map

This file summarizes ASD-STE100 Issue 9 (2025-01-15). It paraphrases the 53 writing rules in Part 1 and lists the 8 general recommendations. It does not reproduce the controlled dictionary or the standard's examples. Use the official standard as the authority for exact wording and dictionary checks.

## Structure of the standard

ASD-STE100 has two parts: writing rules and a controlled dictionary. The dictionary defines approved meanings and parts of speech, plus unapproved words and alternatives. Organizations can also maintain approved technical nouns and verbs for their subject fields. This repo does not include the official dictionary. The linter can inspect a user-supplied local PDF for entry status, but it cannot validate dictionary compliance in context.

## Part 1: Writing rules

### Section 1 — Words (Rules 1.1–1.14)

- Use words that the dictionary approves, or approved technical nouns and verbs. Use approved words only in their listed meaning and part of speech, and use only listed forms.
- Use non-dictionary words only as technical nouns or parts of technical nouns. Use technical terms approved for the applicable company, industry, or subject field.
- Select technical nouns that are short and easy to understand. Do not use regional, slang, or jargon words as technical nouns. Use one technical noun consistently for the same item.
- Do not use technical nouns as verbs or technical verbs as nouns.
- Use American English spelling unless an official directive specifies another form.

### Section 2 — Multi-word nouns (Rules 2.1–2.2)

- Keep ordinary multi-word nouns to three words or fewer.
- Write a technical noun that has more than three words in full. Do not shorten it in a way that changes the term.

### Section 3 — Verbs (Rules 3.1–3.7)

- Use verb forms that the dictionary lists. The permitted forms are infinitive, imperative, simple present, simple past, simple future, and past participle used as an adjective.
- Do not use other verb tenses or complex auxiliary constructions. In particular, do not use *have* with a past participle to form a perfect tense.
- Use an -ing verb form only as a technical noun or as a modifier in a technical noun.
- Use active voice. In descriptive writing, use passive voice only when the agent is unknown.
- Describe actions with approved verbs, not nouns or other parts of speech.

### Section 4 — Sentences (Rules 4.1–4.5)

- Write short, clear sentences.
- Do not omit words or use contractions to shorten a sentence.
- Use a vertical list for complex text. End the lead-in sentence with a colon. Identify each item, start it with an uppercase letter, and use an article where applicable. End full-sentence items with a period. Do not put a comma or semicolon at an item end. End the final item with a period. Make each item connect clearly to the lead-in, and do not mix procedural and descriptive writing in one list. In a safety list, repeat negative commands for each item where needed.
- Use connecting words or phrases to link sentences about related topics.
- When applicable, use an article or demonstrative adjective before a noun or multi-word noun. Do not add articles to general statements where they do not apply.

### Section 5 — Procedural writing (Rules 5.1–5.5)

- Limit each procedural sentence to 20 words.
- Use one instruction per sentence, except when actions occur at the same time or when a result immediately follows an action.
- Write instructions in the imperative form. Do not add *must* before an imperative unless safety or an important condition requires it.
- Put a condition that the reader must know first before the command. Separate the condition from the command with a comma.
- Use notes to give information, not instructions.

### Section 6 — Descriptive writing (Rules 6.1–6.6)

- Give information gradually. Use key words and phrases to show a logical structure.
- Limit each descriptive sentence to 25 words.
- Use paragraphs to group related information. Keep one topic in each paragraph and no more than six sentences in a paragraph.

### Section 7 — Safety instructions (Rules 7.1–7.3)

- Use an applicable word or symbol to identify the risk level. In the standard's examples, *warning* identifies risk of injury or death, and *caution* identifies risk of damage to objects.
- Start the safety instruction with a clear, accurate command or condition.
- Explain the risk or possible result. Do not infer the risk level when the source does not give enough information.

### Section 8 — Punctuation and word count (Rules 8.1–8.7)

- Do not use semicolons. Use hyphens to connect words that are directly related.
- Use parentheses for the functions listed in the standard, such as references, identifiers, procedure steps, abbreviations, singular and plural forms, explanations, and alternatives.
- In a vertical list, the lead-in colon has the effect of a period for sentence length. Count each list item as a new sentence.
- Parenthetical text counts as one word in its surrounding sentence. If the parenthetical text is a sentence, count it as a separate sentence too.
- Count each number, number with its unit, abbreviation, alphanumeric identifier, quoted text, title, heading, placard or label, and proper noun in the categories stated by the standard as one word.
- Count a hyphenated word as one word.

### Section 9 — Writing practices (Rules 9.1–9.4)

- When a word-for-word replacement does not produce a clear sentence, change the sentence construction.
- Use every approved word correctly. Do not combine words to create a phrasal verb with a meaning that differs from the dictionary meanings of its parts. Only a small number of phrasal verbs have restricted approved meanings; verify them in the dictionary.
- Use terminology and wording consistently.

## General recommendations (GR-1–GR-8)

Issue 9 also gives recommendations about the conjunction *that*, the preposition *with*, pronouns, the pronoun *this*, false friends, Latin abbreviations, inclusive language, and possessive forms. Apply the full recommendations from the official standard when these topics occur. This summary does not replace their detailed guidance.

## Limits of this repo's linter

The linter checks selected text patterns. If you provide a local Issue 9 PDF, it can report whether a word appears as an uppercase entry, a lowercase entry, or no entry. It cannot confirm approved meaning, part of speech, or form in context. It also cannot check whether a term is an approved domain term unless you list that term in a separate user-managed glossary. It cannot check whether a condition is required, safety risk classification, article use, or every rule for lists and word counts. A clean lint result is not proof of ASD-STE100 compliance.

## Source

- [ASD-STE100 Issue 9 (official PDF)](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
- [ASD-STE100 — About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD-STE100 downloads](https://www.asd-ste100.org/STE_downloads.html)
