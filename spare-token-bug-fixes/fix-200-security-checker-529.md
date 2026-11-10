# Fix 200: security-checker: no test covers the day boundary helper of the quota record

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(observability): quota.py の _today で未テストの分岐をテストする（1 行）
- Bug report: number 529 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/529))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/200-security-checker-529.patch](fixes/200-security-checker-529.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/200-security-checker-529.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-200-security-checker-529.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-200-security-checker-529.html

## The bug

_today in src/security_checker/observability/quota.py returns the current date in UTC. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_quota_today.py expects a date that lies between two UTC readings taken right before and right after the call.

## Files changed

- tests/unit/test_quota_today.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 200-security-checker-529.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 529.

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

security-checker quota _today UTC date untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_quota_today.py b/tests/unit/test_quota_today.py
new file mode 100644
index 0000000..51c66a4
--- /dev/null
+++ b/tests/unit/test_quota_today.py
@@ -0,0 +1,18 @@
+"""quota._today: 日付の区切りは UTC であること."""
+
+from __future__ import annotations
+
+from datetime import UTC, date, datetime, timedelta
+
+from security_checker.observability.quota import _today
+
+
+def test_today_is_a_date_in_utc() -> None:
+    before = datetime.now(UTC).date()
+    today = _today()
+    after = datetime.now(UTC).date()
+
+    assert type(today) is date
+    # 実行中に UTC の日付が変わっても落ちないよう、前後で挟む
+    assert before <= today <= after
+    assert after - before <= timedelta(days=1)
`````

[Back to the shelf](README.md)
