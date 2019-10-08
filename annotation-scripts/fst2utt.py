#!/usr/bin/env python2

# This script takes an FSA in openfst format,
# assumed to have one single path through it,
# and prints the output. For extracting output of
# a transduction.

import sys
lines_output = 0
with sys.stdin as fi:
    while True:
        linesplit = fi.readline().strip().split()
        if len(linesplit) > 2:
            #final state not reached yet.   
            print linesplit[3],  #the fourth column has the output label
        else:
            break
print
