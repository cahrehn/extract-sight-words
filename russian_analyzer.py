import re
from collections import Counter
from typing import Dict, List, Tuple
from string import punctuation
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text
import argparse
from pathlib import Path
import pymorphy2

class RussianTextAnalyzer:
    def __init__(self):
        # Initialize the morphological analyzer
        self.morph = pymorphy2.MorphAnalyzer()
        # Define Russian vowels
        self.vowels = set('аеёиоуыэюя')
        # Russian stopwords (common words that don't carry much meaning)
        self.stopwords = set(['ее'])
        # Initialize HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True

    def read_text_file(self, file_path: str) -> str:
        """Read text content from a plain text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_text_from_epub(self, epub_path: str) -> str:
        """Extract text content from an EPUB file."""
        book = epub.read_epub(epub_path)
        text_content = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            for element in soup(['script', 'style', 'header', 'footer', 'nav']):
                element.decompose()
            content = self.html_converter.handle(str(soup))
            text_content.append(content)

        return '\n'.join(text_content)

    def read_file(self, file_path: str) -> str:
        """Read content from either a text file or EPUB file."""
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.epub':
            return self.extract_text_from_epub(file_path)
        elif file_extension in ['.txt', '.text']:
            return self.read_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def clean_text(self, text: str) -> str:
        """Remove punctuation and extra whitespace."""
        text = ''.join(char for char in text if char not in punctuation)
        return ' '.join(text.split()).lower()

    def extract_words(self, text: str) -> List[str]:
        """Extract individual words from text."""
        clean = self.clean_text(text)
        return [word for word in clean.split() if any(c.isalpha() for c in word)]

    def get_lemma(self, word: str) -> str:
        """Get the base form (lemma) of a word."""
        return self.morph.parse(word)[0].normal_form

    def count_syllables(self, word: str) -> int:
        """Count syllables in a Russian word."""
        return sum(1 for letter in word.lower() if letter in self.vowels)

    def get_frequency_distribution(self, text: str, exclude_stopwords: bool = True, lemmatize: bool = True) -> List[Tuple[str, int]]:
        """Get frequency distribution of either words or lemmas."""
        words = self.extract_words(text)
        if exclude_stopwords:
            words = [w for w in words if w not in self.stopwords]
        if lemmatize:
            items = [self.get_lemma(w) for w in words]
        else:
            items = words
        return Counter(items).most_common()

    def calculate_vocabulary_coverage(self, frequency_distribution: List[Tuple[str, int]], target_items: int = 100) -> Dict:
        """Calculate the coverage achieved by learning the top N items (words or lemmas)."""
        total_occurrences = sum(count for _, count in frequency_distribution)
        
        # Take only the specified number of top items
        top_items = frequency_distribution[:target_items]
        cumulative_count = sum(count for _, count in top_items)
        
        return {
            'target_items': target_items,
            'coverage_percentage': cumulative_count / total_occurrences,
            'total_unique_items': len(frequency_distribution),
            'total_occurrences': total_occurrences,
            'cumulative_frequencies': [
                (i + 1, sum(count for _, count in frequency_distribution[:i+1]) / total_occurrences)
                for i in range(min(target_items, len(frequency_distribution)))
            ]
        }

    def analyze_text(self, text: str) -> Dict:
        """Perform comprehensive analysis of the text."""
        # Extract and count raw words
        words = self.extract_words(text)
        raw_word_count = len(words)
        
        # Get lemmatized frequency distribution and coverage
        lemma_frequencies = self.get_frequency_distribution(text, lemmatize=True)
        common_lemmas = lemma_frequencies[:100]
        lemma_coverage = self.calculate_vocabulary_coverage(lemma_frequencies, 100)
        
        # Calculate statistics
        unique_words = len(set(words))
        
        # Map lemmas to their word forms for common lemmas
        lemma_to_wordforms = {}
        for lemma, count in common_lemmas:
            # Find original word forms for this lemma
            word_forms = set()
            for word in words:
                if self.get_lemma(word) == lemma:
                    word_forms.add(word)
            lemma_to_wordforms[lemma] = list(word_forms)

        return {
            'raw_word_count': raw_word_count,
            'unique_word_count': unique_words,
            'common_lemmas': common_lemmas,
            'wordforms_by_lemma': lemma_to_wordforms,
            'lemma_coverage': lemma_coverage
        }

    def save_analysis_to_file(self, analysis: Dict, output_path: str):
        """Save analysis results to a text file."""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Text Analysis Results ===\n\n")
            f.write(f"Raw word count: {analysis['raw_word_count']}\n")
            f.write(f"Unique words: {analysis['unique_word_count']}\n")
            
            f.write("\nMost common lemmas:\n")
            for lemma, count in analysis['common_lemmas']:
                forms = analysis['wordforms_by_lemma'].get(lemma, [])
                f.write(f"  {lemma} ({count} occurrences)\n")
                if forms:
                    f.write(f"    Word forms found: {', '.join(forms)}\n")
                        
            f.write("\nLemma Coverage Analysis:\n")
            coverage = analysis['lemma_coverage']
            f.write(f"  Coverage with top {coverage['target_items']} lemmas: {coverage['coverage_percentage']:.2%}\n")
            f.write(f"  Total unique lemmas: {coverage['total_unique_items']}\n")
            f.write(f"  Total word occurrences: {coverage['total_occurrences']}\n")
            
            f.write("\nCumulative Coverage by Lemma Count:\n")
            for items, coverage in coverage['cumulative_frequencies']:
                if items % 10 == 0 or items == 1:  # Show at item 1 and every 10 items
                    f.write(f"  Top {items:3d} lemmas: {coverage:.2%}\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze Russian text from file')
    parser.add_argument('input_path', type=str, help='Path to input file (EPUB or TXT)')
    parser.add_argument('--output', '-o', type=str, help='Path to output file for analysis results', 
                      default='analysis_results.txt')
    args = parser.parse_args()

    if not Path(args.input_path).exists():
        print(f"Error: File '{args.input_path}' not found.")
        return

    analyzer = RussianTextAnalyzer()

    try:
        print(f"Reading file {args.input_path}...")
        text = analyzer.read_file(args.input_path)
        
        print("Analyzing text...")
        results = analyzer.analyze_text(text)
        
        analyzer.save_analysis_to_file(results, args.output)
        print(f"\nAnalysis complete! Results saved to {args.output}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()