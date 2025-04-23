from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import uuid
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime
from google.cloud import vision
import io

# Import your utility modules
from utils.color_utils import get_color_name, calculate_color_match_score
from utils.vision_utils import extract_colors, predict_clothing_category
from utils.outfit_generator import generate_color_coordinated_outfit, has_color
from utils.gemini_utils import analyze_clothing_occasion
from utils.weather_utils import get_weather_data, categorize_weather
from utils.outfit_generator import generate_weather_based_outfit

app = Flask(__name__, 
            template_folder="../templates",  
            static_folder="../static")  

CORS(app)
app.secret_key = os.urandom(24)  # Stronger secret key for security

# Session security configurations
app.config["SESSION_PERMANENT"] = False  # Session expires when browser closes
app.config["SESSION_TYPE"] = "filesystem"  # Store session data securely

# Configure MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/fashionProject"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
users_collection = mongo.db.users  
uploads_collection = mongo.db.uploads
outfits_collection = mongo.db.outfits

# Folder for uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Google Cloud Vision client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/kpersand/credentials/fashionproject-455321-7a2d0b04586c.json"  # Update with your service key path
vision_client = vision.ImageAnnotatorClient()

# Set your Gemini API key 
os.environ["GEMINI_API_KEY"] = "AIzaSyCSzFT7uYvI-qH8vJIveXXNrfKlIZ5ZdFA"

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    
    # Extract only colors that exist in tops
    available_colors = set()
    for item in tops:
        if 'colors' in item and item['colors']:
            for color_data in item['colors']:
                color_name = color_data['name'].lower()
                if color_name != 'unknown':  # Skip unknown colors
                    available_colors.add(color_name)
    
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
    if len(all_tops) < 1 or len(bottoms) < 1 or len(shoes) < 1:
        return jsonify({
            "success": False, 
            "message": "Your wardrobe needs at least one top, one bottom, and one pair of shoes to generate an outfit."
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
            # Use the outfit generator module with the random top as the basis
            _, best_bottom, best_shoes = generate_color_coordinated_outfit(
                [selected_top], bottoms, shoes, base_color
            )
            
            if not all([selected_top, best_bottom, best_shoes]):
                return jsonify({
                    "success": False,
                    "message": "Could not generate a well-coordinated outfit. Please try again or try with different items."
                }), 400
            
            return jsonify({
                "success": True,
                "top": {
                    "id": selected_top["item_id"],
                    "image_url": f"/static/uploads/{selected_top['filename']}",
                    "colors": selected_top.get("colors", [])
                },
                "bottom": {
                    "id": best_bottom["item_id"],
                    "image_url": f"/static/uploads/{best_bottom['filename']}",
                    "colors": best_bottom.get("colors", [])
                },
                "shoes": {
                    "id": best_shoes["item_id"],
                    "image_url": f"/static/uploads/{best_shoes['filename']}",
                    "colors": best_shoes.get("colors", [])
                },
                "coordination_style": f"Random Color Coordination",
                "base_color": base_color
            })
        except Exception as e:
            print(f"Error generating random color outfit: {e}")
            return jsonify({
                "success": False,
                "message": "Failed to generate random color outfit. Please try again."
            }), 500
    
    # Regular color-coordinated flow (unchanged)
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
        
        if not all([selected_top, best_bottom, best_shoes]):
            return jsonify({
                "success": False,
                "message": "Could not generate a well-coordinated outfit. Please try again or try with different items."
            }), 400
        
        return jsonify({
            "success": True,
            "top": {
                "id": selected_top["item_id"],
                "image_url": f"/static/uploads/{selected_top['filename']}",
                "colors": selected_top.get("colors", [])
            },
            "bottom": {
                "id": best_bottom["item_id"],
                "image_url": f"/static/uploads/{best_bottom['filename']}",
                "colors": best_bottom.get("colors", [])
            },
            "shoes": {
                "id": best_shoes["item_id"],
                "image_url": f"/static/uploads/{best_shoes['filename']}",
                "colors": best_shoes.get("colors", [])
            },
            "coordination_style": f"{base_color.capitalize()} Coordinated Outfit",
            "base_color": base_color
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
    
    # Check if wardrobe has enough items
    if len(tops) < 1 or len(bottoms) < 1 or len(shoes) < 1:
        return jsonify({
            "success": False, 
            "message": "Your wardrobe needs at least one top, one bottom, and one pair of shoes to generate an outfit."
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
    if not tops_matching_occasion and not bottoms_matching_occasion and not shoes_matching_occasion:
        return jsonify({
            "success": False,
            "message": f"No items found for the '{target_occasion}' occasion. Try uploading more items or selecting a different occasion."
        }), 400
    
    # Use the outfit generator module to generate an occasion-based outfit
    try:
        # Import the function if needed
        from utils.outfit_generator import generate_occasion_based_outfit
        
        # IMPORTANT: Only pass items that match the selected occasion to the generator
        selected_top, best_bottom, best_shoes = generate_occasion_based_outfit(
            tops_matching_occasion, bottoms_matching_occasion, shoes_matching_occasion, target_occasion
        )
        
        if not all([selected_top, best_bottom, best_shoes]):
            return jsonify({
                "success": False,
                "message": f"Could not generate a suitable outfit for {target_occasion}. Try uploading more items."
            }), 400
        
        return jsonify({
            "success": True,
            "top": {
                "id": selected_top["item_id"],
                "image_url": f"/static/uploads/{selected_top['filename']}",
                "colors": selected_top.get("colors", []),
                "occasions": selected_top.get("occasions", [])
            },
            "bottom": {
                "id": best_bottom["item_id"],
                "image_url": f"/static/uploads/{best_bottom['filename']}",
                "colors": best_bottom.get("colors", []),
                "occasions": best_bottom.get("occasions", [])
            },
            "shoes": {
                "id": best_shoes["item_id"],
                "image_url": f"/static/uploads/{best_shoes['filename']}",
                "colors": best_shoes.get("colors", []),
                "occasions": best_shoes.get("occasions", [])
            },
            "outfit_type": f"{target_occasion.capitalize()} Outfit"
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
    bottom_id = data.get("bottom_id")
    shoe_id = data.get("shoe_id")
    
    # Validate data
    if not all([top_id, bottom_id, shoe_id]):
        return jsonify({"success": False, "message": "Missing outfit items"}), 400
        
    # Get user information
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Create new outfit entry
    new_outfit = {
        "outfit_id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "top_id": top_id,
        "bottom_id": bottom_id,
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

    # Convert MongoDB ObjectId to string and format the data
    for item in wardrobe_items:
        item["_id"] = str(item["_id"])
        item["image_url"] = f"/static/uploads/{item['filename']}"

    return render_template("wardrobe.html", wardrobe_items=wardrobe_items)

@app.route("/get_wardrobe")
def get_wardrobe():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"message": "User not found"}), 404

    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))

    wardrobe = {"tops": [], "bottoms": [], "shoes": []}

    for item in wardrobe_items:
        item_data = {
            "id": item["item_id"],  # Include the item ID
            "image_url": f"/static/uploads/{item['filename']}",
            "category": item["category"]
        }
        if item["category"] == "top":
            wardrobe["tops"].append(item_data)
        elif item["category"] == "bottom":
            wardrobe["bottoms"].append(item_data)
        elif item["category"] == "shoes":
            wardrobe["shoes"].append(item_data)

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
    
    # Build detailed outfit data including image URLs
    outfits_data = []
    for outfit in saved_outfits:
        top = uploads_collection.find_one({"item_id": outfit["top_id"]})
        bottom = uploads_collection.find_one({"item_id": outfit["bottom_id"]})
        shoe = uploads_collection.find_one({"item_id": outfit["shoe_id"]})
        
        if top and bottom and shoe:
            outfit_data = {
                "outfit_id": outfit["outfit_id"],
                "name": outfit["name"],
                "created_at": outfit["created_at"],
                "top_image": f"/static/uploads/{top['filename']}",
                "bottom_image": f"/static/uploads/{bottom['filename']}",
                "shoe_image": f"/static/uploads/{shoe['filename']}"
            }
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

    # Save file
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)

    # Predict category using object detection
    predicted_category = predict_clothing_category(filepath, vision_client)

    if not predicted_category:
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error removing temporary file: {e}")

        return render_template("upload.html", 
                               error_message="This image doesn't appear to be a clothing item. Please upload a clearer or different image.")

    # Extract dominant colors
    try:
        colors = extract_colors(filepath, vision_client)
        dominant_colors = []
        for color in colors[:3]:
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
        
    # Analyze clothing occasion using Gemini 2.0 Flash
    try:
        occasions = analyze_clothing_occasion(filepath)
        print(f"Detected occasions: {occasions}")
    except Exception as e:
        print(f"Error analyzing clothing occasion: {e}")
        occasions = []

    # Save item in database with occasion tags
    new_upload = {
        "item_id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "image_url": filepath,
        "category": predicted_category,
        "filename": unique_filename,
        "timestamp": datetime.utcnow().isoformat(),
        "colors": dominant_colors,
        "occasions": occasions  # Add the occasions field to the document
    }

    uploads_collection.insert_one(new_upload)

    # Construct success message with occasion information
    success_message = f"Image uploaded successfully! Detected as: {predicted_category.capitalize()}"
    if occasions:
        occasions_str = ", ".join(occasions)
        success_message += f" (Occasions: {occasions_str})"

    return render_template("upload.html", success_message=success_message)

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
    
    # Delete the item from the database
    result = uploads_collection.delete_one({"item_id": item_id, "user_id": user["_id"]})
    
    if result.deleted_count > 0:
        # Remove the file from the filesystem
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], item['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Continue even if file deletion fails (file might not exist)
            print(f"Error deleting file: {e}")
        
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
        
        # Delete all files from the filesystem
        for item in wardrobe_items:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], item['filename'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Continue even if some file deletions fail
                print(f"Error deleting file {item['filename']}: {e}")
        
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
    
@app.route("/generate_weather_outfit", methods=["POST"])
def generate_weather_outfit():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    city = data.get("city")
    
    if not city:
        return jsonify({
            "success": False,
            "message": "Please provide a city name for weather-based outfit generation."
        }), 400
    
    # Get user
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Get weather data
    api_key = "09143375996e1f16666a753b3ffba37b"  # Your API key
    weather_data = get_weather_data(city, api_key)
    
    if not weather_data:
        return jsonify({
            "success": False,
            "message": f"Could not get weather data for {city}. Please check the city name and try again."
        }), 400
    
    # Categorize weather
    categorized_weather = categorize_weather(weather_data)
    
    # Get the user's wardrobe items
    wardrobe_items = list(uploads_collection.find({"user_id": user["_id"]}))
    
    # Separate items by category
    tops = [item for item in wardrobe_items if item["category"] == "top"]
    bottoms = [item for item in wardrobe_items if item["category"] == "bottom"]
    shoes = [item for item in wardrobe_items if item["category"] == "shoes"]
    
    # Check if wardrobe has enough items
    if len(tops) < 1 or len(bottoms) < 1 or len(shoes) < 1:
        return jsonify({
            "success": False, 
            "message": "Your wardrobe needs at least one top, one bottom, and one pair of shoes to generate an outfit."
        }), 400
    
    # Generate outfit
    try:
        selected_top, best_bottom, best_shoes = generate_weather_based_outfit(
            tops, bottoms, shoes, categorized_weather
        )
        
        if not all([selected_top, best_bottom, best_shoes]):
            return jsonify({
                "success": False,
                "message": "Could not generate a suitable outfit for this weather. Try uploading more varied items."
            }), 400
        
        # Format weather description
        weather_temp = weather_data["main"]["temp"]
        weather_desc = weather_data["weather"][0]["description"].capitalize()
        weather_summary = f"{weather_temp}°F, {weather_desc}"
        
        return jsonify({
            "success": True,
            "top": {
                "id": selected_top["item_id"],
                "image_url": f"/static/uploads/{selected_top['filename']}",
                "colors": selected_top.get("colors", [])
            },
            "bottom": {
                "id": best_bottom["item_id"],
                "image_url": f"/static/uploads/{best_bottom['filename']}",
                "colors": best_bottom.get("colors", [])
            },
            "shoes": {
                "id": best_shoes["item_id"],
                "image_url": f"/static/uploads/{best_shoes['filename']}",
                "colors": best_shoes.get("colors", [])
            },
            "weather": {
                "city": city,
                "temperature": weather_temp,
                "description": weather_desc,
                "summary": weather_summary,
                "category": categorized_weather["temp_category"],
                "condition": categorized_weather["weather_condition"]
            }
        })
    except Exception as e:
        print(f"Error generating weather-based outfit: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to generate weather-based outfit. Please try again."
        }), 500

if __name__ == "__main__":
    app.run(debug=True)