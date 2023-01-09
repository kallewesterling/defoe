"""
Object model representation of a page represented as an XML file in
METS/MODS format.
"""

from __future__ import annotations

from lxml import etree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .document import Document
    from typing import BinaryIO, Optional

# FIXME: This needs docstring and typing fixing


class Page(object):
    """
    Object model representation of a page represented as an XML file
    in METS/MODS format.

    :param document: Document object corresponding to document to
        which this page belongs
    :type document: defoe.alto.document.Document
    :param code: Identifier for this page within an archive
    :type code: str
    :param source: Stream. If None then an attempt is made to
        open the file holding the page via the given "document"
    :type source: zipfile.ZipExt or another file-like object
    """

    WORDS_XPATH = etree.XPath("//String/@CONTENT")
    STRINGS_XPATH = etree.XPath("//String")
    IMAGES_XPATH = etree.XPath("//GraphicalElement")
    PAGE_XPATH = etree.XPath("//Page")
    WC_XPATH = etree.XPath("//String/@WC")
    CC_XPATH = etree.XPath("//String/@CC")

    def __init__(
        self, document: Document, code: str, source: Optional[BinaryIO] = None
    ):
        """
        Constructor method.
        """
        if not source:
            source = document.archive.open_page(document.code, code)
        self.document = document
        self.code = code
        self.tree = etree.parse(source)
        self.page_tree = self.single_query(Page.PAGE_XPATH)
        self.width = int(self.page_tree.get("WIDTH"))
        self.height = int(self.page_tree.get("HEIGHT"))
        self.pc = self.page_tree.get("PC")
        self.page_words = None
        self.page_strings = None
        self.page_images = None
        self.page_wc = None
        self.page_cc = None

    def query(self, xpath_query: etree.XPath) -> list:
        """
        Run XPath query.

        :meta private:
        :param xpath_query: XPath query
        :type xpath_query: lxml.etree.XPath
        :return: List of query results or None if none
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        return xpath_query(self.tree)

    def single_query(self, xpath_query: etree.XPath):
        """
        Run XPath query and return first result.

        :meta private:
        :param xpath_query: XPath query
        :type xpath_query: lxml.etree.XPath
        :return: Query result or None if none
        :rtype: lxml.etree.<MODULE> (depends on query)
        """
        result = self.query(xpath_query)
        if not result:
            return None
        return result[0]

    @property
    def words(self) -> list[str]:
        """
        Gets all words in page. These are then saved in an attribute, so the
        words are only retrieved once.

        :return: Words
        :rtype: list[str]
        """
        if not self.page_words:
            self.page_words = list(map(str, self.query(Page.WORDS_XPATH)))
        return self.page_words

    @property
    def wc(self):
        """
        Gets all word confidences (wc)  in page. These are then saved in an
        attribute, so the wc are only retrieved once.

        :return: Wc
        :rtype: list(str)
        """
        if not self.page_wc:
            self.page_wc = list(self.query(Page.WC_XPATH))

        return self.page_wc

    @property
    def cc(self):
        """
        Gets all character confidences (cc)  in page. These are then saved in an attribute,
        so the cc are only retrieved once.

        :return: Cc
        :rtype: list(str)
        """
        if not self.page_cc:
            self.page_cc = list(self.query(Page.CC_XPATH))

        return self.page_cc

    @property
    def strings(self):
        """
        Gets all strings in page. These are then saved in an attribute,
        so the strings are only retrieved once.

        :return: Strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
        if not self.page_strings:
            self.page_strings = self.query(Page.STRINGS_XPATH)
        return self.page_strings

    @property
    def images(self):
        """
        Gets all images in page. These are then saved in an attribute,
        so the images are only retrieved once.

        :return: Images
        :rtype: list(lxml.etree._Element)
        """
        if not self.page_images:
            self.page_images = self.query(Page.IMAGES_XPATH)
        return self.page_images

    @property
    def content(self):
        """
        Gets all words in page and contatenates together using ' ' as
        delimiter.

        :return: Content
        :rtype: str
        """
        return " ".join(self.words)
