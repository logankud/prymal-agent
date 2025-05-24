import subprocess
import json


def call_mcp_tool(tool: str, input_dict: dict) -> dict:
  """Send a tool request to the dev-mcp subprocess and get response."""
  request = json.dumps({"tool": tool, "input": input_dict})
  mcp_process.stdin.write(request + '\n')
  mcp_process.stdin.flush()

  # Read one line from stdout (MCP responds one line at a time)
  response_line = mcp_process.stdout.readline()
  return json.loads(response_line)

# Start the dev-mcp server
mcp_process = subprocess.Popen(
    ['npx', '-y', '@shopify/dev-mcp@latest'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,  # handles string input/output instead of bytes
    bufsize=1   # line-buffered
)
