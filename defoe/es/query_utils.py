"""
Query-related utility functions.
"""

from pyspark.sql.functions import col, when

import re


def get_sentences_list_matches(text, keysentence):
    """
    Check which key-sentences from occurs within a string
    and return the list of matches.

    :param text: text
    :type text: str or unicode
    :type: list(str or uniocde)
    :return: Set of sentences
    :rtype: set(str or unicode)
    """
    text_list = text.split()

    matches = []
    for sentence in keysentence:
        if len(sentence.split()) > 1:
            if sentence in text:
                count = text.count(sentence)

                for _ in range(0, count):
                    matches.append(sentence)
        else:
            pattern = re.compile(r"^%s$" % sentence)

            for word in text_list:
                if re.search(pattern, word):
                    matches.append(sentence)

    return sorted(matches)


def blank_as_null(x):
    return when(col(x) != "", col(x)).otherwise(None)
