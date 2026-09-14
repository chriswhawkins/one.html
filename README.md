# one.html

**One HTML file. Every web feature I can fit into it.**

This started as a long-running kitchen sink for the web platform: HTML, CSS, JavaScript, browser APIs, hardware access, storage, graphics, AI, accessibility, and whatever comes next.

More recently, I’ve found it useful as a compact, working body of examples that constrains coding agents toward modern, browser-native solutions instead of generic framework-shaped answers.

It’s not intended to be a framework, component library, or canonical implementation. It’s a maintained reference: working examples of what the platform itself can do right now.

## Run it

No install or build step. From this directory:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [localhost:8000](http://localhost:8000/). Opening `index.html` directly works for some examples; use localhost or HTTPS for secure-context APIs, modules, and service workers. Browser, OS, hardware, permissions, and experimental flags affect what runs. Detection badges indicate API presence or accepted syntax, not guaranteed behavior; cross-browser tags are rough notes, not a compatibility promise.

Storage examples read and modify this origin’s browser storage. Use a dedicated local port or origin when experimenting; clear buttons affect the whole origin. The report editor saves to IndexedDB and caches its shell for offline use. Its imported rich text preserves basic formatting but strips attributes and unsupported elements. Hardware access and other permission-sensitive demonstrations run from their controls. The abort demo contacts httpbin.org; the Cache API demo fetches the URL you enter. Speech recognition may use a browser vendor’s remote service. Built-in AI demonstrations depend on browser-provided models.

## What lives here

- [`index.html`](index.html): the main reference, with inline styles, scripts, generated media, and feature detection. Use its section links to share individual examples.
- [`sw.js`](sw.js): the opt-in offline demo. Service workers require a separate served resource.
- [`editor/`](editor/index.html): a report-editing spike derived from the reference, with its own service worker. It demonstrates local editing and an operation log; it is not a production editor or multi-user sync system. [`report-editor.html`](report-editor.html) forwards to it.
- [`AGENTS.md`](AGENTS.md): guidance for working on this repository.
- [`skills/browser-native-spike/SKILL.md`](skills/browser-native-spike/SKILL.md): reusable guidance for building browser-native prototypes elsewhere.

## Use it with an agent

Point your agent at `index.html` and describe the interaction you want to explore. Ask for a working, inspectable prototype using the browser platform before adding dependencies.

The `browser-native-spike` skill can be copied as a folder into your agent’s supported skills directory without cloning the rest of this repository. It consults the current [main artifact](https://raw.githubusercontent.com/chriswhawkins/one.html/main/index.html), keeping examples out of the skill itself. A local checkout or commit-pinned copy also works when offline or when reproducibility matters.

## Keep it small

Add useful examples, fix incorrect ones, and document meaningful limitations. Keep native HTML, CSS, and JavaScript inspectable; preserve older examples unless they are wrong. Supporting files are fine where the platform needs them. Let real experiments drive organization rather than designing a taxonomy in advance.
