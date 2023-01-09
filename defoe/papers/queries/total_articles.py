"""
Counts total number of articles.
"""

from operator import add


def do_query(issues, config_file=None, logger=None, context=None):
    """
    Iterate through issues and count total number of issues
    and total number of articles.

    Returns result of form:

        {
          "num_issues": num_issues,
          "num_articles": num_articles
        }

    :param issues: RDD of defoe.papers.issue.Issue
    :type issues: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file (unused)
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: total number of issues and articles
    :rtype: dict
    """

    # [num_articles, num_articles, ...]
    num_articles = issues.map(lambda issue: len(issue.articles))

    result = [issues.count(), num_articles.reduce(add)]

    return {"num_issues": result[0], "num_articles": result[1]}
