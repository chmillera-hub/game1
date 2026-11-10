# Fix 10: Gulliver: check accepts a negative --min-rows and a negative or NaN or infinite --max-change

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Gulliver
- Bug report title: check: refuse a negative --min-rows and a negative, NaN or infinite --max-change
- Bug report: number 106 ([open the bug report](https://github.com/laaielichter/Gulliver/issues/106))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/10-gulliver-106.patch](fixes/10-gulliver-106.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/10-gulliver-106.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-10-gulliver-106.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-10-gulliver-106.html

## The bug

The command gulliver check accepts --min-rows -5 and the check can then never fail. --max-change -5 always fails even when the row count did not change. --max-change nan can never fail.

## The fix

parse_spec in src/gulliver/checks.py now raises ValueError for a negative min_rows and for a max_change_pct that is negative or NaN or infinite. The check command turns the error into status error with exit code 1 before any query runs. Zero stays valid for both. New tests go through parse_spec and through the command line. A changelog line is included.

## Files changed

- CHANGELOG.md
- src/gulliver/checks.py
- tests/test_checks.py
- tests/test_cli_and_mcp.py

## How to use the fix

1. Get a copy of the project laaielichter/Gulliver.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 10-gulliver-106.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 106.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 10 and fix 21 both add text at the same spots in CHANGELOG.md and tests/test_cli_and_mcp.py. Applying both needs a small manual merge.

## Search words

gulliver check --min-rows negative --max-change nan inf parse_spec CheckSpec threshold validation

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 5e325bb..911e36f 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -34,6 +34,7 @@
 - @abu-tahir-0 for five fixes on their first day: strict `check --range` bounds (#85), one row-count history per connection (#86), whole-number and non-boolean budget limits (#84), refusing unknown `gulliver.toml` sections (#83) and GV013 for leading `_` (#82).
 
 ### Fixed
+- `check --min-rows` refuses a negative number, and `check --max-change` refuses a negative, `nan` or infinite number, with `status: error` and exit 1 before any query runs. Before, a negative `--min-rows` or a `nan` `--max-change` could never fail and a negative `--max-change` always failed. `0` stays valid for both (#106).
 - `spend --days N`, `calibration --days N` and `top --limit N` refuse a value below 1 with `status: error` and a `next_step`, and exit 1 instead of quietly reporting an empty or off-by-one window. `top --analyze` refuses a negative value too, while `--analyze 0` still lists the groups without analysing them (#92).
 - `check --range` refuses `nan`, infinite and non-numeric bounds and an inverted `min > max` before any query runs, naming the column. Before, `nan` / `inf` reached the engine as column names and an inverted range silently failed every row (#74, #85).
 - `check --max-change` keys the row-count history on the resolved connection name, so a check with and without `-c default` shares one history. Histories saved under the old key are still read and migrated (#75, #86).
diff --git a/src/gulliver/checks.py b/src/gulliver/checks.py
index 3e664d7..26f7a59 100644
--- a/src/gulliver/checks.py
+++ b/src/gulliver/checks.py
@@ -36,6 +36,10 @@ def parse_spec(unique: list[str] | None = None, not_null: list[str] | None = Non
                max_change_pct: float | None = None) -> CheckSpec:
     """Parse CLI-style strings: unique 'id' or 'a,b'; accepted 'status=new|paid'; range 'amount=0:1000';
     fresh 'ts=24h'."""
+    if min_rows is not None and min_rows < 0:
+        raise ValueError(f"--min-rows must be 0 or more, got {min_rows}")
+    if max_change_pct is not None and not (math.isfinite(max_change_pct) and max_change_pct >= 0):
+        raise ValueError(f"--max-change must be a finite number of 0 or more, got {max_change_pct}")
     spec = CheckSpec(min_rows=min_rows, max_change_pct=max_change_pct)
     for u in unique or []:
         spec.unique.append([c.strip() for c in u.split(",") if c.strip()])
diff --git a/tests/test_checks.py b/tests/test_checks.py
index 7bd5004..61d21d1 100644
--- a/tests/test_checks.py
+++ b/tests/test_checks.py
@@ -27,3 +27,21 @@ def test_range_bounds_still_parse():
     assert _bounds("0:") == (0.0, None)
     assert _bounds(":10") == (None, 10.0)
     assert _bounds("5:5") == (5.0, 5.0)
+
+
+@pytest.mark.parametrize("rows", [-1, -5])
+def test_min_rows_refuses_a_negative_number(rows):
+    with pytest.raises(ValueError, match=rf"--min-rows must be 0 or more, got {rows}"):
+        parse_spec(min_rows=rows)
+
+
+@pytest.mark.parametrize("change", [-5.0, -0.1, float("nan"), float("inf"), float("-inf")])
+def test_max_change_refuses_negative_and_non_finite_numbers(change):
+    with pytest.raises(ValueError, match="--max-change must be a finite number of 0 or more"):
+        parse_spec(max_change_pct=change)
+
+
+def test_zero_thresholds_stay_valid():
+    spec = parse_spec(min_rows=0, max_change_pct=0)
+    assert spec.min_rows == 0
+    assert spec.max_change_pct == 0
diff --git a/tests/test_cli_and_mcp.py b/tests/test_cli_and_mcp.py
index 7e1d67f..a976a6c 100644
--- a/tests/test_cli_and_mcp.py
+++ b/tests/test_cli_and_mcp.py
@@ -97,3 +97,16 @@ def test_cli_translate_output_file(tmp_path, capsys):
     data = json.loads(capsys.readouterr().out)
     assert data["warnings"]  # still printed
     assert out.read_text(encoding="utf-8") == data["sql"]
+
+
+def test_cli_check_refuses_senseless_thresholds(demo_db, state, capsys):
+    refused = [("--min-rows", "-5"), ("--max-change", "-5"), ("--max-change", "nan"),
+               ("--max-change", "inf"), ("--max-change", "-inf")]
+    for flag, value in refused:
+        code = main(["--dsn", demo_db, "check", "events", "--not-null", "event_id", f"{flag}={value}", "--json"])
+        data = json.loads(capsys.readouterr().out)
+        assert code == 1, (flag, value)
+        assert data["status"] == "error" and flag in data["error"], data
+    assert main(["--dsn", demo_db, "check", "events", "--not-null", "event_id",
+                 "--min-rows", "0", "--max-change", "0", "--json"]) == 0
+    assert json.loads(capsys.readouterr().out)["status"] == "ok"
`````

[Back to the shelf](README.md)
