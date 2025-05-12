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
    Improved to better distinguish between colors, especially in the pink/purple range.
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
    
    # Special case for bright yellow colors
    if r > 180 and g > 150 and b < 100 and r_ratio > 0.4 and g_ratio > 0.35 and b_ratio < 0.15:
        if abs(r - g) < 80:  # Red and green should be fairly close for yellow
            return "yellow"
    
    # Handle bright pinks EARLY (before reaching the purple checks)
    # This will correctly categorize colors like RGB(232, 108, 147) as pink
    if r > 200 and g < 150 and b > 80 and b < 200 and r > g + 80 and r > b + 30:
        return "pink"
    
    # Additional bright pink check for colors with medium-high green values
    if r > 200 and 100 <= g <= 180 and 100 <= b <= 180 and r > g + 50 and r > b + 30:
        return "pink"
    
    # Step 3: Special case for medium-dark navy blues
    if b > r and b > g and 140 <= total <= 180:
        if b > max(r, g) * 1.15:  # Only 15% blue dominance required in this range
            return "navy"
    
    # Step 3b: Special case for dark navy blues (brightness between 60-80)
    if total >= 60 and total < 80 and b > r and b > g and b > max(r, g) * 1.3:
        return "navy"
    
    # Step 4: Handle grayscale colors with better gray/white/black distinction
    if abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15:
        if r < 50:  # Very dark grayscale colors are black
            return "black"
        elif r < 180:  # Mid-range is gray
            return "gray"
        elif r < 230:  # Light gray range (180-230)
            return "gray"
        else:
            return "white"  # Only very bright grays are "white"
    
    # Step 5: Handle navy blue colors with more significant blue dominance
    if b > r and b > g:  # Blue is dominant
        # For true navy, blue should be significantly higher than red and green
        if b <= 100 and r < 70 and g < 70:
            if b > max(r, g) * 1.2:  # Blue must be at least 20% higher than both red and green
                return "navy"
    
    # Special detection for other navy colors with distinct blue dominance
    if 30 <= b <= 120 and r < 70 and g < 80 and b > max(r, g) * 1.25:
        return "navy"
    
    # MODIFIED: Improved Pink vs Purple Detection
    # Pink: High red, moderate to low green and blue, with red being clearly dominant
    if r > g and r > b:
        # Light pink/peach colors
        if r > 200 and 170 <= g <= 200 and 160 <= b <= 190 and r > g > b:
            return "pink"
            
        # Another pink check for strong saturation with high red
        if r > 180 and r > g + 60 and r > b * 1.3:
            return "pink"
    
    # Purple: When red and blue are both relatively high, and green is lower
    if b > 70 and r > 50 and g < r * 0.9 and g < b * 0.9:
        # More pinks to catch - when red is clearly higher than blue
        if r > 150 and r > b * 1.2 and r > g * 1.5:
            return "pink"
            
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
            
        # Check for the specific RGB values for darker purples
        if (r in range(50, 90) and g in range(40, 80) and b in range(100, 140)):
            return "purple"
        
        # More general purple check - but now more careful about pinks
        if abs(r - b) < 70 and b > g and r > g and r <= b * 1.2:
            return "purple"

    # Define thresholds for color categories
    high_threshold = 0.4
    mid_threshold = 0.3
    low_threshold = 0.2
    very_low_threshold = 0.1
    
    # Special case for dark olive green / army green
    if (60 <= r <= 90) and (59 <= g <= 85) and (40 <= b <= 65) and r/g > 0.9 and r/g < 1.2:
        return "green"  # Dark olive/army green
    
    # MODIFIED: Expanded the pink detection section
    # Salmon pink and coral pink colors
    if r > 200 and 100 <= g <= 160 and 100 <= b <= 160 and r > g + 60 and r > b + 60:
        return "pink"
    
    # Special case for brown colors like RGB(213, 138, 66), RGB(175, 95, 32), RGB(177, 106, 41)
    if r > 150 and (70 <= g <= 150) and (30 <= b <= 70) and (r > g > b) and (r/b > 2.5):
        return "brown"  # These are definite browns with orangey tint
    
    # More general case for brown with orangey tint
    if r > 150 and (90 <= g <= 160) and (40 <= b <= 90) and (r > g > b) and (g/b > 1.5):
        return "brown"  # More general brown detection
    
    # MODIFIED: Improved Red and Pink Detection
    # Red hues with special case for reddish-brown / burgundy / maroon colors
    if r_ratio > mid_threshold and r > g + 30 and r > b + 10:
        # Pink check - high red, moderate green and blue
        if r > 180 and g > 80 and b > 100 and r > g + 80 and r > b + 40:
            return "pink"
            
        # Reddish-purple / burgundy / maroon colors - these should be red, not brown
        if r > 75 and r > g * 1.8 and r > b * 1.5 and g < 100 and b < 100:
            return "red"  # These are red colors with slight purple tint
            
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
            return "red" if red_dominance > 1.8 else "brown"
    
    # Brown hues
    if r_ratio > mid_threshold and g_ratio > low_threshold and g_ratio < high_threshold and b_ratio < mid_threshold:
        if r > 180 and g > 140 and b < 100:
            # Modified to categorize more orange-browns as brown
            if r > g * 1.5 and g > b * 1.5:
                return "brown"  # This should catch colors like RGB(213, 138, 66)
            return "orange"
        elif r > 120 and g > 60 and b < 80:  # Expanded brown range
            return "brown"
        elif r > 180 and g > 160 and b > 100:
            return "beige" if g > 170 and b > 140 and r-b < 60 else "brown"
        # Additional check for brown
        if r > g > b and r > 100 and g > 40 and b < 80:
            return "brown"
        return "brown"
    
    # Yellow hues
    if r_ratio > mid_threshold and g_ratio > mid_threshold and b_ratio < mid_threshold:
        if r > 180 and g > 180 and b < 120:
            return "yellow"
        elif r > 190 and g > 170 and b > 130:
            # Modified beige check to not catch light pink colors
            if r > g > b and r-b < 60:
                return "beige"
            else:
                return "pink"  # This will catch our problem color RGB(225,189,178)
        return "brown" if r < 150 else "yellow"
    
    # Green hues
    if g_ratio > high_threshold and r_ratio < high_threshold and b_ratio < high_threshold:
        if g > 130:
            if r > 130 and b < 100:
                return "green"  # Olive green
            return "green"
        return "green"
    
    # Teal/Cyan/Turquoise colors now classified as either blue or green
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
        # Expanded navy detection for lower blue values
        if b > 80 and r < 70 and g < 70:
            return "navy"
        return "navy"
    
    # Improved Navy Detection - capturing blues with even slightly dominant blue channel
    if b > r and b > g:
        # Dark navy with slightly dominant blue
        if b < 120 and max(r, g) < 100 and b > max(r, g) * 1.1:
            return "navy"
    
    # MODIFIED: Enhanced Pink Detection
    # Pink hues with various cases
    if r_ratio > mid_threshold and b_ratio > low_threshold and g_ratio < mid_threshold:
        # Typical pinks
        if r > 180 and b > 140:
            return "pink"
        
        # Enhanced detection for bright pinks (like RGB(232, 108, 147))
        if r > 180 and 80 <= g <= 150 and 80 <= b <= 180 and r > g + 60:
            return "pink"
        
        # Some pinks might be misclassified as purple - check if it's a pink-leaning purple
        if r > b and r > 160 and b > 120:
            return "pink"
            
        return "purple"
    
    # Modified Beige/Tan hues - more specific to avoid catching light pinks
    if r > 180 and g > 150 and b > 120 and r > g > b:
        # Pink-peach colors will have a significant difference between red and blue
        if r - b > 40:
            return "pink"  # For colors like RGB(225,189,178)
        return "beige"  # For true beige colors
    
    # Handle other edge cases
    if r > 190 and g > 170 and b > 140:
        # Check for pink-ish colors
        if r - b > 40:
            return "pink"
        return "beige"
    
    # Handle taupe/grayish-brown colors
    if r > g > b and 120 < r < 180 and 100 < g < 160 and 90 < b < 150:
        return "brown" 
    
    # One more brown check for colors like RGB(175, 95, 32)
    if r > 140 and 70 < g < 120 and 10 < b < 70 and r > g + 40 and g > b:
        return "brown"
    
    # Additional check for light grayish colors that aren't pure grayscale
    if abs(r - g) <= 20 and abs(r - b) <= 20 and abs(g - b) <= 20:
        if r > 160 and r < 230:  # Light gray range even with slight color tint
            return "gray"
    
    # Final check for navy - this catches any remaining dark blues that might be missed
    if b > max(r, g) and b < 120 and r < 80 and g < 80:
        blue_dominance = b / max(r, g) if max(r, g) > 0 else 2
        if blue_dominance > 1.1:  # Blue is at least 10% higher
            return "navy"
    
    # Fallback
    return "unknown"