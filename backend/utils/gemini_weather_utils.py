# utils/gemini_weather_utils.py
import os
import base64
import requests
import json

def analyze_clothing_weather_suitability(image_path, api_key=None):
    """
    Analyze an image using Google's Gemini 2.0 Flash API to determine 
    suitable weather conditions for the clothing item.
    
    Args:
        image_path (str): Path to the image file
        api_key (str, optional): Gemini API key. If None, will try to load from env
        
    Returns:
        dict: Dictionary containing:
            - weather_conditions: list of weather conditions (sunny, cloudy, rain, snow, etc.)
            - temperature_range: list of temperature ranges (cold, cool, warm, hot)
              Returns empty lists if analysis fails
    """
    # Get API key from environment variable if not provided
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: No Gemini API key provided or found in environment")
            return {"weather_conditions": [], "temperature_range": []}
    
    # Gemini API endpoint for generating content
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    try:
        # Read and encode the image file
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
            base64_encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Prepare the request payload with improved prompt
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": """Please analyze this clothing item and determine:

                            1. What weather conditions it's suitable for (from ONLY these options: sunny, cloudy, rain, snow)
                            2. What temperature ranges it's appropriate for (from ONLY these options: cold, cool, warm, hot)

                            TEMPERATURE RANGES & DEFINITIONS:
                            - cold: 0-39°F - Heavy insulation needed
                            - cool: 40-59°F - Medium insulation needed
                            - warm: 60-79°F - Light layers appropriate
                            - hot: 80°F+ - Minimal, breathable clothing

                            SPECIFIC CLOTHING GUIDELINES:
                            - Heavy coats, parkas, thermal layers: ONLY cold temperatures and potentially snow/rain conditions
                            - Sweaters: cold to cool temperatures only
                            - Light jackets/windbreakers: cool to warm temperatures, good for cloudy/rain conditions
                            - Hoodies: ONLY cool or warm temperatures, good for sunny/cloudy/rain conditions
                            - Long-sleeve shirts: cool to warm temperatures
                            - T-shirts: ONLY warm to hot temperatures, primarily sunny/cloudy conditions
                            - Tank tops: ONLY hot temperatures, primarily sunny conditions
                            - Shorts: ONLY warm to hot temperatures
                            - Sneakers: ONLY cool to hot temperatures, ONLY sunny/cloudy/rainy conditions
                            - Snow boots: ONLY snow/rain conditions and ONLY cold and cool temperatures
                            - Dress pants/slacks: NOT appropriate for snow conditions
                            - Formal shirts/blouses: NOT appropriate for snow conditions
                            - Rain jackets/coats: ONLY for rain conditions and ONLY cool to warm temperatures, NOT cloudy/sunny conditions
                            - Rain boots: ONLY for rain conditions, good for cold-to-warm temperatures
                            - Snow jackets: Specifically for snow conditions
                            - Bomber jackets: Good for ONLY cool temperatures and for any weather condition except snow
                            - Wool/tweed coats: cold temperatures, not for rain
                            - Joggers/sweatpants: Godd for all temperature ranges and weather conditions, except hot temperature range

                            IMPORTANT RULES:
                            1. For weather conditions, choose ALL that apply from the list: sunny, cloudy, rain, snow
                            2. For temperature ranges, choose ALL that apply from the list: cold, cool, warm, hot
                            3. Format your response EXACTLY like this JSON:
                            ```json
                            {
                            "weather_conditions": ["condition1", "condition2"],
                            "temperature_range": ["range1", "range2"]
                            }
                            ```
                            4. DO NOT add any comments, explanations or additional text.
                            5. Follow the specific clothing guidelines above strictly.

                            Examples:
                            - A parka with fur hood → {"weather_conditions": ["snow", "cloudy"], "temperature_range": ["cold"]}
                            - A t-shirt → {"weather_conditions": ["sunny", "cloudy"], "temperature_range": ["warm", "hot"]}
                            - Rain boots → {"weather_conditions": ["rain"], "temperature_range": ["cold", "cool", "warm"]}
                            - Shorts → {"weather_conditions": ["sunny", "cloudy"], "temperature_range": ["warm", "hot"]}
                            - Light sweater → {"weather_conditions": ["sunny", "cloudy"], "temperature_range": ["cool"]}"""
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_encoded_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 100
            }
        }
        
        # Make the API request
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse the response
        result = response.json()
        
        # Extract the generated text
        if "candidates" in result and len(result["candidates"]) > 0:
            if "content" in result["candidates"][0]:
                if "parts" in result["candidates"][0]["content"]:
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Extract JSON from the response
                    json_start = text.find("{")
                    json_end = text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = text[json_start:json_end]
                        try:
                            data = json.loads(json_str)
                            # Validate the expected structure
                            if "weather_conditions" in data and "temperature_range" in data:
                                # Validate that returned values are from our allowed lists
                                valid_weather = ["sunny", "cloudy", "rain", "snow"]
                                valid_temps = ["cold", "cool", "warm", "hot"]
                                
                                weather_conditions = [w for w in data["weather_conditions"] if w in valid_weather]
                                temperature_range = [t for t in data["temperature_range"] if t in valid_temps]
                                
                                return {
                                    "weather_conditions": weather_conditions,
                                    "temperature_range": temperature_range
                                }
                        except json.JSONDecodeError as e:
                            print(f"Error parsing JSON from Gemini response: {e}")
        
        print("Error: Could not extract weather suitability from Gemini API response")
        return {"weather_conditions": [], "temperature_range": []}
        
    except Exception as e:
        print(f"Error analyzing image with Gemini API: {e}")
        return {"weather_conditions": [], "temperature_range": []}