"""
Object model representation of a page area represented as an XML file in
METS/MODS format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from defoe.fmp.document import Document
    from defoe.fmp.page import Page
    from defoe.fmp.textblock import TextBlock
    from lxml import etree
    from typing import Optional


class Area:
    """
    Object model representation of a page area represented as an XML file in
    METS/MODS format.

    You would not typically create an Area object yourself, but find it by
    iterating through a ``defoe.fmp.page.Page``'s areas property.
    See :func:`~defoe.fmp.page.Page.areas` and the usage below for more
    detailed information.

    Usage:

    .. code-block:: python

        from defoe.fmp.archive import Archive

        archive = Archive("path/to/xml-files/")

        # See documentation for defoe.fmp.document.Document here:
        document = archive[0]

        # See documentation for defoe.fmp.page.Page here:
        page = document[0]

        # Iterate through an archive's document's page's areas
        for area in page.areas:
            # Access the properties and methods from the TextBlock
            print(area.tokens)

    :param document: ``defoe.fmp.document.Document`` object corresponding to
        document to which this page belongs.
    :type document: defoe.fmp.document.Document
    :param code: Identifier for this page within an archive
    :type code: str
    :param area_element: The METS file's structural map element that identifies
        the ``defoe.fmp.area.Area`` object in the
        ``defoe.fmp.document.Document``
    :type area_element: lxml.etree._Element
    :param file_pointer_element: The METS file's file pointer (<fptr>) element
        that identifies the ``defoe.fmp.area.Area`` in the corresponding
        ``defoe.fmp.document.Document``
    :type file_pointer_element: lxml.etree._Element
    :param article_id_lookup: Dictionary with the page area identifier as key
        and the article ID to which the page area belongs as key, see
        :func:`~defoe.fmp.document.Document.article_id_lookup` for creation of
        such a ``dict``
    :type article_id_lookup: Optional[dict]
    :param page_parts: A dictionary with parts/textblocks IDs as keys, and
        page and area as values, defaults to the provided
        ``defoe.fmp.document.Document``'s ``page_parts`` property, see
        :func:`~defoe.fmp.document.Document.page_parts` for detailed
        information
    :type page_parts: Optional[dict], optional
    """

    def __init__(
        self,
        document: Document,
        page_code: str,
        area_element: etree._Element,
        file_pointer_element: etree._Element,
        article_id_lookup: Optional[dict] = None,
        page_parts: Optional[dict] = None,
    ):
        if not article_id_lookup:
            article_id_lookup = document.article_id_lookup

        if not page_parts:
            page_parts = document.page_parts

        self.document = document
        self.page_code = page_code

        # Extract element values
        self.id, self.type, self.category = area_element.values()
        self.img, self.type, _coords = file_pointer_element.values()

        # Correct coords
        self.coords = [int(x) for x in _coords.split(",")]
        """
        Returns the ``defoe.fmp.area.Area``'s pixel coordinates
        ``[x0, y0, x1, y1]`` on its page.

        :rtype: list[int, int, int, int]
        """

        self.x0, self.y0, self.x1, self.y1 = self.coords

        self.width = self.x1 - self.x0
        """
        Returns the ``defoe.fmp.area.Area``'s width in pixels.

        :rtype: int
        """

        self.height = self.y1 - self.y0
        """
        Returns the ``defoe.fmp.area.Area``'s height in pixels.

        :rtype: int
        """

        self.x = self.x0
        """
        Returns the ``defoe.fmp.area.Area``'s X position on the page in
        pixels.

        :rtype: int
        """

        self.y = self.y0
        """
        Returns the ``defoe.fmp.area.Area``'s Y position on the page in
        pixels.

        :rtype: int
        """

        # Get article_id
        try:
            self.article_id = article_id_lookup[self.id]
            """
            Returns the ``defoe.fmp.area.Area``'s ID as a string
            representation.

            :rtype: str
            """
        except KeyError:
            # TODO: Issue warning that article ID is set to None
            self.article_id = None

        # Get page part
        try:
            self.page_part = page_parts[self.id]
        except KeyError:
            # TODO: Issue warning that page part is set to None
            self.page_part = None

        # See property accessors below
        self._page = None
        self._textblock = None
        self._page_textblocks = None
        self._content = None

    @property
    def page(self) -> Page:
        """
        Easy access to the parent ``defoe.fmp.page.Page`` for the
        ``defoe.fmp.area.Area``.

        :return: The ``defoe.fmp.area.Area``'s parent ``defoe.fmp.page.Page``
        :rtype: defoe.fmp.page.Page
        """
        if not self._page:
            self._page = self.document.page(self.page_code)
        return self._page

    @property
    def textblock(self) -> TextBlock:
        """
        Easy access to the parent ``defoe.fmp.textblock.TextBlock`` for the
        ``defoe.fmp.area.Area``.

        :return: The parent ``defoe.fmp.page.Page``'s
            ``defoe.fmp.textblock.TextBlock`` that corresponds to the
            ``defoe.fmp.area.Area``
        :rtype: defoe.fmp.textblock.TextBlock
        """
        if not self._textblock:
            for tb in self.page_textblocks:
                if self._textblock:
                    continue
                if tb.id == self.id:
                    self._textblock = tb
        return self._textblock

    @property
    def page_textblocks(self) -> list[TextBlock]:
        """
        Returns a list of all the ``defoe.fmp.textblock.TextBlock`` objects on
        ``defoe.fmp.area.Area``'s parent ``defoe.fmp.page.Page``.

        :return: List of all the ``defoe.fmp.textblock.TextBlock`` objects on
            ``defoe.fmp.area.Area``'s parent page
        :rtype: list[TextBlock]
        """
        if not self._page_textblocks:
            self._page_textblocks = list(self.page.textblocks)
        return self._page_textblocks

    @property
    def content(self) -> str:
        """
        Shortcut property to self.textblock.content.

        :return: A string containing all of the ``defoe.fmp.area.Area``'s
            content
        :rtype: str
        """
        if not self._content:
            if self.textblock:
                self._content = self.textblock.content
            else:
                self._content = ""

        return self._content

    @property
    def tokens(self) -> list[Optional[tuple[int, int, int, int, str]]]:
        """
        Returns all tokens in the Area and returns them as a list of
        tuples: ``[(x, y, width, height, content)]``.

        :return: The ``defoe.fmp.area.Area``'s tokens as list of tuples
        :rtype: list[Optional[tuple[int, int, int, int, str]]]
        """
        if not self.textblock:
            return []

        attribs = [string.attrib for string in self.textblock.strings]
        return [
            (
                int(x["HPOS"]),
                int(x["VPOS"]),
                int(x["WIDTH"]),
                int(x["HEIGHT"]),
                x["CONTENT"],
            )
            for x in attribs
        ]
