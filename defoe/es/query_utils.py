"""
Query-related utility functions.
"""

from pyspark.sql.functions import col, when

import re


def get_sentences_list_matches(text: str, keysentence: list[str]) -> list[str]:
    """
    Check which key-sentences from occurs within a string
    and return the list of matches.

    :param text: Text
    :type text: str
    :param keysentence: Key sentence
    :type keysentence: list[str]
    :return: Sorted list of sentences
    :rtype: list[str]
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
            pattern = re.compile(rf"^{sentence}$")

            for word in text_list:
                if re.search(pattern, word):
                    matches.append(sentence)

    return sorted(matches)


def blank_as_null(x):
    return when(col(x) != "", col(x)).otherwise(None)
