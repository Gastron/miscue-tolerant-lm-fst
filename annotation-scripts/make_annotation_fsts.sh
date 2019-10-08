#!/bin/bash

#Takes a reference text indexed by uttid
#And creates a directory of FSTs which can be used to annotate miscues.

set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <langdir> <reftext> <outdir>"
  exit 65
fi

langdir="$1"
reftext="$2"
fstdir="$3"
mkdir -p "$fstdir"

[ -f ./path.sh ] && . ./path.sh

wordstxt="$fstdir/words.txt"
cat miscue-tolerant-lm-fst/kaldi-scripts/eps.txt\
  "$langdir/words.txt" \
  miscue-tolerant-lm-fst/kaldi-scripts/extra_special_labels.txt |\
  awk '{print $1 " " NR-1}' > "$wordstxt"

while read promptline; do
  uttid=$(echo "$promptline" | cut -d " " -f 1 )
  prompt=$(echo "$promptline" | cut -d " " -f 2- )
  keyfst="$fstdir/$uttid.key.fst"
  echo "$prompt" |\
    miscue-tolerant-lm-fst/make_miscue_annotation_transducer.py \
    --rubbish-label $(cat "$langdir/rubbish") --truncation-label $(cat "$langdir/truncation_symbol") \
    --homophones "$langdir/homophones.txt" --truncations "$langdir/truncations.txt" |\
    fstcompile --isymbols="$wordstxt" --osymbols="$wordstxt" > "$keyfst"
done < "$reftext"
