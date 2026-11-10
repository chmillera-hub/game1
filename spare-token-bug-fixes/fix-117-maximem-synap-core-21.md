# Fix 117: maximem_synap_core: the document id returned to the caller differs from the id stored on the memories

Status: UNSENT and UNTESTED. Free to take.

- Project: maximem-ai/maximem_synap_core
- Bug report title: Returned `document_id` does not match the one stored on the memories
- Bug report: number 21 ([open the bug report](https://github.com/maximem-ai/maximem_synap_core/issues/21))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/117-maximem-synap-core-21.patch](fixes/117-maximem-synap-core-21.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/117-maximem-synap-core-21.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-117-maximem-synap-core-21.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-117-maximem-synap-core-21.html

## The bug

When a memory was created without a document id the service made up an id and returned the id in the response. The request that went into the queue did not carry that id so the workers used the ingestion id instead. Callers could not link the stored memories to the document they had sent.

## The fix

ingest_document in synap/cloud/application/ingestion/manager.py now writes the generated id onto the request before the request is queued. The path for split documents already did the same. synap/tests/application/ingestion/test_manager.py gains a test that the queued request carries the returned id and a test that a supplied id is kept.

## Files changed

- synap/cloud/application/ingestion/manager.py
- synap/tests/application/ingestion/test_manager.py

## How to use the fix

1. Get a copy of the project maximem-ai/maximem_synap_core.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 117-maximem-synap-core-21.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 21.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The request object passed in by the caller is changed in place (its document_id is filled in). The chatbot confirmed by reading that the duplicate check hashes only the content so the new field value does not change that check. The chatbot did not run the project's tests or the pipeline. Fixes 70 and 87 and 88 and 101 on this shelf are for the same project and all five patches apply one after another.

## Search words

maximem synap ingest_document document_id source_document_id ingestion id mismatch queue request stage4_worker

## The full patch

`````diff
diff --git a/synap/cloud/application/ingestion/manager.py b/synap/cloud/application/ingestion/manager.py
index df2bc9b..c82cd42 100644
--- a/synap/cloud/application/ingestion/manager.py
+++ b/synap/cloud/application/ingestion/manager.py
@@ -471,6 +471,10 @@ class IngestionManager:
             # Generate IDs
             ingestion_id = uuid4()
             document_id = request.document_id or str(uuid4())
+            # The queued request must carry the id returned to the caller. Without
+            # it the workers fell back to the ingestion id, so the stored memories
+            # carried a different source_document_id than the response.
+            request.document_id = document_id
             set_current_span_attributes({"synap.ingestion_id": str(ingestion_id)})
             logger.info(
                 "ingestion_ids_allocated request_id=%s ingestion_id=%s document_id=%s",
diff --git a/synap/tests/application/ingestion/test_manager.py b/synap/tests/application/ingestion/test_manager.py
index f411520..17e2c2e 100644
--- a/synap/tests/application/ingestion/test_manager.py
+++ b/synap/tests/application/ingestion/test_manager.py
@@ -96,6 +96,39 @@ class TestIngestionManager:
         assert response.ingestion_id is not None
         assert response.document_id is not None
 
+    @pytest.mark.asyncio
+    async def test_generated_document_id_is_on_the_queued_request(self, manager, doc_request):
+        """The id returned to the caller is the id the workers stamp on the memories.
+
+        The manager generated a document_id for the response and queued the
+        request without it, so the workers fell back to the ingestion id and
+        callers could not link memories to the document they sent.
+        """
+        assert doc_request.document_id is None
+        queued = {}
+        real_enqueue = manager._queue.enqueue
+
+        async def spy(*, ingestion_id, request, priority):
+            queued["document_id"] = request.document_id
+            return await real_enqueue(ingestion_id=ingestion_id, request=request, priority=priority)
+
+        manager._queue.enqueue = spy
+
+        response = await manager.ingest_document(doc_request)
+
+        assert response.document_id
+        assert queued["document_id"] == response.document_id
+
+    @pytest.mark.asyncio
+    async def test_supplied_document_id_is_kept(self, manager, scope):
+        """A document_id the caller supplies is returned and queued unchanged."""
+        request = IngestDocumentRequest(content="Test content", scope=scope, document_id="doc-123")
+
+        response = await manager.ingest_document(request)
+
+        assert response.document_id == "doc-123"
+        assert request.document_id == "doc-123"
+
     @pytest.mark.asyncio
     async def test_ingest_document_validates_request(self, manager, scope):
         """Test ingestion validates request."""
`````

[Back to the shelf](README.md)
