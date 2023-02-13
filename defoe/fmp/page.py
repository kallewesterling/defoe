"""
Object model representation of a page represented as an XML file in METS/MODS
format.
"""

from __future__ import annotations

from .textblock import TextBlock
from .constants import FUZZ_METHOD, MIN_RATIO, AUTO_FILL, AUTO_OPACITY

from lxml import etree
from PIL import Image, ImageDraw
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .area import Area
    from .document import Document
    from typing import BinaryIO, Union, Iterator, Optional


class Page(object):
    """
    Object model representation of a page represented as an XML file in
    METS/MODS format.

    Usage:

    .. code-block:: python

        from defoe.fmp.archive import Archive

        archive = Archive("path/to/xml-files/")

        # See documentation for defoe.fmp.document.Document here:
        document = archive[0]

        # Get page by indexing
        page = document[0]

        # Iterate through an archive's document's pages
        for page in document:
            # Access the properties and methods from the Page
            print(page.width)

    :param document: ``defoe.fmp.document.Document`` object corresponding to
        document to which this page belongs
    :type document: defoe.fmp.document.Document
    :param code: Identifier for this page within an archive
    :type code: str
    :param source: File stream, defaults to the file stream from the file
        holding the page via the given ``defoe.fmp.document.Document``
    :type source: :class:`zipfile.ZipExt` or another file-like object, optional
    """

    # XPath Queries
    WORDS_XPATH = etree.XPath("//String/@CONTENT")  # String content
    STRINGS_XPATH = etree.XPath("//String")  # String elements
    GRAPHICS_XPATH = etree.XPath("//GraphicalElement")  # Graphical elements
    PAGE_XPATH = etree.XPath("//Page")  # Page
    WC_XPATH = etree.XPath("//String/@WC")  # Word confidence content
    CC_XPATH = etree.XPath("//String/@CC")  # Character confience content
    TB_XPATH_ID = etree.XPath("//TextBlock/@ID")  # Textblock ID
    TB_XPATH = etree.XPath("//TextBlock")  # Textblock content

    def __init__(self, document: Document, code: str, source: BinaryIO = None):
        """
        Constructor method.
        """

        self.document = document
        self.code = code

        self.source = source
        if not self.source:
            self.source = document.archive.open_page(document.code, code)

        self.tree = etree.parse(self.source)
        self.page_tree = self._single_query(Page.PAGE_XPATH)

        self.width = int(self.page_tree.get("WIDTH"))
        """
        Returns ``defoe.fmp.page.Page``'s width in pixels

        :rtype: int
        """

        self.height = int(self.page_tree.get("HEIGHT"))
        """
        Returns ``defoe.fmp.page.Page``'s height in pixels

        :rtype: int
        """

        self.page_confidence = self.page_tree.get("PC")
        """
        Returns ``defoe.fmp.page.Page``'s confidence

        :rtype: str
        """

        # Try setting page_confidence to float
        try:
            self.page_confidence = float(self.page_confidence)
        except ValueError:
            # TODO: Warning: page confidence was set to 0
            self.page_confidence = 0
        except TypeError:
            # TODO: Warning: page confidence was set to 0
            self.page_confidence = 0

        # See property accessors below
        self._words = None
        self._strings = None
        self._graphics = None
        self._word_confidences = None
        self._character_confidences = None
        self._textblock_ids = None
        self._image = None
        self._image_path = None
        self._areas = None

        # Adding backward compatibility
        self.query = self._query
        self.single_query = self._single_query
        self.page_words = self.words
        self.page_strings = self.strings
        self.cc = self.character_confidences
        self.wc = self.word_confidences
        self._cc = self._character_confidences
        self._wc = self._word_confidences
        self.page_wc = self.word_confidences
        self.page_cc = self.character_confidences
        self.pc = self.page_confidence
        self.tb = self.textblocks
        self.tbs = self.textblocks
        self.get_image_name = self.get_image_path

    def crop(
        self, x: int = 0, y: int = 0, width: int = 0, height: int = 0
    ) -> Image.Image:
        """
        Crops the page's image to the provided coordinates.

        :param x: X coordinate in pixels of crop rectangle's start, defaults
            to 0
        :type x: int, optional
        :param y: Y coordinate in pixels of crop rectangle's start, defaults
            to 0
        :type y: int, optional
        :param width: Width in pixels of crop rectangle
        :type width: int
        :param height: Height in pixels of crop rectangle
        :type height: int
        :rtype: PIL.Image.Image
        :return: The ``defoe.fmp.page.Page``'s image, cropped
        :raises SyntaxError: if not the correct values (integers for ``x``,
            ``y``, ``width`` and ``height``) are provided or ``width`` and
            ``height`` is lower than or equal to 0 pixels
        """

        if not all(
            [
                isinstance(x, int),
                isinstance(y, int),
                isinstance(width, int),
                isinstance(height, int),
            ]
        ):
            raise SyntaxError(
                "X, Y, width, and height integer values must all be provided."
            )

        if width <= 0 or height <= 0:
            raise SyntaxError("Width and height must be over 0.")

        return self.image.crop([x, y, x + width, y + height])

    def _query(
        self, xpath_query
    ) -> list[Optional[Union[etree._ElementUnicodeResult, etree._Element]]]:
        """
        Run XPath query.

        :param xpath_query: XPath query
        :type xpath_query: lxml.etree.XPath
        :return: A list of query results or an empty list if no result is
            returned from query
        :rtype: list[Optional[Union[etree._ElementUnicodeResult,
            etree._Element]]], depending on the query
        """
        return xpath_query(self.tree)

    def _single_query(
        self, xpath_query
    ) -> Optional[Union[etree._ElementUnicodeResult, etree._Element]]:
        """
        Run XPath query and return first result.

        :param xpath_query: XPath query
        :type xpath_query: lxml.etree.XPath
        :return: The query's result or None if no result is returned
        :rtype: Optional[Union[etree._ElementUnicodeResult, etree._Element]]
        """
        result = self._query(xpath_query)
        if not result:
            return None
        return result[0]

    @property
    def areas(self) -> list[Area]:
        """
        Returns a list of the ``defoe.fmp.page.Page``'s
        :class:`defoe.fmp.area.Area` objects.

        (Calls :func:`~defoe.fmp.document.Document.get_areas_by_page_code`
        with the current ``defoe.fmp.page.Page``'s code as its argument)

        :return: The ``defoe.fmp.page.Page``'s areas as a list.
        :rtype: list[:class:`defoe.fmp.area.Area`]
        """
        if not self._areas:
            self._areas = self.document.get_areas_by_page_code(
                selected_page_code=self.code
            )

            # Select this page's areas, as we get back a dict with one key--
            # this page's code
            self._areas = self._areas[self.code]

        return self._areas

    @property
    def textblocks(self) -> Iterator[TextBlock]:
        """
        Iterate over textblocks.

        :return: The ``defoe.fmp.page.Page``'s Textblocks
        :rtype: Iterator[:class:`defoe.fmp.textblock.TextBlock`]
        """
        for tb in self._query(Page.TB_XPATH):
            yield TextBlock(tb, self)

    @property
    def words(self) -> list[str]:
        """
        Returns all the words in the ``defoe.fmp.page.Page``. These are then
        saved in an attribute, so the words are only retrieved once.

        :return: List of words on ``defoe.fmp.page.Page``
        :rtype: list[str]
        """
        if not self._words:
            self._words = list(map(str, self._query(Page.WORDS_XPATH)))
        return self._words

    @property
    def word_confidences(self):
        """
        Returns all the word confidences in the ``defoe.fmp.page.Page``. These
        are then saved in an attribute, so the word confidences are only
        retrieved once.

        :return: List of word confidences on ``defoe.fmp.page.Page``
        :rtype: list[float]
        """
        if not self._word_confidences:
            self._word_confidences = list(self._query(Page.WC_XPATH))

        # Attempt to set word confidence to floating point
        try:
            self._word_confidences = [
                float(x) if x else 0 for x in self._word_confidences
            ]
        except ValueError:
            pass

        return self._word_confidences

    @property
    def character_confidences(self) -> list[float]:
        """
        Returns all the character confidences in the ``defoe.fmp.page.Page``.
        These are then saved in an attribute, so the character confidences are
        only retrieved once.

        :return: List of character confidences on ``defoe.fmp.page.Page``
        :rtype: list[float]
        """
        if not self._character_confidences:
            self._character_confidences = list(self._query(Page.CC_XPATH))

        # Attempt to set character confidence to floating point
        try:
            self._character_confidences = [
                float(x) if x else 0 for x in self._character_confidences
            ]
        except ValueError:
            pass

        return self._character_confidences

    @property
    def strings(self) -> list[etree._ElementStringResult]:
        """
        Returns all strings in the ``defoe.fmp.page.Page``. These are then
        saved in an attribute, so the strings are only retrieved once.

        :return: List of strings on ``defoe.fmp.page.Page``
        :rtype: list[lxml.etree._ElementStringResult]
        """
        if not self._strings:
            self._strings = self._query(Page.STRINGS_XPATH)
        return self._strings

    @property
    def textblock_ids(self) -> list[etree._ElementStringResult]:
        """
        Returns all strings in the ``defoe.fmp.page.Page``. These are then
        saved in an attribute, so the strings are only retrieved once.

        :return: List of strings on ``defoe.fmp.page.Page``
        :rtype: list[lxml.etree._ElementStringResult]
        """
        if not self._textblock_ids:
            self._textblock_ids = list(self._query(Page.TB_XPATH_ID))
        return self._textblock_ids

    @property
    def graphics(self) -> list[etree._Element]:
        """
        Returns all graphical elements in the ``defoe.fmp.page.Page``. These
        are then saved in an attribute, so the graphical elements are only
        retrieved once.

        :return: List of graphical elements on ``defoe.fmp.page.Page``
        :rtype: list[lxml.etree._Element]
        """
        if not self._graphics:
            self._graphics = self._query(Page.GRAPHICS_XPATH)
        return self._graphics

    @property
    def content(self) -> str:
        """
        Returns all the words in the ``defoe.fmp.page.Page``, concatenated
        together using ' ' as delimiter.

        :return: Content
        :rtype: str
        """
        return " ".join(self.words)

    @property
    def image(self) -> Image.Image:
        """
        Returns the ``defoe.fmp.page.Page``'s image.

        :return: Page image
        :rtype: PIL.Image.Image
        """
        if not self._image:
            self._image = self.document.archive.open_image(
                self.document.code, self.code
            )
        return self._image

    @property
    def image_path(self) -> Union[str, None]:
        """
        Returns the path to the ``defoe.fmp.page.Page``'s image. (Calls
        :func:`~defoe.fmp.page.Page.get_image_path`)

        :return: Page image path
        :rtype: str
        """
        if not self._image_path:
            self._image_path = self.get_image_path()
        return self._image_path

    def get_image_path(
        self,
        document_code: Optional[str] = None,
        page_code: Optional[str] = None,
    ) -> str:
        """
        Returns the path to a given ``defoe.fmp.document.Document``'s
        ``defoe.fmp.page.Page``'s image.
        (Calls :func:`~defoe.fmp.archive.Archive.get_image_path`)

        :param document_code: Page file code,
        :type document_code: str, optional
        :param page_code: File code
        :type page_code: str, optional
        :return: Page image path
        :rtype: str
        """
        if not document_code:
            document_code = self.document.code
        if not page_code:
            page_code = self.code

        return self.document.archive.get_image_path(document_code, page_code)

    def highlight(
        self,
        image: Optional[Image.Image] = None,
        highlight: list[Optional[tuple[int, int, int, int, str, str]]] = [],
    ) -> Image.Image:
        """
        Takes an optional image (or defaults to the ``defoe.fmp.page.Page``'s
        image) and annotates it with highlights.

        :param image: The input image
        :type image: Optional[PIL.Image.Image]
        :param highlight: A list of all the rectangles in need of highlight.
            The list should contain 4-, 5-, or 6-tuples with
            ``[(x0, y0, x1, y1)]`` as the minimum required tuple information.
            The remaining two positions can include an RGB value for the fill
            colour, and a floating point value between 0 and 1 for opacity:
            ``[(x0, y0, x1, y1, (255, 255, 255))]`` or
            ``[(x0, y0, x1, y1, (255, 255, 255), 0.4)]``
        :type highlight: list[Optional[tuple[int, int, int, int, str, str]]]
        :return: A copy of the input image with highlights applied
        :rtype: PIL.Image.Image
        :raises TypeError: if the image provided is not of the correct format
        """

        if not image:
            image = self.image

        if not isinstance(image, Image.Image):
            raise TypeError("Image needs to be of type PIL.Image.Image")

        # create a copy of im
        im = image.copy().convert("RGBA")

        # create overlay
        for rect in highlight:
            x0, y0, x1, y1, *others = rect
            if len(others) == 0:
                fill = AUTO_FILL
                opacity = AUTO_OPACITY
            elif len(others) == 1:
                fill = others[0]
                opacity = AUTO_OPACITY
            elif len(others) == 2:
                fill = others[0]
                opacity = others[1]
            else:
                raise SyntaxError(
                    f"Too many arguments passed to highlight function: {rect}"
                )

            overlay = Image.new("RGBA", im.size, fill + (0,))

            opacity = int(255 * opacity)
            fill = fill + (opacity,)

            draw = ImageDraw.Draw(overlay)
            draw.rectangle(((x0, y0), (x1, y1)), fill=fill)

            im = Image.alpha_composite(im, overlay)

        return im

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
        ``TextBlock`` on the ``defoe.fmp.page.Page``. See the documentation of
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

    def get_cropped_areas(self, include_areas: Optional[list[str]] = []):
        """
        Returns a dictionary consisting of page area IDs as keys and a
        dictionary as value with two keys: "area" and "image". "Area" provides
        the ``defoe.fmp.area.Area`` object for the page area and "image"
        provides a ``PIL.Image.Image`` with a cropped image of the given page
        area.

        The function can be limited to a restricted list of area IDs, provided
        as an ``include_areas`` parameter.

        :param include_areas: List of area IDs to include; if no list provided,
            all page areas will be included
        :type include_areas: list[str], optional
        :return: Dictionary with page area IDs as keys and value consisting of
            a dictionary providing access to the ``defoe.fmp.area.Area``
            object and cropped ``PIL.Image.Image`` for the page area.
        :rtype: dict
        """
        areas = self.areas

        if include_areas:
            areas = [x for x in areas if x.id in include_areas]

        return {
            area.id: {
                "area": area,
                "image": self.crop(area.x, area.y, area.width, area.height),
            }
            for area in areas
        }
