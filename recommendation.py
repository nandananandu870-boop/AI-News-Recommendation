import os

from pymongo import MongoClient
from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")


# ==========================================
# MONGODB CONNECTION
# ==========================================

client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]

news_collection = db["news"]

interactions_collection = db["user_interactions"]


# ==========================================
# GET USER INTERESTS
# ==========================================

def get_user_interests(user_id):

    interactions = list(
        interactions_collection.find(
            {
                "user_id": user_id,
                "action": "read"
            }
        )
    )


    # No interactions yet
    if not interactions:

        return []


    # Count how many times each category
    # was read by the user

    category_counts = {}


    for interaction in interactions:

        category = interaction.get(
            "category"
        )

        if not category:

            continue


        category_counts[category] = (
            category_counts.get(
                category,
                0
            ) + 1
        )


    # Sort categories by number of reads

    sorted_categories = sorted(
        category_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )


    return sorted_categories


# ==========================================
# GET PERSONALIZED NEWS
# ==========================================

def get_recommended_news(
    user_id,
    limit=10
):

    # Find user's preferred categories

    interests = get_user_interests(
        user_id
    )


    # If user has no history,
    # return latest news

    if not interests:

        return list(
            news_collection.find(
                {},
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
            ).sort(
                "publishedAt",
                -1
            ).limit(limit)
        )


    # Get category names

    preferred_categories = [
        category
        for category, count
        in interests
    ]


    # Find news from preferred categories

    recommended_news = list(
        news_collection.find(
            {
                "category": {
                    "$in":
                        preferred_categories
                }
            },
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


    # Sort articles according to
    # user's category preference

    category_score = {
        category: len(preferred_categories)
        - index

        for index, category
        in enumerate(
            preferred_categories
        )
    }


    recommended_news.sort(
        key=lambda article:
            category_score.get(
                article.get("category"),
                0
            ),
        reverse=True
    )


    return recommended_news[:limit]


# ==========================================
# TEST THE RECOMMENDATION SYSTEM
# ==========================================

if __name__ == "__main__":

    # Replace this with a real user_id
    # from MongoDB when testing

    test_user_id = "6ac1096e4e0dded7272acee1"


    print("\nUser Interests:")
    print(
        get_user_interests(
            test_user_id
        )
    )


    print("\nRecommended News:")

    recommendations = get_recommended_news(
        test_user_id,
        limit=10
    )


    for article in recommendations:

        print(
            article.get("category"),
            "->",
            article.get("title")
        )