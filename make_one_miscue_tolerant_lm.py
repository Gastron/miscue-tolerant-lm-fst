#!/usr/bin/env python

from __future__ import print_function
import prompt_lmfst
import argparse

parser = argparse.ArgumentParser(description="""
        This script creates a reading miscue tolerant language model,
        which is suitable for decoding read prompts. 
        It reads a line of text from the standard input and writes a
        text-form WFST that models reading errors into the standard
        output, ready for fstcompile from openfst.""")

# The weights dict defines relative probabilities of transitions.
# They are normalised at each state so that the probabilites sum to one.
# Not all transitions are possible at every step, and this way we can
# ensure that the FST stays stochastic.
# It may also be more intuitive to define the weights as 10:1, instead of  
# 0.9091:0.0909 (the true probabilities).
# In the resulting FST these are converted to OpenFst weights, in the log semiring.
# In that semiring the weight (==the cost) of a transition is a 
# negative logarithm of the probability.
weights = {
        "Correct":      100,    #The correct next word
        "Rubbish":      5,      #Speech-like noises, hesitations, etc.
        "Skip":         10,     #Jump forward one word
        "Repeat":       30,     #Jump backward one word
        "JumpForward":  3,      #Jump forward multiple words
        "JumpBackward": 5,      #Jump backward multiple words
        "Truncation":   5,      #An incomplete pronounciation
        "PrematureEnd": 3,      #Unexpected end of utterance
        "FinalState":   0.0     #NOTE: This is an actual weight!
                                # For interface simplicity, it is kept in the same dict.
}

# The special_labels dict defines non-word labels which are used for
# the miscue paths.
special_labels = {
        "Rubbish":      "[RUB]",
        "Skip":         "[SKP]"
        "Epsilon":      "<eps>"
}


## The next functions define recipes for adding the different types of paths
## to the FST. They are separate functions but some assume that all of them are run.
## This is necessary because some will add conditional paths which are mutually exclusive.
## We will use the variable p_fst as a prompt FST, see prompt_lmfst.py

def addCorrectPaths(p_fst, weights):
    for word in p_fst.words: 
        p_fst.addArc(word.start, word.final, word.label, word.label, weights["Correct"])
    p_fst.addFinalState(p_fst.words[-1].final, weights["FinalState"])

def addRubbishPaths(p_fst, weights):
    for word in p_fst.words:
        p_fst.addArc(word.start, word.start, 
            special_labels["Rubbish"], special_labels["Rubbish"],
            weights["Rubbish"])
    p_fst.addArc(p_fst.words[-1].final, p_fst.words[-1].final,
            special_labels["Rubbish"], special_labels["Rubbish"],
            weights["Rubbish"])

def addSkipPaths(p_fst, weights):
    # This will loop over all but the last word.
    for word, next_word in zip(p_fst.words,p_fst.words[1:]):
        # If the labels are the same, epsilon removal makes it so that the
        # FST may become indeterministic. Thus don't add skip here.
        # This way, skips are always notated at the end of a sequence of repeated words.
        if word.label != next_word.label:
            p_fst.addArc(word.start, word.final, 
                    special_labels["Epsilon"], special_labels["Skip"],
                    weights["Skip"])
    # Premature end and skip correspond to the same input sequence.
    # We can only have one, so we should pick the one with higher relative probability.
    # TODO: Think through this path of epsilons... there is probably some trouble ahead.
    if weights["Skip"] > weights["PrematureEnd"]:
        p_fst.addArc(p_fst.words[-1].start, p_fst.







fst = prompt_lmfst.PromptLMFST()
