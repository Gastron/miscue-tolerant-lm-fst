#!/bin/bash

#Takes a reference text and a hypothesis (both indexed by uttid)
#And prints an annotation of miscues

set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <langdir> <reftext> <hyptext>"
  exit 65
fi

langdir="$1"
reftext="$2"
hyptext="$3"

tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT HUP INT PIPE TERM

declare -A refs #key-value store
while read promptline; do
  uttid=$(cut -d " " -f 1 "$promptline")
  prompt=$(cut -d " " -f 2- "$promptline")
  keyfst="$tmpdir/uttid.key.fst"
  echo "$prompt" |\
    miscue-tolerant-lm-fst/make_miscue_annotation_transducer.py \
    --rubbish-label $(cat "$langdir/rubbish") --truncation-label $(cat "$langdir/truncation_symbol.txt") \
    --homophones "$langdir/homophones.txt" --truncations "$langdir/truncations.txt" |\
    fstcompile --isymbols="$wordstxt" --osymbols="$wordstxt" > "$keyfst"
  refs["$uttid"]="$keyfst"
done < $reftext

while read hypline; do
  uttid=$(cut -d " " -f 1 "$hypline")
  hyp=$(cut -d " " -f 2- "$hypline")
  echo -n "$uttid" 
  echo "$hyp" |\
    miscue-tolerant-lm-fst/utt2fst.py \
    fstcompile --isymbols="$wordstxt" --osymbols="$wordstxt" |\
    fstcompose - ${refs["$uttid"]} |\
    fstproject --project_output |\
    fstprint --isymbols="$wordstxt" --osymbols="$wordstxt" |\
    miscue-tolerant-lm-fst/fst2utt.py
done
