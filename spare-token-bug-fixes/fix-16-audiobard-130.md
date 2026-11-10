# Fix 16: audiobard: the Spanish title don matches inside the English contraction don't

Status: UNSENT and UNTESTED. Free to take.

- Project: oscarbol09/audiobard
- Bug report title: [BUG] Word-boundary contraction bug in VoiceMapper matches 'don' inside 'don't'
- Bug report: number 130 ([open the bug report](https://github.com/oscarbol09/audiobard/issues/130))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/16-audiobard-130.patch](fixes/16-audiobard-130.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/16-audiobard-130.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-16-audiobard-130.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-16-audiobard-130.html

## The bug

VoiceMapper guesses the gender of a neutral character from clue words in names and aliases. The male clue list holds the Spanish title don. An apostrophe counts as a word break so the clue also matches inside don't. An alias such as "The girl who don't talk" gets a male voice.

## The fix

_has_whole_word_clue in src/audiobard/tts/voice_mapper.py no longer counts a clue that is directly followed by an apostrophe and the letter t. Both the plain apostrophe and the curly apostrophe are covered. Other forms such as he's still count. New tests cover the helper and a full voice assignment. A changelog line is included. The chatbot checked the pattern with a separate script on twelve phrases.

## Files changed

- CHANGELOG.md
- src/audiobard/tts/voice_mapper.py
- tests/test_voice_mapper.py

## How to use the fix

1. Get a copy of the project oscarbol09/audiobard.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 16-audiobard-130.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 130.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 15 and fix 16 both add text at the same spot in CHANGELOG.md. Applying both needs a small manual merge of CHANGELOG.md.

## Search words

audiobard VoiceMapper gender clue don don't contraction word boundary apostrophe GenderHint MALE wrong voice

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 3ae0b55..680ac00 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -11,6 +11,9 @@ adds an entry under the relevant section, in the same commit as the change.
 
 ### Fixed
 
+- The Spanish title "don" no longer matches inside the English contraction "don't" when
+  guessing a neutral character's gender, so an alias such as "The girl who don't talk" is
+  no longer given a male voice (#130).
 - Restrict secret-scan exemptions to exact repository-relative files and explicitly listed
   directories, so similarly named files and nested copies are still scanned (#132).
 - Allow only catalog JSON files and the exact `.gitkeep` filename under `data/voices/`,
diff --git a/src/audiobard/tts/voice_mapper.py b/src/audiobard/tts/voice_mapper.py
index 44bd3c4..7697830 100644
--- a/src/audiobard/tts/voice_mapper.py
+++ b/src/audiobard/tts/voice_mapper.py
@@ -72,8 +72,15 @@ _FEMALE_GENDER_CLUES: tuple[str, ...] = (
 
 
 def _has_whole_word_clue(text: str, clues: tuple[str, ...]) -> bool:
-    """True if any clue appears as a whole word in *text* (case-insensitive)."""
-    return any(re.search(rf"\b{re.escape(w)}\b", text, flags=re.IGNORECASE) for w in clues)
+    """True if any clue appears as a whole word in *text* (case-insensitive).
+
+    An apostrophe is a non-word character, so ``\\bdon\\b`` also matches inside the
+    English contraction "don't". A clue directly followed by ``'t`` is therefore not a
+    whole word (issue #130). Other apostrophe forms such as "he's" still count.
+    """
+    return any(
+        re.search(rf"\b{re.escape(w)}\b(?!['\u2019]t)", text, flags=re.IGNORECASE) for w in clues
+    )
 
 
 # ---------------------------------------------------------------------------
diff --git a/tests/test_voice_mapper.py b/tests/test_voice_mapper.py
index b183af1..2557c6e 100644
--- a/tests/test_voice_mapper.py
+++ b/tests/test_voice_mapper.py
@@ -193,6 +193,20 @@ def test_neutral_with_whole_word_female_clue_gets_female_voice(mapper: VoiceMapp
     assert "female" in result.voice_id
 
 
+def test_contraction_dont_is_not_a_male_clue(mapper: VoiceMapper) -> None:
+    """ "don't" must not match the Spanish title "don" and flip a female alias to male."""
+    char = Character(
+        canonical_id="Character_A",
+        name="Alex",
+        aliases=["The girl who don't talk"],
+        gender_hint=GenderHint.NEUTRAL,
+        age_hint=AgeHint.ADULT,
+        tone=Tone.NEUTRAL,
+    )
+    result = mapper.assign(char)
+    assert "female" in result.voice_id
+
+
 def test_has_whole_word_clue_helper() -> None:
     from audiobard.tts.voice_mapper import _has_whole_word_clue
 
@@ -202,6 +216,13 @@ def test_has_whole_word_clue_helper() -> None:
     assert _has_whole_word_clue("he said", ("he",)) is True
     assert _has_whole_word_clue("humana", ("man",)) is False
     assert _has_whole_word_clue("Mr. Darcy", ("mr",)) is True
+    # "don" is a Spanish title, not the start of the contraction "don't" (#130).
+    assert _has_whole_word_clue("The girl who don't talk", ("don",)) is False
+    assert _has_whole_word_clue("The girl who don\u2019t talk", ("don",)) is False
+    assert _has_whole_word_clue("DON'T ASK", ("don",)) is False
+    assert _has_whole_word_clue("Don Quixote", ("don",)) is True
+    assert _has_whole_word_clue("the don", ("don",)) is True
+    assert _has_whole_word_clue("he's late", ("he",)) is True
 
 
 # ---------------------------------------------------------------------------
`````

[Back to the shelf](README.md)
