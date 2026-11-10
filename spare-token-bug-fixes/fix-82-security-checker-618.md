# Fix 82: security-checker: a trivy dependency finding with an unknown severity is treated as medium without saying so

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(scanners): trivy の依存の脆弱性で重大度が UNKNOWN のとき、medium として扱ったことがメッセージに出ない
- Bug report: number 618 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/618))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/82-security-checker-618.patch](fixes/82-security-checker-618.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/82-security-checker-618.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-82-security-checker-618.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-82-security-checker-618.html

## The bug

When trivy reported a misconfiguration with an unknown severity the message said the finding is treated as medium. A dependency vulnerability with an unknown severity was also treated as medium and the message did not say so. Only the trivy dependency findings behaved differently from the other scanners.

## The fix

parse_trivy in src/security_checker/scanners/trivy.py now adds the same note to the message of a dependency vulnerability whose severity is not in the severity table. A new file tests/unit/test_trivy_unknown_vuln_severity.py checks the note for an unknown and a missing and a non-text severity and checks that a known severity gets no note.

## Files changed

- src/security_checker/scanners/trivy.py
- tests/unit/test_trivy_unknown_vuln_severity.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 82-security-checker-618.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 618.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The note text is the exact text the project already uses for misconfigurations. The chatbot did not run the project's tests. Fixes 71 and 79 and 83 and 84 and 85 on this shelf are for the same project and touch different files.

## Search words

security-checker trivy parse_trivy Vulnerabilities UNKNOWN severity medium note message 重大度不明

## The full patch

`````diff
diff --git a/src/security_checker/scanners/trivy.py b/src/security_checker/scanners/trivy.py
index 257a497..7e9005c 100644
--- a/src/security_checker/scanners/trivy.py
+++ b/src/security_checker/scanners/trivy.py
@@ -144,6 +144,11 @@ def parse_trivy(
             )
             title = str(item.get("Title") or vuln_id)
             fixed = item.get("FixedVersion")
+            severity = SEVERITY_MAP.get(str(item.get("Severity")).upper())
+            message = f"{name} {ref.version or ''} に既知の脆弱性があります: {title}"
+            if severity is None:
+                # 誤設定・osv と同じく、medium として扱ったことを message に残す
+                message += " (重大度不明のため medium として扱います)"
             candidates.append(
                 Candidate(
                     id=ids.make("trivy", vuln_id, path, ref.as_key()),
@@ -151,10 +156,9 @@ def parse_trivy(
                     category=Category.DEPENDENCY,
                     rule_id=vuln_id,
                     title=title,
-                    message=f"{name} {ref.version or ''} に既知の脆弱性があります: {title}",
+                    message=message,
                     package=ref,
-                    severity_reported=SEVERITY_MAP.get(str(item.get("Severity")).upper())
-                    or Severity.MEDIUM,
+                    severity_reported=severity or Severity.MEDIUM,
                     cwe=[c for c in item.get("CweIDs") or [] if isinstance(c, str)],
                     cve=[vuln_id] if _CVE_RE.match(vuln_id) else [],
                     references=_references(item),
diff --git a/tests/unit/test_trivy_unknown_vuln_severity.py b/tests/unit/test_trivy_unknown_vuln_severity.py
new file mode 100644
index 0000000..68469a7
--- /dev/null
+++ b/tests/unit/test_trivy_unknown_vuln_severity.py
@@ -0,0 +1,39 @@
+"""trivy の依存の脆弱性で重大度が不明のとき、medium として扱ったことを message に残す."""
+
+from __future__ import annotations
+
+from pathlib import Path
+from typing import Any
+
+import pytest
+
+from security_checker.models.enums import Category, Severity
+from security_checker.scanners.trivy import parse_trivy
+
+
+def _payload(severity: Any) -> dict[str, Any]:
+    item: dict[str, Any] = {
+        "VulnerabilityID": "CVE-2099-0001",
+        "PkgName": "demo",
+        "InstalledVersion": "1.0.0",
+        "Title": "demo の脆弱性",
+    }
+    if severity is not None:
+        item["Severity"] = severity
+    return {"Results": [{"Target": "requirements.txt", "Type": "pip", "Vulnerabilities": [item]}]}
+
+
+@pytest.mark.parametrize("severity", ["UNKNOWN", None, 3])
+def test_trivy_vulnerability_with_unknown_severity_says_medium(severity):
+    candidates, _ = parse_trivy(_payload(severity), Path("/repo"))
+    assert len(candidates) == 1
+    assert candidates[0].category is Category.DEPENDENCY
+    assert candidates[0].severity_reported is Severity.MEDIUM
+    assert "重大度不明" in candidates[0].message
+
+
+def test_trivy_vulnerability_with_known_severity_has_no_note():
+    candidates, _ = parse_trivy(_payload("HIGH"), Path("/repo"))
+    assert len(candidates) == 1
+    assert candidates[0].severity_reported is Severity.HIGH
+    assert "重大度不明" not in candidates[0].message
`````

[Back to the shelf](README.md)
