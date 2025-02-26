#!/usr/bin/env bash
# Copyright    2025  Xiaomi Corp.        (authors: Fangjun Kuang)

# This script sets up and tests the Kokoro TTS system by downloading necessary models and resources.
# The -e flag causes the script to exit immediately if any command fails
# The -x flag prints each command before executing it, useful for debugging
# -e: exit immediately if a command exits with a non-zero status
# -x: print each command before executing it (useful for debugging)
# set -e: exit immediately if a command exits with a non-zero status
# set -x: print each command before executing it (useful for debugging)
set -ex

# Download the Kokoro ONNX model if it doesn't exist locally
# This is the main neural network model for the TTS system
# This line checks if the kokoro.onnx file exists in the current directory
# If the file doesn't exist (! -f), the code inside the if statement will execute
# to download the file from the GitHub repository
if [ ! -f kokoro.onnx ]; then
# The semicolon (;) in this line is used to separate the condition from the 'then' keyword
# In Bash, the semicolon acts as a command terminator, allowing multiple commands on one line
# Here it allows the condition [ ! -f kokoro.onnx ] and the 'then' keyword to be on the same line
# Without the semicolon, 'then' would need to be on a separate line
  # The model is sourced from taylorchu's GitHub repository
  curl -SL -O https://github.com/taylorchu/kokoro-onnx/releases/download/v0.2.0/kokoro.onnx
fi

# Download the configuration file for the Kokoro model if it doesn't exist locally
# This JSON file contains parameters and settings for the TTS model
if [ ! -f config.json ]; then
  # The config is sourced from Hugging Face's model repository
  curl -SL -O https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/config.json
fi

# This section defines voice identifiers for the TTS system
# The comments explain the naming convention:
# af -> American female
# am -> American male
# bf -> British female
# bm -> British male
# Additional voice types include other languages and accents
voices=(
af_alloy
af_aoede
af_bella
af_heart
af_jessica
af_kore
af_nicole
af_nova
af_river
af_sarah
af_sky
am_adam
am_echo
am_eric
am_fenrir
am_liam
am_michael
am_onyx
am_puck
am_santa
bf_alice
bf_emma
bf_isabella
bf_lily
bm_daniel
bm_fable
bm_george
bm_lewis
ef_dora
em_alex
ff_siwis
hf_alpha
hf_beta
hm_omega
hm_psi
if_sara
im_nicola
jf_alpha
jf_gongitsune
jf_nezumi
jf_tebukuro
jm_kumo
pf_dora
pm_alex
pm_santa
zf_xiaobei # 东北话 (Northeastern Chinese dialect)
zf_xiaoni
zf_xiaoxiao
zf_xiaoyi
zm_yunjian
zm_yunxi
zm_yunxia
zm_yunyang
)

# Create a directory to store voice model files
mkdir -p voices

# Download each voice model file if it doesn't exist locally
# These are speaker embedding files that give each voice its unique characteristics
for v in ${voices[@]}; do
  if [ ! -f voices/$v.pt ]; then
    curl -SL --output voices/$v.pt https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/$v.pt
  fi
done

# Run a script to add metadata to the models if it hasn't been done before
# The .done file acts as a flag to prevent repeated execution
if [ ! -f ./.add-meta-data.done ]; then
  python3 ./add_meta_data.py
  touch ./.add-meta-data.done
fi

# Download pronunciation dictionaries for American English (US)
# These files contain mappings between words and their pronunciations
# "gold" typically refers to high-quality, manually verified entries
if [ ! -f us_gold.json ]; then
  curl -SL -O https://raw.githubusercontent.com/hexgrad/misaki/refs/heads/main/misaki/data/us_gold.json
fi

# "silver" typically refers to automatically generated entries that are less verified
if [ ! -f us_silver.json ]; then
  curl -SL -O https://raw.githubusercontent.com/hexgrad/misaki/refs/heads/main/misaki/data/us_silver.json
fi

# Download pronunciation dictionaries for British English (GB)
if [ ! -f gb_gold.json ]; then
  curl -SL -O https://raw.githubusercontent.com/hexgrad/misaki/refs/heads/main/misaki/data/gb_gold.json
fi

if [ ! -f gb_silver.json ]; then
  curl -SL -O https://raw.githubusercontent.com/hexgrad/misaki/refs/heads/main/misaki/data/gb_silver.json
fi

# Generate tokens file if it doesn't exist
# This likely contains the vocabulary or tokenization information for the TTS system
if [ ! -f ./tokens.txt ]; then
  ./generate_tokens.py
fi

# Generate a Chinese lexicon file if it doesn't exist
# This maps Chinese characters to their pronunciations
if [ ! -f ./lexicon-zh.txt ]; then
  ./generate_lexicon.py
fi

# Generate a binary file containing voice information if it doesn't exist
# This is likely a more efficient format for the voice models during runtime
if [ ! -f ./voices.bin ]; then
  ./generate_voices_bin.py
fi

# Run a test script to verify the TTS system works correctly
./test.py
# List all files in the current directory with human-readable file sizes
ls -lh