
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Connect to the SFILS MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "sfils_db")
        )
        return connection
    except Error as error:
        print(f"\nDatabase connection failed: {error}")
        return None


def view_summary(connection):
    """Display overall database statistics."""
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            COUNT(*) AS total_records,
            SUM(checkout_total) AS total_checkouts,
            SUM(renewal_total) AS total_renewals,
            ROUND(AVG(checkout_total), 2) AS average_checkouts,
            ROUND(AVG(renewal_total), 2) AS average_renewals
        FROM library_usage_records
    """

    cursor.execute(query)
    result = cursor.fetchone()

    print("\n--- SFILS DATABASE SUMMARY ---")
    print(f"Total records:       {result['total_records']:,}")
    print(f"Total checkouts:     {result['total_checkouts']:,}")
    print(f"Total renewals:      {result['total_renewals']:,}")
    print(f"Average checkouts:   {result['average_checkouts']}")
    print(f"Average renewals:    {result['average_renewals']}")

    cursor.close()


def view_usage_records(connection):
    """Display a sample of library usage records."""
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            u.record_id,
            p.patron_type_definition AS patron_type,
            u.checkout_total,
            u.renewal_total,
            u.age_range,
            l.home_library_definition AS library,
            u.circulation_active_month,
            u.circulation_active_year
        FROM library_usage_records u
        LEFT JOIN patron_types p
            ON u.patron_type_code = p.patron_type_code
        LEFT JOIN libraries l
            ON u.library_id = l.library_id
        ORDER BY u.record_id
        LIMIT 20
    """

    cursor.execute(query)
    records = cursor.fetchall()

    print("\n--- FIRST 20 USAGE RECORDS ---")
    for record in records:
        print(
            f"\nRecord ID: {record['record_id']}"
            f"\nPatron type: {record['patron_type']}"
            f"\nCheckouts: {record['checkout_total']}"
            f"\nRenewals: {record['renewal_total']}"
            f"\nAge range: {record['age_range']}"
            f"\nLibrary: {record['library']}"
            f"\nCirculation period: "
            f"{record['circulation_active_month']} "
            f"{record['circulation_active_year']}"
        )

    cursor.close()


def search_by_patron_type(connection):
    """Search usage records by patron type."""
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT patron_type_code, patron_type_definition
        FROM patron_types
        ORDER BY patron_type_code
    """)

    patron_types = cursor.fetchall()

    print("\n--- PATRON TYPES ---")
    for patron in patron_types:
        print(
            f"{patron['patron_type_code']}: "
            f"{patron['patron_type_definition']}"
        )

    choice = input("\nEnter a patron type code: ").strip()

    if not choice.isdigit():
        print("Please enter a valid numeric code.")
        cursor.close()
        return

    cursor.execute("""
        SELECT
            p.patron_type_definition AS patron_type,
            COUNT(*) AS total_records,
            SUM(u.checkout_total) AS total_checkouts,
            SUM(u.renewal_total) AS total_renewals
        FROM library_usage_records u
        JOIN patron_types p
            ON u.patron_type_code = p.patron_type_code
        WHERE p.patron_type_code = %s
        GROUP BY p.patron_type_definition
    """, (int(choice),))

    result = cursor.fetchone()

    if result:
        print("\n--- SEARCH RESULTS ---")
        print(f"Patron type: {result['patron_type']}")
        print(f"Records: {result['total_records']:,}")
        print(f"Checkouts: {result['total_checkouts']:,}")
        print(f"Renewals: {result['total_renewals']:,}")
    else:
        print("No records found for that patron type.")

    cursor.close()


def view_usage_by_library(connection):
    """Summarize usage records by library."""
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            l.home_library_definition AS library,
            COUNT(*) AS total_records,
            SUM(u.checkout_total) AS total_checkouts,
            SUM(u.renewal_total) AS total_renewals
        FROM library_usage_records u
        LEFT JOIN libraries l
            ON u.library_id = l.library_id
        GROUP BY l.home_library_definition
        ORDER BY total_checkouts DESC
    """)

    results = cursor.fetchall()

    print("\n--- USAGE BY LIBRARY ---")
    for row in results:
        library = row["library"] or "Unknown"
        print(
            f"{library}: "
            f"{row['total_records']:,} records, "
            f"{row['total_checkouts']:,} checkouts, "
            f"{row['total_renewals']:,} renewals"
        )

    cursor.close()


def main():
    connection = get_connection()

    if connection is None:
        print("Unable to start the application.")
        return

    print("\nWelcome to the SFILS Library Usage System!")

    while True:
        print("\n========== MAIN MENU ==========")
        print("1. View database summary")
        print("2. View sample usage records")
        print("3. Search by patron type")
        print("4. View usage by library")
        print("5. Exit")

        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            view_summary(connection)
        elif choice == "2":
            view_usage_records(connection)
        elif choice == "3":
            search_by_patron_type(connection)
        elif choice == "4":
            view_usage_by_library(connection)
        elif choice == "5":
            print("\nThank you for using SFILS!")
            break
        else:
            print("Invalid selection. Please choose 1-5.")

    connection.close()


if __name__ == "__main__":
    main()
