#!/bin/bash

cmd=run.pl
stage=0
beam=6
word_ins_penalty=0.0
lmwt=13.0

. path.sh
. parse_options.sh


if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <lang-dir|graph-dir> <decode-dir>"
  exit 1
fi

lang_or_graph=$1
dir=$2

symtab=$lang_or_graph/words.txt

if [ $stage -le 0 ]; then
  $cmd $dir/log/best_path.${lmwt}.log \
    lattice-scale --inv-acoustic-scale=${lmwt} "ark:gunzip -c $dir/lat.*.gz|" ark:- \| \
    lattice-add-penalty --word-ins-penalty=${word_ins_penalty} ark:- ark:- \| \
    lattice-best-path --word-symbol-table=${symtab} ark:- ark,t:- \| \
    utils/int2sym.pl -f 2- ${symtab} '>' $dir/output.${lmwt}.${word_ins_penalty}.txt || exit 1;
fi
