
from pymongo import MongoClient
from pprint import pprint
import re

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "sfils_mongo"
COLLECTION_NAME = "library_usage_records"


def normalize(name):
    name = name.splitlines()[0].strip()
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main():
    client = MongoClient(MONGO_URI)
    collection = client[DATABASE_NAME][COLLECTION_NAME]

    sample = collection.find_one()
    if sample is None:
        print("No records found. Import the dataset first.")
        client.close()
        return

    fields = {normalize(name): name for name in sample.keys()}

    def field(name):
        key = normalize(name)
        if key not in fields:
            raise KeyError(f"Could not find dataset field: {name}")
        return fields[key]

    def get_number(name):
        return {
            "$sum": {"$ifNull": [f"${field(name)}", 0]}
        }

    def show_summary():
        totals = collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_checkouts": get_number("Total Checkouts"),
                    "total_renewals": get_number("Total Renewals"),
                }
            }
        ])
        result = next(totals, {})
        count = collection.count_documents({})

        print("\n--- DATABASE SUMMARY ---")
        print(f"Total records: {count:,}")
        print(f"Total checkouts: {result.get('total_checkouts', 0):,}")
        print(f"Total renewals: {result.get('total_renewals', 0):,}")

    def show_sample():
        print("\n--- SAMPLE RECORDS ---")
        for record in collection.find().limit(5):
            record.pop("_id", None)
            pprint(record)
            print("-" * 40)

    def search_patron_type():
        code = input("Enter patron type code: ").strip()
        code_field = field("Patron Type Code")

        example = sample.get(code_field)
        if isinstance(example, int):
            code = int(code)

        results = collection.aggregate([
            {"$match": {code_field: code}},
            {
                "$group": {
                    "_id": None,
                    "records": {"$sum": 1},
                    "checkouts": get_number("Total Checkouts"),
                    "renewals": get_number("Total Renewals"),
                }
            }
        ])

        result = next(results, None)
        print("\n--- PATRON TYPE RESULTS ---")
        if result:
            print(f"Records: {result['records']:,}")
            print(f"Checkouts: {result['checkouts']:,}")
            print(f"Renewals: {result['renewals']:,}")
        else:
            print("No matching records found.")

    def usage_by_library():
        library_field = field("Home Library Definition")

        results = collection.aggregate([
            {
                "$group": {
                    "_id": f"${library_field}",
                    "records": {"$sum": 1},
                    "checkouts": get_number("Total Checkouts"),
                    "renewals": get_number("Total Renewals"),
                }
            },
            {"$sort": {"checkouts": -1}},
            {"$limit": 10}
        ])

        print("\n--- TOP 10 LIBRARIES BY CHECKOUTS ---")
        for result in results:
            print(
                f"{result['_id']}: "
                f"{result['records']:,} records, "
                f"{result['checkouts']:,} checkouts, "
                f"{result['renewals']:,} renewals"
            )

    def search_registration_year():
        year = int(input("Enter registration year: "))
        year_field = field("Year Patron Registered")

        count = collection.count_documents({year_field: year})
        print(f"\nRecords registered in {year}: {count:,}")

    try:
        while True:
            print("\n===== SFILS MONGODB APPLICATION =====")
            print("1. View database summary")
            print("2. View sample records")
            print("3. Search by patron type")
            print("4. View usage by library")
            print("5. Search by registration year")
            print("6. Exit")

            choice = input("Choose an option: ").strip()

            try:
                if choice == "1":
                    show_summary()
                elif choice == "2":
                    show_sample()
                elif choice == "3":
                    search_patron_type()
                elif choice == "4":
                    usage_by_library()
                elif choice == "5":
                    search_registration_year()
                elif choice == "6":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
            except (ValueError, KeyError) as error:
                print(f"Could not complete that operation: {error}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
