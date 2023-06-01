"""
Get concordance (also called details) of articles in which we have keywords or
keysentences. Group results by year. This query is the recommended to use when
there are not target words.
"""
from __future__ import annotations

from ..query_utils import (
    preprocess_clean_article,
    clean_article_as_string,
    get_articles_list_matches,
)

from defoe import query_utils
from typing import TYPE_CHECKING

import os

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
    Select the articles text along with metadata by using a list of keywords
    or keysentences and groups by year.

    config_file must be the path to a lexicon file with a list of the keywords
    to search for, one per line.

    Also the config_file can indicate the preprocess treatment, along with the
    Defoe path, and the type of operating system.

    Returns result of form:

        {
            <YEAR>:
                [
                    [
                        article_id: ...
                        authors: ...
                        filename: ...
                        issue_id: ...
                        page_ids: ...
                        text: ...
                        term: ...
                        title: ...
                    ],
                    ...
                ],
            <YEAR>:
                ...
        }

    :param issues: RDD of defoe.papers.issue.Issue
    :type archives: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: Number of occurrences of keywords grouped by year
    :rtype: dict
    """

    config = query_utils.get_config(config_file)

    if "os_type" in config:
        if config["os_type"] == "linux":
            os_type = "sys-i386-64"
        else:
            os_type = "sys-i386-snow-leopard"
    else:
        os_type = "sys-i386-64"

    if "defoe_path" in config:
        defoe_path = config["defoe_path"]
    else:
        defoe_path = "./"

    preprocess_type = query_utils.extract_preprocess_word_type(config)
    data_file = query_utils.extract_data_file(
        config, os.path.dirname(config_file)
    )

    keysentences = []
    with open(data_file, "r") as f:
        for keysentence in list(f):
            k_split = keysentence.split()
            sentence_word = [
                query_utils.preprocess_word(word, preprocess_type)
                for word in k_split
            ]
            sentence_norm = ""
            for word in sentence_word:
                if sentence_norm == "":
                    sentence_norm = word
                else:
                    sentence_norm += " " + word
            keysentences.append(sentence_norm)

    # [(year, issue, article, clean_article_string), ...]
    clean_articles = issues.flatMap(
        lambda issue: [
            (
                issue.date.year,
                issue,
                article,
                clean_article_as_string(article, defoe_path, os_type),
            )
            for article in issue.articles
        ]
    )

    # [(year, issue, article, preprocessed_article_string), ...]
    t_articles = clean_articles.flatMap(
        lambda cl_article: [
            (
                cl_article[0],
                cl_article[1],
                cl_article[2],
                preprocess_clean_article(cl_article[3], preprocess_type),
            )
        ]
    )

    # Filter only where preprocessed_article_string has correspondence in any
    # of keysentences
    filter_articles = t_articles.filter(
        lambda year_article: any(
            keysentence in year_article[3] for keysentence in keysentences
        )
    )

    # [(year, issue, article, [keysentence, keysentence]), ...]
    # Note: get_articles_list_matches ---> articles count
    # Note: get_sentences_list_matches ---> word_count
    matching_articles = filter_articles.map(
        lambda year_article: (
            year_article[0],
            year_article[1],
            year_article[2],
            get_articles_list_matches(year_article[3], keysentences),
        )
    )

    # [(year, issue, article, keysentence), ...]
    matching_sentences = matching_articles.flatMap(
        lambda year_sentence: [
            (year_sentence[0], year_sentence[1], year_sentence[2], sentence)
            for sentence in year_sentence[3]
        ]
    )

    # [(year, {"title": <title>, "article_id": article_id, ...}, ...]
    matching_data = matching_sentences.map(
        lambda sentence_data: (
            sentence_data[0],
            {
                "title": sentence_data[2].title_string,
                "article_id:": sentence_data[2].article_id,
                "authors:": sentence_data[2].authors_string,
                "page_ids": list(sentence_data[2].page_ids),
                "term": sentence_data[3],
                "original text": sentence_data[2].words_string,
                "issue_id": sentence_data[1].newspaper_id,
                "filename": sentence_data[1].filename,
            },
        )
    )

    # [(year, {"title": <title>, "article_id": article_id, ...}, ...]
    # =>
    result = (
        matching_data.groupByKey()
        .map(lambda date_context: (date_context[0], list(date_context[1])))
        .collect()
    )

    return result
