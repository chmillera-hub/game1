# Fix 41: Archy: a module with a non-ASCII file name is dropped from churn and co-change

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(hotspots,coupling): every module with a non-ASCII filename is dropped from churn and co-change, because git's quoted paths never match a node
- Bug report: number 761 ([open the bug report](https://github.com/hslee16/Archy/issues/761))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/41-archy-761.patch](fixes/41-archy-761.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/41-archy-761.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-41-archy-761.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-41-archy-761.html

## The bug

By default git prints a non-ASCII path in quotes with octal escapes. Archy read that form from git log and the quoted name never matched a module. A module such as pkg.café got churn 0 and no co-change and could never be a hotspot.

## The fix

The git log calls in src/archy/hotspots.py and src/archy/coupling.py now pass -c core.quotePath=false so git prints each path as the path is on disk. The note in coupling.py that said such files may be undercounted is replaced. tests/test_hotspots.py and tests/test_coupling.py each gain a test with a real repository that holds café.py and forces git's default quoting.

## Files changed

- src/archy/coupling.py
- src/archy/hotspots.py
- tests/test_coupling.py
- tests/test_hotspots.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 41-archy-761.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 761.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- git still quotes a name that holds a quote mark or a backslash or a control character. Such names are still dropped. The chatbot tried the git option by hand in a scratch repository of the chatbot's own.

## Search words

Archy hotspots coupling churn co-change non-ASCII filename core.quotePath quoted octal escape café git log --name-status

## The full patch

`````diff
diff --git a/src/archy/coupling.py b/src/archy/coupling.py
index e7886f8..5d6a61c 100644
--- a/src/archy/coupling.py
+++ b/src/archy/coupling.py
@@ -37,9 +37,9 @@ numerator and the denominator; the displayed `support` (commit count) is the
 honest evidence base and `min_support` is the backstop. Merge-commit conflict
 resolutions are invisible under the default `git log` (which shows no diff for
 merges), so co-change that happens only in an evil merge is undercounted.
-Non-ASCII module filenames may be undercounted: git's default `core.quotePath`
-escapes them, and the git-vs-filesystem path encoding does not always join to a
-graph node - a pre-existing limitation shared with `hotspots.git_churn`.
+Non-ASCII module filenames are counted: the log is read with
+`core.quotePath=false`, so git prints them as they are on disk (as
+`hotspots.git_churn` does).
 
 archy:owns        CoChangeData, CoChangeHint, CouplingPair, co_changed_with,
                   compute_coupling, git_cochange, internal_module_paths
@@ -173,7 +173,19 @@ def git_cochange(
 
     # `-M` forces rename detection regardless of the user's `diff.renames` config
     # so the `R` lines the rename-folding relies on are always present.
-    cmd = ["git", "-C", str(repo_root), "log", "-M", "--name-status", "--format=%H"]
+    # `core.quotePath=false`: by default git prints a non-ASCII path quoted and
+    # octal-escaped (`"pkg/caf\303\251.py"`), which never joins to a graph node.
+    cmd = [
+        "git",
+        "-C",
+        str(repo_root),
+        "-c",
+        "core.quotePath=false",
+        "log",
+        "-M",
+        "--name-status",
+        "--format=%H",
+    ]
     if since:
         cmd.extend(resolve_since_log_args(repo_root, since))
     try:
diff --git a/src/archy/hotspots.py b/src/archy/hotspots.py
index 8e45c79..95311f5 100644
--- a/src/archy/hotspots.py
+++ b/src/archy/hotspots.py
@@ -103,7 +103,19 @@ def git_churn(root: Path, *, since: str | None = None) -> dict[str, int] | None:
 
     # `-M` forces rename detection regardless of the user's `diff.renames`
     # config so the `R` lines we rely on are always present.
-    cmd = ["git", "-C", str(repo_root), "log", "-M", "--name-status", "--format="]
+    # `core.quotePath=false`: by default git prints a non-ASCII path quoted and
+    # octal-escaped (`"pkg/caf\303\251.py"`), which never joins to a graph node.
+    cmd = [
+        "git",
+        "-C",
+        str(repo_root),
+        "-c",
+        "core.quotePath=false",
+        "log",
+        "-M",
+        "--name-status",
+        "--format=",
+    ]
     if since:
         cmd.extend(resolve_since_log_args(repo_root, since))
     try:
diff --git a/tests/test_coupling.py b/tests/test_coupling.py
index 5f0772c..571c77d 100644
--- a/tests/test_coupling.py
+++ b/tests/test_coupling.py
@@ -222,6 +222,24 @@ def test_git_cochange_counts_pair_support(tmp_path: Path):
     assert data.pair_support[_key(a, b)] == 3
 
 
+def test_git_cochange_pairs_a_non_ascii_filename(tmp_path: Path):
+    """A non-ASCII filename co-changes like any other, under git's default quoting (#761)."""
+    repo = tmp_path
+    _init_repo(repo)
+    _git(repo, "config", "core.quotePath", "true")
+    for i in range(4):
+        _write(repo, "café.py", f"x = {i}\n")
+        _write(repo, "plain.py", f"y = {i}\n")
+        _git(repo, "add", "-A")
+        _git(repo, "commit", "-q", "-m", f"both {i}")
+
+    data = git_cochange(repo)
+    assert data is not None
+    cafe, plain = _p(repo, "café.py"), _p(repo, "plain.py")
+    assert data.counts[cafe] == 4 and data.counts[plain] == 4
+    assert data.pair_support[_key(cafe, plain)] == 4
+
+
 def test_git_cochange_folds_rename_into_pair(tmp_path: Path):
     repo = tmp_path
     _init_repo(repo)
diff --git a/tests/test_hotspots.py b/tests/test_hotspots.py
index a5b55f8..643ce11 100644
--- a/tests/test_hotspots.py
+++ b/tests/test_hotspots.py
@@ -126,6 +126,32 @@ def test_git_churn_counts_commits_per_file(tmp_path: Path):
     assert churn[b_key] == 1
 
 
+def test_git_churn_counts_a_non_ascii_filename(tmp_path: Path):
+    """git quotes and octal-escapes a non-ASCII path by default; churn must still join (#761)."""
+    repo = tmp_path
+    _init_repo(repo)
+    # Force git's default, so the test reaches the bug on a machine whose
+    # global config already sets core.quotePath=false.
+    _git(repo, "config", "core.quotePath", "true")
+    for i in range(4):
+        (repo / "café.py").write_text(f"x = {i}\n")
+        (repo / "plain.py").write_text(f"y = {i}\n")
+        _git(repo, "add", "-A")
+        _git(repo, "commit", "-q", "-m", f"edit {i}")
+    raw = subprocess.run(
+        ["git", "-C", str(repo), "log", "--name-only", "--format="],
+        check=True,
+        capture_output=True,
+        text=True,
+    ).stdout
+    assert '"caf\\303\\251.py"' in raw, "the fixture must reach git's quoted form"
+
+    churn = git_churn(repo)
+    assert churn is not None
+    assert churn[str((repo / "café.py").resolve())] == 4
+    assert churn[str((repo / "plain.py").resolve())] == 4
+
+
 def test_git_churn_folds_renamed_file_history_onto_current_path(tmp_path: Path):
     """Regression for #166: a renamed file must keep its full churn on the
     current path. Without rename folding, `git log` splits the history across
`````

[Back to the shelf](README.md)
