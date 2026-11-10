# Fix 46: cluv: submit exits with code 0 when every submission failed

Status: UNSENT and UNTESTED. Free to take.

- Project: mila-iqia/cluv
- Bug report title: [BUG]: `cluv submit first` exits 0 when every submission fails
- Bug report: number 257 ([open the bug report](https://github.com/mila-iqia/cluv/issues/257))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/46-cluv-257.patch](fixes/46-cluv-257.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/46-cluv-257.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-46-cluv-257.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-46-cluv-257.html

## The bug

When every job of a cluv submit first race failed the command logged that all submissions failed and then ended with exit code 0. A script could not tell the failure from a submitted job.

## The fix

main in cluv/__main__.py keeps the value the command function returns. submit returns nothing when every submission failed. In that case main now exits with code 1. tests/test_submit.py gains a test for the failed case (for first and for a named cluster) and a test that a submitted job still ends normally.

## Files changed

- cluv/__main__.py
- tests/test_submit.py

## How to use the fix

1. Get a copy of the project mila-iqia/cluv.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 46-cluv-257.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 257.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The exit code 1 also applies to cluv submit with one named cluster because submit returns nothing there too when the submission fails. The bug report names only cluv submit first. The value 1 is the chatbot's choice.

## Search words

cluv submit first exit code 0 all job submissions have failed exit status non-zero scripts

## The full patch

`````diff
diff --git a/cluv/__main__.py b/cluv/__main__.py
index ff697ad..d483315 100644
--- a/cluv/__main__.py
+++ b/cluv/__main__.py
@@ -159,9 +159,9 @@ def main(argv: list[str] | None = None) -> None:
 
     try:
         if inspect.iscoroutinefunction(function):
-            asyncio.run(function(**args_dict))
+            result = asyncio.run(function(**args_dict))
         else:
-            function(**args_dict)
+            result = function(**args_dict)
     except subprocess.CalledProcessError as err:
         logger.error(f"Command '{err.cmd}' failed with exit code {err.returncode}:")
         if err.output:
@@ -174,6 +174,11 @@ def main(argv: list[str] | None = None) -> None:
             logger.error("No standard error.")
         sys.exit(err.returncode)
 
+    if subcommand == "submit" and result is None:
+        # `submit` returns None when every submission failed (it has already logged why).
+        # Exit non-zero so scripts and agents can tell that from a submitted job.
+        sys.exit(1)
+
 
 def add_submit_args(subparsers: Subparsers):
     submit_parser = subparsers.add_parser(
diff --git a/tests/test_submit.py b/tests/test_submit.py
index 8f2025f..a143ed8 100644
--- a/tests/test_submit.py
+++ b/tests/test_submit.py
@@ -937,6 +937,28 @@ class TestSubmitCliParsing:
             }
         )
 
+    @pytest.mark.parametrize("cluster", ["first", "tamia"])
+    def test_exits_non_zero_when_every_submission_failed(
+        self, monkeypatch: pytest.MonkeyPatch, cluster: str
+    ) -> None:
+        """`submit` returns None when all submissions failed; the command must not exit 0."""
+        monkeypatch.setattr(
+            cluv_main, "submit", mock.AsyncMock(spec=cluv_main.submit, return_value=None)
+        )
+
+        with pytest.raises(SystemExit) as exc_info:
+            cluv_main.main(["submit", cluster, "--", "python", "main.py"])
+
+        assert exc_info.value.code == 1
+
+    def test_exits_zero_when_a_job_was_submitted(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.setattr(
+            cluv_main, "submit", mock.AsyncMock(spec=cluv_main.submit, return_value=mock.Mock())
+        )
+
+        # No SystemExit: `main` returns normally.
+        assert cluv_main.main(["submit", "tamia", "--", "python", "main.py"]) is None
+
     def test_chunking_with_value_is_recovered_from_sbatch_args(
         self, monkeypatch: pytest.MonkeyPatch
     ) -> None:
`````

[Back to the shelf](README.md)
