# Fix 188: security-checker: an inline comment after a tab stays in the ignore pattern

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(policy): .security-checker-ignore の行内コメントが「 #」でしか切れず、タブの後の # がパターンに残る
- Bug report: number 446 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/446))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/188-security-checker-446.patch](fixes/188-security-checker-446.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/188-security-checker-446.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-188-security-checker-446.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-188-security-checker-446.html

## The bug

parse_ignore_file in src/security_checker/policy/ignore.py cut inline comments only at a space followed by #. A line like tests/** then a tab then # fixtures kept the comment as part of the pattern and the pattern matched nothing.

## The fix

The parser now cuts at any blank character (space or tab) followed by #. The docstring states the rule. A new file tests/unit/test_ignore_file_inline_comment.py checks four spellings of the comment and a # with no blank before and a rule: line and a full-line comment.

## Files changed

- src/security_checker/policy/ignore.py
- tests/unit/test_ignore_file_inline_comment.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 188-security-checker-446.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 446.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report also asks the maintainers to decide whether a backslash before # should give a literal #. The patch does not add that form and a # with no blank before stays part of the pattern as before. The chatbot ran a scratch copy of the split on seven lines. The chatbot did not run the project's tests.

## Search words

security-checker .security-checker-ignore parse_ignore_file inline comment tab # split whitespace pattern

## The full patch

`````diff
diff --git a/src/security_checker/policy/ignore.py b/src/security_checker/policy/ignore.py
index 07632fb..f934676 100644
--- a/src/security_checker/policy/ignore.py
+++ b/src/security_checker/policy/ignore.py
@@ -84,12 +84,22 @@ def rule_matches(rule: str, candidate: Candidate) -> bool:
     return rule in ("*", candidate.rule_id, f"{candidate.scanner}/{candidate.rule_id}")
 
 
+#: 行内コメントの始まり. 空白類に続く `#`
+_INLINE_COMMENT = re.compile(r"\s+#")
+
+
 def parse_ignore_file(text: str, source: str = IGNORE_FILENAME) -> tuple[IgnoreFile, list[str]]:
-    """内容を解釈する. 解釈できない行は黙って捨てず、警告にする."""
+    """内容を解釈する. 解釈できない行は黙って捨てず、警告にする.
+
+    行内コメントは、空白類 (スペースやタブ) に続く `#` から行末まで。
+    空白を挟まない `#` (`a#b`) はパターンの一部として残す。
+    """
     ignore = IgnoreFile()
     warnings: list[str] = []
     for number, raw in enumerate(text.splitlines(), start=1):
-        line = raw.split(" #", 1)[0].strip() if not raw.lstrip().startswith("#") else ""
+        if raw.lstrip().startswith("#"):
+            continue
+        line = _INLINE_COMMENT.split(raw, maxsplit=1)[0].strip()
         if not line:
             continue
         if line.startswith("!"):
diff --git a/tests/unit/test_ignore_file_inline_comment.py b/tests/unit/test_ignore_file_inline_comment.py
new file mode 100644
index 0000000..ffac45e
--- /dev/null
+++ b/tests/unit/test_ignore_file_inline_comment.py
@@ -0,0 +1,45 @@
+""".security-checker-ignore の行内コメントが、タブ区切りでも落ちること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.policy.ignore import parse_ignore_file
+
+
+@pytest.mark.parametrize(
+    "line",
+    [
+        "tests/**\t# fixtures",
+        "tests/** # fixtures",
+        "tests/**  \t # fixtures",
+        "tests/**\t#fixtures",
+    ],
+)
+def test_inline_comment_after_whitespace_is_dropped(line: str) -> None:
+    ignore, warnings = parse_ignore_file(line + "\n")
+
+    assert ignore.path_patterns == ["tests/**"]
+    assert warnings == []
+
+
+def test_hash_without_whitespace_before_it_stays_in_the_pattern() -> None:
+    ignore, _ = parse_ignore_file("docs/a#b.md\n")
+
+    assert ignore.path_patterns == ["docs/a#b.md"]
+
+
+def test_inline_comment_on_a_rule_line_is_dropped() -> None:
+    ignore, warnings = parse_ignore_file("rule: python.lang.eval\ttests/**\t# 理由\n")
+
+    assert len(ignore.rules) == 1
+    assert ignore.rules[0].rule == "python.lang.eval"
+    assert ignore.rules[0].paths == ("tests/**",)
+    assert warnings == []
+
+
+def test_full_line_comment_is_skipped() -> None:
+    ignore, warnings = parse_ignore_file("\t# only a comment\n")
+
+    assert ignore.path_patterns == []
+    assert warnings == []
`````

[Back to the shelf](README.md)
