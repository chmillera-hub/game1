# Fix 28: orm-lens: suggest-indexes counts lookups from test files and proposes indexes that production code never uses

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report title: suggest-indexes counts queries from test modules and proposes indexes production never uses
- Bug report: number 224 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/224))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/28-orm-lens-224.patch](fixes/28-orm-lens-224.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/28-orm-lens-224.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-28-orm-lens-224.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-28-orm-lens-224.html

## The bug

suggest-indexes proposes an index when a field is filtered on in two or more places. Every .py file was counted including test files. A field that only tests filter on reached the threshold and got an index proposal. An unused index still slows down every write.

## The fix

suggest_indexes() in cli/orm_lens/query_analyzer.py gains an include_tests parameter that defaults to False and skips test files with the existing _is_test_file helper. cli/orm_lens/cli.py gains the --include-tests option on suggest-indexes with the same help text as on nplusone as the bug report asks. Three new tests in cli/tests/test_query_analyzer.py cover the example from the bug report. A changelog entry is included.

## Files changed

- CHANGELOG.md
- cli/orm_lens/cli.py
- cli/orm_lens/query_analyzer.py
- cli/tests/test_query_analyzer.py

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 28-orm-lens-224.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 224.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The default behaviour changes: lookups in test files no longer count unless --include-tests is given. The bug report asks for that change. The MCP tool calls the same function and gets the new default with no new argument. Fixes 27 and 28 both add an entry to CHANGELOG.md at different spots and apply together.

## Search words

orm-lens suggest-indexes include-tests test modules _is_test_file Meta.indexes proposal 2 filter sites healthchecks

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index dccd535..4f7f57a 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -17,6 +17,14 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
   (`basket_Line`, `order_Line`), and relation ends resolve to the model in
   the field's own app, or the app named in the reference (`"order.Line"`).
   Diagrams without duplicate names are unchanged.
+- **`orm-lens suggest-indexes` skips test modules by default**
+  ([#224](https://github.com/FROWNINGdev/orm-lens/issues/224)). Every `.py`
+  file was counted, so a field that only tests filter on (`get(name="Mug")`)
+  reached the 2-site threshold and got an index proposal that production
+  never uses. Test modules are now left out, the same set `nplusone` skips
+  (`test_*.py`, `*_test.py`, `tests.py`, `conftest.py`, anything under
+  `tests/` or `test/`). `--include-tests` (and `include_tests=True` on
+  `suggest_indexes()`) counts them again. The MCP tool gets the new default.
 - **nplusone / suggest-indexes: `models.Nap.objects` is a model.** Projects
   that import the models module (`from core import models`) and write
   `models.Nap.objects.filter(...)` now get the model resolved like
diff --git a/cli/orm_lens/cli.py b/cli/orm_lens/cli.py
index 185e8da..9f8af33 100644
--- a/cli/orm_lens/cli.py
+++ b/cli/orm_lens/cli.py
@@ -333,7 +333,9 @@ def _cmd_suggest_indexes(args: argparse.Namespace) -> int:
         print(f"error: model {args.model!r} not found", file=sys.stderr)
         return 2
     app_label = next((a.name for a in idx.apps if model in a.models), "")
-    result = suggest_indexes(app_label, model.name, args.path, index=idx)
+    result = suggest_indexes(
+        app_label, model.name, args.path, index=idx, include_tests=args.include_tests
+    )
     if args.format == "json":
         print(json.dumps(result, indent=2, ensure_ascii=False))
         return 0
@@ -872,6 +874,15 @@ def build_parser() -> argparse.ArgumentParser:
     sidx.add_argument(
         "--format", "-f", choices=("text", "json"), default="text"
     )
+    sidx.add_argument(
+        "--include-tests",
+        action="store_true",
+        help=(
+            "Also scan test modules (test_*.py, *_test.py, tests.py, conftest.py "
+            "and anything under tests/ or test/). Skipped by default: a query "
+            "per row in a test is not a production N+1"
+        ),
+    )
     sidx.set_defaults(func=_cmd_suggest_indexes)
 
     signals = sub.add_parser(
diff --git a/cli/orm_lens/query_analyzer.py b/cli/orm_lens/query_analyzer.py
index 4ab33f6..85c2ec2 100644
--- a/cli/orm_lens/query_analyzer.py
+++ b/cli/orm_lens/query_analyzer.py
@@ -590,12 +590,17 @@ def suggest_indexes(
     model_name: str,
     root: str,
     index: WorkspaceIndex | None = None,
+    include_tests: bool = False,
 ) -> dict[str, Any]:
     """Analyse the workspace for QuerySet usage of ``app_label.model_name``.
 
     Returns the dict shape documented in the MCP tool spec. If the model
     isn't found in the parsed workspace, returns an ``error`` key rather
     than raising — matches the existing tool conventions.
+
+    Test modules are skipped unless ``include_tests``: a test filters on
+    whatever is convenient to assert, and an index that only tests would
+    use still costs every write.
     """
     from .parser import DEFAULT_EXCLUDES, scan_workspace
 
@@ -630,6 +635,13 @@ def suggest_indexes(
     all_aggregate: list[dict[str, Any]] = []
 
     for py in _iter_py_files(root_path):
+        if not include_tests:
+            try:
+                rel = py.relative_to(root_path)
+            except ValueError:
+                rel = py
+            if _is_test_file(rel):
+                continue
         try:
             source = py.read_text(encoding="utf-8", errors="replace")
         except OSError:
diff --git a/cli/tests/test_query_analyzer.py b/cli/tests/test_query_analyzer.py
index 52627c4..4351ed3 100644
--- a/cli/tests/test_query_analyzer.py
+++ b/cli/tests/test_query_analyzer.py
@@ -287,5 +287,68 @@ class ForeignKeyColumnAliasTest(unittest.TestCase):
             self.assertIn(["external_id"], [p["fields"] for p in result["proposed_indexes"]])
 
 
+class TestModulesAreSkippedTest(unittest.TestCase):
+    """Lookups that only tests make do not earn an index (#224)."""
+
+    _MODELS = (
+        "from django.db import models\n\n\n"
+        "class Product(models.Model):\n"
+        "    slug = models.SlugField()\n"
+        "    name = models.CharField(max_length=100)\n"
+    )
+    _TESTS = (
+        "from shop.models import Product\n\n\n"
+        "def test_lookup_by_name():\n"
+        '    assert Product.objects.filter(name="Mug").exists()\n\n\n'
+        "def test_get_by_name():\n"
+        '    Product.objects.get(name="Mug")\n'
+    )
+
+    def _workspace(self, root: Path) -> None:
+        _write(root / "shop" / "models.py", self._MODELS)
+        _write(root / "shop" / "tests" / "test_products.py", self._TESTS)
+
+    def test_usage_only_in_tests_proposes_nothing(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            self._workspace(root)
+
+            result = suggest_indexes("shop", "Product", str(root))
+
+            self.assertEqual(result["proposed_indexes"], [])
+            self.assertEqual(result["filter_usages"], [])
+
+    def test_include_tests_brings_the_proposal_back(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            self._workspace(root)
+
+            result = suggest_indexes("shop", "Product", str(root), include_tests=True)
+
+            proposed = [p["fields"] for p in result["proposed_indexes"]]
+            self.assertIn(["name"], proposed)
+
+    def test_production_usage_still_counts_beside_tests(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            self._workspace(root)
+            _write(
+                root / "shop" / "views.py",
+                "from .models import Product\n"
+                "def a(name):\n"
+                "    return Product.objects.get(name=name)\n"
+                "def b(name):\n"
+                "    return Product.objects.filter(name=name)\n",
+            )
+
+            result = suggest_indexes("shop", "Product", str(root))
+
+            proposed = [p["fields"] for p in result["proposed_indexes"]]
+            self.assertIn(["name"], proposed)
+            # The two test-module lookups are not added to the two real ones.
+            usage = next(u for u in result["filter_usages"] if u.get("field") == "name")
+            self.assertEqual(usage["sites"], 2)
+
+
 if __name__ == "__main__":
     unittest.main()
`````

[Back to the shelf](README.md)
