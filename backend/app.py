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
    