# Fix 250: security-checker: public names in review/prompts/__init__.py have no docstring (render_judge_system and render_user and sanitized)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(review): __init__.py の公開クラス・メソッド 3 個に docstring が無い
- Bug report: number 418 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/418))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/250-security-checker-418.patch](fixes/250-security-checker-418.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/250-security-checker-418.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-250-security-checker-418.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-250-security-checker-418.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/review/prompts/__init__.py: render_judge_system and render_user and sanitized. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/review/prompts/__init__.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/review/prompts/__init__.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 250-security-checker-418.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 418.

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

security-checker docstring D1 ruff missing docstring __init__.py render_judge_system and render_user and sanitized

## The full patch

`````diff
diff --git a/src/security_checker/review/prompts/__init__.py b/src/security_checker/review/prompts/__init__.py
index 7b36d5d..939bad8 100644
--- a/src/security_checker/review/prompts/__init__.py
+++ b/src/security_checker/review/prompts/__init__.py
@@ -44,6 +44,7 @@ def render_system(language: str = DEFAULT_LANGUAGE) -> str:
 
 
 def render_user(task: ReviewTask, schema: dict[str, object]) -> str:
+    """Reviewer に送る user プロンプトを作る. 候補・コードの文脈・応答のスキーマを含む."""
     primary = task.code_context.primary
     return (
         _environment()
@@ -130,6 +131,7 @@ class PeerOpinion:
     needs_more_context: list[str] = field(default_factory=list)
 
     def sanitized(self) -> dict[str, Any]:
+        """テンプレートに渡す形. 自由記述の項目はデリミタをエスケープしてある."""
         return {
             "label": self.label,
             "vulnerable": self.vulnerable,
@@ -144,6 +146,7 @@ class PeerOpinion:
 
 
 def render_judge_system(language: str = DEFAULT_LANGUAGE) -> str:
+    """Judge 用の system プロンプトを作る. `language` に応じて出力言語の指示を足す."""
     base = _environment().get_template(f"judge_system.{PROMPT_VERSION}.jinja").render()
     instruction = output_language_instruction(language)
     return f"{base}\n{instruction}\n" if instruction else base
`````

[Back to the shelf](README.md)
