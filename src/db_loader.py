"""
Creates the MySQL database and schema (if they don't exist), then loads:
  - reviews_with_sentiment.csv -> `hotels` + `reviews` tables
  - review_aspects.csv         -> `review_aspects` table

Schema:
    hotels (hotel_id PK, hotel_name, city)
    reviews (review_id PK, hotel_id FK, review_date, title, review_text,
             sentiment_score, sentiment_label)
    review_aspects (id PK, review_id FK, aspect, aspect_sentiment)
"""

import pandas as pd
from sqlalchemy import create_engine, text
from loggers import logging as _logging_setup  
import logging

from config.config import (
    REVIEWS_WITH_SENTIMENT_CSV,
    REVIEW_ASPECTS_CSV,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
)

logger = logging.getLogger(__name__)

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS hotels (
        hotel_id INT AUTO_INCREMENT PRIMARY KEY,
        hotel_name VARCHAR(255) NOT NULL,
        city VARCHAR(100) NOT NULL,
        UNIQUE KEY uq_hotel (hotel_name, city)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reviews (
        review_id INT PRIMARY KEY,
        hotel_id INT NOT NULL,
        review_date DATE NULL,
        title VARCHAR(1000) NULL,
        review_text TEXT NULL,
        sentiment_score FLOAT NULL,
        sentiment_label VARCHAR(20) NULL,
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_aspects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        review_id INT NOT NULL,
        aspect VARCHAR(50) NOT NULL,
        aspect_sentiment FLOAT NULL,
        FOREIGN KEY (review_id) REFERENCES reviews(review_id)
    )
    """,
]


def get_server_engine():
    url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
    return create_engine(url)


def get_db_engine():
    url = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    return create_engine(url)


def create_database_if_missing():
    engine = get_server_engine()
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}"))
        conn.commit()
    logger.info(f"Database '{MYSQL_DATABASE}' ready")


def create_schema(engine):
    with engine.connect() as conn:
        for statement in SCHEMA_SQL:
            conn.execute(text(statement))
        conn.commit()
    logger.info("Schema created (hotels, reviews, review_aspects)")


def build_hotels_table(reviews_df: pd.DataFrame) -> pd.DataFrame:
    hotels = (
        reviews_df[["hotel_name", "city"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    hotels["hotel_id"] = hotels.index + 1
    return hotels[["hotel_id", "hotel_name", "city"]]


def load_data(engine):
    if not REVIEWS_WITH_SENTIMENT_CSV.exists() or not REVIEW_ASPECTS_CSV.exists():
        raise FileNotFoundError(
            "Missing input CSVs. Run 'python -m src.nlp_processing' first."
        )

    reviews_df = pd.read_csv(REVIEWS_WITH_SENTIMENT_CSV)
    review_aspects_df = pd.read_csv(REVIEW_ASPECTS_CSV)
    logger.info(f"Loaded {len(reviews_df)} reviews and {len(review_aspects_df)} aspect rows from CSV")

    # hotels
    hotels_df = build_hotels_table(reviews_df)
    hotels_df.to_sql("hotels", engine, if_exists="append", index=False, chunksize=500)
    logger.info(f"Inserted {len(hotels_df)} rows into hotels")

    # reviews (attach hotel_id via merge)
    reviews_final = reviews_df.merge(hotels_df, on=["hotel_name", "city"], how="left")
    reviews_final = reviews_final.rename(
        columns={"date_parsed": "review_date", "title_clean": "title", "review_clean": "review_text"}
    )[
        [
            "review_id",
            "hotel_id",
            "review_date",
            "title",
            "review_text",
            "sentiment_score",
            "sentiment_label",
        ]
    ]
    reviews_final.to_sql("reviews", engine, if_exists="append", index=False, chunksize=500)
    logger.info(f"Inserted {len(reviews_final)} rows into reviews")

    # review_aspects 
    review_aspects_df.to_sql(
        "review_aspects", engine, if_exists="append", index=False, chunksize=500
    )
    logger.info(f"Inserted {len(review_aspects_df)} rows into review_aspects")


def main():
    create_database_if_missing()
    engine = get_db_engine()
    create_schema(engine)
    load_data(engine)

    print("Database load complete.")
    print(f"Database: {MYSQL_DATABASE} on {MYSQL_HOST}:{MYSQL_PORT}")
    print("Tables: hotels, reviews, review_aspects")


if __name__ == "__main__":
    main()
