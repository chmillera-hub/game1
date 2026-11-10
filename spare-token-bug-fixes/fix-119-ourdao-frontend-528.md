# Fix 119: ourdao-frontend: the step that posts the preview link on a pull request would stop with an error

Status: UNSENT and UNTESTED. Free to take.

- Project: ourdao/ourdao-frontend
- Bug report title: The Deploy Preview comment step reads `steps.deployment` inside github-script, where `steps` is not defined, so it throws a ReferenceError
- Bug report: number 528 ([open the bug report](https://github.com/ourdao/ourdao-frontend/issues/528))
- Project license: MIT
- Language: YAML and TypeScript
- Test included: yes
- Patch file: [fixes/119-ourdao-frontend-528.patch](fixes/119-ourdao-frontend-528.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/119-ourdao-frontend-528.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-119-ourdao-frontend-528.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-119-ourdao-frontend-528.html

## The bug

The preview workflow has a step that posts a comment with the preview address. The script of that step read steps.deployment and the word steps does not exist inside that kind of script so the step would stop with a ReferenceError. The script also did not wait for the comment call so a refused comment would not fail the step.

## The fix

.github/workflows/preview.yml now passes the address to the script through an environment value named DEPLOYMENT_URL and the script reads that value and waits for the comment call. A new file test/preview-workflow.test.ts takes the script out of the workflow file and runs the script with stand-ins: one test checks the posted link and one test checks that a refused comment fails the step.

## Files changed

- .github/workflows/preview.yml
- test/preview-workflow.test.ts

## How to use the fix

1. Get a copy of the project ourdao/ourdao-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 119-ourdao-frontend-528.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 528.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The step has never run in the project's automated checks because an earlier step fails (the bug report says so). The chatbot ran a scratch copy of the test logic against the workflow before and after the change: before the change the script stopped with steps is not defined and after the change the script posted the link and passed a refusal on. That run executed the short script of this one step and no other project code. The search result cut off the last lines of the bug report text. Fixes 109 and 113 on this shelf are for the same project and all three patches apply together.

## Search words

ourdao-frontend preview.yml actions/github-script steps.deployment ReferenceError page_url env createComment await

## The full patch

`````diff
diff --git a/.github/workflows/preview.yml b/.github/workflows/preview.yml
index e0dbdfb..e724dbe 100644
--- a/.github/workflows/preview.yml
+++ b/.github/workflows/preview.yml
@@ -54,9 +54,13 @@ jobs:
       - name: Add preview comment
         if: github.event_name == 'pull_request'
         uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0
+        env:
+          # `steps` is a workflow context, not a variable inside github-script, so
+          # the URL is interpolated here and read from the environment below.
+          DEPLOYMENT_URL: ${{ steps.deployment.outputs.page_url }}
         with:
           script: |
-            const deploymentUrl = steps.deployment.outputs.page_url;
+            const deploymentUrl = process.env.DEPLOYMENT_URL;
             const body = `## 🔍 Preview Deployment
 
             A preview of this PR has been built with **testnet** configuration.
@@ -71,7 +75,7 @@ jobs:
 
             > **Note:** If this PR requires a wallet (Freighter), please test locally as preview deployments may not have full wallet integration.`;
 
-            github.rest.issues.createComment({
+            await github.rest.issues.createComment({
               issue_number: context.issue.number,
               owner: context.repo.owner,
               repo: context.repo.repo,
diff --git a/test/preview-workflow.test.ts b/test/preview-workflow.test.ts
new file mode 100644
index 0000000..91ae821
--- /dev/null
+++ b/test/preview-workflow.test.ts
@@ -0,0 +1,59 @@
+import { describe, expect, it, vi } from 'vitest'
+import fs from 'node:fs'
+import path from 'node:path'
+
+/**
+ * Issue #528: the "Add preview comment" step read `steps.deployment` inside
+ * actions/github-script, where `steps` is not a variable, and did not await
+ * `createComment`. These tests take the script body out of preview.yml and run
+ * it with stand-ins for `github`, `context` and `process`.
+ */
+const workflow = fs.readFileSync(path.resolve('.github/workflows/preview.yml'), 'utf8')
+
+function commentScript(): string {
+  const lines = workflow.split('\n')
+  const start = lines.findIndex((line) => /^\s+script: \|\s*$/.test(line))
+  expect(start, 'preview.yml has a github-script step').toBeGreaterThan(-1)
+  const indent = lines[start].indexOf('script') + 2
+  const body: string[] = []
+  for (const line of lines.slice(start + 1)) {
+    if (line.trim() !== '' && line.search(/\S/) < indent) break
+    body.push(line.slice(indent))
+  }
+  return body.join('\n')
+}
+
+type Comment = { issue_number: number; owner: string; repo: string; body: string }
+
+function run(createComment: (comment: Comment) => Promise<unknown>) {
+  const AsyncFunction = Object.getPrototypeOf(async () => {}).constructor as new (
+    ...args: string[]
+  ) => (...args: unknown[]) => Promise<unknown>
+  const script = new AsyncFunction('github', 'context', 'process', commentScript())
+  const github = { rest: { issues: { createComment } } }
+  const context = { issue: { number: 7 }, repo: { owner: 'ourdao', repo: 'ourdao-frontend' } }
+  const process = { env: { DEPLOYMENT_URL: 'https://preview.example/pr-7/' } }
+  return script(github, context, process)
+}
+
+describe('issue #528: preview comment step', () => {
+  it('passes the deployment URL through env, not the bare steps context', () => {
+    expect(workflow).toContain('DEPLOYMENT_URL: ${{ steps.deployment.outputs.page_url }}')
+    expect(commentScript()).not.toMatch(/\bsteps\./)
+  })
+
+  it('posts a comment that links the deployment URL', async () => {
+    const createComment = vi.fn((comment: Comment) => Promise.resolve(comment))
+    await run(createComment)
+
+    expect(createComment).toHaveBeenCalledTimes(1)
+    const comment = createComment.mock.calls[0][0]
+    expect(comment).toMatchObject({ issue_number: 7, owner: 'ourdao', repo: 'ourdao-frontend' })
+    expect(comment.body).toContain('[View Preview](https://preview.example/pr-7/)')
+  })
+
+  it('fails the step when the comment cannot be posted', async () => {
+    const refused = () => Promise.reject(new Error('403 Forbidden'))
+    await expect(run(refused)).rejects.toThrow('403 Forbidden')
+  })
+})
`````

[Back to the shelf](README.md)
