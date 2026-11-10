# Fix 151: security-checker: no test covers a missing bundled rules folder

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(rules): __init__.py の bundled_semgrep_rules で未テストの分岐をテストする（1 行）
- Bug report: number 570 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/570))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/151-security-checker-570.patch](fixes/151-security-checker-570.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/151-security-checker-570.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-151-security-checker-570.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-151-security-checker-570.html

## The bug

bundled_semgrep_rules in src/security_checker/rules/__init__.py returns an empty list when the bundled rules folder does not exist. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_rules_bundled_dir_missing.py points the folder at a missing path and expects an empty list. A second test fills a folder and expects the sorted names of the .yml files only.

## Files changed

- tests/unit/test_rules_bundled_dir_missing.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 151-security-checker-570.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 570.

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

security-checker rules bundled_semgrep_rules SEMGREP_DIR missing directory empty list untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_rules_bundled_dir_missing.py b/tests/unit/test_rules_bundled_dir_missing.py
new file mode 100644
index 0000000..47c7282
--- /dev/null
+++ b/tests/unit/test_rules_bundled_dir_missing.py
@@ -0,0 +1,27 @@
+"""bundled_semgrep_rules: 同梱ルールのディレクトリが無ければ空のリストを返すこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker import rules
+
+
+def test_missing_rules_directory_gives_an_empty_list(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
+) -> None:
+    monkeypatch.setattr(rules, "SEMGREP_DIR", tmp_path / "absent")
+
+    assert rules.bundled_semgrep_rules() == []
+
+
+def test_rule_names_are_the_sorted_file_stems(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
+) -> None:
+    for name in ("zeta.yml", "alpha.yml", "notes.txt"):
+        (tmp_path / name).write_text("", encoding="utf-8")
+    monkeypatch.setattr(rules, "SEMGREP_DIR", tmp_path)
+
+    assert rules.bundled_semgrep_rules() == ["alpha", "zeta"]
`````

[Back to the shelf](README.md)
