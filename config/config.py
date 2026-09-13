import os
from pathlib import Path

# Root of the project (two levels up from this file: config/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = Path(os.getenv("HOTEL_DATA_DIR", PROJECT_ROOT / "data" / "hotels"))
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_INGESTED_CSV = PROCESSED_DIR / "raw_ingested_reviews.csv"
CLEANED_REVIEWS_CSV = PROCESSED_DIR / "cleaned_reviews.csv"
REVIEWS_WITH_SENTIMENT_CSV = PROCESSED_DIR / "reviews_with_sentiment.csv"
REVIEW_ASPECTS_CSV = PROCESSED_DIR / "review_aspects.csv"

# Parsing constants 
EXPECTED_FIELD_COUNT = 3  # date, title, review
DELIMITER = "\t"

# dataset folders and must be skipped rather than parsed as text
SKIP_EXTENSIONS = {".rar", ".zip", ".7z", ".db", ".ini"}

# Cleaning constants
DATE_FORMATS = [
    "%b %d %Y",   
    "%B %d %Y",   
    "%b %d, %Y",  
    "%B %d, %Y",  
]

# NLP constants 
ASPECT_KEYWORDS = {
    "room": ["room", "bed", "bathroom", "shower"],
    "staff": ["staff", "service", "reception", "receptionist"],
    "location": ["location", "located", "walk", "distance", "nearby"],
    "breakfast": ["breakfast", "buffet"],
    "price": ["price", "value", "expensive", "cheap", "cost"],
    "cleanliness": ["clean", "dirty", "dust", "smell"],
    "noise": ["noise", "noisy", "quiet", "loud"],
}
SENTIMENT_POSITIVE_THRESHOLD = 0.05
SENTIMENT_NEGATIVE_THRESHOLD = -0.05

# MySQL database config
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "hotel_reviews")


PROCESSED_DIR.mkdir(parents=True, exist_ok=True)