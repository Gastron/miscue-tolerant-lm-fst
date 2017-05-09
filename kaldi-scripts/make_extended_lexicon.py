#!/usr/bin/env python
from __future__ import print_function

ENCODING="utf8"
IMPORTANT_WORDS = set([])

def getHomophones(lexicondict, allwords):
    """ Returns a list of lists of homophones for a given lexicon """
    #Indexed by pronunciations, gives all corresponding words, i.e. gives homophones:
    words_by_pronunciation = {}
    for word in allwords:
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
        rawline = fi.readline().decode(ENCODING)
        while rawline:
            linesplit = rawline.strip().split()
            word = linesplit[0]
            # Some word entries might not have a pronunciation listed.
            if len(linesplit) > 1: 
                pronunciation = u" ".join(linesplit[1:])
                lexicon.setdefault(word,[]).append(pronunciation)
            else: 
                pass #ie. exclude from lexicon dict: it can then be treated with OOV addition.
            rawline = fi.readline().decode(ENCODING)
    return lexicon 

def addOOVs(textwords, lexicon, oov):
    """ Adds the pronunciation of oov as the pronunciation of each
    out-of-vocabulary word in the texts """
    for word in textwords:
        try:
            if word not in lexicon:
                print("Adding pronunciation "+repr(lexicon[oov])+" for OOV word "+word)
                lexicon[word] = lexicon[oov]
        except:
            print(word)
            raise

def addTruncations(lexicon, textwords, truncation_label, min_cut_phonemes=2, min_left_phonemes=2):
    """ Adds truncated lexicon entries for all textwords into the lexicon inplace.
    Returns the added words as a set. 

    Note: LEXICON_CONSTANT is used here to keep compatibility with both lexiconp.txt and lexicon.txt
    formats. It is either 1 or 0, as lexicon[uttid][0] can be a weight or the first phoneme of the
    pronunciation.
    """
    truncation_words = set()
    for word in textwords:
        for pronunciation in lexicon[word]:
            pronunciation_list = pronunciation.split()
            if len(pronunciation_list) - LEXICON_CONSTANT < min_cut_phonemes + min_left_phonemes:
                continue
            for upto_pos in range(min_left_phonemes + LEXICON_CONSTANT, len(pronunciation_list) - min_cut_phonemes):
                truncation = u" ".join(pronunciation_list[:upto_pos])
                truncation_word = truncation_label + word
                lexicon.setdefault(truncation_word, []).append(truncation)
                truncation_words.add(truncation_word)
    return truncation_words

def readText(textfile):
    """ Reads a Kaldi style text file containing all the prompts.
    Each line in the format:
        <UTTID> <word1> <word2>...
    """
    texts = {}
    with open(textfile, "r") as fi:
        rawline = fi.readline().decode(ENCODING)
        while rawline:
            linesplit = rawline.strip().split()
            uttid = linesplit[0]
            # Expect to have at least one word for each utterance
            texts[uttid] = linesplit[1:]
            rawline = fi.readline().decode(ENCODING)
    return texts

def getAllTextWords(texts):
    """ Returns a set of all the words in the given texts """
    return reduce(lambda x,y: x | set(y), texts.values(), set()) #union of all the texts as sets
        
def getFilteredLexicon(lexicondict, allwords):
    """ Returns a lexicon with just the necessary words.
    Assumes all wanted keys exist in the given lexicon """
    return { word: lexicondict[word] for word in allwords }
        
def writeLexicon(lexicondict, outfile):
    entries = [] 
    for word, pronunciations in lexicondict.items():
        #Last entry has to end in new line, or validate_dict_dir.pl will fail!
        entries.extend(word + " " + pronunciation + "\n" for pronunciation in pronunciations)
    #For example truncations can result in duplicates, remove them:
    entries = sorted(list(set(entries)), key=lambda x:x[0])
    outunicode = u"".join(entries)
    with open(outfile, "w") as fo:
        fo.write(outunicode.encode(ENCODING))

def writeHomophones(homophones, outfile):
    outunicode = u"\n".join([u" ".join(words) for words in homophones])
    with open(outfile, "w") as fo:
        fo.write(outunicode.encode(ENCODING))

def writeTruncations(truncations, outfile):
    outunicode = u"\n".join(truncations)
    with open(outfile, "w") as fo:
        fo.write(outunicode.encode(ENCODING))

if __name__ == "__main__":
    import argparse
    import os.path

    ###Parse script arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("srcdir", help = "The source dictionary directory")
    parser.add_argument("tmpdir", help = "The directory to place the output")
    parser.add_argument("textfile", help = "The Kaldi style text file")
    parser.add_argument("--oov", dest="oov", help="Dictionary entry to use for missing words")
    parser.add_argument("--truncation-label", dest="truncation_label", help="Prefix for truncation entries in the lexicon")
    inputs = parser.parse_args()

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
    texts = readText(inputs.textfile)
    textwords = getAllTextWords(texts)
    if inputs.oov is not None: 
        print("Adding pronunciation for any missing words from the pronunciation of: "+inputs.oov)
        oov_entry = inputs.oov.decode(ENCODING)
        #Modifies lexicon in place, note this does not add new words:
        addOOVs(textwords, lexicon, oov_entry)
        IMPORTANT_WORDS.add(oov_entry)
    if inputs.truncation_label is not None:
        print("Adding truncations with truncation prefix: "+inputs.truncation_label)
        #Modifies lexicon in place, returns a set of all used word entries (sets are immutable)
        truncwords = addTruncations(lexicon, textwords, inputs.truncation_label.decode(ENCODING))
    words_to_keep = truncwords | textwords | IMPORTANT_WORDS #union 
    filtered_lexicon = getFilteredLexicon(lexicon, words_to_keep)
    #This must of course be done last:
    homophones = getHomophones(filtered_lexicon, words_to_keep)

    ###Write outputs:
    lexiconout = os.path.join(inputs.tmpdir, lexiconstyle)
    homophoneout = os.path.join(inputs.tmpdir, "homophones.txt")
    truncwordout = os.path.join(inputs.tmpdir, "truncations.txt")
    writeLexicon(filtered_lexicon, lexiconout)
    writeHomophones(homophones, homophoneout)
    writeTruncations(truncwords, truncwordout)
