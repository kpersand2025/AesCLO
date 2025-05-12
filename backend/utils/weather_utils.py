# utils/weather_utils.py
import requests
import math

def get_weather_by_location(location, api_key):
    """
    Get weather information for a specific location using OpenWeather API
    Returns weather data including temperature and weather condition
    
    Args:
        location (str): City name or zip code
        api_key (str): OpenWeather API key
        
    Returns:
        dict: Weather data or None if request fails
    """
    try:
        # Check if the location is a US zip code
        if location.isdigit() and len(location) == 5:
            # US zip code
            url = f"https://api.openweathermap.org/data/2.5/weather?zip={location},us&appid={api_key}&units=imperial"
        else:
            # City name
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial"
            
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        weather_data = response.json()
        
        # Round temperature to nearest whole number
        if 'main' in weather_data and 'temp' in weather_data['main']:
            weather_data['main']['temp'] = round(weather_data['main']['temp'])
        
        return weather_data
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_weather_condition_by_id(weather_id):
    """
    Map OpenWeather condition ID to simplified condition name
    
    Args:
        weather_id (int): OpenWeather condition ID
        
    Returns:
        str: Simplified weather condition (sunny, cloudy, rain, snow, etc.)
    """
    # Weather ID ranges based on OpenWeather API documentation
    # https://openweathermap.org/weather-conditions
    
    # Thunderstorm
    if 200 <= weather_id < 300:
        return "rain"  # Simplify thunderstorm to rain
    
    # Drizzle and Rain
    elif 300 <= weather_id < 600:
        return "rain"
    
    # Snow
    elif 600 <= weather_id < 700:
        return "snow"
    
    # Atmosphere conditions (mist, fog, etc.)
    elif 700 <= weather_id < 800:
        return "cloudy"
    
    # Clear
    elif weather_id == 800:
        return "sunny"
    
    # Clouds
    elif 801 <= weather_id < 900:
        return "cloudy"
    
    # Default
    else:
        return "other"

def get_season_by_month(month):
    """
    Determine the season based on the month (Northern Hemisphere)
    
    Args:
        month (int): Month as number (1-12)
        
    Returns:
        str: Season name (winter, spring, summer, fall)
    """
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "fall"

def determine_outfit_type_by_weather(temp, condition):
    """
    Determine what type of outfit is appropriate based on temperature and weather condition
    Using updated temperature ranges:
    - Cold: 0-39°F - Heavy insulation needed
    - Cool: 40-59°F - Medium insulation needed
    - Warm: 60-79°F - Light layers appropriate
    - Hot: 80+°F - Minimal, breathable clothing
    
    Args:
        temp (float): Temperature in Fahrenheit
        condition (str): Weather condition (sunny, cloudy, rain, snow, etc.)
        
    Returns:
        dict: Dictionary with recommended outfit characteristics
    """
    outfit_type = {
        "temp_range": "",
        "layers": 0,
        "characteristics": []
    }
    
    # Determine temperature range using the updated ranges
    if temp <= 39:
        outfit_type["temp_range"] = "cold"
        outfit_type["layers"] = 3
        outfit_type["characteristics"] = ["warm", "insulated", "layered"]
    elif temp <= 59:
        outfit_type["temp_range"] = "cool"
        outfit_type["layers"] = 2
        outfit_type["characteristics"] = ["warm", "light layered"]
    elif temp <= 79:
        outfit_type["temp_range"] = "warm"
        outfit_type["layers"] = 1
        outfit_type["characteristics"] = ["comfortable", "breathable"]
    else:  # temp >= 80
        outfit_type["temp_range"] = "hot"
        outfit_type["layers"] = 1
        outfit_type["characteristics"] = ["light", "breathable", "loose"]
    
    # Add condition-specific characteristics
    if condition == "rain":
        outfit_type["characteristics"].extend(["waterproof", "rain-appropriate"])
    elif condition == "snow":
        outfit_type["characteristics"].extend(["snow-appropriate", "waterproof", "insulated"])
    elif condition == "sunny" and temp >= 80:
        outfit_type["characteristics"].extend(["sun-protective", "light-colored"])
    elif condition == "cloudy" and temp <= 59:
        outfit_type["characteristics"].append("windproof")
    
    return outfit_type