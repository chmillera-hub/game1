# Fix 92: Archy: the README never mentions the archy simulate command and describes archy duplicates incompletely

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: docs(readme): the `archy simulate` CLI is never mentioned, and `archy duplicates` is called "two-tier" without its `--near-miss` tier
- Bug report: number 788 ([open the bug report](https://github.com/hslee16/Archy/issues/788))
- Project license: MIT
- Language: Markdown
- Test included: no
- Patch file: [fixes/92-archy-788.patch](fixes/92-archy-788.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/92-archy-788.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-92-archy-788.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-92-archy-788.html

## The bug

archy simulate is a full command and the README only documented the matching MCP tool. A person looking in the README for a check before an edit did not find the command. The README also called archy duplicates two-tier while the command has a third optional tier behind --near-miss.

## The fix

The table of commands in README.md gains a row for archy simulate with the --add and --remove options and the duplicates row now mentions the optional --near-miss tier. Both wordings follow the bug report.

## Files changed

- README.md

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 92-archy-788.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 788.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Text only. The bug report says no test is needed. Fix 78 on this shelf changes another line of README.md and the two patches apply together.

## Search words

archy README archy simulate --add --remove pre-edit simulation duplicates two-tier --near-miss Type-3

## The full patch

`````diff
diff --git a/README.md b/README.md
index 10c212e..c6188ce 100644
--- a/README.md
+++ b/README.md
@@ -215,7 +215,8 @@ uvx archy check .        # layer rules from archy.yaml; exits 1 on violation
 | One-shot score | `archy score` |
 | Trended score | `archy score --record` + `archy trend` |
 | Refactor priority | `archy hotspots` (CC x git churn), `archy what-to-refactor-next` (fused hotspots + edit-risk) |
-| Duplicate detection | `archy duplicates` (two-tier: likely duplicates vs demoted variants - same-class/boilerplate/test/vendored; advisory, not a score axis) |
+| Duplicate detection | `archy duplicates` (two-tier: likely duplicates vs demoted variants - same-class/boilerplate/test/vendored, plus an opt-in `--near-miss` Type-3 tier; advisory, not a score axis) |
+| Pre-edit simulation | `archy simulate . --add a:b --remove c:d` (predicts the structural consequence of adding or removing an import edge before the edit; text and JSON) |
 | House style | `archy conventions` (naming families by home module, kind families by transitive base, `NAME = Ctor(...)` registries, mirrored surfaces, a gate inventory kept separate from user-error exits, model census, and the members a project's own `__all__` or docs leave out - derived from the source, so an agent stops guessing conventions; advisory, exits 0 on a successful report, and `--module NAME` switches to a complete, unranked lookup on one module - what it imports, what imports it, and whether it was set aside - which answers a negative the ranked report cannot; `--emit-headers` derives a per-module block (what it owns, what mirrors it, whether a finding here gates) from that same report and prints it, `--write` puts it in the module docstring, and `--check` exits 1 when one is stale) |
 | Change coupling | `archy coupling` (module pairs that co-change in git history but share no import/call edge - hidden dependencies; source-only, advisory) |
 | CI impact lookup | `archy affected` (`git diff` -> impacted modules + tests, depth-capped) |
`````

[Back to the shelf](README.md)
