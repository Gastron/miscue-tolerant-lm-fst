#!/bin/bash

cmd=run.pl
stage=0
beam=6
word_ins_penalty=0.0
lmwt=13.0

. path.sh
. parse_options.sh


if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <data-dir> <lang-dir|graph-dir> <decode-dir>"
  echo "Data directory is only needed for sorting the output"
  exit 1
fi

data=$1
lang_or_graph=$2
dir=$3

symtab=$lang_or_graph/words.txt

if [ $stage -le 0 ]; then
  $cmd $dir/log/best_path.${lmwt}.log \
    lattice-scale --inv-acoustic-scale=${lmwt} "ark:gunzip -c $dir/lat.*.gz|" ark:- \| \
    lattice-add-penalty --word-ins-penalty=${word_ins_penalty} ark:- ark:- \| \
    lattice-best-path --word-symbol-table=${symtab} ark:- ark,t:- \| \
    utils/int2sym.pl -f 2- ${symtab} '>' $dir/output.${lmwt}.${word_ins_penalty}.txt || exit 1;
fi

if [ $stage -le 1 ]; then
  utils/filter_scp.pl $dir/output.${lmwt}.${word_ins_penalty}.txt $data/text > $dir/prompts.filt.txt
  sort $dir/prompts.filt.txt -o $dir/prompts.filt.txt
  sort $dir/output.${lmwt}.${word_ins_penalty}.txt -o $dir/output.${lmwt}.${word_ins_penalty}.txt
fi
