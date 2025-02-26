#!/usr/bin/env python3
# Copyright    2025  Xiaomi Corp.        (authors: Fangjun Kuang)
# This is a shebang line that specifies the script should be run with Python 3

import json  # Imports the json module for handling JSON data
from typing import List, Tuple  # Imports type hints for lists and tuples

from misaki import zh  # Imports the zh module from misaki package for Chinese text processing
from pypinyin import load_phrases_dict, phrases_dict, pinyin_dict  # Imports pypinyin modules for Chinese pinyin conversion

# Defines a custom dictionary for Chinese words with their pinyin representations
# Each word is mapped to a list of syllables with tone numbers
user_dict = {
    "还田": [["huan2"], ["tian2"]],  # Pinyin for "还田" with correct tones
    "行长": [["hang2"], ["zhang3"]],  # Pinyin for "行长" with correct tones
    "银行行长": [["yin2"], ["hang2"], ["hang2"], ["zhang3"]],  # Pinyin for "银行行长" with correct tones
}

load_phrases_dict(user_dict)  # Loads the custom dictionary into pypinyin

phrases_dict.phrases_dict.update(**user_dict)  # Updates the phrases dictionary with our custom entries


def generate_english_lexicon(kind: str):
    """Generates an English pronunciation lexicon based on the specified accent (US or GB)"""
    assert kind in ("us", "gb"), kind  # Ensures the kind parameter is either "us" or "gb"
    
    # Dictionary of user-defined pronunciations for specific words
    # If you want to add new words, please add them to the user_defined dict.
    user_defined = {
        "Kokoro": "kˈOkəɹO",  # Custom pronunciation for "Kokoro"
        "Misaki": "misˈɑki",  # Custom pronunciation for "Misaki"
    }

    # Creates a lowercase version of the user-defined dictionary for case-insensitive matching
    user_defined_lower = dict()
    for k, v in user_defined.items():
        user_defined_lower[k.lower()] = v

    # Loads the "gold" standard pronunciations from a JSON file
    with open(f"./{kind}_gold.json", encoding="utf-8") as f:
        gold = json.load(f)

    # Loads the "silver" standard pronunciations from a JSON file
    with open(f"./{kind}_silver.json", encoding="utf-8") as f:
        silver = json.load(f)

    # Combines silver and gold dictionaries, with gold taking precedence
    # words in us_gold has a higher priority than those in s_silver, so
    # we put us_gold after us_silver below
    english = {**silver, **gold}

    # Processes the combined dictionary to create the final lexicon
    lexicon = dict()
    for k, v in english.items():
        k_lower = k.lower()  # Converts the word to lowercase

        # Skips words that are already in the user-defined dictionary
        if k_lower in user_defined_lower:
            print(f"{k} already exist in the user defined dict. Skip adding")
            continue

        # Handles different formats in the input dictionaries
        if isinstance(v, str):
            lexicon[k_lower] = v  # Direct string pronunciation
        else:
            assert isinstance(v, dict), (k, v)  # Ensures v is a dictionary
            assert "DEFAULT" in v, (k, v)  # Ensures the dictionary has a DEFAULT key
            lexicon[k_lower] = v["DEFAULT"]  # Uses the DEFAULT pronunciation

    # Returns the combined lexicon (user-defined + processed entries)
    return list(user_defined_lower.items()) + list(lexicon.items())


def generate_chinese_lexicon():
    """Generates a Chinese pronunciation lexicon using IPA (International Phonetic Alphabet)"""
    word_dict = pinyin_dict.pinyin_dict  # Gets the pinyin dictionary for single characters
    phrases = phrases_dict.phrases_dict  # Gets the pinyin dictionary for multi-character phrases

    g2p = zh.ZHG2P()  # Creates a Chinese grapheme-to-phoneme converter
    lexicon = []  # Initializes an empty lexicon

    # Processes single Chinese characters
    for key in word_dict:
        if not (0x4E00 <= key <= 0x9FFF):  # Checks if the character is in the CJK Unified Ideographs range
            continue
        w = chr(key)  # Converts the Unicode code point to a character
        tokens: str = g2p.word2ipa(w)  # Converts the character to IPA representation
        tokens = tokens.replace(chr(815), "")  # Removes the combining macron below character (U+032F)
        lexicon.append((w, tokens))  # Adds the character and its pronunciation to the lexicon

    # Processes multi-character phrases
    for key in phrases:
        tokens: str = g2p.word2ipa(key)  # Converts the phrase to IPA representation
        tokens = tokens.replace(chr(815), "")  # Removes the combining macron below character
        lexicon.append((key, tokens))  # Adds the phrase and its pronunciation to the lexicon
    
    return lexicon  # Returns the complete Chinese lexicon


def save(filename: str, lexicon: List[Tuple[str, str]]):
    """Saves the lexicon to a text file with space-separated phonemes"""
    with open(filename, "w", encoding="utf-8") as f:
        for word, phones in lexicon:
            tokens = " ".join(list(phones))  # Separates each phoneme with a space
            f.write(f"{word} {tokens}\n")  # Writes the word and its space-separated phonemes


def main():
    """Main function that generates and saves all lexicons"""
    us = generate_english_lexicon("us")  # Generates US English lexicon
    gb = generate_english_lexicon("gb")  # Generates GB (British) English lexicon
    zh = generate_chinese_lexicon()  # Generates Chinese lexicon

    save("lexicon-us-en.txt", us)  # Saves US English lexicon to file
    save("lexicon-gb-en.txt", gb)  # Saves GB English lexicon to file
    save("lexicon-zh.txt", zh)  # Saves Chinese lexicon to file


if __name__ == "__main__":
    main()  # Executes the main function when the script is run directly
