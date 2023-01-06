"""
Object model representation of [ZIP] archive of files in ALTO format.

A [ZIP] archive corresponds to a document and each file to a page.

The [ZIP] archive is assumed to hold the following files and directories:
>    <METADATA_CODE>_metadata.xml
>    <METADATA_CODE>_metadata.xml
>    ...
>    ALTO/
>        <METADATA_CODE>_<FILE_CODE>.xml
>        <METADATA_CODE>_<FILE_CODE>.xml
>        ...
>        <METADATA_CODE>_<FILE_CODE>.xml
>        <METADATA_CODE>_<FILE_CODE>.xml
>        ...

where:

> <METADATA_CODE> is ``[0-9]*``
> <FILE_CODE> is ``[0-9_]*``
"""

from defoe.nls.archive_combine import AltoArchive
from defoe.spark_utils import open_stream
from typing import BinaryIO

import zipfile


class Archive(AltoArchive):
    """
    Object model representation of [ZIP] archive of files in ALTO format.

    :param filename: Archive filename
    :type: filename: str
    """

    def __init__(self, filename: str):
        """
        Constructor method.
        """
        AltoArchive.__init__(self, filename)

    def get_document_pattern(self) -> str:
        """
        Gets pattern to find metadata filename which has information about
        the document as a whole.

        :return: Pattern
        :rtype: str
        """
        return r"([0-9]*)[-_]met([[a-zA-Z]*)\.xml"

    def get_page_pattern(self) -> str:
        """
        Gets pattern to find filenames corresponding to individual pages.

        :return: Pattern
        :rtype: str
        """
        return r"(?i)alto\/([0-9]*)[^a-zA-Z0-9]([0-9]*)\.xml"

    def get_document_info(self, document_code: str) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about metadata file.

        :param document_code: document file code
        :type document_code: str
        :return: File information
        :rtype: zipfile.ZipInfo
        """
        return self.zip.getinfo(f"{document_code}-mets.xml")

    def get_page_info(
        self, document_code: str, page_code: str
    ) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about a page file.

        :param document_code: Document file code
        :type document_code: str
        :param page_code: Page file code
        :type page_code: str
        :return: File information
        :rtype: zipfile.ZipInfo
        """

        # TODO: Looks like page_code isn't used as a parameter. Remove?
        return self.zip.getinfo(document_code)

    def open_document(self, document_code: str) -> BinaryIO:
        """
        Opens metadata file.

        :param document_code: Document file code
        :type document_code: str
        :return: Stream
        """
        if ".zip" in self.filename:
            return self.zip.open(f"{document_code}-mets.xml")
        else:
            filename = f"{self.filename}/{document_code}-mets.xml"
            return open_stream(filename)

    def open_page(self, document_code: str, page_code: str) -> BinaryIO:
        """
        Opens page file.

        :param document_code: Document file code
        :type document_code: str
        :param page_code: Page file code
        :type page_code: str
        :return: Stream
        """

        # TODO: Looks like document_code isn't used as a parameter. Remove?
        if ".zip" in self.filename:
            return self.zip.open(page_code)
        else:
            return open_stream(self.filename + "/" + page_code)
