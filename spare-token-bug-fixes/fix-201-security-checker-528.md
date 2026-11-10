# Fix 201: security-checker: no test covers the default place of the quota record

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(observability): quota.py の default_quota_path で未テストの分岐をテストする（3 行）
- Bug report: number 528 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/528))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/201-security-checker-528.patch](fixes/201-security-checker-528.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/201-security-checker-528.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-201-security-checker-528.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-201-security-checker-528.html

## The bug

default_quota_path in src/security_checker/observability/quota.py puts the quota file under XDG_CACHE_HOME or under .cache in the home folder. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_quota_default_path.py checks the path with the variable set and with the variable unset and with the variable empty.

## Files changed

- tests/unit/test_quota_default_path.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 201-security-checker-528.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 528.

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

security-checker quota default_quota_path XDG_CACHE_HOME home .cache quota.json untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_quota_default_path.py b/tests/unit/test_quota_default_path.py
new file mode 100644
index 0000000..84dadd2
--- /dev/null
+++ b/tests/unit/test_quota_default_path.py
@@ -0,0 +1,28 @@
+"""quota.default_quota_path: XDG_CACHE_HOME があればその下、無ければ ~/.cache の下."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.observability.quota import QUOTA_FILENAME, default_quota_path
+
+
+def test_xdg_cache_home_is_used_when_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
+
+    assert default_quota_path() == tmp_path / "security-checker" / QUOTA_FILENAME
+
+
+@pytest.mark.parametrize("unset", [True, False], ids=["unset", "empty"])
+def test_home_cache_is_the_fallback(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unset: bool
+) -> None:
+    if unset:
+        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
+    else:
+        monkeypatch.setenv("XDG_CACHE_HOME", "")
+    monkeypatch.setattr(Path, "home", lambda: tmp_path)
+
+    assert default_quota_path() == tmp_path / ".cache" / "security-checker" / QUOTA_FILENAME
`````

[Back to the shelf](README.md)
