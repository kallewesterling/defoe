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
        (
            self.area_id,
            self.area_type,
            self.area_category,
        ) = area_element.values()
        self.img, self.type, _coords = file_pointer_element.values()

        # Correct coords
        self.coords = [int(x) for x in _coords.split(",")]

        # Get article_id
        self.article_id = art_id_lookup[self.area_id]

        # See property accessors below
        self._page = None
        self._textblock = None
        self._page_textblocks = None

    @property
    def page(self):
        if not self._page:
            self._page = self.document.page(self.page_code)
        return self._page

    @property
    def textblock(self):
        if not self._textblock:
            for tb in self.page_textblocks:
                if self._textblock:
                    continue
                if tb.id == self.area_id:
                    self._textblock = tb
        return self._textblock

    @property
    def page_textblocks(self):
        if not self._page_textblocks:
            self._page_textblocks = list(self.page.textblocks)
        return self._page_textblocks
