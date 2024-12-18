import sqlite3
import logging
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import datetime

logging.basicConfig(filename="email_processing.log", level=logging.INFO, format="%(asctime)s - %(message)s")

REFRESH_TOKEN = '1//0gnpuS3W9uWvDCgYIARAAGBASNwF-L9Iru7k6qoJn1XgVGAd-sKkDt8TVZmp2nWbo3WwpGQWVpHyzXjO7L87x5g_6oJgG148g8Rg'
ACCESS_TOKEN = 'ya29.a0ARW5m76sbw51MhMXe7HGi2rfMSgc6vibBpXzbJ0l2ki2HmTMIvnmjs37eQRSOzkDnPn0m5bM8ajwZs6XQ3-QqhdlSw1G8IOX13xCo6roCgleGsQTKc52J5S2yFM4tSnLH3zw6kL569Jnf6jYaDU-klDbs2YwcicaXOsZAijEaCgYKASESARESFQHGX2MilcJPSzmLzPLq6GgSvompBQ0175'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_new_access_token(refresh_token):
    url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': '742915756100-tipcf98b8g7im6eo9l3iblsl13f71rrl.apps.googleusercontent.com',
        'client_secret': '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',
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        access_token = response.json()['access_token']
        logging.info("Access token obtained successfully.")
        return access_token
    else:
        logging.error("Failed to refresh access token.")
        return None

def fetch_unread_emails(access_token):
    url = 'https://www.googleapis.com/gmail/v1/users/me/messages'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'labelIds': 'INBOX', 'q': 'is:unread'}  

    response = requests.get(url, headers=headers, params=params)
    logging.info(f"API Response: {response.json()}")  
    if response.status_code == 200:
        messages = response.json().get('messages', [])
        logging.info(f"Fetched Messages: {messages}")  
        return messages
    else:
        logging.error("Failed to fetch emails.")
        return []

def get_email_details(message_id, access_token):
    url = f'https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}'
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        message = response.json()
        headers = message['payload']['headers']
        
        # Extract details
        sender = next((header['value'] for header in headers if header['name'] == 'From'), 'No sender')
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No subject')
        timestamp = message['internalDate']

        timestamp = int(timestamp) / 1000  
        readable_timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        return sender, subject, readable_timestamp
    else:
        logging.error(f"Failed to fetch message {message_id}.")
        return None, None, None

def mark_as_read(message_id, access_token):
    url = f'https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify'
    headers = {'Authorization': f'Bearer {access_token}'}
    data = {
        "removeLabelIds": ["UNREAD"]
    }
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"Marking email {message_id} as read: {response.status_code}")
    if response.status_code == 200:
        logging.info(f"Message {message_id} marked as read.")
    else:
        logging.error(f"Failed to mark message {message_id} as read.")

def save_to_database(emails):
    try:
        conn = sqlite3.connect("emails.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            subject TEXT,
            timestamp TEXT
        )""")
        for email_data in emails:
            cursor.execute("INSERT INTO emails (sender, subject, timestamp) VALUES (?, ?, ?)", email_data)
        conn.commit()
        logging.info("Emails saved to database successfully!")
    except Exception as e:
        logging.error(f"Error saving emails to database: {str(e)}")
    finally:
        conn.close()

def main():
    access_token = ACCESS_TOKEN
    if not access_token:
        access_token = get_new_access_token(REFRESH_TOKEN)
        if not access_token:
            logging.error("Could not obtain access token. Exiting.")
            return

    emails_to_process = []
    messages = fetch_unread_emails(access_token)
    if messages:
        for message in messages:
            message_id = message['id']
            sender, subject, timestamp = get_email_details(message_id, access_token)
            if sender and subject and timestamp:
                emails_to_process.append((sender, subject, timestamp))
                mark_as_read(message_id, access_token)
        if emails_to_process:
            save_to_database(emails_to_process)
            logging.info("Emails processed and saved successfully.")
        else:
            logging.info("No unread emails found.")
    else:
        logging.info("No unread emails found.")

if __name__ == "__main__":
    main()
