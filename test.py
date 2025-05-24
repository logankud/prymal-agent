import subprocess
import json
import time
import threading

def log_stderr(process):
    def stream():
        for line in process.stderr:
            print("[MCP STDERR]", line.strip())
    threading.Thread(target=stream, daemon=True).start()

def main():
    print("Launching MCP server...")
    process = subprocess.Popen(
        ['npx', '-y', '@shopify/dev-mcp@latest'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    log_stderr(process)

    try:
        request = {
            "tool": "search_dev_docs",
            "input": {"query": "how to create a discount code"}
        }

        print("[DEBUG] Sending request:", request)
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()

        start = time.time()
        while True:
            if process.poll() is not None:
                raise RuntimeError("MCP server exited unexpectedly")

            if process.stdout.readable():
                line = process.stdout.readline()
                if line:
                    print("[MCP RESPONSE]", line.strip())
                    break

            if time.time() - start > 10:
                raise TimeoutError("Timed out waiting for response")
            time.sleep(0.1)

    finally:
        print("Shutting down MCP...")
        process.terminate()

if __name__ == "__main__":
    main()
