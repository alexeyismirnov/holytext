"""
Orthodox Dictionary Handler
Loads and processes the specialized Orthodox Christian terminology dictionary
"""

import json
import os
import glob
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path
import re
from fuzzy_match import AdvancedFuzzyMatcher, fuzz
import streamlit as st

class OrthodoxDictionary:
    def __init__(self, dict_dir: str = "dict", min_score: int = 65):
        """
        Initialize the Orthodox dictionary handler
        
        Args:
            dict_dir: Directory containing dictionary JSONL files
            min_score: Minimum score threshold for fuzzy matching (0-100)
        """
        self.dict_dir = dict_dir
        self.terms_dict = self._load_dictionaries()
        
        # Use user-defined min_score from session state if available
        if "orthodox_min_score" in st.session_state:
            self.min_score = st.session_state.orthodox_min_score
        else:
            self.min_score = min_score
            
        self.fuzzy_matcher = AdvancedFuzzyMatcher(min_score=self.min_score)
        
    def _load_dictionaries(self) -> Dict[str, List[str]]:
        """
        Load all dictionaries from JSONL files in the dict directory
        
        Returns:
            Dictionary mapping English terms to lists of Chinese translations
        """
        terms_dict = {}
        
        try:
            # Get all .jsonl files in the dict directory
            dict_files = glob.glob(os.path.join(self.dict_dir, "*.jsonl"))
            
            if not dict_files:
                print(f"Warning: No .jsonl files found in {self.dict_dir} directory")
                return {}
            
            # Load each dictionary file
            for dict_file in dict_files:
                print(f"Loading dictionary file: {dict_file}")
                try:
                    with open(dict_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    term_entry = json.loads(line)
                                    # Each line is a single key-value pair
                                    for english_term, chinese_translation in term_entry.items():
                                        # Strip any extra whitespace
                                        english_term = english_term.strip()
                                        chinese_translation = chinese_translation.strip()
                                        
                                        # Store multiple translations for the same term
                                        if english_term not in terms_dict:
                                            terms_dict[english_term] = [chinese_translation]
                                        else:
                                            # Only add if this translation is not already in the list
                                            if chinese_translation not in terms_dict[english_term]:
                                                terms_dict[english_term].append(chinese_translation)
                                except json.JSONDecodeError:
                                    # Skip invalid lines
                                    continue
                except Exception as e:
                    print(f"Error loading dictionary file {dict_file}: {e}")
                    continue
            
            term_count = len(terms_dict)
            translation_count = sum(len(translations) for translations in terms_dict.values())
            print(f"Loaded {term_count} terms with {translation_count} translations from {len(dict_files)} dictionary files")
            return terms_dict
        except Exception as e:
            print(f"Error loading dictionaries: {e}")
            return {}
    
    def get_all_english_terms(self) -> List[str]:
        """Get all English terms from the dictionary"""
        return list(self.terms_dict.keys())
    
    def find_matching_terms(self, text: str) -> List[Tuple[str, List[str], float]]:
        """
        Find Orthodox terms in the input text using direct and fuzzy matching
        
        Returns:
            List of tuples containing (english_term, list_of_chinese_translations, match_score)
        """
        # Update min_score from session state if it has changed
        if "orthodox_min_score" in st.session_state:
            self.min_score = st.session_state.orthodox_min_score
            self.fuzzy_matcher.min_score = self.min_score
        
        # Split text into sentences for more accurate matching
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        all_matches = []
        english_terms = self.get_all_english_terms()
        
        # Process each sentence separately
        for sentence in sentences:
            sentence_matches = []
            
            # First pass: Direct substring matching (case insensitive)
            direct_matches = []
            for term in english_terms:
                if term.lower() in sentence.lower():
                    # Direct match found
                    direct_matches.append((term, self.terms_dict[term], 100.0))
            
            # Add direct matches to our results
            sentence_matches.extend(direct_matches)
            
            # Second pass: Word-level matching
            for term in english_terms:
                # Skip terms we've already directly matched
                if any(term == direct_term for direct_term, _, _ in direct_matches):
                    continue
                    
                # Check individual words in the text against each term
                words = re.findall(r'\b\w+\b', sentence.lower())
                term_words = re.findall(r'\b\w+\b', term.lower())
                
                # If all words in the term are found in the text (in any order)
                if all(word in words for word in term_words) and len(term_words) > 1:
                    sentence_matches.append((term, self.terms_dict[term], 90.0))
            
            # Third pass: Fuzzy matching for each term
            # Use a slightly higher threshold for fuzzy matching in sentences
            fuzzy_min_score = self.min_score   # Increase threshold for fuzzy matching
            
            for term in english_terms:
                # Skip terms we've already matched
                if any(term == matched_term for matched_term, _, _ in sentence_matches):
                    continue
                    
                # Use token_set_ratio which is good for finding terms within longer text
                score = fuzz.token_set_ratio(term.lower(), sentence.lower())
                
                if score >= fuzzy_min_score:  # Use higher threshold
                    sentence_matches.append((term, self.terms_dict[term], float(score)))
            
            all_matches.extend(sentence_matches)
        
        # Remove duplicates (keep highest score)
        unique_matches = {}
        for term, translations, score in all_matches:
            if term not in unique_matches or score > unique_matches[term][1]:
                unique_matches[term] = (translations, score)
        
        # Convert back to list format
        result = [(term, trans, score) for term, (trans, score) in unique_matches.items()]
        
        # Sort by score (highest first)
        result.sort(key=lambda x: x[2], reverse=True)
        
        return result
    
    def create_dictionary_prompt(self, matches: List[Tuple[str, List[str], float]]) -> str:
        """
        Create a prompt section with the dictionary terms
        
        Args:
            matches: List of matched terms (english_term, list_of_chinese_translations, score)
        
        Returns:
            Formatted prompt section with dictionary terms
        """
        if not matches:
            return ""
        
        # Create the dictionary prompt
        prompt = "\nWhen translating the text, you MUST use the following dictionary of special Orthodox Christian terms:\n\n"
        
        # Add each term with all its translations
        for english, chinese_translations, _ in matches:
            if len(chinese_translations) == 1:
                prompt += f"- \"{english}\": \"{chinese_translations[0]}\"\n"
            else:
                # Format multiple translations
                translations_str = "\", \"".join(chinese_translations)
                prompt += f"- \"{english}\": [\"{translations_str}\"] (choose the most appropriate translation based on context)\n"
        
        prompt += "\nThese translations for specialized Orthodox terms are authoritative and must be used exactly as provided. "
        prompt += "When multiple translations are available for a term, select the most appropriate one based on the context.\n"
        
        return prompt

# Example usage
if __name__ == "__main__":
    orthodox_dict = OrthodoxDictionary()
    sample_text = "The Divine Liturgy was celebrated by the Archbishop with the Cherubic hymn."
    
    matches = orthodox_dict.find_matching_terms(sample_text)
    prompt_section = orthodox_dict.create_dictionary_prompt(matches)
    
    print(f"Found {len(matches)} matching terms:")
    for term, translations, score in matches:
        print(f"  - {term} → {translations} (score: {score:.1f})")
    
    print("\nDictionary Prompt Section:")
    print(prompt_section)