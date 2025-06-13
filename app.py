import streamlit as st
from typing import Dict, List, Optional

# Import from our refactored modules
from constants import MODELS, CUSTOM_CSS, ARENA_TITLE_HTML, BASIC_TITLE_HTML, API_KEY_MISSING_WARNING, API_KEY_INFO
from utils import process_user_message, show_debug_query, show_command_indicator
from api_service import call_openrouter_api
from settings import show_settings, load_api_key_from_file

# Configure page
st.set_page_config(
    page_title="Orthodox Translation Assistant",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit's default UI elements
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

# Arena mode chat interface
def arena_chat():
    # Title
    st.markdown(ARENA_TITLE_HTML, unsafe_allow_html=True)
    
    # Show warning if no API key
    if not st.session_state.api_key:
        st.warning(API_KEY_MISSING_WARNING)
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
    st.markdown(BASIC_TITLE_HTML, unsafe_allow_html=True)
    
    # Show warning if no API key
    if not st.session_state.api_key:
        st.warning(API_KEY_MISSING_WARNING)
        st.info(API_KEY_INFO)
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