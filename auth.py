import os
import bcrypt
import jwt

from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# JWT secret
JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-this-secret-key"
)


# Connect to MongoDB
client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]

users_collection = db["users"]


# Create unique indexes
users_collection.create_index(
    "email",
    unique=True
)

users_collection.create_index(
    "username",
    unique=True
)


# --------------------------------------------------
# REGISTER USER
# --------------------------------------------------

def register_user(username, email, password):

    # Check whether user already exists

    existing_user = users_collection.find_one(
        {
            "$or": [
                {"username": username},
                {"email": email}
            ]
        }
    )

    if existing_user:
        return {
            "success": False,
            "message": "Username or email already exists."
        }


    # Convert password into bytes

    password_bytes = password.encode("utf-8")


    # Generate password hash

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )


    # Create user document

    user = {

        "username": username,

        "email": email,

        "password": password_hash.decode("utf-8"),

        "interests": [],

        "created_at": datetime.now(timezone.utc)

    }


    # Insert user into MongoDB

    result = users_collection.insert_one(user)


    return {

        "success": True,

        "message": "User registered successfully.",

        "user_id": str(result.inserted_id)

    }


# --------------------------------------------------
# LOGIN USER
# --------------------------------------------------

def login_user(email, password):

    # Find user

    user = users_collection.find_one(
        {
            "email": email
        }
    )


    # User not found

    if not user:

        return {

            "success": False,

            "message": "Invalid email or password."

        }


    # Convert stored password to bytes

    stored_password =user["password"].encode("utf-8")


    # Check password

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        stored_password
    ):

        return {

            "success": False,

            "message": "Invalid email or password."

        }


    # Create JWT token

    payload = {

        "user_id": str(user["_id"]),

        "username": user["username"],

        "exp": datetime.now(
            timezone.utc
        ) + timedelta(hours=24)

    }


    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )


    return {

        "success": True,

        "message": "Login successful.",

        "token": token,

        "username": user["username"]

    }