"""
Abstract base class for object model representation of ZIP archive of files in
ALTO format.
"""

from defoe.alto.document import Document
from defoe.spark_utils import open_stream
from typing import Iterator

import abc
import re
import zipfile


class AltoArchive(abc.ABCMeta("ABC", (object,), {})):
    """
    Abstract base class for object model representation of ZIP archive of
    files in ALTO format.

    :param filename: Archive filename
    :type: filename: str
    """

    def __init__(self, filename: str):
        """
        Constructor method.

        """
        self.filename = filename
        stream = open_stream(self.filename)
        self.zip = zipfile.ZipFile(stream)
        self.filenames = [entry.filename for entry in self.zip.infolist()]
        document_pattern = re.compile(self.get_document_pattern())
        page_pattern = re.compile(self.get_page_pattern())
        document_matches = [
            _f
            for _f in [document_pattern.match(name) for name in self.filenames]
            if _f
        ]
        page_matches = [
            _f
            for _f in [page_pattern.match(name) for name in self.filenames]
            if _f
        ]
        self.document_codes = {
            match.group(1): [] for match in document_matches
        }
        for match in page_matches:
            self.document_codes[match.group(1)].append(match.group(2))

    def __getitem__(self, index: int) -> Document:
        """
        Given a document index, return a new Document object.

        :param index: Document index
        :type index: int
        :return: Document object
        :rtype: defoe.alto.document.Document
        """
        return Document(list(self.document_codes.keys())[index], self)

    def __iter__(self) -> Iterator[Document]:
        """
        Iterate over document codes, creating Document objects.

        :return: Document object
        :rtype: Iterator[defoe.alto.document.Document]
        """
        for document in self.document_codes:
            yield Document(document, self)

    def __len__(self) -> int:
        """
        Gets number of documents in ZIP archive.

        :return: Number of documents
        :rtype: int
        """
        return len(self.document_codes)

    @abc.abstractmethod
    def get_document_pattern(self) -> str:
        """
        Gets pattern to find metadata filename which has information about the
        document as a whole.

        :return: Pattern
        :rtype: str
        """
        return

    @abc.abstractmethod
    def get_page_pattern(self) -> str:
        """
        Gets pattern to find filenames corresponding to individual pages.

        :return: Pattern
        :rtype: str
        """
        return

    @abc.abstractmethod
    def get_document_info(self, document_code: str) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about metadata file.

        :param document_code: Document file code
        :type document_code: str
        :return: File information
        :rtype: zipfile.ZipInfo
        """
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
    def open_document(self, document_code: str) -> zipfile.ZipExtFile:
        """
        Opens metadata file.

        :param document_code: Document file code
        :type document_code: str
        :return: Stream
        :rtype: zipfile.ZipExtFile
        """
        return

    @abc.abstractmethod
    def open_page(
        self, document_code: str, page_code: str
    ) -> zipfile.ZipExtFile:
        """
        Opens page file.

        :param document_code: Document file code
        :type document_code: str
        :param page_code: Page file code
        :type page_code: str
        :return: Stream
        :rtype: zipfile.ZipExtFile
        """
        return
