# Fix 140: codelens-graph: an unused FileWatcher class still sits in the code with its own tests

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Remove the unused FileWatcher class
- Bug report: number 49 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/49))
- Project license: MIT
- Language: TypeScript
- Test included: no
- Patch file: [fixes/140-codelens-graph-49.patch](fixes/140-codelens-graph-49.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/140-codelens-graph-49.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-140-codelens-graph-49.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-140-codelens-graph-49.html

## The bug

src/ingestion/fileWatcher.ts is imported nowhere because the extension uses VS Code's own file watchers. The class still had a test file. A contributor could mistake the class for the real watcher.

## The fix

The patch deletes src/ingestion/fileWatcher.ts and test/ingestion/fileWatcher.test.ts and removes the file from the folder listing in README.md. changelog.md gains one line.

## Files changed

- README.md
- changelog.md
- src/ingestion/fileWatcher.ts
- test/ingestion/fileWatcher.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 140-codelens-graph-49.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 49.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report says to comment on the report before starting and has one comment the chatbot could not read: someone may already be working on the report. A search of the project found no other use of the class. The chatbot did not run the tests or the TypeScript compiler. Fixes 138 and 139 and 140 on this shelf apply one after another.

## Search words

codelens-graph FileWatcher fileWatcher.ts unused dead code remove ingestion test

## The full patch

`````diff
diff --git a/README.md b/README.md
index 7871025..8c89814 100644
--- a/README.md
+++ b/README.md
@@ -147,8 +147,7 @@ src/
 │   ├── astParser.ts          # tree-sitter WASM parser (regex fallback)
 │   ├── workspaceScanner.ts   # Walks the selected folders, reconciles the graph with them
 │   ├── indexScope.ts         # Folder selection (codeLensGraph.includeFolders) rules
-│   ├── dependencyManifest.ts # Direct dependencies from package.json (no node_modules walk)
-│   └── fileWatcher.ts        # Standalone file watcher (outside VS Code)
+│   └── dependencyManifest.ts # Direct dependencies from package.json (no node_modules walk)
 ├── graph/
 │   ├── graphDB.ts            # SQLite graph store (integer-keyed), relationship resolution
 │   └── differ.ts             # Pre/post agent run diff engine
diff --git a/changelog.md b/changelog.md
index 2986438..ccbd2a2 100644
--- a/changelog.md
+++ b/changelog.md
@@ -26,6 +26,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 ### Changed
 - **Agent MCP configs keep working across extension updates.** Configs ran the server from the versioned install folder (`…/pranaydas.codelens-graph-<version>/dist/mcp.js`), which the next update deletes, so agents configured outside the workspace (`~/.claude.json`, `~/.cursor/mcp.json`, Windsurf) silently lost CodeLens after every update. Generated configs now run a stable launcher, `~/.codelens/mcp.js`, that starts the newest CodeLens version installed in any editor (VS Code, Insiders, Cursor, Windsurf, Antigravity, …). On startup, existing configs that point at a versioned folder are switched to the launcher automatically; only that path changes, and configs pointing anywhere else (e.g. a development build) are left alone.
 - **Existing indexes are re-parsed once after an update that changes parsing**, so fixes like the ones above apply to files that haven't changed since they were indexed. Previously those kept their old results until edited or rebuilt with **CodeLens: Force Rebuild Graph**.
+- Removed the unused standalone `FileWatcher` class (`src/ingestion/fileWatcher.ts`). The extension has always used VS Code's own file watchers, so nothing changes for users.
 
 ---
 
diff --git a/src/ingestion/fileWatcher.ts b/src/ingestion/fileWatcher.ts
deleted file mode 100644
index 9423726..0000000
--- a/src/ingestion/fileWatcher.ts
+++ /dev/null
@@ -1,99 +0,0 @@
-import * as fs from 'fs';
-import { WorkspaceScanner } from './workspaceScanner';
-
-type ChangeCallback = (filePath: string, changeType: 'change' | 'add' | 'unlink') => void;
-
-// ─── FileWatcher ───────────────────────────────────────────────────────────────
-// Watches the workspace for file changes and triggers incremental graph updates.
-// In a VS Code extension, this wraps vscode.workspace.createFileSystemWatcher.
-// This standalone version uses fs.watch for testability outside VS Code.
-
-export class FileWatcher {
-  private callbacks: ChangeCallback[] = [];
-  private watchers: fs.FSWatcher[] = [];
-  private debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();
-  private readonly DEBOUNCE_MS = 500; // Wait 500ms after last change before processing
-
-  constructor(private scanner: WorkspaceScanner) {}
-
-  // Register a callback for file change events
-  onChange(cb: ChangeCallback): void {
-    this.callbacks.push(cb);
-  }
-
-  // Start watching a set of root directories
-  watchRoots(roots: string[], supportedExtensions: string[]): void {
-    const extSet = new Set(supportedExtensions.map(e => e.toLowerCase()));
-
-    for (const root of roots) {
-      try {
-        const watcher = fs.watch(root, { recursive: true }, (eventType, filename) => {
-          if (!filename) { return; }
-
-          const fullPath = require('path').join(root, filename);
-          const ext = require('path').extname(filename).toLowerCase();
-          if (!extSet.has(ext)) { return; }
-
-          // Debounce rapid saves
-          this.debounce(fullPath, () => {
-            const exists = fs.existsSync(fullPath);
-            const changeType = exists
-              ? (eventType === 'rename' ? 'add' : 'change')
-              : 'unlink';
-            this.emit(fullPath, changeType);
-          });
-        });
-
-        this.watchers.push(watcher);
-      } catch (err) {
-        console.warn(`[CodeLens] Could not watch ${root}: ${err}`);
-      }
-    }
-  }
-
-  // Handle a specific file change (called from VS Code's FileSystemWatcher)
-  async handleFileChange(filePath: string): Promise<void> {
-    try {
-      await this.scanner.updateFile(filePath);
-      this.emit(filePath, 'change');
-    } catch (err) {
-      console.error(`[CodeLens] Error updating file ${filePath}: ${err}`);
-    }
-  }
-
-  async handleFileCreate(filePath: string): Promise<void> {
-    try {
-      await this.scanner.updateFile(filePath);
-      this.emit(filePath, 'add');
-    } catch (err) {
-      console.error(`[CodeLens] Error adding file ${filePath}: ${err}`);
-    }
-  }
-
-  handleFileDelete(filePath: string): void {
-    // GraphDB cascades deletes via FK when nodes are removed by file path
-    this.emit(filePath, 'unlink');
-  }
-
-  // Stop all watchers
-  dispose(): void {
-    for (const w of this.watchers) { w.close(); }
-    this.watchers = [];
-    this.callbacks = [];
-    for (const t of this.debounceTimers.values()) { clearTimeout(t); }
-    this.debounceTimers.clear();
-  }
-
-  private emit(filePath: string, changeType: 'change' | 'add' | 'unlink'): void {
-    for (const cb of this.callbacks) { cb(filePath, changeType); }
-  }
-
-  private debounce(key: string, fn: () => void): void {
-    const existing = this.debounceTimers.get(key);
-    if (existing) { clearTimeout(existing); }
-    this.debounceTimers.set(key, setTimeout(() => {
-      this.debounceTimers.delete(key);
-      fn();
-    }, this.DEBOUNCE_MS));
-  }
-}
diff --git a/test/ingestion/fileWatcher.test.ts b/test/ingestion/fileWatcher.test.ts
deleted file mode 100644
index e1c2f25..0000000
--- a/test/ingestion/fileWatcher.test.ts
+++ /dev/null
@@ -1,184 +0,0 @@
-import { describe, it, before, after, beforeEach, afterEach, mock } from 'node:test';
-import assert from 'node:assert/strict';
-import * as fs from 'node:fs';
-import * as path from 'node:path';
-import { FileWatcher } from '../../src/ingestion/fileWatcher';
-import { WorkspaceScanner } from '../../src/ingestion/workspaceScanner';
-import { TempDir } from './tmp';
-import { newWorkspace } from './workspace';
-
-type Event = { file: string; type: 'change' | 'add' | 'unlink' };
-
-const DEBOUNCE_MS = 500;
-const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
-
-// Records events and lets a test await the first one matching a predicate.
-function recorder(watcher: FileWatcher) {
-  const events: Event[] = [];
-  const waiters: Array<{ match: (e: Event) => boolean; resolve: (e: Event) => void }> = [];
-  watcher.onChange((file, type) => {
-    const e = { file, type };
-    events.push(e);
-    for (const w of [...waiters]) {
-      if (w.match(e)) { waiters.splice(waiters.indexOf(w), 1); w.resolve(e); }
-    }
-  });
-  const next = (match: (e: Event) => boolean, timeoutMs = 5000) => {
-    const seen = events.find(match);
-    if (seen) { return Promise.resolve(seen); }
-    return new Promise<Event>((resolve, reject) => {
-      const timer = setTimeout(() => reject(new Error('timed out waiting for a watcher event')), timeoutMs);
-      waiters.push({ match, resolve: e => { clearTimeout(timer); resolve(e); } });
-    });
-  };
-  return { events, next };
-}
-
-function fakeScanner(updateFile: (filePath: string) => Promise<unknown>) {
-  return { updateFile } as unknown as WorkspaceScanner;
-}
-
-describe('FileWatcher: VS Code event handlers', () => {
-  let errorSpy: ReturnType<typeof mock.method>;
-  beforeEach(() => { errorSpy = mock.method(console, 'error', () => {}); });
-  afterEach(() => errorSpy.mock.restore());
-
-  it('handleFileChange updates the file, then notifies every listener with "change"', async () => {
-    const updated: string[] = [];
-    const watcher = new FileWatcher(fakeScanner(async f => { updated.push(f); }));
-    const a: Event[] = [];
-    const b: Event[] = [];
-    watcher.onChange((file, type) => a.push({ file, type }));
-    watcher.onChange((file, type) => b.push({ file, type }));
-
-    await watcher.handleFileChange('/w/x.ts');
-    assert.deepEqual(updated, ['/w/x.ts']);
-    assert.deepEqual(a, [{ file: '/w/x.ts', type: 'change' }]);
-    assert.deepEqual(b, a);
-  });
-
-  it('handleFileCreate updates the file and notifies with "add"', async () => {
-    const updated: string[] = [];
-    const watcher = new FileWatcher(fakeScanner(async f => { updated.push(f); }));
-    const { events } = recorder(watcher);
-    await watcher.handleFileCreate('/w/new.ts');
-    assert.deepEqual(updated, ['/w/new.ts']);
-    assert.deepEqual(events, [{ file: '/w/new.ts', type: 'add' }]);
-  });
-
-  it('handleFileDelete notifies with "unlink" without touching the scanner', () => {
-    const watcher = new FileWatcher(fakeScanner(async () => { throw new Error('must not be called'); }));
-    const { events } = recorder(watcher);
-    watcher.handleFileDelete('/w/old.ts');
-    assert.deepEqual(events, [{ file: '/w/old.ts', type: 'unlink' }]);
-  });
-
-  it('logs scanner failures instead of throwing, and does not notify', async () => {
-    const watcher = new FileWatcher(fakeScanner(async () => { throw new Error('boom'); }));
-    const { events } = recorder(watcher);
-    await assert.doesNotReject(watcher.handleFileChange('/w/x.ts'));
-    await assert.doesNotReject(watcher.handleFileCreate('/w/y.ts'));
-    assert.deepEqual(events, []);
-    assert.equal(errorSpy.mock.callCount(), 2);
-    assert.match(String(errorSpy.mock.calls[0].arguments[0]), /x\.ts.*boom/);
-  });
-
-  it('dispose drops listeners', () => {
-    const watcher = new FileWatcher(fakeScanner(async () => {}));
-    const { events } = recorder(watcher);
-    watcher.dispose();
-    watcher.handleFileDelete('/w/old.ts');
-    assert.deepEqual(events, []);
-  });
-
-  it('indexes the file through a real scanner', async () => {
-    const ws = newWorkspace();
-    try {
-      await ws.open();
-      const file = ws.write('src/fresh.js', 'function freshlyAdded() { return 1; }\n');
-      await new FileWatcher(ws.scanner).handleFileCreate(file);
-      assert.doesNotThrow(() => ws.node('freshlyAdded', 'src/fresh.js'));
-    } finally {
-      ws.close();
-    }
-  });
-});
-
-describe('FileWatcher.watchRoots', () => {
-  const tmp = new TempDir();
-  let watcher: FileWatcher;
-  let rec: ReturnType<typeof recorder>;
-  let warnSpy: ReturnType<typeof mock.method>;
-
-  before(async () => {
-    warnSpy = mock.method(console, 'warn', () => {});
-    tmp.mkdir('root/sub');
-    watcher = new FileWatcher(fakeScanner(async () => {}));
-    rec = recorder(watcher);
-    watcher.watchRoots([tmp.path('missing-root'), tmp.path('root')], ['.TS']);
-
-    // fs.watch starts asynchronously on some platforms (FSEvents on macOS), so
-    // writes made right after watchRoots can be missed. Touch a probe file
-    // until the watcher reports it, so every test starts with a live watcher.
-    // Touches are spaced well past the debounce, which a faster rewrite would
-    // keep restarting.
-    const probe = tmp.path('root/_probe.ts');
-    const deadline = Date.now() + 20000;
-    for (let i = 0; !rec.events.some(ev => ev.file === probe); i++) {
-      if (Date.now() > deadline) { throw new Error('the watcher never became ready'); }
-      fs.writeFileSync(probe, `export const probe = ${i};`);
-      await delay(DEBOUNCE_MS * 3);
-    }
-  });
-
-  after(() => {
-    watcher.dispose();
-    warnSpy.mock.restore();
-    tmp.remove();
-  });
-
-  it('warns about a root it cannot watch and keeps watching the others', () => {
-    assert.equal(warnSpy.mock.callCount(), 1);
-    assert.match(String(warnSpy.mock.calls[0].arguments[0]), /Could not watch .*missing-root/);
-  });
-
-  it('reports a new file with a supported extension (debounced), ignoring other extensions', async () => {
-    const ignored = tmp.write('root/notes.txt', 'x');
-    const file = tmp.write('root/a.ts', 'export const a = 1;');
-    const started = Date.now();
-    const e = await rec.next(ev => ev.file === file);
-    assert.ok(['add', 'change'].includes(e.type), e.type);
-    assert.ok(Date.now() - started >= DEBOUNCE_MS - 50, 'events are debounced');
-    assert.ok(!rec.events.some(ev => ev.file === ignored), 'unsupported extension is not reported');
-  });
-
-  it('watches subfolders recursively', async () => {
-    const file = tmp.write('root/sub/b.ts', 'export const b = 1;');
-    await rec.next(ev => ev.file === file);
-  });
-
-  it('coalesces rapid saves of one file into a single event', async () => {
-    const file = tmp.path('root/burst.ts');
-    for (let i = 0; i < 5; i++) { fs.writeFileSync(file, `export const v = ${i};`); }
-    await rec.next(ev => ev.file === file);
-    await delay(DEBOUNCE_MS + 150);
-    assert.equal(rec.events.filter(ev => ev.file === file).length, 1);
-  });
-
-  it('reports a deleted file as "unlink"', async () => {
-    const file = tmp.write('root/doomed.ts', 'x');
-    await rec.next(ev => ev.file === file);
-    fs.rmSync(file);
-    await rec.next(ev => ev.file === file && ev.type === 'unlink');
-  });
-
-  it('stops reporting after dispose', async () => {
-    watcher.dispose();
-    const late: Event[] = [];
-    watcher.onChange((file, type) => late.push({ file, type }));
-    tmp.write('root/late.ts', 'x');
-    await delay(DEBOUNCE_MS + 150);
-    assert.deepEqual(late, []);
-    assert.ok(!rec.events.some(ev => path.basename(ev.file) === 'late.ts'));
-  });
-});
`````

[Back to the shelf](README.md)
