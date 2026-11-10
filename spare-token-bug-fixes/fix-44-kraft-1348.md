# Fix 44: kraft: a changed file with a non-ASCII name shows no diff on the review page

Status: UNSENT and UNTESTED. Free to take.

- Project: itsOmidKarami/kraft
- Bug report title: A changed file with a non-ASCII name shows no diff on the review page
- Bug report: number 1348 ([open the bug report](https://github.com/itsOmidKarami/kraft/issues/1348))
- Project license: Apache-2.0
- Language: Python and TypeScript
- Test included: yes
- Patch file: [fixes/44-kraft-1348.patch](fixes/44-kraft-1348.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/44-kraft-1348.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-44-kraft-1348.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-44-kraft-1348.html

## The bug

By default git writes a non-ASCII path in quotes with octal escapes. Kraft's review reads kept that form. The review page listed café.txt under the escaped name and drew no diff for the file.

## The fix

src/kraft/review.py passes -c core.quotePath=false on the diff and numstat and status reads and on both name-only reads. unquote in frontend/src/ng/review/patch.ts now decodes C-style escapes and octal bytes as UTF-8 and the parser also reads a quoted diff --git header and quoted rename lines. tests/test_review.py gains a test with a real repository and frontend/src/ng/review/patch.test.ts gains a quoted header case and a table of unquote cases.

## Files changed

- frontend/src/ng/review/patch.test.ts
- frontend/src/ng/review/patch.ts
- src/kraft/review.py
- tests/test_review.py

## How to use the fix

1. Get a copy of the project itsOmidKarami/kraft.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 44-kraft-1348.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1348.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report sizes this work at half a day. Nobody ran the Python tests or the frontend tests. The chatbot ran a plain JavaScript copy of the new unquote logic against the same cases and tried the git option by hand in a scratch repository. unquote is now exported from patch.ts so the test can call the function. The bug report asks people to comment on the bug report before starting and the chatbot made no comment. Anyone who sends this fix should comment first.

## Search words

kraft review page non-ASCII file name core.quotePath quoted octal escapes café.txt read_change unquote patch.ts diff not drawn

## The full patch

`````diff
diff --git a/frontend/src/ng/review/patch.test.ts b/frontend/src/ng/review/patch.test.ts
index 300c911..01a3ce8 100644
--- a/frontend/src/ng/review/patch.test.ts
+++ b/frontend/src/ng/review/patch.test.ts
@@ -1,5 +1,5 @@
 import { describe, expect, it } from "vitest";
-import { parsePatch } from "./patch";
+import { parsePatch, unquote } from "./patch";
 
 const TWO = `diff --git a/search/embed.py b/search/embed.py
 index 1111111..2222222 100644
@@ -91,6 +91,33 @@ Binary files a/logo.png and b/logo.png differ
     expect(bin).toMatchObject({ path: "logo.png", binary: true, hunks: [] });
   });
 
+  it("reads a quoted, escaped header as the file's real name", () => {
+    const [cafe, odd] = parsePatch(String.raw`diff --git "a/caf\303\251.txt" "b/caf\303\251.txt"
+index 1..2 100644
+--- "a/caf\303\251.txt"
++++ "b/caf\303\251.txt"
+@@ -1 +1 @@
+-one
++two
+diff --git "a/say \"hi\".txt" "b/say \"hi\".txt"
+index 1..2 100755
+`);
+    expect(cafe).toMatchObject({ path: "café.txt", status: "modified" });
+    expect(cafe.hunks).toHaveLength(1);
+    expect(odd.path).toBe('say "hi".txt');
+  });
+
+  it.each([
+    ["plain.txt", "plain.txt"],
+    ['"with space.txt"', "with space.txt"],
+    [String.raw`"caf\303\251.txt"`, "café.txt"],
+    [String.raw`"a\tb\\c\"d\n"`, 'a\tb\\c"d\n'],
+    [String.raw`"\360\237\230\200.md"`, "😀.md"],
+    ['"é already plain.txt"', "é already plain.txt"],
+  ])("unquotes %s", (written, name) => {
+    expect(unquote(written)).toBe(name);
+  });
+
   it("is empty for an empty diff", () => {
     expect(parsePatch("")).toEqual([]);
   });
diff --git a/frontend/src/ng/review/patch.ts b/frontend/src/ng/review/patch.ts
index c9813d6..23e93c4 100644
--- a/frontend/src/ng/review/patch.ts
+++ b/frontend/src/ng/review/patch.ts
@@ -37,7 +37,37 @@ export interface PatchFile {
 const HUNK = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/;
 // `diff --git a/x b/x`: the b-side, for a file whose other headers say nothing (a mode change).
 const GIT = /^diff --git a\/(.*) b\/(.*)$/;
-const unquote = (p: string) => (p.startsWith('"') && p.endsWith('"') ? p.slice(1, -1) : p);
+// `diff --git "a/x" "b/x"`: git quotes a name holding `"`, `\`, a control character or (with core.quotePath on) a non-ASCII byte.
+const QUOTED_GIT = /^diff --git ("a\/(?:[^"\\]|\\.)*") ("b\/(?:[^"\\]|\\.)*")$/;
+const ESCAPES: Record<string, number> = { a: 7, b: 8, t: 9, n: 10, v: 11, f: 12, r: 13, '"': 34, "\\": 92 };
+/** A path as git wrote it. A quoted one has C-style escapes: `\"`, `\\`, `\t`, `\n`, and octal bytes that read as UTF-8 (`caf\303\251` is `café`). */
+export const unquote = (p: string) => {
+  if (p.length < 2 || !p.startsWith('"') || !p.endsWith('"')) return p;
+  const body = p.slice(1, -1);
+  if (!body.includes("\\")) return body;
+  const bytes: number[] = [];
+  const plain = new TextEncoder();
+  for (let i = 0; i < body.length; ) {
+    if (body[i] !== "\\") {
+      // A whole code point, so a character outside the BMP is not split.
+      const ch = String.fromCodePoint(body.codePointAt(i)!);
+      bytes.push(...plain.encode(ch));
+      i += ch.length;
+      continue;
+    }
+    const octal = /^[0-7]{1,3}/.exec(body.slice(i + 1));
+    if (octal) {
+      bytes.push(parseInt(octal[0], 8) & 0xff);
+      i += 1 + octal[0].length;
+      continue;
+    }
+    const next = body[i + 1];
+    if (next !== undefined && next in ESCAPES) bytes.push(ESCAPES[next]);
+    else bytes.push(92, ...plain.encode(next ?? ""));
+    i += 2;
+  }
+  return new TextDecoder().decode(new Uint8Array(bytes));
+};
 const side = (line: string, prefix: string) => {
   const p = unquote(line.slice(4).replace(/\t.*$/, ""));
   return p === "/dev/null" ? null : p.startsWith(prefix) ? p.slice(prefix.length) : p;
@@ -50,8 +80,9 @@ export function parsePatch(diff: string): PatchFile[] {
     const raw = chunk.endsWith("\n") ? chunk.slice(0, -1) : chunk;
     const rows = raw.split("\n");
     const git = GIT.exec(rows[0]);
-    let oldPath: string | null = git ? git[1] : null;
-    let newPath: string | null = git ? git[2] : null;
+    const quoted = git ? null : QUOTED_GIT.exec(rows[0]);
+    let oldPath: string | null = git ? git[1] : quoted ? unquote(quoted[1]).slice(2) : null;
+    let newPath: string | null = git ? git[2] : quoted ? unquote(quoted[2]).slice(2) : null;
     let status: PatchFile["status"] = "modified";
     let binary = false;
     let noNewline = false;
@@ -77,8 +108,8 @@ export function parsePatch(diff: string): PatchFile[] {
         hunks.push(hunk);
       } else if (row.startsWith("new file mode")) status = "added";
       else if (row.startsWith("deleted file mode")) status = "deleted";
-      else if (row.startsWith("rename from ")) { oldPath = row.slice(12); status = "renamed"; }
-      else if (row.startsWith("rename to ")) newPath = row.slice(10);
+      else if (row.startsWith("rename from ")) { oldPath = unquote(row.slice(12)); status = "renamed"; }
+      else if (row.startsWith("rename to ")) newPath = unquote(row.slice(10));
       else if (row.startsWith("Binary files ")) binary = true;
       else if (row.startsWith("--- ")) oldPath = side(row, "a/") ?? oldPath;
       else if (row.startsWith("+++ ")) newPath = side(row, "b/") ?? newPath;
diff --git a/src/kraft/review.py b/src/kraft/review.py
index 2fa11c3..0036ace 100644
--- a/src/kraft/review.py
+++ b/src/kraft/review.py
@@ -46,6 +46,13 @@ class Change(NamedTuple):
     untracked: list[str]
 
 
+#: git options that make every path in a read come out as itself. By default
+#: (`core.quotePath` on) git quotes a non-ASCII name and writes its bytes as
+#: octal escapes (`"caf\303\251.txt"`); the review page then listed the file
+#: under that name and drew no diff for it.
+_PLAIN_PATHS = ("-c", "core.quotePath=false")
+
+
 def read_change(
     worktree: Path,
     base: str,
@@ -78,7 +85,7 @@ def read_change(
     ws = ["-w"] if ignore_whitespace else []
     only = ["--", *paths] if paths else []
     # A path, not a pathspec: `*` must not keep whatever file it matches.
-    diff = (["--literal-pathspecs"] if paths else []) + ["diff", unentered, *ws]
+    diff = [*_PLAIN_PATHS, *(["--literal-pathspecs"] if paths else []), "diff", unentered, *ws]
     diff_args = diff + ([f"-U{context}"] if context is not None else []) + rev + only
     # strip=False: a diff whose last line is blank context is still that diff
     body = _config.git_read(worktree, *diff_args, strip=False)
@@ -93,7 +100,7 @@ def read_change(
         # (Kraft-tugdf.22). A tracked file under a root still shows, via `diff`.
         roots = [f":(exclude){r}" for r in _config.KRAFT_ROOTS]
         status = _config.git_read(
-            worktree, "status", unentered, "--porcelain", "-uall", "--", ".", *roots
+            worktree, *_PLAIN_PATHS, "status", unentered, "--porcelain", "-uall", "--", ".", *roots
         )
         if status is None:
             return None
@@ -199,7 +206,7 @@ def touched_by(worktree: Path, runs, from_sha: str, to_sha: str) -> dict[str, li
             continue
         if not _is_ancestor(worktree, end, to_sha) or _is_ancestor(worktree, end, from_sha):
             continue
-        names = _config.git_read(worktree, "diff", "--name-only", start, end) or ""
+        names = _config.git_read(worktree, *_PLAIN_PATHS, "diff", "--name-only", start, end) or ""
         for path in names.splitlines():
             if r["node_id"] not in out.setdefault(path, []):
                 out[path].append(r["node_id"])
@@ -225,7 +232,7 @@ def last_toucher(worktree: Path, runs, path: str) -> str | None:
         start, end = r["start_sha"], r["end_sha"]
         if not end or start == end:
             continue
-        names = _config.git_read(worktree, "diff", "--name-only", start, end) or ""
+        names = _config.git_read(worktree, *_PLAIN_PATHS, "diff", "--name-only", start, end) or ""
         if path in names.splitlines():
             return r["node_id"]
     return None
diff --git a/tests/test_review.py b/tests/test_review.py
index a8754fd..124046b 100644
--- a/tests/test_review.py
+++ b/tests/test_review.py
@@ -130,6 +130,26 @@ def test_a_renamed_file_survives_the_diff_filter(tmp_path):
     assert "moved.py" in kept and "other.py" not in kept
 
 
+def test_a_non_ascii_file_name_reaches_the_review_as_itself(tmp_path):
+    """git quotes `café.txt` as `"caf\\303\\251.txt"` unless core.quotePath is off."""
+    repo = make_repo(tmp_path)
+    git(repo, "config", "core.quotePath", "true")  # git's default, whatever this machine sets
+    write(repo, "café.txt", "one\n")
+    c1 = commit_all(repo)
+    assert '"caf\\303\\251.txt"' in git(repo, "show", "--name-only", "--format=", "HEAD")
+    write(repo, "café.txt", "two\n")
+    head = commit_all(repo, "edit")
+    write(repo, "naïve.txt", "new\n")
+
+    committed = review.read_change(repo, c1, head=head)
+    assert [f["path"] for f in committed.files] == ["café.txt"]
+    assert "diff --git a/café.txt b/café.txt" in committed.diff
+    assert "\\303" not in committed.diff
+
+    working = review.read_change(repo, c1)
+    assert working.untracked == ["naïve.txt"]
+
+
 def test_ignore_whitespace_drops_whitespace_only_files_from_patch_and_counts(tmp_path):
     repo = make_repo(tmp_path)
     write(repo, "ws.txt", "a\nb\n")
`````

[Back to the shelf](README.md)
