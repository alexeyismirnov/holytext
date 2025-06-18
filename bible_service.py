"""
Bible Service
Handles interactions with the Bible API to fetch scripture passages
"""

import requests
import re
from typing import Dict, List, Optional, Tuple

# Bible API endpoint
BIBLE_API_URL = "https://ponomarserver-production.up.railway.app/pericope"

def parse_bible_reference(reference: str) -> Optional[Tuple[str, str]]:
    """
    Parse a Bible reference into book name and where expression
    
    Args:
        reference: Bible reference (e.g., "John 1:2-5", "Matthew 7:21", "1 Corinthians 13:4-7")
        
    Returns:
        Tuple of (book_name, where_expression) or None if parsing fails
    """
    # Common abbreviations mapping
    book_abbreviations = {
        "1 corinthians": "1cor", "1 cor": "1cor", "i cor": "1cor", "i corinthians": "1cor",
        "2 corinthians": "2cor", "2 cor": "2cor", "ii cor": "2cor", "ii corinthians": "2cor",
        "1 thessalonians": "1thess", "1 thess": "1thess", "i thess": "1thess", "i thessalonians": "1thess",
        "2 thessalonians": "2thess", "2 thess": "2thess", "ii thess": "2thess", "ii thessalonians": "2thess",
        "1 timothy": "1tim", "1 tim": "1tim", "i tim": "1tim", "i timothy": "1tim",
        "2 timothy": "2tim", "2 tim": "2tim", "ii tim": "2tim", "ii timothy": "2tim",
        "1 peter": "1pet", "1 pet": "1pet", "i pet": "1pet", "i peter": "1pet",
        "2 peter": "2pet", "2 pet": "2pet", "ii pet": "2pet", "ii peter": "2pet",
        "1 john": "1john", "1 jn": "1john", "i jn": "1john", "i john": "1john",
        "2 john": "2john", "2 jn": "2john", "ii jn": "2john", "ii john": "2john",
        "3 john": "3john", "3 jn": "3john", "iii jn": "3john", "iii john": "3john",
        "1 kings": "1kings", "1 kgs": "1kings", "i kgs": "1kings", "i kings": "1kings",
        "2 kings": "2kings", "2 kgs": "2kings", "ii kgs": "2kings", "ii kings": "2kings",
        "1 samuel": "1sam", "1 sam": "1sam", "i sam": "1sam", "i samuel": "1sam",
        "2 samuel": "2sam", "2 sam": "2sam", "ii sam": "2sam", "ii samuel": "2sam",
        "1 chronicles": "1chron", "1 chron": "1chron", "i chron": "1chron", "i chronicles": "1chron",
        "2 chronicles": "2chron", "2 chron": "2chron", "ii chron": "2chron", "ii chronicles": "2chron",
        "matthew": "matthew", "mark": "mark", "luke": "luke", "john": "john",
        "acts": "acts", "romans": "rom", "galatians": "gal", "ephesians": "eph",
        "philippians": "phil", "colossians": "col", "titus": "titus", "philemon": "philem",
        "hebrews": "heb", "james": "james", "jude": "jude", "revelation": "rev",
        "genesis": "gen", "exodus": "exod", "leviticus": "lev", "numbers": "num",
        "deuteronomy": "deut", "joshua": "josh", "judges": "judg", "ruth": "ruth",
        "ezra": "ezra", "nehemiah": "neh", "esther": "esth", "job": "job",
        "psalms": "ps", "psalm": "ps", "proverbs": "prov", "ecclesiastes": "eccl",
        "song of solomon": "song", "isaiah": "isa", "jeremiah": "jer", "lamentations": "lam",
        "ezekiel": "ezek", "daniel": "dan", "hosea": "hos", "joel": "joel",
        "amos": "amos", "obadiah": "obad", "jonah": "jonah", "micah": "mic",
        "nahum": "nah", "habakkuk": "hab", "zephaniah": "zeph", "haggai": "hag",
        "zechariah": "zech", "malachi": "mal"
    }
    
    try:
        # Remove parentheses if present
        reference = reference.strip()
        if reference.startswith('(') and reference.endswith(')'):
            reference = reference[1:-1].strip()
        
        # More flexible pattern that handles variable spacing
        # This pattern allows for any amount of whitespace between components
        pattern = r'([\w\s]+?)\s+(\d+)\s*:\s*(\d+)(?:\s*-\s*(\d+))?'
        match = re.match(pattern, reference)
        
        if not match:
            return None
        
        book_name = match.group(1).strip().lower()
        chapter = match.group(2)
        start_verse = match.group(3)
        end_verse = match.group(4)  # May be None if no range
        
        # Convert book name to API format
        api_book_name = book_abbreviations.get(book_name, book_name.replace(' ', '').lower())
        
        # Build the where expression
        where_expr = f"chapter={chapter} AND verse>={start_verse}"
        if end_verse:
            where_expr += f" AND verse<={end_verse}"
        else:
            where_expr += f" AND verse<={start_verse}"  # Just one verse
        
        return (api_book_name, where_expr)
    
    except Exception as e:
        print(f"Error parsing Bible reference: {e}")
        return None

def fetch_bible_text(book_name: str, where_expr: str, lang: str = "en") -> Optional[str]:
    """
    Fetch Bible text from the API
    
    Args:
        book_name: Name of the Bible book in API format
        where_expr: SQL-like WHERE clause for chapter/verse selection
        lang: Language code (default: "en")
        
    Returns:
        Formatted Bible text or None if request fails
    """
    try:
        payload = {
            "bookName": book_name,
            "lang": lang,
            "whereExpr": where_expr
        }
        
        response = requests.post(BIBLE_API_URL, json=payload)
        
        if response.status_code == 200:
            verses = response.json()
            
            if not verses:
                return None
            
            # Format the text
            formatted_text = ""
            for verse in verses:
                #formatted_text += f"{verse['verse']}. {verse['text']} "
                formatted_text += f"{verse['text']} "

            return formatted_text.strip()
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error fetching Bible text: {e}")
        return None

def extract_bible_references(text: str) -> List[Tuple[str, str]]:
    """
    Extract Bible references from annotated text
    
    Args:
        text: Annotated text with Bible references in parentheses
        
    Returns:
        List of tuples containing (reference, full_match)
    """
    # More flexible pattern to match Bible references in parentheses with variable spacing
    pattern = r'\(([\w\s]+?\s+\d+\s*:\s*\d+(?:\s*-\s*\d+)?)\)'
    
    matches = re.finditer(pattern, text)
    references = []
    
    for match in matches:
        full_match = match.group(0)  # The entire match including parentheses
        reference = match.group(1)   # Just the reference without parentheses
        references.append((reference, full_match))
    
    return references

def process_footnotes(text: str) -> Tuple[str, List[Dict]]:
    """
    Process annotated text and generate footnotes
    
    Args:
        text: Annotated text with Bible references
        
    Returns:
        Tuple of (processed_text, footnotes)
        where footnotes is a list of dictionaries with 'reference' and 'text' keys
    """
    references = extract_bible_references(text)
    footnotes = []
    processed_text = text
    
    for i, (reference, full_match) in enumerate(references):
        footnote_marker = f"[{i+1}]"
        
        # Parse the reference
        parsed = parse_bible_reference(reference)
        
        if parsed:
            book_name, where_expr = parsed
            bible_text = fetch_bible_text(book_name, where_expr)
            
            if bible_text:
                # Replace the reference with a footnote marker
                processed_text = processed_text.replace(full_match, f"{full_match}{footnote_marker}", 1)
                
                # Add to footnotes
                footnotes.append({
                    "reference": reference,
                    "text": bible_text
                })
    
    return processed_text, footnotes