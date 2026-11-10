# Fix 248: security-checker: public names in models/report.py have no docstring (count_by_severity and count_by_status and dump and has_failed_scanner and utcnow)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(models): report.py の公開クラス・メソッド 5 個に docstring が無い
- Bug report: number 399 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/399))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/248-security-checker-399.patch](fixes/248-security-checker-399.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/248-security-checker-399.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-248-security-checker-399.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-248-security-checker-399.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/models/report.py: count_by_severity and count_by_status and dump and has_failed_scanner and utcnow. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/models/report.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/models/report.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 248-security-checker-399.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 399.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring report.py count_by_severity and count_by_status and dump and has_failed_scanner and utcnow

## The full patch

`````diff
diff --git a/src/security_checker/models/report.py b/src/security_checker/models/report.py
index cc5ece4..a554f0d 100644
--- a/src/security_checker/models/report.py
+++ b/src/security_checker/models/report.py
@@ -160,17 +160,21 @@ class Report(BaseModel):
 
     @property
     def has_failed_scanner(self) -> bool:
+        """失敗 (failed) で終わったスキャナが 1 つでもあるか."""
         return any(run.status is ScanStatus.FAILED for run in self.scanners)
 
     def dump(self) -> dict[str, Any]:
+        """report.json に書く形 (JSON にできる値だけの辞書). None の項目も残す."""
         return self.model_dump(mode="json", exclude_none=False)
 
 
 def utcnow() -> datetime:
+    """タイムゾーン付きの現在時刻 (UTC)."""
     return datetime.now(UTC)
 
 
 def count_by_status(findings: list[Finding]) -> dict[str, int]:
+    """Finding を status ごとに数える. 0 件の status も 0 として入れる."""
     counts = {status.value: 0 for status in FindingStatus}
     for finding in findings:
         counts[finding.status.value] += 1
@@ -178,6 +182,7 @@ def count_by_status(findings: list[Finding]) -> dict[str, int]:
 
 
 def count_by_severity(candidates: list[Candidate]) -> dict[str, int]:
+    """候補をスキャナの報告した重大度ごとに数える. 重大度が無いものは info に数える."""
     counts = {severity.value: 0 for severity in Severity}
     for candidate in candidates:
         key = (candidate.severity_reported or Severity.INFO).value
`````

[Back to the shelf](README.md)
