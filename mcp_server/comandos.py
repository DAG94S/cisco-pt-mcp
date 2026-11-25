"""execCommand with deferred output: ping/traceroute and PC command prompts.

``CiscoDevice.enterCommand`` returns only what the console printed at that instant, so a
ping comes back as ``"\\n"`` before its ``!!!!!`` arrive, and PCs have no ``enterCommand`` at
all (their console is ``Pc.getCommandPrompt()``). For those cases the extension exposes
``startCommand`` (subscribes to the terminal line's ``outputWritten``/``commandEnded`` events
and launches the command) and ``readCommandOutput`` (returns what has accumulated). This
module polls the latter until the command finishes.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, Awaitable, Callable

Call = Callable[[str, dict[str, Any]], Awaitable[Any]]

DEFERRED = re.compile(r"^\s*(ping|traceroute|tracert|trace)\b", re.I)
PING = re.compile(r"^\s*ping\b", re.I)
PING_DONE = re.compile(
    r"Success rate is \d+ percent"                         # IOS
    r"|Packets: Sent = \d+, Received = \d+, Lost = \d+"    # PC
)
TRACE_DONE = re.compile(r"Trace complete", re.I)
PC_WITHOUT_IOS_CONSOLE = "enterCommand"

DEFAULT_WAIT_S = 30.0
POLL_S = 0.5
GRACE_S = 1.0      # after the summary line, one more read for the trailing lines
STABLE_S = 3.0     # non-ping commands: ended and no new output for this long


def _text(read: dict[str, Any]) -> tuple[str, str]:
    """Best available output of a readCommandOutput result and where it came from."""
    events = str(read.get("output") or "")
    if events.strip():
        return events, "events"
    immediate = str(read.get("immediate") or "")
    tail = str(read.get("consoleTail") or "")
    command = str(read.get("command") or "")
    if tail.strip() and command and command in tail:
        return tail[tail.rfind(command):], "consoleTail"
    if immediate.strip():
        return immediate, "return"
    return "", "none"


async def exec_command(
    call: Call,
    args: dict[str, Any],
    *,
    poll: float = POLL_S,
    sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
) -> Any:
    command = str(args.get("command") or "")
    device = args.get("deviceName")

    if not DEFERRED.match(command):
        result = await call("execCommand", args)
        failed_on_pc = (
            isinstance(result, dict)
            and result.get("success") is False
            and PC_WITHOUT_IOS_CONSOLE in str(result.get("error", ""))
        )
        if not failed_on_pc:
            return result

    wait = float(args.get("waitSeconds") or DEFAULT_WAIT_S)
    start = await call(
        "startCommand", {"deviceName": device, "command": command, "mode": args.get("mode")}
    )
    if not (isinstance(start, dict) and start.get("success")):
        return start

    is_ping = bool(PING.match(command))
    elapsed = 0.0
    done_at: float | None = None
    last, unchanged = None, 0.0
    complete = False
    while True:
        await sleep(poll)
        elapsed += poll
        read = await call("readCommandOutput", {"deviceName": device, "finish": False})
        if not (isinstance(read, dict) and read.get("success")):
            return read
        text, _ = _text(read)
        if done_at is None and (PING_DONE.search(text) or TRACE_DONE.search(text)):
            done_at = elapsed
        unchanged = unchanged + poll if text == last else 0.0
        last = text
        if done_at is not None and elapsed - done_at >= GRACE_S:
            complete = True
            break
        if not is_ping and read.get("ended") and text.strip() and unchanged >= STABLE_S:
            complete = True
            break
        if elapsed >= wait:
            break

    final = await call("readCommandOutput", {"deviceName": device, "finish": True})
    if not (isinstance(final, dict) and final.get("success")):
        return final
    text, source = _text(final)
    result = {
        "success": True,
        "device": device,
        "command": command,
        "output": text,
        "complete": complete,
        "waitedSeconds": round(elapsed, 1),
        "terminal": final.get("terminal"),
        "outputFrom": source,
        "events": final.get("events"),
    }
    if not complete:
        result["note"] = (
            f"command did not finish within {wait:.0f}s; output may be partial"
        )
    if not text.strip():
        result["eventSample"] = final.get("eventSample")
        result["endStatus"] = final.get("endStatus")
    return result
