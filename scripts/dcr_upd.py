import requests
import json
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timezone

# ------------------ Configuration ------------------
TENANT_URL = "https://mpe-01.reltio.com/reltio/api/T5gkVWCMqxyf8ic"
WORKFLOW_TASK_URL = "https://eu-test-workflow.reltio.com/workflow-adapter/workflow/T5gkVWCMqxyf8ic/tasks"
ENVIRONMENT_URL = "https://mpe-01.reltio.com"
TASK_SEARCH_PAYLOAD = {
    "ascending": False,
    "orderBy": "createTime",
    "open": True,
    "completed": True,
    "offset": 0,
    "max": 500,
    "showTaskVariables": True
}

# ------------------ Authentication ------------------
def get_access_token():
    print("Fetching access token...")
    url = "https://auth.reltio.com/oauth/token?grant_type=client_credentials"
    headers = {
        'Authorization': 'Basic Tk9WQVJUSVNfSU1ETkFfQVBJX1VTRVI6M2dhWmhtNm9yYkFxJU0wbXo+dHZJPHBVZjY2VTFyQj8'
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    token = response.json()["access_token"]
    print("Access token retrieved.")
    return token

# ------------------ Data Classes ------------------
@dataclass
class TaskResponse:
    size: int
    total: int
    data: list

    @staticmethod
    def from_json(text):
        obj = json.loads(text)
        return TaskResponse(size=obj.get("size", 0), total=obj.get("total", 0), data=obj.get("data", []))

# ------------------ Workflow Logic ------------------
def process_tasks():
    access_token = get_access_token()
    offset = 0
    total_tasks = 0
    loop = True
    all_tasks = []

    print("Starting task processing...")

    while loop:
        print(f"Fetching tasks with offset: {offset}")
        TASK_SEARCH_PAYLOAD["offset"] = offset
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': "application/json",
            'EnvironmentURL': ENVIRONMENT_URL
        }

        response = requests.post(WORKFLOW_TASK_URL, headers=headers, json=TASK_SEARCH_PAYLOAD)
        tasks = TaskResponse.from_json(response.text)
        print(f"Retrieved {tasks.size} tasks (Total: {tasks.total})")
        total_tasks += tasks.size

        all_tasks.extend(tasks.data)

        if total_tasks >= tasks.total:
            print("All tasks processed.")
            loop = False
        else:
            offset += TASK_SEARCH_PAYLOAD["max"]
            print("Continuing to next batch of tasks...")

    # Convert full task list to DataFrame
    df_raw = pd.json_normalize(all_tasks)

    # Convert createTime from milliseconds to datetime
    df_raw["createTime_dt"] = pd.to_datetime(df_raw["createTime"], unit='ms', utc = True)

    # Calculate current time
    current_time = datetime.now(timezone.utc)

    # Add new columns
    df_raw["6_days_gap"] = (current_time - df_raw["createTime_dt"]).dt.days == 6
    df_raw["gap_days"] = (current_time - df_raw["createTime_dt"]).dt.days
   
    # Filter rows where gap_days > 5
    df_raw = df_raw[df_raw["gap_days"] > 5]
       
    # Format createTime for display
    df_raw["createTime"] = df_raw["createTime_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Extract relevant fields
    df_filtered = pd.DataFrame({
        "assignee": df_raw.get("assignee"),
        "objectURIs": df_raw.get("objectURIs"),
        "createdBy": df_raw.get("createdBy"),
        "taskType": df_raw.get("taskType"),
        "createTime": df_raw.get("createTime"),
        "Country": df_raw.get("taskVariables.Country"),
        "DCRSourceID": df_raw.get("taskVariables.DCRSourceID"),
        "SourceSystem": df_raw.get("taskVariables.SourceSystem"),
        "6_days_gap": df_raw.get("6_days_gap"),
        "gap_days": df_raw.get("gap_days")
    })

    # Save to CSV
    df_filtered.to_csv("filtered_task_data.csv", index=False)
    print("CSV file saved as 'filtered_task_data.csv'.")

# ------------------ Main Execution ------------------
if __name__ == "__main__":
    process_tasks()