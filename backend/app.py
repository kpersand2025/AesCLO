from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from bson.objectid import ObjectId

app = Flask(__name__, 
            template_folder="../templates",  
            static_folder="../static")  

CORS(app)

# Configure MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/fashionProject"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
users_collection = mongo.db.users  # Collection for storing users

# Route for the login page (set as default page)
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if the username exists in the database
        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            return redirect(url_for("home"))
        else:
            return "Invalid credentials. Please try again."

    return render_template("login.html")  # Default page to login

# Route for user signup
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json  # Expecting JSON payload from frontend

    # Extract user details
    username = data.get("username")
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    password = data.get("password")

    # Check if username or email already exists
    if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"message": "Username or email already exists"}), 400

    # Hash the password before storing
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Insert user into MongoDB
    user = {
        "_id": ObjectId(),
        "username": username,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "password": hashed_password
    }
    users_collection.insert_one(user)

    return jsonify({"message": "User signed up successfully"}), 201

# Route for the home page after successful login
@app.route("/home")
def home():
    return render_template("home.html")  # Home page after login

if __name__ == "__main__":
    app.run(debug=True)
