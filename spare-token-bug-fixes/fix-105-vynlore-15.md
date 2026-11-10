# Fix 105: vynlore: on a first run no theme is highlighted in Settings

Status: UNSENT and UNTESTED. Free to take.

- Project: dhanushbs10/vynlore
- Bug report title: Default theme ID is missing the builtin: prefix
- Bug report: number 15 ([open the bug report](https://github.com/dhanushbs10/vynlore/issues/15))
- Project license: MIT
- Language: TypeScript (React)
- Test included: no
- Patch file: [fixes/105-vynlore-15.patch](fixes/105-vynlore-15.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/105-vynlore-15.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-105-vynlore-15.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-105-vynlore-15.html

## The bug

The default theme id was stored as onyx. The lookup of a theme only knows ids that start with builtin: or custom:. On a first run the default theme was never applied through the lookup and no built-in theme was highlighted in Settings until the person picked a theme.

## The fix

src/context/ThemeContext.tsx now builds the default id with builtinId so the default id is builtin:onyx. CHANGELOG.md gains one line under Unreleased.

## Files changed

- CHANGELOG.md
- src/context/ThemeContext.tsx

## How to use the fix

1. Get a copy of the project dhanushbs10/vynlore.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 105-vynlore-15.patch
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
- The bug report suggests the one-line change. The chatbot also moved the line below the definition of builtinId because the suggested line placed above that definition would fail when the app starts (the function would be used before it exists). A value of onyx saved by an earlier run is replaced by builtin:onyx on the next start by the existing code. The project has no test setup so the patch adds no test. The chatbot did not run the app. Fix 106 on this shelf adds a changelog line at the same spot so the two patches do not apply together: add the other changelog line by hand.

## Search words

vynlore ThemeContext DEFAULT_ID builtin: prefix onyx findSkin applyById first run theme not highlighted Settings

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 71dc17d..dcae775 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -2,6 +2,10 @@
 
 ## Unreleased
 
+### Bug fixes
+
+- On a first run the default theme is now stored and applied as `builtin:onyx`, so Settings highlights the active built-in theme before the user picks one.
+
 ### Documentation and contributor infrastructure
 
 - Rewrote the README with accurate UI limits, project status, supported formats and contributor links.
diff --git a/src/context/ThemeContext.tsx b/src/context/ThemeContext.tsx
index 9ac61bf..ea1a4c7 100644
--- a/src/context/ThemeContext.tsx
+++ b/src/context/ThemeContext.tsx
@@ -10,10 +10,10 @@ import {
 } from "../themes";
 
 const STORAGE_KEY = "vynlore.theme";
-const DEFAULT_ID = BUILTIN_THEMES[0].id;
-
 export const builtinId = (id: string) => `builtin:${id}`;
 export const customId = (fileName: string) => `custom:${fileName}`;
+// Prefixed like every stored theme id: findSkin only knows `builtin:` and `custom:` ids.
+const DEFAULT_ID = builtinId(BUILTIN_THEMES[0].id);
 
 interface ThemeContextValue {
   currentId: string;
`````

[Back to the shelf](README.md)
