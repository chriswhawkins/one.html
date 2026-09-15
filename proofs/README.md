# Surface lab

**[Open the public demo](https://chriswhawkins.github.io/one.html/proofs/)** · [Runtime lab](https://chriswhawkins.github.io/one.html/proofs/runtime.html)

The public demo is static: use manual WebRTC pairing there. Link pairing, delayed streaming and the bundled WebSocket echo require the local helper below.

A working companion to the main reference. Open `index.html` through the ordinary static server for portable editing, manual peer pairing, agent commands, codec tests and device observations.

For link pairing, delayed HTML streaming and WebSocket echo, run the optional dependency-free Python helper:

```sh
python3 proofs/server.py --port 8765
```

Open `http://127.0.0.1:8765/proofs/`. The helper serves the repository, has no directory listings, and excludes hidden files and private key/certificate formats. Python 3.9+ is required. It is a development service, not an authenticated production collaboration backend.

For a phone, bind to a reachable interface and provide a certificate trusted by both devices:

```sh
python3 proofs/server.py --bind 0.0.0.0 --port 8443 --cert /path/cert.pem --key /path/key.pem
```

Open the host's LAN address or trusted hostname on both devices. HTTP on a LAN IP does not provide the secure context needed by capture and other APIs. No certificate, TURN server or public deployment is supplied.

## What to try

| Proof | Exercise | Requirements |
| --- | --- | --- |
| Portable surface | Edit a card, attach an image, draw, export HTML, reopen offline, edit and import back. | Browser HTML/JS; storage optional. No runtime downloads. |
| Real peers | Create a session, share its link, join from another browser, grant/revoke edits and test a stale draft. | WebRTC; helper for links or manual signaling. Different networks may require configured STUN/TURN. |
| Agent commands | Read state, propose text, apply at its expected revision; reject a stale or consumed proposal. | Local inspector always works. Native WebMCP requires a compatible implementation. |
| HTML & canvas | Stream regions while typing beside them; render an HTML form in canvas, select/edit it and export PNG. | Helper for the stream; native patching support. HTML-in-Canvas needs a compatible experimental browser. |
| Codec & mobile | Measure HTML/PNG bytes, encode/decode frames, record lifecycle observations and export evidence. | Working VP8 WebCodecs for video. Physical hardware needed for real device conclusions. |

The separate [`runtime.html`](runtime.html) runs SQLite and Python through WebAssembly workers, exports SQLite databases, saves/restores one OPFS snapshot and measures an actual WebSocket echo. Its WebTransport client needs a separately supplied HTTPS/HTTP3 stream-echo endpoint. Dependencies download only on **Load runtime from CDN**, with pinned versions and resource timing output. It does not claim a self-contained or guaranteed-offline runtime.

## Data and concurrency contract

A surface has an explicit schema, document identity, monotonically increasing revision, cards, strokes and provenance. Limits are 30 cards, 100 strokes, 1,200 points per stroke and 1.5 MB of normalized state. Images are limited to inline PNG/JPEG/WebP; new image uploads are resized and re-encoded. Cards use text, never imported HTML.

HTML exports contain the app and the selected committed state. Apply or reload an unfinished draft before exporting live state. JSON/HTML imports extract and validate only the state block. The preview renders escaped text in a scriptless sandbox with restrictive CSP. Imported scripts, event handlers, URLs and arbitrary markup are not adopted. Import is available only while disconnected.

Committed state and unapplied text drafts are recovered from namespaced localStorage keys per tab/session and path. Recovery can fail when storage is blocked or full; the UI reports this. Export is the portable backup. Session undo and the last 40 replay states are in memory. Replay is read-only; a fork receives a new document identity. Peer changes clear local undo to prevent undoing a peer's work accidentally.

The host validates commands against the latest revision synchronously before publishing state. Guests do not apply speculative changes. Conflicting edits are rejected; drafts remain available to review. This is an authoritative two-peer prototype, not a CRDT or offline multiwriter merge engine. A disconnected guest remains read-only until explicitly disconnecting into standalone mode or joining a fresh session.

Reliable messages are chunked and bounded; pointers use a separate unreliable channel. The host grants editing to one connected peer. Revocation is checked by the host even if the guest UI is stale. Session links grant viewer access, expire after 15 minutes and accept one answer. The helper retains only SDP in memory; it does not store the surface. Use new invitations to reconnect. ICE settings remain in memory and no public ICE service is contacted by default.

Screen/camera capture starts from its button. Available audio is optional; received sound starts muted. Select local or peer video explicitly. Stopping capture or disconnecting releases local tracks and notifies the receiver. Pointer coordinates account for video letterboxing. Captured-tab scroll/zoom are separate browser-gated capabilities, not arbitrary remote mouse/keyboard or OS control.

## Experimental APIs

WebMCP registration is awaited and failures are shown. The reference registers `list_patterns`, `open_pattern`, and `get_pattern_prompt`; the surface registers `get_surface`, `propose_edit`, and `apply_edit`. A compatible client can discover and invoke them. Application validation is retained independently of any schema validation the client performs.

In the tested Chromium 153 build, native `document.modelContext.executeTool` required a JSON **string** for its input, while the September 14 draft described an input object. The application callbacks receive parsed arguments. Pin the browser/version when reproducing native invocation tests; this API is evolving.

HTML-in-Canvas demonstrates an owned HTML form through both 2D canvas and a WebGL texture. Each captures an explicitly sized source region containing a rotated child form, then synchronizes the source geometry. This avoids applying the rotation twice. The tested 2D API already snapshots at device scale; scaling its context again breaks high-density output. Both the API and its geometry behavior vary by experimental version. Full assistive-technology and cross-browser audits remain separate checks.

The test browser was launched in an isolated process with experimental flags. No flags in the user's normal browser were changed:

```text
--enable-experimental-web-platform-features
--enable-blink-features=CanvasDrawElement,WebMCP
--enable-features=WebMCP
```

## Verification record · 2026-09-15

Browser checks ran in Chromium 153 using independent contexts and disposable data. The normal and experimental runs had no uncaught page errors.

| Area | Verified behavior |
| --- | --- |
| Portability | Text containing script syntax round-trips safely; exported `file:` document opens offline, remains editable, and recovers committed edits after reload. Unapplied text drafts also recover. |
| Editing | Keyboard movement, undo, pointer strokes, validated image import, replay read-only state and independent fork identity. |
| Imports | Invalid image formats leave state unchanged. Appended scripts in an imported HTML file do not execute. |
| Peers | Separate contexts pair through the helper, transfer a multi-chunk image, converge edits, preserve active drafts, reject stale commits, revoke editing and reconnect to current host state. |
| Media | Browser-generated camera video reaches the other peer; remote pointing, stop, restart and disconnect cleanup work. This used synthetic media, not the user's camera or screen. |
| Native HTML | Parser patching works without scripts. Delayed network fragments preserve an independent active textarea; interrupting delivery retains it. |
| Experimental canvas | Both 2D and WebGL pass form editing/selection, pointer focus after rotation, and visually inspected PNG export in flagged Chromium. Desktop and 390 px / 2× device-scale layouts were checked. |
| Native WebMCP | Registration, native tool discovery/invocation and consumed-proposal rejection pass. The main catalog exposes 25 patterns with correct source prompts. External model reasoning was not tested. |
| Codec | All 30 VP8 frames encode and decode. One disposable run produced 33,616 encoded bytes in 465 ms; this is an observation, not a performance guarantee or a complete media container. |
| Runtimes | Real SQLite query and OPFS save/restore pass; SQL errors permit retry. Python runs in a worker; its infinite loop leaves the UI clock responsive and can be terminated. |
| Transport | Native WebSocket echo matches its payload. Server checks reject bad origins, invalid SDP, wrong token roles, reused invitations and hidden-file requests. |
| Layout | All five surface views and the runtime lab fit a 390 px viewport. This does not establish actual iOS/Android behavior. |

Public deployment checks also cover source links under `/one.html/`, static-helper fallback, and offline reloads with section fragments. Worker asset matching ignores fragments so bookmarked sections use the cached shell.

Artifacts and executable Playwright CLI check scripts live in ignored `output/playwright/`. No package manager or test framework was added to the repository.

Still requiring the corresponding environment: physical iPhone/iPad/Android input and lifecycle tests; actual screen chooser/scroll/zoom tests; cross-network TURN traversal; a real WebTransport/MoQ endpoint; MQTT broker/WebTorrent swarm integration; installed IWA controlled frames and direct sockets. The UI and roadmap distinguish those from verified results.
