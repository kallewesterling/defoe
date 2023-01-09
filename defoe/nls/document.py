"""
Object model representation of a document represented as a collection
of XML files in METS/MODS format.
"""
from __future__ import annotations

from .page import Page

from lxml import etree
from typing import TYPE_CHECKING

import re

if TYPE_CHECKING:
    from .archive import Archive
    from typing import Optional, Iterator, Union
    import zipfile


class Document(object):
    """
    Object model representation of a document represented as a
    collection of XML files in METS/MODS format.

    :param code: Identifier for this document within an archive
    :type code: str
    :param archive: Archive to which this document belongs
    :type archive: defoe.nls.archive.Archive
    """

    def __init__(self, code: str, archive: Archive):
        """
        Constructor method.
        """
        self.namespaces = {
            "mods": "http://www.loc.gov/mods/v3",
            "mets": "http://www.loc.gov/METS/",
        }
        self.archive = archive
        self.code = code
        self.num_pages = 0
        self.metadata = self.archive.open_document(self.code)
        self.metadata_tree = etree.parse(self.metadata)
        self.title = self.single_query("//mods:title/text()")
        self.edition = self.single_query("//mods:partName/text()")
        self.page_codes = sorted(
            self.archive.document_codes[self.code], key=Document.sorter
        )
        # sorted(self.archive.document_codes[self.code], key=Document.sorter)
        self.num_pages = len(self.page_codes)
        self.years = Document.parse_year(
            self.single_query("//mods:dateIssued/text()")
        )
        self.publisher = self.single_query("//mods:publisher/text()")
        self.place = self.single_query("//mods:placeTerm[@type='text']/text()")
        # place may often have a year in.
        self.years += Document.parse_year(self.place)
        self.years = sorted(self.years)
        if self.years:
            self.year = self.years[0]
        else:
            self.year = None
        self.date = self.single_query("//mods:dateIssued/text()")
        self.document_type = "book"
        self.model = "nls"

    @staticmethod
    def parse_year(text: str) -> list[Optional[int]]:
        """
        Parse text to extract years of form 16xx to 19xx.

        Any date of form NN following a year of form CCYY to CCYY
        is used to derive a date CCNN.

        As an exception to this rule, single years are parsed
        from dates precisely matching the format YYYY-MM-DD.

        For example:

        * "1862, [1861]" returns [1861, 1862]
        * "1847 [1846, 47]" returns [1846, 1847]
        * "1873-80" returns [1873, 1880]
        * "1870-09-01" returns [1870]

        :param text: Text to parse
        :type text: str
        :return: List of years in text or an empty list
        :rtype: list[Optional[int]]
        """
        try:
            date_pattern = re.compile(
                r"(1[6-9]\d{2}(-|/)(0[1-9]|1[0-2])(-|/)(0[1-9]|[12]\d|3[01]))"
            )
            if date_pattern.match(text):
                return [int(text[0:4])]
            long_pattern = re.compile(r"(1[6-9]\d\d)")
            short_pattern = re.compile(r"\d\d")
            results = []
            chunks = iter(long_pattern.split(text)[1:])
            for year, rest in zip(chunks, chunks):
                results.append(int(year))
                century = year[0:2]
                short_years = short_pattern.findall(rest)
                for short_year in short_years:
                    results.append(int(century + short_year))
            return sorted(set(results))
        except TypeError:
            return []

    @staticmethod
    def sorter(page_code: str) -> list[int]:
        """
        Given a page code of form ``[0-9]*(_[0-9]*)``, split it into its
        sub-codes as integers. For example, given ``123_456``, return
        ``[123, 456]``.

        :param page_code: Page code
        :type page_code: str
        :return: List of page codes
        :rtype: list[int]
        """
        codes = list(map(int, page_code.split("/")[1].split(".")[0]))
        return codes

    def query(
        self, query: etree.XPath
    ) -> list[Optional[Union[etree._ElementUnicodeResult, etree._Element]]]:
        """
        Run XPath query.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: List of query results or an empty list if query returns no
            results
        :rtype: list[Optional[Union[etree._ElementUnicodeResult,
            etree._Element]]], depending on the query
        """
        return self.metadata_tree.xpath(query, namespaces=self.namespaces)

    def single_query(
        self, query: etree.XPath
    ) -> Optional[Union[etree._ElementUnicodeResult, etree._Element]]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: The query's result or None if no result is returned
        :rtype: Optional[Union[etree._ElementUnicodeResult, etree._Element]]
        """
        result = self.query(query)
        if not result:
            return None
        return str(result[0])

    def page(self, code: str) -> Page:
        """
        Given a page code, return a new Page object.

        :param code: Page code
        :type code: str
        :return: ``Page`` object
        :rtype: defoe.nls.page.Page
        """
        return Page(self, code)

    def get_document_info(self) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about metadata file
        corresponding to this document.

        :return: File information
        :rtype: zipfile.ZipInfo
        """
        return self.archive.get_document_info(self.code)

    def get_page_info(self, page_code: str) -> zipfile.ZipInfo:
        """
        Gets information from ZIP file about a page file within
        this document.

        :param page_code: File code
        :type page_code: str
        :return: File information
        :rtype: zipfile.ZipInfo
        """
        return self.archive.get_page_info(self.code, page_code)

    def __getitem__(self, index: int) -> Page:
        """
        Given a page index, return a new Page object.

        :param index: Page index
        :type index: int
        :return: Page object
        :rtype: defoe.nls.page.Page
        """
        return self.page(self.page_codes[index])

    def __iter__(self) -> Iterator[Page]:
        """
        Iterate over the ``Document``'s page codes, returning new ``Page``
            objects.

        :return: Page object
        :rtype: Iterator[defoe.nls.page.Page]
        """
        for page_code in self.page_codes:
            yield self.page(page_code)

    def scan_strings(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over the ``Document``'s string for each ``Page``.

        :return: A tuple consisting of ``Page`` and the string
        :rtype: Iterator[tuple[defoe.nls.page.Page, str]]
        """
        for page in self:
            for string in page.strings:
                yield page, string

    def scan_words(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over the ``Document``'s words for each ``Page``.

        :return: A tuple consisting of ``Page`` and the word
        :rtype: Iterator[tuple[defoe.nls.page.Page, str]]
        """
        for page in self:
            for word in page.words:
                yield page, word

    def scan_wc(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over the ``Document``'s word qualities for each ``Page``.

        :return: A tuple consisting of ``Page`` and the word quality
        :rtype: Iterator[tuple[defoe.nls.page.Page, str]]
        """
        for page in self:
            for wc in page.wc:
                yield page, wc

    def scan_cc(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over the ``Document``'s character qualities for each ``Page``.

        :return: A tuple consisting of ``Page`` and the character quality
        :rtype: Iterator[tuple[defoe.nls.page.Page, str]]
        """
        for page in self:
            for cc in page.cc:
                yield page, cc

    def scan_images(self) -> Iterator[tuple[Page, etree._Element]]:
        """
        Iterate over the ``Document``'s images for each ``Page``.

        :return: A tuple consisting of ``Page`` and the XML fragment with the
            image
        :rtype: Iterator[tuple[defoe.nls.page.Page, lxml.etree._Element]]
        """
        for page in self:
            for image in page.images:
                yield page, image

    def strings(self) -> Iterator[str]:
        """
        Iterate over the ``Document``'s strings.

        :return: String
        :rtype: Iterator[str]
        """
        for _, string in self.scan_strings():
            yield string

    def words(self) -> Iterator[str]:
        """
        Iterate over the ``Document``'s words.

        :return: Word
        :rtype: Iterator[str]
        """
        for _, word in self.scan_words():
            yield word

    def images(self) -> Iterator[etree._Element]:
        """
        Iterate over the ``Document``'s images.

        :return: XML fragment with image
        :rtype: Iterator[lxml.etree._Element]
        """
        for _, image in self.scan_images():
            yield image

    def wc(self) -> Iterator[str]:
        """
        Iterate over the ``Document``'s word qualities.

        :return: Word quality
        :rtype: Iterator[str]
        """
        for _, wc in self.scan_wc():
            yield wc

    def cc(self) -> Iterator[str]:
        """
        Iterate over the ``Document``'s character qualities.

        :return: Character quality
        :rtype: Iterator[str]
        """
        for _, cc in self.scan_cc():
            yield cc
