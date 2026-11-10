# Fix 8: orm-lens: objects = models.Manager() is parsed as a model field and drift fails the build

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report: number 219 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/219))
- Project license: MIT
- Language: Python and TypeScript
- Test included: yes
- Patch file: [fixes/8-orm-lens-219.patch](fixes/8-orm-lens-219.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/8-orm-lens-219.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-8-orm-lens-219.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-8-orm-lens-219.html

## The bug

A Django model that declares an explicit manager such as objects = models.Manager() gets a field named objects of type Manager. The drift command then reports "declared but never migrated: objects" and exits with code 1 on a healthy project. The ER diagram shows Manager objects as a column.

## The fix

The fix adds a small set named _NOT_A_FIELD holding Manager and QuerySet in cli/orm_lens/parser.py and skips those assignments including calls that span several lines. TaggableManager stays a relation. The same change is mirrored in the TypeScript parser src/parser.ts. The stored snapshot saleor.snapshot.json loses its one Manager entry. New tests cover the parser and the drift command. A changelog line is included.

## Files changed

- CHANGELOG.md
- cli/orm_lens/parser.py
- cli/tests/fixtures/golden/saleor.snapshot.json
- cli/tests/test_manager_is_not_a_field.py
- src/parser.ts
- test/taggable-manager.test.js

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 8-orm-lens-219.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 219.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 8 and fix 9 both add text at the same spot in CHANGELOG.md. Applying both needs a small manual merge of CHANGELOG.md.

## Search words

orm-lens drift declared but never migrated: objects models.Manager() parsed as a field Manager objects ER diagram blocking exit code 1 Django

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index a30b9be..9ce5907 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -7,6 +7,10 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
 
 ## [Unreleased]
 
+### Fixed
+
+- An explicit manager in a model body (`objects = models.Manager()`) is no longer parsed as a field of type `Manager`. `drift` used to report it as blocking and exit 1 on a healthy project, and the ER diagram showed it as a column. `TaggableManager` is still a relation. (#219)
+
 ## [py-1.17.1] - 2026-11-05
 
 > The orm-lens-* pre-commit hooks exist, and the old name says it is old.
diff --git a/cli/orm_lens/parser.py b/cli/orm_lens/parser.py
index e1cc0b3..2653869 100644
--- a/cli/orm_lens/parser.py
+++ b/cli/orm_lens/parser.py
@@ -74,6 +74,11 @@ NON_MODEL_TAIL = re.compile(
     r"Backend|Command)$"
 )
 
+# ``models.<Name>(...)`` assignments in a model body that are not fields.
+# ``objects = models.Manager()`` matches FIELD_RE but never becomes a column.
+# ``TaggableManager`` is not listed: it is a real relation.
+_NOT_A_FIELD = frozenset({"Manager", "QuerySet"})
+
 BARE_FIELD_TYPES = "|".join(
     [
         "CharField", "TextField", "SlugField", "EmailField", "URLField", "UUIDField",
@@ -583,6 +588,9 @@ def _collect_defs(file_path: str, content: str) -> list[ParsedModel]:
             if fm:
                 fname, ftype = fm.group(1), fm.group(2)
                 args_block, end_idx = _read_balanced_args(lines, j)
+                if ftype in _NOT_A_FIELD:
+                    j = end_idx + 1
+                    continue
                 relation_kind = (
                     "ManyToManyField"
                     if ftype == "TaggableManager"
diff --git a/cli/tests/fixtures/golden/saleor.snapshot.json b/cli/tests/fixtures/golden/saleor.snapshot.json
index 21b5c3b..87d80aa 100644
--- a/cli/tests/fixtures/golden/saleor.snapshot.json
+++ b/cli/tests/fixtures/golden/saleor.snapshot.json
@@ -917,13 +917,6 @@
               "lineNumber": 68,
               "name": "background_image_alt",
               "type": "CharField"
-            },
-            {
-              "args": "",
-              "isRelation": false,
-              "lineNumber": 70,
-              "name": "objects",
-              "type": "Manager"
             }
           ],
           "filePath": "saleor/product/models.py",
diff --git a/cli/tests/test_manager_is_not_a_field.py b/cli/tests/test_manager_is_not_a_field.py
new file mode 100644
index 0000000..a20d571
--- /dev/null
+++ b/cli/tests/test_manager_is_not_a_field.py
@@ -0,0 +1,99 @@
+"""A manager assignment in a model body is not a field.
+
+``objects = models.Manager()`` matches ``FIELD_RE`` (``name = models.X(``), so
+it used to be recorded as a field of type ``Manager``. No migration ever
+creates an ``objects`` column, so ``drift`` reported it as blocking and failed
+the build on a healthy project.
+
+Run: python -m unittest discover cli/tests -v
+"""
+
+from __future__ import annotations
+
+import tempfile
+import unittest
+from pathlib import Path
+
+from orm_lens.drift import detect_drift
+from orm_lens.parser import parse_models_file
+
+
+class ManagerIsNotAFieldTest(unittest.TestCase):
+    def test_default_manager_is_skipped(self) -> None:
+        src = (
+            "from django.db import models\n\n"
+            "class Note(models.Model):\n"
+            "    text = models.TextField()\n\n"
+            "    objects = models.Manager()\n"
+        )
+        models = parse_models_file("notes/models.py", src)
+        self.assertEqual([f.name for f in models[0].fields], ["text"])
+
+    def test_multi_line_manager_call_is_skipped_as_a_whole(self) -> None:
+        src = (
+            "from django.db import models\n\n"
+            "class Note(models.Model):\n"
+            "    all_objects = models.Manager(\n"
+            "    )\n"
+            "    text = models.TextField()\n"
+            "    qs = models.QuerySet()\n"
+            "    title = models.CharField(max_length=10)\n"
+        )
+        models = parse_models_file("notes/models.py", src)
+        self.assertEqual([f.name for f in models[0].fields], ["text", "title"])
+
+    def test_taggable_manager_stays_a_relation(self) -> None:
+        src = (
+            "from django.db import models\n"
+            "from taggit.managers import TaggableManager\n\n"
+            "class Post(models.Model):\n"
+            "    objects = models.Manager()\n"
+            "    tags = TaggableManager()\n"
+        )
+        models = parse_models_file("blog/models.py", src)
+        self.assertEqual([f.name for f in models[0].fields], ["tags"])
+        self.assertTrue(models[0].fields[0].is_relation)
+
+
+class ManagerDoesNotDriftTest(unittest.TestCase):
+    def test_explicit_default_manager_reports_no_drift(self) -> None:
+        with tempfile.TemporaryDirectory() as tmp:
+            app = Path(tmp) / "notes"
+            (app / "migrations").mkdir(parents=True)
+            (app / "__init__.py").write_text("", encoding="utf-8")
+            (app / "migrations" / "__init__.py").write_text("", encoding="utf-8")
+            (app / "migrations" / "0001_initial.py").write_text(
+                "from django.db import migrations, models\n"
+                "\n"
+                "class Migration(migrations.Migration):\n"
+                "    initial = True\n"
+                "    dependencies = []\n"
+                "    operations = [\n"
+                "        migrations.CreateModel(\n"
+                "            name='Note',\n"
+                "            fields=[\n"
+                "                ('id', models.AutoField(primary_key=True)),\n"
+                "                ('text', models.TextField()),\n"
+                "            ],\n"
+                "        ),\n"
+                "    ]\n",
+                encoding="utf-8",
+            )
+            (app / "models.py").write_text(
+                "from django.db import models\n"
+                "\n"
+                "class Note(models.Model):\n"
+                "    text = models.TextField()\n"
+                "\n"
+                "    objects = models.Manager()\n",
+                encoding="utf-8",
+            )
+
+            payload = detect_drift(tmp).to_dict()
+
+            self.assertEqual(payload["drifted"], [], payload["drifted"])
+            self.assertEqual(payload["summary"]["blocking"], 0)
+
+
+if __name__ == "__main__":
+    unittest.main()
diff --git a/src/parser.ts b/src/parser.ts
index 542dd43..8d72887 100644
--- a/src/parser.ts
+++ b/src/parser.ts
@@ -83,6 +83,12 @@ export function resolveRelatedTail(
 const NON_MODEL_TAIL =
   /^(ModelAdmin|ModelForm|ModelSerializer|ModelChoiceField|ModelMultipleChoiceField|Serializer|Form|Admin|View|ViewSet|Manager|QuerySet|Config|AppConfig|Response|Handler|Middleware|Backend|Command)$/;
 
+// `models.<Name>(...)` assignments in a model body that are not fields.
+// `objects = models.Manager()` matches FIELD_RE but never becomes a column.
+// `TaggableManager` is not listed: it is a real relation.
+// Mirrors `_NOT_A_FIELD` in cli/orm_lens/parser.py.
+const NOT_A_FIELD = new Set(['Manager', 'QuerySet']);
+
 export function looksLikeModel(baseClasses: string[]): boolean {
   for (const b of baseClasses) {
     const tail = b.split('.').pop() ?? '';
@@ -365,6 +371,10 @@ export function collectDefs(filePath: string, content: string): ParsedModel[] {
         const fieldName = fieldMatch[1];
         const fieldType = fieldMatch[2];
         const { argsBlock, endIdx } = readBalancedArgs(lines, j);
+        if (NOT_A_FIELD.has(fieldType)) {
+          j = endIdx + 1;
+          continue;
+        }
         const relationKind =
           fieldType === 'TaggableManager'
             ? 'ManyToManyField'
diff --git a/test/taggable-manager.test.js b/test/taggable-manager.test.js
index 1ddaa05..126a117 100644
--- a/test/taggable-manager.test.js
+++ b/test/taggable-manager.test.js
@@ -39,3 +39,20 @@ class Post(models.Model):
   assert.equal(tags.relatedModel, 'taggit.Tag');
   assert.equal(tags.throughModel, 'CustomTaggedItem');
 });
+
+test('does not record an explicit default manager as a field', () => {
+  const [note] = parseModelsFile('/project/notes/models.py', `
+class Note(models.Model):
+    text = models.TextField()
+
+    objects = models.Manager()
+    all_objects = models.Manager(
+    )
+    tags = TaggableManager()
+`);
+
+  assert.deepEqual(
+    note.fields.map((field) => field.name),
+    ['text', 'tags'],
+  );
+});
`````

[Back to the shelf](README.md)
