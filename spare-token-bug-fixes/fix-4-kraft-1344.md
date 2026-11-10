# Fix 4: kraft: update_repo skips the shared response handling

Status: UNSENT and UNTESTED. Free to take.

- Project: itsOmidKarami/kraft
- Bug report title: update_repo reports an answer that isn't JSON as success
- Bug report: number 1344 ([open the bug report](https://github.com/itsOmidKarami/kraft/issues/1344))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/4-kraft-1344.patch](fixes/4-kraft-1344.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/4-kraft-1344.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-4-kraft-1344.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-4-kraft-1344.html

## The bug

The client call update_repo parsed the server reply with code of its own. A reply with status 200 and a body that is not JSON (for example an HTML page from a proxy) slipped through as a fake success. The other client calls report that case as a bad response.

## The fix

The fix makes update_repo use the shared helpers transport._detail and transport._json in src/kraft/client/actions.py. A new parametrized test case named text-200-patch covers the HTML reply.

## Files changed

- src/kraft/client/actions.py
- tests/client/test_transport.py

## How to use the fix

1. Get a copy of the project itsOmidKarami/kraft.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 4-kraft-1344.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1344.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

kraft client update_repo BAD_RESPONSE non-JSON 200 response proxy html transport._json transport._detail status_error

## The full patch

`````diff
diff --git a/src/kraft/client/actions.py b/src/kraft/client/actions.py
index 7043869..82b72ba 100644
--- a/src/kraft/client/actions.py
+++ b/src/kraft/client/actions.py
@@ -241,13 +241,9 @@ async def ensure_repo(
 async def update_repo(path: str, fields: dict) -> dict:
     """Change a connected repo's `fields` (`PATCH /repos`); the entry as saved."""
     response = await transport._send("PATCH", "/repos", params={"path": path}, json=fields)
-    try:
-        body = response.json() if response.content else {}
-    except ValueError:
-        body = {"detail": response.text}
     if response.status_code >= 400:
-        raise transport.status_error(response.status_code, str(body.get("detail", body)))
-    return body
+        raise transport.status_error(response.status_code, transport._detail(response))
+    return transport._json(response) if response.content else {}
 
 
 async def _connected_path(path: str | None) -> str:
diff --git a/tests/client/test_transport.py b/tests/client/test_transport.py
index 2daed93..48c5bde 100644
--- a/tests/client/test_transport.py
+++ b/tests/client/test_transport.py
@@ -263,6 +263,11 @@ _ELSEWHERE = httpx.Response(200, json={"run_dir": "/elsewhere"})
             client.Failure.SERVER_ERROR,
             httpx.Response(500, text="Internal Server Error"),
         ),
+        (
+            lambda: client.update_repo("/r", {}),
+            client.Failure.BAD_RESPONSE,
+            httpx.Response(200, text="<html>proxy</html>"),
+        ),
         (
             lambda: client.pause(work_item_id="w1"),
             client.Failure.BAD_RESPONSE,
@@ -279,6 +284,7 @@ _ELSEWHERE = httpx.Response(200, json={"run_dir": "/elsewhere"})
         "blank-note",
         "no-item",
         "text-500",
+        "text-200-patch",
         "text-200-post",
         "update-not-object",
     ],
`````

[Back to the shelf](README.md)
