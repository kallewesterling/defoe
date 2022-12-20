"""
Object model representation of a ZIP or UNZIP archive of files in
Find My Past Newspapers-compliant ALTO format.

A archive corresponds to a document and each file to a page.

The archive is assumed to hold the following files:

    <METADATA_CODE>_mets.xml
    <METADATA_CODE>_<FILE_CODE>.xml
    <METADATA_CODE>_<FILE_CODE>.xml
    ...
    <METADATA_CODE>_mets.xml
    <METADATA_CODE>_<FILE_CODE>.xml
    <METADATA_CODE>_<FILE_CODE>.xml
    ...

where:

* <METADATA_CODE> is [0-9]*?_[0-9]*?
* <FILE_CODE> is [0-9_]*
"""

from .archive_combine import AltoArchive
from .constants import NAMESPACES
from .article import Article
from defoe.spark_utils import open_stream

from lxml import etree
from pathlib import Path
from PIL import Image
import mimetypes

mimetypes.init()
image_types = [
    type
    for type, desc in mimetypes.types_map.items()
    if desc.split("/")[0] == "image"
]


class Archive(AltoArchive):
    """
    Object model representation of archive of files in
    Find My Past Newspapers-compliant ALTO format.
    """

    def __init__(self, filename):
        """
        Constructor

        :param filename: archive filename
        :type: filename: str
        """
        AltoArchive.__init__(self, filename)

    def get_document_pattern(self):
        """
        Gets pattern to find metadata filename which has information about
        the document as a whole.

        :return: pattern
        :rtype: str
        """
        return "([0-9]*?_[0-9]*?)_mets\.xml"  # pylint: disable=anomalous-backslash-in-string # noqa

    def get_page_pattern(self):
        """
        Gets pattern to find filenames corresponding to individual pages.

        :return: pattern
        :rtype: str
        """
        return "([0-9]*?_[0-9]*?)_([0-9_]*)\.xml"  # pylint: disable=anomalous-backslash-in-string  # noqa

    def get_document_info(self, document_code):
        """
        Gets information from ZIP file about metadata file.

        :param document_code: document file code
        :type document_code: str
        :return: information
        :rtype: zipfile.ZipInfo
        """
        if ".zip" in self.filename:
            return self.zip.getinfo(document_code + "_mets.xml")
        else:
            return

    def get_page_info(self, document_code, page_code):
        """
        Gets information from ZIP file about a page file.

        :param document_code: page file code
        :type document_code: str
        :param page_code: file code
        :type page_code: str
        :return: information
        :rtype: zipfile.ZipInfo
        """
        if ".zip" in self.filename:
            return self.zip.getinfo(document_code + "_" + page_code + ".xml")
        else:
            return

    def open_document(self, document_code):
        """
        Opens metadata file.

        :param document_code: document file code
        :type document_code: str
        :return: stream
        """
        if ".zip" in self.filename:
            return self.zip.open(document_code + "_mets.xml")
        else:
            return open_stream(
                self.filename + "/" + document_code + "_mets.xml"
            )

    def open_page(self, document_code, page_code):
        """
        Opens page file.

        :param document_code: page file code
        :type document_code: str
        :param page_code: file code
        :type page_code: str
        :return: stream
        :rtype: zipfile.ZipExt
        """
        if ".zip" in self.filename:
            return self.zip.open(document_code + "_" + page_code + ".xml")
        else:
            return open_stream(
                self.filename + "/" + document_code + "_" + page_code + ".xml"
            )

    def get_image_path(self, document_code, page_code):
        """
        Get path to image file.

        :param document_code: page file code
        :type document_code: str
        :param page_code: file code
        :type page_code: str
        :return: image path
        :rtype: str
        """

        stem = self.filename + document_code + "_" + page_code

        test = [
            f"{stem}{ext}"
            for ext in image_types
            if Path(f"{stem}{ext}").exists()
        ]

        if len(test) == 1:
            return test[0]
        elif len(test) > 1:
            raise RuntimeError(
                "Multiple possible images found: " + ", ".join(test)
            )
        else:
            return None

    def open_image(self, document_code, page_code):
        """
        Open image file.

        :param document_code: page file code
        :type document_code: str
        :param page_code: file code
        :type page_code: str
        :return: image
        :rtype: PIL.Image.Image
        """

        path = self.get_image_path(document_code, page_code)
        return Image.open(path)

    @property
    def articles(self, document_codes=[]):
        if not document_codes:
            document_codes = self.document_codes

        for document_code in document_codes:
            metadata = self.open_document(document_code)
            metadata_tree = etree.parse(metadata)

            struct_map = metadata_tree.find(
                'mets:structMap[@TYPE="PHYSICAL"]', NAMESPACES
            )

            for div in struct_map:
                parts = div.findall('mets:div[@TYPE="page"]', NAMESPACES)
                for part in parts:
                    metadata_parts = part.findall("mets:div", NAMESPACES)
                    for metadata_part in metadata_parts:
                        (
                            area_id,
                            area_type,
                            area_category,
                        ) = metadata_part.values()
                        fptr = metadata_part.find("mets:fptr", NAMESPACES)
                        for fp in fptr:
                            original_image, coord_type, coords = fp.values()

                            yield Article(
                                self,
                                document_code,
                                area_id,
                                area_type,
                                area_category,
                                original_image,
                                coord_type,
                                coords,
                            )

    def get_articles(self, document_codes=[]):
        return self.articles(document_codes=document_codes)
