"""
Object model representation of archive of files in METS/ALTO format compliant
with Find My Past's newspapers.

An archive corresponds to either a ZIP file or directory containing a file
representing the metadata (METS) and any given files representing the page/s
(ALTO).
"""

from __future__ import annotations

from .archive_combine import AltoArchive
from .constants import IMAGE_TYPES

from defoe.spark_utils import open_stream
from pathlib import Path
from PIL import Image
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import zipfile
    from typing import BinaryIO, Optional


class Archive(AltoArchive):
    """
    Object model representation of archive of files in ALTO format compliant
    with Find My Past's newspapers.

    Usage:

    .. code-block:: python

        from defoe.fmp.archive import Archive
        archive = Archive("path/to/xml-files/")

    :param path: path to a ZIP filename or directory containing the necessary
        files
    :type path: str
    """

    def __init__(self, path: str):
        """
        Constructor method.
        """
        AltoArchive.__init__(self, path)

    def get_document_pattern(self) -> str:
        """
        Gets pattern to find metadata filename which has information about the
        document as a whole.

        :return: Pattern
        :rtype: str
        """
        return r"([0-9]*?_[0-9]*?)_mets\.xml"

    def get_page_pattern(self) -> str:
        """
        Gets pattern to find filenames corresponding to individual pages.

        :return: Pattern
        :rtype: str
        """
        return r"([0-9]*?_[0-9]*?)_([0-9_]*)\.xml"

    def get_document_info(
        self, document_code: str
    ) -> Optional[zipfile.ZipInfo]:
        """
        Gets information from ZIP file about metadata file.

        :param document_code: Document file code
        :type document_code: str
        :return: Information, if available
        :rtype: Optional[:class:`zipfile.ZipInfo`]
        """
        if ".zip" in self.filename:
            return self.zip.getinfo(f"{document_code}_mets.xml")
        else:
            return None

    def get_page_info(
        self, document_code: str, page_code: str
    ) -> Optional[zipfile.ZipInfo]:
        """
        Gets information from ZIP file about a page file.

        :param document_code: Page file code
        :type document_code: str
        :param page_code: File code
        :type page_code: str
        :return: Information, if available
        :rtype: Optional[:class:`zipfile.ZipInfo`]
        """
        if ".zip" in self.filename:
            filename = f"{document_code}_{page_code}.xml"
            return self.zip.getinfo(filename)

        return None

    def open_document(self, document_code) -> BinaryIO:
        """
        Opens metadata file.

        :param document_code: Document file code
        :type document_code: str
        :return: File stream
        :rtype: BinaryIO
        """
        if ".zip" in self.filename:
            return self.zip.open(f"{document_code}_mets.xml")

        mets_file = f"{self.filename}/{document_code}_mets.xml"
        return open_stream(mets_file)

    def open_page(self, document_code, page_code) -> BinaryIO:
        """
        Opens page file.

        :param document_code: Page file code
        :type document_code: str
        :param page_code: File code
        :type page_code: str
        :return: File stream
        :rtype: BinaryIO
        """
        if ".zip" in self.filename:
            filename = f"{document_code}_{page_code}.xml"
            return self.zip.open(filename)

        filename = f"{self.filename}/{document_code}_{page_code}.xml"
        return open_stream(filename)

    def get_image_path(self, document_code, page_code) -> Optional[str]:
        """
        Returns path to image file for a given ``defoe.fmp.document.Document``
        and ``defoe.fmp.page.Page`` in the ``defoe.fmp.archive.Archive``.

        :param document_code: Page file code
        :type document_code: str
        :param page_code: File code
        :type page_code: str
        :return: Image path
        :rtype: Optional[str]
        :raises RuntimeError: if multiple image paths are found for the
            same page
        """

        stem = f"{self.filename}{document_code}_{page_code}"

        test = [
            f"{stem}{ext}"
            for ext in IMAGE_TYPES
            if Path(f"{stem}{ext}").exists()
        ]

        if len(test) == 1:
            return test[0]
        elif len(test) > 1:
            files = ", ".join(test)
            raise RuntimeError(f"Multiple possible images found: {files}")

        return None

    def open_image(self, document_code, page_code) -> Image.Image:
        """
        Returns the open image file for a given ``defoe.fmp.document.Document``
        and ``defoe.fmp.page.Page`` in the ``defoe.fmp.archive.Archive``.

        :param document_code: Page file code
        :type document_code: str
        :param page_code: File code
        :type page_code: str
        :return: Page image
        :rtype: PIL.Image.Image
        """

        return Image.open(self.get_image_path(document_code, page_code))
