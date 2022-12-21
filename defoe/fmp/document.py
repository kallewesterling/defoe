"""
Object model representation of a document represented as a collection
of XML files in METS/MODS format.
"""

from .area import Area
from .page import Page
from .patterns import DATE_PATTERNS, PART_ID
from .constants import FUZZ_METHOD, MIN_RATIO, NAMESPACES

from lxml import etree
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
        self.archive = archive
        self.code = code
        self.type = "newspaper"
        self.model = "fmp"
        self.source = self.archive.open_document(self.code)
        self.tree = etree.parse(self.source)
        self.num_pages = len(self.page_codes)

        self.year, self.years = self._get_years()

        # See property accessors below
        self._id = None
        self._articles = None
        self._title = None
        self._publisher = None
        self._place = None
        self._date = None
        self._areas = None
        self._pages_metadata = None
        self._art_id_lookup = None
        self._parts_coord = None
        self._articles_ids = self.articles_ids

        # TODO docs: `num_articles` only includes ID starting with "art"
        self.num_articles = len(self.articles_ids)

        # Adding backward compatibility
        self.metadata = self.source
        self._parse_structMap_Physical = self.parts_coord
        self._parse_structLink = self._get_struct_link
        self.partsPage = self.page_parts
        self.articlesId = self.articles_ids
        self.documentId = self.id
        self.partsCoord = self.parts_coord
        self.document_type = self.type
        self.tb = self.textblocks
        self.tbs = self.textblocks
        self.scan_tb = self.scan_textblocks
        self.scan_wc = self.scan_word_confidences
        self.scan_cc = self.scan_character_confidences
        self.wc = self.word_confidences
        self.cc = self.character_confidences
        self.query = self._query
        self.single_query = self._single_query
        self.page = self.get_page
        self._parse_structMap_Logical = self.articles_ids
        self.namespaces = NAMESPACES
        self.articles_parts = self.locators
        self.articlesParts = self.locators
        self._get_parts_coord = self.parts_coord

        # Deprecated
        #
        # `self.page_codes` now comes from the metadata instead (see property
        #                   below)
        # self.page_codes = sorted(
        #     self.archive.document_codes[self.code], key=Document._sorter
        # )
        #
        # `self.articles_parts` is now called `self.locators` (added backward
        # compatibility above), `self.page_parts` has accessor below.
        # `self._get_struct_link` still exists as a shortcut method below.
        # self.articles_parts, self.page_parts = self._get_struct_link()

    @property
    def title(self):
        if not self._title:
            self._title = self._single_query("//mods:title/text()")
        return self._title

    @property
    def publisher(self):
        if not self._publisher:
            self._publisher = self._single_query("//mods:publisher/text()")
        return self._publisher

    @property
    def id(self):
        if not self._id:
            self._id = self._single_query("//mods:identifier/text()")
        return self._id

    @property
    def place(self):
        try:
            self._place
        except AttributeError:
            self._place = None

        if not self._place:
            self._place = self._single_query("//mods:placeTerm/text()")
        return self._place

    @property
    def date(self):
        try:
            self._date
        except AttributeError:
            self._date = None

        if not self._date:
            self._date = self._single_query("//mods:dateIssued/text()")
        return self._date

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

        return {
            art_id: {
                area.id: [
                    area.type,
                    ",".join(map(str, area.coords)),
                    area.page_part,
                ]
                for area in areas
            }
            for art_id, areas in self.article_id_to_area_lookup.items()
        }

    def scan_strings(self) -> tuple:
        """
        Iterate over strings in pages.

        :return: page and string
        :rtype: tuple(defoe.alto.page.Page, lxml.etree._Element)
        """
        for page in self:
            for string in page.strings:
                yield page, string

    def scan_textblocks(self) -> tuple:
        """
        Iterate over textblocks in pages

        :return: page and textblock
        :rtype: tuple(defoe.alto.page.Page, TextBlock)
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

    def scan_word_confidences(self) -> tuple:
        """
        Iterate over words' words confidences in pages.

        :return: page and wc
        :rtype: tuple(defoe.alto.page.Page, str)
        """
        for page in self:
            for wc in page.wc:
                yield page, wc

    def scan_character_confidences(self) -> tuple:
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

    def textblocks(self) -> str:
        """
        Iterate over textblocks.

        :return: string
        :rtype: str
        """
        for _, tb in self.scan_textblocks():
            yield tb

    def words(self) -> str:
        """
        Iterate over words.

        :return: word
        :rtype: str
        """
        for _, word in self.scan_words():
            yield word

    def graphics(self) -> etree.Element:
        """
        Iterate over graphics.

        :return: XML fragment with graphics
        :rtype: lxml.etree._Element
        """
        for _, graphic in self.scan_graphics():
            yield graphic

    def word_confidences(self) -> str:
        """
        Iterate over words qualities.

        :return: wc
        :rtype: str
        """
        for _, wc in self.scan_word_confidences():
            yield wc

    def character_confidences(self) -> str:
        """
        Iterate over characters qualities.

        :return: wc
        :rtype: str
        """
        for _, cc in self.scan_character_confidences():
            yield cc

    def get_page(self, code: str) -> Page:
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

    def match(
        self,
        token: Union[str, list] = [],
        normalise: bool = True,
        include_numbers: bool = True,
        lemmatise: bool = True,
        stem: bool = True,
        fuzz_method: str = FUZZ_METHOD,
        min_ratio: float = MIN_RATIO,
        all_results: bool = False,
        sort_results: bool = True,
        sort_reverse: bool = True,
        add_textblock: bool = False,
        regex: bool = False,
    ) -> list:
        return [
            match
            for tb in self.textblocks
            for match in tb.match(
                token,
                normalise=normalise,
                include_numbers=include_numbers,
                lemmatise=lemmatise,
                stem=stem,
                fuzz_method=fuzz_method,
                min_ratio=min_ratio,
                all_results=all_results,
                sort_results=sort_results,
                sort_reverse=sort_reverse,
                add_textblock=add_textblock,
                regex=regex,
            )
        ]

    @property
    def parts_coord(self) -> dict:
        """
        Parse the structMap Physical information
        :return: dictionary with the ID of each part as a keyword. For each
        part, it gets the shape and coord.
        :rtype: dictionary
        """
        if not self._parts_coord:
            self._parts_coord = {
                area.id: [area.type, ",".join(map(str, area.coords))]
                for areas in self.areas.values()
                for area in areas
            }
        return self._parts_coord

    @property
    def articles_ids(self) -> list:
        """
        Parse the structMap Logical information
        :return: list of articlesID that conforms each document/issue. It only
        returns the articles ID, no other type of elements.
        :rtype: list
        """
        return sorted(
            list(
                set(
                    [
                        area.article_id
                        for _, areas in self.areas.items()
                        for area in areas
                        if area.article_id.startswith("art")
                    ]
                )
            )
        )

    @staticmethod
    def _clean_id(string):
        return PART_ID.sub("", string)

    @property
    def page_parts(self) -> dict:
        """
        Parses the structLink information from the METS document.
        :return: A dictionary with parts/textblocks IDs as keys, and page and
        area as values.
        :rtype: dict
        """
        return {
            self._clean_id(link.values()[0]): link.values()[1]
            for x in self.struct_link
            for link in x.findall("mets:smLocatorLink", NAMESPACES)
        }

    @property
    def locators(self) -> dict:
        """
        Parses the structLink information from the METS document.
        :return: A dictionary with articles IDs as keys. And per article ID, we
        have a list of parts/textblocks IDs that conform each article.
        :rtype: dict
        """
        locators = {}
        for x in self.struct_link:
            for link in x.findall("mets:smLocatorLink", NAMESPACES):
                locator = self._clean_id(link.values()[0])
                if not locator.startswith("pa") and not locator.startswith(
                    "phys"
                ):
                    current = locator
                    locators[current] = []
                else:
                    locators[current].append(locator)
        return locators

    def _get_struct_link(self) -> tuple:
        """
        Shortcut that returns the dictionary from `Document.locators` and
        `Document.page_parts`.
        :returns: Two dictionaries. First one with parts/textblocks IDs as
        keys and page and area as values. Second one with articles IDs as
        keys. And per article ID, we have a list of parts/textblocks IDs
        that conform each article.
        :rtype: tuple
        """
        return (self.locators, self.page_parts)

    def _articles_info(self) -> dict:
        """
        :return: create a dicitionary, with articles IDs as keys. Each entry
        has has a dictionary of parts/textblocks as values, with all the parts
        information (shape, coords and page_area).
        :rtype: dictionary
        """
        # {
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
        articlesInfo = {}
        for a_id in self.articles_ids:
            articlesInfo[a_id] = {}
            for p_id in self.articles_parts[a_id]:
                if p_id in self.parts_coord:
                    self.parts_coord[p_id].append(self.page_parts[p_id])
                    articlesInfo[a_id][p_id] = self.parts_coord[p_id]
        return articlesInfo

    def _get_years(self):
        years = Document._parse_year(self.date)

        # place may often have a year in.
        years += Document._parse_year(self.place)

        years = sorted(years)

        # todo: issue warning here if > 0?
        first_year = years[0] if len(years) else None

        return first_year, years

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

    def _query(self, query: str) -> Union[list, None]:
        """
        Run XPath query.

        :param query: XPath query
        :type query: str
        :return: list of query results or None if none
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        return self.tree.xpath(query, namespaces=NAMESPACES)

    def _single_query(self, query: str) -> Union[str, None]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: str
        :return: query result or None if none
        :rtype: str
        """
        result = self._query(query)
        if not result:
            return None
        return str(result[0])

    def __getitem__(self, index: int) -> Page:
        """
        Given a page index, return a new Page object.

        :param index: page index
        :type index: int
        :return: Page object
        :rtype: defoe.alto.page.Page
        """
        return self.get_page(self.page_codes[index])

    def __iter__(self) -> Page:
        """
        Iterate over page codes, returning new Page objects.

        :return: Page object
        :rtype: defoe.alto.page.Page
        """
        for page_code in self.page_codes:
            yield self.get_page(page_code)

    @property
    def struct_map_physical(self):
        return self.tree.find('mets:structMap[@TYPE="PHYSICAL"]', NAMESPACES)

    @property
    def struct_map_logical(self):
        return self.tree.find('mets:structMap[@TYPE="LOGICAL"]', NAMESPACES)

    @property
    def struct_link(self):
        return self.tree.find("mets:structLink", NAMESPACES)

    @property
    def pages_metadata(self):
        try:
            self._pages_metadata
        except AttributeError:
            self._pages_metadata = None

        if not self._pages_metadata:
            self._pages_metadata = {
                y.values()[1].zfill(4): y
                for x in self.struct_map_physical
                for y in x.findall('mets:div[@TYPE="page"]', NAMESPACES)
            }
        return self._pages_metadata

    @property
    def art_id_lookup(self):
        if not self._art_id_lookup:
            _parts = {}
            for link_group in self.struct_link:
                links = link_group.findall("mets:smLocatorLink", NAMESPACES)
                _tmp = []

                for link in links:
                    link_id, *_ = link.values()
                    link_id = self._clean_id(link_id)
                    _tmp.append(link_id)

                _parts[_tmp[0]] = _tmp[1:]

            self._art_id_lookup = {}
            for art_id, lst in _parts.items():
                for pa_id in lst:
                    self._art_id_lookup[pa_id] = art_id
        return self._art_id_lookup

    @property
    def page_codes(self) -> list:
        return list(self.pages_metadata.keys())

    def _select_metadata(self, selected_page_code=None) -> dict:
        if not selected_page_code:
            return self.pages_metadata
        return {selected_page_code: self.pages_metadata[selected_page_code]}

    def scan_areas(self, selected_page_code=None) -> Area:
        metadata = self._select_metadata(selected_page_code)

        for page_code, page_metadata in metadata.items():
            for area in page_metadata.findall("mets:div", NAMESPACES):
                for file_pointer in area.find("mets:fptr", NAMESPACES):
                    yield Area(self, page_code, area, file_pointer)

    def get_areas_by_page_code(self, selected_page_code=None) -> dict:
        metadata = self._select_metadata(selected_page_code)
        page_codes = list(metadata.keys())

        areas_by_page_code = {page_code: [] for page_code in page_codes}

        for page_code in page_codes:
            page = self.get_page(page_code)
            for area in self.scan_areas(page_code):
                area._page = page
                areas_by_page_code[page_code].append(area)

        return areas_by_page_code

    @property
    def areas(self) -> dict:
        if not self._areas:
            self._areas = self.get_areas_by_page_code()
        return self._areas

    @property
    def article_id_to_area_lookup(self):
        area_lookup = {y.id: y for x in self.areas.values() for y in x}

        return {
            art_id: [
                area_lookup[k]
                for k, v in self.art_id_lookup.items()
                if v == art_id
            ]
            for art_id in self.articles_ids
        }
