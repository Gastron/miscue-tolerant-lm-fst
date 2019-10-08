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

stage=0
nj=16
cmd=run.pl
scale_opts="--transition-scale=1.0 --self-loop-scale=0.1"
correct_boost=1.0
cleanup=true

. ./path.sh
. parse_options.sh || exit 1;

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <langdir> <modeldir> <datadir> <outdir>" 
  echo "Options:"
  echo "--scale_opts <scale-opts>           Scale options to pass to kaldi. default:"
  echo "                            --transition-scale=1.0 --self-loop-scale=0.1"
  echo "--correct_boost <float>                Multiply the probability of the correct words by float, default 1.0 (no boost)"
  exit 1
fi

langdir="$1"
modeldir="$2"
datadir="$3"
outdir="$4"
mkdir -p "$outdir"/log

required="$datadir/text $datadir/utt2spk $modeldir/final.mdl $modeldir/tree $langdir/truncation_symbol $langdir/rubbish $langdir/homophones.txt"
for f in $required; do
  [ ! -f "$f" ] && echo "$0 expected $f to exist" >&2 && exit 1;
done

if [ $stage -le 1 ]; then
  #Map uttids to unique prompts:
  utils/split_data.sh $datadir $nj
  $cmd JOB=1:$nj $outdir/log/get_prompt_ids.JOB.log \
    miscue-tolerant-lm-fst/kaldi-scripts/map_utts_to_prompts.sh \
    $datadir/split$nj/JOB/text \
    $outdir/log/utt2promptcrc.JOB \
    $outdir/log/prompts.JOB.scp
  cat $outdir/log/utt2promptcrc.* > $outdir/utt2promptcrc
  cat $outdir/log/prompts.*.scp | sort -u > $outdir/prompts.scp
fi

if [ $stage -le 2 ]; then
  #Compile graphs (NOTE: now they map to promptcrcs):
  $cmd JOB=1:$nj $outdir/log/compile_graphs.JOB.log \
    miscue-tolerant-lm-fst/make_miscue_tolerant_lms.py \
      --kaldi-style \
      --rubbish-label $langdir/rubbish \
      --truncation-label $langdir/truncation_symbol \
      --truncations $langdir/truncations.txt \
      --homophones $langdir/homophones.txt \
      $outdir/log/prompts.JOB.scp \|\
    utils/eps2disambig.pl \|\
    utils/sym2int.pl -f 3-4 "$langdir"/words.txt \|\
    compile-train-graphs-fsts $scale_opts \
      --read-disambig-syms="$langdir"/phones/disambig.int \
      "$modeldir"/tree $modeldir/final.mdl "$langdir"/L_disambig.fst ark:- \
      ark,scp:$outdir/HCLG.JOB.fsts,$outdir/log/HCLG.JOB.fsts.per_prompt.scp
  cat $outdir/log/HCLG.*.fsts.per_prompt.scp > $outdir/HCLG.fsts.per_prompt.scp
fi

if [ $stage -le 3 ]; then
  #Now map the uttids to the correct fst:
  utils/apply_map.pl -f 2 "$outdir"/HCLG.fsts.per_prompt.scp \
    <$outdir/utt2promptcrc > $outdir/HCLG.fsts.scp

  cp -a "$langdir"/* "$outdir"
  am-info --print-args=false "$modeldir/final.mdl" |\
   grep pdfs | awk '{print $NF}' > "$outdir/num_pdfs"

  if [ $cleanup = true ]; then
    rm $outdir/log/utt2promptcrc.* $outdir/log/prompts.*.scp \
      $outdir/utt2promptcrc $outdir/prompts.scp
  fi
fi
