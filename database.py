import sqlite3
from datetime import datetime
import pandas as pd
import traceback

def initialize_orphans_database():
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Create 'users' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        telegram_username TEXT NOT NULL
    )
    """)

    # Create 'orphans' table with parent_phone and hyper_link columns
    cursor.execute('''CREATE TABLE IF NOT EXISTS orphans (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        age INTEGER,
                        gift TEXT,
                        parent_phone TEXT,
                        hyper_link TEXT,
                        chosen INTEGER DEFAULT 0,
                        chosen_by TEXT)''')

    # Create 'chosen_kids' table with the 'chosen_time' column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chosen_kids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_phone TEXT NOT NULL,
            telegram_username TEXT,
            orphan_id INTEGER NOT NULL,
            orphan_name TEXT NOT NULL,
            orphan_gift TEXT NOT NULL,
            orphan_parent_phone TEXT NOT NULL,
            orphan_hyper_link TEXT NOT NULL,
            chosen_time TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (orphan_id) REFERENCES orphans(id)
        )   
    """)

    conn.commit()
    conn.close()
    export_to_excel()  # Initial export of the tables to Excel


def export_to_excel():
    try:
        conn = sqlite3.connect("orphans.db")
        
        # Export orphans table
        orphans_df = pd.read_sql_query("SELECT * FROM orphans", conn)
        orphans_df.to_excel("orphans.xlsx", index=False, engine="openpyxl")
        
        # Export chosen_kids table
        chosen_kids_df = pd.read_sql_query("SELECT * FROM chosen_kids", conn)
        chosen_kids_df.to_excel("chosen_kids.xlsx", index=False, engine="openpyxl")
        
        conn.close()
    except Exception as e:
        print("Error exporting to Excel:", traceback.format_exc())


# Modify the 'chosen_kids' table to include telegram_username
def log_chosen_kid(user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chosen_kids (user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift, chosen_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift))

    conn.commit()  # Ensure changes are committed immediately
    conn.close()

    export_to_excel()  # Update Excel files after logging


def mark_orphan_chosen(orphan_id, chosen_by):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Update the chosen and chosen_by columns for the orphan
    cursor.execute("""
        UPDATE orphans SET chosen = 1, chosen_by = ? WHERE id = ?
    """, (chosen_by, orphan_id))

    conn.commit()  # Ensure changes are committed immediately
    conn.close()

    export_to_excel()  # Update Excel files after marking an orphan



def store_user_info(user_name, phone, telegram_username):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    try:
        # Check if the phone number already exists
        cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        existing_user = cursor.fetchone()

        if existing_user:
            # If the phone number exists, return the user_id
            user_id = existing_user[0]
        else:
            # Insert user info into the users table if phone doesn't exist
            cursor.execute("""
                INSERT INTO users (name, phone, telegram_username) VALUES (?, ?, ?)
            """, (user_name, phone, telegram_username))
            conn.commit()
            user_id = cursor.lastrowid  # Fetch the user_id of the inserted user

    except sqlite3.IntegrityError as e:
        print(f"Database error: {e}")
        user_id = None  # Handle the error gracefully

    finally:
        conn.close()

    return user_id


def get_all_unchosen_orphan_ids():
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Fetch IDs of all unchosen orphans
    cursor.execute("""
        SELECT id FROM orphans WHERE chosen = 0
    """)
    result = [row[0] for row in cursor.fetchall()]
    conn.close()

    return result


def get_orphan_by_id(orphan_id):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    # Fetch orphan details including the new columns
    cursor.execute("""
        SELECT id, name, age, gift, parent_phone, hyper_link 
        FROM orphans WHERE id = ?
    """, (orphan_id,))
    orphan = cursor.fetchone()
    conn.close()

    return orphan