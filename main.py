from src import data_ingestion, data_cleaning, nlp_processing, db_loader
def main():
    print("Step 1: Ingestion")
    data_ingestion.main()

    print("\nStep 2: Cleaning")
    data_cleaning.main()

    print("\nStep 3: NLP processing")
    nlp_processing.main()

    print("\nStep 4: Database load")
    db_loader.main()

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()