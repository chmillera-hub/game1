# Fix 9: orm-lens: @receiver with a list or tuple of signals becomes one unknown custom edge

Status: UNSENT and UNTESTED. Free to take.

- Project: FROWNINGdev/orm-lens
- Bug report title: signals: @receiver([post_save, post_delete], ...) becomes one '&lt;unknown>' custom edge
- Bug report: number 221 ([open the bug report](https://github.com/FROWNINGdev/orm-lens/issues/221))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/9-orm-lens-221.patch](fixes/9-orm-lens-221.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/9-orm-lens-221.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-9-orm-lens-221.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-9-orm-lens-221.html

## The bug

Django's receiver() accepts one signal or a list or tuple of signals. For @receiver([post_save, post_delete], sender=Attachment) the signals command records a single edge with the signal name `<unknown>` and labels the edge custom. The cascade command then leaves list-form post_delete receivers out of its warning about receivers that will not run for DB_CASCADE rows.

## The fix

The fix replaces _signal_arg_name with _signal_arg_names in cli/orm_lens/signals_parser.py. The new helper returns one name per signal for a single signal or a list or a tuple. signal_graph adds one edge per name and keeps `<unknown>` only when nothing is readable. New tests cover the list form and the tuple form and the cascade warning. A changelog line is included. The chatbot checked the helper logic with a separate script on seven cases.

## Files changed

- CHANGELOG.md
- cli/orm_lens/signals_parser.py
- cli/tests/test_new_cli_commands.py
- cli/tests/test_signals_parser.py

## How to use the fix

1. Get a copy of the project FROWNINGdev/orm-lens.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 9-orm-lens-221.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 221.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 8 and fix 9 both add text at the same spot in CHANGELOG.md. Applying both needs a small manual merge of CHANGELOG.md.

## Search words

orm-lens signals @receiver([post_save, post_delete]) list tuple of signals `<unknown>` custom edge skipped_receivers DB_CASCADE signal_graph Django

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index a30b9be..905224a 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -7,6 +7,10 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
 
 ## [Unreleased]
 
+### Fixed
+
+- `signals` now reads `@receiver([post_save, post_delete], ...)` and the tuple form as one edge per signal instead of a single `<unknown>` custom edge. A list-form `post_delete` receiver is therefore listed in the `cascade` warning for `DB_CASCADE` rows. (#221)
+
 ## [py-1.17.1] - 2026-11-05
 
 > The orm-lens-* pre-commit hooks exist, and the old name says it is old.
diff --git a/cli/orm_lens/signals_parser.py b/cli/orm_lens/signals_parser.py
index 10b69a4..6415743 100644
--- a/cli/orm_lens/signals_parser.py
+++ b/cli/orm_lens/signals_parser.py
@@ -93,12 +93,25 @@ def _extract_receiver_call(dec: ast.AST) -> ast.Call | None:
     return dec
 
 
-def _signal_arg_name(call: ast.Call) -> str | None:
-    """First positional arg of ``receiver(signal, sender=..., ...)`` as a dotted
-    name (``post_save`` or ``orders.signals.order_shipped``)."""
+def _signal_arg_names(call: ast.Call) -> list[str]:
+    """Signals named by the first positional arg of ``receiver(signal, ...)``.
+
+    Django's ``receiver()`` takes one signal (``post_save`` or
+    ``orders.signals.order_shipped``) or a list / tuple of signals
+    (``[post_save, post_delete]``). Returns one dotted name per signal, in
+    source order. Elements that are not a plain dotted name are skipped, so an
+    empty list means nothing was readable.
+    """
     if not call.args:
-        return None
-    return _name_of(call.args[0])
+        return []
+    first = call.args[0]
+    nodes = first.elts if isinstance(first, (ast.List, ast.Tuple)) else [first]
+    names: list[str] = []
+    for node in nodes:
+        name = _name_of(node)
+        if name is not None:
+            names.append(name)
+    return names
 
 
 def _sender_kwarg(call: ast.Call) -> str | None:
@@ -305,13 +318,16 @@ def signal_graph(
                     handler_fqn = (
                         f"{module_path}.{node.name}" if module_path else node.name
                     )
-                    add_edge(
-                        _signal_arg_name(rcall) or "<unknown>",
-                        _sender_kwarg(rcall),
-                        handler_fqn,
-                        _rel(root_path, py, node.lineno),
-                        "@receiver",
-                    )
+                    # One edge per signal: receiver() accepts a list or
+                    # tuple of signals as well as a single one.
+                    for signal_name in _signal_arg_names(rcall) or ["<unknown>"]:
+                        add_edge(
+                            signal_name,
+                            _sender_kwarg(rcall),
+                            handler_fqn,
+                            _rel(root_path, py, node.lineno),
+                            "@receiver",
+                        )
 
             if isinstance(node, ast.Call):
                 # <signal>.connect(handler, sender=...) — the handler is
diff --git a/cli/tests/test_new_cli_commands.py b/cli/tests/test_new_cli_commands.py
index 50c7fea..d957da4 100644
--- a/cli/tests/test_new_cli_commands.py
+++ b/cli/tests/test_new_cli_commands.py
@@ -262,6 +262,43 @@ class CascadeCommandTest(unittest.TestCase):
             self.assertIn("! 3 delete receiver(s) will NOT run for (db) rows:", out)
             self.assertIn("post_delete shop.signals.audit_line  for shop.Line", out)
 
+    def test_db_cascade_lists_a_receiver_registered_with_a_list_of_signals(self) -> None:
+        """@receiver([post_save, post_delete], ...) is a delete receiver too."""
+        with TemporaryDirectory() as tmp:
+            _write(
+                Path(tmp) / "media" / "models.py",
+                "from django.db import models\n\n"
+                "class Album(models.Model):\n"
+                "    pass\n\n"
+                "class Attachment(models.Model):\n"
+                "    album = models.ForeignKey(Album, on_delete=models.DB_CASCADE)\n",
+            )
+            _write(
+                Path(tmp) / "media" / "signals.py",
+                "from django.db.models.signals import post_delete, post_save\n"
+                "from django.dispatch import receiver\n"
+                "from .models import Attachment\n\n"
+                "@receiver([post_save, post_delete], sender=Attachment)\n"
+                "def refresh_cache(sender, instance, **kw):\n"
+                "    pass\n\n"
+                "@receiver((post_delete,), sender=Attachment)\n"
+                "def remove_file(sender, instance, **kw):\n"
+                "    pass\n",
+            )
+            code, out, _err = _run(
+                ["cascade", "media.Album", "--path", tmp, "--format", "json"]
+            )
+            self.assertEqual(code, 0)
+            kills = {e["model"]: e for e in json.loads(out)["cascade_kills"]}
+            skipped = kills["media.Attachment"]["skipped_receivers"]
+            self.assertEqual(
+                sorted((r["handler"], r["signal"]) for r in skipped),
+                [
+                    ("media.signals.refresh_cache", "post_delete"),
+                    ("media.signals.remove_file", "post_delete"),
+                ],
+            )
+
     def test_orm_level_policies_print_no_db_footnote(self) -> None:
         code, out, _err = _run(["cascade", "orders.Order", "--path", str(MINIAPP)])
         self.assertEqual(code, 0)
diff --git a/cli/tests/test_signals_parser.py b/cli/tests/test_signals_parser.py
index b000ab0..1821340 100644
--- a/cli/tests/test_signals_parser.py
+++ b/cli/tests/test_signals_parser.py
@@ -54,6 +54,55 @@ class SignalGraphTest(unittest.TestCase):
             self.assertTrue(edge.get("builtin"))
             self.assertEqual(result["orphan_handlers"], [])
 
+    def test_receiver_with_a_list_or_tuple_of_signals_gets_one_edge_each(self) -> None:
+        """receiver() takes one signal or a list / tuple of signals."""
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            _copy_miniapp(root)
+            _write(
+                root / "notifications" / "signals.py",
+                "from django.db.models.signals import post_delete, post_save\n"
+                "from django.dispatch import receiver\n"
+                "from orders.models import Order\n\n"
+                "@receiver([post_save, post_delete], sender=Order)\n"
+                "def refresh_cache(sender, instance, **kwargs):\n"
+                "    pass\n\n"
+                "@receiver((post_delete,), sender=Order)\n"
+                "def remove_file(sender, instance, **kwargs):\n"
+                "    pass\n",
+            )
+
+            edges = signal_graph(str(root))["edges"]
+
+            self.assertEqual(
+                sorted((e["handler"].rsplit(".", 1)[-1], e["signal"]) for e in edges),
+                [
+                    ("refresh_cache", "post_delete"),
+                    ("refresh_cache", "post_save"),
+                    ("remove_file", "post_delete"),
+                ],
+            )
+            for edge in edges:
+                self.assertTrue(edge.get("builtin"), edge)
+                self.assertEqual(edge["sender"], "orders.Order")
+
+    def test_receiver_with_an_unreadable_signal_list_keeps_one_unknown_edge(self) -> None:
+        with TemporaryDirectory() as tmp:
+            root = Path(tmp)
+            _copy_miniapp(root)
+            _write(
+                root / "notifications" / "signals.py",
+                "from django.dispatch import receiver\n"
+                "from orders.models import Order\n\n"
+                "@receiver([pick_signal()], sender=Order)\n"
+                "def handler(sender, instance, **kwargs):\n"
+                "    pass\n",
+            )
+
+            edges = signal_graph(str(root))["edges"]
+
+            self.assertEqual([e["signal"] for e in edges], ["<unknown>"])
+
     def test_receiver_no_sender_gets_null_and_note(self) -> None:
         with TemporaryDirectory() as tmp:
             root = Path(tmp)
`````

[Back to the shelf](README.md)
