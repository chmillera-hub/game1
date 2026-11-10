# Fix 54: resume-agent-skills: Phase 4 says Section 17 framings but framings are Section 19

Status: UNSENT and UNTESTED. Free to take.

- Project: vignzpie/resume-agent-skills
- Bug report title: Phase 4 says 'Section 17 framings' but framings are Section 19
- Bug report: number 3 ([open the bug report](https://github.com/vignzpie/resume-agent-skills/issues/3))
- Project license: MIT
- Language: Markdown
- Test included: no
- Patch file: [fixes/54-resume-agent-skills-3.patch](fixes/54-resume-agent-skills-3.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/54-resume-agent-skills-3.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-54-resume-agent-skills-3.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-54-resume-agent-skills-3.html

## The bug

The Phase 4 draft template in resume-tailor/SKILL.md told the AI model to pull the headline from Section 17 framings. Section 17 is the achievements bank. The approved framings live in Section 19.

## The fix

One line in resume-tailor/SKILL.md now says Section 19 framings.

## Files changed

- resume-tailor/SKILL.md

## How to use the fix

1. Get a copy of the project vignzpie/resume-agent-skills.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 54-resume-agent-skills-3.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 3.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report offers two wordings and the fix takes the first one (Section 19). The project has no tests so no test is included.

## Search words

resume-agent-skills resume-tailor SKILL.md Phase 4 Section 17 framings Section 19 headline

## The full patch

`````diff
diff --git a/resume-tailor/SKILL.md b/resume-tailor/SKILL.md
index 8c59c0a..a969d57 100644
--- a/resume-tailor/SKILL.md
+++ b/resume-tailor/SKILL.md
@@ -94,7 +94,7 @@ Write `resume_<JD-ID>.md`. The structure is:
 
 ```
 # <Name>
-<Headline tailored to the JD's role title — pull from Section 17 framings if available>
+<Headline tailored to the JD's role title — pull from Section 19 framings if available>
 <Location · Email · Phone · LinkedIn · GitHub>
 
 ## Summary
`````

[Back to the shelf](README.md)
