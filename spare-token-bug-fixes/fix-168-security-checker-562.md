# Fix 168: security-checker: no test covers the stop reason and the trace folder in the report footer

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(report): markdown.py の _footer で未テストの分岐をテストする（2 行）
- Bug report: number 562 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/562))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/168-security-checker-562.patch](fixes/168-security-checker-562.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/168-security-checker-562.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-168-security-checker-562.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-168-security-checker-562.html

## The bug

_footer in src/security_checker/report/markdown.py adds one line when the run stopped early and one line with the trace folder. No test ran those two lines.

## The fix

Tests only. A new file tests/unit/test_markdown_footer_notes.py expects the stop reason line and the trace folder line and expects neither line for an ordinary run.

## Files changed

- tests/unit/test_markdown_footer_notes.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 168-security-checker-562.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 562.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker report markdown _footer stopped_reason trace_dir untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_markdown_footer_notes.py b/tests/unit/test_markdown_footer_notes.py
new file mode 100644
index 0000000..3a8f58f
--- /dev/null
+++ b/tests/unit/test_markdown_footer_notes.py
@@ -0,0 +1,27 @@
+"""report.md のフッタ: 途中停止の理由と監査証跡の場所を載せること."""
+
+from __future__ import annotations
+
+from security_checker.report.markdown import _footer
+from tests.factories import make_candidate, make_report
+
+
+def test_footer_shows_why_the_run_stopped() -> None:
+    report = make_report([make_candidate()], stopped_reason="予算の上限に達しました")
+
+    assert "⚠️ 途中で停止しました: 予算の上限に達しました" in _footer(report)
+
+
+def test_footer_shows_the_trace_directory() -> None:
+    report = make_report([make_candidate()], trace_dir=".security-checker/trace/R1")
+
+    assert "監査証跡: `.security-checker/trace/R1`" in _footer(report)
+
+
+def test_footer_has_neither_line_for_an_ordinary_run() -> None:
+    """対になるケース. 停止も証跡も無ければどちらの行も出ない."""
+    text = "\n".join(_footer(make_report([make_candidate()])))
+
+    assert "途中で停止しました" not in text
+    assert "監査証跡" not in text
+    assert "run `R1`" in text
`````

[Back to the shelf](README.md)
