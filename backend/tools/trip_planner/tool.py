"""Trip planner tool for generating day-by-day itineraries."""

import os
from backend.utils import get_openai_client, get_runtime_context

# Tool definition for OpenAI function calling
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "generate_trip_plan",
        "description": "Generate a day-by-day itinerary for a trip. Requires destination AND either duration_days OR date_range (at least one must be provided).",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The destination (city, country, or region)"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Trip duration in days. Provide this OR date_range."
                },
                "date_range": {
                    "type": "string",
                    "description": "Date range in format 'YYYY-MM-DD to YYYY-MM-DD'. Provide this OR duration_days."
                },
                "travelers_count": {
                    "type": "integer",
                    "description": "Number of travelers (optional)"
                },
                "budget_level": {
                    "type": "string",
                    "description": "Budget level: budget, mid, or luxury (optional)",
                    "enum": ["budget", "mid", "luxury"]
                },
                "trip_style": {
                    "type": "string",
                    "description": "Trip style: relaxed, balanced, or intense (optional)"
                },
                "interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of interests or activities (e.g., culture, food, nature, adventure) (optional)"
                },
                "constraints": {
                    "type": "string",
                    "description": "Any special constraints or requirements (e.g., accessibility needs, dietary restrictions) (optional)"
                }
            },
            "required": ["destination"]
        }
    }
}


def generate_trip_plan(
    destination: str,
    duration_days: int = None,
    date_range: str = None,
    travelers_count: int = None,
    budget_level: str = None,
    trip_style: str = None,
    interests: list = None,
    constraints: str = None
):
    """
    Generate a day-by-day itinerary using LLM based on trip details.
    Streams the response as it's generated.
    
    Args:
        destination: Travel destination
        duration_days: Number of days (optional if date_range provided)
        date_range: Date range string (optional if duration_days provided)
        travelers_count: Number of travelers (optional)
        budget_level: Budget level (optional)
        trip_style: Trip style/pace (optional)
        interests: List of interests (optional)
        constraints: Special requirements (optional)
    
    Yields:
        Chunks of the generated itinerary
    """
    # Load prompt from markdown file
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'trip_planner.md')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read().strip()
    
    # Build user message with trip context
    context_parts = [f"Destination: {destination}"]
    
    # Duration (prefer date_range if both provided)
    if date_range:
        context_parts.append(f"Duration: {date_range}")
    elif duration_days:
        context_parts.append(f"Duration: {duration_days} days")
    
    # Optional fields
    if travelers_count:
        context_parts.append(f"Travelers: {travelers_count}")
    if budget_level:
        context_parts.append(f"Budget: {budget_level}")
    if trip_style:
        context_parts.append(f"Style: {trip_style}")
    if interests:
        context_parts.append(f"Interests: {', '.join(interests)}")
    if constraints:
        context_parts.append(f"Constraints: {constraints}")
    
    user_message = "\n".join(context_parts)
    
    # Call LLM with streaming (inject runtime context)
    client = get_openai_client()
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": get_runtime_context()},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        stream=True
    )
    
    # Yield chunks as they come
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
