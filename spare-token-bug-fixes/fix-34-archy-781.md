# Fix 34: Archy: graph --format dot writes node names unescaped so a quote mark in a path gives invalid DOT

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(graph): `archy graph --format dot` writes node names unescaped, so a `"` in a path produces invalid DOT
- Bug report: number 781 ([open the bug report](https://github.com/hslee16/Archy/issues/781))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/34-archy-781.patch](fixes/34-archy-781.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/34-archy-781.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-34-archy-781.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-34-archy-781.html

## The bug

archy graph --format dot put node names straight between quote marks. A directory name that holds a quote mark or a backslash ended the DOT name early and Graphviz rejected the file.

## The fix

src/archy/cli_graph.py gains a _dot_id helper that escapes the backslash first and then the quote mark. Node lines and edge lines both use the helper. tests/test_cli_graph.py gains a test that builds a graph directly and checks the escaped output and reads the quoted strings back with a small tokenizer.

## Files changed

- src/archy/cli_graph.py
- tests/test_cli_graph.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 34-archy-781.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 781.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report names src/archy/cli.py as the file. The function had moved to src/archy/cli_graph.py by the day of writing and the fix is made there.

## Search words

Archy graph --format dot _graph_to_dot escape quote backslash invalid DOT id Graphviz _dot_id

## The full patch

`````diff
diff --git a/src/archy/cli_graph.py b/src/archy/cli_graph.py
index 5e25b90..44bb2f6 100644
--- a/src/archy/cli_graph.py
+++ b/src/archy/cli_graph.py
@@ -517,12 +517,18 @@ def _affected_test_paths(graph: nx.DiGraph, result: Affected) -> list[str]:
     return out
 
 
+def _dot_id(name: str) -> str:
+    """`name` as a quoted DOT id, with `\\` and then `"` escaped so the string stays one id."""
+    escaped = str(name).replace("\\", "\\\\").replace('"', '\\"')
+    return f'"{escaped}"'
+
+
 def _graph_to_dot(g: nx.DiGraph) -> str:
     lines = ["digraph imports {", '  rankdir="LR";']
     for n, d in sorted(g.nodes(data=True)):
         style = ' style="dashed" color="gray"' if d.get("external") else ""
-        lines.append(f'  "{n}"[{style.strip()}];')
+        lines.append(f"  {_dot_id(n)}[{style.strip()}];")
     for u, v in sorted(g.edges()):
-        lines.append(f'  "{u}" -> "{v}";')
+        lines.append(f"  {_dot_id(u)} -> {_dot_id(v)};")
     lines.append("}")
     return "\n".join(lines)
diff --git a/tests/test_cli_graph.py b/tests/test_cli_graph.py
index 8ba19c1..bcbc8e4 100644
--- a/tests/test_cli_graph.py
+++ b/tests/test_cli_graph.py
@@ -672,3 +672,52 @@ def test_impact_headline_is_unchanged_when_any_file_resolves(tmp_path: Path):
     result = CliRunner().invoke(main, args)
     assert result.output.startswith("# 1 module(s) depend on 1 changed module(s)")
     assert "(did you mean" in result.output
+
+
+def _dot_strings(text: str) -> list[str]:
+    """The quoted strings of a DOT file, unescaped; raises on a quote that never closes."""
+    out: list[str] = []
+    i = 0
+    while i < len(text):
+        if text[i] != '"':
+            i += 1
+            continue
+        i += 1
+        chars: list[str] = []
+        while text[i] != '"':
+            if text[i] == "\\":
+                i += 1
+            chars.append(text[i])
+            i += 1
+        out.append("".join(chars))
+        i += 1
+    return out
+
+
+def test_graph_to_dot_escapes_quotes_and_backslashes_in_node_names() -> None:
+    """A `"` or `\\` in a directory name must not end the DOT id early (#781)."""
+    import networkx as nx
+
+    from archy.cli_graph import _graph_to_dot
+
+    g = nx.DiGraph()
+    g.add_node('pkg.q"x.m', external=False)
+    g.add_node("pkg.back\\slash", external=False)
+    g.add_node("pkg.with space.m", external=False)
+    g.add_node("pkg.a", external=False)
+    g.add_edge('pkg.q"x.m', "pkg.a")
+    g.add_edge("pkg.back\\slash", "pkg.a")
+    g.add_edge("pkg.with space.m", "pkg.a")
+
+    dot = _graph_to_dot(g)
+
+    assert '  "pkg.q\\"x.m"[];' in dot
+    assert '  "pkg.q\\"x.m" -> "pkg.a";' in dot
+    assert '  "pkg.back\\\\slash" -> "pkg.a";' in dot
+    # Already valid DOT, and unchanged.
+    assert '  "pkg.with space.m" -> "pkg.a";' in dot
+    # Every quote closes, and the ids read back as the node names.
+    strings = _dot_strings(dot)
+    for name in g.nodes:
+        assert name in strings
+    assert dot.count('"pkg.q"x') == 0
`````

[Back to the shelf](README.md)
