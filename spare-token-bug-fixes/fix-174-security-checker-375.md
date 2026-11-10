# Fix 174: security-checker: terminal.py compares against unnamed numbers (5)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: terminal.py の render にある比較用の数値 (5) を名前付き定数にする
- Bug report: number 375 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/375))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/174-security-checker-375.patch](fixes/174-security-checker-375.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/174-security-checker-375.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-174-security-checker-375.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-174-security-checker-375.html

## The bug

src/security_checker/report/terminal.py compared the number of warnings shown against bare numbers (5). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constant MAX_WARNING_NOTICES.

## Files changed

- src/security_checker/report/terminal.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 174-security-checker-375.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 375.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant terminal.py 5

## The full patch

`````diff
diff --git a/src/security_checker/report/terminal.py b/src/security_checker/report/terminal.py
index c75154a..9ba37c7 100644
--- a/src/security_checker/report/terminal.py
+++ b/src/security_checker/report/terminal.py
@@ -32,6 +32,8 @@ STATUS_MARK = {
 }
 MAX_ROWS = 50
 MAX_FINDING_PANELS = 20
+#: 端末に並べる警告 (warn) の上限. 残りは件数だけを示す
+MAX_WARNING_NOTICES = 5
 
 # review_required を confirmed の直後に置く。割れた判断こそ人間が見るべきもの (§18.2)。
 FINDING_SECTIONS: tuple[tuple[FindingStatus, str, str], ...] = (
@@ -237,10 +239,11 @@ def render(
     notices = [w for w in report.warnings if w.level == "warn"]
     for warning in errors:
         console.print(Text(f"  ⚠ {warning.source}: {_one_line(warning.message)}", style="bold red"))
-    for warning in notices[:5]:
+    for warning in notices[:MAX_WARNING_NOTICES]:
         console.print(Text(f"  · {warning.source}: {_one_line(warning.message)}", style="yellow"))
-    if len(notices) > 5:
-        console.print(Text(f"  · ほか {len(notices) - 5} 件の警告 (report.json 参照)", style="dim"))
+    if len(notices) > MAX_WARNING_NOTICES:
+        rest = len(notices) - MAX_WARNING_NOTICES
+        console.print(Text(f"  · ほか {rest} 件の警告 (report.json 参照)", style="dim"))
 
     if report.findings:
         _render_findings(console, report)
`````

[Back to the shelf](README.md)
