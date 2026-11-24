
from pymongo import MongoClient, ASCENDING

client = MongoClient("mongodb://localhost:27017")
database = client["sfils_mongo"]
collection = database["library_usage_records"]

indexes = [
    ("patron_type_code", ASCENDING),
    ("home_library_code", ASCENDING),
    ("year_patron_registered", ASCENDING),
    ("circulation_active_year", ASCENDING),
    ("circulation_active_month", ASCENDING),
]

for field, direction in indexes:
    collection.create_index([(field, direction)])
    print(f"Created index: {field}")

print("\nIndexes:")
for index in collection.list_indexes():
    print(index["name"], index["key"])

client.close()
