# Fix 185: security-checker: pricing.yml accepts a negative price

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(observability): pricing.yml の価格に負の値を書けてしまう
- Bug report: number 453 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/453))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/185-security-checker-453.patch](fixes/185-security-checker-453.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/185-security-checker-453.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-185-security-checker-453.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-185-security-checker-453.html

## The bug

ModelPrice in src/security_checker/observability/cost.py had no lower limit on input_per_1m and output_per_1m. A negative price made the cost estimate negative and the budget.max_usd check lost its meaning.

## The fix

Both fields now refuse values below zero. A new file tests/unit/test_cost_negative_price.py expects a validation error from the model and a ConfigError from load_price_table for a negative price and checks that zero is still allowed.

## Files changed

- src/security_checker/observability/cost.py
- tests/unit/test_cost_negative_price.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 185-security-checker-453.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 453.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot did not run the tests. Fix 186 on this shelf changes the same file in another spot and both patches apply together.

## Search words

security-checker pricing.yml ModelPrice input_per_1m output_per_1m negative price Field ge=0 ConfigError budget max_usd

## The full patch

`````diff
diff --git a/src/security_checker/observability/cost.py b/src/security_checker/observability/cost.py
index 2ec7b56..379837f 100644
--- a/src/security_checker/observability/cost.py
+++ b/src/security_checker/observability/cost.py
@@ -9,7 +9,7 @@ import os
 from pathlib import Path
 
 import yaml
-from pydantic import BaseModel, ConfigDict, ValidationError
+from pydantic import BaseModel, ConfigDict, Field, ValidationError
 
 from security_checker.errors import ConfigError
 from security_checker.models.verdict import Usage
@@ -23,8 +23,9 @@ class ModelPrice(BaseModel):
 
     model_config = ConfigDict(frozen=True, extra="forbid")
 
-    input_per_1m: float = 0.0
-    output_per_1m: float = 0.0
+    # 負の価格は見積りを負にし、budget.max_usd の判定を無意味にする
+    input_per_1m: float = Field(default=0.0, ge=0.0)
+    output_per_1m: float = Field(default=0.0, ge=0.0)
 
     def estimate(self, usage: Usage) -> float:
         return (
diff --git a/tests/unit/test_cost_negative_price.py b/tests/unit/test_cost_negative_price.py
new file mode 100644
index 0000000..010d9be
--- /dev/null
+++ b/tests/unit/test_cost_negative_price.py
@@ -0,0 +1,34 @@
+"""pricing.yml の価格に負の値を書けないこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+from pydantic import ValidationError
+
+from security_checker.errors import ConfigError
+from security_checker.observability.cost import ModelPrice, load_price_table
+
+
+@pytest.mark.parametrize("field", ["input_per_1m", "output_per_1m"])
+def test_negative_price_is_rejected_by_the_model(field: str) -> None:
+    with pytest.raises(ValidationError):
+        ModelPrice(**{field: -0.01})
+
+
+@pytest.mark.parametrize("field", ["input_per_1m", "output_per_1m"])
+def test_negative_price_in_pricing_yml_is_a_config_error(tmp_path: Path, field: str) -> None:
+    path = tmp_path / "pricing.yml"
+    path.write_text(f"models:\n  m:\n    {field}: -1.0\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="pricing.yml"):
+        load_price_table(explicit=path)
+
+
+def test_zero_price_is_still_allowed(tmp_path: Path) -> None:
+    """対になるケース. 0 (無料・ローカル実行) は有効な価格."""
+    path = tmp_path / "pricing.yml"
+    path.write_text("models:\n  m:\n    input_per_1m: 0\n    output_per_1m: 0\n", encoding="utf-8")
+
+    assert load_price_table(explicit=path).lookup("m") == ModelPrice()
`````

[Back to the shelf](README.md)
