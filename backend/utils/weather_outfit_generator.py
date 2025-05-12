# utils/weather_outfit_generator.py

import random
from utils.outfit_generator import calculate_dominant_color_match_score, has_matching_occasion
from utils.color_utils import is_neutral_color

def calculate_weather_tag_match_score(item1, item2, current_temp_range, weather_condition):
    """
    Calculate a match score based on weather tags between two items
    With improved penalties for inappropriate temperature ranges
    
    Args:
        item1 (dict): First clothing item
        item2 (dict): Second clothing item
        current_temp_range (str): Current temperature range
        weather_condition (str): Current weather condition
        
    Returns:
        float: Match score between 0 and 1
    """
    # Start with a base score
    score = 0.5
    
    # Check if either item has temperature tags
    item1_temp_ranges = item1.get('temperature_range', [])
    item2_temp_ranges = item2.get('temperature_range', [])
    
    # SEVERE PENALTY for inappropriate temperature ranges
    # For cold weather (0-39°F), strongly penalize non-cold items
    if current_temp_range == "cold":
        if item1_temp_ranges and "cold" not in item1_temp_ranges:
            score -= 0.6  # Critical penalty for non-cold items in cold weather
            
        if item2_temp_ranges and "cold" not in item2_temp_ranges:
            score -= 0.6  # Critical penalty for non-cold items in cold weather
    
    # For other temperature ranges, keep existing penalties but make them stronger
    elif item1_temp_ranges and current_temp_range not in item1_temp_ranges:
        # If this item is only for cold and we're in hot weather
        if len(item1_temp_ranges) == 1 and item1_temp_ranges[0] == "cold" and current_temp_range == "hot":
            score -= 0.5  # Increased from 0.4
        # If this item is only for hot and we're in cold weather
        elif len(item1_temp_ranges) == 1 and item1_temp_ranges[0] == "hot" and current_temp_range == "cold":
            score -= 0.5  # Increased from 0.4
        # Adding penalty for cool-only items in hot weather
        elif len(item1_temp_ranges) == 1 and item1_temp_ranges[0] == "cool" and current_temp_range == "hot":
            score -= 0.4  # Increased from 0.3
            
    if item2_temp_ranges and current_temp_range not in item2_temp_ranges:
        # If this item is only for cold and we're in hot weather
        if len(item2_temp_ranges) == 1 and item2_temp_ranges[0] == "cold" and current_temp_range == "hot":
            score -= 0.5  # Increased from 0.4
        # If this item is only for hot and we're in cold weather
        elif len(item2_temp_ranges) == 1 and item2_temp_ranges[0] == "hot" and current_temp_range == "cold":
            score -= 0.5  # Increased from 0.4
        # Adding penalty for cool-only items in hot weather
        elif len(item2_temp_ranges) == 1 and item2_temp_ranges[0] == "cool" and current_temp_range == "hot":
            score -= 0.4  # Increased from 0.3
    
    # Check if both items have the same weather condition tag
    if has_weather_tag(item1, weather_condition) and has_weather_tag(item2, weather_condition):
        score += 0.3
    
    # Check if both items have the same temperature range tag
    if has_temperature_range_tag(item1, current_temp_range) and has_temperature_range_tag(item2, current_temp_range):
        score += 0.3
    
    # IMPROVED: Add a penalty for inappropriate items at extreme temperatures
    if current_temp_range == "cold":
        # For cold weather, heavily penalize items that are ONLY tagged as warm or hot
        if (item1_temp_ranges and len(item1_temp_ranges) == 1 and 
            item1_temp_ranges[0] in ["warm", "hot"]):
            score -= 0.6
        
        if (item2_temp_ranges and len(item2_temp_ranges) == 1 and 
            item2_temp_ranges[0] in ["warm", "hot"]):
            score -= 0.6
    
    # Add occasion matching bonus - this helps ensure better occasion matching
    if 'occasions' in item1 and item1['occasions'] and 'occasions' in item2 and item2['occasions']:
        common_occasions = set(item1['occasions']).intersection(set(item2['occasions']))
        if common_occasions:
            score += 0.2  # Increased from implicit zero to emphasize occasion matching
    
    # Additional bonus if one item's tags complement the other (e.g., one is warm, one is water-resistant)
    complementary_tags = False
    
    # Check for rain/snow condition with waterproof items
    if weather_condition in ["rain", "snow"]:
        if (has_weather_tag(item1, weather_condition) and not has_weather_tag(item2, weather_condition)) or \
           (not has_weather_tag(item1, weather_condition) and has_weather_tag(item2, weather_condition)):
            complementary_tags = True
    
    # Check for temperature complementary items (e.g., warm top with thermal bottoms)
    if current_temp_range in ["cold", "cool"]:
        if (has_temperature_range_tag(item1, current_temp_range) and not has_temperature_range_tag(item2, current_temp_range)) or \
           (not has_temperature_range_tag(item1, current_temp_range) and has_temperature_range_tag(item2, current_temp_range)):
            complementary_tags = True
    
    if complementary_tags:
        score += 0.1
    
    # Cap the score between 0.0 and 1.0
    return max(0.0, min(1.0, score))

def filter_items_by_strict_temperature(items, current_temp_range, weather_condition):
    """
    More strictly filter items by temperature and weather condition
    Especially useful for cold temperatures and prevents inappropriate items in extreme weather
    IMPROVED: Added shuffling of results to prevent first-added bias
    
    Args:
        items (list): List of clothing items
        current_temp_range (str): Current temperature range
        weather_condition (str): Current weather condition
        
    Returns:
        list: Filtered list of weather-appropriate items
    """
    if not items:
        return []
        
    # SPECIAL CASE: For hot temperatures when it's raining, use warm-weather rain gear
    # This helps select hoodies and rain jackets even in hot weather
    if current_temp_range == "hot" and weather_condition == "rain":
        # Look specifically for rain-appropriate items in both hot and warm ranges
        rain_appropriate_items = []
        
        for item in items:
            # Check if item has weather conditions and is tagged for rain
            if 'weather_conditions' in item and item['weather_conditions'] and "rain" in item['weather_conditions']:
                # If item is a top like a hoodie or rain jacket, allow warm-range items
                if item.get('category') == 'top':
                    # For tops, include both hot and warm items tagged for rain
                    # This allows lighter hoodies and rain jackets to be selected
                    if 'temperature_range' in item and item['temperature_range']:
                        if "hot" in item['temperature_range'] or "warm" in item['temperature_range']:
                            rain_appropriate_items.append(item)
                    else:
                        # If no temperature tags, include anyway as it might be rain-appropriate
                        rain_appropriate_items.append(item)
                # For bottoms and shoes, also allow warm-range items
                else:
                    if 'temperature_range' in item and item['temperature_range']:
                        if "hot" in item['temperature_range'] or "warm" in item['temperature_range']:
                            rain_appropriate_items.append(item)
                    else:
                        # If no temperature tags, include anyway
                        rain_appropriate_items.append(item)
        
        # If we found rain-appropriate items, shuffle them and return
        if rain_appropriate_items:
            random.shuffle(rain_appropriate_items)  # Shuffle to prevent first-added bias
            return rain_appropriate_items
        # Otherwise, continue with normal filtering
    
    # For cold temperatures (0-39°F), be EXTREMELY strict about what's appropriate
    if current_temp_range == "cold":
        cold_items = []
        
        for item in items:
            if 'temperature_range' in item and item['temperature_range']:
                # Item must be explicitly tagged for cold weather ONLY
                if "cold" in item['temperature_range']:
                    # For tops, prioritize items that have "cold" as their ONLY or PRIMARY temperature tag
                    if item.get('category') == 'top':
                        # Ideal case: item is tagged ONLY for cold
                        if len(item['temperature_range']) == 1:
                            cold_items.append(item)
                        # Second best: cold is the first/primary tag
                        elif item['temperature_range'][0] == "cold":
                            cold_items.append(item)
                        # Not ideal but acceptable: cold is one of multiple tags
                        else:
                            # Only add if we don't have better options
                            if not cold_items:
                                cold_items.append(item)
                    # For bottoms and shoes, any item tagged with cold is acceptable
                    else:
                        cold_items.append(item)
        
        # Return cold-specific items (shuffled) or fall back to regular filtering if nothing found
        if cold_items:
            random.shuffle(cold_items)  # Shuffle to prevent first-added bias
            return cold_items
        else:
            result = filter_items_by_temperature_priority(items, current_temp_range, weather_condition)
            random.shuffle(result)  # Shuffle the fallback results too
            return result
    
    # For hot temperatures, be very strict about what's appropriate
    if current_temp_range == "hot":
        hot_items = []
        
        for item in items:
            if 'temperature_range' in item and item['temperature_range']:
                # Item must be explicitly tagged for hot weather
                if "hot" in item['temperature_range']:
                    # And the weather condition must match what we need
                    if 'weather_conditions' not in item or not item['weather_conditions'] or weather_condition in item['weather_conditions']:
                        hot_items.append(item)
        
        if hot_items:
            random.shuffle(hot_items)  # Shuffle to prevent first-added bias
            return hot_items
        else:
            result = filter_items_by_temperature_priority(items, current_temp_range, weather_condition)
            random.shuffle(result)  # Shuffle the fallback results too
            return result
    
    # For warm temperatures, create a more balanced selection
    if current_temp_range == "warm":
        warm_items = []
        
        # First pass: get items specifically tagged for warm weather and current weather condition
        for item in items:
            if 'temperature_range' in item and item['temperature_range'] and "warm" in item['temperature_range']:
                if 'weather_conditions' in item and item['weather_conditions'] and weather_condition in item['weather_conditions']:
                    warm_items.append(item)
        
        # If we have enough items (at least 3), shuffle and return this refined set
        if len(warm_items) >= 3:
            random.shuffle(warm_items)  # Shuffle to prevent first-added bias
            return warm_items
            
        # Second pass: get items tagged for warm weather regardless of weather condition
        if not warm_items:
            for item in items:
                if 'temperature_range' in item and item['temperature_range'] and "warm" in item['temperature_range']:
                    warm_items.append(item)
                    
        # Return warm items (shuffled) or fall back to normal filtering
        if warm_items:
            random.shuffle(warm_items)  # Shuffle to prevent first-added bias
            return warm_items
        else:
            result = filter_items_by_temperature_priority(items, current_temp_range, weather_condition)
            random.shuffle(result)  # Shuffle the fallback results too
            return result
    
    # For cool temperatures, apply stricter filtering than before
    if current_temp_range == "cool":
        cool_items = []
        
        for item in items:
            if 'temperature_range' in item and item['temperature_range']:
                # Item must be explicitly tagged for cool weather (or cool+cold)
                if "cool" in item['temperature_range']:
                    # For tops, prioritize items that have appropriate weather condition tags
                    if item.get('category') == 'top':
                        if 'weather_conditions' not in item or not item['weather_conditions'] or weather_condition in item['weather_conditions']:
                            cool_items.append(item)
                    # For bottoms and shoes, any cool-tagged item is acceptable
                    else:
                        cool_items.append(item)
        
        # Return cool-specific items (shuffled) or fall back to regular filtering if nothing found
        if cool_items:
            random.shuffle(cool_items)  # Shuffle to prevent first-added bias
            return cool_items
        else:
            result = filter_items_by_temperature_priority(items, current_temp_range, weather_condition)
            random.shuffle(result)  # Shuffle the fallback results too
            return result
    
    # For other temperature ranges, use the normal filtering algorithm and shuffle the results
    result = filter_items_by_temperature_priority(items, current_temp_range, weather_condition)
    random.shuffle(result)  # Shuffle to prevent first-added bias
    return result

def filter_items_by_temperature_priority(items, current_temp_range, weather_condition):
    """
    Filter clothing items based on their tagged weather metadata
    with stronger temperature matching requirements
    IMPROVED: Added shuffling of results to prevent first-added bias
    
    Args:
        items (list): List of clothing items
        current_temp_range (str): Current temperature range
        weather_condition (str): Current weather condition
        
    Returns:
        list: Filtered list of weather-appropriate items
    """
    if not items:
        return []
    
    # First priority: Items that match both current temperature range AND weather condition
    perfect_matches = []
    
    # Second priority: Items that match current temperature range (or adjacent ranges)
    temp_matches = []
    
    # Third priority: Items that match just the weather condition but with compatible temperature
    weather_matches = []
    
    for item in items:
        item_temp_ranges = item.get('temperature_range', [])
        item_weather_conditions = item.get('weather_conditions', [])
        
        # 1. Check for perfect matches (both temp and weather)
        if has_temperature_range_tag(item, current_temp_range) and has_weather_tag(item, weather_condition):
            perfect_matches.append(item)
            continue
            
        # Check if the item has incompatible temperature ranges
        if item_temp_ranges and not is_temp_range_compatible(item_temp_ranges, current_temp_range):
            # Skip items with incompatible temperature ranges
            continue
            
        # 2. Check for temperature range matches or adjacent ranges
        if not item_temp_ranges or current_temp_range in item_temp_ranges:
            # Direct match with current temperature range
            temp_matches.append(item)
            continue
            
        # Check for adjacent temperature ranges
        adjacent_ranges = get_adjacent_temp_ranges(current_temp_range)
        if any(adj_range in item_temp_ranges for adj_range in adjacent_ranges):
            temp_matches.append(item)
            continue
            
        # 3. Check for weather condition match with compatible temperature
        if weather_condition in item_weather_conditions:
            # Additional check to avoid temperature mismatches (like heavy coats in hot weather)
            if is_temp_range_compatible(item_temp_ranges, current_temp_range):
                weather_matches.append(item)
                continue
    
    # Return the highest priority matches we found (with shuffling for each category)
    if perfect_matches:
        random.shuffle(perfect_matches)  # Shuffle to prevent first-added bias
        return perfect_matches
    elif temp_matches:
        random.shuffle(temp_matches)  # Shuffle to prevent first-added bias
        return temp_matches
    elif weather_matches:
        random.shuffle(weather_matches)  # Shuffle to prevent first-added bias
        return weather_matches
    else:
        # Fallback to check for any items that are simply not incompatible with current weather
        compatible_items = []
        for item in items:
            item_temp_ranges = item.get('temperature_range', [])
            if not item_temp_ranges or is_temp_range_compatible(item_temp_ranges, current_temp_range):
                compatible_items.append(item)
        
        if compatible_items:
            random.shuffle(compatible_items)  # Shuffle to prevent first-added bias
            return compatible_items
        else:
            random.shuffle(items)  # Shuffle even the last resort items
            return items

def generate_weather_based_outfit(tops, bottoms, shoes, temperature, weather_condition):
    """
    Generate an outfit appropriate for the current weather conditions
    Prioritizing items with matching weather_conditions and temperature_range tags
    Excludes formal tops and bottoms but allows formal shoes
    Ensures shoes match the top color or are neutral
    Ensures tops, bottoms, and shoes share at least one occasion tag
    IMPROVED: Added randomization to prevent first-added bias
    
    Args:
        tops (list): List of top items
        bottoms (list): List of bottom items
        shoes (list): List of shoe items
        temperature (int): Current temperature in Fahrenheit
        weather_condition (str): Current weather condition (sunny, cloudy, rain, snow, etc.)
        
    Returns:
        tuple: (top, bottom, shoes) where bottom may be None for complete tops
    """
    if not tops or not shoes:
        return None, None, None
    
    # Filter out formal and lounge/sleepwear tops and bottoms, but keep all shoes
    tops = [item for item in tops if not has_excluded_occasion_for_top_bottom(item)]
    bottoms = [item for item in bottoms if not has_excluded_occasion_for_top_bottom(item)]
    # No filtering for shoes based on formal occasion
    shoes = [item for item in shoes if not has_lounge_sleepwear_occasion(item)]
    
    # Check if we still have enough items after filtering
    if not tops or not shoes:
        return None, None, None
    
    # Determine the current temperature range based on given temperature
    current_temp_range = get_temperature_range(temperature)
    
    # SPECIAL CASE: Handle hot rainy conditions differently
    # For hot temperatures when it's raining, we want to prefer warm-range rain items
    if current_temp_range == "hot" and weather_condition == "rain":
        using_adjusted_temp_range = True
        filtering_temp_range = "warm"  # Use warm range for filtering
        display_temp_range = current_temp_range  # But preserve original for display
    else:
        using_adjusted_temp_range = False
        filtering_temp_range = current_temp_range
    
    # IMPROVED: Filter items appropriate for the weather using their tagged metadata with STRICTER filters
    # These functions now shuffle results internally to prevent first-added bias
    weather_appropriate_tops = filter_items_by_strict_temperature(tops, filtering_temp_range, weather_condition)
    weather_appropriate_bottoms = filter_items_by_strict_temperature(bottoms, filtering_temp_range, weather_condition)
    weather_appropriate_shoes = filter_items_by_strict_temperature(shoes, filtering_temp_range, weather_condition)
    
    # If we don't have enough weather-appropriate items, fall back to the actual temp range
    if using_adjusted_temp_range and (not weather_appropriate_tops or not weather_appropriate_bottoms or not weather_appropriate_shoes):
        # Try with the original temperature range
        if not weather_appropriate_tops:
            weather_appropriate_tops = filter_items_by_strict_temperature(tops, current_temp_range, weather_condition)
        if not weather_appropriate_bottoms:
            weather_appropriate_bottoms = filter_items_by_strict_temperature(bottoms, current_temp_range, weather_condition)
        if not weather_appropriate_shoes:
            weather_appropriate_shoes = filter_items_by_strict_temperature(shoes, current_temp_range, weather_condition)
    
    # If we still don't have enough items, fall back to less strict filter
    if not weather_appropriate_tops:
        weather_appropriate_tops = filter_items_by_temperature_priority(tops, current_temp_range, weather_condition)
        if not weather_appropriate_tops:  # If still nothing, use all tops
            weather_appropriate_tops = list(tops)
            random.shuffle(weather_appropriate_tops)  # Shuffle to prevent first-added bias
    
    if not weather_appropriate_bottoms:
        weather_appropriate_bottoms = filter_items_by_temperature_priority(bottoms, current_temp_range, weather_condition)
        if not weather_appropriate_bottoms:  # If still nothing, use all bottoms
            weather_appropriate_bottoms = list(bottoms)
            random.shuffle(weather_appropriate_bottoms)  # Shuffle to prevent first-added bias
    
    if not weather_appropriate_shoes:
        weather_appropriate_shoes = filter_items_by_temperature_priority(shoes, current_temp_range, weather_condition)
        if not weather_appropriate_shoes:  # If still nothing, use all shoes
            weather_appropriate_shoes = list(shoes)
            random.shuffle(weather_appropriate_shoes)  # Shuffle to prevent first-added bias
    
    # IMPROVED: If temperature is hot, exclude items that are only for cool/cold temperatures
    # BUT skip this check if we're in the hot+rain special case
    if current_temp_range == "hot" and not using_adjusted_temp_range:
        hot_appropriate_tops = [item for item in weather_appropriate_tops 
                               if not (item.get('temperature_range') and 
                                      set(item.get('temperature_range')) <= set(["cool", "cold"]))]
        
        if hot_appropriate_tops:  # Only use filtered list if it's not empty
            weather_appropriate_tops = hot_appropriate_tops
            random.shuffle(weather_appropriate_tops)  # Shuffle after filtering
        elif not weather_appropriate_tops:  # If filtering removed all tops, find tops tagged with "hot"
            hot_tops = [item for item in tops if item.get('temperature_range') and "hot" in item.get('temperature_range')]
            if hot_tops:
                weather_appropriate_tops = hot_tops
                random.shuffle(weather_appropriate_tops)  # Shuffle the hot tops
            else:
                weather_appropriate_tops = list(tops)  # Fallback to all tops if no hot tops
                random.shuffle(weather_appropriate_tops)  # Shuffle the fallback list
    
    # NEW: For warm weather, identify and handle frequent items like your black hoodie
    if current_temp_range == "warm":
        # Identify potential hoodies or frequently selected items
        potential_hoodies = []
        other_tops = []
        
        for item in weather_appropriate_tops:
            # Identify items that might be overselected based on their properties
            is_potential_hoodie = False
            
            # Check if it's a black item with cool/warm tags (like your hoodie)
            if ('colors' in item and item['colors'] and 
                item['colors'][0]['name'].lower() == 'black' and
                'temperature_range' in item and item['temperature_range'] and
                set(item['temperature_range']) == set(["cool", "warm"])):
                is_potential_hoodie = True
            
            if is_potential_hoodie:
                potential_hoodies.append(item)
            else:
                other_tops.append(item)
        
        # If we have both potential hoodies and other tops, decide which pool to use
        if potential_hoodies and other_tops:
            # Only 25% chance to select from potential hoodies in warm weather
            # But increased chance for rain/snow conditions where hoodies make sense
            hoodie_chance = 0.25
            if weather_condition in ["rain", "snow"]:
                hoodie_chance = 0.6  # 60% chance for rainy/snowy conditions
                
            if random.random() < hoodie_chance:
                weather_appropriate_tops = potential_hoodies
                random.shuffle(weather_appropriate_tops)  # Shuffle after selection
            else:
                weather_appropriate_tops = other_tops
                random.shuffle(weather_appropriate_tops)  # Shuffle after selection
    
    # Make sure we have appropriate items after all these filters
    if not weather_appropriate_tops or not weather_appropriate_shoes:
        return None, None, None
    
    # Refined selection process with anti-bias mechanism
    # Use a true random selection rather than any color bias
    base_top = random.choice(weather_appropriate_tops)
    
    # Check if the selected top is a "complete" top (dress, jumpsuit, etc.)
    is_complete_top = base_top.get("subcategory") == "complete"
    
    if is_complete_top:
        # For complete tops, skip bottom selection and directly match with shoes
        # First, check which shoes share at least one occasion tag with the top
        matching_occasion_shoes = [shoe for shoe in weather_appropriate_shoes if shares_any_occasion(base_top, shoe)]
        
        # If no shoes with matching occasions, fall back to all shoes
        if not matching_occasion_shoes:
            matching_occasion_shoes = weather_appropriate_shoes
        else:
            # IMPROVED: Shuffle the occasion-matching shoes to prevent bias
            random.shuffle(matching_occasion_shoes)
        
        # Then, from these occasion-matching shoes, filter to include color-matching, complementary, or neutral shoes
        # This now returns a dictionary of categories instead of a flat list
        shoe_categories = filter_shoes_by_color_match(base_top, matching_occasion_shoes)
        
        # IMPROVED: Check if we have any direct color matches and prioritize them
        if isinstance(shoe_categories, dict) and 'direct_match' in shoe_categories and shoe_categories['direct_match']:
            # Shuffle the direct matches to prevent first-added bias
            random.shuffle(shoe_categories['direct_match'])
            
            # Score them based on weather and occasion criteria
            scored_direct_matches = []
            for shoe in shoe_categories['direct_match']:
                # Score based on weather tag appropriateness
                weather_score = calculate_weather_tag_match_score(base_top, shoe, current_temp_range, weather_condition)
                
                # Score based on occasion matching
                occasion_score = 0.25 if has_matching_occasion(base_top, shoe) else 0
                
                # IMPROVED: Give higher weight to color match (exact match is guaranteed here)
                combined_score = (weather_score * 0.45) + (1.0 * 0.30) + occasion_score
                
                # Special case for rain/snow - still prioritize waterproof shoes
                if weather_condition in ["rain", "snow"] and has_weather_tag(shoe, weather_condition):
                    combined_score = min(1.0, combined_score * 1.2)
                
                scored_direct_matches.append((shoe, combined_score))
            
            # If we have scored direct matches, select from them with higher probability
            if scored_direct_matches:
                scored_direct_matches.sort(key=lambda x: x[1], reverse=True)
                top_direct_matches = scored_direct_matches[:min(3, len(scored_direct_matches))]
                
                # HIGH chance of selecting from color-matched shoes
                if random.random() < 0.85:  # 85% chance to use direct color matches
                    selected_shoes = random.choices(
                        [item[0] for item in top_direct_matches], 
                        weights=[max(0.1, item[1]) for item in top_direct_matches],
                        k=1
                    )[0]
                    return base_top, None, selected_shoes
        
        # If no direct matches OR we randomly decided not to use them (15% chance),
        # proceed with the regular scoring but with adjusted weights
        
        # If we have categorized shoes - score them with category bonuses
        if isinstance(shoe_categories, dict) and sum(len(shoes_list) for shoes_list in shoe_categories.values()) > 0:
            # We have categorized shoes - score them with category bonuses
            scored_shoes = []
            
            # IMPROVED: Shuffle each category before processing to prevent bias
            for category in shoe_categories:
                random.shuffle(shoe_categories[category])
            
            # Process each category with appropriate bonuses
            for category, shoes_list in shoe_categories.items():
                for shoe in shoes_list:
                    # Score based on weather appropriateness
                    weather_score = calculate_weather_tag_match_score(base_top, shoe, current_temp_range, weather_condition)
                    
                    # Base color score
                    color_score = calculate_dominant_color_match_score(base_top, shoe)
                    
                    # IMPROVED: Apply stronger category-based color bonuses
                    if category == 'direct_match':
                        # Much larger bonus for exact color match with top's dominant color
                        color_score = min(1.0, color_score + 0.5)  # Increased from 0.3
                    elif category == 'complementary':
                        # Moderate bonus for complementary color match
                        color_score = min(1.0, color_score + 0.2)  # Same as before
                    elif category == 'neutral':
                        # Slight bonus for neutral colors
                        color_score = min(1.0, color_score + 0.1)  # Same as before
                    
                    # Score based on occasion matching
                    occasion_score = 0.25 if has_matching_occasion(base_top, shoe) else 0
                    
                    # IMPROVED: Combine scores with updated weights
                    # New weights: 45% weather, 30% color, 25% occasion
                    combined_score = (weather_score * 0.45) + (color_score * 0.30) + occasion_score
                    
                    # Special case for rain/snow - prioritize waterproof shoes
                    if weather_condition in ["rain", "snow"] and has_weather_tag(shoe, weather_condition):
                        combined_score *= 1.5
                    
                    scored_shoes.append((shoe, combined_score))
        else:
            # Filter returned all shoes or empty categories, use original list
            all_shoes = matching_occasion_shoes
            
            # If still no matches, use all weather-appropriate shoes
            if not all_shoes:
                all_shoes = weather_appropriate_shoes
            
            # IMPROVED: Shuffle before scoring to prevent first-added bias
            random.shuffle(all_shoes)
                
            # Score all shoes without color categorization
            scored_shoes = []
            for shoe in all_shoes:
                # Score based on weather appropriateness (using tagged data)
                weather_score = calculate_weather_tag_match_score(base_top, shoe, current_temp_range, weather_condition)
                
                # Score based on color coordination
                color_score = calculate_dominant_color_match_score(base_top, shoe)
                
                # IMPROVED: Check for direct color match and apply bonus
                top_dominant_color = base_top['colors'][0]['name'].lower() if 'colors' in base_top and base_top['colors'] else None
                shoe_dominant_color = shoe['colors'][0]['name'].lower() if 'colors' in shoe and shoe['colors'] else None
                
                if top_dominant_color and shoe_dominant_color and top_dominant_color == shoe_dominant_color:
                    # Direct color match bonus - much higher than before
                    color_score = min(1.0, color_score + 0.5)
                
                # Score based on occasion matching
                occasion_score = 0.25 if has_matching_occasion(base_top, shoe) else 0
                
                # IMPROVED: Combine scores with updated weights
                combined_score = (weather_score * 0.45) + (color_score * 0.30) + occasion_score
                
                # Special case for rain/snow - prioritize waterproof shoes
                if weather_condition in ["rain", "snow"] and has_weather_tag(shoe, weather_condition):
                    combined_score *= 1.5
                
                scored_shoes.append((shoe, combined_score))
        
        # Sort by score and get top matches
        scored_shoes.sort(key=lambda x: x[1], reverse=True)
        top_shoes = scored_shoes[:min(3, len(scored_shoes))]
        
        # IMPROVED: If we don't have any shoe options, return None
        if not top_shoes:
            return None, None, None
        
        selected_shoes = random.choices(
            [item[0] for item in top_shoes], 
            weights=[max(0.1, item[1]) for item in top_shoes],
            k=1
        )[0]
        
        return base_top, None, selected_shoes
    
    # For standard tops, find matching bottom and shoes
    
    # IMPROVED: First, filter bottoms that share at least one occasion with the top
    # This ensures occasion matching between tops and bottoms
    matching_occasion_bottoms = [bottom for bottom in weather_appropriate_bottoms if shares_any_occasion(base_top, bottom)]
    
    # If no bottoms with matching occasions, fall back to all bottoms
    if not matching_occasion_bottoms:
        matching_occasion_bottoms = weather_appropriate_bottoms
    
    # IMPROVED: Shuffle matching occasion bottoms to prevent first-added bias
    random.shuffle(matching_occasion_bottoms)
    
    # If there are no bottoms at all, return None
    if not matching_occasion_bottoms:
        return None, None, None
    
    scored_bottoms = []
    for bottom in matching_occasion_bottoms:
        # Base score on weather tag appropriateness
        weather_score = calculate_weather_tag_match_score(base_top, bottom, current_temp_range, weather_condition)
        
        # Add color coordination score
        color_score = calculate_dominant_color_match_score(base_top, bottom)
        
        # Add occasion score - IMPROVED: increased weight for occasion matching
        occasion_score = 0.35 if has_matching_occasion(base_top, bottom) else 0
        
        # Combine scores with updated weights: 45% weather, 30% color, 25% occasion
        combined_score = (weather_score * 0.45) + (color_score * 0.30) + occasion_score
        
        scored_bottoms.append((bottom, combined_score))
    
    # Sort by score and get top matches
    scored_bottoms.sort(key=lambda x: x[1], reverse=True)
    top_bottoms = scored_bottoms[:min(3, len(scored_bottoms))]
    
    # IMPROVED: If we don't have any bottom options, return None
    if not top_bottoms:
        return None, None, None
    
    selected_bottom = random.choices(
        [item[0] for item in top_bottoms], 
        weights=[max(0.1, item[1]) for item in top_bottoms],
        k=1
    )[0]
    
    # For shoes, first find shoes that share occasions with the top AND bottom when possible
    matching_top_shoes = [shoe for shoe in weather_appropriate_shoes if shares_any_occasion(base_top, shoe)]
    matching_bottom_shoes = [shoe for shoe in weather_appropriate_shoes if shares_any_occasion(selected_bottom, shoe)]
    
    # Find shoes that match both top and bottom occasions
    matching_both_shoes = [shoe for shoe in matching_top_shoes if shoe in matching_bottom_shoes]
    
    # If no shoes match both, prioritize shoes matching the top
    matching_occasion_shoes = matching_both_shoes if matching_both_shoes else matching_top_shoes
    
    # If still no matches, use all shoes
    if not matching_occasion_shoes:
        matching_occasion_shoes = weather_appropriate_shoes
    
    # IMPROVED: Shuffle the shoe candidates to prevent first-added bias
    random.shuffle(matching_occasion_shoes)
    
    # If there are no shoes at all, return None
    if not matching_occasion_shoes:
        return None, None, None
    
    # Then from these occasion-matching shoes, filter to include color-matching, complementary, or neutral shoes
    # This returns a dictionary of categories instead of a flat list
    shoe_categories = filter_shoes_by_color_match(base_top, matching_occasion_shoes)
    
    # IMPROVED: Check if we have any direct color matches and prioritize them
    if isinstance(shoe_categories, dict) and 'direct_match' in shoe_categories and shoe_categories['direct_match']:
        # Shuffle the direct matches to prevent first-added bias
        random.shuffle(shoe_categories['direct_match'])
        
        # We have direct color matches - score them based on weather and occasion criteria
        scored_direct_matches = []
        for shoe in shoe_categories['direct_match']:
            # Score based on weather tag appropriateness
            top_weather_score = calculate_weather_tag_match_score(base_top, shoe, current_temp_range, weather_condition)
            bottom_weather_score = calculate_weather_tag_match_score(selected_bottom, shoe, current_temp_range, weather_condition)
            weather_score = (top_weather_score + bottom_weather_score) / 2
            
            # Score based on occasion matching
            occasion_score = 0
            if has_matching_occasion(base_top, shoe) and has_matching_occasion(selected_bottom, shoe):
                occasion_score = 0.25  # Full occasion matching bonus
            elif has_matching_occasion(base_top, shoe) or has_matching_occasion(selected_bottom, shoe):
                occasion_score = 0.1  # Half occasion matching bonus
            
            # IMPROVED: Give higher weight to color match (exact match is guaranteed here)
            # New weights: 45% weather, 30% color (which is 1.0), 25% occasion
            combined_score = (weather_score * 0.45) + (1.0 * 0.30) + occasion_score
            
            # Special case for rain/snow - still prioritize waterproof shoes
            if weather_condition in ["rain", "snow"] and has_weather_tag(shoe, weather_condition):
                combined_score = min(1.0, combined_score * 1.2)  # Smaller multiplier to avoid overwhelming color preference
            
            scored_direct_matches.append((shoe, combined_score))
        
        # If we have scored direct matches, select from them with higher probability
        if scored_direct_matches:
            scored_direct_matches.sort(key=lambda x: x[1], reverse=True)
            top_direct_matches = scored_direct_matches[:min(3, len(scored_direct_matches))]
            
            # HIGH chance of selecting from color-matched shoes
            if random.random() < 0.85:  # 85% chance to use direct color matches
                selected_shoes = random.choices(
                    [item[0] for item in top_direct_matches], 
                    weights=[max(0.1, item[1]) for item in top_direct_matches],
                    k=1
                )[0]
                return base_top, selected_bottom, selected_shoes
    
    # If we didn't have direct matches OR we randomly decided not to use them (15% chance),
    # proceed with the regular scoring but with adjusted weights
    
    # If using the dictionary categories
    if isinstance(shoe_categories, dict) and sum(len(shoes_list) for shoes_list in shoe_categories.values()) > 0:
        scored_shoes = []
        
        # IMPROVED: Shuffle each category before processing to prevent bias
        for category in shoe_categories:
            random.shuffle(shoe_categories[category])
        
        # Process each category with adjusted category bonuses
        for category, shoes_list in shoe_categories.items():
            for shoe in shoes_list:
                # Score based on weather tag appropriateness
                top_weather_score = calculate_weather_tag_match_score(base_top, shoe, current_temp_range, weather_condition)
                bottom_weather_score = calculate_weather_tag_match_score(selected_bottom, shoe, current_temp_range, weather_condition)
                weather_score = (top_weather_score + bottom_weather_score) / 2
                
                # Base color score
                color_score = calculate_dominant_color_match_score(base_top, shoe)
                
                # IMPROVED: Apply category-based color bonuses
                if category == 'direct_match':
                    # Much larger bonus for exact color match with top's dominant color
                    color_score = min(1.0, color_score + 0.5)
                elif category == 'complementary':
                    # Moderate bonus for complementary color match
                    color_score = min(1.0, color_score + 0.2)
                elif category == 'neutral':
                    # Slight bonus for neutral colors
                    color_score = min(1.0, color_score + 0.1)
                
                # Score based on occasion matching with updated weights
                occasion_score = 0
                if has_matching_occasion(base_top, shoe) and has_matching_occasion(selected_bottom, shoe):
                    occasion_score = 0.25  # Full occasion matching bonus
                elif has_matching_occasion(base_top, shoe) or has_matching_occasion(selected_bottom, shoe):
                    occasion_score = 0.1  # Half occasion matching bonus
                
                # IMPROVED: Combine scores with updated weights
                # New weights: 45% weather, 30% color, 25% occasion
                combined_score = (weather_score * 0.45) + (color_score * 0.30) + occasion_score
                
                # Special case for rain/snow - still prioritize waterproof shoes
                if weather_condition in ["rain", "snow"] and has_weather_tag(shoe, weather_condition):
                    combined_score = min(1.0, combined_score * 1.3)
                
                scored_shoes.append((shoe, combined_score))
    else:
        # For cases when we're using the simpler flat list of shoes
        all_shoes = matching_occasion_shoes if matching_occasion_shoes else weather_appropriate_shoes
        
        # IMPROVED: Shuffle before scoring to prevent first-added bias
        random.shuffle(all_shoes)
            
        # Score all shoes with updated weights
        scored_shoes = []
        for shoe in all_shoes:
            # Score based on weather tag appropriateness
            top_weather_score = calculate_weather_tag_match_score(base_top, shoe, current_temp_range, weather_condition)
            bottom_weather_score = calculate_weather_tag_match_score(selected_bottom, shoe, current_temp_range, weather_condition)
            weather_score = (top_weather_score + bottom_weather_score) / 2
            
            # Score based on color coordination
            top_color_score = calculate_dominant_color_match_score(base_top, shoe)
            bottom_color_score = calculate_dominant_color_match_score(selected_bottom, shoe)
            color_score = (top_color_score + bottom_color_score) / 2
            
            # IMPROVED: Check for direct color match and apply bonus
            top_colors = [color_data['name'].lower() for color_data in base_top['colors']] if 'colors' in base_top and base_top['colors'] else []
            shoe_colors = [color_data['name'].lower() for color_data in shoe['colors']] if 'colors' in shoe and shoe['colors'] else []
            
            # Check for any color match between top and shoe colors
            if top_colors and shoe_colors:
                primary_color_match = shoe_colors[0] == top_colors[0] if shoe_colors and top_colors else False
                any_color_match = any(shoe_color in top_colors for shoe_color in shoe_colors)
                
                if primary_color_match:
                    # Highest bonus for primary color match (index 0 to index 0)
                    color_score = min(1.0, color_score + 0.5)
                elif any_color_match:
                    # Good bonus for any color match
                    color_score = min(1.0, color_score + 0.4)
            
            # Score based on occasion matching
            occasion_score = 0
            if has_matching_occasion(base_top, shoe) and has_matching_occasion(selected_bottom, shoe):
                occasion_score = 0.25  # Full occasion matching bonus
            elif has_matching_occasion(base_top, shoe) or has_matching_occasion(selected_bottom, shoe):
                occasion_score = 0.1  # Half occasion matching bonus
            
            # IMPROVED: Combine scores with updated weights
            # New weights: 45% weather, 30% color, 25% occasion
            combined_score = (weather_score * 0.45) + (color_score * 0.30) + occasion_score
            
            # Special case for rain/snow - prioritize waterproof shoes
            if weather_condition in ["rain", "snow"] and has_weather_tag(shoe, weather_condition):
                combined_score = min(1.0, combined_score * 1.3)
            
            scored_shoes.append((shoe, combined_score))
    
    # Sort by score and get top matches
    scored_shoes.sort(key=lambda x: x[1], reverse=True)
    top_shoes = scored_shoes[:min(3, len(scored_shoes))]
    
    # IMPROVED: If we don't have any shoe options, return None
    if not top_shoes:
        return None, None, None
    
    selected_shoes = random.choices(
        [item[0] for item in top_shoes], 
        weights=[max(0.1, item[1]) for item in top_shoes],
        k=1
    )[0]
    
    return base_top, selected_bottom, selected_shoes

def filter_shoes_by_color_match(top, shoes):
    """
    Filter shoes to include those that match any of the top's colors, complement the top's colors,
    or have all neutral colors. Considers ALL color indexes for each item, not just dominant color.
    
    Args:
        top (dict): Top clothing item
        shoes (list): List of shoe items
        
    Returns:
        dict: Filtered list of shoes grouped by color match type (direct match, complementary, neutral)
    """
    if not top or not shoes:
        return shoes
    
    # Check if top has colors
    if 'colors' not in top or not top['colors']:
        return shoes
    
    # Get ALL of the top's colors
    top_colors = [color_data['name'].lower() for color_data in top['colors']] if top['colors'] else []
    
    if not top_colors:
        return shoes
    
    # Primary color is still the first one (index 0)
    primary_top_color = top_colors[0] if top_colors else None
    
    # Get list of complementary colors for all of the top's colors
    from utils.color_utils import get_matching_colors
    complementary_colors = []
    for color in top_colors:
        complementary_colors.extend(get_matching_colors(color))
    # Remove duplicates
    complementary_colors = list(set(complementary_colors))
    
    # Create separate lists for different types of matching shoes
    direct_match_shoes = []  # Shoes with any color matching any top color
    complementary_shoes = [] # Shoes with any color complementing any top color
    neutral_shoes = []       # Shoes with ALL neutral colors
    other_shoes = []         # All other shoes
    
    for shoe in shoes:
        # Check if shoe has colors
        if 'colors' not in shoe or not shoe['colors']:
            other_shoes.append(shoe)
            continue
            
        # Get ALL of the shoe's colors
        shoe_colors = [color_data['name'].lower() for color_data in shoe['colors']]
        
        # Check if ANY shoe color directly matches ANY top color
        has_direct_match = any(shoe_color in top_colors for shoe_color in shoe_colors)
        
        # Special case: Primary color match (index 0 to index 0) gets priority
        primary_color_match = shoe_colors[0] == primary_top_color if shoe_colors and primary_top_color else False
        
        # Check if ANY shoe color complements ANY top color
        has_complementary_match = any(shoe_color in complementary_colors for shoe_color in shoe_colors)
        
        # Check if ALL shoe colors are neutral (must all be neutral to qualify)
        from utils.color_utils import is_neutral_color
        all_neutral = all(is_neutral_color(shoe_color) for shoe_color in shoe_colors) if shoe_colors else False
        
        # Categorize shoes with priority order
        if primary_color_match:
            # Primary color match gets highest priority
            direct_match_shoes.append(shoe)
        elif has_direct_match:
            # Other direct matches still go in direct match category
            direct_match_shoes.append(shoe)
        elif has_complementary_match:
            # Any complementary match goes in complementary category
            complementary_shoes.append(shoe)
        elif all_neutral:
            # Shoes with all neutral colors
            neutral_shoes.append(shoe)
        else:
            # No match
            other_shoes.append(shoe)
    
    # Combine all shoes groups, preserving priority order
    # This preserves the groups so they can be used in scoring
    all_matched_shoes = {
        'direct_match': direct_match_shoes,
        'complementary': complementary_shoes,
        'neutral': neutral_shoes,
        'other': other_shoes
    }
    
    # If no matching shoes found at all, return all shoes
    all_shoes = direct_match_shoes + complementary_shoes + neutral_shoes + other_shoes
    if not all_shoes:
        return shoes
        
    return all_matched_shoes

def shares_any_occasion(item1, item2):
    """
    Check if two items share at least one occasion tag
    
    Args:
        item1 (dict): First clothing item
        item2 (dict): Second clothing item
        
    Returns:
        bool: True if items share at least one occasion tag, False otherwise
    """
    if 'occasions' not in item1 or not item1['occasions'] or 'occasions' not in item2 or not item2['occasions']:
        # If either item has no occasion tags, consider them as not sharing occasions
        return False
    
    # Check for intersection between occasion lists
    return bool(set(item1['occasions']).intersection(set(item2['occasions'])))

def has_excluded_occasion_for_top_bottom(item):
    """
    Check if an item has any excluded occasion tags for tops and bottoms
    Currently excludes 'formal' and 'lounge/sleepwear' for tops and bottoms
    
    Args:
        item (dict): Clothing item
        
    Returns:
        bool: True if the item has an excluded occasion tag, False otherwise
    """
    if 'occasions' in item and item['occasions']:
        excluded_occasions = ["formal", "lounge/sleepwear"]
        return any(occasion in excluded_occasions for occasion in item['occasions'])
    return False

def has_lounge_sleepwear_occasion(item):
    """
    Check if an item has the lounge/sleepwear occasion tag
    Used for shoes since we want to allow formal shoes but not lounge/sleepwear
    
    Args:
        item (dict): Clothing item
        
    Returns:
        bool: True if the item has the lounge/sleepwear tag, False otherwise
    """
    if 'occasions' in item and item['occasions']:
        return "lounge/sleepwear" in item['occasions']
    return False

def get_temperature_range(temperature):
    """
    Convert temperature to a temperature range string
    
    Args:
        temperature (int): Temperature in Fahrenheit
        
    Returns:
        str: Temperature range (cold, cool, warm, hot)
    """
    if temperature <= 39:
        return "cold"
    elif temperature <= 59:
        return "cool"
    elif temperature <= 79:
        return "warm"
    else:  # temperature >= 80
        return "hot"

def has_weather_tag(item, weather_condition):
    """
    Check if an item has a specific weather condition tag
    
    Args:
        item (dict): Clothing item
        weather_condition (str): Weather condition to check for
        
    Returns:
        bool: True if the item has the weather tag, False otherwise
    """
    if 'weather_conditions' in item and item['weather_conditions']:
        return weather_condition in item['weather_conditions']
    return False

def has_temperature_range_tag(item, temp_range):
    """
    Check if an item has a specific temperature range tag
    
    Args:
        item (dict): Clothing item
        temp_range (str): Temperature range to check for
        
    Returns:
        bool: True if the item has the temperature range tag, False otherwise
    """
    if 'temperature_range' in item and item['temperature_range']:
        return temp_range in item['temperature_range']
    return False

def get_adjacent_temp_ranges(temp_range):
    """
    Get adjacent temperature ranges
    
    Args:
        temp_range (str): Temperature range
        
    Returns:
        list: List of adjacent temperature ranges
    """
    temp_ranges = ["cold", "cool", "warm", "hot"]
    idx = temp_ranges.index(temp_range)
    adjacent = []
    
    if idx > 0:
        adjacent.append(temp_ranges[idx - 1])
    if idx < len(temp_ranges) - 1:
        adjacent.append(temp_ranges[idx + 1])
        
    return adjacent

def is_temp_range_compatible(item_temp_ranges, current_temp_range):
    """
    Check if an item's temperature ranges are compatible with the current temperature
    Much stricter for cold weather - only cold-tagged items for cold weather
    
    Args:
        item_temp_ranges (list): Item's temperature range tags
        current_temp_range (str): Current temperature range
        
    Returns:
        bool: True if compatible, False if specifically incompatible
    """
    # If item has no temperature tags, assume it's compatible
    if not item_temp_ranges:
        return True
        
    # For cold temperatures (0-39°F), ONLY allow items tagged for cold
    if current_temp_range == "cold":
        return "cold" in item_temp_ranges
        
    # Check if current temperature range is in item's ranges
    if current_temp_range in item_temp_ranges:
        return True
        
    # For non-cold temperatures, check for adjacent compatibility
    adjacent_ranges = get_adjacent_temp_ranges(current_temp_range)
    for adj_range in adjacent_ranges:
        if adj_range in item_temp_ranges:
            # For hot temperatures, don't consider cool as adjacent
            if current_temp_range == "hot" and adj_range == "cool":
                return False
            return True
            
    # Special case - cold/cool are incompatible with hot
    if current_temp_range == "hot" and set(item_temp_ranges).intersection({"cold", "cool"}):
        return False
        
    # Special case - hot items are incompatible with cold
    if current_temp_range == "cold" and "hot" in item_temp_ranges:
        return False
        
    # Default to incompatible
    return False