# Project Agent Guide

This repository is an evidence-bounded agent workspace for the game `率土之滨`.
It supports current-account account intake, lineup construction, resource
validation, battle-report review, and retrieval from a curated strategy library.

## Read order

1. `README.md` for the current entry points and runnable commands.
2. `迁移知识与流程接手_20261012.md` for the adopted workflow and evidence boundaries.
3. `.workbuddy/memory/RULES/` for the authoritative rules, read 01 through 05.
4. `工具/配将服务/README.md` for the executable service contract.
5. The mechanism and battle-report rules under `资料库/官方机制库/`.
6. `PUBLISHING.md` before adding large files or publishing artifacts.

Historical `HANDOFF_*.md` files are snapshots, not current-state proof. Later
decisions in the rules and migration note take precedence over stale entries.

## Non-negotiable evidence boundaries

- Use the current client, current account export, current skill text, and current
  battle evidence before relying on old reports or historical lineups.
- Never commit or print a raw 百家社 account export, login token, cookie, API key,
  or other credential. Use read-only parsing; persist a sanitized profile only
  when the user explicitly asks for an account archive.
- Resolve heroes by exact IDs and matching built-in skills. Never infer a hero
  version or star level from name order, `hero_extra.quality`, or a report alone.
- Treat `lineup_ready` and `delivery_ready` as different states. A passing
  structural validator is not proof of lineup strength or current meta rank.
- Keep verified facts, structural judgments, and unresolved items separate.
  Unknown season, skill parameters, research state, gear, or duplicate-card counts
  must remain unknown.
- Historical articles and refined reports are low-weight cases. The mechanism
  rules and current evidence override them.

## Working defaults

- A complete consultation first asks for season/script, purpose, team count,
  COST, and explicitly preserved old teams.
- Treat hero level as 30 by default for planning unless the user specifies another
  value. This is a calculation default, not an account fact.
- Inventory skills by total allocatable copies. Old teams can normally be
  dismantled; explicitly preserved teams reserve their heroes and skills.
- Prioritize the first three main teams before allocating later utility teams.
- For random or strength findings, require at least five representative battle
  reports per team; a fully evidenced deterministic hard error can be corrected
  immediately.

## Verification

Use Python 3.10 or newer. From the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
python -m unittest discover -s '.\工具\配将服务' -p 'test_*.py' -v
python '.\资料库\test_aa_rate_supplement.py'
python '.\资料库\test_hero_version_resolver.py'
python '.\资料库\test_legacy_version_evidence.py'
```

The local Windows verification baseline has also been run with:

```text
C:\Users\30493\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

That absolute interpreter path is machine-specific and must not be treated as a
portable project dependency.

## Repository hygiene

The main branch intentionally carries searchable text, source code, structured
JSON, and DOCX reports. Portable tools, videos, screenshots, archives, and scratch
renders belong outside the main tree. See `PUBLISHING.md`.

