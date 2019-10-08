#!/bin/bash

#Takes a hypothesis indexed by uttid
#And an directory of annotation fsts from make_annotation_fsts.sh
#And prints an annotation of miscues

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <annotation-fst-dir> <hyp-text>"
  exit 65
fi

fstdir="$1"
hyptext="$2"

[ -f ./path.sh ] && . ./path.sh

wordstxt="$fstdir/words.txt"

while read hypline; do
  uttid=$(echo "$hypline" | cut -d " " -f 1 )
  if [ "$hypline" = "$uttid" ]; then
    continue
  fi
  hyp=$(echo "$hypline" | cut -d " " -f 2- )
  echo -n "$uttid " 
  echo "$hyp" |\
    miscue-tolerant-lm-fst/utt2fst.py |\
    fstcompile --isymbols="$wordstxt" --osymbols="$wordstxt" |\
    fstcompose - "$fstdir/$uttid.key.fst" |\
    fstproject --project_output |\
    fstprint --isymbols="$wordstxt" --osymbols="$wordstxt" |\
    miscue-tolerant-lm-fst/fst2utt.py
done < "$hyptext"
