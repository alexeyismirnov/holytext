import streamlit as st
from pathlib import Path
from constants import (
    MODELS, COMMAND_HELP_TEXT, API_KEY_REQUIRED_ERROR, API_KEY_MISSING_WARNING,
    API_KEY_SAVED_SUCCESS, API_KEY_CLEARED_SUCCESS, API_KEY_SAVE_ERROR,
    API_KEY_LOADED_SUCCESS
)

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
        st.sidebar.error(f"{API_KEY_SAVE_ERROR}: {e}")
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

def show_settings():
    """Display and handle all settings in the sidebar"""
    st.sidebar.header("⚙️ Settings")
    
    # Show if API key was loaded from file
    if st.session_state.api_key and not st.session_state.key_loaded_from_file:
        saved_key = load_api_key_from_file()
        if saved_key and saved_key == st.session_state.api_key:
            st.sidebar.success(API_KEY_LOADED_SUCCESS)
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
                st.sidebar.success(API_KEY_SAVED_SUCCESS)
            else:
                st.sidebar.warning(API_KEY_SAVE_ERROR)
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
        show_arena_settings()
    else:
        show_basic_settings()
    
    st.sidebar.divider()
    
    # Action buttons
    show_action_buttons()
    
    # Status indicator
    show_status_indicator()

def show_arena_settings():
    """Show settings specific to arena mode"""
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
    
def show_basic_settings():
    """Show settings for basic mode"""
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
    

def show_command_help():
    """Show help information about available commands"""
    st.sidebar.subheader("📖 Available Commands")
    st.sidebar.markdown(COMMAND_HELP_TEXT)
    
    # Only show debug info message in basic mode
    if not st.session_state.arena_mode and st.session_state.debug_mode:
        st.sidebar.info("🐛 Debug mode shows the actual query sent to LLM when commands modify the original input")

def show_action_buttons():
    """Show action buttons in the sidebar"""
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.messages_a = []
            st.session_state.messages_b = []
            # Also clear debug information
            if "debug_queries" in st.session_state:
                st.session_state.debug_queries = []
            st.rerun()
    
    with col2:
        if st.button("🧪 Test API", use_container_width=True):
            if st.session_state.api_key:
                from api_service import test_api_connection
                model_id = MODELS[st.session_state.selected_model]
                test_api_connection(st.session_state.api_key, model_id)
            else:
                st.error("❌ Set API key first")
    
    # Clear API key button
    if st.session_state.api_key:
        if st.sidebar.button("🔑 Clear Saved Key", use_container_width=True):
            if clear_api_key_file():
                st.session_state.api_key = ""
                st.sidebar.success(API_KEY_CLEARED_SUCCESS)
                st.rerun()

def show_status_indicator():
    """Show API key status indicator"""
    if not st.session_state.api_key:
        st.sidebar.error(API_KEY_REQUIRED_ERROR)
        st.sidebar.markdown("[Get API Key →](https://openrouter.ai/keys)")