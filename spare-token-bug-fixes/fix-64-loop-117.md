# Fix 64: loop: cleaning a session title removes the visible text between two terminal escape sequences

Status: UNSENT and UNTESTED. Free to take.

- Project: JimmyDi/loop
- Bug report title: bug(coding-agent): OSC stripping removes visible text between escape sequences
- Bug report: number 117 ([open the bug report](https://github.com/JimmyDi/loop/issues/117))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/64-loop-117.patch](fixes/64-loop-117.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/64-loop-117.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-64-loop-117.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-64-loop-117.html

## The bug

The session title cleaner strips terminal title sequences (OSC sequences). When two such sequences ended with the ESC-backslash terminator the pattern ran from the start of the first sequence to the end of the second one. The ordinary text between the two sequences was deleted.

## The fix

The first pattern in normalizeTitle in packages/coding-agent/src/core/titles/title-text.ts no longer lets the body of a sequence hold an ESC character. Each sequence now ends at its own terminator. The test file gains cases for repeated ESC-backslash terminators and for mixed terminators. CHANGELOG.md gains a line.

## Files changed

- CHANGELOG.md
- packages/coding-agent/src/core/titles/title-text.test.ts
- packages/coding-agent/src/core/titles/title-text.ts

## How to use the fix

1. Get a copy of the project JimmyDi/loop.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 64-loop-117.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 117.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot checked the new pattern with a scratch script against the new cases and the existing case. Nobody ran the project's tests. Fixes 62 and 64 change neighbouring lines of the same function and the same test file and fixes 62 and 63 and 64 each add a line at the same spot of CHANGELOG.md. Applying more than one needs a small manual merge.

## Search words

loop coding-agent normalizeTitle OSC escape sequence ESC backslash string terminator ST greedy visible text removed

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index b4bfee1..f052653 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -18,6 +18,8 @@ Notable changes across Agent, coding-agent, and Web UI are recorded here. Pendin
 
 - Website: eliminate the dark gap above the homepage background on mobile.
 
+- Coding-agent: keep the visible text between two terminal title (OSC) sequences when a session title is cleaned.
+
 ## [0.6.0] - 2026-11-06
 
 ### Added
diff --git a/packages/coding-agent/src/core/titles/title-text.test.ts b/packages/coding-agent/src/core/titles/title-text.test.ts
index bab7a25..ce91165 100644
--- a/packages/coding-agent/src/core/titles/title-text.test.ts
+++ b/packages/coding-agent/src/core/titles/title-text.test.ts
@@ -12,3 +12,16 @@ test("titles strip controls, collapse whitespace and preserve UTF-8 boundaries",
   expect(validTitle({ text: "Task", source: "model", messageIndices: [2, 0] })).toBe(false);
   expect(validTitle({ text: "Task", source: "user", messageIndices: [] })).toBe(true);
 });
+
+test("titles keep the visible text between two OSC sequences", () => {
+  const esc = String.fromCharCode(27);
+  const st = `${esc}\\`;
+  const bel = String.fromCharCode(7);
+  const osc = (terminator: string) => `${esc}]0;hidden${terminator}`;
+
+  expect(normalizeTitle(`${osc(st)}Keep me${osc(st)} visible`)).toBe("Keep me visible");
+  expect(normalizeTitle(`${osc(bel)}Keep me${osc(bel)} visible`)).toBe("Keep me visible");
+  expect(normalizeTitle(`${osc(bel)}Keep me${osc(st)} visible`)).toBe("Keep me visible");
+  expect(normalizeTitle(`${osc(st)}Keep me${osc(bel)} visible`)).toBe("Keep me visible");
+  expect(normalizeTitle(`${osc(st)}${esc}[31mRed${esc}[0m${osc(st)} text`)).toBe("Red text");
+});
diff --git a/packages/coding-agent/src/core/titles/title-text.ts b/packages/coding-agent/src/core/titles/title-text.ts
index a3ddc68..78168eb 100644
--- a/packages/coding-agent/src/core/titles/title-text.ts
+++ b/packages/coding-agent/src/core/titles/title-text.ts
@@ -4,7 +4,9 @@ import type { SessionTitle, TitleInput } from "./types";
 
 export function normalizeTitle(value: string, maxBytes = 120): string {
   const clean = value
-    .replace(/\u001b\][^\u0007]*(?:\u0007|\u001b\\)/g, "")
+    // An OSC sequence runs to its own terminator, BEL or ESC-backslash, and no further: the body
+    // may not hold an ESC, or one sequence would swallow the visible text up to a later terminator.
+    .replace(/\u001b\][^\u0007\u001b]*(?:\u0007|\u001b\\)/g, "")
     .replace(/\u001b\[[0-?]*[ -/]*[@-~]/g, "")
     .replace(
       /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]/g,
`````

[Back to the shelf](README.md)
