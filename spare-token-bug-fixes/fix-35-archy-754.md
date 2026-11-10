# Fix 35: Archy: the trend table shows UTC times with no zone so the times read as local time

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(trend): the `when` column shows UTC times with the zone stripped, so they read as local time
- Bug report: number 754 ([open the bug report](https://github.com/hslee16/Archy/issues/754))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/35-archy-754.patch](fixes/35-archy-754.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/35-archy-754.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-35-archy-754.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-35-archy-754.html

## The bug

History rows are stored in UTC. The text trend table and the HTML trend table cut the Z off the time and the column header only said when. A reader takes the times as local time and can look at the wrong session or commit.

## The fix

The column header becomes when (UTC) in src/archy/trend.py and in src/archy/render.py. The text column was already wide enough so the layout does not move. tests/test_trend.py and tests/test_render.py each gain one test with a fixed timestamp.

## Files changed

- src/archy/render.py
- src/archy/trend.py
- tests/test_render.py
- tests/test_trend.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 35-archy-754.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 754.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report offers two fixes: label the column or print the Z after each time. The chatbot chose the label. The maintainer may prefer the other one.

## Search words

Archy trend when column UTC zone stripped local time history.jsonl render trend table header

## The full patch

`````diff
diff --git a/src/archy/render.py b/src/archy/render.py
index 4e9f23c..983023c 100644
--- a/src/archy/render.py
+++ b/src/archy/render.py
@@ -412,7 +412,7 @@ def _chart(label: str, values: list[float | None]) -> str:
 
 def _trend_table(window: list[HistoryRow]) -> str:
     head = (
-        "<tr><th>when</th><th>commit</th><th>score</th><th>mod</th><th>acy</th>"
+        "<tr><th>when (UTC)</th><th>commit</th><th>score</th><th>mod</th><th>acy</th>"
         "<th>dep</th><th>eq</th><th>cpx</th></tr>"
     )
     rows: list[str] = []
diff --git a/src/archy/trend.py b/src/archy/trend.py
index 1d13f1b..f0a7809 100644
--- a/src/archy/trend.py
+++ b/src/archy/trend.py
@@ -26,7 +26,8 @@ def render_text(rows: list[HistoryRow], *, last_n: int) -> str:
         "",
         f"score: {spark}  ({window[0].overall:.3f} -> {window[-1].overall:.3f})",
         "",
-        f"{'when':<17} {'commit':<8} {'score':>6} "
+        # Rows are stored in UTC; the label says so, the same on every machine.
+        f"{'when (UTC)':<17} {'commit':<8} {'score':>6} "
         f"{'mod':>5} {'acy':>5} {'dep':>5} {'eq':>5} {'cpx':>5}",
         f"{'-' * 17} {'-' * 8} {'-' * 6} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 5}",
     ]
diff --git a/tests/test_render.py b/tests/test_render.py
index 3c23025..498c9fc 100644
--- a/tests/test_render.py
+++ b/tests/test_render.py
@@ -188,6 +188,13 @@ def test_trend_without_history_explains_how_to_record() -> None:
     assert "archy score --record" in html
 
 
+def test_trend_table_says_the_when_column_is_utc() -> None:
+    html = render_trend_html([_row("2026-01-02T03:04:05Z", 0.5)], last_n=10)
+
+    assert "<th>when (UTC)</th>" in html
+    assert "2026-01-02 03:04" in html
+
+
 def test_trend_plots_every_axis() -> None:
     rows = [_row("2026-01-01T00:00:00Z", 0.5), _row("2026-01-02T00:00:00Z", 0.6)]
     html = render_trend_html(rows, last_n=10)
diff --git a/tests/test_trend.py b/tests/test_trend.py
index 2133959..f3ed827 100644
--- a/tests/test_trend.py
+++ b/tests/test_trend.py
@@ -87,6 +87,16 @@ def test_render_text_includes_table_columns_and_sparkline():
         assert column in out
 
 
+def test_render_text_says_the_when_column_is_utc():
+    """Rows are stored in UTC with a Z; the table drops the Z, so the header names the zone."""
+    out = render_text([_row(0.5, when="2026-01-02T03:04:05Z")], last_n=10)
+    header = next(line for line in out.splitlines() if "commit" in line)
+    assert header.startswith("when (UTC)")
+    row = next(line for line in out.splitlines() if line.startswith("2026-01-02 03:04"))
+    # The header and the row still line up on the commit column.
+    assert header.index("commit") == row.index("abc1234")
+
+
 def test_render_text_truncates_to_last_n():
     rows = [_row(i / 10) for i in range(20)]
     out = render_text(rows, last_n=5)
`````

[Back to the shelf](README.md)
