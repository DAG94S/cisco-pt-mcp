import json

import mcp.types as mt
import pytest

from mcp_server import server, tools


def test_fast_forward_descriptor_has_no_arguments():
    schema = tools.TOOLS_BY_NAME["fastForwardTime"]["inputSchema"]
    assert schema["properties"] == {}
    assert schema["required"] == []
    assert schema["additionalProperties"] is False


@pytest.mark.asyncio
async def test_fast_forward_forwards_empty_arguments():
    class RecordingBridge:
        is_connected = True
        calls = []

        async def call_tool(self, name, args):
            self.calls.append((name, args))
            return {"success": True, "message": "Fast forward requested"}

    bridge = RecordingBridge()
    app = server.build_server(bridge)
    request = mt.CallToolRequest(params=mt.CallToolRequestParams(name="fastForwardTime", arguments={}))
    result = await app.request_handlers[mt.CallToolRequest](request)
    assert json.loads(result.root.content[0].text)["success"] is True
    assert bridge.calls == [("fastForwardTime", {})]
