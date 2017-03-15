#!/usr/bin/env python


def fetchLexiconEntries(lexiconfile, prompt):
    """ Finds in the lexiconfile the lines corresponding to words
    which appear in the prompt, returns a dict of those """
    #TODO

def uniqueLexiconAndPrompt(lexicondict, prompt):
    """ Creates a dict with separate entries for each word in the prompt,
    even if a word is repeated.
    Returns the prompt as these words, the dict and a list of homophones. """
    #TODO


#TODO: IO
def readPrompt(promptfile):
    raise RuntimeError("Not implemented yet") 
def writePrompt(prompt):
    raise RuntimeError("Not implemented yet") 
def writeLexicon(lexicondict):
    raise RuntimeError("Not implemented yet") 
def writeHomophones(homophones):
    raise RuntimeError("Not implemented yet") 



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("srcdir", "+", help = "The source dictionary directory")
    parser.add_argument("tmpdir", "+", help = "The directory to place the output")
    parser.add_argument("promptfile", "+", help = "The file containing the prompt")

    parser.parse_args()
    
