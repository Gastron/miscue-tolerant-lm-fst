#!/bin/bash

# This script creates a decoding graph (HCLG) for a known text,
# using the miscue-tolerant-lm-fst for a language model.
# The lexicon and language model are created on the fly. 

if [ "$#" -ne 3 ] then;
    echo "Usage: $0 <dict-src-dir> <model-dir> <work-dir> <graph-dir>"
    echo "Note: the work dir is assumed to contain a text file called prompt"
    echo "and be a directory where the script may create any temporary files."
    echo "It may be the same directory as graph-dir, which is where the graph is output."
    exit 1;
fi



