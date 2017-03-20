#!/bin/bash

# This script creates a decoding graph for all entries in a Kaldi data directory
# text file. Format for each line is:
#   <UTTID> <prompt of many words>
# The graphs are created in subdirectories of the given model directory.
# An .scp file is created in the data directory, which gives for each uttid
# the corresponding graph, in the format:
#   <UTTID> <path-to-HCLG.fst>

set -e -u

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <dictsrcdir> <modeldir> <datadir> <workdir>" >&2 
  exit 1
fi

dictsrcdir="$1"
modeldir="$2"
datadir="$3"
workdir="$4"

required="$datadir/text"
for f in $required; do
  [ ! -f "$f" ] && echo "$0 expected $f to exist" >&2 && exit 1;
done

graphsdir="$modeldir/graphs_mtlm_"$(basename "$datadir")
graphsscp="$graphsdir/graphs.scp"
rm -f "$graphsscp"
cat "$datadir/text" | while read promptline; do
  uttid=$(echo "$promptline" | awk '{print $1}' )
  prompt=$(echo "$promptline" | cut -f 2- -d " " )
  echo "Processing: $uttid"
  promptdir="$workdir/$uttid"
  graphdir="$graphsdir/$uttid"
  mkdir -p "$promptdir"
  echo "$prompt" > "$promptdir"/prompt.txt
  kaldi-scripts/make_one_decode_graph.sh "$dictsrcdir" "$modeldir" "$promptdir" "$graphdir"
  pathtograph="$graphdir/HCLG.fst"
  [ ! -f "$pathtograph" ] && echo "Looks like graph creation for $pathtograph failed" >&2 && exit 1;
  echo "$uttid $pathtograph" >> "$graphsscp"
done
