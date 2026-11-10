# Fix 263: security-checker: public names in policy/ignore.py have no docstring (Annotation and IgnoreFile and RuleIgnore and __init__ and find and load_ignore_file and matches and parse_annotation and rule_matches)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(policy): ignore.py の公開クラス・メソッド 9 個に docstring が無い
- Bug report: number 407 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/407))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/263-security-checker-407.patch](fixes/263-security-checker-407.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/263-security-checker-407.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-263-security-checker-407.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-263-security-checker-407.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/policy/ignore.py: Annotation and IgnoreFile and RuleIgnore and __init__ and find and load_ignore_file and matches and parse_annotation and rule_matches. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/policy/ignore.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/policy/ignore.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 263-security-checker-407.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 407.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring ignore.py Annotation and IgnoreFile and RuleIgnore and __init__ and find and load_ignore_file and matches and parse_annotation and rule_matches

## The full patch

`````diff
diff --git a/src/security_checker/policy/ignore.py b/src/security_checker/policy/ignore.py
index 07632fb..8b1cfe1 100644
--- a/src/security_checker/policy/ignore.py
+++ b/src/security_checker/policy/ignore.py
@@ -43,10 +43,13 @@ _COMMENT_LEAD_RE = re.compile(r"[\s#/*<!\-;%{]*")
 
 @dataclass(frozen=True)
 class RuleIgnore:
+    """ignore ファイルの `rule:` 行 1 つ. ルール ID と、限定するパス (無ければ全体)."""
+
     rule: str
     paths: tuple[str, ...] = ()
 
     def matches(self, candidate: Candidate) -> bool:
+        """候補のルールがこの行のルールに合い、パスの限定があればそれにも合うか."""
         if not rule_matches(self.rule, candidate):
             return False
         if not self.paths:
@@ -57,6 +60,8 @@ class RuleIgnore:
 
 @dataclass
 class IgnoreFile:
+    """`.security-checker-ignore` の内容. パスのパターンと `rule:` 行."""
+
     path_patterns: list[str] = field(default_factory=list)
     rules: list[RuleIgnore] = field(default_factory=list)
 
@@ -81,6 +86,7 @@ def _candidate_path(candidate: Candidate) -> str | None:
 
 
 def rule_matches(rule: str, candidate: Candidate) -> bool:
+    """`rule` が `*`、ルール ID、または `スキャナ名/ルール ID` のどれかとして候補に合うか."""
     return rule in ("*", candidate.rule_id, f"{candidate.scanner}/{candidate.rule_id}")
 
 
@@ -108,6 +114,7 @@ def parse_ignore_file(text: str, source: str = IGNORE_FILENAME) -> tuple[IgnoreF
 
 
 def load_ignore_file(directory: Path) -> tuple[IgnoreFile | None, list[str]]:
+    """`directory` の ignore ファイルを読む. 無ければ (None, []) を返す."""
     path = directory / IGNORE_FILENAME
     if not path.is_file():
         return None, []
@@ -116,6 +123,8 @@ def load_ignore_file(directory: Path) -> tuple[IgnoreFile | None, list[str]]:
 
 @dataclass(frozen=True)
 class Annotation:
+    """コード内の ignore 注釈 1 つ. 抑制するルールと、書かれていれば理由."""
+
     rules: tuple[str, ...]
     reason: str | None
 
@@ -127,6 +136,7 @@ def is_annotation_only(line: str) -> bool:
 
 
 def parse_annotation(line: str) -> Annotation | None:
+    """行に ignore 注釈があれば解釈して返す. 無ければ None."""
     match = _ANNOTATION_RE.search(line)
     if match is None:
         return None
@@ -141,6 +151,7 @@ class AnnotationReader:
     """候補の行と、直前の注釈だけの行から注釈を探す. 同じファイルは一度だけ読む."""
 
     def __init__(self, root: Path) -> None:
+        """`root` は検査対象のルート. その外のファイルは読まない."""
         self._root = root.resolve()
         self._cache: dict[str, list[str] | None] = {}
 
@@ -160,6 +171,7 @@ class AnnotationReader:
         return self._cache[relative]
 
     def find(self, candidate: Candidate) -> Annotation | None:
+        """候補の行か、その直前の注釈だけの行にある注釈を返す. 位置の無い候補には None."""
         location = candidate.location
         if location is None or location.start_line < 1:
             return None
`````

[Back to the shelf](README.md)
