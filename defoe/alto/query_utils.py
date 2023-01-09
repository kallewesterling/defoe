"""
Query-related utility functions.
"""

from __future__ import annotations

from defoe import query_utils
from defoe.query_utils import PreprocessWordType

from nltk.corpus import words

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .document import Document
    from .page import Page
    from typing import Optional


def get_page_matches(
    document: Document,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> list[Optional[tuple[int, Document, Page, str]]]:
    """
    Get pages within a document that include one or more keywords. For each
    page that includes a specific keyword, add a tuple of form
    ``(<YEAR>, <DOCUMENT>, <PAGE>, <KEYWORD>)``.

    If a keyword occurs more than once on a page, there will be only one tuple
    for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple per
    keyword.

    If no keywords are found in the document, the returned list will be empty.

    :param document: Document
    :type document: defoe.alto.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: List of tuples consisting of the document's publication year, the
        document itself, the page on which the keyword was found, and the
        keyword found
    :rtype: list[Optional[tuple[int, Document, Page, str]]]
    """
    matches = []
    for keyword in keywords:
        for page in document:
            match = None
            for word in page.words:
                preprocessed_word = query_utils.preprocess_word(
                    word, preprocess_type
                )
                if preprocessed_word == keyword:
                    match = (document.year, document, page, keyword)
                    break
            if match:
                matches.append(match)
                continue  # move to next page
    return matches


def get_document_keywords(
    document: Document,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> list[str]:
    """
    Gets list of keywords occuring within an document.

    :param article: Document
    :type article: defoe.alto.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Sorted list of keywords that occur within article
    :rtype: list[str]
    """

    matches = set()

    for page in document:
        for word in page.words:
            preprocessed_word = query_utils.preprocess_word(
                word, preprocess_type
            )
            if preprocessed_word in keywords:
                matches.add(preprocessed_word)

    return sorted(list(matches))


def document_contains_word(
    document: Document,
    keyword: str,
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> bool:
    """
    Checks if a keyword occurs within a document.

    :param article: Document
    :type article: defoe.alto.document.Document
    :param keywords: Keyword
    :type keywords: str
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: ``True`` if the article contains the word, ``False`` otherwise
    :rtype: bool
    """

    for page in document:
        for word in page.words:
            preprocessed_word = query_utils.preprocess_word(
                word, preprocess_type
            )

            if keyword == preprocessed_word:
                return True

    return False


def calculate_words_within_dictionary(
    page: Page,
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> str:
    """
    Calculates the % of a given page's words within a dictionary (see
    ``nltk.corpus.words``). Page words are normalized.

    :param page: Page
    :type page: defoe.alto.page.Page
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :return: Percent of a given page's words that appear within a dictionary
    :rtype: str
    """

    # TODO: Should return a floating point value instead?

    dictionary = words.words()

    counter = 0
    total_words = 0

    for word in page.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)

        if preprocessed_word == "":
            continue

        total_words += 1

        if preprocessed_word in dictionary:
            counter += 1

    try:
        calculate_pc = str(counter * 100 / total_words)
    except:  # TODO: Change bare excepts to explicit
        calculate_pc = "0"

    return calculate_pc


def calculate_words_confidence_average(page: Page) -> str:
    """
    Calculates the word confidence average of a given page.

    :param page: Page
    :type page: defoe.alto.page.Page
    :return: Word confidence average for the provided page
    :rtype: str
    """

    # TODO: Should return a floating point value instead?

    total_wc = 0
    for wc in page.wc:
        total_wc += float(wc)

    try:
        calculate_wc = str(total_wc / len(page.wc))
    except:  # TODO: Change bare excepts to explicit
        calculate_wc = "0"

    return calculate_wc
