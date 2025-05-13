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
    Improved to better distinguish between red and pink based on human perception.
    Also fixes brown/beige categorization issues.
    """
    r, g, b = rgb
    
    # Calculate proportions for color categorization
    total = r + g + b
    r_ratio = r / total if total > 0 else 0
    g_ratio = g / total if total > 0 else 0
    b_ratio = b / total if total > 0 else 0
    
    # Step 1: Handle true black cases first (very dark colors with very similar RGB values)
    if total < 90 and abs(r - g) <= 8 and abs(r - b) <= 8 and abs(g - b) <= 8:
        # These are true black colors
        return "black"
    
    # Step 2: Handle very dark color cases that should be black
    if total < 60: 
        return "black"
    
    # Special case for bright yellow colors
    if r > 180 and g > 150 and b < 100 and r_ratio > 0.4 and g_ratio > 0.35 and b_ratio < 0.15:
        if abs(r - g) < 80:  
            return "yellow"
    
    # Step 3: Special case for medium-dark navy blues
    if b > r and b > g and 140 <= total <= 180:
        if b > max(r, g) * 1.15: 
            return "navy"
    
    # Step 3b: Special case for dark navy blues (brightness between 60-80)
    if total >= 60 and total < 80 and b > r and b > g and b > max(r, g) * 1.3:
        return "navy"
    
    # Step 4: Handle grayscale colors with better gray/white/black distinction
    if abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15:
        if r < 50:  # Very dark grayscale colors are black
            return "black"
        elif r < 180:  
            return "gray"
        elif r < 230:  
            return "gray"
        else:
            return "white"  
    
    # Step 5: Handle navy blue colors with more significant blue dominance
    if b > r and b > g:  # Blue is dominant
        # For true navy, blue should be significantly higher than red and green
        if b <= 100 and r < 70 and g < 70:
            if b > max(r, g) * 1.2:  
                return "navy"
    
    # Special detection for other navy colors with distinct blue dominance
    if 30 <= b <= 120 and r < 70 and g < 80 and b > max(r, g) * 1.25:
        return "navy"
    
    # IMPROVED BROWN/BEIGE DETECTION - Place this before red detection
    # Brown has red dominant but also significant green, with lower blue
    if r > g > b:  # Red > Green > Blue is the signature of browns
        # Strong browns
        if r > 120 and 60 <= g <= 160 and 10 <= b <= 120 and g > b * 1.2:
            # Classic browns
            if r > g * 1.1 and g > b * 1.3:
                return "brown"
        
        # Light browns / tans / beiges
        if 160 <= r <= 230 and 140 <= g <= 200 and 100 <= b <= 170:
            # If r, g, b are relatively close together but still following r > g > b
            if r/b < 1.9 and r/g < 1.3 and g/b < 1.6:
                return "beige"
    
    # More brown detection - colors like RGB(190,164,133) should be beige
    if 160 <= r <= 230 and 140 <= g <= 200 and 100 <= b <= 170 and r > g > b:
        brown_proportion_check = (r - b) / r  # How much "brown-ness" is in the color
        if 0.15 <= brown_proportion_check <= 0.45:  # Not too stark, not too subtle
            return "beige"
    
    # More beige/tan detection
    if 180 <= r <= 240 and 160 <= g <= 220 and 120 <= b <= 190 and r > g > b:
        # For lighter beiges with less difference between channels
        if r/b < 1.75 and r/g < 1.3:
            return "beige"
    
    # Base case: When red is dominant (red > green and red > blue)
    if r > g and r > b:
        # First check if this matches brown criteria - brown takes precedence over red in ambiguous cases
        if g > b * 1.3 and r/g < 1.5:
            # Brown colors with more pronounced red tint
            if 100 <= r <= 200 and 60 <= g <= 150 and 10 <= b <= 100:
                return "brown"
        
        # More brown detection - focused on medium browns
        if 100 <= r <= 180 and 60 <= g <= 140 and 0 <= b <= 100:
            # If there's enough green presence compared to red
            if g/r > 0.5 and (r-g) < 70:
                return "brown"
        
        # Deep/pure reds: Very dominant red with low green and blue
        if r > 160 and g < 90 and b < 90:
            return "red"  
        
        # Traditional reds
        if r > 120 and g < 90 and b < 90 and r > (g + b):
            return "red"  
            
        # Burgundy/maroon/ruby
        if r > 100 and r < 180 and g < 80 and b < 80 and r > (g + b) * 0.7:
            return "red"  
            
        # Clear pink cases
        if r > 200 and g > 150 and b > 150:
            return "pink"  
            
        # Bright pinks
        if r > 220 and 100 <= g <= 180 and 120 <= b <= 200:
            return "pink" 
            
        # Medium pinks
        if r > 180 and 100 <= g <= 150 and 100 <= b <= 170 and b > g * 0.8:
            return "pink" 
            
        # Subtle pinks
        if r > 180 and g > 120 and b > 120 and b > g * 0.8:
            return "pink" 
        
        # Pinkish red or reddish pink 
        if r > 190 and 80 <= g <= 140 and 80 <= b <= 140:
            # If blue is relatively high compared to green, it's more pink
            if b > g * 1.1 or (b > 110 and g < 100):
                return "pink"  
            # If red is extremely dominant, it's still red
            elif r > g * 2.2 and r > b * 2.2:
                return "red"  
            # If green and blue are both quite low, it's red
            elif g < 100 and b < 100:
                return "red"
            else:
                return "pink" 
        
        # Coral/salmon territory - often confused between red, pink and orange
        if r > 200 and 120 <= g <= 170 and 90 <= b <= 140:
            # If green is significantly higher than blue, it's more orange/coral
            if g > b * 1.3:
                return "orange"  # Coral/salmon territory
            # If blue is relatively high, it's pink
            elif b > g * 0.8:
                return "pink" 
            else:
                return "red"  
        
        # Additional detection for browns that might be misclassified as red
        if 120 <= r <= 180 and 80 <= g <= 140 and 40 <= b <= 100:
            if g > b * 1.5 and r/g < 1.8:
                return "brown"
                
        # Remaining red-dominant colors
        if g < 100 and b < 100:
            return "red"
        # If blue is relatively high compared to green, it leans pink
        elif b > g * 0.9:
            return "pink"
        # If red is extremely dominant over both green and blue, it's red
        elif r > g * 2 and r > b * 2:
            return "red"
        else:
            # Default to red for remaining red-dominant colors
            return "red"
    
    # Purple detection
    if b > 70 and r > 70 and g < r * 0.9 and g < b * 0.9:
        # Distinguish purples from pinks more clearly
        if b > r * 1.2: 
            return "purple"
        elif r > b * 1.2: 
            if r > 160 and g < 120: 
                return "pink"
            else:
                return "purple"  
        # When red and blue are relatively balanced, it's purple
        elif abs(r - b) < 30:
            return "purple"
    
    # Define thresholds for color categorization
    high_threshold = 0.4
    mid_threshold = 0.3
    low_threshold = 0.2
    very_low_threshold = 0.1
    
    # Special case for dark olive green / army green
    if (60 <= r <= 90) and (59 <= g <= 85) and (40 <= b <= 65) and r/g > 0.9 and r/g < 1.2:
        return "green"  
    
    # Salmon pink and coral pink colors - these are distinct from red
    if r > 200 and 100 <= g <= 160 and 100 <= b <= 160:
        # Coral colors
        if g > b * 1.3:
            return "orange" 
        return "pink"  
    
    # Brown colors with orangey tint
    if r > 150 and (70 <= g <= 150) and (30 <= b <= 70) and (r > g > b) and (r/b > 2.5):
        return "brown"  
    
    # More general case for brown with orangey tint
    if r > 150 and (90 <= g <= 160) and (40 <= b <= 90) and (r > g > b) and (g/b > 1.5):
        return "brown"  
    
    # Red hues with special case for reddish-brown / burgundy / maroon colors
    if r_ratio > mid_threshold and r > g + 30 and r > b + 10:
        # Reddish-purple / burgundy / maroon colors
        if r > 75 and r > g * 1.8 and r > b * 1.5 and g < 100 and b < 100:
            return "red"  
            
        if r > 220 and g > 150:
            # High red, green and blue = pink
            if b > 150:
                return "pink"
            # High red and green, low blue = orange
            elif g > 180 and b < 100:
                return "orange"
            # High red, medium green = red
            else:
                return "red"
        # Pure red check
        elif r > 160 and g < 80 and b < 80:
            return "red"
        # Burgundy/maroon still reads as red to most people
        elif r > 140 and g > 60 and g < 110 and b < 100:
            return "red"
        # Red vs orange differentiation
        elif r > 160 and g > 110 and b < 100:
            return "orange" if g > 130 else "red"
        else:
            # For darker reds, check red dominance ratio
            red_dominance = r / max(g, b) if max(g, b) > 0 else 2
            return "red" if red_dominance > 1.8 else "brown"
    
    # Brown hues with improved detection
    if r_ratio > mid_threshold and g_ratio > low_threshold and g_ratio < high_threshold and b_ratio < mid_threshold:
        if r > 180 and g > 140 and b < 100:
            # Modified to categorize more orange-browns as brown
            if r > g * 1.5 and g > b * 1.5:
                return "brown"  
            return "orange"
        elif r > 120 and g > 60 and b < 80:  
            return "brown"
        elif r > 180 and g > 160 and b > 100:
            # Improved beige detection with broader parameters
            if g > 170 and b > 140 and r-b < 80:
                return "beige"
            return "brown"
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
            if r > g > b and r-b < 80:
                return "beige"
            # If red is significantly higher than blue, it's more pink
            elif r - b > 80:
                return "pink"
            else:
                return "beige"
        return "brown" if r < 150 else "yellow"
    
    # Green hues
    if g_ratio > high_threshold and r_ratio < high_threshold and b_ratio < high_threshold:
        if g > 130:
            if r > 130 and b < 100:
                return "green"  
            return "green"
        return "green"
    
    # Teal/Cyan/Turquoise colors now classified as either blue or green
    if g_ratio > mid_threshold and b_ratio > mid_threshold and r_ratio < mid_threshold:
        # Compare green and blue values to determine if it appears more blue or green
        if g > b * 1.2:  
            return "green"
        elif b > g * 1.1:  
            return "blue"
        elif g > b:  
            return "green"
        else:  
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
    
    # IMPROVED Beige/Tan hues detection - capturing a broader range
    # Specifically for RGB values like (190,164,133)
    if 180 <= r <= 210 and 140 <= g <= 185 and 110 <= b <= 150 and r > g > b:
        return "beige"
    
    # More general beige detection
    if 180 <= r <= 235 and 160 <= g <= 215 and 130 <= b <= 180 and r > g > b:
        return "beige"
    
    # Handle other edge cases
    if r > 190 and g > 170 and b > 140:
        # Improved check for beige vs pink
        if r > g > b and r-b < 80:
            return "beige"
        # Check for pink-ish colors
        if r - b > 80:
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
        if r > 160 and r < 230:  
            return "gray"
    
    # Check for navy
    if b > max(r, g) and b < 120 and r < 80 and g < 80:
        blue_dominance = b / max(r, g) if max(r, g) > 0 else 2
        if blue_dominance > 1.1:  
            return "navy"
    
    # Fallback
    return "unknown"
