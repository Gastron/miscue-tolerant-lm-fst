#!/bin/bash
# Test make_one_miscue_tolerant_lm by making an fst with it.
# Requires openfst and dot (graphviz).
# Prints a info and draws the output.

test_string="the cat and the dog"
sym_table="tests/words_table.txt"
outname=tests/$(echo $test_string | sed -r "s/ /_/g")

echo "Testing make_one_miscue_tolerant_lm.py"
echo "Test string: $test_string"
echo


echo $test_string | ./make_one_miscue_tolerant_lm.py |\
    fstcompile --isymbols=$sym_table --osymbols=$sym_table > ${outname}.fst

echo "Here is some info about the WFST:"
fstinfo ${outname}.fst

# If Kaldi is on the path, check fstisstochastic
find_kaldi=$(which fstisisstochastic)
[ $? -ne 0 ] && fstisstochastic ${outname}.fst
fstdraw --isymbols=$sym_table --osymbols=$sym_table ${outname}.fst ${outname}.dot
dot -Grotate=0 -Tpng -O ${outname}.dot
mv ${outname}.dot.png ${outname}.png

# Remove tempfiles:
rm $outname.dot

echo
echo "To view the resulting WFST, simply open $outname.png"
echo "e.g. xdg-open $outname.png"
