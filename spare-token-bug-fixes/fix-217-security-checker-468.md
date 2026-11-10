# Fix 217: security-checker: no test covers a plugin that fails to load in discover_plugin_aggregators

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(aggregate): registry.py の discover_plugin_aggregators で未テストの分岐をテストする（4 行）
- Bug report: number 468 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/468))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/217-security-checker-468.patch](fixes/217-security-checker-468.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/217-security-checker-468.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-217-security-checker-468.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-217-security-checker-468.html

## The bug

discover_plugin_aggregators in src/security_checker/aggregate/registry.py turns a plugin that fails to load into a warning and keeps going. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_aggregator_registry_plugins.py replaces the entry point lookup with one broken entry and one good entry and expects one warning plus the good entry.

## Files changed

- tests/unit/test_aggregator_registry_plugins.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 217-security-checker-468.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 468.

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

security-checker aggregate registry discover_plugin_aggregators entry_points plugin load failure warning untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_aggregator_registry_plugins.py b/tests/unit/test_aggregator_registry_plugins.py
new file mode 100644
index 0000000..458236d
--- /dev/null
+++ b/tests/unit/test_aggregator_registry_plugins.py
@@ -0,0 +1,49 @@
+"""aggregate.registry.discover_plugin_aggregators: 読み込めないプラグインは警告にして続けること."""
+
+from __future__ import annotations
+
+from typing import Any
+
+import pytest
+
+from security_checker.aggregate import registry
+from security_checker.aggregate.registry import ENTRY_POINT_GROUP, discover_plugin_aggregators
+
+
+class _Entry:
+    def __init__(self, name: str, loaded: Any = None, error: Exception | None = None) -> None:
+        self.name = name
+        self._loaded = loaded
+        self._error = error
+
+    def load(self) -> Any:
+        if self._error is not None:
+            raise self._error
+        return self._loaded
+
+
+def test_broken_plugin_becomes_a_warning_and_the_rest_still_load(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    factory = object()
+    groups: list[str] = []
+
+    def fake_entry_points(*, group: str) -> list[_Entry]:
+        groups.append(group)
+        return [_Entry("broken", error=ImportError("no module")), _Entry("good", loaded=factory)]
+
+    monkeypatch.setattr(registry, "entry_points", fake_entry_points)
+
+    found, warnings = discover_plugin_aggregators()
+
+    assert groups == [ENTRY_POINT_GROUP]
+    assert found == {"good": factory}
+    assert len(warnings) == 1
+    assert "broken" in warnings[0]
+    assert "no module" in warnings[0]
+
+
+def test_no_plugins_gives_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
+    monkeypatch.setattr(registry, "entry_points", lambda *, group: [])
+
+    assert discover_plugin_aggregators() == ({}, [])
`````

[Back to the shelf](README.md)
