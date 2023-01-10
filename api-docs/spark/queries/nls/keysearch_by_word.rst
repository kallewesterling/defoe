Count number of occurrences of keywords or keysentences and group by word
==========================================================================

- Both keywords/keysentences and words in documents are cleaned (long-S and hyphen fixes) and preprocessed according to the configuration file
- Query module: ``defoe.nls.queries.keysentence_by_word``
- Configuration file:

  - defoe path (defoe_path)
  - operating system (os)
  - preprocessing treatment (preprocess)
  - File with keywords or keysentece (data)
  - Examples:

    - preprocess: normalize
    - data: sc_cities.txt
    - defoe_path: /lustre/home/sc048/rosaf4/defoe/
    - os_type: linux

**Result format:**

..  code-block:: yaml

  <WORD>:
    - [<YEAR>, <NUM_WORDS>]
    - ...
  <WORD>:
    - ...
