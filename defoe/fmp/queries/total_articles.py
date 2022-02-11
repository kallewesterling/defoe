"""
Counts total number of pages.
"""

from operator import add


def do_query(archives, config_file=None, logger=None, context=None):
    """
    Iterate through archives and count total number of documents
    and total number of pages.

    Returns result of form:

        {
          "num_documents": num_documents,
          "num_articles": num_articles
        }

    :param archives: RDD of defoe.fmp.archive.Archive
    :type archives: pyspark.rdd.PipelinedRDD
    :param config_file: query configuration file (unused)
    :type config_file: str or unicode
    :param logger: logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: total number of documents and pages
    :rtype: dict
    """
    # [archive, archive, ...]
    documents = archives.flatMap(lambda archive: list(archive))
    print("num documents %s" % documents.count())
    # [num_articles, num_articles, ...]
    num_articles = documents.map(lambda document: document.num_articles)
    result = [documents.count(), num_articles.reduce(add)]
    return {"num_documents": result[0], "num_articles": result[1]}
