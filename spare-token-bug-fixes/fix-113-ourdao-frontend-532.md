# Fix 113: ourdao-frontend: the unused-package check reports a package that the formatter needs

Status: UNSENT and UNTESTED. Free to take.

- Project: ourdao/ourdao-frontend
- Bug report title: `npm run depcheck` flags `prettier-plugin-tailwindcss` as unused, but `.prettierrc` loads it
- Bug report: number 532 ([open the bug report](https://github.com/ourdao/ourdao-frontend/issues/532))
- Project license: MIT
- Language: JSON
- Test included: no
- Patch file: [fixes/113-ourdao-frontend-532.patch](fixes/113-ourdao-frontend-532.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/113-ourdao-frontend-532.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-113-ourdao-frontend-532.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-113-ourdao-frontend-532.html

## The bug

The Prettier settings load the plugin prettier-plugin-tailwindcss. The depcheck tool cannot see plugins named in Prettier settings so the tool reported the package as unused and the depcheck job of the automated checks failed for a package that is needed.

## The fix

.depcheckrc.json now lists prettier-plugin-tailwindcss among the ignored packages.

## Files changed

- .depcheckrc.json

## How to use the fix

1. Get a copy of the project ourdao/ourdao-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 113-ourdao-frontend-532.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 532.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- One line in a settings file. No test is included. The chatbot did not run depcheck. The search result cut off the last lines of the bug report text. Fix 109 on this shelf is for the same project and touches a different file.

## Search words

ourdao-frontend depcheck prettier-plugin-tailwindcss unused devDependency .depcheckrc.json ignores .prettierrc plugins

## The full patch

`````diff
diff --git a/.depcheckrc.json b/.depcheckrc.json
index 2002166..cf697a4 100644
--- a/.depcheckrc.json
+++ b/.depcheckrc.json
@@ -2,6 +2,7 @@
   "ignores": [
     "@tailwindcss/postcss",
     "tailwindcss",
+    "prettier-plugin-tailwindcss",
     "depcheck"
   ]
 }
`````

[Back to the shelf](README.md)
