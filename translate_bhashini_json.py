import json
import os
import requests
import copy
import time
from typing import Dict, Any, List
from tqdm import tqdm

# added exception if tqdm is not installed
# try:
#     from tqdm import tqdm
# except ImportError:
#     print("tqdm not found. Install it with `pip install tqdm` for progress bars.")
#     # Dummy tqdm if not installed
#     def tqdm(iterable, *args, **kwargs):
#         return iterable

# Configuration
INPUT_FILE = "input_documents/ACBP.json"
TARGET_LANGUAGES = {
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "mr": "Marathi",
    "ta": "Tamil",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "or": "Oriya",
    "pa": "Punjabi",
    "bn": "Bengali",
    "as": "Assamese",
}
# Keys to translate
TRANSLATE_KEYS = [
    # "instruction",
    "role_responsibilities", 
    "activities",
    "rationale",
    # "course",
    "designation_name",
    "wing_division_section",
    # "theme",
    # "sub_theme",
    # "competencyThemeName",
    # "competencySubThemeName",
    # "organisation",
    # "status",
    # "state_center_name",
    # "department_name" 
    # Added based on JSON inspection
]

PIPELINE_CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"

# Load environment variables from .env file manually to avoid external dependencies
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

if not USER_ID or not API_KEY:
    print("Error: BHASHINI_USER_ID and BHASHINI_API_KEY must be set in .env file or environment variables.")
    exit(1)

def get_pipeline_config(source_lang: str, target_lang: str) -> Dict:
    """
    Fetches the pipeline configuration for a specific language pair.
    """
    headers = {
        "userID": USER_ID,
        "ulcaApiKey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_lang,
                        "targetLanguage": target_lang
                    }
                }
            }
        ],
        "pipelineRequestConfig": {
            "pipelineId": "64392f96daac500b55c543cd" # MeitY standard pipeline ID
        }
    }

    try:
        response = requests.post(PIPELINE_CONFIG_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pipeline config for {source_lang}->{target_lang}: {e}")
        if response is not None:
             print(f"Response content: {response.text}")
        return None

def translate_text(text: str, config: Dict, compute_url: str) -> str:
    """
    Translates a single string using the Service ID and Compute URL.
    """
    if not text or not text.strip(): # Skip empty or whitespace-only strings
        return text

    # Extract serviceId and authorization header from config response
    try:
        service_id = config["pipelineResponseConfig"][0]["config"][0]["serviceId"]
        
        # Auth header is usually in pipelineInferenceAPIEndPoint
        if "pipelineInferenceAPIEndPoint" in config:
             auth_header_key = config["pipelineInferenceAPIEndPoint"]["inferenceApiKey"]["name"]
             auth_header_value = config["pipelineInferenceAPIEndPoint"]["inferenceApiKey"]["value"]
        else:
             # Fallback to old location if API changes
             auth_header_key = config["pipelineResponseConfig"][0]["config"][0]["inferenceApiKey"]["name"]
             auth_header_value = config["pipelineResponseConfig"][0]["config"][0]["inferenceApiKey"]["value"]
        
        source_lang = config["pipelineResponseConfig"][0]["config"][0]["language"]["sourceLanguage"]
        target_lang = config["pipelineResponseConfig"][0]["config"][0]["language"]["targetLanguage"]
        
    except (KeyError, IndexError) as e:
        print(f"Error parsing pipeline config: {e}")
        return text

    headers = {
        auth_header_key: auth_header_value,
        "Content-Type": "application/json"
    }
    
    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_lang,
                        "targetLanguage": target_lang
                    },
                    "serviceId": service_id
                }
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": text
                }
            ]
        }
    }

    try:
        response = requests.post(compute_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        translated_text = data["pipelineResponse"][0]["output"][0]["target"]
        return translated_text
    except requests.exceptions.RequestException as e:
        print(f"Error translating text: '{text[:20]}...'. Error: {e}")
        return text
    except (KeyError, IndexError):
        print(f"Unexpected response format from compute API. Response: {response.text}")
        return text

def count_translatable_items(data: Any) -> int:
    """
    Counts the number of items that will be translated.
    """
    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            if key in TRANSLATE_KEYS:
                if isinstance(value, str) and value.strip():
                    count += 1
                elif isinstance(value, list):
                     for item in value:
                        if isinstance(item, str) and item.strip():
                            count += 1
            else:
                count += count_translatable_items(value)
    elif isinstance(data, list):
        for item in data:
            count += count_translatable_items(item)
    return count

def traverse_and_translate(data: Any, config: Dict, compute_url: str, pbar=None):
    """
    Recursively traverses the JSON data and translates specific keys.
    Modifies data in-place. Updates progress bar if provided.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key in TRANSLATE_KEYS:
                # Logic: Skip null/None, skip empty strings, only translate non-empty strings
                if value is None:
                    continue

                if isinstance(value, str):
                    if value.strip(): # Check if not empty/whitespace
                        data[key] = translate_text(value, config, compute_url)
                        if pbar: pbar.update(1)
                elif isinstance(value, list):
                     for i in range(len(value)):
                        if isinstance(value[i], str):
                            if value[i].strip():
                                value[i] = translate_text(value[i], config, compute_url)
                                if pbar: pbar.update(1)
            else:
                traverse_and_translate(value, config, compute_url, pbar)
    elif isinstance(data, list):
        for item in data:
            traverse_and_translate(item, config, compute_url, pbar)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} not found.")
        return

    print("Loading input file...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    # Calculate total items to translate for the first pass (assuming structure matches)
    print("Calculating translation workload...")
    total_items = count_translatable_items(original_data)
    print(f"Total items to translate per language: {total_items}")

    for lang_code, lang_name in TARGET_LANGUAGES.items():
        print(f"\n--- Starting translation for {lang_name} ({lang_code}) ---")
        
        # 1. Get Pipeline Config
        print("Fetching pipeline configuration...")
        config = get_pipeline_config("en", lang_code)
        if not config:
            print(f"Skipping {lang_name} due to config failure.")
            continue

        try:
           compute_url = config["pipelineInferenceAPIEndPoint"]["callbackUrl"]
        except KeyError:
           print("Could not find callbackUrl in config response.")
           continue

        # 2. Deep Copy Data
        translated_data = copy.deepcopy(original_data)

        # 3. Translate with Progress Bar
        with tqdm(total=total_items, desc=f"Translating to {lang_name}", unit="item") as pbar:
            traverse_and_translate(translated_data, config, compute_url, pbar)

        # 4. Save
        output_dir = "translated_files"
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"ACBP_{lang_code}.json")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=4, ensure_ascii=False)
        print(f"Saved translated JSON to {output_filename}")
        
        # Delay between languages
        print("Waiting 15 seconds before next language...")
        time.sleep(15)

if __name__ == "__main__":
    main()
