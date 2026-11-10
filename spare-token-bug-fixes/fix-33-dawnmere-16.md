# Fix 33: dawnmere: uninstall says 'add this by hand' for a config file with comments and does not say what to remove

Status: UNSENT and UNTESTED. Free to take.

- Project: Hadeva-Dev/dawnmere
- Bug report title: uninstall: for a config file with comments, say exactly what to remove
- Bug report: number 16 ([open the bug report](https://github.com/Hadeva-Dev/dawnmere/issues/16))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/33-dawnmere-16.patch](fixes/33-dawnmere-16.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/33-dawnmere-16.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-33-dawnmere-16.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-33-dawnmere-16.html

## The bug

dawnmere uninstall leaves a config file alone when the file has comments. The printed line reused the wording from setup (add this by hand) and did not name the entry to take out.

## The fix

unplan() in cli/src/lflabs_memory_cli/apps.py now turns the skip reason into uninstall wording that names what to remove: the lflabs-memory key under mcpServers for an MCP file and the mcp_servers.lflabs-memory table for the Codex file and the hooks whose command runs lflabs-memory for a hooks file. uninstall.py prints that text. Setup's wording is untouched. test_uninstall_leaves_jsonc_alone checks the new wording and a new test covers a hooks file.

## Files changed

- cli/src/lflabs_memory_cli/apps.py
- cli/src/lflabs_memory_cli/uninstall.py
- cli/tests/test_uninstall.py

## How to use the fix

1. Get a copy of the project Hadeva-Dev/dawnmere.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 33-dawnmere-16.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 16.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The printed line is: ~/.cursor/mcp.json is not plain JSON (comments?), so it was left alone: remove "lflabs-memory" from "mcpServers" by hand. The bug report gives its wording only as an example so the exact words are the chatbot's choice. The bug report says the tests need an engine project that is not public yet. Nobody ran the tests.

## Search words

dawnmere uninstall jsonc comments left alone add this by hand remove lflabs-memory mcpServers hooks.json Cursor Codex

## The full patch

`````diff
diff --git a/cli/src/lflabs_memory_cli/apps.py b/cli/src/lflabs_memory_cli/apps.py
index 1641d35..1029a3c 100644
--- a/cli/src/lflabs_memory_cli/apps.py
+++ b/cli/src/lflabs_memory_cli/apps.py
@@ -246,6 +246,23 @@ def _drop_toml(text, block):
     return out, removed
 
 
+def _by_hand(entry):
+    """What to take out of a file that could not be rewritten, named so the user can find it."""
+    kind = entry["kind"]
+    if kind == "codex-toml":
+        return f"remove the [mcp_servers.{SERVER}] table by hand"
+    if kind == "mcp-json":
+        return f'remove "{SERVER}" from "{entry.get("key", "mcpServers")}" by hand'
+    return f"remove the hooks whose command runs {ENGINE} by hand"
+
+
+def _left_alone(skip, entry):
+    """A Skip in uninstall's words. The reason is kept; setup's "add this by hand" ending is replaced by what to
+    remove."""
+    why = str(skip).split(": left alone")[0]
+    return f"{why}, so it was left alone: {_by_hand(entry)}"
+
+
 def unplan(entry, h=None):
     """The plan that takes our entry out of one file (entry: an install.json file record, or one found by discovery:
     {"path", "kind", "added", "created"})."""
@@ -282,7 +299,7 @@ def unplan(entry, h=None):
         return Plan(app, kind, path, "remove", f"remove {n} memory hook" + ("s" if n > 1 else ""),
                     new=edits.dump_json(new, old), old=old)
     except Skip as e:
-        return Plan(app, kind, path, "error", str(e))
+        return Plan(app, kind, path, "error", _left_alone(e, entry))
 
 
 def discover(h=None):
diff --git a/cli/src/lflabs_memory_cli/uninstall.py b/cli/src/lflabs_memory_cli/uninstall.py
index 01d9ef3..608712f 100644
--- a/cli/src/lflabs_memory_cli/uninstall.py
+++ b/cli/src/lflabs_memory_cli/uninstall.py
@@ -62,7 +62,7 @@ def _file(entry, rep):
     if p.state == "gone":
         return rep.row(label, "gone", f"{short(path)}: {p.note}")
     if p.state == "error":
-        return rep.row(label, "error", f"{short(path)}: {p.note}; remove the {SERVER} entries by hand")
+        return rep.row(label, "error", f"{short(path)} {p.note}")
     try:
         backup = edits.write(path, p.new, p.old)
     except edits.Skip as e:
diff --git a/cli/tests/test_uninstall.py b/cli/tests/test_uninstall.py
index dae98f9..0fcae5c 100644
--- a/cli/tests/test_uninstall.py
+++ b/cli/tests/test_uninstall.py
@@ -113,7 +113,27 @@ def test_uninstall_leaves_jsonc_alone(mac):
     out = []
     assert uninstall.main(out=out.append) == 1
     assert (home / ".cursor/mcp.json").read_text() == jsonc
-    assert "by hand" in "\n".join(out)
+    said = "\n".join(out)
+    assert ('.cursor/mcp.json is not plain JSON (comments?), so it was left alone: '
+            'remove "lflabs-memory" from "mcpServers" by hand') in said
+    assert "add this by hand" not in said, "that is setup's wording"
+
+
+def test_uninstall_names_the_hooks_to_remove_from_a_jsonc_hooks_file(mac):
+    home = mac.home
+    seed(home)
+    fake_setup(home)
+    layout.install_json().unlink()
+    jsonc = ('// mine\n{"version": 1, "hooks": {"sessionStart": '
+             '[{"command": "lflabs-memory hook-cursor-start", "timeout": 10}]}}\n')
+    (home / ".cursor/hooks.json").write_text(jsonc)
+    out = []
+    assert uninstall.main(out=out.append) == 1
+    assert (home / ".cursor/hooks.json").read_text() == jsonc
+    said = "\n".join(out)
+    assert ".cursor/hooks.json is not plain JSON (comments?), so it was left alone: " \
+           "remove the hooks whose command runs lflabs-memory by hand" in said
+    assert "add this by hand" not in said and "add the hook by hand" not in said
 
 
 def test_uninstall_asks_before_deleting_memory(mac, monkeypatch):
`````

[Back to the shelf](README.md)
