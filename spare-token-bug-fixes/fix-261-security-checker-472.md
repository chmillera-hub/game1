# Fix 261: security-checker: no test covers the settings overrides built from command line options

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(cli): cli.py の _cli_overrides で未テストの分岐をテストする（9 行）
- Bug report: number 472 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/472))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/261-security-checker-472.patch](fixes/261-security-checker-472.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/261-security-checker-472.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-261-security-checker-472.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-261-security-checker-472.html

## The bug

_cli_overrides in src/security_checker/cli.py turns the policy and exclude and output and semgrep options into settings overrides. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_cli_overrides.py checks no options and the three policy options and the exclude option and the two output options and the semgrep option.

## Files changed

- tests/unit/test_cli_overrides.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 261-security-checker-472.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 472.

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

security-checker cli _cli_overrides fail_on min_score strict exclude output formats semgrep config untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_cli_overrides.py b/tests/unit/test_cli_overrides.py
new file mode 100644
index 0000000..2351905
--- /dev/null
+++ b/tests/unit/test_cli_overrides.py
@@ -0,0 +1,50 @@
+"""cli._cli_overrides: 指定されたオプションだけを設定の上書きにすること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+from typing import Any
+
+from security_checker.cli import _cli_overrides
+from security_checker.models.enums import Severity
+
+
+def _overrides(**given: Any) -> dict[str, Any]:
+    options: dict[str, Any] = {
+        "fail_on": None,
+        "min_score": None,
+        "strict": None,
+        "exclude": None,
+        "output_dir": None,
+        "formats": None,
+        "semgrep_config": None,
+    }
+    options.update(given)
+    return _cli_overrides(**options)
+
+
+def test_nothing_given_is_no_override() -> None:
+    assert _overrides() == {}
+
+
+def test_policy_options_go_under_policy() -> None:
+    overrides = _overrides(fail_on=Severity.CRITICAL, min_score=70, strict=False)
+
+    assert overrides == {"policy": {"fail_on": "critical", "min_score": 70, "strict": False}}
+
+
+def test_exclude_goes_under_target() -> None:
+    assert _overrides(exclude=["tests/**"]) == {"target": {"exclude": ["tests/**"]}}
+    assert _overrides(exclude=[]) == {}
+
+
+def test_output_options_go_under_output() -> None:
+    overrides = _overrides(output_dir=Path("out"), formats=["json", "sarif"])
+
+    assert overrides == {"output": {"dir": "out", "formats": ["json", "sarif"]}}
+
+
+def test_semgrep_config_goes_under_scanners() -> None:
+    overrides = _overrides(semgrep_config="p/default")
+
+    assert overrides == {"scanners": {"semgrep": {"config": "p/default"}}}
`````

[Back to the shelf](README.md)
