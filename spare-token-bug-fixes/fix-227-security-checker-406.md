# Fix 227: security-checker: public names in observability/trace.py have no docstring (__init__ and sha256_text and write_call and write_run)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(observability): trace.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 406 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/406))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/227-security-checker-406.patch](fixes/227-security-checker-406.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/227-security-checker-406.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-227-security-checker-406.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-227-security-checker-406.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/observability/trace.py: __init__ and sha256_text and write_call and write_run. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/observability/trace.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/observability/trace.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 227-security-checker-406.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 406.

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

security-checker docstring D1 ruff missing docstring trace.py __init__ and sha256_text and write_call and write_run

## The full patch

`````diff
diff --git a/src/security_checker/observability/trace.py b/src/security_checker/observability/trace.py
index 66459d2..b735b0a 100644
--- a/src/security_checker/observability/trace.py
+++ b/src/security_checker/observability/trace.py
@@ -15,6 +15,7 @@ from security_checker.context.redact import redact_known_patterns
 
 
 def sha256_text(text: str) -> str:
+    """UTF-8 にした文字列の SHA-256 (16 進). プロンプト全文の代わりにトレースへ残す."""
     return hashlib.sha256(text.encode("utf-8")).hexdigest()
 
 
@@ -22,11 +23,13 @@ class TraceWriter:
     """run 単位のトレース出力."""
 
     def __init__(self, output_dir: Path, run_id: str, *, enabled: bool = True) -> None:
+        """出力先は `<output_dir>/trace/<run_id>/`. `enabled` が False なら何も書かない."""
         self.root = output_dir / "trace" / run_id
         self.enabled = enabled
         self._index = 0
 
     def write_run(self, payload: dict[str, Any]) -> Path | None:
+        """run 全体の記録を run.json に書く. 無効なら None."""
         if not self.enabled:
             return None
         self.root.mkdir(parents=True, exist_ok=True)
@@ -35,6 +38,7 @@ class TraceWriter:
         return path
 
     def write_call(self, payload: dict[str, Any]) -> Path | None:
+        """LLM 呼び出し 1 回の記録を calls/NNNN.json に書く. 番号は書いた順. 無効なら None."""
         if not self.enabled:
             return None
         calls = self.root / "calls"
`````

[Back to the shelf](README.md)
