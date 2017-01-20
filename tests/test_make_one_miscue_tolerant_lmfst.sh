#!/bin/bash
# Test make_one_miscue_tolerant_lm by making an fst with it.
# Requires openfst and dot (graphviz).
# Prints a info and draws the output.

test_string="The cat and the dog"
sym_table="tests/words_table.txt"
outname=tests/momtlm

echo $test_string | ./make_one_miscue_tolerant_lm.py |\
    fstcompile --isymbols=$sym_table --osymbols=$sym_table > ${outname}.fst
fstinfo ${outname}.fst
fstdraw --isymbols=$sym_table --osymbols=$sym_table ${outname}.fst ${outname}.dot
dot -Tpng ${outname}.dot ${outname}.png
