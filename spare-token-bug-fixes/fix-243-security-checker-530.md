# Fix 243: security-checker: no test covers a quota record that cannot be written

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(observability): quota.py の consume で未テストの分岐をテストする（2 行）
- Bug report: number 530 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/530))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/243-security-checker-530.patch](fixes/243-security-checker-530.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/243-security-checker-530.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-243-security-checker-530.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-243-security-checker-530.html

## The bug

QuotaStore.consume in src/security_checker/observability/quota.py keeps going and records a warning when the quota file cannot be written. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_quota_consume_write_error.py puts the quota file under a path whose parent is a plain file and expects the count back plus one recorded error. A paired test checks a normal write.

## Files changed

- tests/unit/test_quota_consume_write_error.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 243-security-checker-530.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 530.

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

security-checker quota QuotaStore consume OSError write failure errors untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_quota_consume_write_error.py b/tests/unit/test_quota_consume_write_error.py
new file mode 100644
index 0000000..da2d021
--- /dev/null
+++ b/tests/unit/test_quota_consume_write_error.py
@@ -0,0 +1,27 @@
+"""クォータの記録に書けなくても実行を止めず、警告を残すこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+from security_checker.observability.quota import QuotaStore
+
+
+def test_write_failure_is_recorded_and_the_count_is_still_returned(tmp_path: Path) -> None:
+    blocker = tmp_path / "not-a-directory"
+    blocker.write_text("", encoding="utf-8")
+    # 親がファイルなので mkdir も書き込みも OSError になる
+    store = QuotaStore(blocker / "quota.json")
+
+    assert store.consume("r1") == 1
+    assert len(store.errors) == 1
+    assert "に書けません" in store.errors[0]
+
+
+def test_successful_write_leaves_no_error(tmp_path: Path) -> None:
+    """対になるケース. 書ければ警告は無く、累計が増える."""
+    store = QuotaStore(tmp_path / "cache" / "quota.json")
+
+    assert store.consume("r1") == 1
+    assert store.consume("r1", 2) == 3
+    assert store.errors == []
`````

[Back to the shelf](README.md)
