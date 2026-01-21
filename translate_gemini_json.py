import os
import json
import copy
import time
from typing import Dict, Any, List
from google.cloud import translate_v2 as translatek
from tqdm import tqdm
import html



# Try importing tqdm for progress bars
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

# Keys to translate (same as Bhashini script)
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
]

def load_env():
    """Load environment variables from .env file manually."""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        os.environ[key] = value
                    except ValueError:
                        pass

# Load environment variables
load_env()

# Initialize Google Cloud Translation Client
# We try to use GOOGLE_API_KEY from .env if available, otherwise it falls back to 
# GOOGLE_APPLICATION_CREDENTIALS (standard auth).
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    translate_client = translate.Client(api_key=api_key)
else:
    # This will look for GOOGLE_APPLICATION_CREDENTIALS automatically
    print("GOOGLE_API_KEY not found in .env. Attempting to use Default Credentials (Service Account)...")
    try:
        translate_client = translate.Client()
    except Exception as e:
        print(f"Error initializing Google Cloud Translation Client: {e}")
        print("Please set GOOGLE_API_KEY in .env or configure GOOGLE_APPLICATION_CREDENTIALS.")
        exit(1)

def translate_text(text: str, target_lang: str) -> str:
    """
    Translates a single string using Google Cloud Translation API.
    """
    if not text or not text.strip():
        return text

    try:
        # Google Cloud Translation V2 API call
        # format_='text' preserves formatting better than 'html' for plain text, 
        # but if the source is HTML, use format_='html'
        result = translate_client.translate(
            text, 
            target_language=target_lang,
            format_='text' 
        )
        
        # The result is a dictionary: {'input': 'source_text', 'translatedText': 'target_text', ...}
        # HTML entities are unescaped automatically by the library usually, 
        # but sometimes 'translatedText' might contain HTML entities like &#39;
        translated_text = html.unescape(result['translatedText'])
        
        # Small delay to be polite and avoid basic rate limits (though Cloud API is robust)
        time.sleep(0.1) 
        
        return translated_text

    except Exception as e:
        print(f"Error translating text: '{text[:20]}...'. Error: {e}")
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

def traverse_and_translate(data: Any, target_lang: str, pbar=None):
    """
    Recursively traverses the JSON data and translates specific keys.
    Modifies data in-place. Updates progress bar if provided.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key in TRANSLATE_KEYS:
                if value is None:
                    continue

                if isinstance(value, str):
                    if value.strip():
                        data[key] = translate_text(value, target_lang)
                        if pbar: pbar.update(1)
                elif isinstance(value, list):
                     for i in range(len(value)):
                        if isinstance(value[i], str):
                            if value[i].strip():
#     from tqdm import tqdm
# except ImportError:
#     print("tqdm not found. Install it with `pip install tqdm` for progress bars.")
#     # Dummy tqdm if not installed
#     def tqdm(iterable, *args, **kwargs):
#         return iterable
                                value[i] = translate_text(value[i], target_lang)
                                if pbar: pbar.update(1)
            else:
                traverse_and_translate(value, target_lang, pbar)
    elif isinstance(data, list):
        for item in data:
            traverse_and_translate(item, target_lang, pbar)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} not found.")
        return

    print("Loading input file...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    print("Calculating translation workload...")
    total_items = count_translatable_items(original_data)
    print(f"Total items to translate per language: {total_items}")

    for lang_code, lang_name in TARGET_LANGUAGES.items():
        print(f"\n--- Starting translation for {lang_name} ({lang_code}) ---")
        
        # Deep Copy Data to avoid modifying the original for the next language pass (though we reload/reuse logic)
        # Actually copying original_data is better to start fresh from English each time
        translated_data = copy.deepcopy(original_data)

        with tqdm(total=total_items, desc=f"Translating to {lang_name}", unit="item") as pbar:
            traverse_and_translate(translated_data, lang_code, pbar)

        # Save
        output_dir = "google_translated_files"
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"ACBP_{lang_code}.json")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=4, ensure_ascii=False)
        print(f"Saved translated JSON to {output_filename}")

if __name__ == "__main__":
    main()
