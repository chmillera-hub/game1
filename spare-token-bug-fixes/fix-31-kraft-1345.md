# Fix 31: kraft: the console command palette lists Textual's own Maximize and Screenshot commands

Status: UNSENT and UNTESTED. Free to take.

- Project: itsOmidKarami/kraft
- Bug report title: Console: Ctrl+P lists Textual's own Maximize and Screenshot commands
- Bug report: number 1345 ([open the bug report](https://github.com/itsOmidKarami/kraft/issues/1345))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/31-kraft-1345.patch](fixes/31-kraft-1345.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/31-kraft-1345.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-31-kraft-1345.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-31-kraft-1345.html

## The bug

Ctrl+P in the Kraft console showed two commands that come from the Textual framework and that Kraft does not use: Maximize and Screenshot. The bug report says the maintainer decided to hide both and keep Quit.

## The fix

get_system_commands in src/kraft/console/app.py now also drops the titles Maximize and Minimize and Screenshot. The comment above the filter is updated. tests/console/test_app.py gains a sibling test that checks the three titles are gone and that Quit and Keys and Dark and Light remain.

## Files changed

- src/kraft/console/app.py
- tests/console/test_app.py

## How to use the fix

1. Get a copy of the project itsOmidKarami/kraft.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 31-kraft-1345.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1345.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report asks people to comment on the bug report before starting. The chatbot posts nothing so no comment was made. Anyone who sends this fix should comment first. The bug report asks to confirm that the test fails before the change. Nobody ran the test. The chatbot read the source of Textual 8.2.8 and confirmed the three command titles and that Textual always offers Screenshot. The new test relies on that.

## Search words

kraft console command palette Ctrl+P Textual Maximize Minimize Screenshot get_system_commands SystemCommand

## The full patch

`````diff
diff --git a/src/kraft/console/app.py b/src/kraft/console/app.py
index 4082ec9..067ac5e 100644
--- a/src/kraft/console/app.py
+++ b/src/kraft/console/app.py
@@ -585,8 +585,10 @@ class KraftConsole(App):
     def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
         # Textual's theme picker lists its themes (Kraft has two), and its
         # "Keys" opens a panel of the framework's own bindings: `?` is Kraft's.
+        # "Maximize" (and the "Minimize" that undoes it) and "Screenshot" are
+        # the framework's own, which Kraft doesn't use. Quit stays.
         for command in super().get_system_commands(screen):
-            if command.title not in ("Theme", "Keys"):
+            if command.title not in ("Theme", "Keys", "Maximize", "Minimize", "Screenshot"):
                 yield command
         yield SystemCommand("Keys", "Kraft's keys for this screen", self.action_keys)
         yield SystemCommand("Dark", "Kraft's dark look", lambda: self._use("kraft-dark"))
diff --git a/tests/console/test_app.py b/tests/console/test_app.py
index a578961..661eec6 100644
--- a/tests/console/test_app.py
+++ b/tests/console/test_app.py
@@ -390,6 +390,23 @@ def test_the_palette_switches_kraft_looks_not_textuals(console):
     assert (theme, side) == ("kraft-light", console_app.theme.LIGHT["side"])
 
 
+def test_the_palette_lists_none_of_textuals_maximize_minimize_or_screenshot(console):
+    """Kraft uses none of the three; Quit and Kraft's own commands stay."""
+
+    async def scenario(app, pilot):
+        # Textual offers Maximize only while something focusable has focus.
+        app.screen.focus_next()
+        await pilot.pause()
+        textuals = {c.title for c in App.get_system_commands(app, app.screen)}
+        return textuals, {c.title for c in app.get_system_commands(app.screen)}
+
+    textuals, titles = console.run(scenario)
+    # Textual always offers Screenshot, so the filter is what keeps it out.
+    assert "Screenshot" in textuals
+    assert not titles & {"Maximize", "Minimize", "Screenshot"}
+    assert {"Quit", "Keys", "Dark", "Light"} <= titles
+
+
 def test_the_palettes_keys_command_opens_krafts_dialog_not_textuals_panel(console):
     async def scenario(app, pilot):
         commands = [c for c in app.get_system_commands(app.screen) if c.title == "Keys"]
`````

[Back to the shelf](README.md)
