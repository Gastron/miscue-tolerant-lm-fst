#!/bin/bash
# Compiles actual graphs
# Mostly should be used as a subtask of graphs_for_text.sh
set -e -u
set -o pipefail

scale_opts="--transition-scale=1.0 --self-loop-scale=0.1"
lm_opts="--correct-word-boost 1.0"

. path.sh
. parse_options.sh 

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <model-dir> <langdir> <promptstbl> <out>"
  echo "NOTE: <out> should be a kaldi style <wspecifier>"
  echo " e.g. ark,scp:data/train/mtlm_graphs/HCLG.fsts,data/train/mtlm_graphs/HCLG.fsts.scp"
  exit 1 
fi

langdir=$1
modeldir=$2
promptstbl=$3
out=$4

#The while loop makes a text format G FST 
#for each utterance in $textfile, then and echoes that:
cat "$promptstbl" | while read promptline; do
  promptid=$(echo "$promptline" | awk '{print $1}' )
  prompt=$(echo "$promptline" | cut -f 2- -d " " )
  echo "$promptid" #Header
  echo "$prompt"  | miscue-tolerant-lm-fst/make_one_miscue_tolerant_lm.py \
    $lm_opts |\
    utils/eps2disambig.pl |\
    utils/sym2int.pl -f 3-4 "$langdir"/words.txt >&1
  echo #empty line as separator
done |\
  compile-train-graphs-fsts $scale_opts --read-disambig-syms="$langdir"/phones/disambig.int \
    "$modeldir"/tree $modeldir/final.mdl "$langdir"/L_disambig.fst ark:- \
    $out
