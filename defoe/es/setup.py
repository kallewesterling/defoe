"""
Given a filename create a dataframe
"""
from __future__ import annotations

from pyspark.sql import SQLContext
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pyspark.context import SparkContext


def filename_to_object(filename: str, context: SparkContext):
    """
    Given a filename create a defoe.books.archive.Archive.  If an error
    arises during its creation this is caught and returned as a
    string.

    :param filename: Filename
    :type filename: str
    :param context: Spark Context
    :type context: pyspark.context.SparkContext
    :return: #TODO
    :rtype: #TODO
    """

    lines = open(filename).readlines()
    es_index, es_host, es_port = lines[1].split(",")
    es_port = es_port.rstrip("\n")

    print(f"es_index {es_index}, es_host {es_host}, es_port {es_port}")

    sqlContext = SQLContext(context)
    reader = (
        sqlContext.read.format("org.elasticsearch.spark.sql")
        .option("es.read.metadata", "true")
        .option("es.nodes.wan.only", "true")
        .option("es.port", es_port)
        .option("es.net.ssl", "false")
        .option("es.nodes", "http://" + es_host)
    )
    df = reader.load(es_index)

    return df
