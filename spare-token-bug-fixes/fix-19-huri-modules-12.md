# Fix 19: huri-modules: RemoteEmbedder ignores --no-verify-ssl and never verifies TLS

Status: UNSENT and UNTESTED. Free to take.

- Project: Lucy-Robotics/huri-modules
- Bug report title: RemoteEmbedder ignores --no-verify-ssl and never verifies TLS
- Bug report: number 12 ([open the bug report](https://github.com/Lucy-Robotics/huri-modules/issues/12))
- Project license: GPL-3.0
- Language: Python
- Test included: yes
- Patch file: [fixes/19-huri-modules-12.patch](fixes/19-huri-modules-12.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/19-huri-modules-12.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-19-huri-modules-12.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-19-huri-modules-12.html

## The bug

python -m huri_rag.ingestion has a --no-verify-ssl flag. The flag is honoured for Qdrant. RemoteEmbedder always builds its HTTP client with verify=False so an HTTPS embeddings endpoint is never verified. bandit reports the line as B501.

## The fix

RemoteEmbedder.__init__ in packages/huri-module-rag/huri_rag/ingestion.py gains a verify_ssl parameter that defaults to True and passes the value to httpx.Client. The script passes its verify_ssl value when building the embedder. A new test file checks that both values reach the client with no network use. The package version goes from 0.1.0 to 0.1.1 and the two matching pins in meta/pyproject.toml follow.

## Files changed

- meta/pyproject.toml
- packages/huri-module-rag/huri_rag/ingestion.py
- packages/huri-module-rag/pyproject.toml
- packages/huri-module-rag/tests/test_ingestion.py

## How to use the fix

1. Get a copy of the project Lucy-Robotics/huri-modules.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 19-huri-modules-12.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 12.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The default behaviour changes: TLS is verified unless --no-verify-ssl is passed. The new test is skipped when the rag extra is not installed.

## Search words

huri-modules huri_rag ingestion RemoteEmbedder httpx.Client verify=False --no-verify-ssl TLS certificate verification bandit B501

## The full patch

`````diff
diff --git a/meta/pyproject.toml b/meta/pyproject.toml
index c652c5b..8ab197d 100644
--- a/meta/pyproject.toml
+++ b/meta/pyproject.toml
@@ -24,8 +24,8 @@ stt = ["huri-module-stt==0.1.0"]
 tag = ["huri-module-tag==0.1.0"]
 emo = ["huri-module-emo[model]==0.1.0"]
 eag = ["huri-module-emo==0.1.0"]
-rag = ["huri-module-rag[rag]==0.1.0"]
-qag = ["huri-module-rag==0.1.0"]
+rag = ["huri-module-rag[rag]==0.1.1"]
+qag = ["huri-module-rag==0.1.1"]
 tts = ["huri-module-tts[piper]==0.1.0"]
 # The module only: CosyVoice itself is not pip-installable (install.sh adds it).
 tts-cosyvoice = ["huri-module-tts[cosyvoice]==0.1.0"]
diff --git a/packages/huri-module-rag/huri_rag/ingestion.py b/packages/huri-module-rag/huri_rag/ingestion.py
index d02ceb2..0a9699a 100644
--- a/packages/huri-module-rag/huri_rag/ingestion.py
+++ b/packages/huri-module-rag/huri_rag/ingestion.py
@@ -33,10 +33,12 @@ class RemoteEmbedder:
     the existing ``.tolist()`` / ``len(...)`` call sites keep working unchanged.
     """
 
-    def __init__(self, url: str, model_name: str):
+    def __init__(self, url: str, model_name: str, verify_ssl: bool = True):
         self.url = url.rstrip("/")
         self.model_name = model_name
-        self._client = httpx.Client(timeout=60.0, verify=False)
+        # TLS is verified unless the caller opts out (``--no-verify-ssl``, for
+        # self-signed LAN certificates), the same as the Qdrant client.
+        self._client = httpx.Client(timeout=60.0, verify=verify_ssl)
 
     def encode(self, text: str, normalize_embeddings: bool = True) -> np.ndarray:
         resp = self._client.post(
@@ -535,7 +537,9 @@ def main():
                 f"Embedding remotely via {args.embedding_url} "
                 f"(model={args.embedding_model})"
             )
-            model = RemoteEmbedder(args.embedding_url, args.embedding_model)
+            model = RemoteEmbedder(
+                args.embedding_url, args.embedding_model, verify_ssl=verify_ssl
+            )
         else:
             from sentence_transformers import SentenceTransformer
 
diff --git a/packages/huri-module-rag/pyproject.toml b/packages/huri-module-rag/pyproject.toml
index 61fa29c..06e834f 100644
--- a/packages/huri-module-rag/pyproject.toml
+++ b/packages/huri-module-rag/pyproject.toml
@@ -4,7 +4,7 @@ build-backend = "setuptools.build_meta"
 
 [project]
 name = "huri-module-rag"
-version = "0.1.0"
+version = "0.1.1"
 description = "HuRI module: Retrieval-augmented answers with long-term memory (Qdrant + an OpenAI-compatible LLM), and the question aggregator"
 readme = "README.md"
 requires-python = ">=3.10"
diff --git a/packages/huri-module-rag/tests/test_ingestion.py b/packages/huri-module-rag/tests/test_ingestion.py
new file mode 100644
index 0000000..f603545
--- /dev/null
+++ b/packages/huri-module-rag/tests/test_ingestion.py
@@ -0,0 +1,40 @@
+"""The ingestion tool's remote embedder: TLS verification follows the caller."""
+
+import pytest
+
+# huri_rag.ingestion needs the `rag` extra (httpx, qdrant-client, numpy).
+pytest.importorskip("httpx")
+pytest.importorskip("qdrant_client")
+pytest.importorskip("numpy")
+
+from huri_rag import ingestion  # noqa: E402
+
+
+class _RecordingClient:
+    """Stands in for httpx.Client: records how it was built, opens no socket."""
+
+    calls: list[dict] = []
+
+    def __init__(self, **kwargs):
+        type(self).calls.append(kwargs)
+
+
+@pytest.fixture
+def client_calls(monkeypatch):
+    _RecordingClient.calls = []
+    monkeypatch.setattr(ingestion.httpx, "Client", _RecordingClient)
+    return _RecordingClient.calls
+
+
+def test_remote_embedder_verifies_tls_by_default(client_calls):
+    ingestion.RemoteEmbedder("https://embeddings.example/", "some-model")
+    assert [call["verify"] for call in client_calls] == [True]
+
+
+@pytest.mark.parametrize("verify_ssl", [True, False])
+def test_remote_embedder_passes_verify_ssl_to_the_client(client_calls, verify_ssl):
+    embedder = ingestion.RemoteEmbedder(
+        "https://embeddings.example/", "some-model", verify_ssl=verify_ssl
+    )
+    assert [call["verify"] for call in client_calls] == [verify_ssl]
+    assert embedder.url == "https://embeddings.example"
`````

[Back to the shelf](README.md)
