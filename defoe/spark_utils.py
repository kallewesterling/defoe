"""
Spark-related file-handling utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from io import BytesIO, StringIO
import os

if TYPE_CHECKING:
    from pyspark.context import SparkContext
    from pyspark.rdd import RDD
    from typing import BinaryIO, Union

# Constants
ROOT_MODULE = "defoe"
SETUP_MODULE = "setup"
MODELS = [
    "books",
    "papers",
    "fmp",
    "nzpp",
    "generic_xml",
    "nls",
    "nlsArticles",
    "hdfs",
    "psql",
    "es",
]
HTTP = "http://"
HTTPS = "https://"
BLOB = "blob:"


def files_to_rdd(
    context: SparkContext, num_cores: int = 1, data_file: str = "data.txt"
) -> RDD:
    """
    Populate Spark RDD with file names or URLs over which a query is to be run.

    :param context: Spark Context
    :type context: pyspark.context.SparkContext
    :param num_cores: Number of cores over which to parallelize Spark job
    :type num_cores: int
    :param data_file: Name of file with file names or URLs, one per line
    :type data_file: str
    :return: A Resilient Distributed Dataset
    :rtype: pyspark.rdd.RDD
    """

    filenames = [filename.strip() for filename in list(open(data_file))]

    rdd_filenames = context.parallelize(filenames, num_cores)

    return rdd_filenames


# Note: This function was the same as the one above; keeping reference here
# for backwards compatibility
files_to_dataframe = files_to_rdd


def open_stream(filename: str) -> Union[StringIO, BytesIO, BinaryIO]:
    """
    Open a file and return a stream to the file.

    If filename starts with "http://" or "https://", the "file" is assumed to
    be a URL.

    If filename starts with "blob:", the "file" is assumed to be held in
    an Azure blob container. This expects three environment variables to be
    set: ``BLOB_SAS_TOKEN``, ``BLOB_ACCOUNT_NAME`` and ``BLOB_CONTAINER_NAME``.

    Otherwise, the filename is assumed to be held on the file system.

    :param filename: File name, URL, or blob path
    :type filename: str
    :raises SyntaxError: In case of an empty filename, the function will raise
        a SyntaxError.
    :return: Stream
    :rtype: Union[StringIO, BytesIO, BinaryIO]
    """

    if filename == "":
        raise SyntaxError("Filename must not be empty.")

    is_url = filename.lower().startswith(HTTP) or filename.lower().startswith(
        HTTPS
    )
    is_blob = filename.lower().startswith(BLOB)

    if is_url:
        stream = requests.get(filename, stream=True).raw
        stream.decode_content = True
        stream = StringIO(stream.read())

    elif is_blob:
        """
        TODO: Ensure azure is part of requirements or add an exception for
        ImportError here
        """
        from azure.storage.blob import BlobService

        SAS_TOKEN = os.environ["BLOB_SAS_TOKEN"]
        ACCOUNT_NAME = os.environ["BLOB_ACCOUNT_NAME"]
        CONTAINER_NAME = os.environ["BLOB_CONTAINER_NAME"]

        # TODO: Test that environment variable have been correctly set up here

        if SAS_TOKEN[0] == "?":
            SAS_TOKEN = SAS_TOKEN[1:]

        blob_service = BlobService(
            account_name=ACCOUNT_NAME, sas_token=SAS_TOKEN
        )
        start = len(BLOB)
        filename = filename[start:]
        blob = blob_service.get_blob_to_bytes(CONTAINER_NAME, filename)
        stream = BytesIO(blob)

    else:
        stream = open(filename, "rb")

    return stream
