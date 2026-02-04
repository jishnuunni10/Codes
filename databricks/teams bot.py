import json
import requests

def send_teams_message(message):
    webhook_url = "<YOUR_POWER_AUTOMATE_WEBHOOK_URL>"  # Replace with your webhook URL
    payload = { "message": message }
    headers = { "Content-Type": "application/json" }
    
    response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))

send_teams_message("Hi team, how are u ?")