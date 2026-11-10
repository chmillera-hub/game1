# Fix 29: repo-roast-skill: facts.py says 'not a git repo' when pointed at a subfolder of a repository

Status: UNSENT and UNTESTED. Free to take.

- Project: vivekbhange-hub/repo-roast-skill
- Bug report title: facts.py reports 'not a git repo' when run from a subfolder
- Bug report: number 2 ([open the bug report](https://github.com/vivekbhange-hub/repo-roast-skill/issues/2))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/29-repo-roast-skill-2.patch](fixes/29-repo-roast-skill-2.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/29-repo-roast-skill-2.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-29-repo-roast-skill-2.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-29-repo-roast-skill-2.html

## The bug

facts.py looked for a .git entry in the scanned folder only. A subfolder of a repository (one package in a monorepo) has no .git entry. facts.py reported is_git_repo false and skipped every git statistic.

## The fix

skills/roast-repo/facts.py gains git_toplevel() which asks git rev-parse --show-toplevel. list_files() and git_facts() use git_toplevel() in place of the .git check. In a subfolder every git statistic is limited to that subfolder with a path filter and file paths are given relative to the scanned folder. The git block gains a scoped_to_subfolder key in that case. tests/test_facts.py gains a test that builds a temporary repository with three commits and scans a subfolder.

## Files changed

- skills/roast-repo/facts.py
- tests/test_facts.py

## How to use the fix

1. Get a copy of the project vivekbhange-hub/repo-roast-skill.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 29-repo-roast-skill-2.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 2.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A plain folder that sits anywhere inside another git repository now counts as part of that repository. The bug report asks for that behaviour. The key name scoped_to_subfolder is the chatbot's choice. For a subfolder the first_commit date comes from git log --reverse and not from the root commit. The chatbot tried each git command by hand in a scratch repository of the chatbot's own. The project's facts.py and tests were not run.

## Search words

repo-roast-skill facts.py is_git_repo false subfolder monorepo git rev-parse --show-toplevel git log -- path churn_hotspots

## The full patch

`````diff
diff --git a/skills/roast-repo/facts.py b/skills/roast-repo/facts.py
index fa526d2..edc23de 100644
--- a/skills/roast-repo/facts.py
+++ b/skills/roast-repo/facts.py
@@ -100,12 +100,24 @@ def run_git(repo: Path, *args: str) -> str | None:
     return proc.stdout
 
 
+def git_toplevel(repo: Path) -> Path | None:
+    """Top folder of the git repository that holds ``repo``, or None outside one.
+
+    ``repo`` may be a subfolder (one package in a monorepo), so asking git is
+    the only reliable test: only the top folder has a ``.git`` entry.
+    """
+    out = run_git(repo, "rev-parse", "--show-toplevel")
+    if out is None or not out.strip():
+        return None
+    return Path(out.strip())
+
+
 def list_files(repo: Path) -> tuple[list[str], int, bool]:
     """Return (relative posix paths, tracked dependency files skipped, is_git)."""
     out = run_git(repo, "ls-files", "-z")
     skipped_deps = 0
     files: list[str] = []
-    if out is not None and (repo / ".git").exists():
+    if out is not None and git_toplevel(repo) is not None:
         for rel in out.split("\0"):
             if not rel:
                 continue
@@ -246,27 +258,40 @@ def dependency_facts(repo: Path, files: list[str]) -> dict:
 
 
 def git_facts(repo: Path) -> dict | None:
-    if not (repo / ".git").exists():
+    top = git_toplevel(repo)
+    if top is None:
         return None
-    count = run_git(repo, "rev-list", "--count", "HEAD")
+    # In a subfolder of a repository every stat is limited to that subfolder.
+    subfolder = top.resolve() != repo.resolve()
+    scope = ("--", ".") if subfolder else ()
+    count = run_git(repo, "rev-list", "--count", "HEAD", *scope)
     if count is None:
         return {"commits": 0, "note": "repository has no commits yet"}
     facts: dict = {"commits": int(count.strip() or 0)}
-    shortlog = run_git(repo, "shortlog", "-sn", "HEAD") or ""
+    if subfolder:
+        facts["scoped_to_subfolder"] = repo.resolve().relative_to(top.resolve()).as_posix()
+    shortlog = run_git(repo, "shortlog", "-sn", "HEAD", *scope) or ""
     facts["contributors"] = len([ln for ln in shortlog.splitlines() if ln.strip()])
-    roots = (run_git(repo, "rev-list", "--max-parents=0", "HEAD") or "").split()
-    if roots:
-        facts["first_commit"] = (run_git(repo, "log", "-1", "--format=%cs", roots[-1]) or "").strip()
-    facts["last_commit"] = (run_git(repo, "log", "-1", "--format=%cs") or "").strip()
-    recent = run_git(repo, "rev-list", "--count", "--since=90.days", "HEAD")
+    if subfolder:
+        dates = (run_git(repo, "log", "--reverse", "--format=%cs", *scope) or "").split()
+        if dates:
+            facts["first_commit"] = dates[0]
+    else:
+        roots = (run_git(repo, "rev-list", "--max-parents=0", "HEAD") or "").split()
+        if roots:
+            facts["first_commit"] = (run_git(repo, "log", "-1", "--format=%cs", roots[-1]) or "").strip()
+    facts["last_commit"] = (run_git(repo, "log", "-1", "--format=%cs", *scope) or "").strip()
+    recent = run_git(repo, "rev-list", "--count", "--since=90.days", "HEAD", *scope)
     facts["commits_last_90_days"] = int((recent or "0").strip() or 0)
-    subjects = (run_git(repo, "log", "-n", "200", "--format=%s") or "").splitlines()
+    subjects = (run_git(repo, "log", "-n", "200", "--format=%s", *scope) or "").splitlines()
     lazy = [s for s in subjects if LAZY_MESSAGE.match(s.strip()) or len(s.strip()) < 4]
     facts["lazy_commit_messages"] = {"count": len(lazy), "of_last": len(subjects),
                                      "examples": sorted(set(lazy))[:5]}
-    churn = Counter(f for f in (run_git(repo, "log", "-n", "500", "--format=", "--name-only") or "").splitlines() if f)
+    # --relative gives paths from the scanned folder, the same form list_files uses.
+    names = run_git(repo, "log", "-n", "500", "--format=", "--name-only", "--relative", *scope) or ""
+    churn = Counter(f for f in names.splitlines() if f)
     facts["churn_hotspots"] = [{"path": p, "changes": n} for p, n in churn.most_common(10)]
-    status = run_git(repo, "status", "--porcelain") or ""
+    status = run_git(repo, "status", "--porcelain", *scope) or ""
     facts["uncommitted_changes"] = len([ln for ln in status.splitlines() if ln.strip()])
     return facts
 
diff --git a/tests/test_facts.py b/tests/test_facts.py
index 31f8f44..98e083e 100644
--- a/tests/test_facts.py
+++ b/tests/test_facts.py
@@ -188,6 +188,29 @@ class GitTests(FactsCase):
         # node_modules was committed; it is counted, not scanned
         self.assertGreaterEqual(f["files"]["tracked_dependency_files"], 1)
 
+    def test_subfolder_of_a_repo_is_still_a_git_repo(self):
+        self.git("init", "-q")
+        self.git("add", "-A")
+        self.git("commit", "-q", "-m", "wip")
+        self.write("README.md", "# Demo\n\nChanged outside the app folder.\n")
+        self.git("commit", "-q", "-am", "Touch only the README")
+        self.write("app/main.py", "changed\n")
+        self.git("commit", "-q", "-am", "Touch only the app folder")
+        f = facts.gather(self.repo / "app")
+        self.assertTrue(f["is_git_repo"])
+        g = f["git"]
+        # Three commits in the repository, two of them touch app/.
+        self.assertEqual(g["commits"], 2)
+        self.assertEqual(g["scoped_to_subfolder"], "app")
+        self.assertEqual(g["lazy_commit_messages"]["of_last"], 2)
+        # Paths are relative to the scanned folder, like the file list.
+        self.assertEqual(g["churn_hotspots"][0], {"path": "main.py", "changes": 2})
+        self.assertNotIn("README.md", [h["path"] for h in g["churn_hotspots"]])
+        self.assertIn("main.py", [x["path"] for x in f["largest_source_files"]])
+        whole = facts.gather(self.repo)["git"]
+        self.assertEqual(whole["commits"], 3)
+        self.assertNotIn("scoped_to_subfolder", whole)
+
 
 if __name__ == "__main__":
     unittest.main()
`````

[Back to the shelf](README.md)
