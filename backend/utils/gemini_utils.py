import os
import base64
import requests
import json

def analyze_clothing_occasion(image_path, api_key=None):
    """
    Analyze an image using Google's Gemini 2.0 Flash API to determine 
    the most appropriate occasion(s) for the clothing item.
    
    Args:
        image_path (str): Path to the image file
        api_key (str, optional): Gemini API key. If None, will try to load from env
        
    Returns:
        list: List of occasion tags (from: casual, work/professional, formal, athletic/sport, lounge/sleepwear)
              Returns empty list if analysis fails
    """
    # Get API key from environment variable if not provided
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: No Gemini API key provided or found in environment")
            return []
    
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
                            "text": "Please analyze this clothing item and determine which occasion categories it best fits into. Choose from ONLY these categories: casual, work/professional, formal, athletic/sport, lounge/sleepwear.\n\nIMPORTANT RULES:\n1. If you identify both \"casual\" and \"lounge/sleepwear\" as possible categories, ONLY return \"lounge/sleepwear\".\n2. Men's dress pants or suit pants should be categorized as \"formal\" or \"work/professional\", NOT as \"casual\".\n3. Return AT LEAST 1 category that best matches the clothing item, or 2 if absolutely necessary.\n4. Only return the category names separated by a comma if there are two (e.g., \"formal, work/professional\").\n5. Do not include any explanations or additional text in your response.\n\nExamples:\n- A blue polo shirt → \"casual, work/professional\"\n- A suit jacket → \"formal, work/professional\"\n- A t-shirt with graphic print → \"casual\"\n- Running shorts → \"athletic/sport\"\n- Sweatpants → \"casual, lounge/sleepwear\" → \"lounge/sleepwear\" (applying rule #1)\n- Pajama set → \"lounge/sleepwear\"\n- Dress pants → \"work/professional, formal\"\n- Yoga leggings → \"athletic/sport, casual\"\n- Button-down white shirt → \"casual, work/professional\"\n- Tuxedo → \"formal\""
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
                    
                    # Process the text response
                    occasions = [tag.strip().lower() for tag in text.split(",")]
                    
                    # Validate that returned occasions are from our allowed list
                    valid_occasions = ["casual", "work/professional", "formal", "athletic/sport", "lounge/sleepwear"]
                    occasions = [occ for occ in occasions if occ in valid_occasions]
                    
                    # Additional safety check: if casual and lounge are both present, remove casual
                    if "casual" in occasions and "lounge/sleepwear" in occasions:
                        occasions.remove("casual")
                    
                    # Limit to at most 2 occasions
                    return occasions[:2]
        
        print("Error: Could not extract occasions from Gemini API response")
        return []
        
    except Exception as e:
        print(f"Error analyzing image with Gemini API: {e}")
        return []