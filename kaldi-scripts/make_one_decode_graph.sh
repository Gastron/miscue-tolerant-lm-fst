#!/bin/bash

# This script creates a decoding graph (HCLG) for a known text,
# using the miscue-tolerant-lm-fst for a language model.
# The lexicon and language model are created on the fly. 

set -e -u 

OOV="<SPOKEN_NOISE>"
truncation_symbol="[TRUNC]:"
scale_opts="--transition-scale 1.0 --self-loop-scale 0.1"
correct_boost=1.0
lang_opts=""
while getopts "o:t:s:b:l:" OPTNAME; do
  case "$OPTNAME" in
    o) OOV="$OPTARG";;
    t) truncation_symbol="$OPTARG";;
    s) scale_opts="$OPTARG";;
    b) correct_boost="$OPTARG";;
    l) lang_opts="$OPTARG";;
  esac
done
shift $((OPTIND - 1))

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
miscue-tolerant-lm-fst/kaldi-scripts/make_utt_specific_lexicon.py --oov "$OOV" --truncation-label "$truncation_symbol" "$dictsrcdir" "$workdir" "$promptfile"
mv "$workdir"/lexicon*.txt "$localdictsrc"
utils/prepare_lang.sh $lang_opts "$localdictsrc" "$OOV" "$langtmpdir" "$langdir"
cp "$workdir"/{homophones,truncations}.txt "$langdir"
echo "$OOV" > "$langdir"/rubbish
echo "$truncation_symbol" > "$langdir"/truncation_symbol

cat "$workdir"/uniqued_prompt.txt | miscue-tolerant-lm-fst/make_one_miscue_tolerant_lm.py \
  --homophones "$langdir"/homophones.txt --rubbish-label "$OOV" \
  --correct-word-boost "$correct_boost" \
  --truncations "$langdir"/truncations.txt --truncation-label "$langdir"/truncation_symbol \
  | utils/eps2disambig.pl |\
  fstcompile --isymbols="$langdir"/words.txt --osymbols="$langdir"/words.txt |\
  fstarcsort --sort_type=ilabel > "$langdir"/G.fst

utils/mkgraph.sh $scale_opts "$langdir" "$modeldir" "$graphdir"
