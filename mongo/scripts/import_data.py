
from pathlib import Path

import pandas as pd
from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "SFPL_DataSF_library-usage_Jan_2023.xlsx"

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "sfils_mongo"
COLLECTION_NAME = "library_usage_records"

BATCH_SIZE = 1000


def main():
    print("Connecting to MongoDB...")

    client = MongoClient(MONGO_URI)
    database = client[DATABASE_NAME]
    collection = database[COLLECTION_NAME]

    try:
        existing_count = collection.count_documents({})

        if existing_count > 0:
            print(
                f"Import cancelled: collection already contains "
                f"{existing_count:,} records."
            )
            print("No existing data was changed.")
            return

        if not DATA_FILE.exists():
            print(f"Dataset not found: {DATA_FILE}")
            return

        print("Reading Excel dataset...")
        dataframe = pd.read_excel(DATA_FILE)

        total_rows = len(dataframe)
        print(f"Found {total_rows:,} rows.")

        dataframe = dataframe.astype(object).where(
            pd.notna(dataframe), None
        )

        records = dataframe.to_dict(orient="records")

        print("Importing records...")

        for start in range(0, total_rows, BATCH_SIZE):
            batch = records[start:start + BATCH_SIZE]

            batch = [
                {
                    key: value.item() if hasattr(value, "item") else value
                    for key, value in record.items()
                }
                for record in batch
            ]

            collection.insert_many(batch)

            imported = min(start + BATCH_SIZE, total_rows)
            print(f"Imported {imported:,} / {total_rows:,}")

        final_count = collection.count_documents({})

        print("\nImport complete!")
        print(f"Records in MongoDB: {final_count:,}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
