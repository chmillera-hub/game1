# Fix 40: orm-lens: inherited fields come from the wrong abstract base when two apps define a base with the same name

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report title: Inherited fields come from the wrong abstract base when two apps define a base with the same name
- Bug report: number 227 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/227))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/40-orm-lens-227.patch](fixes/40-orm-lens-227.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/40-orm-lens-227.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-40-orm-lens-227.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-40-orm-lens-227.html

## The bug

The parser looked up an abstract base by class name across the whole workspace and the first class with that name won. django-oscar defines AbstractLine in basket and in order. order.Line received the basket line's fields and the drift command reported blocking drift that does not exist.

## The fix

cli/orm_lens/parser.py keeps every definition of a class name and gains _pick_base. When a base name has several definitions the one in the same folder as the subclass is used. With none in that folder the first definition is used as before. A name with one definition resolves as before. cli/tests/test_abstract_inheritance_and_indexes.py gains two tests built from the example in the bug report. A changelog entry is included.

## Files changed

- CHANGELOG.md
- cli/orm_lens/parser.py
- cli/tests/test_abstract_inheritance_and_indexes.py

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 40-orm-lens-227.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 227.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- This fix covers step 1 of the three steps in the bug report (same folder). The bug report calls step 1 a good first change and says step 2 (follow the import) can come later. Step 2 is not included. The bug report rates the work as medium and asks for care that results stay the same for projects with unique names. No scratch check was run for this fix. Fixes 39 and 40 both change cli/orm_lens/parser.py in different places and apply together.

## Search words

orm-lens abstract base same name two apps AbstractLine basket order wishlists inherited fields _attach_inherited_fields _abstract_bases_fields drift netbox ComponentModel

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index dccd535..4862c87 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -30,6 +30,14 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
   no longer proposed again, and `filter(category_id=...)` and
   `filter(category=...)` are counted as one field. Only real ForeignKey /
   OneToOneField names are folded; a plain `external_id` keeps its name (#225).
+- **Inherited fields come from the abstract base in the model's own app**
+  ([#227](https://github.com/FROWNINGdev/orm-lens/issues/227)). A base was
+  looked up by class name across the whole workspace and the first class
+  with that name won, so with an `AbstractLine` in both `basket` and `order`
+  (django-oscar) `order.Line` got the basket line's columns and `drift`
+  reported blocking drift. When a base name has several definitions, the one
+  in the subclass's own directory is now used; with none there the first
+  definition is used, as before. Names defined once resolve as they did.
 - **signals: `@receiver([post_save, post_delete], ...)` produces one edge per signal.** `signal_graph` read the first decorator argument as a single dotted name, so a list or tuple became one `<unknown>` `[custom]` edge and a list-form `post_delete` receiver vanished from the DB_CASCADE `skipped_receivers` warning. `_signal_arg_names` now returns one name per readable element, and the decorator branch adds one edge per name. `<unknown>` remains for the case where nothing is readable. `signal.connect()` is unchanged.
 - **drift: `objects = models.Manager()` is no longer a model field.** Both parsers treated any `models.<Name>(...)` assignment as a field, so an explicit default manager showed up in `scan`, `describe`, ER diagrams, and, worst of all, blocking drift. `Manager` and `QuerySet` are skipped in both `cli/orm_lens/parser.py` and `src/parser.ts`, with the whole call skipped so multi-line declarations do not leak their arguments. `TaggableManager` stays a relation. The saleor golden snapshot drops the `objects` field that its `Category` model declares.
 
diff --git a/cli/orm_lens/parser.py b/cli/orm_lens/parser.py
index 6023ffd..fcbeedb 100644
--- a/cli/orm_lens/parser.py
+++ b/cli/orm_lens/parser.py
@@ -677,9 +677,28 @@ def _is_abstract(model: ParsedModel) -> bool:
     return model.meta.get("abstract", "").strip() in ("True", "1", "true")
 
 
+def _pick_base(model: ParsedModel, candidates: list[ParsedModel]) -> ParsedModel | None:
+    """The definition a base-class name refers to, seen from ``model``.
+
+    Pluggable apps reuse base names (django-oscar has an ``AbstractLine`` in
+    basket, order and wishlists), so a name alone can mean several classes.
+    A definition in the subclass's own directory wins; with none there the
+    first definition is used, as before. A name with one definition resolves
+    exactly as it always did.
+    """
+    if not candidates:
+        return None
+    if len(candidates) > 1:
+        here = os.path.dirname(model.file_path)
+        for candidate in candidates:
+            if candidate is not model and os.path.dirname(candidate.file_path) == here:
+                return candidate
+    return candidates[0]
+
+
 def _abstract_bases_fields(
     model: ParsedModel,
-    by_name: dict[str, ParsedModel],
+    by_name: dict[str, list[ParsedModel]],
     stack: tuple[str, ...] = (),
 ) -> list[ParsedField]:
     """Fields ``model`` inherits from its abstract bases, parent-first.
@@ -700,7 +719,7 @@ def _abstract_bases_fields(
         tail = base.split(".")[-1]
         if tail in stack:
             continue
-        parent = by_name.get(tail)
+        parent = _pick_base(model, by_name.get(tail, []))
         if parent is None or parent is model or not _is_abstract(parent):
             continue
         contributed = [
@@ -726,11 +745,12 @@ def _attach_inherited_fields(all_defs: list[ParsedModel]) -> None:
     the list. A field the class declares itself shadows the inherited one of
     the same name, exactly as an override does in Django.
     """
-    by_name: dict[str, ParsedModel] = {}
+    by_name: dict[str, list[ParsedModel]] = {}
     for m in all_defs:
-        # First definition wins when two files declare the same class name;
-        # the parser has no import graph to disambiguate with.
-        by_name.setdefault(m.name, m)
+        # Every definition of a name is kept, in scan order. ``_pick_base``
+        # prefers the one in the subclass's own directory and otherwise takes
+        # the first; the parser has no import graph to disambiguate further.
+        by_name.setdefault(m.name, []).append(m)
     for m in all_defs:
         own = {f.name for f in m.fields}
         m.inherited_fields = [
diff --git a/cli/tests/test_abstract_inheritance_and_indexes.py b/cli/tests/test_abstract_inheritance_and_indexes.py
index 3de31f4..c1279bf 100644
--- a/cli/tests/test_abstract_inheritance_and_indexes.py
+++ b/cli/tests/test_abstract_inheritance_and_indexes.py
@@ -420,6 +420,76 @@ class AbstractModelsFileTest(unittest.TestCase):
             self.assertEqual(names, ["Product"])
 
 
+def _abstract_line(field: str) -> str:
+    return (
+        "from django.db import models\n"
+        "\n"
+        "\n"
+        "class AbstractLine(models.Model):\n"
+        f"    {field} = models.CharField(max_length=50)\n"
+        "\n"
+        "    class Meta:\n"
+        "        abstract = True\n"
+    )
+
+
+def _line_migration(field: str) -> str:
+    return (
+        "from django.db import migrations, models\n"
+        "\n"
+        "\n"
+        "class Migration(migrations.Migration):\n"
+        "    initial = True\n"
+        "    dependencies = []\n"
+        "    operations = [\n"
+        '        migrations.CreateModel(name="Line", fields=[\n'
+        '            ("id", models.BigAutoField(primary_key=True)),\n'
+        f'            ("{field}", models.CharField(max_length=50)),\n'
+        "        ]),\n"
+        "    ]\n"
+    )
+
+
+class SameBaseNameInTwoAppsTest(unittest.TestCase):
+    """Two apps each define ``AbstractLine``; each ``Line`` gets its own (#227)."""
+
+    def _layout(self, root: Path) -> None:
+        for app, field in (("basket", "basket"), ("order", "title")):
+            _write(root / app / "__init__.py", "")
+            _write(root / app / "abstract_models.py", _abstract_line(field))
+            _write(
+                root / app / "models.py",
+                f"from {app}.abstract_models import AbstractLine\n"
+                "\n"
+                "\n"
+                "class Line(AbstractLine):\n"
+                "    pass\n",
+            )
+            _write(root / app / "migrations" / "__init__.py", "")
+            _write(root / app / "migrations" / "0001_initial.py", _line_migration(field))
+
+    def test_each_line_inherits_from_the_base_in_its_own_app(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            self._layout(root)
+            index = scan_workspace(str(root))
+            fields = {
+                app.name: [f.name for f in m.all_fields()]
+                for app in index.apps
+                for m in app.models
+                if m.name == "Line"
+            }
+            self.assertEqual(fields, {"basket": ["basket"], "order": ["title"]})
+
+    def test_drift_is_clean(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            self._layout(root)
+            report = detect_drift(root)
+            self.assertEqual(report.drifted, [])
+            self.assertEqual(report.blocking_count, 0)
+
+
 class WorkspaceInheritanceTest(unittest.TestCase):
     def test_abstract_base_in_another_file_still_donates(self) -> None:
         """Cross-file resolution already worked for *recognition* (#20).
`````

[Back to the shelf](README.md)
