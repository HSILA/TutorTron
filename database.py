import pandas as pd
import sqlite3

def get_user_credentials():
    conn = sqlite3.connect('users.db')
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

def post_user_credentials():
    df = pd.read_csv('users.csv')
    conn = sqlite3.connect('users.db')
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
