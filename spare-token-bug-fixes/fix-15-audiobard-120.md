# Fix 15: audiobard: export_m4b crashes when the destination folder does not exist

Status: UNSENT and UNTESTED. Free to take.

- Project: oscarbol09/audiobard
- Bug report title: [BUG] AudioProcessor.export_m4b crashes if destination parent directory does not exist
- Bug report: number 120 ([open the bug report](https://github.com/oscarbol09/audiobard/issues/120))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/15-audiobard-120.patch](fixes/15-audiobard-120.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/15-audiobard-120.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-15-audiobard-120.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-15-audiobard-120.html

## The bug

Running audiobard generate book.txt -o ./new_folder/book.m4b fails with the FFmpeg error "new_folder/book.m4b: No such file or directory". The MP3 export path creates missing folders and the M4B export path does not.

## The fix

export_m4b in src/audiobard/audio/processor.py now creates the destination folder before calling FFmpeg. A new test exports into a nested folder that does not exist yet. A changelog line is included.

## Files changed

- CHANGELOG.md
- src/audiobard/audio/processor.py
- tests/test_audio.py

## How to use the fix

1. Get a copy of the project oscarbol09/audiobard.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 15-audiobard-120.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 120.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 15 and fix 16 both add text at the same spot in CHANGELOG.md. Applying both needs a small manual merge of CHANGELOG.md.

## Search words

audiobard export_m4b ffmpeg No such file or directory output folder missing parent directory mkdir m4b

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 3ae0b55..e2e3e4d 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -11,6 +11,9 @@ adds an entry under the relevant section, in the same commit as the change.
 
 ### Fixed
 
+- `export_m4b` creates the destination folder when it does not exist, so
+  `audiobard generate book.txt -o ./new_folder/book.m4b` no longer fails with FFmpeg's
+  "No such file or directory" (#120).
 - Restrict secret-scan exemptions to exact repository-relative files and explicitly listed
   directories, so similarly named files and nested copies are still scanned (#132).
 - Allow only catalog JSON files and the exact `.gitkeep` filename under `data/voices/`,
diff --git a/src/audiobard/audio/processor.py b/src/audiobard/audio/processor.py
index bbc6666..3c4c857 100644
--- a/src/audiobard/audio/processor.py
+++ b/src/audiobard/audio/processor.py
@@ -542,6 +542,10 @@ class AudioProcessor:
         if not ffmpeg_bin:
             raise FileNotFoundError(FFMPEG_MISSING_MESSAGE)
 
+        # FFmpeg does not create missing folders: without this, ``-o new_folder/book.m4b``
+        # fails with "No such file or directory" (the MP3 path already does the same).
+        path.parent.mkdir(parents=True, exist_ok=True)
+
         with tempfile.TemporaryDirectory() as tmpdir:
             tmp_path = Path(tmpdir)
             raw_m4b = tmp_path / "raw.m4b"
diff --git a/tests/test_audio.py b/tests/test_audio.py
index daf7236..5c92b8d 100644
--- a/tests/test_audio.py
+++ b/tests/test_audio.py
@@ -250,6 +250,37 @@ async def test_audio_processor_export_m4b(mock_subproc: AsyncMock, mock_find: An
         assert "copy" in call2_args
 
 
+@pytest.mark.asyncio
+@patch("audiobard.audio.processor.find_ffmpeg", return_value="/usr/bin/ffmpeg")
+@patch("asyncio.create_subprocess_exec")
+async def test_audio_processor_export_m4b_creates_missing_parent_dirs(
+    mock_subproc: AsyncMock, mock_find: Any
+) -> None:
+    """export_m4b must create the destination folder: FFmpeg will not."""
+    mock_proc1 = AsyncMock()
+    mock_proc1.returncode = 0
+    mock_proc1.communicate.return_value = (b"", b"")
+
+    mock_proc2 = AsyncMock()
+    mock_proc2.returncode = 0
+    mock_proc2.communicate.return_value = (b"", b"")
+
+    mock_subproc.side_effect = [mock_proc1, mock_proc2]
+
+    processor = AudioProcessor()
+    chapters = [ChapterMarker(title="Ch 1", start_ms=0, end_ms=5000)]
+
+    with tempfile.TemporaryDirectory() as tmpdir:
+        out_path = Path(tmpdir) / "new_folder" / "nested" / "book.m4b"
+        assert not out_path.parent.exists()
+
+        await processor.export_m4b(b"audio-data", out_path, chapters)
+
+        assert out_path.parent.is_dir()
+        # The folder exists before FFmpeg is asked to write into it.
+        assert mock_subproc.call_args_list[1][0][-1] == str(out_path)
+
+
 # 64x64 JPEG generated with ffmpeg; used to prove cover art is really attached.
 _DUMMY_COVER_JPEG = base64.b64decode(
     "/9j/4AAQSkZJRgABAgAAAQABAAD//gAQTGF2YzYyLjE1LjEwMAD/2wBDAAgEBAQEBAUFBQUFBQYGBgYGBgYG"
`````

[Back to the shelf](README.md)
