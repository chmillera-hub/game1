# Fix 84: security-checker: text logs do not quote values that hold spaces so a program cannot tell where a value ends

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(observability): text 形式のログで値に空白や = を含むと key=value の区切りが曖昧になる
- Bug report: number 663 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/663))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/84-security-checker-663.patch](fixes/84-security-checker-663.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/84-security-checker-663.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-84-security-checker-663.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-84-security-checker-663.html

## The bug

The text log format wrote each field as key=value separated by spaces and never quoted a value. A value with a space such as a timeout reason could not be read back by a program because the end of the value was unclear.

## The fix

src/security_checker/observability/logging.py gains _text_value. A value that holds a space or an equals sign or a double quote and an empty value are written as a JSON text in double quotes. Every other value is written bare as before. A new file tests/unit/test_text_log_quoting.py covers a value with spaces and a value with an equals sign and quotes and plain values and an empty value.

## Files changed

- src/security_checker/observability/logging.py
- tests/unit/test_text_log_quoting.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 84-security-checker-663.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 663.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Quoting the empty value is the chatbot's addition and the bug report does not mention the empty value. The event name itself is still written bare. The chatbot checked the rule with a scratch copy and did not run the project's tests.

## Search words

security-checker logging _Formatter text format key=value logfmt quote spaces equals structured log

## The full patch

`````diff
diff --git a/src/security_checker/observability/logging.py b/src/security_checker/observability/logging.py
index e390fc9..d30552a 100644
--- a/src/security_checker/observability/logging.py
+++ b/src/security_checker/observability/logging.py
@@ -40,6 +40,14 @@ def set_run_id(run_id: str | None) -> None:
     _run_id.set(run_id)
 
 
+def _text_value(value: Any) -> str:
+    """text 形式の値. 空白・`=`・引用符を含む値と空の値は JSON 文字列にする (logfmt)."""
+    text = str(value)
+    if text == "" or any(ch.isspace() or ch in '="' for ch in text):
+        return json.dumps(text, ensure_ascii=False)
+    return text
+
+
 class _Formatter(logging.Formatter):
     def __init__(self, fmt: Literal["text", "json"]) -> None:
         super().__init__()
@@ -59,7 +67,7 @@ class _Formatter(logging.Formatter):
         if self.fmt == "json":
             text = json.dumps(payload, ensure_ascii=False, default=str)
         else:
-            extras = " ".join(f"{key}={value}" for key, value in fields.items())
+            extras = " ".join(f"{key}={_text_value(value)}" for key, value in fields.items())
             text = f"{payload['ts']} {payload['level']:<5} {payload['event']}" + (
                 f" {extras}" if extras else ""
             )
diff --git a/tests/unit/test_text_log_quoting.py b/tests/unit/test_text_log_quoting.py
new file mode 100644
index 0000000..d36f1cf
--- /dev/null
+++ b/tests/unit/test_text_log_quoting.py
@@ -0,0 +1,44 @@
+"""text 形式のログは、空白・`=`・引用符を含む値を引用する (logfmt として読めるようにする)."""
+
+from __future__ import annotations
+
+import io
+from collections.abc import Iterator
+
+import pytest
+
+from security_checker.observability import logging as log
+
+
+@pytest.fixture(autouse=True)
+def _reset_logging() -> Iterator[None]:
+    yield
+    log.disable()
+
+
+def _line(**fields: object) -> str:
+    stream = io.StringIO()
+    log.configure(fmt="text", level="info", stream=stream)
+    log.event("scan.done", **fields)
+    lines = stream.getvalue().splitlines()
+    assert len(lines) == 1
+    return lines[0]
+
+
+def test_value_with_spaces_is_quoted():
+    line = _line(reason="スキャナが 300s でタイムアウトしました", scanner="trivy")
+    assert 'reason="スキャナが 300s でタイムアウトしました" scanner=trivy' in line
+
+
+def test_value_with_equals_or_quote_is_quoted():
+    line = _line(detail='a=b "c"')
+    assert 'detail="a=b \\"c\\""' in line
+
+
+def test_plain_values_stay_bare():
+    line = _line(reason="x", count=3)
+    assert "scan.done reason=x count=3" in line
+
+
+def test_empty_value_is_quoted():
+    assert 'reason=""' in _line(reason="")
`````

[Back to the shelf](README.md)
