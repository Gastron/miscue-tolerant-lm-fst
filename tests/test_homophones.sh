#!/bin/bash
# Test homophones by making an fst with them.
# Requires openfst and dot (graphviz).
# Prints a info and draws the output.

set -eu
set -o pipefail

test_string="two carat carrot too"
sym_table="tests/words_table.txt"
outname=tests/$(echo $test_string | sed -r "s/ /_/g")

echo "Testing homophones"
echo "Test string: $test_string"
echo


echo $test_string | ./make_one_miscue_tolerant_lm.py --homophones tests/homophones.txt |\
    fstcompile --isymbols=$sym_table --osymbols=$sym_table > ${outname}.fst

echo "Here is some info about the WFST:"
fstinfo ${outname}.fst

# If Kaldi is on the path, check fstisstochastic
if which fstisstochastic; then
    fstisstochastic ${outname}.fst
fi

fstdraw --isymbols=$sym_table --osymbols=$sym_table ${outname}.fst ${outname}.dot
dot -Grotate=0 -Tsvg -O ${outname}.dot
mv ${outname}.dot.svg ${outname}.svg

# Remove tempfiles:
rm $outname.dot

echo
echo "To view the resulting WFST, simply open $outname.svg"
echo "e.g. xdg-open $outname.svg"
