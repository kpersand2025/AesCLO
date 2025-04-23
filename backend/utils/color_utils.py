# utils/color_utils.py

def is_neutral_color(color_name):
    """
    Check if a color is neutral
    """
    neutral_colors = ["black", "white", "gray", "beige", "brown"]
    return color_name.lower() in neutral_colors

def get_matching_colors(color_name):
    """
    Return a list of colors that go well with the given color
    Using a simple predefined lookup table
    """
    color_matches = {
        "black": ["black", "white", "gray", "red", "blue", "green", "purple", "yellow"],
        "white": ["black", "blue", "red", "brown", "gray", "purple", "green"],
        "gray": ["black", "white", "blue", "purple", "red", "pink"],
        "blue": ["brown", "beige", "navy", "yellow", "blue"],
        "navy": ["white", "gray", "blue", "red"],
        "red": ["black", "white", "gray", "navy", "red"],
        "green": ["white", "black", "brown", "gray", "beige"],
        "brown": ["white", "beige", "black","blue", "green", "red"],
        "purple": ["white", "black", "gray", "pink"],
        "yellow": ["blue", "gray", "black", "purple"],
        "pink": ["white", "gray", "navy", "black", "purple"],
        "beige": ["brown", "navy", "blue","green", "blue", "black"],
        "orange": ["blue", "navy", "white", "gray", "black"]
    }
    
    # Default to matching with neutrals if color not in our dictionary
    return color_matches.get(color_name.lower(), ["black", "white", "gray"])

def calculate_color_match_score(item1, item2):
    """
    Calculate a simple color match score between two items
    Returns a score between 0 and 1
    """
    # If either item doesn't have colors, return a neutral score
    if 'colors' not in item1 or 'colors' not in item2 or not item1['colors'] or not item2['colors']:
        return 0.5
    
    # Get the dominant color names of each item
    color1_name = item1['colors'][0]['name'].lower()
    color2_name = item2['colors'][0]['name'].lower()
    
    # If the colors are the same, it's a match
    if color1_name == color2_name:
        return 0.8
    
    # If either color is neutral, it's a good match
    if is_neutral_color(color1_name) or is_neutral_color(color2_name):
        return 0.9
    
    # Check if the colors are in each other's matching lists
    if color2_name in get_matching_colors(color1_name) or color1_name in get_matching_colors(color2_name):
        return 1.0
    
    # Default score for colors that don't have a specific rule
    return 0.3

def get_color_name(rgb):
    """
    Function to map RGB values to common color names that better match human perception.
    Takes an RGB tuple and returns a color name string.
    Teal and turquoise are categorized as either blue or green based on dominant component.
    """
    r, g, b = rgb
    
    # Handle grayscale colors
    if abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15:
        if r < 40:
            return "black"
        elif r < 120:
            return "gray"
        elif r < 220:
            return "gray"  # Lighter gray
        else:
            return "white"
    
    # If any component is very low, it's most likely not that color
    # Calculate color intensities and total intensity
    total = r + g + b
    if total < 40:  # Very dark color
        return "black"
    
    # Calculate proportions instead of absolute values
    # This helps with better color categorization
    r_ratio = r / total if total > 0 else 0
    g_ratio = g / total if total > 0 else 0
    b_ratio = b / total if total > 0 else 0

    # Add special case for dark olive green / army green
    if (60 <= r <= 90) and (59 <= g <= 85) and (40 <= b <= 65) and r/g > 0.9 and r/g < 1.2:
        return "green"  # Dark olive/army green
    
    # Define thresholds for color categories
    high_threshold = 0.4
    mid_threshold = 0.3
    low_threshold = 0.2
    very_low_threshold = 0.1
    
    # Red hues
    if r_ratio > high_threshold and g_ratio < mid_threshold and b_ratio < mid_threshold:
        if r > 220 and g > 150:
            return "pink" if b > 150 else "orange" if g > 180 else "red"
        elif r > 160 and g < 80 and b < 80:
            return "red"  # Pure red
        elif r > 140 and g > 60 and g < 110 and b < 100:
            return "red"  # Burgundy/maroon still reads as red to most people
        elif r > 160 and g > 110 and b < 100:
            return "orange" if g > 130 else "red"
        else:
            # For darker reds, check red dominance ratio
            red_dominance = r / max(g, b) if max(g, b) > 0 else 2
            return "brown" if (r < 120 and red_dominance < 3.0) else "red"
    
    # Orange/Brown hues
    if r_ratio > mid_threshold and g_ratio > low_threshold and g_ratio < high_threshold and b_ratio < mid_threshold:
        if r > 180 and g > 140 and b < 100:
            return "orange"
        elif r > 130 and g > 90 and b < 80:
            return "brown"
        elif r > 180 and g > 160 and b > 100:
            return "beige" if g > 170 and b > 140 else "brown"
        return "brown"
    
    # Yellow hues
    if r_ratio > mid_threshold and g_ratio > mid_threshold and b_ratio < mid_threshold:
        if r > 180 and g > 180 and b < 120:
            return "yellow"
        elif r > 190 and g > 170 and b > 130:
            return "beige"
        return "brown" if r < 150 else "yellow"
    
    # Green hues
    if g_ratio > high_threshold and r_ratio < high_threshold and b_ratio < high_threshold:
        if g > 130:
            if r > 130 and b < 100:
                return "green"  # Olive green
            return "green"
        return "green"
    
    # Modified: Teal/Cyan/Turquoise colors now classified as either blue or green
    if g_ratio > mid_threshold and b_ratio > mid_threshold and r_ratio < mid_threshold:
        # Compare green and blue values to determine if it appears more blue or green to humans
        if g > b * 1.2:  # Green is significantly higher - appears more green
            return "green"
        elif b > g * 1.1:  # Blue is higher - appears more blue
            return "blue"
        elif g > b:  # Green is slightly higher
            return "green"
        else:  # Blue is equal or slightly higher
            return "blue"
    
    # Blue hues
    if b_ratio > high_threshold and r_ratio < high_threshold and g_ratio < high_threshold:
        if b > 150:
            if r < 80 and g < 80:
                return "navy" if b < 170 else "blue"
            return "blue"
        return "navy"
    
    # Purple hues
    if r_ratio > low_threshold and r_ratio < high_threshold and b_ratio > mid_threshold and g_ratio < mid_threshold:
        if r > 150 and b > 150:
            return "purple" if r < 180 else "pink"
        return "purple"
    
    # Pink hues
    if r_ratio > mid_threshold and b_ratio > low_threshold and g_ratio < mid_threshold:
        if r > 180 and b > 140:
            return "pink"
        return "purple"
    
    # Beige/Tan hues - handle colors like RGB(201, 176, 146)
    if r > 180 and g > 150 and b > 120 and r > g > b:
        return "beige"
    
    # Handle other edge cases
    if r > 190 and g > 170 and b > 140:
        return "beige"
    
    # Handle taupe/grayish-brown colors
    if r > g > b and 120 < r < 180 and 100 < g < 160 and 90 < b < 150:
        return "brown" 
    
    # Fallback
    return "unknown"