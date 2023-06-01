"""
Gets colocated words and groups by year.
"""
from __future__ import annotations

from defoe import query_utils
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..issue import Issue
    from py4j.java_gateway import JavaObject
    from pyspark import SparkContext
    from pyspark.rdd import RDD


def do_query(
    issues: RDD[Issue],
    config_file: str = None,
    logger: JavaObject = None,
    context: SparkContext = None,
):
    """
    Gets colocated words and groups by year.

    config_file must be the path to a configuration file with the
    words to be searched for and the maximum number of intervening
    words (a "window"). This file must be a YAML document of form:

        start_word: <WORD>
        end_word: <WORD>
        window: <WINDOW>

    where <WINDOW> is greater than or equal to 0. If omitted then a
    default of 0 is assumed.

    Both colocated words and words in articles are normalized, by
    removing all non-``a-z|A-Z``|non-``a-z|A-Z`` characters.

    Returns result of form:

        {
            <YEAR>:
                [
                    {
                        "article_id": <ARTICLE_ID>,
                        "issue_id": <ISSUE_ID>,
                        "page_ids": <PAGE_IDS>,
                        "filename": <FILENAME>,
                        "matches":
                            [
                                [<WORD>, ..., <WORD>],
                                ...
                            ]
                    },
                    ...
                ],
            <YEAR>:
                ...
        }

    :param issues: RDD of defoe.alto.issue.Issue
    :type issues: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: Information on articles in which keywords occur grouped
    by year
    :rtype: dict
    :raises ValueError: if window is not larger than or equal to 0
    """

    config = query_utils.get_config(config_file)

    start_word = query_utils.normalize(config["start_word"])
    end_word = query_utils.normalize(config["end_word"])
    window = config["window"]
    if window < 0:
        raise ValueError("window must be at least 0")

    # [(issue, article), ...]
    issue_articles = issues.flatMap(
        lambda issue: [(issue, article) for article in issue.articles]
    )

    # [(issue, article, matches), ...]
    colocated_words = issue_articles.map(
        lambda issue_article: (
            issue_article[0],
            issue_article[1],
            get_colocates_matches(
                issue_article[1], start_word, end_word, window
            ),
        )
    )

    # [(issue, article, matches), ...]
    colocated_words = colocated_words.filter(
        lambda issue_article_matches: len(issue_article_matches[2]) > 0
    )

    # [(issue, article, matches), ...]
    # =>
    # [(year, {"title": title, ...}), ...]
    matching_articles = colocated_words.map(
        lambda issue_article_matches: (
            issue_article_matches[0].date.year,
            {
                "title": issue_article_matches[1].title_string,
                "article_id": issue_article_matches[1].article_id,
                "page_ids": list(issue_article_matches[1].page_ids),
                "issue_id": issue_article_matches[0].newspaper_id,
                "filename": issue_article_matches[0].filename,
                "matches": issue_article_matches[2],
            },
        )
    )

    # [(year, {"title": title, ...}), ...]
    # =>
    # [(year, [{"title": title, ...], {...}), ...)]
    result = (
        matching_articles.groupByKey()
        .map(lambda year_context: (year_context[0], list(year_context[1])))
        .collect()
    )

    return result


def get_colocates_matches(article, start_word, end_word, window=0):
    """
    Get text within an article that include colocates, one word
    followed by another word, with 0 or more intervening words.

    A list of lists of each span of text, '<START_WORD>
    ... <END_WORD>', delimited by the colocates, is returned.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param start_word: Start_word colocate
    :type start_word: str or unicode
    :param end_word: End_word colocate
    :type end_word: str or unicode
    :return: List of lists of words
    :rtype: list(list(str or unicode))
    """

    window_plus_colocates = window + 2

    in_span = False
    span = []
    span_length = 0
    matches = []
    for word in article.words:
        normalized_word = query_utils.normalize(word)

        if not normalized_word:
            continue

        if normalized_word == start_word:
            in_span = True
            span = []
            span_length = 0

        if in_span:
            span.append(normalized_word)
            span_length += 1

            if span_length > window_plus_colocates:
                in_span = False
                span = []
                span_length = 0
                continue

            if normalized_word == end_word:
                matches.append(span)
                in_span = False
                span = []
                span_length = 0

    return matches
