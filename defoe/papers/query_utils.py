"""
Query-related utility functions.
"""
from __future__ import annotations

from nltk.corpus import stopwords

from defoe import query_utils
from defoe.query_utils import PreprocessWordType, longsfix_sentence
from defoe.query_utils import PreprocessWordType
from typing import TYPE_CHECKING

import re

if TYPE_CHECKING:
    from .article import Article
    from .issue import Issue
    import datetime


def get_article_matches(
    issue: Issue,
    keysentences: list[str],
    defoe_path: str,
    os_type: str,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> list[tuple[datetime.date, Issue, Article, str, str]]:
    """
    Get articles within an issue that include one or more keywords.
    For each article that includes a specific keyword, add a tuple of
    form: ``(<DATE>, <ISSUE>, <ARTICLE>, <KEYWORD>)``

    If a keyword occurs more than once in an article, there will be
    only one tuple for the article for that keyword.

    If more than one keyword occurs in an article, there will be one
    tuple per keyword.

    :param issue: Issue
    :type issue: defoe.papers.issue.Issue
    :param keysentences: Key sentences
    :type keysentences: list[str]
    :param defoe_path: TODO
    :type defoe_path: str
    :param os_type: TODO
    :type os_type: str
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: List of tuples consisting of the issue's date, the issue, the
        article, the key sentence and the cleaned article text
    :rtype: list[tuple[datetime.date, Issue, Article, str, str]]
    """

    matches = []
    for keysentence in keysentences:
        for article in issue:
            sentence_match = None
            clean_article = clean_article_as_string(
                article, defoe_path, os_type
            )
            preprocess_article = preprocess_clean_article(
                clean_article, preprocess_type
            )
            sentence_match = get_sentences_list_matches(
                preprocess_article, keysentence
            )

            if sentence_match:
                match = (
                    issue.date.date(),
                    issue,
                    article,
                    keysentence,
                    clean_article,
                )
                matches.append(match)

    return matches


def get_article_keywords(
    article: Article,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> list[str]:
    """
    Get list of keywords occuring within an article.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Sorted list of unique keywords that occur within the article
    :rtype: list[str]
    """
    matches = set()
    for word in article.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)
        if preprocessed_word in keywords:
            matches.add(preprocessed_word)
    return sorted(list(matches))


def article_contains_word(
    article: Article,
    keyword: str,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> bool:
    """
    Check if a keyword occurs within an article.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param keyword: Keyword
    :type keyword: str
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: True if the article contains the word, false otherwise
    :rtype: bool
    """

    for word in article.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)
        if keyword == preprocessed_word:
            return True

    return False


def article_stop_words_removal(
    article: Article,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> list[str]:
    """
    Remove the stop words of an article.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param preprocess_type: How words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: List of article words without stop words
    :rtype: list[str]
    """

    stop_words = set(stopwords.words("english"))

    article_words = []
    for word in article.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)

        if preprocessed_word not in stop_words:
            article_words.append(preprocessed_word)

    return article_words


def get_article_as_string(
    article: Article,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> str:
    """
    Return an article as a single string.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param preprocess_type: How words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Article words as a string
    :rtype: str
    """
    article_string = ""
    for word in article.words:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)
        if article_string == "":
            article_string = preprocessed_word
        else:
            article_string += " " + preprocessed_word
    return article_string


def get_sentences_list_matches_2(
    text: str, keysentence: list[str]
) -> list[str]:
    """
    Check which key-sentences from occurs within a string and return the list
    of matches.

    :param text: Text
    :type text: str
    :param keysentence: Sentences
    :type keysentence: list[str]
    :return: Sorted list of matching sentences
    :rtype: list[str]
    """
    match = set()
    for sentence in keysentence:
        if sentence in text:
            match.add(sentence)
    return sorted(list(match))


def get_article_keyword_idx(
    article: Article,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> list[tuple[str, int]]:
    """
    Gets a list of keywords (and their position indices) within an article.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Sorted list of keywords and their indices
    :rtype: list[tuple[str,int]]
    """

    matches = set()
    for idx, word in enumerate(article.words):
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)

        if preprocessed_word in keywords:
            match = (preprocessed_word, idx)
            matches.add(match)

    return sorted(list(matches))


def get_concordance(
    article: Article,
    keyword: str,
    idx: int,
    window: int,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> list[str]:
    """
    For a given keyword (and its position in an article), return
    the concordance of words (before and after) using a window.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param keyword: Keyword
    :type keyword: str
    :param idx: Keyword index (position) in list of article's words
    :type idx: int
    :param window: number of words to the right and left
    :type window: int
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Concordance
    :rtype: list[str]
    """
    article_size = len(article.words)

    if idx >= window:
        start_idx = idx - window
    else:
        start_idx = 0

    if idx + window >= article_size:
        end_idx = article_size
    else:
        end_idx = idx + window + 1

    concordance_words = []
    for word in article.words[start_idx:end_idx]:
        concordance_words.append(
            query_utils.preprocess_word(word, preprocess_type)
        )
    return concordance_words


def clean_article_as_string(
    article: Article, defoe_path: str, os_type: str
) -> str:
    """
    Clean a article as a single string.

    Handling hyphenated words: combine and split and also fixing the long-s.

    :param article: Article
    :type article: defoe.papers.article.Article
    :return: Clean article words as a string
    :rtype: str
    """
    article_string = ""
    for word in article.words:
        if article_string == "":
            article_string = word
        else:
            article_string += " " + word

    article_separete = article_string.split("- ")
    article_combined = "".join(article_separete)

    if (len(article_combined) > 1) and ("f" in article_combined):
        article_clean = longsfix_sentence(
            article_combined, defoe_path, os_type
        )
        return article_clean
    else:
        return article_combined


def preprocess_clean_article(
    clean_article: str,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
) -> str:
    """
    TODO
    """

    clean_list = clean_article.split(" ")

    article_string = ""
    for word in clean_list:
        preprocessed_word = query_utils.preprocess_word(word, preprocess_type)

        if article_string == "":
            article_string = preprocessed_word
        else:
            article_string += " " + preprocessed_word

    return article_string


def get_sentences_list_matches(text: str, keysentence: list[str]) -> list[str]:
    """
    Check which key-sentences from occurs within a string
    and return the list of matches.

    Term count: The query counts as a “hint” every time that finds a term from
    our lexicon in the previously selected articles (by the target words
    and/or time period). So, if a term is repeated 10 times in an article, it
    will be counted as 10. In this way, we are basically calculating the
    "frequency of terms" over time.

    :param text: Text
    :type text: str
    :type keysentence: list[str]
    :return: Set of sentences
    :rtype: list[str]
    """
    matches = []
    text_list = text.split()
    for sentence in keysentence:
        if len(sentence.split()) > 1:
            if sentence in text:
                count = text.count(sentence)
                for i in range(0, count):
                    matches.append(sentence)
        else:
            pattern = re.compile(r"^%s$" % sentence)
            for word in text_list:
                if re.search(pattern, word):
                    matches.append(sentence)
    return sorted(matches)


def get_articles_list_matches(text: str, keysentence: list[str]) -> list[str]:
    """
    Article count: The query counts as a “hint” every time that finds an
    article with a particular term from our lexicon in the previously selected
    articles (by the target words or/and time period).  So, if a term is
    repeated several times in an article, it will be counted just as ONE. In
    this way, we are basically calculating the “frequency of articles” over
    time.

    Check which key-sentences from occurs within a string and return the list
    of matches.

    :param text: Text
    :type text: str
    :param keysentence: List of key sentences
    :type keysentence: list[str]
    :return: Sorted list of matching sentences
    :rtype: list[str]
    """

    text_list = text.split()

    matches = []
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


def get_articles_text_matches(text: str, keysentence: list[str]) -> list[str]:
    """
    Article count: The query counts as a “hint” every time that finds an
    article with a particular term from our lexicon in the previously selected
    articles (by the target words or/and time period).  So, if a term is
    repeated several times in an article, it will be counted just as ONE. In
    this way, we are basically calculating the “frequency of articles” over
    time.

    Check which key-sentences from occurs within a string and return the list
    of matches.

    :param text: Text
    :type text: str
    :type keysentence: list[str]
    :return: Sorted list of matching sentences
    :rtype: list[str]
    """
    match_text = {}
    for sentence in keysentence:
        if len(sentence.split()) > 1:
            if sentence in text:
                if sentence not in match_text:
                    match_text[sentence] = text
        else:
            text_list = text.split()
            pattern = re.compile(r"^%s$" % sentence)
            for word in text_list:
                if re.search(pattern, word) and (sentence not in match_text):
                    match_text[sentence] = text
    return match_text
