#!/usr/bin/env python
from __future__ import print_function
from make_extended_lexicon import (getHomophones, readLexiconEntries, 
    addOOVs, addTruncations, writeHomophones, writeLexicon, writeTruncations,
    getFilteredLexicon)

ENCODING="utf8"
IMPORTANT_WORDS = set([])
WORDPOS_SEPARATOR = "@"

def uniquefyPrompt(prompt, lexicondict):
    """ Makes uniquefied version of the prompt by appending to each word its position.
    Returns the prompt as these words and adds these to the lexicon inplace. """
    uniquefied_prompt = []
    for pos, word in enumerate(prompt):
        #Simply uniquefy by appending word position in prompt
        uniquefied_word = word + WORDPOS_SEPARATOR + str(pos)
        uniquefied_prompt.append(uniquefied_word)
        lexicondict[uniquefied_word] = lexicondict[word]
    return uniquefied_prompt

def readPrompt(promptfile):
    """ Expects the prompt to be the first (only) line, already tokenised,
    with words separated by whitespace """
    with open(promptfile, "r") as fi:
        promptline = fi.readline().decode(ENCODING)
    tokens = promptline.strip().split()
    if not tokens:
        raise ValueError("The prompt was empty!")
    return tokens 

def writePrompt(prompt, outfile):
    outstr = " ".join(prompt)
    with open(outfile, "w") as fo:
        fo.write(outstr.encode(ENCODING))

if __name__ == "__main__":
    import argparse
    import os.path

    ###Parse script arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("srcdir", help = "The source dictionary directory")
    parser.add_argument("tmpdir", help = "The directory to place the output")
    parser.add_argument("promptfile", help = "The file containing the prompt")
    parser.add_argument("--keep", dest="keepwords", 
            help = "Words to keep from the lexicon, even if not found in prompt, in the form they appear.")
    parser.add_argument("--oov", dest="oov", help="Dictionary entry to use for missing words")
    parser.add_argument("--truncation-label", dest="truncation_label", help="Prefix for truncation entries in the lexicon")
    inputs = parser.parse_args()

    ###Process inputs:
    prompt = readPrompt(inputs.promptfile)
    keepwords = inputs.keepwords.split() if inputs.keepwords is not None else []
    oov = inputs.oov
    demand_comprehensive_lexicon = True
    #The lexiconp.txt is prioritised, lexicon.txt is also tried:
    try:
        lexiconstyle = "lexiconp.txt"
        LEXICON_CONSTANT = 1 #the pronunciation entry is lexicon[uttid][1:]
        lexiconfile = os.path.join(inputs.srcdir, lexiconstyle)
        lexicon = readLexiconEntries(lexiconfile)
    except IOError:
        lexiconstyle = "lexicon.txt"
        LEXICON_CONSTANT = 0 #the pronunciation entry is lexicon[uttid][0:] 
        lexiconfile = os.path.join(inputs.srcdir, lexiconstyle)
        lexicon = readLexiconEntries(lexiconfile)
    textwords = set(prompt)
    if inputs.oov is not None: 
        print("Adding pronunciation for any missing words from the pronunciation of: "+inputs.oov)
        oov_entry = inputs.oov.decode(ENCODING)
        #Modifies lexicon in place, note this does not add new words:
        addOOVs(textwords, lexicon, oov_entry)
        IMPORTANT_WORDS.add(oov_entry)
    uniqued_prompt = uniquefyPrompt(prompt, lexicon)
    unique_textwords = set(uniqued_prompt)
    if inputs.truncation_label is not None:
        print("Adding truncations with truncation prefix: "+inputs.truncation_label)
        #Modifies lexicon in place, returns a set of all used word entries (sets are immutable)
        truncwords = addTruncations(lexicon, unique_textwords, inputs.truncation_label.decode(ENCODING), LEXICON_CONSTANT=LEXICON_CONSTANT)
    words_to_keep = truncwords | unique_textwords | IMPORTANT_WORDS #union 
    filtered_lexicon = getFilteredLexicon(lexicon, words_to_keep)
    #This must of course be done last:
    homophones = getHomophones(filtered_lexicon, words_to_keep)

    ###Write outputs:
    promptout = os.path.join(inputs.tmpdir, "uniqued_prompt.txt")
    lexiconout = os.path.join(inputs.tmpdir, lexiconstyle)
    homophoneout = os.path.join(inputs.tmpdir, "homophones.txt")
    truncwordout = os.path.join(inputs.tmpdir, "truncations.txt")
    writePrompt(uniqued_prompt, promptout)
    writeLexicon(filtered_lexicon, lexiconout)
    writeHomophones(homophones, homophoneout)
    writeTruncations(truncwords, truncwordout)
