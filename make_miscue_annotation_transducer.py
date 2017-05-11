#!/usr/bin/env python2
from __future__ import print_function
import prompt_lmfst
import argparse
import sys
import math

parser = argparse.ArgumentParser(description="""
        This script creates a transducer which can be composed with a text acceptor,
        and the resulting fst gives the key of miscues.""") 


# The special_labels dict defines non-word labels which are used for
# the miscue paths. Not all need specific labels, but some do.
special_labels = {
        "Epsilon":      "<eps>",
        "Rubbish":      "[RUB]",
        "Truncation":   "[TRUNC]:",
        "Correct":      "[CORRECT]",
        "Repeat":       "[REP]",
        "Skip":         "[SKIP]",
        "Jump":         "[JUMP]",
}
weights = {
        }

#The path additions are copied from make_one_miscue_tolerant_lm.py
#They are modified to add actual key symbols.

def addCorrectPaths(p_fst, weights, special_labels):
    for word in p_fst.words:
        labelstate = p_fst.newState() 
        p_fst.addArc(word.start, labelstate, word.label, special_labels["Correct"], 1.0)
        p_fst.addArc(labelstate, word.final, special_labels["Epsilon"], word.label, 1.0)
    p_fst.addFinalState(p_fst.words[-1].final, 1.0) 

def addRubbishPaths(p_fst, weights, special_labels):
    # Rubbish means speech like sounds here. This can model e.g. hesitation sounds ("umm") or 
    # a failed pronunciation
    # We add a path for rubbish both to be inserted before a word and to be substituted for the word.
    if len(p_fst.words) > 1:
        for word, next_word in zip(p_fst.words, p_fst.words[1:]):
            p_fst.addArc(word.start, word.start,
                    special_labels["Rubbish"], special_labels["Rubbish"],
                    0.5)
                    
    # Deal with the last word separately. Don't allow substitution,
    # this is notated as premature end instead.
    p_fst.addArc(p_fst.words[-1].start, p_fst.words[-1].start,
            special_labels["Rubbish"], special_labels["Rubbish"],
            0.5)
    p_fst.addArc(p_fst.words[-1].final, p_fst.words[-1].final,
            special_labels["Rubbish"], special_labels["Rubbish"],
            0.5)

def addSkipPaths(p_fst, weights, special_labels):
    # This will loop over all but the last word.
    # It makes no sense to skip the last word; that should always mean a
    # premature end.
    if len(p_fst.words) > 1:
        for word, next_word in zip(p_fst.words, p_fst.words[1:]):
            skiplabelstate = p_fst.newState()
            p_fst.addArc(word.start, skiplabelstate,
                    next_word.label, special_labels["Skip"],
                    0.5)
            skipwordstate = p_fst.newState()
            p_fst.addArc(skiplabelstate, skipwordstate,
                    special_labels["Epsilon"], word.label,
                    1.0)
            correctlabelstate = p_fst.newState()
            p_fst.addArc(skipwordstate, correctlabelstate,
                    special_labels["Epsilon"], special_labels["Correct"],
                    1.0)
            p_fst.addArc(correctlabelstate, next_word.final,
                    special_labels["Epsilon"], next_word.label,
                    1.0)

def addRepeatPaths(p_fst, weights, special_labels):
    if len(p_fst.words) > 1:
        # This will loop over all but the last word:
        for word, next_word in zip(p_fst.words, p_fst.words[1:]):
            labelstate = p_fst.newState()
            p_fst.addArc(word.final, labelstate,
                    word.label, special_labels["Repeat"],
                    0.5)
            p_fst.addArc(labelstate, word.final,
                    special_labels["Epsilon"], word.label,
                    1.0)
    # Then the last word:
    labelstate = p_fst.newState()
    p_fst.addArc(p_fst.words[-1].final, labelstate,
            p_fst.words[-1].label, special_labels["Repeat"],
            0.5)
    p_fst.addArc(labelstate, p_fst.words[-1].final,
            special_labels["Epsilon"], p_fst.words[-1].label,
            1.0)

def addPrematureEnds(p_fst, weights, special_labels):
    # Add a premature end at the beginning of every word.
    # This way it won't be added to the correct end state.
    for word in p_fst.words:
        p_fst.addFinalState(word.start, 1.0)

def addJumpsBackward(p_fst, weights, special_labels):
    # This will care of all but the last word 
    # (it's simpler code to add jumps from the start state, so we know the next correct word)
    for i, word, in enumerate(p_fst.words):
        for n, prev_word in enumerate(reversed(p_fst.words[:i])):
            # n = number of words jumped over
            if n==0:
                continue # The latest word is special; we add a repeat arc, not a jump back arc.
            labelstate = p_fst.newState()
            p_fst.addArc(word.start, labelstate,
                    prev_word.label, special_labels["Jump"],
                    0.5)
            p_fst.addArc(labelstate, prev_word.final,
                    special_labels["Epsilon"], prev_word.label,
                    1.0)
    # We have to deal with the last word separately
    for n, prev_word in enumerate(reversed(p_fst.words[:-1])):
        labelstate = p_fst.newState()
        p_fst.addArc(p_fst.words[-1].final, labelstate,
                prev_word.label, special_labels["Jump"],
                0.5)
        p_fst.addArc(labelstate, prev_word.final,
                special_labels["Epsilon"], prev_word.label,
                1.0)

def addJumpsForward(p_fst, weights, special_labels):
    # It's again simpler to add jumps from the start states, so we know the next correct word)
    for i, word, in enumerate(p_fst.words):
        for n, later_word in enumerate(p_fst.words[i:]):
            # n = number of words jumped over
            if n == 0:
                continue # The next word is special; we add a skip arc, not a jump forward arc.
            labelstate = p_fst.newState()
            p_fst.addArc(word.start, labelstate,
                    later_word.label, special_labels["Jump"],
                    0.5)
            p_fst.addArc(labelstate, later_word.final,
                    special_labels["Epsilon"], later_word.label,
                    1.0)

def addTruncations(p_fst, weights, special_labels, truncations):
    for word in p_fst.words:
        truncation_entry = special_labels["Truncation"]+word.label #we must build the entry manually here.
        if truncation_entry in truncations: #Some words may not have truncations. For example, words of just one phoneme.
            p_fst.addArc(word.start, word.start,
                    truncation_entry,
                    truncation_entry, 
                    1.0)

def convertRelativeProbs(p_fst):
    # First normalises the weights in relative probabilities into true
    # probabilities, then converts to negative logarithms.
    for state_num, leaves in p_fst.states.items():
        #leaves has Arcs and FinalStates, both of which have a property called weight
        total_weight = reduce(lambda x, y: x + y.weight, leaves, 0.)
        normalised_leaves = []
        for leaf in leaves:
            if total_weight == 0. or leaf.weight == 0.:
                raise ValueError("Relative probability was zero at: " + repr(leaf)) 
            else:
                new_weight = -math.log(leaf.weight / total_weight)
            normalised_leaves.append(leaf._replace(weight = new_weight))
        p_fst.states[state_num] = normalised_leaves

def readTruncations(truncationsfile):
    """ Reads truncations from the given file and returns them as a set """
    with open(truncationsfile, "r") as fi:
        truncationslist = fi.read().split()
    return set(truncationslist)

## Now we just parse arguments and run the functions.
parser.add_argument('--correct-word-boost', dest="correct_boost", 
        nargs="?", type=float,
        help="""Amount to multiply the correct words probability by.
        Lower correct word probability will probably spot more miscues,
        but also have more false positives.""")
parser.add_argument('--homophones', nargs="?", help=
        """File that contains a list of homophones. 
        In each line, words are considered homophones.
        e.g. 
        too two
        carat carrot""")
parser.add_argument('--truncations', nargs="?", help=
        """File that contains a list of words that have truncations in the dictionary.
            On each line is one word""")
parser.add_argument('--rubbish-label', dest="rubbish_label", nargs="?", help=
        """The label to use for Rubbish, i.e. spoken noise""")
parser.add_argument('--truncation-label', dest="truncation_label", nargs="?", help=
        """The label to use for Truncation, concatenated with the word, like [TRUNC]:label""")
args = parser.parse_args()
if args.rubbish_label is not None:
    special_labels["Rubbish"] = args.rubbish_label
if args.truncation_label is not None:
    special_labels["Truncation"] = args.truncation_label
if args.correct_boost is not None:
    weights["Correct"] = weights["Correct"] * args.correct_boost 

fst = prompt_lmfst.PromptLMFST(homophones_path=args.homophones)
prompt = sys.stdin.readline()
prompt_tokenised = prompt.strip().split()
if not prompt_tokenised:
    raise ValueError("Prompt empty!")
fst.addWordSequence(prompt_tokenised)
addCorrectPaths(fst, weights, special_labels)
addRubbishPaths(fst, weights, special_labels)
addSkipPaths(fst, weights, special_labels)
addRepeatPaths(fst, weights, special_labels)
addPrematureEnds(fst, weights, special_labels)
addJumpsBackward(fst, weights, special_labels)
addJumpsForward(fst, weights, special_labels)
if args.truncations is not None:
    truncated_words = readTruncations(args.truncations)
    addTruncations(fst, weights, special_labels, truncated_words)

convertRelativeProbs(fst)
print(fst.inText())
