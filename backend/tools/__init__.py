"""Tools package for OpenAI function calling."""

from backend.tools.packing_list.tool import TOOL_DEFINITION as PACKING_LIST_TOOL, generate_packing_list

# Export all available tools
AVAILABLE_TOOLS = [
    PACKING_LIST_TOOL
]

# Map function names to implementations
TOOL_FUNCTIONS = {
    "generate_packing_list": generate_packing_list
}
