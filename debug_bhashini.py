import json
import os
import requests

# Load environment variables
def load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        pass

load_env()

USER_ID = os.environ.get("BHASHINI_USER_ID")
API_KEY = os.environ.get("BHASHINI_API_KEY")
PIPELINE_CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"

print(f"UserID: {USER_ID}")
# Mask API key for security in logs
print(f"API Key: {API_KEY[:4]}...{API_KEY[-4:] if API_KEY and len(API_KEY)>8 else '****'}")

if not USER_ID or not API_KEY:
    print("Missing credentials.")
    exit(1)

headers = {
    "userID": USER_ID,
    "ulcaApiKey": API_KEY,
    "Content-Type": "application/json"
}

# Try the standard pipeline ID
pipeline_id = "64392f96daac500b55c543cd"
payload = {
    "pipelineTasks": [
        {
            "taskType": "translation",
            "config": {
                "language": {
                    "sourceLanguage": "en",
                    "targetLanguage": "hi"
                }
            }
        }
    ],
    "pipelineRequestConfig": {
        "pipelineId": pipeline_id
    }
}

print(f"\nRequesting config for Pipeline ID: {pipeline_id}")
try:
    response = requests.post(PIPELINE_CONFIG_URL, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response Headers:", response.headers)
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print("Raw Response:", response.text)
except Exception as e:
    print(f"Exception: {e}")
