"""Tools package for OpenAI function calling."""

from backend.tools.packing_list.tool import TOOL_DEFINITION as PACKING_LIST_TOOL, generate_packing_list
from backend.tools.weather_itinerary.tool import TOOL_DEFINITION as WEATHER_TOOL, get_weather_forecast
from backend.tools.trip_planner.tool import TOOL_DEFINITION as TRIP_PLANNER_TOOL, generate_trip_plan

# Export all available tools
AVAILABLE_TOOLS = [
    PACKING_LIST_TOOL,
    WEATHER_TOOL,
    TRIP_PLANNER_TOOL
]

# Map function names to implementations
TOOL_FUNCTIONS = {
    "generate_packing_list": generate_packing_list,
    "get_weather_forecast": get_weather_forecast,
    "generate_trip_plan": generate_trip_plan
}
