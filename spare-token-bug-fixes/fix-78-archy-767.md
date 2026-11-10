# Fix 78: Archy: the README link to a real-world .importlinter example leads to a missing page

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: docs(readme): the "real-world example" link to `.importlinter` in this repo is a 404 since #691 deleted the file
- Bug report: number 767 ([open the bug report](https://github.com/hslee16/Archy/issues/767))
- Project license: MIT
- Language: Markdown and Python
- Test included: yes
- Patch file: [fixes/78-archy-767.patch](fixes/78-archy-767.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/78-archy-767.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-78-archy-767.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-78-archy-767.html

## The bug

README.md pointed readers to a file named .importlinter in the project as a real-world example. That file was deleted so the link led to a page-not-found error at the moment a reader follows the recommended path.

## The fix

The link in README.md now points to bench/fixtures/flask_realworld.importlinter which exists and is the replacement the bug report suggests. A new file tests/test_readme_relative_links.py fails when any relative link in README.md points at a path that does not exist.

## Files changed

- README.md
- tests/test_readme_relative_links.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 78-archy-767.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 767.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the link rule over README.md: 45 relative links and one dead link before the change and none after. The new test checks that a path exists on disk and does not check that git tracks the path. The bug report also mentions an optional wording change in the same paragraph as a choice for the maintainer and the patch leaves that wording alone. The chatbot did not run the project's tests.

## Search words

archy README .importlinter dead link 404 real-world example flask_realworld.importlinter relative link check

## The full patch

`````diff
diff --git a/README.md b/README.md
index 10c212e..d49e7b3 100644
--- a/README.md
+++ b/README.md
@@ -351,7 +351,7 @@ Two configs, one concern each:
 - **`archy.yaml`** owns layer definitions, direct-edge gating (`archy check`), required-reach rules (`required:`), `sdp:`, `exclude:`, and `roots:`.
 - **`.importlinter`** owns transitive contracts: all five contract types (Forbidden, Layers, Independence, Protected, AcyclicSiblings) and `ignore_imports` whitelists.
 
-Reach for `.importlinter` as soon as you need transitive enforcement at all; the archy.yaml fallback is a zero-config onramp, not a feature target. See [`.importlinter`](.importlinter) in this repo for a real-world example, and the [import-linter contract types reference](https://import-linter.readthedocs.io/en/stable/contract_types.html) for the full grammar.
+Reach for `.importlinter` as soon as you need transitive enforcement at all; the archy.yaml fallback is a zero-config onramp, not a feature target. See [`bench/fixtures/flask_realworld.importlinter`](bench/fixtures/flask_realworld.importlinter) in this repo for a real-world example, and the [import-linter contract types reference](https://import-linter.readthedocs.io/en/stable/contract_types.html) for the full grammar.
 
 Common case: forbid services from reaching `psycopg` but allow the sanctioned db library to do so:
 
diff --git a/tests/test_readme_relative_links.py b/tests/test_readme_relative_links.py
new file mode 100644
index 0000000..608c853
--- /dev/null
+++ b/tests/test_readme_relative_links.py
@@ -0,0 +1,32 @@
+"""Every relative link in README.md points at a file or directory in the repo (#767).
+
+The "real-world example" link to `.importlinter` 404ed after the file was
+deleted, at the point where a reader follows the recommended path.
+"""
+
+from __future__ import annotations
+
+import re
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+
+_LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")
+_HAS_SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:")
+
+
+def _relative_link_targets(markdown: str) -> list[str]:
+    targets = _LINK_TARGET.findall(markdown)
+    return [t for t in targets if not t.startswith("#") and not _HAS_SCHEME.match(t)]
+
+
+def test_readme_relative_links_resolve():
+    targets = _relative_link_targets((ROOT / "README.md").read_text())
+    assert targets, "README.md should contain relative links"
+    dead = [t for t in targets if not (ROOT / t.split("#", 1)[0]).exists()]
+    assert not dead, f"README.md links to paths that do not exist: {dead}"
+
+
+def test_the_link_extractor_skips_anchors_and_absolute_urls():
+    sample = "[a](docs/A.md) [b](#top) [c](https://example.com/x) [d](mailto:x@example.com)"
+    assert _relative_link_targets(sample) == ["docs/A.md"]
`````

[Back to the shelf](README.md)
