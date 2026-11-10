# Fix 130: SMART toolkit: no test keeps the conditions next to the at-most-once promise in the docs

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: tests: check that docs keep the conditions of at-most-once scheduled firings
- Bug report: number 63 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/63))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/130-social-messaging-agent-runtime-toolkit-63.patch](fixes/130-social-messaging-agent-runtime-toolkit-63.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/130-social-messaging-agent-runtime-toolkit-63.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-130-social-messaging-agent-runtime-toolkit-63.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-130-social-messaging-agent-runtime-toolkit-63.html

## The bug

Eight docs say a scheduled firing runs at most once. The promise only holds with the state table on. No test checked the wording so an edit could drop the condition and overstate the guarantee.

## The fix

Tests only. A new file tests/test_docs_at_most_once.py reads the eight files and finds every paragraph with at most once or runs once or fire once or fires once and expects the same paragraph to name the state table (state table or features.state_table or the table).

## Files changed

- tests/test_docs_at_most_once.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 130-social-messaging-agent-runtime-toolkit-63.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 63.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The test fails on docs/events-scheduling.md until the wording change of fix 127 on this shelf is applied. The bug report says so too. The chatbot ran a scratch copy of the test logic against the docs: seven files pass as they are and the eighth passes with fix 127 applied.

## Search words

SMART docs test at most once runs once fire once state table features.state_table paragraph scheduled firing wording

## The full patch

`````diff
diff --git a/tests/test_docs_at_most_once.py b/tests/test_docs_at_most_once.py
new file mode 100644
index 0000000..56249d4
--- /dev/null
+++ b/tests/test_docs_at_most_once.py
@@ -0,0 +1,59 @@
+"""Docs that promise an at-most-once scheduled firing must name its condition.
+
+A scheduled firing runs at most once only while the state table is on and the
+schedule's Input carries ``scheduled_time``. EventBridge Scheduler itself
+delivers at least once. Every paragraph that makes the promise has to name the
+state table, so an edit cannot drop the condition and overstate the guarantee.
+"""
+
+from __future__ import annotations
+
+import re
+from pathlib import Path
+
+import pytest
+
+ROOT = Path(__file__).resolve().parents[1]
+
+DOCS = (
+    "docs/events-scheduling.md",
+    "docs/configuration.md",
+    "docs/state.md",
+    "docs/architecture.md",
+    "docs/architecture-decisions.md",
+    "docs/threat-model.md",
+    "docs/adr/0009-direct-sends-and-delivery-records.md",
+    "AGENTS.md",
+)
+
+_PROMISE = re.compile(r"at most once|runs once|fires? once", re.IGNORECASE)
+_CONDITION = re.compile(r"state table|features\.state_table|the table", re.IGNORECASE)
+
+
+def _paragraphs(text: str) -> list[str]:
+    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]
+
+
+def _promises_without_condition(text: str) -> list[str]:
+    return [
+        p.strip()[:120]
+        for p in _paragraphs(text)
+        if _PROMISE.search(p) and not _CONDITION.search(p)
+    ]
+
+
+@pytest.mark.parametrize("doc", DOCS)
+def test_every_at_most_once_promise_names_the_state_table(doc):
+    text = (ROOT / doc).read_text(encoding="utf-8")
+
+    # The file must still make the promise somewhere, or this test checks nothing.
+    assert _PROMISE.search(text), f"{doc} no longer mentions an at-most-once firing"
+    assert _promises_without_condition(text) == []
+
+
+def test_a_bare_promise_is_caught():
+    bare = "Intro.\n\nOne-shot schedules fire once and auto-delete.\n\nOther text."
+
+    assert _promises_without_condition(bare) == [
+        "One-shot schedules fire once and auto-delete."
+    ]
`````

[Back to the shelf](README.md)
