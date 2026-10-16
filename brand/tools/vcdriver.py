"""Minimal stdio MCP client for VectorCraft's headless engine.

VectorCraft ships `vectorcraft-cli mcp --headless`, a Model Context Protocol server that
speaks newline-delimited JSON-RPC 2.0 on stdin/stdout. This module starts one engine
session and exposes two calls:

    VC.tool(name, **args)        an MCP tool (draw_path, export, pathfinder, ...)
    VC.cmd(command, **params)    any engine command by id (file.new, text.setStyle, ...)

Contract
--------
* Inputs: the engine's executable path (VECTORCRAFT_CLI env var or the default install
  path) and one folder that confines every file the engine may read or write.
* Outputs: the parsed JSON result of each call.
* Side effects: one child process for the life of the VC object; files written only
  inside the confined folder.
* Errors: a JSON-RPC error or a tool result flagged isError raises RuntimeError with the
  call that failed, so a broken build stops instead of producing partial assets.
"""
import json
import os
import subprocess
import time

DEFAULT_EXE = r"C:\Program Files\VectorCraft\vectorcraft-cli.exe"


MAX_PATH = 260  # Windows' classic path limit, terminating NUL included


def fresh_export(vc, path, **args):
    """Export the active document to `path` and return only once that new file is on disk.

    Use it wherever a build reads its own export back. Measured on 2026-10-16 with VectorCraft
    0.10: when the full path is 260 characters or longer, `export` reports success (with a byte
    count) but no file appears, so a read-back either fails or, on a rerun, silently reads the
    previous file. Contract: refuses such a path up front (ValueError); deletes any old file at
    `path`; exports; waits until the file exists and its size holds for 0.2 s; raises
    TimeoutError after `timeout` seconds (default 10) so a silent failure stops the build.
    """
    timeout = args.pop("timeout", 10.0)
    full = os.path.abspath(path)
    if len(full) >= MAX_PATH:
        raise ValueError(f"{len(full)}-character path; VectorCraft does not write files at "
                         f"{MAX_PATH} characters or more. Build from a shorter folder: {full}")
    if os.path.exists(path):
        os.remove(path)
    vc.tool("export", path=path, **args)
    deadline, last = time.monotonic() + timeout, -1
    while time.monotonic() < deadline:
        size = os.path.getsize(path) if os.path.exists(path) else -1
        if size > 0 and size == last:
            return path
        last = size
        time.sleep(0.2)
    raise TimeoutError(f"VectorCraft did not finish writing {path} within {timeout} s")


class VC:
    def __init__(self, root, exe=None):
        exe = exe or os.environ.get("VECTORCRAFT_CLI", DEFAULT_EXE)
        self.p = subprocess.Popen(
            [exe, "mcp", "--headless", "--automation-read-root", root, "--automation-write-root", root],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8")
        self.i = 0
        self.server = self._rpc("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "superconducted-brand", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self.i += 1
        self._send({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("VectorCraft engine exited: " + self.p.stderr.read())
            msg = json.loads(line)
            if msg.get("id") == self.i:
                break
        if "error" in msg:
            raise RuntimeError(f"{method} {params}: {msg['error']}")
        return msg["result"]

    def tool(self, name, **args):
        res = self._rpc("tools/call", {"name": name, "arguments": args})
        texts = [c["text"] for c in res.get("content", []) if c.get("type") == "text"]
        if res.get("isError"):
            raise RuntimeError(f"{name} {args}: {texts}")
        out = texts[0] if texts else None
        try:
            return json.loads(out) if out else None
        except json.JSONDecodeError:
            return out

    def cmd(self, command, **params):
        return self.tool("run_command", command=command, params=params)

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=20)
        except Exception:
            self.p.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
