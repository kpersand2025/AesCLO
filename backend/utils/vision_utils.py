# utils/vision_utils.py
import io
from google.cloud import vision

def extract_colors(image_path, vision_client):
    """
    Extract dominant colors from an image using Google Cloud Vision API.
    Returns a list of dominant colors with their RGB values, sorted by score.
    """
    # Read the image file
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    # Create an image object
    image = vision.Image(content=content)
    
    # Use the imageProperties feature to get color information
    image_properties = vision_client.image_properties(image=image).image_properties_annotation
    
    # Extract colors and sort by score (highest first)
    colors = []
    for color in image_properties.dominant_colors.colors:
        # Get RGB values
        r = color.color.red
        g = color.color.green
        b = color.color.blue
        
        # Get score (percentage of the image this color represents)
        score = color.score
        pixel_fraction = color.pixel_fraction
        
        colors.append({
            'rgb': [r, g, b],
            'score': score,
            'pixel_fraction': pixel_fraction
        })
    
    # Sort colors by score in descending order
    colors.sort(key=lambda x: x['score'], reverse=True)
    
    return colors

def get_top_colors(colors, max_colors=3, single_color_threshold=0.7):
    """
    Get the top colors from a list of colors, based on score.
    If the highest scoring color has a score greater than or equal to single_color_threshold,
    only return that color.
    
    Args:
        colors (list): List of color dictionaries with 'rgb', 'score', and 'pixel_fraction' keys
        max_colors (int): Maximum number of colors to return
        single_color_threshold (float): If the highest color score is >= this threshold,
                                        only that color will be returned
        
    Returns:
        list: List of up to max_colors colors, sorted by score
    """
    if not colors:
        return []
        
    # Check if the highest scoring color exceeds the threshold
    if colors[0]['score'] >= single_color_threshold:
        return [colors[0]]  # Return only the highest scoring color
    
    # Otherwise, return the top max_colors colors by score
    return colors[:max_colors]

def predict_clothing_category(image_path, vision_client):
    """
    Predict clothing category using Google Cloud Vision API object detection.
    Returns a category string: "top", "bottom", "shoes", "accessory", or None if no match.
    """
    # Read the image file
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    # Create an image object
    image = vision.Image(content=content)
    
    # Perform object detection instead of label detection
    response = vision_client.object_localization(image=image)
    objects = response.localized_object_annotations
    
    # Keywords for categorization
    top_keywords = ['shirt', 't-shirt', 'top', 'blouse', 'sweater', 'jacket', 'coat', 'hoodie', 'sweatshirt', 'polo']
    bottom_keywords = ['pants', 'jeans', 'shorts', 'skirt', 'trousers', 'leggings', 'slacks', 'joggers', 'denim']
    shoe_keywords = ['shoes', 'shoe', 'sneakers', 'boots', 'footwear', 'sandals', 'heels', 'loafers', 'athletic shoes']
    accessory_keywords = ['hat', 'cap', 'scarf', 'glove', 'necklace', 'bracelet', 'ring', 'earring', 'watch', 'sunglasses', 
                         'glasses', 'belt', 'tie', 'bow tie', 'headband', 'purse', 'bag', 'handbag', 'backpack', 'wallet']
    
    # Check for matches
    for detected_object in objects:
        object_name = detected_object.name.lower()
        
        if any(keyword in object_name for keyword in top_keywords):
            return "top"
        elif any(keyword in object_name for keyword in bottom_keywords):
            return "bottom"
        elif any(keyword in object_name for keyword in shoe_keywords):
            return "shoes"
        elif any(keyword in object_name for keyword in accessory_keywords):
            return "accessory"
    
    # If no match, return None
    return None