# utils/outfit_generator.py - Improved color coordination while keeping all original functions
import random
from utils.color_utils import calculate_color_match_score, is_neutral_color, get_matching_colors

def has_color(item, color_name):
    """
    Check if an item has a specific color in its dominant colors ONLY
    Returns True if the item has the color, False otherwise
    
    Args:
        item: The clothing item to check
        color_name: The color name to look for
    """
    # Check dominant colors only
    if 'colors' in item and item['colors']:
        for color_data in item['colors']:
            if color_data['name'].lower() == color_name.lower():
                # If it's an exact match, return True
                return True
    
    # Check if any of the item's dominant colors match well with this color
    if 'colors' in item and item['colors']:
        for color_data in item['colors']:
            item_color = color_data['name'].lower()
            # Check if the target color is in the list of colors that match with the item's color
            if color_name.lower() in get_matching_colors(item_color):
                return True
    
    return False

def is_item_neutral_color(item):
    """
    Check if an item has ONLY neutral colors (black, white, gray, beige, brown)
    Returns True if ALL of the item's colors are neutral, False otherwise
    """
    neutral_colors = ["black", "white", "gray", "beige", "brown"]
    
    if 'colors' in item and item['colors'] and len(item['colors']) > 0:
        # Check all detected colors (up to 3)
        for color_data in item['colors']:
            color_name = color_data['name'].lower()
            # If any non-neutral color is found, return False
            if color_name not in neutral_colors:
                return False
        # If we've checked all colors and they're all neutral, return True
        return True
    
    return False

# Add this new function - it's not in your original file but used in the weather_outfit_generator.py
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

def is_complementary_color(color1, color2):
    """
    Check if two colors are complementary based on the matching colors list
    Returns True if the colors are complementary, False otherwise
    """
    if color1 == color2:
        return False  # Same color is not complementary
        
    if not color1 or not color2:
        return False
        
    # Check if either color is in the matching colors list of the other
    return color2 in get_matching_colors(color1) or color1 in get_matching_colors(color2)

def get_item_dominant_color(item):
    """
    Get the dominant color of an item
    Returns the dominant color name or None if not available
    """
    if 'colors' in item and item['colors'] and len(item['colors']) > 0:
        return item['colors'][0]['name'].lower()
    return None

def calculate_dominant_color_match_score(item1, item2):
    """
    Calculate a color match score between two items, considering ONLY dominant colors
    Returns a score between 0 and 1
    """
    # Check if items have dominant color information
    has_item1_colors = ('colors' in item1 and item1['colors'])
    has_item2_colors = ('colors' in item2 and item2['colors'])
    
    # If either item has no color information, return a neutral score
    if not has_item1_colors or not has_item2_colors:
        return 0.5
    
    # Get dominant colors from both items
    item1_colors = [c['name'].lower() for c in item1['colors']]
    item2_colors = [c['name'].lower() for c in item2['colors']]
    
    if not item1_colors or not item2_colors:
        return 0.5
    
    # Calculate different match scenarios
    
    # 1. Direct color match: a dominant color from one item matches a dominant color from the other
    dominant_match = False
    for color1 in item1_colors:
        for color2 in item2_colors:
            if color1 == color2:
                dominant_match = True
                break
    
    # 2. Neutral color scenario: if either item has a neutral dominant color
    neutral_dominance = False
    if is_neutral_color(item1_colors[0]) or is_neutral_color(item2_colors[0]):
        neutral_dominance = True
    
    # 3. Color harmony: check if colors from one item are in the matching list of the other
    color_harmony = False
    for color1 in item1_colors:
        for color2 in item2_colors:
            if color2 in get_matching_colors(color1) or color1 in get_matching_colors(color2):
                color_harmony = True
                break
    
    # Calculate final score based on match types
    if dominant_match:
        return 0.95  # Highest score for dominant-dominant match
    elif neutral_dominance:
        return 0.85  # High score if one item has a neutral dominant color
    elif color_harmony:
        return 0.80  # Good score for harmonious colors
    else:
        return 0.3   # Low score for no match

def has_matching_occasion(item1, item2):
    """
    Check if two items share at least one occasion tag
    Returns True if they share an occasion, False otherwise
    """
    # If either item doesn't have occasion information, return False
    if not item1.get('occasions') or not item2.get('occasions'):
        return False
    
    # Check for common occasions
    for occasion in item1['occasions']:
        if occasion in item2['occasions']:
            return True
    
    return False

def is_color_match_suitable(top_color, bottom_color):
    """
    Check if a bottom color is suitable to match with a top color
    A suitable bottom color is either:
    1. The same color as the top
    2. A neutral color (black, white, gray, beige, brown)
    3. A complementary color according to color matching rules
    
    Args:
        top_color: The dominant color of the top
        bottom_color: The dominant color of the bottom
        
    Returns:
        bool: True if the bottom color is suitable for the top, False otherwise
    """
    if not top_color or not bottom_color:
        return True  # If we don't have color info, consider it suitable
        
    # Check if same color
    if top_color == bottom_color:
        return True
        
    # Check if bottom is neutral color
    if is_neutral_color(bottom_color):
        return True
        
    # Check if colors are complementary
    return is_complementary_color(top_color, bottom_color)

def generate_color_coordinated_outfit(tops, bottoms, shoes, base_color=None):
    """
    Generate a color-coordinated outfit from the given items
    If base_color is provided, ALWAYS include a top with that color
    Ensures that chosen items share at least one occasion tag and temperature range
    Ensures bottoms are same color as top, neutral, or complementary
    Increases chance of shoes matching top color
    Returns a tuple of (top, bottom, shoes) where bottom may be None for complete tops
    """
    if not tops or not shoes:
        return None, None, None
    
    # If base color is provided, ensure some item has that color (preferably top)
    if base_color:
        # Find tops that match the selected base color (in dominant colors only)
        matching_tops = [item for item in tops if has_color(item, base_color)]
        
        # If no tops with the selected color, return None
        if not matching_tops:
            return None, None, None
        
        # Filter tops by those having both occasion and temperature tags
        valid_tops = []
        for top in matching_tops:
            has_occasion = 'occasions' in top and top['occasions'] and len(top['occasions']) > 0
            has_temp_range = 'temperature_range' in top and top['temperature_range'] and len(top['temperature_range']) > 0
            if has_occasion and has_temp_range:
                valid_tops.append(top)
            
        # If no valid tops, fall back to all matching tops
        if not valid_tops:
            valid_tops = matching_tops
            
        # Select a random top with the selected color from valid tops
        selected_top = random.choice(valid_tops)
        
        # Get the dominant color of the selected top
        top_dominant_color = get_item_dominant_color(selected_top)
        
        # Check if the selected top is a "complete" top (dress, jumpsuit, etc.)
        is_complete_top = selected_top.get("subcategory") == "complete"
        
        # If it's a complete top, skip bottom selection
        if is_complete_top:
            # Find matching shoes based on the selected top only
            # Filter shoes that share at least one occasion tag and temperature range with the top
            occasion_matching_shoes = []
            if 'occasions' in selected_top and selected_top['occasions']:
                occasion_matching_shoes = [shoe for shoe in shoes if 
                                          'occasions' in shoe and shoe['occasions'] and
                                          any(occasion in selected_top['occasions'] for occasion in shoe['occasions'])]
            
            # If no shoes with matching occasions, fall back to all shoes
            if not occasion_matching_shoes:
                occasion_matching_shoes = shoes
            
            # Further filter shoes by temperature range
            temp_matching_shoes = []
            if 'temperature_range' in selected_top and selected_top['temperature_range']:
                temp_matching_shoes = [shoe for shoe in occasion_matching_shoes if 
                                      'temperature_range' in shoe and shoe['temperature_range'] and
                                      any(temp in selected_top['temperature_range'] for temp in shoe['temperature_range'])]
            
            # If no shoes with matching temperature ranges, fall back to occasion matching shoes
            if not temp_matching_shoes:
                temp_matching_shoes = occasion_matching_shoes
            
            # *** IMPROVED SHOE SELECTION: Group shoes by color matching with top ***
            # Group 1: Shoes with the same dominant color as the top
            same_color_shoes = []
            # Group 2: Shoes with neutral dominant colors
            neutral_shoes = []
            # Group 3: Shoes with complementary colors to the top
            complementary_shoes = []
            # Group 4: All other shoes
            other_shoes = []
            
            for shoe in temp_matching_shoes:
                shoe_dominant_color = get_item_dominant_color(shoe)
                
                if not shoe_dominant_color:
                    other_shoes.append(shoe)
                    continue
                    
                # Check if shoe has same dominant color as top
                if shoe_dominant_color == top_dominant_color:
                    same_color_shoes.append(shoe)
                # Check if shoe has neutral dominant color
                elif is_neutral_color(shoe_dominant_color):
                    neutral_shoes.append(shoe)
                # Check if shoe color is complementary to top color
                elif is_complementary_color(top_dominant_color, shoe_dominant_color):
                    complementary_shoes.append(shoe)
                else:
                    other_shoes.append(shoe)
            
            # *** IMPROVED: Select shoes with weighted probability ***
            # 60% chance for same color shoes
            # 30% chance for neutral shoes
            # 10% chance for complementary shoes
            # Only if none of the above are available, use other shoes
            all_options = []
            
            if same_color_shoes:
                all_options.append((same_color_shoes, 60))
            if neutral_shoes:
                all_options.append((neutral_shoes, 30))
            if complementary_shoes:
                all_options.append((complementary_shoes, 10))
                
            # If we have no specific matches, use all available shoes
            if not all_options:
                all_options = [(temp_matching_shoes, 100)]
                
            # Select shoe group based on weighted probabilities
            shoes_group, _ = random.choices(
                all_options,
                weights=[opt[1] for opt in all_options],
                k=1
            )[0]
            
            # Final scoring for the selected group
            scored_shoes = []
            for shoe in shoes_group:
                # Calculate color match score
                color_score = calculate_dominant_color_match_score(selected_top, shoe)
                
                # Check if the shoe has a matching occasion with the top
                occasion_bonus = 0
                if has_matching_occasion(selected_top, shoe):
                    occasion_bonus = 0.35
                
                # Check if the shoe has a matching temperature range with the top
                temp_bonus = 0
                if has_matching_temperature_range(selected_top, shoe):
                    temp_bonus = 0.25
                
                # Combine bonuses, but cap at a maximum of 60% total boost
                total_bonus = min(0.6, occasion_bonus + temp_bonus)
                final_score = min(1.0, color_score * (1 + total_bonus))
                
                scored_shoes.append((shoe, final_score))
            
            # Sort by score and get top matches
            scored_shoes.sort(key=lambda x: x[1], reverse=True)
            top_shoes = scored_shoes[:min(3, len(scored_shoes))]
            if not top_shoes:
                return None, None, None
                
            best_shoe = random.choices(
                [item[0] for item in top_shoes], 
                weights=[item[1] for item in top_shoes],
                k=1
            )[0]
            
            # Return outfit with no bottom
            return selected_top, None, best_shoe
        
        # For standard tops, continue with normal bottom selection
        if not bottoms:
            return None, None, None
            
        # Filter bottoms that share at least one occasion with the top
        occasion_matching_bottoms = []
        if 'occasions' in selected_top and selected_top['occasions']:
            occasion_matching_bottoms = [bottom for bottom in bottoms if 
                                        'occasions' in bottom and bottom['occasions'] and
                                        any(occasion in selected_top['occasions'] for occasion in bottom['occasions'])]
        
        # If no bottoms with matching occasions, fall back to all bottoms
        if not occasion_matching_bottoms:
            occasion_matching_bottoms = bottoms
        
        # Further filter bottoms by temperature range
        temp_matching_bottoms = []
        if 'temperature_range' in selected_top and selected_top['temperature_range']:
            temp_matching_bottoms = [bottom for bottom in occasion_matching_bottoms if 
                                    'temperature_range' in bottom and bottom['temperature_range'] and
                                    any(temp in selected_top['temperature_range'] for temp in bottom['temperature_range'])]
        
        # If no bottoms with matching temperature ranges, fall back to occasion matching bottoms
        if not temp_matching_bottoms:
            temp_matching_bottoms = occasion_matching_bottoms
            
        # *** IMPROVED BOTTOM SELECTION: Only include bottoms with suitable colors ***
        # Filter bottoms to only include:
        # 1. Same color as top
        # 2. Neutral colors
        # 3. Complementary colors
        filtered_bottoms = []
        
        for bottom in temp_matching_bottoms:
            bottom_dominant_color = get_item_dominant_color(bottom)
            
            # Skip if we can't determine bottom color
            if not bottom_dominant_color:
                continue
                
            # Check if bottom color is suitable for the top
            if is_color_match_suitable(top_dominant_color, bottom_dominant_color):
                filtered_bottoms.append(bottom)
        
        # If no suitable bottoms found, fall back to neutral bottoms if available
        if not filtered_bottoms:
            neutral_bottoms = [bottom for bottom in temp_matching_bottoms if is_item_neutral_color(bottom)]
            if neutral_bottoms:
                filtered_bottoms = neutral_bottoms
            else:
                # If still no bottoms, fall back to all available bottoms
                filtered_bottoms = temp_matching_bottoms
            
        scored_bottoms = []
        for bottom in filtered_bottoms:
            # Calculate color match score using the dominant color method
            color_score = calculate_dominant_color_match_score(selected_top, bottom)
            
            # Apply occasion bonus if items have matching occasions
            occasion_bonus = 0.35 if has_matching_occasion(selected_top, bottom) else 0
            
            # Apply temperature range bonus if items have matching temperature ranges
            temp_bonus = 0.25 if has_matching_temperature_range(selected_top, bottom) else 0
            
            # Apply a stronger bonus (35%) for same-color bottoms
            bottom_dominant_color = get_item_dominant_color(bottom)
            same_color_bonus = 0.35 if bottom_dominant_color and bottom_dominant_color == top_dominant_color else 0
            
            # Apply a 25% bonus for neutral colored bottoms
            neutral_bonus = 0.25 if is_item_neutral_color(bottom) else 0
            
            # Apply a 15% bonus for complementary colors
            complementary_bonus = 0
            if not same_color_bonus and not neutral_bonus and bottom_dominant_color:
                complementary_bonus = 0.15 if is_complementary_color(top_dominant_color, bottom_dominant_color) else 0
            
            # Combine the bonuses, but cap at a maximum of 75% total boost (increased)
            total_bonus = min(0.75, occasion_bonus + temp_bonus + same_color_bonus + neutral_bonus + complementary_bonus)
            final_score = min(1.0, color_score * (1 + total_bonus))
            
            scored_bottoms.append((bottom, final_score))
        
        # Sort by score and get top matches
        scored_bottoms.sort(key=lambda x: x[1], reverse=True)
        top_bottoms = scored_bottoms[:min(3, len(scored_bottoms))]  # Using top 3 candidates
        
        if not top_bottoms:
            return None, None, None
            
        best_bottom = random.choices(
            [item[0] for item in top_bottoms], 
            weights=[item[1] for item in top_bottoms],
            k=1
        )[0]
        
        # Now get the bottom's dominant color for shoe selection
        bottom_dominant_color = get_item_dominant_color(best_bottom)
        
        # Now, find shoes that match both the top and bottom in terms of occasion and temperature range
        occasion_matching_shoes = []
        top_occasions = selected_top.get('occasions', [])
        bottom_occasions = best_bottom.get('occasions', [])
        
        # Find common occasions between top and bottom
        common_occasions = []
        if top_occasions and bottom_occasions:
            common_occasions = [occasion for occasion in top_occasions if occasion in bottom_occasions]
        
        # If there are common occasions, filter shoes by those common occasions
        if common_occasions:
            occasion_matching_shoes = [shoe for shoe in shoes if 
                                     'occasions' in shoe and shoe['occasions'] and
                                     any(occasion in common_occasions for occasion in shoe['occasions'])]
        else:
            # If no common occasions, find shoes that match either top or bottom
            shoes_matching_top = [shoe for shoe in shoes if 
                                'occasions' in shoe and shoe['occasions'] and
                                any(occasion in top_occasions for occasion in shoe['occasions'])] if top_occasions else []
                                
            shoes_matching_bottom = [shoe for shoe in shoes if 
                                    'occasions' in shoe and shoe['occasions'] and
                                    any(occasion in bottom_occasions for occasion in shoe['occasions'])] if bottom_occasions else []
                                    
            # Combine the two lists and remove duplicates
            occasion_matching_shoes = list(set(shoes_matching_top + shoes_matching_bottom))
        
        # If no shoes with matching occasions, fall back to all shoes
        if not occasion_matching_shoes:
            occasion_matching_shoes = shoes
        
        # Similarly, find common temperature ranges
        top_temp_ranges = selected_top.get('temperature_range', [])
        bottom_temp_ranges = best_bottom.get('temperature_range', [])
        
        common_temp_ranges = []
        if top_temp_ranges and bottom_temp_ranges:
            common_temp_ranges = [temp for temp in top_temp_ranges if temp in bottom_temp_ranges]
        
        # Filter shoes by temperature range
        temp_matching_shoes = []
        if common_temp_ranges:
            temp_matching_shoes = [shoe for shoe in occasion_matching_shoes if 
                                  'temperature_range' in shoe and shoe['temperature_range'] and
                                  any(temp in common_temp_ranges for temp in shoe['temperature_range'])]
        else:
            # If no common temperature ranges, find shoes that match either top or bottom
            shoes_matching_top_temp = [shoe for shoe in occasion_matching_shoes if 
                                     'temperature_range' in shoe and shoe['temperature_range'] and
                                     any(temp in top_temp_ranges for temp in shoe['temperature_range'])] if top_temp_ranges else []
                                    
            shoes_matching_bottom_temp = [shoe for shoe in occasion_matching_shoes if 
                                        'temperature_range' in shoe and shoe['temperature_range'] and
                                        any(temp in bottom_temp_ranges for temp in shoe['temperature_range'])] if bottom_temp_ranges else []
                                        
            # Combine the two lists and remove duplicates
            temp_matching_shoes = list(set(shoes_matching_top_temp + shoes_matching_bottom_temp))
        
        # If no shoes with matching temperature ranges, fall back to occasion matching shoes
        if not temp_matching_shoes:
            temp_matching_shoes = occasion_matching_shoes
            
        # *** IMPROVED: Categorize shoes by color matching priority ***
        # Group 1: Shoes with the same dominant color as the top (highest priority)
        same_as_top_shoes = []
        # Group 2: Shoes with the same dominant color as the bottom
        same_as_bottom_shoes = []
        # Group 3: Shoes with neutral colors
        neutral_shoes = []
        # Group 4: Shoes with complementary colors to the top
        complementary_to_top_shoes = []
        # Group 5: All other shoes
        other_shoes = []
        
        for shoe in temp_matching_shoes:
            shoe_dominant_color = get_item_dominant_color(shoe)
            
            if not shoe_dominant_color:
                other_shoes.append(shoe)
                continue
                
            # Check priority order for shoes
            if shoe_dominant_color == top_dominant_color:
                same_as_top_shoes.append(shoe)
            elif shoe_dominant_color == bottom_dominant_color:
                same_as_bottom_shoes.append(shoe)
            elif is_neutral_color(shoe_dominant_color):
                neutral_shoes.append(shoe)
            elif is_complementary_color(top_dominant_color, shoe_dominant_color):
                complementary_to_top_shoes.append(shoe)
            else:
                other_shoes.append(shoe)
        
        # *** IMPROVED: Select shoes with weighted probability ***
        # 50% chance for same-as-top-color shoes (increased from original)
        # 20% chance for same-as-bottom-color shoes
        # 20% chance for neutral shoes
        # 10% chance for complementary-to-top-color shoes
        all_options = []
        
        if same_as_top_shoes:
            all_options.append((same_as_top_shoes, 50))
        if same_as_bottom_shoes:
            all_options.append((same_as_bottom_shoes, 20))
        if neutral_shoes:
            all_options.append((neutral_shoes, 20))
        if complementary_to_top_shoes:
            all_options.append((complementary_to_top_shoes, 10))
            
        # If we have no specific matches, use all available shoes
        if not all_options:
            all_options = [(temp_matching_shoes, 100)]
            
        # Select shoe group based on weighted probabilities
        shoes_group, _ = random.choices(
            all_options,
            weights=[opt[1] for opt in all_options],
            k=1
        )[0]
        
        # Final scoring for the selected group
        scored_shoes = []
        for shoe in shoes_group:
            # Calculate color match scores with top and bottom
            top_color_score = calculate_dominant_color_match_score(selected_top, shoe)
            bottom_color_score = calculate_dominant_color_match_score(best_bottom, shoe)
            
            # Weight top color match more heavily (60% top, 40% bottom)
            weighted_color_score = (top_color_score * 0.6) + (bottom_color_score * 0.4)
            
            # Apply occasion match bonuses
            occasion_bonus = 0
            if has_matching_occasion(selected_top, shoe) and has_matching_occasion(best_bottom, shoe):
                # Bigger bonus if shoes match occasion of BOTH top and bottom
                occasion_bonus = 0.4
            elif has_matching_occasion(selected_top, shoe) or has_matching_occasion(best_bottom, shoe):
                # Smaller bonus if shoes match occasion of either top or bottom
                occasion_bonus = 0.25
                
            # Apply temperature range match bonuses
            temp_bonus = 0
            if has_matching_temperature_range(selected_top, shoe) and has_matching_temperature_range(best_bottom, shoe):
                # Bigger bonus if shoes match temperature range of BOTH top and bottom
                temp_bonus = 0.3
            elif has_matching_temperature_range(selected_top, shoe) or has_matching_temperature_range(best_bottom, shoe):
                # Smaller bonus if shoes match temperature range of either top or bottom
                temp_bonus = 0.15
            
            # Apply color match bonuses
            shoe_dominant_color = get_item_dominant_color(shoe)
            
            color_bonus = 0
            if shoe_dominant_color == top_dominant_color:
                # Biggest bonus for matching top color
                color_bonus = 0.3
            elif shoe_dominant_color == bottom_dominant_color:
                # Good bonus for matching bottom color
                color_bonus = 0.2
            elif is_neutral_color(shoe_dominant_color):
                # Decent bonus for neutral shoes
                color_bonus = 0.15
                
            # Combine bonuses, but cap at a maximum of 80% total boost (increased)
            total_bonus = min(0.8, occasion_bonus + temp_bonus + color_bonus)
            final_score = min(1.0, weighted_color_score * (1 + total_bonus))
            
            scored_shoes.append((shoe, final_score))
        
        # Sort by score and get top matches
        scored_shoes.sort(key=lambda x: x[1], reverse=True)
        top_shoes = scored_shoes[:min(3, len(scored_shoes))]
        
        if not top_shoes:
            return None, None, None
            
        best_shoe = random.choices(
            [item[0] for item in top_shoes], 
            weights=[item[1] for item in top_shoes],
            k=1
        )[0]
        
        return selected_top, best_bottom, best_shoe
    
    # Default flow if no base color provided - similar to above but starting with a random top
    # Choose a random top and check if it's complete
    base_item = random.choice(tops)
    is_complete_top = base_item.get("subcategory") == "complete"
    
    # Get the dominant color of the selected top
    top_dominant_color = get_item_dominant_color(base_item)
    
    if is_complete_top:
        # If it's a complete top, only select matching shoes
        # Use the improved shoe selection logic we developed above
        
        # Find occasion-matching shoes
        occasion_matching_shoes = []
        if 'occasions' in base_item and base_item['occasions']:
            occasion_matching_shoes = [shoe for shoe in shoes if 
                                     'occasions' in shoe and shoe['occasions'] and
                                     any(occasion in base_item['occasions'] for occasion in shoe['occasions'])]
        else:
            occasion_matching_shoes = shoes
            
        # Group shoes by color matching with top
        same_color_shoes = []
        neutral_shoes = []
        complementary_shoes = []
        other_shoes = []
        
        for shoe in occasion_matching_shoes:
            shoe_dominant_color = get_item_dominant_color(shoe)
            
            if not shoe_dominant_color:
                other_shoes.append(shoe)
                continue
                
            # Check if shoe has same dominant color as top
            if shoe_dominant_color == top_dominant_color:
                same_color_shoes.append(shoe)
            # Check if shoe has neutral dominant color
            elif is_neutral_color(shoe_dominant_color):
                neutral_shoes.append(shoe)
            # Check if shoe color is complementary to top color
            elif is_complementary_color(top_dominant_color, shoe_dominant_color):
                complementary_shoes.append(shoe)
            else:
                other_shoes.append(shoe)
        
        # Select shoes with weighted probability
        all_options = []
        
        if same_color_shoes:
            all_options.append((same_color_shoes, 60))
        if neutral_shoes:
            all_options.append((neutral_shoes, 30))
        if complementary_shoes:
            all_options.append((complementary_shoes, 10))
            
        # If we have no specific matches, use all available shoes
        if not all_options:
            all_options = [(occasion_matching_shoes, 100)]
            
        # Select shoe group based on weighted probabilities
        shoes_group, _ = random.choices(
            all_options,
            weights=[opt[1] for opt in all_options],
            k=1
        )[0]
        
        # Final scoring for selected group
        scored_shoes = []
        for shoe in shoes_group:
            # Calculate color match score
            color_score = calculate_dominant_color_match_score(base_item, shoe)
            
            # Add occasion and temperature bonuses
            occasion_bonus = 0.35 if has_matching_occasion(base_item, shoe) else 0
            temp_bonus = 0.25 if has_matching_temperature_range(base_item, shoe) else 0
            
            # Add color match bonus
            shoe_dominant_color = get_item_dominant_color(shoe)
            color_bonus = 0
            if shoe_dominant_color == top_dominant_color:
                color_bonus = 0.3  # Bonus for matching top color
            
            # Combine bonuses, capped at 70%
            total_bonus = min(0.7, occasion_bonus + temp_bonus + color_bonus)
            final_score = min(1.0, color_score * (1 + total_bonus))
            
            scored_shoes.append((shoe, final_score))
        
        # Sort by score and select top matches
        scored_shoes.sort(key=lambda x: x[1], reverse=True)
        top_shoes = scored_shoes[:min(3, len(scored_shoes))]
        
        if not top_shoes:
            return None, None, None
        
        best_shoe = random.choices(
            [item[0] for item in top_shoes], 
            weights=[item[1] for item in top_shoes],
            k=1
        )[0]
        
        return base_item, None, best_shoe
    else:
        # Normal flow for standard tops
        if not bottoms:
            return None, None, None
            
        # Filter bottoms that share occasion with the top
        occasion_matching_bottoms = []
        if 'occasions' in base_item and base_item['occasions']:
            occasion_matching_bottoms = [bottom for bottom in bottoms if 
                                       'occasions' in bottom and bottom['occasions'] and
                                       any(occasion in base_item['occasions'] for occasion in bottom['occasions'])]
        else:
            occasion_matching_bottoms = bottoms
            
        # Filter bottoms by suitable colors (same as top, neutral, or complementary)
        filtered_bottoms = []
        for bottom in occasion_matching_bottoms:
            bottom_dominant_color = get_item_dominant_color(bottom)
            
            if not bottom_dominant_color:
                continue
                
            if is_color_match_suitable(top_dominant_color, bottom_dominant_color):
                filtered_bottoms.append(bottom)
                
        # If no suitable bottoms, fall back to neutral or all bottoms
        if not filtered_bottoms:
            neutral_bottoms = [bottom for bottom in occasion_matching_bottoms if is_item_neutral_color(bottom)]
            if neutral_bottoms:
                filtered_bottoms = neutral_bottoms
            else:
                filtered_bottoms = occasion_matching_bottoms
                
        # Score bottoms and select best match
        scored_bottoms = []
        for bottom in filtered_bottoms:
            # Color match score
            color_score = calculate_dominant_color_match_score(base_item, bottom)
            
            # Occasion and temperature bonuses
            occasion_bonus = 0.35 if has_matching_occasion(base_item, bottom) else 0
            temp_bonus = 0.25 if has_matching_temperature_range(base_item, bottom) else 0
            
            # Color matching bonuses
            bottom_dominant_color = get_item_dominant_color(bottom)
            same_color_bonus = 0.35 if bottom_dominant_color and bottom_dominant_color == top_dominant_color else 0
            neutral_bonus = 0.25 if is_item_neutral_color(bottom) else 0
            complementary_bonus = 0
            if not same_color_bonus and not neutral_bonus and bottom_dominant_color:
                complementary_bonus = 0.15 if is_complementary_color(top_dominant_color, bottom_dominant_color) else 0
                
            # Combine bonuses, capped at 75%
            total_bonus = min(0.75, occasion_bonus + temp_bonus + same_color_bonus + neutral_bonus + complementary_bonus)
            final_score = min(1.0, color_score * (1 + total_bonus))
            
            scored_bottoms.append((bottom, final_score))
            
        # Sort by score and get top matches
        scored_bottoms.sort(key=lambda x: x[1], reverse=True)
        top_bottoms = scored_bottoms[:min(3, len(scored_bottoms))]
        
        if not top_bottoms:
            return None, None, None
            
        best_bottom = random.choices(
            [item[0] for item in top_bottoms], 
            weights=[item[1] for item in top_bottoms],
            k=1
        )[0]
        
        # Get bottom dominant color for shoe selection
        bottom_dominant_color = get_item_dominant_color(best_bottom)
        
        # Find shoes that match with both top and bottom
        # Prioritize shoes matching top color
        
        # Group shoes by color matching priority
        same_as_top_shoes = []
        same_as_bottom_shoes = []
        neutral_shoes = []
        complementary_shoes = []
        other_shoes = []
        
        # Get shoes that match occasion
        occasion_matching_shoes = []
        if 'occasions' in base_item and base_item['occasions'] and 'occasions' in best_bottom and best_bottom['occasions']:
            common_occasions = [occasion for occasion in base_item['occasions'] if occasion in best_bottom['occasions']]
            if common_occasions:
                occasion_matching_shoes = [shoe for shoe in shoes if 
                                        'occasions' in shoe and shoe['occasions'] and
                                        any(occasion in common_occasions for occasion in shoe['occasions'])]
            else:
                occasion_matching_shoes = shoes
        else:
            occasion_matching_shoes = shoes
            
        # Categorize shoes by color match
        for shoe in occasion_matching_shoes:
            shoe_dominant_color = get_item_dominant_color(shoe)
            
            if not shoe_dominant_color:
                other_shoes.append(shoe)
                continue
                
            if shoe_dominant_color == top_dominant_color:
                same_as_top_shoes.append(shoe)
            elif shoe_dominant_color == bottom_dominant_color:
                same_as_bottom_shoes.append(shoe)
            elif is_neutral_color(shoe_dominant_color):
                neutral_shoes.append(shoe)
            elif is_complementary_color(top_dominant_color, shoe_dominant_color):
                complementary_shoes.append(shoe)
            else:
                other_shoes.append(shoe)
                
        # Select shoes with weighted probability
        all_options = []
        
        if same_as_top_shoes:
            all_options.append((same_as_top_shoes, 50))
        if same_as_bottom_shoes:
            all_options.append((same_as_bottom_shoes, 20))
        if neutral_shoes:
            all_options.append((neutral_shoes, 20))
        if complementary_shoes:
            all_options.append((complementary_shoes, 10))
            
        # If no specific matches, use all shoes
        if not all_options:
            all_options = [(occasion_matching_shoes, 100)]
            
        # Select shoe group based on weighted probabilities
        shoes_group, _ = random.choices(
            all_options,
            weights=[opt[1] for opt in all_options],
            k=1
        )[0]
        
        # Final scoring for selected shoes
        scored_shoes = []
        for shoe in shoes_group:
            # Calculate color match scores
            top_color_score = calculate_dominant_color_match_score(base_item, shoe)
            bottom_color_score = calculate_dominant_color_match_score(best_bottom, shoe)
            
            # Weight top color match more (60% top, 40% bottom)
            weighted_color_score = (top_color_score * 0.6) + (bottom_color_score * 0.4)
            
            # Apply occasion match bonuses
            occasion_bonus = 0
            if has_matching_occasion(base_item, shoe) and has_matching_occasion(best_bottom, shoe):
                occasion_bonus = 0.4  # Matches both
            elif has_matching_occasion(base_item, shoe) or has_matching_occasion(best_bottom, shoe):
                occasion_bonus = 0.25  # Matches one
                
            # Apply temperature bonuses
            temp_bonus = 0
            if has_matching_temperature_range(base_item, shoe) and has_matching_temperature_range(best_bottom, shoe):
                temp_bonus = 0.3  # Matches both
            elif has_matching_temperature_range(base_item, shoe) or has_matching_temperature_range(best_bottom, shoe):
                temp_bonus = 0.15  # Matches one
                
            # Apply color match bonuses
            shoe_dominant_color = get_item_dominant_color(shoe)
            color_bonus = 0
            
            if shoe_dominant_color == top_dominant_color:
                color_bonus = 0.3  # Matches top
            elif shoe_dominant_color == bottom_dominant_color:
                color_bonus = 0.2  # Matches bottom
            elif is_neutral_color(shoe_dominant_color):
                color_bonus = 0.15  # Neutral color
                
            # Combine bonuses, capped at 80%
            total_bonus = min(0.8, occasion_bonus + temp_bonus + color_bonus)
            final_score = min(1.0, weighted_color_score * (1 + total_bonus))
            
            scored_shoes.append((shoe, final_score))
            
        # Sort by score and select top matches
        scored_shoes.sort(key=lambda x: x[1], reverse=True)
        top_shoes = scored_shoes[:min(3, len(scored_shoes))]
        
        if not top_shoes:
            return None, None, None
            
        best_shoe = random.choices(
            [item[0] for item in top_shoes], 
            weights=[item[1] for item in top_shoes],
            k=1
        )[0]
        
        return base_item, best_bottom, best_shoe

def select_matching_shoes_for_complete_top(top, shoes):
    """
    Select shoes that match well with a complete top (dress, jumpsuit)
    Returns the best matching shoe
    """
    scored_shoes = []
    for shoe in shoes:
        # Calculate color match score
        color_score = calculate_dominant_color_match_score(top, shoe)
        
        # Apply occasion bonus if items have matching occasions
        occasion_bonus = 0.35 if has_matching_occasion(top, shoe) else 0
        
        # Calculate final score with occasion bonus
        final_score = min(1.0, color_score * (1 + occasion_bonus))
        
        scored_shoes.append((shoe, final_score))
    
    # Sort by score and get top matches
    scored_shoes.sort(key=lambda x: x[1], reverse=True)
    top_shoes = scored_shoes[:min(3, len(scored_shoes))]
    
    # Select best shoe with weighted random choice
    if top_shoes:
        best_shoe = random.choices(
            [item[0] for item in top_shoes], 
            weights=[item[1] for item in top_shoes],
            k=1
        )[0]
        return best_shoe
    
    # Fallback if no shoes are available
    return None

def select_matching_items(base_item, item_list1, item_list2):
    """
    Select items from item_list1 and item_list2 that match well with the base_item
    Now also considers occasion matching and prefers neutral bottoms
    Returns a tuple of (best_item1, best_item2)
    """
    # Find matching items for the first list (typically bottoms)
    scored_items1 = []
    for item in item_list1:
        # Calculate color match score
        color_score = calculate_dominant_color_match_score(base_item, item)
        
        # Apply occasion bonus if items have matching occasions (increased from 0.2 to 0.35)
        occasion_bonus = 0.35 if has_matching_occasion(base_item, item) else 0
        
        # Apply a 25% bonus for neutral colored bottoms
        neutral_bonus = 0.25 if is_item_neutral_color(item) else 0
        
        # Combine the bonuses, but cap at a maximum of 60% total boost (increased from 50%)
        total_bonus = min(0.6, occasion_bonus + neutral_bonus)
        final_score = min(1.0, color_score * (1 + total_bonus))
        
        scored_items1.append((item, final_score))
    
    # Sort by score and get top matches
    scored_items1.sort(key=lambda x: x[1], reverse=True)
    top_items1 = scored_items1[:min(3, len(scored_items1))]  # Using top 3 candidates
    
    if not top_items1:
        return None, None
        
    best_item1 = random.choices(
        [item[0] for item in top_items1], 
        weights=[item[1] for item in top_items1],
        k=1
    )[0]
    
    # Find matching items for the second list (typically shoes)
    scored_items2 = []
    for item in item_list2:
        # Calculate color match scores with both base item and first selected item
        base_color_score = calculate_dominant_color_match_score(base_item, item)
        item1_color_score = calculate_dominant_color_match_score(best_item1, item)
        avg_color_score = (base_color_score + item1_color_score) / 2
        
        # Calculate occasion match bonus - increased values
        occasion_bonus = 0
        if has_matching_occasion(base_item, item) and has_matching_occasion(best_item1, item):
            # Bigger bonus if item matches occasion of BOTH base item and item1 (increased from 0.3 to 0.4)
            occasion_bonus = 0.4
        elif has_matching_occasion(base_item, item) or has_matching_occasion(best_item1, item):
            # Smaller bonus if item matches occasion of either base item or item1 (increased from 0.15 to 0.25)
            occasion_bonus = 0.25
            
        # Calculate final score with occasion bonus
        final_score = min(1.0, avg_color_score * (1 + occasion_bonus))
        
        scored_items2.append((item, final_score))
    
    # Sort by score and get top matches
    scored_items2.sort(key=lambda x: x[1], reverse=True)
    top_items2 = scored_items2[:min(3, len(scored_items2))]  # Using top 3 candidates
    
    if not top_items2:
        return best_item1, None
        
    best_item2 = random.choices(
        [item[0] for item in top_items2], 
        weights=[item[1] for item in top_items2],
        k=1
    )[0]
    
    return best_item1, best_item2

def has_matching_temperature_range(item1, item2):
    """
    Check if two items share at least one temperature range tag
    Returns True if they share a temperature range, False otherwise
    """
    # If either item doesn't have temperature range information, return False
    if not item1.get('temperature_range') or not item2.get('temperature_range'):
        return False
    
    # Check for common temperature ranges
    for temp_range in item1['temperature_range']:
        if temp_range in item2['temperature_range']:
            return True
    
    return False

def generate_occasion_based_outfit(tops, bottoms, shoes, target_occasion="casual"):
    """
    Generate an outfit appropriate for a specific occasion from the given items
    with enhanced color coordination and temperature range matching to ensure visual
    coherence and appropriate outfit for weather conditions.
    
    Args:
        tops (list): List of top items
        bottoms (list): List of bottom items
        shoes (list): List of shoe items
        target_occasion (str): The target occasion for the outfit. 
                               Options: "casual", "work/professional", "formal", 
                                        "athletic/sport", "lounge/sleepwear"
    
    Returns:
        tuple: (top, bottom, shoes) where bottom may be None for complete tops
    """
    if not tops or not shoes:
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
    if not tops_matching_occasion or not shoes_matching_occasion:
        # We need at least tops and shoes
        tops_matching_occasion = tops if not tops_matching_occasion else tops_matching_occasion
        shoes_matching_occasion = shoes if not shoes_matching_occasion else shoes_matching_occasion
    
    # Check if we have bottoms when needed
    if not bottoms_matching_occasion:
        # Check if all tops are "complete" (don't need bottoms)
        all_complete_tops = all(top.get("subcategory") == "complete" for top in tops_matching_occasion)
        if not all_complete_tops:
            # We need bottoms for standard tops
            bottoms_matching_occasion = bottoms
    
    # Filter tops by those having both occasion and temperature tags
    valid_tops = []
    for top in tops_matching_occasion:
        has_temp_range = 'temperature_range' in top and top['temperature_range'] and len(top['temperature_range']) > 0
        if has_temp_range:
            valid_tops.append(top)
    
    # If no valid tops, fall back to all tops matching occasion
    if not valid_tops:
        valid_tops = tops_matching_occasion
    
    # Select a random top for this occasion from valid tops
    selected_top = random.choice(valid_tops)
    
    # Get the dominant color of the selected top
    top_dominant_color = get_item_dominant_color(selected_top)
    
    # Get temperature range from selected top
    top_temp_ranges = selected_top.get('temperature_range', [])
    
    # Check if the selected top is a "complete" top (dress, jumpsuit, etc.)
    is_complete_top = selected_top.get("subcategory") == "complete"
    
    if is_complete_top:
        # For complete tops, skip bottom selection and directly match with shoes
        # First, filter shoes by temperature range
        temp_matching_shoes = []
        if top_temp_ranges:
            temp_matching_shoes = [shoe for shoe in shoes_matching_occasion if 
                                  'temperature_range' in shoe and shoe['temperature_range'] and
                                  any(temp in top_temp_ranges for temp in shoe['temperature_range'])]
        else:
            temp_matching_shoes = shoes_matching_occasion
            
        # If no shoes with matching temperature ranges, fall back to all shoes matching occasion
        if not temp_matching_shoes:
            temp_matching_shoes = shoes_matching_occasion
            
        # Group shoes by color matching with top
        same_color_shoes = []
        neutral_shoes = []
        complementary_shoes = []
        other_shoes = []
        
        for shoe in temp_matching_shoes:
            shoe_dominant_color = get_item_dominant_color(shoe)
            
            if not shoe_dominant_color:
                other_shoes.append(shoe)
                continue
                
            # Check if shoe has same dominant color as top
            if shoe_dominant_color == top_dominant_color:
                same_color_shoes.append(shoe)
            # Check if shoe has neutral dominant color
            elif is_neutral_color(shoe_dominant_color):
                neutral_shoes.append(shoe)
            # Check if shoe color is complementary to top color
            elif is_complementary_color(top_dominant_color, shoe_dominant_color):
                complementary_shoes.append(shoe)
            else:
                other_shoes.append(shoe)
        
        # Select shoes with weighted probability
        # 60% chance for same color shoes
        # 30% chance for neutral shoes
        # 10% chance for complementary shoes
        all_options = []
        
        if same_color_shoes:
            all_options.append((same_color_shoes, 60))
        if neutral_shoes:
            all_options.append((neutral_shoes, 30))
        if complementary_shoes:
            all_options.append((complementary_shoes, 10))
            
        # If we have no specific matches, use all available shoes
        if not all_options:
            all_options = [(temp_matching_shoes, 100)]
            
        # Select shoe group based on weighted probabilities
        shoes_group, _ = random.choices(
            all_options,
            weights=[opt[1] for opt in all_options],
            k=1
        )[0]
        
        # Final scoring for the selected group
        scored_shoes = []
        for shoe in shoes_group:
            # Calculate color match score
            color_score = calculate_dominant_color_match_score(selected_top, shoe)
            
            # Apply occasion match bonus
            occasion_bonus = 0.35 if "occasions" in shoe and shoe["occasions"] and target_occasion in shoe["occasions"] else 0
            
            # Apply temperature range match bonus
            temp_bonus = 0
            if has_matching_temperature_range(selected_top, shoe):
                temp_bonus = 0.3  # 30% bonus for matching temperature range
            
            # Apply color match bonus
            shoe_dominant_color = get_item_dominant_color(shoe)
            color_bonus = 0
            if shoe_dominant_color == top_dominant_color:
                color_bonus = 0.3  # 30% bonus for matching top color
            
            # Combine bonuses, but cap at 75% total boost
            total_bonus = min(0.75, occasion_bonus + temp_bonus + color_bonus)
            final_score = min(1.0, color_score * (1 + total_bonus))
            
            scored_shoes.append((shoe, final_score))
        
        # Sort by score and get top matches
        scored_shoes.sort(key=lambda x: x[1], reverse=True)
        top_shoes = scored_shoes[:min(3, len(scored_shoes))]
        
        if not top_shoes:
            return None, None, None
            
        best_shoe = random.choices(
            [item[0] for item in top_shoes], 
            weights=[item[1] for item in top_shoes],
            k=1
        )[0]
        
        return selected_top, None, best_shoe
    
    # For standard tops, continue with normal bottom and shoe selection
    if not bottoms_matching_occasion:
        # If no bottoms available for standard tops, can't create outfit
        return None, None, None
    
    # First, filter bottoms by temperature range
    temp_matching_bottoms = []
    if top_temp_ranges:
        temp_matching_bottoms = [bottom for bottom in bottoms_matching_occasion if 
                                'temperature_range' in bottom and bottom['temperature_range'] and
                                any(temp in top_temp_ranges for temp in bottom['temperature_range'])]
    else:
        temp_matching_bottoms = bottoms_matching_occasion
        
    # If no bottoms with matching temperature ranges, fall back to all bottoms matching occasion
    if not temp_matching_bottoms:
        temp_matching_bottoms = bottoms_matching_occasion
    
    # Filter bottoms to only include:
    # 1. Same color as top
    # 2. Neutral colors
    # 3. Complementary colors
    filtered_bottoms = []
    
    for bottom in temp_matching_bottoms:
        bottom_dominant_color = get_item_dominant_color(bottom)
        
        # Skip if we can't determine bottom color
        if not bottom_dominant_color:
            continue
            
        # Check if bottom color is suitable for the top
        if is_color_match_suitable(top_dominant_color, bottom_dominant_color):
            filtered_bottoms.append(bottom)
    
    # If no suitable bottoms found, fall back to neutral bottoms if available
    if not filtered_bottoms:
        neutral_bottoms = [bottom for bottom in temp_matching_bottoms if is_item_neutral_color(bottom)]
        if neutral_bottoms:
            filtered_bottoms = neutral_bottoms
        else:
            # If still no bottoms, fall back to all available bottoms
            filtered_bottoms = temp_matching_bottoms
        
    # Select bottom for standard tops
    scored_bottoms = []
    for bottom in filtered_bottoms:
        # Calculate color match score using the dominant color method
        color_score = calculate_dominant_color_match_score(selected_top, bottom)
        
        # Apply occasion match bonus
        occasion_bonus = 0.35 if "occasions" in bottom and bottom["occasions"] and target_occasion in bottom["occasions"] else 0
        
        # Apply temperature range match bonus
        temp_bonus = 0
        if has_matching_temperature_range(selected_top, bottom):
            temp_bonus = 0.3  # 30% bonus for matching temperature range
            
        # Apply color match bonuses
        bottom_dominant_color = get_item_dominant_color(bottom)
        same_color_bonus = 0.35 if bottom_dominant_color and bottom_dominant_color == top_dominant_color else 0
        neutral_bonus = 0.25 if is_item_neutral_color(bottom) else 0
        complementary_bonus = 0
        if not same_color_bonus and not neutral_bonus and bottom_dominant_color:
            complementary_bonus = 0.15 if is_complementary_color(top_dominant_color, bottom_dominant_color) else 0
        
        # Combine the bonuses, but cap at a maximum of 80% total boost
        total_bonus = min(0.8, occasion_bonus + temp_bonus + same_color_bonus + neutral_bonus + complementary_bonus)
        final_score = min(1.0, color_score * (1 + total_bonus))
        
        scored_bottoms.append((bottom, final_score))
    
    # Sort by score and get top matches
    if not scored_bottoms:
        # If we have no bottoms for standard tops, we can't create an outfit
        return None, None, None
        
    scored_bottoms.sort(key=lambda x: x[1], reverse=True)
    top_bottoms = scored_bottoms[:min(3, len(scored_bottoms))]
    best_bottom = random.choices(
        [item[0] for item in top_bottoms], 
        weights=[item[1] for item in top_bottoms],
        k=1
    )[0]
    
    # Get bottom dominant color for shoe selection
    bottom_dominant_color = get_item_dominant_color(best_bottom)
    
    # Get the common temperature ranges between top and bottom
    bottom_temp_ranges = best_bottom.get('temperature_range', [])
    common_temp_ranges = []
    if top_temp_ranges and bottom_temp_ranges:
        common_temp_ranges = [temp for temp in top_temp_ranges if temp in bottom_temp_ranges]
    
    # Filter shoes by temperature range
    temp_matching_shoes = []
    if common_temp_ranges:
        temp_matching_shoes = [shoe for shoe in shoes_matching_occasion if 
                             'temperature_range' in shoe and shoe['temperature_range'] and
                             any(temp in common_temp_ranges for temp in shoe['temperature_range'])]
    else:
        # If no common temperature ranges, find shoes that match either top or bottom
        shoes_matching_top_temp = [shoe for shoe in shoes_matching_occasion if 
                                 'temperature_range' in shoe and shoe['temperature_range'] and
                                 any(temp in top_temp_ranges for temp in shoe['temperature_range'])] if top_temp_ranges else []
                                
        shoes_matching_bottom_temp = [shoe for shoe in shoes_matching_occasion if 
                                    'temperature_range' in shoe and shoe['temperature_range'] and
                                    any(temp in bottom_temp_ranges for temp in shoe['temperature_range'])] if bottom_temp_ranges else []
                                    
        # Combine the two lists and remove duplicates
        temp_matching_shoes = list(set(shoes_matching_top_temp + shoes_matching_bottom_temp))
    
    # If no shoes with matching temperature ranges, fall back to all shoes matching occasion
    if not temp_matching_shoes:
        temp_matching_shoes = shoes_matching_occasion
    
    # Group shoes by color matching priority
    same_as_top_shoes = []
    same_as_bottom_shoes = []
    neutral_shoes = []
    complementary_to_top_shoes = []
    other_shoes = []
    
    for shoe in temp_matching_shoes:
        shoe_dominant_color = get_item_dominant_color(shoe)
        
        if not shoe_dominant_color:
            other_shoes.append(shoe)
            continue
            
        # Check priority order for shoes
        if shoe_dominant_color == top_dominant_color:
            same_as_top_shoes.append(shoe)
        elif shoe_dominant_color == bottom_dominant_color:
            same_as_bottom_shoes.append(shoe)
        elif is_neutral_color(shoe_dominant_color):
            neutral_shoes.append(shoe)
        elif is_complementary_color(top_dominant_color, shoe_dominant_color):
            complementary_to_top_shoes.append(shoe)
        else:
            other_shoes.append(shoe)
    
    # Select shoes with weighted probability
    # 50% chance for same-as-top-color shoes
    # 20% chance for same-as-bottom-color shoes
    # 20% chance for neutral shoes
    # 10% chance for complementary-to-top-color shoes
    all_options = []
    
    if same_as_top_shoes:
        all_options.append((same_as_top_shoes, 50))
    if same_as_bottom_shoes:
        all_options.append((same_as_bottom_shoes, 20))
    if neutral_shoes:
        all_options.append((neutral_shoes, 20))
    if complementary_to_top_shoes:
        all_options.append((complementary_to_top_shoes, 10))
        
    # If we have no specific matches, use all available shoes
    if not all_options:
        all_options = [(temp_matching_shoes, 100)]
        
    # Select shoe group based on weighted probabilities
    shoes_group, _ = random.choices(
        all_options,
        weights=[opt[1] for opt in all_options],
        k=1
    )[0]
    
    # Find matching shoes based on the selected top and bottom
    scored_shoes = []
    for shoe in shoes_group:
        # Calculate color match scores with top and bottom
        top_score = calculate_dominant_color_match_score(selected_top, shoe)
        bottom_score = calculate_dominant_color_match_score(best_bottom, shoe)
        
        # Weight top color match more heavily (60% top, 40% bottom)
        weighted_color_score = (top_score * 0.6) + (bottom_score * 0.4)
        
        # Apply occasion match bonus
        occasion_bonus = 0.35 if "occasions" in shoe and shoe["occasions"] and target_occasion in shoe["occasions"] else 0
        
        # Apply temperature range match bonuses
        temp_bonus = 0
        if has_matching_temperature_range(selected_top, shoe) and has_matching_temperature_range(best_bottom, shoe):
            # Bigger bonus if shoes match temperature range of BOTH top and bottom
            temp_bonus = 0.4
        elif has_matching_temperature_range(selected_top, shoe) or has_matching_temperature_range(best_bottom, shoe):
            # Smaller bonus if shoes match temperature range of either top or bottom
            temp_bonus = 0.2
        
        # Apply color match bonuses
        shoe_dominant_color = get_item_dominant_color(shoe)
        color_bonus = 0
        
        if shoe_dominant_color == top_dominant_color:
            # Biggest bonus for matching top color
            color_bonus = 0.3
        elif shoe_dominant_color == bottom_dominant_color:
            # Good bonus for matching bottom color
            color_bonus = 0.2
        elif is_neutral_color(shoe_dominant_color):
            # Decent bonus for neutral shoes
            color_bonus = 0.15
        
        # Combine bonuses, but cap at a maximum of 85% total boost
        total_bonus = min(0.85, occasion_bonus + temp_bonus + color_bonus)
        final_score = min(1.0, weighted_color_score * (1 + total_bonus))
        
        scored_shoes.append((shoe, final_score))
    
    # Sort by score and get top matches
    scored_shoes.sort(key=lambda x: x[1], reverse=True)
    top_shoes = scored_shoes[:min(3, len(scored_shoes))]
    
    if not top_shoes:
        return None, None, None
        
    best_shoe = random.choices(
        [item[0] for item in top_shoes], 
        weights=[item[1] for item in top_shoes],
        k=1
    )[0]
    
    return selected_top, best_bottom, best_shoe