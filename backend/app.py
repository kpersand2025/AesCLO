from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os

app = Flask(__name__, 
            template_folder="../templates",  # Adjusted to point to the correct location
            static_folder="../static")  # Adjusted to point to the correct location
CORS(app)

# Configure MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/fashionProject"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
users_collection = mongo.db.users  # Collection for storing users

# Route for home page
@app.route("/")
def home():
    return render_template("home.html")  # Ensure home.html exists in the templates folder

# Route for user registration
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if users_collection.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    users_collection.insert_one({"username": username, "password": hashed_password})
    
    return jsonify({"message": "User registered successfully"}), 201

# Route for user login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(debug=True)
