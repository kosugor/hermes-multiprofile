# Importing and Merging Prior Research into Obsidian

Use this pattern when the user already has research saved as markdown outside the vault and wants it brought into Obsidian.

## Import pattern

1. Resolve the vault path first.
2. Identify the source markdown files to import.
3. Create cleaned Obsidian-native note titles rather than preserving awkward export filenames as the primary note names.
4. Store the original path in frontmatter as `source_file:`.
5. Put bulk imports under a dedicated folder such as `Imported Research/` unless the user requested another destination.
6. Add `[[wikilinks]]` between notes that belong to the same topic cluster.
7. Create an index note that links the imported note set.

## Merge pattern

When the user wants one master note:

1. Read the imported notes.
2. Synthesize them into a single master note with sections such as:
   - Executive Summary
   - Main Findings
   - Tax / Legal Notes
   - Checklists
   - Comparisons
   - Recommendations
   - Source Notes
3. Keep links back to the source notes with wikilinks.
4. Keep the source notes unless the user explicitly asks to archive, replace, or delete them.

## Verification

- Confirm the imported files exist in the vault.
- Read back the index or master note.
- Search for the expected wikilinks to confirm the note graph was created as intended.
