import csv
from pathlib import Path
import chardet
import pandas as pd
from loggers import logging as _logging_setup  
import logging

from config.config import (
    DATA_DIR,
    RAW_INGESTED_CSV,
    EXPECTED_FIELD_COUNT,
    DELIMITER,
    SKIP_EXTENSIONS,
)

logger = logging.getLogger(__name__)


def detect_encoding(file_path: Path, sample_size: int = 5000) -> str:
    try:
        with open(file_path, "rb") as f:
            raw = f.read(sample_size)
        result = chardet.detect(raw)
        return result["encoding"] or "utf-8"
    except Exception as e:
        logger.warning(f"Encoding detection failed for {file_path}, defaulting to utf-8: {e}")
        return "utf-8"


def parse_hotel_file(file_path: Path, city: str, hotel_name: str) -> list[dict]:
    parsed_rows = []
    encoding = detect_encoding(file_path)

    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            reader = csv.reader(f, delimiter=DELIMITER, quoting=csv.QUOTE_NONE)
            for line_num, fields in enumerate(reader, start=1):
                if len(fields) == EXPECTED_FIELD_COUNT + 1 and fields[-1] == "":
                    fields = fields[:EXPECTED_FIELD_COUNT]

                if len(fields) != EXPECTED_FIELD_COUNT:
                    logger.warning(
                        f"Skipping malformed line {line_num} in {file_path} "
                        f"(expected {EXPECTED_FIELD_COUNT} fields, got {len(fields)}): {fields}"
                    )
                    continue

                date_raw, title_raw, review_raw = fields
                parsed_rows.append(
                    {
                        "city": city,
                        "hotel_name": hotel_name,
                        "date_raw": date_raw.strip(),
                        "title_raw": title_raw.strip(),
                        "review_raw": review_raw.strip()
                    }
                )
    except (UnicodeDecodeError, PermissionError, FileNotFoundError) as e:
        logger.error(f"Failed to read {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")

    return parsed_rows


def ingest_all(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    all_rows = []
    city_folders = [p for p in data_dir.iterdir() if p.is_dir()]
    logger.info(f"Found {len(city_folders)} city folders under {data_dir}")

    for city_folder in city_folders:
        city = city_folder.name
        hotel_files = [
            p for p in city_folder.glob("*")
            if p.is_file() and p.suffix.lower() not in SKIP_EXTENSIONS
        ]
        logger.info(f"Processing city '{city}': {len(hotel_files)} hotel files")

        for hotel_file in hotel_files:
            hotel_name = hotel_file.stem
            rows = parse_hotel_file(hotel_file, city, hotel_name)
            all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    logger.info(f"Ingestion complete: {len(df)} total rows from {len(city_folders)} cities")
    return df


def main():
    df = ingest_all()
    print(f"Total reviews ingested: {len(df)}")
    if not df.empty:
        print(f"Cities found: {df['city'].nunique()}")
        print(f"Hotels found: {df['hotel_name'].nunique()}")
        print(df.head())

    df.to_csv(RAW_INGESTED_CSV, index=False)
    logger.info(f"Saved raw ingested data to {RAW_INGESTED_CSV}")
    print(f"Saved raw ingested data to {RAW_INGESTED_CSV}")
    print("Check the logs/ folder for any skipped/malformed lines.")


if __name__ == "__main__":
    main()