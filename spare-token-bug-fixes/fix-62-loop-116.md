# Fix 62: loop: session titles split a joined emoji by removing the zero width joiner

Status: UNSENT and UNTESTED. Free to take.

- Project: JimmyDi/loop
- Bug report title: bug(coding-agent): session titles split joined emoji by removing ZWJ
- Bug report: number 116 ([open the bug report](https://github.com/JimmyDi/loop/issues/116))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/62-loop-116.patch](fixes/62-loop-116.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/62-loop-116.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-62-loop-116.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-62-loop-116.html

## The bug

The session title cleaner removed every zero width joiner character. A joined emoji such as the woman technologist emoji is two emoji held together by that character. In a title the joined emoji fell apart into two separate symbols.

## The fix

normalizeTitle in packages/coding-agent/src/core/titles/title-text.ts keeps the joiner between two emoji (with an optional variation selector or skin tone before the joiner) and removes the joiner everywhere else. A joiner left at the end by the byte limit is removed. The test file gains cases for four joined emoji and for stray joiners and for the byte limit. The session titles doc and CHANGELOG.md each gain a sentence.

## Files changed

- CHANGELOG.md
- packages/coding-agent/src/core/titles/title-text.test.ts
- packages/coding-agent/src/core/titles/title-text.ts
- packages/coding-agent/src/docs/session-titles.md

## How to use the fix

1. Get a copy of the project JimmyDi/loop.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 62-loop-116.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 116.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a plain JavaScript copy of the changed function against the new cases and the three existing cases and all passed. Nobody ran the project's tests. The byte limit can still cut a joined emoji between its parts and the title then keeps the first part only. Fixes 62 and 63 each add a line at the same spot of CHANGELOG.md. Applying both needs a small manual merge of CHANGELOG.md.

## Search words

loop coding-agent session title normalizeTitle ZWJ U+200D zero width joiner joined emoji split woman technologist

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index b4bfee1..65600c6 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -18,6 +18,8 @@ Notable changes across Agent, coding-agent, and Web UI are recorded here. Pendin
 
 - Website: eliminate the dark gap above the homepage background on mobile.
 
+- Coding-agent: keep joined emoji intact in session titles; the zero width joiner is now removed only where it joins no emoji.
+
 ## [0.6.0] - 2026-11-06
 
 ### Added
diff --git a/packages/coding-agent/src/core/titles/title-text.test.ts b/packages/coding-agent/src/core/titles/title-text.test.ts
index bab7a25..d15474e 100644
--- a/packages/coding-agent/src/core/titles/title-text.test.ts
+++ b/packages/coding-agent/src/core/titles/title-text.test.ts
@@ -12,3 +12,32 @@ test("titles strip controls, collapse whitespace and preserve UTF-8 boundaries",
   expect(validTitle({ text: "Task", source: "model", messageIndices: [2, 0] })).toBe(false);
   expect(validTitle({ text: "Task", source: "user", messageIndices: [] })).toBe(true);
 });
+
+test("titles keep the joiner inside a joined emoji and drop it everywhere else", () => {
+  const technologist = String.fromCodePoint(0x1f469, 0x200d, 0x1f4bb);
+  const family = String.fromCodePoint(0x1f468, 0x200d, 0x1f469, 0x200d, 0x1f467);
+  const toned = String.fromCodePoint(0x1f469, 0x1f3fd, 0x200d, 0x1f4bb);
+  const flag = String.fromCodePoint(0x1f3f3, 0xfe0f, 0x200d, 0x1f308);
+
+  for (const emoji of [technologist, family, toned, flag]) {
+    expect(normalizeTitle(emoji)).toBe(emoji);
+    expect(normalizeTitle(`Fix login ${emoji} today`)).toBe(`Fix login ${emoji} today`);
+    expect(validTitle({ text: `Fix ${emoji}`, source: "user", messageIndices: [] })).toBe(true);
+  }
+
+  // A joiner that joins no emoji is still an invisible character and is removed.
+  expect(normalizeTitle("a\u200db")).toBe("ab");
+  expect(normalizeTitle("\u200dTask\u200d")).toBe("Task");
+  expect(normalizeTitle(`${String.fromCodePoint(0x1f469)}\u200dx`)).toBe(`${String.fromCodePoint(0x1f469)}x`);
+  expect(normalizeTitle("a\u200b\u200c\u200e\u200fb")).toBe("ab");
+});
+
+test("titles cut at the byte limit never end in a dangling joiner", () => {
+  const technologist = String.fromCodePoint(0x1f469, 0x200d, 0x1f4bb);
+  // 4 bytes for the first emoji, 3 for the joiner, 4 for the second: 11 in all.
+  expect(normalizeTitle(technologist, 11)).toBe(technologist);
+  expect(normalizeTitle(technologist, 10)).toBe(String.fromCodePoint(0x1f469));
+  expect(normalizeTitle(technologist, 7)).toBe(String.fromCodePoint(0x1f469));
+  const cut = normalizeTitle(technologist, 7);
+  expect(normalizeTitle(cut)).toBe(cut);
+});
diff --git a/packages/coding-agent/src/core/titles/title-text.ts b/packages/coding-agent/src/core/titles/title-text.ts
index a3ddc68..7ebb05e 100644
--- a/packages/coding-agent/src/core/titles/title-text.ts
+++ b/packages/coding-agent/src/core/titles/title-text.ts
@@ -7,7 +7,14 @@ export function normalizeTitle(value: string, maxBytes = 120): string {
     .replace(/\u001b\][^\u0007]*(?:\u0007|\u001b\\)/g, "")
     .replace(/\u001b\[[0-?]*[ -/]*[@-~]/g, "")
     .replace(
-      /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]/g,
+      /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u200b\u200c\u200e\u200f\u202a-\u202e\u2060-\u206f\ufeff]/g,
+      "",
+    )
+    // U+200D (zero width joiner) is what holds a joined emoji together, so it stays between
+    // two emoji (an optional variation selector or skin tone may sit before it) and goes
+    // everywhere else, where it is only an invisible character.
+    .replace(
+      /(?<!\p{Extended_Pictographic}[\ufe0f\u{1f3fb}-\u{1f3ff}]?)\u200d|\u200d(?!\p{Extended_Pictographic})/gu,
       "",
     )
     .replace(/\s+/g, " ")
@@ -19,7 +26,8 @@ export function normalizeTitle(value: string, maxBytes = 120): string {
     if (bytes > maxBytes) break;
     result += character;
   }
-  return result.trim();
+  // The byte limit can cut a joined emoji after its joiner; a joiner with nothing after it goes too.
+  return result.replace(/\u200d+$/, "").trim();
 }
 
 export function titleInputs(messages: readonly Message[]): TitleInput[] {
diff --git a/packages/coding-agent/src/docs/session-titles.md b/packages/coding-agent/src/docs/session-titles.md
index d2a8f93..1c034b3 100644
--- a/packages/coding-agent/src/docs/session-titles.md
+++ b/packages/coding-agent/src/docs/session-titles.md
@@ -55,7 +55,7 @@ The first eligible text produces a fallback immediately: up to eight whitespace-
 
 The background request uses an independent context, no tools, one model turn, and a short language-aware instruction. The model API is reached through the existing Agent loop and injected model runtime. No title request, response, tool result, or token usage is added to the main conversation; the auxiliary request has its own provider token cost.
 
-Accepted titles are normalized to one line, stripped of terminal/invisible controls, capped at 120 UTF-8 bytes without splitting code points, and saved in the existing JSONL header. Storage writes serialize with model changes and history commits, preserving both. Title-only changes do not alter activity timestamps. A fallback display event can precede its storage write; model/manual title events follow persistence.
+Accepted titles are normalized to one line, stripped of terminal/invisible controls, capped at 120 UTF-8 bytes without splitting code points, and saved in the existing JSONL header. A zero width joiner (U+200D) is kept only between two emoji, where it forms a joined emoji such as the woman-technologist emoji; anywhere else it is removed like the other invisible characters, and a joiner left at the end by the byte cap is removed too. Storage writes serialize with model changes and history commits, preserving both. Title-only changes do not alter activity timestamps. A fallback display event can precede its storage write; model/manual title events follow persistence.
 
 New text supersedes in-flight automatic work; all-prompts starts a new revision, while first-prompt does not automatically retry. Manual rename, explicit refresh, model switching, cancellation, runtime replacement, and disposal invalidate older work. Stale completions cannot become the accepted title. The Web backend also cancels and drains titles before provider reconfiguration or project disposal.
`````

[Back to the shelf](README.md)
