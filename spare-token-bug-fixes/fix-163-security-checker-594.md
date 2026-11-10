# Fix 163: security-checker: no test covers a cassette file with another version

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(testing): cassette.py の _load で未テストの分岐をテストする（1 行）
- Bug report: number 594 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/594))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/163-security-checker-594.patch](fixes/163-security-checker-594.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/163-security-checker-594.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-163-security-checker-594.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-163-security-checker-594.html

## The bug

CassetteProvider._load in src/security_checker/testing/cassette.py raises an error for a cassette file whose version differs. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_cassette_load_version.py expects ValueError for another version and for a missing version and expects a file with the current version to load.

## Files changed

- tests/unit/test_cassette_load_version.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 163-security-checker-594.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 594.

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

security-checker testing cassette CassetteProvider _load version mismatch ValueError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_cassette_load_version.py b/tests/unit/test_cassette_load_version.py
new file mode 100644
index 0000000..18b5168
--- /dev/null
+++ b/tests/unit/test_cassette_load_version.py
@@ -0,0 +1,34 @@
+"""CassetteProvider._load: 版の違うカセットは読み込まずにエラーにすること."""
+
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+import pytest
+
+from security_checker.testing.cassette import CASSETTE_VERSION, CassetteProvider
+
+
+def test_cassette_with_another_version_is_rejected(tmp_path: Path) -> None:
+    path = tmp_path / "cassette.json"
+    path.write_text(json.dumps({"version": "not-a-version", "entries": {}}), encoding="utf-8")
+
+    with pytest.raises(ValueError, match="カセットの版が違います"):
+        CassetteProvider(path)
+
+
+def test_cassette_without_a_version_is_rejected(tmp_path: Path) -> None:
+    path = tmp_path / "cassette.json"
+    path.write_text(json.dumps({"entries": {}}), encoding="utf-8")
+
+    with pytest.raises(ValueError, match="cassette.json"):
+        CassetteProvider(path)
+
+
+def test_cassette_with_the_current_version_loads(tmp_path: Path) -> None:
+    """対になるケース. 版が合えばエラーにならない."""
+    path = tmp_path / "cassette.json"
+    path.write_text(json.dumps({"version": CASSETTE_VERSION, "entries": {}}), encoding="utf-8")
+
+    assert CassetteProvider(path).path == path
`````

[Back to the shelf](README.md)
