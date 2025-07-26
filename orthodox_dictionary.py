"""
Orthodox Dictionary Handler
Loads and processes the specialized Orthodox Christian terminology dictionary
"""

import json
import os
import glob
from typing import Dict, List, Set, Tuple
from pathlib import Path
import re
from fuzzy_match import AdvancedFuzzyMatcher, fuzz

class OrthodoxDictionary:
    def __init__(self, dict_dir: str = "dict", min_score: int = 75):
        """
        Initialize the Orthodox dictionary handler
        
        Args:
            dict_dir: Directory containing dictionary JSONL files
            min_score: Minimum score threshold for fuzzy matching (0-100)
        """
        self.dict_dir = dict_dir
        self.terms_dict = self._load_dictionaries()
        self.min_score = min_score
        self.fuzzy_matcher = AdvancedFuzzyMatcher(min_score=min_score)
        
    def _load_dictionaries(self) -> Dict[str, str]:
        """Load all dictionaries from JSONL files in the dict directory"""
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
                                        terms_dict[english_term] = chinese_translation
                                except json.JSONDecodeError:
                                    # Skip invalid lines
                                    continue
                except Exception as e:
                    print(f"Error loading dictionary file {dict_file}: {e}")
                    continue
            
            print(f"Loaded {len(terms_dict)} terms from {len(dict_files)} dictionary files")
            return terms_dict
        except Exception as e:
            print(f"Error loading dictionaries: {e}")
            return {}
    
    def get_all_english_terms(self) -> List[str]:
        """Get all English terms from the dictionary"""
        return list(self.terms_dict.keys())
    
    def find_matching_terms(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Find Orthodox terms in the input text using direct and fuzzy matching
        
        Returns:
            List of tuples containing (english_term, chinese_translation, match_score)
        """
        matches = []
        english_terms = self.get_all_english_terms()
        
        # First pass: Direct substring matching (case insensitive)
        direct_matches = []
        for term in english_terms:
            if term.lower() in text.lower():
                # Direct match found
                direct_matches.append((term, self.terms_dict[term], 100.0))
        
        # Add direct matches to our results
        matches.extend(direct_matches)
        
        # Second pass: Word-level matching
        for term in english_terms:
            # Skip terms we've already directly matched
            if any(term == direct_term for direct_term, _, _ in direct_matches):
                continue
                
            # Check individual words in the text against each term
            words = re.findall(r'\b\w+\b', text.lower())
            term_words = re.findall(r'\b\w+\b', term.lower())
            
            # If all words in the term are found in the text (in any order)
            if all(word in words for word in term_words) and len(term_words) > 1:
                matches.append((term, self.terms_dict[term], 90.0))
        
        # Third pass: Fuzzy matching for each term
        # Even if we have direct matches, still try fuzzy matching for other terms
        for term in english_terms:
            # Skip terms we've already matched
            if any(term == matched_term for matched_term, _, _ in matches):
                continue
                
            # Use token_set_ratio which is good for finding terms within longer text
            score = fuzz.token_set_ratio(term.lower(), text.lower())
            
            if score >= self.min_score:
                matches.append((term, self.terms_dict[term], float(score)))
        
        # Remove duplicates (keep highest score)
        unique_matches = {}
        for term, translation, score in matches:
            if term not in unique_matches or score > unique_matches[term][1]:
                unique_matches[term] = (translation, score)
        
        # Convert back to list format
        result = [(term, trans, score) for term, (trans, score) in unique_matches.items()]
        
        # Sort by score (highest first)
        result.sort(key=lambda x: x[2], reverse=True)
        
        return result
    
    def create_dictionary_prompt(self, matches: List[Tuple[str, str, float]]) -> str:
        """
        Create a prompt section with the dictionary terms
        
        Args:
            matches: List of matched terms (english_term, chinese_translation, score)
        
        Returns:
            Formatted prompt section with dictionary terms
        """
        if not matches:
            return ""
        
        # Create the dictionary prompt
        prompt = "\nWhen translating the text, you MUST use the following dictionary of special Orthodox Christian terms:\n\n"
        
        # Add each term with its translation
        for english, chinese, _ in matches:
            prompt += f"- \"{english}\": \"{chinese}\"\n"
        
        prompt += "\nThese translations for specialized Orthodox terms are authoritative and must be used exactly as provided.\n"
        
        return prompt

# Example usage
if __name__ == "__main__":
    orthodox_dict = OrthodoxDictionary()
    sample_text = "The Divine Liturgy was celebrated by the Archbishop with the Cherubic hymn."
    
    matches = orthodox_dict.find_matching_terms(sample_text)
    prompt_section = orthodox_dict.create_dictionary_prompt(matches)
    
    print(f"Found {len(matches)} matching terms:")
    for term, translation, score in matches:
        print(f"  - {term} → {translation} (score: {score:.1f})")
    
    print("\nDictionary Prompt Section:")
    print(prompt_section)