# Miscue tolerant language model FSTs

Speech recognition from reading aloud from a given text (which I will call the prompt) may seem trivial. However humans naturally deviate from the text. These deviations are called miscues, and they include repetitions, false starts, skipping words etc. The scripts here create prompt-specific language model FSTs, which take miscues into account. In experiments for my master's thesis these miscue tolerant models outperformed a naive forced alignment by an order of magnitude.

The FSTs are created in the OpenFST format, and designed to work with the Kaldi toolkit.

## Usage:
- The repository is designed to be cloned into a Kaldi egs/_<corpusname>_/s5 directory and called from that directory, ie. one level above the repository.
- To create an FST for each utterance in a Kaldi-style data directory, use miscue-tolerant-lm-fst/kaldi-scripts/prepare_extended_lang.sh and miscue-tolerant-lm-fst/kaldi-scripts/graphs_for_text.sh
- To create just one FST use miscue-tolerant-lm-fst/kaldi-scripts/make_one_decode_graph.sh
- Decoding with these FSTs proceeds as normal in Kaldi, except that you need to specify the HCLG.fsts.scp where you would normally use a single HCLG.fst
  - The cleanup and segment scripts implement this already, so you can use for example:
    steps/cleanup/decode_segmentation_nnet3.sh 
    --online-ivector-dir 
    exp/nnet3_cleaned/ivectors_test 
    data/test/mtlm_graphs 
    data/test 
    exp/chain/tdnn/decode_mtlm_test
