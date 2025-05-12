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
        "black": ["black", "white", "gray", "red", "blue", "green", "purple", "yellow", "navy"],
        "white": ["black", "blue", "red", "brown", "gray", "purple", "green", "navy"],
        "gray": ["black", "white", "blue", "purple", "red", "pink", "navy"],
        "blue": ["brown", "beige", "black", "gray", "white"],
        "navy": ["white", "gray", "orange", "pink", "beige", "black"],
        "red": ["black", "white", "gray", "red", "beige"],
        "green": ["white", "black", "brown", "gray", "beige"],
        "brown": ["white", "beige", "black", "blue", "green", "red", "navy"],
        "purple": ["white", "black", "gray", "pink"],
        "yellow": ["blue", "gray", "black", "purple", "navy"],
        "pink": ["white", "gray", "navy", "black", "purple"],
        "beige": ["brown", "navy", "blue", "green", "blue", "black", "red"],
        "orange": ["blue", "navy", "white", "gray", "black"]
    }
    
    # Default to matching with neutrals if color not in our dictionary
    return color_matches.get(color_name.lower(), ["black", "white", "gray", "navy"])

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
    Improved to better distinguish between red, pink, and orange colors.
    """
    r, g, b = rgb
    
    # Calculate proportions for color categorization
    total = r + g + b
    r_ratio = r / total if total > 0 else 0
    g_ratio = g / total if total > 0 else 0
    b_ratio = b / total if total > 0 else 0
    
    # Step 1: Handle true black cases first (very dark colors with very similar RGB values)
    if total < 90 and abs(r - g) <= 8 and abs(r - b) <= 8 and abs(g - b) <= 8:
        # These are true black colors - very low brightness and all channels similar
        return "black"
    
    # Step 2: Handle very dark color cases that should be black
    if total < 60:  # Very dark colors are black regardless of blue dominance
        return "black"
    
    # Step 3: Handle grayscale colors with better gray/white/black distinction
    if abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15:
        if r < 50:  # Very dark grayscale colors are black
            return "black"
        elif r < 180:  # Mid-range is gray
            return "gray"
        elif r < 230:  # Light gray range (180-230)
            return "gray"
        else:
            return "white"  # Only very bright grays are "white"
    
    # Special case for bright yellow colors
    if r > 180 and g > 150 and b < 100 and r_ratio > 0.4 and g_ratio > 0.35 and b_ratio < 0.15:
        if abs(r - g) < 80:  # Red and green should be fairly close for yellow
            return "yellow"
    
    #---------- RED, PINK, ORANGE IMPROVED CATEGORIZATION ----------#
    
    # IMPROVED RED detection - Pure reds have high red value with low green and blue
    if r > g and r > b:
        # Pure red: Very high red, very low green and blue
        if r > 160 and g < 90 and b < 90:
            # Special case for darker reds/burgundy/maroon
            if r < 200 and g < 60 and b < 60:
                return "red"  # These are dark/deep reds
                
            # Regular reds - high red saturation, low green and blue
            return "red"
            
        # ORANGE detection (high red, medium-high green, low blue)
        # True orange should have significant green component but much less blue
        if r > 180 and g > 90 and g/total > 0.25 and b < 90 and b/total < 0.2 and g > 1.7*b:
            # First check for true oranges (high red, reasonable green, very low blue)
            if r > g + 50 and g > b + 40:
                return "orange"
        
        # Additional orange check for bright orange tones
        if r > 220 and g > 120 and g < 180 and b < 60 and r > g and g > b*2:
            return "orange"
            
        # IMPROVED PINK detection - high red with significant blue component
        # True pinks should have a significant blue component relative to green
        if r > 180:
            # Light pinks/baby pinks: high red, high green, high blue, but red dominates
            if g > 150 and b > 150 and r > g and r > b and b > 0.85*g:
                return "pink"
                
            # Bright/hot pinks: high red, moderate green, higher blue
            if g < 150 and b > 90 and b > g:
                return "pink"
                
            # Rose/medium pinks: high red, moderate green and blue, where blue is significant
            if g < 150 and b > 80 and b > 0.7*g:
                return "pink"
        
        # Salmon/coral pinks (pinkish-orange): high red, medium green, lower blue
        if r > 200 and 90 <= g <= 160 and 60 <= b <= 110 and r > g + 60 and g > b + 20:
            if b > 75:  # Enough blue to be pinkish rather than orange
                return "pink"
            else:
                return "orange"  # Lower blue makes it more orange
    
    #----- END OF RED, PINK, ORANGE SECTION -----#
    
    # Step 4: Special case for medium-dark navy blues
    if b > r and b > g and 140 <= total <= 180:
        if b > max(r, g) * 1.15:  # Only 15% blue dominance required in this range
            return "navy"
    
    # Special case for dark navy blues (brightness between 60-80)
    if total >= 60 and total < 80 and b > r and b > g and b > max(r, g) * 1.3:
        return "navy"
    
    # Handle navy blue colors with more significant blue dominance
    if b > r and b > g:  # Blue is dominant
        # For true navy, blue should be significantly higher than red and green
        if b <= 100 and r < 70 and g < 70:
            if b > max(r, g) * 1.2:  # Blue must be at least 20% higher than both red and green
                return "navy"
    
    # Special detection for other navy colors with distinct blue dominance
    if 30 <= b <= 120 and r < 70 and g < 80 and b > max(r, g) * 1.25:
        return "navy"
    
    # PURPLE detection: When red and blue are both relatively high, and green is lower
    if b > 70 and r > 50 and g < r * 0.9 and g < b * 0.9:
        # Check for specific purple cases
        if (r > 50 and b > 100) or (b > r and b > 90 and g < 80):
            # But don't classify as purple if the red is significantly higher than blue
            if r <= b * 1.2:  # Less strict purple condition
                return "purple"
        
        # Check for specific RGB values that should be purple
        if (r in range(140, 180) and g in range(120, 160) and b in range(180, 230)):
            # Only if red isn't too dominant
            if r <= b:
                return "purple"
            
        # Check for darker purples
        if (r in range(50, 90) and g in range(40, 80) and b in range(100, 140)):
            return "purple"
        
        # More general purple check
        if abs(r - b) < 70 and b > g and r > g and r <= b * 1.2:
            return "purple"

    # BROWN detection (improved)
    
    # Special case for dark olive green / army green
    if (60 <= r <= 90) and (59 <= g <= 85) and (40 <= b <= 65) and r/g > 0.9 and r/g < 1.2:
        return "green"  # Dark olive/army green
    
    # More precise case for brown colors with orangey tint
    if r > 150 and (70 <= g <= 150) and (30 <= b <= 70) and (r > g > b) and (r/b > 2.5):
        return "brown"  # These are definite browns with orangey tint
    
    # Specific case for browns in the orange-brown territory
    if r > 150 and (90 <= g <= 160) and (40 <= b <= 90) and (r > g > b) and (g/b > 1.5):
        # Only classify as brown if not too orangey (i.e., green not too high relative to red)
        if g < r * 0.7:
            return "brown"
    
    # Brown hues (general case)
    if r_ratio > 0.3 and g_ratio > 0.2 and g_ratio < 0.4 and b_ratio < 0.3:
        if r > 120 and g > 60 and b < 80:
            return "brown"
        # Additional check for richer browns
        if r > g > b and r > 100 and g > 40 and b < 80:
            return "brown"
    
    # YELLOW hues
    if r_ratio > 0.3 and g_ratio > 0.3 and b_ratio < 0.25:
        if r > 180 and g > 180 and b < 120:
            return "yellow"
        return "brown" if r < 150 else "yellow"
    
    # GREEN hues
    if g_ratio > 0.4 and r_ratio < 0.4 and b_ratio < 0.4:
        if g > 130:
            if r > 130 and b < 100:
                return "green"  # Olive green
            return "green"
        return "green"
    
    # BLUE/GREEN (teal/cyan/turquoise) colors
    if g_ratio > 0.3 and b_ratio > 0.3 and r_ratio < 0.3:
        # Compare green and blue values to determine if it appears more blue or green to humans
        if g > b * 1.2:  # Green is significantly higher - appears more green
            return "green"
        elif b > g * 1.1:  # Blue is higher - appears more blue
            return "blue"
        elif g > b:  # Green is slightly higher
            return "green"
        else:  # Blue is equal or slightly higher
            return "blue"
    
    # BLUE hues
    if b_ratio > 0.4 and r_ratio < 0.4 and g_ratio < 0.4:
        if b > 150:
            if r < 80 and g < 80:
                return "navy" if b < 170 else "blue"
            return "blue"
        # Expanded navy detection for lower blue values
        if b > 80 and r < 70 and g < 70:
            return "navy"
        return "navy"
    
    # BEIGE/TAN hues
    if r > 180 and g > 150 and b > 120 and r > g > b:
        # Ensure it's not a light pink by checking the red-blue difference
        if r - b < 50:
            return "beige"
    
    # Handle taupe/grayish-brown colors
    if r > g > b and 120 < r < 180 and 100 < g < 160 and 90 < b < 150:
        return "brown" 
    
    # Additional check for light grayish colors that aren't pure grayscale
    if abs(r - g) <= 20 and abs(r - b) <= 20 and abs(g - b) <= 20:
        if r > 160 and r < 230:  # Light gray range even with slight color tint
            return "gray"
    
    # Fallback
    return "unknown"
