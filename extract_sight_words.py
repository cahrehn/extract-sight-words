import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
from collections import Counter
from typing import Dict, List, Union
import argparse
import csv
import os

def read_epub(epub_path: str) -> str:
    """Read and extract text content from an EPUB file."""
    book = epub.read_epub(epub_path)
    text = []
    
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Parse HTML content
        soup = BeautifulSoup(item.content, 'html.parser')
        # Extract text and remove HTML tags
        text.append(soup.get_text())
    
    return ' '.join(text)

def read_text_file(file_path: str) -> str:
    """Read content from a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def process_text(text: str) -> List[str]:
    """Clean and tokenize text into words."""
    # Convert to lowercase and split into words
    text = text.lower()
    # Remove punctuation and split into words
    words = re.findall(r'\b\w+\b', text)
    return words

def get_cumulative_frequencies(word_counts: Counter, total_words: int) -> Dict[str, float]:
    """Calculate cumulative frequencies for each word."""
    # Sort words by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    cumulative_freq = {}
    cumulative_sum = 0
    
    for word, count in sorted_words:
        cumulative_sum += count
        cumulative_freq[word] = (cumulative_sum / total_words) * 100
        
    return cumulative_freq

def get_words_up_to_percentage(word_counts: Counter, target_percentage: float) -> List[tuple]:
    """Get words that cumulatively account for the target percentage of total words."""
    total_words = sum(word_counts.values())
    cumulative_freq = get_cumulative_frequencies(word_counts, total_words)
    
    result = []
    for word, cum_percent in cumulative_freq.items():
        result.append((word, word_counts[word], cum_percent))
        if cum_percent >= target_percentage:
            break
            
    return result

def save_results_to_csv(results: List[tuple], output_path: str):
    """Save just the words from the results to a CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for word, _, _ in results:
            writer.writerow([word])

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Analyze word frequencies in text or EPUB files')
    parser.add_argument('file_path', help='Path to the input file (EPUB or text)')
    parser.add_argument('percentage', type=float, help='Target cumulative percentage (0-100)')
    args = parser.parse_args()
    
    # Read file based on extension
    if args.file_path.lower().endswith('.epub'):
        text = read_epub(args.file_path)
    else:
        text = read_text_file(args.file_path)
    
    # Process text and get word counts
    words = process_text(text)
    word_counts = Counter(words)
    total_words = sum(word_counts.values())
    unique_words = len(word_counts)
    
    # Get words up to target percentage
    results = get_words_up_to_percentage(word_counts, args.percentage)
    
    # Create output CSV filename from input filename
    base_name = os.path.splitext(args.file_path)[0]
    csv_path = f"{base_name}_top_words.csv"
    
    # Save result words to CSV
    save_results_to_csv(results, csv_path)
    
    # Print results
    print(f"\nAnalyzing text containing {total_words:,} total words ({unique_words:,} unique words)")
    print(f"Words accounting for {args.percentage}% of the text:")
    print("\n#\tWord\t\tCount\t\tCumulative %")
    print("-" * 45)
    for i, (word, count, cum_percent) in enumerate(results, 1):
        print(f"{i}\t{word:<15}{count:<15}{cum_percent:.2f}%")
    
    print(f"\nTop words have been saved to: {csv_path}")

if __name__ == "__main__":
    main()