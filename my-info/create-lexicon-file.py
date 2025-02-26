import os
import json
from phonemizer import phonemize
import re

# Load the config file
with open('/content/vits/configs/vctk_base.json', 'r') as f:
    config = json.load(f)

# Load words from the downloaded file
with open('english_words.txt', 'r') as f:
    all_words = [line.strip() for line in f]

# Take a subset of words to make processing manageable
# You can adjust this number based on your needs
word_list = all_words[:10000]  # First 10,000 words

print(f"Generating lexicon for {len(word_list)} words...")

# Process words in batches to avoid memory issues
batch_size = 500
lexicon = {}

for i in range(0, len(word_list), batch_size):
    batch = word_list[i:i+batch_size]
    print(f"Processing batch {i//batch_size + 1}/{(len(word_list) + batch_size - 1)//batch_size}")
    
    # Phonemize the batch
    phonemized = phonemize(
        batch,
        language='en-us',
        backend='espeak',
        strip=True,
        preserve_punctuation=True,
        with_stress=True
    )
    
    # Process the phonemized output
    for word, phones in zip(batch, phonemized):
        # Clean up the phonemes to match the model's format
        phones = re.sub(r'[\,\.\?\!\-\;\:\"\"\%\'\"\\(\)\[\]\{\}]', '', phones)
        
        # Convert the phonemes to the required format
        # First ensure phones is a string
        if isinstance(phones, list):
            phones = ' '.join(phones)
            
        # Replace spaces with a temporary marker, then split into characters, then replace the marker back
        phones = ' '.join(list(phones.replace(' ', '|'))).replace('|', ' ')
        
        lexicon[word.lower()] = phones

# Write to lexicon.txt
with open('lexicon.txt', 'w') as f:
    for word, phones in lexicon.items():
        f.write(f"{word} {phones}\n")

print(f"Generated lexicon.txt with {len(lexicon)} entries")
print("Sample entries:")
!head -10 lexicon.txt