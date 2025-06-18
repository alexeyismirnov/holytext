import streamlit as st
from typing import Dict, List, Optional, Tuple
from constants import ORTHODOX_TRANSLATION_PROMPT, BIBLE_ANNOTATION_PROMPT
from orthodox_dictionary import OrthodoxDictionary
from bible_service import process_footnotes, extract_bible_references, parse_bible_reference, fetch_bible_text

# Initialize the Orthodox Dictionary handler
orthodox_dict = OrthodoxDictionary(dict_path="dict.jsonl", min_score=65)

import re
import streamlit as st
from typing import Dict, List, Optional, Tuple
from constants import ORTHODOX_TRANSLATION_PROMPT, BIBLE_ANNOTATION_PROMPT
from orthodox_dictionary import OrthodoxDictionary
from bible_service import process_footnotes, extract_bible_references, parse_bible_reference, fetch_bible_text

# Initialize the Orthodox Dictionary handler
orthodox_dict = OrthodoxDictionary(dict_path="dict.jsonl", min_score=65)

def extract_command_and_text(user_message: str, command_prefix: str) -> Tuple[str, str]:
    """
    Extract the command and the text to process, considering variations in command format.
    Looks for punctuation marks that might separate the command from the text.
    
    Args:
        user_message: The full user message
        command_prefix: The basic command prefix to look for (e.g., "translate", "annotate")
        
    Returns:
        Tuple of (command_part, text_to_process)
    """
    # Check if the message starts with the command prefix
    if not user_message.lower().startswith(command_prefix.lower()):
        return "", user_message
    
    # Find the first punctuation mark after the command prefix
    # Common separators: ":", ".", ",", "-", ";"
    command_part = user_message
    text_to_process = ""
    
    # Look for punctuation marks that might separate command from text
    separators = [":", ".", ",", "-", ";", "\n"]
    min_pos = len(user_message)
    
    for sep in separators:
        pos = user_message.find(sep, len(command_prefix))
        if pos > 0 and pos < min_pos:
            min_pos = pos
            command_part = user_message[:min_pos + 1]  # Include the separator
            text_to_process = user_message[min_pos + 1:].strip()
    
    # If no separator found, assume the command is just the prefix
    # and everything after is the text
    if text_to_process == "":
        command_part = command_prefix
        text_to_process = user_message[len(command_prefix):].strip()
    
    return command_part, text_to_process

def get_bible_quote_translations(text: str) -> List[Tuple[str, str]]:
    """
    Extract Bible references from text and fetch their translations in both English and Chinese.
    
    Args:
        text: Text containing Bible references in parentheses
        
    Returns:
        List of tuples containing (english_quote, chinese_quote)
    """
    bible_translations = []
    references = extract_bible_references(text)
    
    for reference, _ in references:
        parsed = parse_bible_reference(reference)
        if parsed:
            book_name, where_expr = parsed
            
            # Fetch English version
            english_text = fetch_bible_text(book_name, where_expr, lang="en")
            
            # Fetch Chinese version
            chinese_text = fetch_bible_text(book_name, where_expr, lang="hk")
            
            if english_text and chinese_text:
                bible_translations.append((english_text, chinese_text))
    
    return bible_translations

# Enhanced prompt engineering function for Orthodox Christian translation and Bible annotation
def process_user_message(user_message: str, messages: List[Dict], orthodox_enabled: bool) -> tuple[List[Dict], str, str]:
    """
    Process user message through prompt engineering.
    Detects special commands (translate, annotate, add footnotes) and applies appropriate context.
    Commands are only recognized when they appear at the beginning of the message.
    Returns: (processed_messages, command_type, processed_query)
    """
    processed_messages = messages.copy()
    command_type = "normal"
    processed_query = user_message  # Default to original message
    
    user_message_lower = user_message.lower().strip()
    
    # Check for "add footnotes" command (only at the beginning of the message)
    if user_message_lower.startswith("add footnotes"):
        command_type = "add_footnotes"
        
        # Extract the command part and the text to process
        _, text_to_process = extract_command_and_text(user_message, "add footnotes")
        
        if text_to_process:
            # Process the text to extract Bible references and fetch their content
            try:
                processed_text, footnotes = process_footnotes(text_to_process)
                
                # Create a prompt for the AI to format the text with footnotes
                footnotes_prompt = "Please format the following text with Bible footnotes. Add the footnote text at the end of the document, with each footnote on a new line. The footnotes have already been marked with [n] in the text.\n\n"
                footnotes_prompt += processed_text + "\n\n"
                footnotes_prompt += "Footnotes:\n"
                
                for i, footnote in enumerate(footnotes):
                    footnotes_prompt += f"[{i+1}] {footnote['reference']}: {footnote['text']}\n"
                
                processed_query = footnotes_prompt
            except Exception as e:
                processed_query = f"I encountered an error processing the Bible references: {str(e)}. Please make sure the text contains valid Bible references in parentheses, such as (John 3:16) or (Romans 8:28-30)."
        else:
            # If no text after "add footnotes", ask for clarification
            processed_query = "Please provide the annotated text you would like to add Bible footnotes to. The text should already contain Bible references in parentheses, such as (John 3:16) or (Romans 8:28-30)."
        
        processed_messages.append({"role": "user", "content": processed_query})
    
    # Check for "annotate" command (only at the beginning of the message)
    elif user_message_lower.startswith("annotate"):
        command_type = "annotate"
        
        # Extract the command part and the text to annotate
        _, text_to_annotate = extract_command_and_text(user_message, "annotate")
        
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
        
        # Extract the command part and the text to translate
        _, text_to_translate = extract_command_and_text(user_message, "translate")
        
        # Find matching Orthodox terms in the text to translate
        if text_to_translate:
            # Use the fuzzy matcher to find Orthodox terms in the text
            matching_terms = orthodox_dict.find_matching_terms(text_to_translate)
            
            # Create dictionary prompt section if matches were found
            dictionary_prompt = orthodox_dict.create_dictionary_prompt(matching_terms)
            
            # NEW: Check for Bible references in the text and add their translations to the dictionary
            bible_translations = get_bible_quote_translations(text_to_translate)
            
            # If Bible translations were found, add them to the dictionary prompt
            if bible_translations:
                if not dictionary_prompt:
                    dictionary_prompt = "\nWhen translating the text, you MUST use the following dictionary of terms:\n\n"
                else:
                    dictionary_prompt += "\nAdditionally, use these translations for Bible quotes found in the text:\n\n"
                
                for english_quote, chinese_quote in bible_translations:
                    # Format the Bible quotes as dictionary entries
                    # Truncate long quotes if needed to keep the prompt manageable
                    eng_quote = english_quote[:150] + "..." if len(english_quote) > 150 else english_quote
                    dictionary_prompt += f"- \"{eng_quote}\": \"{chinese_quote}\"\n"
                
                dictionary_prompt += "\nThese translations for Bible quotes are authoritative and must be used exactly as provided.\n"
            
            # Create the enhanced message with Orthodox Christian context and dictionary
            processed_query = f"{ORTHODOX_TRANSLATION_PROMPT}{dictionary_prompt}\n\n" + "Please translate the following text:\n\n" + text_to_translate
  
        else:
            # If no text after "translate", ask for clarification
            processed_query = f"{ORTHODOX_TRANSLATION_PROMPT}\n\n(Please provide the English text you would like me to translate to traditional Chinese.)"
        
        processed_messages.append({"role": "user", "content": processed_query})
        
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
    elif command_type == "add_footnotes":
        st.info("📝 **Bible Footnotes Mode**: Adding full Bible text as footnotes for each reference")