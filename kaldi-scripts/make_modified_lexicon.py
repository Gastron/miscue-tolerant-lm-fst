#!/usr/bin/env python

WORDPOS_SEPARATOR = "#"
def uniqueLexiconAndPrompt(lexicondict, prompt):
    """ Creates a dict with separate entries for each word in the prompt,
    even if a word is repeated. 
    Uniquefication is done by appending the position of the word in the prompt.
    Returns the prompt as these words and the corresponding lexicon. """
    uniquefied_prompt = []
    uniquefied_lexicon = {}
    for pos, word in enumerate(prompt):
        #Simply uniquefy by appending word position in prompt
        uniquefied_word = word + WORDPOS_SEPARATOR + str(pos)
        uniquefied_prompt.append(uniquefied_word)
        uniquefied_lexicon[uniquefied_word] = lexicondict[word]
    return [uniquefied_prompt, uniquefied_lexicon]

def getHomophones(lexicondict):
    """ Returns a list of lists of homophones for a given lexicon """
    #Indexed by pronunciations, gives all corresponding words, i.e. gives homophones:
    words_by_pronunciation = {}
    for word in lexicondict.keys():
        for pronunciation in lexicondict[word]:
            words_by_pronunciation.setdefault(pronunciation,[]).append(word)
    #The homophones list could also be simply words_by_pronunciation.values()
    #But we exclude entries where there is just one word for a given pronunciation
    homophones = [words for words in words_by_pronunciation.values() if len(words) > 1] 
    #And also delete duplicates, e.g.[[lead#1, lead#2], [lead#1, lead#2]]
    nodup_homophones = [list(tup) for tup in set(tuple(words) for words in homophones)]
    return nodup_homophones 

def readLexiconEntries(lexiconfile, prompt):
    """ Finds in the lexiconfile the lines corresponding to words
    which appear in the prompt, returns a dict of those.
    Expects prompt to be in the same tokenisation as lexicon (case, etc.) 
    Expects to find all prompt words in the lexicon, no OOV supported. 
    Expects lexiconfile to have lines in the format:
        <WORD> <phoneme> <phoneme> <phoneme>... 
    A probability at the end is also supported, like in lexiconp.txt
    In case of multiple pronunciations, expects multiple entries for the same word. """
    filtered_lexicon = {}
    with open(lexiconfile, "r") as fi:
        rawline = fi.readline()
        while rawline:
            linesplit = rawline.strip().split()
            if len(linesplit) > 1: #Some word entries might not have a pronunciation listed.
                word = linesplit[0]
                if word in prompt:
                    pronunciation = " ".join(linesplit[1:])
                    filtered_lexicon.setdefault(word,[]).append(pronunciation)
            rawline = fi.readline()
    if not all((word in filtered_lexicon for word in prompt)):
        raise RuntimeError("Prompt contained out-of-vocabulary words!")
    return filtered_lexicon

def readPrompt(promptfile):
    """ Expects the prompt to be the first (only) line, already tokenised,
    with words separated by whitespace """
    with open(promptfile, "r") as fi:
        promptline = fi.readline()
    tokens = promptline.strip().split()
    if not tokens:
        raise ValueError("The prompt was empty!")
    return tokens 

def writePrompt(prompt, outfile):
    with open(outfile, "w") as fo:
        fo.write(" ".join(prompt))
        
def writeLexicon(lexicondict, outfile):
    entries = [] 
    for word, pronunciations in sorted(lexicondict.items(), key=lambda x:x[0]):
        entries.extend(word + " " + pronunciation for pronunciation in pronunciations)
    with open(outfile, "w") as fo:
        fo.write("\n".join(entries))
        
def writeHomophones(homophones, outfile):
    with open(outfile, "w") as fo:
        fo.write("\n".join([" ".join(words) for words in homophones]))



if __name__ == "__main__":
    import argparse
    import os.path

    ###Parse script arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("srcdir", help = "The source dictionary directory")
    parser.add_argument("tmpdir", help = "The directory to place the output")
    parser.add_argument("promptfile", help = "The file containing the prompt")
    inputs = parser.parse_args()

    ###Process inputs:
    prompt = readPrompt(inputs.promptfile)
    #The lexiconp.txt is prioritised, lexicon.txt is also tried:
    try:
        lexiconstyle = "lexiconp.txt"
        lexiconfile = os.path.join(inputs.srcdir, lexiconstyle)
        filtered_lexicon = readLexiconEntries(lexiconfile, prompt)
    except IOError:
        lexiconstyle = "lexicon.txt"
        lexiconfile = os.path.join(inputs.srcdir, lexiconstyle)
        filtered_lexicon = readLexiconEntries(lexiconfile, prompt)
    uniquefied_prompt, uniquefied_lexicon = uniqueLexiconAndPrompt(filtered_lexicon, prompt)
    homophones = getHomophones(uniquefied_lexicon)

    ###Write outputs:
    promptname = os.path.basename(inputs.promptfile)
    promptout = os.path.join(inputs.tmpdir, "uniqued_"+promptname)
    lexiconout = os.path.join(inputs.tmpdir, lexiconstyle)
    homophoneout = os.path.join(inputs.tmpdir, "homophones.txt")
    writePrompt(uniquefied_prompt, promptout)
    writeLexicon(uniquefied_lexicon, lexiconout)
    writeHomophones(homophones, homophoneout)
