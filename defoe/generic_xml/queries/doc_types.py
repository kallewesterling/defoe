"""
Finds every unique document type (DOCTYPE) and its frequency.
"""

from operator import add


def do_query(documents, config_file=None, logger=None, context=None):
    """
    Finds every unique document type (DOCTYPE) and its frequency.

    Returns result of form:

        {
          <DOCTYPE>: <COUNT>,
          ...
        }

    :param documents: RDD of defoe.generic_xml.document.Document
    :type documents: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file (unused)
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: Unique document types and frequencies
    :rtype: dict
    """

    doc_types = documents.map(lambda document: (document.doc_type, 1))

    doc_type_counts = doc_types.reduceByKey(add).collect()

    return doc_type_counts
