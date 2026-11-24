import sqlite3


connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT NOT NULL,
        checked_out_books INTEGER
    )
""")
cursor.executemany(
    "INSERT INTO users (username, password, checked_out_books) VALUES (?, ?, ?)",
    [
        ("jane", "jane-password", 3),
        ("john", "john-password", 2),
    ],
)
connection.commit()


def vulnerable_login(username_input, password_input):
    query = f"SELECT * FROM users WHERE username = '{username_input}' AND password = '{password_input}'"
    print(f"\nExecuting Query: {query}")

    cursor.execute(query)
    result = cursor.fetchall()

    if result:
        print("[Access Granted] Records retrieved: ")
        for row in result:
            print(f" = ID: {row[0]} | User: {row[1]} | Password: {row[2]} | Books: {row[3]}")
    else:
        print(f"[Access Denied] Invalid credentials.")

print("Normal login:")
vulnerable_login("jane", "jane-password")

print("\nSQL Injection Attack:")
# this uses SQL syntax to make the value "true"
malicious_user = "' OR '1'='1' -- "
fake_password = 'fake_pass'
vulnerable_login(malicious_user, fake_password)


def secure_login(username_input, pin_input):
    secure_query = """
        SELECT username
        FROM users
        WHERE username = ? AND password = ?
    """

    cursor.execute(secure_query, (username_input, pin_input))
    results = cursor.fetchall()

    if results:
        print("[Access Granted]")
        for row in results:
            print(f"User: {row[0]}")
    else:
        print("[Access Denied] Invalid credentials.")


print(f'\nAnother SQL Injection attempt:')
secure_login(malicious_user, fake_password)