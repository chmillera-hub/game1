# Fix 106: vynlore: the artist page crashes to a white screen when the artist has no tracks left

Status: UNSENT and UNTESTED. Free to take.

- Project: dhanushbs10/vynlore
- Bug report title: Artist detail view crashes when the artist has no tracks
- Bug report: number 14 ([open the bug report](https://github.com/dhanushbs10/vynlore/issues/14))
- Project license: MIT
- Language: TypeScript (React)
- Test included: no
- Patch file: [fixes/106-vynlore-14.patch](fixes/106-vynlore-14.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/106-vynlore-14.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-106-vynlore-14.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-106-vynlore-14.html

## The bug

The artist detail view read the cover of the artist's first track before checking that any track exists. When a rescan removed the last track of the open artist the view crashed and the screen went white.

## The fix

src/components/views/ArtistDetailView.tsx now checks that a first track exists before reading its cover. With no tracks the view shows the artist name and a back button and one line of text. CHANGELOG.md gains one line under Unreleased.

## Files changed

- CHANGELOG.md
- src/components/views/ArtistDetailView.tsx

## How to use the fix

1. Get a copy of the project dhanushbs10/vynlore.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 106-vynlore-14.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 14.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The wording of the empty state is the chatbot's choice. The project has no test setup so the patch adds no test. The chatbot did not run the app or the TypeScript compiler. Fix 105 on this shelf adds a changelog line at the same spot so the two patches do not apply together: add the other changelog line by hand.

## Search words

vynlore ArtistDetailView hasCover artistTracks[0] undefined cover_path crash white screen empty artist rescan

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 71dc17d..64667ed 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -2,6 +2,10 @@
 
 ## Unreleased
 
+### Bug fixes
+
+- The artist detail view no longer crashes when a rescan removes the last track of the open artist. The view shows an empty state with a back button.
+
 ### Documentation and contributor infrastructure
 
 - Rewrote the README with accurate UI limits, project status, supported formats and contributor links.
diff --git a/src/components/views/ArtistDetailView.tsx b/src/components/views/ArtistDetailView.tsx
index f29c28e..fc1262f 100644
--- a/src/components/views/ArtistDetailView.tsx
+++ b/src/components/views/ArtistDetailView.tsx
@@ -38,8 +38,9 @@ export function ArtistDetailView({ artist, tracks, onBack, playTrack }: ArtistDe
     return Array.from(map.entries()).map(([album, tracks]) => ({ album, tracks }));
   }, [artistTracks]);
 
-  const coverSrc = hasCover(artistTracks[0])
-    ? convertFileSrc(artistTracks[0].cover_path!)
+  const firstTrack = artistTracks[0];
+  const coverSrc = firstTrack && hasCover(firstTrack)
+    ? convertFileSrc(firstTrack.cover_path!)
     : undefined;
 
   const totalDuration = artistTracks.reduce((acc, t) => acc + t.duration_secs, 0);
@@ -59,6 +60,22 @@ export function ArtistDetailView({ artist, tracks, onBack, playTrack }: ArtistDe
     await playTrack(shuffled[0], shuffled);
   }, [artistTracks, isShuffle, toggleShuffle, playTrack]);
 
+  // A rescan or a watcher removal can delete this artist's last track while the
+  // view is still mounted. Show an empty state instead of reading a missing track.
+  if (artistTracks.length === 0) {
+    return (
+      <div>
+        <div className="flex items-center gap-4 mb-7">
+          <button onClick={onBack} className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text transition-colors" aria-label="Back to artists">
+            <ArrowLeft size={18} />
+          </button>
+          <h1 className="font-display text-2xl font-bold text-text tracking-tight">{artist}</h1>
+        </div>
+        <p className="text-sm text-text-secondary">No tracks by this artist are in the library any more.</p>
+      </div>
+    );
+  }
+
   return (
     <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
       <div className="flex items-center gap-4 mb-7">
`````

[Back to the shelf](README.md)
