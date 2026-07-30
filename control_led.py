import urllib.request
import json
import sys

def fetch_tools_list(url, session_id, protocol_version, req_id=1):
    tool_list_payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "tools/list",
        "params": {}
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(tool_list_payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id,
            "Mcp-Protocol-Version": protocol_version
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            res_json = json.loads(body)
            print("Available Tools (tools/list):")
            if "result" in res_json and "tools" in res_json["result"]:
                tools = res_json["result"]["tools"]
                if not tools:
                    print("  No tools registered on server.")
                for tool in tools:
                    name = tool.get("name", "Unknown")
                    desc = tool.get("description", "")
                    print(f"  - {name}: {desc}")
                    schema = tool.get("inputSchema")
                    if schema:
                        print(f"    Schema: {json.dumps(schema)}")
            else:
                print(json.dumps(res_json, indent=2))
    except Exception as e:
        print(f"Error fetching tools list: {e}")
        sys.exit(1)

def main():
    valid_actions = ["on", "off", "toggle", "red", "green", "blue", "list"]
    flag_aliases = ["--list-tools", "--list", "-l"]

    list_tools_flag = False
    args = []
    for arg in sys.argv[1:]:
        if arg in flag_aliases:
            list_tools_flag = True
        else:
            args.append(arg)

    if not list_tools_flag and len(args) == 0:
        print("Usage: python control_led.py [on|off|toggle|red|green|blue|list] [mdns] [port] [--list-tools]")
        sys.exit(1)

    action = None
    mdns = "mcp-led"
    port = "8080"

    if len(args) > 0:
        first_arg = args[0].lower()
        if first_arg in valid_actions:
            action = first_arg
            mdns = args[1] if len(args) > 1 else "mcp-led"
            port = args[2] if len(args) > 2 else "8080"
        elif list_tools_flag:
            mdns = args[0]
            port = args[1] if len(args) > 1 else "8080"
        else:
            print(f"Error: Invalid action '{args[0]}'. Choose from: {', '.join(valid_actions)} (or use --list-tools)")
            sys.exit(1)

    url = f"http://{mdns}.local:{port}/mcp"

    # protocol_version = "2025-11-25"

    # 1. Initialize session
    init_payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            # "protocolVersion": protocol_version,
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
            # "Mcp-Protocol-Version": protocol_version
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read().decode('utf-8'))
            protocol_version = body["result"]["protocolVersion"]
            headers = response.info()
            session_id = headers.get("Mcp-Session-Id")
    except Exception as e:
        print(f"Error during initialize: {e}")
        sys.exit(1)

    if not session_id:
        print("Error: No Mcp-Session-Id header returned!")
        sys.exit(1)

    print("Protocol Version: ",protocol_version)

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

    req_id = 1

    # 3. Fetch tools list if action is 'list' or --list-tools flag is set
    if action == "list" or list_tools_flag:
        fetch_tools_list(url, session_id, protocol_version, req_id=req_id)
        req_id += 1

    # 4. Call tool led_control if action is a standard LED action (not 'list' or None)
    if action and action != "list":
        tool_payload = {
            "jsonrpc": "2.0",
            "id": req_id,
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
