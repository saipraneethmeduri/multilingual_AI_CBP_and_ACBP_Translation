# Multilingual AI CBP and ACBP Translation Suite

A powerful automated solution for translating complex JSON documents into multiple Indian languages using the **MeitY Bhashini API**. This project includes a high-performance translation engine and a sleek, side-by-side translation viewer.

## 🚀 Features

- **Recursive JSON Translation**: Automatically traverses deeply nested JSON structures to translate specific keys.
- **Multi-Language Support**: Translates into 11 major Indic languages: Hindi, Telugu, Kannada, Marathi, Tamil, Gujarati, Malayalam, Oriya, Punjabi, Bengali, and Assamese.
- **Smart Filtering**: Skips null values and empty strings to optimize API usage and maintain data integrity.
- **Progress Tracking**: Real-time progress bars for each language being processed.
- **Interactive Viewer**: A premium web-based viewer for side-by-side comparison of original and translated content.
- **Synchronized Scrolling**: Perfectly aligned viewing experience to compare translations with ease.

## 🛠️ Components

### 1. Translation Engine (`translate_bhashini_json.py`)
The core Python script that handles the heavy lifting:
- Manages Bhashini API authentication and pipeline configuration.
- Implements efficient deep-cleaning and recursive translation logic.
- Maintains a 15-second delay between languages to ensure API stability.

### 2. Side-by-Side Viewer (`Bhashini_Translator.html`)
A standalone, high-performance HTML/JS application:
- Interactive language selector.
- Syntax-highlighted JSON display.
- Synchronous scroll-sync between original (English) and translated panels.

## 📋 Getting Started

### Prerequisites

- Python 3.8+ (recommended: 3.12)
- Bhashini API Credentials (User ID and API Key)

### Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install requests tqdm
   ```

### Configuration

Create a `.env` file in the root directory (or update existing) with your Bhashini credentials:

```env

# Bhashini API Credentials
BHASHINI_USER_ID=your_user_id_here
BHASHINI_API_KEY=your_api_key_here

# Gemini API Credentials
GEMINI_API_KEY=your_gemini_api_key_here
```

### Usage

1. **Translate Documents**:
   Place your source JSON in `input_documents/ACBP.json` and run:
   ```bash
   python translate_bhashini_json.py
   ```
   Translated files will be saved in the `translated_files/` directory.

2. **View Translations**:
   Open `Bhashini_Translator.html` in any modern web browser to compare results side-by-side.

## 📂 Project Structure

- `input_documents/`: Source files for translation.
- `translated_files/`: Output directory for translated JSONs.
- `Bhashini_Translator.html`: The interactive comparison tool.
- `translate_bhashini_json.py`: The main translation script.

---
*Powered by MeitY Bhashini API*# multilingual_AI_CBP_and_ACBP_Translation
# multilingual_AI_CBP_and_ACBP_Translation
