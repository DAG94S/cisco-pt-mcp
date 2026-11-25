# cisco-pt-mcp

Let AI clients control a running Cisco Packet Tracer instance. Open source.

> **This is a fork of [muhammadbalawal/cisco-pt-mcp](https://github.com/muhammadbalawal/cisco-pt-mcp)**
> (v0.1.6, MIT). All credit for the original server, extension and site goes to its author.
> The fork adds, tested on Packet Tracer 9.0.1:
>
> - **Canvas notes:** `addNote`, `getNotes`, `updateNote`, `deleteNote`.
> - **Files:** `saveFile` and `openFile` for `.pkt` workspaces.
> - **Time:** `fastForwardTime`, one native Realtime "Fast Forward Time" click.
> - **`execCommand` with real console output:**
>   - On PCs and servers it runs Command Prompt commands (`ping`, `tracert`, `ipconfig`, `arp -a`).
>   - On routers and switches, `ping` and `traceroute` wait for their summary line instead of
>     returning an empty string.
> - **Antigravity bridge** (`cisco_pt_bridge.py`).
>
> The fork is not published on PyPI: `uvx cisco-pt-mcp` installs the upstream package, which
> lacks these tools. Install from this checkout instead (see
> [Installation from this Repository](#installation-from-this-repository)) and load the bundled
> `extension/cisco-pt-mcp.pts`.

![Demo](https://raw.githubusercontent.com/muhammadbalawal/cisco-pt-mcp/main/docs/demo.gif)

---

## Install

Two components. Five minutes. The steps below describe the upstream package; for this fork's
tools use [Installation from this Repository](#installation-from-this-repository).

### 1. MCP Server

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then register with your client:

**Claude Code**
```sh
claude mcp add cisco-pt-mcp --scope user -- uvx cisco-pt-mcp
```

**Cursor** (`~/.cursor/mcp.json` or `.cursor/mcp.json` per project)
```json
{
  "mcpServers": {
    "cisco-pt-mcp": { "command": "uvx", "args": ["cisco-pt-mcp"] }
  }
}
```

**VS Code** (`.vscode/mcp.json`)
```json
{
  "servers": {
    "cisco-pt-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["cisco-pt-mcp"]
    }
  }
}
```

**Codex CLI** (`~/.codex/config.toml`)
```toml
[mcp_servers.cisco-pt-mcp]
command = "uvx"
args = ["cisco-pt-mcp"]
```

### 2. Packet Tracer Extension

1. Open Packet Tracer.
2. Go to **Extensions → Scripting → Configure PT Script Modules…**
3. Click **Add** and select [`cisco-pt-mcp.pts`](extension/cisco-pt-mcp.pts).
4. Restart Packet Tracer.

### 3. Run

Click **Extensions → Packet Tracer MCP** to open the bridge window, then start your MCP client. The status pill flips to `connected` within a second. Start prompting.

---

## Tools

### Opening a saved network

Call `openFile` with an absolute, existing local `.pkt` path, for example:

```json
{"filePath": "C:/Labs/team-01.pkt"}
```

The server rejects missing files, relative paths and other extensions before
contacting Packet Tracer. The extension uses the native `fileOpen` operation,
retains its return code and verifies `getActiveFile().getSavedFilename()`.
An already active target returns `alreadyOpen: true` without reloading it.
Packet Tracer's save/cancel prompts are preserved: answer any prompt in Packet
Tracer, then check the result and call `getNetwork` to inspect the loaded network.
No source file is saved or overwritten by this tool.

**Installing this update:** replace the previously registered module with the
bundled `extension/cisco-pt-mcp.pts`, which includes `openFile` and
`fastForwardTime`, then restart the module and MCP client. Importing individual
JavaScript files is only necessary when rebuilding after further source edits.

**Rebuilding after source changes:** the checked-in `extension/cisco-pt-mcp.pts` is an
encrypted Packet Tracer module, not a ZIP and not rebuilt by Python installation.
Use **Extensions → Scripting → Configure PT Script Modules**, select the MCP module
and click **Edit** to open its Scripting Interface.
Import/update `extension/source/userfunctions.js` in its **Script Engine** files
and `extension/source/interface/interface.js` in its **Custom Interface** files,
preserving the existing module ID and other source files, then save/export the
module to a new `.pts`. Stop the old module in **Configure PT Script Modules**,
load/start the updated module and reconnect its bridge window. Restart the MCP
server/client so that `openFile` is advertised. Verify with an expendable `.pkt`
before using student submissions. Offline source tests do not verify the installed
encrypted module.

Run `python -m pytest -q` and `node --test tests/open_file.test.cjs` for offline tests.

### Fast Forward Time

Call `fastForwardTime` with `{}` to invoke one native click of the Realtime
**Fast Forward Time** button. The operation calls
`ipc.appWindow().getRealtimeToolbar().fastForwardTime()` once and reports the
request. It does not claim the network has converged: inspect adjacencies and
routing tables separately. Update the same `userfunctions.js` and
`interface/interface.js` module sources described above and restart the MCP
server/client to expose this tool. Test its adapter with
`node --test tests/fast_forward.test.cjs`.

Integration checked on Packet Tracer 9.0.1: opening a copy of a saved network
returned success and the subsequent network query found 14 devices and 14 links.
A repeated open kept the bridge connected. Fast Forward Time was accepted and
kept the bridge connected on an empty workspace; protocol convergence was not
tested by that check. Save/cancel dialogs were not exercised in the live test.

| Tool | Description |
|---|---|
| `fastForwardTime` | Request one native Realtime Fast Forward Time click; verify convergence separately |
| `openFile` | Open an existing absolute `.pkt` path and verify the active filename |
| `addDevice` | Drop a router, switch, or PC onto the canvas |
| `addModule` | Install an interface module into a device slot |
| `addLink` | Connect two devices with a cable |
| `removeDevice` | Delete one or more devices |
| `removeLink` | Delete one or more cables |
| `renameDevice` | Rename an existing device |
| `moveDevice` | Reposition a device on the canvas |
| `setPower` | Power a device on or off |
| `configurePcIp` | Set IP, subnet, gateway, DNS, or enable DHCP on a PC |
| `configureIosDevice` | Run IOS CLI commands on a router or switch |
| `getNetwork` | Snapshot of all devices, interfaces, and cables |
| `getDeviceInfo` | Detailed view of a single device |
| `setSimulationMode` | Switch between simulation and realtime mode |
| `getSimulationStatus` | Query simulation state and frame count |
| `stepSimulation` | Step the simulation forward, backward, or reset |
| `sendPdu` | Add an ICMP ping PDU between two devices |
| `getPduResults` | Read PDU outcomes after stepping the simulation |
| `getCommandLog` | Read the IOS command history logged by Packet Tracer |
| `addNote` | Place floating text note / IP annotation on canvas |
| `getNotes` | Read all text notes on canvas with text, coordinates, and UUIDs |
| `updateNote` | Modify note text content or canvas coordinates |
| `deleteNote` | Remove a text note from canvas by UUID |
| `saveFile` | Save active Packet Tracer workspace (.pkt) to an absolute path |
| `execCommand` | Run one command and capture its real output: IOS commands on routers and switches, Command Prompt commands (`ping`, `tracert`, `ipconfig`) on PCs; `ping`/`traceroute` wait until they finish (`waitSeconds`, default 10) |

---

## Installation from this Repository

```sh
# Clone this repository
git clone https://github.com/DAG94S/cisco-pt-mcp.git
cd cisco-pt-mcp

# Install in editable mode
pip install -e .
```

### Configure in Claude Code
```sh
claude mcp add cisco-pt-mcp --scope user -- python -m mcp_server.server
```
Use the same Python interpreter that ran `pip install -e .`.

Then load `extension/cisco-pt-mcp.pts` in Packet Tracer
(**Extensions → Scripting → Configure PT Script Modules → Add**), start it and open
**Extensions → Packet Tracer MCP** until it shows `connected`. See
[TROUBLESHOOTING_EXTENSION.md](TROUBLESHOOTING_EXTENSION.md) if the menu item does not appear.

### Antigravity AI Bridge (`cisco_pt_bridge.py`)
To use with Antigravity assistant on port 7532:
```sh
python cisco_pt_bridge.py
```

## License

MIT. Copyright of the original work: Muhammad Balawal (see [LICENSE](LICENSE)).
