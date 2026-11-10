# Fix 23: orm-lens: suggest-indexes proposes an index that already exists when Meta.indexes names the foreign key column

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report title: suggest-indexes proposes an index that exists when Meta.indexes names the FK column (`category_id`)
- Bug report: number 225 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/225))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/23-orm-lens-225.patch](fixes/23-orm-lens-225.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/23-orm-lens-225.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-23-orm-lens-225.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-23-orm-lens-225.html

## The bug

A Django foreign key can be named by field (category) or by column (category_id). suggest-indexes compares the two spellings as different text. An index declared with fields category_id and slug is proposed again as category and slug. filter(category_id=x) and filter(category=y) are counted as two different fields.

## The fix

cli/orm_lens/query_analyzer.py gains helpers that fold a name ending in _id onto the foreign key field name when the model really has that foreign key. The folding is applied to the lookup rows and to the index groups read from Meta. A plain field that only ends in _id keeps its name. New tests cover the three cases from the bug report. A changelog line is included.

## Files changed

- CHANGELOG.md
- cli/orm_lens/query_analyzer.py
- cli/tests/test_query_analyzer.py

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 23-orm-lens-225.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 225.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fixes 8 and 9 and 23 all add text at the same spot in CHANGELOG.md. Applying more than one needs a small manual merge of CHANGELOG.md.

## Search words

orm-lens suggest-indexes Meta.indexes category_id foreign key column alias duplicate index proposal filter(category_id=) Django

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index a30b9be..f63cf15 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -7,6 +7,10 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
 
 ## [Unreleased]
 
+### Fixed
+
+- `suggest-indexes` treats a foreign key's column name (`category_id`) and its field name (`category`) as the same field, in `Meta.indexes` and in `filter()` lookups. An index declared as `fields=["category_id", "slug"]` is no longer proposed again as `['category', 'slug']`, and the two spellings are counted as one field. A plain field that only ends in `_id` keeps its name. (#225)
+
 ## [py-1.17.1] - 2026-11-05
 
 > The orm-lens-* pre-commit hooks exist, and the old name says it is old.
diff --git a/cli/orm_lens/query_analyzer.py b/cli/orm_lens/query_analyzer.py
index 2061f5f..e661541 100644
--- a/cli/orm_lens/query_analyzer.py
+++ b/cli/orm_lens/query_analyzer.py
@@ -60,6 +60,33 @@ def _canonical_pk(field: str, pk_name: str) -> str:
     return prefix + (pk_name if body == "pk" else body)
 
 
+def _fk_field_names(model: Any) -> set[str]:
+    """Names of the model's ``ForeignKey`` / ``OneToOneField`` fields."""
+    return {
+        f.name
+        for f in model.all_fields()
+        if getattr(f, "relation_kind", None) in ("ForeignKey", "OneToOneField")
+    }
+
+
+def _canonical_fk(field: str, fk_names: set[str]) -> str:
+    """Fold the ``<fk>_id`` column alias onto the foreign key's field name.
+
+    ``filter(category_id=…)`` and ``filter(category=…)`` hit the same column, and
+    ``Meta.indexes`` may name either. Only names that really are foreign keys on
+    the model are folded, so a plain field called ``external_id`` keeps its name.
+    Keeps any ``-`` prefix, like :func:`_canonical_pk`.
+    """
+    prefix, body = ("-", field[1:]) if field.startswith("-") else ("", field)
+    if body.endswith("_id") and body[: -len("_id")] in fk_names:
+        body = body[: -len("_id")]
+    return prefix + body
+
+
+def _canonical_fk_groups(groups: list[list[str]], fk_names: set[str]) -> list[list[str]]:
+    return [[_canonical_fk(f, fk_names) for f in group] for group in groups]
+
+
 def _order_field(raw: str) -> str:
     """Normalise ``-created_at`` / ``created_at`` — keep the ``-`` prefix but
     strip any ``__`` lookup tail (rare but appears in ``order_by`` on JSONField)."""
@@ -613,9 +640,14 @@ def suggest_indexes(
     # and ``filter(id=…)`` are the same lookup and must not be counted as two
     # different fields (#60).
     pk_name = primary_key_field(target_model)
+    # ``<fk>_id`` is the column name of a foreign key, so ``filter(category_id=…)``
+    # and ``filter(category=…)`` are the same lookup too.
+    fk_names = _fk_field_names(target_model)
     for bucket in (all_filter, all_exclude, all_get, all_order_by, all_aggregate):
         for row in bucket:
-            row["fields"] = [_canonical_pk(f, pk_name) for f in row["fields"]]
+            row["fields"] = [
+                _canonical_fk(_canonical_pk(f, pk_name), fk_names) for f in row["fields"]
+            ]
 
     filter_singles, filter_composites = _summarise_filter_like(
         all_filter + all_exclude + all_get
@@ -623,15 +655,17 @@ def suggest_indexes(
     order_by_summary = _summarise_order_by(all_order_by)
     aggregate_summary = _summarise_order_by(all_aggregate)  # same shape
 
-    existing = _existing_meta_indexes(target_model.meta)
-    already_indexed = _indexed_single_fields(target_model)
+    # ``Meta.indexes`` may name a foreign key by its column (``category_id``):
+    # fold those too, so an index that exists is not proposed again.
+    existing = _canonical_fk_groups(_existing_meta_indexes(target_model.meta), fk_names)
+    already_indexed = {_canonical_fk(f, fk_names) for f in _indexed_single_fields(target_model)}
     proposed = _propose_indexes(
         filter_singles,
         filter_composites,
         order_by_summary,
         existing,
         already_indexed,
-        _covered_field_groups(target_model),
+        _canonical_fk_groups(_covered_field_groups(target_model), fk_names),
     )
 
     filter_usages: list[dict[str, Any]] = list(filter_singles)
diff --git a/cli/tests/test_query_analyzer.py b/cli/tests/test_query_analyzer.py
index 19c143b..e039741 100644
--- a/cli/tests/test_query_analyzer.py
+++ b/cli/tests/test_query_analyzer.py
@@ -177,6 +177,70 @@ class SuggestIndexesTest(unittest.TestCase):
             # …and the primary key is already indexed, so nothing is proposed.
             self.assertNotIn(["id"], [p["fields"] for p in result["proposed_indexes"]])
 
+    _SHOP_MODELS = (
+        "from django.db import models\n\n\n"
+        "class Category(models.Model):\n"
+        "    title = models.CharField(max_length=50)\n\n\n"
+        "class Product(models.Model):\n"
+        "    category = models.ForeignKey(Category, on_delete=models.CASCADE)\n"
+        "    slug = models.SlugField()\n"
+        "    external_id = models.CharField(max_length=20)\n\n"
+        "    class Meta:\n"
+        "        indexes = [\n"
+        "            models.Index(fields=[\"category_id\", \"slug\"], name=\"product_cat_slug\"),\n"
+        "        ]\n"
+    )
+
+    def test_meta_index_naming_the_fk_column_is_not_proposed_again(self) -> None:
+        # ``Meta.indexes`` names the FK by its column (``category_id``); the
+        # lookups use the field name (``category``). Same column, same index.
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            _write(root / "shop" / "models.py", self._SHOP_MODELS)
+            _write(
+                root / "shop" / "views.py",
+                "from .models import Product\n\n"
+                "def detail(category, slug):\n"
+                "    return Product.objects.get(category=category, slug=slug)\n\n"
+                "def exists(category, slug):\n"
+                "    return Product.objects.filter(category=category, slug=slug).exists()\n",
+            )
+
+            result = suggest_indexes("shop", "Product", str(root))
+
+            proposed = [p["fields"] for p in result["proposed_indexes"]]
+            self.assertNotIn(["category", "slug"], proposed)
+            self.assertNotIn(["category_id", "slug"], proposed)
+
+    def test_fk_column_alias_counts_as_the_fk_field(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            _write(root / "shop" / "models.py", self._SHOP_MODELS)
+            _write(
+                root / "shop" / "views.py",
+                "from .models import Product\n\n"
+                "def by_id(x):\n"
+                "    return Product.objects.filter(category_id=x)\n\n"
+                "def by_object(y):\n"
+                "    return Product.objects.filter(category=y)\n\n"
+                "def by_external(z):\n"
+                "    return Product.objects.filter(external_id=z)\n",
+            )
+
+            result = suggest_indexes("shop", "Product", str(root))
+
+            fields = {
+                u["field"]: u["sites"]
+                for u in result["filter_usages"]
+                if not u.get("composite")
+            }
+            self.assertEqual(fields.get("category"), 2)
+            self.assertNotIn("category_id", fields)
+            # A plain field that merely ends in ``_id`` keeps its own name.
+            self.assertEqual(fields.get("external_id"), 1)
+            self.assertNotIn("external", fields)
+
+
 
 if __name__ == "__main__":
     unittest.main()
`````

[Back to the shelf](README.md)
