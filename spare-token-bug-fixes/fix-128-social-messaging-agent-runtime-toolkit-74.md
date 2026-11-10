# Fix 128: SMART admin console: the State views list the scheduler's firing records as users

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: console: State views list scheduler firing records as users
- Bug report: number 74 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/74))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/128-social-messaging-agent-runtime-toolkit-74.patch](fixes/128-social-messaging-agent-runtime-toolkit-74.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/128-social-messaging-agent-runtime-toolkit-74.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-128-social-messaging-agent-runtime-toolkit-74.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-128-social-messaging-agent-runtime-toolkit-74.html

## The bug

With the state table on the scheduler writes one record per scheduled firing under a partition key that starts with _schedule#. The admin console's State page and the stack's State tab listed those rows next to real users' keys and counted each one as a user.

## The fix

socialagent-admin-console/backend/routes/state.py now skips every row whose partition key starts with _schedule# in the per-stack listing and in the cross-stack listing. A new file backend/tests/unit/test_state_internal_partitions.py stores one user key and one firing record and expects only the user key from both listings. CHANGELOG.md gains one line.

## Files changed

- CHANGELOG.md
- socialagent-admin-console/backend/routes/state.py
- socialagent-admin-console/backend/tests/unit/test_state_internal_partitions.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 128-social-messaging-agent-runtime-toolkit-74.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 74.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The rows are left out before the 2000-row safety cap is counted. The chatbot did not run the tests (they need the moto package and the project's test setup). Fixes 72 and 96 and 97 and 99 and 126 and 128 and 129 on this shelf each add text at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand.

## Search words

SMART admin console state page _schedule# FiringRecord partition users count routes/state.py handle_get_state handle_list_all_state

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..382c065 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Admin console (beta)
+- The State page and the stack's State tab leave out the scheduler's firing records (`_schedule#` partitions), so they are no longer listed or counted as users.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/socialagent-admin-console/backend/routes/state.py b/socialagent-admin-console/backend/routes/state.py
index c8fbc59..978dab5 100644
--- a/socialagent-admin-console/backend/routes/state.py
+++ b/socialagent-admin-console/backend/routes/state.py
@@ -25,6 +25,18 @@ _STATE_TABLE_RE = re.compile(r"^[A-Za-z0-9_.-]+-state$")
 def _is_valid_state_table(name: str) -> bool:
     return bool(name) and len(name) <= 255 and _STATE_TABLE_RE.match(name) is not None
 
+
+# The scheduler keeps one record per scheduled firing under a partition key of
+# its own (``_schedule#<hash>``, see FiringRecord in handlers/scheduled.py).
+# Those rows are bookkeeping, not a user's state, so the state views leave
+# them out of the rows and of the user count.
+_INTERNAL_PARTITION_PREFIX = "_schedule#"
+
+
+def _is_internal_partition(pk) -> bool:
+    return isinstance(pk, str) and pk.startswith(_INTERNAL_PARTITION_PREFIX)
+
+
 def handle_delete_state_key(params, body):
     """Delete a single key from the state table, phone and key from the JSON body.
 
@@ -73,6 +85,8 @@ def handle_get_state(params, _body):
         while True:
             resp = table.scan(**kwargs)
             for item in resp.get("Items", []):
+                if _is_internal_partition(item.get("pk")):
+                    continue
                 raw = item.get("data", "")
                 try:
                     value = json.loads(raw) if isinstance(raw, str) else raw
@@ -110,6 +124,8 @@ def handle_list_all_state(_params, _body):
             while True:
                 resp = table.scan(**kwargs)
                 for item in resp.get("Items", []):
+                    if _is_internal_partition(item.get("pk")):
+                        continue
                     raw = item.get("data", "")
                     try:
                         value = json.loads(raw) if isinstance(raw, str) else raw
diff --git a/socialagent-admin-console/backend/tests/unit/test_state_internal_partitions.py b/socialagent-admin-console/backend/tests/unit/test_state_internal_partitions.py
new file mode 100644
index 0000000..2c9db14
--- /dev/null
+++ b/socialagent-admin-console/backend/tests/unit/test_state_internal_partitions.py
@@ -0,0 +1,63 @@
+# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
+# SPDX-License-Identifier: Apache-2.0
+
+"""The state views leave out the scheduler's firing records.
+
+With the state table on, the scheduler writes one record per scheduled firing
+under a partition key of its own (``_schedule#<hash>``). Those rows are not a
+user's state, so neither the per-stack listing nor the cross-stack listing
+returns them, and the console does not count them as users.
+"""
+
+import json
+
+import boto3
+import pytest
+from moto import mock_aws
+
+# Route modules read shared.config at import time, which needs the env vars the
+# autouse aws_env fixture provides, so import inside each test or fixture.
+
+TABLE = "bot-dev-state"
+PHONE = "+15555550100"
+FIRING_PK = "_schedule#3f2a9c"
+
+
+@pytest.fixture
+def state(monkeypatch):
+    from routes import state as state_routes
+
+    registry = {"region": "us-east-1", "outputs": {"state_table_name": TABLE}}
+    monkeypatch.setattr(state_routes, "_get_registry", lambda sid: registry)
+    monkeypatch.setattr(state_routes, "_get_all_registries", lambda: {"bot-dev": registry})
+    with mock_aws():
+        boto3.client("dynamodb", region_name="us-east-1").create_table(
+            TableName=TABLE,
+            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
+            AttributeDefinitions=[
+                {"AttributeName": "pk", "AttributeType": "S"},
+                {"AttributeName": "sk", "AttributeType": "S"},
+            ],
+            BillingMode="PAY_PER_REQUEST",
+        )
+        table = boto3.resource("dynamodb", region_name="us-east-1").Table(TABLE)
+        table.put_item(Item={"pk": PHONE, "sk": "booking", "data": json.dumps({"slot": "10:00"})})
+        table.put_item(Item={"pk": FIRING_PK, "sk": "firing#2026-11-05T10:00:00Z", "data": "{}"})
+        yield state_routes
+
+
+def _body(response) -> list:
+    return json.loads(response["body"])
+
+
+def test_the_stack_state_listing_leaves_out_firing_records(state):
+    entries = _body(state.handle_get_state({"id": "bot-dev"}, {}))
+
+    assert [(e["phone"], e["key"]) for e in entries] == [(PHONE, "booking")]
+
+
+def test_the_cross_stack_listing_leaves_out_firing_records(state):
+    entries = _body(state.handle_list_all_state({}, {}))
+
+    assert [(e["phone"], e["key"], e["stack"]) for e in entries] == [(PHONE, "booking", "bot-dev")]
+    assert {e["phone"] for e in entries} == {PHONE}
`````

[Back to the shelf](README.md)
