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


dictsrcdir="$1"

workdir="$3"
promptfile="$3"/prompt
tmpdir="$3"/tmp
graphdir="$4"

[ ! -f "$promptfile" ] && echo "Did not find prompt-file $promptfile " >&2 && exit 1;

mkdir -p "$workdir"/phones "$tmpdir" "$graphdir"

silprob=false
[ -f "$dictsrcdir"/lexiconp_silprob.txt ] && silprob=true

[ -f path.sh ] && . ./path.sh

! utils/validate_dict_dir.pl "$dictsrcdir" && \
  echo "Error validating directory $dictsrcdir" >&2 && exit 1;

kaldi-scripts/make_modified_lexicon.py "$dictsrcdir" "$tmpdir" "$promptfile"


