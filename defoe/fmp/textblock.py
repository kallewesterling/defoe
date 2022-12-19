"""
Object model representation of a textblock represented as an XML file in
METS/MODS format.
"""

from pathlib import Path
import mimetypes

mimetypes.init()
image_types = [
    x for x, y in mimetypes.types_map.items() if y.split("/")[0] == "image"
]


class TextBlock(object):
    """
    Object model representation of a textblock represented as an XML file
    in METS/MODS format.
    """

    # XPath Queries
    STRINGS_XPATH = "TextLine/String"  # String elements
    WC_XPATH = "TextLine/String/@WC"  # Word confidence content
    CC_XPATH = "TextLine/String/@CC"  # Character confidence content
    WORDS_XPATH = "TextLine/String/@CONTENT"  # Word content

    def __init__(
        self, textblock_tree, document_code, page_code, document, page
    ):
        """
        Constructor.
        """
        self.textblock_tree = textblock_tree
        self.document_code = document_code
        self.page_code = page_code
        self.document = document
        self.page = page
        self._words = None
        self._strings = None
        self.textblock_images = None
        self._wc = None
        self._cc = None
        self._image = None
        self.textblock_shape = None  # this is set by defoe.fmp.document
        # Note that the attribute `textblock_coords` is only set when
        # iterating through a Document.articles.
        # TODO: The attribute `textblock_coords` should be set on the object
        # instead.
        self.textblock_coords = None  # this is set by defoe.fmp.document
        self.textblock_page_area = None
        self.textblock_id = self.textblock_tree.get("ID")
        self.page_name = document_code + "_" + page_code + ".xml"
        self.image_name = self.get_image_name(document_code, page_code)

    # TODO: write this function and get it in the __init__
    def get_textblock_coords(self):
        """this should get minX maxX minY maxY"""
        raise NotImplementedError()

    @property
    def image(self):
        """
        Gets the image for the text block. This is then saved in an attribute,
        so the image is only retrieved once.

        :return: page image
        :rtype: PIL.Image.Image
        """
        if not self._image:
            self._image = self.get_image_name()
        return self._image

    # TODO: write this function and get it in the __init__
    def get_cropped_image(self):
        """
        should return the image cropped to this TextBlock...
        i.e. test for image, test for textblock_coords
        """
        raise NotImplementedError()

    def get_image_name(self, document_code=None, page_code=None):
        return self.page.image

    @property
    def words(self):
        """
        Gets all words in textblock. These are then saved in an attribute,
        so the words are only retrieved once.

        :return: words
        :rtype: list(str)
        """
        if not self._words:
            self._words = list(
                map(str, self.textblock_tree.xpath(TextBlock.WORDS_XPATH))
            )
        return self._words

    @property
    def wc(self):
        """
        Gets all word confidences (wc)  in textblock. These are then saved in
        an attribute, so the wc are only retrieved once.

        :return: wc
        :rtype: list(str)
        """
        if not self._wc:
            self._wc = list(self.textblock_tree.xpath(TextBlock.WC_XPATH))
        return self._wc

    @property
    def cc(self):
        """
        Gets all character confidences (cc)  in textblock. These are then
        saved in an attribute, so the cc are only retrieved once.

        :return: cc
        :rtype: list(str)
        """
        if not self._cc:
            self._cc = list(self.textblock_tree.xpath(TextBlock.CC_XPATH))

        return self._cc

    @property
    def strings(self):
        """
        Gets all strings in textblock. These are then saved in an attribute,
        so the strings are only retrieved once.

        :return: strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
        if not self._strings:
            self._strings = self.textblock_tree.xpath(TextBlock.STRINGS_XPATH)
        return self._strings

    @property
    def content(self):
        """
        Gets all words in textblock and concatenates together using ' ' as
        delimiter.

        :return: content
        :rtype: str
        """
        return " ".join(self.words)

    @property
    def locations(self):
        """
        Gets all strings in textblock and returns them as a list of tuples:
            [
                (x, y, width, height, content)
            ]
        """
        attribs = [string.attrib for string in self.strings]
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

    def get_article_id(self):
        """Attempts to get article ID in parent document for the TextBlock"""
        test = [
            id
            for id, textblock_ids in self.document.articlesParts.items()
            if self.textblock_id in textblock_ids
        ]

        if len(test) == 1:
            return test[0]

        raise RuntimeError(
            "Article ID for TextBlock could not be reconstructed:\n- "
            + "\n- ".join(test)
        )
