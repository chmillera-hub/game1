# Fix 11: wheelgap: a private-index lockfile package with no file list is still looked up on PyPI

Status: UNSENT and UNTESTED. Free to take.

- Project: wheelgap/wheelgap
- Bug report title: Lockfiles: a private-index package with no file list is still looked up on PyPI
- Bug report: number 145 ([open the bug report](https://github.com/wheelgap/wheelgap/issues/145))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/11-wheelgap-145.patch](fixes/11-wheelgap-145.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/11-wheelgap-145.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-11-wheelgap-145.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-11-wheelgap-145.html

## The bug

An old-format poetry.lock records hashes under [metadata.hashes] and gives packages no file list. A package from a private index in such a lock file is looked up on pypi.org by name. The internal package name gets sent to a public server and a public package with the same name can be reported in place of the internal one.

## The fix

fill_all in src/wheelgap/pypi.py now marks a package with no files and a non-PyPI registry as skipped with the reason private index before any lookup. The --offline check in src/wheelgap/cli.py no longer counts such a package as needing the index. A PyPI package with no file list is still looked up. One existing test that asserted the old behaviour is replaced. New tests cover the function and the command line. A changelog line is included.

## Files changed

- CHANGELOG.md
- src/wheelgap/cli.py
- src/wheelgap/pypi.py
- tests/test_cli.py
- tests/test_pypi.py

## How to use the fix

1. Get a copy of the project wheelgap/wheelgap.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 11-wheelgap-145.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 145.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The --offline change goes one step beyond the bug report text. A maintainer may prefer to drop that one line.

## Search words

wheelgap poetry.lock metadata.hashes private index dependency confusion fill_all PyPI lookup skipped private index

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 48d48e4..98c4b96 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -2,6 +2,7 @@
 
 ## Unreleased
 
+- A lockfile package from a private index that has no file list (old-format `poetry.lock` files, which record hashes under `[metadata.hashes]`) is no longer looked up on pypi.org by name. It is listed as skipped with the reason `private index`, as in `Pipfile.lock`, so an internal package name stays off PyPI and a namesake's wheels are not reported. `--offline` no longer asks for the index on its behalf. A PyPI package with no file list is still looked up. (#145)
 - `--dockerfile` says when an official python image isn't published for the `--platform` asked for, instead of checking a target Docker can't pull: `FROM --platform=linux/riscv64 python:3.13-bookworm` is now an error (`... isn't published for linux/riscv64 (3.13-trixie is)`), as are s390x on current `bookworm` tags and ppc64le or s390x on current `bullseye` tags. Patch tags and the end-of-life tags that were still built for those arches are accepted. (#143, thanks [@sarankumar1325](https://github.com/sarankumar1325))
 - `--offline` never contacts an index, for CI and coding agents without network: an input that needs a lookup (a requirements file, `Pipfile.lock`, package names, lockfile entries with no file list) exits 2 with an error naming the packages (as does a `--pyodide-lock` URL), and the `requires-python` re-check is skipped with a note that those Pythons may show false gaps. It can't be combined with `--online`. (#140, thanks [@sarankumar1325](https://github.com/sarankumar1325))
 
diff --git a/src/wheelgap/cli.py b/src/wheelgap/cli.py
index 24f4b9b..a60d4ee 100644
--- a/src/wheelgap/cli.py
+++ b/src/wheelgap/cli.py
@@ -588,7 +588,8 @@ def require_offline(sources: list[Source]) -> None:
     """--offline: raise SourceError if an input has packages that can only be answered by looking them up."""
     problems = []
     for s in sources:
-        need = [p.name for p in s.packages if not p.skip and p.files is None]
+        # A private-index package with no files is skipped, not looked up (see fill_all), so it needs no index.
+        need = [p.name for p in s.packages if not p.skip and p.files is None and is_pypi(p.registry)]
         if need:
             names = ", ".join(need[:3]) + (", …" if len(need) > 3 else "")
             problems.append(
diff --git a/src/wheelgap/pypi.py b/src/wheelgap/pypi.py
index 15cca59..cb32916 100644
--- a/src/wheelgap/pypi.py
+++ b/src/wheelgap/pypi.py
@@ -213,9 +213,13 @@ def recheck_lock(packages: list[Package]) -> tuple[int, int]:
 
 
 def fill_all(packages: list[Package], refresh: bool = False, workers: int = 16) -> int:
-    """Look packages up on PyPI. With refresh (--online), a package the lock says came from another index keeps
-    its locked files instead: PyPI doesn't know it. A package with no files is still looked up, as before.
-    Returns how many kept their locked files for that reason."""
+    """Look packages up on PyPI. A package the lock says came from another index is never looked up there:
+    PyPI doesn't know it, and a namesake's wheels would be reported instead. With files in the lock it keeps
+    them, also with refresh (--online); with no files (old poetry.lock formats) it is skipped as "private index".
+    Returns how many kept their locked files under refresh for that reason."""
+    for p in packages:
+        if not p.skip and p.files is None and not is_pypi(p.registry):
+            p.skip = "private index"  # the same reason Pipfile.lock uses
     kept = {id(p) for p in packages if refresh and not p.skip and p.files is not None and not is_pypi(p.registry)}
     todo = [p for p in packages if not p.skip and id(p) not in kept and (refresh or p.files is None)]
     if todo:
diff --git a/tests/test_cli.py b/tests/test_cli.py
index 36a2287..13913f9 100644
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -1067,6 +1067,41 @@ def test_online_still_warns_about_private_packages_locked_for_other_pythons(caps
     assert fake_pypi == [] and "1 from other indexes may show false gaps" in err
 
 
+# #145: an old-format poetry.lock records hashes under [metadata.hashes], so its packages have no file list.
+LEGACY_POETRY_LOCK = (
+    '[[package]]\nname = "purewheel"\nversion = "3.1"\ndescription = ""\ncategory = "main"\noptional = false\n'
+    'python-versions = ">=3.9"\n\n'
+    "[package.source]\n"
+    'type = "legacy"\n'
+    'url = "https://pkgs.example.com/simple"\n'
+    'reference = "private"\n\n'
+    '[[package]]\nname = "fastlib"\nversion = "2.0.0"\ndescription = ""\ncategory = "main"\noptional = false\n'
+    'python-versions = ">=3.9"\n\n'
+    '[metadata]\npython-versions = ">=3.9"\ncontent-hash = "00"\n\n'
+    "[metadata.hashes]\n"
+    'purewheel = ["00"]\n'
+    'fastlib = ["00"]\n'
+)
+
+
+@pytest.mark.parametrize("flags", [[], ["--online"]])
+def test_private_index_package_with_no_file_list_is_not_looked_up(capsys, fake_pypi, tmp_path, flags):
+    (tmp_path / "poetry.lock").write_text(LEGACY_POETRY_LOCK, encoding="utf-8")
+    code, out, err = run(capsys, str(tmp_path), *flags, "-p", "3.13", "-t", "linux-x86_64", "--json")
+    assert code == 0, err
+    data = json.loads(out)
+    assert data["skipped"] == [{"name": "purewheel", "reason": "private index"}]
+    assert [p["name"] for p in data["packages"]] == ["fastlib"]  # from PyPI with no files: still looked up
+    assert fake_pypi and not [url for url in fake_pypi if "purewheel" in url], fake_pypi
+
+
+def test_offline_names_only_the_packages_that_need_pypi(capsys, fake_pypi, tmp_path):
+    (tmp_path / "poetry.lock").write_text(LEGACY_POETRY_LOCK, encoding="utf-8")
+    code, _, err = run(capsys, str(tmp_path), "--offline", "-p", "3.13", "-t", "linux-x86_64")
+    assert code == 2 and fake_pypi == []
+    assert "needs the index for 1 package (fastlib)" in err
+
+
 def test_offline_uses_the_lock_and_never_contacts_the_index(capsys, fixtures, fake_pypi):
     args = [str(fixtures / "uvproj"), "-p", "3.13", "-t", "linux-x86_64", "--json"]
     expected = run(capsys, *args)
diff --git a/tests/test_pypi.py b/tests/test_pypi.py
index 673a471..f129f04 100644
--- a/tests/test_pypi.py
+++ b/tests/test_pypi.py
@@ -170,10 +170,20 @@ def test_mirror_fallback_with_no_usable_files_is_unknown(monkeypatch):
     assert pkg.error == "unexpected response from the index" and pkg.files is None
 
 
-def test_fill_all_without_online_still_looks_up_a_private_package_with_no_files(fake_pypi):
+@pytest.mark.parametrize("refresh", [False, True])
+def test_fill_all_skips_a_private_package_with_no_files(fake_pypi, refresh):
     pkg = Package(name="purewheel", version="3.1", files=None, registry="https://pkgs.example.com/simple")
+    assert pypi.fill_all([pkg], refresh=refresh) == 0
+    assert fake_pypi == []
+    assert pkg.skip == "private index" and pkg.files is None
+
+
+@pytest.mark.parametrize("registry", [None, "https://pypi.org/simple"])
+def test_fill_all_still_looks_up_a_pypi_package_with_no_files(fake_pypi, registry):
+    pkg = Package(name="purewheel", version="3.1", files=None, registry=registry)
     assert pypi.fill_all([pkg]) == 0
     assert [url for url in fake_pypi if "purewheel" in url], fake_pypi
+    assert pkg.skip is None and pkg.files
 
 
 @pytest.mark.parametrize(
`````

[Back to the shelf](README.md)
