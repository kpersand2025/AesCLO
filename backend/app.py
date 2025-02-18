from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__, 
            template_folder="../templates",  # Explicitly point to the templates folder
            static_folder="../static")  # Explicitly point to the static folder

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

# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if users_collection.find_one({"username": username}):
            return "Username already exists."

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        users_collection.insert_one({"username": username, "password": hashed_password})
        
        return redirect(url_for("login"))

    return render_template("signup.html")  # Registration page

# Route for the home page after successful login
@app.route("/home")
def home():
    return render_template("home.html")  # Home page after login

# Route for signup page
@app.route("/signup")
def signup():
    return render_template("signup.html")  # Render signup page

if __name__ == "__main__":
    app.run(debug=True)
