import subprocess
import json
import uuid
import time
import threading
import sys

class ShopifyMCPClient:
    def __init__(self):
        """Launch the Dev-MCP subprocess and perform handshake."""
        # Try local installation first, then fallback to remote
        try:
            self.process = subprocess.Popen(
                ['npx', '@shopify/dev-mcp'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            # Fallback to remote installation
            self.process = subprocess.Popen(
                ['npx', '-y', '@shopify/dev-mcp@latest'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        self._log_stderr()
        self._initialize()

    def _log_stderr(self):
        """Background thread to stream stderr logs."""
        def stream():
            for line in self.process.stderr:
                # Filter out verbose response text while keeping other logs
                if "Response text (truncated)" not in line:
                    print("[dev-mcp STDERR]", line.strip(), file=sys.stderr)
        threading.Thread(target=stream, daemon=True).start()

    def _rpc(self, payload: dict) -> dict:
        """Send JSON-RPC message and wait for response."""
        if self.process.poll() is not None:
            raise RuntimeError("dev-mcp process has exited")

        self.process.stdin.write(json.dumps(payload) + '\n')
        self.process.stdin.flush()

        start = time.time()
        while True:
            if self.process.poll() is not None:
                raise RuntimeError("dev-mcp exited during response")

            line = self.process.stdout.readline()
            if line:
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    raise RuntimeError(f"Invalid JSON from dev-mcp: {line.strip()}")

            if time.time() - start > 10:
                raise TimeoutError("Timeout waiting for dev-mcp response")
            time.sleep(0.1)

    def _initialize(self):
        """Send MCP initialize message and wait for capabilities."""
        init_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "shopify-agent",
                    "version": "0.1.0"
                }
            }
        }

        response = self._rpc(init_payload)
        if response.get("error"):
            raise RuntimeError(f"Dev-MCP initialization failed: {response['error']}")

        # Optional: send initialized notification
        self.process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "initialized"
        }) + "\n")
        self.process.stdin.flush()

    def call_tool(self, tool: str, input_dict: dict) -> dict:
        """Call a registered tool via JSON-RPC."""
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": input_dict
            }
        }

        response = self._rpc(request)
        if response.get("error"):
            raise RuntimeError(f"Tool error: {response['error']}")
        return response["result"]

    def shutdown(self):
        self.process.terminate()
