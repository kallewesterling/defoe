"""
Object model representation of ZIP archive of files in British Library Books-compliant ALTO format.

A ZIP archive corresponds to a document and each file to a page.

The ZIP archive is assumed to hold the following files and
directories:

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

from defoe.alto.archive import AltoArchive
import zipfile


class Archive(AltoArchive):
    """
    Object model representation of ZIP archive of files in
    British Library Books-compliant ALTO format.

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
        return r"([0-9]*)_metadata\.xml"

    def get_page_pattern(self) -> str:
        """
        Gets pattern to find filenames corresponding to individual pages.

        :return: Pattern
        :rtype: str
        """
        return r"ALTO\/([0-9]*?)_([0-9_]*)\.xml"

    def get_document_info(self, document_code: str) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about metadata file.

        :param document_code: Document file code
        :type document_code: str
        :return: File information
        :rtype: zipfile.ZipInfo
        """
        return self.zip.getinfo(f"{document_code}_metadata.xml")

    def get_page_info(
        self, document_code: str, page_code: str
    ) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about a page file.

        :param document_code: Page file code
        :type document_code: str
        :param page_code: File code
        :type page_code: str
        :return: File information
        :rtype: zipfile.ZipInfo
        """
        filename = f"ALTO/{document_code}_{page_code}.xml"
        return self.zip.getinfo(filename)

    def open_document(self, document_code: str) -> zipfile.ZipExtFile:
        """
        Opens metadata file.

        :param document_code: document file code
        :type document_code: str
        :return: Stream
        :rtype: zipfile.ZipExtFile
        """
        return self.zip.open(f"{document_code}_metadata.xml")

    def open_page(
        self, document_code: str, page_code: str
    ) -> zipfile.ZipExtFile:
        """
        Opens page file.

        :param document_code: Page file code
        :type document_code: str
        :param page_code: File code
        :type page_code: str
        :return: Stream
        :rtype: zipfile.ZipExtFile
        """
        filename = f"ALTO/{document_code}_{page_code}.xml"
        return self.zip.open(filename)
