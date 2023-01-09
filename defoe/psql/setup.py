"""
Given a filename create a dataframe.
"""
from __future__ import annotations

from pyspark.sql import SQLContext
from pyspark.sql import DataFrameReader


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
    :return: PySpark SQL DataFrame
    :rtype: pyspark.sql.dataframe.DataFrame
    """

    lines = open(filename).readlines()
    host, port, database, user, driver, table = lines[1].split(",")
    url = f"postgresql://{host}:{port}/{database}"

    sqlContext = SQLContext(context)

    df = DataFrameReader(sqlContext).jdbc(
        url=f"jdbc:{url}",
        table=table,
        properties={"user": user, "driver": driver},
    )

    return df
