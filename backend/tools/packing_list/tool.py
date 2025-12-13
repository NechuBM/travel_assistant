"""Packing list generation tool for travel planning."""

import os
from backend.utils import get_openai_client

# Tool definition for OpenAI function calling
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "generate_packing_list",
        "description": "Generate a packing list for a destination based on trip details",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The destination (city, country, or region)"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Trip duration in days"
                },
                "activities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of planned activities (e.g., hiking, beach, business)"
                },
                "season": {
                    "type": "string",
                    "description": "Season or month of travel"
                }
            },
            "required": ["destination"]
        }
    }
}


def generate_packing_list(destination: str, duration_days: int = None, activities: list = None, season: str = None):
    """
    Generate a packing list using LLM based on destination and trip details.
    Streams the response as it's generated.
    
    Args:
        destination: Travel destination
        duration_days: Number of days (optional)
        activities: List of activities (optional)
        season: Season of travel (optional)
    
    Yields:
        Chunks of the generated packing list
    """
    # Load prompt from markdown file
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'packing_list.md')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read().strip()
    
    # Build user message with trip context
    context_parts = [f"Destination: {destination}"]
    if duration_days:
        context_parts.append(f"Duration: {duration_days} days")
    if activities:
        context_parts.append(f"Activities: {', '.join(activities)}")
    if season:
        context_parts.append(f"Season: {season}")
    
    user_message = "\n".join(context_parts)
    
    # Call LLM with streaming
    client = get_openai_client()
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        stream=True
    )
    
    # Yield chunks as they come
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
