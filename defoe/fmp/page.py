"""
Object model representation of a page represented as an XML file in METS/MODS
format.
"""

from .textblock import TextBlock

from lxml import etree
from PIL import Image, ImageDraw
from typing import Union

AUTO_FILL = (200, 100, 0)
AUTO_OPACITY = 0.25


class Page(object):
    """
    Object model representation of a page represented as an XML file in METS/
    MODS format.
    """

    # XPath Queries
    WORDS_XPATH = etree.XPath("//String/@CONTENT")  # String content
    STRINGS_XPATH = etree.XPath("//String")  # String elements
    GRAPHICS_XPATH = etree.XPath("//GraphicalElement")  # Graphical elements
    # TODO: for doc, the above was renamed due to images being in the mix
    PAGE_XPATH = etree.XPath("//Page")  # Page
    WC_XPATH = etree.XPath("//String/@WC")  # Word confidence content
    CC_XPATH = etree.XPath("//String/@CC")  # Character confience content
    TB_XPATH_ID = etree.XPath("//TextBlock/@ID")  # Textblock ID
    TB_XPATH = etree.XPath("//TextBlock")  # Textblock content

    def __init__(self, document, code, source=None):
        """
        Constructor.

        :param document: Document object corresponding to document to
        which this page belongs
        :type document: defoe.alto.document.Document
        :param code: identifier for this page within an archive
        :type code: str
        :param source: stream. If None then an attempt is made to
        open the file holding the page via the given "document"
        :type source: zipfile.ZipExt or another file-like object
        """

        self.document = document
        self.code = code

        self.source = source
        if not self.source:
            self.source = document.archive.open_page(document.code, code)

        self.tree = etree.parse(self.source)
        self.page_tree = self.single_query(Page.PAGE_XPATH)
        self.width = int(self.page_tree.get("WIDTH"))
        self.height = int(self.page_tree.get("HEIGHT"))
        self.pc = self.page_tree.get("PC")

        self.tb = [
            TextBlock(tb, document.code, code, document, self)
            for tb in self.query(Page.TB_XPATH)
        ]

        # See property accessors below
        self._words = None
        self._strings = None
        self._graphics = None
        self._wc = None
        self._cc = None
        self._textblock_ids = None
        self._image = None
        self._image_path = None

        # Adding backward compatibility
        self.page_words = self.words
        self.page_strings = self.strings
        self.page_wc = self.wc
        self.page_cc = self.cc

    def crop(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        """
        should return the page image cropped to the provided coord...
        i.e. test for image
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

    def query(self, xpath_query):
        """
        Run XPath query.

        :param xpath_query: XPath query
        :type xpath_query: lxml.etree.XPath
        :return: list of query results or None if none
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        return xpath_query(self.tree)

    def single_query(self, xpath_query):
        """
        Run XPath query and return first result.

        :param xpath_query: XPath query
        :type xpath_query: lxml.etree.XPath
        :return: query result or None if none
        :rtype: lxml.etree.<MODULE> (depends on query)
        """
        result = self.query(xpath_query)
        if not result:
            return None
        return result[0]

    @property
    def words(self) -> list:
        """
        Gets all words in page. These are then saved in an attribute,
        so the words are only retrieved once.

        :return: words
        :rtype: list(str)
        """
        if not self._words:
            self._words = list(map(str, self.query(Page.WORDS_XPATH)))
        return self._words

    @property
    def wc(self):
        """
        Gets all word confidences (wc) in page. These are then saved in an
        attribute, so the wc are only retrieved once.

        :return: wc
        :rtype: list(str)
        """
        if not self._wc:
            self._wc = list(self.query(Page.WC_XPATH))
        return self._wc

    @property
    def cc(self) -> list:
        """
        Gets all character confidences (cc) in page. These are then saved in
        an attribute, so the cc are only retrieved once.

        :return: cc
        :rtype: list(str)
        """
        if not self._cc:
            self._cc = list(self.query(Page.CC_XPATH))
        return self._cc

    @property
    def strings(self) -> list:
        """
        Gets all strings in page. These are then saved in an attribute, so the
        strings are only retrieved once.

        :return: strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
        if not self._strings:
            self._strings = self.query(Page.STRINGS_XPATH)
        return self._strings

    @property
    def textblock_ids(self) -> list:
        """
        Gets all strings in page. These are then saved in an attribute, so the
        strings are only retrieved once.

        :return: strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
        if not self._textblock_ids:
            self._textblock_ids = list(self.query(Page.TB_XPATH_ID))
        return self._textblock_ids

    @property
    def graphics(self) -> list:
        """
        Gets all graphical elements in page. These are then saved in an
        attribute, so the graphical elements are only retrieved once.

        :return: images
        :rtype: list(lxml.etree._Element)
        """
        if not self._graphics:
            self._graphics = self.query(Page.GRAPHICS_XPATH)
        return self._graphics

    @property
    def content(self) -> str:
        """
        Gets all words in page and concatenates together using ' ' as
        delimiter.

        :return: content
        :rtype: str
        """
        return " ".join(self.words)

    @property
    def image(self) -> Image.Image:
        if not self._image:
            self._image = self.document.archive.open_image(
                self.document.code, self.code
            )
        return self._image

    @property
    def image_path(self) -> Union[str, None]:
        if not self._image_path:
            self._image_path = self.get_image_name()
        return self._image_path

    def get_image_name(self, document_code=None, page_code=None):
        if not document_code:
            document_code = self.document.code
        if not page_code:
            page_code = self.code

        return self.document.archive.get_image_path(document_code, page_code)

    def highlight(self, image=None, highlight=[]):
        """
        image: (optional) image
        highlight: [(x0, y0, x1, y1, "")]
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
