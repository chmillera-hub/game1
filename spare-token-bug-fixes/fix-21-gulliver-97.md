# Fix 21: Gulliver: inspect quietly clamps --limit and --scan values outside the allowed range

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Gulliver
- Bug report title: inspect: refuse --limit and --scan outside the range MCP already enforces, instead of quietly clamping
- Bug report: number 97 ([open the bug report](https://github.com/laaielichter/Gulliver/issues/97))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/21-gulliver-97.patch](fixes/21-gulliver-97.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/21-gulliver-97.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-21-gulliver-97.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-21-gulliver-97.html

## The bug

gulliver inspect --limit 0 lists 1 table and --limit 500 lists at most 200 and --sensitive --scan 5000 scans 1000 rows and --scan -5 scans nothing. No message tells the person that the number was changed. The MCP tool already refuses the same values.

## The fix

core.inspect and guard.inspect_sensitive now return status error with a next step for a limit outside 1 to 200 and a scan value outside 0 to 1000. The limit is still ignored when a table is named and --scan 0 still means no value scan. A new test covers the functions and the command line. A changelog line is included.

## Files changed

- CHANGELOG.md
- src/gulliver/core.py
- src/gulliver/guard.py
- tests/test_cli_and_mcp.py

## How to use the fix

1. Get a copy of the project laaielichter/Gulliver.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 21-gulliver-97.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 97.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 10 and fix 21 both add text at the same spots in CHANGELOG.md and tests/test_cli_and_mcp.py. Applying both needs a small manual merge. The bug report had one comment on 9 November 2026 and the chatbot could not read comments.

## Search words

gulliver inspect --limit --scan clamp silently out of range 1-200 0-1000 inspect_sensitive status error

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 5e325bb..61ce753 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -34,6 +34,7 @@
 - @abu-tahir-0 for five fixes on their first day: strict `check --range` bounds (#85), one row-count history per connection (#86), whole-number and non-boolean budget limits (#84), refusing unknown `gulliver.toml` sections (#83) and GV013 for leading `_` (#82).
 
 ### Fixed
+- `inspect --limit N` refuses a value outside 1-200 and `inspect --sensitive --scan N` refuses a value outside 0-1000 with `status: error` and a `next_step` (exit 1), the ranges the MCP tool already enforces, instead of quietly clamping them. `--limit` is still ignored when a table is named and `--scan 0` still means no value scan (#97).
 - `spend --days N`, `calibration --days N` and `top --limit N` refuse a value below 1 with `status: error` and a `next_step`, and exit 1 instead of quietly reporting an empty or off-by-one window. `top --analyze` refuses a negative value too, while `--analyze 0` still lists the groups without analysing them (#92).
 - `check --range` refuses `nan`, infinite and non-numeric bounds and an inverted `min > max` before any query runs, naming the column. Before, `nan` / `inf` reached the engine as column names and an inverted range silently failed every row (#74, #85).
 - `check --max-change` keys the row-count history on the resolved connection name, so a check with and without `-c default` shares one history. Histories saved under the old key are still read and migrated (#75, #86).
diff --git a/src/gulliver/core.py b/src/gulliver/core.py
index 116fb92..db4c790 100644
--- a/src/gulliver/core.py
+++ b/src/gulliver/core.py
@@ -112,8 +112,25 @@ def status(settings: Settings) -> dict[str, Any]:
 
 
 # -- inspect ---------------------------------------------------------------------------
+def _whole_number_in(value: Any, low: int, high: int) -> bool:
+    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high
+
+
+def inspect_limit_error(table: str | None, limit: Any) -> dict[str, Any] | None:
+    """The error for an `inspect` --limit outside 1-200 (the range MCP enforces), or None.
+
+    The limit only applies to the table listing, so it is not checked when a table is named."""
+    if table or _whole_number_in(limit, 1, 200):
+        return None
+    return _error("--limit must be a whole number from 1 to 200.",
+                  "Use a limit in that range, for example --limit 25.")
+
+
 def inspect(settings: Settings, connection: str | None = None, table: str | None = None,
             limit: int = 25) -> dict[str, Any]:
+    refused = inspect_limit_error(table, limit)
+    if refused:
+        return refused
     try:
         with _engine(settings, connection) as (conn, engine):
             if table:
diff --git a/src/gulliver/guard.py b/src/gulliver/guard.py
index 40fd334..6b94a6a 100644
--- a/src/gulliver/guard.py
+++ b/src/gulliver/guard.py
@@ -1170,10 +1170,17 @@ def inspect_sensitive(settings: Settings, connection: str | None = None, table:
                       limit: int = 25, scan_rows: int = 0) -> dict[str, Any]:
     """Sensitive columns per table: by name and cached value tags (free), or by sampling text values
     (scan_rows > 0, one budget-gated LIMIT query per table; values never leave Gulliver, only tags)."""
-    from .core import _engine, _error
+    from .core import _engine, _error, _whole_number_in, inspect_limit_error
     from .engines import EngineError, dialect_for
     from .features import Blocked, _gated_run
 
+    refused = inspect_limit_error(table, limit)
+    if refused:
+        return refused
+    if not _whole_number_in(scan_rows, 0, 1000):
+        return _error("--scan must be a whole number from 0 to 1000.",
+                      "Use a row count in that range, for example --scan 200, or 0 for no value scan.")
+
     try:
         with _engine(settings, connection) as (conn, engine):
             if table:
diff --git a/tests/test_cli_and_mcp.py b/tests/test_cli_and_mcp.py
index 7e1d67f..1900fdc 100644
--- a/tests/test_cli_and_mcp.py
+++ b/tests/test_cli_and_mcp.py
@@ -97,3 +97,29 @@ def test_cli_translate_output_file(tmp_path, capsys):
     data = json.loads(capsys.readouterr().out)
     assert data["warnings"]  # still printed
     assert out.read_text(encoding="utf-8") == data["sql"]
+
+
+def test_inspect_refuses_limit_and_scan_outside_the_mcp_range(settings, demo_db, capsys):
+    from gulliver import core
+    from gulliver.guard import inspect_sensitive
+
+    for limit in (0, -1, 201, 500):
+        res = core.inspect(settings, limit=limit)
+        assert res["status"] == "error" and "--limit" in res["error"] and res["next_step"], limit
+        res = inspect_sensitive(settings, limit=limit)
+        assert res["status"] == "error" and "--limit" in res["error"], limit
+        assert main(["--dsn", demo_db, "inspect", "--limit", str(limit), "--json"]) == 1
+        assert "--limit" in json.loads(capsys.readouterr().out)["error"]
+    for scan in (-5, 1001, 5000):
+        res = inspect_sensitive(settings, scan_rows=scan)
+        assert res["status"] == "error" and "--scan" in res["error"] and res["next_step"], scan
+        assert main(["--dsn", demo_db, "inspect", "--sensitive", f"--scan={scan}", "--json"]) == 1
+        assert "--scan" in json.loads(capsys.readouterr().out)["error"]
+
+    # The edges of the range stay valid, and --limit is still ignored when a table is named.
+    for limit in (1, 200):
+        assert core.inspect(settings, limit=limit)["status"] == "ok"
+    assert core.inspect(settings, table="events", limit=0)["status"] == "ok"
+    assert inspect_sensitive(settings, scan_rows=0)["status"] == "ok"
+    assert main(["--dsn", demo_db, "inspect", "events", "--limit", "500", "--json"]) == 0
+    assert json.loads(capsys.readouterr().out)["status"] == "ok"
`````

[Back to the shelf](README.md)
