# Fix 133: security-checker: parse_trivy overwrites its own loop variables in three places

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor(scanners): parse_trivy でループ変数 result / item を自分自身で上書きしている
- Bug report: number 678 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/678))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/133-security-checker-678.patch](fixes/133-security-checker-678.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/133-security-checker-678.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-133-security-checker-678.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-133-security-checker-678.html

## The bug

parse_trivy in src/security_checker/scanners/trivy.py had three loops of the form for result in results: result = as_dict(result). The code works but one name holds two different kinds of value and the lint rule PLW2901 reports each spot.

## The fix

The loop variables are now raw_result and raw_item and the converted values keep the names result and item. Nothing else changes.

## Files changed

- src/security_checker/scanners/trivy.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 133-security-checker-678.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 678.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A rename only with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker parse_trivy PLW2901 loop variable overwritten as_dict raw_result raw_item ruff

## The full patch

`````diff
diff --git a/src/security_checker/scanners/trivy.py b/src/security_checker/scanners/trivy.py
index 257a497..8b8097f 100644
--- a/src/security_checker/scanners/trivy.py
+++ b/src/security_checker/scanners/trivy.py
@@ -80,8 +80,8 @@ def parse_trivy(
     if not isinstance(results, list):
         return [], ["trivy の出力の Results が配列ではありません"]
 
-    for result in results:
-        result = as_dict(result)
+    for raw_result in results:
+        result = as_dict(raw_result)
         target = result.get("Target")
         if not isinstance(target, str):
             warnings.append("trivy の結果に Target がありません")
@@ -90,8 +90,8 @@ def parse_trivy(
         if exclude and is_excluded(path, exclude):
             continue
 
-        for item in result.get("Misconfigurations") or []:
-            item = as_dict(item)
+        for raw_item in result.get("Misconfigurations") or []:
+            item = as_dict(raw_item)
             if item.get("Status") != "FAIL":
                 continue
             rule = item.get("ID") or item.get("AVDID")
@@ -128,8 +128,8 @@ def parse_trivy(
             )
 
         ecosystem = str(result.get("Type") or "unknown")
-        for item in result.get("Vulnerabilities") or []:
-            item = as_dict(item)
+        for raw_item in result.get("Vulnerabilities") or []:
+            item = as_dict(raw_item)
             vuln_id = item.get("VulnerabilityID")
             name = item.get("PkgName")
             if not isinstance(vuln_id, str) or not isinstance(name, str):
`````

[Back to the shelf](README.md)
