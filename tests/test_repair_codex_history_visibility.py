import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "repair_codex_history_visibility.py"
SPEC = importlib.util.spec_from_file_location("repair_codex_history_visibility", SCRIPT_PATH)
repair = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(repair)


class RepairCodexHistoryVisibilityTest(unittest.TestCase):
    def test_project_roots_are_derived_from_visible_threads_by_default(self) -> None:
        state = {
            "electron-saved-workspace-roots": [
                r"D:\object\old-project",
                r"D:\object\plan-a",
            ]
        }
        threads = [{"cwd": r"D:\object\plan-a\backend"}]

        roots = repair.build_project_roots(state, threads, [])

        self.assertIn(r"D:\object\plan-a", roots)
        self.assertNotIn(r"D:\object\old-project", roots)

    def test_existing_project_roots_can_be_kept_explicitly(self) -> None:
        state = {"electron-saved-workspace-roots": [r"D:\object\old-project"]}
        threads = [{"cwd": r"D:\object\plan-a\backend"}]

        roots = repair.build_project_roots(state, threads, [], keep_existing_roots=True)

        self.assertIn(r"D:\object\old-project", roots)
        self.assertIn(r"D:\object\plan-a", roots)

    def test_repair_database_preserves_archived_at_when_not_unarchiving(self) -> None:
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                rollout_path TEXT,
                cwd TEXT,
                title TEXT,
                updated_at INTEGER,
                updated_at_ms INTEGER,
                created_at INTEGER,
                created_at_ms INTEGER,
                archived INTEGER,
                archived_at INTEGER,
                source TEXT,
                thread_source TEXT,
                model_provider TEXT
            )
            """
        )
        con.execute(
            """
            INSERT INTO threads
              (id, rollout_path, cwd, title, updated_at, updated_at_ms, created_at, created_at_ms,
               archived, archived_at, source, thread_source, model_provider)
            VALUES
              ('thread-1', 'rollout.jsonl', 'D:\\object\\plan-a', 'Title', 10, 10000, 1, 1000,
               1, 99999, 'cli', 'user', 'OpenAI')
            """
        )

        threads = repair.fetch_threads(con, "all")
        repair.repair_database(con, threads, "ccswitch", "vscode", "user", unarchive=False, dry_run=False)

        row = con.execute("SELECT archived, archived_at FROM threads WHERE id = 'thread-1'").fetchone()
        self.assertEqual(row["archived"], 1)
        self.assertEqual(row["archived_at"], 99999)

    def test_auto_metadata_uses_latest_visible_thread(self) -> None:
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                updated_at INTEGER,
                updated_at_ms INTEGER,
                archived INTEGER,
                source TEXT,
                model_provider TEXT
            )
            """
        )
        con.executemany(
            """
            INSERT INTO threads
              (id, updated_at, updated_at_ms, archived, source, model_provider)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("old", 1, 1000, 0, "cli", "OpenAI"),
                ("new", 2, 2000, 0, "vscode", "ccswitch"),
                ("archived-newer", 3, 3000, 1, "cli", "OpenAI"),
            ],
        )

        provider, source = repair.resolve_provider_and_source(con, "auto", "auto")

        self.assertEqual(provider, "ccswitch")
        self.assertEqual(source, "vscode")

    def test_protect_state_default_is_disabled(self) -> None:
        with patch.object(sys, "argv", ["repair"]):
            args = repair.parse_args()

        self.assertEqual(args.protect_state_minutes, 0)

    def test_verify_timeout_default_allows_slow_scan_mode(self) -> None:
        with patch.object(sys, "argv", ["repair"]):
            args = repair.parse_args()

        self.assertGreaterEqual(args.verify_timeout_seconds, 90)


if __name__ == "__main__":
    unittest.main()
