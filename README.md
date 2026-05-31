# Codex History Visibility Repair

Repair hidden Codex Desktop history after local session migration.

This skill is for the case where old Codex sessions, migrated rollout JSONL
files, or restored project history exist on disk but do not appear in the Codex
Desktop sidebar. The repair is local-only: it edits Codex Desktop metadata under
`CODEX_HOME`, creates backups before changes, and does not send session content
or credentials anywhere.

## Install

Install from OpenClaw:

```powershell
openclaw skills install codex-history-visibility-repair
```

After installation, the skill is available to Codex as:

```text
codex-history-visibility-repair
```

You can also clone this repository and copy the skill folder into
`%USERPROFILE%\.codex\skills\codex-history-visibility-repair`.

## When To Use It

Use this when:

- Codex Desktop sidebar shows fewer conversations than the files under
  `%USERPROFILE%\.codex\sessions`.
- You migrated or restored `sessions`, `session_index.jsonl`, `history.jsonl`,
  `state_5.sqlite`, or `.codex-global-state.json`.
- Old projects exist on disk but conversations are grouped incorrectly or
  appear as projectless.
- Rollout JSONL files exist, but `thread/list` or Desktop history surfaces do
  not return them.

The common root cause is not missing session files. Recent Codex Desktop builds
also depend on exact metadata in SQLite, rollout JSONL `session_meta`, local
history indexes, and project assignments. In particular, current builds can
filter by exact `model_provider` and `source` values.

## Quick Start

Close Codex Desktop first. Then run a dry run:

```powershell
py "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --dry-run --verify-app-server
```

Apply the repair:

```powershell
py "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --verify-app-server
```

If restored sessions are still archived and you want them visible:

```powershell
py "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --target all --unarchive --verify-app-server
```

Reopen Codex Desktop after the repair finishes.

On Windows, use `py` if `python` points to the Microsoft Store/WindowsApps
placeholder. Only pass `--scan-project-parent D:\object` when you intentionally
want every child directory under that parent to become a saved Codex project.

## What It Repairs

| Store | Repair |
| --- | --- |
| `state_5.sqlite` | Normalizes `\\?\` path prefixes, sets `source`, `thread_source`, exact `model_provider`, and millisecond timestamps. |
| Rollout JSONL files | Updates the first `session_meta.payload` so app-server scans do not restore stale metadata. |
| `session_index.jsonl` | Rebuilds the visible session index from repaired thread rows. |
| `history.jsonl` | Rebuilds prompt history rows used by Desktop history surfaces. |
| `.codex-global-state.json` | Rewrites workspace roots, thread root hints, and project assignments. Stale saved roots are pruned by default. |

Backups are created in:

```text
%USERPROFILE%\.codex\history_sync_backups\visibility-repair.YYYYMMDD-HHMMSS
```

## Script Options

```text
--codex-home PATH
    Override CODEX_HOME. Defaults to CODEX_HOME or %USERPROFILE%\.codex.

--target visible|all
    Select visible threads only, or every thread in state_5.sqlite.

--unarchive
    Set selected threads archived=0.

--provider VALUE
    Exact model_provider to write, or auto. Defaults to auto.

--source VALUE
    Thread source to write, or auto. Defaults to auto.

--thread-source VALUE
    Thread source kind to write. Defaults to user.

--scan-project-parent PATH
    Add child folders of PATH as candidate project roots. Can be repeated.

--keep-existing-project-roots
    Keep saved project roots that are not referenced by visible threads.

--protect-state-minutes N
    Temporarily mark .codex-global-state.json read-only after repair.
    Defaults to 0 minutes.

--verify-app-server
    Start Codex app-server and call thread/list in both state-db-only and
    scan modes to verify visibility.

--verify-timeout-seconds N
    Verification timeout for each app-server thread/list call. Defaults to 90.

--dry-run
    Print the planned repair summary without modifying files.
```

## Reading The Output

The script prints JSON. Useful fields:

| Field | Meaning |
| --- | --- |
| `selectedThreads` | Number of threads selected for repair. |
| `visibleThreads` | Number of unarchived threads after repair selection. |
| `resolvedProvider` | Provider chosen from args or the latest visible local thread. |
| `resolvedSource` | Source chosen from args or the latest visible local thread. |
| `sessionIndexRows` | Rows written to `session_index.jsonl`. |
| `historyRows` | Rows written to `history.jsonl`. |
| `rolloutMetaChanged` | Rollout JSONL files whose first `session_meta` row changed. |
| `rolloutMetaSkippedLocked` | Rollout files skipped because they could not be read. |
| `rolloutMissing` | Thread rows whose rollout path is missing. |
| `projectRoots` | Workspace roots written into global state. |
| `projectMappings` | Thread-to-project assignments written into global state. |
| `providerDistribution` | Distribution of visible thread `model_provider` values. |
| `sourceDistribution` | Distribution of visible thread `source` values. |
| `threadListStateDbOnly` | Verification result from app-server using SQLite only. |
| `threadListScanMode` | Verification result from app-server scan mode. |

## Safety Model

- No network calls are made by the repair script.
- No secrets, tokens, credentials, or auth files are read or published.
- The script only changes local Codex Desktop metadata under `CODEX_HOME`.
- Backups are made before non-dry-run changes.
- Personal backups, SQLite databases, logs, and rollout contents should never be
  committed to this repository.

## Troubleshooting

If the sidebar still does not show the expected history:

1. Fully exit Codex Desktop, wait 5 to 10 seconds, then reopen it.
2. Run with `--verify-app-server` and compare `threadListStateDbOnly.returned`
   with `threadListScanMode.returned`.
3. Check `resolvedProvider`, `resolvedSource`, `providerDistribution`, and
   `sourceDistribution`. If your Desktop build expects different exact values,
   rerun with `--provider` or `--source`.
4. Check `rolloutMetaSkippedLocked`. Close processes that may hold session files
   open and rerun the repair.
5. Check for old after-exit scripts, stale read-only attributes, or manual sync
   jobs that rewrite `.codex-global-state.json` after the repair.
6. If sessions are archived, use `--target all --unarchive`.
7. If scan-mode verification times out on very large rollout files, increase
   `--verify-timeout-seconds`.

## Repository Layout

```text
SKILL.md
agents/openai.yaml
scripts/repair_codex_history_visibility.py
tests/test_repair_codex_history_visibility.py
```

Only `SKILL.md`, `agents/openai.yaml`, and `scripts/repair_codex_history_visibility.py`
are required for the skill package. The test file is for repository validation.

## Contributing

Issues and pull requests are welcome. Please keep changes focused on local
Codex Desktop history repair, avoid adding telemetry or network calls, and do
not include personal `.codex` data in examples or tests.
