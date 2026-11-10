# Fix 129: SMART admin console: the Events action View full payload only shows the summary

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: console: Events "View full payload" shows only the summary
- Bug report: number 87 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/87))
- Project license: Apache-2.0
- Language: TypeScript (React)
- Test included: no
- Patch file: [fixes/129-social-messaging-agent-runtime-toolkit-87.patch](fixes/129-social-messaging-agent-runtime-toolkit-87.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/129-social-messaging-agent-runtime-toolkit-87.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-129-social-messaging-agent-runtime-toolkit-87.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-129-social-messaging-agent-runtime-toolkit-87.html

## The bug

The row action View full payload on the Events page opened a dialog with the event type and the same one-line masked summary the table already shows. The console never has a full payload so the name promised data that does not exist.

## The fix

The action text in socialagent-admin-console/src/pages/events/index.tsx is now Details. CHANGELOG.md gains one line.

## Files changed

- CHANGELOG.md
- socialagent-admin-console/src/pages/events/index.tsx

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 129-social-messaging-agent-runtime-toolkit-87.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 87.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report offers two options (rename the action or drop the action). The patch renames because that is the smaller change. No test is included. Fixes 72 and 96 and 97 and 99 and 126 and 128 and 129 on this shelf each add text at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand.

## Search words

SMART admin console events page View full payload Details payloadSummary ButtonDropdown rename action

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..95383f9 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Admin console (beta)
+- The Events table's row action is named "Details", not "View full payload": the dialog shows the event type and the masked one-line summary, which is all the console has.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/socialagent-admin-console/src/pages/events/index.tsx b/socialagent-admin-console/src/pages/events/index.tsx
index c6c7a3f..eec9f52 100644
--- a/socialagent-admin-console/src/pages/events/index.tsx
+++ b/socialagent-admin-console/src/pages/events/index.tsx
@@ -172,7 +172,7 @@ export default function EventsPage({ navigate }: { navigate: (href: string) => v
             { id: "lambda", header: "Lambda invoked", minWidth: 140, cell: (e) => e.lambdaInvoked },
             { id: "payload", header: "Payload summary", minWidth: 200, cell: (e) => e.payloadSummary },
             { id: "status", header: "Status", minWidth: 120, cell: (e) => <StatusIndicator type={eventStatusType(e.status)}>{e.status}</StatusIndicator> },
-            { id: "actions", header: "Actions", minWidth: 80, cell: (e) => <ButtonDropdown variant="inline-icon" expandToViewport items={[{ id: "view-payload", text: "View full payload" }, { id: "go-to-stack", text: "Go to stack" }]} onItemClick={({ detail }) => { if (detail.id === "view-payload") setPayloadEvent(e); else navigate(`#/stacks/${e.stack}`); }} /> },
+            { id: "actions", header: "Actions", minWidth: 80, cell: (e) => <ButtonDropdown variant="inline-icon" expandToViewport items={[{ id: "view-payload", text: "Details" }, { id: "go-to-stack", text: "Go to stack" }]} onItemClick={({ detail }) => { if (detail.id === "view-payload") setPayloadEvent(e); else navigate(`#/stacks/${e.stack}`); }} /> },
           ]}
           header={
             <Header variant="awsui-h1-sticky" counter={`(${filtered.length})`} description="Events received via API Gateway and EventBridge across all stacks."
`````

[Back to the shelf](README.md)
