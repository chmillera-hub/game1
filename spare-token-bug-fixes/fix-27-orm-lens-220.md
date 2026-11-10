# Fix 27: orm-lens: drift reports a moved model as unmigrated because operations inside SeparateDatabaseAndState are skipped

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report title: drift ignores operations inside SeparateDatabaseAndState, so moved models look unmigrated
- Bug report: number 220 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/220))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/27-orm-lens-220.patch](fixes/27-orm-lens-220.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/27-orm-lens-220.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-27-orm-lens-220.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-27-orm-lens-220.html

## The bug

The drift command replays each migration file and compares the result with models.py. The replay only read operations written directly in the operations list. An operation wrapped in SeparateDatabaseAndState(state_operations=[...]) was skipped. Django projects use that wrapper to move a model between apps. The command then printed blocking drift that does not exist and exited with code 1.

## The fix

cli/orm_lens/drift.py gains two small helpers. The helpers replace a SeparateDatabaseAndState call with the calls from its state_operations list. The keyword form and the positional form and nested wrappers are handled. database_operations are ignored as the bug report asks. cli/tests/test_drift.py gains three replay tests and one detect_drift test built from the example in the bug report. A changelog entry is included.

## Files changed

- CHANGELOG.md
- cli/orm_lens/drift.py
- cli/tests/test_drift.py

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 27-orm-lens-220.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 220.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fixes 27 and 28 both add an entry to CHANGELOG.md at different spots. The chatbot confirmed with git apply --check that fix 28 still applies after fix 27. The scratch check ran the two new helper functions together with the project's 8-line _op_name helper. No other project code was run.

## Search words

orm-lens drift SeparateDatabaseAndState state_operations database_operations moved model declared but never migrated replay_app Django migrations netbox

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index dccd535..30e1617 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -9,6 +9,14 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
 
 ### Fixed
 
+- **`orm-lens drift`: operations inside `SeparateDatabaseAndState` are
+  replayed** ([#220](https://github.com/FROWNINGdev/orm-lens/issues/220)).
+  The replay read only the calls that sit directly in `operations`, so a
+  model created or changed in `state_operations=[...]` (the standard way to
+  move a model between apps) was reported as "declared but never migrated"
+  and failed the build. The calls in `state_operations` now count, in the
+  keyword and the positional form and when nested. `database_operations`
+  are ignored: they change the table, not the state drift compares.
 - **`orm-lens er`: two models with the same class name stay two entities in
   Mermaid** ([#223](https://github.com/FROWNINGdev/orm-lens/issues/223)).
   Mermaid has one namespace for entity names, so `basket.Line` and
diff --git a/cli/orm_lens/drift.py b/cli/orm_lens/drift.py
index 2366098..331e7ee 100644
--- a/cli/orm_lens/drift.py
+++ b/cli/orm_lens/drift.py
@@ -163,8 +163,47 @@ def _create_model_fields(call: ast.Call) -> list[str]:
     return names
 
 
+def _state_operations(call: ast.Call) -> ast.expr | None:
+    """The ``state_operations`` value of a ``SeparateDatabaseAndState`` call.
+
+    The signature is ``(database_operations=None, state_operations=None)``,
+    so the positional form carries it as the second argument.
+    """
+    for kw in call.keywords:
+        if kw.arg == "state_operations":
+            return kw.value
+    if len(call.args) >= 2:
+        return call.args[1]
+    return None
+
+
+def _flatten_operations(elts: list[ast.expr]) -> list[ast.Call]:
+    """Calls from an operations list, with state wrappers opened up.
+
+    ``SeparateDatabaseAndState`` is replaced by the calls in its
+    ``state_operations``, recursively: that list is what Django builds its
+    model state from. ``database_operations`` change the table, not the
+    state that drift compares, so they are ignored.
+    """
+    out: list[ast.Call] = []
+    for e in elts:
+        if not isinstance(e, ast.Call):
+            continue
+        if _op_name(e) == "SeparateDatabaseAndState":
+            inner = _state_operations(e)
+            if isinstance(inner, (ast.List, ast.Tuple)):
+                out.extend(_flatten_operations(inner.elts))
+            continue
+        out.append(e)
+    return out
+
+
 def _operations(tree: ast.AST) -> list[ast.Call]:
-    """Every call inside a ``Migration.operations = [...]`` list."""
+    """Every call inside a ``Migration.operations = [...]`` list.
+
+    Calls wrapped in ``SeparateDatabaseAndState(state_operations=[...])``
+    are returned in place of the wrapper.
+    """
     out: list[ast.Call] = []
     for node in ast.walk(tree):
         if not isinstance(node, ast.Assign):
@@ -173,7 +212,7 @@ def _operations(tree: ast.AST) -> list[ast.Call]:
         if "operations" not in targets:
             continue
         if isinstance(node.value, (ast.List, ast.Tuple)):
-            out.extend(e for e in node.value.elts if isinstance(e, ast.Call))
+            out.extend(_flatten_operations(node.value.elts))
     return out
 
 
diff --git a/cli/tests/test_drift.py b/cli/tests/test_drift.py
index d345038..ac01395 100644
--- a/cli/tests/test_drift.py
+++ b/cli/tests/test_drift.py
@@ -137,6 +137,60 @@ class ReplayTest(unittest.TestCase):
         )
         self.assertEqual(replay_app(self.migrations)[0], {"post": {"title"}})
 
+    def test_state_operations_inside_separate_database_and_state_count(self) -> None:
+        # The standard way to move a model between apps: Django builds its
+        # state from state_operations, so the replay has to read them too.
+        self._write(
+            "0001_move_entry.py",
+            "        migrations.SeparateDatabaseAndState(\n"
+            "            state_operations=[\n"
+            '                migrations.CreateModel(name="Entry", fields=[\n'
+            '                    ("id", models.BigAutoField(primary_key=True)),\n'
+            '                    ("action", models.CharField(max_length=50)),\n'
+            "                ]),\n"
+            "            ],\n"
+            "            database_operations=[],\n"
+            "        ),\n",
+        )
+        self._write(
+            "0002_entry_message.py",
+            '        migrations.AddField(model_name="entry", name="message",\n'
+            "                            field=models.TextField(blank=True)),\n",
+        )
+        state, replayed = replay_app(self.migrations)
+        self.assertEqual(state, {"entry": {"action", "message"}})
+        self.assertEqual(replayed, 2)
+
+    def test_database_operations_do_not_change_the_state(self) -> None:
+        self._write(
+            "0001_initial.py",
+            '        migrations.CreateModel(name="Post", fields=[("title", None)]),\n',
+        )
+        self._write(
+            "0002_table_only.py",
+            "        migrations.SeparateDatabaseAndState(\n"
+            "            database_operations=[\n"
+            '                migrations.RemoveField(model_name="post", name="title"),\n'
+            "            ],\n"
+            "        ),\n",
+        )
+        self.assertEqual(replay_app(self.migrations)[0], {"post": {"title"}})
+
+    def test_positional_and_nested_state_operations(self) -> None:
+        self._write(
+            "0001_initial.py",
+            "        migrations.SeparateDatabaseAndState(\n"
+            "            [],\n"
+            "            [\n"
+            '                migrations.CreateModel(name="Post", fields=[("title", None)]),\n'
+            "                migrations.SeparateDatabaseAndState(state_operations=[\n"
+            '                    migrations.AddField(model_name="post", name="slug"),\n'
+            "                ]),\n"
+            "            ],\n"
+            "        ),\n",
+        )
+        self.assertEqual(replay_app(self.migrations)[0], {"post": {"title", "slug"}})
+
     def test_unparseable_migration_is_skipped_not_fatal(self) -> None:
         self._write(
             "0001_initial.py",
@@ -182,6 +236,37 @@ class DetectDriftTest(unittest.TestCase):
         self.assertTrue(d.is_blocking)
         self.assertIn("declared but never migrated", format_drift(report))
 
+    def test_model_created_in_state_operations_is_not_drift(self) -> None:
+        migrations = self.root / "audit" / "migrations"
+        migrations.mkdir(parents=True)
+        (migrations / "0001_move_entry.py").write_text(
+            _migration(
+                "        migrations.SeparateDatabaseAndState(\n"
+                "            state_operations=[\n"
+                '                migrations.CreateModel(name="Entry", fields=[\n'
+                '                    ("id", None), ("action", None),\n'
+                "                ]),\n"
+                "            ],\n"
+                "            database_operations=[],\n"
+                "        ),\n"
+            ),
+            encoding="utf-8",
+        )
+        (migrations / "0002_entry_message.py").write_text(
+            _migration(
+                '        migrations.AddField(model_name="entry", name="message"),\n'
+            ),
+            encoding="utf-8",
+        )
+        report = self._detect(
+            {
+                "blog": {"post": {"id", "title"}},
+                "audit": {"entry": {"id", "action", "message"}},
+            }
+        )
+        self.assertEqual(report.drifted, [])
+        self.assertEqual(report.blocking_count, 0)
+
     def test_migrated_but_undeclared_field_does_not_block(self) -> None:
         report = self._detect({"blog": {"post": set()}})
         d = report.drifted[0]
`````

[Back to the shelf](README.md)
