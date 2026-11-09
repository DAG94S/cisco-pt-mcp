# Open Packet Tracer files

Approved by user: expose native `ipc.appWindow().fileOpen(path)` through MCP.

The server validates an absolute, existing `.pkt` file before forwarding. The extension preserves native save/cancel prompts and never auto-saves or discards changes. An already active target is reported with `alreadyOpen: true` without reloading it. No undocumented dirty flag is assumed. Verify success using documented `getActiveFile().getSavedFilename()` and include the native return code, never a guessed numeric enum. Tests cover forwarding, validation, native failure, cancellation/mismatched filename and already-open behavior.

The encrypted `.pts` module must be rebuilt in Packet Tracer Scripting Interface after importing the updated Script Engine and Custom Interface sources. Source tests do not prove installed-module behavior.
