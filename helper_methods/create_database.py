import sqlite3
import csv


def load_orphans_from_csv(csv_file):
    conn = sqlite3.connect("orphans.db")
    cursor = conn.cursor()

    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            cursor.execute(
                '''INSERT OR REPLACE INTO orphans (id, name, age, gift, chosen, chosen_by) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (row["id"], row["name"], row["age"], row["gift"], row["chosen"], row["chosen_by"]),
            )
    
    conn.commit()
    conn.close()

def main():
    # Step 1: Create the database tables
    #create_tables()

    # Step 2: Load orphans data from CSV into the database
    csv_file = "Orphans_Table.csv"  # Ensure this file is in the same directory
    load_orphans_from_csv(csv_file)

    print("Orphans data has been successfully loaded into the database.")

if __name__ == "__main__":
    main()
