"""
Custom Weather Tool for Tool Chat Example using Open-Meteo API
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any

from agentx.tool.base import Tool
from agentx.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherTool(Tool):
    """Custom weather tool using the free Open-Meteo API (no API key required)."""
    
    def __init__(self):
        super().__init__()
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        logger.info("Custom Weather Tool initialized with Open-Meteo API")
        
    async def get_weather(self, location: str) -> str:
        """
        Get tomorrow's weather forecast for a specific location using Open-Meteo API.
        
        Args:
            location: The city and state/country, e.g., "San Francisco, CA" or "Paris, France".
            
        Returns:
            A formatted string containing tomorrow's weather forecast.
        """
        try:
            # Get coordinates for the location
            coordinates = await self._get_coordinates(location)
            if not coordinates:
                return f"Sorry, I couldn't find the location '{location}'. Please try a more specific location name."
            
            # Get weather forecast
            weather_data = await self._get_weather_forecast(coordinates)
            if not weather_data:
                return f"Sorry, I couldn't get the weather forecast for {location}. Please try again later."
            
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_date = tomorrow.strftime("%B %d, %Y")
            
            return self._format_weather_response(location, tomorrow_date, weather_data, coordinates)
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return f"Sorry, I encountered an error getting the weather forecast for {location}. Error: {str(e)}"
    
    async def _get_coordinates(self, location: str) -> Dict[str, Any]:
        """Get latitude and longitude for a location using Open-Meteo Geocoding API."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
                
                async with session.get(self.geocoding_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results") and len(data["results"]) > 0:
                            result = data["results"][0]
                            return {
                                "latitude": result["latitude"],
                                "longitude": result["longitude"],
                                "name": result["name"],
                                "country": result.get("country", ""),
                                "admin1": result.get("admin1", "")  # state/province
                            }
                    return None
        except Exception as e:
            logger.error(f"Error getting coordinates for {location}: {e}")
            return None
    
    async def _get_weather_forecast(self, coordinates: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather forecast using Open-Meteo API."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                    "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant",
                    "timezone": "auto",
                    "forecast_days": 2  # today and tomorrow
                }
                
                async with session.get(self.weather_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("daily") and len(data["daily"]["time"]) >= 2:
                            # Get tomorrow's data (index 1)
                            daily = data["daily"]
                            return {
                                "date": daily["time"][1],
                                "temp_max": daily["temperature_2m_max"][1],
                                "temp_min": daily["temperature_2m_min"][1],
                                "weather_code": daily["weathercode"][1],
                                "precipitation": daily["precipitation_sum"][1],
                                "wind_speed": daily["windspeed_10m_max"][1],
                                "wind_direction": daily["winddirection_10m_dominant"][1],
                                "timezone": data.get("timezone", "UTC")
                            }
                    return None
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None
    
    def _get_weather_description(self, weather_code: int) -> str:
        """Convert WMO weather code to human-readable description."""
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
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
        return weather_codes.get(weather_code, f"Unknown weather (code: {weather_code})")
    
    def _get_wind_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _format_weather_response(self, location: str, date: str, weather: Dict[str, Any], coordinates: Dict[str, Any]) -> str:
        """Format weather data into a readable response."""
        location_name = coordinates["name"]
        if coordinates.get("admin1"):
            location_name += f", {coordinates['admin1']}"
        if coordinates.get("country"):
            location_name += f", {coordinates['country']}"
        
        temp_max_f = round(weather["temp_max"] * 9/5 + 32)  # Convert C to F
        temp_min_f = round(weather["temp_min"] * 9/5 + 32)
        
        weather_desc = self._get_weather_description(weather["weather_code"])
        wind_dir = self._get_wind_direction(weather["wind_direction"])
        wind_speed_mph = round(weather["wind_speed"] * 0.621371)  # Convert km/h to mph
        precipitation_in = round(weather["precipitation"] * 0.0393701, 2)  # Convert mm to inches
        
        response = f"""Tomorrow's Weather Forecast for {location_name} ({date}):

🌡️ Temperature: High {temp_max_f}°F ({weather['temp_max']:.1f}°C), Low {temp_min_f}°F ({weather['temp_min']:.1f}°C)
☁️ Conditions: {weather_desc}
🌧️ Precipitation: {precipitation_in}" ({weather['precipitation']:.1f}mm)
💨 Wind: {wind_speed_mph} mph ({weather['wind_speed']:.1f} km/h) from the {wind_dir}
📍 Location: {coordinates['latitude']:.2f}°N, {coordinates['longitude']:.2f}°E

Weather data provided by Open-Meteo API (open-meteo.com)"""

        return response 