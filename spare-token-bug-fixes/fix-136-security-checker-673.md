# Fix 136: security-checker: the pre-commit hook does not say when gitleaks is missing and only the simple check runs

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(contrib): gitleaks が無いとき、pre-commit フックが簡易検査に落ちたことを知らせない
- Bug report: number 673 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/673))
- Project license: MIT
- Language: Bash
- Test included: no
- Patch file: [fixes/136-security-checker-673.patch](fixes/136-security-checker-673.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/136-security-checker-673.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-136-security-checker-673.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-136-security-checker-673.html

## The bug

When gitleaks is not installed the pre-commit hook silently switched to a simple text search. A person could believe gitleaks checked the commit and never notice what the simple search misses.

## The fix

contrib/host-audit/hooks/pre-commit now prints one warning line to stderr with the address of the gitleaks install guide when the simple check runs. SECURITY_CHECKER_HOOK_QUIET=1 turns the line off.

## Files changed

- contrib/host-audit/hooks/pre-commit

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 136-security-checker-673.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 673.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 121 on this shelf changes the line right below in the same file so patches 121 and 136 do not apply together: apply one and add the other change by hand. The environment variable name is the chatbot's choice. No test is included. Nobody ran the hook.

## Search words

security-checker pre-commit hook gitleaks missing fallback simple pattern check notice warning stderr quiet

## The full patch

`````diff
diff --git a/contrib/host-audit/hooks/pre-commit b/contrib/host-audit/hooks/pre-commit
index 6234647..21ba654 100755
--- a/contrib/host-audit/hooks/pre-commit
+++ b/contrib/host-audit/hooks/pre-commit
@@ -18,7 +18,11 @@ if command -v gitleaks >/dev/null 2>&1; then
     exit 1
   fi
 else
-  # gitleaks が無い場合の簡易パターン検査
+  # gitleaks が無い場合の簡易パターン検査。黙って切り替えると gitleaks で検査されていると
+  # 思い込まれるので 1 行で知らせる (SECURITY_CHECKER_HOOK_QUIET=1 で抑止)
+  if [[ "${SECURITY_CHECKER_HOOK_QUIET:-}" != "1" ]]; then
+    echo "⚠️  gitleaks が見つからないため簡易検査のみ実行します (導入: https://github.com/gitleaks/gitleaks#installing)" >&2
+  fi
   if git diff --cached -U0 | grep -E '^\+' | grep -qE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[bp]-[0-9A-Za-z-]{20,}|-----BEGIN .*PRIVATE KEY'; then
     echo "❌ コミットにシークレットらしき文字列が含まれています"
     echo "   誤検知なら: git commit --no-verify"
`````

[Back to the shelf](README.md)
