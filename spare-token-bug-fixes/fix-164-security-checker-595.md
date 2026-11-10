# Fix 164: security-checker: no test covers the health check of the cassette provider

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(testing): cassette.py の health_check で未テストの分岐をテストする（3 行）
- Bug report: number 595 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/595))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/164-security-checker-595.patch](fixes/164-security-checker-595.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/164-security-checker-595.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-164-security-checker-595.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-164-security-checker-595.html

## The bug

CassetteProvider.health_check in src/security_checker/testing/cassette.py asks the real provider only in record mode and otherwise answers ok. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_cassette_health_check.py uses a tiny stand-in provider that counts calls and checks record mode and replay mode with and without an inner provider.

## Files changed

- tests/unit/test_cassette_health_check.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 164-security-checker-595.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 595.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The stand-in provider is not a full provider so two lines carry a type: ignore comment for the type checker. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker testing cassette CassetteProvider health_check record replay inner untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_cassette_health_check.py b/tests/unit/test_cassette_health_check.py
new file mode 100644
index 0000000..e0673f5
--- /dev/null
+++ b/tests/unit/test_cassette_health_check.py
@@ -0,0 +1,51 @@
+"""CassetteProvider.health_check: 記録モードだけ inner に問い合わせること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+from security_checker.providers.base import HealthStatus
+from security_checker.testing.cassette import CassetteProvider
+
+
+class _Inner:
+    """health_check が呼ばれた回数だけを数える最小の Provider."""
+
+    model = "inner-model"
+    name = "inner"
+
+    def __init__(self) -> None:
+        self.health_checks = 0
+
+    async def health_check(self) -> HealthStatus:
+        self.health_checks += 1
+        return HealthStatus(ok=False, detail="inner says no")
+
+
+async def test_record_mode_asks_the_inner_provider(tmp_path: Path) -> None:
+    inner = _Inner()
+    provider = CassetteProvider(tmp_path / "c.json", inner=inner, record=True)  # type: ignore[arg-type]
+
+    status = await provider.health_check()
+
+    assert inner.health_checks == 1
+    assert status.ok is False
+    assert status.detail == "inner says no"
+
+
+async def test_replay_mode_with_an_inner_provider_does_not_ask_it(tmp_path: Path) -> None:
+    inner = _Inner()
+    provider = CassetteProvider(tmp_path / "c.json", inner=inner)  # type: ignore[arg-type]
+
+    status = await provider.health_check()
+
+    assert inner.health_checks == 0
+    assert status.ok is True
+    assert status.detail == "cassette"
+
+
+async def test_replay_mode_without_an_inner_provider_is_ok(tmp_path: Path) -> None:
+    status = await CassetteProvider(tmp_path / "c.json").health_check()
+
+    assert status.ok is True
+    assert status.detail == "cassette"
`````

[Back to the shelf](README.md)
