"""
Given a filename create a dataframe
"""

from __future__ import annotations

from pyspark.sql import SQLContext
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pyspark.context import SparkContext
    from pyspark.sql.dataframe import DataFrame


def filename_to_object(filename: str, context: SparkContext) -> DataFrame:
    """
    Given a filename create a defoe.books.archive.Archive.  If an error
    arises during its creation this is caught and returned as a
    string.

    :param filename: Filename
    :type filename: str
    :param context: Spark Context
    :type context: pyspark.context.SparkContext
    :return: A Pyspark SQL DataFrame
    :rtype: pyspark.sql.dataframe
    """

    data = open(filename).readline().rstrip()
    sqlContext = SQLContext(context)
    df = sqlContext.read.csv(data, header="true")

    return df
