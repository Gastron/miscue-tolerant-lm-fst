#!/bin/bash
set -e -u
set -o pipefail

OOV="<SPOKEN_NOISE>"
truncation_symbol="[TRUNC]:"
silprob=0.7 #the default is 0.5, this should reflect higher hesitation time.

. path.sh
. parse_options.sh

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <dictsrcdir> <datadir> <outdir>"
  echo "Options:"
  echo "--OOV <OOV>                  Entry to use as pronunciation for oov words, default: <SPOKEN_NOISE>"
  echo "-truncation_symbol <truncation-prefix>   Prefix for truncated words in lexicon, default: [TRUNC]:" 
  exit 1
fi

dictsrcdir="$1"
datadir="$2"
outdir="$3"

textfile="$datadir/text" 
required="$textfile"
for f in $required; do
  [ ! -f "$f" ] && echo "$0 expected $f to exist" >&2 && exit 1;
done

langdir="$outdir"
localdictsrc="$langdir"/dict
langtmpdir="$langdir"/tmp

mkdir -p "$langtmpdir" "$localdictsrc"
trap "rm -rf $langtmpdir $localdictsrc" EXIT HUP INT PIPE TERM

[ -f path.sh ] && . ./path.sh

cp -a "$dictsrcdir"/* "$localdictsrc"
rm "$localdictsrc"/lexicon*.txt

miscue-tolerant-lm-fst/kaldi-scripts/make_extended_lexicon.py \
  --oov "$OOV" --truncation-label "$truncation_symbol" \
  "$dictsrcdir" "$localdictsrc" "$textfile"
utils/prepare_lang.sh --sil-prob "$silprob" "$localdictsrc" "$OOV" "$langtmpdir" "$langdir"
cp "$localdictsrc"/{homophones,truncations}.txt "$langdir"
echo "$OOV" > "$langdir"/rubbish
echo "$truncation_symbol" > "$langdir"/truncation_symbol
