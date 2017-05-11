#!/bin/bash

# This script creates a decoding graph (HCLG) for a known text,
# using the miscue-tolerant-lm-fst for a language model.
# The lexicon and language model are created on the fly. 

set -e -u 

OOV="<SPOKEN_NOISE>"
keepwords="$OOV !SIL <NOISE>"
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <dict-src-dir> <model-dir> <work-dir> <graph-dir>"
    echo
    echo "Note: the work dir is assumed to contain a text file called prompt.txt"
    echo "and be a directory where the script may create any temporary files."
    echo "It may be the same directory as graph-dir, which is where the graph is output."
    exit 1;
fi


dictsrcdir="$1"
modeldir="$2"
workdir="$3"

langdir="$workdir"/lang
localdictsrc="$langdir"/dict
langtmpdir="$langdir"/tmp

promptfile="$workdir"/prompt.txt
graphdir="$4"


[ ! -f "$promptfile" ] && echo "Did not find prompt-file $promptfile " >&2 && exit 1;

mkdir -p "$langtmpdir" "$graphdir" "$localdictsrc"
trap "rm -rf $langtmpdir $localdictsrc $langdir" EXIT HUP INT PIPE TERM

[ -f path.sh ] && . ./path.sh

cp -a "$dictsrcdir"/* "$localdictsrc"
rm "$localdictsrc"/lexicon*.txt
miscue-tolerant-lm-fst/kaldi-scripts/make_utt_specific_lexicon.py --keep "$keepwords" --oov "$OOV" "$dictsrcdir" "$workdir" "$promptfile"
mv "$workdir"/lexicon*.txt "$localdictsrc"
utils/prepare_lang.sh "$localdictsrc" "$OOV" "$langtmpdir" "$langdir"

cat "$workdir"/uniqued_prompt.txt | miscue-tolerant-lm-fst/make_one_miscue_tolerant_lm.py \
  --homophones "$workdir"/homophones.txt --rubbish-label "$OOV" \
  | utils/eps2disambig.pl |\
  fstcompile --isymbols="$langdir"/words.txt --osymbols="$langdir"/words.txt |\
  fstarcsort --sort_type=ilabel > "$langdir"/G.fst

utils/mkgraph.sh "$langdir" "$modeldir" "$graphdir"
