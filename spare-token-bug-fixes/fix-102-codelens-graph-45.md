# Fix 102: codelens-graph: the stats sidebar treats built-in names such as toString as commands

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Stats sidebar passes Object.prototype names to executeCommand
- Bug report: number 45 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/45))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/102-codelens-graph-45.patch](fixes/102-codelens-graph-45.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/102-codelens-graph-45.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-102-codelens-graph-45.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-102-codelens-graph-45.html

## The bug

The stats sidebar looked up incoming message names in a plain object. A message named toString or constructor found a built-in function of every object and that function was passed to VS Code as a command. The rule that unknown commands are ignored was broken.

## The fix

src/ui/statsView.ts now checks that the name is one of the listed commands (an own key of the map) before running a command. The existing test in test/ui/statsView.test.ts for this case loses its todo mark. changelog.md gains one line under Unreleased.

## Files changed

- changelog.md
- src/ui/statsView.ts
- test/ui/statsView.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 102-codelens-graph-45.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 45.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The patch uses Object.prototype.hasOwnProperty.call because the project compiles for ES2020 and Object.hasOwn needs ES2022. The chatbot checked the rule with a scratch script. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The test already existed in the project marked as todo and the patch removes the todo mark. The chatbot did not run the project's tests. Fixes 102 and 103 and 104 for this project apply one after another. Fixes 110 and 111 and 112 each add a changelog line next to one of those lines so each of them needs its changelog line added by hand when another codelens-graph fix from this shelf is already applied.

## Search words

codelens-graph statsView onDidReceiveMessage command map Object.prototype toString constructor executeCommand hasOwn

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..7575ae8 100644
--- a/changelog.md
+++ b/changelog.md
@@ -16,6 +16,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **Importing a folder now links to its index file** (`require('./lib')` → `lib/index.js`, Python packages → `__init__.py`). Previously no link was created.
 - **Calls through an aliased import keep their link** when the imported file is edited (`import { helper as h }`). Previously the link was lost until a full rebuild.
 - **CodeLens no longer damages your files when updating its section**: front matter in `CLAUDE.md` and similar files is kept, a leftover CodeLens marker no longer causes the text after it to be deleted, and removing the CodeLens block from `.gitignore` no longer merges the lines around it.
+- The stats sidebar ignores unknown messages whose name matches a built-in such as `toString` or `constructor`. Previously such a message reached VS Code as a command call that was then rejected.
 - `codelens_clear_config` no longer recreates `.codelens` and starts re-indexing right after clearing it.
 - **The graph panel no longer freezes VS Code on large repos.** It built its data with two queries per symbol and drew every symbol, which on a 100k-symbol monorepo blocked the extension host for minutes. It now loads in about a second, and above 1,000 symbols it shows the most connected ones with their neighbours. Search and the filter buttons still find any symbol in the index.
 
diff --git a/src/ui/statsView.ts b/src/ui/statsView.ts
index 14bf45e..610fbf5 100644
--- a/src/ui/statsView.ts
+++ b/src/ui/statsView.ts
@@ -46,7 +46,9 @@ export class StatsViewProvider implements vscode.WebviewViewProvider {
         enableWorkspace:  'codelens-graph.enableWorkspace',
         disableWorkspace: 'codelens-graph.disableWorkspace',
       };
-      if (map[cmd]) { vscode.commands.executeCommand(map[cmd]); }
+      // Own keys only: `map['toString']` or `map['constructor']` would find a built-in on
+      // Object.prototype and hand a function to executeCommand.
+      if (Object.prototype.hasOwnProperty.call(map, cmd)) { vscode.commands.executeCommand(map[cmd]); }
     });
 
     setTimeout(() => this.sendData(), 200);
diff --git a/test/ui/statsView.test.ts b/test/ui/statsView.test.ts
index b110708..91dd38e 100644
--- a/test/ui/statsView.test.ts
+++ b/test/ui/statsView.test.ts
@@ -157,15 +157,13 @@ describe('StatsViewProvider webview messages', () => {
     assert.deepEqual(commands.executed, []);
   });
 
-  it('ignores Object.prototype names as commands',
-    { todo: 'BUG #45: statsView.ts:37-49 looks commands up in a plain object, so toString/constructor/__proto__ call executeCommand with a function/object' },
-    (t) => {
-      const { view } = setup(t);
-      for (const command of ['toString', 'constructor', '__proto__', 'hasOwnProperty', 'valueOf']) {
-        view.webview.receive({ command });
-      }
-      assert.deepEqual(commands.executed, []);
-    });
+  it('ignores Object.prototype names as commands', (t) => {
+    const { view } = setup(t);
+    for (const command of ['toString', 'constructor', '__proto__', 'hasOwnProperty', 'valueOf']) {
+      view.webview.receive({ command });
+    }
+    assert.deepEqual(commands.executed, []);
+  });
 
   it("'ready' sends the current data and runs no command", async (t) => {
     const { view } = setup(t, { initialized: true, status: 'ready' });
`````

[Back to the shelf](README.md)
