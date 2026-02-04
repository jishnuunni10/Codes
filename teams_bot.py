import json
import requests
import os

def send_teams_message(message):
    # Use environment variable for webhook URL
    webhook_url = os.environ.get('TEAMS_WEBHOOK_URL', 'YOUR_WEBHOOK_URL_HERE')
    payload = { "message": message }
    headers = { "Content-Type": "application/json" }
    
    response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))

send_teams_message("Hi team, how are u ?")