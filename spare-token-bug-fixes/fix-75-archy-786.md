# Fix 75: Archy: the help for archy conventions says the command always exits 0 but --emit-headers --check exits 1

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: docs(cli): `archy conventions --help` says it "always exits 0", but `--emit-headers --check` exits 1
- Bug report: number 786 ([open the bug report](https://github.com/hslee16/Archy/issues/786))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/75-archy-786.patch](fixes/75-archy-786.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/75-archy-786.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-75-archy-786.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-75-archy-786.html

## The bug

The help text of archy conventions said the command always exits 0 and listed only check and contracts and the --strict variants as build failures. The same help documents --emit-headers --check which exits 1 when a header is missing or stale. A person reading the help could treat the header check as non-blocking.

## The fix

The help text in src/archy/cli_conventions.py now says the report always exits 0 and names --emit-headers --check as the one exception that exits 1. A new file tests/test_conventions_help_exit_code.py reads the help output and checks for the new sentence.

## Files changed

- src/archy/cli_conventions.py
- tests/test_conventions_help_exit_code.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 75-archy-786.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 786.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report names src/archy/cli.py. The text had moved to src/archy/cli_conventions.py by 2026-11-10. The new wording follows the wording suggested in the bug report. The chatbot did not run the new test.

## Search words

archy conventions --help always exits 0 --emit-headers --check exit 1 docstring advisory gate

## The full patch

`````diff
diff --git a/src/archy/cli_conventions.py b/src/archy/cli_conventions.py
index ff50aba..bf6dd65 100644
--- a/src/archy/cli_conventions.py
+++ b/src/archy/cli_conventions.py
@@ -147,8 +147,9 @@ def conventions(
     as a vendored copy of a previous major version. The header says what
     was set aside and why. Pass `--include-tests` to census them too.
 
-    Advisory, never a gate: it reports and always exits 0. Only `check`,
-    `contracts` and the `--strict` variants fail a build.
+    Advisory: the report always exits 0. `--emit-headers --check` is the one
+    exception and exits 1 when a header is missing or stale. Otherwise only
+    `check`, `contracts` and the `--strict` variants fail a build.
     """
     _require(top_n >= 1, "top", ">= 1", top_n)
     _require(min_family >= 2, "min-family", ">= 2", min_family)
diff --git a/tests/test_conventions_help_exit_code.py b/tests/test_conventions_help_exit_code.py
new file mode 100644
index 0000000..eb798ad
--- /dev/null
+++ b/tests/test_conventions_help_exit_code.py
@@ -0,0 +1,23 @@
+"""`archy conventions --help` states the one exit-1 case of the command (#786)."""
+
+from __future__ import annotations
+
+from click.testing import CliRunner
+
+from archy.cli import main
+
+
+def test_conventions_help_names_the_emit_headers_check_exit_code():
+    """The help used to say the command "always exits 0" with no exception.
+
+    `--emit-headers --check` exits 1 on a missing or stale header, and archy's
+    own CI gates on it, so a reader of `--help` must see that exception beside
+    the exit-code claim.
+    """
+    r = CliRunner().invoke(main, ["conventions", "--help"])
+    assert r.exit_code == 0, r.output
+    # Click re-wraps the docstring and may break a line at a hyphen, so compare
+    # with every run of whitespace removed.
+    squeezed = "".join(r.output.split())
+    assert "alwaysexits0.Only" not in squeezed
+    assert "`--emit-headers--check`istheoneexceptionandexits1" in squeezed
`````

[Back to the shelf](README.md)
