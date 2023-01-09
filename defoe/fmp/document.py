"""
Object model representation of a document represented as a collection of XML
files in METS/MODS format.
"""

from __future__ import annotations

from .area import Area
from .constants import FUZZ_METHOD, MIN_RATIO, NAMESPACES
from .page import Page
from .patterns import DATE_PATTERNS, PART_ID

from lxml import etree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .archive import Archive
    from .textblock import TextBlock
    from typing import Union, Iterator, Optional
    from zipfile import ZipInfo


class Document(object):
    """
    Object model representation of a document represented as a collection of
    XML files in METS/MODS format.

    Usage:

    .. code-block:: python

        from defoe.fmp.archive import Archive

        archive = Archive("path/to/xml-files/")

        # Get document by indexing
        document = archive[0]

        # Iterate through an archive's document
        for document in archive:
            # Access the properties and methods from the Document
            print(document.code)

    :param code: Identifier for this document within an archive
    :type code: str
    :param archive: Archive to which this document belongs
    :type archive: defoe.fmp.archive.Archive
    """

    def __init__(self, code: str, archive: Archive):
        """
        Constructor method.
        """

        self.archive = archive
        self.code = code
        self.type = "newspaper"
        self.model = "fmp"
        self.source = self.archive.open_document(self.code)
        self.tree = etree.parse(self.source)

        self.num_pages = len(self.page_codes)
        """
        Returns the number of ``defoe.fmp.page.Page`` objects in the
        ``defoe.fmp.document.Document``

        :rtype: int
        """

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
        self._article_id_lookup = None
        self._parts_coord = None
        self._articles_ids = None
        self._area_lookup = None
        self._article_id_to_area_lookup_obj = None

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
        self.art_id_lookup = self.article_id_lookup
        self.struct_link = self.struct_links

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
    def title(self) -> str:
        """
        Returns the title from the MODS document.

        :return: The title from the MODS document (``//mods:title``)
        :rtype: str
        """

        if not self._title:
            self._title = self._single_query("//mods:title/text()")
        return self._title

    @property
    def publisher(self) -> str:
        """
        Returns the publisher from the MODS document.

        :return: The publisher from the MODS document (``//mods:publisher``)
        :rtype: str
        """

        if not self._publisher:
            self._publisher = self._single_query("//mods:publisher/text()")
        return self._publisher

    @property
    def id(self) -> str:
        """
        Returns the identifier from the MODS document.

        :return: The identifier from the MODS document (``//mods:identifier``)
        :rtype: str
        """

        if not self._id:
            self._id = self._single_query("//mods:identifier/text()")
        return self._id

    @property
    def place(self) -> str:
        """
        Returns the place term from the MODS document.

        :return: The place term from the MODS document (``//mods:placeTerm``)
        :rtype: str
        """

        try:
            self._place
        except AttributeError:
            self._place = None

        if not self._place:
            self._place = self._single_query("//mods:placeTerm/text()")
        return self._place

    @property
    def date(self) -> str:
        """
        Returns the date issued from the MODS document.

        :return: The the date issued from the MODS document
            (``//mods:dateIssued``)
        :rtype: str
        """

        try:
            self._date
        except AttributeError:
            self._date = None

        if not self._date:
            self._date = self._single_query("//mods:dateIssued/text()")
        return self._date

    @property
    def articles(self) -> tuple[str, list[Optional[TextBlock]]]:
        """
        Iterate over the articles in the document.

        :return: A tuple consisting of the article ID and a list of the
            article's available textblocks.
        :rtype: tuple[str, list[Optional[TextBlock]]]
        """
        for art_id, areas in self._article_id_to_area_lookup.items():
            yield art_id, [area.textblock for area in areas if area.textblock]

    def scan_strings(self) -> Iterator[tuple[Page, etree._Element]]:
        """
        Iterate over strings in pages.

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and string
        :rtype: Iterator[tuple[defoe.fmp.page.Page, lxml.etree._Element]]
        """
        for page in self:
            for string in page.strings:
                yield page, string

    def scan_textblocks(self) -> Iterator[tuple[Page, TextBlock]]:
        """
        Iterate over textblocks in pages

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and
            ``defoe.fmp.textblock.TextBlock``
        :rtype: Iterator[tuple[defoe.fmp.page.Page, TextBlock]]
        """
        for page in self:
            for tb in page.tb:
                yield page, tb

    def scan_words(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over words in pages.

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and word
        :rtype: Iterator[tuple[defoe.fmp.page.Page, str]]
        """
        for page in self:
            for word in page.words:
                yield page, word

    def scan_page_confidences(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over page confidences in pages.

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and page
            confidence
        :rtype: Iterator[tuple[defoe.fmp.page.Page, str]]
        """
        for page in self:
            yield page, page.page_confidence

    def scan_word_confidences(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over words' word confidences in pages.

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and word
            confidence
        :rtype: Iterator[tuple[defoe.fmp.page.Page, str]]
        """
        for page in self:
            for wc in page.wc:
                yield page, wc

    def scan_character_confidences(self) -> Iterator[tuple[Page, str]]:
        """
        Iterate over characters qualities in pages.

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and character
            confidence
        :rtype: Iterator[tuple[defoe.fmp.page.Page, str]]
        """
        for page in self:
            for cc in page.cc:
                yield page, cc

    def scan_graphics(self) -> Iterator[tuple[Page, etree._Element]]:
        """
        Iterate over graphical elements in pages.

        :return: A tuple consisting of ``defoe.fmp.page.Page`` and XML
            fragment with graphical elements
        :rtype: Iterator[tuple[defoe.fmp.page.Page, lxml.etree._Element]]
        """
        for page in self:
            for graphic in page.graphics:
                yield page, graphic

    def strings(self) -> Iterator[str]:
        """
        Iterate over strings.

        :return: The ``defoe.fmp.document.Document``'s strings
        :rtype: Iterator[str]
        """
        for _, string in self.scan_strings():
            yield string

    def textblocks(self) -> Iterator[TextBlock]:
        """
        Iterate over textblocks.

        :return: The ``defoe.fmp.document.Document``'s Textblocks
        :rtype: Iterator[:class:`defoe.fmp.textblock.TextBlock`]
        """
        for _, tb in self.scan_textblocks():
            yield tb

    def words(self) -> Iterator[str]:
        """
        Iterate over words.

        :return: The ``defoe.fmp.document.Document``'s words
        :rtype: Iterator[str]
        """
        for _, word in self.scan_words():
            yield word

    def graphics(self) -> Iterator[etree.Element]:
        """
        Iterate over graphics.

        :return: The ``defoe.fmp.document.Document``'s graphical elements' XML
            fragments
        :rtype: Iterator[lxml.etree._Element]
        """
        for _, graphic in self.scan_graphics():
            yield graphic

    def page_confidences(self) -> Iterator[str]:
        """
        Iterate over page qualities.

        :return: The ``defoe.fmp.document.Document``'s page confidences
        :rtype: Iterator[str]
        """
        for _, pc in self.scan_page_confidences():
            yield pc

    def word_confidences(self) -> Iterator[str]:
        """
        Iterate over words qualities.

        :return: The ``defoe.fmp.document.Document``'s word confidences
        :rtype: str
        """
        for _, wc in self.scan_word_confidences():
            yield wc

    def character_confidences(self) -> Iterator[str]:
        """
        Iterate over characters qualities.

        :return: The ``defoe.fmp.document.Document``'s character confidences
        :rtype: str
        """
        for _, cc in self.scan_character_confidences():
            yield cc

    def get_page(self, code: str) -> Page:
        """
        Given a page code, return a new ``defoe.fmp.page.Page`` object.

        :param code: Page code
        :type code: str
        :return: ``defoe.fmp.page.Page`` object
        :rtype: :class:`defoe.fmp.page.Page`
        """
        return Page(self, code)

    def get_document_info(self) -> Union[ZipInfo, None]:
        """
        Returns information from ZIP file about metadata file
        corresponding to this document.

        :return: Information
        :rtype: :class:`zipfile.ZipInfo`
        """
        return self.archive.get_document_info(self.code)

    def get_page_info(self, page_code: str) -> Union[ZipInfo, None]:
        """
        Returns information from ZIP file about a page file within
        this document.

        :param page_code: File code
        :type page_code: str
        :return: Information
        :rtype: :class:`zipfile.ZipInfo`
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
    ) -> list[tuple, int, int, int, int, str, int]:
        """
        This method runs :func:`~defoe.fmp.textblock.TextBlock.match` for each
        ``defoe.fmp.textblock.TextBlock`` in the
        ``defoe.fmp.document.Document``. See the documentation of
        :func:`TextBlock's match <defoe.fmp.textblock.TextBlock.match>`
        for information about the possible parameters.

        :param token: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type token: Union[str, list]
        :param normalise: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type normalise: bool, optional
        :param include_numbers: See
            :func:`~defoe.fmp.textblock.TextBlock.match`
        :type include_numbers: bool, optional
        :param lemmatise: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type lemmatise: bool, optional
        :param stem: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type stem: bool, optional
        :param fuzz_method: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type fuzz_method: str, optional
        :param min_ratio: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type min_ratio: float, optional
        :param all_results: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type all_results: bool, optional
        :param sort_results: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type sort_results: bool, optional
        :param sort_reverse: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type sort_reverse: bool, optional
        :param add_textblock: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type add_textblock: bool, optional
        :param regex: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :type regex: bool, optional

        :return: See :func:`~defoe.fmp.textblock.TextBlock.match`
        :rtype: list[tuple]
        """
        return [
            match
            for tb in self.textblocks()
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
        Parse the structMap Physical information.

        :return: Dictionary with the ID of each part as a keyword. For each
            part, it returns the shape and coord.
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
        Returns a different view of the logical structural map of the METS
        document (see :func:`~defoe.fmp.document.Document.struct_map_logical`)
        where the article IDs are picked out (the ones starting with ``art``)
        and returned as a list.

        :return: List of article IDs available in the document.
        :rtype: list
        """
        try:
            self._articles_ids
        except AttributeError:
            self._articles_ids = None

        if not self._articles_ids:
            self._articles_ids = sorted(
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
        return self._articles_ids

    @property
    def page_parts(self) -> dict:
        """
        Returns a different view of the structural links of the METS document
        (see  :func:`~defoe.fmp.document.Document.struct_links`)) where
        article IDs and page areas of the document are provided back as keys
        in a dictionary, and the type of area (for article IDs) and the area's
        designated string representation (for page areas) are provided as
        values.

        :return: A dictionary with parts/textblocks IDs as keys, and page and
            area as values.
        :rtype: dict
        """
        return {
            self._clean_id(link.values()[0]): link.values()[1]
            for x in self.struct_links
            for link in x.findall("mets:smLocatorLink", NAMESPACES)
        }

    @property
    def locators(self) -> dict:
        """
        Returns a different view of the structural links of the METS document
        (see  :func:`~defoe.fmp.document.Document.struct_links`)) where the
        article IDs from the document are provided as keys and a list of their
        pertaining page areas are provided as string representations of their
        IDs as values.

        :return: A dictionary with articles IDs as keys. And per article ID, we
            have a list of parts/textblocks IDs that conform each article.
        :rtype: dict
        """
        locators = {}
        for x in self.struct_links:
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

    @property
    def struct_map_physical(self) -> etree._Element:
        """
        Returns the METS document's "physical structural map", which lists the
        directories and files in the objects directory as they are laid out on
        the disk.

        If you want to preview the contents of the physical structural map of
        the document, given that you already have a ``document`` assigned:

        .. code-block:: python

            from lxml import etree

            # Extract as byte-encoded string
            string = etree.tostring(document.struct_map_physical)

            print(string.decode("utf-8"))

        :return: The METS document's "physical structural map"  as XML element
        :rtype: lxml.etree._Element
        """
        return self.tree.find('mets:structMap[@TYPE="PHYSICAL"]', NAMESPACES)

    @property
    def struct_map_logical(self) -> etree._Element:
        """
        Returns the METS document's "logical structural map", an outline of
        the hierarchical structure for the digital library object, and links
        the elements of that structure to content files and metadata that
        pertain to each element.

        If you want to preview the contents of the physical structural map of
        the document, given that you already have a ``document`` assigned:

        .. code-block:: python

            from lxml import etree

            # Extract as byte-encoded string
            string = etree.tostring(document.struct_map_logical)

            print(string.decode("utf-8"))

        :return: The METS document's "logical structural map" as XML element
        :rtype: lxml.etree._Element
        """
        return self.tree.find('mets:structMap[@TYPE="LOGICAL"]', NAMESPACES)

    @property
    def struct_links(self) -> etree._Element:
        """
        Returns the METS document's structural links, which allow METS
        creators to record the existence of hyperlinks between nodes in the
        hierarchy outlined in the structural map.

        Usage, if you want to preview the contents of the physical structural
        map of the document, given that you already have a ``document``
        assigned:

        .. code-block:: python

            from lxml import etree

            # Extract as byte-encoded string
            string = etree.tostring(document.struct_links)

            print(string.decode("utf-8"))

        :return: The METS document's structural links as XML element
        :rtype: lxml.etree._Element
        """
        return self.tree.find("mets:structLink", NAMESPACES)

    @property
    def pages_metadata(self) -> dict:
        """
        Returns a different view of the physical structural map of the METS
        document (see :func:`~defoe.fmp.document.Document.struct_map_physical`)
        where each ``div`` in the structural map are divided into the pages in
        the document and returned as a dictionary, which can be indexed into
        with the help of each page code.

        :return: Dictionary with page code as key and each page's metadata as
            XML element as values
        :rtype: dict
        """
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
    def article_id_lookup(self) -> dict:
        """
        Returns a different view of the structural links of the METS document
        (see  :func:`~defoe.fmp.document.Document.struct_links`)) where the
        links are reorganised into a dictionary with the page area identifier
        as key and the article ID to which the page area belongs as key. Can
        thus easily be used to look up the article ID by page area ID.

        :return: Dictionary with the page area identifier as key and the
            article ID to which the page area belongs as key.
        :rtype: dict
        """
        if not self._article_id_lookup:
            _parts = {}
            for link_group in self.struct_links:
                links = link_group.findall("mets:smLocatorLink", NAMESPACES)
                _tmp = []

                for link in links:
                    link_id, *_ = link.values()
                    link_id = self._clean_id(link_id)
                    _tmp.append(link_id)

                _parts[_tmp[0]] = _tmp[1:]

            self._article_id_lookup = {}
            for art_id, lst in _parts.items():
                for pa_id in lst:
                    self._article_id_lookup[pa_id] = art_id

        return self._article_id_lookup

    @property
    def page_codes(self) -> list[str]:
        """
        Returns a list of all page codes that belong to the
        ``defoe.fmp.document.Document``.

        :return: List of all the ``defoe.fmp.document.Document``'s page codes
        :rtype: list[str]
        """
        return list(self.pages_metadata.keys())

    def _select_metadata(self, selected_page_code=None) -> dict:
        if not selected_page_code:
            return self.pages_metadata
        return {selected_page_code: self.pages_metadata[selected_page_code]}

    def scan_areas(
        self, selected_page_code: Optional[str] = None
    ) -> Iterator[Area]:
        """
        Iterate over areas in ``defoe.fmp.document.Document``. The iterator
        can be restricted to a given page code by providing it a
        ``selected_page_code`` parameter.

        Usage, given that you already have a ``document`` assigned:

        .. code-block:: python

            for area in document.scan_areas(selected_page_code="0001"):
                area.tokens

        :param selected_page_code: A page file code if you are only requesting
            one page's areas
        :type selected_page_code: str, optional
        :return: Each ``defoe.fmp.area.Area`` that belongs to the
            ``defoe.fmp.document.Document``
        :rtype: Iterator[:class:`defoe.fmp.area.Area`]
        """
        metadata = self._select_metadata(selected_page_code)

        for page_code, page_metadata in metadata.items():
            for area in page_metadata.findall("mets:div", NAMESPACES):
                for file_pointer in area.find("mets:fptr", NAMESPACES):
                    yield Area(self, page_code, area, file_pointer)

    def get_areas_by_page_code(
        self, selected_page_code: Optional[str] = None
    ) -> dict:
        """
        Returns a list of areas (see :class:`defoe.fmp.area.Area`) for the
        each of the document's page/s, structured as a dictionary. If a
        ``selected_page_code`` is set, the function will only return the areas
        for the given page code.

        :param selected_page_code: A page file code if you are only requesting
            one page's areas
        :type selected_page_code: str, optional
        :return: Dictionary with page codes as keys and each
            ``defoe.fmp.page.Page``'s areas as a list as value for each key.
        :rtype: dict
        """
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
        """
        Shortcut property for storing and returning the output of
        :func:`~defoe.fmp.document.Document.get_areas_by_page_code`.

        :return: Dictionary with page codes as keys and each
            ``defoe.fmp.page.Page``'s areas as a list as value for each key.
        :rtype: dict
        """
        if not self._areas:
            self._areas = self.get_areas_by_page_code()
        return self._areas

    @property
    def _article_id_to_area_lookup(self) -> dict:
        if not self._area_lookup:
            self._area_lookup = {
                y.id: y for x in self.areas.values() for y in x
            }

        if not self._article_id_to_area_lookup_obj:
            self._article_id_to_area_lookup_obj = {
                art_id: [
                    self._area_lookup[k]
                    for k, v in self.article_id_lookup.items()
                    if v == art_id
                ]
                for art_id in self.articles_ids
            }

        return self._article_id_to_area_lookup_obj

    @staticmethod
    def _clean_id(string):
        return PART_ID.sub("", string)

    def _get_struct_link(self) -> tuple[dict, dict]:
        """
        Shortcut that returns the dictionary from `Document.locators` and
        `Document.page_parts`.

        :return: Two dictionaries. First one with parts/textblocks IDs as keys
            and page and area as values. Second one with articles IDs as keys.
            And per article ID, we have a list of parts/textblocks IDs that
            conform each article.
        :rtype: tuple[dict, dict]
        """
        return (self.locators, self.page_parts)

    def _articles_info(self) -> dict:
        """
        :return: A dictionary with articles IDs as keys. Each entry has a
            dictionary of parts/textblocks as values, with all the parts
            information (shape, coords and page_area).
        :rtype: dictionary
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
            for art_id, areas in self._article_id_to_area_lookup.items()
        }

    def _get_years(self) -> tuple[Optional[int], list]:
        years = Document._parse_year(self.date)

        # place may often have a year in.
        years += Document._parse_year(self.place)

        years = sorted(years)

        first_year = years[0] if len(years) else None

        if len(years) > 1:
            pass  # TODO: issue warning here if > 0?

        return first_year, years

    @staticmethod
    def _parse_year(text: str) -> list[Optional[int]]:
        """
        Parse text to extract years of form 16xx to 19xx.

        Any date of form ``NN`` following a year of form ``CCYY`` to ``CCYY``
        is used to derive a date ``CCNN``.

        As an exception to this rule, single years are parsed from dates
        precisely matching the format ``YYYY-MM-DD``.

        For example:

        * ``1862, [1861]`` returns ``[1861, 1862]``
        * ``1847 [1846, 47]`` returns ``[1846, 1847]``
        * ``1873-80`` returns ``[1873, 1880]``
        * ``1870-09-01`` returns ``[1870]``

        :param text: Text to parse
        :type text: str
        :return: Years
        :rtype: list[Optional[int]]
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
    def _sorter(page_code: str) -> list[int]:
        """
        Given a page code of form ``[0-9]*(_[0-9]*)``, split it into its
        sub-codes. For example, given ``123_456``, return ``[123, 456]``.

        :param page_code: Page code
        :type page_code: str
        :return: List of page codes
        :rtype: list[int]
        """
        codes = list(map(int, page_code.split("_")))
        return codes

    def _query(self, query: etree.XPath) -> Optional[list]:
        """
        Run XPath query.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: List of query results or an empty list if query returns no
            results
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        return self.tree.xpath(query, namespaces=NAMESPACES)

    def _single_query(self, query: etree.XPath) -> Optional[str]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: Query result or None if none
        :rtype: str
        """
        result = self._query(query)
        if not result:
            return None
        return str(result[0])

    def __getitem__(self, index: int) -> Page:
        """
        Given a page index, return a new ``defoe.fmp.page.Page`` object.

        :param index: page index
        :type index: int
        :return: Page object
        :rtype: defoe.fmp.page.Page
        """
        return self.get_page(self.page_codes[index])

    def __iter__(self) -> Iterator[Page]:
        """
        Iterate over page codes, returning new ``defoe.fmp.page.Page`` objects.

        :return: Page object
        :rtype: defoe.fmp.page.Page
        """
        for page_code in self.page_codes:
            yield self.get_page(page_code)
