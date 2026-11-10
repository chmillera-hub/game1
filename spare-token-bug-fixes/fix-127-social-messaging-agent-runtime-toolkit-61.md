# Fix 127: SMART toolkit docs: the scheduling page says one-shot schedules fire once without the conditions

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: docs: events-scheduling.md states one-shot schedules fire once without the conditions
- Bug report: number 61 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/61))
- Project license: Apache-2.0
- Language: Markdown
- Test included: no
- Patch file: [fixes/127-social-messaging-agent-runtime-toolkit-61.patch](fixes/127-social-messaging-agent-runtime-toolkit-61.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/127-social-messaging-agent-runtime-toolkit-61.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-127-social-messaging-agent-runtime-toolkit-61.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-127-social-messaging-agent-runtime-toolkit-61.html

## The bug

docs/events-scheduling.md said one-shot schedules fire once and auto-delete. That sentence reads as a delivery promise. EventBridge Scheduler delivers at least once and a firing runs at most once only with the state table on and a scheduled_time in the schedule's Input.

## The fix

One sentence in the Scheduling section of docs/events-scheduling.md now states both conditions and links to the Handling Scheduled Events section that explains them.

## Files changed

- docs/events-scheduling.md

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 127-social-messaging-agent-runtime-toolkit-61.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 61.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docs only. Fix 130 on this shelf adds a test that fails until this wording change is applied. Both patches apply together.

## Search words

SMART docs events-scheduling one-shot schedules fire once at most once state table scheduled_time EventBridge Scheduler at least once

## The full patch

`````diff
diff --git a/docs/events-scheduling.md b/docs/events-scheduling.md
index fb64bd5..79512f1 100644
--- a/docs/events-scheduling.md
+++ b/docs/events-scheduling.md
@@ -99,7 +99,7 @@ left = seconds_left(ctx.lambda_context)
 
 ## Scheduling
 
-Schedule future messages using EventBridge Scheduler. One-shot schedules fire once and auto-delete; recurring ones persist until cancelled (see [Recurring Schedules](#recurring-schedules-cron)).
+Schedule future messages using EventBridge Scheduler. One-shot schedules auto-delete after they fire. EventBridge Scheduler delivers at least once, so a firing runs at most once only while the state table is on (`features.state_table: true`) and the schedule's Input carries `scheduled_time` (see [Handling Scheduled Events](#handling-scheduled-events)). Recurring ones persist until cancelled (see [Recurring Schedules](#recurring-schedules-cron)).
 
 `ctx.schedule` and the agent's `scheduler.schedule` both target the scheduler Lambda, which the stack deploys only when `socialagent.<env>.yaml` sets `features.scheduler_lambda: true` (every blueprint sets it). Without it a schedule targets the notification Lambda, which runs only the built-in sends `send_text`, `send_template` and `send_message`. Both calls still schedule those, and refuse any other operation with `SchedulerUnavailableError`, a `ValueError` whose message names the setting, before anything is created: the notification Lambda would answer it with a 400 that EventBridge counts as delivered, so a one-shot would delete itself unsent and a recurring one would fail every time. Catch it as `ValueError`, or by name: a handler imports it from `socialagent.handlers.event`, and an agent tool from `socialagent_runtime.scheduler`, a class of its own with the same name, since the runtime cannot import the Lambda layer. `socialagent dev` refuses the same when `socialagent.<env>.yaml` turns the flag off, and `socialagent deploy` prints a warning when a file under the handlers directory registers an `@app.on_schedule` handler while the flag is off. A schedule's target is fixed when the schedule is created, so one made before the flag was turned on keeps the notification Lambda until you cancel it and create it again; one of those for an `@app.on_schedule` operation, made before the refusal or by an agent whose vendored `socialagent_runtime/` predates it, is dropped with an ERROR in the notification Lambda's log.
`````

[Back to the shelf](README.md)
