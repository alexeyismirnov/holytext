import streamlit as st
from typing import Dict, List, Optional, Tuple
from constants import ORTHODOX_TRANSLATION_PROMPT, BIBLE_ANNOTATION_PROMPT
from orthodox_dictionary import OrthodoxDictionary

# Initialize the Orthodox Dictionary handler
orthodox_dict = OrthodoxDictionary(dict_path="dict.jsonl", min_score=65)

# Enhanced prompt engineering function for Orthodox Christian translation and Bible annotation
def process_user_message(user_message: str, messages: List[Dict], orthodox_enabled: bool) -> tuple[List[Dict], str, str]:
    """
    Process user message through prompt engineering.
    Detects special commands (translate, annotate) and applies appropriate context.
    Commands are only recognized when they appear at the beginning of the message.
    Returns: (processed_messages, command_type, processed_query)
    """
    processed_messages = messages.copy()
    command_type = "normal"
    processed_query = user_message  # Default to original message
    
    user_message_lower = user_message.lower().strip()
    
    # Check for "annotate" command (only at the beginning of the message)
    if user_message_lower.startswith("annotate"):
        command_type = "annotate"
        
        # Extract the text to be annotated (everything after "annotate")
        text_to_annotate = user_message[8:].strip()  # Remove "annotate " (8 chars)
        
        # Create the enhanced message with Bible annotation instructions
        if text_to_annotate:
            processed_query = f"{BIBLE_ANNOTATION_PROMPT}\n\n{text_to_annotate}"
        else:
            # If no text after "annotate", ask for clarification
            processed_query = f"{BIBLE_ANNOTATION_PROMPT}\n\n(Please provide the text you would like me to analyze for Bible quotes.)"
        
        processed_messages.append({"role": "user", "content": processed_query})
        
    # Check for "translate" command (only at the beginning of the message)
    elif user_message_lower.startswith("translate") and orthodox_enabled:
        command_type = "translate_orthodox"
        
        # Extract the text to be translated (everything after "translate")
        text_to_translate = user_message[9:].strip()  # Remove "translate " (9 chars)
        
        # Find matching Orthodox terms in the text to translate
        if text_to_translate:
            # Use the fuzzy matcher to find Orthodox terms in the text
            matching_terms = orthodox_dict.find_matching_terms(text_to_translate)
            
            # Create dictionary prompt section if matches were found
            dictionary_prompt = orthodox_dict.create_dictionary_prompt(matching_terms)
            
            # Create the enhanced message with Orthodox Christian context and dictionary
            processed_query = f"{ORTHODOX_TRANSLATION_PROMPT}{dictionary_prompt}\n\n" + "Please translate the following text:\n\n" + text_to_translate
  
        else:
            # If no text after "translate", ask for clarification
            processed_query = f"{ORTHODOX_TRANSLATION_PROMPT}\n\n(Please provide the English text you would like me to translate to traditional Chinese.)"
        
        processed_messages.append({"role": "user", "content": processed_query})
        
    elif user_message_lower.startswith("translate"):
        command_type = "translate_standard"
        
        # Extract the text to be translated (everything after "translate")
        text_to_translate = user_message[9:].strip()  # Remove "translate " (9 chars)
        
        if text_to_translate:
            # Even in standard mode, we can use the dictionary for consistent terminology
            matching_terms = orthodox_dict.find_matching_terms(text_to_translate)
            dictionary_prompt = orthodox_dict.create_dictionary_prompt(matching_terms)
            
            # For standard translation, add dictionary but not the Orthodox context
            if dictionary_prompt:
                processed_query = f"Please translate the following text from English to Traditional Chinese.{dictionary_prompt}\n\n{text_to_translate}"
                processed_messages.append({"role": "user", "content": processed_query})
            else:
                # If no specialized terms found, just add the user message as-is
                processed_messages.append({"role": "user", "content": user_message})
        else:
            # If no text after "translate", just add the user message as-is
            processed_messages.append({"role": "user", "content": user_message})
        
    else:
        # For regular messages, just add the user message as-is
        processed_messages.append({"role": "user", "content": user_message})
    
    return processed_messages, command_type, processed_query

# Function to show debug query
def show_debug_query(original_query: str, processed_query: str, debug_enabled: bool):
    """
    Show the processed query in debug mode if it differs from original.
    Only shows the current debug query in the chat window.
    Stores all debug information in session state for sidebar display.
    """
    if debug_enabled and original_query != processed_query:
        # Store the debug information in session state for sidebar display
        if "debug_queries" not in st.session_state:
            st.session_state.debug_queries = []
        
        # Add the current debug query to the list
        st.session_state.debug_queries.append({
            "original": original_query,
            "processed": processed_query
        })
        
        # Only display the current debug query in the chat window
        with st.expander("🐛 Debug: Processed Query Sent to LLM", expanded=False):
            st.markdown(f"""
            <div class="debug-query">
            {processed_query}
            </div>
            """, unsafe_allow_html=True)

# Function to show command indicators
def show_command_indicator(command_type: str, orthodox_enabled: bool = False):
    """Show visual indicators for different command types"""
    if command_type == "annotate":
        st.info("📖 **Bible Annotation Mode**: Identifying and referencing Bible quotes in the text")
    elif command_type == "translate_orthodox":
        st.info("🔄 **Orthodox Translation Mode**: Using specialized Orthodox Christian translation context")
    elif command_type == "translate_standard":
        st.info("ℹ️ **Standard Translation**: Orthodox Christian context is disabled. Enable it in settings for specialized theological translations.")