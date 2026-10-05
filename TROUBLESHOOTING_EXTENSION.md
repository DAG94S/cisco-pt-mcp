# Troubleshooting & Extension Installation Guide for Cisco Packet Tracer MCP

This document explains how to properly install, activate, and fix the `cisco-pt-mcp.pts` extension in Packet Tracer on Windows.

---

## 1. Common Bug: Ghost Entry `com.yourcompany.NewPTScriptModule1`
When creating or editing script modules through Packet Tracer's *Script Module Packager* UI, Packet Tracer may register an empty in-memory draft with the ID:
`com.yourcompany.NewPTScriptModule1`
This prevents the actual `Packet Tracer MCP` menu item from appearing under the `Extensions` menu.

---

## 2. Definitive Fix Procedure

### Step 1: Copy the PTS binary to the system extensions directory
```powershell
New-Item -ItemType Directory -Force -Path "F:\Program Files\Cisco Packet Tracer 9.0.1\extensions\cisco-pt-mcp"
Copy-Item -Force "C:\Users\Diego\.gemini\antigravity-cli\tools\cisco-pt-mcp-repo\extension\cisco-pt-mcp.pts" "F:\Program Files\Cisco Packet Tracer 9.0.1\extensions\cisco-pt-mcp\cisco-pt-mcp.pts"
```

### Step 2: Configure in Packet Tracer GUI
1. Open Cisco Packet Tracer.
2. Go to **Extensions -> Scripting -> Configure PT Script Modules...**
3. Select any residual `com.yourcompany...` row and click **Remove**.
4. Click **Add** and choose:
   `F:\Program Files\Cisco Packet Tracer 9.0.1\extensions\cisco-pt-mcp\cisco-pt-mcp.pts`
5. On the right panel, select **On Startup**.
6. On the left panel, click **Start**.
7. Click **Ok** and restart Packet Tracer.

### Step 3: Connect Bridge
Go to **Extensions -> Packet Tracer MCP** to open the bridge window and establish the Socket.IO link on port `7531`.
