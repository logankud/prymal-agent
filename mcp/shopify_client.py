
import subprocess
import json
import time
import threading
import select

class ShopifyMCPClient:
    def __init__(self):
        # Start the dev-mcp server
        self.process = subprocess.Popen(
            ['npx', '-y', '@shopify/dev-mcp@latest'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Start logging stderr
        self.log_stderr()
        
        # Wait for server ready message
        self._wait_for_server_ready()

    def _wait_for_server_ready(self):
        """Wait for the server ready message in stderr."""
        for line in self.process.stderr:
            print("[dev-mcp STDERR]", line.strip())
            if "running on stdio" in line:
                return
            
    def log_stderr(self):
        """Logs dev-mcp stderr output in the background."""
        def stream_logs():
            for line in self.process.stderr:
                print("[dev-mcp STDERR]", line.strip())

        threading.Thread(target=stream_logs, daemon=True).start()

    def call_tool(self, tool: str, input_dict: dict) -> dict:
        """Send a tool request to dev-mcp and get response."""
        if self.process.poll() is not None:
            raise RuntimeError("dev-mcp process has terminated")
            
        request = json.dumps({"tool": tool, "input": input_dict})
        print("[dev-mcp REQUEST]", request)
        
        try:
            self.process.stdin.write(request + '\n')
            self.process.stdin.flush()
        except IOError as e:
            self.process.terminate()
            raise RuntimeError(f"Failed to write to dev-mcp process: {e}")

        # Use select to wait for data with timeout
        readable, _, _ = select.select([self.process.stdout], [], [], 30.0)
        if not readable:
            self.process.terminate()
            raise TimeoutError("Timeout waiting for dev-mcp response")
            
        try:
            line = self.process.stdout.readline().strip()
            print("[dev-mcp RESPONSE]", line)
            if line:
                return json.loads(line)
            raise RuntimeError("Empty response from dev-mcp")
        except Exception as e:
            self.process.terminate()
            raise RuntimeError(f"Failed to read/parse dev-mcp response: {e}")

    def shutdown(self):
        """Terminate the MCP process."""
        self.process.terminate()
