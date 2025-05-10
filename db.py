import sqlite3

# Connect to the SQLite database
def connect_db():
    return sqlite3.connect("chatbot.db")

# Create the necessary tables
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Create the users table (for registration and login)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        scheduled_meeting INTEGER DEFAULT 0
    )
    """)

    # Create the chats table (to save user-chat history)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        question TEXT,
        answer TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# Register a new user
def register_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:  # Handles case where username already exists
        return False
    finally:
        conn.close()

# Log in an existing user
def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Check if the user has already scheduled a meeting
def has_scheduled_meeting(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT scheduled_meeting FROM users WHERE username = ?", (username,))
    scheduled = cursor.fetchone()
    conn.close()
    return scheduled and scheduled[0] == 1

# Mark the meeting as scheduled for the user
def mark_meeting_scheduled(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET scheduled_meeting = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# Cancel the meeting for the user
def cancel_meeting(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET scheduled_meeting = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# Save the user chat history
def save_chat(username, question, answer):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chats (username, question, answer) VALUES (?, ?, ?)", (username, question, answer))
    conn.commit()
    conn.close()

# Retrieve the user's chat history
def get_user_chats(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM chats WHERE username = ? ORDER BY timestamp", (username,))
    chats = cursor.fetchall()
    conn.close()
    return chats

