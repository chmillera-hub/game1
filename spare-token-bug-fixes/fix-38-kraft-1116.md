# Fix 38: kraft: the document viewer adds a second banner landmark

Status: UNSENT and UNTESTED. Free to take.

- Project: itsOmidKarami/kraft
- Bug report title: The document viewer adds a second banner landmark
- Bug report: number 1116 ([open the bug report](https://github.com/itsOmidKarami/kraft/issues/1116))
- Project license: Apache-2.0
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/38-kraft-1116.patch](fixes/38-kraft-1116.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/38-kraft-1116.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-38-kraft-1116.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-38-kraft-1116.html

## The bug

The document viewer drawer had a header element at its top. A header element outside main and sectioning elements counts as a banner landmark. A person using a screen reader met a second page banner inside a dialog.

## The fix

frontend/src/ng/item/DocViewer.tsx uses a div with the same class name in place of the header element. The styles select by class so the look stays the same. frontend/src/ng/item/DocViewer.test.tsx gains the test the bug report asks for: no banner role inside the dialog.

## Files changed

- frontend/src/ng/item/DocViewer.test.tsx
- frontend/src/ng/item/DocViewer.tsx

## How to use the fix

1. Get a copy of the project itsOmidKarami/kraft.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 38-kraft-1116.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1116.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Nobody ran the frontend tests (just test-ui). The bug report asks people to comment on the bug report before starting. The chatbot posts nothing so no comment was made. Anyone who sends this fix should comment first.

## Search words

kraft DocViewer header dv-head banner landmark accessibility screen reader dialog queryByRole banner

## The full patch

`````diff
diff --git a/frontend/src/ng/item/DocViewer.test.tsx b/frontend/src/ng/item/DocViewer.test.tsx
index 28e618b..358d472 100644
--- a/frontend/src/ng/item/DocViewer.test.tsx
+++ b/frontend/src/ng/item/DocViewer.test.tsx
@@ -1,4 +1,4 @@
-import { render, screen, waitFor } from "@testing-library/react";
+import { render, screen, waitFor, within } from "@testing-library/react";
 import userEvent from "@testing-library/user-event";
 import { useState } from "react";
 import { afterEach, describe, expect, it, vi } from "vitest";
@@ -129,6 +129,14 @@ describe("DocViewer", () => {
     expect([...drawer.querySelectorAll(".dv-title, .dv-path, .dv-by")].map((c) => c.textContent)).toEqual(["Review notes", doc.path, "written by review › code_review › attempt 2"]);
   });
 
+  it("adds no banner landmark: the app's own header is the only one", async () => {
+    stubFetch({ "GET /documents/d1": [200, doc] });
+    render(<DocViewer source={{ kind: "document", id: "d1" }} onClose={() => {}} />);
+    const drawer = await screen.findByRole("dialog", { name: "Review notes" });
+    expect(within(drawer).queryByRole("banner")).toBeNull();
+    expect(drawer.querySelector(".dv-head")).not.toBeNull();
+  });
+
   describe("opened from search", () => {
     const bar = () => screen.getByRole("group", { name: "Search matches" });
 
diff --git a/frontend/src/ng/item/DocViewer.tsx b/frontend/src/ng/item/DocViewer.tsx
index 5afedb0..8f8f0d9 100644
--- a/frontend/src/ng/item/DocViewer.tsx
+++ b/frontend/src/ng/item/DocViewer.tsx
@@ -110,7 +110,8 @@ export function DocViewer({ source, query, onClose, returnTo }: { source: DocSou
   return createPortal(
     <div className="dv-scrim" {...backdropProps(onClose)}>
       <div ref={ref} role="dialog" aria-modal="true" aria-labelledby={titleId} tabIndex={-1} className={`dv-drawer${full ? " is-full" : ""}`}>
-        <header className="dv-head">
+        {/* A div, not a <header>: outside <main> and sectioning elements a <header> is a second banner landmark. */}
+        <div className="dv-head">
           <div className="dv-head-top">
             <h2 id={titleId} className="dv-title">{doc?.title ?? "Document"}</h2>
             <button type="button" className="dv-full" onClick={() => setFull(!full)}>{full ? "⤡ exit full screen" : "⤢ full screen"}</button>
@@ -124,7 +125,7 @@ export function DocViewer({ source, query, onClose, returnTo }: { source: DocSou
               <Button onClick={() => copyPath(doc.absolute_path ?? copyablePath(doc))}>Copy path</Button>
             </div>
           )}
-        </header>
+        </div>
         {query && doc && (
           <div className="dv-find" role="group" aria-label="Search matches">
             <Search size={14} aria-hidden />
`````

[Back to the shelf](README.md)
