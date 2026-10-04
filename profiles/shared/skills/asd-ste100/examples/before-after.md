# Before / After Examples

## Part 1 — Official STE Examples

These illustrate ASD-STE100 rules. They paraphrase rule concepts and do not reproduce the standard's examples. Verify example vocabulary in the official dictionary before claiming compliance.

| Rule | Before | After | Why |
|---|---|---|---|
| One meaning per word | "Verify the system." / "Check the connections." / "Confirm receipt." | "Make sure the system is correct." (one approved term used consistently) | Three near-synonyms force the reader to guess whether they mean the same action. |
| One part of speech per word | "Oil the valve." | "Apply oil to the valve." | If "oil" is approved only as a noun, using it as a verb breaks the one-word-one-role guarantee. |
| Precise verb meaning | "Follow the safety instructions." | "Obey the safety instructions." | "Follow" can mean "come after" or "obey" — STE picks the unambiguous one. |
| Verb forms (Rule 3.4) | "We have received the technical reports." | "We received the technical reports." | The standard does not permit the present perfect construction. |
| Verb, not noun | "Perform an inspection of the filter." | "Inspect the filter." | The noun form hides the action and adds a filler verb that carries no meaning. |
| Phrasal verbs (Rule 9.3) | "Take off the access panel." | "Remove the access panel." | Do not create a phrasal verb whose meaning differs from the dictionary meanings of its parts. Verify the verb in the dictionary. |

## Part 2 — Applied to Agent Output

These are original examples built for this skill's actual use case: rewriting AI agent output so another agent, a translation layer, or a non-native reader can parse it without ambiguity. They are illustrations, not quotes from any real system.

Word-count notes use the Issue 9 counting rules where stated. The linter's whitespace count is only an estimate and does not apply all exceptions in Rules 8.4–8.7.

### Example A — Tool description

**Before:**
> This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review.

**Violations flagged:**
- Several claims and branches share one sentence.
- Present perfect in the relative clauses ("have been configured", "has been set").
- 44 words, far over the 25-word descriptive cap.

Note what is *not* flagged: "will attempt to" and "may resolve". Those are hedges, not violations. The tool is not promised to succeed, and the rewrite must not promise it either.

**After:**
> The tool will try to synchronize state across the configured backends. If it finds a conflict, it reads the configured strategy. If the strategy allows automatic resolution, the tool may resolve the conflict without a user. If the tool does not resolve the conflict, it reports the conflict for manual review.

The last sentence branches on whether the conflict was resolved, not on what the strategy allows. That is what "or otherwise" meant in the original: the fallback covers a permitted resolution that still did not happen.

### Example B — Error message

**Before:**
> An error may have occurred while processing your request due to a possible mismatch in the expected data format, which could be caused by an outdated client version.

**Violations flagged:**
- One sentence carrying three separate claims (an error occurred, a format mismatch, a client version).
- 28 words, over the descriptive cap.

The source uses modal perfect and passive constructions. Keep the uncertainty. Flag the modal perfect because Rule 3.4 does not permit it.

**After:**
> An error may have occurred when the system processed your request. The cause may be a mismatch in the expected data format. An outdated client version may cause this mismatch.

The rewrite preserves uncertainty and does not add a cause or frequency claim. It still contains "may have occurred," which conflicts with Rule 3.4. The note below flags that conflict instead of changing the claim.

STE review required: the source meaning uses a modal perfect construction. This rewrite preserves that meaning but does not fully comply with Rule 3.4.

### Example C — Inter-agent instruction

**Before:**
> Once the upstream job has completed and assuming no errors were raised, the downstream agent should proceed to consume the output artifact, though partial artifacts are sometimes produced under timeout conditions.

**Violations flagged:**
- Present perfect ("has completed") and subordinate-clause stacking ("assuming...", "though partial artifacts are sometimes produced...").
- One sentence, three separate facts (completion condition, next action, edge-case warning).
- The sentence exceeds the 20-word procedural cap.

**After:**
> After the upstream job completes without errors, the downstream agent should read the output artifact. A timeout can produce a partial artifact.

The rewrite puts the condition first and keeps "should" because it expresses a recommendation. Rule 5.3 requires imperative form for an instruction. Preserve the recommendation and flag this conflict rather than strengthening it silently. The timeout sentence gives information. It does not add a warning label because the source does not classify this as a safety risk.

STE review required: Rule 5.3 requires an imperative. The source expresses a recommendation with "should".

### Example D — README prose (STE-flavored mode)

**Before:**
> Our caching layer is designed to slot seamlessly into your existing stack with minimal friction and no vendor lock-in; it leverages semantic similarity to dramatically reduce the cache misses that traditionally plague LLM workloads.

**Violations flagged:**
- Marketing adjectives and claims without measurement ("seamlessly", "minimal friction", "dramatically").
- Semicolon joining two separate ideas.
- Nominalization and soft phrasing ("is designed to slot into", "leverages").
- 34 words, over the 25-word descriptive cap.

**After:**
> The cache uses semantic similarity to reduce cache misses in LLM workloads. It works with your current stack and does not require vendor lock-in.

Flavored mode keeps the claims from the source. It removes unsupported marketing language and splits the semicolon into separate sentences.

## How to Read These Examples

Part 1 shows selected Issue 9 rules. Part 2 applies those rules to agent text. The skill cannot verify dictionary compliance without the official dictionary and applicable domain terminology.
