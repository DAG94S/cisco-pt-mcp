"""Offline tests for execCommand with deferred output (mcp_server.comandos)."""

from __future__ import annotations

import asyncio

from mcp_server.comandos import exec_command


class FakePT:
    """Answers bridge calls; readCommandOutput reveals one more chunk per read."""

    def __init__(self, chunks, *, exec_result=None, ended_after=None):
        self.chunks = list(chunks)
        self.exec_result = exec_result or {"success": True, "output": "show output"}
        self.ended_after = ended_after
        self.reads = 0
        self.calls = []

    async def __call__(self, name, args):
        self.calls.append((name, dict(args)))
        if name == "execCommand":
            return self.exec_result
        if name == "startCommand":
            return {"success": True, "terminal": "pc"}
        if name == "readCommandOutput":
            if not args["finish"]:
                self.reads += 1
            shown = "".join(self.chunks[: self.reads])
            ended = self.ended_after is not None and self.reads >= self.ended_after
            return {"success": True, "command": "x", "output": shown, "ended": ended,
                    "terminal": "pc", "events": self.reads}
        raise AssertionError(name)


async def _no_sleep(_):
    return None


def run(fake, args):
    return asyncio.run(exec_command(fake, args, poll=0.5, sleep=_no_sleep))


def test_show_keeps_the_synchronous_path():
    fake = FakePT([])
    result = run(fake, {"deviceName": "DS1", "command": "show vlan brief"})
    assert result == {"success": True, "output": "show output"}
    assert [c[0] for c in fake.calls] == ["execCommand"]


def test_ping_waits_for_the_summary_and_one_grace_read():
    fake = FakePT(["Pinging 192.168.10.1\n", "Reply from 192.168.10.1\n",
                   "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n",
                   "Approximate round trip times\n", "unused\n"])
    result = run(fake, {"deviceName": "PC10", "command": "ping 192.168.10.1"})
    assert result["complete"] is True
    assert "Approximate round trip times" in result["output"]
    assert result["outputFrom"] == "events"
    assert fake.calls[0][0] == "startCommand"
    assert fake.calls[-1] == ("readCommandOutput", {"deviceName": "PC10", "finish": True})


def test_ping_without_summary_stops_at_wait_and_says_partial():
    fake = FakePT(["Pinging\n"] + [""] * 100)
    result = run(fake, {"deviceName": "PC10", "command": "ping 10.9.9.9", "waitSeconds": 3})
    assert result["complete"] is False
    assert "partial" in result["note"]
    assert result["waitedSeconds"] == 3.0


def test_pc_command_falls_back_when_ios_console_is_missing():
    fake = FakePT(["Physical Address......: 0001.42AA.0001\n"], ended_after=1,
                  exec_result={"success": False, "error":
                               "Error executing command: Property 'enterCommand' of object "
                               "[object Object] is not a function"})
    result = run(fake, {"deviceName": "PC10", "command": "ipconfig /all"})
    assert result["complete"] is True
    assert "Physical Address" in result["output"]
    assert [c[0] for c in fake.calls[:2]] == ["execCommand", "startCommand"]


def test_other_execcommand_errors_are_returned_unchanged():
    error = {"success": False, "error": "Device not found: R9"}
    fake = FakePT([], exec_result=error)
    assert run(fake, {"deviceName": "R9", "command": "show ip route"}) == error


class Enveloped(FakePT):
    """The extension wraps every answer as runCode's {success, result, code}."""

    async def __call__(self, name, args):
        inner = await super().__call__(name, args)
        return {"success": True, "result": inner, "code": "return f();"}


def test_runcode_envelope_is_unwrapped():
    fake = Enveloped(["Reply\n", "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n",
                      "Approximate round trip times\n"])
    result = run(fake, {"deviceName": "PC10", "command": "ping 192.168.10.1"})
    assert result["complete"] is True
    assert "Approximate round trip times" in result["output"]


def test_pc_fallback_sees_the_error_inside_the_envelope():
    fake = Enveloped(["IPv4 Address......: 192.168.10.10\n"], ended_after=1,
                     exec_result={"success": False, "error":
                                  "Property 'enterCommand' of object is not a function"})
    result = run(fake, {"deviceName": "PC10", "command": "ipconfig"})
    assert "IPv4 Address" in result["output"]


class Silent(FakePT):
    async def __call__(self, name, args):
        out = await super().__call__(name, args)
        if name == "readCommandOutput":
            out.update(output="", events=0)
        return out


def test_no_output_events_stop_early_with_a_clear_note():
    result = run(Silent([]), {"deviceName": "PC10", "command": "ping 192.168.10.1"})
    assert result["waitedSeconds"] == 3.0
    assert result["note"] == "no output event from the terminal"
