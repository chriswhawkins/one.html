# Next proofs for one.html

Research date: 2026-09-14. These are proposed experiments, with current platform documentation and local source evidence. They are not claims that the experiments have passed.

## Implementation checkpoint · 2026-09-15

The five priority tracks now have working demonstrations in [Surface lab](../proofs/index.html), with an additional [runtime and transport lab](../proofs/runtime.html). See the [verification record](../proofs/README.md) for exact results and limits. Implemented: portable export/import and replay, authoritative two-peer sharing, versioned commands and native WebMCP registration, delayed native HTML patching, 2D and WebGL HTML-in-Canvas, real WebCodecs encode/decode, device observations, SQLite/Python workers, OPFS snapshots and WebSocket echo.

The following sections preserve the acceptance criteria and future directions. Physical-device tests, cross-network relay testing, external protocol ecosystems and installed IWA capabilities remain explicitly unverified or follow-on work; API presence is not counted as their completion.

## Recommendation

Build a **portable, shared surface** as the next substantial spike. A person creates a card, annotates it, exports it as HTML, opens it on a phone, and collaborates with another person or an agent. Use that journey to test representation, transport, persistence, rendering, and control.

The strongest question is: **what is the smallest transferable representation that preserves the actions someone needs to perform?** Reading a report, editing a diagram, watching a camera, and operating a remote app have different answers.

## What the reference currently stops short of proving

| Existing example | Next meaningful boundary |
| --- | --- |
| BroadcastChannel room | Two physical devices, independent browsers, reconnect and state convergence |
| WebRTC loopback | Real remote pairing, signaling, relay requirements, loss and latency |
| WebCodecs configuration probes | Actual encode → transport → decode → render, with backpressure |
| Canvas sketch and iframe messaging | Portable state, accessible interaction, coordinate mapping and explicit control |
| API compatibility badges | Successful behavior in a named browser/device, with prerequisites and failure results |

## Local inspiration

The requested `~/dev/extensions` directory is actually `~/dev/extension`. Nearby projects contain the stronger connections below. Inspection covered READMEs and selected implementation paths; these applications were not all run or independently revalidated.

| Project | Existing idea to carry over | Concrete reference |
| --- | --- | --- |
| `surface` + `strata` | Movable surfaces with explicit fidelity: snapshot, text, source-linked, semantic, controlled. Store origin and capabilities with the artifact. | `../surface/background.js` (`createSelectionSurface`); `../strata/shared/strata_project.schema.json` |
| `lens` + `margin` | A page contract, selection context, revision proposals and insertion into an editable surface. | `../lens/docs/aia-page-contract.md`; `../margin/content.js` |
| `glass-feedback-extension` + `safety-glass` | Crop regions, annotations, source evidence and JSON/image export. Extension capture privileges must be declared separately from ordinary page capabilities. | Their READMEs and capture/content scripts |
| `virtual-codec` | Side-by-side pixels and derived signals, exportable payloads, bounded agent settings and stale-result guards. | `../virtual-codec/hooks/use-video-pipeline.ts`; `../virtual-codec/lib/codec/stages/` |
| `playground` + `live-context-agent-demo` | iPad pointer interaction; phone camera/audio as a session input; reconnect and evidence attribution. | `../playground/js/canvas-studio.js`; `../live-context-agent-demo/public/live.js` |

Paths in this table are relative to the repository root, referring to sibling projects.

## Five priority proofs

### 1. An HTML surface that survives export and reopening

Start with owned content: a note, image, diagram, annotation layer and a few controls. Export a self-contained HTML file containing the renderer, assets, versioned state and source metadata. Reopen it offline in another browser, edit it, export again, and import it back.

**Pass:** text, geometry, assets and supported actions survive; the normalized application state matches after a round trip; missing capabilities are visible. Explicitly test both downloaded `file:` opening and a served origin because permission and storage behavior differ.

**Measure:** total artifact bytes, external requests, startup time, recoverable edits and unsupported behavior. Include runtime and asset overhead in the size.

`outerHTML` alone cannot capture a running application's state, event listeners or canvas bitmap. Serializable Shadow DOM and `getHTML()` can help preserve component markup; application state and behavior still need an explicit contract. [HTML serialization standard](https://html.spec.whatwg.org/multipage/dynamic-markup-insertion.html#dom-element-gethtml).

Treat imported documents as untrusted: preview them in an isolated frame and import validated data into the owned renderer. Do not execute arbitrary imported scripts in the editor's origin.

### 2. A desktop-and-phone shared surface

Extend the room into a real two-device session. Pair by a short-lived room link or QR code, send transient cursors separately from durable edits, then disconnect and reconnect. Use an explicit authoritative state/version for the first implementation; introduce a conflict-free data structure only if independent offline editing becomes a requirement.

**Pass:** simultaneous actions converge; late joiners receive current state; reload does not duplicate edits; a stale client cannot overwrite a newer document silently. Permission to control the shared surface can be revoked immediately.

**Measure:** round-trip latency, acknowledged action latency, queue growth, bytes and recovery time. One-way timing across devices needs clock synchronization; do not simply subtract unrelated browser clocks.

WebRTC data channels offer ordered/reliable and limited-retransmission modes. A real session also needs signaling and, for networks that cannot connect directly, a TURN relay. A hand-exchanged offer/answer is a useful diagnostic mode, not the finished pairing experience. [WebRTC specification](https://www.w3.org/TR/webrtc/), [WebRTC connection guidance](https://webrtc.org/getting-started/peer-connections).

### 3. Humans and agents invoke the same commands

Expose the reference's own actions through WebMCP: `list_patterns`, `open_pattern`, `get_pattern_prompt`. Then try `propose_edit` and `apply_edit(expectedVersion)` on the shared surface. Keep normal buttons and agent tools wired to the same application commands.

**Pass:** a compatible agent discovers and invokes the real tools; invalid inputs and stale versions fail usefully; changes remain visible and undoable. A JavaScript test harness verifies command logic, but does not prove native agent discovery.

Chrome documents an origin trial from version 149 and a local testing flag. The current draft uses `document.modelContext`; older preview snippets may differ. It remains a draft community proposal, so record the implementation version. [Chrome WebMCP documentation](https://developer.chrome.com/docs/ai/webmcp), [current draft](https://webmachinelearning.github.io/webmcp/).

### 4. HTML updates as a transport format

Stream a report shell, then deliver independently completed sections as HTML fragments. Add an active textarea next to one section and test updates while someone types. Compare native patching with a small existing DOM update path.

**Pass:** useful content appears before the stream completes; updates reach the intended regions; unrelated drafts, focus and selection survive; interruption leaves understandable content. Updating an active editor itself requires an explicit conflict policy.

Chrome's September 8 documentation lists out-of-order `<template for>` patching from Chrome 150. The newer `streamHTML*` insertion methods remain behind a testing flag, with launch planned for 155. They should have separate support labels. [Declarative partial updates](https://developer.chrome.com/docs/web-platform/declarative-partial-updates).

Native patching was minimally reproduced in test Chromium 153 with no page JavaScript:

```html
<!doctype html>
<body>
  <div id="target"><?marker name="proof"></div>
  <template for="proof"><strong>arrived</strong></template>
</body>
```

After navigation, `#target` contained `arrived`. This proves parser patching for this fixture, not incremental network streaming or edit preservation. Keep the processing-instruction attribute quoted: an unquoted probe did not patch.

### 5. Real HTML inside a canvas surface

Render an owned HTML card through 2D canvas and a transformed GPU surface. Include text selection, a form field, keyboard navigation, zoom and an image/video export. Keep an ordinary DOM view for comparison.

**Pass:** visual location, pointer targeting, focus, selection and accessibility agree after transforms. Exported pixels agree with the intended view. Test complex text and device pixel ratios.

HTML-in-Canvas is experimental; the living explainer documents a Chromium flag and geometry synchronization APIs. The earlier origin-trial article and current explainer contain evolving API shapes. Use the implementation-matching version. Cross-origin iframe pixels are excluded from readable output. [Living explainer](https://wicg.github.io/html-in-canvas/), [official interactive demos](https://chrome.dev/html-in-canvas/).

## Screen sharing and remote control: three distinct proofs

| Scope | Useful experiment | Actual boundary |
| --- | --- | --- |
| Owned application | A phone moves a desktop card, advances slides or edits a diagram through validated commands. | Normal web app plus a transport; full semantic control over the app's own state. |
| Captured browser tab | Send selected-tab video and overlay remote annotations; try scroll and zoom controls. | Captured Surface Control is desktop Chrome 136+ and controls scroll/zoom of captured tabs. It is not general remote clicking or typing. |
| Arbitrary external application | Extension-assisted or native remote desktop experiment. | Requires a privileged integration and a separate capability declaration; ordinary HTML cannot promise arbitrary OS input. |

[Captured Surface Control documentation](https://developer.chrome.com/docs/web-platform/captured-surface-control).

For shared annotations, test source coordinates against scrolling, resizing, browser zoom and differing aspect ratios. Present an owned sharing surface that excludes private notes. Region Capture crops to a region, but cropping alone should not be treated as an isolation boundary. [Region Capture documentation](https://developer.chrome.com/docs/web-platform/region-capture/).

For mobile, begin with receiving the desktop share, drawing annotations, sending camera/audio and controlling owned content. Current browser compatibility data lists `getDisplayMedia` as unsupported in Safari on iOS and Chrome on Android. [Compatibility data](https://github.com/mdn/browser-compat-data/blob/main/api/MediaDevices.json).

## HTML as a codec: a testable definition

Use **HTML + structured state + assets + operations** as a representation for a bounded class of interactive scenes. Test three deliveries of the same task: pixels/video, semantic state/operations, and a hybrid with raster fallbacks.

| Workload | What must survive |
| --- | --- |
| Report | Read, search, select, copy, cite and reopen offline |
| Diagram or board | Move an object, change text, preserve identity and undo |
| Captured external page | Visual fidelity and source attribution; declare lost editability |
| Camera scene | The specific visual task and its error rate; extracted edges are not a reconstruction of the source video |

Measure total delivered bytes including the initial renderer/assets, update bytes, time to useful display, action latency, readability, editability and task error. Compare cold and warm starts. Do not declare a compression win when one representation discarded information the other retained.

`virtual-codec` already states the crucial limitation: its JSON/JPEG ratio compares extracted signals with a sampled JPEG, not equivalent-information video compression. Its reported CV time also excludes parts of capture/render/serialization. The next experiment should add the complete path and task outcomes.

Two ambitious variants: an HTML “recording” that can pause and fork into an editable scene; and a shared surface that switches from video to semantic updates when both ends understand its document contract. These are hypotheses to benchmark, not established advantages.

## Other protocols and code types worth trying

| Candidate | Useful proof | Required support |
| --- | --- | --- |
| WebTransport / Media over QUIC | Compare interactive updates and live media under delay, loss and congestion. | Compatible endpoint; MoQ additionally needs a protocol implementation and relay. It is not a built-in HTML media source. [IETF MoQ](https://datatracker.ietf.org/wg/moq/about/) |
| MQTT over secure WebSockets | A phone publishes sensor values; another surface subscribes and controls an owned demo device. | Client library and WebSocket-capable broker. [MQTT.js](https://github.com/mqttjs/MQTT.js) |
| WebTorrent | Transfer an exported HTML artifact through browser peers and verify its content. | Library, discovery and available WebRTC-capable peers; regular TCP-only torrent peers cannot directly serve browsers. [WebTorrent FAQ](https://webtorrent.io/faq) |
| SQLite or Python through WebAssembly | An offline HTML workbench queries a local dataset or runs a reproducible computation. | Runtime assets and a worker; measure startup, memory, persistence and cancellation. [SQLite persistence](https://www.sqlite.org/wasm/doc/trunk/persistence.md), [Pyodide workers](https://pyodide.org/en/stable/usage/webworker.html) |
| Controlled Frame / Direct Sockets | Test the embedding and raw TCP/UDP limits encountered by `surface`. | Installed Isolated Web App, permissions and packaging. These capabilities are not available to an ordinary HTML tab. [Controlled Frame](https://developer.chrome.com/docs/iwa/controlled-frame), [Direct Sockets](https://developer.chrome.com/docs/iwa/direct-sockets) |

Keep runtime claims precise: SVG and MathML are markup; GLSL and WGSL are shader languages invoked through graphics APIs; WebAssembly is a binary execution format. Adding an unfamiliar `script type` does not make a browser execute Python or SQL. Runtime-backed demonstrations belong in an explicitly labeled lane with download costs.

## Mobile must test lifecycle, not just layout

Borrow the iPad playground's pressure and pointer capture work, then test actual hardware. The minimum useful matrix is iPhone Safari, iPad Safari with Pencil, and Android Chrome, with device/OS/browser versions recorded.

Test drawing while panning, multi-touch, virtual keyboard and rotation. Then lock/unlock, background the app, interrupt audio/camera, disconnect the network and reopen after process termination. Define which edits must survive, when media restarts require a gesture, and what the peer sees while the device is suspended.

A narrow viewport test remains useful for layout, but proves none of those hardware and lifecycle behaviors.

## How the explorer should present these

Each proof needs five compact fields:

- **Try:** one concrete task and its expected result.
- **Proves:** the boundary under test and a pass/fail result.
- **Requires:** ordinary tab, HTTPS/permission, server, runtime, flag, or installed integration.
- **Evidence:** browser/device/date, measured behavior, known failure and source.
- **Reuse:** copy-agent prompt containing the objective, source anchors, requirements and acceptance test.

Keep “API detected,” “demo passed here,” and “tested on these devices” separate. Reuse Strata's fidelity categories for surfaces; they express what a person or agent can actually do with them.

## Verification performed for this research

Selected local source and current official documentation were inspected. Test Chromium reported version 153, with a secure local origin. WebTransport, WebCodecs, WebGPU, screen capture and Captured Surface Control were present; permission grants, real remote sessions and hardware behavior were not exercised in this research pass.

`document.modelContext`, `navigator.modelContext`, `drawElementImage` and `streamHTML` were absent in that test configuration. `getHTML` was present. The quoted native patching fixture above passed. No experimental flags were changed.

Suggested order: **portable surface → real desktop/phone session → shared human/agent commands**. Run native HTML patching and HTML-in-Canvas as small, separately labeled experiments feeding into that surface.
