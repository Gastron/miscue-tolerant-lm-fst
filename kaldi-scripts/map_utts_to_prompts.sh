#!/bin/bash
# Finds the unique prompts in a text file, and maps uttids to those (via prompt_ids)
# Mostly should be used as a subtask of graphs_for_text.sh

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <text> <utt2prompt> <prompts-table>"
  echo " NOTE: the last two arguments are outputs."
  exit 1
fi

text=$1
utt2prompt=$2
promptstbl=$3
rm -f $2 $3
while read promptline; do
  uttid=$(echo "$promptline" | awk '{print $1}' )
  prompt=$(echo "$promptline" | cut -f 2- -d " " )
  promptcrc=$(echo "$prompt" | cksum - | cut -d" " -f 1)
  #Save the relation, then echo for output
  echo "$uttid $promptcrc" >> "$utt2prompt"
  echo "$promptcrc $prompt" >> "$promptstbl"
done <$text
