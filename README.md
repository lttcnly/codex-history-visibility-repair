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
filter by an exact `model_provider` value such as `OpenAI`.

## Quick Start

Close Codex Desktop first. Then run a dry run:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --dry-run --scan-project-parent D:\object
```

Apply the repair:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --scan-project-parent D:\object --verify-app-server
```

If restored sessions are still archived and you want them visible:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-history-visibility-repair\scripts\repair_codex_history_visibility.py" --target all --unarchive --scan-project-parent D:\object --verify-app-server
```

Reopen Codex Desktop after the repair finishes.

## What It Repairs

| Store | Repair |
| --- | --- |
| `state_5.sqlite` | Normalizes `\\?\` path prefixes, sets `source`, `thread_source`, exact `model_provider`, and millisecond timestamps. |
| Rollout JSONL files | Updates the first `session_meta.payload` so app-server scans do not restore stale metadata. |
| `session_index.jsonl` | Rebuilds the visible session index from repaired thread rows. |
| `history.jsonl` | Rebuilds prompt history rows used by Desktop history surfaces. |
| `.codex-global-state.json` | Rewrites workspace roots, thread root hints, and project assignments. |

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
    Exact model_provider to write. Defaults to OpenAI.

--source VALUE
    Thread source to write. Defaults to cli.

--thread-source VALUE
    Thread source kind to write. Defaults to user.

--scan-project-parent PATH
    Add child folders of PATH as candidate project roots. Can be repeated.

--protect-state-minutes N
    Temporarily mark .codex-global-state.json read-only after repair.
    Defaults to 15 minutes.

--verify-app-server
    Start Codex app-server and call thread/list in both state-db-only and
    scan modes to verify visibility.

--dry-run
    Print the planned repair summary without modifying files.
```

## Reading The Output

The script prints JSON. Useful fields:

| Field | Meaning |
| --- | --- |
| `selectedThreads` | Number of threads selected for repair. |
| `visibleThreads` | Number of unarchived threads after repair selection. |
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
3. Check `providerDistribution`. If your Desktop build expects a different
   exact provider string, rerun with `--provider`.
4. Check `rolloutMetaSkippedLocked`. Close processes that may hold session files
   open and rerun the repair.
5. Check for old after-exit scripts or manual sync jobs that rewrite
   `.codex-global-state.json` after the repair.
6. If sessions are archived, use `--target all --unarchive`.

## Repository Layout

```text
SKILL.md
agents/openai.yaml
scripts/repair_codex_history_visibility.py
```

Only these files are required for the skill package.

## Contributing

Issues and pull requests are welcome. Please keep changes focused on local
Codex Desktop history repair, avoid adding telemetry or network calls, and do
not include personal `.codex` data in examples or tests.
