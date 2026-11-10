# Fix 264: security-checker: public names in github/client.py have no docstring (__enter__ and __exit__ and two __init__ methods and close and create_issue_comment and create_review and head_sha and issue_comments and pull_files and review_comments and update_issue_comment)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(github): client.py の公開クラス・メソッド 12 個に docstring が無い
- Bug report: number 395 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/395))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/264-security-checker-395.patch](fixes/264-security-checker-395.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/264-security-checker-395.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-264-security-checker-395.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-264-security-checker-395.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/github/client.py: __enter__ and __exit__ and two __init__ methods and close and create_issue_comment and create_review and head_sha and issue_comments and pull_files and review_comments and update_issue_comment. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/github/client.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/github/client.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 264-security-checker-395.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 395.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 132 on this shelf changes the __enter__ line that this patch documents so patches 132 and 264 do not apply together: apply one and add the other change by hand. Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring client.py __enter__ and __exit__ and two __init__ methods and close and create_issue_comment and create_review and head_sha and issue_comments and pull_files and review_comments and update_issue_comment

## The full patch

`````diff
diff --git a/src/security_checker/github/client.py b/src/security_checker/github/client.py
index 8fcf3b0..f6795be 100644
--- a/src/security_checker/github/client.py
+++ b/src/security_checker/github/client.py
@@ -37,6 +37,7 @@ class GithubError(SecurityCheckerError):
     """GitHub API の呼び出しに失敗した."""
 
     def __init__(self, message: str, status_code: int | None = None) -> None:
+        """`status_code` は GitHub が返した HTTP ステータス. 接続できなかったときは None."""
         super().__init__(message)
         self.status_code = status_code
 
@@ -88,6 +89,7 @@ class GithubClient:
         api_url: str = DEFAULT_API_URL,
         transport: httpx.BaseTransport | None = None,
     ) -> None:
+        """`token` で認証する HTTP クライアントを作る. `transport` はテストで差し替える."""
         self._client = httpx.Client(
             base_url=api_url.rstrip("/"),
             headers={
@@ -101,12 +103,15 @@ class GithubClient:
         )
 
     def close(self) -> None:
+        """HTTP クライアントを閉じる."""
         self._client.close()
 
     def __enter__(self) -> GithubClient:
+        """with 文で使えるようにする. 抜けるときに閉じる."""
         return self
 
     def __exit__(self, *_: object) -> None:
+        """with 文を抜けるときに閉じる. 例外は握り潰さない."""
         self.close()
 
     def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
@@ -140,9 +145,11 @@ class GithubClient:
         return items
 
     def issue_comments(self, pr: PullRequestContext) -> list[dict[str, Any]]:
+        """PR の会話欄のコメントをすべて取る (ページをたどる)."""
         return self._paginate(f"/repos/{pr.repository}/issues/{pr.number}/comments")
 
     def create_issue_comment(self, pr: PullRequestContext, body: str) -> dict[str, Any]:
+        """PR の会話欄にコメントを 1 件投稿する."""
         url = f"/repos/{pr.repository}/issues/{pr.number}/comments"
         result: dict[str, Any] = self._request("POST", url, json={"body": body}).json()
         return result
@@ -150,23 +157,28 @@ class GithubClient:
     def update_issue_comment(
         self, pr: PullRequestContext, comment_id: int, body: str
     ) -> dict[str, Any]:
+        """既存のコメントの本文を書き換える (sticky コメントの更新)."""
         url = f"/repos/{pr.repository}/issues/comments/{comment_id}"
         result: dict[str, Any] = self._request("PATCH", url, json={"body": body}).json()
         return result
 
     def review_comments(self, pr: PullRequestContext) -> list[dict[str, Any]]:
+        """PR の inline コメント (レビューコメント) をすべて取る."""
         return self._paginate(f"/repos/{pr.repository}/pulls/{pr.number}/comments")
 
     def pull_files(self, pr: PullRequestContext) -> list[dict[str, Any]]:
+        """PR で変更されたファイルの一覧をすべて取る."""
         return self._paginate(f"/repos/{pr.repository}/pulls/{pr.number}/files")
 
     def head_sha(self, pr: PullRequestContext) -> str:
+        """PR の head のコミット SHA を API から取る."""
         data = self._request("GET", f"/repos/{pr.repository}/pulls/{pr.number}").json()
         return str(data["head"]["sha"])
 
     def create_review(
         self, pr: PullRequestContext, commit_id: str, comments: list[dict[str, Any]]
     ) -> dict[str, Any]:
+        """inline コメントをまとめて 1 つのレビュー (COMMENT) として投稿する."""
         url = f"/repos/{pr.repository}/pulls/{pr.number}/reviews"
         payload = {
             "commit_id": commit_id,
`````

[Back to the shelf](README.md)
