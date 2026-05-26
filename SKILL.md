---
name: codex-history-visibility-repair
description: Use when Codex Desktop history, migrated sessions, restored rollout JSONL files, or old projects exist on disk but do not appear in the sidebar, especially after editing .codex sessions, session_index.jsonl, history.jsonl, state_5.sqlite, archived_sessions, or .codex-global-state.json.
---

# Codex History Visibility Repair

## Overview

Use the bundled Python script to repair Codex Desktop's local history indexes after migrations. The common root cause is not missing JSONL files: `thread/list` filters by exact `model_provider`, source metadata, state database rows, and project assignments.

## Quick Start

Run a dry run first:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --dry-run --scan-project-parent D:\object
```

Apply the repair and verify via `app-server thread/list`:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --scan-project-parent D:\object --verify-app-server
```

If restored sessions are still archived, include them explicitly:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --target all --unarchive --scan-project-parent D:\object --verify-app-server
```

## Workflow

1. Confirm the symptom with local counts: session files exist but `thread/list` or the sidebar returns too few rows.
2. Run `--dry-run`; check `selectedThreads`, `visibleThreads`, `providerDistribution`, and `projectMappings`.
3. Run without `--dry-run`; the script creates `~/.codex/history_sync_backups/visibility-repair.*`.
4. Prefer `--verify-app-server`; success means both `threadListStateDbOnly.returned` and `threadListScanMode.returned` match visible thread count.
5. Fully exit Codex Desktop, wait 5-10 seconds, reopen it.

## What The Script Repairs

| File or store | Repair |
|---|---|
| `state_5.sqlite` | normalizes `\\?\` prefixes, sets `source`, `thread_source`, exact `model_provider`, and millisecond timestamps |
| rollout JSONL | syncs first `session_meta.payload` so scans do not restore stale metadata |
| `session_index.jsonl` | rebuilds visible thread index |
| `history.jsonl` | rebuilds prompt history entries used by desktop history surfaces |
| `.codex-global-state.json` | rewrites project roots, root hints, and complete project assignments |

Default provider is `OpenAI` because recent Codex Desktop builds filter by that exact value. Override with `--provider` only after verifying the active build expects another string.

## Common Mistakes

- Do not only copy files into `sessions/`; the sidebar also depends on SQLite and global state.
- Do not use lowercase `openai` unless `thread/list` proves the current app expects it.
- Do not patch only `state_5.sqlite`; app-server scans rollout JSONL and can reintroduce stale provider/source metadata.
- Do not leave old after-exit scripts running; they can overwrite the repaired global state.
- Do not publish personal backups, databases, logs, or auth files with this skill.

## Publishing Hygiene

Before sharing or publishing the skill, include only:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/repair_codex_history_visibility.py`

Never include `.codex` backups, SQLite databases, `history.jsonl`, `session_index.jsonl`, logs, auth files, or user-specific rollout contents.
