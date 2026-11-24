
import pandas as pd
from pathlib import Path
import re

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "SFPL_DataSF_library-usage_Jan_2023.xlsx"
)

RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def clean_column_name(column):
    parts = [p.strip() for p in str(column).split("\n")]
    parts = [p for p in parts if p]
    name = parts[-1] if parts else str(column)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    return name.strip("_").lower()

df = pd.read_excel(DATA_FILE)
df.columns = [clean_column_name(c) for c in df.columns]

relationships = [
    ("patron_type_code", "patron_type_definition"),
    ("home_library_code", "home_library_definition"),
    ("notification_medium_code", "notification_code_definition")
]

all_mappings = []

for code, definition in relationships:

    print(f"\n===== {code} -> {definition} =====")

    mapping = (
        df[[code, definition]]
        .drop_duplicates()
        .sort_values(by=[code, definition], na_position="last")
    )

    all_mappings.append(mapping.assign(
        source_code_column=code,
        source_definition_column=definition
    ))

    print(mapping.to_string(index=False))

    code_counts = (
        df.groupby(code, dropna=False)[definition]
        .nunique(dropna=False)
    )

    violations = code_counts[code_counts > 1]

    print("\nCodes with multiple definitions:")
    print(violations if not violations.empty else "None")

    definition_counts = (
        df.groupby(definition, dropna=False)[code]
        .nunique(dropna=False)
    )

    reverse_violations = definition_counts[
        definition_counts > 1
    ]

    print("\nDefinitions with multiple codes:")
    print(reverse_violations if not reverse_violations.empty else "None")

output = pd.concat(all_mappings, ignore_index=True)

output.to_csv(
    RESULTS_DIR / "dimension_mappings.csv",
    index=False
)

print("\n===== UNIQUE CIRCULATION MONTHS =====")
print(sorted(df["circulation_active_month"].dropna().unique()))

print("\n===== RELATIONSHIP ANALYSIS COMPLETE =====")
print("Saved results/dimension_mappings.csv")
