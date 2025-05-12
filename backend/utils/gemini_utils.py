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
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: No Gemini API key provided or found in environment")
            return []

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
            base64_encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "Analyze this clothing item and determine which occasion categories it best fits into. "
            "Choose from ONLY these categories: casual, work/professional, formal, athletic/sport, lounge/sleepwear.\n\n"

            "IMPORTANT RULES:\n"
            "1. If both 'casual' and 'lounge/sleepwear' apply, ONLY return 'lounge/sleepwear'.\n"
            "2. Do NOT mark lounge/sleepwear as casual, even if it looks comfortable. Lounge/sleepwear is for lounging and sleeping.\n"
            "3. Casual is mostly for streetwear: graphic tees, joggers, jeans, casual hoodies, sneakers.\n"
            "4. Do NOT mark the following as casual:\n"
            "   - Slacks or dress pants (work/professional, formal)\n"
            "   - Polo shirts (work/professional)\n"
            "   - Dress shoes or leather shoes (formal, work/professional)\n"
            "   - Loungewear or sleepwear\n"
            "5. Examples of casual: graphic shirt, denim jacket, jeans, joggers, sneakers, Timberland boots.\n"
            "6. Timberland boots should be tagged only as casual, NOT formal or work/professional.\n"
            "7. Slacks, chinos, or pleated pants belong under 'work/professional' or 'formal', NOT 'casual'.\n"
            "8. Jerseys, gym shorts, sweatbands = athletic/sport only.\n"
            "9. Sleepwear or loungewear = lounge/sleepwear only (e.g., sleep shirts, pajama pants).\n"
            "10. Rain coats/jackets belong under 'casual' only, NOT 'athletic/sport' or 'lounge/sleepwear'.\n"
            "11. Casual shorts belong under 'casual' only, NOT 'athletic/sport' or 'work/professional'.\n"
            "12. Joggers and Sweatpants belong under 'casual' only, NOT 'athletic/sport' or 'lounge/sleepwear'.\n\n"

            "RESPONSE FORMAT:\n"
            "- Return AT LEAST 1 occasion that best matches, or 2 if strongly appropriate.\n"
            "- Only return the occasion names, separated by a comma if there are two (e.g., 'casual, athletic/sport').\n"
            "- Do not return explanations, just the category tags.\n\n"

            "EXAMPLES:\n"
            "- Graphic T-shirt → 'casual'\n"
            "- Gray joggers → 'casual'\n"
            "- Dress pants → 'work/professional, formal'\n"
            "- Jersey → 'athletic/sport'\n"
            "- Sleep shorts → 'lounge/sleepwear'\n"
            "- Slacks → 'work/professional, formal'\n"
            "- Timberland boots → 'casual'\n"
            "- Yoga pants → 'athletic/sport, casual'\n"
            "- Polo shirt → 'work/professional'\n"
            "- Suit jacket → 'formal, work/professional'\n"
            "- Plain gray polo ralph lauren sleep shirt → 'lounge/sleepwear'\n"
            "- Jordan Retros (1s, 4s, 11s, etc.) → 'casual'\n"
            "- Hoodies → 'casual'\n"
            "- Nike dunk shoes → 'casual'\n"
            "- Nike LeBron shoes → 'athletic/sport'\n"
            "- Nike gray sweatpants → 'athletic/sport'\n"
            "- Navy rain coat/jacket → 'casual'\n"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
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

        response = requests.post(url, json=payload)
        response.raise_for_status()

        result = response.json()

        if "candidates" in result and len(result["candidates"]) > 0:
            if "content" in result["candidates"][0]:
                if "parts" in result["candidates"][0]["content"]:
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    occasions = [tag.strip().lower() for tag in text.split(",")]

                    valid_occasions = [
                        "casual", "work/professional", "formal", "athletic/sport", "lounge/sleepwear"
                    ]
                    occasions = [occ for occ in occasions if occ in valid_occasions]

                    if "casual" in occasions and "lounge/sleepwear" in occasions:
                        occasions.remove("casual")

                    return occasions[:2]

        print("Error: Could not extract valid occasion categories from Gemini API response")
        return []

    except Exception as e:
        print(f"Error analyzing image with Gemini API: {e}")
        return []
    
def categorize_clothing_item(image_path, api_key=None):
    """
    Use Google's Gemini 2.0 Flash API to categorize a clothing item into top, bottom, shoes, or accessory.
    Also identifies if a top is a "complete" top like a dress or jumpsuit,
    or if an accessory belongs to a specific subcategory.
    
    Args:
        image_path (str): Path to the image file
        api_key (str, optional): Gemini API key. If None, will try to load from env
        
    Returns:
        tuple: (category, subcategory) where:
            - category is "top", "bottom", "shoes", or "accessory"
            - subcategory is:
                - "standard" or "complete" for tops
                - "jewelry", "winter", "bags", "headwear", or "other" for accessories
                - None for others
    """
    # Get API key from environment variable if not provided
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: No Gemini API key provided or found in environment")
            return None, None
    
    # Gemini API endpoint for generating content
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    try:
        # Read and encode the image file
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
            base64_encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Prepare the request payload with precise prompt
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": "Please analyze this clothing item image and answer TWO questions:\n\n1. What category does this item belong to? Choose EXACTLY ONE: top, bottom, shoes, or accessory.\n\n2. IF the item is a top, is it a 'standard' top (shirts, t-shirts, blouses, sweaters, hoodies, jackets) that requires bottoms, OR is it a 'complete' top (dresses, jumpsuits, overalls, rompers) that doesn't require bottoms?\n\nIF the item is an accessory, what subcategory does it belong to? Choose EXACTLY ONE: jewelry (necklaces, bracelets, earrings, rings, watches), winter (scarves, gloves, beanies, earmuffs), bags (purses, backpacks, totes), headwear (hats, caps, headbands), or other (belts, sunglasses, ties).\n\nRules for categorization:\n- TOP: Any upper body garment (shirts, t-shirts, blouses, sweaters, hoodies, jackets, dresses, jumpsuits, etc.)\n- BOTTOM: Any lower body garment (pants, jeans, shorts, skirts, leggings, etc.)\n- SHOES: Any footwear (sneakers, boots, sandals, heels, slippers, etc.)\n- ACCESSORY: Any decorative or functional item worn to complement an outfit (jewelry, scarves, hats, bags, etc.)\n\nReturn your answer in this EXACT format:\nCategory: [top/bottom/shoes/accessory]\nSubcategory: [standard/complete/jewelry/winter/bags/headwear/other/none]"
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
                "temperature": 0.1,
                "maxOutputTokens": 50
            }
        }
        
        # Make the API request
        response = requests.post(url, json=payload)
        response.raise_for_status()  
        
        # Parse the response
        result = response.json()
        
        # Extract the generated text
        if "candidates" in result and len(result["candidates"]) > 0:
            if "content" in result["candidates"][0]:
                if "parts" in result["candidates"][0]["content"]:
                    text = result["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                    
                    # Parse the formatted response
                    category = None
                    subcategory = None
                    
                    lines = text.split('\n')
                    for line in lines:
                        if line.startswith('category:'):
                            category = line.split(':')[1].strip()
                        elif line.startswith('subcategory:'):
                            subcategory_value = line.split(':')[1].strip()
                            if subcategory_value != 'none':
                                subcategory = subcategory_value
                    
                    # Validate category
                    valid_categories = ["top", "bottom", "shoes", "accessory"]
                    if category in valid_categories:
                        # If it's not a top or accessory, subcategory should be None
                        if category != "top" and category != "accessory":
                            subcategory = None
                        return category, subcategory
        
        print("Error: Could not extract category from Gemini API response")
        return None, None
        
    except Exception as e:
        print(f"Error analyzing image with Gemini API: {e}")
        return None, None
