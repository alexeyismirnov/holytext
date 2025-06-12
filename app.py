import streamlit as st
import requests
import json
from typing import Dict, List, Optional
import os
import pickle
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Orthodox Translation Assistant",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit's default UI elements
hide_streamlit_style = """
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
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
5. If encountering specific Orthodox terms (like "theosis", "hesychasm", "economia"), provide both translation and brief explanation if needed
6. Be mindful of the sacred nature of liturgical and theological texts

Please translate the following text:"""

# Bible Annotation Instructions
BIBLE_ANNOTATION_PROMPT = """You are an Orthodox Christian expert in theology and Bible studies. 
Identify and annotate any possible quotes from the Bible in the text below. 
Modify the original text so that after each identified quote, there will be a reference (in parenthesis) to the corresponding location of Bible from which the quote was taken in the standard form. e.g. John 1:2-5 refers to Gospel of John, chapter 1, verses 2-5. 
After processing text return the text with Bible references (if found any). IMPORTANT: If no quotes were found in the entire text, just return the original text.
Text to analyze:"""

# Simple file-based persistence (works locally)
def get_cache_file():
    """Get the cache file path for storing API key"""
    cache_dir = Path.home() / ".streamlit_orthodox_translator"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "api_key.txt"

def save_api_key_to_file(api_key: str):
    """Save API key to local file"""
    try:
        if api_key.strip():
            with open(get_cache_file(), 'w') as f:
                f.write(api_key.strip())
            return True
    except Exception as e:
        st.sidebar.error(f"Could not save API key: {e}")
    return False

def load_api_key_from_file():
    """Load API key from local file"""
    try:
        cache_file = get_cache_file()
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                key = f.read().strip()
                if key:
                    return key
    except Exception as e:
        st.sidebar.error(f"Could not load API key: {e}")
    return ""

def clear_api_key_file():
    """Clear the saved API key file"""
    try:
        cache_file = get_cache_file()
        if cache_file.exists():
            cache_file.unlink()
        return True
    except Exception as e:
        st.sidebar.error(f"Could not clear API key: {e}")
    return False

# Initialize session state
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "messages_a" not in st.session_state:
        st.session_state.messages_a = []
    if "messages_b" not in st.session_state:
        st.session_state.messages_b = []
    if "api_key" not in st.session_state:
        # Try to load from file on first run
        saved_key = load_api_key_from_file()
        st.session_state.api_key = saved_key
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = list(MODELS.keys())[0]
    if "selected_model_a" not in st.session_state:
        st.session_state.selected_model_a = list(MODELS.keys())[0]
    if "selected_model_b" not in st.session_state:
        st.session_state.selected_model_b = list(MODELS.keys())[1] if len(MODELS) > 1 else list(MODELS.keys())[0]
    if "orthodox_translation_enabled" not in st.session_state:
        st.session_state.orthodox_translation_enabled = True  # Default is ON
    if "orthodox_translation_enabled_a" not in st.session_state:
        st.session_state.orthodox_translation_enabled_a = True  # Default is ON
    if "orthodox_translation_enabled_b" not in st.session_state:
        st.session_state.orthodox_translation_enabled_b = False  # Default is OFF for comparison
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False  # Default is OFF
    if "debug_mode_a" not in st.session_state:
        st.session_state.debug_mode_a = False  # Default is OFF
    if "debug_mode_b" not in st.session_state:
        st.session_state.debug_mode_b = False  # Default is OFF
    if "arena_mode" not in st.session_state:
        st.session_state.arena_mode = False  # Default is basic mode
    if "key_loaded_from_file" not in st.session_state:
        st.session_state.key_loaded_from_file = False

# API call function
def call_openrouter_api(messages: List[Dict], model: str, api_key: str) -> Optional[str]:
    """Call OpenRouter API with the given messages and model"""
    if not api_key:
        st.error("❌ Please set your OpenRouter API key in the settings.")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Orthodox Translation Assistant"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        with st.spinner("🤔 Thinking..."):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    st.error("❌ No choices in API response")
                    return None
            else:
                st.error(f"❌ API Error: {response.status_code}")
                try:
                    error_data = response.json()
                    st.error(f"Error details: {error_data}")
                except:
                    st.error(f"Response text: {response.text}")
                return None
                
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Connection error. Please check your internet connection.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"📡 Request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"📄 JSON decode error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"💥 Unexpected error: {str(e)}")
        return None

# Test API connection
def test_api_connection():
    """Test the API connection with a simple message"""
    if not st.session_state.api_key:
        st.error("❌ Please set your API key first")
        return
    
    test_messages = [{"role": "user", "content": "Hello, please respond with just 'API test successful'"}]
    model_id = MODELS[st.session_state.selected_model]
    
    st.write("🧪 Testing API connection...")
    response = call_openrouter_api(test_messages, model_id, st.session_state.api_key)
    
    if response:
        st.success(f"✅ API Test Successful! Response: {response}")
    else:
        st.error("❌ API Test Failed")

# Enhanced prompt engineering function for Orthodox Christian translation and Bible annotation
def process_user_message(user_message: str, messages: List[Dict], orthodox_enabled: bool) -> tuple[List[Dict], str, str]:
    """
    Process user message through prompt engineering.
    Detects special commands (translate, annotate) and applies appropriate context.
    Returns: (processed_messages, command_type, processed_query)
    """
    processed_messages = messages.copy()
    command_type = "normal"
    processed_query = user_message  # Default to original message
    
    user_message_lower = user_message.lower()
    
    # Check for "annotate" command first (higher priority)
    if "annotate" in user_message_lower:
        command_type = "annotate"
        
        # Extract the text to be annotated (everything after "annotate")
        annotate_index = user_message_lower.find("annotate")
        
        if annotate_index == 0:
            # "annotate" is at the beginning
            text_to_annotate = user_message[8:].strip()  # Remove "annotate " (8 chars)
        else:
            # "annotate" appears elsewhere, use the full message
            text_to_annotate = user_message
        
        # Create the enhanced message with Bible annotation instructions
        if text_to_annotate:
            processed_query = f"{BIBLE_ANNOTATION_PROMPT}\n\n{text_to_annotate}"
        else:
            # If no text after "annotate", ask for clarification
            processed_query = f"{BIBLE_ANNOTATION_PROMPT}\n\n(Please provide the text you would like me to analyze for Bible quotes.)"
        
        processed_messages.append({"role": "user", "content": processed_query})
        
    # Check for "translate" command
    elif "translate" in user_message_lower and orthodox_enabled:
        command_type = "translate_orthodox"
        
        # Extract the text to be translated (everything after "translate")
        translate_index = user_message_lower.find("translate")
        
        if translate_index == 0:
            # "translate" is at the beginning
            text_to_translate = user_message[9:].strip()  # Remove "translate " (9 chars)
        else:
            # "translate" appears elsewhere, use the full message but add context
            text_to_translate = user_message
        
        # Create the enhanced message with Orthodox Christian context
        if text_to_translate:
            processed_query = f"{ORTHODOX_TRANSLATION_PROMPT}\n\n{text_to_translate}"
        else:
            # If no text after "translate", ask for clarification
            processed_query = f"{ORTHODOX_TRANSLATION_PROMPT}\n\n(Please provide the English text you would like me to translate to traditional Chinese.)"
        
        processed_messages.append({"role": "user", "content": processed_query})
        
    elif "translate" in user_message_lower:
        command_type = "translate_standard"
        # For standard translation (Orthodox mode disabled), just add the user message as-is
        processed_messages.append({"role": "user", "content": user_message})
        
    else:
        # For regular messages, just add the user message as-is
        processed_messages.append({"role": "user", "content": user_message})
    
    return processed_messages, command_type, processed_query

# Function to show debug query
def show_debug_query(original_query: str, processed_query: str, debug_enabled: bool):
    """Show the processed query in debug mode if it differs from original"""
    if debug_enabled and original_query != processed_query:
        with st.expander("🐛 Debug: Processed Query Sent to LLM", expanded=False):
            st.markdown(f"""
            <div class="debug-query">
            {processed_query}
            </div>
            """, unsafe_allow_html=True)

# Settings interface with debug mode toggle
def show_settings():
    st.sidebar.header("⚙️ Settings")
    
    # Show if API key was loaded from file
    if st.session_state.api_key and not st.session_state.key_loaded_from_file:
        saved_key = load_api_key_from_file()
        if saved_key and saved_key == st.session_state.api_key:
            st.sidebar.success("💾 API key loaded from saved file")
            st.session_state.key_loaded_from_file = True
    
    # API Key input
    api_key = st.sidebar.text_input(
        "OpenRouter API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Enter your API key (e.g., sk-or-v1-...)",
        help="Your API key will be saved locally and persist between sessions"
    )
    
    # Handle API key changes
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        if api_key:
            # Save to file
            if save_api_key_to_file(api_key):
                st.sidebar.success("💾 API key saved locally!")
            else:
                st.sidebar.warning("⚠️ Could not save API key to file")
        st.rerun()
    
    # Arena Mode Toggle
    arena_mode = st.sidebar.toggle(
        "🏟️ Arena Mode (Advanced)",
        value=st.session_state.arena_mode,
        help="Enable split-screen comparison between two models"
    )
    
    if arena_mode != st.session_state.arena_mode:
        st.session_state.arena_mode = arena_mode
        st.rerun()
    
    st.sidebar.divider()
    
    # Model configuration based on mode
    if st.session_state.arena_mode:
        st.sidebar.subheader("🔵 Model A Settings")
        
        # Model A selection
        selected_model_a = st.sidebar.selectbox(
            "Model A",
            options=list(MODELS.keys()),
            index=list(MODELS.keys()).index(st.session_state.selected_model_a),
            key="model_a_select"
        )
        
        if selected_model_a != st.session_state.selected_model_a:
            st.session_state.selected_model_a = selected_model_a
            st.rerun()
        
        # Orthodox Translation Toggle for Model A
        orthodox_enabled_a = st.sidebar.toggle(
            "✝️ Orthodox Mode A",
            value=st.session_state.orthodox_translation_enabled_a,
            help="Orthodox Christian translation context for Model A",
            key="orthodox_a"
        )
        
        if orthodox_enabled_a != st.session_state.orthodox_translation_enabled_a:
            st.session_state.orthodox_translation_enabled_a = orthodox_enabled_a
            st.rerun()
        
        # Debug Mode Toggle for Model A
        debug_enabled_a = st.sidebar.toggle(
            "🐛 Debug Mode A",
            value=st.session_state.debug_mode_a,
            help="Show processed queries sent to Model A",
            key="debug_a"
        )
        
        if debug_enabled_a != st.session_state.debug_mode_a:
            st.session_state.debug_mode_a = debug_enabled_a
            st.rerun()
        
        st.sidebar.subheader("🟣 Model B Settings")
        
        # Model B selection
        selected_model_b = st.sidebar.selectbox(
            "Model B",
            options=list(MODELS.keys()),
            index=list(MODELS.keys()).index(st.session_state.selected_model_b),
            key="model_b_select"
        )
        
        if selected_model_b != st.session_state.selected_model_b:
            st.session_state.selected_model_b = selected_model_b
            st.rerun()
        
        # Orthodox Translation Toggle for Model B
        orthodox_enabled_b = st.sidebar.toggle(
            "✝️ Orthodox Mode B",
            value=st.session_state.orthodox_translation_enabled_b,
            help="Orthodox Christian translation context for Model B",
            key="orthodox_b"
        )
        
        if orthodox_enabled_b != st.session_state.orthodox_translation_enabled_b:
            st.session_state.orthodox_translation_enabled_b = orthodox_enabled_b
            st.rerun()
        
        # Debug Mode Toggle for Model B
        debug_enabled_b = st.sidebar.toggle(
            "🐛 Debug Mode B",
            value=st.session_state.debug_mode_b,
            help="Show processed queries sent to Model B",
            key="debug_b"
        )
        
        if debug_enabled_b != st.session_state.debug_mode_b:
            st.session_state.debug_mode_b = debug_enabled_b
            st.rerun()
        
    else:
        # Basic mode settings
        selected_model = st.sidebar.selectbox(
            "AI Model",
            options=list(MODELS.keys()),
            index=list(MODELS.keys()).index(st.session_state.selected_model)
        )
        
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            st.rerun()
        
        # Orthodox Translation Toggle
        orthodox_enabled = st.sidebar.toggle(
            "✝️ Orthodox Translation Mode",
            value=st.session_state.orthodox_translation_enabled,
            help="When enabled, 'translate' commands will use Orthodox Christian theological context"
        )
        
        if orthodox_enabled != st.session_state.orthodox_translation_enabled:
            st.session_state.orthodox_translation_enabled = orthodox_enabled
            st.rerun()
        
        # Debug Mode Toggle
        debug_enabled = st.sidebar.toggle(
            "🐛 Debug Mode",
            value=st.session_state.debug_mode,
            help="Show processed queries sent to the LLM (useful when Orthodox/Annotate modes modify the original query)"
        )
        
        if debug_enabled != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_enabled
            st.rerun()
        
        # Show current mode status
        status_items = []
        if st.session_state.orthodox_translation_enabled:
            status_items.append("✝️ Orthodox: ON")
        else:
            status_items.append("📝 Standard: ON")
        
        if st.session_state.debug_mode:
            status_items.append("🐛 Debug: ON")
        
        st.sidebar.success(" | ".join(status_items))
    
    st.sidebar.divider()
    
    # Command help section
    st.sidebar.subheader("📖 Available Commands")
    st.sidebar.markdown("""
    **translate** [text]  
    *Translate English to Chinese*
    
    **annotate** [text]  
    *Find & reference Bible quotes*
    """)
    
    if st.session_state.debug_mode or st.session_state.debug_mode_a or st.session_state.debug_mode_b:
        st.sidebar.info("🐛 Debug mode shows the actual query sent to LLM when commands modify the original input")
    
    st.sidebar.divider()
    
    # Action buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.messages_a = []
            st.session_state.messages_b = []
            st.rerun()
    
    with col2:
        if st.button("🧪 Test API", use_container_width=True):
            if st.session_state.api_key:
                test_api_connection()
            else:
                st.error("❌ Set API key first")
    
    # Clear API key button
    if st.session_state.api_key:
        if st.sidebar.button("🔑 Clear Saved Key", use_container_width=True):
            if clear_api_key_file():
                st.session_state.api_key = ""
                st.sidebar.success("🗑️ API key cleared!")
                st.rerun()
    
    # Status indicator
    if st.session_state.api_key:
        st.sidebar.success("✅ Ready to chat")
        cache_file = get_cache_file()
        if cache_file.exists():
            st.sidebar.caption("💾 API key saved locally")
        else:
            st.sidebar.caption("⚠️ API key not saved")
    else:
        st.sidebar.error("❌ API key required")
        st.sidebar.markdown("[Get API Key →](https://openrouter.ai/keys)")

# Function to show command indicators
def show_command_indicator(command_type: str, orthodox_enabled: bool = False):
    """Show visual indicators for different command types"""
    if command_type == "annotate":
        st.info("📖 **Bible Annotation Mode**: Identifying and referencing Bible quotes in the text")
    elif command_type == "translate_orthodox":
        st.info("🔄 **Orthodox Translation Mode**: Using specialized Orthodox Christian translation context")
    elif command_type == "translate_standard":
        st.info("ℹ️ **Standard Translation**: Orthodox Christian context is disabled. Enable it in settings for specialized theological translations.")

# Arena mode chat interface
def arena_chat():
    # Title
    st.markdown("""
        <div style="text-align: center; padding: 20px 0; margin-bottom: 20px;">
            <h1 style="color: #1f77b4; font-size: 2.5rem; margin: 0;">🏟️ Model Arena</h1>
            <p style="color: #666; font-size: 1.1rem; margin: 10px 0 0 0;">Compare responses from two different models side by side</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Show warning if no API key
    if not st.session_state.api_key:
        st.warning("⚠️ Please set your OpenRouter API key in the sidebar settings to start chatting.")
        return
    
    # Create two columns for side-by-side comparison
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Model A header
        orthodox_status_a = "✝️ Orthodox ON" if st.session_state.orthodox_translation_enabled_a else "📝 Standard"
        debug_status_a = " | 🐛 Debug ON" if st.session_state.debug_mode_a else ""
        st.markdown(f"""
            <div class="arena-header model-a-header">
                🔵 Model A: {st.session_state.selected_model_a}<br>
                <small>{orthodox_status_a}{debug_status_a}</small>
            </div>
        """, unsafe_allow_html=True)
        
        # Display Model A messages
        for message in st.session_state.messages_a:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    with col_b:
        # Model B header
        orthodox_status_b = "✝️ Orthodox ON" if st.session_state.orthodox_translation_enabled_b else "📝 Standard"
        debug_status_b = " | 🐛 Debug ON" if st.session_state.debug_mode_b else ""
        st.markdown(f"""
            <div class="arena-header model-b-header">
                🟣 Model B: {st.session_state.selected_model_b}<br>
                <small>{orthodox_status_b}{debug_status_b}</small>
            </div>
        """, unsafe_allow_html=True)
        
        # Display Model B messages
        for message in st.session_state.messages_b:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Single chat input for both models
    if prompt := st.chat_input("Try: 'translate [text]' or 'annotate [text]' to compare responses..."):
        # Add user message to both chat histories
        st.session_state.messages_a.append({"role": "user", "content": prompt})
        st.session_state.messages_b.append({"role": "user", "content": prompt})
        
        # Process messages for both models
        processed_messages_a, command_type_a, processed_query_a = process_user_message(prompt, st.session_state.messages_a[:-1], st.session_state.orthodox_translation_enabled_a)
        processed_messages_b, command_type_b, processed_query_b = process_user_message(prompt, st.session_state.messages_b[:-1], st.session_state.orthodox_translation_enabled_b)
        
        # Show command indicators
        if command_type_a == "annotate" or command_type_b == "annotate":
            show_command_indicator("annotate")
        elif command_type_a != command_type_b and ("translate" in command_type_a or "translate" in command_type_b):
            st.info("🔄 **Comparing Translation Modes**: Model A and B using different Orthodox settings")
        elif command_type_a == "translate_orthodox" or command_type_b == "translate_orthodox":
            show_command_indicator("translate_orthodox")
        elif command_type_a == "translate_standard" or command_type_b == "translate_standard":
            show_command_indicator("translate_standard")
        
        # Show debug queries if enabled
        col_debug_a, col_debug_b = st.columns(2)
        with col_debug_a:
            show_debug_query(prompt, processed_query_a, st.session_state.debug_mode_a)
        with col_debug_b:
            show_debug_query(prompt, processed_query_b, st.session_state.debug_mode_b)
        
        # Get model IDs
        model_id_a = MODELS[st.session_state.selected_model_a]
        model_id_b = MODELS[st.session_state.selected_model_b]
        
        # Create columns for responses
        col_a, col_b = st.columns(2)
        
        # Get response from Model A
        with col_a:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                response_a = call_openrouter_api(processed_messages_a, model_id_a, st.session_state.api_key)
                
                if response_a:
                    st.session_state.messages_a.append({"role": "assistant", "content": response_a})
                    st.markdown(response_a)
                else:
                    st.error("❌ Failed to get response from Model A")
                    st.session_state.messages_a.pop()  # Remove user message if no response
        
        # Get response from Model B
        with col_b:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                response_b = call_openrouter_api(processed_messages_b, model_id_b, st.session_state.api_key)
                
                if response_b:
                    st.session_state.messages_b.append({"role": "assistant", "content": response_b})
                    st.markdown(response_b)
                else:
                    st.error("❌ Failed to get response from Model B")
                    st.session_state.messages_b.pop()  # Remove user message if no response
        
        st.rerun()
        
# Basic mode chat interface
def basic_chat():
    # Title
    st.markdown("""
        <div style="text-align: center; padding: 20px 0; margin-bottom: 30px;">
            <h1 style="color: #1f77b4; font-size: 3rem; margin: 0;">✝️ Orthodox Translation Assistant</h1>
            <p style="color: #666; font-size: 1.2rem; margin: 10px 0 0 0;">English ↔ Traditional Chinese • Orthodox Christian Context • Bible Annotation</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Show warning if no API key
    if not st.session_state.api_key:
        st.warning("⚠️ Please set your OpenRouter API key in the sidebar settings to start chatting.")
        st.info("💡 Your API key will be saved locally and automatically loaded when you restart the app.")
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input with dynamic placeholder
    placeholder_text = "Try: 'translate [text]' for translation or 'annotate [text]' for Bible quotes..."
    
    if prompt := st.chat_input(placeholder_text):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process message through prompt engineering
        processed_messages, command_type, processed_query = process_user_message(prompt, st.session_state.messages[:-1], st.session_state.orthodox_translation_enabled)
        
        # Show command indicator
        show_command_indicator(command_type, st.session_state.orthodox_translation_enabled)
        
        # Show debug query if enabled and different from original
        show_debug_query(prompt, processed_query, st.session_state.debug_mode)
        
        # Get AI response
        model_id = MODELS[st.session_state.selected_model]
        
        with st.chat_message("assistant"):
            response = call_openrouter_api(processed_messages, model_id, st.session_state.api_key)
            
            if response:
                # Add assistant response to chat
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.markdown(response)
            else:
                st.error("❌ Failed to get response from AI. Please try again.")
                # Remove the user message if we couldn't get a response
                st.session_state.messages.pop()
        
        st.rerun()

# Main app
def main():
    initialize_session_state()
    show_settings()
    
    # Route to appropriate chat interface based on mode
    if st.session_state.arena_mode:
        arena_chat()
    else:
        basic_chat()

if __name__ == "__main__":
    main()
