import sqlite3
from datetime import datetime
import traceback



def initialize_orphans_database():
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Создание таблицы users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE
        )
    """)

    # Создание таблицы orphans
    cursor.execute('''CREATE TABLE IF NOT EXISTS orphans (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        age INTEGER,
                        gift TEXT,
                        chosen INTEGER DEFAULT 0,
                        chosen_by TEXT)''')

    # Создание таблицы chosen_kids
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chosen_kids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_phone TEXT NOT NULL,
            orphan_id INTEGER NOT NULL,
            orphan_name TEXT NOT NULL,
            orphan_gift TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (orphan_id) REFERENCES orphans(id)
        )
    """)

    conn.commit()
    conn.close()




# Modify the 'chosen_kids' table to include telegram_username
def log_chosen_kid(user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chosen_kids (user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift, chosen_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift))

    conn.commit()
    conn.close()





# Mark an orphan as chosen and record who chose them
def mark_orphan_chosen(orphan_id, user_name):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()
    
    # Mark orphan as chosen and store the user's name
    cursor.execute("UPDATE orphans SET chosen = 1, chosen_by = ? WHERE id = ?", (user_name, orphan_id))
    
    conn.commit()
    conn.close()

# Log the inquiry (which user inquired about which orphan)
def log_inquiry(user_id, orphan_id):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inquiries (user_id, orphan_id, timestamp) VALUES (?, ?, ?)",
        (user_id, orphan_id, datetime.now()),
    )
    conn.commit()
    conn.close()

# Store user information (name and phone)
import sqlite3

def store_user_info(user_name, phone_number, telegram_username):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Check if the user already exists by phone number
    cursor.execute("SELECT id FROM users WHERE phone = ?", (phone_number,))
    existing_user = cursor.fetchone()

    if existing_user:
        # User exists, fetch user_id
        user_id = existing_user[0]
    else:
        # User does not exist, insert new user and get the user_id starting from 1
        cursor.execute("""
            INSERT INTO users (name, phone, telegram_username)
            VALUES (?, ?, ?)
        """, (user_name, phone_number, telegram_username))
        
        # Ensure the user_id starts from 1 or continues with the next available ID
        cursor.execute("SELECT MAX(id) FROM users")
        max_id = cursor.fetchone()[0]
        user_id = max_id if max_id is not None else 1  # If no users exist, start from 1

    # Commit changes
    conn.commit()
    conn.close()

    return user_id







# Get all unchosen orphan ids
def get_all_unchosen_orphan_ids():
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM orphans WHERE chosen = 0")
    orphan_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return orphan_ids

# Get orphan details by id
def get_orphan_by_id(orphan_id):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orphans WHERE id = ?", (orphan_id,))
    orphan = cursor.fetchone()
    conn.close()
    return orphan


def get_user_id(telegram_user_id):
    # Connect to the database
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Query to fetch the user_id from the users table based on the telegram_user_id
    cursor.execute("""
        SELECT id FROM users WHERE telegram_user_id = ?
    """, (telegram_user_id,))

    # Fetch the result
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]  # Return the user_id
    else:
        return None 