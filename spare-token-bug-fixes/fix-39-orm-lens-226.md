# Fix 39: orm-lens: a plain class above an if block hides every model declared below it

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report title: Parser: a plain class above `if not is_model_registered(...)` hides every model below it
- Bug report: number 226 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/226))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/39-orm-lens-226.patch](fixes/39-orm-lens-226.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/39-orm-lens-226.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-39-orm-lens-226.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-39-orm-lens-226.html

## The bug

The parser read the body of a class at column 0 until the next class at column 0. An exception class at the top of models.py ran over the following if blocks and swallowed the models declared inside them. django-oscar's basket models went missing from every command.

## The fix

cli/orm_lens/parser.py gains a pattern for a module-level statement at column 0: a block header (if or elif or else or try or except or finally or with) that ends in a colon or a def or a decorator. The body of a column-0 class now also ends at such a line. cli/tests/test_conditional_models.py gains a test with the oscar basket shape and a test that a model above an if block keeps only its own fields and a guard test with a column-0 comment and column-0 text inside a triple-quoted string. A changelog entry is included.

## Files changed

- CHANGELOG.md
- cli/orm_lens/parser.py
- cli/tests/test_conditional_models.py

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 39-orm-lens-226.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 226.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report offers two options and the fix takes the first one. The bug report says the project's golden snapshot tests will show whether files without conditional models still parse as before. Nobody ran the golden snapshot tests. A block header that spans several lines does not end the class body. Fixes 27 and 28 and 39 and 40 each add an entry to CHANGELOG.md at different spots and the chatbot confirmed that all four patches apply together. Fixes 39 and 40 both change cli/orm_lens/parser.py in different places.

## Search words

orm-lens parser _collect_defs column-0 class body is_model_registered conditional models django-oscar basket Basket Line LineAttribute hidden

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index dccd535..2bcc6d9 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,16 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
   longer gets `select_related` advice (a `FieldError` at runtime), a real
   foreign key is reported at `high` confidence, and `suggest-indexes` counts
   these filter sites (#222).
+- **Parser: a plain class above `if not is_model_registered(...)` no longer
+  hides the models below it**
+  ([#226](https://github.com/FROWNINGdev/orm-lens/issues/226)). The body of a
+  column-0 class only ended at the next column-0 `class`, so an exception
+  class at the top of a `models.py` ran over the following `if` blocks and
+  swallowed the models declared inside them (django-oscar's `basket.Basket`,
+  `basket.Line` and `basket.LineAttribute`). The body now also ends at a
+  column-0 block header (`if`, `elif`, `else`, `try`, `except`, `finally`,
+  `with`), `def` or decorator. Comments and text inside a triple-quoted
+  string at column 0 do not end it.
 - **suggest-indexes: `<fk>_id` and `<fk>` are the same column.** A
   `Meta.indexes` entry written with the column name (`fields=["category_id",
   "slug"]`) now covers `filter(category=..., slug=...)`, so the same index is
diff --git a/cli/orm_lens/parser.py b/cli/orm_lens/parser.py
index 6023ffd..d417779 100644
--- a/cli/orm_lens/parser.py
+++ b/cli/orm_lens/parser.py
@@ -402,6 +402,18 @@ def _read_balanced_args(lines: Sequence[str], start: int):
     return "".join(parts).lstrip("("), len(lines) - 1
 
 
+#: A column-0 line that starts a new module-level statement after a class:
+#: a block header (``if ...:``, ``try:``, ``with ...:`` and their branches),
+#: a ``def`` or a decorator. The header forms must end in ``:`` so that prose
+#: at column 0 inside a triple-quoted string ("if you need ...") is not taken
+#: for one.
+_MODULE_STATEMENT_RE = re.compile(
+    r"^(?:(?:if|elif|else|try|except|finally|with)\b[^#]*:\s*(?:#.*)?$"
+    r"|(?:async\s+)?def\s+\w+\s*\("
+    r"|@[A-Za-z_])"
+)
+
+
 def _encloses_only_blocks(lines: Sequence[str], idx: int, indent: int) -> bool:
     """Is the indented statement at ``lines[idx]`` still at module level?
 
@@ -556,8 +568,8 @@ def _collect_defs(file_path: str, content: str) -> list[ParsedModel]:
         while j < len(lines):
             inner = lines[j]
             # An indented class ends where the source dedents back out of it.
-            # Column-0 classes keep the original terminator exactly, so files
-            # without conditional models parse byte-for-byte as before.
+            # A column-0 class ends at the next column-0 ``class``, as it
+            # always did, or at the next module-level statement (below).
             if (
                 class_indent
                 and inner.strip()
@@ -566,6 +578,12 @@ def _collect_defs(file_path: str, content: str) -> list[ParsedModel]:
                 break
             if re.match(r"^class\s+", inner) and not re.match(r"^\s+class", inner):
                 break
+            # A column-0 class also ends at the next module-level block, def
+            # or decorator. Without this the body of a plain class ran over
+            # every ``if not is_model_registered(...)`` block below it and
+            # swallowed the models declared inside them.
+            if not class_indent and _MODULE_STATEMENT_RE.match(inner):
+                break
             if not inner.strip():
                 j += 1
                 continue
diff --git a/cli/tests/test_conditional_models.py b/cli/tests/test_conditional_models.py
index f1df11c..5cec05a 100644
--- a/cli/tests/test_conditional_models.py
+++ b/cli/tests/test_conditional_models.py
@@ -160,5 +160,80 @@ class OtherBlockStatementsTest(unittest.TestCase):
         )
 
 
+OSCAR_BASKET_SHAPE = '''
+from django.db import models
+from oscar.core.loading import is_model_registered
+
+
+class InvalidBasketLineError(Exception):
+    pass
+
+
+if not is_model_registered("basket", "Basket"):
+
+    class Basket(models.Model):
+        owner = models.CharField(max_length=50)
+
+
+if not is_model_registered("basket", "Line"):
+
+    class Line(models.Model):
+        quantity = models.PositiveIntegerField()
+
+
+if not is_model_registered("basket", "LineAttribute"):
+
+    class LineAttribute(models.Model):
+        value = models.CharField(max_length=255)
+'''
+
+
+class PlainClassAboveConditionalModelsTest(unittest.TestCase):
+    """A column-0 class must not swallow the ``if`` blocks below it (#226)."""
+
+    def test_models_below_a_plain_class_are_found(self) -> None:
+        got = parse_models_file("basket/models.py", OSCAR_BASKET_SHAPE)
+        self.assertEqual([m.name for m in got], ["Basket", "Line", "LineAttribute"])
+        fields = {m.name: [f.name for f in m.fields] for m in got}
+        self.assertEqual(
+            fields,
+            {"Basket": ["owner"], "Line": ["quantity"], "LineAttribute": ["value"]},
+        )
+
+    def test_a_model_above_an_if_block_keeps_only_its_own_fields(self) -> None:
+        src = (
+            "from django.db import models\n"
+            "\n"
+            "class Shop(models.Model):\n"
+            "    name = models.CharField(max_length=50)\n"
+            "\n"
+            "if True:\n"
+            "    class Basket(models.Model):\n"
+            "        owner = models.CharField(max_length=50)\n"
+        )
+        got = parse_models_file("shop/models.py", src)
+        self.assertEqual([m.name for m in got], ["Shop", "Basket"])
+        self.assertEqual([f.name for f in got[0].fields], ["name"])
+
+    def test_column_0_comment_and_string_text_do_not_end_the_body(self) -> None:
+        """Guard: only a real statement at column 0 ends a class body."""
+        src = (
+            "from django.db import models\n"
+            "\n"
+            "class Widget(models.Model):\n"
+            "    sku = models.CharField(max_length=20)\n"
+            "# a comment at column 0\n"
+            "    def describe(self):\n"
+            '        return """\n'
+            "if you read this, the text sits at column 0\n"
+            "with nothing after it\n"
+            '"""\n'
+            "    price = models.IntegerField()\n"
+        )
+        got = parse_models_file("shop/models.py", src)
+        self.assertEqual([m.name for m in got], ["Widget"])
+        self.assertEqual([f.name for f in got[0].fields], ["sku", "price"])
+
+
 if __name__ == "__main__":
     unittest.main()
`````

[Back to the shelf](README.md)
