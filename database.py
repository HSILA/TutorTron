import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import pickle

def get_user_credentials():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, name, email, role FROM users")
    users = cursor.fetchall()

    credentials = {'usernames': {}}
    for username, password, name, email, role in users:
        credentials['usernames'][str(username)] = {
            'password': str(password),
            'name': str(name),
            'email': str(email),
            'failed_login_attempts': 0,
            'logged_in': False,
            'role':str(role)
        }
    conn.close()
    return credentials

def create_user_credentials():
    df = pd.read_csv('users.csv')
    conn = sqlite3.connect('database.db')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT,
        role TEXT
    )
    ''')
    df.to_sql('users', conn, if_exists='replace', index=False)
    conn.close()


def create_history():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        username TEXT,
        user_message TEXT,
        bot_response TEXT,
        additional_metadata TEXT
    );
    '''
    cursor.execute(create_table_query)
    conn.commit()
    conn.close()
    print("Database and table created successfully.")


def insert_chat_history(username, user_message, bot_response, additional_metadata=None):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    insert_query = '''
    INSERT INTO chat_history (username, user_message, bot_response, additional_metadata)
    VALUES (?, ?, ?, ?);
    '''
    try:
        cursor.execute(insert_query, (username, user_message, bot_response, additional_metadata))
        conn.commit()
        print("Chat history record added successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()




def get_recent_chats(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    time_5_minutes_ago = datetime.now() - timedelta(minutes=5)
    select_query = '''
    SELECT * FROM chat_history 
    WHERE username = ? AND timestamp > ?
    ORDER BY timestamp DESC;
    '''
    try:
        cursor.execute(select_query, (username, time_5_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')))
        records = cursor.fetchall()
        if records:
            return records
        else:
            return "No recent chats found for this user."
    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        conn.close()

def create_index_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create a table for the index if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS index_storage (
            id INTEGER PRIMARY KEY,
            data BLOB
        )
    ''')
    # Commit changes and close the connection
    conn.commit()
    conn.close()

def load_index_from_db():
    # Connect to SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Retrieve the serialized index
    try:
        cursor.execute('SELECT data FROM index_storage WHERE id = ?', (1,))
        data = cursor.fetchone()
        index = pickle.loads(data[0])
        flag=True
    except Exception as e:
        # print(e)
        index=None
        flag=False
    conn.close()
    
    return index,flag

def save_index_in_db(index):
    # Serialize the index
    serialized_index = pickle.dumps(index)

    # Connect to SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create a table for the index if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS index_storage (
            id INTEGER PRIMARY KEY,
            data BLOB
        )
    ''')

    # Insert or replace the serialized index
    cursor.execute('''
        INSERT OR REPLACE INTO index_storage (id, data) VALUES (?, ?)
    ''', (1, sqlite3.Binary(serialized_index)))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

# # Example usage
# username = "exampleUser"
# print(get_recent_chats(username))