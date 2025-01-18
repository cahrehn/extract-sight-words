# Extract Sight Words

This Python script analyzes word frequencies in text and EPUB files. It identifies the most frequently occurring words that make up a specified percentage of the total text and outputs both a console summary and a CSV file containing these key words.

## Features

- Supports both plain text (.txt) and EPUB (.epub) files
- Calculates word frequencies and cumulative percentages
- Shows how many unique words compose a given percentage of the text
- Outputs results to both console and CSV
- Handles text cleaning and tokenization
- Case-insensitive analysis

## Requirements

```bash
pip install ebooklib beautifulsoup4
```

## Usage

```bash
python extract_sight_words.py <file_path> <percentage>
```

### Arguments

- `file_path`: Path to your input file (either .txt or .epub)
- `percentage`: Target percentage of text to analyze (0-100)

### Example

```bash
python extract_sight_words.py mybook.epub 50
```

This will:
1. Analyze mybook.epub
2. Find the most frequent words that make up 50% of the text
3. Display a frequency table in the console
4. Create mybook_top_words.csv containing these words

### Sample Output

```
Analyzing text containing 100,000 total words (8,432 unique words)
Words accounting for 50% of the text:

#       Word            Count           Cumulative %
---------------------------------------------
1       the             5,230           5.23%
2       and             4,891           10.12%
3       to              4,562           14.68%
...

Top words have been saved to: mybook_top_words.csv
```

## Output Files

The script generates a CSV file named `[input_filename]_top_words.csv` containing the words that make up your specified percentage of the text, ordered by frequency.
