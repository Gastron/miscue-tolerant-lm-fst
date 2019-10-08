#!/usr/bin/env python2

# This script takes an string an converts it to a finite state acceptor

import sys
with sys.stdin as fi:
    linesplit = fi.readline().strip().split()
    for i, word in enumerate(linesplit):
        print i, i+1, word, word, 0.0
    print i+1, 0.0
