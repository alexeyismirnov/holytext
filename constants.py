# Available models
MODELS = {
    "Qwen3 8B (Free)": "qwen/qwen3-8b:free",
    "Qwen3 32B (Free)": "qwen/qwen3-32b:free", 
    "Llama 3.3 70B (Free)": "meta-llama/llama-3.3-70b-instruct:free"
}

# Orthodox Christian Translation Context
ORTHODOX_TRANSLATION_PROMPT = """You are an Orthodox Christian translator from English to Chinese that uses traditional Chinese characters. You have deep knowledge of Orthodox Christian theology, liturgy, and terminology. When translating Orthodox Christian texts, please:

1. Use traditional Chinese characters (繁體中文)
2. Maintain the theological accuracy and reverence of Orthodox Christian concepts
3. Use appropriate Chinese Orthodox Christian terminology when available
4. Preserve the liturgical and spiritual tone of the original text

"""

# Bible Annotation Instructions
BIBLE_ANNOTATION_PROMPT = """You are an Orthodox Christian expert in theology and Bible studies. 
Identify and annotate any possible quotes from the Bible in the text below. 
Modify the original text so that after each identified quote, there will be a reference (in parenthesis) to the corresponding location of Bible from which the quote was taken in the standard form. e.g. John 1:2-5 refers to Gospel of John, chapter 1, verses 2-5. 
After processing text return the text with Bible references (if found any). IMPORTANT: If no quotes were found in the entire text, just return the original text.
Text to analyze:"""

# Custom CSS styles
CUSTOM_CSS = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    div[data-testid="stDecoration"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    div[data-testid="stStatusWidget"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    #MainMenu {visibility: hidden;}
    .stActionButton {visibility: hidden;}
    
    /* Custom styling for arena mode */
    .arena-header {
        text-align: center;
        padding: 10px;
        margin: 10px 0;
        border-radius: 8px;
        font-weight: bold;
    }
    .model-a-header {
        background-color: #e3f2fd;
        color: #1976d2;
        border: 2px solid #1976d2;
    }
    .model-b-header {
        background-color: #f3e5f5;
        color: #7b1fa2;
        border: 2px solid #7b1fa2;
    }
    
    /* Debug mode styling */
    .debug-query {
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
        padding: 12px;
        margin: 10px 0;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9em;
        color: #495057;
    }
    </style>
"""

# UI Text Constants
ARENA_TITLE_HTML = """
    <div style="text-align: center; padding: 20px 0; margin-bottom: 20px;">
        <h1 style="color: #1f77b4; font-size: 2.5rem; margin: 0;">🏟️ Model Arena</h1>
        <p style="color: #666; font-size: 1.1rem; margin: 10px 0 0 0;">Compare responses from two different models side by side</p>
    </div>
"""

BASIC_TITLE_HTML = """
    <div style="text-align: center; padding: 20px 0; margin-bottom: 30px;">
        <h1 style="color: #1f77b4; font-size: 3rem; margin: 0;">✝️ Orthodox Translation Assistant</h1>
        <p style="color: #666; font-size: 1.2rem; margin: 10px 0 0 0;">English ↔ Traditional Chinese • Orthodox Christian Context • Bible Annotation</p>
    </div>
"""

# Command help text
COMMAND_HELP_TEXT = """
**translate** [text]  
*Translate English to Chinese*

**annotate** [text]  
*Find & reference Bible quotes*
"""

# Error and info messages
API_KEY_REQUIRED_ERROR = "❌ API key required"
API_KEY_MISSING_WARNING = "⚠️ Please set your OpenRouter API key in the sidebar settings to start chatting."
API_KEY_SAVED_SUCCESS = "💾 API key saved locally!"
API_KEY_CLEARED_SUCCESS = "🗑️ API key cleared!"
API_KEY_SAVE_ERROR = "⚠️ Could not save API key to file"
API_KEY_LOADED_SUCCESS = "💾 API key loaded from saved file"
API_KEY_INFO = "💡 Your API key will be saved locally and automatically loaded when you restart the app."