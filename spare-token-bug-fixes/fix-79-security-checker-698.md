# Fix 79: security-checker: a review with no reviewers set up leaves an empty output folder behind

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(run): reviewers が無いときの ConfigError の前に出力ディレクトリを作ってしまう
- Bug report: number 698 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/698))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/79-security-checker-698.patch](fixes/79-security-checker-698.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/79-security-checker-698.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-79-security-checker-698.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-79-security-checker-698.html

## The bug

run_review created the output folder .security-checker/raw before checking whether any reviewer is configured. With no reviewer the command stopped with a configuration error and had run nothing and still left an empty folder in the current directory.

## The fix

src/security_checker/run.py now checks for reviewers before resolving and creating the output folder. tests/e2e/test_review_pipeline.py gains a test that the configuration error leaves no output folder.

## Files changed

- src/security_checker/run.py
- tests/e2e/test_review_pipeline.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 79-security-checker-698.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 698.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The change only moves an existing check a few lines up. The chatbot did not run the project's tests. Fix 71 on this shelf is for the same project and touches different files so the two patches apply together.

## Search words

security-checker run_review reviewers ConfigError raw_dir.mkdir empty output directory .security-checker/raw order of checks

## The full patch

`````diff
diff --git a/src/security_checker/run.py b/src/security_checker/run.py
index cefc183..ff0122b 100644
--- a/src/security_checker/run.py
+++ b/src/security_checker/run.py
@@ -480,16 +480,17 @@ async def run_review(
     started_at = utcnow()
     identifier = run_id or new_run_id()
     log.set_run_id(identifier)
-    output_dir = resolve_output_dir(config, base_dir or Path.cwd())
-    raw_dir = output_dir / "raw"
-    raw_dir.mkdir(parents=True, exist_ok=True)
-
+    # 設定エラーは出力ディレクトリを作る前に検出する (空の raw/ を残さない)。
     if not config.reviewers and reviewer_setup is None:
         raise ConfigError(
             "reviewers が設定されていません。security-checker.yml に reviewer を定義するか、"
             "LLM を使わない `security-checker scan` を実行してください"
         )
 
+    output_dir = resolve_output_dir(config, base_dir or Path.cwd())
+    raw_dir = output_dir / "raw"
+    raw_dir.mkdir(parents=True, exist_ok=True)
+
     results, runs, warnings = await _execute_scanners(
         config,
         root,
diff --git a/tests/e2e/test_review_pipeline.py b/tests/e2e/test_review_pipeline.py
index 28944a3..70f79c9 100644
--- a/tests/e2e/test_review_pipeline.py
+++ b/tests/e2e/test_review_pipeline.py
@@ -226,3 +226,10 @@ async def test_missing_reviewers_is_config_error(workspace, tmp_path):
     config = make_config(tmp_path, reviewers=[])
     with pytest.raises(ConfigError, match="reviewers"):
         await run_review(config, workspace, base_dir=tmp_path, scanners=[])
+
+
+async def test_missing_reviewers_creates_no_output_dir(workspace, tmp_path):
+    config = make_config(tmp_path, reviewers=[])
+    with pytest.raises(ConfigError, match="reviewers"):
+        await run_review(config, workspace, base_dir=tmp_path, scanners=[])
+    assert not (tmp_path / "out").exists()
`````

[Back to the shelf](README.md)
