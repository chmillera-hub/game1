# Fix 266: security-checker: no test covers a connection failure or a non-JSON error body in the GitHub client

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): client.py の _request で未テストの分岐をテストする（4 行）
- Bug report: number 506 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/506))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/266-security-checker-506.patch](fixes/266-security-checker-506.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/266-security-checker-506.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-266-security-checker-506.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-266-security-checker-506.html

## The bug

GithubClient._request in src/security_checker/github/client.py turns a connection failure and an error reply whose body is not JSON into a GithubError. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_github_client_request_errors.py uses a stand-in transport and checks a refused connection and a 502 reply with an HTML body and a 404 reply with a JSON message.

## Files changed

- tests/unit/test_github_client_request_errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 266-security-checker-506.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 506.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker github client _request httpx.HTTPError GithubError ValueError status_code untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_github_client_request_errors.py b/tests/unit/test_github_client_request_errors.py
new file mode 100644
index 0000000..5924f86
--- /dev/null
+++ b/tests/unit/test_github_client_request_errors.py
@@ -0,0 +1,49 @@
+"""GithubClient._request: 接続できない・本文が JSON でない失敗を GithubError にすること."""
+
+from __future__ import annotations
+
+import httpx
+import pytest
+
+from security_checker.github.client import GithubClient, GithubError, PullRequestContext
+
+PR = PullRequestContext(repository="owner/repo", number=7)
+
+
+def test_connection_failure_is_a_github_error() -> None:
+    def handler(request: httpx.Request) -> httpx.Response:
+        raise httpx.ConnectError("connection refused", request=request)
+
+    with (
+        GithubClient("token", transport=httpx.MockTransport(handler)) as client,
+        pytest.raises(GithubError, match="GitHub API に接続できません"),
+    ):
+        client.head_sha(PR)
+
+
+def test_error_with_a_body_that_is_not_json_is_still_a_github_error() -> None:
+    def handler(_request: httpx.Request) -> httpx.Response:
+        return httpx.Response(502, text="<html>Bad Gateway</html>")
+
+    with (
+        GithubClient("token", transport=httpx.MockTransport(handler)) as client,
+        pytest.raises(GithubError) as excinfo,
+    ):
+        client.head_sha(PR)
+
+    assert excinfo.value.status_code == 502
+
+
+def test_error_with_a_json_message_keeps_the_status() -> None:
+    """対になるケース. JSON の message がある失敗もステータスを持つ GithubError になる."""
+
+    def handler(_request: httpx.Request) -> httpx.Response:
+        return httpx.Response(404, json={"message": "Not Found"})
+
+    with (
+        GithubClient("token", transport=httpx.MockTransport(handler)) as client,
+        pytest.raises(GithubError, match="Not Found") as excinfo,
+    ):
+        client.head_sha(PR)
+
+    assert excinfo.value.status_code == 404
`````

[Back to the shelf](README.md)
