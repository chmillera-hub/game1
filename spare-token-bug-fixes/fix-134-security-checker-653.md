# Fix 134: security-checker: the raw-sarif CI job runs apt-get every time to install jq that is already there

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: chore(ci): security.yml の raw-sarif ジョブで毎回 apt-get update と jq のインストールをしている
- Bug report: number 653 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/653))
- Project license: MIT
- Language: GitHub Actions YAML
- Test included: no
- Patch file: [fixes/134-security-checker-653.patch](fixes/134-security-checker-653.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/134-security-checker-653.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-134-security-checker-653.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-134-security-checker-653.html

## The bug

The raw-sarif job in .github/workflows/security.yml ran apt-get update and apt-get install jq on every run. jq ships with the GitHub-hosted ubuntu runners. The apt step adds time and fails the job when a package mirror is slow or down.

## The fix

The two apt-get lines are gone. One line checks that jq exists with command -v and stops the job with a clear message when jq is missing.

## Files changed

- .github/workflows/security.yml

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 134-security-checker-653.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 653.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Nobody ran the workflow. On a self-hosted runner without jq the job now stops with the message and does not install jq.

## Search words

security-checker security.yml raw-sarif apt-get update install jq command -v GitHub Actions runner

## The full patch

`````diff
diff --git a/.github/workflows/security.yml b/.github/workflows/security.yml
index 4f18ef0..b2b03a4 100644
--- a/.github/workflows/security.yml
+++ b/.github/workflows/security.yml
@@ -52,8 +52,8 @@ jobs:
         shell: bash
         run: |
           set -euo pipefail
-          sudo apt-get update -qq
-          sudo apt-get install -y -qq jq
+          # jq は GitHub ホストの ubuntu ランナーに標準で入っている。apt は使わず存在だけ確かめる
+          command -v jq >/dev/null || { echo "jq が見つかりません" >&2; exit 1; }
           # action.yml と同じく、版と sha256 を固定して取得する (scripts/scanner-versions.sh)
           BIN="$RUNNER_TEMP/security-checker-bin"
           scripts/install-scanners.sh "$BIN"
`````

[Back to the shelf](README.md)
