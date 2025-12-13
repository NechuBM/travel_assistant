"""Weather-adaptive itinerary adjuster tool for travel planning."""

import os
import requests
from datetime import datetime
from backend.utils import get_openai_client, get_runtime_context

# Tool definition for OpenAI function calling
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_weather_forecast",
        "description": "Fetch and summarize weather forecast for a location and date range. Use when user asks about weather, OR when user asks what to wear/pack AND location + dates are known.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location (city and country, e.g., 'Rome, Italy')"
                },
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["start", "end"],
                    "description": "Date range for the weather forecast"
                },
                "units": {
                    "type": "string",
                    "enum": ["C", "F"],
                    "description": "Temperature units (Celsius or Fahrenheit)",
                    "default": "C"
                }
            },
            "required": ["location", "date_range"]
        }
    }
}


def geocode_location(location: str):
    """
    Geocode a location to get latitude and longitude using Open-Meteo's geocoding API.
    
    Args:
        location: Location string (e.g., "Rome, Italy")
    
    Returns:
        Dictionary with lat, lon, and formatted location name, or None if failed
    """
    try:
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        response = requests.get(geocoding_url, params={"name": location, "count": 1, "language": "en"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results"):
            result = data["results"][0]
            return {
                "lat": result["latitude"],
                "lon": result["longitude"],
                "name": result["name"],
                "country": result.get("country", ""),
                "formatted": f"{result['name']}, {result.get('country', '')}"
            }
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def fetch_weather_forecast(lat: float, lon: float, start_date: str, end_date: str, units: str = "C"):
    """
    Fetch weather forecast from Open-Meteo API.
    Note: Free API provides forecasts up to 7-16 days ahead depending on variables.
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        units: Temperature units ("C" or "F")
    
    Returns:
        Dictionary with daily weather data, or None if failed
    """
    try:
        from datetime import datetime, timedelta, date
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        today = date.today()
        
        # Calculate days ahead
        days_until_start = (start - today).days
        days_until_end = (end - today).days
        
        # Open-Meteo free API limits: 
        # - Can forecast up to ~7-16 days ahead (varies by model/date)
        # - For past dates, need to use historical API (not implemented here)
        # - Use conservative 14-day limit to avoid API errors
        MAX_FORECAST_DAYS = 14
        
        if days_until_end < 0:
            print(f"Weather API: Cannot fetch forecast for past dates (end date: {end_date})")
            return None
        
        if days_until_start > MAX_FORECAST_DAYS:
            print(f"Weather API: Start date {start_date} is too far in future (max {MAX_FORECAST_DAYS} days ahead)")
            return None
        
        # Adjust end date if it exceeds the forecast limit
        max_forecast_date = today + timedelta(days=MAX_FORECAST_DAYS)
        date_adjusted = False
        original_end_date = end_date
        
        if end > max_forecast_date:
            end_date = max_forecast_date.strftime("%Y-%m-%d")
            date_adjusted = True
            print(f"Weather API: Adjusting end date from {original_end_date} to {end_date} ({MAX_FORECAST_DAYS}-day forecast limit)")
            end = max_forecast_date
        
        weather_url = "https://api.open-meteo.com/v1/forecast"
        temp_unit = "fahrenheit" if units == "F" else "celsius"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code",
            "temperature_unit": temp_unit,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": "auto"
        }
        
        response = requests.get(weather_url, params=params, timeout=10)
        
        # Check response status and get detailed error if it fails
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get('reason', 'Unknown error')
                print(f"Weather API error ({response.status_code}): {error_msg}")
                print(f"Full error response: {error_data}")
            except:
                print(f"Weather API error: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        
        # Format the daily data into a more readable structure
        daily = data.get("daily", {})
        forecast_days = []
        
        for i in range(len(daily.get("time", []))):
            weather_code = daily["weather_code"][i]
            day_data = {
                "date": daily["time"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "precipitation": daily["precipitation_sum"][i],
                "precipitation_prob": daily["precipitation_probability_max"][i],
                "wind_speed": daily["wind_speed_10m_max"][i],
                "weather_code": weather_code,
                "condition": _interpret_weather_code(weather_code),
                "units": units
            }
            forecast_days.append(day_data)
        
        return {
            "days": forecast_days,
            "timezone": data.get("timezone", ""),
            "units": units,
            "date_adjusted": date_adjusted,
            "original_end_date": original_end_date if date_adjusted else None
        }
    except requests.exceptions.RequestException as e:
        print(f"Weather API request error: {e}")
        return None
    except Exception as e:
        print(f"Weather API processing error: {e}")
        return None


def _interpret_weather_code(code: int) -> str:
    """Interpret WMO weather codes into readable conditions."""
    code_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return code_map.get(code, "Unknown")


def format_weather_summary(forecast_data: dict) -> str:
    """Format weather data into a readable summary for the LLM."""
    if not forecast_data:
        return "Weather forecast unavailable."
    
    summary_lines = []
    for day in forecast_data["days"]:
        units_symbol = "°F" if day["units"] == "F" else "°C"
        summary_lines.append(
            f"{day['date']}: {day['condition']}, {day['temp_min']}-{day['temp_max']}{units_symbol}, "
            f"Precip: {day['precipitation']}mm ({day['precipitation_prob']}% chance), "
            f"Wind: {day['wind_speed']} km/h"
        )
    
    return "\n".join(summary_lines)


def get_weather_forecast(
    location: str,
    date_range: dict,
    units: str = "C"
):
    """
    Fetch and summarize weather forecast for a location and date range.
    Returns a concise, human-readable forecast summary.
    
    Args:
        location: Travel location
        date_range: Dictionary with 'start' and 'end' dates
        units: Temperature units (C or F, default C)
    
    Yields:
        Chunks of the weather forecast summary
    """
    # Load prompt from markdown file
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'weather_itinerary.md')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read().strip()
    
    # Try to geocode and fetch weather
    geo_data = geocode_location(location)
    forecast_data = None
    error_reason = None
    
    # Check if geocoding failed
    if not geo_data:
        error_reason = "location_not_found"
    else:
        # Check date constraints before fetching weather
        from datetime import datetime, date
        try:
            start = datetime.strptime(date_range["start"], "%Y-%m-%d").date()
            end = datetime.strptime(date_range["end"], "%Y-%m-%d").date()
            today = date.today()
            
            days_until_start = (start - today).days
            days_until_end = (end - today).days
            
            # Check for past dates
            if days_until_end < 0:
                error_reason = "past_dates"
            # Check if start date is too far in the future
            elif days_until_start > 14:
                error_reason = "too_far_future"
            else:
                # Dates are valid, try to fetch weather
                forecast_data = fetch_weather_forecast(
                    geo_data["lat"],
                    geo_data["lon"],
                    date_range["start"],
                    date_range["end"],
                    units
                )
                # If still None, it's an API error
                if not forecast_data:
                    error_reason = "api_error"
        except ValueError:
            error_reason = "invalid_date_format"
    
    # Build user message for LLM
    if forecast_data:
        # Success: we have weather data
        # Check if dates were adjusted
        if forecast_data.get("date_adjusted"):
            yield f"\n📅 **Note**: Weather forecast limited to 14 days ahead. Showing forecast through {forecast_data['days'][-1]['date']} (original request: {forecast_data['original_end_date']}).\n\n"
        
        user_message = f"""Location: {geo_data['formatted']}
Date Range: {date_range['start']} to {date_range['end']}

Weather Data:
{format_weather_summary(forecast_data)}"""
        
    else:
        # Provide specific error message based on the reason
        if error_reason == "location_not_found":
            yield f"\n⚠️ **Weather forecast unavailable** - I couldn't find the location '{location}'. Please try a different city name or include the country (e.g., 'Paris, France').\n\n"
        elif error_reason == "past_dates":
            yield f"\n⚠️ **Weather forecast unavailable** - The dates you requested ({date_range['start']} to {date_range['end']}) are in the past. I can only provide forecasts for current and future dates.\n\n"
        elif error_reason == "too_far_future":
            yield f"\n⚠️ **Weather forecast unavailable** - The start date ({date_range['start']}) is too far in the future. I can only provide weather forecasts up to **14 days** ahead. Please try dates closer to today.\n\n"
        elif error_reason == "invalid_date_format":
            yield f"\n⚠️ **Weather forecast unavailable** - Invalid date format. Dates should be in YYYY-MM-DD format.\n\n"
        else:
            # Generic API error
            yield f"\n⚠️ **Weather forecast unavailable** - I couldn't fetch live weather data for {location}. This might be a temporary API issue. Please try again later.\n\n"
        return
    
    # Call LLM with streaming to format the weather nicely
    client = get_openai_client()
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": get_runtime_context()},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,  # Lower temperature for consistent formatting
        stream=True
    )
    
    # Yield chunks as they come
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
