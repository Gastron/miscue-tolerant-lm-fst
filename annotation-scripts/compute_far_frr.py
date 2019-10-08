#!/usr/bin/env python2
from __future__ import division, print_function


import sys
from collections import Counter
import argparse
parser = argparse.ArgumentParser(description = """
This script computes miscue detection false acceptance rate and
false rejection rate for a decoded output
The input is an alignment file for annotated miscues, with miscue labels
attached to the words, from align-text Kaldi tool""")
parser.add_argument("--verbose", action="store_const", const=True, default=False)
parser.add_argument("align_file", )
args = parser.parse_args()
labels = {"correct": "[CORRECT]",
        "jump": "[JUMP]",
        "eps": "<eps>",
        "skip": "[SKIP]"}

with open(args.align_file, "r") as fi:
    correctcorrect = Counter() 
    correctmiscue = Counter()
    missed = Counter()
    hallucinated = Counter()
    false_accept = Counter() 
    false_reject = Counter()
    wrong_miscue = Counter()
    alignment = fi.readline().strip().split(";")
    while alignment[0]:
        first = alignment.pop(0)
        uttid, ref, hyp = first.split()
        alignment.insert(0, " ".join([ref,hyp]))
        for pos in alignment:
            ref, hyp = pos.split()
            if ref == hyp:
                if ref.startswith(labels["correct"]):
                    correctcorrect[ref] += 1
                else:
                    correctmiscue[ref] += 1
                if args.verbose:
                    print("Correct:", ref, hyp)
            elif ref.startswith(labels["jump"]) and hyp.startswith(labels["correct"]) and ref.split("]")[1] == hyp.split("]")[1]:
                correctcorrect[ref] += 1
                if args.verbose:
                    print("Correct with jump:", ref, hyp)
            elif hyp.startswith(labels["jump"]) and ref.startswith(labels["correct"]) and ref.split("]")[1] == hyp.split("]")[1]:
                correctcorrect[ref] += 1
                if args.verbose:
                    print("Correct with jump:", ref, hyp)
            elif hyp == labels["eps"]:
                if ref.startswith(labels["skip"]):
                    pass #non-action
                else:
                    missed[ref] += 1
                    if args.verbose:
                        print("Missed:", ref, hyp)
            elif ref.startswith(labels["correct"]):
                false_reject[ref] += 1
                if args.verbose:
                    print("False reject:", ref, hyp)
            elif not hyp.startswith(labels["correct"]):
                if ref == labels["eps"] and hyp.startswith(labels["skip"]):
                    pass #non-action
                elif ref == labels["eps"]:
                    hallucinated[hyp] += 1 
                    if args.verbose:
                        print("Hallucinated:", ref, hyp)
                else:
                    wrong_miscue[ref] += 1
                    if args.verbose:
                        print("Wrong miscue:", ref, hyp)
            else:
                false_accept[ref] += 1
                if args.verbose:
                    print("Wrong miscue", ref, hyp)
        alignment = fi.readline().strip().split(";")

print("False acceptance rate:", (sum(missed.values()) + sum(false_accept.values())) / (sum(correctmiscue.values()) + sum(missed.values()) + sum(false_accept.values()) + sum(wrong_miscue.values())))

print("False rejection rate:", sum(false_reject.values()) / (sum(correctcorrect.values()) + sum(false_reject.values())))
