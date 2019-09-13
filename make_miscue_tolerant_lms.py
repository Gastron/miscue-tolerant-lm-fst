#!/usr/bin/env python3
import locale
locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
import prompt_lmfst
import math
import functools

#NOTE: See the if __name__ == "__main__": block below for a description

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
        "Correct":      1000.,    #The correct next word
        "Rubbish":      5.,      #Speech-like noises, hesitations, etc.
        "Skip":         10.,     #Jump forward one word
        "Repeat":       30.,     #Jump backward one word
        "JumpForward":  2.,      #Jump forward multiple words
        "JumpBackward": 5.,      #Jump backward multiple words
        "LongJumpDecay":0.9,    #A decay term applied to the relative probability for jumps: 
                                #P(jump) = d^n * <jump_relative_probability>, n == number of words jumped over
        "Truncation":   5.,      #An incomplete pronounciation
        "PrematureEnd": 3.,      #Unexpected end of utterance
        "FinalState":   1000.     #The probability that the utterance ends at the correct point. 
                                #There could also be repetition, rubbish, etc.
}

# The special_labels dict defines non-word labels which are used for
# the miscue paths. Not all need specific labels, but some do.
special_labels = {
        "Epsilon":      "<eps>",
        "Rubbish":      "[RUB]",
        "Truncation":   "[TRUNC]:",
}


## The next functions define recipes for adding the different types of paths
## to the FST.
## The idea is to always consume a label and design the recipes so that for the truely
## ambiguous cases, e.g. where in a line of repetitions to put the repetitions, make
## the choice unified. The FST will not end up 100% deterministic for all phone sequences
## but in the weight of the paths should end up different and thus the desired path
## is found (path of least weight).

def addCorrectPaths(p_fst, weights):
    for word in p_fst.words:
        p_fst.addArc(word.start, word.final, word.label, word.label, weights["Correct"])
    p_fst.addFinalState(p_fst.words[-1].final, weights["FinalState"])

def addRubbishPaths(p_fst, weights, special_labels):
    # Rubbish means speech like sounds here. This can model e.g. hesitation sounds ("umm") or 
    # a failed pronunciation
    # We add a path for rubbish both to be inserted before a word and to be substituted for the word.
    if len(p_fst.words) > 1:
        for word, next_word in zip(p_fst.words, p_fst.words[1:]):
            rubbish_state = p_fst.newState()
            p_fst.addArc(word.start, rubbish_state,
                    special_labels["Rubbish"], special_labels["Rubbish"],
                    weights["Rubbish"])
            p_fst.addArc(rubbish_state, word.start,
                    special_labels["Epsilon"], special_labels["Epsilon"],
                    weights["Correct"])
            p_fst.addArc(rubbish_state, next_word.final,
                    next_word.label, next_word.label,
                    weights["Correct"])
    # Deal with the last word separately. Don't allow substitution,
    # this is notated as premature end instead.
    p_fst.addArc(p_fst.words[-1].start, p_fst.words[-1].start,
            special_labels["Rubbish"], special_labels["Rubbish"],
            weights["Rubbish"])
    p_fst.addArc(p_fst.words[-1].final, p_fst.words[-1].final,
            special_labels["Rubbish"], special_labels["Rubbish"],
            weights["Rubbish"])

def addSkipPaths(p_fst, weights):
    # This will loop over all but the last word.
    # It makes no sense to skip the last word; that should always mean a
    # premature end.
    if len(p_fst.words) > 1:
        for word, next_word in zip(p_fst.words, p_fst.words[1:]):
            p_fst.addArc(word.start, next_word.final,
                    next_word.label, next_word.label,
                    weights["Skip"])

def addRepeatPaths(p_fst, weights):
    if len(p_fst.words) > 1:
        # This will loop over all but the last word:
        for word, next_word in zip(p_fst.words, p_fst.words[1:]):
            p_fst.addArc(word.final, word.final,
                    word.label, word.label,
                    weights["Repeat"])
    # Then the last word:
    p_fst.addArc(p_fst.words[-1].final, p_fst.words[-1].final,
            p_fst.words[-1].label, p_fst.words[-1].label,
            weights["Repeat"])

def addPrematureEnds(p_fst, weights):
    # Add a premature end at the beginning of every word.
    # This way it won't be added to the correct end state.
    for word in p_fst.words:
        p_fst.addFinalState(word.start, weights["PrematureEnd"])

def addJumpsBackward(p_fst, weights):
    # This will care of all but the last word 
    # (it's simpler code to add jumps from the start state, so we know the next correct word)
    for i, word, in enumerate(p_fst.words):
        for n, prev_word in enumerate(reversed(p_fst.words[:i])):
            # n = number of words jumped over
            if n==0:
                continue # The latest word is special; we add a repeat arc, not a jump back arc.
            decayed_weight = weights["LongJumpDecay"] ** n * weights["JumpBackward"]
            p_fst.addArc(word.start, prev_word.final,
                    prev_word.label, prev_word.label,
                    decayed_weight)
    # We have to deal with the last word separately
    for n, prev_word in enumerate(reversed(p_fst.words[:-1])):
        decayed_weight = weights["LongJumpDecay"] ** n * weights["JumpBackward"]
        p_fst.addArc(p_fst.words[-1].final, prev_word.final,
                prev_word.label, prev_word.label,
                decayed_weight)

def addJumpsForward(p_fst, weights):
    # It's again simpler to add jumps from the start states, so we know the next correct word)
    for i, word, in enumerate(p_fst.words):
        for n, later_word in enumerate(p_fst.words[i:]):
            # n = number of words jumped over
            if n == 0:
                continue # The next word is special; we add a skip arc, not a jump forward arc.
            decayed_weight = weights["LongJumpDecay"] ** n * weights["JumpForward"]
            p_fst.addArc(word.start, later_word.final,
                    later_word.label, later_word.label,
                    decayed_weight)

def addTruncations(p_fst, weights, special_labels, truncations):
    for word in p_fst.words:
        truncation_entry = special_labels["Truncation"]+word.label #we must build the entry manually here.
        if truncation_entry in truncations: #Some words may not have truncations. For example, words of just one phoneme.
            p_fst.addArc(word.start, word.start,
                    truncation_entry,
                    truncation_entry, 
                    weights["Truncation"])

def convertRelativeProbs(p_fst):
    # First normalises the weights in relative probabilities into true
    # probabilities, then converts to negative logarithms.
    for state_num, leaves in p_fst.states.items():
        #leaves has Arcs and FinalStates, both of which have a property called weight
        total_weight = functools.reduce(lambda x, y: x + y.weight, leaves, 0.)
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
    with open(truncationsfile) as fi:
        truncationslist = fi.read().split()
    return set(truncationslist)

if __name__ == "__main__":
    import argparse
    import fileinput
    parser = argparse.ArgumentParser(description="""
            This script creates a reading miscue tolerant language model,
            which is suitable for decoding read prompts.
            It reads a line of text from the standard input and writes a
            text format WFST that models reading errors into the standard
            output, in the openfst format. If multiple lines are given in the input,
            this script outputs multiple text format FSTs, separated by an empty line.
            That format in particular was chosen because of the Kaldi program
            compile-training-graphs-fsts.

            The script will accept a list of homophones, which in this context also
            includes the above mentioned uniquefied words. This will be used for some
            miscue types to keep the result deterministic and make sane inferences about
            the reading miscues.
            """)
    parser.add_argument('--correct-word-boost', type=float,
        help="""Amount to multiply the correct words probability by.
        Lower correct word probability will probably spot more miscues,
        but also have more false positives.""")
    parser.add_argument('--homophones', help=
        """File that contains a list of homophones. 
        In each line, words are considered homophones.
        e.g. 
        too two
        carat carrot""")
    parser.add_argument('--truncations', help=
        """File that contains a list of words that have truncations in the dictionary.
            On each line is one word""")
    parser.add_argument('--rubbish-label', help=
        """File to read the label to use for rubbish, i.e. spoken noise""")
    parser.add_argument('--truncation-label', help=
        """File to read label to use for Truncation, 
        concatenated with the word, like [TRUNC]:label""")  
    parser.add_argument('--kaldi-style', action='store_true', help=
        """For kaldi style inputs, but may be useful otherwise as well.
        With this option, the first column in the input is treated as an id, 
        which should be output as is.""")
    parser.add_argument("input", help="""Input as a filepath or - for stdin. 
        Prompts are read line by line.""") 
    args = parser.parse_args()
    if args.rubbish_label:
        with open(args.rubbish_label) as fi:
            special_labels["Rubbish"] = fi.read().strip()
    if args.truncation_label:
        with open(args.truncation_label) as fi:
            special_labels["Truncation"] = fi.read().strip()
    if args.correct_word_boost:
        weights["Correct"] = weights["Correct"] * args.correct_boost 
    if args.truncations:
        truncated_words = readTruncations(args.truncations)
    homophones = prompt_lmfst.readHomophones(args.homophones)

    #Process each line in input:
    for line in fileinput.input(args.input):
        if args.kaldi_style:
            ID, *prompt_tokenised = line.strip().split()
            fst = prompt_lmfst.PromptLMFST(homophones = homophones, ID=ID)
        else:
            prompt_tokenised = line.strip().split()
            fst = prompt_lmfst.PromptLMFST(homophones = homophones, ID=None)
        fst.addWordSequence(prompt_tokenised)
        addCorrectPaths(fst, weights)
        addRubbishPaths(fst, weights, special_labels)
        addSkipPaths(fst, weights)
        addRepeatPaths(fst, weights)
        addPrematureEnds(fst, weights)
        addJumpsBackward(fst, weights)
        addJumpsForward(fst, weights)
        if args.truncations is not None:
            addTruncations(fst, weights, special_labels, truncated_words)
        convertRelativeProbs(fst)
        print(fst.inText())
        print() #Empty line means end of FST
