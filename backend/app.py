from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import uuid
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime

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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

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

# Add this route to your app.py file

@app.route("/remove_wardrobe_item", methods=["POST"])
def remove_wardrobe_item():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    item_id = data.get("item_id")
    
    if not item_id:
        return jsonify({"success": False, "message": "No item ID provided"}), 400
        
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # First, find the item to get its filename for file deletion
    item = uploads_collection.find_one({"item_id": item_id, "user_id": user["_id"]})
    
    if not item:
        return jsonify({"success": False, "message": "Item not found or not authorized to delete"}), 404
    
    # Delete the item from the database
    result = uploads_collection.delete_one({"item_id": item_id, "user_id": user["_id"]})
    
    if result.deleted_count > 0:
        # Delete the physical file from the uploads folder
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], item['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error deleting file: {e}")
            
        # Check if this item is part of any saved outfits
        # Option 1: Delete outfits that contain this item
        outfits_collection.delete_many({
            "user_id": user["_id"],
            "$or": [
                {"top_id": item_id},
                {"bottom_id": item_id},
                {"shoe_id": item_id}
            ]
        })
        
        # Alternatively, you could mark outfits as having missing items instead of deleting them
        
        return jsonify({"success": True, "message": "Item deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Failed to delete item"}), 500

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

# Image upload handler (POST request)
@app.route("/upload", methods=["POST"])
def upload_image():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files['file']
    category = request.form.get('category')

    # Retrieve the user document using the username stored in the session
    user = users_collection.find_one({"username": session["user"]})
    if not user:
        return jsonify({"message": "User not found"}), 404

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"  # Avoid filename conflicts
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(filepath)

        # Save image details in MongoDB with ObjectId as user_id and item_id
        new_upload = {
            "item_id": str(uuid.uuid4()),  # Unique ID for each clothing item
            "user_id": user["_id"],  # Store MongoDB ObjectId instead of username
            "image_url": filepath,
            "category": category,
            "filename": unique_filename,
            "timestamp": datetime.utcnow().isoformat()  # Proper timestamp
        }

        uploads_collection.insert_one(new_upload)

        # Return success message and redirect to the upload page
        return render_template("upload.html", success_message="Image uploaded successfully!")

    else:
        return jsonify({"message": "Invalid file type. Only .png, .jpg, .jpeg are allowed."}), 400

if __name__ == "__main__":
    app.run(debug=True)
    