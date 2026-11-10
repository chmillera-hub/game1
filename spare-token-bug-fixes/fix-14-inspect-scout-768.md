# Fix 14: inspect_scout: retry_refusals=True allows one retry instead of the default three

Status: UNSENT and UNTESTED. Free to take.

- Project: meridianlabs-ai/inspect_scout
- Bug report title: retry_refusals=True allows one retry instead of the default three
- Bug report: number 768 ([open the bug report](https://github.com/meridianlabs-ai/inspect_scout/issues/768))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/14-inspect-scout-768.patch](fixes/14-inspect-scout-768.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/14-inspect-scout-768.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-14-inspect-scout-768.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-14-inspect-scout-768.html

## The bug

llm_scanner(retry_refusals=True) gives up after two refused responses and raises RefusalError. retry_refusals=3 recovers. The option accepts a bool or an int and Python treats True as the integer 1 so the branch that maps True to 3 never runs.

## The fix

The resolution code in src/inspect_scout/_llm_scanner/_llm_scanner.py now checks for a bool before an int. True means 3 retries and False means 0 and an explicit integer keeps its meaning. The docstring says so. A new test passes retry_refusals=True with three refusals followed by a success.

## Files changed

- src/inspect_scout/_llm_scanner/_llm_scanner.py
- tests/llm_scanner/test_retry_refusals.py

## How to use the fix

1. Get a copy of the project meridianlabs-ai/inspect_scout.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 14-inspect-scout-768.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 768.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The person who reported the bug offered to prepare a fix. Please check the bug report for a linked pull request before sending this one. The project builds its changelog automatically so the patch adds no changelog line.

## Search words

inspect_scout llm_scanner retry_refusals True RefusalError isinstance bool int content_filter one retry instead of three

## The full patch

`````diff
diff --git a/src/inspect_scout/_llm_scanner/_llm_scanner.py b/src/inspect_scout/_llm_scanner/_llm_scanner.py
index 3753455..5126292 100644
--- a/src/inspect_scout/_llm_scanner/_llm_scanner.py
+++ b/src/inspect_scout/_llm_scanner/_llm_scanner.py
@@ -257,7 +257,7 @@ def llm_scanner(
             ``True`` for default caching, a :class:`CachePolicy` for explicit
             expiry/scope, or ``None`` (default) for no caching. Threaded
             through to ``model.generate()`` via ``GenerateConfig.cache``.
-        retry_refusals: Retry model refusals. Pass an ``int`` for number of retries (defaults to 3). Pass ``False`` to not retry refusals. If the limit of refusals is exceeded then a ``RuntimeError`` is raised.
+        retry_refusals: Retry model refusals. Pass an ``int`` for number of retries (defaults to 3). Pass ``True`` for the default of 3 retries. Pass ``False`` to not retry refusals. If the limit of refusals is exceeded then a ``RuntimeError`` is raised.
         name: Scanner name.
             Use this to assign a name when passing ``llm_scanner()`` directly to ``scan()`` rather than delegating to it from another scanner.
         content: Override the transcript content filters for this scanner.
@@ -344,12 +344,12 @@ def llm_scanner(
     )
 
     # resolve retry_refusals
+    # (bool is a subclass of int, so it has to be checked first: otherwise
+    # True is taken as an explicit budget of 1 retry rather than the default)
     retry_refusals = (
-        retry_refusals
-        if isinstance(retry_refusals, int)
-        else 3
-        if retry_refusals is True
-        else 0
+        (3 if retry_refusals else 0)
+        if isinstance(retry_refusals, bool)
+        else retry_refusals
     )
 
     async def scan(transcript: Transcript | TranscriptHandle) -> Result:
diff --git a/tests/llm_scanner/test_retry_refusals.py b/tests/llm_scanner/test_retry_refusals.py
index 852fd13..0e6e94b 100644
--- a/tests/llm_scanner/test_retry_refusals.py
+++ b/tests/llm_scanner/test_retry_refusals.py
@@ -66,6 +66,53 @@ def test_retry_success_after_refusals_regular_answer() -> None:
         assert df["value"].iloc[0] is True
 
 
+def test_retry_refusals_true_uses_the_default_budget() -> None:
+    """retry_refusals=True means the default of 3 retries, not 1 (bool is an int)."""
+
+    @scanner(name="retry_true_test", messages="all")
+    def retry_scanner() -> Scanner[Transcript]:
+        return llm_scanner(
+            question="Is this conversation helpful?",
+            answer="boolean",
+            retry_refusals=True,
+        )
+
+    # Prime: 3 refusals, then success (an explicit budget of 1 would fail here)
+    mock_responses = [
+        ModelOutput.from_content(
+            model="mockllm",
+            content="I cannot answer that question.",
+            stop_reason="content_filter",
+        )
+        for _ in range(3)
+    ] + [
+        ModelOutput.from_content(
+            model="mockllm",
+            content="The assistant in [M2] provided helpful information.\n\nANSWER: yes",
+            stop_reason="stop",
+        ),
+    ]
+
+    with tempfile.TemporaryDirectory() as tmpdir:
+        status = scan(
+            scanners=[retry_scanner()],
+            transcripts=transcripts_from(LOGS_DIR),
+            scans=tmpdir,
+            limit=1,
+            max_processes=1,
+            model="mockllm/model",
+            model_args={"custom_outputs": mock_responses},
+        )
+
+        assert status.complete
+        assert len(status.errors) == 0
+
+        results = scan_results_df(status.location, scanner="retry_true_test")
+        df = results.scanners["retry_true_test"]
+        assert len(df) == 1
+        assert df["value"].iloc[0] is True
+
+
 def test_retry_success_after_refusals_structured_answer() -> None:
     """Test that scanner succeeds after retrying refusals (structured answer)."""
     # Note: This test is a placeholder for structured answer retry testing.
`````

[Back to the shelf](README.md)
