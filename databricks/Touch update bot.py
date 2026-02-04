import gradio as gr
import requests
import time
import re
import csv
import os

# Databricks config - Use environment variables for security
host = os.getenv("DATABRICKS_HOST", "https://your-databricks-instance.cloud.databricks.com")
token = os.getenv("DATABRICKS_TOKEN", "<YOUR_DATABRICKS_TOKEN>")  # Set via environment variable
warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "<YOUR_WAREHOUSE_ID>")
job_id = os.getenv("DATABRICKS_JOB_ID", "<YOUR_JOB_ID>")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def execute_sql(sql_command):
    endpoint = f"{host}/api/2.0/sql/statements"
    payload = {"statement": sql_command, "warehouse_id": warehouse_id}
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def run_job(job_id):
    run_endpoint = f"{host}/api/2.1/jobs/run-now"
    payload = {"job_id": job_id}
    response = requests.post(run_endpoint, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("run_id")

def poll_job_status(run_id, interval=10, timeout=300):
    status_endpoint = f"{host}/api/2.1/jobs/runs/get"
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{status_endpoint}?run_id={run_id}", headers=headers)
        response.raise_for_status()
        status_data = response.json()
        life_cycle_state = status_data.get("state", {}).get("life_cycle_state")
        result_state = status_data.get("state", {}).get("result_state")
        if life_cycle_state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
            return result_state
        time.sleep(interval)
    return "TIMEOUT"

def fetch_table_and_generate_csv():
    sql = "SELECT * FROM workspace.mdm_publish.customers"
    response = execute_sql(sql)
    statement_id = response.get("statement_id")

    # Poll for result
    result_endpoint = f"{host}/api/2.0/sql/statements/{statement_id}"
    while True:
        result_response = requests.get(result_endpoint, headers=headers)
        result_response.raise_for_status()
        result_data = result_response.json()
        if result_data.get("status", {}).get("state") == "SUCCEEDED":
            break
        time.sleep(2)

    # Extract result
    columns = [col["name"] for col in result_data["manifest"]["schema"]["columns"]]
    rows = result_data["result"]["data_array"]

    filename = "customers_table_export.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    return filename

def chatbot_ui_live(ids_input):
    customer_ids = re.split(r'[\s,;]+', ids_input.strip())
    customer_ids = [id for id in customer_ids if id]

    if not customer_ids:
        yield "No valid customer IDs provided.", None
        return

    yield "Step 1: Truncating table...", None
    execute_sql("TRUNCATE TABLE workspace.mdm_publish.customers")

    yield f"Step 2: Inserting {len(customer_ids)} customer IDs...", None
    values_clause = ", ".join([f"('{id}')" for id in customer_ids])
    insert_sql = f"INSERT INTO workspace.mdm_publish.customers (customer_id) VALUES {values_clause}"
    execute_sql(insert_sql)

    yield "Step 3: Triggering job...", None
    run_id = run_job(job_id)

    yield f"Step 4: Job in progress...", None
    result = poll_job_status(run_id)

    yield f"Step 5: Job completed with status: {result}", None

    # Fetch table and generate CSV
    csv_file = fetch_table_and_generate_csv()
    yield "Step 6: Download full customer table below.", csv_file

# Gradio UI
with gr.Blocks(css="""
.gradio-container {
    background: linear-gradient(to right, #1e3c72, #2a5298);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
input, textarea {
    background-color: #ffffff10;
    color: white;
}
button {
    background-color: #00bcd4;
    color: white;
    border: none;
}
""") as demo:
    gr.Markdown("## Touch Update Bot")
    gr.Markdown("**Touch, refresh, done - Reltio profiles updated in seconds.**")

    with gr.Row():
        ids_input = gr.Textbox(label="Customer IDs", placeholder="Paste IDs here", lines=10)
        run_button = gr.Button("Run Update")

    status_output = gr.Textbox(label="Live Status", lines=10)
    file_output = gr.File(label="Download Summary CSV")

    run_button.click(fn=chatbot_ui_live, inputs=ids_input, outputs=[status_output, file_output])

demo.launch()