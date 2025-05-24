import subprocess
import json
import time
import threading

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

    def log_stderr(self):
        """Logs dev-mcp stderr output in the background."""
        def stream_logs():
            for line in self.process.stderr:
                print("[dev-mcp STDERR]", line.strip())

        threading.Thread(target=stream_logs, daemon=True).start()

    def call_tool(self, tool: str, input_dict: dict) -> dict:
        request = json.dumps({"tool": tool, "input": input_dict})
        self.process.stdin.write(request + '\n')
        self.process.stdin.flush()

        # Add timeout to prevent hanging
        start_time = time.time()
        while True:
            if self.process.poll() is not None:
                raise RuntimeError("dev-mcp process exited unexpectedly.")

            if self.process.stdout.readable():
                line = self.process.stdout.readline()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON from dev-mcp: {line}")

            if time.time() - start_time > 10:
                raise TimeoutError("Timeout waiting for dev-mcp response.")

            time.sleep(0.1)

    def shutdown(self):
        self.process.terminate()
