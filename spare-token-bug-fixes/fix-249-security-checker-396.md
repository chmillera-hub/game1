# Fix 249: security-checker: public names in github/comment.py have no docstring (InlineComment and InlinePlan and finding_marker and render_inline)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(github): comment.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 396 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/396))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/249-security-checker-396.patch](fixes/249-security-checker-396.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/249-security-checker-396.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-249-security-checker-396.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-249-security-checker-396.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/github/comment.py: InlineComment and InlinePlan and finding_marker and render_inline. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/github/comment.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/github/comment.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 249-security-checker-396.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 396.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring comment.py InlineComment and InlinePlan and finding_marker and render_inline

## The full patch

`````diff
diff --git a/src/security_checker/github/comment.py b/src/security_checker/github/comment.py
index 274992a..7d4bc25 100644
--- a/src/security_checker/github/comment.py
+++ b/src/security_checker/github/comment.py
@@ -279,6 +279,7 @@ def _footer(report: Report, report_url: str | None) -> str:
 
 
 def finding_marker(finding: Finding) -> str:
+    """inline コメントの先頭に置く HTML コメント. 同じ検出への二重投稿を防ぐ目印になる."""
     return f"{FINDING_MARKER_PREFIX}{finding.candidate.id} -->"
 
 
@@ -293,6 +294,7 @@ def existing_finding_ids(bodies: Iterable[str]) -> set[str]:
 
 
 def render_inline(finding: Finding) -> str:
+    """Finding 1 件分の inline コメントの本文 (Markdown) を作る."""
     candidate = finding.candidate
     if finding.status is FindingStatus.REVIEW_REQUIRED:
         head = "❓ **REVIEW REQUIRED** — Reviewer の判断が分かれました"
@@ -318,6 +320,8 @@ def render_inline(finding: Finding) -> str:
 
 @dataclass(frozen=True)
 class InlineComment:
+    """投稿する inline コメント 1 件. どのファイルのどの行に何を書くか."""
+
     path: str
     line: int
     body: str
@@ -326,6 +330,8 @@ class InlineComment:
 
 @dataclass
 class InlinePlan:
+    """inline コメントの投稿計画. 投稿するものと、見送った件数の内訳."""
+
     comments: list[InlineComment] = field(default_factory=list)
     already_posted: int = 0
     outside_diff: int = 0
`````

[Back to the shelf](README.md)
