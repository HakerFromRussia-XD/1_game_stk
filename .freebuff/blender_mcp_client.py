#!/usr/bin/env python3
"""Client for the blender-mcp addon socket server (localhost:9876 by default).

The addon accepts one JSON request per TCP connection:
  {"type": "<command>", "params": {...}}
and answers with a single JSON line:
  {"status": "success"|"error", "result": ... } | {"status":"error","message":"..."}

Usage:
  python3 blender_mcp_client.py scene                     # get_scene_info
  python3 blender_mcp_client.py object <name>             # get_object_info
  python3 blender_mcp_client.py viewport [--out shot.png] # screenshot to project file
  python3 blender_mcp_client.py code  '<python>'          # execute arbitrary bpy code
  python3 blender_mcp_client.py file  script.py [arg ...] # run a .py file: its body gets
                                                          #   exec'd inside Blender; `argv`
                                                          #   variable holds the args
  python3 blender_mcp_client.py call  <type> '<json params>'   # raw command
"""
import json
import os
import socket
import sys
import base64

HOST = "127.0.0.1"
PORT = int(os.environ.get("BLENDER_MCP_PORT", "9876"))


def call(cmd_type, params=None, timeout=120.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((HOST, PORT))
        s.sendall(json.dumps({"type": cmd_type, "params": params or {}}).encode())
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                json.loads(data.decode())
                break  # complete JSON object received
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue  # keep reading
        return json.loads(data.decode())
    finally:
        s.close()


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        sys.exit(1)
    cmd = argv[0]

    if cmd == "scene":
        resp = call("get_scene_info")
    elif cmd == "object":
        resp = call("get_object_info", {"name": argv[1]})
    elif cmd == "viewport":
        out = argv[argv.index("--out") + 1] if "--out" in argv else "blender_viewport.png"
        # The addon resolves relative paths against Blender's cwd, not ours.
        out = os.path.abspath(out)
        resp = call("get_viewport_screenshot", {"max_size": 800, "filepath": out, "format": "png"}, timeout=180)
    elif cmd == "code":
        resp = call("execute_code", {"code": argv[1]}, timeout=600)
    elif cmd == "file":
        path = argv[1]
        args = argv[2:]
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        payload = (
            "import json,sys\n"
            f"argv = json.loads({json.dumps(json.dumps(args))})\n"
            "import traceback\n"
            "try:\n"
            f"    exec(compile({json.dumps(src)}, {json.dumps(path)}, 'exec'), {{'__name__': '__main__', 'argv': argv}})\n"
            "    print('SCRIPT_OK')\n"
            "except Exception:\n"
            "    print('SCRIPT_FAIL'); traceback.print_exc()\n"
        )
        resp = call("execute_code", {"code": payload}, timeout=3600)
    elif cmd == "call":
        resp = call(argv[1], json.loads(argv[2]) if len(argv) > 2 else {}, timeout=600)
    else:
        print(f"unknown command: {cmd}\n{__doc__}")
        sys.exit(2)

    out = json.dumps(resp, ensure_ascii=False, indent=2)
    # Keep terminal output readable: truncate very large results.
    if len(out) > 12000:
        print(out[:12000] + f"\n... [truncated, total {len(out)} chars]")
    else:
        print(out)
    sys.exit(0 if resp.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
