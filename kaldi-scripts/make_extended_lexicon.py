#!/usr/bin/env python
from __future__ import print_function

def getHomophones(lexicondict):
    """ Returns a list of lists of homophones for a given lexicon """
    #Indexed by pronunciations, gives all corresponding words, i.e. gives homophones:
    words_by_pronunciation = {}
    for word in lexicondict.keys():
        for pronunciation in lexicondict[word]:
            words_by_pronunciation.setdefault(pronunciation,[]).append(word)
    #The homophones list could also be simply words_by_pronunciation.values()
    homophones = words_by_pronunciation.values()
    #But we delete duplicates, e.g.[[lead#1, lead#2], [lead#1, lead#2]]
    nodup_homophones = [list(tup) for tup in set(tuple(words) for words in homophones)]
    return nodup_homophones 

def readLexiconEntries(lexiconfile):
    """ Read the lexiconfile as a dict 
    Expects lexiconfile to have lines in the format:
        <WORD> [<prob>] <phoneme> <phoneme> <phoneme>... 
    A probability after the word is also supported, like in lexiconp.txt
    In case of multiple pronunciations, expects multiple entries for the same word. """
    lexicon = {}
    with open(lexiconfile, "r") as fi:
        rawline = fi.readline()
        while rawline:
            linesplit = rawline.strip().split()
            word = linesplit[0]
            # Some word entries might not have a pronunciation listed.
            if len(linesplit) > 1: 
                pronunciation = " ".join(linesplit[1:])
                lexicon.setdefault(word,[]).append(pronunciation)
            else: 
                lexicon.setdefault(word,[]).append("")
            rawline = fi.readline()
    return lexicon 

def addOOVs(texts, lexicon, oov):
    """ Adds the pronunciation of oov as the pronunciation of each
    out-of-vocabulary word in the texts """
    for text in texts.values():
        for word in text:
            if word not in lexicon:
                print("Adding pronunciation "+repr(lexicon[oov])+" for OOV word "+word)
                lexicon[word] = lexicon[oov]


def extendLexicon(lexicondict):
    """ Adds miscues """
    #TODO
    pass

def readText(textfile):
    """ Reads a Kaldi style text file containing all the prompts.
    Each line in the format:
        <UTTID> <word1> <word2>...
    """
    texts = {}
    with open(textfile, "r") as fi:
        rawline = fi.readline()
        while rawline:
            linesplit = rawline.strip().split()
            uttid = linesplit[0]
            # Expect to have at least one word for each utterance
            texts[uttid] = linesplit[1:]
            rawline = fi.readline()
    return texts
        
def writeLexicon(lexicondict, outfile):
    entries = [] 
    for word, pronunciations in sorted(lexicondict.items(), key=lambda x:x[0]):
        #Last entry has to end in new line, or validate_dict_dir.pl will fail!
        entries.extend(word + " " + pronunciation + "\n" for pronunciation in pronunciations)
    with open(outfile, "w") as fo:
        fo.write("".join(entries))
        
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
    parser.add_argument("textfile", help = "The Kaldi style text file")
    parser.add_argument("--oov", dest="oov", help="Dictionary entry to use for missing words")
    inputs = parser.parse_args()

    #The lexiconp.txt is prioritised, lexicon.txt is also tried:
    try:
        lexiconstyle = "lexiconp.txt"
        lexiconfile = os.path.join(inputs.srcdir, lexiconstyle)
        lexicon = readLexiconEntries(lexiconfile)
    except IOError:
        lexiconstyle = "lexicon.txt"
        lexiconfile = os.path.join(inputs.srcdir, lexiconstyle)
        lexicon = readLexiconEntries(lexiconfile)
    texts = readText(inputs.textfile)
    if inputs.oov is not None: 
        #Modifies lexicon in place:
        addOOVs(texts, lexicon, inputs.oov)
    extendLexicon(lexicon)
    homophones = getHomophones(lexicon)

    ###Write outputs:
    lexiconout = os.path.join(inputs.tmpdir, lexiconstyle)
    homophoneout = os.path.join(inputs.tmpdir, "homophones.txt")
    writeLexicon(lexicon, lexiconout)
    writeHomophones(homophones, homophoneout)
