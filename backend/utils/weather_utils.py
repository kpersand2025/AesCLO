# utils/weather_utils.py
import requests
import math

def get_weather_data(city_name, api_key):
    """
    Get current weather data from OpenWeatherMap API
    
    Args:
        city_name (str): Name of the city to get weather for
        api_key (str): OpenWeatherMap API key
        
    Returns:
        dict: Weather data or None if request failed
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "imperial"  # For temperature in Fahrenheit
    }
    
    try:
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # Round temperature to nearest whole number
            if "main" in weather_data and "temp" in weather_data["main"]:
                weather_data["main"]["temp"] = round(weather_data["main"]["temp"])
                
            return weather_data
        else:
            print(f"Error getting weather data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during weather API call: {e}")
        return None

def categorize_weather(weather_data):
    """
    Categorize weather data into temperature range and conditions
    
    Args:
        weather_data (dict): Weather data from OpenWeatherMap API
        
    Returns:
        dict: Categorized weather data
    """
    if not weather_data or "main" not in weather_data:
        return None
    
    temp = weather_data["main"]["temp"]
    conditions = weather_data["weather"][0]["main"].lower()
    
    # Categorize temperature
    if temp < 50:
        temp_category = "cold"
    elif temp < 65:
        temp_category = "cool"
    elif temp < 75:
        temp_category = "mild"
    elif temp < 85:
        temp_category = "warm"
    else:
        temp_category = "hot"
    
    # Simplify weather conditions
    if conditions in ["thunderstorm", "drizzle", "rain"]:
        weather_condition = "rainy"
    elif conditions == "snow":
        weather_condition = "snowy"
    elif conditions == "clear":
        weather_condition = "sunny"
    elif conditions in ["clouds", "mist", "smoke", "haze", "dust", "fog"]:
        weather_condition = "cloudy"
    else:
        weather_condition = "normal"  # Default case
    
    # Check if it's windy
    is_windy = False
    if "wind" in weather_data and "speed" in weather_data["wind"]:
        if weather_data["wind"]["speed"] > 15:  # Wind speed greater than 15 mph
            is_windy = True
            
    return {
        "temperature": temp,
        "temp_category": temp_category,
        "weather_condition": weather_condition,
        "is_windy": is_windy,
        "original_condition": conditions
    }