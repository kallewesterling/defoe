"""
Query-related utility functions.
"""
from __future__ import annotations

from defoe import query_utils
from defoe.query_utils import (
    PreprocessWordType,
    longsfix_sentence,
    xml_geo_entities_snippet,
    georesolve_cmd,
    coord_xml_snippet,
    geomap_cmd,
    geoparser_cmd,
    geoparser_coord_xml,
)
from nltk.corpus import words
from typing import TYPE_CHECKING

import re
import spacy

if TYPE_CHECKING:
    from .archive import Archive
    from .document import Document
    from .page import Page

NON_AZ_REGEXP = re.compile("[^a-z]")


def get_pages_matches_no_prep(
    title: str,
    edition: str,
    archive: Archive,
    filename: str,
    text: str,
    keysentences: list[str],
) -> list[tuple[str, str, Archive, str, str, str]]:
    """
    Get pages within a document that include one or more keywords.
    For each page that includes a specific keyword, add a tuple of
    form:

        (<TITLE>, <EDITION>, <ARCHIVE>, <FILENAME>, <TEXT>, <KEYWORD>)

    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.
    If more than one keyword occurs on a page, there will be one tuple
    per keyword.

    :return: List of tuples
    """
    # FIXME: This function won't work because of undefined names below

    matches = []
    for keysentence in keysentences:
        # sentence_match = get_sentences_list_matches(text, keysentence)
        sentence_match_idx = get_text_keyword_idx(text, keysentence)
        if sentence_match:
            match = (title, edition, archive, filename, text, keysentence)
            matches.append(match)
    return matches


def get_page_matches(
    document: Document,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> list[tuple[int, Document, Page, str]]:
    """
    Get pages within a document that include one or more keywords.
    For each page that includes a specific keyword, add a tuple of
    form: ``(<YEAR>, <DOCUMENT>, <PAGE>, <KEYWORD>)``.

    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple
    per keyword.

    :param document: Document
    :type document: defoe.nls.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: List of tuples
    :rtype: list[tuple[int, Document, Page, str]]
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

    :param document: Document
    :type document: defoe.nls.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Sorted list of keywords that occur within document
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
    :type article: defoe.nls.document.Document
    :param keyword: Keyword
    :type keyword: str
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
    :type page: defoe.nls.page.Page
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :return: Percent of a given page's words that appear within a dictionary
    :rtype: str
    """
    dictionary = words.words()
    counter = 0
    total_words = 0
    for word in page.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)
        if preprocessed_word != "":
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
    Calculates the average of "words confidence (wc)" within a page.
    Page words are normalized.

    :param page: Page
    :type page: defoe.nls.page.Page
    :return: Word confidence average
    :rtype: str
    """

    total_wc = 0
    for wc in page.wc:
        total_wc += float(wc)

    try:
        wc_avg = str(total_wc / len(page.wc))
    except:  # TODO: Change bare excepts to explicit
        wc_avg = "0"

    return wc_avg


def get_page_as_string(
    page: Page,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> str:
    """
    Return a page as a single string.

    :param page: Page
    :type page: defoe.nls.Page
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Page words as a string
    :rtype: str
    """

    page_string = ""
    for word in page.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)

        if page_string == "":
            page_string = preprocessed_word
        else:
            page_string += " " + preprocessed_word

    return page_string


def clean_page_as_string(page: Page, defoe_path: str, os_type: str) -> str:
    """
    Clean a page as a single string.

    Handling hyphenated words: combine and split and also fixing the long-s.

    :param page: Page
    :type page: defoe.nls.Page
    :return: Clean page words as a string
    :rtype: str
    """
    page_string = ""
    for word in page.words:
        if page_string == "":
            page_string = word
        else:
            page_string += " " + word

    page_separated = page_string.split("- ")
    page_combined = "".join(page_separated)

    if (len(page_combined) > 1) and ("f" in page_combined):

        page_clean = longsfix_sentence(page_combined, defoe_path, os_type)
    else:
        page_clean = page_combined

    page_final = page_clean.split()
    page_string_final = ""
    for word in page_final:
        if "." not in word:
            separated_str = re.sub(
                r"([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))", r"\1 ", word
            )
        else:
            separated_str = word

        if page_string_final == "":
            page_string_final = separated_str
        else:
            page_string_final += " " + separated_str
    return page_string_final


def preprocess_clean_page(
    clean_page,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
):
    clean_list = clean_page.split(" ")
    page_string = ""
    for word in clean_list:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)
        if page_string == "":
            page_string = preprocessed_word
        else:
            page_string += " " + preprocessed_word
    return page_string


def get_sentences_list_matches(text: str, keysentence: list[str]) -> list[str]:
    """
    Check which key-sentences from occurs within a string and return the list
    of matches.

    :param text: Text
    :type text: str
    :param text: Keysentence
    :type text: list[str]
    :return: Sorted list of matching sentences
    :rtype: list[str]
    """

    matches = []
    text_list = text.split()
    for sentence in keysentence:
        if len(sentence.split()) > 1:
            if sentence in text:
                matches.append(sentence)

        else:
            pattern = re.compile(r"^%s$" % sentence)
            for word in text_list:
                if re.search(pattern, word) and (sentence not in matches):
                    matches.append(sentence)
    return sorted(matches)


def get_sentences_list_matches_per_page(
    text: str, keysentences: list[str]
) -> list[str]:
    """
    Gets a list the total list of keywords within an article.

    :param text: Text
    :type article: str
    :param keysentences: Sentences to match? TODO: Verify
    :type keysentences: list[str]
    :return: List of matching sentences
    :rtype: list[str]
    """
    matches = []
    text_list = text.split()
    for sentence in keysentences:
        if len(sentence.split()) > 1:
            if sentence in text:
                results = [
                    matches.start() for matches in re.finditer(sentence, text)
                ]
                for r in results:
                    matches.append(sentence)
        else:
            pattern = re.compile(r"^%s$" % sentence)
            for word in text_list:
                if re.search(pattern, word):
                    matches.append(sentence)
    return sorted(matches)


def preprocess_clean_page_spacy(
    clean_page,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
):
    # FIXME: Function does not work (overwritten by function with same name below)
    clean_list = clean_page.split(" ")
    page_string = ""
    for word in clean_list:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)
        if page_string == "":
            page_string = preprocessed_word
        else:
            page_string += " " + preprocessed_word
    return page_string


def preprocess_clean_page_spacy(clean_page: str):
    nlp = spacy.load("en")
    doc = nlp(clean_page)
    page_nlp_spacy = []
    for i, word in enumerate(doc):
        word_normalized = re.sub(NON_AZ_REGEXP, "", word.text.lower())
        output = "%d\t%s\t%s\t%s\t%s\t%s\t%s\t" % (
            i + 1,
            word,
            word_normalized,
            word.lemma_,
            word.pos_,
            word.tag_,
            word.ent_type_,
        )
        page_nlp_spacy.append(output)
    return page_nlp_spacy


def georesolve_page_2(text, lang_model, defoe_path, gazetteer, bounding_box):
    nlp = spacy.load(lang_model)
    doc = nlp(text)
    if doc.ents:
        flag, in_xml, snippet = xml_geo_entities_snippet(doc)
        if flag == 1:
            geo_xml = georesolve_cmd(
                in_xml, defoe_path, gazetteer, bounding_box
            )
            dResolved_loc = coord_xml_snippet(geo_xml, snippet)
            return dResolved_loc
        else:
            return {}
    else:
        return {}


def georesolve_page(doc):
    # FIXME: Function does not work (xml_geo_entities is not defined)

    if doc.ents:
        flag, in_xml = xml_geo_entities(doc)
        if flag == 1:
            geo_xml = georesolve_cmd(in_xml)
            dResolved_loc = coord_xml(geo_xml)
            return dResolved_loc
        else:
            return {}
    else:
        return {}


def geoparser_page(text, defoe_path, os_type, gazetteer, bounding_box):
    geo_xml = geoparser_cmd(text, defoe_path, os_type, gazetteer, bounding_box)
    dResolved_loc = geoparser_coord_xml(geo_xml)
    return dResolved_loc


def geomap_page(doc):
    # FIXME: Function does not work (xml_geo_entities is not defined)

    geomap_html = ""

    if doc.ents:
        flag, in_xml = xml_geo_entities(doc)

        if flag == 1:
            geomap_html = geomap_cmd(in_xml)

    return geomap_html


def get_text_keyword_idx(
    text: str, keywords: list[str]
) -> list[tuple[str, int]]:
    """
    Gets a list of keywords (and their position indices) within an
    article.

    :param text: Text
    :type article: str
    :param keywords: Keywords
    :type keywords: list[str]
    :return: Sorted list of keywords and their indices
    :rtype: list[tuple[str, int]]
    """
    text_list = text.split()
    matches = set()
    for idx, word in enumerate(text_list):
        if word in keywords:
            match = (word, idx)
            matches.add(match)
    return sorted(list(matches))


def get_text_keysentence_idx(
    text: str, keysentences: list[str]
) -> list[tuple[str, int]]:
    """
    Gets a list of keywords (and their position indices) within an article.

    :param text: Text
    :type article: str
    :param keysentences: Keywords
    :type keysentences: list[str]
    :return: Sorted list of keywords and their indices
    :rtype: list[tuple[str, int]]
    """
    matches = []
    text_list = text.split()
    for sentence in keysentences:
        if len(sentence.split()) > 1:
            if sentence in text:
                results = [
                    match.start() for match in re.finditer(sentence, text)
                ]
                for r in results:
                    idx = len(text[0:r].split())
                    match = (sentence, idx)
                    matches.append(match)
        else:
            pattern = re.compile(r"^%s$" % sentence)
            for idx, word in enumerate(text_list):
                if re.search(pattern, word):
                    match = (word, idx)
                    matches.append(match)
    return sorted(matches)


def get_concordance(
    text: str, keyword: str, idx: int, window: int
) -> list[str]:
    """
    For a given keyword (and its position in an article), return the
    concordance of words (before and after) using a window.

    :param text: Text
    :type text: str
    :param keyword: Keyword
    :type keyword: str
    :param idx: Keyword index (position) in list of article's words
    :type idx: int
    :param window: number of words to the right and left
    :type window: int
    :return: Concordance
    :rtype: list[str]
    """

    # FIXME: This function does not do what it says (keyword is not used)

    text_list = text.split()
    text_size = len(text_list)

    if idx >= window:
        start_idx = idx - window
    else:
        start_idx = 0

    if idx + window >= text_size:
        end_idx = text_size
    else:
        end_idx = idx + window + 1

    concordance_words = []
    for word in text_list[start_idx:end_idx]:
        concordance_words.append(word)
    return concordance_words


def get_concordance_string(
    text: str, keyword: str, idx: int, window: int
) -> str:
    """
    For a given keyword (and its position in an article), return
    the concordance of words (before and after) using a window.

    :param text: Text
    :type text: str
    :param keyword: Keyword
    :type keyword: str
    :param idx: Keyword index (position) in list of article's words
    :type idx: int
    :param window: number of words to the right and left
    :type window: int
    :return: Concordance
    :rtype: str
    """

    # FIXME: This function does not do what it says (keyword is not used)

    text_list = text.split()
    text_size = len(text_list)

    if idx >= window:
        start_idx = idx - window
    else:
        start_idx = 0

    if idx + window >= text_size:
        end_idx = text_size
    else:
        end_idx = idx + window + 1

    concordance_words = ""
    flag_first = 1
    for word in text_list[start_idx:end_idx]:
        if flag_first == 1:
            concordance_words += word
            flag_first = 0
        else:
            concordance_words += " " + word
    return concordance_words
