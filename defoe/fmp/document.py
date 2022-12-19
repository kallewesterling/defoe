"""
Object model representation of a document represented as a collection
of XML files in METS/MODS format.
"""

from .page import Page
from .patterns import DATE_PATTERNS, PART_ID

from lxml import etree
from lxml.etree import Element
from typing import Union
from zipfile import ZipInfo


class Document(object):
    """
    Object model representation of a document represented as a collection of
    XML files in METS/MODS format.
    """

    # TODO: cannot do typehinting here due to circular import
    def __init__(self, code: str, archive):
        """
        Constructor

        :param code: identifier for this document within an archive
        :type code: str
        :param archive: archive to which this document belongs
        :type archive: defoe.alto.archive.Archive
        """
        self.namespaces = {
            "mods": "http://www.loc.gov/mods/v3",
            "mets": "http://www.loc.gov/METS/",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "premis": "info:lc/xmlns/premis-v2",
            "dcterms": "http://purl.org/dc/terms/",
            "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
            "xlink": "http://www.w3.org/1999/xlink",
        }
        self.archive = archive
        self.code = code
        self.document_type = "newspaper"
        self.model = "fmp"
        self.metadata = self.archive.open_document(self.code)
        self.metadata_tree = etree.parse(self.metadata)
        self.title = self.single_query("//mods:title/text()")
        self.page_codes = sorted(
            self.archive.document_codes[self.code], key=Document._sorter
        )
        self.num_pages = len(self.page_codes)

        self.publisher = self.single_query("//mods:publisher/text()")
        self.place = self.single_query("//mods:placeTerm/text()")
        self.documentId = self.single_query("//mods:identifier/text()")
        self.date = self.single_query("//mods:dateIssued/text()")

        self.years = Document._parse_year(
            self.single_query("//mods:dateIssued/text()")
        )
        # place may often have a year in.
        self.years += Document._parse_year(self.place)
        self.years = sorted(self.years)
        if self.years:
            self.year = self.years[0]  # todo: issue warning here?
        else:
            self.year = None

        # See property accessors below
        self._articles = None

        # TODO: the following slows down, but needed for now!
        self.textblocks = list(self.tb())

        # New #################
        # [art0001, art0002, art0003]
        self.articlesId = self._parse_structMap_Logical()
        # {
        #   '#art0001': [
        #       '#pa0001001',
        #       '#pa0001002',
        #        ...
        #   ],
        #   '#art0002': [
        #       '#pa0001008',
        #       '#pa0001009' ..
        #   ]
        # }

        # {'pa0001001': 'page1 area1', 'pa0001003': 'page1 area3'}
        self.articlesParts, self.partsPage = self._parse_structLink()

        # {
        #   'pa0001001': [
        #       'RECT', '1220,5,2893,221'
        #   ],
        #   'pa0001003': [
        #       'RECT', '2934,14,3709,211'
        #   ],
        #   'pa0004044': [
        #       'RECT', '5334,2088,5584,2121'
        #   ]
        # }
        self.partsCoord = self._parse_structMap_Physical()

        self.num_articles = len(self.articlesId)
        #######################

    @staticmethod
    def _parse_year(text: str) -> list:
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

        :param text: text to parse
        :type text: str
        :return: years
        :rtype: set(int)
        """
        try:
            if DATE_PATTERNS.standard.match(text):
                return [int(text[0:4])]
            # long_pattern = re.compile(r"(1[6-9]\d\d)")
            # short_pattern = re.compile(r"\d\d")
            results = []
            chunks = iter(DATE_PATTERNS.long.split(text)[1:])
            for year, rest in zip(chunks, chunks):
                results.append(int(year))
                century = year[0:2]
                short_years = DATE_PATTERNS.short.findall(rest)
                for short_year in short_years:
                    results.append(int(century + short_year))
            return sorted(set(results))
        except TypeError:
            return []

    @staticmethod
    def _sorter(page_code: str) -> list:
        """
        Given a page code of form [0-9]*(_[0-9]*), split this
        into the sub-codes. For example, given 123_456, return
        [123, 456]

        :param page_code: page code
        :type page_code: str
        :return: list of page codes
        :rtype: list(int)
        """
        codes = list(map(int, page_code.split("_")))
        return codes

    def query(self, query: str) -> Union[list, None]:
        """
        Run XPath query.

        :param query: XPath query
        :type query: str
        :return: list of query results or None if none
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        return self.metadata_tree.xpath(query, namespaces=self.namespaces)

    def single_query(self, query: str) -> Union[str, None]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: str
        :return: query result or None if none
        :rtype: str
        """
        result = self.query(query)
        if not result:
            return None
        return str(result[0])

    def page(self, code: str) -> Page:
        """
        Given a page code, return a new Page object.

        :param code: page code
        :type code: str
        :return: Page object
        :rtype: defoe.alto.page.Page
        """
        return Page(self, code)

    def get_document_info(self) -> Union[ZipInfo, None]:
        """
        Gets information from ZIP file about metadata file
        corresponding to this document.

        :return: information
        :rtype: zipfile.ZipInfo
        """
        return self.archive.get_document_info(self.code)

    def get_page_info(self, page_code: str) -> Union[ZipInfo, None]:
        """
        Gets information from ZIP file about a page file within
        this document.

        :param page_code: file code
        :type page_code: str
        :return: information
        :rtype: zipfile.ZipInfo
        """
        return self.archive.get_page_info(self.code, page_code)

    def __getitem__(self, index: int) -> Page:
        """
        Given a page index, return a new Page object.

        :param index: page index
        :type index: int
        :return: Page object
        :rtype: defoe.alto.page.Page
        """
        return self.page(self.page_codes[index])

    def __iter__(self) -> Page:
        """
        Iterate over page codes, returning new Page objects.

        :return: Page object
        :rtype: defoe.alto.page.Page
        """
        for page_code in self.page_codes:
            yield self.page(page_code)

    def scan_strings(self) -> tuple:
        """
        Iterate over strings in pages.

        :return: page and string
        :rtype: tuple(defoe.alto.page.Page, str)
        """
        for page in self:
            for string in page.strings:
                yield page, string

    def scan_tb(self) -> tuple:
        """
        Iterate over textblocks in pages

        :return: page and textblock
        :rtype: tuple(defoe.alto.page.Page, str)
        """
        for page in self:
            for tb in page.tb:
                yield page, tb

    def scan_words(self) -> tuple:
        """
        Iterate over words in pages.

        :return: page and word
        :rtype: tuple(defoe.alto.page.Page, str)
        """
        for page in self:
            for word in page.words:
                yield page, word

    def scan_wc(self) -> tuple:
        """
        Iterate over words qualities in pages.

        :return: page and wc
        :rtype: tuple(defoe.alto.page.Page, str)
        """
        for page in self:
            for wc in page.wc:
                yield page, wc

    @property
    def articles(self) -> dict:
        """
        Iterate calculates the articles in each page.

        :return: a dictionary per page with all the articles. Each article
        is conformed by one or more textblocks
        :rtype: dictionary of articles. Each
        {
            'art0001': [
                'pa0001001': [
                    'RECT', '1220,5,2893,221', 'page1 area1'
                ],
                'pa0001003': [
                    'RECT', '2934,14,3709,211', page1 area3
                ],
                ...
            ],
            ...
        }
        """
        if not self._articles:
            self._articles = dict()
            articlesInfo = self._articles_info()
            for page in self:
                for tb in page.tb:
                    for articleId in articlesInfo:
                        for partId in articlesInfo[articleId]:
                            if partId == tb.textblock_id:
                                if articleId not in self._articles:
                                    self._articles[articleId] = []
                                tb.textblock_shape = articlesInfo[articleId][
                                    partId
                                ][0]
                                tb.textblock_coords = articlesInfo[articleId][
                                    partId
                                ][1]
                                tb.textblock_page_area = articlesInfo[
                                    articleId
                                ][partId][2]
                                self._articles[articleId].append(tb)

        return self._articles

    def scan_cc(self) -> tuple:
        """
        Iterate over characters qualities in pages.

        :return: page and cc
        :rtype: tuple(defoe.alto.page.Page, str)
        """
        for page in self:
            for cc in page.cc:
                yield page, cc

    def scan_graphics(self) -> tuple:
        """
        Iterate over graphical elements in pages.

        :return: page and XML fragment with graphical elements
        :rtype: tuple(defoe.alto.page.Page, lxml.etree._Element)
        """
        for page in self:
            for graphic in page.graphics:
                yield page, graphic

    def strings(self) -> str:
        """
        Iterate over strings.

        :return: string
        :rtype: str
        """
        for _, string in self.scan_strings():
            yield string

    def tb(self) -> str:
        """
        Iterate over textblocks.
        # TODO: Shouldn't this be called tbs (to be consistent with strings,
        # words, or images)?

        :return: string
        :rtype: str
        """
        for _, tb in self.scan_tb():
            yield tb

    def words(self) -> str:
        """
        Iterate over words.

        :return: word
        :rtype: str
        """
        for _, word in self.scan_words():
            yield word

    def graphics(self) -> Element:
        """
        Iterate over graphics.

        :return: XML fragment with graphics
        :rtype: lxml.etree._Element
        """
        for _, graphic in self.scan_graphics():
            yield graphic

    def wc(self) -> str:
        """
        Iterate over words qualities.

        :return: wc
        :rtype: str
        """
        for _, wc in self.scan_wc():
            yield wc

    def cc(self) -> str:
        """
        Iterate over characters qualities.

        :return: wc
        :rtype: str
        """
        for _, cc in self.scan_cc():
            yield cc

    def _parse_structMap_Physical(self) -> dict:
        """
        Parse the structMap Physical information
        :return: dictionary with the ID of each part as a keyword. For each
        part, it gets the shape and coord.
        :rtype: dictionary
        {
            'pa0001001': [
                'RECT', '1220,5,2893,221'
            ],
            'pa0001003': [
                'RECT', '2934,14,3709,211'
            ],
            'pa0004044': [
                'RECT', '5334,2088,5584,2121'
            ]
        }
        """
        partsCoord = dict()
        elem = self.metadata_tree.find(
            'mets:structMap[@TYPE="PHYSICAL"]', self.namespaces
        )
        for physic in elem:
            parts = physic.findall('mets:div[@TYPE="page"]', self.namespaces)
            for part in parts:
                metadata_parts = part.findall("mets:div", self.namespaces)
                for metadata in metadata_parts:
                    fptr = metadata.find("mets:fptr", self.namespaces)
                    for fp in fptr:
                        partsCoord[list(metadata.values())[0]] = [
                            list(fp.values())[1],
                            list(fp.values())[2],
                        ]
        return partsCoord

    def _parse_structMap_Logical(self) -> list:
        """
        Parse the structMap Logical information
        :return: list of articlesID that conforms each document/issue. It only
        returns the articles ID, no other type of elements.
        :rtype: list
        [art0001, art0002, art0003]
        """
        articlesId = []
        elem = self.metadata_tree.find(
            'mets:structMap[@TYPE="LOGICAL"]', self.namespaces
        )
        for logic in elem:
            articles = logic.findall(
                'mets:div[@TYPE="ARTICLE"]', self.namespaces
            )
            for article in articles:
                articlesId.append(list(article.values())[0])
        return articlesId

    def _parse_structLink(self) -> tuple:
        """
        Parse the strucLink information
        :return: 1) A dictionary with articles IDs as keys. And per article
                    ID, we have a list of parts/textblokcs ids that conform
                    each article.
                 2) A dictionary with parts/textblocks ids as keys, and page
                    and area as values.
        :rtype: two dictionaries
        {
            '#art0001':[
                '#pa0001001',
                '#pa0001002',
                '#pa0001003',
                ...
            ],
            '#art0002': [
                '#pa0001008',
                '#pa0001009'
                ..
            ]
        }
        {
            'pa0001001': 'page1 area1',
            'pa0001003': 'page1 area3'
        }
        """
        articlesParts = dict()
        partsPage = dict()
        elem = self.metadata_tree.findall("mets:structLink", self.namespaces)
        for smlinkgrp in elem:
            # TODO: following line is not accessed so commented out
            # (note: test this)
            # parts = smlinkgrp.findall("mets:smLinkGrp", self.namespaces)
            for linklocator in smlinkgrp:
                linkl = linklocator.findall(
                    "mets:smLocatorLink", self.namespaces
                )
                article_parts = []
                for link in linkl:
                    idstring = list(link.values())[0]
                    partId = PART_ID.sub("", idstring)
                    article_parts.append(partId)
                    partsPage[partId] = list(link.values())[1]
                articlesParts[article_parts[0]] = article_parts[1:]
        return articlesParts, partsPage

    def _articles_info(self) -> dict:
        """
        :return: create a dicitionary, with articles IDs as keys. Each entry
        has has a dictionary of parts/textblocks as values, with all the parts
        information (shape, coords and page_area).
        :rtype: dictionary
        #{
        #   'art0001 {
        #       'pa0001001': [
        #           'RECT', '1220,5,2893,221', 'page1 area1'
        #       ],
        #       'pa0001003': [
        #           'RECT', '2934,14,3709,211', 'page1 area3'
        #       ],
        #       ...
        #    }
        # }
        """
        articlesInfo = dict()
        for a_id in self.articlesId:
            articlesInfo[a_id] = dict()
            for p_id in self.articlesParts[a_id]:
                if p_id in self.partsCoord:
                    self.partsCoord[p_id].append(self.partsPage[p_id])
                    articlesInfo[a_id][p_id] = self.partsCoord[p_id]
        return articlesInfo
