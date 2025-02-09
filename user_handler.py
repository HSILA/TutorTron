import os
import argparse
import uuid
import hashlib
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
load_dotenv()


def generate_uuid(seed: int) -> str:
    """
    Generate a UUID from a seed.

    Args:
        seed (int): The seed to generate the UUID from.

    Returns:
        str: The generated UUID.
    """
    return str(uuid.UUID(hashlib.md5(str(seed).encode()).hexdigest()))


def get_supabase_client() -> Client:
    """
    Create a Supabase client object.

    Returns:
        Client: The Supabase client object.
    """
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


def preprocess_csv(path: str) -> pd.DataFrame:
    """
    Preprocess the CSV file and make it ready for insertion into the database.

    Args:
        path (str): The path to the CSV file.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    df = pd.read_csv(path)
    if df.columns[-1] == 'End-of-Line Indicator':
        df = df.drop(columns=['End-of-Line Indicator'])
    df['OrgDefinedId'] = df['OrgDefinedId'].apply(lambda x: x[1:] if x[0] == '#' else x)
    df['Username'] = df['Username'].apply(lambda x: x[1:] if x[0] == '#' else x)
    df.drop(columns=['Email'], inplace=True)

    df.rename(columns={
        'OrgDefinedId': 'student_number',
        'Username': 'macid',
        'Last Name': 'last_name',
        'First Name': 'first_name'
    }, inplace=True)

    df['student_number'] = df['student_number'].astype(int)
    return df


def upsert_user(user_data: dict) -> None:
    """
    Upsert a single user into the database.

    Args:
        user_data (dict): The dictionary containing the user data.
    """
    client = get_supabase_client()
    try:
        _ = client.table('users').upsert(user_data, returning='minimal').execute()
    except Exception as e:
        print(f"Error {e} inserting user: {user_data['macid']}")


def upsert_users_batch(df: pd.DataFrame) -> None:
    """
    Insert the users DataFrame into the database.

    Args:
        df (pd.DataFrame): The DataFrame containing the users data.
    """
    for i, row in df.iterrows():
        row_data = row.to_dict()
        upsert_user(row_data)
    print("Users inserted successfully.")


def fetch_users() -> dict:
    """
    Fetch the users from the database and return them as a dictionary for authentication.

    Returns:
        dict: The dictionary containing the users data.
    """

    client = get_supabase_client()
    try:
        response = client.table("users").select("*").execute()
    except Exception as e:
        print(f"Error {e} fetching users")
        return {}

    usernames_dict = {}
    for user in response.data:
        usernames_dict[user['macid']] = {
            'email': f"{user['macid']}@mcmaster.ca",
            'failed_login_attempts': 0,
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'password': user['student_number'],
            'logged_in': False,
            'roles': ['viewer']
        }

    out_dict = {
        'credentials': {
            'usernames': usernames_dict
        },
        'cookie': {'expiry_days': 7,
                   'key': generate_uuid(42),
                   'name': 'TA-Chatbot-Auth'}
    }
    return out_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users-path", type=str, help="The path to the users CSV file.")
    parser.add_argument("--student-number", type=int, help="Student number of the user.")
    parser.add_argument("--macid", type=str, help="MAC ID of the user.")
    parser.add_argument("--first-name", type=str, help="First name of the user.")
    parser.add_argument("--last-name", type=str, help="Last name of the user.")
    args = parser.parse_args()

    if args.users_path:
        users = preprocess_csv(args.users_path)
        upsert_users_batch(users)
    elif args.student_number and args.macid and args.first_name and args.last_name:
        user_data = {
            "student_number": args.student_number,
            "macid": args.macid,
            "first_name": args.first_name,
            "last_name": args.last_name
        }
        upsert_user(user_data)
        print("User inserted successfully.")
    else:
        print("Please provide either --users-path or all of --student-number, --macid, --first-name, and --last-name arguments.")
