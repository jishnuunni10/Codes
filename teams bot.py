import json
import requests

def send_teams_message(message):
    webhook_url = "https://default5989ece0f90e40bf9c791a7beccdb8.61.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/ede306c10f4948938502bfde2103132e/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=nie__8-X9ISxIdZU0S1qvJwdhnLDW_5uQTwynzXOOCM"
    payload = { "message": message }
    headers = { "Content-Type": "application/json" }
    
    response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))

send_teams_message("Hi team, how are u ?")