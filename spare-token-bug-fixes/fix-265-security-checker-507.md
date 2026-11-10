# Fix 265: security-checker: no test covers reading the head commit of a pull request

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): client.py の head_sha で未テストの分岐をテストする（2 行）
- Bug report: number 507 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/507))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/265-security-checker-507.patch](fixes/265-security-checker-507.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/265-security-checker-507.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-265-security-checker-507.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-265-security-checker-507.html

## The bug

GithubClient.head_sha in src/security_checker/github/client.py asks the GitHub API for the head commit of a pull request. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_github_client_head_sha.py answers the request with a stand-in transport and expects the commit id and the request path.

## Files changed

- tests/unit/test_github_client_head_sha.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 265-security-checker-507.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 507.

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

security-checker github client head_sha pulls head sha MockTransport untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_github_client_head_sha.py b/tests/unit/test_github_client_head_sha.py
new file mode 100644
index 0000000..61098d0
--- /dev/null
+++ b/tests/unit/test_github_client_head_sha.py
@@ -0,0 +1,22 @@
+"""GithubClient.head_sha: PR の head の SHA を API から取ること."""
+
+from __future__ import annotations
+
+import httpx
+
+from security_checker.github.client import GithubClient, PullRequestContext
+
+PR = PullRequestContext(repository="owner/repo", number=7)
+
+
+def test_head_sha_is_read_from_the_pull_request() -> None:
+    seen: list[tuple[str, str]] = []
+
+    def handler(request: httpx.Request) -> httpx.Response:
+        seen.append((request.method, request.url.path))
+        return httpx.Response(200, json={"number": 7, "head": {"sha": "abc123"}})
+
+    with GithubClient("token", transport=httpx.MockTransport(handler)) as client:
+        assert client.head_sha(PR) == "abc123"
+
+    assert seen == [("GET", "/repos/owner/repo/pulls/7")]
`````

[Back to the shelf](README.md)
