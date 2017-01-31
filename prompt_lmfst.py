#!/usr/bin/env python

# Copyright 2017 Aku Rouhe
# Licence: BSD-2-Clause

from __future__ import print_function
from collections import namedtuple


class Word(object):
    ## A word object is created for each word in the input prompt.
    ## Most importantly it keeps track of the corresponding FST state numbers
    ## Here the label is the word (as written) or its corresponding integer
    ## (in case using integer-to-symbol tables)
    ## In general, labels are the input and output labels of an FST
    def __init__(self, label, start, final):
        self.label = label
        self.start = start
        self.final = final
        self.nextStart = self.final
        self.prevFinal = self.start

#FST Building-block classes:
Arc = namedtuple("Arc", "from_state to_state in_label out_label weight")
FinalState = namedtuple("FinalState", "state weight")

class PromptLMFST(object):
    ## Language model weighted finite state transducer
    ## for a prompt.
    ## Represents the prompt as a sequence of Word objects.

    def __init__(self,ID=None):
        self.ID = ID
        self.words = [] #Word objects
        self.states = {}
        self.state_counter = 0
        self.initialised = False

    def addNextWord(self, label):
        # Use this to add words one by one into the PromptLMFST from a prompt text
        # Note: This does not add an arc between the start and final states of the word.
        # We would need a weight for that.
        if not self.initialised:
            #Note: the initial state becomes the value state_counter is initialised to.
            self.states[self.state_counter] = []
            self.words.append(Word(label, self.state_counter, self.newState()))
            self.initialised = True
        else:
            self.words.append(Word(label, self.curr_word.final, self.newState()))

    @property
    def curr_word(self):
        # This is the last word added to the FST
        if not self.initialised:
            raise RuntimeError("Tried to get current word but no words added yet.")
        else:
            return self.words[-1]

    def newState(self):
        # Creates a new, unused state, with a unique number, returns that number
        self.state_counter += 1
        self.states[self.state_counter] = []
        return self.state_counter

    def addArc(self, from_state, to_state, in_label, out_label, weight):
        self.states[from_state].append(Arc(from_state, to_state, in_label, out_label, weight))

    def addFinalState(self, state, weight):
        self.states[state].append(FinalState(state, weight))

    def addWordSequence(self, sequence):
        # Sequence is expected to be a list of labels (tokenisation is left to user)
        for label in sequence:
            self.addNextWord(label)

    def inText(self):
        # Returns a text representation of the FST. Compatible with OpenFST text format.
        result = "" if self.ID is None else self.ID + "\n"
        for state in self.states.values():
            for leaf in state: #leaf is an Arc or a FinalState
                result += " ".join(map(str, leaf)) + "\n"
        return result

    def isDeterministic(self):
        # Checks if the FST is deterministic, i.e. no state has multiple
        # outgoing arcs with the same input label.
        # NOTE: This method does treats epsilons like any other label.
        for state in self.states.values():
            seen_labels = {}
            for item in state:
                if has_attr(item, "in_label"):
                    if item.in_label in seen_labels:
                        return False
                    else:
                        seen_labels[item.in_label] = True
        return True

