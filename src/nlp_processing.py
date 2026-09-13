import re
import time
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from loggers import logging as _logging_setup 
import logging

from config.config import (
    CLEANED_REVIEWS_CSV,
    REVIEWS_WITH_SENTIMENT_CSV,
    REVIEW_ASPECTS_CSV,
    ASPECT_KEYWORDS,
    SENTIMENT_POSITIVE_THRESHOLD,
    SENTIMENT_NEGATIVE_THRESHOLD,
)

logger = logging.getLogger(__name__)
analyzer = SentimentIntensityAnalyzer()


def get_sentiment(text: str):
    if pd.isnull(text):
        return None, None

    compound = analyzer.polarity_scores(text)["compound"]
    if compound >= SENTIMENT_POSITIVE_THRESHOLD:
        label = "positive"
    elif compound <= SENTIMENT_NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"
    return compound, label


def split_sentences(text: str) -> list[str]:
    if pd.isnull(text):
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def get_sentence_aspect_sentiments(text: str) -> dict:
    if pd.isnull(text):
        return {}

    aspect_scores = {aspect: [] for aspect in ASPECT_KEYWORDS}

    for sentence in split_sentences(text):
        sentence_lower = sentence.lower()
        matched_aspects = [
            aspect for aspect, keywords in ASPECT_KEYWORDS.items()
            if any(kw in sentence_lower for kw in keywords)
        ]
        if not matched_aspects:
            continue
        compound = analyzer.polarity_scores(sentence)["compound"]
        for aspect in matched_aspects:
            aspect_scores[aspect].append(compound)

    return {
        aspect: sum(scores) / len(scores)
        for aspect, scores in aspect_scores.items()
        if scores
    }


def build_review_aspects_table(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for review_id, aspect_dict in zip(df["review_id"], df["aspect_sentiments"]):
        for aspect, score in aspect_dict.items():
            records.append(
                {"review_id": review_id, "aspect": aspect, "aspect_sentiment": score}
            )
    return pd.DataFrame(records)


def main():
    if not CLEANED_REVIEWS_CSV.exists():
        raise FileNotFoundError(
            f"{CLEANED_REVIEWS_CSV} not found. Run 'python -m src.data_cleaning' first."
        )

    df = pd.read_csv(CLEANED_REVIEWS_CSV)
    df["review_id"] = df.index  # stable id shared between both output files
    logger.info(f"Loaded {len(df)} cleaned reviews")

    start = time.time()

    sentiment_results = df["review_clean"].apply(get_sentiment)
    df["sentiment_score"] = sentiment_results.apply(lambda x: x[0])
    df["sentiment_label"] = sentiment_results.apply(lambda x: x[1])
    logger.info(f"Document-level sentiment done in {time.time() - start:.1f}s")

    start = time.time()
    df["aspect_sentiments"] = df["review_clean"].apply(get_sentence_aspect_sentiments)
    logger.info(f"Sentence-level aspect sentiment done in {time.time() - start:.1f}s")

    review_aspects_df = build_review_aspects_table(df)

    reviews_out = df[
        [
            "review_id",
            "city",
            "hotel_name",
            "date_parsed",
            "title_clean",
            "review_clean",
            "sentiment_score",
            "sentiment_label",
        ]
    ]

    reviews_out.to_csv(REVIEWS_WITH_SENTIMENT_CSV, index=False)
    review_aspects_df.to_csv(REVIEW_ASPECTS_CSV, index=False)

    logger.info(f"Saved {len(reviews_out)} rows to {REVIEWS_WITH_SENTIMENT_CSV}")
    logger.info(f"Saved {len(review_aspects_df)} rows to {REVIEW_ASPECTS_CSV}")

    print(f"Reviews with sentiment: {len(reviews_out)} rows -> {REVIEWS_WITH_SENTIMENT_CSV}")
    print(f"Review aspects (long format): {len(review_aspects_df)} rows -> {REVIEW_ASPECTS_CSV}")
    print("\nSentiment label distribution:")
    print(reviews_out["sentiment_label"].value_counts(dropna=False))
    print("\nAspect sentiment averages (sentence-level):")
    print(review_aspects_df.groupby("aspect")["aspect_sentiment"].mean().sort_values())


if __name__ == "__main__":
    main()
