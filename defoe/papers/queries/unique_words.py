"""
Finds every unique word and its frequency.
"""

from defoe import query_utils

from operator import add


def do_query(issues, config_file=None, logger=None, context=None):
    """
    Finds every unique word and its frequency.

    config_file can be the path to a configuration file with a
    threshold, the minimum number of occurrences of the word for the
    word to be counted. This file, if provided, must be of form:

        threshold: <COUNT>

    where <COUNT> is >= 1.

    If no configuration file is provided then a threshold of 1 is
    assumed.

    Words in documents are normalized, by removing all non-'a-z|A-Z'
    characters.

    Returns result of form:

        {
            <WORD>: <COUNT>,
            ...
        }

    :param issues: RDD of defoe.papers.issue.Issue
    :type issues: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file (optional)
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: total number of issues and words
    :rtype: dict
    """

    config = query_utils.get_config(config_file, optional=True)
    value = config.get("threshold", 1)
    threshold = max(1, value)

    # [article, article, ...]
    articles = issues.flatMap(
        lambda issue: [article for article in issue.articles]
    )

    # [(word, 1), (word, 1), ...]
    words = articles.flatMap(
        lambda article: [
            (query_utils.normalize(word), 1) for word in article.words
        ]
    )

    # [(word, 1), (word, 1), ...]
    # =>
    # [(word, count), (word, count), ...]
    word_counts = (
        words.reduceByKey(add)
        .filter(lambda word_year: word_year[1] > threshold)
        .collect()
    )

    return word_counts
