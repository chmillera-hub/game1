# Fix 215: security-checker: no test covers an id that matches no candidate or several candidates in explain

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(observability): explain.py の explain で未テストの分岐をテストする（3 行）
- Bug report: number 526 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/526))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/215-security-checker-526.patch](fixes/215-security-checker-526.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/215-security-checker-526.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-215-security-checker-526.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-215-security-checker-526.html

## The bug

explain in src/security_checker/observability/explain.py raises ConfigError when the id matches several candidates. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_explain_candidate_lookup.py checks an unknown id and a prefix that matches two candidates and an exact id and a unique prefix.

## Files changed

- tests/unit/test_explain_candidate_lookup.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 215-security-checker-526.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 526.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report also names two lines that skip an unreadable trace file. The new tests do not cover those two lines. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker explain finding id prefix ambiguous several candidates ConfigError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_explain_candidate_lookup.py b/tests/unit/test_explain_candidate_lookup.py
new file mode 100644
index 0000000..95b3e33
--- /dev/null
+++ b/tests/unit/test_explain_candidate_lookup.py
@@ -0,0 +1,32 @@
+"""explain.explain: ID で候補を引けない・1 つに決まらないときは ConfigError になること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.observability.explain import explain
+from tests.factories import make_candidate, make_report
+
+REPORT = make_report([make_candidate("abc1", line=1), make_candidate("abc2", line=2)])
+
+
+def test_unknown_id_is_a_config_error() -> None:
+    with pytest.raises(ConfigError, match="候補はこのレポートにありません"):
+        explain(REPORT, "zzz")
+
+
+def test_prefix_that_matches_several_candidates_is_a_config_error() -> None:
+    with pytest.raises(ConfigError, match="複数あります: abc1, abc2"):
+        explain(REPORT, "abc")
+
+
+def test_exact_id_is_found() -> None:
+    """対になるケース. ID が 1 つに決まれば、その候補を返す."""
+    assert explain(REPORT, "abc2").candidate.id == "abc2"
+
+
+def test_unique_prefix_is_found() -> None:
+    report = make_report([make_candidate("abc1", line=1), make_candidate("xyz9", line=2)])
+
+    assert explain(report, "xy").candidate.id == "xyz9"
`````

[Back to the shelf](README.md)
