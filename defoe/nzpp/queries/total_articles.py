"""
Counts total number of articles.
"""

from operator import add


def do_query(all_articles, config_file=None, logger=None, context=None):
    """
    Count total number of articles.

    Returns result of form:

        { "num_articles": num_articles }

    :param all_articles: RDD of defoe.nzpp.articles.Articles
    :type all_articles: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file (unused)
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: Total number of articles
    :rtype: dict
    """

    # [num_articles, num_articles, ...]
    num_articles = all_articles.map(lambda articles: len(articles.articles))

    result = num_articles.reduce(add)

    return {"num_articles": result}
