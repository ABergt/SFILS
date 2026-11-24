
import re
from pathlib import Path
from numbers import Integral, Real

import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os


PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "SFPL_DataSF_library-usage_Jan_2023.xlsx"
)

BATCH_SIZE = 5000

load_dotenv(PROJECT_DIR / ".env")


def clean_column_name(column):
    parts = [p.strip() for p in str(column).split("\n")]
    parts = [p for p in parts if p]

    name = parts[-1] if parts else str(column)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)

    return name.strip("_").lower()


def clean_text(value):
    if pd.isna(value):
        return None

    if isinstance(value, Integral):
        return str(int(value))

    if isinstance(value, Real):
        if float(value).is_integer():
            return str(int(value))

    result = str(value).strip()
    return result if result else None


def clean_integer(value, field_name, nullable=False):
    if pd.isna(value):
        if nullable:
            return None
        raise ValueError(f"{field_name} cannot be missing.")

    number = float(value)

    if not number.is_integer():
        raise ValueError(
            f"{field_name} must be a whole number. Found: {value!r}"
        )

    return int(number)


def clean_boolean(value, field_name):
    if pd.isna(value):
        raise ValueError(f"{field_name} cannot be missing.")

    if isinstance(value, bool):
        return value

    if value in (1, 1.0, "1", "True", "true", "TRUE"):
        return True

    if value in (0, 0.0, "0", "False", "false", "FALSE"):
        return False

    raise ValueError(
        f"Unexpected boolean value in {field_name}: {value!r}"
    )


EXPECTED_COLUMNS = [
    "patron_type_code",
    "patron_type_definition",
    "checkout_total",
    "renewal_total",
    "age_range",
    "home_library_code",
    "home_library_definition",
    "circulation_active_month",
    "circulation_active_year",
    "notification_medium_code",
    "notification_code_definition",
    "provided_email_address",
    "within_san_francisco_county",
    "year_patron_registered",
]


def load_source_data():
    print("Reading Excel dataset...")

    df = pd.read_excel(DATA_FILE)
    df.columns = [clean_column_name(c) for c in df.columns]

    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names found after cleaning.")

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {missing_columns}"
        )

    df = df[EXPECTED_COLUMNS]

    print(f"Loaded {len(df):,} source rows.")
    return df


def insert_dimensions(cursor, df):
    print("\nInserting dimension records...")

    patron_mapping = {}

    for code, definition in df[
        ["patron_type_code", "patron_type_definition"]
    ].itertuples(index=False, name=None):

        code = clean_integer(code, "patron_type_code")
        definition = clean_text(definition)

        if definition is None:
            raise ValueError(
                f"Missing definition for patron type {code}."
            )

        if code in patron_mapping and patron_mapping[code] != definition:
            raise ValueError(
                f"Patron type code {code} has multiple definitions."
            )

        patron_mapping[code] = definition

    patron_rows = list(patron_mapping.items())

    cursor.executemany(
        """
        INSERT INTO patron_types
            (patron_type_code, patron_type_definition)
        VALUES (%s, %s)
        """,
        patron_rows,
    )

    print(f"  Patron types: {len(patron_rows)}")


    library_mapping = {}

    for code, definition in df[
        ["home_library_code", "home_library_definition"]
    ].itertuples(index=False, name=None):

        code = clean_text(code)
        definition = clean_text(definition)

        if definition is None:
            raise ValueError(
                f"Missing library definition for code {code!r}."
            )

        if code in library_mapping:
            if library_mapping[code] != definition:
                raise ValueError(
                    f"Library code {code!r} has multiple definitions."
                )
        else:
            library_mapping[code] = definition

    library_rows = list(library_mapping.items())

    cursor.executemany(
        """
        INSERT INTO libraries
            (home_library_code, home_library_definition)
        VALUES (%s, %s)
        """,
        library_rows,
    )

    print(f"  Libraries: {len(library_rows)}")

    age_values = {
        clean_text(value)
        for value in df["age_range"]
    }
    age_values.discard(None)

    age_rows = [(value,) for value in sorted(age_values)]

    cursor.executemany(
        """
        INSERT INTO age_ranges (age_range)
        VALUES (%s)
        """,
        age_rows,
    )

    print(f"  Age ranges: {len(age_rows)}")

    notification_mapping = {}

    for code, definition in df[
        ["notification_medium_code", "notification_code_definition"]
    ].itertuples(index=False, name=None):

        code = clean_text(code)
        definition = clean_text(definition)

        if code is None:
            continue

        if code in notification_mapping:
            if notification_mapping[code] != definition:
                raise ValueError(
                    f"Notification code {code!r} has multiple definitions."
                )
        else:
            notification_mapping[code] = definition

    notification_rows = list(notification_mapping.items())

    cursor.executemany(
        """
        INSERT INTO notification_preferences
            (notification_medium_code, notification_code_definition)
        VALUES (%s, %s)
        """,
        notification_rows,
    )

    print(f"  Notification preferences: {len(notification_rows)}")



def get_dimension_mappings(cursor):
    cursor.execute(
        "SELECT patron_type_code FROM patron_types"
    )
    patron_codes = {
        row[0] for row in cursor.fetchall()
    }

    cursor.execute(
        "SELECT home_library_code, library_id FROM libraries"
    )
    library_ids = {
        code: library_id
        for code, library_id in cursor.fetchall()
    }

    cursor.execute(
        "SELECT age_range FROM age_ranges"
    )
    age_ranges = {
        row[0] for row in cursor.fetchall()
    }

    cursor.execute(
        "SELECT notification_medium_code FROM notification_preferences"
    )
    notification_codes = {
        row[0] for row in cursor.fetchall()
    }

    return (
        patron_codes,
        library_ids,
        age_ranges,
        notification_codes,
    )



def build_usage_record(
    row,
    index,
    patron_codes,
    library_ids,
    age_ranges,
    notification_codes,
):
    patron_code = clean_integer(
        row[index["patron_type_code"]],
        "patron_type_code",
    )

    if patron_code not in patron_codes:
        raise ValueError(
            f"Unknown patron type code: {patron_code}"
        )

    library_code = clean_text(
        row[index["home_library_code"]]
    )

    if library_code not in library_ids:
        raise ValueError(
            f"Unknown library code: {library_code!r}"
        )

    library_id = library_ids[library_code]

    age_range = clean_text(
        row[index["age_range"]]
    )

    if age_range is not None and age_range not in age_ranges:
        raise ValueError(
            f"Unknown age range: {age_range!r}"
        )

    notification_code = clean_text(
        row[index["notification_medium_code"]]
    )

    if (
        notification_code is not None
        and notification_code not in notification_codes
    ):
        raise ValueError(
            f"Unknown notification code: {notification_code!r}"
        )

    return (
        patron_code,
        clean_integer(
            row[index["checkout_total"]],
            "checkout_total",
        ),
        clean_integer(
            row[index["renewal_total"]],
            "renewal_total",
        ),
        age_range,
        library_id,
        clean_text(
            row[index["circulation_active_month"]]
        ),
        clean_integer(
            row[index["circulation_active_year"]],
            "circulation_active_year",
            nullable=True,
        ),
        notification_code,
        clean_boolean(
            row[index["provided_email_address"]],
            "provided_email_address",
        ),
        clean_boolean(
            row[index["within_san_francisco_county"]],
            "within_san_francisco_county",
        ),
        clean_integer(
            row[index["year_patron_registered"]],
            "year_patron_registered",
        ),
    )


def insert_usage_records(cursor, df):
    print("\nPreparing usage records...")

    (
        patron_codes,
        library_ids,
        age_ranges,
        notification_codes,
    ) = get_dimension_mappings(cursor)

    column_index = {
        column: position
        for position, column in enumerate(df.columns)
    }

    insert_sql = """
        INSERT INTO library_usage_records (
            patron_type_code,
            checkout_total,
            renewal_total,
            age_range,
            library_id,
            circulation_active_month,
            circulation_active_year,
            notification_medium_code,
            provided_email_address,
            within_san_francisco_county,
            year_patron_registered
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """

    batch = []
    total_inserted = 0

    for row in df.itertuples(index=False, name=None):
        record = build_usage_record(
            row,
            column_index,
            patron_codes,
            library_ids,
            age_ranges,
            notification_codes,
        )

        batch.append(record)

        if len(batch) >= BATCH_SIZE:
            cursor.executemany(insert_sql, batch)
            total_inserted += len(batch)
            batch.clear()

            print(
                f"  Processed {total_inserted:,} records..."
            )

    if batch:
        cursor.executemany(insert_sql, batch)
        total_inserted += len(batch)

    print(f"  Usage records inserted: {total_inserted:,}")
    return total_inserted



def check_tables_are_empty(cursor):
    tables = [
        "patron_types",
        "libraries",
        "age_ranges",
        "notification_preferences",
        "library_usage_records",
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        if count != 0:
            raise RuntimeError(
                f"Table '{table}' already contains {count:,} rows. "
                "Import stopped to avoid duplicating data."
            )



def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = load_source_data()

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "sfils_db"),
        )

        cursor = connection.cursor()

        print("\nConnected to MySQL.")
        check_tables_are_empty(cursor)

        insert_dimensions(cursor, df)
        total_inserted = insert_usage_records(cursor, df)

        connection.commit()

        print("\nImport completed successfully.")
        print(f"Total source rows: {len(df):,}")
        print(f"Total inserted rows: {total_inserted:,}")

    except Exception:
        if connection is not None:
            connection.rollback()

        print("\nImport failed. The transaction was rolled back.")
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
