import urllib.request
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python control_led.py [on|off|toggle|red|green|blue]")
        sys.exit(1)

    action = sys.argv[1].lower()
    valid_actions = ["on", "off", "toggle", "red", "green", "blue"]
    if action not in valid_actions:
        print(f"Error: Invalid action '{sys.argv[1]}'. Choose from: {', '.join(valid_actions)}")
        sys.exit(1)

    url = "http://mcp-led.local:8080/mcp"
    protocol_version = "2025-11-25"

    # 1. Initialize session
    init_payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "clientInfo": {
                "name": "antigravity-client",
                "version": "1.0.0"
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(init_payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Mcp-Protocol-Version": protocol_version
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            headers = response.info()
            session_id = headers.get("Mcp-Session-Id")
    except Exception as e:
        print(f"Error during initialize: {e}")
        sys.exit(1)

    if not session_id:
        print("Error: No Mcp-Session-Id header returned!")
        sys.exit(1)

    # 2. Send initialized notification
    notif_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    req_notif = urllib.request.Request(
        url,
        data=json.dumps(notif_payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id,
            "Mcp-Protocol-Version": protocol_version
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req_notif) as response:
            pass
    except Exception as e:
        print(f"Warning: Error sending notification: {e}")

    # 3. Call tool led_control with the chosen action
    tool_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "led_control",
            "arguments": {
                "action": action
            }
        }
    }
    req_tool = urllib.request.Request(
        url,
        data=json.dumps(tool_payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id,
            "Mcp-Protocol-Version": protocol_version
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req_tool) as response:
            body = response.read().decode('utf-8')
            res_json = json.loads(body)
            if "result" in res_json and "content" in res_json["result"]:
                for content_item in res_json["result"]["content"]:
                    if content_item.get("type") == "text":
                        print(content_item.get("text"))
            else:
                print("Tool call executed. Response:")
                print(body)
    except Exception as e:
        print(f"Error calling tool: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
