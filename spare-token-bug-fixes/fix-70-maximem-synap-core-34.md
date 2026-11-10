# Fix 70: maximem_synap_core: two different lists of search queries can share one cache entry

Status: UNSENT and UNTESTED. Free to take.

- Project: maximem-ai/maximem_synap_core
- Bug report title: Different query lists share one retrieval cache entry
- Bug report: number 34 ([open the bug report](https://github.com/maximem-ai/maximem_synap_core/issues/34))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/70-maximem-synap-core-34.patch](fixes/70-maximem-synap-core-34.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/70-maximem-synap-core-34.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-70-maximem-synap-core-34.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-70-maximem-synap-core-34.html

## The bug

The retrieval cache key joined the search queries with the | character. The list holding the single query a|b and the list holding the two queries a and b produced the same key. The two lists run different searches and the second caller received the cached results of the first caller.

## The fix

synap/cloud/shared/cache_keys.py gains query_list_component. A list in which no query holds the | character keeps the old plain join so ordinary keys stay the same byte for byte. Any other list is written as the marker ql1: followed by the JSON form of the list. synap/cloud/application/client_api/retrieval_manager.py calls the new helper. A new file synap/tests/agents/test_query_list_cache_component.py covers the case from the bug report and ordinary lists and empty lists and a brute-force search for two lists with one result.

## Files changed

- synap/cloud/application/client_api/retrieval_manager.py
- synap/cloud/shared/cache_keys.py
- synap/tests/agents/test_query_list_cache_component.py

## How to use the fix

1. Get a copy of the project maximem-ai/maximem_synap_core.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 70-maximem-synap-core-34.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 34.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report suggests a JSON list for every key. The chatbot kept the old form for ordinary lists because comments in the project say existing keys should stay byte-identical. That choice is a guess about what the maintainers prefer and a plain JSON list for every key is a valid alternative. A list holding one empty query and an empty list still share the empty component as before. The option markers such as |sqg0 that the caller appends after the queries are outside this fix and a query list ending in a query named like a marker can still match a request with that option set. The chatbot checked the rule with a scratch copy over 16104 small lists and found no two lists with one result. The chatbot did not run the project's code or tests.

## Search words

maximem synap retrieval cache key search_queries pipe join collision l1_query_key _build_cache_key cache_keys.py

## The full patch

`````diff
diff --git a/synap/cloud/application/client_api/retrieval_manager.py b/synap/cloud/application/client_api/retrieval_manager.py
index c47fc50..d6b885a 100644
--- a/synap/cloud/application/client_api/retrieval_manager.py
+++ b/synap/cloud/application/client_api/retrieval_manager.py
@@ -35,7 +35,7 @@ from synap.cloud.agents.models.bundles import (
 from synap.cloud.shared import graph_boundary as _graph_boundary
 from synap.cloud.shared import scope_filter as _scope_filter
 from synap.cloud.shared.scope import ScopeResolver, ScopeHierarchy, derive_item_scope
-from synap.cloud.shared.cache_keys import CacheKeyGenerator
+from synap.cloud.shared.cache_keys import CacheKeyGenerator, query_list_component
 from synap.cloud.shared.scope_rung import rung_key_from_rungs as _rung_key_from_rungs
 from synap.cloud.shared.confidence import meets_confidence_threshold, ConfidenceConfig
 from synap.cloud.shared.tokens import TokenCounter
@@ -9690,7 +9690,7 @@ class RetrievalManager:
         if _chain:
             _skip_suffix += "|chain:" + ",".join(_chain)
 
-        _query_component = "|".join(decision.search_queries) if decision.search_queries else ""
+        _query_component = query_list_component(decision.search_queries)
 
         cache_key = CacheKeyGenerator.l1_query_key(
             client_id=resolved_client_id,
diff --git a/synap/cloud/shared/cache_keys.py b/synap/cloud/shared/cache_keys.py
index 98ef964..6c68ebf 100644
--- a/synap/cloud/shared/cache_keys.py
+++ b/synap/cloud/shared/cache_keys.py
@@ -10,6 +10,7 @@ non-anticipation callers (e.g. ``retrieval_manager``) keep working.
 """
 
 import hashlib
+import json
 import os
 from dataclasses import dataclass, field
 from typing import List, Optional, Sequence, Tuple
@@ -73,6 +74,31 @@ def _payload_build() -> str:
     return os.environ.get("SYNAP_BUILD_SHA") or "dev"
 
 
+_QUERY_LIST_PREFIX = "ql1:"
+
+
+def query_list_component(queries: Optional[Sequence[str]]) -> str:
+    """A list of search queries as one unambiguous key component.
+
+    The queries used to be joined with ``|`` and nothing else, so
+    ``["a|b"]`` and ``["a", "b"]`` produced the same component. They run
+    different searches, and the second caller was served the first caller's
+    cached bundle.
+
+    A list in which no query contains ``|`` keeps the plain join, so the keys
+    of ordinary requests stay byte-identical. Any other list is written as
+    ``ql1:`` plus its JSON form. The two shapes cannot meet: a plain join
+    never starts with ``ql1:`` because a list whose first query starts with
+    it takes the JSON form too.
+    """
+    items = [str(q) for q in (queries or [])]
+    if not items:
+        return ""
+    if items[0].startswith(_QUERY_LIST_PREFIX) or any("|" in q for q in items):
+        return _QUERY_LIST_PREFIX + json.dumps(items, ensure_ascii=False, separators=(",", ":"))
+    return "|".join(items)
+
+
 @dataclass(frozen=True)
 class ScopeKey:
     """Canonical scope identifier used to derive cache keys.
diff --git a/synap/tests/agents/test_query_list_cache_component.py b/synap/tests/agents/test_query_list_cache_component.py
new file mode 100644
index 0000000..b3206db
--- /dev/null
+++ b/synap/tests/agents/test_query_list_cache_component.py
@@ -0,0 +1,46 @@
+"""The retrieval cache key must tell different query lists apart.
+
+``["a|b"]`` and ``["a", "b"]`` used to share one key component, so the second
+caller was served the first caller's cached results.
+"""
+
+import itertools
+
+from synap.cloud.shared.cache_keys import CacheKeyGenerator, query_list_component
+
+
+def _key(queries):
+    return CacheKeyGenerator.l1_query_key(
+        client_id="c1",
+        customer_id="cust1",
+        user_id="u1",
+        query=query_list_component(queries),
+        context_types=["facts"],
+        instance_id="inst_a",
+    )
+
+
+class TestQueryListComponent:
+    def test_pipe_inside_a_query_differs_from_two_queries(self):
+        assert query_list_component(["a|b"]) != query_list_component(["a", "b"])
+        assert _key(["a|b"]) != _key(["a", "b"])
+
+    def test_ordinary_lists_keep_the_plain_join(self):
+        assert query_list_component(["a"]) == "a"
+        assert query_list_component(["a", "b"]) == "a|b"
+
+    def test_empty_and_missing_lists_are_empty(self):
+        assert query_list_component([]) == ""
+        assert query_list_component(None) == ""
+
+    def test_a_query_that_imitates_the_encoded_form_does_not_collide(self):
+        imitation = [query_list_component(["a|b"])]
+        assert query_list_component(imitation) != query_list_component(["a|b"])
+
+    def test_no_two_small_lists_share_a_component(self):
+        atoms = ["a", "|", "a|a", "ql1:", 'ql1:["a', '"]', ""]
+        seen = {}
+        for size in (1, 2, 3):
+            for combo in itertools.product(atoms, repeat=size):
+                component = query_list_component(list(combo))
+                assert seen.setdefault(component, combo) == combo, (seen[component], combo)
`````

[Back to the shelf](README.md)
