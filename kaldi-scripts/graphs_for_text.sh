#!/bin/bash

# This script creates a decoding graph for all entries in a Kaldi data directory
# text file. Format for each line is:
#   <UTTID> <prompt of many words>
# The graphs are created in subdirectories of the given model directory.
# An .scp file is created in the data directory, which gives for each uttid
# the corresponding graph, in the format:
#   <UTTID> <path-to-HCLG.fst>

set -e -u
set -o pipefail

scale_opts="--transition-scale=1.0 --self-loop-scale=0.1"
correct_boost=1.0
while getopts "s:b:" OPTNAME; do
  case "$OPTNAME" in
    s) scale_opts="$OPTARG";;
    b) correct_boost="$OPTARG";;
  esac
done
shift $((OPTIND - 1))

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <langdir> <modeldir> <datadir> <outdir>" 
  echo "Options:"
  echo "-s <scale-opts>           Scale options to pass to kaldi. default:"
  echo "                            --transition-scale=1.0 --self-loop-scale=0.1"
  echo "-b <float>                Multiply the probability of the correct words by float, default 1.0 (no boost)"
  exit 1
fi

langdir="$1"
modeldir="$2"
datadir="$3"
outdir="$4"

textfile="$datadir/text" 
required="$textfile $modeldir/final.mdl $modeldir/tree $langdir/truncation_symbol $langdir/rubbish"
for f in $required; do
  [ ! -f "$f" ] && echo "$0 expected $f to exist" >&2 && exit 1;
done

#Retrieve the rubbish, truncation and homophone info if available:
rubbish_text=
[ -f "$langdir"/rubbish ] && rubbish_text="--rubbish-label "$(cat $langdir/rubbish)
truncation_text=
[ -f "$langdir"/truncation_symbol ] && truncation_text="--truncation-label "$(cat $langdir/truncation_symbol)" --truncations $langdir/truncations.txt"
homophone_text=
[ -f "$langdir"/homophones.txt ] && homophone_text="--homophones $langdir/homophones.txt"

[ -f path.sh ] && . ./path.sh

graphsdir="$outdir"
graphsscp="$graphsdir/HCLG.fsts.scp"
#Make sure dir exists but graphsscp does not:
mkdir -p "$graphsdir"
rm -f "$graphsscp"

#The while loop makes a text format G FST 
#for each utterance in $textfile, then and echoes that:
cat "$textfile" | while read promptline; do
  uttid=$(echo "$promptline" | awk '{print $1}' )
  prompt=$(echo "$promptline" | cut -f 2- -d " " )
  echo "$uttid" #Header
  echo "$prompt"  | miscue-tolerant-lm-fst/make_one_miscue_tolerant_lm.py --correct-word-boost $correct_boost \
    $rubbish_text \
    $truncation_text \
    $homophone_text |\
    utils/eps2disambig.pl |\
    utils/sym2int.pl -f 3-4 "$langdir"/words.txt >&1
  echo #empty line as separator
done |\
  compile-train-graphs-fsts --batch-size=500 $scale_opts --read-disambig-syms="$langdir"/phones/disambig.int \
    "$modeldir"/tree $modeldir/final.mdl "$langdir"/L_disambig.fst ark:- \
  ark,scp:"$graphsdir"/HCLG.fsts,"$graphsscp" 

cp -a "$langdir"/* "$graphsdir"
am-info --print-args=false "$modeldir/final.mdl" |\
 grep pdfs | awk '{print $NF}' > "$graphsdir/num_pdfs"
