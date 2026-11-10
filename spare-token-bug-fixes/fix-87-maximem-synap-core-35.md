# Fix 87: maximem_synap_core: a new client-level memory is missing from cached user fetches for up to five minutes

Status: UNSENT and UNTESTED. Free to take.

- Project: maximem-ai/maximem_synap_core
- Bug report title: Client-scope memories don't appear in cached user fetches for up to 5 minutes
- Bug report: number 35 ([open the bug report](https://github.com/maximem-ai/maximem_synap_core/issues/35))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/87-maximem-synap-core-35.patch](fixes/87-maximem-synap-core-35.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/87-maximem-synap-core-35.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-87-maximem-synap-core-35.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-87-maximem-synap-core-35.html

## The bug

After a client-level memory was stored only the cached results under the client's global entry were cleared. Fetches for a user or a customer also include client-level memories and kept serving the cached result without the new memory for up to 300 seconds.

## The fix

synap/cloud/application/client_api/retrieval_manager.py gains _l1_invalidation_pattern. A write with no customer and no user clears every cached query result of the client. Every other write keeps the narrow pattern as before. invalidate_user_cache uses the helper. A new file synap/tests/application/test_l1_invalidation_pattern.py covers the four combinations.

## Files changed

- synap/cloud/application/client_api/retrieval_manager.py
- synap/tests/application/test_l1_invalidation_pattern.py

## How to use the fix

1. Get a copy of the project maximem-ai/maximem_synap_core.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 87-maximem-synap-core-35.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 35.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot treats a write with no customer and no user as a client-level write. That reading comes from the bug report and from the call in stage4_worker.py and the chatbot did not confirm the reading by running the pipeline. Only the cached query results are widened. The separate in-memory graph cache in the same function is unchanged. Fix 70 on this shelf changes other lines of the same file and the two patches apply together. The chatbot did not run the project's tests.

## Search words

maximem synap invalidate_user_cache client-scope memory L1 cache query:{client}:global stale 300s stage4_worker

## The full patch

`````diff
diff --git a/synap/cloud/application/client_api/retrieval_manager.py b/synap/cloud/application/client_api/retrieval_manager.py
index c47fc50..4c1148d 100644
--- a/synap/cloud/application/client_api/retrieval_manager.py
+++ b/synap/cloud/application/client_api/retrieval_manager.py
@@ -1878,6 +1878,23 @@ def invalidate_visibility_cache(client_id: str) -> None:
     _visibility_bundle_cache.pop(client_id, None)
 
 
+def _l1_invalidation_pattern(
+    effective_client: str, customer_id: str, user_id: Optional[str]
+) -> str:
+    """The L1 key pattern a memory write must clear.
+
+    A write with no customer and no user is a client-scope memory. User and
+    customer fetches include client-level memories too, so their cached
+    bundles live under ``query:{client}:{customer}:*`` and would keep serving
+    the pre-write result for the whole TTL. Such a write therefore clears the
+    whole ``query:{client}:*`` namespace, as the delete path already does.
+    Every other write keeps the narrow ``query:{client}:{customer}:*`` pattern.
+    """
+    if not customer_id and not user_id:
+        return f"query:{effective_client}:*"
+    return f"query:{effective_client}:{customer_id or 'global'}:*"
+
+
 async def invalidate_client_query_cache(client_id: str) -> int:
     """Bust every cached L1 query result for a client (Redis, cross-process).
 
@@ -9858,8 +9875,7 @@ class RetrievalManager:
             return 0
 
         try:
-            # Pattern: query:{client_id}:{customer_id}:*
-            pattern = f"query:{effective_client}:{effective_customer}:*"
+            pattern = _l1_invalidation_pattern(effective_client, customer_id, user_id)
             cursor = 0
             deleted = 0
 
diff --git a/synap/tests/application/test_l1_invalidation_pattern.py b/synap/tests/application/test_l1_invalidation_pattern.py
new file mode 100644
index 0000000..9d91d89
--- /dev/null
+++ b/synap/tests/application/test_l1_invalidation_pattern.py
@@ -0,0 +1,29 @@
+"""A client-scope write must clear every cached fetch of the client.
+
+User and customer fetches include client-level memories, so clearing only
+``query:{client}:global:*`` left their cached bundles stale for up to 300 s.
+"""
+
+import fnmatch
+
+from synap.cloud.application.client_api.retrieval_manager import _l1_invalidation_pattern
+
+
+class TestL1InvalidationPattern:
+    def test_client_scope_write_clears_the_whole_client_namespace(self):
+        pattern = _l1_invalidation_pattern("c1", "", None)
+        assert pattern == "query:c1:*"
+        assert fnmatch.fnmatchcase("query:c1:global:abc", pattern)
+        assert fnmatch.fnmatchcase("query:c1:cust1:abc", pattern)
+        assert not fnmatch.fnmatchcase("query:c2:cust1:abc", pattern)
+
+    def test_customer_scope_write_stays_within_the_customer(self):
+        pattern = _l1_invalidation_pattern("c1", "cust1", None)
+        assert pattern == "query:c1:cust1:*"
+        assert not fnmatch.fnmatchcase("query:c1:cust2:abc", pattern)
+
+    def test_user_write_without_customer_keeps_the_global_pattern(self):
+        assert _l1_invalidation_pattern("c1", "", "u1") == "query:c1:global:*"
+
+    def test_user_write_with_customer_stays_within_the_customer(self):
+        assert _l1_invalidation_pattern("c1", "cust1", "u1") == "query:c1:cust1:*"
`````

[Back to the shelf](README.md)
