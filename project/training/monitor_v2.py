import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('project/.env')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def monitor_v2():
    with open("project/config/job_registry.json", "r") as f:
        job_data = json.load(f)
        job_id = job_data["job_id"]

    print(f"Monitoring Job: {job_id}")
    
    last_status = None
    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)
        if job.status != last_status:
            print(f"Status Change: {job.status}")
            last_status = job.status
            
        if job.status == "succeeded":
            model_name = job.fine_tuned_model
            print(f"Training Succeeded! Model: {model_name}")
            
            # Save to registry
            registry_path = "project/config/model_registry.json"
            if os.path.exists(registry_path):
                with open(registry_path, "r") as f:
                    registry = json.load(f)
            else:
                registry = {}
                
            registry["fine_tuned_model_v2"] = model_name
            with open(registry_path, "w") as f:
                json.dump(registry, f, indent=4)
                
            break
        elif job.status in ["failed", "cancelled"]:
            print(f"Job ended with status: {job.status}")
            break
            
        time.sleep(60)

if __name__ == "__main__":
    monitor_v2()
