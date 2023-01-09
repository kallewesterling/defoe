"""
Counts total number of documents.
"""


def do_query(archives, config_file=None, logger=None, context=None):
    """
    Iterate through archives and count total number of documents.
    Returns result of form:

        {"num_documents": num_documents}

    :param archives: RDD of defoe.fmp.archive.Archive
    :type archives: pyspark.rdd.PipelinedRDD
    :param config_file: Query configuration file (unused)
    :type config_file: str
    :param logger: Logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: total number of documents
    :rtype: dict
    """

    # [archive, archive, ...]
    documents = archives.flatMap(lambda archive: list(archive))

    num_documents = documents.count()

    return {"num_documents": num_documents}
