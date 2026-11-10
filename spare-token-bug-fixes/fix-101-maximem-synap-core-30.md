# Fix 101: maximem_synap_core: a fully downloaded leftover .part file makes the first start fail on every boot

Status: UNSENT and UNTESTED. Free to take.

- Project: maximem-ai/maximem_synap_core
- Bug report title: A complete leftover `.part` file makes first start fail on every boot
- Bug report: number 30 ([open the bug report](https://github.com/maximem-ai/maximem_synap_core/issues/30))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/101-maximem-synap-core-30.patch](fixes/101-maximem-synap-core-30.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/101-maximem-synap-core-30.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-101-maximem-synap-core-30.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-101-maximem-synap-core-30.html

## The bug

When the first-start download stopped after the last byte and before the file was renamed a complete file named .part stayed on disk. Every later start asked the server for the bytes after the end. A server that answers 416 made all eight attempts fail and the stack never became ready until a person deleted the file by hand.

## The fix

_fetch in synap/boot/first_start.py now handles the 416 answer when a part exists. When the size the server reports equals the size of the part (or the server reports no size) the part is renamed to the final name and the existing hash check judges the file. A part of any other size is deleted and the download starts from zero. A new file synap/tests/boot/test_first_start_complete_part.py covers both cases with a strict test server.

## Files changed

- synap/boot/first_start.py
- synap/tests/boot/test_first_start_complete_part.py

## How to use the fix

1. Get a copy of the project maximem-ai/maximem_synap_core.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 101-maximem-synap-core-30.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 30.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- When the server reports no size the fix trusts the part and relies on the hash check that both callers already run after the download. The chatbot confirmed in a scratch script how Python reports a 416 answer and its Content-Range header. The chatbot did not run the project's code or tests. Fixes 70 and 87 and 88 on this shelf are for the same project and all four patches apply one after another.

## Search words

maximem synap first_start _fetch .part leftover Range 416 HTTPError ATTEMPTS FirstStartError resume download

## The full patch

`````diff
diff --git a/synap/boot/first_start.py b/synap/boot/first_start.py
index 8d9f8f0..51d9331 100644
--- a/synap/boot/first_start.py
+++ b/synap/boot/first_start.py
@@ -112,6 +112,14 @@ def _size(n: float) -> str:
     return f"{n / 1e9:.2f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB"
 
 
+def _range_total(content_range: str | None) -> int | None:
+    """The file size from a ``Content-Range: bytes */SIZE`` header, or None when it is not given."""
+    if not content_range:
+        return None
+    total = content_range.rpartition("/")[2].strip()
+    return int(total) if total.isdigit() else None
+
+
 def _fetch(url: str, dest: Path, *, attempts: int = ATTEMPTS, log=print) -> None:
     """Download to ``dest.part`` and resume it if a run was cut off.
 
@@ -160,6 +168,21 @@ def _fetch(url: str, dest: Path, *, attempts: int = ATTEMPTS, log=print) -> None
             part.replace(dest)
             return
         except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
+            if isinstance(e, urllib.error.HTTPError) and e.code == 416 and have:
+                # 416: the server has nothing after byte ``have``. That is what a run cut off after
+                # the last byte and before the rename leaves behind, and every later start asked
+                # for the same empty range and failed. If the server's size is the part's size (or
+                # it does not say), the part is the whole file: finish the rename and let the
+                # caller's hash check judge it. A part of any other size cannot be resumed, so it
+                # is dropped and the next attempt starts from zero.
+                size = _range_total(e.headers.get("Content-Range") if e.headers else None)
+                if size is None or size == have:
+                    part.replace(dest)
+                    return
+                part.unlink(missing_ok=True)
+                last = e
+                log(f"first-start: {dest.name}: the part on disk does not match the file; starting over")
+                continue
             last = e
             log(f"first-start: {dest.name}: attempt {n} of {attempts} failed ({type(e).__name__}: {e})")
             if (part.stat().st_size if part.exists() else 0) > have:
diff --git a/synap/tests/boot/test_first_start_complete_part.py b/synap/tests/boot/test_first_start_complete_part.py
new file mode 100644
index 0000000..cb1b198
--- /dev/null
+++ b/synap/tests/boot/test_first_start_complete_part.py
@@ -0,0 +1,84 @@
+"""A complete leftover ``.part`` file must not make every later start fail.
+
+A run that dies after the last byte and before the rename leaves a whole file named ``.part``.
+The next start asks for ``Range: bytes=<size>-`` and a server that answers 416 used to fail all
+eight attempts on every boot, until someone deleted the file by hand.
+"""
+from __future__ import annotations
+
+import re
+import threading
+from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
+
+import pytest
+
+from synap.boot import first_start as fs
+
+BODY = b"B" * 200_000
+
+
+def _serve(seen: list, *, content_range: bool = True) -> ThreadingHTTPServer:
+    """A server that answers an empty or out-of-range ``Range`` with 416, as a CDN does."""
+
+    class Strict(BaseHTTPRequestHandler):
+        def log_message(self, *a):  # quiet
+            pass
+
+        def do_GET(self):
+            rng = self.headers.get("Range")
+            start = int(re.match(r"bytes=(\d+)-", rng).group(1)) if rng else 0
+            seen.append(start)
+            if start >= len(BODY):
+                self.send_response(416)
+                if content_range:
+                    self.send_header("Content-Range", f"bytes */{len(BODY)}")
+                self.send_header("Content-Length", "0")
+                self.end_headers()
+                return
+            self.send_response(206 if start else 200)
+            self.send_header("Content-Length", str(len(BODY) - start))
+            self.end_headers()
+            self.wfile.write(BODY[start:])
+
+    server = ThreadingHTTPServer(("127.0.0.1", 0), Strict)
+    threading.Thread(target=server.serve_forever, daemon=True).start()
+    return server
+
+
+@pytest.mark.parametrize("content_range", [True, False])
+def test_a_complete_leftover_part_is_finished_not_refused(tmp_path, monkeypatch, content_range):
+    monkeypatch.setattr(fs.time, "sleep", lambda s: None)
+    seen: list = []
+    dest = tmp_path / "f.bin"
+    (tmp_path / "f.bin.part").write_bytes(BODY)
+    server = _serve(seen, content_range=content_range)
+    try:
+        fs._fetch(f"http://127.0.0.1:{server.server_port}/f", dest, log=lambda *_: None)
+    finally:
+        server.shutdown()
+    assert dest.read_bytes() == BODY
+    assert not (tmp_path / "f.bin.part").exists()
+    assert seen == [len(BODY)]
+
+
+def test_a_part_longer_than_the_file_is_dropped_and_downloaded_again(tmp_path, monkeypatch):
+    monkeypatch.setattr(fs.time, "sleep", lambda s: None)
+    seen: list = []
+    lines: list = []
+    dest = tmp_path / "f.bin"
+    (tmp_path / "f.bin.part").write_bytes(b"X" * (len(BODY) + 10))
+    server = _serve(seen)
+    try:
+        fs._fetch(f"http://127.0.0.1:{server.server_port}/f", dest, log=lines.append)
+    finally:
+        server.shutdown()
+    assert dest.read_bytes() == BODY
+    assert seen == [len(BODY) + 10, 0]
+    assert any("starting over" in ln for ln in lines)
+
+
+def test_range_total_reads_the_size_or_gives_none():
+    assert fs._range_total("bytes */200000") == 200_000
+    assert fs._range_total("bytes */*") is None
+    assert fs._range_total("") is None
+    assert fs._range_total(None) is None
`````

[Back to the shelf](README.md)
