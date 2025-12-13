# Tool 2: Weather-Adaptive Assistant

## Overview

This tool provides weather-based guidance for travel planning using real-time forecasts from the Open-Meteo API. It operates in two distinct modes:

1. **Packing Support**: Provides weather forecast + packing implications (no itinerary)
2. **Itinerary Adjustment**: Adjusts an existing itinerary based on weather conditions

**Critical**: This tool NEVER creates an itinerary from scratch.

## Features

- **Real-time Weather Data**: Fetches forecasts using Open-Meteo's free API (no API key required)
- **Intelligent Geocoding**: Automatically converts location names to coordinates
- **Smart Adjustments**: Uses LLM to suggest itinerary changes based on weather conditions
- **Graceful Fallback**: Provides weather-agnostic plans when API is unavailable
- **Streaming Response**: Results are streamed to the user in real-time

## When the Tool Triggers

### Mode 1: Packing Support (`purpose="packing_support"`)

Triggers when:
- User asks for packing/clothing advice
- You have location + date range
- Before generating packing lists

Output:
- Forecast snapshot (day-by-day, max 5-7 days)
- Packing implications (4-8 concrete bullet points)
- Confidence note

### Mode 2: Itinerary Adjustment (`purpose="adjust_itinerary"`)

Triggers when:
- User asks to validate/adjust plans: "Is this plan ok?", "Should we change anything?", "What if it rains?"
- You have location + date range + existing itinerary

Output:
- Forecast snapshot
- Changes made (with reasons)
- Updated itinerary (day-by-day)
- One follow-up question

### The tool does NOT trigger when:
- No dates are provided (give season-typical advice in normal chat)
- User is only brainstorming destinations without a timeframe
- User wants adjustments but no itinerary exists (ask for outline first or route to planning tool)

## Technical Details

### Runtime Context Awareness

The tool leverages **runtime context injection** to correctly interpret relative dates:
- System always knows the current date via `get_runtime_context()`
- Users can say "next week", "this weekend", etc.
- LLM converts to absolute dates (e.g., 2025-12-20)
- Weather API receives valid date parameters

See `backend/RUNTIME_CONTEXT.md` for full details.

### External APIs Used

1. **Open-Meteo Geocoding API**: 
   - Endpoint: `https://geocoding-api.open-meteo.com/v1/search`
   - Converts location names to lat/lon coordinates

2. **Open-Meteo Forecast API**:
   - Endpoint: `https://api.open-meteo.com/v1/forecast`
   - Provides 16-day weather forecasts
   - Data includes: temperature, precipitation, wind speed, weather conditions
   - Note: Only works for future dates (today and beyond)

### Weather Interpretation

The tool interprets weather codes and makes recommendations based on:

- **Rain Risk**: Precipitation > 5mm or probability > 60%
  - Suggests: Indoor attractions, covered areas, museums, cafes
  - Provides: Outdoor backups if weather improves

- **Heat**: Temperature > 30°C/86°F
  - Suggests: Outdoor activities in early morning/evening
  - Adds: Midday indoor/rest blocks

- **Cold**: Temperature < 10°C/50°F
  - Suggests: Minimize prolonged outdoor exposure
  - Recommends: Sheltered activities

- **Wind**: Speed > 40 km/h
  - Suggests: Avoid exposed areas
  - Recommends: Sheltered alternatives

### Implementation

The tool follows a two-step pipeline:

1. **API Call**: Fetch weather data from Open-Meteo
2. **LLM Synthesis**: Use GPT-4o-mini with specialized prompt to adjust itinerary

### Error Handling

If the API fails or data is unavailable:
- Tool notifies user with a warning
- Provides a robust weather-agnostic plan with both indoor and outdoor options
- Asks user to provide more specific location/dates for live forecast

## Example Usage

### Example 1: Packing Support Mode

**User**: "What should I pack for Paris, March 10-14?"

**Assistant**: Triggers Tool 2 with `purpose="packing_support"`

**Tool Output**:
```
Forecast Snapshot:
- March 10: Partly cloudy, 8-12°C, light rain possible
- March 11: Overcast, 7-11°C, 60% rain
- March 12: Mainly clear, 9-14°C
- March 13: Partly cloudy, 10-15°C
- March 14: Clear, 11-16°C

Packing Implications:
• Light waterproof jacket or packable rain shell
• Layers for cool mornings (8-10°C)
• Umbrella or compact rain gear for March 11
• Comfortable walking shoes (water-resistant preferred)
• Light sweater for evenings
• Scarf or light neck layer

Forecast can change; recheck closer to departure.
```

**Then**: Assistant uses Packing List Tool with weather context

### Example 2: Itinerary Adjustment Mode

**User**: "Here's my 3-day Rome itinerary next week—lots of walking. Anything I should change?"

**Assistant**: Triggers Tool 2 with `purpose="adjust_itinerary"`

**Tool Output**:
```
Forecast Snapshot:
- Dec 15: Clear, 8-14°C
- Dec 16: Heavy rain, 10-12°C, 80% chance
- Dec 17: Mainly clear, 7-13°C

Changes Made:
• Moved Colosseum visit from Dec 16 to Dec 15 afternoon (rain forecast)
• Scheduled Vatican Museums for Dec 16 morning (indoor)
• Added backup: Borghese Gallery if weather improves Dec 16

Updated Itinerary:
Day 1 (Dec 15): Morning - Trevi Fountain & Spanish Steps, Afternoon - Colosseum
Day 2 (Dec 16): Vatican Museums & Sistine Chapel (indoor), backup: Borghese if weather clears
Day 3 (Dec 17): Roman Forum & Palatine Hill (clear weather)

Should I suggest specific cafes or restaurants for rainy day breaks?
```

### Example 3: Missing Itinerary

**User**: "Adjust my Seattle trip for the weather, June 15-18"

**Assistant**: Triggers Tool 2 with `purpose="adjust_itinerary"` but no itinerary

**Tool Output**:
```
💡 I need an itinerary to adjust!

To adjust your travel plans based on weather, I need a rough outline of what you're planning to do.
You can provide:
- A day-by-day plan
- A list of activities you want to do
- Just the general idea of your trip

Alternatively, I can help you create a first itinerary if you'd like!
```

## Files

- `tool.py`: Main implementation with API integration and tool definition
- `README.md`: This documentation
- `__init__.py`: Package initialization
- `../../prompts/weather_itinerary.md`: LLM synthesis prompt

## Dependencies

- `requests`: For HTTP API calls to Open-Meteo
- `openai`: For LLM synthesis
- Standard library: `os`, `json`, `datetime`

## Future Enhancements

Potential improvements:
- Add caching for weather data to reduce API calls
- Support for multiple location itineraries
- Integration with more weather APIs for redundancy
- Historical weather data for past trips
- Extreme weather alerts and notifications
