from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timezone

from auth import register_user, login_user
from recommendation import get_user_interests, get_recommended_news

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Test MongoDB connection
try:
    client.admin.command("ping")
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed:", e)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Get news from MongoDB
@app.route("/news")
def get_news():

    category = request.args.get("category")

    query = {}

    if category and category != "all":
        query["category"] = category

    articles = list(
        db.news.find(
            query,
            {
                "_id": 0,
                "title": 1,
                "description": 1,
                "url": 1,
                "image": 1,
                "publishedAt": 1,
                "source": 1,
                "category": 1
            }
        )
    )

    return jsonify(articles)
# --------------------------------------------------
# REGISTER API
# --------------------------------------------------

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    result = register_user(
        username,
        email,
        password
    )

    if result["success"]:

        return jsonify(result), 201

    return jsonify(result), 409
# --------------------------------------------------
# LOGIN API
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    result = login_user(
        email,
        password
    )

    if result["success"]:

        return jsonify(result), 200

    return jsonify(result), 401

@app.route("/login-page")
def login_page():
    return render_template("login.html")

# ==========================================
# RECORD USER INTERACTION
# ==========================================

@app.route("/interaction", methods=["POST"])
def record_interaction():

    data = request.get_json()

    token = data.get("token")
    article_url = data.get("article_url")
    category = data.get("category")
    action = data.get("action", "read")

    # Check required data
    if not token or not article_url or not category:

        return jsonify({
            "success": False,
            "message": "Missing interaction data."
        }), 400

    try:

        # Decode JWT token
        payload = jwt.decode(
            token,
            os.getenv(
                "JWT_SECRET",
                "change-this-secret-key"
            ),
            algorithms=["HS256"]
        )

        user_id = payload["user_id"]

        # Save interaction in MongoDB
        db.user_interactions.insert_one({

            "user_id": user_id,

            "article_url": article_url,

            "category": category,

            "action": action,

            "timestamp":
                datetime.now(timezone.utc)

        })

        return jsonify({

            "success": True,

            "message":
                "Interaction recorded successfully."

        }), 200


    except jwt.ExpiredSignatureError:

        return jsonify({

            "success": False,

            "message":
                "Login session expired."

        }), 401


    except jwt.InvalidTokenError:

        return jsonify({

            "success": False,

            "message":
                "Invalid login token."

        }), 401


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500

    # ==========================================
# PERSONALIZED RECOMMENDATIONS
# ==========================================

@app.route("/recommendations")
def recommendations():

    token = request.headers.get("Authorization")

    if not token:
        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    try:

        # Remove "Bearer " if it exists
        if token.startswith("Bearer "):
            token = token[7:]

        # Decode JWT
        payload = jwt.decode(
            token,
            os.getenv(
                "JWT_SECRET",
                "change-this-secret-key"
            ),
            algorithms=["HS256"]
        )

        user_id = payload["user_id"]

        # Get recommendations
        articles = get_recommended_news(
            user_id,
            limit=10
        )

        # Get user's interests
        interests = get_user_interests(
            user_id
        )

        return jsonify({
            "success": True,
            "interests": interests,
            "articles": articles
        })

    except jwt.ExpiredSignatureError:

        return jsonify({
            "success": False,
            "message": "Login session expired."
        }), 401

    except jwt.InvalidTokenError:

        return jsonify({
            "success": False,
            "message": "Invalid login token."
        }), 401

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)