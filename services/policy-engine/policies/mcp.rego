package agentos.mcp

default allow = false

# Allow reading resources if authorized
allow {
    input.action == "read_resource"
    input.resource.sensitivity != "high"
}

# Allow calling tools if they are in the allowed list
allow {
    input.action == "call_tool"
    allowed_tools[input.tool.name]
}

allowed_tools = {
    "calculator",
    "search",
    "weather"
}
