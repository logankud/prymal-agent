import subprocess, json, uuid, time, threading

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
        # Step 1: initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "0.1.0"
            }
        }

        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        init_response = process.stdout.readline().strip()
        print("Init response:", init_response)

        # Step 2: tool call
        tool_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "search_dev_docs",
                "arguments": {
                    "prompt": "fetch all orders from 2025-01-01 to 2025-01-10"
                }
            }
        }

        process.stdin.write(json.dumps(tool_request) + '\n')
        process.stdin.flush()
        tool_response = process.stdout.readline().strip()
        print("Tool response:", tool_response)

    finally:
        print("Shutting down MCP...")
        process.terminate()

if __name__ == "__main__":
    main()
