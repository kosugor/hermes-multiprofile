# Obsidian Vault Smoke Test Example

Use this as a minimal reference when validating a vault.

## Sequence

1. Resolve `OBSIDIAN_VAULT_PATH` to an absolute path.
2. Verify the directory exists.
3. List `*.md` files in the vault.
4. Read one existing note if available.
5. Search note contents with `file_glob: "*.md"`.
6. Create `Hermes Obsidian Skill Test.md`.
7. Optionally create `Hermes Obsidian Companion.md` for wikilink verification.
8. Patch the main test note to append a status line and a short section.
9. Read the note back and confirm the appended text is present.

## Minimal success criteria

- Vault path resolved
- Directory exists
- Note listing works
- Read works
- Search works
- Create works
- Patch works
- Read-back confirms final content

## Example note names

- `Hermes Obsidian Skill Test.md`
- `Hermes Obsidian Companion.md`

## Example wikilinks

- `[[test]]`
- `[[Hermes Obsidian Companion]]`
