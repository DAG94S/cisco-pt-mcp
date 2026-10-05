# cisco-pt-mcp

Let AI clients control a running Cisco Packet Tracer instance. Open source.

![Demo](https://raw.githubusercontent.com/muhammadbalawal/cisco-pt-mcp/main/docs/demo.gif)

---

## Install

Two components. Five minutes.

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

| Tool | Description |
|---|---|
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
| `execCommand` | Execute a single IOS command and capture real terminal output |

---

## Installation from this Repository

```sh
# Clone this repository
git clone https://github.com/DAG94S/cisco-pt-mcp.git
cd cisco-pt-mcp

# Install in editable mode
pip install -e .
```

### Configure in Claude Code (`~/.claude.json`)
```json
{
  "mcpServers": {
    "cisco-pt-mcp": {
      "type": "stdio",
      "command": "cisco-pt-mcp"
    }
  }
}
```

### Antigravity AI Bridge (`cisco_pt_bridge.py`)
To use with Antigravity assistant on port 7532:
```sh
python cisco_pt_bridge.py
```

## License

MIT
