# Memory maintenance

How to keep these Serena memories healthy (seeded 2026-06-25).

## Layout
Memories are human-readable Markdown in `.serena/memories/`, versioned with the repo.
`mem:core` is the entry point and links the rest. Cross-reference other memories with the
`` `mem:NAME` `` convention (backticked) so renames stay in sync.

Current set: `mem:core`, `mem:tech_stack`, `mem:architecture_backend`, `mem:auth_and_rbac`,
`mem:security_status`, `mem:conventions`, `mem:memory_maintenance` (this file).

## Rules
- **Update memories in the same change as the code.** When a `mem:security_status` item is
  fixed, move it from OPEN to DONE; when a flow changes, update `mem:auth_and_rbac` /
  `mem:architecture_backend`.
- Keep each memory focused and skimmable; put detail in the right topic file, not in `mem:core`.
- Convert relative dates to absolute. State facts that are NOT obvious from the code/git
  (decisions, gotchas, owner preferences) — don't duplicate what the code already says.
- The SRS PDF (`SRS_..._Final.pdf`) is the ultimate spec authority; if a memory and the SRS
  disagree, trust the SRS and fix the memory.

## Provenance
Seeded from a full foundation review of the backend (4-domain audit + per-line verification)
and the source docs. Login/RBAC content reflects SRS §21.
