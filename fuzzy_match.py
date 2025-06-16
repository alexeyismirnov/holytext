"""
Advanced Fuzzy Matcher for Theological Terms
Optimized version using RapidFuzz with multiple algorithms
Usage: python advanced_fuzzy_matcher.py <source_file> <terminology_file> [options]
"""

from rapidfuzz import fuzz, process, utils
from typing import List, Dict, Tuple, Optional
import re
import argparse
import sys
import json
from pathlib import Path

class AdvancedFuzzyMatcher:
    def __init__(self, 
                 min_score: int = 80,
                 token_set_weight: float = 0.3,
                 token_sort_weight: float = 0.3, 
                 partial_weight: float = 0.2,
                 ratio_weight: float = 0.2):
        """
        Advanced fuzzy matcher with weighted algorithm combination
        
        Args:
            min_score: Minimum score threshold (0-100)
            token_set_weight: Weight for token set ratio
            token_sort_weight: Weight for token sort ratio  
            partial_weight: Weight for partial ratio
            ratio_weight: Weight for basic ratio
        """
        self.min_score = min_score
        self.weights = {
            'token_set': token_set_weight,
            'token_sort': token_sort_weight,
            'partial': partial_weight,
            'ratio': ratio_weight
        }
        
        # Normalize weights to sum to 1
        total_weight = sum(self.weights.values())
        self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def preprocess_text(self, text: str) -> str:
        """Enhanced preprocessing for theological texts"""
        # Remove extra whitespace and normalize
        text = utils.default_process(text)
        
        # Handle common theological abbreviations
        theological_normalizations = {
            r'\bSt\.': 'Saint',
            r'\bBl\.': 'Blessed', 
            r'\bVen\.': 'Venerable',
            r'\bFr\.': 'Father',
            r'\bMt\.': 'Mount',
            r'\bMgr\.': 'Monsignor'
        }
        
        for pattern, replacement in theological_normalizations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def get_composite_score(self, term: str, text: str) -> Tuple[float, Dict]:
        """Calculate weighted composite score using multiple algorithms"""
        
        # Preprocess both strings
        term_clean = self.preprocess_text(term)
        text_clean = self.preprocess_text(text)
        
        # Calculate scores using different algorithms
        scores = {
            'token_set': fuzz.token_set_ratio(term_clean, text_clean),
            'token_sort': fuzz.token_sort_ratio(term_clean, text_clean),
            'partial': fuzz.partial_ratio(term_clean, text_clean),
            'ratio': fuzz.ratio(term_clean, text_clean)
        }
        
        # Calculate weighted average
        composite_score = sum(
            scores[alg] * self.weights[alg] 
            for alg in scores
        )
        
        return composite_score, scores
    
    def find_best_matches(self, 
                         term: str, 
                         text_list: List[str], 
                         limit: int = 5) -> List[Tuple[str, float, Dict]]:
        """Find best matches with detailed scoring"""
        
        results = []
        for text in text_list:
            composite_score, individual_scores = self.get_composite_score(term, text)
            
            if composite_score >= self.min_score:
                results.append((text, composite_score, individual_scores))
        
        # Sort by composite score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def bulk_extract(self, 
                    terms: List[str], 
                    text_list: List[str],
                    limit_per_term: int = 3) -> Dict[str, List[Tuple[str, float]]]:
        """Efficient bulk extraction for multiple terms"""
        results = {}
        
        for term in terms:
            matches = self.find_best_matches(term, text_list, limit_per_term)
            results[term] = [(text, score) for text, score, _ in matches]
        
        return results

def load_file(file_path: str) -> List[str]:
    """Load text lines from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file '{file_path}': {e}")
        sys.exit(1)

def save_results(results: Dict, output_file: str, format_type: str = 'json'):
    """Save results to file"""
    try:
        if format_type.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:  # text format
            with open(output_file, 'w', encoding='utf-8') as f:
                for term, matches in results.items():
                    f.write(f"\n🔍 '{term}' matches:\n")
                    for text, score in matches:
                        f.write(f"  📍 {score:.1f}% - '{text}'\n")
        print(f"✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Advanced Fuzzy Matcher for Theological Terms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python advanced_fuzzy_matcher.py source.txt terms.txt
  python advanced_fuzzy_matcher.py source.txt terms.txt --min-score 75 --output results.json
  python advanced_fuzzy_matcher.py source.txt terms.txt --limit 5 --format text
        """
    )
    
    # Required arguments
    parser.add_argument('source_file', help='Source text file to search in')
    parser.add_argument('terminology_file', help='File containing search terms (one per line)')
    
    # Optional arguments
    parser.add_argument('--min-score', type=int, default=80, 
                       help='Minimum similarity score (0-100, default: 80)')
    parser.add_argument('--limit', type=int, default=3,
                       help='Maximum matches per term (default: 3)')
    parser.add_argument('--output', '-o', type=str,
                       help='Output file (default: print to console)')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format (default: json)')
    
    # Algorithm weights
    parser.add_argument('--token-set-weight', type=float, default=0.3,
                       help='Weight for token set ratio (default: 0.3)')
    parser.add_argument('--token-sort-weight', type=float, default=0.3,
                       help='Weight for token sort ratio (default: 0.3)')
    parser.add_argument('--partial-weight', type=float, default=0.2,
                       help='Weight for partial ratio (default: 0.2)')
    parser.add_argument('--ratio-weight', type=float, default=0.2,
                       help='Weight for basic ratio (default: 0.2)')
    
    args = parser.parse_args()
    
    # Validate files exist
    if not Path(args.source_file).exists():
        print(f"❌ Error: Source file '{args.source_file}' not found.")
        sys.exit(1)
    
    if not Path(args.terminology_file).exists():
        print(f"❌ Error: Terminology file '{args.terminology_file}' not found.")
        sys.exit(1)
    
    # Load files
    print(f"📂 Loading source file: {args.source_file}")
    source_texts = load_file(args.source_file)
    print(f"   Loaded {len(source_texts)} text entries")
    
    print(f"📂 Loading terminology file: {args.terminology_file}")
    search_terms = load_file(args.terminology_file)
    print(f"   Loaded {len(search_terms)} search terms")
    
    # Initialize matcher
    matcher = AdvancedFuzzyMatcher(
        min_score=args.min_score,
        token_set_weight=args.token_set_weight,
        token_sort_weight=args.token_sort_weight,
        partial_weight=args.partial_weight,
        ratio_weight=args.ratio_weight
    )
    
    print(f"\n🔍 Processing with minimum score: {args.min_score}%")
    print(f"⚖️  Algorithm weights: TokenSet={args.token_set_weight}, TokenSort={args.token_sort_weight}, Partial={args.partial_weight}, Ratio={args.ratio_weight}")
    
    # Process matches
    results = matcher.bulk_extract(search_terms, source_texts, args.limit)
    
    # Filter out empty results
    filtered_results = {term: matches for term, matches in results.items() if matches}
    
    # Display results
    total_matches = sum(len(matches) for matches in filtered_results.values())
    print(f"\n📊 Found {total_matches} total matches for {len(filtered_results)} terms")
    
    if args.output:
        # Save to file
        save_results(filtered_results, args.output, args.format)
    else:
        # Print to console
        if filtered_results:
            print("\n" + "="*80)
            for term, matches in filtered_results.items():
                print(f"\n🔍 '{term}' matches:")
                for text, score in matches:
                    print(f"  📍 {score:.1f}% - '{text}'")
        else:
            print("\n❌ No matches found above the minimum score threshold.")
    
    print(f"\n✅ Processing complete!")

if __name__ == "__main__":
    main()