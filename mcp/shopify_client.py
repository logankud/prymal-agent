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
        try:
            self.process.stdin.write(request + '\n')
            self.process.stdin.flush()
        except IOError as e:
            self.process.terminate()
            raise RuntimeError(f"Failed to write to dev-mcp process: {e}")

        # Add timeout to prevent hanging
        start_time = time.time()
        while True:
            if self.process.poll() is not None:
                raise RuntimeError("dev-mcp process exited unexpectedly.")

            try:
                if self.process.stdout.readable():
                    line = self.process.stdout.readline().strip()
                    if line:
                        try:
                            return json.loads(line)
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid JSON received: {line}")
                            continue
            except IOError as e:
                raise RuntimeError(f"Failed to read from dev-mcp process: {e}")

            if time.time() - start_time > 15:  # Increased timeout
                self.process.terminate()
                raise TimeoutError("Timeout waiting for dev-mcp response")

            time.sleep(0.1)

    def shutdown(self):
        self.process.terminate()
