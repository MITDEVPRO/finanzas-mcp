"""Smoke test del protocolo MCP por stdio.

Mantiene stdin del servidor abierto hasta recibir la respuesta de tools/list,
eliminando la carrera EOF-vs-respuesta que hacía flaky al smoke test en CI.
Uso: uv run python tests/smoke_mcp.py
"""

import json
import shutil
import subprocess
import sys
import threading

TOOLS_ESPERADAS = 25
TIMEOUT_S = 30


def main() -> int:
    cmd = shutil.which("finanzas-mcp")
    if not cmd:
        print("finanzas-mcp no está en PATH", file=sys.stderr)
        return 1

    proc = subprocess.Popen(
        [cmd],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    def enviar(msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    resultado: dict = {}

    def leer() -> None:
        for line in proc.stdout:
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if m.get("id") == 2:
                resultado["tools"] = m["result"]["tools"]
                return

    lector = threading.Thread(target=leer, daemon=True)
    lector.start()

    enviar({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "smoke", "version": "0"},
        },
    })
    enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
    enviar({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    lector.join(timeout=TIMEOUT_S)
    proc.stdin.close()
    proc.terminate()

    tools = resultado.get("tools")
    if tools is None:
        print(f"sin respuesta a tools/list en {TIMEOUT_S}s", file=sys.stderr)
        return 1
    print(f"{len(tools)} tools expuestas")
    return 0 if len(tools) == TOOLS_ESPERADAS else 1


if __name__ == "__main__":
    sys.exit(main())
