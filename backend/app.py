from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import uuid
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime
from google.cloud import vision, storage
from google.oauth2 import service_account
import io
import certifi
import json
import os
from dotenv import load_dotenv
from flask import send_file
import tempfile

# Try to load environment variables from .env file in development
if os.path.exists('.env'):
    load_dotenv()

# Import your utility modules
from utils.color_utils import get_color_name, calculate_color_match_score
from utils.vision_utils import extract_colors, predict_clothing_category
from utils.outfit_generator import generate_color_coordinated_outfit, has_color
from utils.gemini_utils import analyze_clothing_occasion, categorize_clothing_item
from utils.weather_utils import get_weather_by_location, get_weather_condition_by_id, determine_outfit_type_by_weather
from utils.weather_outfit_generator import generate_weather_based_outfit
from utils.gemini_weather_utils import analyze_clothing_weather_suitability

app = Flask(__name__, 
            template_folder="../templates",  
            static_folder="../static")  

CORS(app)
# Get secret key from environment or generate a random one
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Session security configurations
app.config["SESSION_PERMANENT"] = False  # Session expires when browser closes
app.config["SESSION_TYPE"] = "filesystem"  # Store session data securely

# Configure MongoDB connection from environment variable
connection_string = os.environ.get("MONGODB_URI")
app.config["MONGO_URI"] = connection_string

# Initialize Flask-PyMongo with certificate verification
mongo = PyMongo(app, tlsCAFile=certifi.where())
bcrypt = Bcrypt(app)

# Set up collections
users_collection = mongo.db.users  
uploads_collection = mongo.db.uploads
outfits_collection = mongo.db.outfits

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Google Cloud setup
# Set up clients for Vision API and Cloud Storage
vision_client = None
storage_client = None
GCS_BUCKET = os.environ.get('GCS_BUCKET_NAME', 'aesclo-images')

try:
    # Option 1: Check for file path
    google_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds_path
        vision_client = vision.ImageAnnotatorClient()
        storage_client = storage.Client()
    else:
        # Option 2: Check for JSON content in environment variable
        google_creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if google_creds_json:
            credentials_info = json.loads(google_creds_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            vision_client = vision.ImageAnnotatorClient(credentials=credentials)
            storage_client = storage.Client(credentials=credentials)
        else:
            print("WARNING: No Google credentials found. Vision API and Cloud Storage will not work.")
except Exception as e:
    print(f"Error setting up Google Cloud clients: {e}")

# Get Gemini API key from environment
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if gemini_api_key:
    os.environ["GEMINI_API_KEY"] = gemini_api_key
else:
    print("WARNING: No Gemini API key found. Gemini features will not work.")

# OpenWeather API key from environment
app.config['OPENWEATHER_API_KEY'] = os.environ.get("OPENWEATHER_API_KEY")
if not app.config['OPENWEATHER_API_KEY']:
    print("WARNING: No OpenWeather API key found. Weather features will not work.")

# Create tmp directory if it doesn't exist (for temporary file storage)
if not os.path.exists('/tmp'):
    os.makedirs('/tmp')

# Check if the uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for login page
@app.route("/", methods=["GET"])
def login_page():
    if "user" in session:
        return redirect(url_for("home"))  # Redirect logged-in users to home
    return render_template("login.html")  

# Login route
@app.route("/login", methods=["POST"])
def login_post():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["passwordHash"], password):
        session["user"] = username  # Store user session
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Logout route
@app.route("/logout")
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for("login_page"))

# Route for user registration
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    password = data.get("password")

    if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"message": "Username or email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = {
        "userID": str(uuid.uuid4()),  
        "username": username,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "passwordHash": hashed_password  
    }

    users_collection.insert_one(new_user)
    return jsonify({"message": "Account created successfully!"}), 201

# Home route (requires authentication)
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("home.html")  

# Upload page (GET request)
@app.route("/upload")
def upload_page():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("upload.html") 

@app.route("/generator")
def generator():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("generator.html") 

@app.route("/get_wardrobe_colors")
def get_wardrobe_colors():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    # Get all tops from the wardrobe
    tops = list(uploads_collection.find({"user_id": user["_id"], "category": "top"}))
    
    # Extract only the first (dominant) color from each top
    available_colors = set()
    for item in tops:
        if 'colors' in item and item['colors'] and len(item['colors']) > 0:
            # Only add the first color (dominant color) from each top
            first_color = item['colors'][0]['name'].lower()
            if first_color != 'unknown':  # Skip unknown colors
                available_colors.add(first_color)
    
    # Sort colors alphabetically
    sorted_colors = sorted(list(available_colors))
    
    return jsonify({
        "success": True,
        "colors": sorted_colors
    })

@app.route("/generate_color_outfit", methods=["POST"])
def generate_color_outfit():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    base_color = data.get("base_color")  # Get the base color
    random_color = data.get("random_color", False)  # Check if random color mode is enabled
    
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Get the user's wardrobe items
    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))
    
    # Separate items by category
    all_tops = [item for item in wardrobe_items if item["category"] == "top"]
    bottoms = [item for item in wardrobe_items if item["category"] == "bottom"]
    shoes = [item for item in wardrobe_items if item["category"] == "shoes"]
    
    # Check if wardrobe has enough items
    if len(all_tops) < 1 or len(shoes) < 1:
        return jsonify({
            "success": False, 
            "message": "Your wardrobe needs at least one top and one pair of shoes to generate an outfit."
        }), 400
    
    # Handle random color coordination if requested
    if random_color or base_color == 'random':
        # For random color, choose a random top first
        selected_top = random.choice(all_tops)
        
        # Get the dominant color of the selected top if available
        if 'colors' in selected_top and selected_top['colors']:
            base_color = selected_top['colors'][0]['name'].lower()
        else:
            # If no color data available, just use a neutral color
            base_color = "black"
            
        # Now use the standard color coordination algorithm with this new base_color
        try:
            # Check if the selected top is a "complete" top (dress, jumpsuit, etc.)
            is_complete_top = selected_top.get("subcategory") == "complete"
            
            if is_complete_top:
                # For complete tops, generate outfit without bottoms
                _, _, best_shoes = generate_color_coordinated_outfit(
                    [selected_top], bottoms, shoes, base_color
                )
                
                if not all([selected_top, best_shoes]):
                    return jsonify({
                        "success": False,
                        "message": "Could not generate a well-coordinated outfit. Please try again or try with different items."
                    }), 400
                
                # Return outfit with no bottom - UPDATED to use GCS URL
                return jsonify({
                    "success": True,
                    "top": {
                        "id": selected_top["item_id"],
                        "image_url": selected_top["image_url"],  # Use GCS URL directly
                        "colors": selected_top.get("colors", []),
                        "unavailable": selected_top.get("unavailable", False)
                    },
                    "bottom": None,  # No bottom for complete tops
                    "shoes": {
                        "id": best_shoes["item_id"],
                        "image_url": best_shoes["image_url"],  # Use GCS URL directly
                        "colors": best_shoes.get("colors", []),
                        "unavailable": best_shoes.get("unavailable", False)
                    },
                    "coordination_style": f"Random Color Coordination",
                    "base_color": base_color,
                    "is_complete_top": True  # Flag to indicate this is a complete top
                })
            else:
                # Use the outfit generator module with the random top as the basis
                _, best_bottom, best_shoes = generate_color_coordinated_outfit(
                    [selected_top], bottoms, shoes, base_color
                )
                
                if not all([selected_top, best_bottom, best_shoes]):
                    return jsonify({
                        "success": False,
                        "message": "Could not generate a well-coordinated outfit. Please try again or try with different items."
                    }), 400
                
                # UPDATED to use GCS URLs
                return jsonify({
                    "success": True,
                    "top": {
                        "id": selected_top["item_id"],
                        "image_url": selected_top["image_url"],  # Use GCS URL directly
                        "colors": selected_top.get("colors", []),
                        "unavailable": selected_top.get("unavailable", False)
                    },
                    "bottom": {
                        "id": best_bottom["item_id"],
                        "image_url": best_bottom["image_url"],  # Use GCS URL directly
                        "colors": best_bottom.get("colors", []),
                        "unavailable": best_bottom.get("unavailable", False)
                    },
                    "shoes": {
                        "id": best_shoes["item_id"],
                        "image_url": best_shoes["image_url"],  # Use GCS URL directly
                        "colors": best_shoes.get("colors", []),
                        "unavailable": best_shoes.get("unavailable", False)
                    },
                    "coordination_style": f"Random Color Coordination",
                    "base_color": base_color,
                    "is_complete_top": False  # Flag to indicate this is a standard top
                })
        except Exception as e:
            print(f"Error generating random color outfit: {e}")
            return jsonify({
                "success": False,
                "message": "Failed to generate random color outfit. Please try again."
            }), 500
    
    # Regular color-coordinated flow
    # Validate that a color was selected for non-random mode
    if not base_color:
        return jsonify({
            "success": False,
            "message": "Please select a color for your outfit."
        }), 400
    
    # Filter tops to only include those with the selected color
    tops_with_color = []
    for item in all_tops:
        if 'colors' in item and item['colors']:
            for color_data in item['colors']:
                if color_data['name'].lower() == base_color.lower():
                    tops_with_color.append(item)
                    break
    
    if not tops_with_color:
        return jsonify({
            "success": False,
            "message": f"No tops found with {base_color} color. Please try another color or upload more items."
        }), 400
    
    # Use the outfit generator module to generate a color-coordinated outfit
    try:
        # Generate outfit using the module function
        selected_top, best_bottom, best_shoes = generate_color_coordinated_outfit(
            tops_with_color, bottoms, shoes, base_color
        )
        
        # Check if selected top is a "complete" top
        is_complete_top = selected_top.get("subcategory") == "complete"
        
        if is_complete_top:
            # For complete tops, we expect best_bottom to be None
            if not all([selected_top, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": "Could not generate a well-coordinated outfit. Please try again or try with different items."
                }), 400
            
            # Return outfit with no bottom - UPDATED to use GCS URLs
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": selected_top["image_url"],  # Use GCS URL directly
                    "colors": selected_top.get("colors", []),
                    "unavailable": selected_top.get("unavailable", False)
                },
                "bottom": None,  # No bottom for complete tops
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": best_shoes["image_url"],  # Use GCS URL directly
                    "colors": best_shoes.get("colors", []),
                    "unavailable": best_shoes.get("unavailable", False)
                },
                "coordination_style": f"{base_color.capitalize()} Coordinated Outfit",
                "base_color": base_color,
                "is_complete_top": True  # Flag to indicate this is a complete top
            })
        else:
            # For standard tops, we need bottom + shoes
            if not all([selected_top, best_bottom, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": "Could not generate a well-coordinated outfit. Please try again or try with different items."
                }), 400
            
            # UPDATED to use GCS URLs
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": selected_top["image_url"],  # Use GCS URL directly
                    "colors": selected_top.get("colors", []),
                    "unavailable": selected_top.get("unavailable", False)
                },
                "bottom": {
                    "id": best_bottom["item_id"],
                    "image_url": best_bottom["image_url"],  # Use GCS URL directly
                    "colors": best_bottom.get("colors", []),
                    "unavailable": best_bottom.get("unavailable", False)
                },
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": best_shoes["image_url"],  # Use GCS URL directly
                    "colors": best_shoes.get("colors", []),
                    "unavailable": best_shoes.get("unavailable", False)
                },
                "coordination_style": f"{base_color.capitalize()} Coordinated Outfit",
                "base_color": base_color,
                "is_complete_top": False  # Flag to indicate this is a standard top
            })
    except Exception as e:
        print(f"Error generating outfit: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to generate outfit. Please try again."
        }), 500
    
@app.route("/generate_occasion_outfit", methods=["POST"])
def generate_occasion_outfit():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    target_occasion = data.get("occasion", "casual")  # Default to casual if not specified
    
    # Validate the occasion
    valid_occasions = ["casual", "work/professional", "formal", "athletic/sport", "lounge/sleepwear"]
    if target_occasion not in valid_occasions:
        return jsonify({
            "success": False,
            "message": f"Invalid occasion. Valid options are: {', '.join(valid_occasions)}"
        }), 400
    
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Get the user's wardrobe items
    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))
    
    # Separate items by category
    tops = [item for item in wardrobe_items if item["category"] == "top"]
    bottoms = [item for item in wardrobe_items if item["category"] == "bottom"]
    shoes = [item for item in wardrobe_items if item["category"] == "shoes"]
    
    # Check if wardrobe has enough items (only require tops and shoes)
    if len(tops) < 1 or len(shoes) < 1:
        return jsonify({
            "success": False, 
            "message": "Your wardrobe needs at least one top and one pair of shoes to generate an outfit."
        }), 400
    
    # Check if there are items matching the selected occasion
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
    
    # Check if we have at least some items for each category that match the occasion
    if not tops_matching_occasion and not shoes_matching_occasion:
        return jsonify({
            "success": False,
            "message": f"No items found for the '{target_occasion}' occasion. Try uploading more items or selecting a different occasion."
        }), 400
    
    # Use the outfit generator module to generate an occasion-based outfit
    try:
        # Import the function if needed
        from utils.outfit_generator import generate_occasion_based_outfit
        
        # Only pass items that match the selected occasion to the generator
        selected_top, best_bottom, best_shoes = generate_occasion_based_outfit(
            tops_matching_occasion, bottoms_matching_occasion, shoes_matching_occasion, target_occasion
        )
        
        # Check if this is a complete top outfit (no bottom)
        is_complete_top = selected_top.get("subcategory") == "complete"
        
        if is_complete_top:
            # For complete tops, best_bottom will be None
            if not all([selected_top, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": f"Could not generate a suitable outfit for {target_occasion}. Try uploading more items."
                }), 400
            
            # Return outfit with no bottom - UPDATED to use GCS URLs
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": selected_top["image_url"],  # Use GCS URL directly
                    "colors": selected_top.get("colors", []),
                    "occasions": selected_top.get("occasions", []),
                    "unavailable": selected_top.get("unavailable", False)
                },
                "bottom": None,  # No bottom for complete tops
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": best_shoes["image_url"],  # Use GCS URL directly
                    "colors": best_shoes.get("colors", []),
                    "occasions": best_shoes.get("occasions", []),
                    "unavailable": best_shoes.get("unavailable", False)
                },
                "outfit_type": f"{target_occasion.capitalize()} Outfit",
                "is_complete_top": True  # Flag to indicate this is a complete top
            })
        else:
            # For standard tops, we need bottom + shoes
            if not all([selected_top, best_bottom, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": f"Could not generate a suitable outfit for {target_occasion}. Try uploading more items."
                }), 400
            
            # UPDATED to use GCS URLs
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": selected_top["image_url"],  # Use GCS URL directly
                    "colors": selected_top.get("colors", []),
                    "occasions": selected_top.get("occasions", []),
                    "unavailable": selected_top.get("unavailable", False)
                },
                "bottom": {
                    "id": best_bottom["item_id"],
                    "image_url": best_bottom["image_url"],  # Use GCS URL directly
                    "colors": best_bottom.get("colors", []),
                    "occasions": best_bottom.get("occasions", []),
                    "unavailable": best_bottom.get("unavailable", False)
                },
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": best_shoes["image_url"],  # Use GCS URL directly
                    "colors": best_shoes.get("colors", []),
                    "occasions": best_shoes.get("occasions", []),
                    "unavailable": best_shoes.get("unavailable", False)
                },
                "outfit_type": f"{target_occasion.capitalize()} Outfit",
                "is_complete_top": False  # Flag to indicate this is a standard top
            })
    except Exception as e:
        print(f"Error generating outfit: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to generate outfit. Please try again."
        }), 500

@app.route("/save_outfit", methods=["POST"])
def save_outfit():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    # Get JSON data from request
    data = request.get_json()
    top_id = data.get("top_id")
    bottom_id = data.get("bottom_id")  # This might be None for complete tops
    shoe_id = data.get("shoe_id")
    
    # Validate data - only top and shoes are required now
    if not all([top_id, shoe_id]):
        return jsonify({"success": False, "message": "Missing required outfit items"}), 400
        
    # Get user information
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Create new outfit entry
    new_outfit = {
        "outfit_id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "top_id": top_id,
        "bottom_id": bottom_id,  # This can be None for complete tops
        "shoe_id": shoe_id,
        "created_at": datetime.utcnow().isoformat(),
        "name": data.get("name", f"Outfit {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    }
    
    # Save to database
    outfits_collection.insert_one(new_outfit)
    
    return jsonify({"success": True, "message": "Outfit saved successfully"})

@app.route("/wardrobe")
def wardrobe():
    if "user" not in session:
        return redirect(url_for("login_page"))

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return redirect(url_for("login_page"))

    # Fetch wardrobe items for the logged-in user
    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))

    # Convert MongoDB ObjectId to string
    for item in wardrobe_items:
        item["_id"] = str(item["_id"])
        # No change needed here - image_url is already stored as GCS URL

    return render_template("wardrobe.html", wardrobe_items=wardrobe_items)

@app.route("/get_wardrobe")
def get_wardrobe():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"message": "User not found"}), 404

    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))

    wardrobe = {"tops": [], "bottoms": [], "shoes": [], "accessories": []}

    for item in wardrobe_items:
        item_data = {
            "id": item["item_id"],
            "image_url": item["image_url"],  # Use the stored GCS URL directly
            "category": item["category"]
        }
        if "subcategory" in item:
            item_data["subcategory"] = item["subcategory"]
            
        if item["category"] == "top":
            wardrobe["tops"].append(item_data)
        elif item["category"] == "bottom":
            wardrobe["bottoms"].append(item_data)
        elif item["category"] == "shoes":
            wardrobe["shoes"].append(item_data)
        elif item["category"] == "accessory":
            wardrobe["accessories"].append(item_data)

    return jsonify(wardrobe)

@app.route("/signup")
def signup():
    return render_template("signup.html")  

@app.route("/saved_outfits")
def saved_outfits():
    if "user" not in session:
        return redirect(url_for("login_page"))
        
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return redirect(url_for("login_page"))
    
    # Get all saved outfits for the user
    saved_outfits = list(outfits_collection.find({"user_id": user["_id"]}))
    
    # Build detailed outfit data
    outfits_data = []
    for outfit in saved_outfits:
        top = uploads_collection.find_one({"item_id": outfit["top_id"]})
        
        # Check if this outfit has a bottom or is a complete top outfit
        has_bottom = outfit.get("bottom_id") is not None
        bottom = None
        
        if has_bottom:
            bottom = uploads_collection.find_one({"item_id": outfit["bottom_id"]})
            # Skip if bottom is missing
            if not bottom:
                continue
        
        shoe = uploads_collection.find_one({"item_id": outfit["shoe_id"]})
        
        # Ensure we have at least top and shoes
        if top and shoe:
            # Determine if this is a complete top outfit
            is_complete_top = top.get("subcategory") == "complete"
            
            outfit_data = {
                "outfit_id": outfit["outfit_id"],
                "name": outfit["name"],
                "created_at": outfit["created_at"],
                "top_image": top["image_url"],  # Use GCS URL
                "shoe_image": shoe["image_url"],  # Use GCS URL
                "is_complete_top": is_complete_top or not has_bottom
            }
            
            # Add bottom image only if it exists
            if bottom:
                outfit_data["bottom_image"] = bottom["image_url"]  # Use GCS URL
            
            outfits_data.append(outfit_data)
    
    return render_template("saved_outfits.html", outfits=outfits_data)

@app.route("/delete_outfit", methods=["POST"])
def delete_outfit():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    outfit_id = data.get("outfit_id")
    
    if not outfit_id:
        return jsonify({"success": False, "message": "No outfit ID provided"}), 400
        
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    # Delete the outfit, ensuring it belongs to the current user
    result = outfits_collection.delete_one({"outfit_id": outfit_id, "user_id": user["_id"]})
    
    if result.deleted_count > 0:
        return jsonify({"success": True, "message": "Outfit deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Outfit not found or not authorized to delete"}), 404

# Updated image upload handler with color detection and occasion tagging
@app.route("/upload", methods=["POST"])
def upload_image():
    if "user" not in session:
        return redirect(url_for("login_page"))

    if 'file' not in request.files:
        return render_template("upload.html", error_message="No file provided")

    file = request.files['file']

    if file.filename == '':
        return render_template("upload.html", error_message="No file selected")

    if not allowed_file(file.filename):
        return render_template("upload.html", error_message="Invalid file type. Only .png, .jpg, .jpeg, .webp are allowed.")

    # Retrieve the user
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return render_template("upload.html", error_message="User not found")

    # Save file to a temporary location for processing
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    temp_filepath = os.path.join('/tmp', unique_filename)
    file.save(temp_filepath)

    # Use Gemini to predict the clothing category and subcategory
    from utils.gemini_utils import categorize_clothing_item
    predicted_category, predicted_subcategory = categorize_clothing_item(temp_filepath)

    if not predicted_category:
        try:
            os.remove(temp_filepath)
        except Exception as e:
            print(f"Error removing temporary file: {e}")

        return render_template("upload.html", 
                               error_message="This image doesn't appear to be a clothing item. Please upload a clearer or different image.")

    # Extract dominant colors
    try:
        colors = extract_colors(temp_filepath, vision_client)
        
        from utils.vision_utils import get_top_colors
        top_colors = get_top_colors(colors, max_colors=3, single_color_threshold=0.6)
        
        dominant_colors = []
        for color in top_colors:
            rgb = color['rgb']
            color_name = get_color_name(rgb)
            dominant_colors.append({
                'name': color_name,
                'rgb': rgb,
                'score': color['score'],
                'pixel_fraction': color['pixel_fraction']
            })
            
    except Exception as e:
        print(f"Error extracting colors: {e}")
        dominant_colors = []
        
    # Analyze clothing occasion
    try:
        occasions = analyze_clothing_occasion(temp_filepath)
        print(f"Detected occasions: {occasions}")
    except Exception as e:
        print(f"Error analyzing clothing occasion: {e}")
        occasions = []

    # Analyze for weather suitability
    try:
        weather_suitability = analyze_clothing_weather_suitability(temp_filepath)
        weather_conditions = weather_suitability.get("weather_conditions", [])
        temperature_range = weather_suitability.get("temperature_range", [])
        print(f"Detected weather suitability: {weather_suitability}")
    except Exception as e:
        print(f"Error analyzing clothing weather suitability: {e}")
        weather_conditions = []
        temperature_range = []

    # Upload to Google Cloud Storage
    try:
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(unique_filename)
        
        # Upload the file
        blob.upload_from_filename(temp_filepath)
        
        # Instead of direct GCS URL, use our serve_image route
        image_url = f"/serve_image/{unique_filename}"
        
        # Save item in database with the new image URL format
        new_upload = {
            "item_id": str(uuid.uuid4()),
            "user_id": user["_id"],
            "image_url": image_url,  # Use our serve_image route
            "gcs_path": f"gs://{GCS_BUCKET}/{unique_filename}", 
            "filename": unique_filename,
            "timestamp": datetime.utcnow().isoformat(),
            "category": predicted_category,
            "subcategory": predicted_subcategory,
            "colors": dominant_colors,
            "occasions": occasions,
            "weather_conditions": weather_conditions,
            "temperature_range": temperature_range
        }

        uploads_collection.insert_one(new_upload)
        
        # Clean up the temporary file
        os.remove(temp_filepath)
        
        success_message = f"Image uploaded successfully!"
        return render_template("upload.html", success_message=success_message)
        
    except Exception as e:
        print(f"Error uploading to Google Cloud Storage: {e}")
        # Clean up the temporary file
        try:
            os.remove(temp_filepath)
        except:
            pass
        return render_template("upload.html", error_message=f"Upload failed: {str(e)}")
    
@app.route("/serve_image/<filename>")
def serve_image(filename):
    """Serve images from Google Cloud Storage"""
    if "user" not in session:
        return "Unauthorized", 401
    
    temp_local_filename = None
    try:
        # Create a temporary file to store the downloaded image
        _, temp_local_filename = tempfile.mkstemp()
        
        # Download the file from Google Cloud Storage
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        blob.download_to_filename(temp_local_filename)
        
        # Determine the MIME type based on file extension
        mime_type = 'image/jpeg'  # Default
        if filename.lower().endswith('.png'):
            mime_type = 'image/png'
        elif filename.lower().endswith('.webp'):
            mime_type = 'image/webp'
        
        # Set cache control headers
        response = send_file(
            temp_local_filename,
            mimetype=mime_type,
            as_attachment=False,
            download_name=filename
        )
        response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
        return response
    
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return "Image not found", 404
    finally:
        # Always clean up the temporary file
        if temp_local_filename and os.path.exists(temp_local_filename):
            try:
                os.remove(temp_local_filename)
            except Exception as e:
                print(f"Error removing temporary file: {e}")
    
@app.route("/fix_image_urls")
def fix_image_urls():
    if "user" not in session:
        return "Unauthorized", 401
        
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return "User not found", 404
    
    # Find all uploads for this user
    user_uploads = list(uploads_collection.find({"user_id": user["_id"]}))
    updated_count = 0
    
    for item in user_uploads:
        if "image_url" in item and "filename" in item:
            # Create the new URL
            filename = item["filename"]
            new_url = f"/serve_image/{filename}"
            
            # Update the item
            result = uploads_collection.update_one(
                {"_id": item["_id"]},
                {"$set": {"image_url": new_url}}
            )
            
            if result.modified_count > 0:
                updated_count += 1
    
    return f"Updated {updated_count} image URLs. Please refresh your wardrobe page."

@app.route("/remove_item/<item_id>", methods=["POST"])
def remove_item(item_id):
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Find the item to get the filename
    item = uploads_collection.find_one({"item_id": item_id, "user_id": user["_id"]})
    if not item:
        return jsonify({"success": False, "message": "Item not found or not authorized to delete"}), 404
    
    # Delete the item from Google Cloud Storage
    try:
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(item['filename'])
        blob.delete()
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file from Google Cloud Storage: {e}")
    
    # Delete the item from the database
    result = uploads_collection.delete_one({"item_id": item_id, "user_id": user["_id"]})
    
    if result.deleted_count > 0:
        # Also remove the item from any saved outfits
        outfits_to_delete = []
        
        # Find outfits containing this item
        outfits = outfits_collection.find({
            "$or": [
                {"top_id": item_id},
                {"bottom_id": item_id},
                {"shoe_id": item_id}
            ],
            "user_id": user["_id"]
        })
        
        for outfit in outfits:
            outfits_to_delete.append(outfit["outfit_id"])
        
        # Delete identified outfits
        if outfits_to_delete:
            outfits_collection.delete_many({
                "outfit_id": {"$in": outfits_to_delete},
                "user_id": user["_id"]
            })
        
        return jsonify({"success": True, "message": "Item deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Failed to delete item"}), 500
    
@app.route("/clear_wardrobe", methods=["POST"])
def clear_wardrobe():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    try:
        # Get all wardrobe items for this user
        wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))
        
        # Delete all files from Google Cloud Storage
        bucket = storage_client.bucket(GCS_BUCKET)
        for item in wardrobe_items:
            try:
                blob = bucket.blob(item['filename'])
                blob.delete()
            except Exception as e:
                # Continue even if some file deletions fail
                print(f"Error deleting file {item['filename']} from GCS: {e}")
        
        # Delete all items from the database
        uploads_result = uploads_collection.delete_many({"user_id": user["_id"]})
        
        # Delete all outfits for this user
        outfits_result = outfits_collection.delete_many({"user_id": user["_id"]})
        
        return jsonify({
            "success": True, 
            "message": f"Wardrobe cleared successfully. Removed {uploads_result.deleted_count} items and {outfits_result.deleted_count} outfits."
        })
    except Exception as e:
        print(f"Error clearing wardrobe: {e}")
        return jsonify({"success": False, "message": f"Error clearing wardrobe: {str(e)}"}), 500
    
@app.route("/get_weather", methods=["POST"])
def get_weather():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    location = data.get("location")
    
    if not location:
        return jsonify({
            "success": False,
            "message": "Please provide a location (city name or ZIP code)."
        }), 400
    
    try:
        # Call OpenWeather API
        weather_data = get_weather_by_location(location, app.config['OPENWEATHER_API_KEY'])
        
        if not weather_data:
            return jsonify({
                "success": False,
                "message": "Could not retrieve weather data. Please check the location and try again."
            }), 404
        
        # Extract relevant weather data
        temp = weather_data['main']['temp']  # Already rounded to nearest whole number in the utility function
        weather_id = weather_data['weather'][0]['id']
        weather_condition = get_weather_condition_by_id(weather_id)
        weather_description = weather_data['weather'][0]['description']
        
        # Get recommended outfit type
        outfit_recommendation = determine_outfit_type_by_weather(temp, weather_condition)
        
        return jsonify({
            "success": True,
            "location": weather_data['name'],
            "temperature": temp,
            "weather_condition": weather_condition,
            "weather_description": weather_description,
            "outfit_recommendation": outfit_recommendation
        })
    except Exception as e:
        print(f"Error getting weather data: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred while fetching weather data. Please try again."
        }), 500
    
@app.route("/generate_weather_outfit", methods=["POST"])
def generate_weather_outfit():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    temperature = data.get("temperature")
    weather_condition = data.get("weather_condition")
    
    # Validate data
    if temperature is None or not weather_condition:
        return jsonify({
            "success": False,
            "message": "Temperature and weather condition are required."
        }), 400
        
    # Validate weather condition
    valid_conditions = ["sunny", "cloudy", "rain", "snow", "other"]
    if weather_condition not in valid_conditions:
        return jsonify({
            "success": False,
            "message": f"Invalid weather condition. Valid options are: {', '.join(valid_conditions)}"
        }), 400
    
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Get the user's wardrobe items
    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))
    
    # Separate items by category
    tops = [item for item in wardrobe_items if item["category"] == "top"]
    bottoms = [item for item in wardrobe_items if item["category"] == "bottom"]
    shoes = [item for item in wardrobe_items if item["category"] == "shoes"]
    
    # Check if wardrobe has enough items (only require tops and shoes)
    if len(tops) < 1 or len(shoes) < 1:
        return jsonify({
            "success": False, 
            "message": "Your wardrobe needs at least one top and one pair of shoes to generate an outfit."
        }), 400
    
    # Use the weather-based outfit generator to generate an outfit
    try:
        selected_top, best_bottom, best_shoes = generate_weather_based_outfit(
            tops, bottoms, shoes, temperature, weather_condition
        )
        
        # Check if this is a complete top outfit (no bottom)
        is_complete_top = selected_top.get("subcategory") == "complete"
        
        if is_complete_top:
            # For complete tops, best_bottom will be None
            if not all([selected_top, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": f"Could not generate a suitable outfit for {weather_condition} weather at {temperature}°F. Try uploading more items."
                }), 400
            
            # Return outfit with no bottom - UPDATED to use GCS URLs
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": selected_top["image_url"],  # Use GCS URL directly
                    "colors": selected_top.get("colors", []),
                    "weather_conditions": selected_top.get("weather_conditions", []),
                    "temperature_range": selected_top.get("temperature_range", []),
                    "unavailable": selected_top.get("unavailable", False)
                },
                "bottom": None,  # No bottom for complete tops
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": best_shoes["image_url"],  # Use GCS URL directly
                    "colors": best_shoes.get("colors", []),
                    "weather_conditions": best_shoes.get("weather_conditions", []),
                    "temperature_range": best_shoes.get("temperature_range", []),
                    "unavailable": best_shoes.get("unavailable", False)
                },
                "outfit_type": f"{weather_condition.capitalize()} Weather Outfit ({temperature}°F)",
                "is_complete_top": True  # Flag to indicate this is a complete top
            })
        else:
            # For standard tops, we need bottom + shoes
            if not all([selected_top, best_bottom, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": f"Could not generate a suitable outfit for {weather_condition} weather at {temperature}°F. Try uploading more items."
                }), 400
            
            # UPDATED to use GCS URLs
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": selected_top["image_url"],  # Use GCS URL directly
                    "colors": selected_top.get("colors", []),
                    "weather_conditions": selected_top.get("weather_conditions", []),
                    "temperature_range": selected_top.get("temperature_range", []),
                    "unavailable": selected_top.get("unavailable", False)
                },
                "bottom": {
                    "id": best_bottom["item_id"],
                    "image_url": best_bottom["image_url"],  # Use GCS URL directly
                    "colors": best_bottom.get("colors", []),
                    "weather_conditions": best_bottom.get("weather_conditions", []),
                    "temperature_range": best_bottom.get("temperature_range", []),
                    "unavailable": best_bottom.get("unavailable", False)
                },
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": best_shoes["image_url"],  # Use GCS URL directly
                    "colors": best_shoes.get("colors", []),
                    "weather_conditions": best_shoes.get("weather_conditions", []),
                    "temperature_range": best_shoes.get("temperature_range", []),
                    "unavailable": best_shoes.get("unavailable", False)
                },
                "outfit_type": f"{weather_condition.capitalize()} Weather Outfit ({temperature}°F)",
                "is_complete_top": False  # Flag to indicate this is a standard top
            })
    except Exception as e:
        print(f"Error generating weather-based outfit: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to generate outfit. Please try again."
        }), 500
    
@app.route("/toggle_item_availability/<item_id>", methods=["POST"])
def toggle_item_availability(item_id):
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Get the request data
    data = request.get_json()
    unavailable = data.get("unavailable", False)
    
    # Find the item
    item = uploads_collection.find_one({"item_id": item_id, "user_id": user["_id"]})
    if not item:
        return jsonify({"success": False, "message": "Item not found or not authorized to update"}), 404
    
    # Update the item's unavailable status
    result = uploads_collection.update_one(
        {"item_id": item_id, "user_id": user["_id"]},
        {"$set": {"unavailable": unavailable}}
    )
    
    if result.modified_count > 0 or result.matched_count > 0:
        return jsonify({
            "success": True, 
            "message": f"Item marked as {'unavailable' if unavailable else 'available'}"
        })
    else:
        return jsonify({"success": False, "message": "Failed to update item status"}), 500

if __name__ == "__main__":
    app.run(debug=True)