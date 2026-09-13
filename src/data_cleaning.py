import html
import re
import pandas as pd
from loggers import logging as _logging_setup 
import logging

from config.config import RAW_INGESTED_CSV, CLEANED_REVIEWS_CSV, DATE_FORMATS

logger = logging.getLogger(__name__)


def clean_review_text(text: str) -> str | None:
    if pd.isnull(text):
        return None

    text = html.unescape(text)          # &amp; -> &, &quot; -> "
    text = text.replace("\ufffd", "")   # strip leftover replacement chars
    text = re.sub(r"\s+", " ", text)    # collapse whitespace,newlines,tabs
    text = text.strip()

    return text if text else None


def parse_date(date_str: str):
    if pd.isnull(date_str):
        return None

    date_str = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse date with any known format: '{date_str}'")
    return None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    initial_rows = len(df)
    logger.info(f"Starting cleaning on {initial_rows} rows")

    df = df.copy()

    # Drop exact duplicates
    dup_count = df.duplicated().sum()
    if dup_count:
        logger.info(f"Dropping {dup_count} exact duplicate rows")
    df = df.drop_duplicates()

    # Clean text fields
    df["title_clean"] = df["title_raw"].apply(clean_review_text)
    df["review_clean"] = df["review_raw"].apply(clean_review_text)

    # Parse dates
    df["date_parsed"] = df["date_raw"].apply(parse_date)
    unparsed_dates = df["date_parsed"].isnull().sum() - df["date_raw"].isnull().sum()
    if unparsed_dates > 0:
        logger.warning(f"{unparsed_dates} non-null dates failed to parse; see log for values")

    logger.info(f"Cleaning complete: {len(df)} rows remain (from {initial_rows})")
    return df


def main():
    if not RAW_INGESTED_CSV.exists():
        raise FileNotFoundError(
            f"{RAW_INGESTED_CSV} not found. Run 'python -m src.data_ingestion' first."
        )

    df = pd.read_csv(RAW_INGESTED_CSV)
    df_clean = clean_dataframe(df)

    df_clean.to_csv(CLEANED_REVIEWS_CSV, index=False)
    logger.info(f"Saved cleaned data to {CLEANED_REVIEWS_CSV}")

    print(f"Rows before cleaning: {len(df)}")
    print(f"Rows after cleaning: {len(df_clean)}")
    print(f"Saved cleaned data to {CLEANED_REVIEWS_CSV}")
    print("Check the logs/ folder for any dates that failed to parse.")


if __name__ == "__main__":
    main()
