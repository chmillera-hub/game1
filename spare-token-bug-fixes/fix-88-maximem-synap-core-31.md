# Fix 88: maximem_synap_core: one passing server error from the cloud service permanently fails a MACA job

Status: UNSENT and UNTESTED. Free to take.

- Project: maximem-ai/maximem_synap_core
- Bug report title: MACA plugin job fails permanently on a single 5xx from Cloud
- Bug report: number 31 ([open the bug report](https://github.com/maximem-ai/maximem_synap_core/issues/31))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/88-maximem-synap-core-31.patch](fixes/88-maximem-synap-core-31.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/88-maximem-synap-core-31.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-88-maximem-synap-core-31.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-88-maximem-synap-core-31.html

## The bug

While the plugin waited for a MACA run any answer other than 200 failed the job. A single passing 502 or 503 ended a job that was still running on the cloud service and spending credits and the job could not be resumed.

## The fix

_poll in synap/cloud/application/sdk_api/maca_plugin.py now counts an answer of 500 or above as a failed attempt the same way a network error is counted. The job only fails after six failed attempts in a row and then shows what the cloud service answered. A 4xx answer still fails the job at once. synap/tests/application/test_maca_plugin.py gains three tests: two passing errors and then success and an error on every attempt and a 404.

## Files changed

- synap/cloud/application/sdk_api/maca_plugin.py
- synap/tests/application/test_maca_plugin.py

## How to use the fix

1. Get a copy of the project maximem-ai/maximem_synap_core.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 88-maximem-synap-core-31.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 31.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Network errors and 5xx answers share one counter so a mix of the two in a row also ends the job after six attempts. The chatbot modelled the counting in a scratch script and did not run the project's tests. The three new tests sit at one spot of the existing test file so a second patch that adds tests at the same spot would not apply together with this patch.

## Search words

maximem synap maca_plugin _poll 5xx 502 503 transient retry MAX_POLL_FAILURES job fails permanently

## The full patch

`````diff
diff --git a/synap/cloud/application/sdk_api/maca_plugin.py b/synap/cloud/application/sdk_api/maca_plugin.py
index 7df807a..33dcd3b 100644
--- a/synap/cloud/application/sdk_api/maca_plugin.py
+++ b/synap/cloud/application/sdk_api/maca_plugin.py
@@ -295,13 +295,21 @@ async def _poll(client: httpx.AsyncClient, job: Job) -> None:
     while True:
         try:
             resp = await client.get(f"{BUILDS_PATH}/{job.build_id}")
-            failures = 0
         except httpx.RequestError:
             failures += 1
             if failures >= MAX_POLL_FAILURES:
                 raise _CloudError(NETWORK_MESSAGE) from None
             resp = None
+        if resp is not None and resp.status_code >= 500:
+            # A 5xx on a status poll (a 502 or 503 from a proxy, say) is not a
+            # verdict on the run, which may still be working and spending
+            # credits on Cloud. Retry it the way a network error is retried.
+            failures += 1
+            if failures >= MAX_POLL_FAILURES:
+                raise _CloudError(_cloud_error(resp))
+            resp = None
         if resp is not None:
+            failures = 0
             if resp.status_code != 200:
                 raise _CloudError(_cloud_error(resp))
             try:
diff --git a/synap/tests/application/test_maca_plugin.py b/synap/tests/application/test_maca_plugin.py
index 4728c00..3c15c63 100644
--- a/synap/tests/application/test_maca_plugin.py
+++ b/synap/tests/application/test_maca_plugin.py
@@ -371,6 +371,52 @@ def test_a_run_that_never_finishes_times_out(env, monkeypatch):
     assert body["status"] == "failed" and "taking longer" in body["message"]
 
 
+def _poll_answers(cloud, answer):
+    """A fake Cloud whose status poll is answered by ``answer`` (None falls through to ``cloud``)."""
+    def transport(request):
+        if request.method == "GET" and request.url.path == f"{mp.BUILDS_PATH}/b1":
+            resp = answer(request)
+            if resp is not None:
+                return resp
+        return cloud(request)
+    return transport
+
+
+def test_a_passing_5xx_while_polling_does_not_fail_the_job(env, monkeypatch):
+    flaky = [httpx.Response(503, json={"detail": "busy"}), httpx.Response(502, text="bad gateway")]
+    transport = _poll_answers(FakeCloud(), lambda r: flaky.pop(0) if flaky else None)
+    with TestClient(_app(transport, monkeypatch)) as c:
+        body = _wait(c, _start(c).json()["job_id"])
+    assert body["status"] == "succeeded"
+    assert flaky == []
+
+
+def test_a_5xx_on_every_poll_fails_the_job_with_what_cloud_said(env, monkeypatch):
+    polls = []
+
+    def down(request):
+        polls.append(request)
+        return httpx.Response(503, json={"detail": "busy"})
+
+    with TestClient(_app(_poll_answers(FakeCloud(), down), monkeypatch)) as c:
+        body = _wait(c, _start(c).json()["job_id"])
+    assert body["status"] == "failed" and "answered 503" in body["message"]
+    assert len(polls) == mp.MAX_POLL_FAILURES
+
+
+def test_a_4xx_while_polling_still_fails_at_once(env, monkeypatch):
+    polls = []
+
+    def gone(request):
+        polls.append(request)
+        return httpx.Response(404, json={"detail": "no such build"})
+
+    with TestClient(_app(_poll_answers(FakeCloud(), gone), monkeypatch)) as c:
+        body = _wait(c, _start(c).json()["job_id"])
+    assert body["status"] == "failed" and "answered 404" in body["message"]
+    assert len(polls) == 1
+
+
 def test_a_redirect_is_not_followed(env, monkeypatch):
     cloud = FakeCloud(submit=lambda r: httpx.Response(302, headers={"location": "https://attacker.example/steal"}))
     with TestClient(_app(cloud, monkeypatch)) as c:
`````

[Back to the shelf](README.md)
