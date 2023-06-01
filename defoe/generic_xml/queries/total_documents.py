"""
Counts total number of documents.
"""


def do_query(documents, config_file=None, logger=None, context=None):
    """
    Iterate through documents and count total number of documents.
    Returns result of form:

        {"num_documents": num_documents}

    :param documents: RDD of defoe.generic_xml.document.Document
    :type documents: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file (unused)
    :type config_file: str or unicode
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: Total number of documents
    :rtype: dict
    """

    num_documents = documents.count()

    return {"num_documents": num_documents}
