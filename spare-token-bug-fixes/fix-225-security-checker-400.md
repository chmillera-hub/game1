# Fix 225: security-checker: public names in observability/cost.py have no docstring (apply and default_pricing_paths and estimate and lookup)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(observability): cost.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 400 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/400))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/225-security-checker-400.patch](fixes/225-security-checker-400.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/225-security-checker-400.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-225-security-checker-400.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-225-security-checker-400.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/observability/cost.py: apply and default_pricing_paths and estimate and lookup. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/observability/cost.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/observability/cost.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 225-security-checker-400.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 400.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 185 on this shelf changes the lines right above one of the docstrings so patches 185 and 225 do not apply together: apply one and add the other change by hand. Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring cost.py apply and default_pricing_paths and estimate and lookup

## The full patch

`````diff
diff --git a/src/security_checker/observability/cost.py b/src/security_checker/observability/cost.py
index 2ec7b56..f5bc966 100644
--- a/src/security_checker/observability/cost.py
+++ b/src/security_checker/observability/cost.py
@@ -27,6 +27,7 @@ class ModelPrice(BaseModel):
     output_per_1m: float = 0.0
 
     def estimate(self, usage: Usage) -> float:
+        """`usage` の入力・出力トークン数にこの単価を掛けた見積り (USD)."""
         return (
             usage.input_tokens * self.input_per_1m + usage.output_tokens * self.output_per_1m
         ) / PER_TOKENS
@@ -40,9 +41,11 @@ class PriceTable(BaseModel):
     prices: dict[str, ModelPrice] = {}
 
     def lookup(self, model: str) -> ModelPrice | None:
+        """モデル名の完全一致で価格を引く. 無ければ None (推測しない)."""
         return self.prices.get(model)
 
     def apply(self, usage: Usage, model: str) -> Usage:
+        """`usage` に見積り額を入れた写しを返す. 価格が不明なら cost_known を False にする."""
         price = self.lookup(model)
         if price is None:
             return usage.model_copy(update={"estimated_usd": None, "cost_known": False})
@@ -50,6 +53,7 @@ class PriceTable(BaseModel):
 
 
 def default_pricing_paths(config_dir: Path | None) -> list[Path]:
+    """pricing.yml を探す場所. 設定ファイルの隣が先、次にユーザーの設定ディレクトリ."""
     base = os.environ.get("XDG_CONFIG_HOME")
     root = Path(base) if base else Path.home() / ".config"
     paths = [root / "security-checker" / PRICING_FILENAME]
`````

[Back to the shelf](README.md)
