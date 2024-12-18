import sqlite3
from datetime import datetime
import pytz

conn = sqlite3.connect('emails.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM emails")

emails = cursor.fetchall()
for email in emails:
    sender = email[1]
    subject = email[2]
    timestamp_str = email[3]  

    try:
        raw_timestamp = float(timestamp_str)  
        utc_time = datetime.utcfromtimestamp(raw_timestamp)  

    except ValueError:
        utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')  
    
    local_timezone = pytz.timezone('Asia/Kolkata')
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)  
    readable_timestamp = local_time.strftime('%Y-%m-%d %H:%M:%S')

    print(f"Sender: {sender}")
    print(f"Subject: {subject}")
    print(f"Timestamp: {readable_timestamp} (IST)")
    print("-" * 40)

conn.close()
