# Fix 131: SMART toolkit docs: the security notes do not say how to log access to two unlogged buckets

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: docs: tell production deployers how to log access to the audit-trails and template-sync buckets
- Bug report: number 93 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/93))
- Project license: Apache-2.0
- Language: Markdown
- Test included: no
- Patch file: [fixes/131-social-messaging-agent-runtime-toolkit-93.patch](fixes/131-social-messaging-agent-runtime-toolkit-93.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/131-social-messaging-agent-runtime-toolkit-93.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-131-social-messaging-agent-runtime-toolkit-93.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-131-social-messaging-agent-runtime-toolkit-93.html

## The bug

Scope Notes for Deployers in SECURITY.md lists the audit-trails bucket and the template-sync bucket as unlogged. The notes gave no reason for the template-sync bucket and ended with Turn on the logging your audit policy needs without saying how.

## The fix

SECURITY.md now gives the template-sync bucket's reason (the only dependable log target would be the bucket itself) and says how to log both buckets: send their server access logs to a separate log bucket the deployer owns or turn on CloudTrail S3 data events for the two buckets.

## Files changed

- SECURITY.md

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 131-social-messaging-agent-runtime-toolkit-93.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 93.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docs only. The reason text follows the project's own .ash.yaml entry for the template-sync bucket. No changelog line is included.

## Search words

SMART SECURITY.md Scope Notes for Deployers audit-trails bucket template-sync bucket S3 server access logging CloudTrail data events

## The full patch

`````diff
diff --git a/SECURITY.md b/SECURITY.md
index fe3210c..9f1dcd7 100644
--- a/SECURITY.md
+++ b/SECURITY.md
@@ -27,6 +27,6 @@ Two SNS topics are unencrypted at rest by default, the inbound WhatsApp topic an
 
 Two defaults deserve a decision before real traffic. Per-user rate limiting is enforced only with the DynamoDB state table (`features.state_table: true`), which is off by default (the `personal-assistant` and `appointment-scheduler` blueprints turn it on in the `socialagent.dev.yaml` they ship): without it any WhatsApp user can drive unbounded paid model calls, and the webhook only logs a warning at cold start. And the Bedrock guardrail evaluates only the text of the model calls that pass it, a PDF summary treated as unguarded, and a custom agent must pass it itself ([Guardrails](docs/configuration.md#guardrails) says which calls pass it). Its blocked messages default to English, and all its filters but the PII ones support only English, French and Spanish, where AWS says a guardrail is ineffective in a language it does not support ([the guardrail policy](docs/configuration.md#the-guardrail-policy)). AWS Budgets alerts and webhook reserved concurrency are useful cost backstops.
 
-The edge is the deployer's too. Neither the stack nor the admin console creates an AWS WAF web ACL: attach a regional one to the event API's stage, and one with CloudFront scope, created in us-east-1, to the console's distribution. The console's API is an HTTP API, which AWS WAF does not support, so its Cognito JWT authorizer and the backend's per-route group check are what stand in front of it. Request logging is partial: the event API and the console's API have access logging to CloudWatch Logs, and two buckets configure S3 server access logging, the per-stack media bucket, which delivers to the audit-trails bucket under `s3-access-logs/conversation-logs/`, and the console's own registry bucket (created only when the console's `shared_runtime_bucket` is empty), which delivers to itself under `s3-access-logs/`. The console's CloudFront distribution and site bucket, the audit-trails bucket itself, the build buckets (the template-sync bucket among them), the Terraform state buckets and the shared runtime and artifacts buckets (`shared_runtime_bucket`, which also holds the console's registry under `admin/registry/`, and `shared_artifacts_bucket`) have none. AWS advises against a bucket logging to itself: S3 logs each delivery as one more access, so the bucket writes logs about its own log deliveries forever, even with no other traffic. So the audit-trails bucket, the stack's log destination, does not log its own access, and since the stack's CloudTrail trail records Bedrock data events only, nothing logs object-level access to the audit logs. The registry bucket logs to itself because the console has no other bucket for its logs, so a lifecycle rule expires them after about 90 days; the media bucket's logs are kept, like everything in the audit-trails bucket, until the deployer removes them. S3 delivers server access logs to a bucket with ACLs disabled, the default for new buckets, only if that bucket's policy lets `logging.s3.amazonaws.com` call `s3:PutObject`, so each target bucket's policy grants it that on the configuration's log prefix, for the source bucket and this account only; after a deploy, check that logs arrive under `s3-access-logs/`. With shared buckets there is no server access logging at all, and the stack's CloudTrail trail records Bedrock data events only, so nothing logs object-level access to conversation media. Turn on the logging your audit policy needs. And the console is served on CloudFront's default `*.cloudfront.net` certificate, on which CloudFront fixes the viewer security policy at `TLSv1`, so it accepts TLS 1.0 and 1.1; in production serve it on a custom domain with an ACM certificate and the `TLSv1.2_2021` policy ([Serving the console on a custom domain](docs/admin-console.md#serving-the-console-on-a-custom-domain)).
+The edge is the deployer's too. Neither the stack nor the admin console creates an AWS WAF web ACL: attach a regional one to the event API's stage, and one with CloudFront scope, created in us-east-1, to the console's distribution. The console's API is an HTTP API, which AWS WAF does not support, so its Cognito JWT authorizer and the backend's per-route group check are what stand in front of it. Request logging is partial: the event API and the console's API have access logging to CloudWatch Logs, and two buckets configure S3 server access logging, the per-stack media bucket, which delivers to the audit-trails bucket under `s3-access-logs/conversation-logs/`, and the console's own registry bucket (created only when the console's `shared_runtime_bucket` is empty), which delivers to itself under `s3-access-logs/`. The console's CloudFront distribution and site bucket, the audit-trails bucket itself, the build buckets (the template-sync bucket among them), the Terraform state buckets and the shared runtime and artifacts buckets (`shared_runtime_bucket`, which also holds the console's registry under `admin/registry/`, and `shared_artifacts_bucket`) have none. AWS advises against a bucket logging to itself: S3 logs each delivery as one more access, so the bucket writes logs about its own log deliveries forever, even with no other traffic. So the audit-trails bucket, the stack's log destination, does not log its own access, and since the stack's CloudTrail trail records Bedrock data events only, nothing logs object-level access to the audit logs. The template-sync bucket does not log its own access for the same reason: the only log target the stack could dependably give it is the bucket itself. The registry bucket logs to itself because the console has no other bucket for its logs, so a lifecycle rule expires them after about 90 days; the media bucket's logs are kept, like everything in the audit-trails bucket, until the deployer removes them. S3 delivers server access logs to a bucket with ACLs disabled, the default for new buckets, only if that bucket's policy lets `logging.s3.amazonaws.com` call `s3:PutObject`, so each target bucket's policy grants it that on the configuration's log prefix, for the source bucket and this account only; after a deploy, check that logs arrive under `s3-access-logs/`. With shared buckets there is no server access logging at all, and the stack's CloudTrail trail records Bedrock data events only, so nothing logs object-level access to conversation media. Turn on the logging your audit policy needs: for the audit-trails and template-sync buckets, a production deployment either sends their server access logs to a separate log bucket it owns (never to the bucket being logged) or turns on CloudTrail S3 data events for the two buckets. And the console is served on CloudFront's default `*.cloudfront.net` certificate, on which CloudFront fixes the viewer security policy at `TLSv1`, so it accepts TLS 1.0 and 1.1; in production serve it on a custom domain with an ACM certificate and the `TLSv1.2_2021` policy ([Serving the console on a custom domain](docs/admin-console.md#serving-the-console-on-a-custom-domain)).
 
 See the [Threat Model](docs/threat-model.md) for the full trust-boundary analysis, threats, mitigations, and the accepted risks a production deployer must address.
`````

[Back to the shelf](README.md)
