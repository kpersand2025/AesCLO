from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import uuid
import os

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

# Protect other routes with session authentication
@app.route("/upload")
def upload():
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
    return render_template("wardrobe.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")  

if __name__ == "__main__":
    app.run(debug=True)
    