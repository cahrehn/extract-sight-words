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
        # self.stopwords = set(['и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему'])
        self.stopwords = set(['ее'])
        # Initialize HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True

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

    def clean_text(self, text: str) -> str:
        """Remove punctuation and extra whitespace."""
        text = ''.join(char for char in text if char not in punctuation)
        return ' '.join(text.split()).lower()

    def get_words(self, text: str) -> List[str]:
        """Split text into words."""
        clean = self.clean_text(text)
        return [word for word in clean.split() if any(c.isalpha() for c in word)]

    def get_lemma(self, word: str) -> str:
        """Get the base form (lemma) of a word."""
        return self.morph.parse(word)[0].normal_form

    def get_pos(self, word: str) -> str:
        """Get the part of speech of a word."""
        return self.morph.parse(word)[0].tag.POS

    def count_syllables(self, word: str) -> int:
        """Count syllables in a Russian word."""
        return sum(1 for letter in word.lower() if letter in self.vowels)

    def get_word_frequency(self, text: str, exclude_stopwords: bool = True, use_lemmas: bool = True) -> List[Tuple[str, int]]:
        """Get word frequency sorted by count."""
        words = self.get_words(text)
        if exclude_stopwords:
            words = [w for w in words if w not in self.stopwords]
        if use_lemmas:
            words = [self.get_lemma(w) for w in words]
        return Counter(words).most_common()

    def calculate_coverage(self, word_frequencies: List[Tuple[str, int]], target_words: int = 100) -> Dict:
        """Calculate the coverage achieved by learning the top N words."""
        total_words = sum(count for _, count in word_frequencies)
        cumulative_count = 0
        
        # Take only the specified number of top words
        top_words = word_frequencies[:target_words]
        cumulative_count = sum(count for _, count in top_words)
        
        return {
            'target_words': target_words,
            'coverage_achieved': cumulative_count / total_words,
            'total_unique_words': len(word_frequencies),
            'total_word_occurrences': total_words,
            'cumulative_frequencies': [
                (i + 1, sum(count for _, count in word_frequencies[:i+1]) / total_words)
                for i in range(min(target_words, len(word_frequencies)))
            ]
        }

    def get_pos_distribution(self, text: str) -> Dict[str, int]:
        """Get distribution of parts of speech."""
        words = self.get_words(text)
        pos_counts = Counter()
        
        for word in words:
            pos = self.get_pos(word)
            if pos:  # Some words might not have a clear POS
                pos_counts[pos] += 1
            
        return dict(pos_counts.most_common())

    def analyze_text(self, text: str) -> Dict:
        """Perform comprehensive analysis of the text."""
        words = self.get_words(text)
        word_count = len(words)
        
        # Get lemmatized word frequencies and coverage
        word_frequencies = self.get_word_frequency(text, use_lemmas=True)
        common_words = word_frequencies[:100]
        coverage_stats = self.calculate_coverage(word_frequencies, 100)
        
        # Calculate word and sentence statistics
        unique_words = len(set(words))
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        total_syllables = sum(self.count_syllables(word) for word in words)
        avg_syllables = total_syllables / word_count if word_count > 0 else 0
        
        # Get parts of speech distribution
        pos_dist = self.get_pos_distribution(text)
        
        # Get lemma to word form mapping for common words
        common_lemmas = {}
        for lemma, count in common_words:
            # Find original word forms for this lemma
            word_forms = set()
            for word in words:
                if self.get_lemma(word) == lemma:
                    word_forms.add(word)
            common_lemmas[lemma] = list(word_forms)

        return {
            'total_words': word_count,
            'unique_words': unique_words,
            'vocabulary_richness': unique_words / word_count if word_count > 0 else 0,
            'avg_word_length': round(avg_word_length, 2),
            'avg_syllables': round(avg_syllables, 2),
            'total_syllables': total_syllables,
            'most_common_lemmas': common_words,
            'lemma_forms': common_lemmas,
            'pos_distribution': pos_dist,
            'coverage_stats': coverage_stats,
            'longest_words': sorted(set(words), key=len, reverse=True)[:10]
        }

    def save_analysis_to_file(self, analysis: Dict, output_path: str):
        """Save analysis results to a text file."""
        pos_names = {
            'NOUN': 'Noun',
            'VERB': 'Verb',
            'ADJF': 'Adjective',
            'ADJS': 'Short Adjective',
            'ADVB': 'Adverb',
            'PREP': 'Preposition',
            'CONJ': 'Conjunction',
            'PRTF': 'Participle',
            'PRTS': 'Short Participle',
            'INFN': 'Infinitive',
            'PRCL': 'Particle',
            'INTJ': 'Interjection'
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Text Analysis Results ===\n\n")
            f.write(f"Total words: {analysis['total_words']}\n")
            f.write(f"Unique words: {analysis['unique_words']}\n")
            f.write(f"Vocabulary richness: {analysis['vocabulary_richness']:.2%}\n")
            f.write(f"Average word length: {analysis['avg_word_length']} characters\n")
            f.write(f"Average syllables per word: {analysis['avg_syllables']}\n")
            
            f.write("\nMost frequent lemmas (base forms):\n")
            for lemma, count in analysis['most_common_lemmas']:
                forms = analysis['lemma_forms'].get(lemma, [])
                f.write(f"  {lemma} ({count} occurrences)\n")
                if forms:
                    f.write(f"    Word forms found: {', '.join(forms)}\n")
            
            f.write("\nParts of speech distribution:\n")
            for pos, count in analysis['pos_distribution'].items():
                pos_name = pos_names.get(pos, pos)
                percentage = count / analysis['total_words'] * 100
                f.write(f"  {pos_name}: {count} ({percentage:.1f}%)\n")
            
            f.write("\nWord Coverage Analysis:\n")
            coverage = analysis['coverage_stats']
            f.write(f"  Coverage with top {coverage['target_words']} words: {coverage['coverage_achieved']:.2%}\n")
            f.write(f"  Total unique words: {coverage['total_unique_words']}\n")
            f.write(f"  Total word occurrences: {coverage['total_word_occurrences']}\n")
            
            f.write("\nCumulative Coverage by Word Count:\n")
            for words, coverage in coverage['cumulative_frequencies']:
                if words % 10 == 0 or words == 1:  # Show at word 1 and every 10 words
                    f.write(f"  Top {words:3d} words: {coverage:.2%}\n")
            
            f.write("\nLongest words:\n")
            for word in analysis['longest_words']:
                f.write(f"  {word} ({len(word)} characters)\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze Russian text from EPUB file')
    parser.add_argument('epub_path', type=str, help='Path to EPUB file')
    parser.add_argument('--output', '-o', type=str, help='Path to output file for analysis results', 
                      default='analysis_results.txt')
    args = parser.parse_args()

    if not Path(args.epub_path).exists():
        print(f"Error: File '{args.epub_path}' not found.")
        return

    analyzer = RussianTextAnalyzer()

    try:
        print("Extracting text from EPUB...")
        text = analyzer.extract_text_from_epub(args.epub_path)
        
        print("Analyzing text...")
        results = analyzer.analyze_text(text)
        
        analyzer.save_analysis_to_file(results, args.output)
        print(f"\nAnalysis complete! Results saved to {args.output}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()