# utils/outfit_generator.py
import random
from utils.color_utils import calculate_color_match_score, is_neutral_color, get_matching_colors

def has_color(item, color_name):
    """
    Enhanced function to check if an item has a specific color
    Returns True if the item has the color, False otherwise
    """
    if 'colors' not in item or not item['colors']:
        return False
    
    # Check each color in the item
    for color_data in item['colors']:
        if color_data['name'].lower() == color_name.lower():
            # If it's an exact match, return highest likelihood
            return True
    
    # If we didn't find an exact match, check if any of the item's colors match with this color
    for color_data in item['colors']:
        item_color = color_data['name'].lower()
        # Check if the target color is in the list of colors that match with the item's color
        if color_name.lower() in get_matching_colors(item_color):
            return True
    
    return False

def generate_color_coordinated_outfit(tops, bottoms, shoes, base_color=None):
    """
    Generate a color-coordinated outfit from the given items
    If base_color is provided, ALWAYS include a top with that color
    Returns a tuple of (top, bottom, shoes) or (None, None, None) if no match
    """
    if not tops or not bottoms or not shoes:
        return None, None, None
    
    # If base color is provided, ensure the top has that color
    if base_color:
        # Find tops that match the selected base color
        matching_tops = [item for item in tops if has_color(item, base_color)]
        
        # If no tops with the selected color, return None
        if not matching_tops:
            return None, None, None
        
        # Select a random top with the selected color
        selected_top = random.choice(matching_tops)
        
        # Find matching bottoms based on the selected top
        scored_bottoms = []
        for bottom in bottoms:
            score = calculate_color_match_score(selected_top, bottom)
            scored_bottoms.append((bottom, score))
        
        # Sort by score and get top matches
        scored_bottoms.sort(key=lambda x: x[1], reverse=True)
        top_bottoms = scored_bottoms[:min(3, len(scored_bottoms))]
        best_bottom = random.choices(
            [item[0] for item in top_bottoms], 
            weights=[item[1] for item in top_bottoms],
            k=1
        )[0]
        
        # Categorize shoes by color priority
        selected_color_shoes = []
        neutral_shoes = []
        other_shoes = []
        
        # Define neutral colors
        neutral_colors = ["black", "white", "gray", "beige", "brown"]
        
        # Categorize shoes
        for shoe in shoes:
            if 'colors' in shoe and shoe['colors']:
                # Get the most prevalent color (first in the list)
                predominant_color = shoe['colors'][0]['name'].lower() if shoe['colors'] else None
                
                # Check if any of the shoe's colors match the selected color
                has_selected_color = any(color_data['name'].lower() == base_color.lower() for color_data in shoe['colors'])
                
                # Check if the shoe's PREDOMINANT color is neutral
                is_predominant_neutral = predominant_color in neutral_colors
                
                if has_selected_color:
                    selected_color_shoes.append(shoe)
                elif is_predominant_neutral:
                    neutral_shoes.append(shoe)
                else:
                    other_shoes.append(shoe)
            else:
                other_shoes.append(shoe)
        
        # Create a weighted pool of candidate shoes
        candidate_shoes = []

        # Only apply weighted selection if we have both selected color and neutral shoes
        if selected_color_shoes and neutral_shoes:
            # 70% chance for selected color shoes, 30% chance for neutral shoes
            shoe_group_selector = random.random()
            
            if shoe_group_selector < 0.85:
                candidate_shoes = selected_color_shoes
            else:
                candidate_shoes = neutral_shoes
        else:
            # If we don't have both categories, use what we have
            if selected_color_shoes:
                candidate_shoes = selected_color_shoes
            elif neutral_shoes:
                candidate_shoes = neutral_shoes
            else:
                candidate_shoes = other_shoes

        # If we somehow have no candidate shoes, use all shoes
        if not candidate_shoes:
            candidate_shoes = shoes
        
        # Calculate scores for the candidate shoes
        scored_shoes = []
        for shoe in candidate_shoes:
            top_score = calculate_color_match_score(selected_top, shoe)
            bottom_score = calculate_color_match_score(best_bottom, shoe)
            
            # If the shoe has the selected color, give it a bonus (smaller now)
            bonus = 0.05 if any(color_data['name'].lower() == base_color.lower() for color_data in shoe.get('colors', [])) else 0
            
            # Calculate average score with bonus
            avg_score = (top_score + bottom_score) / 2 + bonus
            scored_shoes.append((shoe, avg_score))
        
        # Sort by score and get top matches
        scored_shoes.sort(key=lambda x: x[1], reverse=True)
        top_shoes = scored_shoes[:min(3, len(scored_shoes))]
        best_shoe = random.choices(
            [item[0] for item in top_shoes], 
            weights=[item[1] for item in top_shoes],
            k=1
        )[0]
        
        return selected_top, best_bottom, best_shoe
    
    # Default flow if no base color provided
    base_item = random.choice(tops)
    best_bottom, best_shoe = select_matching_items(base_item, bottoms, shoes)
    
    return base_item, best_bottom, best_shoe

def select_matching_items(base_item, item_list1, item_list2):
    """
    Select items from item_list1 and item_list2 that match well with the base_item
    Returns a tuple of (best_item1, best_item2)
    """
    # Find matching items for the first list
    scored_items1 = []
    for item in item_list1:
        score = calculate_color_match_score(base_item, item)
        scored_items1.append((item, score))
    
    # Sort by score and get top matches
    scored_items1.sort(key=lambda x: x[1], reverse=True)
    top_items1 = scored_items1[:min(3, len(scored_items1))]
    best_item1 = random.choices(
        [item[0] for item in top_items1], 
        weights=[item[1] for item in top_items1],
        k=1
    )[0]
    
    # Find matching items for the second list
    scored_items2 = []
    for item in item_list2:
        # Consider match with both the base item and the first selected item
        base_score = calculate_color_match_score(base_item, item)
        item1_score = calculate_color_match_score(best_item1, item)
        # Average the scores
        avg_score = (base_score + item1_score) / 2
        scored_items2.append((item, avg_score))
    
    # Sort by score and get top matches
    scored_items2.sort(key=lambda x: x[1], reverse=True)
    top_items2 = scored_items2[:min(3, len(scored_items2))]
    best_item2 = random.choices(
        [item[0] for item in top_items2], 
        weights=[item[1] for item in top_items2],
        k=1
    )[0]
    
    return best_item1, best_item2

def generate_occasion_based_outfit(tops, bottoms, shoes, target_occasion="casual"):
    """
    Generate an outfit appropriate for a specific occasion from the given items
    
    Args:
        tops (list): List of top items
        bottoms (list): List of bottom items
        shoes (list): List of shoe items
        target_occasion (str): The target occasion for the outfit. 
                               Options: "casual", "work/professional", "formal", 
                                        "athletic/sport", "lounge/sleepwear"
    
    Returns:
        tuple: (top, bottom, shoes) or (None, None, None) if no match found
    """
    if not tops or not bottoms or not shoes:
        return None, None, None
    
    # Filter items by occasion
    tops_matching_occasion = [
        item for item in tops 
        if "occasions" in item and item["occasions"] and target_occasion in item["occasions"]
    ]
    
    bottoms_matching_occasion = [
        item for item in bottoms 
        if "occasions" in item and item["occasions"] and target_occasion in item["occasions"]
    ]
    
    shoes_matching_occasion = [
        item for item in shoes 
        if "occasions" in item and item["occasions"] and target_occasion in item["occasions"]
    ]
    
    # Check if we have enough items for this occasion
    if not tops_matching_occasion or not bottoms_matching_occasion or not shoes_matching_occasion:
        # Fallback to all items if we don't have enough for the specific occasion
        # You could also implement different fallback strategies here
        tops_matching_occasion = tops if not tops_matching_occasion else tops_matching_occasion
        bottoms_matching_occasion = bottoms if not bottoms_matching_occasion else bottoms_matching_occasion
        shoes_matching_occasion = shoes if not shoes_matching_occasion else shoes_matching_occasion
    
    # Select a random top for this occasion
    selected_top = random.choice(tops_matching_occasion)
    
    # Find matching bottoms based on the selected top
    scored_bottoms = []
    for bottom in bottoms_matching_occasion:
        # Calculate color match score
        color_score = calculate_color_match_score(selected_top, bottom)
        
        # Apply occasion match bonus
        if "occasions" in bottom and bottom["occasions"] and target_occasion in bottom["occasions"]:
            # Boost the score for items explicitly tagged for this occasion
            color_score *= 1.2  # 20% bonus for matching the occasion
        
        scored_bottoms.append((bottom, color_score))
    
    # Sort by score and get top matches
    scored_bottoms.sort(key=lambda x: x[1], reverse=True)
    top_bottoms = scored_bottoms[:min(3, len(scored_bottoms))]
    best_bottom = random.choices(
        [item[0] for item in top_bottoms], 
        weights=[item[1] for item in top_bottoms],
        k=1
    )[0]
    
    # Find matching shoes based on the selected top and bottom
    scored_shoes = []
    for shoe in shoes_matching_occasion:
        # Calculate color match score
        top_score = calculate_color_match_score(selected_top, shoe)
        bottom_score = calculate_color_match_score(best_bottom, shoe)
        avg_score = (top_score + bottom_score) / 2
        
        # Apply occasion match bonus
        if "occasions" in shoe and shoe["occasions"] and target_occasion in shoe["occasions"]:
            # Boost the score for items explicitly tagged for this occasion
            avg_score *= 1.2  # 20% bonus for matching the occasion
        
        scored_shoes.append((shoe, avg_score))
    
    # Sort by score and get top matches
    scored_shoes.sort(key=lambda x: x[1], reverse=True)
    top_shoes = scored_shoes[:min(3, len(scored_shoes))]
    best_shoe = random.choices(
        [item[0] for item in top_shoes], 
        weights=[item[1] for item in top_shoes],
        k=1
    )[0]
    
    return selected_top, best_bottom, best_shoe

def get_weather_appropriate_items(items, weather_data):
    """
    Filter items based on weather appropriateness
    
    Args:
        items (list): List of clothing items
        weather_data (dict): Categorized weather data
        
    Returns:
        list: Filtered list of items appropriate for the weather
    """
    if not weather_data:
        return items
    
    temp_category = weather_data["temp_category"]
    weather_condition = weather_data["weather_condition"]
    is_windy = weather_data["is_windy"]
    
    # Define appropriate clothing types for each temperature category
    temp_appropriate = {
        "cold": ["sweater", "jacket", "coat", "long sleeve", "hoodie", "sweatshirt", "jeans", "pants", "boots"],
        "cool": ["jacket", "long sleeve", "hoodie", "sweatshirt", "jeans", "pants"],
        "mild": ["long sleeve", "short sleeve", "jeans", "pants", "shorts"],
        "warm": ["short sleeve", "t-shirt", "polo", "shorts", "sneakers"],
        "hot": ["short sleeve", "t-shirt", "tank top", "shorts", "sandals"]
    }
    
    # Define appropriate clothing for weather conditions
    condition_appropriate = {
        "rainy": ["jacket", "hoodie", "jeans", "pants", "boots", "sneakers"],
        "snowy": ["coat", "jacket", "sweater", "hoodie", "jeans", "pants", "boots"],
        "sunny": ["t-shirt", "shorts", "sunglasses", "cap"],
        "cloudy": [],  # No specific requirements
        "normal": []   # No specific requirements
    }
    
    # Filter items based on both temperature and condition
    weather_appropriate_items = []
    
    for item in items:
        # Check if item has a description field which we can use to match against clothing types
        item_description = item.get("description", "").lower()
        
        # If no description, try using category as fallback
        if not item_description:
            item_description = item.get("category", "").lower()
        
        # Score this item's weather appropriateness
        temp_score = 0
        condition_score = 0
        
        # Temperature appropriateness
        for clothing_type in temp_appropriate[temp_category]:
            if clothing_type in item_description:
                temp_score += 1
        
        # Condition appropriateness
        for clothing_type in condition_appropriate[weather_condition]:
            if clothing_type in item_description:
                condition_score += 1
        
        # For windy days, avoid certain items
        wind_penalty = 0
        if is_windy and any(term in item_description for term in ["flowy", "loose", "light"]):
            wind_penalty = 2
        
        # Calculate final weather score
        weather_score = temp_score + condition_score - wind_penalty
        
        # Add the score to the item for later sorting
        item["weather_score"] = weather_score
        weather_appropriate_items.append(item)
    
    # Sort by weather appropriateness
    weather_appropriate_items.sort(key=lambda x: x.get("weather_score", 0), reverse=True)
    
    # Take the top 70% most appropriate items
    if len(weather_appropriate_items) > 5:
        return weather_appropriate_items[:int(len(weather_appropriate_items) * 0.7)]
    
    # If we have very few items, return them all
    return weather_appropriate_items

def generate_weather_based_outfit(tops, bottoms, shoes, weather_data):
    """
    Generate a weather-appropriate outfit
    
    Args:
        tops (list): List of top items
        bottoms (list): List of bottom items
        shoes (list): List of shoe items
        weather_data (dict): Categorized weather data
        
    Returns:
        tuple: (top, bottom, shoes) or (None, None, None) if no match
    """
    if not tops or not bottoms or not shoes or not weather_data:
        return None, None, None
    
    # Filter items by weather appropriateness
    weather_appropriate_tops = get_weather_appropriate_items(tops, weather_data)
    weather_appropriate_bottoms = get_weather_appropriate_items(bottoms, weather_data)
    weather_appropriate_shoes = get_weather_appropriate_items(shoes, weather_data)
    
    # If any category has no weather-appropriate items, fall back to original list
    if not weather_appropriate_tops:
        weather_appropriate_tops = tops
    if not weather_appropriate_bottoms:
        weather_appropriate_bottoms = bottoms
    if not weather_appropriate_shoes:
        weather_appropriate_shoes = shoes
    
    # Use the color coordination logic from existing function
    # But apply it only to weather-appropriate items
    selected_top, best_bottom, best_shoe = generate_color_coordinated_outfit(
        weather_appropriate_tops, 
        weather_appropriate_bottoms, 
        weather_appropriate_shoes
    )
    
    return selected_top, best_bottom, best_shoe