# Fix 171: security-checker: no test covers semgrep output whose results field is not a list

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): semgrep.py の parse_semgrep で未テストの分岐をテストする（1 行）
- Bug report: number 589 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/589))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/171-security-checker-589.patch](fixes/171-security-checker-589.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/171-security-checker-589.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-171-security-checker-589.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-171-security-checker-589.html

## The bug

parse_semgrep in src/security_checker/scanners/semgrep.py refuses output whose results field is not a list. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_semgrep_parse_results_shape.py expects UnparseableOutputError for three results values that are not lists and for a missing results field and expects an empty list to give no candidates and no warnings.

## Files changed

- tests/unit/test_semgrep_parse_results_shape.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 171-security-checker-589.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 589.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report shows the line returning a warning. The newest code raises UnparseableOutputError there and the test follows the newest code. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker semgrep parse_semgrep results not a list UnparseableOutputError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_semgrep_parse_results_shape.py b/tests/unit/test_semgrep_parse_results_shape.py
new file mode 100644
index 0000000..5df5fd8
--- /dev/null
+++ b/tests/unit/test_semgrep_parse_results_shape.py
@@ -0,0 +1,26 @@
+"""parse_semgrep: results が配列でない出力は「解釈できない」として扱うこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.scanners.base import UnparseableOutputError
+from security_checker.scanners.semgrep import parse_semgrep
+
+
+@pytest.mark.parametrize("results", [{"check_id": "x"}, "text", 3])
+def test_results_that_is_not_a_list_is_unparseable(tmp_path: Path, results: object) -> None:
+    with pytest.raises(UnparseableOutputError, match="results が配列ではありません"):
+        parse_semgrep({"results": results}, tmp_path)
+
+
+def test_missing_results_is_unparseable(tmp_path: Path) -> None:
+    with pytest.raises(UnparseableOutputError, match="results フィールドがありません"):
+        parse_semgrep({"errors": []}, tmp_path)
+
+
+def test_empty_results_gives_no_candidates_and_no_warnings(tmp_path: Path) -> None:
+    """対になるケース. 空の配列は正常な「検出なし」."""
+    assert parse_semgrep({"results": []}, tmp_path) == ([], [])
`````

[Back to the shelf](README.md)
