# 🎅 Arman Bot: Spreading Joy with Telegram 🎁

This repository hosts a Telegram bot designed to support the **"Arman – 2024"** initiative, helping users bring joy to children during the holiday season.

Despite being thousands of kilometers away, I had the incredible opportunity to contribute to this heartfelt charity initiative by developing and deploying a chatbot for a project in Astana. The **Arman** initiative was organized by my sister, Dana Yessimkhanova, and Akerke Korganbekova. It is part of their annual tradition of finding "Secret Santa" (or "Deduska Moroz," or Grandfather Frost in post-Soviet countries) for children with special needs and those in orphanages.

The **Arman Chat Bot** was created to streamline the process of matching children’s heartfelt letters, filled with their wishes, to dedicated volunteers.

---

## Features

### **Interactive Telegram Bot:**
- Collects user information (name, phone number, Telegram username).
- Displays a list of children and their gift wishes.
- Allows users to adopt a child and tracks this in the database.
- Uploads data to Amazon S3 for secure backups.

### **SQLite Integration:**
- Securely stores user and orphan information.
- Keeps track of both chosen and unchosen children.

### **Excel Exports:**
- Automatically generates Excel reports for tracking purposes.

### **AWS S3 Integration:**
- Uploads reports to a specified S3 bucket for remote access and backups.

---

## Repository Structure

```bash
├── dataset/
│   └── [Orphans_Table.csv](dataset/Orphans_Table.csv)         # Input data with orphan details
├── helper_methods/
│   └── [create_database.py](helper_methods/create_database.py)        # Script to create and initialize the database
├── [bot.py](bot.py)                        # Main Telegram bot script
├── [database.py](database.py)                   # Database helper functions
├── [orphans.db](orphans.db)                    # SQLite database file
├── [requirements.txt](requirements.txt)              # Python dependencies
├── [README.md](README.md)                     # Documentation




# Getting Started

### Prerequisites
- Python 3.8+
- A Telegram bot token (can be created using [BotFather](https://core.telegram.org/bots#botfather)).
- AWS credentials for S3 integration.

### Setup

1. **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Initialize the Database:**  
   Run the script to populate the database with orphan details:
    ```bash
    python helper_methods/create_database.py
    ```

4. **Configure the Environment:**  
   Update the `bot.py` file with:
   - Your Telegram bot token (`TOKEN`).
   - Your AWS S3 bucket details (`S3_BUCKET_NAME`, `S3_REGION`).

5. **Run the Bot:**
    ```bash
    python bot.py
    ```

---

## Database

The SQLite database (`[orphans.db](orphans.db)`) includes three tables:

- **users**: Stores user details (name, phone number, Telegram username).
- **orphans**: Stores orphan details (name, age, gift wishes, parent contact, etc.).
- **chosen_kids**: Logs the relationship between users and adopted children.

---

## Deployment

Deploy the bot to a server (e.g., AWS EC2) or a serverless environment (e.g., AWS Lambda). Ensure you use a process manager like **systemd** or **pm2** for long-running scripts.

---

## S3 Backup

The bot uploads two Excel files (`[orphans.xlsx] and `[chosen_kids.xlsx] to an S3 bucket after each update. Ensure your AWS credentials are configured using `~/.aws/credentials` or environment variables.
