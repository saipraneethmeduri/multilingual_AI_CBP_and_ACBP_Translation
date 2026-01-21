import os
import json
import copy
import asyncio
import time
from typing import Dict, Any, List
from googletrans import Translator
from tqdm import tqdm
import html

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

# Keys to translate (same as Gemini script)
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

# Initialize Translator globally
translator = Translator()

async def translate_text(text: str, target_lang: str) -> str:
    """
    Translates a single string using googletrans library (async).
    """
    if not text or not text.strip():
        return text

    try:
        # googletrans API call - await if it returns a coroutine
        # Some versions return coroutines, others don't. We'll handle it.
        result_or_coro = translator.translate(text, dest=target_lang)
        
        if asyncio.iscoroutine(result_or_coro):
            result = await result_or_coro
        else:
            result = result_or_coro
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.1) 
        
        return result.text

    except Exception as e:
        # If it fails, print error and return original text
        # print(f"\nError translating text: '{text[:50]}...'. Error: {e}")
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

async def traverse_and_translate(data: Any, target_lang: str, pbar=None):
    """
    Recursively traverses the JSON data and translates specific keys (async).
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key in TRANSLATE_KEYS:
                if value is None:
                    continue

                if isinstance(value, str):
                    if value.strip():
                        data[key] = await translate_text(value, target_lang)
                        if pbar: pbar.update(1)
                elif isinstance(value, list):
                    for i in range(len(value)):
                        if isinstance(value[i], str):
                            if value[i].strip():
                                value[i] = await translate_text(value[i], target_lang)
                                if pbar: pbar.update(1)
            else:
                await traverse_and_translate(value, target_lang, pbar)
    elif isinstance(data, list):
        for item in data:
            await traverse_and_translate(item, target_lang, pbar)

async def translate_language(original_data, lang_code, lang_name, total_items, output_filename):
    """
    Translates the entire data to a target language.
    """
    print(f"\n--- Starting translation for {lang_name} ({lang_code}) ---")
    
    # Deep Copy Data
    translated_data = copy.deepcopy(original_data)

    with tqdm(total=total_items, desc=f"Translating to {lang_name}", unit="item") as pbar:
        await traverse_and_translate(translated_data, lang_code, pbar)

    # Save
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, indent=4, ensure_ascii=False)
    print(f"Saved translated JSON to {output_filename}")

async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} not found.")
        return

    print(f"Loading input file: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    print("Calculating translation workload...")
    total_items = count_translatable_items(original_data)
    print(f"Total items to translate per language: {total_items}")

    output_dir = "google_ttranslated_files"
    os.makedirs(output_dir, exist_ok=True)

    for lang_code, lang_name in TARGET_LANGUAGES.items():
        output_filename = os.path.join(output_dir, f"ACBP_{lang_code}.json")
        
        # Check if already translated (optional, delete manually if you want fresh run)
        # if os.path.exists(output_filename):
        #     print(f"Skipping {lang_name} ({lang_code}) - already exists.")
        #     continue

        await translate_language(original_data, lang_code, lang_name, total_items, output_filename)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTranslation interrupted by user.")
