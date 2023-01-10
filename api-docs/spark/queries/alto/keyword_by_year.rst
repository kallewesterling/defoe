Count number of occurrences of keywords and group by year
==========================================================

- Both keywords and words in documents are normalized, by removing all non-``a-z|A-Z`` characters.
- Query module: ``defoe.alto.queries.keyword_by_year``
- Configuration file:

  - One or more words to search for, one per line.
  - Examples:

    - ``queries/diseases.txt``
    - ``queries/hearts.txt``

**Result format:**

..  code-block:: yaml

  <YEAR>:
    - [<WORD>, <NUM_WORDS>]
    - ...
  <YEAR>:
    ...

**Sample results:**

Query over British Library Books ``1510_1699/000001143_0_1-20pgs__560409_dat.zip`` and ``1510_1699/000000874_0_1-22pgs__570785_dat.zip`` with ``queries/hearts.txt``:

..  code-block:: yaml

  1676:
    - [heart, 4]
    - [hearts, 1]

Query over British Library Books ``1510_1699/*.zip`` with ``queries/diseases.txt``:

..  code-block:: yaml

  null:
    - [consumption, 1]
  1605:
    - [consumption, 2]
  1608:
    - [consumption, 1]
  1613:
    - [consumption, 2]
  1618:
    - [cancer, 1]
  1623:
    - [consumption, 1]
  1630:
    - [consumption, 2]
  ...
  1689:
    - [cancer, 2]
  1690:
    - [smallpox, 1]
    - [consumption, 1]
  1692:
    - [smallpox, 1]
  1693:
    - [smallpox, 1]
  1695:
    - [cancer, 5]
    - [consumption, 2]
  1697:
    - [smallpox, 1]
  1698:
    - [smallpox, 1]
