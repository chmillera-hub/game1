# Fix 68: OpenKeet: a newly added document is not ticked when building an interview pack

Status: UNSENT and UNTESTED. Free to take.

- Project: Jigsaw777/OpenKeet
- Bug report title: New documents aren't ticked when building an interview pack
- Bug report: number 15 ([open the bug report](https://github.com/Jigsaw777/OpenKeet/issues/15))
- Project license: MIT
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/68-openkeet-15.patch](fixes/68-openkeet-15.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/68-openkeet-15.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-68-openkeet-15.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-68-openkeet-15.html

## The bug

On the Prepare page a person adds a resume and then a job description. Only the resume was ticked under Use these documents. The job description was left out of the interview pack unless the person noticed and ticked the box.

## The fix

A new file apps/desktop/src/prep-sources.ts holds reconcileSources: a document seen for the first time is ticked and an unticked document stays unticked and a removed document leaves the selection. apps/desktop/src/prep.tsx remembers the document ids already handled and calls the helper whenever the list of documents changes. A new file apps/desktop/tests/prep-sources.test.ts covers the three cases from the bug report.

## Files changed

- apps/desktop/src/prep-sources.ts
- apps/desktop/src/prep.tsx
- apps/desktop/tests/prep-sources.test.ts

## How to use the fix

1. Get a copy of the project Jigsaw777/OpenKeet.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 68-openkeet-15.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 15.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The helper file and the test file are both written by the chatbot. The chatbot ran those two files in a scratch folder with the project's own test command line (node --experimental-strip-types --test) and all five tests passed. No other project code was run and the app itself was not started. The effect now reacts to the list of document ids and not only to the number of documents.

## Search words

OpenKeet Prepare page interview pack Use these documents new document not ticked sources selection prep.tsx useEffect

## The full patch

`````diff
diff --git a/apps/desktop/src/prep-sources.ts b/apps/desktop/src/prep-sources.ts
new file mode 100644
index 0000000..f64dbf9
--- /dev/null
+++ b/apps/desktop/src/prep-sources.ts
@@ -0,0 +1,14 @@
+/**
+ * Which documents are ticked for an interview pack after the document list changed.
+ *
+ * - A document seen for the first time is ticked.
+ * - A document that was unticked stays unticked when another one is added.
+ * - A document that is gone leaves the selection.
+ *
+ * `seen` holds the ids already handled by an earlier call; the caller adds `available` to it afterwards.
+ */
+export function reconcileSources(current: readonly string[], seen: ReadonlySet<string>, available: readonly string[]): string[] {
+  const kept = current.filter(id => available.includes(id));
+  const fresh = available.filter(id => !seen.has(id) && !kept.includes(id));
+  return [...kept, ...fresh];
+}
diff --git a/apps/desktop/src/prep.tsx b/apps/desktop/src/prep.tsx
index 5d5b266..b5263fa 100644
--- a/apps/desktop/src/prep.tsx
+++ b/apps/desktop/src/prep.tsx
@@ -2,6 +2,7 @@ import { useEffect, useRef, useState } from "react";
 import type { ChangeEvent, FormEvent, ReactNode } from "react";
 import { invoke } from "@tauri-apps/api/core";
 import { Empty, Icon } from "./components";
+import { reconcileSources } from "./prep-sources";
 
 // Mirrors copilot_core::prep (serde snake_case).
 export type DocKind = "resume" | "job_description" | "project_note" | "manual";
@@ -149,7 +150,16 @@ export function PreparePage({ prep, enabled, aiReady, review, startPractice, pre
   const [community, setCommunity] = useState<string[]>([]);
   const [selected, setSelected] = useState<string | null>(null);
   useEffect(() => { if (presetCommunity) setCommunity(current => current.includes(presetCommunity) ? current : [...current, presetCommunity]); }, [presetCommunity]);
-  useEffect(() => { if (data) setSources(current => current.length ? current.filter(id => data.sources.some(s => s.id === id)) : data.sources.map(s => s.id)); }, [data?.sources.length]);
+  // Document ids this effect has handled. A new document is ticked once; one the user unticked stays unticked.
+  const seenSources = useRef(new Set<string>());
+  const sourceIds = data?.sources.map(s => s.id).join("\n");
+  useEffect(() => {
+    if (!data) return;
+    const available = data.sources.map(s => s.id);
+    const seen = new Set(seenSources.current);
+    setSources(current => reconcileSources(current, seen, available));
+    for (const id of available) seenSources.current.add(id);
+  }, [sourceIds]);
   const pack = data?.packs.find(p => p.id === (selected ?? data?.packs[0]?.id)) ?? null;
   const unreviewed = data?.claims.filter(c => c.state === "extracted_unreviewed").length ?? 0;
 
diff --git a/apps/desktop/tests/prep-sources.test.ts b/apps/desktop/tests/prep-sources.test.ts
new file mode 100644
index 0000000..0bc00a9
--- /dev/null
+++ b/apps/desktop/tests/prep-sources.test.ts
@@ -0,0 +1,45 @@
+import { strict as assert } from "node:assert";
+import test from "node:test";
+import { reconcileSources } from "../src/prep-sources.ts";
+
+/** What the Prepare page does on each change of the document list. */
+function step(current: string[], seen: Set<string>, available: string[]): string[] {
+  const next = reconcileSources(current, new Set(seen), available);
+  for (const id of available) seen.add(id);
+  return next;
+}
+
+test("a newly added document is ticked by default", () => {
+  const seen = new Set<string>();
+  let ticked = step([], seen, ["resume"]);
+  assert.deepEqual(ticked, ["resume"]);
+  ticked = step(ticked, seen, ["resume", "job"]);
+  assert.deepEqual(ticked, ["resume", "job"]);
+});
+
+test("a document the user unticked stays unticked when another one is added", () => {
+  const seen = new Set<string>();
+  let ticked = step([], seen, ["resume", "job"]);
+  ticked = ticked.filter(id => id !== "job"); // the user unticks the job description
+  ticked = step(ticked, seen, ["resume", "job", "notes"]);
+  assert.deepEqual(ticked, ["resume", "notes"]);
+});
+
+test("everything unticked stays unticked: an empty selection is not a reason to tick all again", () => {
+  const seen = new Set<string>();
+  step([], seen, ["resume", "job"]);
+  assert.deepEqual(step([], seen, ["resume", "job", "notes"]), ["notes"]);
+});
+
+test("a removed document leaves the selection", () => {
+  const seen = new Set<string>();
+  const ticked = step([], seen, ["resume", "job"]);
+  assert.deepEqual(step(ticked, seen, ["job"]), ["job"]);
+});
+
+test("running the same change twice ticks nothing twice", () => {
+  const seen = new Set<string>();
+  const once = step([], seen, ["resume", "job"]);
+  assert.deepEqual(step(once, seen, ["resume", "job"]), ["resume", "job"]);
+  assert.deepEqual(reconcileSources(["resume"], new Set<string>(), ["resume", "job"]), ["resume", "job"]);
+});
`````

[Back to the shelf](README.md)
