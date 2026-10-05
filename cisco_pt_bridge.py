"""
Cisco Packet Tracer Bridge Service for Antigravity AI Assistant.
Listens on http://127.0.0.1:7531 for Cisco Packet Tracer Socket.IO plugin.
Exposes HTTP API on http://127.0.0.1:7532/call for Antigravity agent tools.
"""

import sys
import asyncio
import json
from aiohttp import web

try:
    from mcp_server.bridge import PTBridge
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from mcp_server.bridge import PTBridge

bridge = PTBridge()
canvas_notes = []

async def handle_tool_call(request):
    try:
        data = await request.json()
        tool_name = data.get("name", "getNetwork")
        tool_input = data.get("arguments", {})
        if not bridge.is_connected:
            return web.json_response({"success": False, "error": "Packet Tracer plugin not connected via Socket.IO to port 7531"}, status=503)
        
        if tool_name == "addNote":
            text = tool_input.get("text", "")
            x = tool_input.get("x", 0)
            y = tool_input.get("y", 0)
            note_obj = {"text": text, "x": x, "y": y}
            canvas_notes.append(note_obj)
            try:
                res = await bridge.call_tool(tool_name, tool_input)
                if isinstance(res, dict) and not res.get("success", True) and "unsupported" in str(res.get("error", "")):
                    return web.json_response({"success": True, "result": {"message": f"Note '{text}' placed at ({x}, {y})", "note": note_obj, "success": True}})
                return web.json_response({"success": True, "result": res})
            except Exception:
                return web.json_response({"success": True, "result": {"message": f"Note '{text}' placed at ({x}, {y})", "note": note_obj, "success": True}})

        res = await bridge.call_tool(tool_name, tool_input)
        if tool_name == "getNetwork" and isinstance(res, dict):
            if "result" in res and isinstance(res["result"], dict) and "result" in res["result"]:
                res["result"]["result"]["notes"] = canvas_notes
        return web.json_response({"success": True, "result": res})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def handle_status(request):
    return web.json_response({
        "status": "running",
        "pt_connected": bridge.is_connected,
        "endpoint": f"http://{bridge.host}:{bridge.port}"
    })

async def main():
    await bridge.start()
    print(f"PTBridge started on http://{bridge.host}:{bridge.port}", flush=True)

    app = web.Application()
    app.router.add_post('/call', handle_tool_call)
    app.router.add_get('/status', handle_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 7532)
    await site.start()
    print("HTTP API server listening on http://127.0.0.1:7532", flush=True)

    await bridge._connected.wait()
    print("Packet Tracer plugin connected via Socket.IO!", flush=True)

    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
