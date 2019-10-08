#!/usr/bin/env python3
# Prints out a list of utterances to EXCLUDE based on edit distance
# Could be used after kaldi-scripts/get_output.sh to filter 
# entries where the mtlm decoding has produced a very different output,
# compared to the prompt.
# 
# NOTE: Edit distance filtering is not the same as filtering based on the
# number of miscues. 
# Edit distance filtering is only appropriate when
# using mtlm graphs to cleanup data; when you only want to exclude 
# the audio the did not match the prompt.
#
# Very picky about input, their order and uttids need to match exactly
# Use sort text -o text (remember env LC_ALL=C for Kaldi conventions) and 
# utils/filter_scp.pl to make them match

#Implementation from:
#https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
  if len(s1) < len(s2):
    return levenshtein(s2, s1)
  # len(s1) >= len(s2)
  if len(s2) == 0:
    return len(s1)
  previous_row = range(len(s2) + 1)
  for i, c1 in enumerate(s1):
    current_row = [i + 1]
    for j, c2 in enumerate(s2):
      insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
      deletions = current_row[j] + 1     # than s2
      substitutions = previous_row[j] + (c1 != c2)
      current_row.append(min(insertions, deletions, substitutions))
    previous_row = current_row
  return previous_row[-1]

if __name__ == "__main__":
  import argparse
  import pathlib
  import sys
  parser = argparse.ArgumentParser("""
    Prints out a list of utterances to EXCLUDE based on edit distance
    Could be used after kaldi-scripts/get_output.sh to filter 
    entries where the mtlm decoding has produced a very different output,
    compared to the prompt.
    Make sure the texts are sorted in the same order and have exactly the same uttids.
    You can use utils/filter_scp.pl to filter any missing lines.""")
  parser.add_argument("texts", metavar="TEXT", nargs=2, type=pathlib.Path)
  parser.add_argument("--max-distance", default = 1, type=int)
  args = parser.parse_args()
  total_utterances = 0
  total_excluded = 0
  with open(args.texts[0]) as fa, open(args.texts[1]) as fb:
    for line_a, line_b in zip(fa, fb):
      total_utterances +=1
      uttid_a, *text_a = line_a.strip().split()
      uttid_b, *text_b = line_b.strip().split()
      if uttid_a != uttid_b:
        raise ValueError("Utterances did not match exactly! Found out at: "+uttid_a+" != "+uttid_b)
      if levenshtein(text_a, text_b) > args.max_distance:
        print(uttid_a)
        total_excluded+=1
  print("Excluded", total_excluded, "uttids out of", total_utterances, "based on edit distance.", file=sys.stderr)
