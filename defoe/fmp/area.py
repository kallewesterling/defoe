from .textblock import TextBlock
from .page import Page
from typing import Union
from lxml import etree


class Area:
    def __init__(
        self,
        document,
        page_code: str,
        area_element: etree._Element,
        file_pointer_element: etree._Element,
        art_id_lookup: Union[dict, None] = None,
    ):
        if not art_id_lookup:
            art_id_lookup = document.art_id_lookup

        self.document = document
        self.page_code = page_code

        # Extract element values
        self.id, self.type, self.category = area_element.values()
        self.img, self.type, _coords = file_pointer_element.values()

        # Correct coords
        self.coords = [int(x) for x in _coords.split(",")]

        # Get article_id
        self.article_id = art_id_lookup[self.id]

        # See property accessors below
        self._page = None
        self._textblock = None
        self._page_textblocks = None
        self._content = None

    @property
    def page(self) -> Page:
        if not self._page:
            self._page = self.document.page(self.page_code)
        return self._page

    @property
    def textblock(self) -> TextBlock:
        if not self._textblock:
            for tb in self.page_textblocks:
                if self._textblock:
                    continue
                if tb.id == self.id:
                    self._textblock = tb
        return self._textblock

    @property
    def page_textblocks(self) -> list:
        if not self._page_textblocks:
            self._page_textblocks = list(self.page.textblocks)
        return self._page_textblocks

    @property
    def content(self) -> str:
        """
        Shortcut to self.textblock.content
        """
        if not self._content:
            if self.textblock:
                self._content = self.textblock.content
            else:
                self._content = ""

        return self._content
