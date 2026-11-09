import json
import os

import mcp.types as mt
import pytest

from mcp_server import server


class RecordingBridge:
    is_connected = True

    def __init__(self):
        self.calls = []

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return {"success": True, "path": args["filePath"]}


async def invoke(bridge, arguments):
    app = server.build_server(bridge)
    request = mt.CallToolRequest(params=mt.CallToolRequestParams(name="openFile", arguments=arguments))
    result = await app.request_handlers[mt.CallToolRequest](request)
    return json.loads(result.root.content[0].text)


@pytest.mark.asyncio
async def test_open_existing_pkt_is_forwarded(tmp_path):
    path = tmp_path / "red con espacios.pkt"
    path.write_bytes(b"fixture")
    bridge = RecordingBridge()
    result = await invoke(bridge, {"filePath": str(path)})
    assert result["success"] is True
    assert bridge.calls == [("openFile", {"filePath": str(path)})]


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["relative.pkt", "missing.pkt", "wrong.txt"])
async def test_invalid_path_never_reaches_packet_tracer(tmp_path, filename):
    path = filename if filename == "relative.pkt" else str(tmp_path / filename)
    if filename == "wrong.txt":
        (tmp_path / filename).write_text("not a pkt")
    bridge = RecordingBridge()
    result = await invoke(bridge, {"filePath": path})
    assert result["success"] is False
    assert bridge.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("alias", [".", "sub/.."])
async def test_existing_absolute_alias_is_canonicalized_without_mutating_input(tmp_path, alias):
    path = tmp_path / "lab.pkt"
    path.write_bytes(b"fixture")
    (tmp_path / "sub").mkdir()
    alias_path = str(tmp_path) + os.sep + alias.replace("/", os.sep) + os.sep + "lab.pkt"
    arguments = {"filePath": alias_path}
    bridge = RecordingBridge()
    await invoke(bridge, arguments)
    assert bridge.calls == [("openFile", {"filePath": str(path.resolve())})]
    assert arguments == {"filePath": alias_path}


@pytest.mark.asyncio
async def test_existing_symlink_is_forwarded_as_real_file(tmp_path):
    path = tmp_path / "lab.pkt"
    path.write_bytes(b"fixture")
    link = tmp_path / "alias.pkt"
    try:
        link.symlink_to(path)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    bridge = RecordingBridge()
    await invoke(bridge, {"filePath": str(link)})
    assert bridge.calls == [("openFile", {"filePath": str(path.resolve())})]

