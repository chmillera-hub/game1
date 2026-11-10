# Fix 96: SMART toolkit: voice notes in the personal-assistant blueprint ignore the configured languages

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: personal-assistant: voice notes ignore transcribe_languages
- Bug report: number 90 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/90))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/96-social-messaging-agent-runtime-toolkit-90.patch](fixes/96-social-messaging-agent-runtime-toolkit-90.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/96-social-messaging-agent-runtime-toolkit-90.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-96-social-messaging-agent-runtime-toolkit-90.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-96-social-messaging-agent-runtime-toolkit-90.html

## The bug

The personal-assistant blueprint transcribes voice notes in its own code and did not pass the configured list of languages. The transcribe_languages setting worked for the other blueprints and did nothing for personal-assistant so a short Spanish note could be transcribed as a language outside the list.

## The fix

blueprints/personal-assistant/handlers/webhook.py now passes language_options=config.transcribe_languages which is the workaround the bug report gives. tests/test_blueprint_handle_media.py gains a test that sends a voice note and checks the languages handed to the transcriber. CHANGELOG.md gains one line.

## Files changed

- CHANGELOG.md
- blueprints/personal-assistant/handlers/webhook.py
- tests/test_blueprint_handle_media.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 96-social-messaging-agent-runtime-toolkit-90.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 90.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Projects already created from the blueprint keep their own copy of the file and need the same one-line change by hand. The end of the bug report text was cut off in the search result so the chatbot read the proposed fix only in part. The chatbot did not run the project's tests. Fixes 72 and 96 and 97 and 99 on this shelf each add a line at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand. The other files in those patches do not overlap.

## Search words

socialagent personal-assistant voice note transcribe_audio language_options transcribe_languages handle_media Amazon Transcribe

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..8e2bf82 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Fixed
+- The `personal-assistant` blueprint passes `transcribe_languages` to Amazon Transcribe for voice notes, as the other blueprints already do.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/blueprints/personal-assistant/handlers/webhook.py b/blueprints/personal-assistant/handlers/webhook.py
index 4440b36..840418e 100644
--- a/blueprints/personal-assistant/handlers/webhook.py
+++ b/blueprints/personal-assistant/handlers/webhook.py
@@ -68,6 +68,7 @@ async def handle_media(message) -> str:
                 poll_interval=config.transcribe_poll_interval,
                 max_wait=config.transcribe_timeout,
                 key_prefix=config._transcription_prefix,
+                language_options=config.transcribe_languages,
             )
         except Exception as e:  # noqa: BLE001
             logger.warning("Audio transcription failed: %s", e)
diff --git a/tests/test_blueprint_handle_media.py b/tests/test_blueprint_handle_media.py
index fcb40ba..90865c7 100644
--- a/tests/test_blueprint_handle_media.py
+++ b/tests/test_blueprint_handle_media.py
@@ -314,3 +314,31 @@ async def test_a_reaction_tells_the_agent_its_emoji_and_message(webhook):
     )
     out = await mod.handle_media(reaction)
     assert out == "[User reacted \U0001f44e to message wamid.sent]"
+
+
+@pytest.mark.asyncio
+async def test_a_voice_note_is_transcribed_in_the_configured_languages(
+    webhook, monkeypatch
+):
+    """The hook called transcribe_audio without ``language_options``, so the
+    documented ``transcribe_languages`` setting did nothing for this blueprint
+    and Amazon Transcribe could pick a language outside the configured list."""
+    mod, _ = webhook
+    monkeypatch.setattr(mod.config, "_transcription_bucket", "transcripts-bucket")
+    monkeypatch.setattr(mod.config, "transcribe_languages", ("es-MX", "en-US"))
+    mod.app.provider.download_media = AsyncMock(return_value=b"ogg-bytes")
+    transcribe = AsyncMock(return_value="hola")
+    monkeypatch.setattr(mod, "transcribe_audio", transcribe)
+    note = InboundMessage(
+        id="wamid.4",
+        sender="+525555550100",
+        timestamp=MagicMock(),
+        type=MessageType.AUDIO,
+        text="",
+        media=MediaContent(id="m4", mime_type="audio/ogg"),
+    )
+
+    out = await mod.handle_media(note)
+
+    assert out == "hola"
+    assert transcribe.await_args.kwargs["language_options"] == ("es-MX", "en-US")
`````

[Back to the shelf](README.md)
