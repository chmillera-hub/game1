# Fix 216: security-checker: no test covers an unknown strategy or an old-style plugin in build_aggregator

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(aggregate): registry.py の build_aggregator で未テストの分岐をテストする（3 行）
- Bug report: number 469 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/469))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/216-security-checker-469.patch](fixes/216-security-checker-469.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/216-security-checker-469.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-216-security-checker-469.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-216-security-checker-469.html

## The bug

build_aggregator in src/security_checker/aggregate/registry.py raises ConfigError for judge used alone and for an unknown strategy and falls back to a call without weights for an old plugin. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_aggregator_registry_build.py checks judge alone and an unknown name and a stand-in plugin that takes no weights.

## Files changed

- tests/unit/test_aggregator_registry_build.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 216-security-checker-469.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 469.

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

security-checker aggregate registry build_aggregator judge unknown strategy TypeError weights plugin untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_aggregator_registry_build.py b/tests/unit/test_aggregator_registry_build.py
new file mode 100644
index 0000000..1f3bfac
--- /dev/null
+++ b/tests/unit/test_aggregator_registry_build.py
@@ -0,0 +1,36 @@
+"""aggregate.registry.build_aggregator: 未知の戦略と、weights を受け取らないプラグインの扱い."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.aggregate import registry
+from security_checker.aggregate.registry import build_aggregator
+from security_checker.errors import ConfigError
+
+
+class _OldStylePlugin:
+    """weights を受け取らない、旧シグネチャの Aggregator."""
+
+    name = "old-style"
+
+
+def test_judge_alone_is_a_config_error() -> None:
+    with pytest.raises(ConfigError, match="judge は単独の Aggregator ではありません"):
+        build_aggregator("judge")
+
+
+def test_unknown_strategy_is_a_config_error_that_lists_the_choices() -> None:
+    with pytest.raises(ConfigError, match="未知の aggregation.strategy 'no-such-strategy'"):
+        build_aggregator("no-such-strategy")
+
+
+def test_plugin_that_takes_no_weights_is_still_built(monkeypatch: pytest.MonkeyPatch) -> None:
+    monkeypatch.setattr(
+        registry, "discover_plugin_aggregators", lambda: ({"old-style": _OldStylePlugin}, ["w"])
+    )
+
+    aggregator, warnings = build_aggregator("old-style", weights={"r1": 2.0})
+
+    assert isinstance(aggregator, _OldStylePlugin)
+    assert warnings == ["w"]
`````

[Back to the shelf](README.md)
