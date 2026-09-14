# Project purpose

`one.html` is a maintained web-platform reference and a source of constraints for browser-native prototypes. `index.html` is the main artifact; `editor/` is a related spike.

## Working here

- Prefer semantic HTML, CSS, and browser APIs, then small amounts of plain JavaScript. Keep the main artifact self-contained where the platform permits it; document necessary support files such as service workers.
- Make the smallest working example. Do not introduce a framework, build system, dependencies, or speculative abstractions to organize demonstrations.
- Preserve section IDs, inspectable source, and older examples. Fix incorrect behavior; do not refactor unrelated examples just for consistency.
- Feature-detect experimental capabilities and show useful failure states. Account for accessibility, permissions, secure contexts, and actual browser support; API presence alone does not prove an example works.
- Keep test data disposable. Do not clear unrelated storage or unregister unrelated service workers as a side effect of a test. Treat imported content as untrusted.

## Verification

Serve the directory with `python3 -m http.server 8000 --bind 127.0.0.1`. Check the affected demonstrations in a browser, including their console output and relevant unsupported/error states. For worker changes, check offline behavior and registration scope, including serving under a subpath. Match verification to the change; no package manager or general test framework is required.

The reusable skill belongs in `skills/browser-native-spike/SKILL.md`. Keep it focused on how to consult the reference, without copying the examples into it. Let additional real spikes guide future organization.
